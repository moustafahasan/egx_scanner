"""
EGX Whale Hunter — مدارس التحليل (V11.5)
كل الحسابات هنا pandas/numpy بس (من غير Streamlit) عشان تتختبر لوحدها.
المفاتيح اللي بترجعها الدوال متوافقة مع واجهة egx_scanner.py.

قاعدة عامة: آخر قمة/قاع في الـ ZigZag "جاري" (لسه ممكن يتحرك)، فالقرارات بتتبني على
القمم والقيعان المؤكدة بس، والجاري بيتعرض كمعلومة.
"""
import math
from datetime import datetime, date, timedelta

import numpy as np
import pandas as pd

import egx_core as core


# =====================================================================
# المؤشرات الأساسية
# =====================================================================
def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """EMA20/50/200 + متوسط الفوليوم + ATR14 (Wilder). بيرجع نسخة."""
    d = df.copy()
    d["EMA20"] = d["Close"].ewm(span=20, adjust=False).mean()
    d["EMA50"] = d["Close"].ewm(span=50, adjust=False).mean()
    d["EMA200"] = d["Close"].ewm(span=200, adjust=False).mean()
    d["VolSMA20"] = d["Volume"].rolling(20).mean()
    prev_c = d["Close"].shift(1)
    tr = pd.concat([d["High"] - d["Low"], (d["High"] - prev_c).abs(), (d["Low"] - prev_c).abs()], axis=1).max(axis=1)
    d["ATR14"] = tr.ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
    d["ATR"] = d["ATR14"]
    return d


def weekly_trend(df: pd.DataFrame) -> str:
    """اتجاه أسبوعي. أسبوع البورصة المصرية بيقفل الخميس (W-THU)، مش الأحد."""
    if df is None or df.empty or len(df) < 40:
        return "⚪ لا بيانات تاريخية (Yahoo)"
    w = df.resample("W-THU").agg({"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"}).dropna()
    if len(w) < 8:
        return "⚪ بيانات أسبوعية غير كافية"
    ema = w["Close"].ewm(span=20, adjust=False).mean()
    last, prev, e = float(w["Close"].iloc[-1]), float(w["Close"].iloc[-2]), float(ema.iloc[-1])
    if last > e and last > prev:
        return "🟢 صاعد (أسبوعي)"
    if last < e and last < prev:
        return "🔴 هابط (أسبوعي)"
    return "🟡 محايد (أسبوعي)"


# =====================================================================
# ZigZag
# =====================================================================
def extract_zigzag_pivots(df: pd.DataFrame, pct_thresh: float = 0.05) -> list:
    """قمم وقيعان بنسبة انعكاس pct_thresh. آخر نقطة confirmed=False (جارية)."""
    if df is None or len(df) < 5:
        return []
    highs, lows, dates = df["High"].values, df["Low"].values, df.index
    pivots, trend = [], 0
    hi_p, hi_i, lo_p, lo_i = float(highs[0]), 0, float(lows[0]), 0
    last_p, last_idx = 0.0, 0
    for i in range(1, len(df)):
        h, l = float(highs[i]), float(lows[i])
        if trend == 0:
            if h > hi_p:
                hi_p, hi_i = h, i
            if l < lo_p:
                lo_p, lo_i = l, i
            if hi_p >= lo_p * (1 + pct_thresh) and hi_i > lo_i:
                pivots.append({"idx": lo_i, "date": dates[lo_i], "price": lo_p, "type": "L", "confirmed": True})
                trend, last_p, last_idx = 1, hi_p, hi_i
            elif lo_p <= hi_p * (1 - pct_thresh) and lo_i > hi_i:
                pivots.append({"idx": hi_i, "date": dates[hi_i], "price": hi_p, "type": "H", "confirmed": True})
                trend, last_p, last_idx = -1, lo_p, lo_i
        elif trend == 1:
            if h >= last_p:
                last_p, last_idx = h, i
            elif l <= last_p * (1 - pct_thresh):
                pivots.append({"idx": last_idx, "date": dates[last_idx], "price": last_p, "type": "H", "confirmed": True})
                trend, last_p, last_idx = -1, l, i
        else:
            if l <= last_p:
                last_p, last_idx = l, i
            elif h >= last_p * (1 + pct_thresh):
                pivots.append({"idx": last_idx, "date": dates[last_idx], "price": last_p, "type": "L", "confirmed": True})
                trend, last_p, last_idx = 1, h, i
    if trend != 0:
        pivots.append({"idx": last_idx, "date": dates[last_idx], "price": last_p,
                       "type": "H" if trend == 1 else "L", "confirmed": False})
    return pivots


def _confirmed(pivs):
    return [p for p in pivs if p.get("confirmed", True)]


