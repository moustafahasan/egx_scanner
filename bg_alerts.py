import os
import re
import json
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
    return (9 * 60 + 55) <= mins <= (14 * 60 + 55)


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


def log_alert_once(alert_key: str, sent_time: str, sent_keys: set):
    sent_keys.add(alert_key)
    sb_request(
        "POST",
        "egx_alerts_log?on_conflict=alert_key",
        payload={"alert_key": alert_key, "sent_time": sent_time},
        extra_headers={"Prefer": "resolution=merge-duplicates,return=minimal"}
    )


def fetch_tv_quotes() -> dict:
    url = "https://scanner.tradingview.com/egypt/scan"
    cols = [
        "name", "close", "change", "high", "low", "volume",
        "average_volume_10d_calc", "ATR", "EMA20", "EMA50", "EMA200", "VWAP"
    ]
    payload = json.dumps({
        "filter": [{"left": "type", "operation": "in_range", "right": ["stock", "dr", "fund"]}],
        "options": {"lang": "en"},
        "markets": ["egypt"],
        "symbols": {"query": {"types": []}, "tickers": []},
        "columns": cols,
        "sort": {"sortBy": "volume", "sortOrder": "desc"},
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
                if not re.match(r"^[A-Z0-9]{2,12}$", sym):
                    continue
                close_v = float(d[1] or 0.0)
                if close_v <= 0:
                    continue
                quotes[sym] = {
                    "close": close_v,
                    "change": float(d[2] or 0.0),
                    "high": float(d[3] or close_v),
                    "low": float(d[4] or close_v),
                    "volume": float(d[5] or 0.0),
                    "avg_vol10": float(d[6] or 0.0),
                    "atr": float(d[7] or (close_v * 0.025)),
                    "ema20": float(d[8] or close_v),
                    "ema50": float(d[9] or close_v),
                    "ema200": float(d[10] or 0.0),
                    "vwap": float(d[11] or close_v),
                }
    except Exception as e:
        print(f"TV fetch error: {e}")
    return quotes


def get_top_morning_radar(quotes: dict, elapsed_mins: int) -> list:
    progress = max(0.05, min(1.0, float(elapsed_mins) / 270.0))
    ranked = []
    for sym, q in quotes.items():
        close = q["close"]
        vol = q["volume"]
        avg_v = q["avg_vol10"]
        vwap = q["vwap"] if q["vwap"] > 0 else close
        turnover_m = (vol * vwap) / 1_000_000.0
        if turnover_m < 0.3 or q["change"] >= 19.0 or avg_v <= 0:
            continue
        rvol = vol / max(1.0, avg_v * progress)
        if rvol >= 1.35 and close > vwap and q["change"] > 0.3:
            pts = min(100, int(round(rvol * 25 + q["change"] * 4 + (15 if close > q["ema50"] else 0))))
            ranked.append((pts, rvol, sym, q))
    ranked.sort(key=lambda x: (x[0], x[1]), reverse=True)
    return ranked[:3]


def run():
    now_dt = get_cairo_now()
    if not is_egx_market_open(now_dt):
        print(f"[{now_dt.strftime('%H:%M')}] Market closed. Skipping.")
        return

    today_str = now_dt.strftime("%Y-%m-%d")
    time_str = now_dt.strftime("%H:%M")
    mins_now = now_dt.hour * 60 + now_dt.minute
    elapsed_mins = max(10, mins_now - (10 * 60))

    q_prefix = urllib.parse.quote(f"{today_str}%")
    ok_l, logs_raw = sb_request("GET", f"egx_alerts_log?select=alert_key&alert_key=like.{q_prefix}")
    sent_keys = {r["alert_key"] for r in logs_raw} if (ok_l and isinstance(logs_raw, list)) else set()

    quotes = fetch_tv_quotes()
    if not quotes:
        return

    # 1. ملخص افتتاح الجلسة (10:15 - 10:35 صباحاً)
    if (10 * 60 + 15) <= mins_now <= (10 * 60 + 35):
        morning_key = f"{today_str}_MORNING_RADAR"
        if morning_key not in sent_keys:
            top3 = get_top_morning_radar(quotes, elapsed_mins)
            if top3:
                m_lines = [f"☀️ <b>رادار افتتاح الجلسة ({time_str}) — أقوى تدفقات السيولة</b>", ""]
                for idx, (pts, rvol, sym, q) in enumerate(top3, 1):
                    sl_est = round(max(0.01, q["close"] - 2.0 * q["atr"]), 2)
                    tp1_est = round(q["close"] + 1.618 * (q["close"] - sl_est), 2)
                    m_lines.append(
                        f"{idx}. <b>{sym}</b> | السعر: <b>{q['close']}</b> ({q['change']:+.1f}%) | "
                        f"سيولة: <b>{rvol:.1f}x</b> | SL: {sl_est} | TP1: {tp1_est}"
                    )
                if send_telegram("\n".join(m_lines)):
                    log_alert_once(morning_key, time_str, sent_keys)

    # 2. قراءة المحفظة السحابية ومراقبة الوقف المتحرك والأهداف
    ok_p, portfolio = sb_request(
        "GET",
        "egx_portfolio?select=symbol,shares,buy_price,stop_loss,tp1,tp2,trailing_enabled,trailing_stage"
    )
    if not ok_p:
        ok_p, portfolio = sb_request("GET", "egx_portfolio?select=symbol,shares,buy_price,stop_loss,tp1,tp2")
    if not ok_p or not portfolio:
        print("No portfolio items found.")
        return

    total_cost = 0.0
    total_val = 0.0
    eod_lines = []

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

        # الوقف المتحرك الآلي
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
                        log_alert_once(tr_key, time_str, sent_keys)

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
                            log_alert_once(tr2_key, time_str, sent_keys)

        cost_v = shares * buy_p
        mkt_v = shares * curr_p
        net_pnl = (mkt_v - cost_v) - (mkt_v * FEE_RATE)
        net_pct = (net_pnl / cost_v) * 100.0
        total_cost += cost_v
        total_val += mkt_v

        eod_lines.append(
            f"• <b>{sym}</b>: {curr_p} ({q['change']:+.1f}% اليوم) | صافي: <b>{net_pnl:+,.0f} ({net_pct:+.1f}%)</b> | SL: {sl}"
        )

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
                    log_alert_once(dedup_key, time_str, sent_keys)

    # 3. تقرير إغلاق الجلسة اليومي (02:32 - 02:50 ظهراً)
    if (14 * 60 + 32) <= mins_now <= (14 * 60 + 50) and eod_lines:
        eod_key = f"{today_str}_EOD_REPORT"
        if eod_key not in sent_keys:
            tot_net = (total_val - total_cost) - (total_val * FEE_RATE)
            tot_pct = ((tot_net / total_cost) * 100.0) if total_cost > 0 else 0.0
            header = [
                f"🌙 <b>التقرير الختامي لمحفظتك ({today_str})</b>",
                f"القيمة الحالية: <b>{total_val:,.0f} ج.م</b> | الصافي: <b>{tot_net:+,.0f} ج.م ({tot_pct:+.1f}%)</b>",
                ""
            ]
            if send_telegram("\n".join(header + eod_lines)):
                log_alert_once(eod_key, time_str, sent_keys)


if __name__ == "__main__":
    run()
