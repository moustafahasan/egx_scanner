import os
import re
import sys
import json
import time
import urllib.request
import urllib.parse
from datetime import datetime, timedelta, timezone

# ==========================================
# إعدادات البيئة والاتصال (Supabase + Telegram)
# ==========================================
SUPABASE_URL = os.environ.get("SUPABASE_URL", "").strip().rstrip("/")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "").strip()
TG_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
TG_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
FEE_RATE = float(os.environ.get("THNDR_FEE_RATE", "0.0016"))
ALERT_BUFFER_PCT = float(os.environ.get("ALERT_BUFFER_PCT", "2.5"))

EGX_NAMES = {
    "COMI": "البنك التجاري الدولي (CIB)", "TMGH": "مجموعة طلعت مصطفى",
    "HRHO": "إي إف جي القابضة (هيرميس)", "ABUK": "أبو قير للأسمدة",
    "MFPC": "مصر لإنتاج الأسمدة (موبكو)", "SWDY": "السويدي إليكتريك",
    "EAST": "الشرقية - إيسترن كومباني", "EFIH": "إي فاينانس",
    "FWRY": "فوري للمدفوعات", "ESRS": "حديد عز", "ETEL": "المصرية للاتصالات",
    "EKHO": "القابضة المصرية الكويتية ($)", "EKHOA": "القابضة المصرية الكويتية (جنيه)",
    "ORAS": "أوراسكوم كونستراكشون", "OCDI": "سوديك", "PHDC": "بالم هيلز",
    "HELI": "مصر الجديدة للإسكان", "MASR": "مدينة مصر للإسكان",
    "MNHD": "مدينة مصر للإسكان", "EMFD": "إعمار مصر", "ORHD": "أوراسكوم للتنمية",
    "SKPC": "سيدي كرير للبتروكيماويات", "AMOC": "أموك للزيوت المعدنية",
    "JUFO": "جهينة للصناعات الغذائية", "EFID": "إيديتا للصناعات الغذائية",
    "DOMT": "دومتي", "OLFI": "عبور لاند", "ISPH": "ابن سينا فارما",
    "CLHO": "مستشفيات كليوباترا", "RMDA": "راميدا للأدوية", "PHAR": "إيبيكو للأدوية",
    "ADIB": "مصرف أبو ظبي الإسلامي", "CIEB": "كريدي أجريكول مصر",
    "QNBA": "بنك قطر الوطني الأهلي", "FAIT": "بنك فيصل الإسلامي",
    "HDBK": "بنك التعمير والإسكان", "BTFH": "بلتون القابضة", "CIHC": "سي آي كابيتال",
    "DSCW": "دايس للملابس", "KABO": "كابو للمنسوجات", "KABL": "الكابلات الكهربائية",
    "RACC": "راية لخدمات مراكز الاتصالات", "CCAP": "القلعة للاستثمارات",
    "EGAL": "مصر للألومنيوم", "TAQA": "طاقة عربية", "GBCO": "جي بي كورب",
    "MTIE": "إم إم جروب", "ISMQ": "الإسماعيلية الوطنية (فوديكو)",
    "TANM": "تنمية للاستثمار العقاري", "AREH": "المصرية للمنتجعات",
    "ICEN": "إيكون الهندسية", "ALCN": "الإسكندرية لتداول الحاويات",
    "BONY": "بنيان للتنمية والتجارة",
}

def get_cairo_now() -> datetime:
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo("Africa/Cairo"))
    except Exception:
        return datetime.now(timezone(timedelta(hours=2)))

def is_egx_market_open() -> tuple[bool, float]:
    now = get_cairo_now()
    if now.weekday() not in [6, 0, 1, 2, 3]:
        return False, 1.0
    start_dt = now.replace(hour=10, minute=0, second=0, microsecond=0)
    end_dt = now.replace(hour=14, minute=30, second=0, microsecond=0)
    if start_dt <= now <= end_dt:
        elapsed = max(5.0, (now - start_dt).total_seconds() / 60.0)
        return True, min(1.0, max(0.12, elapsed / 270.0))
    return False, 1.0