# =====================================================================
# الشموع اليابانية (مع سياق الاتجاه)
# =====================================================================
def analyze_candlestick_patterns(df: pd.DataFrame) -> dict:
    """
    نفس النمط ليه معنى مختلف حسب الاتجاه قبله: المطرقة بعد هبوط = انعكاس صعودي،
    ونفس الشكل بعد صعود = الرجل المشنوق (هابط). الاتجاه = إغلاق الشمعة السابقة مقابل 5 شموع قبلها.
    """
    note = "الشموع لوحدها دلالتها الإحصائية ضعيفة — استخدمها تأكيد مع الاتجاه والسيولة."
    if df is None or len(df) < 16:
        return {"patterns": [], "verdict": "بيانات غير كافية", "note": note}
    sub = df.tail(16)
    O, H, L, C = (sub[k].astype(float).values for k in ("Open", "High", "Low", "Close"))
    patterns = []

    def add(i, name, bias):
        patterns.append({"التاريخ": str(sub.index[i])[:10], "النمط": name, "الاتجاه": bias, "السعر": round(float(C[i]), 4)})

    for i in range(6, len(sub)):
        o, h, l, c = O[i], H[i], L[i], C[i]
        body, rng = abs(c - o), max(1e-9, h - l)
        upper, lower = h - max(o, c), min(o, c) - l
        down_ctx = C[i - 1] < C[i - 6] * 0.98
        up_ctx = C[i - 1] > C[i - 6] * 1.02
        small_upper = upper <= max(body, 0.1 * rng)
        small_lower = lower <= max(body, 0.1 * rng)

        if lower >= 2 * body and small_upper and body > 0:
            if down_ctx:
                add(i, "🔨 مطرقة Hammer (انعكاس صعودي)", "صعودي")
            elif up_ctx:
                add(i, "🪢 الرجل المشنوق Hanging Man (تحذير هابط)", "هابط")
        if upper >= 2 * body and small_lower and body > 0:
            if up_ctx:
                add(i, "⭐ نجمة ساقطة Shooting Star (انعكاس هابط)", "هابط")
            elif down_ctx:
                add(i, "🔁 مطرقة مقلوبة Inverted Hammer (صعودي ضعيف)", "صعودي")
        if body <= 0.1 * rng:
            add(i, "✚ دوجي Doji (تردد)", "محايد")
        po, pc = O[i - 1], C[i - 1]
        if c > o and pc < po and c >= po and o <= pc and down_ctx:
            add(i, "🟢 ابتلاع صعودي Bullish Engulfing", "صعودي")
        if c < o and pc > po and c <= po and o >= pc and up_ctx:
            add(i, "🔴 ابتلاع هابط Bearish Engulfing", "هابط")
        o2, c2, o1, c1 = O[i - 2], C[i - 2], O[i - 1], C[i - 1]
        big2 = abs(c2 - o2) >= 0.5 * max(1e-9, H[i - 2] - L[i - 2])
        small1 = abs(c1 - o1) < 0.3 * abs(c2 - o2)
        ctx2_down = C[i - 3] < C[i - 8] * 0.98 if i >= 8 else down_ctx
        ctx2_up = C[i - 3] > C[i - 8] * 1.02 if i >= 8 else up_ctx
        if c2 < o2 and big2 and small1 and c > o and c > (o2 + c2) / 2 and ctx2_down:
            add(i, "🌅 نجمة الصباح Morning Star (انعكاس صعودي)", "صعودي")
        if c2 > o2 and big2 and small1 and c < o and c < (o2 + c2) / 2 and ctx2_up:
            add(i, "🌆 نجمة المساء Evening Star (انعكاس هابط)", "هابط")

    if not patterns:
        return {"patterns": [], "verdict": "لا توجد أنماط شموع واضحة في آخر 10 جلسات.", "note": note}
    bull = sum(1 for p in patterns if p["الاتجاه"] == "صعودي")
    bear = sum(1 for p in patterns if p["الاتجاه"] == "هابط")
    verdict = "🟢 ميل صعودي" if bull > bear else ("🔴 ميل هابط" if bear > bull else "🟡 تردد (أنماط مختلطة)")
    return {"patterns": patterns[-8:], "verdict": verdict, "note": note, "bias": (bull > bear) - (bear > bull)}


# =====================================================================
# الدعم والمقاومة
# =====================================================================
def analyze_support_resistance(df: pd.DataFrame, lookback: int = 120, tol: float = 0.015) -> dict:
    """
    القمم والقيعان المؤكدة كلها بتتجمع مع بعض (القمة القديمة ممكن تبقى دعم بعد اختراقها)،
    والنوع بيتحدد بمكان المستوى من السعر الحالي، مش بنوع النقطة.
    """
    if df is None or len(df) < 20:
        return {"levels": [], "verdict": "بيانات غير كافية", "nearest_support": None, "nearest_resistance": None}
    sub = df.tail(lookback)
    curr = float(sub["Close"].iloc[-1])
    prices = sorted(p["price"] for p in _confirmed(extract_zigzag_pivots(sub, pct_thresh=0.03)))
    clusters = []
    for v in prices:
        if clusters and abs(v - clusters[-1]["c"]) / clusters[-1]["c"] < tol:
            cl = clusters[-1]
            cl["n"] += 1
            cl["c"] = cl["c"] + (v - cl["c"]) / cl["n"]
        else:
            clusters.append({"c": v, "n": 1})
    levels = []
    for cl in clusters:
        price = cl["c"]
        kind = "دعم ⬇️" if price < curr else "مقاومة ⬆️"
        levels.append({"المستوى": round(price, 4), "النوع": kind, "اللمسات": cl["n"],
                       "البعد %": round((price - curr) / curr * 100, 2)})
    # الأقرب + الأقوى
    sup = [l for l in levels if l["المستوى"] < curr]
    res = [l for l in levels if l["المستوى"] > curr]
    nearest_sup = max((l["المستوى"] for l in sup), default=None)
    nearest_res = min((l["المستوى"] for l in res), default=None)
    levels = sorted(sorted(levels, key=lambda x: -x["اللمسات"])[:8], key=lambda x: x["المستوى"])
    if nearest_sup and nearest_res:
        verdict = f"🟡 داخل نطاق ({nearest_sup:.4g} — {nearest_res:.4g})"
    elif nearest_res:
        verdict = f"🔴 تحت مقاومة ({nearest_res:.4g}) بدون دعم قريب واضح"
    elif nearest_sup:
        verdict = f"🟢 فوق كل المقاومات المرصودة — أقرب دعم {nearest_sup:.4g}"
    else:
        verdict = "⚪ لا توجد مستويات واضحة"
    return {"levels": levels, "verdict": verdict, "nearest_support": nearest_sup, "nearest_resistance": nearest_res}


