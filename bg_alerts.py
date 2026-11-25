import os
import re
import sys
import json
import time
import urllib.request
import urllib.parse
from datetime import datetime, date, timedelta, timezone

import egx_core as core

# ==========================================
# إعدادات البيئة والاتصال (Supabase + Telegram)
# ==========================================
SUPABASE_URL = os.environ.get("SUPABASE_URL", "").strip().rstrip("/")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "").strip()
# V11.5: البوت لازم يشتغل بالـ service_role key. مفيش رجوع للـ anon key لأنه بعد إصلاح RLS مش هيشوف أي بيانات.
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "").strip()
OWNER_USER_ID = os.environ.get("OWNER_USER_ID", "").strip()   # الـ UID بتاعك من Supabase Auth
TG_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
TG_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
# رسوم لكل جانب (شراء أو بيع): نسبة + مبلغ ثابت لكل أمر (من فاتورة ثاندر — شوف egx_core).
FEE_RATE = float(os.environ.get("THNDR_FEE_RATE") or core.FEE_PCT_PER_SIDE)
FEE_FIXED = float(os.environ.get("THNDR_FEE_FIXED") or core.FEE_FIXED_PER_ORDER)
ALERT_BUFFER_PCT = float(os.environ.get("ALERT_BUFFER_PCT", "2.5"))
MIN_TURNOVER = float(os.environ.get("MIN_TURNOVER_EGP", "500000"))  # حد أدنى لقيمة التداول لإشارات الحيتان
CLOSE_CHECK_FROM = os.environ.get("CLOSE_CHECK_FROM", "14:50")   # بعد الإغلاق + هامش تأخير البيانات
HOLIDAYS = core.load_holidays()
SYM_RE = re.compile(r"[A-Z]{2,6}")

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
    "GOLD": "ذهب (Gold)", "SILVER": "فضة (Silver)", "OIL": "نفط خام (WTI)",
    "BRENT": "نفط برنت (Brent)", "NATGAS": "غاز طبيعي", "COPPER": "نحاس", "PLATINUM": "بلاتين",
    "IDRE": "شركة IDRE (البورصة المصرية)",
    "ENGC": "شركة ENGC (البورصة المصرية)",
    "EEII": "شركة EEII (البورصة المصرية)",
    "ARAB": "العربية للاستثمار (ARAB)",
    "FERC": "شركة FERC (البورصة المصرية)",
}

get_cairo_now = core.cairo_now

def is_egx_market_open() -> tuple:
    now = get_cairo_now()
    if core.session_phase(now, HOLIDAYS) in ("continuous", "closing_auction"):
        return True, min(1.0, max(0.12, core.session_progress(now)))
    return False, 1.0

