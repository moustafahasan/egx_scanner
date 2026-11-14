import os
import json
import urllib.request
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
import yfinance as yf
import pandas as pd

PORTFOLIO_FILE = "my_egx_portfolio.json"
TG_LOG_FILE = "tg_alerts_log.json"

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
EVENT_NAME = os.environ.get("GITHUB_EVENT_NAME", "schedule").strip()
FEE_RATE = float(os.environ.get("FEE_RATE", "0.0016"))
ALERT_BUFFER_PCT = float(os.environ.get("ALERT_BUFFER_PCT", "2.5"))


def get_cairo_now() -> datetime:
    try:
        return datetime.now(ZoneInfo("Africa/Cairo"))
    except Exception:
        return datetime.now(timezone(timedelta(hours=2)))


def is_egx_session_active(now_cairo: datetime) -> bool:
    # أيام التداول في البورصة المصرية: الأحد (6) إلى الخميس (3)
    if now_cairo.weekday() not in [6, 0, 1, 2, 3]:
        return False
    mins = now_cairo.hour * 60 + now_cairo.minute
    # من 10:00 صباحاً (600) إلى 2:40 ظهراً (880) لضمان تغطية الإغلاق والمزاد
    return 600 <= mins <= 880


def send_telegram(text_html: str) -> bool:
    if not BOT_TOKEN or not CHAT_ID:
        print("Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID.")
        return False
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = json.dumps({
            "chat_id": CHAT_ID,
            "text": text_html,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }).encode("utf-8")
        req = urllib.request.Request(
            url, data=payload, headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            return bool(res.get("ok"))
    except Exception as e:
        print(f"Telegram error: {e}")
        return False


def fetch_tv_quotes(symbols: list) -> dict:
    quotes = {}
    if not symbols:
        return quotes
    try:
        url = "https://scanner.tradingview.com/egypt/scan"
        payload = json.dumps({
            "symbols": {
                "tickers": [f"EGX:{s}" for s in symbols],
                "query": {"types": []}
            },
            "columns": ["name", "close", "change", "ATR"]
        }).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            for row in data.get("data", []):
                full_s = row.get("s", "")
                d = row.get("d", [])
                if ":" in full_s and len(d) >= 2 and d[1] is not None:
                    sym = full_s.split(":")[1].strip().upper()
                    close_val = float(d[1])
                    chg_val = float(d[2]) if len(d) > 2 and d[2] is not None else 0.0
                    atr_val = float(d[3]) if len(d) > 3 and d[3] is not None and d[3] > 0 else 0.0
                    quotes[sym] = {"close": close_val, "change": chg_val, "atr": atr_val}
    except Exception as e:
        print(f"TradingView fetch warning: {e}")
    return quotes


def fetch_yf_fallback(symbols: list) -> dict:
    yf_data = {}
    for sym in symbols:
        try:
            df = yf.download(f"{sym}.CA", period="2mo", interval="1d", progress=False, auto_adjust=True)
            if df is None or df.empty:
                continue
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            df = df.dropna(subset=["Close", "High", "Low"])
            if df.empty:
                continue
            prev_close = df["Close"].shift(1)
            tr = pd.concat([
                df["High"] - df["Low"],
                (df["High"] - prev_close).abs(),
                (df["Low"] - prev_close).abs()
            ], axis=1).max(axis=1)
            atr14 = float(tr.ewm(alpha=1/14, adjust=False).mean().iloc[-1])
            close_val = float(df["Close"].iloc[-1])
            yf_data[sym] = {
                "close": close_val,
                "atr": atr14 if pd.notna(atr14) and atr14 > 0 else close_val * 0.025
            }
        except Exception:
            continue
    return yf_data


def main():
    now_cairo = get_cairo_now()
    is_manual = (EVENT_NAME == "workflow_dispatch")

    if not is_manual and not is_egx_session_active(now_cairo):
        print(f"Outside EGX session ({now_cairo.strftime('%Y-%m-%d %H:%M')} Cairo). Exiting.")
        return

    if not os.path.exists(PORTFOLIO_FILE):
        print(f"{PORTFOLIO_FILE} not found.")
        return

    with open(PORTFOLIO_FILE, "r", encoding="utf-8") as f:
        portfolio = json.load(f)

    if not isinstance(portfolio, list) or not portfolio:
        print("Portfolio is empty.")
        return

    sent_log = {}
    if os.path.exists(TG_LOG_FILE):
        try:
            with open(TG_LOG_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                if isinstance(loaded, dict):
                    sent_log = loaded
        except Exception:
            sent_log = {}

    today_str = now_cairo.strftime("%Y-%m-%d")
    # تنظيف السجل من الأيام السابقة لإبقاء الملف خفيفاً
    sent_log = {k: v for k, v in sent_log.items() if k.startswith(today_str)}

    symbols = sorted(list({
        item["symbol"].upper().replace(".CA", "").strip()
        for item in portfolio if item.get("symbol")
    }))

    tv_quotes = fetch_tv_quotes(symbols)
    yf_quotes = fetch_yf_fallback(symbols)

    alerts_sent_count = 0
    summary_lines = []

    for item in portfolio:
        sym = item["symbol"].upper().replace(".CA", "").strip()
        shares = int(item.get("shares", 0))
        buy_p = float(item.get("buy_price", 0.0))
        user_sl = float(item.get("stop_loss", 0.0))
        user_tp1 = float(item.get("tp1", 0.0))
        user_tp2 = float(item.get("tp2", 0.0))

        if not sym or shares <= 0 or buy_p <= 0:
            continue

        tv_q = tv_quotes.get(sym, {})
        yf_q = yf_quotes.get(sym, {})

        curr_p = tv_q.get("close") or yf_q.get("close") or buy_p
        atr14 = tv_q.get("atr") or yf_q.get("atr") or (buy_p * 0.025)

        sl = user_sl if user_sl > 0 else round(max(0.01, buy_p - 2.0 * atr14), 2)
        risk_unit = max(0.01, buy_p - sl)
        tp1 = user_tp1 if user_tp1 > 0 else round(buy_p + 1.618 * risk_unit, 2)
        tp2 = user_tp2 if user_tp2 > 0 else round(buy_p + 2.618 * risk_unit, 2)

        cost_val = shares * buy_p
        mkt_val = shares * curr_p
        net_pnl = (mkt_val - cost_val) - (mkt_val * FEE_RATE)
        net_pnl_pct = (net_pnl / cost_val) * 100

        dist_sl_pct = ((curr_p - sl) / curr_p) * 100
        dist_tp1_pct = ((tp1 - curr_p) / curr_p) * 100

        summary_lines.append(f"• <b>{sym}</b>: {curr_p} ج.م ({net_pnl_pct:+.1f}%) | SL: {sl} | TP1: {tp1}")

        alert_code = None
        msg_body = None

        if curr_p <= sl:
            alert_code = "HIT_SL"
            msg_body = (
                f"🚨 <b>كسر وقف الخسارة — {sym}</b>\n"
                f"السعر الحالي: <b>{curr_p} ج.م</b> | الوقف: <b>{sl} ج.م</b>\n"
                f"صافي المركز: {net_pnl:+,.0f} ج.م ({net_pnl_pct:+.1f}%)"
            )
        elif 0 < dist_sl_pct <= ALERT_BUFFER_PCT:
            alert_code = "NEAR_SL"
            msg_body = (
                f"⚠️ <b>اقتراب من وقف الخسارة — {sym}</b>\n"
                f"السعر الحالي: <b>{curr_p} ج.م</b> (يبعد {dist_sl_pct:.1f}% عن الوقف <b>{sl}</b>)"
            )
        elif curr_p >= tp2:
            alert_code = "HIT_TP2"
            msg_body = (
                f"🏆 <b>تحقق الهدف الثاني TP2 — {sym}</b>\n"
                f"السعر الحالي: <b>{curr_p} ج.م</b> | الهدف TP2: <b>{tp2}</b>\n"
                f"صافي الربح: <b>{net_pnl:+,.0f} ج.م ({net_pnl_pct:+.1f}%)</b>"
            )
        elif curr_p >= tp1:
            alert_code = "HIT_TP1"
            msg_body = (
                f"🎯 <b>تحقق الهدف الأول TP1 — {sym}</b>\n"
                f"السعر الحالي: <b>{curr_p} ج.م</b> | الهدف TP1: <b>{tp1}</b>\n"
                f"صافي الربح: <b>{net_pnl:+,.0f} ج.م ({net_pnl_pct:+.1f}%)</b>"
            )
        elif 0 < dist_tp1_pct <= ALERT_BUFFER_PCT:
            alert_code = "NEAR_TP1"
            msg_body = (
                f"🔔 <b>اقتراب من الهدف TP1 — {sym}</b>\n"
                f"السعر الحالي: <b>{curr_p} ج.م</b> (يبعد {dist_tp1_pct:.1f}% عن الهدف <b>{tp1}</b>)"
            )

        if alert_code and msg_body:
            dedup_key = f"{today_str}_{sym}_{alert_code}"
            if dedup_key not in sent_log:
                if send_telegram(msg_body):
                    sent_log[dedup_key] = now_cairo.strftime("%H:%M")
                    alerts_sent_count += 1

    if is_manual and alerts_sent_count == 0:
        header = f"🦅 <b>فحص الخلفية التجريبي ({now_cairo.strftime('%H:%M')} القاهرة)</b>\n✅ النظام الخلفي يعمل بنجاح. ملخص محفظتك:\n\n"
        send_telegram(header + "\n".join(summary_lines))

    with open(TG_LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(sent_log, f, ensure_ascii=False, indent=2)

    print(f"Done. Alerts sent: {alerts_sent_count}")


if __name__ == "__main__":
    main()