# =====================================================================
# SMC / ICT
# =====================================================================
def analyze_smc_ict(df: pd.DataFrame) -> dict:
    sub = df.tail(120)
    curr_p = float(sub["Close"].iloc[-1])
    O, H, L, C = (sub[k].astype(float).values for k in ("Open", "High", "Low", "Close"))
    n = len(sub)
    fvgs, obs, sweeps = [], [], []

    for i in range(2, n):
        # FVG مش متغطية لحد دلوقتي
        if L[i] > H[i - 2] and (i + 1 >= n or L[i + 1:].min() > H[i - 2]):
            fvgs.append({"النوع": "🟢 فجوة شرائية (Bullish FVG)", "من": round(H[i - 2], 4), "إلى": round(L[i], 4), "التاريخ": str(sub.index[i])[:10]})
        if H[i] < L[i - 2] and (i + 1 >= n or H[i + 1:].max() < L[i - 2]):
            fvgs.append({"النوع": "🔴 فجوة بيعية (Bearish FVG)", "من": round(H[i], 4), "إلى": round(L[i - 2], 4), "التاريخ": str(sub.index[i])[:10]})
        # Order Block: آخر شمعة عكسية قبل اندفاع يقفل فوق/تحت مداها، ولسه ما اتكسرتش بالإغلاق
        j = i - 1
        if C[j] < O[j] and C[i] > H[j] and (i + 1 >= n or C[i + 1:].min() >= L[j]):
            obs.append({"النوع": "🟢 كتلة طلب مؤسسي (Bullish OB)", "من": round(L[j], 4), "إلى": round(H[j], 4), "التاريخ": str(sub.index[j])[:10]})
        elif C[j] > O[j] and C[i] < L[j] and (i + 1 >= n or C[i + 1:].max() <= H[j]):
            obs.append({"النوع": "🔴 كتلة عرض مؤسسي (Bearish OB)", "من": round(L[j], 4), "إلى": round(H[j], 4), "التاريخ": str(sub.index[j])[:10]})

    conf = _confirmed(extract_zigzag_pivots(sub, pct_thresh=0.04))
    hs = [p["price"] for p in conf if p["type"] == "H"]
    ls = [p["price"] for p in conf if p["type"] == "L"]
    structure, badge, bias = "⚖️ نطاق عرضي (Range)", "badge-warn", 0
    last_h = hs[-1] if hs else None
    last_l = ls[-1] if ls else None
    if len(hs) >= 2 and len(ls) >= 2:
        up = hs[-1] > hs[-2] and ls[-1] > ls[-2]
        down = hs[-1] < hs[-2] and ls[-1] < ls[-2]
        if up and curr_p > last_h:
            structure, badge, bias = "🟢 استمرار صاعد — كسر هيكل (Bullish BOS)", "badge-bull", 1
        elif up and curr_p < last_l:
            structure, badge, bias = "🔴 تغيّر الطابع لهابط (Bearish CHoCH)", "badge-bear", -1
        elif down and curr_p < last_l:
            structure, badge, bias = "🔴 استمرار هابط — كسر هيكل (Bearish BOS)", "badge-bear", -1
        elif down and curr_p > last_h:
            structure, badge, bias = "🟢 تغيّر الطابع لصاعد (Bullish CHoCH)", "badge-bull", 1
        elif up:
            structure, badge, bias = "🟢 هيكل صاعد (قمم وقيعان أعلى)", "badge-bull", 1
        elif down:
            structure, badge, bias = "🔴 هيكل هابط (قمم وقيعان أدنى)", "badge-bear", -1
        elif hs[-1] < hs[-2] and ls[-1] > ls[-2]:
            structure = "🟡 انضغاط سعري (قمم أدنى وقيعان أعلى) — انتظر الكسر"

    if last_l is not None and L[-10:].min() < last_l < curr_p:
        sweeps.append(f"🐋 سحب سيولة أسفل القاع ({last_l:.4f}) والارتداد فوقه (Bullish Liquidity Sweep)")
    if last_h is not None and H[-10:].max() > last_h > curr_p:
        sweeps.append(f"⚠️ سحب سيولة أعلى القمة ({last_h:.4f}) والهبوط تحتها (Bearish Liquidity Sweep)")

    return {"structure": structure, "badge_cls": badge, "bias": bias,
            "fvgs": fvgs[-5:], "obs": obs[-5:], "sweeps": sweeps,
            "swing_high": round(last_h, 4) if last_h else None,
            "swing_low": round(last_l, 4) if last_l else None}


