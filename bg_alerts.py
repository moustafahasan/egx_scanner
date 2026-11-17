import os
import json
import math
import urllib.request
import urllib.parse
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").strip().rstrip("/")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "").strip()
TG_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
TG_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
FEE_RATE = float(os.environ.get("EGX_FEE_RATE", "0.0016"))
ALERT_BUFFER_PCT = float(os.environ.get("ALERT_BUFFER_PCT", "2.5"))


def get_cairo_now() -> datetime:
    try:
        return datetime.now(ZoneInfo("Africa/Cairo"))
    except Exception:
        return datetime.now(timezone(timedelta(hours=2)))


def is_egx_market_open(now_dt: datetime) -> bool:
    if now_dt.weekday() not in [6, 0, 1, 2, 3]:
        return False
    mins = now_dt.hour * 60 + now_dt.minute
    return (9 * 60 + 55) <= mins <= (14 * 60 + 40)


def sb_request(method: str, endpoint: str, payload=None, extra_headers: dict = None):
    if not SUPABASE_URL or not SUPABASE_KEY:
        return False, "Missing Supabase credentials"
    url = f"{SUPABASE_URL}/rest/v1/{endpoint}"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }
    if extra_headers:
        headers.update(extra_headers)
    data_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8") if payload is not None else None
    try:
        req = urllib.request.Request(url, data=data_bytes, headers=headers, method=method)
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read().decode("utf-8")
            return True, (json.loads(raw) if raw else [])
    except Exception as e:
        return False, str(e)


def send_telegram(text_html: str) -> bool:
    if not TG_TOKEN or not TG_CHAT_ID:
        return False
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = json.dumps({
        "chat_id": TG_CHAT_ID,
        "text": text_html,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }).encode("utf-8")
    try:
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            return bool(res.get("ok"))
    except Exception:
        return False


