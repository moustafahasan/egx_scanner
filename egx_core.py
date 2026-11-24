"""
EGX Whale Hunter — المنطق المشترك (V11.5)
بيستخدمه egx_scanner.py (Streamlit) و bg_alerts.py (GitHub Actions) عشان الاتنين يفضلوا متطابقين.
مكتبات بايثون القياسية فقط (stdlib) — مفيش أي تثبيت إضافي.
"""
import os
from datetime import datetime, date, time as dtime, timedelta, timezone

# ---------------------------------------------------------------
# الرسوم (لكل جانب: شراء أو بيع)
# Thndr Trader: عمولة ثاندر بتترد لأول 50 أمر في الشهر، وبيفضل الرسوم الحكومية بس:
#   EGX 0.01% + MCDR 0.01% + الرقابة 0.005% + تأمين المخاطر 0.005% + دمغة 0.05% = 0.08%
# بعد الـ 50 أمر: + عمولة ثاندر 0.1% (والـ 2 جنيه الثابتة مش محسوبة هنا) = 0.18%
# ---------------------------------------------------------------
FEE_PER_SIDE_TRADER = 0.0008
FEE_PER_SIDE_STANDARD = 0.0018

# ---------------------------------------------------------------
# مواعيد الجلسة (القاهرة)
# ---------------------------------------------------------------
CONT_START = dtime(10, 0)     # بداية التداول المستمر
CONT_END = dtime(14, 15)      # نهاية التداول المستمر
AUCTION_END = dtime(14, 30)   # نهاية مزاد الإغلاق
SESSION_MINUTES = 270.0       # 10:00 -> 14:30
TRADING_WEEKDAYS = {6, 0, 1, 2, 3}  # الأحد..الخميس (Python: الاثنين=0)

HOLIDAYS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "egx_holidays.txt")


def cairo_now() -> datetime:
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo("Africa/Cairo"))
    except Exception:
        return datetime.now(timezone(timedelta(hours=2)))


def load_holidays(path: str = None) -> set:
    """يقرأ egx_holidays.txt (تاريخ YYYY-MM-DD في كل سطر، و # للتعليقات)."""
    out = set()
    try:
        with open(path or HOLIDAYS_FILE, encoding="utf-8") as f:
            for ln in f:
                ln = ln.split("#", 1)[0].strip()
                if ln:
                    try:
                        out.add(date.fromisoformat(ln))
                    except ValueError:
                        pass
    except OSError:
        pass
    return out


def is_trading_day(d: date, holidays: set = None) -> bool:
    if holidays is None:
        holidays = load_holidays()
    return d.weekday() in TRADING_WEEKDAYS and d not in holidays


def session_phase(now: datetime = None, holidays: set = None) -> str:
    """closed_day | pre_open | continuous | closing_auction | post_close"""
    now = now or cairo_now()
    if not is_trading_day(now.date(), holidays):
        return "closed_day"
    t = now.time()
    if t < CONT_START:
        return "pre_open"
    if t < CONT_END:
        return "continuous"
    if t < AUCTION_END:
        return "closing_auction"
    return "post_close"


def session_progress(now: datetime = None) -> float:
    """نسبة مرور الجلسة 0..1 (بدون حد أدنى صناعي)."""
    now = now or cairo_now()
    start = now.replace(hour=10, minute=0, second=0, microsecond=0)
    return min(1.0, max(0.0, (now - start).total_seconds() / 60.0 / SESSION_MINUTES))


def in_window(now: datetime, start_hhmm: str, end_hhmm: str) -> bool:
    t = now.strftime("%H:%M")
    return start_hhmm <= t < end_hhmm


# ---------------------------------------------------------------
# الحسابات
# ---------------------------------------------------------------
def round_trip_fees(cost: float, proceeds: float, fee_per_side: float) -> float:
    return (cost + proceeds) * fee_per_side


def breakeven_price(buy_price: float, fee_per_side: float) -> float:
    return round(buy_price * (1.0 + 2.0 * fee_per_side), 4)


def initial_levels(buy_price: float, atr: float) -> dict:
    """الوقف 2×ATR والأهداف 1.618R و 2.618R — بتتحسب مرة واحدة وقت الدخول وتتخزن."""
    sl = round(max(0.01, buy_price - 2.0 * atr), 4)
    r = max(0.01, buy_price - sl)
    return {"stop_loss": sl, "tp1": round(buy_price + 1.618 * r, 4), "tp2": round(buy_price + 2.618 * r, 4)}


def flow_metrics(close, vwap, rsi15, macd15, macds15, high, low, rel_vol) -> dict:
    """نفس معادلة flow_score في التطبيق (analyze_intraday_flow) بدون النصوص."""
    vwap = vwap if vwap and vwap > 0 else close
    vwap_diff = ((close - vwap) / vwap * 100.0) if vwap > 0 else 0.0
    clv = ((close - low) / (high - low) * 100.0) if high > low else 50.0
    f = 0
    if vwap_diff >= 0.4:
        f += 30
    elif vwap_diff > 0:
        f += 15
    elif vwap_diff <= -0.4:
        f -= 30
    if rsi15 >= 58:
        f += 20
    elif rsi15 <= 42:
        f -= 20
    if macd15 > macds15:
        f += 15
    elif macd15 < macds15:
        f -= 15
    if clv >= 70:
        f += 15
    elif clv <= 30:
        f -= 15
    if rel_vol >= 1.3 and f > 0:
        f += 20
    return {
        "flow_score": max(-100, min(100, f)),
        "vwap_diff_pct": round(vwap_diff, 4),
        "clv_pct": round(clv, 1),
        "rsi15": round(rsi15, 1),
        "rel_vol": round(rel_vol, 4),
    }