# =====================================================================
# وايكوف و VSA
# =====================================================================
def analyze_wyckoff_vsa(df: pd.DataFrame) -> dict:
    d = df.tail(140).copy()
    # الفوليوم بيتقارن بمتوسط الـ 20 جلسة اللي قبله (من غير الجلسة نفسها)
    d["VolRatio"] = d["Volume"] / d["Volume"].rolling(20).mean().shift(1).replace(0, np.nan)
    cur = d.iloc[-1]
    c_p = float(cur["Close"])
    ema50 = float(d["Close"].ewm(span=50, adjust=False).mean().iloc[-1]) if "EMA50" not in d else float(cur["EMA50"])
    ema200 = float(cur["EMA200"]) if "EMA200" in d else ema50
    v_ratio = float(cur["VolRatio"]) if pd.notna(cur["VolRatio"]) else 1.0
    clv = (c_p - float(cur["Low"])) / max(1e-9, float(cur["High"] - cur["Low"]))

    box = d.iloc[-40:]
    box_high, box_low = float(box["High"].max()), float(box["Low"].min())
    box_range_pct = (box_high - box_low) / max(1e-9, box_low) * 100
    pre = d.iloc[:-40]
    pre_trend = (float(pre["Close"].iloc[-1]) / float(pre["Close"].iloc[0]) - 1) * 100 if len(pre) >= 20 else 0.0

    if c_p > ema50 > ema200 and c_p >= box_high * 0.96:
        phase, badge, bias = "🚀 مرحلة الانطلاق (Markup)", "badge-bull", 1
    elif c_p < ema50 < ema200 and c_p <= box_low * 1.04:
        phase, badge, bias = "📉 مرحلة الهبوط (Markdown)", "badge-bear", -1
    elif box_range_pct <= 18 and pre_trend <= -10:
        phase, badge, bias = "🔋 تجميع محتمل (Accumulation) — نطاق ضيق بعد هبوط", "badge-bull", 1
    elif box_range_pct <= 18 and pre_trend >= 10:
        phase, badge, bias = "⚠️ تصريف محتمل (Distribution) — نطاق ضيق بعد صعود", "badge-bear", -1
    elif box_range_pct <= 18:
        phase, badge, bias = "⚖️ نطاق عرضي (تجميع/إعادة تجميع غير محسوم)", "badge-warn", 0
    else:
        phase, badge, bias = "🔀 مرحلة انتقالية — مفيش نطاق واضح", "badge-warn", 0

    whale = []
    for idx, row in d[d["VolRatio"] >= 2.0].tail(5).iterrows():
        kind = "🟢 شمعة حيتان شرائية (PVSRA)" if row["Close"] >= row["Open"] else "🔴 شمعة حيتان بيعية (PVSRA)"
        whale.append({"التاريخ": str(idx)[:10], "الإشارة": kind, "السعر": round(float(row["Close"]), 4), "نسبة الفوليوم": f"{row['VolRatio']:.1f}x"})

    notes = []
    if v_ratio >= 2.0 and clv >= 0.65:
        notes.append("🟢 **قوة (Effort up):** فوليوم مضاعف مع إغلاق في الثلث العلوي.")
    elif v_ratio >= 2.0 and clv <= 0.35:
        notes.append("🔴 **ضغط بيعي (Selling pressure):** فوليوم مرتفع جداً مع إغلاق قرب القاع.")
    elif v_ratio <= 0.65 and c_p < float(d["Close"].iloc[-2]) and c_p > ema50:
        notes.append("🎯 **جفاف العرض (No Supply):** تراجع هادئ بفوليوم ضعيف داخل اتجاه صاعد.")

    prior = d.iloc[-43:-3]
    p_low, p_high = float(prior["Low"].min()), float(prior["High"].max())
    last3 = d.iloc[-3:]
    if float(last3["Low"].min()) < p_low < c_p:
        sv = float(last3["VolRatio"].max()) if last3["VolRatio"].notna().any() else 1.0
        q = "بفوليوم ضعيف (أقوى)" if sv < 1.0 else "بفوليوم عالي — محتاج اختبار ناجح قبل الدخول"
        notes.append(f"🐋 **Spring:** كسر كاذب لقاع النطاق ({p_low:.4f}) ورجوع فوقه {q}.")
        bias = max(bias, 1)
    if float(last3["High"].max()) > p_high > c_p:
        notes.append(f"⚠️ **Upthrust:** اختراق كاذب لقمة النطاق ({p_high:.4f}) ورجوع تحتها — إشارة تصريف.")
        bias = min(bias, -1)

    return {"phase": phase, "badge_cls": badge, "bias": bias,
            "box_high": round(box_high, 4), "box_low": round(box_low, 4), "vol_ratio": round(v_ratio, 2),
            "vsa_notes": notes or ["الحركة متوافقة مع متوسط الفوليوم بدون شذوذ VSA واضح."],
            "whale_candles": whale}


# =====================================================================
# CPR + بروفايل الفوليوم
# =====================================================================
def _cpr(h, l, c):
    pivot = (h + l + c) / 3.0
    bc = (h + l) / 2.0
    tc = 2 * pivot - bc
    return pivot, max(tc, bc), min(tc, bc)


def analyze_cpr_and_vp(df: pd.DataFrame) -> dict:
    sub = df.tail(90)
    curr_p = float(sub["Close"].iloc[-1])
    # CPR "شهري" = آخر 20 جلسة مكتملة (من غير النهارده)
    prev_m = df.iloc[-21:-1] if len(df) >= 22 else sub.iloc[:-1]
    h_m, l_m, c_m = float(prev_m["High"].max()), float(prev_m["Low"].min()), float(prev_m["Close"].iloc[-1])
    pivot, cpr_top, cpr_bot = _cpr(h_m, l_m, c_m)
    r1, s1 = 2 * pivot - l_m, 2 * pivot - h_m
    # CPR يومي من جلسة أمس (زي مؤشر Whale Hunter)
    y = df.iloc[-2]
    d_piv, d_tc, d_bc = _cpr(float(y["High"]), float(y["Low"]), float(y["Close"]))

    # بروفايل: فوليوم كل شمعة بيتوزع على مداها كله، مش على سعر الإغلاق بس
    p_min, p_max = float(sub["Low"].min()), float(sub["High"].max())
    bins = np.linspace(p_min, max(p_min * 1.001 + 1e-6, p_max), 25)
    centers = (bins[:-1] + bins[1:]) / 2
    hist = np.zeros(len(centers))
    for lo, hi, v in zip(sub["Low"].astype(float), sub["High"].astype(float), sub["Volume"].astype(float)):
        overlap = np.clip(np.minimum(bins[1:], hi) - np.maximum(bins[:-1], lo), 0, None)
        tot = overlap.sum()
        if tot > 0:
            hist += v * overlap / tot
        else:
            hist[min(len(hist) - 1, max(0, np.searchsorted(bins, lo) - 1))] += v
    poc_i = int(np.argmax(hist))
    target, acc = hist.sum() * 0.70, hist[poc_i]
    lo_i = hi_i = poc_i
    while acc < target and (lo_i > 0 or hi_i < len(hist) - 1):
        v_lo = hist[lo_i - 1] if lo_i > 0 else -1
        v_hi = hist[hi_i + 1] if hi_i < len(hist) - 1 else -1
        if v_hi >= v_lo:
            hi_i += 1; acc += v_hi
        else:
            lo_i -= 1; acc += v_lo
    poc, val, vah = float(centers[poc_i]), float(bins[lo_i]), float(bins[hi_i + 1])

    if curr_p > cpr_top and curr_p > vah:
        verdict, badge, bias = "🟢 فوق منطقة القيمة وCPR (اتجاه صاعد)", "badge-bull", 1
    elif curr_p < cpr_bot and curr_p < val:
        verdict, badge, bias = "🔴 تحت منطقة القيمة وCPR (ضغط بيعي)", "badge-bear", -1
    else:
        verdict, badge, bias = "🟡 داخل منطقة التوازن (Value Area)", "badge-warn", 0
    width = (cpr_top - cpr_bot) / max(1e-9, pivot) * 100
    return {"pivot": round(pivot, 4), "tc": round(cpr_top, 4), "bc": round(cpr_bot, 4),
            "r1": round(r1, 4), "s1": round(s1, 4), "cpr_width_pct": round(width, 2),
            "daily_tc": round(d_tc, 4), "daily_bc": round(d_bc, 4), "daily_pivot": round(d_piv, 4),
            "above_daily_cpr": curr_p > d_tc,
            "poc": round(poc, 4), "vah": round(vah, 4), "val": round(val, 4),
            "bin_centers": centers, "vol_hist": hist, "verdict": verdict, "badge_cls": badge, "bias": bias}


