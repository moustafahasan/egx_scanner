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

# ==========================================
# إعدادات الصفحة والتصميم البصري الداكن (V11.0)
# ==========================================
st.set_page_config(
    page_title="EGX Whale Hunter Pro V11.0",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800;900&display=swap');

    html, body, [class*="css"] {
        font-family: 'Cairo', sans-serif !important;
    }

    /* ===== V11.0 Light Theme ===== */
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"], [data-testid="stToolbar"] {
        background-color: #F1F5F9 !important;
        color: #0F172A !important;
    }
    .main .block-container, .block-container {
        direction: rtl;
        text-align: right;
        padding-top: 1.1rem;
        padding-bottom: 2.5rem;
        max-width: 1460px;
    }

    div[data-baseweb="input"], div[data-baseweb="base-input"], input, textarea {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
        border-color: #CBD5E1 !important;
        border-radius: 8px !important;
    }
    input::placeholder { color: #64748B !important; }

    button[data-testid="stNumberInputStepDown"], button[data-testid="stNumberInputStepUp"] {
        background-color: #E2E8F0 !important;
        color: #0F172A !important;
        border-color: #CBD5E1 !important;
    }
    button[data-testid="stNumberInputStepDown"]:hover, button[data-testid="stNumberInputStepUp"]:hover {
        background-color: #0284C7 !important;
        color: #FFFFFF !important;
    }

    label, label p, [data-testid="stWidgetLabel"] p, div[role="radiogroup"] label p, [data-testid="stCheckbox"] label p {
        color: #1E293B !important;
        font-weight: 600 !important;
    }

    .stButton > button, .stDownloadButton > button, .stLinkButton > a {
        background-color: #FFFFFF !important;
        color: #1E3A8A !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
        transition: all 0.2s ease;
    }
    .stButton > button:hover, .stDownloadButton > button:hover, .stLinkButton > a:hover {
        border-color: #0284C7 !important;
        color: #0284C7 !important;
        background-color: #EFF6FF !important;
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #0284C7 0%, #1E3A8A 100%) !important;
        color: #FFFFFF !important;
        border: 1px solid #0284C7 !important;
        box-shadow: 0 4px 14px rgba(2, 132, 199, 0.25);
    }
    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #1E3A8A 0%, #1E40AF 100%) !important;
        color: #FFFFFF !important;
    }

    [data-testid="stExpander"], div[data-baseweb="select"] > div, [data-testid="stFileUploaderDropzone"] {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
        border-color: #CBD5E1 !important;
        border-radius: 10px !important;
    }
    ul[data-baseweb="menu"] {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #FFFFFF;
        padding: 8px 10px;
        border-radius: 14px;
        border: 1px solid #CBD5E1;
        flex-wrap: wrap;
        box-shadow: 0 2px 8px rgba(15, 23, 42, 0.05);
    }
    .stTabs [data-baseweb="tab"] {
        height: 42px;
        background-color: transparent;
        border-radius: 10px;
        color: #475569 !important;
        font-weight: 700;
        font-size: 14px;
        padding: 0 16px;
        border: 1px solid transparent;
        transition: all 0.2s ease;
    }
    .stTabs [data-baseweb="tab"]:hover {
        background-color: #EFF6FF;
        color: #0284C7 !important;
        border-color: #BFDBFE;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #0284C7 0%, #1E3A8A 100%) !important;
        color: #FFFFFF !important;
        border-color: #0284C7 !important;
        box-shadow: 0 4px 14px rgba(2, 132, 199, 0.30);
    }
    .stTabs [data-baseweb="tab-highlight"] { display: none; }

    .kpi-card {
        background: linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%);
        border: 1px solid #CBD5E1;
        border-top: 3px solid #0284C7;
        border-radius: 14px;
        padding: 14px 16px;
        text-align: center;
        box-shadow: 0 4px 16px rgba(15, 23, 42, 0.06);
    }
    .kpi-label { font-size: 12px; color: #475569; margin-bottom: 4px; font-weight: 700; }
    .kpi-val { font-size: 20px; font-weight: 900; color: #0F172A; }

    .pro-card {
        background: #FFFFFF;
        border: 1px solid #CBD5E1;
        border-right: 4px solid #0284C7;
        border-radius: 14px;
        padding: 16px 18px;
        margin-bottom: 12px;
        box-shadow: 0 4px 18px rgba(15, 23, 42, 0.06);
    }
    .top-card {
        background: linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%);
        border: 1px solid #CBD5E1;
        border-radius: 14px;
        padding: 15px;
        margin-bottom: 10px;
        box-shadow: 0 4px 14px rgba(15, 23, 42, 0.05);
    }
    .top-card-gold {
        border: 1px solid #EAB308;
        box-shadow: 0 0 22px rgba(234, 179, 8, 0.18);
    }
    .stock-header-strip {
        background: linear-gradient(90deg, #FFFFFF 0%, #EFF6FF 100%);
        border: 1px solid #CBD5E1;
        border-right: 5px solid #EAB308;
        border-radius: 14px;
        padding: 14px 20px;
        margin-bottom: 14px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 12px;
        box-shadow: 0 4px 14px rgba(15, 23, 42, 0.05);
    }

    .badge-bull { background: #DCFCE7; color: #15803D; border: 1px solid #86EFAC; padding: 3px 10px; border-radius: 999px; font-size: 12px; font-weight: 700; }
    .badge-bear { background: #FEE2E2; color: #B91C1C; border: 1px solid #FCA5A5; padding: 3px 10px; border-radius: 999px; font-size: 12px; font-weight: 700; }
    .badge-warn { background: #FEF3C7; color: #92400E; border: 1px solid #FCD34D; padding: 3px 10px; border-radius: 999px; font-size: 12px; font-weight: 700; }

    .alert-box-success { background: #ECFDF5; border: 1px solid #86EFAC; border-right: 5px solid #22C55E; border-radius: 12px; padding: 12px 16px; margin-bottom: 10px; color: #064E3B; }
    .alert-box-warn { background: #FFFBEB; border: 1px solid #FCD34D; border-right: 5px solid #EAB308; border-radius: 12px; padding: 12px 16px; margin-bottom: 10px; color: #78350F; }
    .alert-box-danger { background: #FEF2F2; border: 1px solid #FCA5A5; border-right: 5px solid #EF4444; border-radius: 12px; padding: 12px 16px; margin-bottom: 10px; color: #7F1D1D; }
    .news-item { background: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 12px; padding: 12px 15px; margin-bottom: 8px; }

    .txt-green { color: #15803D; } .txt-red { color: #B91C1C; } .txt-gold { color: #B45309; }
    .txt-cyan { color: #0369A1; } .txt-white { color: #0F172A; } .txt-muted { color: #475569; }

    .hero-banner {
        background: linear-gradient(135deg, #FFFFFF 0%, #EFF6FF 100%);
        border: 1px solid #BFDBFE;
        border-right: 5px solid #0284C7;
        border-radius: 16px;
        padding: 16px 22px;
        margin-bottom: 14px;
        box-shadow: 0 8px 28px rgba(2, 132, 199, 0.10);
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 12px;
    }
    .hero-title { font-size: 24px; font-weight: 900; color: #0F172A; letter-spacing: 0.3px; }
    .hero-accent { color: #0284C7; }
    .hero-sub { font-size: 13px; color: #475569; margin-top: 3px; }
    .session-pill {
        background: #EFF6FF;
        border: 1px solid #0284C7;
        color: #0284C7;
        padding: 7px 15px;
        border-radius: 999px;
        font-weight: 800;
        font-size: 13px;
    }

    .top-card:hover { transform: translateY(-2px); transition: transform .2s ease; }
    .alert-box-success, .alert-box-warn, .alert-box-danger { animation: fadeIn .35s ease; }
    @keyframes fadeIn { from { opacity: 0; transform: translateY(4px);} to { opacity:1; transform: translateY(0);} }
</style>
""", unsafe_allow_html=True)


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
                                    "الكمية": qty, "السعر": round(price, 2),
                                })
                                found_in_lines = True

                    if not found_in_lines and doc_sym:
                        m_qty = re.search(r"(?:Quantity|Qty|Shares|الكمية|عدد الأسهم)\s*[:\-]?\s*(\d+)", norm_txt, re.IGNORECASE)
                        m_prc = re.search(r"(?:Execution Price|Price|Avg Price|سعر التنفيذ|السعر)\s*[:\-]?\s*(\d+(?:\.\d+)?)", norm_txt, re.IGNORECASE)
                        qty = int(m_qty.group(1)) if m_qty else 100
                        price = float(m_prc.group(1)) if m_prc else 0.0
                        if price > 0:
                            extracted_ops.append({
                                "المصدر": up.name, "العملية": doc_side, "الرمز": doc_sym,
                                "اسم الشركة": known_names.get(doc_sym, doc_sym),
                                "الكمية": qty, "السعر": round(price, 2),
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
                                "الكمية": qty, "السعر": round(price, 2),
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
    is_trading_day = wd in [6, 0, 1, 2, 3]
    start_dt = now.replace(hour=10, minute=0, second=0, microsecond=0)
    end_dt = now.replace(hour=14, minute=30, second=0, microsecond=0)
    total_mins = 270.0

    if not is_trading_day:
        return {"is_open": False, "progress": 1.0, "badge": "🔴 عطلة أسبوعية (EGX مغلقة)"}
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
    base_url, headers = _get_sb_headers()
    if not base_url:
        return False, "Missing SUPABASE_URL or SUPABASE_KEY"
    if extra_headers:
        headers.update(extra_headers)
    url = f"{base_url}/rest/v1/{path}"
    data_bytes = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data_bytes, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            raw = resp.read().decode("utf-8")
            return True, (json.loads(raw) if raw else [])
    except Exception as e:
        return False, str(e)

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
    ok, data = _sb_request("GET", "portfolio?select=*&order=symbol.asc")
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
    ok, data = _sb_request("GET", "closed_trades?select=*&order=closed_at.desc")
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
        "shares": int(shares),
        "buy_price": round(buy_price, 2),
        "sell_price": round(sell_price, 2),
        "net_pnl": round(net_pnl, 2),
        "pnl_pct": round(pnl_pct, 2),
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
                "vwap": float(rec.get("VWAP") or close_p),
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
    vwap = float(q.get("vwap") or close or 0.0)
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
    ba_pressure = f"طلب {bid:.2f} / عرض {ask:.2f}" if (bid > 0 and ask > 0) else "غير متاح خارج الجلسة"

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
        "vwap": round(vwap, 2),
        "vwap_diff_pct": round(vwap_diff_pct, 2),
        "rsi15": round(rsi15, 1),
        "macd15": round(macd15, 3),
        "macds15": round(macds15, 3),
        "clv_pct": round(clv_pct, 1),
        "rel_vol": round(rel_vol, 2),
        "spread_pct": round(spread_pct, 2),
        "ba_pressure": ba_pressure,
        "flow_score": f_score,
        "verdict": verdict,
        "short_verdict": short_v,
        "badge_cls": badge_cls,
        "reasons": reasons or ["بيانات التداول اللحظية في النطاق الطبيعي."],
        "action_hint": hint
    }

def evaluate_smart_stop_loss(sym: str, curr_p: float, sl: float, buy_p: float, flow_res: dict, alert_buffer_pct: float = 2.5) -> dict:
    """
    محرك الوقف الذكي الهجين (V11.0):
    - كسر عميق >= 1.5% أسفل الوقف -> خروج فوري.
    - سيولة بيعية مؤسسية: RVOL >= 1.6x و (VWAP diff <= -0.8% أو flow_score <= -35).
    - انهيار زخم: RSI15 <= 35 + CLV <= 15% + RVOL >= 1.2x.
    خلاف ذلك: كسر لحظي تحت المراقبة (انتظار تأكيد الإغلاق 14:10-14:30).
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
            result["action"] = "EXIT_NOW"
            result["is_hard_break"] = True
            if deep_break:
                result["reason"] = f"كسر عميق أسفل الوقف ({dist_sl_pct:.2f}% <= -1.5%)"
            elif inst_sell:
                result["reason"] = f"سيولة بيعية مؤسسية (RVOL {rvol:.2f}x, VWAP {vwap_diff:+.2f}%)"
            else:
                result["reason"] = f"انهيار زخم (RSI15 {rsi15:.1f}, CLV {clv:.0f}%)"
        else:
            result["action"] = "WATCH_CLOSE"
            result["is_intraday_break"] = True
            result["reason"] = f"كسر لحظي تحت المراقبة (يبعد {dist_sl_pct:.2f}% عن الوقف) - انتظار تأكيد الإغلاق"
    elif 0 < dist_sl_pct <= alert_buffer_pct:
        result["action"] = "NEAR_SL"
        result["reason"] = f"قرب الوقف ({dist_sl_pct:.1f}%)"
    return result



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
    net_profit_tp1 = (shares * (tp1 - entry)) - (position_value * fee_rate)

    return {
        "الرمز": sym,
        "اسم الشركة": q["name"],
        "Ticker": f"{sym}.CA",
        "السكور": score,
        "نوع الإشارة": setup_type,
        "الرأي اللحظي": flow_res["short_verdict"],
        "الإغلاق": round(close, 2),
        "ATR14": round(atr14, 3),
        "EMA20": round(ema20, 2),
        "التغير %": round(pct_change, 2),
        "الفوليوم": round(pace_rvol, 2),
        "فرق VWAP %": round(vwap_diff, 2),
        "القوة النسبية %": round(rs_alpha, 1),
        "السيولة (مليون)": round(effective_turnover_m, 2),
        "الوقف (2xATR)": round(stop_loss, 2),
        "TP1": round(tp1, 2),
        "TP2": round(tp2, 2),
        "TP3": round(tp3, 2),
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
        "TradingView": f"https://www.tradingview.com/chart/?symbol=EGX:{sym}"
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
        df["EMA20"] = df["Close"].ewm(span=20, adjust=False).mean()
        df["EMA50"] = df["Close"].ewm(span=50, adjust=False).mean()
        df["EMA200"] = df["Close"].ewm(span=200, adjust=False).mean()
        df["VolSMA20"] = df["Volume"].rolling(20).mean()
        return df
    except Exception:
        return pd.DataFrame()

# ==========================================
# محركات التحليل المؤسسي العشرة
# ==========================================
def extract_zigzag_pivots(df: pd.DataFrame, pct_thresh: float = 0.05) -> list:
    if df is None or len(df) < 5:
        return []
    highs, lows, dates = df["High"].values, df["Low"].values, df.index
    pivots, trend, last_p, last_idx = [], 0, float(highs[0]), 0

    for i in range(1, len(df)):
        h, l = float(highs[i]), float(lows[i])
        if trend == 0:
            if h >= last_p * (1 + pct_thresh):
                pivots.append({"idx": last_idx, "date": dates[last_idx], "price": float(lows[last_idx]), "type": "L"})
                trend, last_p, last_idx = 1, h, i
            elif l <= last_p * (1 - pct_thresh):
                pivots.append({"idx": last_idx, "date": dates[last_idx], "price": float(highs[last_idx]), "type": "H"})
                trend, last_p, last_idx = -1, l, i
        elif trend == 1:
            if h >= last_p:
                last_p, last_idx = h, i
            elif l <= last_p * (1 - pct_thresh):
                pivots.append({"idx": last_idx, "date": dates[last_idx], "price": last_p, "type": "H"})
                trend, last_p, last_idx = -1, l, i
        elif trend == -1:
            if l <= last_p:
                last_p, last_idx = l, i
            elif h >= last_p * (1 + pct_thresh):
                pivots.append({"idx": last_idx, "date": dates[last_idx], "price": last_p, "type": "L"})
                trend, last_p, last_idx = 1, h, i

    pivots.append({"idx": last_idx, "date": dates[last_idx], "price": last_p, "type": "H" if trend >= 0 else "L"})
    return pivots

def analyze_smc_ict(df: pd.DataFrame) -> dict:
    sub = df.tail(120).copy()
    curr_p = float(sub["Close"].iloc[-1])
    fvgs, obs, sweeps = [], [], []

    for i in range(2, len(sub)):
        h_prev2, l_prev2 = float(sub["High"].iloc[i - 2]), float(sub["Low"].iloc[i - 2])
        c_prev1, o_prev1 = float(sub["Close"].iloc[i - 1]), float(sub["Open"].iloc[i - 1])
        h_curr, l_curr, c_curr = float(sub["High"].iloc[i]), float(sub["Low"].iloc[i]), float(sub["Close"].iloc[i])
        dt_curr = sub.index[i]

        if l_curr > h_prev2:
            mitigated = float(sub["Low"].iloc[i + 1:].min()) <= h_prev2 if i + 1 < len(sub) else False
            if not mitigated:
                fvgs.append({"النوع": "🟢 فجوة شرائية (Bullish FVG)", "من": round(h_prev2, 2), "إلى": round(l_curr, 2), "التاريخ": str(dt_curr)[:10]})
        if h_curr < l_prev2:
            mitigated = float(sub["High"].iloc[i + 1:].max()) >= l_prev2 if i + 1 < len(sub) else False
            if not mitigated:
                fvgs.append({"النوع": "🔴 فجوة بيعية (Bearish FVG)", "من": round(h_curr, 2), "إلى": round(l_prev2, 2), "التاريخ": str(dt_curr)[:10]})

        if c_prev1 < o_prev1 and c_curr > float(sub["High"].iloc[i - 1]):
            ob_low, ob_high = float(sub["Low"].iloc[i - 1]), float(sub["High"].iloc[i - 1])
            if ob_low <= curr_p * 1.15:
                obs.append({"النوع": "🟢 كتلة طلب مؤسسي (Bullish OB)", "من": round(ob_low, 2), "إلى": round(ob_high, 2), "التاريخ": str(sub.index[i - 1])[:10]})
        elif c_prev1 > o_prev1 and c_curr < float(sub["Low"].iloc[i - 1]):
            ob_low, ob_high = float(sub["Low"].iloc[i - 1]), float(sub["High"].iloc[i - 1])
            if ob_high >= curr_p * 0.85:
                obs.append({"النوع": "🔴 كتلة عرض مؤسسي (Bearish OB)", "من": round(ob_low, 2), "إلى": round(ob_high, 2), "التاريخ": str(sub.index[i - 1])[:10]})

    pivs = extract_zigzag_pivots(sub, pct_thresh=0.04)
    structure_state, badge_cls = "⚖️ نطاق عرضي (Range)", "badge-warn"
    last_swing_high, last_swing_low = None, None
    highs_p = [p for p in pivs if p["type"] == "H"]
    lows_p = [p for p in pivs if p["type"] == "L"]

    if len(highs_p) >= 2 and len(lows_p) >= 2:
        last_swing_high, last_swing_low = highs_p[-2]["price"], lows_p[-2]["price"]
        if curr_p > last_swing_high:
            structure_state, badge_cls = "🟢 كسر هيكل صاعد (Bullish BOS)", "badge-bull"
        elif curr_p < last_swing_low:
            structure_state, badge_cls = "🔴 كسر هيكل هابط (Bearish BOS)", "badge-bear"
        elif highs_p[-1]["price"] < highs_p[-2]["price"] and lows_p[-1]["price"] > lows_p[-2]["price"]:
            structure_state = "🟡 تضييق سيولة (CHoCH محتمل)"

    if len(lows_p) >= 2 and float(sub["Low"].tail(10).min()) < lows_p[-2]["price"] and curr_p > lows_p[-2]["price"]:
        sweeps.append(f"🐋 سحب سيولة أسفل القاع ({lows_p[-2]['price']:.2f}) والارتداد أعلاه (Bullish Liquidity Sweep)")
    if len(highs_p) >= 2 and float(sub["High"].tail(10).max()) > highs_p[-2]["price"] and curr_p < highs_p[-2]["price"]:
        sweeps.append(f"⚠️ سحب سيولة أعلى القمة ({highs_p[-2]['price']:.2f}) والهبوط أسفلها (Bearish Liquidity Sweep)")

    return {
        "structure": structure_state, "badge_cls": badge_cls,
        "fvgs": fvgs[-5:], "obs": obs[-5:], "sweeps": sweeps,
        "swing_high": round(last_swing_high, 2) if last_swing_high else None,
        "swing_low": round(last_swing_low, 2) if last_swing_low else None,
    }

def analyze_wyckoff_vsa(df: pd.DataFrame) -> dict:
    sub = df.tail(100).copy()
    sub["VolRatio"] = sub["Volume"] / sub["VolSMA20"].replace(0, np.nan)
    curr = sub.iloc[-1]
    c_p, ema50, ema200 = float(curr["Close"]), float(curr["EMA50"]), float(curr["EMA200"])
    v_ratio = float(curr["VolRatio"]) if pd.notna(curr["VolRatio"]) else 1.0
    rng = max(1e-6, float(curr["High"] - curr["Low"]))
    clv = (c_p - float(curr["Low"])) / rng

    box_high, box_low = float(sub["High"].tail(40).max()), float(sub["Low"].tail(40).min())
    box_range_pct = ((box_high - box_low) / max(0.01, box_low)) * 100.0

    if c_p > ema50 > ema200 and c_p >= box_high * 0.96:
        phase, badge_cls = "🚀 مرحلة الانطلاق (Markup Phase)", "badge-bull"
    elif c_p < ema50 < ema200 and c_p <= box_low * 1.04:
        phase, badge_cls = "📉 مرحلة الهبوط (Markdown Phase)", "badge-bear"
    elif box_range_pct <= 18.0 and c_p >= ema200 * 0.95:
        phase, badge_cls = "🔋 نطاق تجميع مؤسسي (Accumulation)", "badge-bull"
    else:
        phase, badge_cls = "⚠️ نطاق تصريف / إعادة توازن (Distribution)", "badge-warn"

    signals = []
    for dt_idx, row in sub[sub["VolRatio"] >= 2.0].tail(5).iterrows():
        kind = "🟢 شمعة حيتان شرائية (PVSRA)" if row["Close"] >= row["Open"] else "🔴 شمعة حيتان بيعية (PVSRA)"
        signals.append({"التاريخ": str(dt_idx)[:10], "الإشارة": kind, "السعر": round(float(row["Close"]), 2), "نسبة الفوليوم": f"{row['VolRatio']:.1f}x"})

    vsa_notes = []
    if v_ratio >= 2.0 and clv >= 0.65:
        vsa_notes.append("🟢 **ذروة امتصاص شرائي (Buying Absorption):** فوليوم مضاعف مع إغلاق في الثلث العلوي للشمعة.")
    elif v_ratio >= 2.0 and clv <= 0.35:
        vsa_notes.append("🔴 **ضغط بيعي كثيف (Selling Climax):** فوليوم مرتفع جداً مع إغلاق قرب القاع.")
    elif v_ratio <= 0.65 and c_p < float(sub["Close"].iloc[-2]) and c_p > ema50:
        vsa_notes.append("🎯 **جفاف العرض (No Supply):** تراجع سعري هادئ بأحجام تداول منخفضة جداً داخل اتجاه صاعد.")

    prior_30_low = float(sub["Low"].iloc[-31:-3].min()) if len(sub) > 35 else box_low
    if float(sub["Low"].tail(3).min()) < prior_30_low and c_p > prior_30_low:
        vsa_notes.append(f"🐋 **نموذج Spring (كسر كاذب للقاع {prior_30_low:.2f}):** مصيدة دببة كلاسيكية لبدء موجة صعود.")

    return {
        "phase": phase, "badge_cls": badge_cls,
        "box_high": round(box_high, 2), "box_low": round(box_low, 2),
        "vol_ratio": round(v_ratio, 2),
        "vsa_notes": vsa_notes or ["الحركة السعرية متوافقة مع متوسط أحجام التداول دون شذوذ VSA حاد."],
        "whale_candles": signals
    }

def analyze_cpr_and_vp(df: pd.DataFrame) -> dict:
    sub = df.tail(90).copy()
    curr_p = float(sub["Close"].iloc[-1])
    prev_m = df.iloc[-21:-1] if len(df) >= 22 else sub
    h_m, l_m, c_m = float(prev_m["High"].max()), float(prev_m["Low"].min()), float(prev_m["Close"].iloc[-1])

    pivot = (h_m + l_m + c_m) / 3.0
    bc = (h_m + l_m) / 2.0
    tc = (pivot - bc) + pivot
    cpr_top, cpr_bot = max(tc, bc), min(tc, bc)
    cpr_width_pct = ((cpr_top - cpr_bot) / max(0.01, pivot)) * 100.0
    r1, s1 = (2 * pivot) - l_m, (2 * pivot) - h_m

    p_min, p_max = float(sub["Low"].min()), float(sub["High"].max())
    bins = np.linspace(p_min, max(p_min + 0.05, p_max), 25)
    bin_centers = (bins[:-1] + bins[1:]) / 2.0
    vol_hist = np.zeros(len(bin_centers))

    for _, r in sub.iterrows():
        idx = max(0, min(len(vol_hist) - 1, np.digitize(float(r["Close"]), bins) - 1))
        vol_hist[idx] += float(r["Volume"])

    poc_idx = int(np.argmax(vol_hist))
    poc_price = float(bin_centers[poc_idx])
    target_v, acc_v = float(vol_hist.sum()) * 0.70, float(vol_hist[poc_idx])
    lo_i, hi_i = poc_idx, poc_idx
    while acc_v < target_v and (lo_i > 0 or hi_i < len(vol_hist) - 1):
        v_lo = vol_hist[lo_i - 1] if lo_i > 0 else -1
        v_hi = vol_hist[hi_i + 1] if hi_i < len(vol_hist) - 1 else -1
        if v_hi >= v_lo and hi_i < len(vol_hist) - 1:
            hi_i += 1; acc_v += v_hi
        elif lo_i > 0:
            lo_i -= 1; acc_v += v_lo
        else:
            break

    val_price, vah_price = float(bin_centers[lo_i]), float(bin_centers[hi_i])
    if curr_p > cpr_top and curr_p > vah_price:
        verdict, badge_cls = "🟢 اختراق منطقة القيمة وCPR (اتجاه صاعد)", "badge-bull"
    elif curr_p < cpr_bot and curr_p < val_price:
        verdict, badge_cls = "🔴 كسر منطقة القيمة وCPR (ضغط بيعي)", "badge-bear"
    else:
        verdict, badge_cls = "🟡 تداول داخل منطقة التوازن (Value Area)", "badge-warn"

    return {
        "pivot": round(pivot, 2), "tc": round(cpr_top, 2), "bc": round(cpr_bot, 2),
        "r1": round(r1, 2), "s1": round(s1, 2), "cpr_width_pct": round(cpr_width_pct, 2),
        "poc": round(poc_price, 2), "vah": round(vah_price, 2), "val": round(val_price, 2),
        "bin_centers": bin_centers, "vol_hist": vol_hist,
        "verdict": verdict, "badge_cls": badge_cls
    }

def analyze_harmonic_patterns(df: pd.DataFrame) -> dict:
    sub = df.tail(160).copy()
    pivs = extract_zigzag_pivots(sub, pct_thresh=0.045)
    curr_p = float(sub["Close"].iloc[-1])

    if len(pivs) < 5:
        return {"detected": False, "pattern_name": "لا يوجد نموذج توافقي مكتمل", "badge_cls": "badge-warn", "points": [], "prz_low": None, "prz_high": None, "notes": "القمم والقيعان غير كافية لتكوين ضلع XABCD حالياً."}

    X, A, B, C, D = pivs[-5], pivs[-4], pivs[-3], pivs[-2], pivs[-1]
    xa, ab, bc, ad = abs(A["price"] - X["price"]), abs(B["price"] - A["price"]), abs(C["price"] - B["price"]), abs(D["price"] - X["price"])
    if xa < 1e-6 or ab < 1e-6:
        return {"detected": False, "pattern_name": "تذبذب ضعيف", "badge_cls": "badge-warn", "points": pivs[-5:], "prz_low": None, "prz_high": None, "notes": "مدى الحركة صغير جداً."}

    ab_xa, bc_ab, ad_xa = ab / xa, bc / ab, ad / xa
    is_bullish = X["type"] == "L" and A["type"] == "H" and D["type"] == "L"

    pat, prz_ratio = "نموذج توافقي قيد التشكّل (Harmonic Setup)", 0.786
    if 0.55 <= ab_xa <= 0.68 and 0.72 <= ad_xa <= 0.85:
        pat, prz_ratio = "جارتلي (Gartley)", 0.786
    elif 0.35 <= ab_xa <= 0.55 and 0.82 <= ad_xa <= 0.94:
        pat, prz_ratio = "الخفاش (Bat)", 0.886
    elif 0.72 <= ab_xa <= 0.85 and 1.15 <= ad_xa <= 1.35:
        pat, prz_ratio = "الفراشة (Butterfly)", 1.272
    elif 0.35 <= ab_xa <= 0.65 and 1.45 <= ad_xa <= 1.75:
        pat, prz_ratio = "الكابوريا (Crab)", 1.618

    if is_bullish:
        prz_center = A["price"] - (xa * prz_ratio)
        direction_txt, badge_cls = f"🟢 {pat} شرائي (Bullish)", "badge-bull"
        target_1 = D["price"] + 0.382 * abs(A["price"] - D["price"])
        target_2 = D["price"] + 0.618 * abs(A["price"] - D["price"])
    else:
        prz_center = A["price"] + (xa * prz_ratio)
        direction_txt, badge_cls = f"🔴 {pat} بيعي (Bearish)", "badge-bear"
        target_1 = D["price"] - 0.382 * abs(A["price"] - D["price"])
        target_2 = D["price"] - 0.618 * abs(A["price"] - D["price"])

    prz_low, prz_high = round(prz_center * 0.985, 2), round(prz_center * 1.015, 2)
    return {
        "detected": True, "pattern_name": direction_txt, "badge_cls": badge_cls,
        "points": [X, A, B, C, D],
        "prz_low": prz_low, "prz_high": prz_high,
        "target_1": round(target_1, 2), "target_2": round(target_2, 2),
        "notes": f"نسبة تصحيح B/XA = {ab_xa:.2f} | امتداد D/XA = {ad_xa:.2f}. منطقة الانعكاس المحتملة (PRZ) تقع بين {prz_low} و {prz_high} ج.م (السعر الحالي: {curr_p:.2f})."
    }

def analyze_elliott_waves(df: pd.DataFrame, pct_thresh: float = 0.05) -> dict:
    pivs = extract_zigzag_pivots(df, pct_thresh=pct_thresh)
    if len(pivs) < 6:
        lo_p, hi_p = float(df["Low"].min()), float(df["High"].max())
        return {
            "wave_name": "🌊 موجة تأسيسية (1-2)", "badge_cls": "badge-warn",
            "invalidation": round(lo_p, 2), "target_1": round(hi_p, 2), "target_2": round(hi_p * 1.12, 2),
            "summary": "عدد القمم والقيعان في المدى المختار لا يزال في مراحل التأسيس الأولى.",
            "labeled_pivots": pivs, "rules_check": []
        }

    recent6 = pivs[-6:]
    labeled = [{**p, "label": lbl} for p, lbl in zip(recent6, ["(0)", "(1)", "(2)", "(3)", "(4)", "(5)"])]
    p0, p1, p2, p3, p4, p5 = [x["price"] for x in labeled]
    if p1 > p0 and p3 > p1:
        w1, w3, w5 = abs(p1 - p0), abs(p3 - p2), abs(p5 - p4)
        rules = [
            ("عدم كسر الموجة (2) لقاع (0)", f"{p2:.2f} > {p0:.2f}", p2 > p0),
            ("الموجة (3) ليست الأقصر", f"طولها {w3:.2f}", w3 >= min(w1, w5)),
            ("عدم تداخل (4) مع قمة (1)", f"{p4:.2f} > {p1:.2f}", p4 > p1),
        ]
        inv = round(p4, 2)
        return {
            "wave_name": "🌊 موجة دافعة صاعدة (1-2-3-4-5)", "badge_cls": "badge-bull",
            "invalidation": inv, "target_1": round(p5 + 0.618 * w1, 2), "target_2": round(p5 + 1.0 * w1, 2),
            "summary": f"السهم يتحرك في هيكل موجي صاعد. الحفاظ على قاع الموجة الرابعة ({inv} ج.م) يبقي المستهدفات الصاعدة فعالة.",
            "labeled_pivots": labeled, "rules_check": rules
        }
    else:
        w_a, inv = abs(p3 - p2), round(p4, 2)
        return {
            "wave_name": "🌊 موجة تصحيحية هابطة (A-B-C)", "badge_cls": "badge-bear",
            "invalidation": inv, "target_1": round(max(0.05, p5 - 0.618 * w_a), 2), "target_2": round(max(0.05, p5 - 1.0 * w_a), 2),
            "summary": f"السهم في مسار تصحيحي؛ اختراق قمة التصحيح الفرعية ({inv} ج.م) يلغي السيناريو الهابط.",
            "labeled_pivots": labeled, "rules_check": [("قمة B أقل من بداية التصحيح", f"{p4:.2f} < {p2:.2f}", p4 < p2)]
        }

ZODIAC_SIGNS_AR = ["♈ الحمل", "♉ الثور", "♊ الجوزاء", "♋ السرطان", "♌ الأسد", "♍ العذراء", "♎ الميزان", "♏ العقرب", "♐ القوس", "♑ الجدي", "♒ الدلو", "♓ الحوت"]
ORBITAL_ELEMENTS = {
    "Mercury": (0.38709927, 0.00000037, 0.20563593, 0.00001906, 7.00497902, -0.00594749, 252.25032350, 149472.67411175, 77.45779628, 0.16047689, 48.33076593, -0.12534081),
    "Venus":   (0.72333566, 0.00000390, 0.00677672, -0.00004107, 3.39467605, -0.00078890, 181.97909950, 58517.81538729, 131.60246718, 0.00268329, 76.67984255, -0.27769418),
    "Earth":   (1.00000261, 0.00000562, 0.01671123, -0.00004392, -0.00001531, -0.01294668, 100.46457166, 35999.37244981, 102.93768193, 0.32327364, 0.0, 0.0),
    "Mars":    (1.52371034, 0.00001847, 0.09339410, 0.00007882, 1.84969142, -0.00813131, -4.55343205, 19140.30268499, -23.94362959, 0.44441088, 49.55953891, -0.29257343),
    "Jupiter": (5.20288700, -0.00011607, 0.04838624, -0.00013253, 1.30439695, -0.00183714, 34.39644051, 3034.74612775, 14.72847983, 0.21252668, 100.47390909, 0.20469106),
    "Saturn":  (9.53667594, -0.00125060, 0.05386179, -0.00050991, 2.48599187, 0.00193609, 49.95424423, 1222.49362201, 92.59887831, -0.41897216, 113.66242448, -0.28867794),
}

def _julian_centuries(dt: datetime) -> float:
    return (dt.toordinal() + 1721424.5 + (dt.hour + dt.minute / 60.0) / 24.0 - 2451545.0) / 36525.0

def _heliocentric_xyz(planet_name: str, T: float) -> tuple:
    a0, da, e0, de, I0, dI, L0, dL, w0, dw, O0, dO = ORBITAL_ELEMENTS[planet_name]
    a, e = a0 + da * T, e0 + de * T
    I, L = math.radians(I0 + dI * T), (L0 + dL * T) % 360.0
    w_bar = (w0 + dw * T) % 360.0
    O = math.radians((O0 + dO * T) % 360.0)
    w = math.radians((w_bar - math.degrees(O)) % 360.0)
    M = math.radians((L - w_bar) % 360.0)
    E = M + e * math.sin(M)
    for _ in range(5):
        E -= (E - e * math.sin(E) - M) / (1.0 - e * math.cos(E))
    x_p, y_p = a * (math.cos(E) - e), a * math.sqrt(max(0.0, 1.0 - e * e)) * math.sin(E)
    cos_O, sin_O, cos_w, sin_w, cos_I, sin_I = math.cos(O), math.sin(O), math.cos(w), math.sin(w), math.cos(I), math.sin(I)
    return (
        (cos_O * cos_w - sin_O * sin_w * cos_I) * x_p + (-cos_O * sin_w - sin_O * cos_w * cos_I) * y_p,
        (sin_O * cos_w + cos_O * sin_w * cos_I) * x_p + (-sin_O * sin_w + cos_O * sin_w * cos_I) * y_p
    )

def get_planetary_longitudes(dt: datetime) -> dict:
    T = _julian_centuries(dt)
    xe, ye = _heliocentric_xyz("Earth", T)
    sun_lon = math.degrees(math.atan2(-ye, -xe)) % 360.0
    Lp = (218.3164477 + 481267.88123421 * T) % 360.0
    D = math.radians((297.8501921 + 445267.1114034 * T) % 360.0)
    Mp = math.radians((134.9633964 + 477198.8675055 * T) % 360.0)
    moon_lon = (Lp + 6.289 * math.sin(Mp) + 1.274 * math.sin(2 * D - Mp) + 0.658 * math.sin(2 * D)) % 360.0
    pos = {"☀️ الشمس": sun_lon, "🌙 القمر": moon_lon}
    for p_en, p_ar in [("Mercury", "☿ عطارد"), ("Venus", "♀ الزهرة"), ("Mars", "♂ المريخ"), ("Jupiter", "♃ المشتري"), ("Saturn", "♄ زحل")]:
        xp, yp = _heliocentric_xyz(p_en, T)
        pos[p_ar] = math.degrees(math.atan2(yp - ye, xp - xe)) % 360.0
    return pos

def deg_to_zodiac(deg: float) -> str:
    return f"{ZODIAC_SIGNS_AR[int(deg // 30) % 12]} ({deg % 30:.1f}°)"

def convert_deg_to_price(deg: float, ref_price: float) -> float:
    if ref_price <= 0:
        return round(deg, 2)
    scale = 1.0
    while (360.0 / scale) > ref_price * 2.2:
        scale *= 10.0
    while (360.0 / scale) < ref_price * 0.25:
        scale /= 10.0
    step, base_val = 360.0 / scale, deg / scale
    lvl = base_val + round((ref_price - base_val) / step) * step
    return round(lvl + step if lvl <= 0 else lvl, 2)

def add_egx_trading_days(start_dt: date, trading_days: int) -> date:
    curr, added = start_dt, 0
    while added < trading_days:
        curr += timedelta(days=1)
        if curr.weekday() in [6, 0, 1, 2, 3]:
            added += 1
    return curr

def compute_gann_and_planetary(pivot_date: date, pivot_price: float, is_pivot_low: bool, current_price: float, use_trading_days: bool):
    sqrt_p = math.sqrt(max(0.01, pivot_price))
    sq9_prices = []
    for ang in [45, 90, 135, 180, 270, 360]:
        step = ang / 180.0
        target_p = (sqrt_p + step) ** 2 if is_pivot_low else (max(0.1, sqrt_p - step)) ** 2
        sq9_prices.append({
            "الزاوية": f"{ang}°",
            "المستوى السعري": round(target_p, 2),
            "النوع": "مقاومة هندسية ⬆️" if is_pivot_low else "دعم هندسي ⬇️",
            "البعد %": round(((target_p - current_price) / current_price) * 100, 1)
        })

    price_time_sq = max(15, int(round(sqrt_p * 10)))
    today = get_cairo_now().date()
    time_targets = []
    for cyc in sorted(list(set([45, 60, 90, 120, 144, 180, 270, 360, price_time_sq]))):
        target_dt = add_egx_trading_days(pivot_date, cyc) if use_trading_days else (pivot_date + timedelta(days=cyc))
        diff_days = (target_dt - today).days
        if -15 <= diff_days <= 120:
            label = f"تربيع السعر ({cyc})" if cyc == price_time_sq else f"دورة جان ({cyc})"
            status = "🔥 نافذة انعكاس نشطة الآن!" if abs(diff_days) <= 3 else (f"بعد {diff_days} يوم" if diff_days > 0 else f"مضى منذ {abs(diff_days)} يوم")
            time_targets.append({"الدورة / المعادلة": label, "تاريخ الانعكاس المتوقع": target_dt, "الحالة الزمنية": status})

    upcoming_aspects, seen = [], set()
    for d_off in range(0, 31):
        pos = get_planetary_longitudes(datetime.combine(today + timedelta(days=d_off), datetime.min.time()) + timedelta(hours=12))
        for p1, p2 in [("☀️ الشمس", "🌙 القمر"), ("☀️ الشمس", "♂ المريخ"), ("☀️ الشمس", "♃ المشتري"), ("☀️ الشمس", "♄ زحل"), ("♂ المريخ", "♄ زحل")]:
            diff_deg = abs(pos[p1] - pos[p2]) % 360.0
            diff_deg = 360.0 - diff_deg if diff_deg > 180.0 else diff_deg
            for t_ang, asp_name in [(0, "اقتران ☌ (0°)"), (90, "تربيع □ (90°)"), (120, "تثليث △ (120°)"), (180, "تقابل ☍ (180°)")]:
                if abs(diff_deg - t_ang) <= 1.5 and f"{p1}-{p2}-{t_ang}" not in seen:
                    seen.add(f"{p1}-{p2}-{t_ang}")
                    upcoming_aspects.append({"التاريخ": today + timedelta(days=d_off), "الكوكبان": f"{p1} × {p2}", "الزاوية الفلكية": asp_name, "متبقي": "اليوم 🔴" if d_off == 0 else f"بعد {d_off} يوم"})

    return sq9_prices, time_targets, upcoming_aspects

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
        ca0, cl0 = gv(bs, ["Current Assets", "Total Current Assets"], 0), gv(bs, ["Current Liabilities", "Total Current Liabilities"], 0)
        ca1, cl1 = gv(bs, ["Current Assets", "Total Current Assets"], 1), gv(bs, ["Current Liabilities", "Total Current Liabilities"], 1)
        rev0, rev1 = gv(fin, ["Total Revenue", "Operating Revenue"], 0), gv(fin, ["Total Revenue", "Operating Revenue"], 1)
        gp0, gp1 = gv(fin, ["Gross Profit"], 0), gv(fin, ["Gross Profit"], 1)

        if ni0 is not None and ta0 and ta0 > 0:
            tests += 1; ok = (ni0 / ta0) > 0; f_score += int(ok)
            breakdown.append(("1. ربحية الأصول (ROA > 0)", f"{(ni0/ta0)*100:.1f}%", ok))
        if ocf0 is not None:
            tests += 1; ok = ocf0 > 0; f_score += int(ok)
            breakdown.append(("2. التدفق النقدي التشغيلي > 0", f"{ocf0/1e6:,.1f}M", ok))
        if all(v is not None and v != 0 for v in [ni0, ni1, ta0, ta1]):
            tests += 1; ok = (ni0 / ta0) > (ni1 / ta1); f_score += int(ok)
            breakdown.append(("3. نمو العائد على الأصول", f"{((ni0/ta0)-(ni1/ta1))*100:+.1f}%", ok))
        if ocf0 is not None and ni0 is not None:
            tests += 1; ok = ocf0 > ni0; f_score += int(ok)
            breakdown.append(("4. جودة الأرباح (OCF > Net Income)", "نقدي" if ok else "دفتري", ok))
        if all(v is not None and v > 0 for v in [ltd0, ltd1, ta0, ta1]):
            tests += 1; ok = (ltd0 / ta0) <= (ltd1 / ta1); f_score += int(ok)
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

        # تقويم الأرباح والكوبونات (V11.1)
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
            "roe": info.get("returnOnEquity"), "div_yield": info.get("dividendYield"),
            "market_cap": info.get("marketCap"),
            "f_score": f_score, "tests_available": tests, "breakdown": breakdown,
            "calendar": cal_info,
            "ex_dividend": earn_date,
            "dividend_rate": info.get("dividendRate"),
            "payout_ratio": info.get("payoutRatio"),
        }
    except Exception as e:
        return {"error": str(e)}

POS_WORDS = ["أرباح", "نمو", "توزيعات", "كوبون", "استحواذ", "ارتفاع", "قفزة", "توسعات", "عقد", "صفقة", "profit", "growth", "dividend", "surge"]
NEG_WORDS = ["خسائر", "تراجع", "هبوط", "إيقاف", "شطب", "غرامة", "مديونية", "عجز", "انخفاض", "loss", "decline", "drop", "suspend", "fine"]

@st.cache_data(ttl=1800, show_spinner=False)
def fetch_stock_news(symbol_clean: str) -> list:
    news_list = []
    try:
        query = urllib.parse.quote(f"{symbol_clean} البورصة المصرية")
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
force_sync = st.session_state.pop("force_cloud_sync", False)
my_portfolio, cloud_connected = load_portfolio(force_cloud_refresh=force_sync)
closed_trades = load_closed_trades(force_refresh=force_sync)
portfolio_clean_syms = [x["symbol"].upper().replace(".CA", "").strip() for x in my_portfolio if x.get("symbol")]

# ===== Watchlist (V11.1) =====
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

# قراءة الإعدادات من Session State أو Secrets
capital = int(st.session_state.get("cfg_capital", 100000))
risk_pct = float(st.session_state.get("cfg_risk_pct", 1.5))
min_turnover_m = float(st.session_state.get("cfg_min_turnover", 0.5))
fee_rate = 0.0016 if st.session_state.get("cfg_fee_tier", "0.16%") == "0.16%" else 0.0037
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

st.markdown(f"""
<div class="hero-banner">
    <div>
        <div class="hero-title">🦅 <span class="hero-accent">EGX WHALE HUNTER</span> PRO <span style="font-size:13px;color:#FACC15;">V11.0</span></div>
        <div class="hero-sub">🌐 تغطية ({len(raw_egx_tv_map)} سهم) • {sb_badge} • 💼 محفظتي ({len(portfolio_clean_syms)}) • {tg_badge} • آخر تحديث: {last_live_sync}</div>
    </div>
    <div class="session-pill">{session_info['badge']}</div>
</div>
""", unsafe_allow_html=True)

top_bar1, top_bar2, top_bar3 = st.columns([2.2, 1, 1])
with top_bar1:
    if not cloud_connected:
        st.caption("⚠️ **ملاحظة:** السحابة غير مربوطة حالياً؛ افحص الاتصال من تبويب **⚙️ الإعدادات** لحفظ أسهمك بشكل دائم.")
    else:
        st.caption("✅ **المزامنة السحابية نشطة:** جميع مراكزك وصفقاتك محفوظة بأمان على سحابة Supabase.")
with top_bar2:
    live_auto = st.checkbox("⚡ تحديث تلقائي (5 دقائق)", value=False)
with top_bar3:
    if st.button("🔄 تحديث الأسعار والسحابة الآن", use_container_width=True):
        st.session_state["refresh_nonce"] = refresh_nonce + 1
        st.session_state["force_cloud_sync"] = True
        fetch_full_egx_tv_scanner.clear()
        st.rerun()

# ==========================================
# معالجة بيانات السوق والرادار
# ==========================================
perf1m_list = [q["perf_1m"] for q in raw_egx_tv_map.values() if q.get("volume", 0) > 0]
market_median_perf1m = float(np.median(perf1m_list)) if perf1m_list else 0.0

# مزاج السوق (Market Mood) — breadth + VWAP
_gainers = sum(1 for q in raw_egx_tv_map.values() if float(q.get("change") or 0) > 0)
_total_st = len(raw_egx_tv_map) or 1
market_breadth_pct = (_gainers / _total_st) * 100.0
_vwap_above = sum(1 for q in raw_egx_tv_map.values() if float(q.get("close") or 0) > float(q.get("VWAP") or q.get("close") or 0))
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
    all_analyzed_map[sym] = analyzed
    if only_leaders and sym not in LEADERS_EGX_SYMBOLS:
        continue
    if analyzed["السيولة (مليون)"] >= min_turnover_m and analyzed["التغير %"] < 19.5:
        scanner_results.append(analyzed)

for known_sym in set(list(EGX_ARABIC_NAMES.keys()) + portfolio_clean_syms):
    if known_sym not in all_analyzed_map:
        p_item_ref = next((x for x in my_portfolio if x["symbol"].upper().replace(".CA", "").strip() == known_sym), {})
        c_val = round(float(p_item_ref.get("buy_price", 0.0)), 2)
        atr_val = round(max(0.01, c_val * 0.025), 3) if c_val > 0 else 0.1
        sl_val = round(max(0.01, c_val - 2.0 * atr_val), 2) if c_val > 0 else 0.0
        r_sh = max(0.01, c_val - sl_val)
        all_analyzed_map[known_sym] = {
            "الرمز": known_sym,
            "اسم الشركة": get_friendly_stock_name(known_sym),
            "Ticker": f"{known_sym}.CA",
            "السكور": 0, "نوع الإشارة": "📌 مدرج بالبورصة", "الرأي اللحظي": "⚪ انتظار",
            "الإغلاق": c_val, "ATR14": atr_val, "EMA20": c_val,
            "التغير %": 0.0, "الفوليوم": 0.0, "فرق VWAP %": 0.0, "القوة النسبية %": 0.0, "السيولة (مليون)": 0.0,
            "الوقف (2xATR)": sl_val,
            "TP1": round(c_val + 1.618 * r_sh, 2) if c_val > 0 else 0.0,
            "TP2": round(c_val + 2.618 * r_sh, 2) if c_val > 0 else 0.0,
            "TP3": round(c_val + 3.618 * r_sh, 2) if c_val > 0 else 0.0,
            "الأسهم": 0, "قيمة الصفقة": 0, "صافي TP1": 0,
            "التشخيص الفني": "بيانات السعر تُسحب من شارت Yahoo/TV",
            "score_parts": {"الاتجاه اليومي (30)": 0, "وتيرة السيولة ووايكوف (35)": 0, "التدفق اللحظي VWAP (35)": 0},
            "intraday_flow": analyze_intraday_flow({}, fallback_close=c_val, session_progress=session_info["progress"]),
            "tv_raw": {},
            "TradingView": f"https://www.tradingview.com/chart/?symbol=EGX:{known_sym}"
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
    atr14 = sinfo["ATR14"] if sinfo else round(buy_p * 0.025, 3)
    ema20 = sinfo.get("EMA20", curr_p) if sinfo else curr_p
    vwap_val = sinfo["intraday_flow"].get("vwap", curr_p) if sinfo else curr_p

    sl = user_sl if user_sl > 0 else round(max(0.01, buy_p - 2.0 * atr14), 2)
    r_unit = max(0.01, buy_p - sl)
    tp1 = user_tp1 if user_tp1 > 0 else round(buy_p + 1.618 * r_unit, 2)
    tp2 = user_tp2 if user_tp2 > 0 else round(buy_p + 2.618 * r_unit, 2)

    sl_updated = False
    if trailing_on:
        be_price = round(buy_p * (1.0 + fee_rate * 2.0), 2)
        if curr_p >= tp1 and trailing_stage < 1 and be_price < curr_p:
            sl = max(sl, be_price)
            trailing_stage = 1
            sl_updated = True
            active_alerts.append(("success", f"🛡️ <b>تأمين آلي ({sym}):</b> بعد تحقق TP1 تم رفع الوقف للتعادل (<b>{sl} ج.م</b>)."))
        if curr_p >= tp2:
            anchor = max(vwap_val, ema20) if (vwap_val > 0 and ema20 > 0) else curr_p
            cand_sl = round(min(curr_p - 0.5 * atr14, anchor * 0.992), 2)
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
    net_pnl = (mkt_val - cost_val) - (mkt_val * fee_rate)
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

    if alert_code and tg_body and tg_auto_port and tg_token and tg_chat_id:
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
        "الكمية": shares, "متوسط الشراء": round(buy_p, 2), "السعر الحالي": curr_p,
        "تغير اليوم %": sinfo["التغير %"] if sinfo else 0.0,
        "صافي الربح/الخسارة": round(net_pnl, 0), "العائد %": round(net_pnl_pct, 2),
        "وقف الخسارة": sl, "بُعد الوقف %": round(dist_sl_pct, 1),
        "TP1": tp1, "بُعد TP1 %": round(dist_tp1_pct, 1), "TP2": tp2,
        "progress_ratio": min(1.0, max(0.0, (curr_p - sl) / max(0.01, tp1 - sl))),
        "trailing_enabled": trailing_on, "trailing_stage": trailing_stage,
        "TradingView": f"https://www.tradingview.com/chart/?symbol=EGX:{sym}",
        "stock_info": sinfo
    })

if tg_auto_whales and tg_token and tg_chat_id:
    for r in filtered_results:
        if r["السكور"] >= 80:
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
        if tg_auto_port and tg_token and tg_chat_id:
            wk = "%s_WL_%s_%s" % (today_str, sym_w, target)
            if wk not in sent_tg_log:
                ok_w, _ = send_telegram_message(tg_token, tg_chat_id, msg)
                if ok_w:
                    record_sent_tg_alert(wk, get_cairo_now().strftime("%H:%M"), sent_tg_log)

# ==============================================================================
# التنقل الرئيسي المقسم إلى 4 علامات تبويب احترافية مستقلة
# ==============================================================================
tab_radar, tab_portfolio, tab_lab, tab_settings = st.tabs([
    f"🎯 رادار السوق والفرص ({len(filtered_results)})",
    f"💼 محفظتي وإدارة المخاطر ({len(portfolio_rows)})",
    "🔬 مختبر التحليل المؤسسي (10 مدارس)",
    "⚙️ الإعدادات والربط السحابي"
])

# ==============================================================================
# التبويب 1: رادار السوق والفرص
# ==============================================================================
with tab_radar:
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.markdown(f'<div class="kpi-card"><div class="kpi-label">📡 أسهم مفحوصة</div><div class="kpi-val">{len(raw_egx_tv_map)} سهم</div></div>', unsafe_allow_html=True)
    m2.markdown(f'<div class="kpi-card"><div class="kpi-label">🎯 صفقات نشطة</div><div class="kpi-val txt-green">{len(filtered_results)}</div></div>', unsafe_allow_html=True)
    m3.markdown(f'<div class="kpi-card"><div class="kpi-label">📈 أداء السوق (شهر)</div><div class="kpi-val {"txt-green" if market_median_perf1m>=0 else "txt-red"}">{market_median_perf1m:+.2f}%</div></div>', unsafe_allow_html=True)
    m4.markdown(f'<div class="kpi-card" style="border-top-color:#FACC15;"><div class="kpi-label">🛡️ المخاطرة المقترحة</div><div class="kpi-val txt-gold">{capital*(risk_pct/100):,.0f} ج.م</div></div>', unsafe_allow_html=True)
    m5.markdown(f'<div class="kpi-card" style="border-top-color:#22C55E;"><div class="kpi-label">🧭 مزاج السوق</div><div class="kpi-val" style="font-size:15px;"><span class="{market_mood_cls}">{market_mood_txt}</span><div style="font-size:11px;color:#475569;margin-top:2px;">Breadth {market_breadth_pct:.0f}% • VWAP {market_vwap_breadth:.0f}%</div></div></div>', unsafe_allow_html=True)
    st.write("")

    if watchlist_alerts:
        for _sym, _msg in watchlist_alerts:
            st.markdown('<div class="alert-box-success">%s</div>' % _msg, unsafe_allow_html=True)

    if filtered_results:
        st.markdown("### 🏆 أقوى 3 فرص سيولة وزخم الآن (Top 3 Radar)")
        top_n = filtered_results[:3]
        tcols = st.columns(len(top_n))
        medals = ["👑 المركز #1", "🔥 المركز #2", "⚡ المركز #3"]
        for idx, (cbox, item) in enumerate(zip(tcols, top_n)):
            cbox.markdown(f"""
            <div class="{'top-card top-card-gold' if idx==0 else 'top-card'}">
                <div style="display:flex;justify-content:space-between;margin-bottom:6px;">
                    <span class="txt-gold" style="font-weight:800;">{medals[idx]}</span>
                    <span class="badge-bull">{item['نوع الإشارة']}</span>
                </div>
                <div style="display:flex;justify-content:space-between;align-items:baseline;">
                    <span class="txt-white" style="font-size:23px;font-weight:900;">{item['الرمز']}</span>
                    <span class="txt-cyan" style="font-size:18px;font-weight:800;">{item['السكور']}/100</span>
                </div>
                <div style="font-size:12px;color:#FACC15;margin-bottom:6px;font-weight:700;">{item['اسم الشركة']}</div>
                <div style="font-size:13px;margin-bottom:8px;" class="txt-muted">
                    السعر: <b class="txt-white">{item['الإغلاق']}</b> (<span class="{'txt-green' if item['التغير %']>=0 else 'txt-red'}">{item['التغير %']:+.2f}%</span>) • وتيرة: <b class="txt-gold">{item['الفوليوم']}x</b> • {item['الرأي اللحظي']}
                </div>
                <div style="display:flex;justify-content:space-between;background:#F8FAFC;padding:8px 10px;border-radius:10px;font-size:12px;">
                    <span>🛑 الوقف: <b class="txt-red">{item['الوقف (2xATR)']}</b></span>
                    <span>🎯 TP1: <b class="txt-green">{item['TP1']}</b></span>
                    <span>💰 صافي: <b class="txt-green">{item['صافي TP1']:,.0f}</b></span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.write("")
        rf1, rf2 = st.columns([2, 1])
        with rf1:
            radar_search = st.text_input("🔎 تصفية سريعة بالرمز أو اسم الشركة:", placeholder="اكتب مثلاً: ABUK أو بنك أو أسمدة...")
        with rf2:
            sig_filter = st.selectbox("📌 نوع الإشارة:", ["الكل", "🔥 تدفق سيولة", "📈 زخم سيولة", "🎯 تصحيح بلا بائع", "📊 متابعة فنية"])

        df_rad = pd.DataFrame(filtered_results)
        if radar_search.strip():
            q_s = radar_search.strip().upper()
            df_rad = df_rad[df_rad["الرمز"].str.contains(q_s, na=False) | df_rad["اسم الشركة"].str.contains(radar_search.strip(), na=False)]
        if sig_filter != "الكل":
            df_rad = df_rad[df_rad["نوع الإشارة"] == sig_filter]

        st.dataframe(
            df_rad[["الرمز", "اسم الشركة", "السكور", "الرأي اللحظي", "نوع الإشارة", "الإغلاق", "التغير %", "الفوليوم", "فرق VWAP %", "السيولة (مليون)", "الوقف (2xATR)", "TP1", "TP2", "الأسهم", "صافي TP1", "TradingView"]],
            use_container_width=True, hide_index=True, height=400,
            column_config={
                "TradingView": st.column_config.LinkColumn("شارت TV", display_text="فتح ↗"),
                "السكور": st.column_config.ProgressColumn("السكور", min_value=0, max_value=100, format="%d"),
                "الفوليوم": st.column_config.NumberColumn("وتيرة السيولة", format="%.2fx"),
            }
        )
    else:
        st.warning("⚠️ لا توجد أسهم تطابق شروط الفلتر الحالية؛ يمكنك تقليل الحد الأدنى للسكور من تبويب **⚙️ الإعدادات**.")

# ==============================================================================
# التبويب 2: محفظتي وإدارة المخاطر (3 علامات تبويب فرعية نظيفة)
# ==============================================================================
with tab_portfolio:
    if st.session_state.get("last_port_msg"):
        st.success(st.session_state["last_port_msg"])

    for lvl, msg in active_alerts:
        st.markdown(f'<div class="alert-box-{lvl}">{msg}</div>', unsafe_allow_html=True)

    total_net_pnl = total_port_val - total_port_cost - (total_port_val * fee_rate)
    total_pnl_pct = ((total_net_pnl / total_port_cost) * 100.0) if total_port_cost > 0 else 0.0
    open_risk_pct = (total_open_risk / max(1.0, total_port_val)) * 100.0 if total_port_val > 0 else 0.0

    pk1, pk2, pk3, pk4 = st.columns(4)
    pk1.markdown(f'<div class="kpi-card"><div class="kpi-label">💵 إجمالي التكلفة</div><div class="kpi-val">{total_port_cost:,.0f} ج.م</div></div>', unsafe_allow_html=True)
    pk2.markdown(f'<div class="kpi-card"><div class="kpi-label">💰 القيمة الحالية</div><div class="kpi-val txt-cyan">{total_port_val:,.0f} ج.م</div></div>', unsafe_allow_html=True)
    pk3.markdown(f'<div class="kpi-card"><div class="kpi-label">📈 صافي الربح/الخسارة</div><div class="kpi-val {"txt-green" if total_net_pnl>=0 else "txt-red"}">{total_net_pnl:+,.0f} ({total_pnl_pct:+.1f}%)</div></div>', unsafe_allow_html=True)
    pk4.markdown(f'<div class="kpi-card" style="border-top-color:#FACC15;"><div class="kpi-label">🛡️ المخاطرة المفتوحة</div><div class="kpi-val txt-gold">{total_open_risk:,.0f} ({open_risk_pct:.1f}%)</div></div>', unsafe_allow_html=True)
    st.write("")
    # ===== خريطة حرارة المحفظة (Treemap) V11.1 =====
    if portfolio_rows:
        try:
            import plotly.express as _px
            _tdf = pd.DataFrame(portfolio_rows)
            _fig_tm = _px.treemap(
                _tdf, path=["الرمز"], values="الكمية",
                color="العائد %", color_continuous_scale="RdYlGn", color_continuous_midpoint=0,
                title="خريطة حرارة المحفظة (حجم = كمية، لون = العائد %)",
            )
            _fig_tm.update_layout(height=360, template="plotly_white", paper_bgcolor="#FFFFFF", margin=dict(l=10,r=10,t=40,b=10))
            st.plotly_chart(_fig_tm, use_container_width=True)
        except Exception as _e:
            st.caption("تعذر رسم الخريطة: %s" % _e)

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
            if st.button("📲 إرسال تقرير محفظتي اللحظي إلى تليجرام", use_container_width=True):
                if not tg_token or not tg_chat_id:
                    st.warning("⚠️ اربط التليجرام أولاً من تبويب **⚙️ الإعدادات**.")
                else:
                    lines = [f"📊 <b>تقرير محفظتك</b> | القيمة: <b>{total_port_val:,.0f} ج.م</b> | الصافي: <b>{total_net_pnl:+,.0f} ({total_pnl_pct:+.1f}%)</b>", ""]
                    for pr in portfolio_rows:
                        lines.append(f"• <b>{pr['الرمز']}</b> ({pr['اسم الشركة']}): السعر {pr['السعر الحالي']} ({pr['العائد %']:+.1f}%) | SL: {pr['وقف الخسارة']} | TP1: {pr['TP1']}")
                    ok_r, r_m = send_telegram_message(tg_token, tg_chat_id, "\n".join(lines))
                    st.success("✅ تم الإرسال لتليجرام!") if ok_r else st.error(f"❌ {r_m}")

            st.dataframe(
                pd.DataFrame(portfolio_rows)[["الرمز", "اسم الشركة", "الرأي اللحظي", "حالة التنبيه", "الوقف المتحرك", "السكور الفني", "الكمية", "متوسط الشراء", "السعر الحالي", "صافي الربح/الخسارة", "العائد %", "وقف الخسارة", "بُعد الوقف %", "TP1", "TP2", "TradingView"]],
                use_container_width=True, hide_index=True,
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
                if st.button(f"🛡️ تأمين {port_sel} للتعادل", use_container_width=True):
                    be_val = round(p_item["متوسط الشراء"] * (1.0 + fee_rate * 2.0), 2)
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
                if st.button(f"🗑️ حذف {port_sel}", use_container_width=True):
                    _, d_st = delete_portfolio_item(port_sel)
                    st.session_state["last_port_msg"] = f"🗑️ تم حذف {port_sel} ({d_st})."
                    st.rerun()

            clc1, clc2 = st.columns([1.3, 1.7])
            with clc1:
                exit_p = st.number_input(f"💵 سعر البيع الفعلي لإغلاق {port_sel} (ج.م):", min_value=0.01, value=float(p_item["السعر الحالي"]), step=0.05)
            with clc2:
                st.write(""); st.write("")
                if st.button(f"💰 إغلاق صفقة {port_sel} وتسجيلها في دفتر الصفقات", type="primary", use_container_width=True):
                    n_res, p_res = record_closed_trade(port_sel, p_item["الكمية"], p_item["متوسط الشراء"], exit_p, fee_rate)
                    st.session_state["last_port_msg"] = f"✅ تم إغلاق صفقة {port_sel} ({p_item['اسم الشركة']}) بصافي {n_res:+,.0f} ج.م ({p_res:+.1f}%)!"
                    st.rerun()

            df_ph = fetch_single_stock_history(f"{port_sel}.CA")
            if not df_ph.empty:
                sub_p = df_ph.tail(90)
                fig_p = go.Figure(go.Candlestick(x=sub_p.index, open=sub_p["Open"], high=sub_p["High"], low=sub_p["Low"], close=sub_p["Close"], name="السعر"))
                fig_p.add_hline(y=p_item["متوسط الشراء"], line_dash="dot", line_color="#FACC15", annotation_text=f"شرائك: {p_item['متوسط الشراء']}")
                fig_p.add_hline(y=p_item["وقف الخسارة"], line_dash="dash", line_color="#F87171", annotation_text=f"SL: {p_item['وقف الخسارة']}")
                fig_p.add_hline(y=p_item["TP1"], line_dash="dash", line_color="#4ADE80", annotation_text=f"TP1: {p_item['TP1']}")
                fig_p.add_hline(y=p_item["TP2"], line_dash="dash", line_color="#10B981", annotation_text=f"TP2: {p_item['TP2']}")
                fig_p.update_layout(title=f"📊 مستويات مركزك في {port_sel} ({p_item['اسم الشركة']})", height=420, xaxis_rangeslider_visible=False, template="plotly_white", paper_bgcolor="#FFFFFF", plot_bgcolor="#F8FAFC", margin=dict(l=10, r=10, t=40, b=10))
                st.plotly_chart(fig_p, use_container_width=True)

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

        if st.button("💾 حفظ السهم في محفظتي وتفعيل الحماية", type="primary", use_container_width=True):
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
            parsed_ops = parse_thndr_files(thndr_files, EGX_ARABIC_NAMES)
            if not parsed_ops:
                st.warning("⚠️ لم يتم التعرف على بنود الصفقة تلقائياً داخل الملف؛ تأكد أنه فاتورة تنفيذ أو كشف حساب ثاندر.")
            else:
                st.info(f"✅ تم استخراج **{len(parsed_ops)}** عملية من مستندات ثاندر — راجع الجدول أو عدّل أي رقم قبل الاعتماد:")
                edited_ops = st.data_editor(pd.DataFrame(parsed_ops), use_container_width=True, hide_index=True, num_rows="dynamic")
                if st.button("🚀 اعتماد العمليات وتحديث المحفظة والسحابة فوراً", type="primary", use_container_width=True):
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
                                avg_bp = round(((old_sh * old_bp) + (qty_o * prc_o)) / tot_sh, 2)
                                upsert_portfolio_item({**ex_item, "shares": tot_sh, "buy_price": avg_bp})
                            else:
                                s_inf = all_analyzed_map.get(sym_o, {})
                                atr_v = s_inf.get("ATR14", prc_o * 0.025)
                                sl_v = round(max(0.01, prc_o - 2.0 * atr_v), 2)
                                r_u = max(0.01, prc_o - sl_v)
                                upsert_portfolio_item({
                                    "symbol": sym_o, "shares": qty_o, "buy_price": prc_o,
                                    "stop_loss": sl_v, "tp1": round(prc_o + 1.618 * r_u, 2),
                                    "tp2": round(prc_o + 2.618 * r_u, 2),
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
            # ===== Risk Analytics (V11.1) =====
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
            rk4.markdown(f'<div class="kpi-card" style="border-top-color:#FACC15;"><div class="kpi-label">🎯 Expectancy/صفقة</div><div class="kpi-val txt-gold">{_expectancy:+,.0f} ج.م</div></div>', unsafe_allow_html=True)
            rk5, rk6, rk7, rk8 = st.columns(4)
            rk5.markdown(f'<div class="kpi-card"><div class="kpi-label">🏆 متوسط ربح</div><div class="kpi-val txt-green">{_avg_win:+,.0f} ج.م</div></div>', unsafe_allow_html=True)
            rk6.markdown(f'<div class="kpi-card"><div class="kpi-label">💔 متوسط خسارة</div><div class="kpi-val txt-red">{_avg_loss:+,.0f} ج.م</div></div>', unsafe_allow_html=True)
            rk7.markdown(f'<div class="kpi-card"><div class="kpi-label">📊 Calmar</div><div class="kpi-val txt-cyan">{_calmar:+.2f}</div></div>', unsafe_allow_html=True)
            rk8.markdown(f'<div class="kpi-card"><div class="kpi-label">🔢 عدد الصفقات</div><div class="kpi-val">{len(closed_trades)}</div></div>', unsafe_allow_html=True)
            if _cum_series:
                import plotly.graph_objects as _go
                _fig_cum = _go.Figure(_go.Scatter(y=_cum_series, mode="lines+markers", line=dict(color="#0284C7", width=2.5), fill="tozeroy", fillcolor="rgba(2,132,199,0.12)"))
                _fig_cum.update_layout(title="📈 منحنى الأرباح التراكمية (Equity Curve)", height=320, template="plotly_white", paper_bgcolor="#FFFFFF", plot_bgcolor="#F8FAFC", margin=dict(l=10,r=10,t=40,b=10))
                st.plotly_chart(_fig_cum, use_container_width=True)
            st.write("")

            st.dataframe(pd.DataFrame([
                {"الرمز": t.get("symbol"), "اسم الشركة": get_friendly_stock_name(t.get("symbol", "")), "الكمية": t.get("shares"), "سعر الشراء": t.get("buy_price"), "سعر البيع": t.get("sell_price"), "صافي الربح/الخسارة": t.get("net_pnl"), "العائد %": t.get("pnl_pct"), "التاريخ": str(t.get("closed_at", ""))[:16].replace("T", " ")}
                for t in closed_trades
            ]), use_container_width=True, hide_index=True)

        st.divider()
        st.markdown("#### 💾 النسخ الاحتياطي والاستعادة + تصدير Excel")
        b1, b2, b3 = st.columns(3)
        with b1:
            st.download_button(
                "⬇️ نسخة احتياطية (JSON)",
                data=json.dumps(my_portfolio, ensure_ascii=False, indent=2),
                file_name=f"egx_portfolio_{today_str}.json",
                mime="application/json",
                use_container_width=True
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
                    use_container_width=True
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
with tab_lab:
    if not all_analyzed_map:
        st.warning("⚠️ جاري تحميل بيانات الأسهم...")
    else:
        port_set = {p["الرمز"] for p in portfolio_rows}
        radar_set = {r["الرمز"] for r in filtered_results}
        ordered_symbols = sorted(list(port_set)) + [r["الرمز"] for r in filtered_results if r["الرمز"] not in port_set] + sorted([s for s in all_analyzed_map if s not in port_set and s not in radar_set])

        selected_symbol = st.selectbox(
            f"🔬 اختر السهم للدراسة العميقة ({len(ordered_symbols)} سهم — اكتب الرمز للبحث الفوري):",
            options=ordered_symbols,
            format_func=lambda s: f"{'💼 [محفظتي] ' if s in port_set else ('🎯 [رادار] ' if s in radar_set else '📌 ')}{s} — {all_analyzed_map[s]['اسم الشركة']} | {all_analyzed_map[s]['الرأي اللحظي']} | سكور: {all_analyzed_map[s]['السكور']}/100"
        )
        selected_data = all_analyzed_map[selected_symbol]
        chg_s = selected_data["التغير %"]

        mtf_txt = "⚪ غير متوفر"
        try:
            _df_mtf = fetch_single_stock_history(selected_data["Ticker"])
            if not _df_mtf.empty and len(_df_mtf) >= 40:
                _w = _df_mtf.resample("W").agg({"Open":"first","High":"max","Low":"min","Close":"last","Volume":"sum"}).dropna()
                if len(_w) >= 8:
                    _w["EMA20w"] = _w["Close"].ewm(span=20, adjust=False).mean()
                    _last = float(_w["Close"].iloc[-1])
                    _ema = float(_w["EMA20w"].iloc[-1])
                    _prev = float(_w["Close"].iloc[-2])
                    if _last > _ema and _last > _prev:
                        mtf_txt = "🟢 صاعد (أسبوعي)"
                    elif _last < _ema and _last < _prev:
                        mtf_txt = "🔴 هابط (أسبوعي)"
                    else:
                        mtf_txt = "🟡 محايد (أسبوعي)"
        except Exception:
            pass


        st.markdown(f"""
        <div class="stock-header-strip">
            <div>
                <span class="txt-cyan" style="font-size:22px;font-weight:900;">{selected_symbol}</span>
                <span class="txt-gold" style="font-size:17px;font-weight:800;margin-right:10px;">{selected_data['اسم الشركة']}</span>
                <div style="font-size:13px;color:#94A3B8;margin-top:3px;">{selected_data['التشخيص الفني']}</div>
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

        t_flow, t_smc, t_wyk, t_cpr, t_harm, t_ew, t_tech, t_fund, t_gann, t_news = st.tabs([
            "⚡ التدفق اللحظي وعمق السيولة",
            "🏦 الأموال الذكية و ICT",
            "🐋 وايكوف و PVSRA",
            "🎯 CPR وبروفايل السيولة",
            "🦋 النماذج التوافقية",
            "🌊 موجات إليوت",
            "📈 الشارت وخطة التنفيذ",
            "📊 التحليل المالي F-Score",
            "🪐 التحليل الزمني وجان",
            "📰 الرادار الخبري"
        ])

        # 1) التدفق اللحظي وعمق السيولة الأوتوماتيكي 100%
        with t_flow:
            flow = selected_data["intraday_flow"]
            tv_r = selected_data.get("tv_raw", {})
            fk1, fk2, fk3, fk4 = st.columns(4)
            fk1.markdown(f'<div class="kpi-card"><div class="kpi-label">🧭 القرار اللحظي</div><div class="kpi-val" style="font-size:16px;">{flow["short_verdict"]} ({flow["flow_score"]:+d})</div></div>', unsafe_allow_html=True)
            fk2.markdown(f'<div class="kpi-card"><div class="kpi-label">⚖️ متوسط السيولة VWAP</div><div class="kpi-val {"txt-green" if flow["vwap_diff_pct"]>=0 else "txt-red"}">{flow["vwap"]} ({flow["vwap_diff_pct"]:+.2f}%)</div></div>', unsafe_allow_html=True)
            fk3.markdown(f'<div class="kpi-card"><div class="kpi-label">⏱️ زخم 15 دقيقة (RSI)</div><div class="kpi-val txt-cyan">{flow["rsi15"]}</div></div>', unsafe_allow_html=True)
            fk4.markdown(f'<div class="kpi-card" style="border-top-color:#FACC15;"><div class="kpi-label">💧 وتيرة السيولة الآن</div><div class="kpi-val txt-gold">{flow["rel_vol"]}x</div></div>', unsafe_allow_html=True)
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
                    <div style="background:#F8FAFC;padding:10px;border-radius:8px;border-right:4px solid #38BDF8;">
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
                    <div class="pro-card" style="border-right-color:#FACC15;">
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
                <div class="pro-card" style="border-right-color:#38BDF8;">
                    <h4 class="txt-cyan" style="margin-top:0;">⚖️ صافي التدفق المنفذ (Order Flow Delta — أوتوماتيك)</h4>
                    <p class="txt-muted" style="font-size:12px;">تحليل تلقائي لحجم السيولة المنفذة فعلياً على العرض مقابل الطلب دون أي إدخال يدوي:</p>
                    <div style="display:flex;justify-content:space-between;font-size:13px;font-weight:700;margin-bottom:4px;">
                        <span class="txt-green">🟢 شراء منفذ: {buy_vol_est:,.0f} ({buy_bar_w}%)</span>
                        <span class="txt-red">🔴 بيع منفذ: {sell_vol_est:,.0f} ({100-buy_bar_w}%)</span>
                    </div>
                    <div style="width:100%;height:10px;background:#EF4444;border-radius:999px;overflow:hidden;margin-bottom:10px;">
                        <div style="width:{buy_bar_w}%;height:100%;background:#22C55E;"></div>
                    </div>
                    <p class="txt-white">📊 صافي الدلتا (Net Delta): <b class="{'txt-green' if net_delta>=0 else 'txt-red'}">{net_delta:+,.0f} سهم ({delta_pct:+.1f}%)</b></p>
                    <div style="background:#F8FAFC;padding:9px 12px;border-radius:8px;">
                        <b>الخلاصة اللحظية:</b> {delta_verdict}
                    </div>
                </div>
                """, unsafe_allow_html=True)

        # 2) الأموال الذكية و ICT
        with t_smc:
            df_h = fetch_single_stock_history(selected_data["Ticker"])
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
                        col_o = "#4ADE80" if "طلب" in ob["النوع"] else "#F87171"
                        fig_smc.add_hrect(y0=ob["من"], y1=ob["إلى"], line_dash="dot", line_color=col_o, fillcolor="rgba(56,189,248,0.08)", annotation_text="OB", annotation_font_size=10)
                    fig_smc.update_layout(title=f"🏦 مناطق Order Blocks و FVG لسهم {selected_symbol}", height=500, xaxis_rangeslider_visible=False, template="plotly_white", paper_bgcolor="#FFFFFF", plot_bgcolor="#F8FAFC", margin=dict(l=10, r=10, t=40, b=10))
                    st.plotly_chart(fig_smc, use_container_width=True)
                with c2:
                    sweeps_html = "".join([f"<li>{s}</li>" for s in smc["sweeps"]]) if smc["sweeps"] else "<li>لا يوجد سحب سيولة حاد في آخر 10 جلسات.</li>"
                    st.markdown(f"""
                    <div class="pro-card">
                        <h4 class="txt-cyan" style="margin-top:0;">🧭 هيكل السوق المؤسسي</h4>
                        <p><span class="{smc['badge_cls']}">{smc['structure']}</span></p>
                        <p class="txt-white"><b>قمة الهيكل (Swing High):</b> {smc['swing_high'] or '—'} | <b>قاع الهيكل:</b> {smc['swing_low'] or '—'}</p>
                        <hr style="border-color:#26334D;">
                        <b class="txt-gold">🎯 رصد سحب السيولة (Liquidity Sweeps):</b>
                        <ul class="txt-white" style="padding-right:18px;font-size:13px;">{sweeps_html}</ul>
                    </div>
                    """, unsafe_allow_html=True)
                    if smc["obs"]:
                        st.markdown("##### 🧱 كتل الأوامر (Order Blocks)")
                        st.dataframe(pd.DataFrame(smc["obs"]), use_container_width=True, hide_index=True)
                    if smc["fvgs"]:
                        st.markdown("##### 🕳️ فجوات القيمة العادلة (FVG)")
                        st.dataframe(pd.DataFrame(smc["fvgs"]), use_container_width=True, hide_index=True)

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
                            v_cols.append("#4ADE80" if r["Close"] >= r["Open"] else "#F87171")
                    fig_w.add_trace(go.Bar(x=sub_w.index, y=sub_w["Volume"], marker_color=v_cols, name="PVSRA Volume"), row=2, col=1)
                    fig_w.add_trace(go.Scatter(x=sub_w.index, y=sub_w["VolSMA20"], line=dict(color="#FACC15", width=1.4), name="متوسط 20"), row=2, col=1)
                    fig_w.update_layout(title=f"🐋 بصمة الحيتان PVSRA ونطاق وايكوف: {selected_symbol}", height=500, xaxis_rangeslider_visible=False, template="plotly_white", paper_bgcolor="#FFFFFF", plot_bgcolor="#F8FAFC", margin=dict(l=10, r=10, t=40, b=10))
                    st.plotly_chart(fig_w, use_container_width=True)
                with c2:
                    notes_html = "".join([f"<li style='margin-bottom:6px;'>{n}</li>" for n in wyk["vsa_notes"]])
                    st.markdown(f"""
                    <div class="pro-card">
                        <h4 class="txt-cyan" style="margin-top:0;">📊 مرحلة السهم وفق وايكوف</h4>
                        <p><span class="{wyk['badge_cls']}">{wyk['phase']}</span></p>
                        <p class="txt-white"><b>سقف النطاق:</b> {wyk['box_high']} | <b>قاع النطاق:</b> {wyk['box_low']}</p>
                        <p class="txt-white"><b>نسبة فوليوم آخر جلسة:</b> <span class="txt-gold">{wyk['vol_ratio']}x</span></p>
                        <hr style="border-color:#26334D;">
                        <ul class="txt-white" style="padding-right:18px;font-size:13px;">{notes_html}</ul>
                    </div>
                    """, unsafe_allow_html=True)
                    if wyk["whale_candles"]:
                        st.markdown("##### 🐋 أحدث شموع الحيتان (PVSRA ≥ 2.0x)")
                        st.dataframe(pd.DataFrame(wyk["whale_candles"]), use_container_width=True, hide_index=True)

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
                    fig_vp.add_hline(y=cvp["vah"], line_dash="dash", line_color="#4ADE80", annotation_text=f"VAH: {cvp['vah']}", row=1, col=1)
                    fig_vp.add_hline(y=cvp["val"], line_dash="dash", line_color="#F87171", annotation_text=f"VAL: {cvp['val']}", row=1, col=1)
                    fig_vp.add_hrect(y0=cvp["bc"], y1=cvp["tc"], fillcolor="rgba(56,189,248,0.18)", line_color="#38BDF8", line_dash="dot", annotation_text="CPR", row=1, col=1)
                    vp_colors = ["#FACC15" if round(p, 2) == cvp["poc"] else "#38BDF8" for p in cvp["bin_centers"]]
                    fig_vp.add_trace(go.Bar(y=cvp["bin_centers"], x=cvp["vol_hist"], orientation="h", marker_color=vp_colors, name="Volume Profile"), row=1, col=2)
                    fig_vp.update_layout(title=f"🎯 خريطة CPR وبروفايل السيولة الأفقي: {selected_symbol}", height=510, xaxis_rangeslider_visible=False, template="plotly_white", paper_bgcolor="#FFFFFF", plot_bgcolor="#F8FAFC", showlegend=False, margin=dict(l=10, r=10, t=40, b=10))
                    st.plotly_chart(fig_vp, use_container_width=True)
                with c2:
                    st.markdown(f"""
                    <div class="pro-card">
                        <h4 class="txt-cyan" style="margin-top:0;">📐 مستويات صناع السوق</h4>
                        <p><span class="{cvp['badge_cls']}">{cvp['verdict']}</span></p>
                        <p class="txt-white"><b>نقطة التحكم (POC):</b> <span class="txt-gold" style="font-weight:bold;">{cvp['poc']} ج.م</span></p>
                        <p class="txt-white"><b>أعلى منطقة القيمة (VAH):</b> <span class="txt-green">{cvp['vah']}</span></p>
                        <p class="txt-white"><b>أدنى منطقة القيمة (VAL):</b> <span class="txt-red">{cvp['val']}</span></p>
                        <hr style="border-color:#26334D;">
                        <p class="txt-white"><b>نطاق CPR:</b> {cvp['bc']} — {cvp['tc']} (Pivot: {cvp['pivot']})</p>
                        <p class="txt-white"><b>عرض النطاق:</b> {cvp['cpr_width_pct']}% {'🔥 (ضيق — انفجار سعري وشيك)' if cvp['cpr_width_pct'] <= 2.5 else ''}</p>
                        <p class="txt-white"><b>مقاومة R1:</b> {cvp['r1']} | <b>دعم S1:</b> {cvp['s1']}</p>
                    </div>
                    """, unsafe_allow_html=True)

        # 5) النماذج التوافقية
        with t_harm:
            df_h = fetch_single_stock_history(selected_data["Ticker"])
            if df_h.empty or len(df_h) < 50:
                st.info("ℹ️ البيانات التاريخية غير كافية لرصد النماذج التوافقية.")
            else:
                harm = analyze_harmonic_patterns(df_h)
                c1, c2 = st.columns([2.1, 1])
                with c1:
                    sub_hm = df_h.tail(160)
                    fig_hm = go.Figure(go.Candlestick(x=sub_hm.index, open=sub_hm["Open"], high=sub_hm["High"], low=sub_hm["Low"], close=sub_hm["Close"], name="السعر"))
                    if harm["points"]:
                        pts = harm["points"]
                        lbls = ["X", "A", "B", "C", "D"]
                        fig_hm.add_trace(go.Scatter(
                            x=[p["date"] for p in pts], y=[p["price"] for p in pts],
                            mode="lines+markers+text", line=dict(color="#FACC15", width=3),
                            marker=dict(size=10, color="#38BDF8"),
                            text=[f"{l} ({p['price']:.2f})" for l, p in zip(lbls, pts)],
                            textposition="top center", name="XABCD"
                        ))
                    if harm["prz_low"] and harm["prz_high"]:
                        fig_hm.add_hrect(y0=harm["prz_low"], y1=harm["prz_high"], fillcolor="rgba(250,204,21,0.20)", line_color="#FACC15", annotation_text="PRZ")
                    fig_hm.update_layout(title=f"🦋 مسح النماذج التوافقية: {selected_symbol}", height=500, xaxis_rangeslider_visible=False, template="plotly_white", paper_bgcolor="#FFFFFF", plot_bgcolor="#F8FAFC", margin=dict(l=10, r=10, t=40, b=10))
                    st.plotly_chart(fig_hm, use_container_width=True)
                with c2:
                    st.markdown(f"""
                    <div class="pro-card">
                        <h4 class="txt-cyan" style="margin-top:0;">🦋 تشخيص النموذج التوافقي</h4>
                        <p><span class="{harm['badge_cls']}">{harm['pattern_name']}</span></p>
                        <p class="txt-white" style="font-size:14px;">{harm['notes']}</p>
                        <hr style="border-color:#26334D;">
                        <p class="txt-white"><b>منطقة الانعكاس (PRZ):</b> <span class="txt-gold">{harm.get('prz_low', '—')} — {harm.get('prz_high', '—')}</span></p>
                        <p class="txt-white"><b>الهدف الأول (38.2% AD):</b> <span class="txt-green">{harm.get('target_1', '—')}</span></p>
                        <p class="txt-white"><b>الهدف الثاني (61.8% AD):</b> <span class="txt-green">{harm.get('target_2', '—')}</span></p>
                    </div>
                    """, unsafe_allow_html=True)

        # 6) موجات إليوت
        with t_ew:
            df_ew = fetch_single_stock_history(selected_data["Ticker"])
            if df_ew.empty or len(df_ew) < 25:
                st.info("ℹ️ البيانات التاريخية غير كافية لترقيم موجات إليوت.")
            else:
                deg = st.radio("🎚️ حساسية الموجات:", ["متوسطة (5%)", "قصيرة (3%)", "رئيسية (8%)"], horizontal=True)
                pct_v = 0.03 if "3%" in deg else (0.08 if "8%" in deg else 0.05)
                ew_res = analyze_elliott_waves(df_ew.tail(220), pct_thresh=pct_v)
                c1, c2 = st.columns([2.1, 1])
                with c1:
                    sub_e = df_ew.tail(220)
                    fig_e = go.Figure(go.Candlestick(x=sub_e.index, open=sub_e["Open"], high=sub_e["High"], low=sub_e["Low"], close=sub_e["Close"], name="السعر"))
                    lp = ew_res["labeled_pivots"]
                    if lp:
                        fig_e.add_trace(go.Scatter(x=[p["date"] for p in lp], y=[p["price"] for p in lp], mode="lines+markers+text", line=dict(color="#38BDF8", width=2.8), marker=dict(size=9, color="#FACC15"), text=[p.get("label", "") for p in lp], textposition="top center", name="Waves"))
                    fig_e.add_hline(y=ew_res["invalidation"], line_dash="dash", line_color="#F87171", annotation_text=f"إلغاء: {ew_res['invalidation']}")
                    fig_e.add_hline(y=ew_res["target_1"], line_dash="dot", line_color="#4ADE80", annotation_text=f"هدف 1: {ew_res['target_1']}")
                    fig_e.update_layout(title=f"🌊 خريطة موجات إليوت: {selected_symbol}", height=500, xaxis_rangeslider_visible=False, template="plotly_white", paper_bgcolor="#FFFFFF", plot_bgcolor="#F8FAFC", margin=dict(l=10, r=10, t=40, b=10))
                    st.plotly_chart(fig_e, use_container_width=True)
                with c2:
                    st.markdown(f"""
                    <div class="pro-card">
                        <h4 class="txt-cyan" style="margin-top:0;">🧭 القراءة الموجية</h4>
                        <p><span class="{ew_res['badge_cls']}">{ew_res['wave_name']}</span></p>
                        <p class="txt-white">{ew_res['summary']}</p>
                        <hr style="border-color:#26334D;">
                        <p class="txt-white"><b>نقطة الإلغاء:</b> <span class="txt-red">{ew_res['invalidation']}</span></p>
                        <p class="txt-white"><b>الهدف الأول:</b> <span class="txt-green">{ew_res['target_1']}</span> | <b>الثاني:</b> <span class="txt-gold">{ew_res['target_2']}</span></p>
                    </div>
                    """, unsafe_allow_html=True)
                    if ew_res["rules_check"]:
                        df_r = pd.DataFrame(ew_res["rules_check"], columns=["القاعدة", "القيمة", "الحالة"])
                        df_r["الحالة"] = df_r["الحالة"].map({True: "✅ محقق", False: "⚠️ مراقبة"})
                        st.dataframe(df_r, use_container_width=True, hide_index=True)

        # 7) الشارت الفني وخطة التنفيذ
        with t_tech:
            df_h = fetch_single_stock_history(selected_data["Ticker"])
            c1, c2 = st.columns([2.1, 1])
            with c1:
                if df_h.empty:
                    st.info(f"ℹ️ السعر اللحظي الحالي: **{selected_data['الإغلاق']} ج.م**")
                    st.link_button(f"🚀 افتح {selected_symbol} على TradingView ↗", selected_data["TradingView"], use_container_width=True)
                else:
                    sub_f = df_h.tail(120)
                    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.04, row_heights=[0.74, 0.26])
                    fig.add_trace(go.Candlestick(x=sub_f.index, open=sub_f["Open"], high=sub_f["High"], low=sub_f["Low"], close=sub_f["Close"], name="السعر"), row=1, col=1)
                    fig.add_trace(go.Scatter(x=sub_f.index, y=sub_f["EMA20"], line=dict(color="#A855F7", width=1.3), name="EMA 20"), row=1, col=1)
                    fig.add_trace(go.Scatter(x=sub_f.index, y=sub_f["EMA50"], line=dict(color="#38BDF8", width=1.6), name="EMA 50"), row=1, col=1)
                    fig.add_trace(go.Scatter(x=sub_f.index, y=sub_f["EMA200"], line=dict(color="#F59E0B", width=2.2), name="EMA 200"), row=1, col=1)
                    fig.add_hline(y=selected_data["الوقف (2xATR)"], line_dash="dash", line_color="#F87171", annotation_text="SL", row=1, col=1)
                    fig.add_hline(y=selected_data["TP1"], line_dash="dash", line_color="#4ADE80", annotation_text="TP1", row=1, col=1)
                    fig.add_trace(go.Bar(x=sub_f.index, y=sub_f["Volume"], marker_color=["#4ADE80" if c >= o else "#F87171" for c, o in zip(sub_f["Close"], sub_f["Open"])], name="الفوليوم"), row=2, col=1)
                    fig.update_layout(title=f"📈 الشارت الفني ومستويات التنفيذ: {selected_symbol} ({selected_data['اسم الشركة']})", height=520, xaxis_rangeslider_visible=False, template="plotly_white", paper_bgcolor="#FFFFFF", plot_bgcolor="#F8FAFC", margin=dict(l=10, r=10, t=40, b=10))
                    st.plotly_chart(fig, use_container_width=True)
            with c2:
                st.markdown(f"""
                <div class="pro-card">
                    <h4 class="txt-cyan" style="margin-top:0;">📌 خطة التنفيذ: {selected_symbol}</h4>
                    <p><span class="badge-bull">{selected_data['نوع الإشارة']}</span> &nbsp; <b>السكور: {selected_data['السكور']}/100</b></p>
                    <p class="txt-muted" style="font-size:13px;">{selected_data['التشخيص الفني']}</p>
                    <hr style="border-color:#26334D;">
                    <p class="txt-white"><b>الدخول المرجعي:</b> {selected_data['الإغلاق']} ج.م</p>
                    <p class="txt-white"><b>الوقف (2×ATR):</b> <span class="txt-red">{selected_data['الوقف (2xATR)']}</span></p>
                    <p class="txt-white"><b>TP1:</b> <span class="txt-green">{selected_data['TP1']}</span> | <b>TP2:</b> <span class="txt-green">{selected_data['TP2']}</span> | <b>TP3:</b> <span class="txt-green">{selected_data['TP3']}</span></p>
                    <p class="txt-white"><b>حجم الصفقة المقترح:</b> {selected_data['الأسهم']:,} سهم (صافي TP1: {selected_data['صافي TP1']:,.0f} ج.م)</p>
                </div>
                """, unsafe_allow_html=True)
                st.link_button("🚀 افتح على TradingView ↗", selected_data["TradingView"], use_container_width=True)

        # 8) التحليل المالي
        with t_fund:
            fund = fetch_fundamental_analysis(selected_data["Ticker"])
            if "error" in fund:
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
                        st.dataframe(dff, use_container_width=True, hide_index=True)
                    # تقويم الأرباح والكوبونات (V11.1)
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
                        st.dataframe(pd.DataFrame(cal_rows), use_container_width=True, hide_index=True)
                    else:
                        st.caption("ℹ️ لا توجد بيانات تقويم متاحة لهذا السهم.")

        # 9) التحليل الزمني
        with t_gann:
            df_t = fetch_single_stock_history(selected_data["Ticker"])
            if df_t.empty:
                st.info("ℹ️ البيانات التاريخية غير متوفرة لرسم خريطة جان.")
            else:
                r90 = df_t.tail(90)
                low_idx = r90["Low"].idxmin()
                g1, g2, g3 = st.columns(3)
                piv_d = g1.date_input("📅 تاريخ القاع/القمة الارتكازية:", value=low_idx.date())
                piv_p = g2.number_input("💲 سعر الارتكاز:", min_value=0.01, value=float(r90.loc[low_idx, "Low"]), step=0.05)
                is_low = g3.radio("نوع الارتكاز:", ["قاع صاعد", "قمة هابطة"], horizontal=True) == "قاع صاعد"

                sq9, g_times, aspects = compute_gann_and_planetary(piv_d, piv_p, is_low, selected_data["الإغلاق"], False)
                today_p = get_planetary_longitudes(get_cairo_now().replace(tzinfo=None))
                p_rows = [{"الجرم": k, "الدرجة": f"{v:.1f}°", "البرج": deg_to_zodiac(v), "خط السعر": convert_deg_to_price(v, selected_data["الإغلاق"])} for k, v in today_p.items()]

                gc1, gc2 = st.columns(2)
                with gc1:
                    st.markdown("##### 📐 مربع التسعة والدورات الزمنية لجان")
                    if g_times:
                        st.dataframe(pd.DataFrame(g_times), use_container_width=True, hide_index=True)
                    st.dataframe(pd.DataFrame(sq9), use_container_width=True, hide_index=True)
                with gc2:
                    st.markdown("##### 🪐 خطوط الكواكب والزوايا الفلكية القادمة")
                    st.dataframe(pd.DataFrame(p_rows), use_container_width=True, hide_index=True)
                    if aspects:
                        st.dataframe(pd.DataFrame(aspects), use_container_width=True, hide_index=True)

        # 10) الرادار الخبري
        with t_news:
            news_items = fetch_stock_news(selected_symbol)
            if not news_items:
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

# ==============================================================================
# التبويب 4: الإعدادات والربط السحابي والتليجرام
# ==============================================================================
with tab_settings:
    set_c1, set_c2 = st.columns(2)

    with set_c1:
        st.markdown("### ☁️ الربط السحابي الدائم (Supabase)")
        sb_url_in = st.text_input("🌐 Supabase URL:", value=st.session_state.get("sb_url_val", get_secret_safe("SUPABASE_URL")), placeholder="https://xxxx.supabase.co")
        st.session_state["sb_url_val"] = sb_url_in
        sb_key_in = st.text_input("🔐 Supabase Key:", value=st.session_state.get("sb_key_val", get_secret_safe("SUPABASE_KEY")), type="password", placeholder="eyJhbGci...")
        st.session_state["sb_key_val"] = sb_key_in

        sbtn1, sbtn2 = st.columns(2)
        with sbtn1:
            if st.button("🔌 فحص الاتصال واسترجاع المحفظة", use_container_width=True):
                ok_sb, msg_sb = test_supabase_connection()
                if ok_sb:
                    st.session_state["force_cloud_sync"] = True
                    st.success(msg_sb)
                    st.rerun()
                else:
                    st.error(msg_sb)
        with sbtn2:
            if st.button("⬆️ رفع الأسهم المحلية للسحابة", use_container_width=True):
                ok_up, msg_up = sync_full_portfolio_to_cloud(_load_local_portfolio_file() or my_portfolio)
                st.success(msg_up) if ok_up else st.error(msg_up)

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
            if st.button("🔍 جلب Chat ID تلقائياً", use_container_width=True):
                fid, fmsg = detect_telegram_chat_id(tg_t_in)
                if fid:
                    st.session_state["tg_chat_val"] = fid
                    st.rerun()
                else:
                    st.warning(fmsg)

        st.session_state["cfg_tg_port"] = st.checkbox("🔔 إرسال تنبيهات المحفظة تلقائياً", value=tg_auto_port)
        st.session_state["cfg_tg_whales"] = st.checkbox("🐋 تنبيه صفقات الحيتان (سكور 80+)", value=tg_auto_whales)
        if st.button("🧪 إرسال رسالة تجريبية لتليجرام", use_container_width=True):
            ok_t, msg_t = send_telegram_message(tg_t_in, tg_c_in, "🦅 <b>EGX Whale Hunter Pro V11.0</b>\n✅ النظام السحابي، الألوان الداكنة، وتحليل التدفق الأوتوماتيكي تعمل بنجاح!")
            st.success("✅ وصلت الرسالة لتليجرام!") if ok_t else st.error(f"❌ {msg_t}")

    with set_c2:
        st.markdown("### 🎛️ إعدادات السكانر وإدارة رأس المال")
        scope_choice = st.radio(
            "🌐 نطاق أسهم الرادار:",
            ["كل أسهم البورصة المصرية", "الأسهم القيادية والنشطة فقط"],
            index=(1 if only_leaders else 0)
        )
        st.session_state["cfg_only_leaders"] = ("القيادية" in scope_choice)
        st.session_state["cfg_capital"] = st.number_input("💰 رأس المال للمقترحات (ج.م):", min_value=5000, value=capital, step=5000)
        st.session_state["cfg_risk_pct"] = st.slider("🛡️ نسبة المخاطرة في الصفقة الواحدة (%):", 0.5, 5.0, risk_pct, 0.25)
        st.session_state["cfg_min_turnover"] = st.number_input("💧 الحد الأدنى للسيولة اليومية (مليون ج.م):", 0.0, 100.0, min_turnover_m, 0.25)
        fee_choice = st.radio("💳 شريحة عمولة Thndr:", ["أول 50 صفقة بالشهر (~0.16%)", "أكثر من 50 صفقة (~0.37%)"], index=(0 if fee_rate == 0.0016 else 1))
        st.session_state["cfg_fee_tier"] = "0.16%" if "0.16%" in fee_choice else "0.37%"
        st.session_state["cfg_min_score"] = st.slider("🎯 الحد الأدنى للسكور في جدول الرادار:", 0, 100, min_score, 5)
        st.session_state["cfg_alert_buf"] = st.slider("🔔 حساسية تنبيه قرب الوقف/الهدف (%):", 0.5, 8.0, alert_buffer_pct, 0.5)

# ===== واجهة إدارة قائمة المراقبة (Watchlist UI) =====
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
        if st.button("add", key="wl_add_btn", use_container_width=True):
            if wl_sym and wl_tgt > 0:
                wl = list(st.session_state.get("watchlist", []))
                wl.append({"symbol": wl_sym, "direction": "above" if "above" in wl_dir else "below", "target": float(wl_tgt)})
                _save_watchlist(wl)
                st.success("تمت الإضافة.")
                st.rerun()
    wl_df = pd.DataFrame(st.session_state.get("watchlist", []))
    if not wl_df.empty:
        st.dataframe(wl_df, use_container_width=True, hide_index=True)
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
