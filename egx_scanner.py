import os
import re
import io
import json
import math
import time
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, date, timedelta, timezone

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import egx_core as core
import egx_schools as schools
import egx_theme as theme
import egx_ui as ui
from egx_schools import (
    run_simple_backtest, analyze_candlestick_patterns, analyze_support_resistance, compute_gann_simple,
    extract_zigzag_pivots, analyze_smc_ict, analyze_wyckoff_vsa, analyze_cpr_and_vp,
    analyze_harmonic_patterns, analyze_elliott_waves, get_planetary_longitudes, deg_to_zodiac,
)

# ==========================================
# إعدادات الصفحة والتصميم البصري الداكن (V11.4)
# ==========================================
st.set_page_config(
    page_title="EGX Whale Hunter Pro V11.5",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# V11.5: نظام تصميم واحد بوضعين (داكن Terminal / فاتح Fintech). أول مرة بيتبع وضع Streamlit نفسه.
if "theme_mode" not in st.session_state:
    try:
        st.session_state["theme_mode"] = "light" if st.context.theme.type == "light" else "dark"
    except Exception:
        st.session_state["theme_mode"] = "dark"
THEME_MODE = st.session_state["theme_mode"]
PAL = theme.palette(THEME_MODE)
st.markdown(theme.build_css(THEME_MODE), unsafe_allow_html=True)
st.markdown(ui.UI_CSS, unsafe_allow_html=True)


def _toggle_theme():
    st.session_state["theme_mode"] = "light" if st.session_state.get("theme_mode") == "dark" else "dark"


# ==========================================
# قاموس أسماء الشركات المصرية والأسهم القيادية
# ==========================================
EGX_ARABIC_NAMES = {
    "COMI": "البنك التجاري الدولي (CIB)",
    "TMGH": "مجموعة طلعت مصطفى القابضة",
    "HRHO": "مجموعة إي إف جي القابضة (هيرميس)",
    "ABUK": "أبو قير للأسمدة والصناعات الكيماوية",
    "MFPC": "مصر لإنتاج الأسمدة (موبكو)",
    "SWDY": "السويدي إليكتريك",
    "EAST": "الشرقية - إيسترن كومباني",
    "EFIH": "إي فاينانس للاستثمارات المالية والرقمية",
    "FWRY": "فوري لتكنولوجيا البنوك والمدفوعات الإلكترونية",
    "ESRS": "حديد عز",
    "ETEL": "المصرية للاتصالات",
    "EKHO": "القابضة المصرية الكويتية (دولار)",
    "EKHOA": "القابضة المصرية الكويتية (جنيه)",
    "ORAS": "أوراسكوم كونستراكشون بي إل سي",
    "OCDI": "السادس من أكتوبر للتنمية والاستثمار (سوديك)",
    "PHDC": "بالم هيلز للتعمير",
    "HELI": "مصر الجديدة للإسكان والتعمير",
    "MNHD": "مدينة مصر للإسكان والتعمير",
    "MASR": "مدينة مصر للإسكان والتعمير",
    "EMFD": "إعمار مصر للتنمية",
    "ORHD": "أوراسكوم للتنمية مصر",
    "SKPC": "سيدي كرير للبتروكيماويات",
    "AMOC": "الإسكندرية للزيوت المعدنية (أموك)",
    "JUFO": "جهينة للصناعات الغذائية",
    "EFID": "إيديتا للصناعات الغذائية",
    "DOMT": "الصناعات الغذائية العربية (دومتي)",
    "OLFI": "عبور لاند للصناعات الغذائية",
    "POUL": "القاهرة للدواجن",
    "ISPH": "ابن سينا فارما",
    "CLHO": "مستشفيات كليوباترا",
    "RMDA": "العاشر من رمضان للصناعات الدوائية (راميدا)",
    "PHAR": "المصرية الدولية للصناعات الدوائية (إيبيكو)",
    "SPMD": "سبيد ميديكال",
    "CIRA": "القاهرة للاستثمار والتنمية العقارية",
    "ADIB": "مصرف أبو ظبي الإسلامي - مصر",
    "CIEB": "بنك كريدي أجريكول مصر",
    "QNBA": "بنك قطر الوطني الأهلي",
    "FAIT": "بنك فيصل الإسلامي المصري (جنيه)",
    "FAITA": "بنك فيصل الإسلامي المصري (دولار)",
    "HDBK": "بنك التعمير والإسكان",
    "EXPA": "البنك المصري لتنمية الصادرات",
    "CANA": "بنك قناة السويس",
    "SAUD": "بنك البركة مصر",
    "EGBE": "البنك المصري الخليجي",
    "BTFH": "بلتون القابضة",
    "CIHC": "سي آي كابيتال القابضة",
    "AIH": "العربية للاستثمارات والتنمية القابضة",
    "OFH": "أوراسكوم للاستثمار القابضة",
    "OIH": "أوراسكوم للاستثمار القابضة",
    "DSCW": "دايس للملابس الجاهزة",
    "KABO": "النصر للملابس والمنسوجات (كابو)",
    "KABL": "الكابلات الكهربائية المصرية",
    "RACC": "راية لخدمات مراكز الاتصالات",
    "RAYA": "راية القابضة للاستثمارات المالية",
    "CCAP": "القلعة للاستثمارات المالية",
    "EGAL": "مصر للألومنيوم",
    "IRON": "الحديد والصلب المصرية",
    "BINV": "بي إنفستمنتس القابضة",
    "VALU": "فاليو للتمويل الاستهلاكي",
    "ACTF": "أكت فاينانشال للاستشارات",
    "TAQA": "طاقة عربية",
    "MOIL": "ماريدايف والخدمات الملاحية",
    "ZMID": "زهراء المعادي للاستثمار والتعمير",
    "ELSH": "الشمس للإسكان والتعمير",
    "UNIT": "المتحدة للإسكان والتعمير",
    "MENA": "مينا للاستثمار السياحي والعقاري",
    "PRDC": "بايونيرز بروبرتيز للتنمية العمرانية",
    "UEGC": "الصعيد العامة للمقاولات",
    "ELKA": "القاهرة للإسكان والتعمير",
    "GBCO": "جي بي كورب (غبور أوتو)",
    "MTIE": "إم إم جروب للصناعة والتجارة العالمية",
    "MPRC": "المصرية لمدينة الإنتاج الإعلامي",
    "ATLC": "التوفيق للتأجير التمويلي",
    "ISMQ": "الإسماعيلية الوطنية للصناعات الغذائية (فوديكو)",
    "TANM": "تنمية للاستثمار العقاري",
    "AREH": "المصرية للمنتجعات السياحية",
    "ICEN": "إيكون - الصناعات الهندسية المعمارية",
    "EGTS": "المصرية للمنتجعات السياحية",
    "ALCN": "الإسكندرية لتداول الحاويات والبضائع",
    "CSAG": "القناة للتوكيلات الملاحية",
    "ETRS": "المصرية لخدمات النقل (إيجيترانس)",
    "MILS": "مطاحن شمال القاهرة",
    "CEFM": "مطاحن مصر الوسطى",
    "ARCC": "العربية للأسمنت",
    "MCQE": "مصر للأسمنت - قنا",
    "SVCE": "أسمنت جنوب الوادي",
    "SUCE": "أسمنت السويس",
    "ACAMD": "العربية لإدارة وتطوير الأصول",
    "KRDI": "الكردي للاستثمار",
    "BOYN": "بنيان للتنمية والتجارة",
}

LEADERS_EGX_SYMBOLS = set(list(EGX_ARABIC_NAMES.keys())[:45])

# ===== Sector mapping (V11.4) =====
SECTOR_MAP = {
    "COMI": "بنوك", "ADIB": "بنوك", "CIEB": "بنوك", "QNBA": "بنوك", "FAIT": "بنوك", "FAITA": "بنوك",
    "HDBK": "بنوك", "EXPA": "بنوك", "CANA": "بنوك", "SAUD": "بنوك", "EGBE": "بنوك", "ABUK": "أسماء/بترو",
    "MFPC": "أسماء/بترو", "SWDY": "صناعة", "EAST": "استهلاكي", "EFIH": "مالية", "FWRY": "تقنية",
    "ESRS": "حديد/صلب", "ETEL": "اتصالات", "EKHO": "قابضة", "EKHOA": "قابضة", "ORAS": "بناء",
    "OCDI": "عقار", "PHDC": "عقار", "HELI": "عقار", "MNHD": "عقار", "MASR": "عقار", "EMFD": "عقار",
    "ORHD": "عقار", "SKPC": "بتروكيماويات", "AMOC": "بتروكيماويات", "JUFO": "غذائي", "EFID": "غذائي",
    "DOMT": "غذائي", "OLFI": "غذائي", "POUL": "غذائي", "ISPH": "دواء", "CLHO": "صحة",
    "RMDA": "دواء", "PHAR": "دواء", "SPMD": "صحة", "CIRA": "عقار", "BTFH": "مالية",
    "CIHC": "مالية", "DSCW": "ملابس", "KABO": "ملابس", "KABL": "كابلات", "RACC": "تقنية",
    "RAYA": "مالية", "CCAP": "مالية", "EGAL": "ألمنيوم", "IRON": "حديد/صلب", "BINV": "مالية",
    "VALU": "مالية", "ACTF": "مالية", "TAQA": "طاقة", "MOIL": "ملاحة", "ZMID": "عقار",
    "ELSH": "عقار", "UNIT": "عقار", "MENA": "سياحة", "PRDC": "عقار", "UEGC": "بناء",
    "ELKA": "عقار", "GBCO": "سيارات", "MTIE": "تجزئة", "MPRC": "إعلام", "ATLC": "تأجير",
    "ISMQ": "غذائي", "TANM": "عقار", "AREH": "سياحة", "ICEN": "بناء", "EGTS": "سياحة",
    "ALCN": "ملاحة", "CSAG": "ملاحة", "ETRS": "نقل", "MILS": "غذائي", "CEFM": "غذائي",
    "ARCC": "أسمنت", "MCQE": "أسمنت", "SVCE": "أسمنت", "SUCE": "أسمنت", "ACAMD": "مالية",
    "KRDI": "مالية", "BOYN": "مالية", "TMGH": "عقار", "HRHO": "مالية", "IDRE": "عقار",
    "ENGC": "بناء", "EEII": "Industrial", "ARAB": "مالية", "FERC": "طاقة", "BONY": "مالية",
    "GOLD": "معادن", "SILVER": "معادن", "OIL": "بترول", "BRENT": "بترول", "NATGAS": "غاز",
    "COPPER": "معادن", "PLATINUM": "معادن",
}

def get_sector(sym):
    return SECTOR_MAP.get(sym.upper().replace(".CA", "").strip(), "أخرى")


# ===== معادن و بترول (Commodities) — V11.4 =====
COMMODITIES = {
    "GOLD":   ("ذهب (Gold)", "GC=F"),
    "SILVER": ("فضة (Silver)", "SI=F"),
    "OIL":    ("نفط خام (WTI)", "CL=F"),
    "BRENT":  ("نفط برنت (Brent)", "BZ=F"),
    "NATGAS": ("غاز طبيعي (Natural Gas)", "NG=F"),
    "COPPER": ("نحاس (Copper)", "HG=F"),
    "PLATINUM": ("بلاتين (Platinum)", "PL=F"),
}

# إضافة أسماء المعادن إلى قاموس الأسماء (للـ thndr_parser)
for _cs, (_cn, _) in COMMODITIES.items():
    EGX_ARABIC_NAMES[_cs] = _cn


def get_friendly_stock_name(sym: str, fallback_desc: str = "") -> str:
    clean = sym.upper().replace(".CA", "").strip()
    if clean in EGX_ARABIC_NAMES:
        return EGX_ARABIC_NAMES[clean]
    if fallback_desc and fallback_desc.strip():
        return fallback_desc.strip()
    return f"شركة {clean} (البورصة المصرية)"

# ==========================================
# قارئ مستندات ثاندر المدمج (PDF / Excel / CSV)
# ==========================================
try:
    from thndr_parser import parse_thndr_files
except ImportError:
    _ARABIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")

    def _norm_thndr_txt(txt: str) -> str:
        return txt.translate(_ARABIC_DIGITS).replace(",", "").replace("،", "")

    def _match_thndr_sym(line_or_doc: str, known_names: dict) -> str:
        upper_txt = line_or_doc.upper()
        for sym in known_names.keys():
            if re.search(rf"(?<![A-Z0-9]){re.escape(sym)}(?:\.CA)?(?![A-Z0-9])", upper_txt):
                return sym
        for sym, ar_name in known_names.items():
            clean_ar = re.sub(r"\(.*?\)", "", ar_name).strip()
            if len(clean_ar) >= 5 and clean_ar in line_or_doc:
                return sym
        m_ca = re.search(r"\b([A-Z]{3,5})\.CA\b", upper_txt)
        return m_ca.group(1) if m_ca else ""

    def parse_thndr_files(uploaded_files, known_names: dict) -> list:
        extracted_ops = []
        for up in uploaded_files:
            fname = up.name.lower()
            if fname.endswith(".pdf"):
                try:
                    from pypdf import PdfReader
                    reader = PdfReader(io.BytesIO(up.read()))
                    full_text = "\n".join([page.extract_text() or "" for page in reader.pages])
                    norm_txt = _norm_thndr_txt(full_text)
                    lines = [ln.strip() for ln in norm_txt.splitlines() if ln.strip()]

                    doc_side = "شراء (Buy)"
                    if re.search(r"\b(SELL|SALE)\b|بيع|أمر بيع|عملية بيع", norm_txt, re.IGNORECASE):
                        if not re.search(r"\b(BUY|PURCHASE)\b|شراء|أمر شراء", norm_txt, re.IGNORECASE):
                            doc_side = "بيع (Sell)"

                    doc_sym = _match_thndr_sym(norm_txt, known_names)
                    found_in_lines = False
                    for ln in lines:
                        ln_sym = _match_thndr_sym(ln, known_names)
                        if not ln_sym:
                            continue
                        ln_side = doc_side
                        if re.search(r"\bSELL\b|بيع", ln, re.IGNORECASE):
                            ln_side = "بيع (Sell)"
                        elif re.search(r"\bBUY\b|شراء", ln, re.IGNORECASE):
                            ln_side = "شراء (Buy)"

                        nums = [float(x) for x in re.findall(r"\b\d+(?:\.\d+)?\b", ln)]
                        valid_nums = [n for n in nums if 0.05 <= n <= 5000000 and n not in [2024, 2025, 2026, 2027]]
                        if len(valid_nums) >= 2:
                            int_cands = [n for n in valid_nums if float(n).is_integer() and 1 <= n <= 1000000]
                            price_cands = [n for n in valid_nums if not float(n).is_integer() and 0.05 <= n <= 5000]
                            qty = int(int_cands[0]) if int_cands else int(valid_nums[0])
                            price = float(price_cands[0]) if price_cands else float(valid_nums[1])
                            if qty > 0 and price > 0:
                                extracted_ops.append({
                                    "المصدر": up.name, "العملية": ln_side, "الرمز": ln_sym,
                                    "اسم الشركة": known_names.get(ln_sym, ln_sym),
                                    "الكمية": qty, "السعر": round(price, 4),
                                })
                                found_in_lines = True

                    if not found_in_lines and doc_sym:
                        m_qty = re.search(r"(?:Quantity|Qty|Shares|الكمية|عدد الأسهم)\s*[:\-]?\s*(\d+)", norm_txt, re.IGNORECASE)
                        m_prc = re.search(r"(?:Execution Price|Price|Avg Price|سعر التنفيذ|السعر)\s*[:\-]?\s*(\d+(?:\.\d+)?)", norm_txt, re.IGNORECASE)
                        qty = int(m_qty.group(1)) if m_qty else 0  # V11.5: مفيش كمية افتراضية — لازم تدخلها في الجدول
                        price = float(m_prc.group(1)) if m_prc else 0.0
                        if price > 0:
                            extracted_ops.append({
                                "المصدر": up.name, "العملية": doc_side, "الرمز": doc_sym,
                                "اسم الشركة": known_names.get(doc_sym, doc_sym),
                                "الكمية": qty, "السعر": round(price, 4),
                            })
                except Exception:
                    pass
            elif fname.endswith((".csv", ".xlsx", ".xls")):
                try:
                    df_in = pd.read_csv(up) if fname.endswith(".csv") else pd.read_excel(up)
                    for _, row in df_in.iterrows():
                        row_str = " ".join([str(v) for v in row.values if pd.notna(v)])
                        sym = _match_thndr_sym(row_str, known_names)
                        if not sym:
                            continue
                        side = "بيع (Sell)" if re.search(r"\bSELL\b|بيع", row_str, re.IGNORECASE) else "شراء (Buy)"
                        qty, price = 0, 0.0
                        for col in df_in.columns:
                            cl = str(col).lower()
                            val = row[col]
                            if pd.isna(val):
                                continue
                            if any(k in cl for k in ["qty", "quantity", "shares", "كمية", "الكمية"]):
                                qty = int(float(str(val).replace(",", "")))
                            elif any(k in cl for k in ["price", "avg", "سعر", "السعر"]):
                                price = float(str(val).replace(",", ""))
                        if qty > 0 and price > 0:
                            extracted_ops.append({
                                "المصدر": up.name, "العملية": side, "الرمز": sym,
                                "اسم الشركة": known_names.get(sym, sym),
                                "الكمية": qty, "السعر": round(price, 4),
                            })
                except Exception:
                    pass
        return extracted_ops

# ==========================================
# التوقيت وحالة جلسة البورصة المصرية
# ==========================================
def get_cairo_now() -> datetime:
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo("Africa/Cairo"))
    except Exception:
        return datetime.now(timezone(timedelta(hours=2)))

def get_egx_session_metrics() -> dict:
    now = get_cairo_now()
    wd = now.weekday()  # الأحد=6، الإثنين=0، الثلاثاء=1، الأربعاء=2، الخميس=3
    is_trading_day = core.is_trading_day(now.date())
    start_dt = now.replace(hour=10, minute=0, second=0, microsecond=0)
    end_dt = now.replace(hour=14, minute=30, second=0, microsecond=0)
    total_mins = 270.0

    if not is_trading_day:
        return {"is_open": False, "progress": 1.0, "badge": ("🔴 عطلة أسبوعية (EGX مغلقة)" if wd not in core.TRADING_WEEKDAYS else "🔴 إجازة رسمية (EGX مغلقة)")}
    if now < start_dt:
        return {"is_open": False, "progress": 1.0, "badge": "🟡 قبل افتتاح الجلسة (10:00 ص)"}
    if start_dt <= now <= end_dt:
        elapsed = max(5.0, (now - start_dt).total_seconds() / 60.0)
        prog = min(1.0, max(0.12, elapsed / total_mins))
        return {"is_open": True, "progress": prog, "badge": f"🟢 الجلسة مفتوحة ({prog*100:.0f}%)"}
    return {"is_open": False, "progress": 1.0, "badge": "⚪ الجلسة مغلقة (إغلاق اليوم)"}

# ==========================================
# إدارة الأسرار والمزامنة السحابية (Supabase)
# ==========================================
def get_secret_safe(key_name: str, default_val: str = "") -> str:
    try:
        if key_name in st.secrets:
            return str(st.secrets[key_name]).strip()
    except Exception:
        pass
    return os.environ.get(key_name, default_val).strip()