# =====================================================================
# الهارمونيك (XABCD) — عرض فقط
# =====================================================================
HARMONICS = [
    # الاسم, AB/XA, BC/AB, AD/XA (تصحيح D من A), PRZ
    ("جارتلي (Gartley)", (0.55, 0.68), (0.382, 0.886), (0.74, 0.83), 0.786),
    ("الخفاش (Bat)", (0.35, 0.55), (0.382, 0.886), (0.84, 0.92), 0.886),
    ("الفراشة (Butterfly)", (0.74, 0.83), (0.382, 0.886), (1.22, 1.65), 1.272),
    ("الكابوريا (Crab)", (0.35, 0.68), (0.382, 0.886), (1.55, 1.70), 1.618),
]


def analyze_harmonic_patterns(df: pd.DataFrame) -> dict:
    sub = df.tail(160)
    pivs = extract_zigzag_pivots(sub, pct_thresh=0.045)
    curr_p = float(sub["Close"].iloc[-1])
    empty = {"detected": False, "badge_cls": "badge-warn", "points": pivs[-5:], "prz_low": None, "prz_high": None,
             "target_1": None, "target_2": None}
    if len(pivs) < 5:
        return {**empty, "pattern_name": "لا يوجد نموذج توافقي", "notes": "القمم والقيعان غير كافية لتكوين XABCD."}
    X, A, B, C, D = pivs[-5:]
    xa, ab, bc = abs(A["price"] - X["price"]), abs(B["price"] - A["price"]), abs(C["price"] - B["price"])
    if xa < 1e-9 or ab < 1e-9:
        return {**empty, "pattern_name": "تذبذب ضعيف", "notes": "مدى الحركة صغير جداً."}
    r_ab, r_bc, r_ad = ab / xa, bc / ab, abs(A["price"] - D["price"]) / xa
    bullish = X["type"] == "L"
    match = None
    for name, (a1, a2), (b1, b2), (d1, d2), prz in HARMONICS:
        if a1 <= r_ab <= a2 and b1 <= r_bc <= b2 and d1 <= r_ad <= d2:
            match = (name, prz)
            break
    ratios = f"AB/XA = {r_ab:.3f} | BC/AB = {r_bc:.3f} | AD/XA = {r_ad:.3f}"
    if not match:
        return {**empty, "pattern_name": "لا يوجد نموذج توافقي مطابق", "notes": f"النسب الحالية: {ratios} — مش مطابقة لأي نموذج."}
    name, prz = match
    center = A["price"] - xa * prz if bullish else A["price"] + xa * prz
    ad = abs(A["price"] - D["price"])
    t1 = D["price"] + 0.382 * ad if bullish else D["price"] - 0.382 * ad
    t2 = D["price"] + 0.618 * ad if bullish else D["price"] - 0.618 * ad
    state = "" if D.get("confirmed") else " — النقطة D لسه بتتكون"
    return {"detected": True,
            "pattern_name": (f"🟢 {name} شرائي" if bullish else f"🔴 {name} بيعي") + state,
            "badge_cls": "badge-bull" if bullish else "badge-bear", "points": [X, A, B, C, D],
            "prz_low": round(center * 0.985, 4), "prz_high": round(center * 1.015, 4),
            "target_1": round(t1, 4), "target_2": round(t2, 4),
            "notes": f"{ratios}. السعر الحالي {curr_p:.4f}. نماذج الهارمونيك أدلتها الإحصائية ضعيفة — للعرض فقط."}