def evaluate_smart_stop_loss(sym: str, curr_p: float, sl: float, buy_p: float, flow_res: dict, alert_buffer_pct: float = 2.5) -> dict:
    """
    الوقف الهجين:
    - كسر عميق >= 1.5% تحت الوقف -> خروج فوري.
    - سيولة بيعية: RVOL >= 1.6 و (VWAP <= -0.8% أو flow_score <= -35).
    - انهيار زخم: RSI15 <= 35 و CLV <= 15% و RVOL >= 1.2.
    غير كده: كسر لحظي -> WATCH_CLOSE (التأكيد بيحصل في close_check بعد الإغلاق).
    """
    result = {"action": "HOLD", "reason": "داخل النطاق الآمن", "is_hard_break": False, "is_intraday_break": False}
    if sl <= 0 or curr_p <= 0:
        return result
    dist_sl_pct = ((curr_p - sl) / curr_p) * 100.0
    deep_break = dist_sl_pct <= -1.5
    rvol = float(flow_res.get("rel_vol", 1.0) or 1.0)
    vwap_diff = float(flow_res.get("vwap_diff_pct", 0.0) or 0.0)
    flow_score = int(flow_res.get("flow_score", 0) or 0)
    rsi15 = float(flow_res.get("rsi15", 50.0) or 50.0)
    clv = float(flow_res.get("clv_pct", 50.0) or 50.0)
    inst_sell = (rvol >= 1.6) and (vwap_diff <= -0.8 or flow_score <= -35)
    momentum_collapse = (rsi15 <= 35) and (clv <= 15) and (rvol >= 1.2)

    if curr_p <= sl:
        if deep_break or inst_sell or momentum_collapse:
            result.update(action="EXIT_NOW", is_hard_break=True)
            if deep_break:
                result["reason"] = f"كسر عميق أسفل الوقف ({dist_sl_pct:.2f}% <= -1.5%)"
            elif inst_sell:
                result["reason"] = f"سيولة بيعية مؤسسية (RVOL {rvol:.2f}x, VWAP {vwap_diff:+.2f}%)"
            else:
                result["reason"] = f"انهيار زخم (RSI15 {rsi15:.1f}, CLV {clv:.0f}%)"
        else:
            result.update(action="WATCH_CLOSE", is_intraday_break=True,
                          reason=f"كسر لحظي تحت المراقبة (يبعد {dist_sl_pct:.2f}% عن الوقف) - انتظار تأكيد الإغلاق")
    elif 0 < dist_sl_pct <= alert_buffer_pct:
        result.update(action="NEAR_SL", reason=f"قرب الوقف ({dist_sl_pct:.1f}%)")
    return result


def close_check(close: float, sl: float, had_intraday_break: bool):
    """بعد الإغلاق: CLOSE_CONFIRMED (إغلاق تحت الوقف) | BREAK_CANCELLED (كسر لحظي واتقفل فوق الوقف) | None"""
    if sl <= 0 or close <= 0:
        return None
    if close <= sl:
        return "CLOSE_CONFIRMED"
    if had_intraday_break:
        return "BREAK_CANCELLED"
    return None


def whale_signal_ok(m: dict, phase: str, progress: float, min_turnover: float, min_score: int = 80) -> bool:
    """فلتر إشارات الحيتان: جلسة مستمرة، بعد أول 30 دقيقة، سيولة كافية، ومش عند حد الصعود."""
    return (
        phase == "continuous"
        and progress >= 30.0 / SESSION_MINUTES
        and m.get("score", 0) >= min_score
        and m.get("turnover", 0.0) >= min_turnover
        and m.get("change", 0.0) < 19.5
    )


def evaluate_signal(sig: dict, day_high: float, day_low: float, days_open: int, max_days: int = 20):
    """
    تقييم إشارة مفتوحة في سجل الإشارات بعد إغلاق يوم تالٍ ليوم الإشارة.
    لو الوقف والهدف اتلمسوا في نفس اليوم بنحسبها SL (افتراض متحفظ).
    """
    sl, tp1 = float(sig.get("sl") or 0), float(sig.get("tp1") or 0)
    if sl > 0 and day_low > 0 and day_low <= sl:
        return "SL"
    if tp1 > 0 and day_high >= tp1:
        return "TP1"
    if days_open >= max_days:
        return "EXPIRED"
    return None


def is_authorized_chat(sender_chat: str, allowed: set) -> bool:
    """مقفول افتراضياً: لو مفيش chat ids مسموحة، مفيش أوامر بتتنفذ."""
    return bool(sender_chat) and bool(allowed) and str(sender_chat) in allowed