def sb_signup(email: str, password: str):
    sb_url = get_secret_safe("SUPABASE_URL") or st.session_state.get("sb_url_val", "")
    if not sb_url:
        return False, "Missing SUPABASE_URL"
    url = sb_url.rstrip("/") + "/auth/v1/signup"
    payload = json.dumps({"email": email, "password": password}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json", "apikey": get_secret_safe("SUPABASE_KEY") or st.session_state.get("sb_key_val", "")}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        if data.get("access_token"):
            st.session_state["auth_token"] = data["access_token"]
            st.session_state["auth_user_id"] = (data.get("user") or {}).get("id")
            st.session_state["auth_email"] = email
            return True, "✅ تم إنشاء الحساب وتسجيل الدخول!"
        if data.get("user"):
            return True, "✅ تم إنشاء الحساب. يرجى تأكيد البريد الإلكتروني ثم تسجيل الدخول."
        return False, str(data)
    except urllib.error.HTTPError as e:
        try:
            err = json.loads(e.read().decode("utf-8"))
            return False, err.get("msg") or err.get("error_description") or str(err)
        except Exception:
            return False, str(e)
    except Exception as e:
        return False, str(e)


def sb_login(email: str, password: str):
    sb_url = get_secret_safe("SUPABASE_URL") or st.session_state.get("sb_url_val", "")
    sb_key = get_secret_safe("SUPABASE_KEY") or st.session_state.get("sb_key_val", "")
    if not sb_url or not sb_key:
        return False, "Missing SUPABASE_URL/KEY"
    url = sb_url.rstrip("/") + "/auth/v1/token?grant_type=password"
    payload = json.dumps({"email": email, "password": password}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json", "apikey": sb_key}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        if data.get("access_token"):
            _store_auth_session(data)
            st.session_state["auth_email"] = email
            return True, "✅ تم تسجيل الدخول!"
        return False, data.get("error_description") or str(data)
    except urllib.error.HTTPError as e:
        try:
            err = json.loads(e.read().decode("utf-8"))
            return False, err.get("msg") or err.get("error_description") or str(err)
        except Exception:
            return False, str(e)
    except Exception as e:
        return False, str(e)


def _store_auth_session(data: dict):
    st.session_state["auth_token"] = data["access_token"]
    st.session_state["auth_refresh"] = data.get("refresh_token", "")
    st.session_state["auth_expires_at"] = time.time() + float(data.get("expires_in", 3600))
    st.session_state["auth_user_id"] = (data.get("user") or {}).get("id") or st.session_state.get("auth_user_id")


def refresh_auth_if_needed(force: bool = False) -> bool:
    """يجدد التوكن قبل ما يخلص بدقيقتين (أو فوراً لو force). يرجّع False لو التجديد فشل."""
    if not st.session_state.get("auth_refresh"):
        return False
    if not force and time.time() < float(st.session_state.get("auth_expires_at", 0)) - 120:
        return True
    sb_url = get_secret_safe("SUPABASE_URL") or st.session_state.get("sb_url_val", "")
    sb_key = get_secret_safe("SUPABASE_KEY") or st.session_state.get("sb_key_val", "")
    req = urllib.request.Request(
        sb_url.rstrip("/") + "/auth/v1/token?grant_type=refresh_token",
        data=json.dumps({"refresh_token": st.session_state["auth_refresh"]}).encode("utf-8"),
        headers={"Content-Type": "application/json", "apikey": sb_key}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        if data.get("access_token"):
            _store_auth_session(data)
            return True
    except Exception as e:
        print(f"[Auth Refresh Error]: {e}")
    sb_logout()
    return False


def sb_logout():
    for k in ["auth_token", "auth_user_id", "auth_email", "auth_refresh", "auth_expires_at"]:
        st.session_state.pop(k, None)


def is_authenticated() -> bool:
    return bool(st.session_state.get("auth_token") and st.session_state.get("auth_user_id"))


def get_auth_headers():
    refresh_auth_if_needed()
    sb_key = get_secret_safe("SUPABASE_KEY") or st.session_state.get("sb_key_val", "")
    token = st.session_state.get("auth_token") or sb_key
    return {
        "apikey": sb_key,
        "Authorization": "Bearer " + token,
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


def has_permanent_secrets() -> bool:
    return bool(get_secret_safe("SUPABASE_URL") and get_secret_safe("SUPABASE_KEY"))

def _get_sb_headers():
    sb_url = st.session_state.get("sb_url_val") or get_secret_safe("SUPABASE_URL")
    sb_key = st.session_state.get("sb_key_val") or get_secret_safe("SUPABASE_KEY")
    if not sb_url or not sb_key:
        return None, None
    headers = {
        "apikey": sb_key,
        "Authorization": f"Bearer {sb_key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }
    return sb_url.rstrip("/"), headers

def _sb_request(method: str, path: str, payload=None, extra_headers=None):
    base_url = st.session_state.get("sb_url_val") or get_secret_safe("SUPABASE_URL")
    base_url = base_url.rstrip("/") if base_url else ""
    if not base_url:
        return False, "Missing SUPABASE_URL"
    sb_key = st.session_state.get("sb_key_val") or get_secret_safe("SUPABASE_KEY")
    headers = get_auth_headers() if is_authenticated() else {
        "apikey": sb_key,
        "Authorization": "Bearer " + sb_key,
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }
    if extra_headers:
        headers.update(extra_headers)
    if not sb_key:
        return False, "Missing SUPABASE_KEY"
    url = f"{base_url}/rest/v1/{path}"
    data_bytes = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data_bytes, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            raw = resp.read().decode("utf-8")
            return True, (json.loads(raw) if raw else [])
    except urllib.error.HTTPError as e:
        if e.code == 401 and not extra_headers_retry_flag(extra_headers) and refresh_auth_if_needed(force=True):
            return _sb_request(method, path, payload, {**(extra_headers or {}), "X-Retry": "1"})
        return False, str(e)
    except Exception as e:
        return False, str(e)


def extra_headers_retry_flag(h) -> bool:
    return bool(h and h.get("X-Retry"))

def test_supabase_connection():
    ok, res = _sb_request("GET", "portfolio?select=symbol&limit=1")
    if ok:
        return True, "✅ تم الاتصال بسحابة Supabase بنجاح!"
    return False, f"❌ تعذر الاتصال بـ Supabase: {res}"

LOCAL_PORT_FILE = "portfolio_cache.json"
LOCAL_CLOSED_FILE = "closed_trades_cache.json"
LOCAL_TG_LOG_FILE = "tg_log_cache.json"

def _load_local_json(path: str, default):
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return default

def _save_local_json(path: str, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def _load_local_portfolio_file():
    return _load_local_json(LOCAL_PORT_FILE, [])

def _save_local_portfolio_cache(items: list):
    _save_local_json(LOCAL_PORT_FILE, items)

def load_portfolio(force_cloud_refresh: bool = False):
    if not force_cloud_refresh and "cached_portfolio" in st.session_state:
        return st.session_state["cached_portfolio"], st.session_state.get("sb_connected", False)
    q = "portfolio?select=*&order=symbol.asc"
    if is_authenticated():
        q += "&user_id=eq." + str(st.session_state.get("auth_user_id"))
    ok, data = _sb_request("GET", q)
    if ok and isinstance(data, list):
        st.session_state["cached_portfolio"] = data
        st.session_state["sb_connected"] = True
        _save_local_portfolio_cache(data)
        return data, True
    local_data = _load_local_portfolio_file()
    st.session_state["cached_portfolio"] = local_data
    st.session_state["sb_connected"] = False
    return local_data, False

def upsert_portfolio_item(item: dict):
    sym = item["symbol"].upper().replace(".CA", "").strip()
    item["symbol"] = sym
    if is_authenticated() and "user_id" not in item:
        item["user_id"] = st.session_state.get("auth_user_id")
    ok, err_msg = _sb_request(
        "POST",
        "portfolio?on_conflict=symbol",
        payload=[item],
        extra_headers={"Prefer": "resolution=merge-duplicates,return=representation"}
    )
    curr = list(st.session_state.get("cached_portfolio", _load_local_portfolio_file()))
    curr = [x for x in curr if x.get("symbol", "").upper() != sym]
    curr.append(item)
    st.session_state["cached_portfolio"] = curr
    _save_local_portfolio_cache(curr)
    if ok:
        st.session_state["sb_connected"] = True
        return True, "☁️ محفوظ سحابياً في Supabase"
    return False, f"💾 محفوظ محلياً مؤقتاً ({err_msg})"

def delete_portfolio_item(symbol: str):
    sym = symbol.upper().replace(".CA", "").strip()
    ok, _ = _sb_request("DELETE", f"portfolio?symbol=eq.{urllib.parse.quote(sym)}")
    curr = [x for x in st.session_state.get("cached_portfolio", _load_local_portfolio_file()) if x.get("symbol", "").upper() != sym]
    st.session_state["cached_portfolio"] = curr
    _save_local_portfolio_cache(curr)
    return ok, ("☁️ حُذف سحابياً" if ok else "💾 حُذف محلياً")

def sync_full_portfolio_to_cloud(items: list):
    if not items:
        return False, "⚠️ المحفظة فارغة."
    ok, msg = _sb_request(
        "POST",
        "portfolio?on_conflict=symbol",
        payload=items,
        extra_headers={"Prefer": "resolution=merge-duplicates,return=representation"}
    )
    if ok:
        st.session_state["cached_portfolio"] = items
        st.session_state["sb_connected"] = True
        return True, f"✅ تم رفع {len(items)} أسهم إلى السحابة بنجاح!"
    return False, f"❌ فشل الرفع: {msg}"

def load_closed_trades(force_refresh: bool = False):
    if not force_refresh and "cached_closed" in st.session_state:
        return st.session_state["cached_closed"]
    q = "closed_trades?select=*&order=closed_at.desc"
    if is_authenticated():
        q += "&user_id=eq." + str(st.session_state.get("auth_user_id"))
    ok, data = _sb_request("GET", q)
    if ok and isinstance(data, list):
        st.session_state["cached_closed"] = data
        _save_local_json(LOCAL_CLOSED_FILE, data)
        return data
    local_c = _load_local_json(LOCAL_CLOSED_FILE, [])
    st.session_state["cached_closed"] = local_c
    return local_c

def record_closed_trade(symbol: str, shares: int, buy_price: float, sell_price: float, fee_rate: float):
    sym = symbol.upper().replace(".CA", "").strip()
    cost = shares * buy_price
    proceeds = shares * sell_price
    fees = (cost + proceeds) * fee_rate
    net_pnl = (proceeds - cost) - fees
    pnl_pct = (net_pnl / max(0.01, cost)) * 100.0
    row = {
        "symbol": sym,
        "user_id": st.session_state.get("auth_user_id") if is_authenticated() else None,
        "shares": int(shares),
        "buy_price": round(buy_price, 4),
        "sell_price": round(sell_price, 4),
        "net_pnl": round(net_pnl, 4),
        "pnl_pct": round(pnl_pct, 4),
        "closed_at": get_cairo_now().isoformat()
    }
    _sb_request("POST", "closed_trades", payload=[row])
    curr_c = list(st.session_state.get("cached_closed", _load_local_json(LOCAL_CLOSED_FILE, [])))
    curr_c.insert(0, row)
    st.session_state["cached_closed"] = curr_c
    _save_local_json(LOCAL_CLOSED_FILE, curr_c)
    delete_portfolio_item(sym)
    return net_pnl, pnl_pct

def load_sent_tg_log(today_str: str, force_refresh: bool = False) -> set:
    if not force_refresh and "cached_tg_log" in st.session_state:
        return st.session_state["cached_tg_log"]
    ok, data = _sb_request("GET", f"tg_alerts_log?alert_key=like.{today_str}*")
    if ok and isinstance(data, list):
        s = {x["alert_key"] for x in data if "alert_key" in x}
        st.session_state["cached_tg_log"] = s
        return s
    local_log = _load_local_json(LOCAL_TG_LOG_FILE, {})
    return set(local_log.get(today_str, []))

def record_sent_tg_alert(alert_key: str, time_str: str, log_set: set):
    log_set.add(alert_key)
    st.session_state["cached_tg_log"] = log_set
    _sb_request("POST", "tg_alerts_log", payload=[{"alert_key": alert_key, "sent_at": time_str}])
    today_prefix = alert_key.split("_")[0]
    local_log = _load_local_json(LOCAL_TG_LOG_FILE, {})
    day_list = set(local_log.get(today_prefix, []))
    day_list.add(alert_key)
    local_log[today_prefix] = list(day_list)
    _save_local_json(LOCAL_TG_LOG_FILE, local_log)

# ==========================================
# دوال التليجرام
# ==========================================
def send_telegram_message(token: str, chat_id: str, text_html: str):
    if not token or not chat_id:
        return False, "Missing Token or Chat ID"
    url = f"https://api.telegram.org/bot{token.strip()}/sendMessage"
    payload = json.dumps({
        "chat_id": chat_id.strip(),
        "text": text_html,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            return bool(res.get("ok")), res.get("description", "OK")
    except Exception as e:
        return False, str(e)

def detect_telegram_chat_id(token: str):
    if not token:
        return None, "أدخل Bot Token أولاً."
    url = f"https://api.telegram.org/bot{token.strip()}/getUpdates"
    try:
        with urllib.request.urlopen(url, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        for upd in reversed(data.get("result", [])):
            msg = upd.get("message") or upd.get("channel_post") or {}
            cid = msg.get("chat", {}).get("id")
            if cid:
                return str(cid), "تم العثور على Chat ID"
        return None, "افتح البوت في تليجرام واضغط Start ثم أعد المحاولة."
    except Exception as e:
        return None, f"خطأ: {e}"

# ==========================================
# سحب بيانات البورصة المصرية الحية من TradingView (شاملة Bid/Ask Size)
# ==========================================
@st.cache_data(ttl=86400, show_spinner=False)
def fetch_egx_isin_map() -> dict:
    """ISIN -> رمز السهم (فواتير ثاندر بتكتب كود ISIN مش الرمز)."""
    body = json.dumps({"markets": ["egypt"], "columns": ["name", "isin"], "range": [0, 500]}).encode("utf-8")
    try:
        req = urllib.request.Request("https://scanner.tradingview.com/egypt/scan", data=body,
                                     headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}, method="POST")
        with urllib.request.urlopen(req, timeout=12) as resp:
            raw = json.loads(resp.read().decode("utf-8"))
        out = {}
        for row in raw.get("data", []):
            d = row.get("d", [])
            if len(d) >= 2 and d[0] and d[1]:
                out[str(d[1]).upper().strip()] = str(d[0]).upper().strip()
        return out
    except Exception:
        return {}


@st.cache_data(ttl=120, show_spinner=False)
def fetch_full_egx_tv_scanner(nonce: int = 0):
    url = "https://scanner.tradingview.com/egypt/scan"
    cols = [
        "name", "description", "close", "change", "volume", "Value.Traded",
        "average_volume_10d_calc", "average_volume_30d_calc", "ATR",
        "EMA20", "EMA50", "EMA200", "RSI", "MACD.macd", "MACD.signal",
        "VWAP", "RSI|15", "MACD.macd|15", "MACD.signal|15",
        "bid", "ask", "bid_size", "ask_size", "high", "low", "open", "Perf.1M"
    ]
    body = json.dumps({
        "filter": [{"left": "type", "operation": "in_range", "right": ["stock", "dr", "fund"]}],
        "options": {"lang": "en"},
        "markets": ["egypt"],
        "symbols": {"query": {"types": []}, "tickers": []},
        "columns": cols,
        "sort": {"sortBy": "Value.Traded", "sortOrder": "desc"},
        "range": [0, 350]
    }).encode("utf-8")

    tv_map = {}
    try:
        req = urllib.request.Request(
            url, data=body,
            headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"},
            method="POST"
        )
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
            tv_map[sym] = {
                "symbol": sym,
                "name": get_friendly_stock_name(sym, str(rec.get("description") or "")),
                "close": close_p,
                "change": float(rec.get("change") or 0.0),
                "volume": float(rec.get("volume") or 0.0),
                "turnover": float(rec.get("Value.Traded") or 0.0),
                "avg_vol10": float(rec.get("average_volume_10d_calc") or 0.0),
                "avg_vol30": float(rec.get("average_volume_30d_calc") or 0.0),
                "atr": float(rec.get("ATR") or (close_p * 0.025)),
                "ema20": float(rec.get("EMA20") or close_p),
                "ema50": float(rec.get("EMA50") or close_p),
                "ema200": float(rec.get("EMA200") or close_p),
                "rsi": float(rec.get("RSI") or 50.0),
                "macd": float(rec.get("MACD.macd") or 0.0),
                "macds": float(rec.get("MACD.signal") or 0.0),
                "vwap": (float(rec.get("VWAP")) if rec.get("VWAP") not in (None, 0, "0", "") else close_p),
                "rsi15": float(rec.get("RSI|15") or 50.0),
                "macd15": float(rec.get("MACD.macd|15") or 0.0),
                "macds15": float(rec.get("MACD.signal|15") or 0.0),
                "bid": float(rec.get("bid") or 0.0),
                "ask": float(rec.get("ask") or 0.0),
                "bid_size": float(rec.get("bid_size") or 0.0),
                "ask_size": float(rec.get("ask_size") or 0.0),
                "high": float(rec.get("high") or close_p),
                "low": float(rec.get("low") or close_p),
                "open": float(rec.get("open") or close_p),
                "perf_1m": float(rec.get("Perf.1M") or 0.0),
            }
    except Exception:
        pass

    return tv_map, get_cairo_now().strftime("%H:%M:%S")

# ==========================================
# محرك التدفق اللحظي وتقييم الفرص
# ==========================================
def analyze_intraday_flow(q: dict, fallback_close: float = 0.0, session_progress: float = 1.0) -> dict:
    close = float(q.get("close") or fallback_close or 0.0)
    _v = q.get("vwap")
    vwap = float(_v) if _v not in (None, 0, "0", "") else (close or 0.0)
    rsi15 = float(q.get("rsi15") or 50.0)
    macd15 = float(q.get("macd15") or 0.0)
    macds15 = float(q.get("macds15") or 0.0)
    high = float(q.get("high") or close)
    low = float(q.get("low") or close)
    vol = float(q.get("volume") or 0.0)
    avg_v = float(q.get("avg_vol10") or q.get("avg_vol30") or 0.0)
    bid = float(q.get("bid") or 0.0)
    ask = float(q.get("ask") or 0.0)

    vwap_diff_pct = ((close - vwap) / vwap * 100.0) if vwap > 0 else 0.0
    rng = max(1e-6, high - low)
    clv_pct = ((close - low) / rng * 100.0) if high > low else 50.0
    expected_vol = avg_v * max(0.12, session_progress)
    rel_vol = (vol / expected_vol) if expected_vol > 0 else 1.0

    spread_pct = ((ask - bid) / close * 100.0) if (bid > 0 and ask > bid and close > 0) else 0.0
    ba_pressure = f"طلب {bid:.4f} / عرض {ask:.4f}" if (bid > 0 and ask > 0) else "غير متاح خارج الجلسة"

    f_score = 0
    reasons = []

    if vwap_diff_pct >= 0.4:
        f_score += 30
        reasons.append(f"السعر يتداول أعلى متوسط السيولة VWAP بنسبة +{vwap_diff_pct:.2f}% (سيطرة للمشتري).")
    elif vwap_diff_pct > 0:
        f_score += 15
        reasons.append(f"السعر متماسك أعلى VWAP (+{vwap_diff_pct:.2f}%).")
    elif vwap_diff_pct <= -0.4:
        f_score -= 30
        reasons.append(f"السعر يتداول أسفل VWAP بنسبة {vwap_diff_pct:.2f}% (ضغط بيعي لحظي).")

    if rsi15 >= 58:
        f_score += 20
        reasons.append(f"زخم 15 دقيقة قوي (RSI = {rsi15:.1f}).")
    elif rsi15 <= 42:
        f_score -= 20
        reasons.append(f"ضعف زخم 15 دقيقة (RSI = {rsi15:.1f}).")

    if macd15 > macds15:
        f_score += 15
        reasons.append("تقاطع MACD إيجابي على فريم 15 دقيقة.")
    elif macd15 < macds15:
        f_score -= 15
        reasons.append("تقاطع MACD سلبي على فريم 15 دقيقة.")

    if clv_pct >= 70:
        f_score += 15
        reasons.append(f"إغلاق قريب من قمة الجلسة (CLV = {clv_pct:.0f}%).")
    elif clv_pct <= 30:
        f_score -= 15
        reasons.append(f"إغلاق قريب من قاع الجلسة (CLV = {clv_pct:.0f}%).")

    if rel_vol >= 1.3 and f_score > 0:
        f_score += 20
        reasons.append(f"وتيرة سيولة مرتفعة ({rel_vol:.2f}x من المعتاد في نفس التوقيت).")

    f_score = max(-100, min(100, f_score))
    if f_score >= 35:
        verdict, short_v, badge_cls = "🟢 تدفق شرائي مؤسسي قوي", "🟢 شراء لحظي", "badge-bull"
        hint = "السيولة اللحظية في صف الصعود؛ التزم بوقف الخسارة المتحرك ولا تطارد فجوات بعيدة."
    elif f_score >= 10:
        verdict, short_v, badge_cls = "🟢 ميل صعودي وتجميع هادئ", "🟢 إيجابي", "badge-bull"
        hint = "السهم يحافظ على متوسط السيولة VWAP؛ مناسب للاحتفاظ أو الشراء التدريجي قرب الدعوم."
    elif f_score <= -35:
        verdict, short_v, badge_cls = "🔴 ضغط بيعي وتصريف لحظي", "🔴 بيعي", "badge-bear"
        hint = "كسر VWAP مع زخم سلبي؛ تجنب التعديل حالياً والتزم بمستوى وقف الخسارة."
    else:
        verdict, short_v, badge_cls = "🟡 توازن / ترقب سيولة", "🟡 محايد", "badge-warn"
        hint = "حركة عرضية متوازنة؛ انتظر اختراق VWAP بسيولة واضحة قبل زيادة المراكز."

    return {
        "vwap": round(vwap, 4),
        "vwap_diff_pct": round(vwap_diff_pct, 4),
        "rsi15": round(rsi15, 1),
        "macd15": round(macd15, 4),
        "macds15": round(macds15, 4),
        "clv_pct": round(clv_pct, 1),
        "rel_vol": round(rel_vol, 4),
        "spread_pct": round(spread_pct, 4),
        "ba_pressure": ba_pressure,
        "flow_score": f_score,
        "verdict": verdict,
        "short_verdict": short_v,
        "badge_cls": badge_cls,
        "reasons": reasons or ["بيانات التداول اللحظية في النطاق الطبيعي."],
        "action_hint": hint
    }

# V11.5: نفس الدالة بالظبط في البوت — مصدرها egx_core.py
evaluate_smart_stop_loss = core.evaluate_smart_stop_loss


def estimate_time_horizon(atr: float, close: float, rvol: float = 1.0, score: int = 50) -> str:
    """تقدير أفق زمني (أيام تداول) حسب ATR% وRVOL والسكور — V11.4."""
    if close <= 0 or atr <= 0:
        return "— (لا توجد بيانات ATR)"
    atr_pct = (atr / close) * 100.0
    # base days for TP1
    if atr_pct >= 4.0:
        base_lo, base_hi = 2, 4
    elif atr_pct >= 2.5:
        base_lo, base_hi = 3, 6
    elif atr_pct >= 1.5:
        base_lo, base_hi = 5, 10
    else:
        base_lo, base_hi = 7, 14
    # adjust for RVOL (high volume -> faster)
    if rvol >= 2.0:
        base_lo = max(1, int(base_lo * 0.7))
        base_hi = max(2, int(base_hi * 0.7))
    elif rvol >= 1.3:
        base_lo = max(1, int(base_lo * 0.85))
        base_hi = max(2, int(base_hi * 0.85))
    # adjust for score (high score -> faster)
    if score >= 75:
        base_lo = max(1, int(base_lo * 0.8))
        base_hi = max(2, int(base_hi * 0.8))
    tp1_lo, tp1_hi = base_lo, base_hi
    tp2_lo, tp2_hi = int(base_lo * 1.6), int(base_hi * 1.6)
    tp3_lo, tp3_hi = int(base_lo * 2.5), int(base_hi * 2.5)
    tp2_lo = max(tp2_lo, tp1_hi + 1)
    tp3_lo = max(tp3_lo, tp2_hi + 1)
    return f"TP1: {tp1_lo}-{tp1_hi} أيام | TP2: {tp2_lo}-{tp2_hi} يوم | TP3: {tp3_lo}-{tp3_hi} يوم (ATR {atr_pct:.2f}%)"


@st.cache_data(ttl=900, show_spinner=False)
def fetch_commodities() -> dict:
    """سحب بيانات المعادن والبترول من Yahoo Finance (V11.4). يُعيد dict متوافق مع tv_map."""
    out = {}
    for sym, (name, ticker) in COMMODITIES.items():
        try:
            df = yf.download(ticker, period="1y", interval="1d", progress=False, auto_adjust=True)
            if df is None or df.empty or len(df) < 30:
                continue
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            df = df.dropna(subset=["Close", "High", "Low", "Open", "Volume"])
            if df.empty or len(df) < 30:
                continue
            close = float(df["Close"].iloc[-1])
            prev_close = float(df["Close"].iloc[-2]) if len(df) >= 2 else close
            change = ((close - prev_close) / prev_close * 100.0) if prev_close > 0 else 0.0
            vol = float(df["Volume"].iloc[-1])
            vol_sma = float(df["Volume"].tail(10).mean()) if len(df) >= 10 else vol
            avg_vol10 = float(df["Volume"].tail(10).mean()) if len(df) >= 10 else vol
            avg_vol30 = float(df["Volume"].tail(30).mean()) if len(df) >= 30 else vol
            high = float(df["High"].iloc[-1])
            low = float(df["Low"].iloc[-1])
            open_p = float(df["Open"].iloc[-1])
            # ATR(14)
            tr = pd.concat([
                df["High"] - df["Low"],
                (df["High"] - df["Close"].shift(1)).abs(),
                (df["Low"] - df["Close"].shift(1)).abs(),
            ], axis=1).max(axis=1)
            atr = float(tr.tail(14).mean()) if len(tr) >= 14 else (close * 0.02)
            # EMA
            ema20 = float(df["Close"].ewm(span=20, adjust=False).mean().iloc[-1])
            ema50 = float(df["Close"].ewm(span=50, adjust=False).mean().iloc[-1])
            ema200 = float(df["Close"].ewm(span=200, adjust=False).mean().iloc[-1]) if len(df) >= 200 else ema50
            # RSI(14) daily
            delta = df["Close"].diff()
            gain = delta.where(delta > 0, 0.0).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0.0)).rolling(14).mean()
            rs = gain / loss.replace(0, np.nan)
            rsi = float(100 - (100 / (1 + rs)).iloc[-1]) if pd.notna(rs.iloc[-1]) else 50.0
            # Perf 1M
            if len(df) >= 22:
                perf_1m = (close / float(df["Close"].iloc[-22]) - 1.0) * 100.0
            else:
                perf_1m = change
            # VWAP (daily approx = close, but use typical price * volume weighted last 20)
            try:
                tp = (df["High"] + df["Low"] + df["Close"]) / 3.0
                vwap = float((tp * df["Volume"]).tail(20).sum() / df["Volume"].tail(20).sum()) if df["Volume"].tail(20).sum() > 0 else close
            except Exception:
                vwap = close
            turnover = close * vol
            expected_vol = avg_vol10 * 1.0
            rvol = (vol / expected_vol) if expected_vol > 0 else 1.0
            out[sym] = {
                "symbol": sym,
                "name": name,
                "close": close,
                "change": round(change, 4),
                "volume": vol,
                "turnover": turnover,
                "avg_vol10": avg_vol10,
                "avg_vol30": avg_vol30,
                "atr": atr,
                "ema20": ema20,
                "ema50": ema50,
                "ema200": ema200,
                "rsi": rsi,
                "macd": 0.0,
                "macds": 0.0,
                "vwap": vwap,
                "rsi15": rsi,
                "macd15": 0.0,
                "macds15": 0.0,
                "bid": 0.0,
                "ask": 0.0,
                "bid_size": 0.0,
                "ask_size": 0.0,
                "high": high,
                "low": low,
                "open": open_p,
                "perf_1m": perf_1m,
                "_is_commodity": True,
            }
        except Exception as e:
            print(f"[Commodity Fetch Error] {sym}: {e}")
            continue
    return out


def score_stock_from_tv(q: dict, market_median_perf1m: float, capital: float, risk_pct: float, fee_rate: float, session_progress: float) -> dict:
    sym = q["symbol"]
    close = q["close"]
    pct_change = q["change"]
    atr14 = max(0.01, q["atr"])
    ema20, ema50, ema200 = q["ema20"], q["ema50"], q["ema200"]
    vol = q["volume"]
    avg_vol = q["avg_vol10"] if q["avg_vol10"] > 0 else q["avg_vol30"]
    expected_vol = avg_vol * max(0.12, session_progress)
    pace_rvol = (vol / expected_vol) if expected_vol > 0 else 1.0
    effective_turnover_m = (q["turnover"] if q["turnover"] > 0 else (close * vol)) / 1e6
    rs_alpha = q["perf_1m"] - market_median_perf1m

    flow_res = analyze_intraday_flow(q, fallback_close=close, session_progress=session_progress)

    pts_trend, pts_wyckoff, pts_intraday = 0, 0, 0
    tags = []
    setup_type = "📊 متابعة فنية"

    if close > ema20 > ema50:
        pts_trend += 16
        tags.append("ترتيب متوسطات صاعد")
    elif close > ema50:
        pts_trend += 9
    if close > ema200:
        pts_trend += 8
    if rs_alpha >= 3.0:
        pts_trend += 6
        tags.append(f"قوة نسبية (+{rs_alpha:.1f}%)")

    if pace_rvol >= 1.8 and pct_change > 0.5:
        pts_wyckoff = 35
        tags.append(f"انفجار سيولة ({pace_rvol:.1f}x)")
        setup_type = "🔥 تدفق سيولة"
    elif pace_rvol >= 1.2 and pct_change > 0:
        pts_wyckoff = 22
        tags.append(f"سيولة نشطة ({pace_rvol:.1f}x)")
        setup_type = "📈 زخم سيولة"
    elif session_progress >= 0.7 and pct_change < 0 and 0 < pace_rvol <= 0.65 and close > ema50:
        pts_wyckoff = 25
        tags.append(f"جفاف عرض ({pace_rvol:.1f}x)")
        setup_type = "🎯 تصحيح بلا بائع"

    vwap_diff = flow_res["vwap_diff_pct"]
    if vwap_diff >= 0.4:
        pts_intraday += 15
        tags.append(f"فوق VWAP (+{vwap_diff:.1f}%)")
    elif vwap_diff > 0:
        pts_intraday += 8
    if flow_res["rsi15"] >= 56:
        pts_intraday += 8
    elif flow_res["rsi15"] >= 50:
        pts_intraday += 4
    if flow_res["macd15"] > flow_res["macds15"]:
        pts_intraday += 5
    if flow_res["clv_pct"] >= 68.0:
        pts_intraday += 7

    score = min(100, pts_trend + pts_wyckoff + pts_intraday)
    entry = close
    stop_loss = max(0.01, entry - (2.0 * atr14))
    risk_per_share = max(0.01, entry - stop_loss)
    tp1 = entry + (1.618 * risk_per_share)
    tp2 = entry + (2.618 * risk_per_share)
    tp3 = entry + (3.618 * risk_per_share)

    risk_amount = capital * (risk_pct / 100.0)
    shares = int(risk_amount // risk_per_share) if risk_per_share > 0 else 0
    position_value = shares * entry
    net_profit_tp1 = (shares * (tp1 - entry)) - ((position_value + shares * tp1) * fee_rate)

    return {
        "الرمز": sym,
        "اسم الشركة": q["name"],
        "Ticker": f"{sym}.CA",
        "السكور": score,
        "نوع الإشارة": setup_type,
        "الرأي اللحظي": flow_res["short_verdict"],
        "الإغلاق": round(close, 4),
        "ATR14": round(atr14, 4),
        "EMA20": round(ema20, 4),
        "التغير %": round(pct_change, 4),
        "الفوليوم": round(pace_rvol, 4),
        "فرق VWAP %": round(vwap_diff, 4),
        "القوة النسبية %": round(rs_alpha, 1),
        "السيولة (مليون)": round(effective_turnover_m, 4),
        "الوقف (2xATR)": round(stop_loss, 4),
        "TP1": round(tp1, 4),
        "TP2": round(tp2, 4),
        "TP3": round(tp3, 4),
        "الأسهم": shares,
        "قيمة الصفقة": round(position_value, 0),
        "صافي TP1": round(net_profit_tp1, 0),
        "التشخيص الفني": " | ".join(tags) if tags else "حركة عرضية / تجميع هادئ",
        "score_parts": {
            "الاتجاه اليومي (30)": pts_trend,
            "وتيرة السيولة ووايكوف (35)": pts_wyckoff,
            "التدفق اللحظي VWAP (35)": pts_intraday
        },
        "intraday_flow": flow_res,
        "tv_raw": q,
        "TradingView": (f"https://www.tradingview.com/chart/?symbol=COMEX:{sym}" if q.get("_is_commodity") else f"https://www.tradingview.com/chart/?symbol=EGX:{sym}"),
        "is_commodity": bool(q.get("_is_commodity", False)),
        "الأفق الزمني": estimate_time_horizon(atr14, close, pace_rvol, score)
    }

@st.cache_data(ttl=1800, show_spinner=False)
def fetch_single_stock_history(ticker: str) -> pd.DataFrame:
    try:
        df = yf.download(ticker, period="2y", interval="1d", progress=False, auto_adjust=True)
        if df is None or df.empty:
            return pd.DataFrame()
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df = df.dropna(subset=["Close", "High", "Low", "Open", "Volume"])
        if df.empty:
            return pd.DataFrame()
        return schools.add_indicators(df)  # EMA20/50/200 + VolSMA20 + ATR14
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_fundamental_analysis(ticker: str) -> dict:
    try:
        t = yf.Ticker(ticker)
        info = t.info or {}
        fin, bs, cf = t.financials, t.balance_sheet, t.cashflow
        f_score, tests, breakdown = 0, 0, []

        def gv(df_s, keys, idx=0):
            if df_s is None or df_s.empty or df_s.shape[1] <= idx:
                return None
            for k in keys:
                if k in df_s.index and pd.notna(df_s.loc[k].iloc[idx]):
                    return float(df_s.loc[k].iloc[idx])
            return None

        ni0, ni1 = gv(fin, ["Net Income", "Net Income Common Stockholders"], 0), gv(fin, ["Net Income", "Net Income Common Stockholders"], 1)
        ta0, ta1 = gv(bs, ["Total Assets"], 0), gv(bs, ["Total Assets"], 1)
        ocf0 = gv(cf, ["Operating Cash Flow", "Total Cash From Operating Activities"], 0)
        ltd0, ltd1 = gv(bs, ["Long Term Debt", "Total Debt"], 0), gv(bs, ["Long Term Debt", "Total Debt"], 1)
        if ltd0 is None and bs is not None and not bs.empty:
            ltd0 = 0.0  # مفيش بند ديون في الميزانية = مفيش ديون
        ca0, cl0 = gv(bs, ["Current Assets", "Total Current Assets"], 0), gv(bs, ["Current Liabilities", "Total Current Liabilities"], 0)
        ca1, cl1 = gv(bs, ["Current Assets", "Total Current Assets"], 1), gv(bs, ["Current Liabilities", "Total Current Liabilities"], 1)
        rev0, rev1 = gv(fin, ["Total Revenue", "Operating Revenue"], 0), gv(fin, ["Total Revenue", "Operating Revenue"], 1)
        gp0, gp1 = gv(fin, ["Gross Profit"], 0), gv(fin, ["Gross Profit"], 1)

        ta2 = gv(bs, ["Total Assets"], 2)
        sh0 = gv(bs, ["Ordinary Shares Number", "Share Issued"], 0)
        sh1 = gv(bs, ["Ordinary Shares Number", "Share Issued"], 1)
        # V11.5: ROA على أصول أول السنة (Piotroski الأصلي)، ولو مش متاحة نرجع لأصول آخر السنة
        roa_base0 = ta1 if ta1 else ta0
        roa_base1 = ta2 if ta2 else ta1
        if ni0 is not None and roa_base0 and roa_base0 > 0:
            tests += 1; ok = (ni0 / roa_base0) > 0; f_score += int(ok)
            breakdown.append(("1. ربحية الأصول (ROA > 0)", f"{(ni0/roa_base0)*100:.1f}%", ok))
        if ocf0 is not None:
            tests += 1; ok = ocf0 > 0; f_score += int(ok)
            breakdown.append(("2. التدفق النقدي التشغيلي > 0", f"{ocf0/1e6:,.1f}M", ok))
        if all(v is not None and v != 0 for v in [ni0, ni1, roa_base0, roa_base1]):
            tests += 1; ok = (ni0 / roa_base0) > (ni1 / roa_base1); f_score += int(ok)
            breakdown.append(("3. نمو العائد على الأصول", f"{((ni0/roa_base0)-(ni1/roa_base1))*100:+.1f}%", ok))
        if ocf0 is not None and ni0 is not None:
            tests += 1; ok = ocf0 > ni0; f_score += int(ok)
            breakdown.append(("4. جودة الأرباح (OCF > Net Income)", "نقدي" if ok else "دفتري", ok))
        if all(v is not None and v > 0 for v in [ta0, ta1]) and ltd0 is not None:
            # V11.5: شركة بدون ديون بتنجح في الاختبار (كانت بتتشال من الحساب)
            _l1 = (ltd1 or 0.0) / ta1
            tests += 1; ok = (ltd0 / ta0) <= _l1; f_score += int(ok)
            breakdown.append(("5. انخفاض الرفع المالي", f"{(ltd0/ta0)*100:.1f}%", ok))
        if all(v is not None and v > 0 for v in [ca0, cl0, ca1, cl1]):
            tests += 1; ok = (ca0 / cl0) > (ca1 / cl1); f_score += int(ok)
            breakdown.append(("6. تحسن السيولة الجارية", f"{ca0/cl0:.2f}x", ok))
        if all(v is not None and v > 0 for v in [gp0, rev0, gp1, rev1]):
            tests += 1; ok = (gp0 / rev0) > (gp1 / rev1); f_score += int(ok)
            breakdown.append(("7. تحسن هامش مجمل الربح", f"{(gp0/rev0)*100:.1f}%", ok))
        if all(v is not None and v > 0 for v in [rev0, ta0, rev1, ta1]):
            tests += 1; ok = (rev0 / ta0) > (rev1 / ta1); f_score += int(ok)
            breakdown.append(("8. كفاءة دوران الأصول", f"{rev0/ta0:.2f}x", ok))
        if sh0 and sh1:
            # V11.5: الاختبار التاسع — مفيش إصدار أسهم جديدة (تخفيف)
            tests += 1; ok = sh0 <= sh1 * 1.001; f_score += int(ok)
            breakdown.append(("9. عدم إصدار أسهم جديدة", f"{(sh0/sh1-1)*100:+.1f}%", ok))

        # تقويم الأرباح والكوبونات (V11.4)
        cal_info = {}
        try:
            cal = t.calendar
            if isinstance(cal, dict):
                cal_info = cal
            elif cal is not None and hasattr(cal, "to_dict"):
                cal_info = cal.to_dict()
        except Exception:
            cal_info = {}
        earn_date = None
        ex_div = info.get("exDividendDate")
        if ex_div:
            try:
                earn_date = datetime.fromtimestamp(int(ex_div)).strftime("%Y-%m-%d") if not isinstance(ex_div, str) else ex_div
            except Exception:
                earn_date = str(ex_div)[:10]
        return {
            "name": info.get("longName") or info.get("shortName") or ticker,
            "sector": info.get("sector", "غير محدد"),
            "industry": info.get("industry", "غير محدد"),
            "pe": info.get("trailingPE"), "pb": info.get("priceToBook"),
            "roe": info.get("returnOnEquity"),
            # V11.5: Yahoo بيرجع dividendYield أحياناً كنسبة مئوية جاهزة؛ نحسبه بنفسنا
            "div_yield": ((info.get("dividendRate") / (info.get("currentPrice") or info.get("regularMarketPrice")))
                          if info.get("dividendRate") and (info.get("currentPrice") or info.get("regularMarketPrice")) else None),
            "market_cap": info.get("marketCap"),
            "f_score": f_score, "tests_available": tests, "breakdown": breakdown,
            "calendar": cal_info,
            "ex_dividend": earn_date,
            "dividend_rate": info.get("dividendRate"),
            "payout_ratio": info.get("payoutRatio"),
        }
    except Exception as e:
        return {"error": str(e)}

# V11.5: "أرباح" لوحدها بتطلع في "تراجع الأرباح" فاتشالت؛ والعبارات السلبية بتتفحص الأول
POS_WORDS = ["نمو الأرباح", "ارتفاع الأرباح", "قفزة", "توزيعات", "كوبون", "استحواذ", "ارتفاع", "توسعات", "عقد جديد", "ترسية", "زيادة رأس المال بالمنحة", "أسهم مجانية", "profit rises", "growth", "dividend", "surge"]
NEG_WORDS = ["خسائر", "تراجع", "هبوط", "إيقاف", "شطب", "غرامة", "مديونية", "عجز", "انخفاض", "تحقيق", "دعوى", "loss", "decline", "drop", "suspend", "fine"]

@st.cache_data(ttl=1800, show_spinner=False)
def fetch_stock_news(symbol_clean: str, company_name: str = "") -> list:
    news_list = []
    try:
        # V11.5: الأخبار العربي بتذكر اسم الشركة مش الرمز
        _q = f'"{company_name}" OR {symbol_clean} البورصة' if company_name else f"{symbol_clean} البورصة المصرية"
        query = urllib.parse.quote(_q)
        rss_url = f"https://news.google.com/rss/search?q={query}&hl=ar&gl=EG&ceid=EG:ar"
        req = urllib.request.Request(rss_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=6) as resp:
            root = ET.fromstring(resp.read())
        for item in root.findall(".//item")[:10]:
            title = item.find("title").text if item.find("title") is not None else ""
            link = item.find("link").text if item.find("link") is not None else "#"
            pub_d = item.find("pubDate").text[:16] if item.find("pubDate") is not None else ""
            if title:
                tl = title.lower()
                p_h = sum(1 for w in POS_WORDS if w in tl)
                n_h = sum(1 for w in NEG_WORDS if w in tl)
                if p_h > n_h:
                    lbl, bcls, sc = "إيجابي 🟢", "badge-bull", 1
                elif n_h > p_h:
                    lbl, bcls, sc = "سلبي 🔴", "badge-bear", -1
                else:
                    lbl, bcls, sc = "محايد ⚪", "badge-warn", 0
                news_list.append({"title": title, "source": f"Google News ({pub_d})", "link": link, "sentiment": lbl, "badge": bcls, "score": sc})
    except Exception:
        pass
    return news_list

# ==========================================
# تحميل البيانات الحية والمحفظة السحابية
# ==========================================
if not is_authenticated():
    st.markdown('### Auth (Supabase)')
    with st.expander('Supabase settings (once)', expanded=True):
        u = st.text_input('Supabase URL:', value=st.session_state.get('sb_url_val', get_secret_safe('SUPABASE_URL')), key='auth_sb_url')
        k = st.text_input('Supabase Key (anon):', value=st.session_state.get('sb_key_val', get_secret_safe('SUPABASE_KEY')), type='password', key='auth_sb_key')
        if st.button('Save'):
            st.session_state['sb_url_val'] = u
            st.session_state['sb_key_val'] = k
            st.success('Saved.')
    with st.form('auth_form'):
        ae = st.text_input('Email:', key='auth_email_in')
        ap = st.text_input('Password:', type='password', key='auth_pass_in')
        c1, c2 = st.columns(2)
        with c1:
            do_login = st.form_submit_button('Login', width="stretch")
        with c2:
            do_signup = st.form_submit_button('Sign up', width="stretch")
    if do_login:
        ok, msg = sb_login(ae, ap)
        if ok:
            st.success('Logged in')
            st.rerun()
        else:
            st.error(msg)
    if do_signup:
        ok, msg = sb_signup(ae, ap)
        if ok:
            if msg == 'CONFIRM_EMAIL':
                st.success('Account created. Please confirm email.')
            else:
                st.success('Account created & logged in')
                st.rerun()
        else:
            st.error(msg)
    st.stop()

force_sync = st.session_state.pop("force_cloud_sync", False)
my_portfolio, cloud_connected = load_portfolio(force_cloud_refresh=force_sync)
closed_trades = load_closed_trades(force_refresh=force_sync)
portfolio_clean_syms = [x["symbol"].upper().replace(".CA", "").strip() for x in my_portfolio if x.get("symbol")]

# ===== Watchlist (V11.4) =====
LOCAL_WATCH_FILE = "watchlist_cache.json"
def _load_watchlist():
    try:
        if os.path.exists(LOCAL_WATCH_FILE):
            return json.load(open(LOCAL_WATCH_FILE, encoding="utf-8"))
    except Exception:
        pass
    return st.session_state.get("watchlist", [])
def _save_watchlist(wl):
    st.session_state["watchlist"] = wl
    try:
        with open(LOCAL_WATCH_FILE, "w", encoding="utf-8") as f:
            json.dump(wl, f, ensure_ascii=False, indent=2)
    except Exception:
        pass
watchlist = _load_watchlist()
st.session_state["watchlist"] = watchlist


session_info = get_egx_session_metrics()
refresh_nonce = st.session_state.get("refresh_nonce", 0)

with st.spinner("🚀 جاري مسح أسهم البورصة المصرية وتحديث السيولة اللحظية..."):
    raw_egx_tv_map, last_live_sync = fetch_full_egx_tv_scanner(refresh_nonce)

# دمج المعادن والبترول
try:
    _comm = fetch_commodities()
    for _cs, _cq in _comm.items():
        raw_egx_tv_map[_cs] = _cq
except Exception as _ce:
    print(f"[Commodities Error]: {_ce}")

# قراءة الإعدادات من Session State أو Secrets
capital = int(st.session_state.get("cfg_capital", 100000))
risk_pct = float(st.session_state.get("cfg_risk_pct", 1.5))
min_turnover_m = float(st.session_state.get("cfg_min_turnover", 0.5))
fee_rate = core.FEE_PER_SIDE_TRADER if st.session_state.get("cfg_fee_tier", "0.16%") == "0.16%" else core.FEE_PER_SIDE_STANDARD
min_score = int(st.session_state.get("cfg_min_score", 45))
alert_buffer_pct = float(st.session_state.get("cfg_alert_buf", 2.5))
only_leaders = bool(st.session_state.get("cfg_only_leaders", False))

tg_token = st.session_state.get("tg_token_val") or get_secret_safe("TELEGRAM_BOT_TOKEN")
tg_chat_id = st.session_state.get("tg_chat_val") or get_secret_safe("TELEGRAM_CHAT_ID")
tg_auto_port = bool(st.session_state.get("cfg_tg_port", True))
tg_auto_whales = bool(st.session_state.get("cfg_tg_whales", False))

# ==========================================
# البانر الافتتاحي المضيء + شريط التحكم السريع
# ==========================================
tg_badge = "📲 تليجرام متصل" if (tg_token and tg_chat_id) else "📴 تليجرام غير مربوط"
sb_badge = "☁️ سحابة Supabase متصلة" if cloud_connected else "💾 حفظ محلي مؤقت"

def _cmd_submit():
    st.session_state["cmd_pending"] = st.session_state.get("cmd_q", "")
    st.session_state["cmd_q"] = ""


_up_n = sum(1 for q in raw_egx_tv_map.values() if float(q.get("change") or 0) > 0)
_dn_n = sum(1 for q in raw_egx_tv_map.values() if float(q.get("change") or 0) < 0)
cb1, cb2, cb3, cb4, cb5 = st.columns([1.15, 2.4, 2.3, 0.62, 0.5], vertical_alignment="center")
cb1.markdown('<div class="cmd-brand"><div class="cmd-logo">🦅</div><div><div class="cmd-name">EGX <span>Command</span></div>'
             '<div class="cmd-ver">WHALE HUNTER • V11.5</div></div></div>', unsafe_allow_html=True)
cb2.text_input("أمر", key="cmd_q", on_change=_cmd_submit, label_visibility="collapsed",
               placeholder="⌘  اكتب رمز أو اسم شركة واضغط Enter… (COMI، فوري، طلعت)")
cb3.markdown(f'''<div class="pills"><span class="pill"><span class="dot"></span>{session_info['badge']}</span>
<span class="pill mono"><span class="t-up">▲{_up_n}</span> / <span class="t-down">▼{_dn_n}</span></span>
<span class="pill">{"☁️ سحابة" if cloud_connected else "💾 محلي"}</span><span class="pill">{"📲 تليجرام" if (tg_token and tg_chat_id) else "📴 تليجرام"}</span>
<span class="pill mono" title="آخر تحديث">🕒 {last_live_sync}</span></div>''', unsafe_allow_html=True)
cb4.toggle("🌙", value=(THEME_MODE == "dark"), key="theme_toggle", on_change=_toggle_theme, help="الوضع الداكن / الفاتح")
if cb5.button("🔄", help="تحديث الأسعار والسحابة الآن", width="stretch"):
    st.session_state["refresh_nonce"] = refresh_nonce + 1
    st.session_state["force_cloud_sync"] = True
    fetch_full_egx_tv_scanner.clear()
    st.rerun()
live_auto = bool(st.session_state.get("cfg_live_auto", False))

_tk_items = sorted(
    [(sym_, float(q.get("close") or 0), float(q.get("change") or 0), float(q.get("turnover") or 0))
     for sym_, q in raw_egx_tv_map.items() if float(q.get("close") or 0) > 0],
    key=lambda x: -x[3])[:24]
st.markdown(theme.ticker_html([(a, b, c) for a, b, c, _ in _tk_items]), unsafe_allow_html=True)

# ==========================================
# معالجة بيانات السوق والرادار
# ==========================================
perf1m_list = [q["perf_1m"] for q in raw_egx_tv_map.values() if q.get("volume", 0) > 0]
market_median_perf1m = float(np.median(perf1m_list)) if perf1m_list else 0.0

# مزاج السوق (Market Mood) — breadth + VWAP
_gainers = sum(1 for q in raw_egx_tv_map.values() if float(q.get("change") or 0) > 0)
_total_st = len(raw_egx_tv_map) or 1
market_breadth_pct = (_gainers / _total_st) * 100.0
_vwap_above = sum(1 for q in raw_egx_tv_map.values() if float(q.get("close") or 0) > float(q.get("vwap") or q.get("close") or 0))  # V11.5: المفتاح كان "VWAP" فالنسبة كانت دايماً 0%
market_vwap_breadth = (_vwap_above / _total_st) * 100.0
if market_breadth_pct >= 60 and market_vwap_breadth >= 55:
    market_mood_txt, market_mood_cls = "🟢 إيجابي (سيطرة مشترين)", "badge-bull"
elif market_breadth_pct <= 40:
    market_mood_txt, market_mood_cls = "🔴 سلبي (ضغط بيعي)", "badge-bear"
else:
    market_mood_txt, market_mood_cls = "🟡 محايد (توازن)", "badge-warn"


all_analyzed_map = {}
scanner_results = []

for sym, q_data in raw_egx_tv_map.items():
    analyzed = score_stock_from_tv(q_data, market_median_perf1m, capital, risk_pct, fee_rate, session_info["progress"])
    # V11.5: كان هنا تحميل تاريخ سنتين من Yahoo لكل سهم (حتى 350 طلب) في كل تحديث — ده سبب بطء الدخول.
    # التاريخ بيتحمل دلوقتي للسهم اللي بتفتحه في المختبر بس.
    analyzed["توفر البيانات"] = "📡 Live"
    all_analyzed_map[sym] = analyzed
    if only_leaders and sym not in LEADERS_EGX_SYMBOLS and sym not in COMMODITIES:
        continue
    if analyzed["السيولة (مليون)"] >= min_turnover_m and analyzed["التغير %"] < 19.5:
        scanner_results.append(analyzed)

for known_sym in set(list(EGX_ARABIC_NAMES.keys()) + portfolio_clean_syms):
    if known_sym not in all_analyzed_map:
        p_item_ref = next((x for x in my_portfolio if x["symbol"].upper().replace(".CA", "").strip() == known_sym), {})
        c_val = round(float(p_item_ref.get("buy_price", 0.0)), 4)
        atr_val = round(max(0.01, c_val * 0.025), 4) if c_val > 0 else 0.1
        sl_val = round(max(0.01, c_val - 2.0 * atr_val), 4) if c_val > 0 else 0.0
        r_sh = max(0.01, c_val - sl_val)
        all_analyzed_map[known_sym] = {
            "الرمز": known_sym,
            "اسم الشركة": get_friendly_stock_name(known_sym),
            "Ticker": f"{known_sym}.CA",
            "السكور": 0, "نوع الإشارة": "📌 مدرج بالبورصة", "الرأي اللحظي": "⚪ انتظار",
            "الإغلاق": c_val, "ATR14": atr_val, "EMA20": c_val,
            "التغير %": 0.0, "الفوليوم": 0.0, "فرق VWAP %": 0.0, "القوة النسبية %": 0.0, "السيولة (مليون)": 0.0,
            "الوقف (2xATR)": sl_val,
            "TP1": round(c_val + 1.618 * r_sh, 4) if c_val > 0 else 0.0,
            "TP2": round(c_val + 2.618 * r_sh, 4) if c_val > 0 else 0.0,
            "TP3": round(c_val + 3.618 * r_sh, 4) if c_val > 0 else 0.0,
            "الأسهم": 0, "قيمة الصفقة": 0, "صافي TP1": 0,
            "التشخيص الفني": "بيانات السعر تُسحب من شارت Yahoo/TV",
            "score_parts": {"الاتجاه اليومي (30)": 0, "وتيرة السيولة ووايكوف (35)": 0, "التدفق اللحظي VWAP (35)": 0},
            "intraday_flow": analyze_intraday_flow({}, fallback_close=c_val, session_progress=session_info["progress"]),
            "tv_raw": {},
            "TradingView": f"https://www.tradingview.com/chart/?symbol=EGX:{known_sym}",
            "الأفق الزمني": estimate_time_horizon(atr_val, c_val, 1.0, 0),
            "توفر البيانات": "📡 Live only"
        }

scanner_results.sort(key=lambda x: (x["السكور"], x["intraday_flow"]["flow_score"], x["الفوليوم"]), reverse=True)
filtered_results = [r for r in scanner_results if r["السكور"] >= min_score]

# ==========================================
# معالجة المحفظة والوقف المتحرك الآلي
# ==========================================
portfolio_rows = []
active_alerts = []
total_port_cost, total_port_val, total_open_risk = 0.0, 0.0, 0.0
today_str = get_cairo_now().strftime("%Y-%m-%d")
sent_tg_log = load_sent_tg_log(today_str, force_refresh=force_sync)
tg_phase = core.session_phase()
tg_live_ok = tg_phase in ("continuous", "closing_auction")

for item in my_portfolio:
    sym = item["symbol"].upper().replace(".CA", "").strip()
    shares = int(item.get("shares", 0))
    buy_p = float(item.get("buy_price", 0.0))
    user_sl = float(item.get("stop_loss", 0.0))
    user_tp1 = float(item.get("tp1", 0.0))
    user_tp2 = float(item.get("tp2", 0.0))
    trailing_on = bool(item.get("trailing_enabled", True))
    trailing_stage = int(item.get("trailing_stage", 0))
    if not sym or shares <= 0 or buy_p <= 0:
        continue

    sinfo = all_analyzed_map.get(sym)
    comp_name = sinfo["اسم الشركة"] if sinfo else get_friendly_stock_name(sym)
    curr_p = sinfo["الإغلاق"] if (sinfo and sinfo["الإغلاق"] > 0) else buy_p
    atr14 = sinfo["ATR14"] if sinfo else round(buy_p * 0.025, 4)
    ema20 = sinfo.get("EMA20", curr_p) if sinfo else curr_p
    vwap_val = sinfo["intraday_flow"].get("vwap", curr_p) if sinfo else curr_p

    sl = user_sl if user_sl > 0 else round(max(0.01, buy_p - 2.0 * atr14), 4)
    r_unit = max(0.01, buy_p - sl)
    tp1 = user_tp1 if user_tp1 > 0 else round(buy_p + 1.618 * r_unit, 4)
    tp2 = user_tp2 if user_tp2 > 0 else round(buy_p + 2.618 * r_unit, 4)

    # V11.5: لو المستويات مش متخزنة وعندنا بيانات حية، نخزنها مرة واحدة
    sl_updated = bool(sinfo) and (user_sl <= 0 or user_tp1 <= 0 or user_tp2 <= 0)
    if trailing_on:
        be_price = round(buy_p * (1.0 + fee_rate * 2.0), 4)
        if curr_p >= tp1 and trailing_stage < 1 and be_price < curr_p:
            sl = max(sl, be_price)
            trailing_stage = 1
            sl_updated = True
            active_alerts.append(("success", f"🛡️ <b>تأمين آلي ({sym}):</b> بعد تحقق TP1 تم رفع الوقف للتعادل (<b>{sl} ج.م</b>)."))
        if curr_p >= tp2:
            anchor = max(vwap_val, ema20) if (vwap_val > 0 and ema20 > 0) else curr_p
            cand_sl = round(min(curr_p - 0.5 * atr14, anchor * 0.992), 4)
            if cand_sl > sl * 1.003 and cand_sl < curr_p:
                sl = cand_sl
                trailing_stage = 2
                sl_updated = True
                active_alerts.append(("success", f"🚀 <b>ملاحقة أرباح ({sym}):</b> تم رفع الوقف آلياً إلى <b>{sl} ج.م</b>."))

    if sl_updated:
        upsert_portfolio_item({
            "symbol": sym, "shares": shares, "buy_price": buy_p,
            "stop_loss": sl, "tp1": tp1, "tp2": tp2,
            "trailing_enabled": trailing_on, "trailing_stage": trailing_stage
        })

    trail_badge = "⏸️ معطّل" if not trailing_on else ("🚀 ملاحقة TP2" if trailing_stage >= 2 else ("🛡️ مؤمّن (تعادل)" if trailing_stage == 1 else "⏳ بانتظار TP1"))
    cost_val = shares * buy_p
    mkt_val = shares * curr_p
    net_pnl = (mkt_val - cost_val) - ((cost_val + mkt_val) * fee_rate)
    net_pnl_pct = (net_pnl / cost_val) * 100.0
    total_port_cost += cost_val
    total_port_val += mkt_val
    total_open_risk += max(0.0, shares * (curr_p - sl))

    dist_sl_pct = ((curr_p - sl) / curr_p) * 100.0
    dist_tp1_pct = ((tp1 - curr_p) / curr_p) * 100.0

    alert_status, alert_code, tg_body = "⏳ داخل النطاق الآمن", None, None
    flow_res = sinfo["intraday_flow"] if sinfo else analyze_intraday_flow({}, fallback_close=curr_p, session_progress=session_info["progress"])
    smart = evaluate_smart_stop_loss(sym, curr_p, sl, buy_p, flow_res, alert_buffer_pct)
    if smart["action"] == "EXIT_NOW":
        alert_status, alert_code = "🚨 كسر وقف (خروج فوري!)", "HIT_SL"
        active_alerts.append(("danger", f"🚨 <b>خروج فوري ({sym} — {comp_name}):</b> {smart['reason']} | السعر (<b>{curr_p}</b>) | الوقف (<b>{sl}</b>)!"))
        tg_body = f"🚨 <b>خروج فوري — {sym}</b> ({comp_name})\n{smart['reason']}\nالسعر: <b>{curr_p}</b> | الوقف: <b>{sl}</b>"
    elif smart["action"] == "WATCH_CLOSE":
        alert_status, alert_code = f"👁️ كسر لحظي تحت المراقبة", "NEAR_SL"
        active_alerts.append(("warn", f"👁️ <b>كسر لحظي ({sym}):</b> {smart['reason']} — انتظار تأكيد الإغلاق (14:10-14:30)."))
        tg_body = f"👁️ <b>كسر لحظي — {sym}</b>\n{smart['reason']}"
    elif smart["action"] == "NEAR_SL":
        alert_status, alert_code = f"⚠️ قرب الوقف ({dist_sl_pct:.1f}%)", "NEAR_SL"
        active_alerts.append(("warn", f"⚠️ <b>تحذير ({sym}):</b> على بُعد <b>{dist_sl_pct:.1f}%</b> من الوقف ({sl})."))
        tg_body = f"⚠️ <b>قرب وقف الخسارة — {sym}</b>\nالسعر: <b>{curr_p}</b> | الوقف: <b>{sl}</b>"
    elif curr_p >= tp2:
        alert_status, alert_code = "🏆 تحقق TP2!", "HIT_TP2"
        active_alerts.append(("success", f"🏆 <b>مبروك ({sym}):</b> تحقق الهدف الثاني <b>TP2 ({tp2})</b>!"))
        tg_body = f"🏆 <b>تحقق الهدف الثاني TP2 — {sym}</b>\nالسعر: <b>{curr_p}</b> | الربح: <b>{net_pnl:+,.0f} ج.م</b>"
    elif curr_p >= tp1:
        alert_status, alert_code = "🎯 تحقق TP1!", "HIT_TP1"
        active_alerts.append(("success", f"🎯 <b>تحقق الهدف ({sym}):</b> وصل السعر إلى <b>TP1 ({tp1})</b>!"))
        tg_body = f"🎯 <b>تحقق الهدف الأول TP1 — {sym}</b>\nالسعر: <b>{curr_p}</b> | الربح: <b>{net_pnl:+,.0f} ج.م</b>"
    elif 0 < dist_tp1_pct <= alert_buffer_pct:
        alert_status, alert_code = f"🔔 قرب TP1 ({dist_tp1_pct:.1f}%)", "NEAR_TP1"
        active_alerts.append(("success", f"🔔 <b>اقترب الهدف ({sym}):</b> يبعد <b>{dist_tp1_pct:.1f}%</b> عن TP1 ({tp1})."))

    if alert_code and tg_body and tg_auto_port and tg_token and tg_chat_id and tg_live_ok:
        dkey = f"{today_str}_{sym}_{alert_code}"
        if dkey not in sent_tg_log:
            ok_s, _ = send_telegram_message(tg_token, tg_chat_id, tg_body)
            if ok_s:
                record_sent_tg_alert(dkey, get_cairo_now().strftime("%H:%M"), sent_tg_log)

    portfolio_rows.append({
        "الرمز": sym, "اسم الشركة": comp_name,
        "الرأي اللحظي": sinfo["الرأي اللحظي"] if sinfo else "⚪ انتظار",
        "حالة التنبيه": alert_status, "الوقف المتحرك": trail_badge,
        "السكور الفني": sinfo["السكور"] if sinfo else 0,
        "الكمية": shares, "متوسط الشراء": round(buy_p, 4), "السعر الحالي": curr_p,
        "تغير اليوم %": sinfo["التغير %"] if sinfo else 0.0,
        "صافي الربح/الخسارة": round(net_pnl, 0), "العائد %": round(net_pnl_pct, 4),
        "وقف الخسارة": sl, "بُعد الوقف %": round(dist_sl_pct, 1),
        "TP1": tp1, "بُعد TP1 %": round(dist_tp1_pct, 1), "TP2": tp2,
        "progress_ratio": min(1.0, max(0.0, (curr_p - sl) / max(0.01, tp1 - sl))),
        "trailing_enabled": trailing_on, "trailing_stage": trailing_stage,
        "TradingView": f"https://www.tradingview.com/chart/?symbol=EGX:{sym}",
        "الأفق الزمني": (sinfo.get("الأفق الزمني") if sinfo else "—"),
        "توفر البيانات": (sinfo.get("توفر البيانات") if sinfo else "📡 Live only"),
        "stock_info": sinfo
    })

if tg_auto_whales and tg_token and tg_chat_id and tg_phase == "continuous" and core.session_progress() >= 30 / 270:
    for r in filtered_results:
        if r["السكور"] >= 80 and r["التغير %"] < 19.5:
            wk = f"{today_str}_WHALE_{r['الرمز']}"
            if wk not in sent_tg_log:
                ok_w, _ = send_telegram_message(tg_token, tg_chat_id, f"🐋 <b>إشارة حيتان — {r['الرمز']} ({r['اسم الشركة']})</b>\nالسكور: <b>{r['السكور']}/100</b> | السعر: <b>{r['الإغلاق']}</b> | الوقف: <b>{r['الوقف (2xATR)']}</b> | TP1: <b>{r['TP1']}</b>")
                if ok_w:
                    record_sent_tg_alert(wk, get_cairo_now().strftime("%H:%M"), sent_tg_log)

# ===== فحص قائمة المراقبة (Watchlist Alerts) =====
watchlist_alerts = []
for w in list(st.session_state.get("watchlist", [])):
    sym_w = str(w.get("symbol", "")).upper().replace(".CA", "").strip()
    target = float(w.get("target", 0) or 0)
    direction = w.get("direction", "above")
    sinfo_w = all_analyzed_map.get(sym_w)
    if not sinfo_w or target <= 0:
        continue
    cp_w = float(sinfo_w.get("الإغلاق", 0) or 0)
    if cp_w <= 0:
        continue
    triggered = (direction == "above" and cp_w >= target) or (direction == "below" and cp_w <= target)
    if triggered:
        msg = "📌 <b>Watchlist Alert — %s</b> (%s)<br>السعر <b>%s</b> %s الهدف <b>%s</b>" % (sym_w, sinfo_w.get("اسم الشركة",""), cp_w, (">=" if direction=="above" else "<="), target)
        watchlist_alerts.append((sym_w, msg))
        if tg_auto_port and tg_token and tg_chat_id and tg_live_ok:
            wk = "%s_WL_%s_%s" % (today_str, sym_w, target)
            if wk not in sent_tg_log:
                ok_w, _ = send_telegram_message(tg_token, tg_chat_id, msg.replace("<br>", "\n"))
                if ok_w:
                    record_sent_tg_alert(wk, get_cairo_now().strftime("%H:%M"), sent_tg_log)

TPL = theme.plotly_template(THEME_MODE)
# ==============================================================================
# V11.5 — التنقل: شريط واحد بدل التبويبات، والصفحة المختارة بس هي اللي بتتحسب
# ==============================================================================
_pending_q = st.session_state.pop("cmd_pending", "")
if _pending_q:
    _hit = ui.resolve_symbol(_pending_q, all_analyzed_map)
    if _hit:
        st.session_state["lab_sym"] = _hit
        st.session_state["view"] = "lab"
    else:
        st.toast(f"مالقيتش سهم بالاسم ده: {_pending_q}", icon="🔎")
if st.session_state.get("view") not in ui.NAV:
    st.session_state["view"] = "command"
_nav_labels = dict(ui.NAV)
_nav_labels["opps"] = f"🃏 الفرص ({len(filtered_results)})"
_nav_labels["portfolio"] = f"💼 محفظتي ({len(portfolio_rows)})"
st.segmented_control("التنقل", options=list(ui.NAV), format_func=lambda k: _nav_labels[k], key="view",
                     label_visibility="collapsed", width="stretch")
VIEW = st.session_state.get("view") or "command"


def _open_lab(sym):
    st.session_state["lab_sym"] = sym
    st.session_state["view"] = "lab"


def _add_watch(sym, target):
    wl = list(st.session_state.get("watchlist", []))
    if not any(w.get("symbol") == sym and float(w.get("target", 0)) == float(target) for w in wl):
        wl.append({"symbol": sym, "direction": "above", "target": float(target)})
        _save_watchlist(wl)
    st.toast(f"📌 {sym} اتضاف للمراقبة عند {target}", icon="✅")


@st.dialog("➕ إضافة للمحفظة")
def _add_dialog(sym):
    r = all_analyzed_map[sym]
    st.markdown(f"**{sym} — {r['اسم الشركة']}**  \nالمستويات محسوبة من الـ ATR وتقدر تعدلها.")
    d1, d2 = st.columns(2)
    q = d1.number_input("الكمية", min_value=1, value=max(1, int(r.get("الأسهم") or 1)), step=1)
    bp = d2.number_input("سعر الشراء", min_value=0.01, value=float(r["الإغلاق"] or 0.01), step=0.01, format="%.4f")
    d3, d4, d5 = st.columns(3)
    sl_ = d3.number_input("الوقف", min_value=0.0, value=float(r["الوقف (2xATR)"]), step=0.01, format="%.4f")
    t1_ = d4.number_input("TP1", min_value=0.0, value=float(r["TP1"]), step=0.01, format="%.4f")
    t2_ = d5.number_input("TP2", min_value=0.0, value=float(r["TP2"]), step=0.01, format="%.4f")
    risk_ = q * max(0.0, bp - sl_)
    st.caption(f"قيمة الصفقة {q * bp:,.0f} ج.م • المخاطرة لو الوقف اتضرب {risk_:,.0f} ج.م ({risk_ / max(1.0, capital) * 100:.2f}% من رأس المال)")
    if st.button("💾 حفظ وتفعيل الحماية", type="primary", width="stretch"):
        _, msg_ = upsert_portfolio_item({"symbol": sym, "shares": int(q), "buy_price": float(bp), "stop_loss": float(sl_),
                                         "tp1": float(t1_), "tp2": float(t2_), "trailing_enabled": True, "trailing_stage": 0})
        st.session_state["last_port_msg"] = f"✅ {sym} اتضاف للمحفظة ({msg_})"
        st.rerun()


# ------------------------------------------------------------------------------
# 🛰️ غرفة القيادة
# ------------------------------------------------------------------------------
if VIEW == "command":
    _mood = ui.mood_score(market_breadth_pct, market_vwap_breadth)
    _net_all = total_port_val - total_port_cost - ((total_port_cost + total_port_val) * fee_rate)
    _day_pnl = sum(p["الكمية"] * p["السعر الحالي"] * (p["تغير اليوم %"] / (100 + p["تغير اليوم %"])) for p in portfolio_rows if p["تغير اليوم %"] > -100)
    _risk_pct = total_open_risk / max(1.0, capital) * 100
    k1, k2, k3, k4 = st.columns([1.35, 1, 1, 1])
    k1.markdown(ui.mood_card(_mood, market_breadth_pct, market_vwap_breadth), unsafe_allow_html=True)
    k2.markdown(ui.kpi("🎯 فرص فوق السكور", f"{len(filtered_results)}", f"من {len(raw_egx_tv_map)} سهم • أقوى: {filtered_results[0]['الرمز'] if filtered_results else '—'}", "accent"), unsafe_allow_html=True)
    k3.markdown(ui.kpi("💼 محفظتي", f"{total_port_val:,.0f}", f"صافي <b class='{'t-up' if _net_all >= 0 else 't-down'}'>{_net_all:+,.0f}</b> • اليوم <b class='{'t-up' if _day_pnl >= 0 else 't-down'}'>{_day_pnl:+,.0f}</b>"), unsafe_allow_html=True)
    k4.markdown(ui.kpi("🛡️ مخاطرة مفتوحة", f"{_risk_pct:.1f}%", f"{total_open_risk:,.0f} ج.م لو كل الوقفات اتضربت", "gold" if _risk_pct < 6 else "down"), unsafe_allow_html=True)

    hm_col, feed_col = st.columns([2.3, 1], gap="medium")
    with hm_col:
        st.markdown('<div class="sec-t">🗺️ خريطة السوق — الحجم = السيولة • اللون = التغير • اضغط على سهم يفتح تحليله</div>', unsafe_allow_html=True)
        _hm = [(s_, get_sector(s_) or "أخرى", float(q_.get("turnover") or 0) or float(q_.get("close") or 0) * float(q_.get("volume") or 0),
                float(q_.get("change") or 0), float(q_.get("close") or 0)) for s_, q_ in raw_egx_tv_map.items() if float(q_.get("close") or 0) > 0]
        _hm = sorted([x for x in _hm if x[2] > 0], key=lambda x: -x[2])[:90]
        if _hm:
            _fig_hm = ui.heatmap_figure(_hm, PAL, TPL, height=520)
            _ev_hm = st.plotly_chart(_fig_hm, width="stretch", key="heatmap", on_select="rerun", selection_mode="points",
                                     config={"displayModeBar": False})
            try:
                _pts = (_ev_hm or {}).get("selection", {}).get("points", [])
                _lab_hit = (_pts[0].get("customdata") or [None])[0] if _pts else None
            except Exception:
                _lab_hit = None
            if _lab_hit and _lab_hit in all_analyzed_map and st.session_state.get("_hm_last") != _lab_hit:
                st.session_state["_hm_last"] = _lab_hit
                st.session_state["cmd_pending"] = _lab_hit  # الـ nav اتعمل خلاص، فبنحوّل في الـ rerun الجاي
                st.rerun()
        else:
            st.info("مفيش بيانات سيولة كفاية للخريطة.")
    with feed_col:
        st.markdown('<div class="sec-t">🐋 بث الحيتان والتنبيهات</div>', unsafe_allow_html=True)
        st.markdown('<div class="feed">' + ui.feed_html(ui.build_feed(active_alerts, filtered_results, sent_tg_log, watchlist_alerts)) + "</div>", unsafe_allow_html=True)

    st.markdown('<div class="sec-t">💼 مراكزي — من الوقف (يمين) للهدف (شمال)</div>', unsafe_allow_html=True)
    st.markdown(ui.positions_html(portfolio_rows), unsafe_allow_html=True)
    if watchlist_alerts:
        try:
            import streamlit.components.v1 as _sc
            _sc.html("<script>try{var a=new (window.AudioContext||window.webkitAudioContext)();var o=a.createOscillator();o.connect(a.destination);o.frequency.value=880;o.start();setTimeout(function(){o.stop();},200);}catch(e){}</script>", height=0)
        except Exception:
            pass

# ------------------------------------------------------------------------------
# 🃏 كروت الفرص
# ------------------------------------------------------------------------------
if VIEW == "opps":
    of1, of2, of3, of4 = st.columns([1.6, 2.2, 1, 0.9])
    radar_search = of1.text_input("بحث", placeholder="🔎 رمز أو اسم شركة…", label_visibility="collapsed", key="opp_q")
    sig_filter = of2.segmented_control("نوع الإشارة", ["الكل", "🔥 تدفق سيولة", "📈 زخم سيولة", "🎯 تصحيح بلا بائع"], default="الكل",
                                       label_visibility="collapsed", key="opp_sig") or "الكل"
    sort_by = of3.selectbox("ترتيب", ["السكور", "السيولة (مليون)", "التغير %", "الفوليوم"], label_visibility="collapsed", key="opp_sort")
    as_table = of4.toggle("📋 جدول", key="opp_table")

    _rows = list(filtered_results)
    if radar_search.strip():
        _q = radar_search.strip()
        _rows = [r for r in _rows if _q.upper() in r["الرمز"] or _q in str(r["اسم الشركة"])]
    if sig_filter != "الكل":
        _rows = [r for r in _rows if r["نوع الإشارة"] == sig_filter]
    _rows.sort(key=lambda r: r.get(sort_by, 0) or 0, reverse=True)

    if not _rows:
        st.info("مفيش فرص بالفلتر ده. جرّب تقلل الحد الأدنى للسكور من ⚙️ الإعدادات.")
    elif as_table:
        st.dataframe(
            pd.DataFrame(_rows)[["الرمز", "اسم الشركة", "السكور", "الرأي اللحظي", "نوع الإشارة", "الإغلاق", "التغير %", "الفوليوم", "فرق VWAP %", "السيولة (مليون)", "الوقف (2xATR)", "TP1", "TP2", "الأسهم", "صافي TP1", "الأفق الزمني", "TradingView"]],
            width="stretch", hide_index=True, height=560,
            column_config={"TradingView": st.column_config.LinkColumn("شارت TV", display_text="فتح ↗"),
                           "السكور": st.column_config.ProgressColumn("السكور", min_value=0, max_value=100, format="%d"),
                           "الفوليوم": st.column_config.NumberColumn("وتيرة السيولة", format="%.2fx")})
    else:
        _shown = int(st.session_state.get("opp_n", 12))
        _port_syms = {p["الرمز"] for p in portfolio_rows}
        _per_row = 4
        for i0 in range(0, min(_shown, len(_rows)), _per_row):
            cols_ = st.columns(_per_row, gap="medium")
            for j, r in enumerate(_rows[i0:i0 + _per_row]):
                with cols_[j]:
                    with st.container(border=True):
                        st.markdown(ui.opp_card(r, rank=i0 + j if not radar_search and sig_filter == "الكل" and sort_by == "السكور" else 9,
                                                in_portfolio=r["الرمز"] in _port_syms), unsafe_allow_html=True)
                        b1, b2, b3 = st.columns([1.3, 1, 0.7])
                        if b1.button("➕ للمحفظة", key=f"add_{r['الرمز']}", type="primary", width="stretch"):
                            _add_dialog(r["الرمز"])
                        b2.button("🔬 تحليل", key=f"lab_{r['الرمز']}", width="stretch", on_click=_open_lab, args=(r["الرمز"],))
                        b3.button("📌", key=f"wl_{r['الرمز']}", width="stretch", help=f"راقب {r['الرمز']} عند TP1 ({r['TP1']})",
                                  on_click=_add_watch, args=(r["الرمز"], r["TP1"]))
        if len(_rows) > _shown:
            if st.button(f"عرض {min(12, len(_rows) - _shown)} كمان ⬇️ (باقي {len(_rows) - _shown})", width="stretch"):
                st.session_state["opp_n"] = _shown + 12
                st.rerun()

# ==============================================================================
# التبويب 2: محفظتي وإدارة المخاطر (3 علامات تبويب فرعية نظيفة)
# ==============================================================================
if VIEW == "portfolio":
    if st.session_state.get("last_port_msg"):
        st.success(st.session_state["last_port_msg"])

    for lvl, msg in active_alerts:
        st.markdown(f'<div class="alert-box-{lvl}">{msg}</div>', unsafe_allow_html=True)

    total_net_pnl = total_port_val - total_port_cost - ((total_port_cost + total_port_val) * fee_rate)
    total_pnl_pct = ((total_net_pnl / total_port_cost) * 100.0) if total_port_cost > 0 else 0.0
    open_risk_pct = (total_open_risk / max(1.0, total_port_val)) * 100.0 if total_port_val > 0 else 0.0

    pk1, pk2, pk3, pk4 = st.columns(4)
    pk1.markdown(f'<div class="kpi-card"><div class="kpi-label">💵 إجمالي التكلفة</div><div class="kpi-val">{total_port_cost:,.0f} ج.م</div></div>', unsafe_allow_html=True)
    pk2.markdown(f'<div class="kpi-card"><div class="kpi-label">💰 القيمة الحالية</div><div class="kpi-val txt-cyan">{total_port_val:,.0f} ج.م</div></div>', unsafe_allow_html=True)
    pk3.markdown(f'<div class="kpi-card"><div class="kpi-label">📈 صافي الربح/الخسارة</div><div class="kpi-val {"txt-green" if total_net_pnl>=0 else "txt-red"}">{total_net_pnl:+,.0f} ({total_pnl_pct:+.1f}%)</div></div>', unsafe_allow_html=True)
    pk4.markdown(f'<div class="kpi-card" style="border-top-color:var(--gold);"><div class="kpi-label">🛡️ المخاطرة المفتوحة</div><div class="kpi-val txt-gold">{total_open_risk:,.0f} ({open_risk_pct:.1f}%)</div></div>', unsafe_allow_html=True)
    st.write("")
    # ===== خريطة حرارة المحفظة (Treemap) V11.4 =====
    if portfolio_rows:
        try:
            import plotly.express as _px
            _tdf = pd.DataFrame(portfolio_rows)
            _fig_tm = _px.treemap(
                _tdf, path=["الرمز"], values="الكمية",
                color="العائد %", color_continuous_scale="RdYlGn", color_continuous_midpoint=0,
                title="خريطة حرارة المحفظة (حجم = كمية، لون = العائد %)",
            )
            _fig_tm.update_layout(height=360, template=TPL, margin=dict(l=10,r=10,t=40,b=10))
            st.plotly_chart(_fig_tm, width="stretch")
        except Exception as _e:
            st.caption("تعذر رسم الخريطة: %s" % _e)

    if portfolio_rows:
        with st.expander('Performance Attribution (V11.4)', expanded=False):
            try:
                _adf = pd.DataFrame(portfolio_rows)
                _adf['contribution'] = _adf['صافي الربح/الخسارة']
                _adf['weight'] = _adf['الكمية'] * _adf['السعر الحالي']
                _tot = _adf['weight'].sum()
                _adf['weight_pct'] = (_adf['weight'] / _tot * 100).round(1) if _tot > 0 else 0.0
                _adf = _adf.sort_values('contribution', ascending=False)
                import plotly.express as _px
                _fig_attr = _px.bar(_adf, x='الرمز', y='contribution', color='weight_pct', color_continuous_scale='RdYlGn', title='P&L Contribution by Stock (color=portfolio weight %)')
                _fig_attr.update_layout(height=360, template=TPL, margin=dict(l=10,r=10,t=40,b=10))
                st.plotly_chart(_fig_attr, width="stretch")
                st.dataframe(_adf[['الرمز', 'اسم الشركة', 'الكمية', 'السعر الحالي', 'صافي الربح/الخسارة', 'العائد %', 'weight_pct']], width="stretch", hide_index=True)
            except Exception as _e:
                st.caption('Attribution error: %s' % _e)
    st.write('')
    ptab_open, ptab_add, ptab_history = st.tabs([
        f"📋 مراكزي المفتوحة والتحكم الآلي ({len(portfolio_rows)})",
        "➕ إضافة سهم / استيراد فواتير ثاندر",
        f"📜 سجل الصفقات المغلقة والنسخ الاحتياطي ({len(closed_trades)})"
    ])

    # --- فرعي 2.1: المراكز المفتوحة ---
    with ptab_open:
        if not portfolio_rows:
            st.info("📌 محفظتك فارغة حالياً؛ انتقل إلى تبويب **➕ إضافة سهم / استيراد فواتير ثاندر** لإضافة أسهمك يدوياً أو برفع فواتير ثاندر.")
        else:
            if st.button("📲 إرسال تقرير محفظتي اللحظي إلى تليجرام", width="stretch"):
                if not tg_token or not tg_chat_id:
                    st.warning("⚠️ اربط التليجرام أولاً من تبويب **⚙️ الإعدادات**.")
                else:
                    lines = [f"📊 <b>تقرير محفظتك</b> | القيمة: <b>{total_port_val:,.0f} ج.م</b> | الصافي: <b>{total_net_pnl:+,.0f} ({total_pnl_pct:+.1f}%)</b>", ""]
                    for pr in portfolio_rows:
                        lines.append(f"• <b>{pr['الرمز']}</b> ({pr['اسم الشركة']}): السعر {pr['السعر الحالي']} ({pr['العائد %']:+.1f}%) | SL: {pr['وقف الخسارة']} | TP1: {pr['TP1']}")
                    ok_r, r_m = send_telegram_message(tg_token, tg_chat_id, "\n".join(lines))
                    if ok_r:
                        st.success("✅ تم الإرسال لتليجرام!")
                    else:
                        st.error(f"❌ {r_m}")
            st.dataframe(
                pd.DataFrame(portfolio_rows)[["الرمز", "اسم الشركة", "الرأي اللحظي", "حالة التنبيه", "الوقف المتحرك", "السكور الفني", "الكمية", "متوسط الشراء", "السعر الحالي", "صافي الربح/الخسارة", "العائد %", "وقف الخسارة", "بُعد الوقف %", "TP1", "TP2", "توفر البيانات", "الأفق الزمني", "TradingView"]],
                width="stretch", hide_index=True,
                column_config={
                    "TradingView": st.column_config.LinkColumn("شارت TV", display_text="فتح ↗"),
                    "السكور الفني": st.column_config.ProgressColumn("السكور", min_value=0, max_value=100, format="%d"),
                }
            )

            st.divider()
            ps1, ps2, ps3 = st.columns([1.8, 1.1, 1])
            with ps1:
                port_sel = st.selectbox(
                    "🔍 اختر سهماً من محفظتك للتحكم والشارت:",
                    options=[r["الرمز"] for r in portfolio_rows],
                    format_func=lambda s: f"{s} — {next((r['اسم الشركة'] for r in portfolio_rows if r['الرمز'] == s), s)}"
                )
            p_item = next(r for r in portfolio_rows if r["الرمز"] == port_sel)

            with ps2:
                st.write(""); st.write("")
                if st.button(f"🛡️ تأمين {port_sel} للتعادل", width="stretch"):
                    be_val = round(p_item["متوسط الشراء"] * (1.0 + fee_rate * 2.0), 4)
                    if p_item["السعر الحالي"] <= be_val:
                        st.warning(f"⚠️ السعر الحالي ({p_item['السعر الحالي']}) أقل من أو يساوي نقطة التعادل ({be_val}).")
                    else:
                        _, st_be = upsert_portfolio_item({
                            "symbol": port_sel, "shares": p_item["الكمية"], "buy_price": p_item["متوسط الشراء"],
                            "stop_loss": be_val, "tp1": p_item["TP1"], "tp2": p_item["TP2"],
                            "trailing_enabled": p_item["trailing_enabled"], "trailing_stage": max(1, p_item["trailing_stage"])
                        })
                        st.session_state["last_port_msg"] = f"🛡️ تم رفع وقف {port_sel} للتعادل ({be_val} ج.م) ({st_be})."
                        st.rerun()

            with ps3:
                st.write(""); st.write("")
                if st.button(f"🗑️ حذف {port_sel}", width="stretch"):
                    _, d_st = delete_portfolio_item(port_sel)
                    st.session_state["last_port_msg"] = f"🗑️ تم حذف {port_sel} ({d_st})."
                    st.rerun()

            clc1, clc2 = st.columns([1.3, 1.7])
            with clc1:
                exit_p = st.number_input(f"💵 سعر البيع الفعلي لإغلاق {port_sel} (ج.م):", min_value=0.01, value=float(p_item["السعر الحالي"]), step=0.05)
            with clc2:
                st.write(""); st.write("")
                if st.button(f"💰 إغلاق صفقة {port_sel} وتسجيلها في دفتر الصفقات", type="primary", width="stretch"):
                    n_res, p_res = record_closed_trade(port_sel, p_item["الكمية"], p_item["متوسط الشراء"], exit_p, fee_rate)
                    st.session_state["last_port_msg"] = f"✅ تم إغلاق صفقة {port_sel} ({p_item['اسم الشركة']}) بصافي {n_res:+,.0f} ج.م ({p_res:+.1f}%)!"
                    st.rerun()

            df_ph = fetch_single_stock_history(f"{port_sel}.CA")
            if not df_ph.empty:
                sub_p = df_ph.tail(90)
                fig_p = go.Figure(go.Candlestick(x=sub_p.index, open=sub_p["Open"], high=sub_p["High"], low=sub_p["Low"], close=sub_p["Close"], name="السعر"))
                fig_p.add_hline(y=p_item["متوسط الشراء"], line_dash="dot", line_color="#FACC15", annotation_text=f"شرائك: {p_item['متوسط الشراء']}")
                fig_p.add_hline(y=p_item["وقف الخسارة"], line_dash="dash", line_color=PAL["down"], annotation_text=f"SL: {p_item['وقف الخسارة']}")
                fig_p.add_hline(y=p_item["TP1"], line_dash="dash", line_color=PAL["up"], annotation_text=f"TP1: {p_item['TP1']}")
                fig_p.add_hline(y=p_item["TP2"], line_dash="dash", line_color="#10B981", annotation_text=f"TP2: {p_item['TP2']}")
                fig_p.update_layout(title=f"📊 مستويات مركزك في {port_sel} ({p_item['اسم الشركة']})", height=420, xaxis_rangeslider_visible=False, template=TPL, margin=dict(l=10, r=10, t=40, b=10))
                st.plotly_chart(fig_p, width="stretch")

    # --- فرعي 2.2: إضافة سهم جديد + استيراد مستندات ثاندر ---
    with ptab_add:
        st.markdown("#### ➕ إضافة سهم جديد أو تعديل كمية/سعر سهم حالي")
        if st.session_state.pop("clear_add_sym", False):
            st.session_state["add_sym_input"] = ""

        fc1, fc2, fc3 = st.columns([1.4, 1, 1])
        with fc1:
            in_sym_raw = st.text_input(
                "🔍 رمز السهم (اكتب الكود واضغط Enter أو انتقل للكمية ليظهر اسم الشركة فوراً):",
                key="add_sym_input",
                placeholder="مثال: ABUK أو COMI أو TMGH أو OCDI"
            )
        with fc2:
            in_shares = st.number_input("عدد الأسهم (الكمية)", min_value=1, value=100, step=10, key="add_shares_in")
        with fc3:
            in_buy = st.number_input("متوسط سعر الشراء (ج.م)", min_value=0.01, value=5.0, step=0.05, key="add_buy_in")

        clean_in = re.sub(r"[^A-Z0-9]", "", in_sym_raw.upper().replace(".CA", ""))

        if clean_in:
            if clean_in in all_analyzed_map:
                ms = all_analyzed_map[clean_in]
                st.markdown(f"""
                <div class="alert-box-success" style="margin-top:6px;margin-bottom:12px;">
                    <div style="font-size:16px;font-weight:900;">
                        ✅ تم تأكيد السهم: <span class="txt-cyan">{clean_in}</span> — <span class="txt-gold">{ms['اسم الشركة']}</span>
                    </div>
                    <div style="font-size:13px;margin-top:4px;">
                        💰 السعر اللحظي: <b>{ms['الإغلاق']} ج.م</b> (<span class="{'txt-green' if ms['التغير %']>=0 else 'txt-red'}">{ms['التغير %']:+.2f}%</span>) •
                        🛑 الوقف الآلي المقترح (2×ATR): <b>{ms['الوقف (2xATR)']}</b> •
                        🎯 TP1 المقترح: <b>{ms['TP1']}</b>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                suggestions = [f"<b>{k}</b> ({v['اسم الشركة']})" for k, v in all_analyzed_map.items() if clean_in in k][:5]
                sug_html = f"<div style='margin-top:5px;font-size:13px;'>🔎 هل تقصد: {' &nbsp;|&nbsp; '.join(suggestions)}</div>" if suggestions else ""
                st.markdown(f"""
                <div class="alert-box-warn" style="margin-top:6px;margin-bottom:12px;">
                    ⚠️ الرمز <b>({clean_in})</b> غير مكتمل في قائمة البورصة المصرية.{sug_html}
                </div>
                """, unsafe_allow_html=True)

        fc4, fc5, fc6 = st.columns(3)
        with fc4:
            in_sl = st.number_input("وقف الخسارة (0 = آلي 2×ATR)", min_value=0.0, value=0.0, step=0.05)
        with fc5:
            in_tp1 = st.number_input("الهدف الأول TP1 (0 = آلي)", min_value=0.0, value=0.0, step=0.05)
        with fc6:
            in_tp2 = st.number_input("الهدف الثاني TP2 (0 = آلي)", min_value=0.0, value=0.0, step=0.05)

        in_trailing = st.checkbox("🛡️ تفعيل الوقف المتحرك الآلي (تأمين التعادل عند TP1 وملاحقة الربح بعد TP2)", value=True)

        if st.button("💾 حفظ السهم في محفظتي وتفعيل الحماية", type="primary", width="stretch"):
            if not clean_in:
                st.error("⚠️ اكتب رمز السهم أولاً (مثل ABUK أو COMI).")
            else:
                saved_name = all_analyzed_map[clean_in]["اسم الشركة"] if clean_in in all_analyzed_map else get_friendly_stock_name(clean_in)
                _, sv_status = upsert_portfolio_item({
                    "symbol": clean_in, "shares": int(in_shares), "buy_price": float(in_buy),
                    "stop_loss": float(in_sl), "tp1": float(in_tp1), "tp2": float(in_tp2),
                    "trailing_enabled": bool(in_trailing), "trailing_stage": 0
                })
                st.session_state["last_port_msg"] = f"✅ تم حفظ سهم ({clean_in} — {saved_name}) بنجاح ({sv_status})!"
                st.session_state["clear_add_sym"] = True
                st.rerun()

        st.divider()
        st.markdown("#### 📄 استيراد تلقائي من مستندات ثاندر (Thndr PDF / Excel / CSV)")
        thndr_files = st.file_uploader(
            "📎 ارفع فاتورة أو عدة فواتير تنفيذ من ثاندر (PDF) أو كشف حساب (Excel / CSV):",
            type=["pdf", "csv", "xlsx", "xls"],
            accept_multiple_files=True,
            key="thndr_docs_uploader"
        )
        if thndr_files:
            _isin_map = fetch_egx_isin_map()
            try:
                parsed_ops = parse_thndr_files(thndr_files, EGX_ARABIC_NAMES, isin_map=_isin_map)
            except TypeError:  # نسخة قديمة من thndr_parser.py
                parsed_ops = parse_thndr_files(thndr_files, EGX_ARABIC_NAMES)
            if not parsed_ops:
                st.warning("⚠️ لم يتم التعرف على بنود الصفقة تلقائياً داخل الملف؛ تأكد أنه فاتورة تنفيذ أو كشف حساب ثاندر.")
            else:
                st.info(f"✅ تم استخراج **{len(parsed_ops)}** عملية من مستندات ثاندر — راجع الجدول أو عدّل أي رقم قبل الاعتماد:")
                edited_ops = st.data_editor(pd.DataFrame(parsed_ops), width="stretch", hide_index=True, num_rows="dynamic")
                if (edited_ops["الرمز"].astype(str).str.strip() == "").any():
                    st.warning("⚠️ فيه سهم مقدرتش أعرف رمزه من كود ISIN — اكتب الرمز (مثلاً BTFH) في عمود الرمز قبل الاعتماد.")
                if (edited_ops["الكمية"] <= 0).any():
                    st.warning("⚠️ فيه عمليات الكمية بتاعتها 0 (الملف ماكانش فيه كمية واضحة). اكتب الكمية الصحيحة، وإلا السطر هيتجاهل.")
                if st.button("🚀 اعتماد العمليات وتحديث المحفظة والسحابة فوراً", type="primary", width="stretch"):
                    applied_cnt = 0
                    for _, op in edited_ops.iterrows():
                        sym_o = str(op.get("الرمز", "")).upper().replace(".CA", "").strip()
                        qty_o = int(op.get("الكمية", 0))
                        prc_o = float(op.get("السعر", 0.0))
                        side_o = str(op.get("العملية", ""))
                        if not sym_o or qty_o <= 0 or prc_o <= 0:
                            continue

                        if "بيع" in side_o or "Sell" in side_o:
                            ex_item = next((x for x in my_portfolio if x["symbol"].upper() == sym_o), None)
                            if ex_item:
                                ex_sh = int(ex_item["shares"])
                                ex_bp = float(ex_item["buy_price"])
                                sell_qty = min(ex_sh, qty_o)
                                record_closed_trade(sym_o, sell_qty, ex_bp, prc_o, fee_rate)
                                if ex_sh > sell_qty:
                                    upsert_portfolio_item({**ex_item, "shares": ex_sh - sell_qty})
                                applied_cnt += 1
                        else:
                            ex_item = next((x for x in my_portfolio if x["symbol"].upper() == sym_o), None)
                            if ex_item:
                                old_sh = int(ex_item["shares"])
                                old_bp = float(ex_item["buy_price"])
                                tot_sh = old_sh + qty_o
                                avg_bp = round(((old_sh * old_bp) + (qty_o * prc_o)) / tot_sh, 4)
                                upsert_portfolio_item({**ex_item, "shares": tot_sh, "buy_price": avg_bp})
                            else:
                                s_inf = all_analyzed_map.get(sym_o, {})
                                atr_v = s_inf.get("ATR14", prc_o * 0.025)
                                sl_v = round(max(0.01, prc_o - 2.0 * atr_v), 4)
                                r_u = max(0.01, prc_o - sl_v)
                                upsert_portfolio_item({
                                    "symbol": sym_o, "shares": qty_o, "buy_price": prc_o,
                                    "stop_loss": sl_v, "tp1": round(prc_o + 1.618 * r_u, 4),
                                    "tp2": round(prc_o + 2.618 * r_u, 4),
                                    "trailing_enabled": True, "trailing_stage": 0
                                })
                            applied_cnt += 1

                    st.session_state["last_port_msg"] = f"✅ تم اعتماد وتنفيذ {applied_cnt} عملية من مستندات ثاندر ومزامنتها!"
                    st.rerun()

    # --- فرعي 2.3: دفتر الصفقات المغلقة والنسخ الاحتياطي ---
    with ptab_history:
        st.markdown("#### 📜 سجل الصفقات المغلقة وإحصائيات الأداء")
        if not closed_trades:
            st.info("📘 لا توجد صفقات مغلقة مسجلة بعد.")
        else:
            wins = [t for t in closed_trades if float(t.get("net_pnl", 0)) > 0]
            losses = [t for t in closed_trades if float(t.get("net_pnl", 0)) <= 0]
            win_rate = (len(wins) / len(closed_trades)) * 100.0
            g_win = sum(float(t.get("net_pnl", 0)) for t in wins)
            g_loss = abs(sum(float(t.get("net_pnl", 0)) for t in losses))
            pf = (g_win / g_loss) if g_loss > 0 else (99.9 if g_win > 0 else 0.0)
            tot_realized = sum(float(t.get("net_pnl", 0)) for t in closed_trades)

            tk1, tk2, tk3, tk4 = st.columns(4)
            tk1.markdown(f'<div class="kpi-card"><div class="kpi-label">📊 إجمالي الصفقات</div><div class="kpi-val">{len(closed_trades)}</div></div>', unsafe_allow_html=True)
            tk2.markdown(f'<div class="kpi-card"><div class="kpi-label">🎯 نسبة النجاح</div><div class="kpi-val txt-cyan">{win_rate:.1f}%</div></div>', unsafe_allow_html=True)
            tk3.markdown(f'<div class="kpi-card"><div class="kpi-label">⚖️ معامل الربح</div><div class="kpi-val txt-gold">{pf:.2f}x</div></div>', unsafe_allow_html=True)
            tk4.markdown(f'<div class="kpi-card"><div class="kpi-label">💰 صافي الأرباح المحققة</div><div class="kpi-val {"txt-green" if tot_realized>=0 else "txt-red"}">{tot_realized:+,.0f} ج.م</div></div>', unsafe_allow_html=True)
            st.write("")
            # ===== Risk Analytics (V11.4) =====
            try:
                _sorted = sorted(closed_trades, key=lambda t: str(t.get("closed_at", "")))
                _cum = 0.0
                _peak = 0.0
                _maxdd = 0.0
                _cum_series = []
                _rets = []
                for t in _sorted:
                    pnl = float(t.get("net_pnl", 0) or 0)
                    bp = float(t.get("buy_price", 0) or 0)
                    sh = float(t.get("shares", 0) or 0)
                    cost = bp * sh
                    _cum += pnl
                    _cum_series.append(_cum)
                    if _cum > _peak:
                        _peak = _cum
                    dd = _peak - _cum
                    if dd > _maxdd:
                        _maxdd = dd
                    if cost > 0:
                        _rets.append(pnl / cost)
                import statistics as _st
                _mean = (_st.fmean(_rets) if _rets else 0.0)
                _std = (_st.pstdev(_rets) if len(_rets) > 1 else 0.0)
                _down = [r for r in _rets if r < 0]
                _down_std = (_st.pstdev(_down) if len(_down) > 1 else 0.0)
                _sharpe = (_mean / _std * (len(_rets) ** 0.5)) if _std > 0 else 0.0
                _sortino = (_mean / _down_std * (len(_rets) ** 0.5)) if _down_std > 0 else 0.0
                _calmar = (sum(_rets) / _maxdd) if _maxdd > 0 else 0.0
                _avg_win = _st.fmean([float(t.get("net_pnl",0)) for t in closed_trades if float(t.get("net_pnl",0))>0]) if wins else 0.0
                _avg_loss = _st.fmean([float(t.get("net_pnl",0)) for t in closed_trades if float(t.get("net_pnl",0))<=0]) if losses else 0.0
                _expectancy = ( (len(wins)/len(closed_trades))*_avg_win + (len(losses)/len(closed_trades))*_avg_loss ) if closed_trades else 0.0
            except Exception:
                _sharpe = _sortino = _calmar = _maxdd = _expectancy = _avg_win = _avg_loss = 0.0
                _cum_series = []

            rk1, rk2, rk3, rk4 = st.columns(4)
            rk1.markdown(f'<div class="kpi-card"><div class="kpi-label">📐 Sharpe (per-trade)</div><div class="kpi-val txt-cyan">{_sharpe:+.2f}</div></div>', unsafe_allow_html=True)
            rk2.markdown(f'<div class="kpi-card"><div class="kpi-label">📉 Sortino</div><div class="kpi-val txt-cyan">{_sortino:+.2f}</div></div>', unsafe_allow_html=True)
            rk3.markdown(f'<div class="kpi-card"><div class="kpi-label">⬇️ Max Drawdown</div><div class="kpi-val txt-red">{_maxdd:,.0f} ج.م</div></div>', unsafe_allow_html=True)
            rk4.markdown(f'<div class="kpi-card" style="border-top-color:var(--gold);"><div class="kpi-label">🎯 Expectancy/صفقة</div><div class="kpi-val txt-gold">{_expectancy:+,.0f} ج.م</div></div>', unsafe_allow_html=True)
            rk5, rk6, rk7, rk8 = st.columns(4)
            rk5.markdown(f'<div class="kpi-card"><div class="kpi-label">🏆 متوسط ربح</div><div class="kpi-val txt-green">{_avg_win:+,.0f} ج.م</div></div>', unsafe_allow_html=True)
            rk6.markdown(f'<div class="kpi-card"><div class="kpi-label">💔 متوسط خسارة</div><div class="kpi-val txt-red">{_avg_loss:+,.0f} ج.م</div></div>', unsafe_allow_html=True)
            rk7.markdown(f'<div class="kpi-card"><div class="kpi-label">📊 Calmar</div><div class="kpi-val txt-cyan">{_calmar:+.2f}</div></div>', unsafe_allow_html=True)
            rk8.markdown(f'<div class="kpi-card"><div class="kpi-label">🔢 عدد الصفقات</div><div class="kpi-val">{len(closed_trades)}</div></div>', unsafe_allow_html=True)
            if _cum_series:
                import plotly.graph_objects as _go
                _fig_cum = _go.Figure(_go.Scatter(y=_cum_series, mode="lines+markers", line=dict(color=PAL["accent"], width=2.5), fill="tozeroy", fillcolor=PAL["glow"]))
                _fig_cum.update_layout(title="📈 منحنى الأرباح التراكمية (Equity Curve)", height=320, template=TPL, margin=dict(l=10,r=10,t=40,b=10))
                st.plotly_chart(_fig_cum, width="stretch")
            st.write("")

            st.dataframe(pd.DataFrame([
                {"الرمز": t.get("symbol"), "اسم الشركة": get_friendly_stock_name(t.get("symbol", "")), "الكمية": t.get("shares"), "سعر الشراء": t.get("buy_price"), "سعر البيع": t.get("sell_price"), "صافي الربح/الخسارة": t.get("net_pnl"), "العائد %": t.get("pnl_pct"), "التاريخ": str(t.get("closed_at", ""))[:16].replace("T", " ")}
                for t in closed_trades
            ]), width="stretch", hide_index=True)

        st.divider()
        st.markdown("#### 💾 النسخ الاحتياطي والاستعادة + تصدير Excel")
        b1, b2, b3 = st.columns(3)
        with b1:
            st.download_button(
                "⬇️ نسخة احتياطية (JSON)",
                data=json.dumps(my_portfolio, ensure_ascii=False, indent=2),
                file_name=f"egx_portfolio_{today_str}.json",
                mime="application/json",
                width="stretch"
            )
        with b2:
            # Excel export: portfolio + closed trades + radar
            try:
                import io as _io
                _buf = _io.BytesIO()
                with pd.ExcelWriter(_buf, engine="openpyxl") as _w:
                    if my_portfolio:
                        pd.DataFrame(my_portfolio).to_excel(_w, sheet_name="المحفظة", index=False)
                    if closed_trades:
                        pd.DataFrame(closed_trades).to_excel(_w, sheet_name="صفقات مغلقة", index=False)
                    if filtered_results:
                        pd.DataFrame(filtered_results).to_excel(_w, sheet_name="رادار", index=False)
                _buf.seek(0)
                st.download_button(
                    "📊 تصدير Excel (محفظة+صفقات+رادار)",
                    data=_buf.getvalue(),
                    file_name=f"egx_report_{today_str}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    width="stretch"
                )
            except Exception as _e:
                st.caption(f"⚠️ Excel غير متاح: {_e}")
        with b3:
            up_file = st.file_uploader("⬆️ استعادة من JSON", type=["json"], label_visibility="collapsed")
            if up_file is not None:
                try:
                    restored = json.load(up_file)
                    if isinstance(restored, list):
                        ok_r, msg_r = sync_full_portfolio_to_cloud(restored)
                        if not ok_r:
                            _save_local_portfolio_cache(restored)
                            st.session_state["cached_portfolio"] = restored
                        st.session_state["last_port_msg"] = msg_r if ok_r else "✅ تمت استعادة المحفظة محلياً!"
                        st.rerun()
                except Exception:
                    st.error("⚠️ ملف JSON غير صالح.")

# ==============================================================================
# التبويب 3: مختبر التحليل المؤسسي الشامل (10 تبويبات مستقلة لكل مدرسة)
# ==============================================================================
if VIEW == "lab":
    if not all_analyzed_map:
        st.warning("⚠️ جاري تحميل بيانات الأسهم...")
    else:
        port_set = {p["الرمز"] for p in portfolio_rows}
        radar_set = {r["الرمز"] for r in filtered_results}
        ordered_symbols = sorted(list(port_set)) + [r["الرمز"] for r in filtered_results if r["الرمز"] not in port_set] + sorted([s for s in all_analyzed_map if s not in port_set and s not in radar_set])

        if st.session_state.get("lab_sym") not in ordered_symbols:
            st.session_state.pop("lab_sym", None)
        selected_symbol = st.selectbox(
            f"🔬 اختر السهم للدراسة العميقة ({len(ordered_symbols)} سهم — اكتب الرمز للبحث الفوري):",
            options=ordered_symbols,
            format_func=lambda s: f"{'💼 [محفظتي] ' if s in port_set else ('🎯 [رادار] ' if s in radar_set else '📌 ')}{s} — {all_analyzed_map[s]['اسم الشركة']} | {all_analyzed_map[s]['الرأي اللحظي']} | سكور: {all_analyzed_map[s]['السكور']}/100",
            key="lab_sym"
        )
        selected_data = all_analyzed_map[selected_symbol]
        chg_s = selected_data["التغير %"]
        # Prefetch history once (V11.4) — avoids 7 redundant yfinance calls
        with st.spinner("جاري تحميل البيانات التاريخية..."):
            _lab_df = fetch_single_stock_history(selected_data["Ticker"])

        mtf_txt = schools.weekly_trend(_lab_df)  # V11.5: أسبوع البورصة بيقفل الخميس

        st.markdown(f"""
        <div class="stock-header-strip">
            <div>
                <span class="txt-cyan" style="font-size:22px;font-weight:900;">{selected_symbol}</span>
                <span class="txt-gold" style="font-size:17px;font-weight:800;margin-right:10px;">{selected_data['اسم الشركة']}</span>
                <div style="font-size:13px;color:var(--muted);margin-top:3px;">{selected_data['التشخيص الفني']}</div>
                <div style="font-size:11px;color:var(--down);margin-top:2px;">{("📡 <b>Live only</b> (TradingView) — التحليل التاريخي (SMC/Wyckoff/...) غير متوفر. استخدم التدفق اللحظي للقرار." if not _lab_df.shape[0] else "📊 <b>Live + History</b> (TradingView + Yahoo) — التحليل التاريخي متاح.")}</div>
                <div style="font-size:11px;color:var(--muted);margin-top:2px;">📡 التدفق اللحظي: TradingView (100% EGX) | 📊 التاريخي: Yahoo Finance (محدود)</div>
                <div style="font-size:12px;margin-top:4px;"><b>MTF:</b> {mtf_txt}</div>
            </div>
            <div style="display:flex;gap:18px;align-items:center;flex-wrap:wrap;">
                <div><span class="txt-muted" style="font-size:12px;">السعر اللحظي</span><div class="txt-white" style="font-size:18px;font-weight:900;">{selected_data['الإغلاق']} ج.م <span class="{'txt-green' if chg_s>=0 else 'txt-red'}" style="font-size:13px;">({chg_s:+.2f}%)</span></div></div>
                <div><span class="txt-muted" style="font-size:12px;">السكور العام</span><div class="txt-cyan" style="font-size:18px;font-weight:900;">{selected_data['السكور']}/100</div></div>
                <div><span class="txt-muted" style="font-size:12px;">الوقف المقترح</span><div class="txt-red" style="font-size:18px;font-weight:900;">{selected_data['الوقف (2xATR)']}</div></div>
                <div><span class="txt-muted" style="font-size:12px;">الهدف الأول</span><div class="txt-green" style="font-size:18px;font-weight:900;">{selected_data['TP1']}</div></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        t_conf, t_flow, t_smc, t_wyk, t_cpr, t_candle, t_sr, t_tech, t_fund, t_gann, t_exp, t_news, t_bt, t_upload = st.tabs([
            "🧭 الإجماع",
            "⚡ تدفق",
            "🏦 SMC",
            "🐋 وايكوف",
            "🎯 CPR",
            "🕯️ شموع",
            "📏 دعم/مقاومة",
            "📈 شارت",
            "📊 مالي",
            "🪐 جان (مبسط)",
            "🔬 تجريبي",
            "📰 أخبار",
            "🧪 Backtest",
            "📥 رفع بيانات"
        ], key="lab_tabs", on_change="rerun")  # V11.5: التبويبات التقيلة (مالي/أخبار) بتتحمل لما تفتحها بس

        # 0) ملخص الإجماع بين المدارس (V11.5)
        with t_conf:
            st.markdown("#### 🧭 إجماع المدارس — مين متفق ومين مختلف؟")
            if _lab_df.empty or len(_lab_df) < 60:
                st.info("ℹ️ البيانات التاريخية غير كافية لحساب الإجماع. استخدم تبويب ⚡ تدفق.")
            else:
                conf = schools.confluence_summary(_lab_df, selected_data)
                cc1, cc2 = st.columns([1, 2])
                cc1.markdown(f'<div class="kpi-card"><div class="kpi-label">درجة الإجماع (−100 → +100)</div><div class="kpi-val {"txt-green" if conf["score"]>=40 else ("txt-red" if conf["score"]<=-40 else "txt-gold")}">{conf["score"]:+d}</div><div style="font-size:13px;margin-top:4px;">{conf["label"]}</div></div>', unsafe_allow_html=True)
                with cc2:
                    st.dataframe(pd.DataFrame(conf["rows"]), width="stretch", hide_index=True)
                st.caption(f"متوسط قيمة التداول اليومي (20 جلسة): {conf['adv']/1e6:,.2f} مليون ج.م — "
                           "الأوزان حسب قوة الأدلة: الاتجاه والسيولة أعلى، الشموع أقل، وجان/هارمونيك/إليوت مالهمش وزن.")
                if conf["liquidity_warning"]:
                    st.warning(conf["liquidity_warning"])

        # 1) التدفق اللحظي وعمق السيولة الأوتوماتيكي 100%
        with t_flow:
            flow = selected_data["intraday_flow"]
            tv_r = selected_data.get("tv_raw", {})
            fk1, fk2, fk3, fk4 = st.columns(4)
            fk1.markdown(f'<div class="kpi-card"><div class="kpi-label">🧭 القرار اللحظي</div><div class="kpi-val" style="font-size:16px;">{flow["short_verdict"]} ({flow["flow_score"]:+d})</div></div>', unsafe_allow_html=True)
            fk2.markdown(f'<div class="kpi-card"><div class="kpi-label">⚖️ متوسط السيولة VWAP</div><div class="kpi-val {"txt-green" if flow["vwap_diff_pct"]>=0 else "txt-red"}">{flow["vwap"]} ({flow["vwap_diff_pct"]:+.2f}%)</div></div>', unsafe_allow_html=True)
            fk3.markdown(f'<div class="kpi-card"><div class="kpi-label">⏱️ زخم 15 دقيقة (RSI)</div><div class="kpi-val txt-cyan">{flow["rsi15"]}</div></div>', unsafe_allow_html=True)
            fk4.markdown(f'<div class="kpi-card" style="border-top-color:var(--gold);"><div class="kpi-label">💧 وتيرة السيولة الآن</div><div class="kpi-val txt-gold">{flow["rel_vol"]}x</div></div>', unsafe_allow_html=True)
            st.write("")
            fl1, fl2 = st.columns([1.15, 1])
            with fl1:
                reasons_html = "".join([f"<li style='margin-bottom:6px;'>{x}</li>" for x in flow["reasons"]])
                st.markdown(f"""
                <div class="pro-card">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                        <h4 class="txt-cyan" style="margin:0;">🩺 التشخيص اللحظي</h4>
                        <span class="{flow['badge_cls']}">{flow['verdict']}</span>
                    </div>
                    <p class="txt-white"><b>أفضل طلب وعرض:</b> {flow['ba_pressure']} (السبريد: {flow['spread_pct']}%)</p>
                    <ul class="txt-white" style="padding-right:18px;font-size:14px;">{reasons_html}</ul>
                    <div style="background:var(--bg2);padding:10px;border-radius:8px;border-right:4px solid var(--accent);">
                        <b class="txt-gold">💡 التوجيه:</b> <span class="txt-white">{flow['action_hint']}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            with fl2:
                bid_sz = float(tv_r.get("bid_size") or 0.0)
                ask_sz = float(tv_r.get("ask_size") or 0.0)
                tot_vol = float(tv_r.get("volume") or 0.0)
                clv_ratio = flow["clv_pct"] / 100.0

                if (bid_sz + ask_sz) > 0:
                    imb_auto = ((bid_sz - ask_sz) / (bid_sz + ask_sz)) * 100.0
                    st.markdown(f"""
                    <div class="pro-card" style="border-right-color:var(--gold);">
                        <h4 class="txt-gold" style="margin-top:0;">📖 عمق أفضل طلب وعرض (سحب تلقائي)</h4>
                        <p class="txt-white">🟢 كمية الطلب (Bid Size): <b>{bid_sz:,.0f}</b> &nbsp;|&nbsp; 🔴 كمية العرض (Ask Size): <b>{ask_sz:,.0f}</b></p>
                        <p class="txt-white" style="margin-bottom:0;"><b>نسبة التفوق اللحظي:</b> <span class="{'txt-green' if imb_auto>=0 else 'txt-red'}" style="font-size:18px;font-weight:900;">{imb_auto:+.1f}%</span></p>
                    </div>
                    """, unsafe_allow_html=True)

                buy_vol_est = tot_vol * clv_ratio
                sell_vol_est = tot_vol * (1.0 - clv_ratio)
                net_delta = buy_vol_est - sell_vol_est
                delta_pct = ((buy_vol_est - sell_vol_est) / max(1.0, tot_vol)) * 100.0
                buy_bar_w = max(5, min(95, int(round(clv_ratio * 100))))
                delta_verdict = (
                    "🟢 سيطرة شرائية منفذة (تجميع مؤسسي حقيقي)"
                    if delta_pct >= 15 else
                    ("🔴 ضغط بيعي منفذ (تصريف)" if delta_pct <= -15 else "🟡 توازن بين المشتري والبائع")
                )

                st.markdown(f"""
                <div class="pro-card" style="border-right-color:var(--accent);">
                    <h4 class="txt-cyan" style="margin-top:0;">⚖️ صافي التدفق المنفذ (Order Flow Delta — أوتوماتيك)</h4>
                    <p class="txt-muted" style="font-size:12px;">تحليل تلقائي لحجم السيولة المنفذة فعلياً على العرض مقابل الطلب دون أي إدخال يدوي:</p>
                    <div style="display:flex;justify-content:space-between;font-size:13px;font-weight:700;margin-bottom:4px;">
                        <span class="txt-green">🟢 شراء منفذ: {buy_vol_est:,.0f} ({buy_bar_w}%)</span>
                        <span class="txt-red">🔴 بيع منفذ: {sell_vol_est:,.0f} ({100-buy_bar_w}%)</span>
                    </div>
                    <div style="width:100%;height:10px;background:var(--down);border-radius:999px;overflow:hidden;margin-bottom:10px;">
                        <div style="width:{buy_bar_w}%;height:100%;background:var(--up);"></div>
                    </div>
                    <p class="txt-white">📊 صافي الدلتا (Net Delta): <b class="{'txt-green' if net_delta>=0 else 'txt-red'}">{net_delta:+,.0f} سهم ({delta_pct:+.1f}%)</b></p>
                    <div style="background:var(--bg2);padding:9px 12px;border-radius:8px;">
                        <b>الخلاصة اللحظية:</b> {delta_verdict}
                    </div>
                </div>
                """, unsafe_allow_html=True)

        # 2) الأموال الذكية و ICT
        with t_smc:
            df_h = _lab_df
            if df_h.empty or len(df_h) < 30:
                st.info("ℹ️ البيانات التاريخية غير كافية لرسم مناطق SMC لهذا السهم.")
            else:
                smc = analyze_smc_ict(df_h)
                c1, c2 = st.columns([2.1, 1])
                with c1:
                    sub_c = df_h.tail(90)
                    fig_smc = go.Figure(go.Candlestick(x=sub_c.index, open=sub_c["Open"], high=sub_c["High"], low=sub_c["Low"], close=sub_c["Close"], name="السعر"))
                    for fvg in smc["fvgs"]:
                        col_f = "rgba(34,197,94,0.22)" if "شرائية" in fvg["النوع"] else "rgba(239,68,68,0.22)"
                        fig_smc.add_hrect(y0=fvg["من"], y1=fvg["إلى"], fillcolor=col_f, line_width=0, annotation_text="FVG", annotation_font_size=10)
                    for ob in smc["obs"]:
                        col_o = PAL["up"] if "طلب" in ob["النوع"] else PAL["down"]
                        fig_smc.add_hrect(y0=ob["من"], y1=ob["إلى"], line_dash="dot", line_color=col_o, fillcolor="rgba(56,189,248,0.08)", annotation_text="OB", annotation_font_size=10)
                    fig_smc.update_layout(title=f"🏦 مناطق Order Blocks و FVG لسهم {selected_symbol}", height=500, xaxis_rangeslider_visible=False, template=TPL, margin=dict(l=10, r=10, t=40, b=10))
                    st.plotly_chart(fig_smc, width="stretch")
                with c2:
                    sweeps_html = "".join([f"<li>{s}</li>" for s in smc["sweeps"]]) if smc["sweeps"] else "<li>لا يوجد سحب سيولة حاد في آخر 10 جلسات.</li>"
                    st.markdown(f"""
                    <div class="pro-card">
                        <h4 class="txt-cyan" style="margin-top:0;">🧭 هيكل السوق المؤسسي</h4>
                        <p><span class="{smc['badge_cls']}">{smc['structure']}</span></p>
                        <p class="txt-white"><b>قمة الهيكل (Swing High):</b> {smc['swing_high'] or '—'} | <b>قاع الهيكل:</b> {smc['swing_low'] or '—'}</p>
                        <hr style="border-color:var(--border);">
                        <b class="txt-gold">🎯 رصد سحب السيولة (Liquidity Sweeps):</b>
                        <ul class="txt-white" style="padding-right:18px;font-size:13px;">{sweeps_html}</ul>
                    </div>
                    """, unsafe_allow_html=True)
                    if smc["obs"]:
                        st.markdown("##### 🧱 كتل الأوامر (Order Blocks)")
                        st.dataframe(pd.DataFrame(smc["obs"]), width="stretch", hide_index=True)
                    if smc["fvgs"]:
                        st.markdown("##### 🕳️ فجوات القيمة العادلة (FVG)")
                        st.dataframe(pd.DataFrame(smc["fvgs"]), width="stretch", hide_index=True)

        # 3) وايكوف و PVSRA
        with t_wyk:
            df_h = fetch_single_stock_history(selected_data["Ticker"])
            if df_h.empty or len(df_h) < 40:
                st.info("ℹ️ البيانات التاريخية غير كافية لتحليل وايكوف لهذا السهم.")
            else:
                wyk = analyze_wyckoff_vsa(df_h)
                c1, c2 = st.columns([2.1, 1])
                with c1:
                    sub_w = df_h.tail(90)
                    fig_w = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.04, row_heights=[0.72, 0.28])
                    fig_w.add_trace(go.Candlestick(x=sub_w.index, open=sub_w["Open"], high=sub_w["High"], low=sub_w["Low"], close=sub_w["Close"], name="السعر"), row=1, col=1)
                    fig_w.add_hline(y=wyk["box_high"], line_dash="dash", line_color="#FACC15", annotation_text=f"سقف النطاق: {wyk['box_high']}", row=1, col=1)
                    fig_w.add_hline(y=wyk["box_low"], line_dash="dash", line_color="#38BDF8", annotation_text=f"قاع النطاق: {wyk['box_low']}", row=1, col=1)
                    v_cols = []
                    for _, r in sub_w.iterrows():
                        vr = r["Volume"] / max(1.0, r["VolSMA20"]) if pd.notna(r["VolSMA20"]) else 1.0
                        if vr >= 2.0:
                            v_cols.append("#00E5FF" if r["Close"] >= r["Open"] else "#D500F9")
                        else:
                            v_cols.append(PAL["up"] if r["Close"] >= r["Open"] else PAL["down"])
                    fig_w.add_trace(go.Bar(x=sub_w.index, y=sub_w["Volume"], marker_color=v_cols, name="PVSRA Volume"), row=2, col=1)
                    fig_w.add_trace(go.Scatter(x=sub_w.index, y=sub_w["VolSMA20"], line=dict(color="#FACC15", width=1.4), name="متوسط 20"), row=2, col=1)
                    fig_w.update_layout(title=f"🐋 بصمة الحيتان PVSRA ونطاق وايكوف: {selected_symbol}", height=500, xaxis_rangeslider_visible=False, template=TPL, margin=dict(l=10, r=10, t=40, b=10))
                    st.plotly_chart(fig_w, width="stretch")
                with c2:
                    notes_html = "".join([f"<li style='margin-bottom:6px;'>{n}</li>" for n in wyk["vsa_notes"]])
                    st.markdown(f"""
                    <div class="pro-card">
                        <h4 class="txt-cyan" style="margin-top:0;">📊 مرحلة السهم وفق وايكوف</h4>
                        <p><span class="{wyk['badge_cls']}">{wyk['phase']}</span></p>
                        <p class="txt-white"><b>سقف النطاق:</b> {wyk['box_high']} | <b>قاع النطاق:</b> {wyk['box_low']}</p>
                        <p class="txt-white"><b>نسبة فوليوم آخر جلسة:</b> <span class="txt-gold">{wyk['vol_ratio']}x</span></p>
                        <hr style="border-color:var(--border);">
                        <ul class="txt-white" style="padding-right:18px;font-size:13px;">{notes_html}</ul>
                    </div>
                    """, unsafe_allow_html=True)
                    if wyk["whale_candles"]:
                        st.markdown("##### 🐋 أحدث شموع الحيتان (PVSRA ≥ 2.0x)")
                        st.dataframe(pd.DataFrame(wyk["whale_candles"]), width="stretch", hide_index=True)

        # 4) CPR وبروفايل السيولة
        with t_cpr:
            df_h = fetch_single_stock_history(selected_data["Ticker"])
            if df_h.empty or len(df_h) < 30:
                st.info("ℹ️ البيانات التاريخية غير كافية لحساب بروفايل السيولة.")
            else:
                cvp = analyze_cpr_and_vp(df_h)
                c1, c2 = st.columns([2.2, 1])
                with c1:
                    sub_v = df_h.tail(90)
                    fig_vp = make_subplots(rows=1, cols=2, shared_yaxes=True, column_widths=[0.76, 0.24], horizontal_spacing=0.02)
                    fig_vp.add_trace(go.Candlestick(x=sub_v.index, open=sub_v["Open"], high=sub_v["High"], low=sub_v["Low"], close=sub_v["Close"], name="السعر"), row=1, col=1)
                    fig_vp.add_hline(y=cvp["poc"], line_color="#FACC15", line_width=2.2, annotation_text=f"POC: {cvp['poc']}", row=1, col=1)
                    fig_vp.add_hline(y=cvp["vah"], line_dash="dash", line_color=PAL["up"], annotation_text=f"VAH: {cvp['vah']}", row=1, col=1)
                    fig_vp.add_hline(y=cvp["val"], line_dash="dash", line_color=PAL["down"], annotation_text=f"VAL: {cvp['val']}", row=1, col=1)
                    fig_vp.add_hrect(y0=cvp["bc"], y1=cvp["tc"], fillcolor="rgba(56,189,248,0.18)", line_color="#38BDF8", line_dash="dot", annotation_text="CPR", row=1, col=1)
                    vp_colors = [PAL["gold"] if round(p, 4) == cvp["poc"] else PAL["accent"] for p in cvp["bin_centers"]]
                    fig_vp.add_trace(go.Bar(y=cvp["bin_centers"], x=cvp["vol_hist"], orientation="h", marker_color=vp_colors, name="Volume Profile"), row=1, col=2)
                    fig_vp.update_layout(title=f"🎯 خريطة CPR وبروفايل السيولة الأفقي: {selected_symbol}", height=510, xaxis_rangeslider_visible=False, template=TPL, showlegend=False, margin=dict(l=10, r=10, t=40, b=10))
                    st.plotly_chart(fig_vp, width="stretch")
                with c2:
                    st.markdown(f"""
                    <div class="pro-card">
                        <h4 class="txt-cyan" style="margin-top:0;">📐 مستويات صناع السوق</h4>
                        <p><span class="{cvp['badge_cls']}">{cvp['verdict']}</span></p>
                        <p class="txt-white"><b>نقطة التحكم (POC):</b> <span class="txt-gold" style="font-weight:bold;">{cvp['poc']} ج.م</span></p>
                        <p class="txt-white"><b>أعلى منطقة القيمة (VAH):</b> <span class="txt-green">{cvp['vah']}</span></p>
                        <p class="txt-white"><b>أدنى منطقة القيمة (VAL):</b> <span class="txt-red">{cvp['val']}</span></p>
                        <hr style="border-color:var(--border);">
                        <p class="txt-white"><b>نطاق CPR:</b> {cvp['bc']} — {cvp['tc']} (Pivot: {cvp['pivot']})</p>
                        <p class="txt-white"><b>عرض النطاق:</b> {cvp['cpr_width_pct']}% {'🔥 (ضيق — انفجار سعري وشيك)' if cvp['cpr_width_pct'] <= 2.5 else ''}</p>
                        <p class="txt-white"><b>مقاومة R1:</b> {cvp['r1']} | <b>دعم S1:</b> {cvp['s1']}</p>
                    </div>
                    """, unsafe_allow_html=True)

        # 5) Candlestick Patterns (V11.4)
        with t_candle:
            st.markdown("#### 🕯️ أنماط الشموع (Candlestick Patterns) — V11.4")
            if _lab_df.empty or len(_lab_df) < 10:
                st.info("ℹ️ البيانات التاريخية غير كافية.")
            else:
                cp = analyze_candlestick_patterns(_lab_df)
                st.markdown("**Verdict:** %s" % cp["verdict"])
                if cp["patterns"]:
                    st.dataframe(pd.DataFrame(cp["patterns"]), width="stretch", hide_index=True)
                else:
                    st.info(cp["verdict"])
                # Show last 5 candles
                sub_c = _lab_df.tail(10)
                import plotly.graph_objects as _go
                fig_c = _go.Figure(_go.Candlestick(x=sub_c.index, open=sub_c["Open"], high=sub_c["High"], low=sub_c["Low"], close=sub_c["Close"], name="السعر"))
                fig_c.update_layout(title="Last 10 Candles", height=320, template=TPL, xaxis_rangeslider_visible=False, margin=dict(l=10,r=10,t=40,b=10))
                st.plotly_chart(fig_c, width="stretch")

        with t_sr:
            st.markdown("#### 📏 دعم/مقاومة (Support/Resistance) — V11.4")
            if _lab_df.empty or len(_lab_df) < 20:
                st.info("ℹ️ البيانات التاريخية غير كافية.")
            else:
                sr = analyze_support_resistance(_lab_df)
                st.markdown("**Verdict:** %s" % sr["verdict"])
                if sr["levels"]:
                    st.dataframe(pd.DataFrame(sr["levels"]), width="stretch", hide_index=True)
                if sr["nearest_support"]:
                    st.success("🟢 أقرب دعم: %s" % sr["nearest_support"])
                if sr["nearest_resistance"]:
                    st.warning("🔴 أقرب مقاومة: %s" % sr["nearest_resistance"])
                # Show chart with levels
                sub_sr = _lab_df.tail(60)
                import plotly.graph_objects as _go
                fig_sr = _go.Figure(_go.Candlestick(x=sub_sr.index, open=sub_sr["Open"], high=sub_sr["High"], low=sub_sr["Low"], close=sub_sr["Close"], name="السعر"))
                if sr["nearest_support"]:
                    fig_sr.add_hline(y=sr["nearest_support"], line_dash="dash", line_color=PAL["up"], annotation_text="Support")
                if sr["nearest_resistance"]:
                    fig_sr.add_hline(y=sr["nearest_resistance"], line_dash="dash", line_color=PAL["down"], annotation_text="Resistance")
                fig_sr.update_layout(title="Support/Resistance Levels", height=400, template=TPL, xaxis_rangeslider_visible=False, margin=dict(l=10,r=10,t=40,b=10))
                st.plotly_chart(fig_sr, width="stretch")

        with t_tech:
            df_h = fetch_single_stock_history(selected_data["Ticker"])
            c1, c2 = st.columns([2.1, 1])
            with c1:
                if df_h.empty:
                    st.info(f"ℹ️ السعر اللحظي الحالي: **{selected_data['الإغلاق']} ج.م**")
                    st.link_button(f"🚀 افتح {selected_symbol} على TradingView ↗", selected_data["TradingView"], width="stretch")
                else:
                    sub_f = df_h.tail(120)
                    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.04, row_heights=[0.74, 0.26])
                    fig.add_trace(go.Candlestick(x=sub_f.index, open=sub_f["Open"], high=sub_f["High"], low=sub_f["Low"], close=sub_f["Close"], name="السعر"), row=1, col=1)
                    fig.add_trace(go.Scatter(x=sub_f.index, y=sub_f["EMA20"], line=dict(color="#A855F7", width=1.3), name="EMA 20"), row=1, col=1)
                    fig.add_trace(go.Scatter(x=sub_f.index, y=sub_f["EMA50"], line=dict(color="#38BDF8", width=1.6), name="EMA 50"), row=1, col=1)
                    fig.add_trace(go.Scatter(x=sub_f.index, y=sub_f["EMA200"], line=dict(color="#F59E0B", width=2.2), name="EMA 200"), row=1, col=1)
                    fig.add_hline(y=selected_data["الوقف (2xATR)"], line_dash="dash", line_color=PAL["down"], annotation_text="SL", row=1, col=1)
                    fig.add_hline(y=selected_data["TP1"], line_dash="dash", line_color=PAL["up"], annotation_text="TP1", row=1, col=1)
                    fig.add_trace(go.Bar(x=sub_f.index, y=sub_f["Volume"], marker_color=[PAL["up"] if c >= o else PAL["down"] for c, o in zip(sub_f["Close"], sub_f["Open"])], name="الفوليوم"), row=2, col=1)
                    fig.update_layout(title=f"📈 الشارت الفني ومستويات التنفيذ: {selected_symbol} ({selected_data['اسم الشركة']})", height=520, xaxis_rangeslider_visible=False, template=TPL, margin=dict(l=10, r=10, t=40, b=10))
                    st.plotly_chart(fig, width="stretch")
            with c2:
                st.markdown(f"""
                <div class="pro-card">
                    <h4 class="txt-cyan" style="margin-top:0;">📌 خطة التنفيذ: {selected_symbol}</h4>
                    <p><span class="badge-bull">{selected_data['نوع الإشارة']}</span> &nbsp; <b>السكور: {selected_data['السكور']}/100</b></p>
                    <p class="txt-muted" style="font-size:13px;">{selected_data['التشخيص الفني']}</p>
                    <hr style="border-color:var(--border);">
                    <p class="txt-white"><b>الدخول المرجعي:</b> {selected_data['الإغلاق']} ج.م</p>
                    <p class="txt-white"><b>الوقف (2×ATR):</b> <span class="txt-red">{selected_data['الوقف (2xATR)']}</span></p>
                    <p class="txt-white"><b>TP1:</b> <span class="txt-green">{selected_data['TP1']}</span> | <b>TP2:</b> <span class="txt-green">{selected_data['TP2']}</span> | <b>TP3:</b> <span class="txt-green">{selected_data['TP3']}</span></p>
                    <p class="txt-white"><b>حجم الصفقة المقترح:</b> {selected_data['الأسهم']:,} سهم (صافي TP1: {selected_data['صافي TP1']:,.0f} ج.م)</p>
                </div>
                """, unsafe_allow_html=True)
                st.link_button("🚀 افتح على TradingView ↗", selected_data["TradingView"], width="stretch")

        # 8) التحليل المالي
        with t_fund:
            fund = fetch_fundamental_analysis(selected_data["Ticker"]) if t_fund.open else {"error": "lazy"}
            if not t_fund.open:
                pass
            elif "error" in fund:
                st.warning("⚠️ تعذر جلب القوائم المالية التفصيلية لهذا السهم.")
            else:
                f1, f2 = st.columns([1, 1.5])
                with f1:
                    st.markdown(f"""
                    <div class="pro-card">
                        <h4 class="txt-cyan" style="margin-top:0;">🏢 بطاقة التقييم المالي</h4>
                        <p class="txt-white"><b>القطاع:</b> {fund['sector']}</p>
                        <p class="txt-white"><b>درجة المتانة (F-Score):</b> <span class="badge-bull">{fund['f_score']} / {fund['tests_available']}</span></p>
                        <p class="txt-white"><b>مكرر الربحية (P/E):</b> {f"{fund['pe']:.1f}x" if fund.get('pe') else '—'}</p>
                        <p class="txt-white"><b>مضاعف الدفترية (P/B):</b> {f"{fund['pb']:.2f}x" if fund.get('pb') else '—'}</p>
                        <p class="txt-white"><b>العائد على حقوق الملكية (ROE):</b> {f"{fund['roe']*100:.1f}%" if fund.get('roe') else '—'}</p>
                    </div>
                    """, unsafe_allow_html=True)
                with f2:
                    if fund["breakdown"]:
                        dff = pd.DataFrame(fund["breakdown"], columns=["المعيار", "القيمة", "النتيجة"])
                        dff["النتيجة"] = dff["النتيجة"].map({True: "✅ ناجح (+1)", False: "❌ لم يتحقق"})
                        st.dataframe(dff, width="stretch", hide_index=True)
                    # تقويم الأرباح والكوبونات (V11.4)
                    st.markdown("##### 📅 تقويم الأرباح والكوبونات")
                    cal_rows = []
                    if fund.get("ex_dividend"):
                        cal_rows.append({"الحدث": "تاريخ الاستحقاق (Ex-Dividend)", "التاريخ/القيمة": fund["ex_dividend"]})
                    if fund.get("dividend_rate"):
                        cal_rows.append({"الحدث": "معدل التوزيع (Dividend Rate)", "التاريخ/القيمة": fund["dividend_rate"]})
                    if fund.get("div_yield"):
                        cal_rows.append({"الحدث": "عائد التوزيع (Yield)", "التاريخ/القيمة": f"{fund['div_yield']*100:.2f}%"})
                    if fund.get("payout_ratio"):
                        cal_rows.append({"الحدث": "نسبة التوزيع (Payout)", "التاريخ/القيمة": f"{fund['payout_ratio']*100:.1f}%"})
                    cal = fund.get("calendar") or {}
                    if isinstance(cal, dict):
                        for k, v in cal.items():
                            cal_rows.append({"الحدث": str(k), "التanggal/القيمة" if False else "التاريخ/القيمة": str(v)[:60]})
                    if cal_rows:
                        st.dataframe(pd.DataFrame(cal_rows), width="stretch", hide_index=True)
                    else:
                        st.caption("ℹ️ لا توجد بيانات تقويم متاحة لهذا السهم.")

        # 9) التحليل الزمني
        with t_gann:
            df_t = _lab_df
            if df_t.empty:
                st.info("ℹ️ البيانات التاريخية غير متوفرة لرسم خريطة جان.")
            else:
                r90 = df_t.tail(90)
                low_idx = r90["Low"].idxmin()
                g1, g2, g3 = st.columns(3)
                piv_d = g1.date_input("📅 تاريخ القاع/القمة الارتكازية:", value=low_idx.date(), key="gann_piv_d")
                piv_p = g2.number_input("💲 سعر الارتكاز:", min_value=0.01, value=float(r90.loc[low_idx, "Low"]), step=0.05, key="gann_piv_p")
                is_low = g3.radio("نوع الارتكاز:", ["قاع صاعد", "قمة هابطة"], horizontal=True, key="gann_is_low") == "قاع صاعد"

                sq9, g_times = compute_gann_simple(piv_d, piv_p, is_low, selected_data["الإغلاق"])
                st.markdown("##### 📐 مربع التسعة (Square of 9) — مستويات سعرية")
                st.dataframe(pd.DataFrame(sq9), width="stretch", hide_index=True)
                st.markdown("##### ⏱️ دورات جان (Time Cycles) — متى تحدث انعكاسات؟")
                if g_times:
                    st.dataframe(pd.DataFrame(g_times), width="stretch", hide_index=True)
                else:
                    st.info("لا توجد دورات في النطاق (±30 إلى 180 يوم).")
                st.caption("💡 مربع التسعة = مستويات دعم/مقاومة (سعر). دورات جان = تواريخ انعكاس (زمن). ⚠️ مفيش دليل إحصائي على جان — للاستئناس فقط.")
                with st.expander("🪐 الخريطة الفلكية (بدون أي دليل إحصائي — للفضول فقط)"):
                    _now_c = get_cairo_now()
                    _pos = get_planetary_longitudes(_now_c.replace(tzinfo=None))
                    st.dataframe(pd.DataFrame([{"الكوكب": k, "البرج": deg_to_zodiac(v), "الطول °": round(v, 1)} for k, v in _pos.items()]), width="stretch", hide_index=True)
                    _asp = schools.upcoming_aspects(_now_c.date(), 30)
                    if _asp:
                        st.dataframe(pd.DataFrame(_asp), width="stretch", hide_index=True)

        # 9b) هارمونيك + إليوت (تجريبي، V11.5)
        with t_exp:
            st.warning("🔬 الهارمونيك وإليوت مدارس تفسيرية أدلتها الإحصائية ضعيفة — متدخلش بيها لوحدها، ومش داخلة في الإجماع.")
            if _lab_df.empty or len(_lab_df) < 60:
                st.info("ℹ️ البيانات التاريخية غير كافية.")
            else:
                ex1, ex2 = st.columns(2)
                with ex1:
                    hm = analyze_harmonic_patterns(_lab_df)
                    st.markdown(f"##### 🦋 الهارمونيك: <span class='{hm['badge_cls']}'>{hm['pattern_name']}</span>", unsafe_allow_html=True)
                    st.caption(hm["notes"])
                    if hm["detected"]:
                        st.markdown(f"**PRZ:** {hm['prz_low']} — {hm['prz_high']} | **T1:** {hm['target_1']} | **T2:** {hm['target_2']}")
                with ex2:
                    ew = analyze_elliott_waves(_lab_df.tail(250))
                    st.markdown(f"##### 🌊 إليوت: <span class='{ew['badge_cls']}'>{ew['wave_name']}</span>", unsafe_allow_html=True)
                    st.caption(ew["summary"])
                    if ew["rules_check"]:
                        st.dataframe(pd.DataFrame([{"القاعدة": r[0], "القيمة": r[1], "": "✅" if r[2] else "❌"} for r in ew["rules_check"]]), width="stretch", hide_index=True)

        # 10) الرادار الخبري
        with t_news:
            news_items = fetch_stock_news(selected_symbol, selected_data.get("اسم الشركة", "")) if t_news.open else None
            if news_items is None:
                pass
            elif not news_items:
                st.info("ℹ️ لا توجد أخبار حديثة منشورة لهذا السهم حالياً.")
            else:
                for n in news_items:
                    st.markdown(f"""
                    <div class="news-item">
                        <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
                            <span class="{n['badge']}">{n['sentiment']}</span>
                            <span class="txt-muted" style="font-size:12px;">{n['source']}</span>
                        </div>
                        <a href="{n['link']}" target="_blank" class="txt-white" style="text-decoration:none;font-weight:700;">{n['title']} ↗</a>
                    </div>
                    """, unsafe_allow_html=True)

        # 11) Backtest (V11.4)
        with t_bt:
            st.markdown("#### 🧪 Backtest — استراتيجية close>EMA20>EMA50 + RVOL")
            st.caption("V11.5: الدخول على افتتاح الجلسة التالية، الوقف 2×ATR14 حقيقي، الفجوات بتتنفذ بسعر الافتتاح، انزلاق 0.2% + الرسوم على الجانبين. النتايج الماضية مش ضمان.")
            btc1, btc2, btc3 = st.columns(3)
            with btc1:
                bt_sym = st.selectbox("السهم:", options=ordered_symbols, key="bt_sym_sel", format_func=lambda s: "%s — %s" % (s, all_analyzed_map[s]["اسم الشركة"]))
            with btc2:
                bt_cap = st.number_input("رأس المال (ج.م):", min_value=1000.0, value=100000.0, step=5000.0, key="bt_cap")
            with btc3:
                bt_risk = st.slider("نسبة المخاطرة %:", 0.5, 5.0, 1.5, 0.25, key="bt_risk")
            if st.button("🚀 تشغيل Backtest", key="bt_run_btn", type="primary"):
                _df_bt = fetch_single_stock_history(all_analyzed_map[bt_sym]["Ticker"])
                res = run_simple_backtest(_df_bt, capital=bt_cap, risk_pct=bt_risk, fee_rate=fee_rate)
                m = res["metrics"]
                if not res["trades"]:
                    st.warning("⚠️ لا توجد صفقات في هذه الفترة.")
                else:
                    b1, b2, b3, b4 = st.columns(4)
                    b1.markdown('<div class="kpi-card"><div class="kpi-label">📊 صفقات</div><div class="kpi-val">%d</div></div>' % m["trades"], unsafe_allow_html=True)
                    b2.markdown('<div class="kpi-card"><div class="kpi-label">🎯 Win Rate</div><div class="kpi-val txt-cyan">%.1f%%</div></div>' % m["win_rate"], unsafe_allow_html=True)
                    b3.markdown('<div class="kpi-card"><div class="kpi-label">⚖️ Profit Factor</div><div class="kpi-val txt-gold">%.2fx</div></div>' % m["profit_factor"], unsafe_allow_html=True)
                    b4.markdown('<div class="kpi-card"><div class="kpi-label">💰 العائد %%</div><div class="kpi-val %s">%+.2f%%</div></div>' % (("txt-green" if m["return_pct"]>=0 else "txt-red"), m["return_pct"]), unsafe_allow_html=True)
                    b5, b6, b7, b8 = st.columns(4)
                    b5.markdown(f'<div class="kpi-card"><div class="kpi-label">💵 صافي الربح</div><div class="kpi-val {"txt-green" if m["total_pnl"]>=0 else "txt-red"}">{m["total_pnl"]:+,.0f}</div></div>', unsafe_allow_html=True)
                    b6.markdown(f'<div class="kpi-card"><div class="kpi-label">⬇️ Max DD</div><div class="kpi-val txt-red">{m["max_drawdown"]:,.0f}</div></div>', unsafe_allow_html=True)
                    b7.markdown('<div class="kpi-card"><div class="kpi-label">🏆 Wins</div><div class="kpi-val txt-green">%d</div></div>' % m["wins"], unsafe_allow_html=True)
                    b8.markdown('<div class="kpi-card"><div class="kpi-label">💔 Losses</div><div class="kpi-val txt-red">%d</div></div>' % m["losses"], unsafe_allow_html=True)
                    _edge = m["return_pct"] - m["buy_hold_pct"]
                    st.info(f"📐 متوسط الصفقة: **{m['avg_R']:+.2f}R** | الشراء والاحتفاظ لنفس الفترة: **{m['buy_hold_pct']:+.2f}%** | "
                            f"الاستراتيجية {'أحسن' if _edge >= 0 else 'أسوأ'} بـ **{abs(_edge):.2f}** نقطة مئوية.")
                    if res["equity"]:
                        import plotly.graph_objects as _go
                        _fig_eq = _go.Figure(_go.Scatter(y=res["equity"], mode="lines", line=dict(color=PAL["accent"], width=2.5), fill="tozeroy", fillcolor=PAL["glow"]))
                        _fig_eq.update_layout(title="Equity Curve", height=320, template=TPL, margin=dict(l=10,r=10,t=40,b=10))
                        st.plotly_chart(_fig_eq, width="stretch")
                    st.dataframe(pd.DataFrame(res["trades"]), width="stretch", hide_index=True)


        # 12) Manual Historical Data Upload (V11.4)
        with t_upload:
            st.markdown("#### 📥 رفع بيانات تاريخية (CSV/Excel) — حل لأسهم EGX بدون Yahoo")
            st.info("💡 **كيفية الحصول على البيانات:** Mubasher/EGX → تصدير CSV/Excel (OHLCV) → رفع هنا. أو Yahoo Finance → download CSV.")
            up_file = st.file_uploader("📎 ارفع ملف CSV/Excel/PDF (أعمدة: Date, Open, High, Low, Close, Volume):", type=["csv", "xlsx", "xls", "pdf"], key="hist_upload")
            if up_file is not None:
                try:
                    if up_file.name.lower().endswith('.pdf'):
                        from pypdf import PdfReader
                        import io as _io, re as _re
                        _reader = PdfReader(_io.BytesIO(up_file.read()))
                        _full = '\n'.join([p.extract_text() or '' for p in _reader.pages])
                        _lines = [ln.strip() for ln in _full.splitlines() if ln.strip()]
                        _rows = []
                        for ln in _lines:
                            _m_date = None
                            for pat in [r'\d{4}-\d{2}-\d{2}', r'\d{2}/\d{2}/\d{4}', r'\d{2}-\d{2}-\d{4}']:
                                _mm = _re.search(pat, ln)
                                if _mm:
                                    _m_date = _mm.group(0)
                                    break
                            if not _m_date:
                                continue
                            _nums = [float(x) for x in _re.findall(r'\b\d+(?:\.\d+)?\b', ln)]
                            _date_nums = [int(x) for x in _re.findall(r'\b\d+\b', _m_date)]
                            _valid = [n for n in _nums if n not in _date_nums and 0.01 <= n <= 1e9]
                            if len(_valid) >= 4:
                                _rows.append([_m_date] + _valid[:5])
                        if not _rows:
                            st.warning('⚠️ لم يتم العثور على بيانات OHLCV في PDF. تأكد أن الملف يحتوي على جدول (Date, Open, High, Low, Close, Volume).')
                            _df_up = pd.DataFrame()
                        else:
                            _cols = ['Date'] + ['Open', 'High', 'Low', 'Close', 'Volume'][:len(_rows[0])-1]
                            _df_up = pd.DataFrame(_rows, columns=_cols)
                            for c in ['Open', 'High', 'Low', 'Close', 'Volume']:
                                if c not in _df_up.columns:
                                    _df_up[c] = 0.0
                    elif up_file.name.lower().endswith('.csv'):
                        _df_up = pd.read_csv(up_file)
                    else:
                        _df_up = pd.read_excel(up_file)
                    # Normalize column names
                    _df_up.columns = [str(c).strip().lower() for c in _df_up.columns]
                    col_map = {}
                    for c in _df_up.columns:
                        if c in ["date", "datetime", "time", "day"]:
                            col_map[c] = "Date"
                        elif c in ["open", "o"]:
                            col_map[c] = "Open"
                        elif c in ["high", "h"]:
                            col_map[c] = "High"
                        elif c in ["low", "l"]:
                            col_map[c] = "Low"
                        elif c in ["close", "c", "adj close", "adjusted close"]:
                            col_map[c] = "Close"
                        elif c in ["volume", "vol", "v"]:
                            col_map[c] = "Volume"
                    _df_up = _df_up.rename(columns=col_map)
                    if "Date" in _df_up.columns:
                        _df_up["Date"] = pd.to_datetime(_df_up["Date"], errors="coerce")
                        _df_up = _df_up.dropna(subset=["Date"]).set_index("Date").sort_index()
                    for c in ["Open", "High", "Low", "Close", "Volume"]:
                        if c in _df_up.columns:
                            _df_up[c] = pd.to_numeric(_df_up[c], errors="coerce")
                    _df_up = _df_up.dropna(subset=["Close", "High", "Low", "Open"])
                    if "Volume" not in _df_up.columns:
                        _df_up["Volume"] = 1.0
                    if len(_df_up) < 10:
                        st.warning("⚠️ بيانات غير كافية (أقل من 10 صفوف).")
                    else:
                        # Compute indicators
                        _df_up["EMA20"] = _df_up["Close"].ewm(span=20, adjust=False).mean()
                        _df_up["EMA50"] = _df_up["Close"].ewm(span=50, adjust=False).mean()
                        _df_up["EMA200"] = _df_up["Close"].ewm(span=200, adjust=False).mean() if len(_df_up) >= 200 else _df_up["Close"].ewm(span=50, adjust=False).mean()
                        _df_up["VolSMA20"] = _df_up["Volume"].rolling(20).mean()
                        tr = pd.concat([_df_up["High"]-_df_up["Low"], (_df_up["High"]-_df_up["Close"].shift(1)).abs(), (_df_up["Low"]-_df_up["Close"].shift(1)).abs()], axis=1).max(axis=1)
                        _df_up["ATR"] = tr.rolling(14).mean()
                        _df_up["ATR14"] = _df_up["ATR"]
                        st.success("✅ تم تحميل %d صف (من %s إلى %s)" % (len(_df_up), str(_df_up.index[0])[:10], str(_df_up.index[-1])[:10]))
                        # Show SMC
                        try:
                            smc = analyze_smc_ict(_df_up)
                            st.markdown("##### 🏦 SMC/ICT")
                            st.markdown(f"**الهيكل:** {smc['structure']}")
                            if smc["obs"]:
                                st.dataframe(pd.DataFrame(smc["obs"]), width="stretch", hide_index=True)
                            if smc["fvgs"]:
                                st.dataframe(pd.DataFrame(smc["fvgs"]), width="stretch", hide_index=True)
                            if smc["sweeps"]:
                                for sw in smc["sweeps"]:
                                    st.info(sw)
                        except Exception as e:
                            st.warning("SMC error: %s" % e)
                        # Show Wyckoff
                        try:
                            wyk = analyze_wyckoff_vsa(_df_up)
                            st.markdown("##### 🐋 Wyckoff/PVSRA")
                            st.markdown(f"**المرحلة:** {wyk['phase']}")
                            for n in wyk["vsa_notes"]:
                                st.info(n)
                        except Exception as e:
                            st.warning("Wyckoff error: %s" % e)
                        # Show CPR
                        try:
                            cvp = analyze_cpr_and_vp(_df_up)
                            st.markdown("##### 🎯 CPR/VP")
                            st.markdown(f"**Verdict:** {cvp['verdict']}")
                            st.markdown(f"POC: {cvp['poc']} | VAH: {cvp['vah']} | VAL: {cvp['val']}")
                        except Exception as e:
                            st.warning("CPR error: %s" % e)
                        # Show chart
                        try:
                            sub = _df_up.tail(120)
                            import plotly.graph_objects as _go
                            fig = _go.Figure(_go.Candlestick(x=sub.index, open=sub["Open"], high=sub["High"], low=sub["Low"], close=sub["Close"], name="السعر"))
                            fig.update_layout(title="Chart (uploaded data)", height=400, template=TPL, xaxis_rangeslider_visible=False, margin=dict(l=10,r=10,t=40,b=10))
                            st.plotly_chart(fig, width="stretch")
                        except Exception as e:
                            st.warning("Chart error: %s" % e)
                except Exception as e:
                    st.error("⚠️ خطأ في قراءة الملف: %s" % e)


# ==============================================================================
# التبويب 4: الإعدادات والربط السحابي والتليجرام
# ==============================================================================
if VIEW == "settings":
    set_c1, set_c2 = st.columns(2)

    with set_c1:
        st.markdown("### ☁️ الربط السحابي الدائم (Supabase)")
        if is_authenticated():
            st.success("User: %s" % st.session_state.get("auth_email"))
            if st.button("Logout", width="stretch"):
                sb_logout()
                st.rerun()
        st.markdown("---")
        st.caption("استعادة بيانات ما قبل V11.4 (user_id is null):")
        if st.button("Claim Legacy Data", width="stretch"):
            uid = st.session_state.get("auth_user_id")
            if uid:
                _sb_request("PATCH", "portfolio?user_id=is.null", payload={"user_id": uid})
                _sb_request("PATCH", "closed_trades?user_id=is.null", payload={"user_id": uid})
                st.success("تم.")
                st.session_state["force_cloud_sync"] = True
                st.rerun()
        sb_url_in = st.text_input("🌐 Supabase URL:", value=st.session_state.get("sb_url_val", get_secret_safe("SUPABASE_URL")), placeholder="https://xxxx.supabase.co")
        st.session_state["sb_url_val"] = sb_url_in
        sb_key_in = st.text_input("🔐 Supabase Key:", value=st.session_state.get("sb_key_val", get_secret_safe("SUPABASE_KEY")), type="password", placeholder="eyJhbGci...")
        st.session_state["sb_key_val"] = sb_key_in

        sbtn1, sbtn2 = st.columns(2)
        with sbtn1:
            if st.button("🔌 فحص الاتصال واسترجاع المحفظة", width="stretch"):
                ok_sb, msg_sb = test_supabase_connection()
                if ok_sb:
                    st.session_state["force_cloud_sync"] = True
                    st.success(msg_sb)
                    st.rerun()
                else:
                    st.error(msg_sb)
        with sbtn2:
            if st.button("⬆️ رفع الأسهم المحلية للسحابة", width="stretch"):
                ok_up, msg_up = sync_full_portfolio_to_cloud(_load_local_portfolio_file() or my_portfolio)
                if ok_up:
                    st.success(msg_up)
                else:
                    st.error(msg_up)
        with st.expander("🛠️ كود SQL لإنشاء جداول Supabase (إذا كانت قاعدة البيانات جديدة)"):
            st.code("""
create table if not exists portfolio (
  symbol text primary key,
  shares integer not null,
  buy_price numeric not null,
  stop_loss numeric default 0,
  tp1 numeric default 0,
  tp2 numeric default 0,
  trailing_enabled boolean default true,
  trailing_stage integer default 0
);

create table if not exists closed_trades (
  id bigint generated always as identity primary key,
  symbol text not null,
  shares integer not null,
  buy_price numeric not null,
  sell_price numeric not null,
  net_pnl numeric not null,
  pnl_pct numeric not null,
  closed_at timestamptz default now()
);

create table if not exists tg_alerts_log (
  alert_key text primary key,
  sent_at text
);

alter table portfolio disable row level security;
alter table closed_trades disable row level security;
alter table tg_alerts_log disable row level security;
            """, language="sql")

        st.divider()
        st.markdown("### 📲 إعدادات بوت التليجرام")
        tg_t_in = st.text_input("🔑 Bot Token:", value=tg_token, type="password")
        st.session_state["tg_token_val"] = tg_t_in
        tgc1, tgc2 = st.columns([1.4, 1])
        with tgc1:
            tg_c_in = st.text_input("🆔 Chat ID:", value=tg_chat_id)
            st.session_state["tg_chat_val"] = tg_c_in
        with tgc2:
            st.write(""); st.write("")
            if st.button("🔍 جلب Chat ID تلقائياً", width="stretch"):
                fid, fmsg = detect_telegram_chat_id(tg_t_in)
                if fid:
                    st.session_state["tg_chat_val"] = fid
                    st.rerun()
                else:
                    st.warning(fmsg)

        st.session_state["cfg_tg_port"] = st.checkbox("🔔 إرسال تنبيهات المحفظة تلقائياً", value=tg_auto_port)
        st.session_state["cfg_tg_whales"] = st.checkbox("🐋 تنبيه صفقات الحيتان (سكور 80+)", value=tg_auto_whales)
        if st.button("🧪 إرسال رسالة تجريبية لتليجرام", width="stretch"):
            ok_t, msg_t = send_telegram_message(tg_t_in, tg_c_in, "🦅 <b>EGX Whale Hunter Pro V11.5</b>\n✅ الربط مع تليجرام شغال!")
            if ok_t:
                st.success("✅ وصلت الرسالة لتليجرام!")
            else:
                st.error(f"❌ {msg_t}")
    with set_c2:
        st.markdown("### 🎛️ إعدادات السكانر وإدارة رأس المال")
        scope_choice = st.radio(
            "🌐 نطاق أسهم الرادار:",
            ["كل أسهم البورصة المصرية", "الأسهم القيادية والنشطة فقط"],
            index=(1 if only_leaders else 0)
        )
        st.session_state["cfg_only_leaders"] = ("القيادية" in scope_choice)
        try:
            _native = st.context.theme.type
        except Exception:
            _native = None
        st.toggle("⚡ تحديث تلقائي كل 5 دقايق", key="cfg_live_auto")
        if _native and _native != THEME_MODE:
            st.caption("🎨 الجداول بتاخد ألوانها من إعداد Streamlit نفسه. عشان تتطابق مع الوضع الحالي: ⋮ (فوق) ← Settings ← "
                       + ("Dark" if THEME_MODE == "dark" else "Light") + ".")
        st.session_state["profile_name"] = st.text_input("👤 اسم الملف (Profile):", value=st.session_state.get("profile_name", ""), placeholder="مثال: علي")
        st.session_state["cfg_capital"] = st.number_input("💰 رأس المال للمقترحات (ج.م):", min_value=5000, value=capital, step=5000)
        st.session_state["cfg_risk_pct"] = st.slider("🛡️ نسبة المخاطرة في الصفقة الواحدة (%):", 0.5, 5.0, risk_pct, 0.25)
        st.session_state["cfg_min_turnover"] = st.number_input("💧 الحد الأدنى للسيولة اليومية (مليون ج.م):", 0.0, 100.0, min_turnover_m, 0.25)
        fee_choice = st.radio("💳 شريحة عمولة Thndr:", ["Thndr Trader — أول 50 أمر بالشهر (0.08% لكل جانب ≈ 0.16% ذهاب وعودة)", "أكثر من 50 أمر (0.18% لكل جانب ≈ 0.37% ذهاب وعودة)"], index=(0 if fee_rate == core.FEE_PER_SIDE_TRADER else 1))
        st.session_state["cfg_fee_tier"] = "0.16%" if "0.16%" in fee_choice else "0.37%"
        st.session_state["cfg_min_score"] = st.slider("🎯 الحد الأدنى للسكور في جدول الرادار:", 0, 100, min_score, 5)
        st.session_state["cfg_alert_buf"] = st.slider("🔔 حساسية تنبيه قرب الوقف/الهدف (%):", 0.5, 8.0, alert_buffer_pct, 0.5)

# ===== واجهة إدارة قائمة المراقبة (Watchlist UI) — جوه محفظتي =====
if VIEW == "portfolio":
    with st.expander("📌 قائمة المراقبة (Watchlist) — تنبيهات سعر", expanded=False):
        wlc1, wlc2, wlc3, wlc4 = st.columns([1.2, 1, 1, 1])
        with wlc1:
            wl_sym = st.text_input("رمز السهم", key="wl_sym_in", placeholder="ABUK").upper().replace(".CA","").strip()
        with wlc2:
            wl_dir = st.selectbox("الاتجاه", ["above (>=", "below (<="], key="wl_dir_in")
        with wlc3:
            wl_tgt = st.number_input("السعر الهدف", min_value=0.0, value=0.0, step=0.05, key="wl_tgt_in")
        with wlc4:
            st.write(""); st.write("")
            if st.button("add", key="wl_add_btn", width="stretch"):
                if wl_sym and wl_tgt > 0:
                    wl = list(st.session_state.get("watchlist", []))
                    wl.append({"symbol": wl_sym, "direction": "above" if "above" in wl_dir else "below", "target": float(wl_tgt)})
                    _save_watchlist(wl)
                    st.success("تمت الإضافة.")
                    st.rerun()
        wl_df = pd.DataFrame(st.session_state.get("watchlist", []))
        if not wl_df.empty:
            st.dataframe(wl_df, width="stretch", hide_index=True)
            del_sym = st.selectbox("حذف:", options=list(range(len(wl_df))), format_func=lambda i: "%s - %s %s" % (wl_df.iloc[i]["symbol"], wl_df.iloc[i]["direction"], wl_df.iloc[i]["target"]), key="wl_del_sel")
            if st.button("delete", key="wl_del_btn"):
                wl = list(st.session_state.get("watchlist", []))
                if 0 <= del_sym < len(wl):
                    wl.pop(del_sym)
                    _save_watchlist(wl)
                    st.rerun()


if live_auto:
    time.sleep(300)
    st.session_state["refresh_nonce"] = refresh_nonce + 1
    st.session_state["force_cloud_sync"] = True
    fetch_full_egx_tv_scanner.clear()
    st.rerun()