# =====================================================================
# إليوت — عرض فقط
# =====================================================================
def analyze_elliott_waves(df: pd.DataFrame, pct_thresh: float = 0.05) -> dict:
    pivs = extract_zigzag_pivots(df, pct_thresh=pct_thresh)
    base = {"badge_cls": "badge-warn", "invalidation": None, "target_1": None, "target_2": None,
            "labeled_pivots": pivs[-6:], "rules_check": []}
    if len(pivs) < 6:
        return {**base, "wave_name": "🌊 لا يوجد عدّ موجي كافٍ",
                "summary": "عدد القمم والقيعان قليل في المدى ده."}
    six = pivs[-6:]
    p = [x["price"] for x in six]
    up = six[0]["type"] == "L"
    s = 1 if up else -1
    w1, w3, w5 = abs(p[1] - p[0]), abs(p[3] - p[2]), abs(p[5] - p[4])
    rules = [
        ("الموجة (2) ما كسرتش بداية (1)", f"{p[2]:.4f} vs {p[0]:.4f}", s * (p[2] - p[0]) > 0),
        ("الموجة (3) مش الأقصر", f"{w3:.4f}", w3 >= min(w1, w5)),
        ("الموجة (4) ما دخلتش منطقة (1)", f"{p[4]:.4f} vs {p[1]:.4f}", s * (p[4] - p[1]) > 0),
        ("(3) تخطت قمة (1)", f"{p[3]:.4f} vs {p[1]:.4f}", s * (p[3] - p[1]) > 0),
    ]
    labeled = [{**x, "label": lbl} for x, lbl in zip(six, ["(0)", "(1)", "(2)", "(3)", "(4)", "(5)"])]
    if not all(r[2] for r in rules):
        return {**base, "wave_name": "🌊 لا يوجد عدّ دافع صالح", "labeled_pivots": labeled, "rules_check": rules,
                "summary": "آخر 6 قمم وقيعان بتكسر قاعدة أو أكتر من قواعد الموجة الدافعة — الهيكل غير واضح."}
    running = not six[5].get("confirmed", True)
    # مستهدفات الموجة 5 من قاع/قمة الموجة 4
    t1 = p[4] + s * w1                       # 5 = 1
    t2 = p[4] + s * 0.618 * abs(p[3] - p[0])  # 5 = 0.618 × (0→3)
    t1, t2 = sorted([t1, t2], reverse=not up)
    name = ("🌊 موجة دافعة صاعدة" if up else "🌊 موجة دافعة هابطة") + (" — الموجة 5 جارية" if running else " — مكتملة")
    if running:
        summary = (f"الموجة الخامسة جارية؛ مستهدفاتها {t1:.4f} ثم {t2:.4f}. "
                   f"كسر {p[4]:.4f} (نهاية الموجة 4) يلغي العدّ. بعد اكتمال الخامسة المتوقع تصحيح ABC.")
    else:
        summary = f"الخمس موجات اكتملت؛ المتوقع تصحيح ABC نحو منطقة الموجة 4 ({p[4]:.4f})."
    return {"wave_name": name, "badge_cls": "badge-bull" if up else "badge-bear",
            "invalidation": round(p[4], 4), "target_1": round(t1, 4), "target_2": round(t2, 4),
            "summary": summary + " (إليوت تفسيري وأدلته ضعيفة — للعرض فقط)",
            "labeled_pivots": labeled, "rules_check": rules}


# =====================================================================
# جان والفلك — عرض فقط، مفيش دليل إحصائي
# =====================================================================
def compute_gann_simple(pivot_date, pivot_price, is_pivot_low, current_price, today: date = None):
    sqrt_p = pivot_price ** 0.5
    sq9 = []
    for ang in [45, 90, 135, 180, 225, 270, 315, 360]:
        step = ang / 180.0
        target = (sqrt_p + step) ** 2 if is_pivot_low else max(0.01, sqrt_p - step) ** 2
        sq9.append({"الزاوية": f"{ang}°", "المستوى": round(target, 4), "النوع": "مقاومة ⬆️" if is_pivot_low else "دعم ⬇️",
                    "البعد %": round((target - current_price) / current_price * 100, 2)})
    today = today or core.cairo_now().date()
    out = []
    for cyc in [45, 90, 180]:
        t = pivot_date + timedelta(days=cyc)
        diff = (t - today).days
        if -30 <= diff <= 180:
            st_ = "🔥 نافذة انعكاس نشطة!" if abs(diff) <= 5 else (f"بعد {diff} يوم" if diff > 0 else f"مضى {abs(diff)} يوم")
            out.append({"الدورة": f"دورة {cyc} يوم", "التاريخ": t, "الحالة": st_})
    return sq9, out


ZODIAC_SIGNS_AR = ["♈ الحمل", "♉ الثور", "♊ الجوزاء", "♋ السرطان", "♌ الأسد", "♍ العذراء", "♎ الميزان", "♏ العقرب", "♐ القوس", "♑ الجدي", "♒ الدلو", "♓ الحوت"]
ORBITAL_ELEMENTS = {  # JPL approximate elements (1800–2050)
    "Mercury": (0.38709927, 0.00000037, 0.20563593, 0.00001906, 7.00497902, -0.00594749, 252.25032350, 149472.67411175, 77.45779628, 0.16047689, 48.33076593, -0.12534081),
    "Venus": (0.72333566, 0.00000390, 0.00677672, -0.00004107, 3.39467605, -0.00078890, 181.97909950, 58517.81538729, 131.60246718, 0.00268329, 76.67984255, -0.27769418),
    "Earth": (1.00000261, 0.00000562, 0.01671123, -0.00004392, -0.00001531, -0.01294668, 100.46457166, 35999.37244981, 102.93768193, 0.32327364, 0.0, 0.0),
    "Mars": (1.52371034, 0.00001847, 0.09339410, 0.00007882, 1.84969142, -0.00813131, -4.55343205, 19140.30268499, -23.94362959, 0.44441088, 49.55953891, -0.29257343),
    "Jupiter": (5.20288700, -0.00011607, 0.04838624, -0.00013253, 1.30439695, -0.00183714, 34.39644051, 3034.74612775, 14.72847983, 0.21252668, 100.47390909, 0.20469106),
    "Saturn": (9.53667594, -0.00125060, 0.05386179, -0.00050991, 2.48599187, 0.00193609, 49.95424423, 1222.49362201, 92.59887831, -0.41897216, 113.66242448, -0.28867794),
}


def _julian_centuries(dt: datetime) -> float:
    return (dt.toordinal() + 1721424.5 + (dt.hour + dt.minute / 60.0) / 24.0 - 2451545.0) / 36525.0