def fetch_tv_quotes() -> dict:
    url = "https://scanner.tradingview.com/egypt/scan"
    cols = ["name", "close", "change", "volume", "ATR", "EMA20", "VWAP"]
    payload = json.dumps({
        "filter": [{"left": "type", "operation": "in_range", "right": ["stock", "dr", "fund"]}],
        "options": {"lang": "en"},
        "markets": ["egypt"],
        "symbols": {"query": {"types": []}, "tickers": []},
        "columns": cols,
        "range": [0, 500]
    }).encode("utf-8")
    quotes = {}
    try:
        req = urllib.request.Request(
            url, data=payload,
            headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8")).get("data", [])
            for row in data:
                full_s = row.get("s", "")
                d = row.get("d", [])
                if ":" not in full_s or len(d) < 2:
                    continue
                sym = full_s.split(":")[1].strip().upper()
                close_v = float(d[1] or 0.0)
                if close_v <= 0:
                    continue
                quotes[sym] = {
                    "close": close_v,
                    "change": float(d[2] or 0.0),
                    "volume": float(d[3] or 0.0),
                    "atr": float(d[4] or (close_v * 0.025)),
                    "ema20": float(d[5] or close_v),
                    "vwap": float(d[6] or close_v),
                }
    except Exception as e:
        print(f"TV fetch error: {e}")
    return quotes


def run():
    now_dt = get_cairo_now()
    if not is_egx_market_open(now_dt):
        print(f"[{now_dt.strftime('%H:%M')}] Market closed. Skipping.")
        return

    ok_p, portfolio = sb_request(
        "GET",
        "egx_portfolio?select=symbol,shares,buy_price,stop_loss,tp1,tp2,trailing_enabled,trailing_stage"
    )
    if not ok_p:
        ok_p, portfolio = sb_request("GET", "egx_portfolio?select=symbol,shares,buy_price,stop_loss,tp1,tp2")
    if not ok_p or not portfolio:
        print("No portfolio items found or Supabase error.")
        return

    today_str = now_dt.strftime("%Y-%m-%d")
    q_prefix = urllib.parse.quote(f"{today_str}%")
    ok_l, logs_raw = sb_request("GET", f"egx_alerts_log?select=alert_key&alert_key=like.{q_prefix}")
    sent_keys = {r["alert_key"] for r in logs_raw} if (ok_l and isinstance(logs_raw, list)) else set()

    quotes = fetch_tv_quotes()
    if not quotes:
        return

    for item in portfolio:
        sym = str(item.get("symbol", "")).upper().replace(".CA", "").strip()
        shares = int(item.get("shares", 0))
        buy_p = float(item.get("buy_price", 0.0))
        if not sym or shares <= 0 or buy_p <= 0 or sym not in quotes:
            continue

        q = quotes[sym]
        curr_p = q["close"]
        atr14 = q["atr"] if q["atr"] > 0 else (buy_p * 0.025)
        vwap = q["vwap"] if q["vwap"] > 0 else curr_p
        ema20 = q["ema20"] if q["ema20"] > 0 else curr_p

        sl = float(item.get("stop_loss", 0.0))
        if sl <= 0:
            sl = round(max(0.01, buy_p - 2.0 * atr14), 2)
        risk_u = max(0.01, buy_p - sl)
        tp1 = float(item.get("tp1", 0.0)) or round(buy_p + 1.618 * risk_u, 2)
        tp2 = float(item.get("tp2", 0.0)) or round(buy_p + 2.618 * risk_u, 2)
        trailing_on = bool(item.get("trailing_enabled", True))
        trailing_stage = int(item.get("trailing_stage", 0))

        # 1. منطق الوقف المتحرك الآلي (Smart Trailing Stop)
        if trailing_on:
            be_price = round(buy_p * (1.0 + FEE_RATE * 2.0), 2)
            if curr_p >= tp1 and trailing_stage < 1 and be_price < curr_p:
                new_sl = max(sl, be_price)
                sb_request(
                    "PATCH",
                    f"egx_portfolio?symbol=eq.{urllib.parse.quote(sym)}",
                    payload={"stop_loss": new_sl, "trailing_stage": 1, "updated_at": now_dt.isoformat()}
                )
                sl = new_sl
                trailing_stage = 1
                tr_key = f"{today_str}_{sym}_TRAIL_BE"
                if tr_key not in sent_keys:
                    msg = (
                        f"🛡️ <b>تأمين الصفقة آلياً (Breakeven) — {sym}</b>\n"
                        f"السعر وصل للهدف الأول <b>TP1 ({tp1})</b>.\n"
                        f"تم رفع وقف الخسارة تلقائياً إلى نقطة التعادل: <b>{new_sl} ج.م</b>."
                    )
                    if send_telegram(msg):
                        sb_request("POST", "egx_alerts_log", payload={"alert_key": tr_key, "sent_time": now_dt.strftime("%H:%M")})
                        sent_keys.add(tr_key)

            if curr_p >= tp2:
                anchor = max(vwap, ema20)
                cand_sl = round(min(curr_p - 0.5 * atr14, anchor * 0.992), 2)
                if cand_sl > sl * 1.003 and cand_sl < curr_p:
                    sb_request(
                        "PATCH",
                        f"egx_portfolio?symbol=eq.{urllib.parse.quote(sym)}",
                        payload={"stop_loss": cand_sl, "trailing_stage": 2, "updated_at": now_dt.isoformat()}
                    )
                    sl = cand_sl
                    tr2_key = f"{today_str}_{sym}_TRAIL_{int(cand_sl * 100)}"
                    if tr2_key not in sent_keys:
                        msg = (
                            f"🚀 <b>ملاحقة الأرباح (Trailing Stop) — {sym}</b>\n"
                            f"السعر الحالي: <b>{curr_p} ج.م</b> (أعلى TP2).\n"
                            f"تم رفع وقف حماية الأرباح الجديد إلى: <b>{cand_sl} ج.م</b>."
                        )
                        if send_telegram(msg):
                            sb_request("POST", "egx_alerts_log", payload={"alert_key": tr2_key, "sent_time": now_dt.strftime("%H:%M")})
                            sent_keys.add(tr2_key)

        # 2. تنبيهات الوقف والأهداف القياسية
        net_pnl = (shares * (curr_p - buy_p)) - (shares * curr_p * FEE_RATE)
        net_pct = ((curr_p - buy_p) / buy_p) * 100.0
        dist_sl = ((curr_p - sl) / curr_p) * 100.0
        dist_tp1 = ((tp1 - curr_p) / curr_p) * 100.0

        alert_code = None
        msg_body = None
        if curr_p <= sl:
            alert_code = "HIT_SL"
            msg_body = f"🚨 <b>كسر وقف الخسارة — {sym}</b>\nالسعر: <b>{curr_p}</b> | الوقف: <b>{sl}</b>\nالصافي: {net_pnl:+,.0f} ج.م ({net_pct:+.1f}%)"
        elif 0 < dist_sl <= ALERT_BUFFER_PCT:
            alert_code = "NEAR_SL"
            msg_body = f"⚠️ <b>اقتراب من الوقف — {sym}</b>\nالسعر: <b>{curr_p}</b> (يبعد {dist_sl:.1f}% عن <b>{sl}</b>)"
        elif curr_p >= tp2:
            alert_code = "HIT_TP2"
            msg_body = f"🏆 <b>تحقق الهدف الثاني TP2 — {sym}</b>\nالسعر: <b>{curr_p}</b> | TP2: <b>{tp2}</b>\nالربح: <b>{net_pnl:+,.0f} ج.م ({net_pct:+.1f}%)</b>"
        elif curr_p >= tp1:
            alert_code = "HIT_TP1"
            msg_body = f"🎯 <b>تحقق الهدف الأول TP1 — {sym}</b>\nالسعر: <b>{curr_p}</b> | TP1: <b>{tp1}</b>\nالربح: <b>{net_pnl:+,.0f} ج.م ({net_pct:+.1f}%)</b>"
        elif 0 < dist_tp1 <= ALERT_BUFFER_PCT:
            alert_code = "NEAR_TP1"
            msg_body = f"🔔 <b>اقتراب من TP1 — {sym}</b>\nالسعر: <b>{curr_p}</b> (يبعد {dist_tp1:.1f}% عن <b>{tp1}</b>)"

        if alert_code and msg_body:
            dedup_key = f"{today_str}_{sym}_{alert_code}"
            if dedup_key not in sent_keys:
                if send_telegram(msg_body):
                    sb_request("POST", "egx_alerts_log", payload={"alert_key": dedup_key, "sent_time": now_dt.strftime("%H:%M")})
                    sent_keys.add(dedup_key)


if __name__ == "__main__":
    run()