# ==========================================
# دوال Supabase API
# ==========================================
def sb_request(method: str, path: str, payload=None, extra_headers=None):
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        return False, None
    headers = {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
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
        payload=[{"alert_key": "BOT_LAST_OFFSET", "sent_at": str(new_offset), "user_id": OWNER_USER_ID}],
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
def send_tg(text_html: str, chat_id: str = None, reply_markup=None) -> bool:
    target_chat = chat_id or TG_CHAT_ID
    if not TG_TOKEN or not target_chat:
        return False
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {"chat_id": target_chat, "text": text_html, "parse_mode": "HTML", "disable_web_page_preview": True}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    data_bytes = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data_bytes, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            return bool(res.get("ok"))
    except Exception as e:
        print(f"[Telegram Send Error]: {e}")
        return False

def answer_callback_query(callback_id, text=""):
    if not TG_TOKEN:
        return
    url = "https://api.telegram.org/bot%s/answerCallbackQuery" % TG_TOKEN
    payload = json.dumps({"callback_query_id": callback_id, "text": text}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    try:
        urllib.request.urlopen(req, timeout=5)
    except Exception:
        pass


def main_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "💼 محفظتي", "callback_data": "portfolio"}, {"text": "🎯 رادار", "callback_data": "radar"}],
            [{"text": "🔍 سعر سهم", "callback_data": "price"}, {"text": "➕ شراء", "callback_data": "buy"}],
            [{"text": "💰 بيع", "callback_data": "sell"}, {"text": "🛡️ تأمين", "callback_data": "be"}],
            [{"text": "❓ مساعدة", "callback_data": "help"}],
        ]
    }


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
            _v = rec.get("VWAP")
            vwap = float(_v) if _v not in (None, 0, "0", "") else close_p
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

            sl = round(max(0.01, close_p - 2.0 * atr), 4)
            r_sh = max(0.01, close_p - sl)
            high_p = float(rec.get("high") or close_p)
            low_p = float(rec.get("low") or close_p)
            flow = core.flow_metrics(close_p, vwap, rsi15, float(rec.get("MACD.macd|15") or 0),
                                     float(rec.get("MACD.signal|15") or 0), high_p, low_p, rvol)
            market_map[sym] = {
                "symbol": sym,
                "name": EGX_NAMES.get(sym, str(rec.get("description") or sym)),
                "close": round(close_p, 4),
                "change": round(chg, 4),
                "atr": round(atr, 4),
                "ema20": round(ema20, 4),
                "vwap": round(vwap, 4),
                "vwap_diff": round(vwap_diff, 4),
                "rvol": round(rvol, 4),
                "rsi15": round(rsi15, 1),
                "score": min(100, score),
                "sl": sl,
                "tp1": round(close_p + 1.618 * r_sh, 4),
                "tp2": round(close_p + 2.618 * r_sh, 4),
                "turnover": float(rec.get("Value.Traded") or (close_p * vol)),
                "high": high_p,
                "low": low_p,
                "flow": flow,
            }
    except Exception as e:
        print(f"[TV Fetch Error]: {e}")
    return market_map