def _heliocentric_xyz(planet: str, T: float) -> tuple:
    a0, da, e0, de, I0, dI, L0, dL, w0, dw, O0, dO = ORBITAL_ELEMENTS[planet]
    a, e = a0 + da * T, e0 + de * T
    I, L = math.radians(I0 + dI * T), (L0 + dL * T) % 360.0
    w_bar = (w0 + dw * T) % 360.0
    O = math.radians((O0 + dO * T) % 360.0)
    w = math.radians((w_bar - math.degrees(O)) % 360.0)
    M = math.radians((L - w_bar) % 360.0)
    E = M + e * math.sin(M)
    for _ in range(6):
        E -= (E - e * math.sin(E) - M) / (1.0 - e * math.cos(E))
    xp, yp = a * (math.cos(E) - e), a * math.sqrt(max(0.0, 1 - e * e)) * math.sin(E)
    cO, sO, cw, sw, cI = math.cos(O), math.sin(O), math.cos(w), math.sin(w), math.cos(I)
    # V11.5: كان فيه cos_O*sin_w بدل cos_O*cos_w في y، وده كان بيبوظ الأطوال (الشمس يوم الاعتدال طلعت 310° بدل 0°)
    return ((cO * cw - sO * sw * cI) * xp + (-cO * sw - sO * cw * cI) * yp,
            (sO * cw + cO * sw * cI) * xp + (-sO * sw + cO * cw * cI) * yp)


def get_planetary_longitudes(dt: datetime) -> dict:
    T = _julian_centuries(dt)
    xe, ye = _heliocentric_xyz("Earth", T)
    pos = {"☀️ الشمس": math.degrees(math.atan2(-ye, -xe)) % 360.0}
    Lp = (218.3164477 + 481267.88123421 * T) % 360.0
    D = math.radians((297.8501921 + 445267.1114034 * T) % 360.0)
    Mp = math.radians((134.9633964 + 477198.8675055 * T) % 360.0)
    pos["🌙 القمر"] = (Lp + 6.289 * math.sin(Mp) + 1.274 * math.sin(2 * D - Mp) + 0.658 * math.sin(2 * D)) % 360.0
    for en, ar in [("Mercury", "☿ عطارد"), ("Venus", "♀ الزهرة"), ("Mars", "♂ المريخ"), ("Jupiter", "♃ المشتري"), ("Saturn", "♄ زحل")]:
        xp, yp = _heliocentric_xyz(en, T)
        pos[ar] = math.degrees(math.atan2(yp - ye, xp - xe)) % 360.0
    return pos


def deg_to_zodiac(deg: float) -> str:
    return f"{ZODIAC_SIGNS_AR[int(deg // 30) % 12]} ({deg % 30:.1f}°)"


def upcoming_aspects(today: date, days: int = 30) -> list:
    out, seen = [], set()
    for off in range(days + 1):
        pos = get_planetary_longitudes(datetime.combine(today + timedelta(days=off), datetime.min.time()) + timedelta(hours=12))
        for p1, p2 in [("☀️ الشمس", "♂ المريخ"), ("☀️ الشمس", "♃ المشتري"), ("☀️ الشمس", "♄ زحل"), ("♂ المريخ", "♄ زحل"), ("♃ المشتري", "♄ زحل")]:
            dd = abs(pos[p1] - pos[p2]) % 360.0
            dd = 360.0 - dd if dd > 180 else dd
            for ang, nm in [(0, "اقتران ☌"), (90, "تربيع □"), (120, "تثليث △"), (180, "تقابل ☍")]:
                k = f"{p1}-{p2}-{ang}"
                if abs(dd - ang) <= 1.0 and k not in seen:
                    seen.add(k)
                    out.append({"التاريخ": today + timedelta(days=off), "الكوكبان": f"{p1} × {p2}", "الزاوية": nm,
                                "متبقي": "اليوم" if off == 0 else f"بعد {off} يوم"})
    return out


def add_egx_trading_days(start_dt: date, trading_days: int, holidays: set = None) -> date:
    cur, added = start_dt, 0
    while added < trading_days:
        cur += timedelta(days=1)
        if core.is_trading_day(cur, holidays if holidays is not None else set()):
            added += 1
    return cur