# ==========================================
# دوال Supabase API
# ==========================================
def sb_request(method: str, path: str, payload=None, extra_headers=None):
    if not SUPABASE_URL or not SUPABASE_KEY:
        return False, None
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }
    if extra_headers:
        headers.update(extra_headers)
    url = f"{SUPABASE_URL}/rest/v1/{path}"
    data_bytes = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data_bytes, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read().decode("utf-8")
            return True, (json.loads(raw) if raw else [])
    except Exception as e:
        print(f"[Supabase Error] {path}: {e}")
        return False, None

def get_tg_offset() -> int:
    ok, data = sb_request("GET", "tg_alerts_log?alert_key=eq.BOT_LAST_OFFSET&limit=1")
    if ok and isinstance(data, list) and data:
        try:
            return int(data[0].get("sent_at", "0"))
        except Exception:
            pass
    if os.path.exists(".tg_offset"):
        try:
            return int(open(".tg_offset").read().strip())
        except Exception:
            pass
    return 0

def save_tg_offset(new_offset: int):
    sb_request(
        "POST",
        "tg_alerts_log?on_conflict=alert_key",
        payload=[{"alert_key": "BOT_LAST_OFFSET", "sent_at": str(new_offset)}],
        extra_headers={"Prefer": "resolution=merge-duplicates,return=representation"},
    )
    try:
        with open(".tg_offset", "w") as f:
            f.write(str(new_offset))
    except Exception:
        pass