# ==========================================
# معالجة الأوامر الواردة من تليجرام (رايح جاي)
# ==========================================
def handle_command(text: str, chat_id: str, market_map: dict, user_id: str):
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
        ok, port = sb_request("GET", f"portfolio?select=*&user_id=eq.{user_id}&order=symbol.asc")
        if not ok or not port:
            send_tg("💼 محفظتك فارغة حالياً في السحابة.", chat_id)
            return
        tot_cost, tot_val, tot_fees = 0.0, 0.0, 0.0
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
            fees = core.round_trip_fees(cost, val, FEE_RATE, FEE_FIXED)
            pnl = (val - cost) - fees
            pnl_pct = (pnl / max(0.01, cost)) * 100.0
            tot_fees += fees
            tot_cost += cost
            tot_val += val
            icon = "🟢" if pnl >= 0 else "🔴"
            lines.append(
                f"{icon} <b>{sym}</b> ({EGX_NAMES.get(sym, sym)})\n"
                f"   الكمية: {sh} | شرائك: {bp} | الآن: <b>{cp}</b>\n"
                f"   الربح: <b>{pnl:+,.0f} ج.م ({pnl_pct:+.1f}%)</b> | SL: {sl} | TP1: {tp1}"
            )
        tot_pnl = (tot_val - tot_cost) - tot_fees
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
        if not SYM_RE.fullmatch(sym):
            send_tg("⚠️ رمز السهم غير صحيح.", chat_id)
            return
        try:
            new_sh = int(float(parts[2]))
            new_bp = float(parts[3])
        except ValueError:
            send_tg("⚠️ الصيغة الصحيحة: <code>شراء ABUK 100 54.5</code>", chat_id)
            return

        # إذا كان السهم موجوداً نحسب متوسط الشراء المرجح
        ok_ex, ex_data = sb_request("GET", f"portfolio?symbol=eq.{sym}&user_id=eq.{user_id}&limit=1")
        if ok_ex and ex_data:
            old_sh = int(ex_data[0]["shares"])
            old_bp = float(ex_data[0]["buy_price"])
            total_sh = old_sh + new_sh
            avg_bp = round(((old_sh * old_bp) + (new_sh * new_bp)) / total_sh, 4)
        else:
            total_sh, avg_bp = new_sh, new_bp

        m = market_map.get(sym, {})
        atr = m.get("atr", avg_bp * 0.025)
        sl = round(max(0.01, avg_bp - 2.0 * atr), 4)
        r_sh = max(0.01, avg_bp - sl)
        tp1 = round(avg_bp + 1.618 * r_sh, 4)
        tp2 = round(avg_bp + 2.618 * r_sh, 4)

        ok_up, _ = sb_request(
            "POST", "portfolio?on_conflict=symbol",
            payload=[{
                "symbol": sym, "user_id": user_id, "shares": total_sh, "buy_price": avg_bp,
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
        if not SYM_RE.fullmatch(sym):
            send_tg("⚠️ رمز السهم غير صحيح.", chat_id)
            return
        try:
            sell_p = float(parts[2])
        except ValueError:
            send_tg("⚠️ الصيغة الصحيحة: <code>بيع ABUK 59.0</code>", chat_id)
            return

        ok_ex, ex_data = sb_request("GET", f"portfolio?symbol=eq.{sym}&user_id=eq.{user_id}&limit=1")
        if not ok_ex or not ex_data:
            send_tg(f"⚠️ السهم <b>{sym}</b> غير موجود في محفظتك المفتوحة.", chat_id)
            return

        sh = int(ex_data[0]["shares"])
        bp = float(ex_data[0]["buy_price"])
        cost = sh * bp
        proceeds = sh * sell_p
        net_pnl = (proceeds - cost) - core.round_trip_fees(cost, proceeds, FEE_RATE, FEE_FIXED)
        pnl_pct = (net_pnl / max(0.01, cost)) * 100.0

        sb_request("POST", "closed_trades", payload=[{
            "symbol": sym, "user_id": user_id, "shares": sh, "buy_price": bp, "sell_price": sell_p,
            "net_pnl": round(net_pnl, 4), "pnl_pct": round(pnl_pct, 4),
            "closed_at": get_cairo_now().isoformat()
        }])
        sb_request("DELETE", f"portfolio?symbol=eq.{sym}&user_id=eq.{user_id}")
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
        if not SYM_RE.fullmatch(sym):
            send_tg("⚠️ رمز السهم غير صحيح.", chat_id)
            return
        ok_ex, ex_data = sb_request("GET", f"portfolio?symbol=eq.{sym}&user_id=eq.{user_id}&limit=1")
        if not ok_ex or not ex_data:
            send_tg(f"⚠️ السهم <b>{sym}</b> غير موجود في محفظتك.", chat_id)
            return
        bp = float(ex_data[0]["buy_price"])
        be_sl = core.breakeven_price(bp, FEE_RATE, int(ex_data[0].get("shares") or 0), FEE_FIXED)
        sb_request("PATCH", f"portfolio?symbol=eq.{sym}&user_id=eq.{user_id}", payload={"stop_loss": be_sl, "trailing_stage": 1})
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

    send_tg("🤔 لم أفهم الأمر. أرسل كلمة <b>مساعدة</b> لعرض قائمة الأوامر المتاحة.", chat_id, reply_markup=main_keyboard())

# ==========================================
# حلقة المراقبة الآلية والوقف المتحرك (V11.5)
# ==========================================
def load_user_chats() -> dict:
    """user_id -> chat_id. المالك بياخد TELEGRAM_CHAT_ID."""
    chats = {}
    ok, data = sb_request("GET", "user_settings?select=user_id,tg_chat_id")
    if ok and isinstance(data, list):
        for u in data:
            if u.get("user_id") and u.get("tg_chat_id"):
                chats[str(u["user_id"])] = str(u["tg_chat_id"]).strip()
    if OWNER_USER_ID and TG_CHAT_ID:
        chats[OWNER_USER_ID] = TG_CHAT_ID
    return chats


def alert_key(today: str, user_id: str, body: str) -> str:
    """نفس مفاتيح التطبيق للمالك، ومفتاح مميز لأي مستخدم تاني (alert_key عليه unique)."""
    k = f"{today}_{body}"
    return k if (not user_id or user_id == OWNER_USER_ID) else f"{k}_u{str(user_id)[:8]}"


def trading_days_between(d0: date, d1: date) -> int:
    """عدد أيام التداول بعد d0 لحد d1 (شامل d1)."""
    n, d = 0, d0
    while d < d1:
        d += timedelta(days=1)
        if core.is_trading_day(d, HOLIDAYS):
            n += 1
    return n


def evaluate_signal_journal(market_map: dict, today: date) -> str:
    """يقفل الإشارات المفتوحة (TP1 / SL / EXPIRED) ويرجّع سطر إحصائيات للملخص."""
    ok, sigs = sb_request("GET", f"signal_journal?select=*&status=eq.OPEN&signal_date=lt.{today.isoformat()}")
    if ok and isinstance(sigs, list):
        for sg in sigs:
            m = market_map.get(str(sg.get("symbol", "")).upper())
            if not m:
                continue
            days_open = trading_days_between(date.fromisoformat(str(sg["signal_date"])[:10]), today)
            status = core.evaluate_signal(sg, m["high"], m["low"], days_open)
            if not status:
                continue
            entry, sl = float(sg.get("entry_ref") or 0), float(sg.get("sl") or 0)
            risk = max(0.0001, entry - sl)
            r = {"TP1": 1.618, "SL": -1.0}.get(status, round((m["close"] - entry) / risk, 3))
            sb_request("PATCH", f"signal_journal?id=eq.{sg['id']}",
                       payload={"status": status, "closed_date": today.isoformat(), "outcome_r": r})
    ok, rows = sb_request("GET", "signal_journal?select=status,outcome_r")
    if not ok or not isinstance(rows, list) or not rows:
        return ""
    closed = [x for x in rows if x.get("status") != "OPEN"]
    if not closed:
        return f"📒 سجل الإشارات: {len(rows)} إشارة مفتوحة، لسه مفيش نتائج."
    wins = sum(1 for x in closed if x.get("status") == "TP1")
    avg_r = sum(float(x.get("outcome_r") or 0) for x in closed) / len(closed)
    return (f"📒 سجل الإشارات: {len(closed)} مقفولة | وصلت TP1: {wins / len(closed) * 100:.0f}% | "
            f"متوسط R (قبل الرسوم): {avg_r:+.2f} | مفتوحة: {len(rows) - len(closed)}")


def run_auto_monitor(market_map: dict, now: datetime = None):
    now = now or get_cairo_now()
    today_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M")
    phase = core.session_phase(now, HOLIDAYS)
    if phase == "closed_day":
        return  # عطلة أو جمعة/سبت: مفيش تنبيهات بأسعار قديمة

    ok_log, logs = sb_request("GET", f"tg_alerts_log?select=alert_key&alert_key=like.{today_str}*")
    if not ok_log or not isinstance(logs, list):
        print("[Monitor] تعذر قراءة سجل التنبيهات — إيقاف الدورة لتجنب تكرار الرسائل")
        return
    sent_keys = {x["alert_key"] for x in logs}

    def send_once(key: str, msg: str, chat: str, user_id: str) -> bool:
        if key in sent_keys or not chat:
            return False
        if send_tg(msg, chat_id=chat):
            sent_keys.add(key)
            sb_request("POST", "tg_alerts_log",
                       payload=[{"alert_key": key, "sent_at": time_str, "user_id": user_id or OWNER_USER_ID}])
            return True
        return False

    chats = load_user_chats()
    live = phase in ("continuous", "closing_auction")
    post = phase == "post_close" and core.in_window(now, CLOSE_CHECK_FROM, "23:59")
    pre_close = phase == "continuous" and core.in_window(now, "14:00", "14:15")

    # 0) نبض يومي + فحص البيانات
    if core.in_window(now, "09:00", "11:00"):
        send_once(f"{today_str}_HEARTBEAT",
                  f"✅ <b>البوت شغال</b> — {today_str} {time_str}\nبيانات السوق: {len(market_map)} سهم. لو الرسالة دي ماوصلتش في يوم تداول، المراقبة واقفة.",
                  TG_CHAT_ID, OWNER_USER_ID)
    if live and not market_map:
        send_once(f"{today_str}_DATA_DOWN", "⚠️ <b>مفيش بيانات من TradingView</b> — التنبيهات اللحظية واقفة لحد ما ترجع.",
                  TG_CHAT_ID, OWNER_USER_ID)
        return

    # 1) المحفظة
    ok_p, portfolio = sb_request("GET", "portfolio?select=*")
    portfolio = portfolio if (ok_p and isinstance(portfolio, list)) else []
    summaries = {}  # user_id -> lines
    for item in portfolio:
        sym = str(item.get("symbol", "")).upper().strip()
        uid = str(item.get("user_id") or OWNER_USER_ID)
        chat = chats.get(uid)
        sh = int(item.get("shares", 0) or 0)
        bp = float(item.get("buy_price", 0) or 0)
        sl = float(item.get("stop_loss", 0) or 0)
        tp1 = float(item.get("tp1", 0) or 0)
        tp2 = float(item.get("tp2", 0) or 0)
        tr_on = bool(item.get("trailing_enabled", True))
        tr_stage = int(item.get("trailing_stage", 0) or 0)
        m = market_map.get(sym)
        if not m or sh <= 0 or bp <= 0:
            continue
        cp, atr = m["close"], m["atr"]
        k = lambda body: alert_key(today_str, uid, f"{sym}_{body}")

        # الوقف والأهداف بيتحسبوا مرة واحدة ويتخزنوا (مايتحركوش مع ATR كل دورة)
        patch = {}
        if sl <= 0:
            sl = core.initial_levels(bp, atr)["stop_loss"]
            patch["stop_loss"] = sl
        r_u = max(0.01, bp - sl)
        if tp1 <= 0:
            tp1 = round(bp + 1.618 * r_u, 4)
            patch["tp1"] = tp1
        if tp2 <= 0:
            tp2 = round(bp + 2.618 * r_u, 4)
            patch["tp2"] = tp2

        # الوقف المتحرك (بأسعار الجلسة فقط)
        if live and tr_on:
            be_p = core.breakeven_price(bp, FEE_RATE, sh, FEE_FIXED)
            if cp >= tp1 and tr_stage < 1 and be_p < cp:
                sl, tr_stage = max(sl, be_p), 1
                patch.update(stop_loss=sl, trailing_stage=tr_stage)
                send_once(k("TRAIL1"), f"🛡️ <b>تأمين آلي ({sym}):</b> تحقق TP1 وتم رفع الوقف للتعادل (<b>{sl} ج.م</b>).", chat, uid)
            if cp >= tp2:
                anchor = max(m["vwap"], m["ema20"])
                cand = round(min(cp - 0.5 * atr, anchor * 0.992), 4)
                if cand > sl * 1.003 and cand < cp:
                    sl, tr_stage = cand, 2
                    patch.update(stop_loss=sl, trailing_stage=tr_stage)
                    send_once(k("TRAIL2"), f"🚀 <b>ملاحقة أرباح ({sym}):</b> تم رفع الوقف آلياً إلى <b>{sl} ج.م</b>.", chat, uid)
        if patch:
            sb_request("PATCH", f"portfolio?symbol=eq.{sym}&user_id=eq.{uid}", payload=patch)

        net_pnl = (cp - bp) * sh - core.round_trip_fees(bp * sh, cp * sh, FEE_RATE, FEE_FIXED)
        dist_sl = ((cp - sl) / cp) * 100.0
        dist_tp1 = ((tp1 - cp) / cp) * 100.0

        if live:
            smart = core.evaluate_smart_stop_loss(sym, cp, sl, bp, m["flow"], ALERT_BUFFER_PCT)
            if smart["action"] == "EXIT_NOW":
                send_once(k("HIT_SL"), f"🚨 <b>خروج فوري — {sym}</b>\n{smart['reason']}\nالسعر: <b>{cp}</b> | الوقف: <b>{sl}</b>", chat, uid)
            elif smart["action"] == "WATCH_CLOSE":
                send_once(k("INTRADAY_BREAK"), f"👁️ <b>كسر لحظي — {sym}</b>\n{smart['reason']}\nالسعر: <b>{cp}</b> | الوقف: <b>{sl}</b>\nالتأكيد بيوصلك بعد الإغلاق.", chat, uid)
                if pre_close:
                    send_once(k("PRECLOSE"), f"⏰ <b>{sym} لسه تحت الوقف قبل 14:15</b>\nالسعر: <b>{cp}</b> | الوقف: <b>{sl}</b>\nقرر: بيع قبل نهاية التداول المستمر، أو استنى الإغلاق الرسمي (البيانات ممكن تكون متأخرة دقايق).", chat, uid)
            elif smart["action"] == "NEAR_SL":
                send_once(k("NEAR_SL"), f"⚠️ <b>قرب الوقف — {sym}</b>\nالسعر: <b>{cp}</b> (يبعد {dist_sl:.1f}% عن {sl})", chat, uid)
            elif cp >= tp2:
                send_once(k("HIT_TP2"), f"🏆 <b>تحقق TP2 — {sym}</b>\nالسعر: <b>{cp}</b> | الربح: <b>{net_pnl:+,.0f} ج.م</b>", chat, uid)
            elif cp >= tp1:
                send_once(k("HIT_TP1"), f"🎯 <b>تحقق TP1 — {sym}</b>\nالسعر: <b>{cp}</b> | الربح: <b>{net_pnl:+,.0f} ج.م</b>", chat, uid)
            elif 0 < dist_tp1 <= ALERT_BUFFER_PCT:
                send_once(k("NEAR_TP1"), f"🔔 <b>اقترب الهدف TP1 — {sym}</b>\nالسعر: <b>{cp}</b> (يبعد {dist_tp1:.1f}% عن {tp1})", chat, uid)

        elif post:
            # تأكيد الإغلاق: الوقف الهجين بيتقفل هنا
            had_break = k("INTRADAY_BREAK") in sent_keys
            res = core.close_check(cp, sl, had_break)
            if res == "CLOSE_CONFIRMED":
                send_once(k("CLOSE_CONFIRMED"), f"🔴 <b>تأكيد كسر بالإغلاق — {sym}</b>\nالإغلاق: <b>{cp}</b> تحت الوقف <b>{sl}</b>.\nالخطة: الخروج في افتتاح الجلسة القادمة.", chat, uid)
            elif res == "BREAK_CANCELLED":
                send_once(k("BREAK_CANCELLED"), f"🟢 <b>الكسر اللحظي اتلغى — {sym}</b>\nقفل على <b>{cp}</b> فوق الوقف <b>{sl}</b>. الصفقة مستمرة.", chat, uid)
            icon = "🔴" if cp <= sl else ("🟢" if net_pnl >= 0 else "🟠")
            summaries.setdefault(uid, []).append(
                f"{icon} <b>{sym}</b> {cp} ({m['change']:+.1f}%) | الوقف {sl} (يبعد {dist_sl:.1f}%) | TP1 {tp1} | صافي {net_pnl:+,.0f}")

    # 2) إشارات الحيتان (بفلتر سيولة وتوقيت) + تسجيلها في سجل الإشارات
    if phase == "continuous":
        prog = core.session_progress(now)
        for sym, m in market_map.items():
            if not core.whale_signal_ok(m, phase, prog, MIN_TURNOVER):
                continue
            msg = (f"🐋 <b>إشارة حيتان — {sym} ({m['name']})</b>\n"
                   f"السكور: <b>{m['score']}/100</b> | السعر: <b>{m['close']}</b> | السيولة: {m['turnover'] / 1e6:.1f} مليون\n"
                   f"الوقف: <b>{m['sl']}</b> | TP1: <b>{m['tp1']}</b> | TP2: <b>{m['tp2']}</b>")
            if send_once(f"{today_str}_WHALE_{sym}", msg, TG_CHAT_ID, OWNER_USER_ID):
                sb_request("POST", "signal_journal", payload=[{
                    "user_id": OWNER_USER_ID, "signal_date": today_str, "signal_time": time_str,
                    "symbol": sym, "score": m["score"], "entry_ref": m["close"],
                    "sl": m["sl"], "tp1": m["tp1"], "tp2": m["tp2"],
                    "rvol": m["rvol"], "turnover": round(m["turnover"], 0), "status": "OPEN",
                }])

    # 3) ملخص بعد الإغلاق (مرة واحدة في اليوم لكل مستخدم)
    if post:
        journal_line = ""
        if f"{today_str}_JOURNAL_EVAL" not in sent_keys:
            journal_line = evaluate_signal_journal(market_map, now.date())
            sent_keys.add(f"{today_str}_JOURNAL_EVAL")
            sb_request("POST", "tg_alerts_log", payload=[{"alert_key": f"{today_str}_JOURNAL_EVAL", "sent_at": time_str, "user_id": OWNER_USER_ID}])
        if OWNER_USER_ID not in summaries:
            summaries[OWNER_USER_ID] = []
        for uid, lines in summaries.items():
            body = "\n".join(lines) if lines else "مفيش مراكز مفتوحة."
            extra = f"\n\n{journal_line}" if (uid == OWNER_USER_ID and journal_line) else ""
            send_once(alert_key(today_str, uid, "CLOSE_SUMMARY"),
                      f"📋 <b>ملخص إغلاق {today_str}</b>\n\n{body}{extra}", chats.get(uid), uid)


def main():
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        print("❌ SUPABASE_URL و SUPABASE_SERVICE_KEY مطلوبين (service_role key في GitHub Secrets).")
        sys.exit(1)
    if not OWNER_USER_ID:
        print("❌ OWNER_USER_ID مطلوب (الـ UID بتاعك من Supabase > Authentication > Users).")
        sys.exit(1)
    if not TG_CHAT_ID:
        print("⚠️ TELEGRAM_CHAT_ID فاضي: البوت مش هينفذ أوامرك ومش هيبعتلك تنبيهات.")

    daemon_mode = "--loop" in sys.argv
    last_monitor_ts = 0.0

    while True:
        market_map = fetch_egx_market()
        chat_to_user = {c: u for u, c in load_user_chats().items()}
        allowed = set(chat_to_user)

        # 1) الرد على الرسائل — من الشاتات المسموحة فقط
        offset = get_tg_offset()
        for upd in fetch_tg_updates(offset):
            uid = upd.get("update_id", 0)
            cq = upd.get("callback_query")
            if cq:
                sender_chat = str((cq.get("message") or {}).get("chat", {}).get("id", ""))
                if core.is_authorized_chat(sender_chat, allowed):
                    cmd_map = {"portfolio": "محفظتي", "radar": "رادار", "price": "سعر", "buy": "شراء", "sell": "بيع", "be": "تأمين", "help": "مساعدة"}
                    handle_command(cmd_map.get(cq.get("data", ""), cq.get("data", "")), sender_chat, market_map, chat_to_user[sender_chat])
                    answer_callback_query(cq.get("id"), "تم")
                else:
                    print(f"[Security] تجاهل ضغطة من شات غير مسموح: {sender_chat}")
                save_tg_offset(uid + 1)
                continue
            msg = upd.get("message") or {}
            text = msg.get("text", "")
            sender_chat = str(msg.get("chat", {}).get("id", ""))
            if text and core.is_authorized_chat(sender_chat, allowed):
                handle_command(text, sender_chat, market_map, chat_to_user[sender_chat])
            elif text:
                print(f"[Security] تجاهل رسالة من شات غير مسموح: {sender_chat}")
            save_tg_offset(uid + 1)

        # 2) المراقبة كل 3 دقائق
        now_ts = time.time()
        if (now_ts - last_monitor_ts) >= 180:
            run_auto_monitor(market_map)
            last_monitor_ts = now_ts

        if not daemon_mode:
            break
        time.sleep(3)


if __name__ == "__main__":
    main()