# =====================================================================
# باك تيست واقعي
# =====================================================================
def run_simple_backtest(df, capital=100000.0, risk_pct=1.5, fee_rate=core.FEE_PER_SIDE_TRADER, slippage=0.002):
    """
    إشارة: إغلاق > EMA20 > EMA50 و RVOL >= 1.2.
    الدخول على افتتاح الجلسة التالية (مش على إغلاق شمعة الإشارة).
    الوقف 2×ATR14 حقيقي، ولو السعر فتح تحت الوقف الخروج بسعر الافتتاح (فجوة).
    لو الوقف والهدف اتلمسوا في نفس الشمعة بنفترض الوقف الأول (متحفظ). رسوم + انزلاق على الجانبين.
    """
    if df is None or len(df) < 60:
        return {"trades": [], "equity": [], "metrics": {}}
    d = add_indicators(df) if "ATR14" not in df.columns else df.copy()
    d["RVOL"] = d["Volume"] / d["Volume"].rolling(20).mean().shift(1)
    O, H, L, C = (d[k].astype(float).values for k in ("Open", "High", "Low", "Close"))
    E20, E50, ATR, RV = d["EMA20"].values, d["EMA50"].values, d["ATR14"].values, d["RVOL"].values
    idx = d.index
    cash, pos, trades, equity = float(capital), None, [], [float(capital)]

    def close_pos(i, raw_exit, reason):
        nonlocal cash, pos
        px = raw_exit * (1 - slippage)
        proceeds = pos["shares"] * px
        fees = (pos["cost"] + proceeds) * fee_rate
        pnl = proceeds - pos["cost"] - fees
        cash += proceeds - fees  # تكلفة الشراء اتخصمت وقت الدخول
        r_mult = pnl / max(1e-9, pos["risk_amt"])
        trades.append({"entry_date": str(pos["date"])[:10], "exit_date": str(idx[i])[:10], "entry": round(pos["entry"], 4),
                       "exit": round(px, 4), "shares": pos["shares"], "pnl": round(pnl, 2), "R": round(r_mult, 2), "reason": reason})
        equity.append(cash)
        pos = None

    for i in range(30, len(d)):
        if pos is None:
            if i + 1 >= len(d) or np.isnan(ATR[i]) or np.isnan(RV[i]):
                continue
            if C[i] > E20[i] > E50[i] and RV[i] >= 1.2:
                entry = O[i + 1] * (1 + slippage)
                sl = max(0.01, entry - 2.0 * ATR[i])
                r_u = entry - sl
                if r_u <= 0:
                    continue
                shares = int(min(cash * risk_pct / 100.0 / r_u, cash / (entry * (1 + fee_rate))))
                if shares <= 0:
                    continue
                cost = shares * entry
                cash -= cost
                pos = {"entry": entry, "shares": shares, "sl": sl, "tp1": entry + 1.618 * r_u, "date": idx[i + 1],
                       "cost": cost, "risk_amt": shares * r_u, "bar": i + 1}
            continue
        j = i
        if O[j] <= pos["sl"]:
            close_pos(j, O[j], "SL (فجوة)")
        elif L[j] <= pos["sl"]:
            close_pos(j, pos["sl"], "SL")
        elif O[j] >= pos["tp1"]:
            close_pos(j, O[j], "TP1 (فجوة)")
        elif H[j] >= pos["tp1"]:
            close_pos(j, pos["tp1"], "TP1")
        elif C[j] < E20[j]:
            close_pos(j, C[j], "كسر EMA20")
    if pos is not None:
        close_pos(len(d) - 1, C[-1] / (1 - slippage), "مفتوحة (آخر سعر)")

    wins = [t for t in trades if t["pnl"] > 0]
    losses = [t for t in trades if t["pnl"] <= 0]
    gross_l = abs(sum(t["pnl"] for t in losses))
    peak, maxdd = equity[0], 0.0
    for v in equity:
        peak = max(peak, v)
        maxdd = max(maxdd, peak - v)
    bh = (C[-1] / C[30] - 1) * 100
    metrics = {
        "trades": len(trades), "wins": len(wins), "losses": len(losses),
        "win_rate": round(len(wins) / len(trades) * 100, 1) if trades else 0.0,
        "profit_factor": round(sum(t["pnl"] for t in wins) / gross_l, 2) if gross_l > 0 else 0.0,
        "avg_R": round(sum(t["R"] for t in trades) / len(trades), 2) if trades else 0.0,
        "total_pnl": round(cash - capital, 2), "final_equity": round(cash, 2),
        "max_drawdown": round(maxdd, 2), "return_pct": round((cash - capital) / capital * 100, 2),
        "buy_hold_pct": round(bh, 2),
    }
    return {"trades": trades, "equity": equity, "metrics": metrics}


# =====================================================================
# ملخص الإجماع (فكرة جديدة)
# =====================================================================
# الأوزان حسب قوة الأدلة (من البحث): الاتجاه والسيولة أقوى، الشموع أضعف، جان/هارمونيك/إليوت بدون وزن.
SCHOOL_WEIGHTS = {"الاتجاه (EMA)": 3, "الأسبوعي": 2, "وايكوف/السيولة": 2, "هيكل SMC": 2, "CPR/القيمة": 2, "الشموع": 0.5}


def confluence_summary(df: pd.DataFrame, live: dict = None) -> dict:
    """يجمع رأي كل مدرسة (+1/0/−1) بأوزان حسب قوة الأدلة. live = بيانات السهم من الرادار (اختياري)."""
    if df is None or df.empty or len(df) < 60:
        return {"score": None, "label": "⚪ بيانات تاريخية غير كافية", "rows": []}
    d = df if "EMA200" in df.columns else add_indicators(df)
    c = float(d["Close"].iloc[-1])
    e20, e50, e200 = (float(d[k].iloc[-1]) for k in ("EMA20", "EMA50", "EMA200"))
    trend = 1 if c > e50 > e200 else (-1 if c < e50 < e200 else 0)
    wk = weekly_trend(d)
    wk_b = 1 if wk.startswith("🟢") else (-1 if wk.startswith("🔴") else 0)
    wy, smc, cpr, cnd = analyze_wyckoff_vsa(d), analyze_smc_ict(d), analyze_cpr_and_vp(d), analyze_candlestick_patterns(d)
    rows = [
        ("الاتجاه (EMA)", trend, "فوق EMA50 و EMA200" if trend > 0 else ("تحت EMA50 و EMA200" if trend < 0 else "مختلط")),
        ("الأسبوعي", wk_b, wk),
        ("وايكوف/السيولة", wy["bias"], wy["phase"]),
        ("هيكل SMC", smc["bias"], smc["structure"]),
        ("CPR/القيمة", cpr["bias"], cpr["verdict"]),
        ("الشموع", cnd.get("bias", 0), cnd["verdict"]),
    ]
    tot_w = sum(SCHOOL_WEIGHTS[n] for n, _, _ in rows)
    score = round(sum(SCHOOL_WEIGHTS[n] * b for n, b, _ in rows) / tot_w * 100)
    label = "🟢 إجماع صعودي" if score >= 40 else ("🔴 إجماع هابط" if score <= -40 else "🟡 إشارات متضاربة")
    # السيولة الفعلية: متوسط قيمة التداول 20 جلسة
    adv = float((d["Close"] * d["Volume"]).tail(20).mean())
    liq_warn = None
    if live and live.get("قيمة الصفقة") and adv > 0:
        share = live["قيمة الصفقة"] / adv * 100
        if share >= 10:
            liq_warn = f"⚠️ حجم الصفقة المقترح = {share:.0f}% من متوسط التداول اليومي — التنفيذ هيحرّك السعر. قسّم الأمر."
    return {"score": score, "label": label,
            "rows": [{"المدرسة": n, "الرأي": "🟢" if b > 0 else ("🔴" if b < 0 else "🟡"), "الوزن": SCHOOL_WEIGHTS[n], "التفاصيل": t} for n, b, t in rows],
            "adv": adv, "liquidity_warning": liq_warn}