# ==========================================
# دوال تليجرام (إرسال + استقبال الأوامر)
# ==========================================
def send_tg(text_html: str, chat_id: str = None) -> bool:
    target_chat = chat_id or TG_CHAT_ID
    if not TG_TOKEN or not target_chat:
        return False
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = json.dumps({
        "chat_id": target_chat,
        "text": text_html,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            return bool(res.get("ok"))
    except Exception as e:
        print(f"[Telegram Send Error]: {e}")
        return False

def fetch_tg_updates(offset: int) -> list:
    if not TG_TOKEN:
        return []
    url = f"https://api.telegram.org/bot{TG_TOKEN}/getUpdates?offset={offset}&timeout=2"
    try:
        with urllib.request.urlopen(url, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("result", []) if data.get("ok") else []
    except Exception as e:
        print(f"[Telegram Poll Error]: {e}")
        return []

# ==========================================
# سحب بيانات البورصة المصرية اللحظية من TradingView
# ==========================================
def fetch_egx_market() -> dict:
    url = "https://scanner.tradingview.com/egypt/scan"
    cols = [
        "name", "description", "close", "change", "volume", "Value.Traded",
        "average_volume_10d_calc", "ATR", "EMA20", "EMA50", "EMA200",
        "VWAP", "RSI|15", "MACD.macd|15", "MACD.signal|15", "high", "low"
    ]
    body = json.dumps({
        "filter": [{"left": "type", "operation": "in_range", "right": ["stock", "dr", "fund"]}],
        "options": {"lang": "en"},
        "markets": ["egypt"],
        "symbols": {"query": {"types": []}, "tickers": []},
        "columns": cols,
        "sort": {"sortBy": "Value.Traded", "sortOrder": "desc"},
        "range": [0, 350],
    }).encode("utf-8")

    _, prog = is_egx_market_open()
    market_map = {}
    try:
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}, method="POST")
        with urllib.request.urlopen(req, timeout=12) as resp:
            raw = json.loads(resp.read().decode("utf-8"))

        for row in raw.get("data", []):
            d = row.get("d", [])
            if len(d) < len(cols):
                continue
            rec = dict(zip(cols, d))
            sym = str(rec.get("name", "")).upper().strip()
            close_p = float(rec.get("close") or 0.0)
            if not sym or close_p <= 0:
                continue

            atr = float(rec.get("ATR") or (close_p * 0.025))
            ema20, ema50, ema200 = float(rec.get("EMA20") or close_p), float(rec.get("EMA50") or close_p), float(rec.get("EMA200") or close_p)
            vwap = float(rec.get("VWAP") or close_p)
            vol = float(rec.get("volume") or 0.0)
            avg_v = float(rec.get("average_volume_10d_calc") or 0.0)
            rvol = (vol / (avg_v * prog)) if avg_v > 0 else 1.0
            chg = float(rec.get("change") or 0.0)
            rsi15 = float(rec.get("RSI|15") or 50.0)
            vwap_diff = ((close_p - vwap) / vwap * 100.0) if vwap > 0 else 0.0

            score = 0
            if close_p > ema20 > ema50:
                score += 18
            elif close_p > ema50:
                score += 10
            if close_p > ema200:
                score += 10
            if rvol >= 1.8 and chg > 0.5:
                score += 35
            elif rvol >= 1.2 and chg > 0:
                score += 22
            if vwap_diff >= 0.4:
                score += 18
            elif vwap_diff > 0:
                score += 9
            if rsi15 >= 56:
                score += 12
            if float(rec.get("MACD.macd|15") or 0) > float(rec.get("MACD.signal|15") or 0):
                score += 7

            sl = round(max(0.01, close_p - 2.0 * atr), 2)
            r_sh = max(0.01, close_p - sl)
            market_map[sym] = {
                "symbol": sym,
                "name": EGX_NAMES.get(sym, str(rec.get("description") or sym)),
                "close": round(close_p, 2),
                "change": round(chg, 2),
                "atr": round(atr, 3),
                "ema20": round(ema20, 2),
                "vwap": round(vwap, 2),
                "vwap_diff": round(vwap_diff, 2),
                "rvol": round(rvol, 2),
                "rsi15": round(rsi15, 1),
                "score": min(100, score),
                "sl": sl,
                "tp1": round(close_p + 1.618 * r_sh, 2),
                "tp2": round(close_p + 2.618 * r_sh, 2),
            }
    except Exception as e:
        print(f"[TV Fetch Error]: {e}")
    return market_map

# ==========================================
# معالجة الأوامر الواردة من تليجرام (رايح جاي)
# ==========================================
def handle_command(text: str, chat_id: str, market_map: dict):
    raw_txt = text.strip()
    parts = raw_txt.split()
    if not parts:
        return
    cmd = parts[0].lower()

    # 1) المساعدة والقائمة الرئيسية
    if cmd in ["/start", "/help", "مساعدة", "مساعده", "اوامر", "أوامر", "القائمة"]:
        msg = (
            "🦅 <b>EGX Whale Hunter Bot — الأوامر التفاعلية (24/7)</b>\n\n"
            "💼 <b>محفظتي</b> (أو <code>/portfolio</code>)\n"
            "   ⬅️ عرض أسهمك وأرباحك ومستويات الوقف والأهداف\n\n"
            "🎯 <b>رادار</b> (أو <code>/radar</code>)\n"
            "   ⬅️ أقوى 5 فرص حيتان في البورصة المصرية الآن\n\n"
            "🔍 <b>سعر ABUK</b> (أو اكتب رمز السهم مباشرة مثل <code>COMI</code>)\n"
            "   ⬅️ السعر اللحظي، VWAP، السكور، والوقف المقترح\n\n"
            "➕ <b>شراء ABUK 100 54.5</b> (أو <code>/buy ABUK 100 54.5</code>)\n"
            "   ⬅️ إضافة السهم لمحفظتك أو تعديل متوسط الشراء\n\n"
            "💰 <b>بيع ABUK 59.0</b> (أو <code>/sell ABUK 59.0</code>)\n"
            "   ⬅️ إغلاق الصفقة وتسجيلها في دفتر الصفقات المغلقة\n\n"
            "🛡️ <b>تأمين ABUK</b> (أو <code>/be ABUK</code>)\n"
            "   ⬅️ رفع وقف الخسارة لنقطة التعادل فوراً"
        )
        send_tg(msg, chat_id)
        return

    # 2) عرض المحفظة
    if cmd in ["/portfolio", "محفظتي", "المحفظة", "المحفظه", "اسهمي", "أسهمي"]:
        ok, port = sb_request("GET", "portfolio?select=*&order=symbol.asc")
        if not ok or not port:
            send_tg("💼 محفظتك فارغة حالياً في السحابة.", chat_id)
            return
        tot_cost, tot_val = 0.0, 0.0
        lines = ["💼 <b>تقرير محفظتك اللحظي:</b>\n"]
        for item in port:
            sym = item["symbol"].upper()
            sh = int(item.get("shares", 0))
            bp = float(item.get("buy_price", 0))
            sl = float(item.get("stop_loss", 0))
            tp1 = float(item.get("tp1", 0))
            m = market_map.get(sym, {})
            cp = m.get("close", bp)
            cost = sh * bp
            val = sh * cp
            pnl = (val - cost) - (val * FEE_RATE)
            pnl_pct = (pnl / max(0.01, cost)) * 100.0
            tot_cost += cost
            tot_val += val
            icon = "🟢" if pnl >= 0 else "🔴"
            lines.append(
                f"{icon} <b>{sym}</b> ({EGX_NAMES.get(sym, sym)})\n"
                f"   الكمية: {sh} | شرائك: {bp} | الآن: <b>{cp}</b>\n"
                f"   الربح: <b>{pnl:+,.0f} ج.م ({pnl_pct:+.1f}%)</b> | SL: {sl} | TP1: {tp1}"
            )
        tot_pnl = (tot_val - tot_cost) - (tot_val * FEE_RATE)
        tot_pct = (tot_pnl / max(0.01, tot_cost)) * 100.0
        lines.append(f"\n💰 <b>الإجمالي:</b> {tot_val:,.0f} ج.م | الصافي: <b>{tot_pnl:+,.0f} ج.م ({tot_pct:+.1f}%)</b>")
        send_tg("\n".join(lines), chat_id)
        return

    # 3) رادار أقوى الفرص
    if cmd in ["/radar", "رادار", "الرادار", "فرص", "الفرص"]:
        ranked = sorted(market_map.values(), key=lambda x: (x["score"], x["rvol"]), reverse=True)[:5]
        if not ranked:
            send_tg("⚠️ تعذر سحب بيانات الرادار حالياً.", chat_id)
            return
        lines = ["🎯 <b>أقوى 5 فرص في البورصة المصرية الآن:</b>\n"]
        for i, r in enumerate(ranked, 1):
            lines.append(
                f"{i}. <b>{r['symbol']}</b> ({r['name']})\n"
                f"   السكور: <b>{r['score']}/100</b> | السعر: <b>{r['close']}</b> ({r['change']:+.1f}%)\n"
                f"   السيولة: {r['rvol']}x | VWAP: {r['vwap_diff']:+.1f}% | SL: {r['sl']} | TP1: {r['tp1']}"
            )
        send_tg("\n".join(lines), chat_id)
        return

    # 4) إضافة / شراء سهم: شراء ABUK 100 54.5
    if cmd in ["/buy", "شراء", "اضافة", "إضافة"] and len(parts) >= 4:
        sym = parts[1].upper().replace(".CA", "")
        try:
            new_sh = int(float(parts[2]))
            new_bp = float(parts[3])
        except ValueError:
            send_tg("⚠️ الصيغة الصحيحة: <code>شراء ABUK 100 54.5</code>", chat_id)
            return

        # إذا كان السهم موجوداً نحسب متوسط الشراء المرجح
        ok_ex, ex_data = sb_request("GET", f"portfolio?symbol=eq.{sym}&limit=1")
        if ok_ex and ex_data:
            old_sh = int(ex_data[0]["shares"])
            old_bp = float(ex_data[0]["buy_price"])
            total_sh = old_sh + new_sh
            avg_bp = round(((old_sh * old_bp) + (new_sh * new_bp)) / total_sh, 2)
        else:
            total_sh, avg_bp = new_sh, new_bp

        m = market_map.get(sym, {})
        atr = m.get("atr", avg_bp * 0.025)
        sl = round(max(0.01, avg_bp - 2.0 * atr), 2)
        r_sh = max(0.01, avg_bp - sl)
        tp1 = round(avg_bp + 1.618 * r_sh, 2)
        tp2 = round(avg_bp + 2.618 * r_sh, 2)

        ok_up, _ = sb_request(
            "POST", "portfolio?on_conflict=symbol",
            payload=[{
                "symbol": sym, "shares": total_sh, "buy_price": avg_bp,
                "stop_loss": sl, "tp1": tp1, "tp2": tp2,
                "trailing_enabled": True, "trailing_stage": 0
            }],
            extra_headers={"Prefer": "resolution=merge-duplicates,return=representation"},
        )
        if ok_up:
            send_tg(
                f"✅ <b>تم حفظ {sym} ({EGX_NAMES.get(sym, sym)}) في محفظتك!</b>\n"
                f"الكمية الكلية: <b>{total_sh}</b> | المتوسط: <b>{avg_bp} ج.م</b>\n"
                f"🛑 الوقف: <b>{sl}</b> | 🎯 TP1: <b>{tp1}</b> | TP2: <b>{tp2}</b>",
                chat_id,
            )
        else:
            send_tg("❌ تعذر الحفظ في Supabase؛ تأكد من المفاتيح.", chat_id)
        return

    # 5) بيع / إغلاق صفقة: بيع ABUK 59.0
    if cmd in ["/sell", "بيع", "اغلاق", "إغلاق"] and len(parts) >= 3:
        sym = parts[1].upper().replace(".CA", "")
        try:
            sell_p = float(parts[2])
        except ValueError:
            send_tg("⚠️ الصيغة الصحيحة: <code>بيع ABUK 59.0</code>", chat_id)
            return

        ok_ex, ex_data = sb_request("GET", f"portfolio?symbol=eq.{sym}&limit=1")
        if not ok_ex or not ex_data:
            send_tg(f"⚠️ السهم <b>{sym}</b> غير موجود في محفظتك المفتوحة.", chat_id)
            return

        sh = int(ex_data[0]["shares"])
        bp = float(ex_data[0]["buy_price"])
        cost = sh * bp
        proceeds = sh * sell_p
        net_pnl = (proceeds - cost) - ((cost + proceeds) * FEE_RATE)
        pnl_pct = (net_pnl / max(0.01, cost)) * 100.0

        sb_request("POST", "closed_trades", payload=[{
            "symbol": sym, "shares": sh, "buy_price": bp, "sell_price": sell_p,
            "net_pnl": round(net_pnl, 2), "pnl_pct": round(pnl_pct, 2),
            "closed_at": get_cairo_now().isoformat()
        }])
        sb_request("DELETE", f"portfolio?symbol=eq.{sym}")
        send_tg(
            f"💰 <b>تم إغلاق صفقة {sym} ({EGX_NAMES.get(sym, sym)})</b>\n"
            f"الكمية: {sh} | الشراء: {bp} ⬅️ البيع: <b>{sell_p}</b>\n"
            f"صافي النتيجة: <b>{net_pnl:+,.0f} ج.م ({pnl_pct:+.1f}%)</b>",
            chat_id,
        )
        return

    # 6) تأمين التعادل: تأمين ABUK
    if cmd in ["/be", "تأمين", "تامين", "تعادل"] and len(parts) >= 2:
        sym = parts[1].upper().replace(".CA", "")
        ok_ex, ex_data = sb_request("GET", f"portfolio?symbol=eq.{sym}&limit=1")
        if not ok_ex or not ex_data:
            send_tg(f"⚠️ السهم <b>{sym}</b> غير موجود في محفظتك.", chat_id)
            return
        bp = float(ex_data[0]["buy_price"])
        be_sl = round(bp * (1.0 + FEE_RATE * 2.0), 2)
        sb_request("PATCH", f"portfolio?symbol=eq.{sym}", payload={"stop_loss": be_sl, "trailing_stage": 1})
        send_tg(f"🛡️ <b>تم تأمين {sym} للتعادل!</b>\nوقف الخسارة الجديد: <b>{be_sl} ج.م</b>", chat_id)
        return

    # 7) الاستعلام عن سهم: سعر ABUK أو كتابة ABUK مباشرة
    target_sym = None
    if cmd in ["/price", "سعر", "تحليل", "فحص"] and len(parts) >= 2:
        target_sym = parts[1].upper().replace(".CA", "")
    elif re.fullmatch(r"[A-Za-z]{3,5}", cmd):
        target_sym = cmd.upper()

    if target_sym:
        m = market_map.get(target_sym)
        if not m:
            send_tg(f"⚠️ الرمز <b>{target_sym}</b> غير متاح حالياً في بيانات البورصة.", chat_id)
            return
        vwap_st = "أعلى VWAP 🟢" if m["vwap_diff"] >= 0 else "أسفل VWAP 🔴"
        send_tg(
            f"📊 <b>{target_sym} — {m['name']}</b>\n"
            f"💰 السعر اللحظي: <b>{m['close']} ج.م</b> ({m['change']:+.2f}%)\n"
            f"⚡ التدفق: <b>{vwap_st}</b> ({m['vwap']} | {m['vwap_diff']:+.1f}%)\n"
            f"💧 وتيرة السيولة: <b>{m['rvol']}x</b> | RSI15: <b>{m['rsi15']}</b>\n"
            f"🎯 السكور الفني: <b>{m['score']}/100</b>\n"
            f"🛑 الوقف (2×ATR): <b>{m['sl']}</b> | 🎯 TP1: <b>{m['tp1']}</b> | TP2: <b>{m['tp2']}</b>",
            chat_id,
        )
        return

    send_tg("🤔 لم أفهم الأمر. أرسل كلمة <b>مساعدة</b> لعرض قائمة الأوامر المتاحة.", chat_id)

# ==========================================
# حلقة المراقبة الآلية والوقف المتحرك
# ==========================================
def run_auto_monitor(market_map: dict):
    today_str = get_cairo_now().strftime("%Y-%m-%d")
    time_str = get_cairo_now().strftime("%H:%M")

    ok_log, logs = sb_request("GET", f"tg_alerts_log?alert_key=like.{today_str}*")
    sent_keys = {x["alert_key"] for x in logs} if (ok_log and isinstance(logs, list)) else set()

    def send_once(key: str, msg: str):
        if key not in sent_keys:
            if send_tg(msg):
                sent_keys.add(key)
                sb_request("POST", "tg_alerts_log", payload=[{"alert_key": key, "sent_at": time_str}])

    ok_p, portfolio = sb_request("GET", "portfolio?select=*")
    if ok_p and isinstance(portfolio, list):
        for item in portfolio:
            sym = item["symbol"].upper().strip()
            sh = int(item.get("shares", 0))
            bp = float(item.get("buy_price", 0))
            sl = float(item.get("stop_loss", 0))
            tp1 = float(item.get("tp1", 0))
            tp2 = float(item.get("tp2", 0))
            tr_on = bool(item.get("trailing_enabled", True))
            tr_stage = int(item.get("trailing_stage", 0))

            m = market_map.get(sym)
            if not m or sh <= 0 or bp <= 0:
                continue

            cp = m["close"]
            atr = m["atr"]
            if sl <= 0:
                sl = round(max(0.01, bp - 2.0 * atr), 2)
            r_u = max(0.01, bp - sl)
            if tp1 <= 0:
                tp1 = round(bp + 1.618 * r_u, 2)
            if tp2 <= 0:
                tp2 = round(bp + 2.618 * r_u, 2)

            # الوقف المتحرك الآلي
            updated = False
            if tr_on:
                be_p = round(bp * (1.0 + FEE_RATE * 2.0), 2)
                if cp >= tp1 and tr_stage < 1 and be_p < cp:
                    sl = max(sl, be_p)
                    tr_stage = 1
                    updated = True
                    send_once(f"{today_str}_{sym}_TRAIL1", f"🛡️ <b>تأمين آلي ({sym}):</b> تحقق TP1 وتم رفع الوقف للتعادل (<b>{sl} ج.م</b>).")
                if cp >= tp2:
                    anchor = max(m["vwap"], m["ema20"])
                    cand = round(min(cp - 0.5 * atr, anchor * 0.992), 2)
                    if cand > sl * 1.003 and cand < cp:
                        sl = cand
                        tr_stage = 2
                        updated = True
                        send_once(f"{today_str}_{sym}_TRAIL2", f"🚀 <b>ملاحقة أرباح ({sym}):</b> تم رفع الوقف آلياً إلى <b>{sl} ج.م</b>.")

            if updated:
                sb_request("PATCH", f"portfolio?symbol=eq.{sym}", payload={"stop_loss": sl, "tp1": tp1, "tp2": tp2, "trailing_stage": tr_stage})

            net_pnl = ((cp - bp) * sh) - (cp * sh * FEE_RATE)
            dist_sl = ((cp - sl) / cp) * 100.0
            dist_tp1 = ((tp1 - cp) / cp) * 100.0

            if cp <= sl:
                send_once(f"{today_str}_{sym}_HIT_SL", f"🚨 <b>كسر وقف الخسارة — {sym}</b>\nالسعر: <b>{cp}</b> | الوقف: <b>{sl}</b>")
            elif 0 < dist_sl <= ALERT_BUFFER_PCT:
                send_once(f"{today_str}_{sym}_NEAR_SL", f"⚠️ <b>قرب الوقف — {sym}</b>\nالسعر: <b>{cp}</b> (يبعد {dist_sl:.1f}% عن {sl})")
            elif cp >= tp2:
                send_once(f"{today_str}_{sym}_HIT_TP2", f"🏆 <b>تحقق TP2 — {sym}</b>\nالسعر: <b>{cp}</b> | الربح: <b>{net_pnl:+,.0f} ج.م</b>")
            elif cp >= tp1:
                send_once(f"{today_str}_{sym}_HIT_TP1", f"🎯 <b>تحقق TP1 — {sym}</b>\nالسعر: <b>{cp}</b> | الربح: <b>{net_pnl:+,.0f} ج.م</b>")
            elif 0 < dist_tp1 <= ALERT_BUFFER_PCT:
                send_once(f"{today_str}_{sym}_NEAR_TP1", f"🔔 <b>اقترب الهدف TP1 — {sym}</b>\nالسعر: <b>{cp}</b> (يبعد {dist_tp1:.1f}% عن {tp1})")

    # تنبيهات فرص الحيتان (سكور 80+) أثناء الجلسة
    is_open, _ = is_egx_market_open()
    if is_open:
        for sym, m in market_map.items():
            if m["score"] >= 80:
                send_once(
                    f"{today_str}_WHALE_{sym}",
                    f"🐋 <b>إشارة حيتان — {sym} ({m['name']})</b>\n"
                    f"السكور: <b>{m['score']}/100</b> | السعر: <b>{m['close']}</b> | الوقف: <b>{m['sl']}</b> | TP1: <b>{m['tp1']}</b>"
                )

def main():
    daemon_mode = "--loop" in sys.argv
    last_monitor_ts = 0.0

    while True:
        market_map = fetch_egx_market()

        # 1) فحص والرد على أي رسائل واردة على تليجرام
        offset = get_tg_offset()
        updates = fetch_tg_updates(offset)
        for upd in updates:
            uid = upd.get("update_id", 0)
            msg = upd.get("message") or {}
            text = msg.get("text", "")
            sender_chat = str(msg.get("chat", {}).get("id", ""))
            if text and sender_chat and (not TG_CHAT_ID or sender_chat == TG_CHAT_ID):
                handle_command(text, sender_chat, market_map)
            save_tg_offset(uid + 1)

        # 2) تشغيل مراقب المحفظة والتنبيهات كل 3 دقائق
        now_ts = time.time()
        if (now_ts - last_monitor_ts) >= 180:
            run_auto_monitor(market_map)
            last_monitor_ts = now_ts

        if not daemon_mode:
            break
        time.sleep(3)

if __name__ == "__main__":
    main()
