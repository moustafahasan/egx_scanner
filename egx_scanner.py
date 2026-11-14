import os
import re
import math
import json

# ==========================================
# فرض الثيم الداكن والخط الأبيض على Streamlit تلقائياً
# ==========================================
os.makedirs(".streamlit", exist_ok=True)
_config_file = os.path.join(".streamlit", "config.toml")
if not os.path.exists(_config_file):
    with open(_config_file, "w", encoding="utf-8") as _f:
        _f.write(
            '[theme]\n'
            'base="dark"\n'
            'primaryColor="#38BDF8"\n'
            'backgroundColor="#0B0F19"\n'
            'secondaryBackgroundColor="#111827"\n'
            'textColor="#FFFFFF"\n'
        )

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta, date

# ==========================================
# إعدادات الصفحة والتصميم البصري عالي التباين
# ==========================================
st.set_page_config(
    page_title="EGX Whale Hunter Pro V7.1",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    .stApp, [data-testid="stAppViewContainer"] {
        background-color: #0B0F19 !important;
        color: #FFFFFF !important;
    }
    [data-testid="stHeader"] {
        background-color: #0B0F19 !important;
    }
    [data-testid="stSidebar"], [data-testid="stSidebar"] > div:first-child {
        background-color: #111827 !important;
        border-left: 1px solid #1E293B !important;
    }

    [data-testid="stMarkdownContainer"] p,
    [data-testid="stMarkdownContainer"] li,
    [data-testid="stMarkdownContainer"] h1,
    [data-testid="stMarkdownContainer"] h2,
    [data-testid="stMarkdownContainer"] h3,
    [data-testid="stMarkdownContainer"] h4,
    [data-testid="stWidgetLabel"] p,
    [data-testid="stWidgetLabel"] label,
    [data-testid="stWidgetLabel"] span,
    [data-testid="stCaptionContainer"] p,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    button[data-baseweb="tab"] p,
    button[data-baseweb="tab"] div {
        color: #FFFFFF !important;
    }

    [data-baseweb="input"], [data-baseweb="base-input"], [data-baseweb="select"] > div {
        background-color: #1E293B !important;
        color: #FFFFFF !important;
        border: 1px solid #334155 !important;
        border-radius: 8px !important;
    }
    input {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
    }

    .hero-banner {
        direction: rtl;
        text-align: right;
        background: linear-gradient(135deg, #0F172A 0%, #1E1B4B 50%, #0F172A 100%);
        padding: 18px 22px;
        border-radius: 14px;
        border: 1px solid rgba(56, 189, 248, 0.4);
        box-shadow: 0 0 25px rgba(56, 189, 248, 0.15);
        margin-bottom: 14px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 10px;
    }
    .hero-title {
        font-size: 24px;
        font-weight: 900;
        color: #FFFFFF !important;
        margin: 0;
    }
    .hero-accent { color: #38BDF8 !important; }
    .hero-sub { font-size: 13px; color: #E2E8F0 !important; margin-top: 4px; }
    .session-pill {
        background-color: rgba(15, 23, 42, 0.85);
        border: 1px solid #38BDF8;
        padding: 6px 14px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: bold;
        color: #FFFFFF !important;
    }

    .kpi-card {
        direction: rtl;
        text-align: center;
        background: linear-gradient(180deg, #161E31 0%, #0F172A 100%);
        padding: 12px 10px;
        border-radius: 12px;
        border: 1px solid #1E293B;
        border-top: 3px solid #38BDF8;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.35);
    }
    .kpi-label { color: #CBD5E1 !important; font-size: 12px; margin-bottom: 4px; }
    .kpi-val { color: #FFFFFF !important; font-size: 19px; font-weight: 800; }

    .alert-box-danger {
        direction: rtl;
        text-align: right;
        background: rgba(239, 68, 68, 0.22);
        border: 1px solid #EF4444;
        border-right: 6px solid #EF4444;
        padding: 12px 16px;
        border-radius: 10px;
        margin-bottom: 8px;
        color: #FFFFFF !important;
    }
    .alert-box-warn {
        direction: rtl;
        text-align: right;
        background: rgba(245, 158, 11, 0.22);
        border: 1px solid #F59E0B;
        border-right: 6px solid #F59E0B;
        padding: 12px 16px;
        border-radius: 10px;
        margin-bottom: 8px;
        color: #FFFFFF !important;
    }
    .alert-box-success {
        direction: rtl;
        text-align: right;
        background: rgba(34, 197, 94, 0.22);
        border: 1px solid #22C55E;
        border-right: 6px solid #22C55E;
        padding: 12px 16px;
        border-radius: 10px;
        margin-bottom: 8px;
        color: #FFFFFF !important;
    }

    .top-card {
        direction: rtl;
        text-align: right;
        background: linear-gradient(145deg, #131C31 0%, #0F172A 100%);
        padding: 16px;
        border-radius: 12px;
        border: 1px solid rgba(56, 189, 248, 0.35);
        box-shadow: 0 6px 18px rgba(0, 0, 0, 0.4);
        margin-bottom: 10px;
    }
    .top-card-gold {
        border: 1px solid rgba(250, 204, 21, 0.6);
        box-shadow: 0 0 20px rgba(250, 204, 21, 0.12);
    }

    .pro-card {
        direction: rtl;
        text-align: right;
        background-color: #131C31;
        padding: 18px;
        border-radius: 12px;
        border: 1px solid #26334D;
        border-right: 5px solid #38BDF8;
        margin-bottom: 12px;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.35);
    }

    .badge-bull {
        background-color: rgba(34, 197, 94, 0.2);
        color: #4ADE80 !important;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: bold;
        border: 1px solid rgba(74, 222, 128, 0.5);
    }
    .badge-warn {
        background-color: rgba(250, 204, 21, 0.2);
        color: #FACC15 !important;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: bold;
        border: 1px solid rgba(250, 204, 21, 0.5);
    }
    .badge-bear {
        background-color: rgba(248, 113, 113, 0.2);
        color: #F87171 !important;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: bold;
        border: 1px solid rgba(248, 113, 113, 0.5);
    }
    .txt-white { color: #FFFFFF !important; }
    .txt-cyan  { color: #38BDF8 !important; }
    .txt-green { color: #4ADE80 !important; }
    .txt-red   { color: #F87171 !important; }
    .txt-gold  { color: #FACC15 !important; }
    .txt-muted { color: #CBD5E1 !important; }

    .news-item {
        direction: rtl;
        text-align: right;
        background-color: #131C31;
        padding: 14px 16px;
        border-radius: 10px;
        border: 1px solid #26334D;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# محرك إرسال تنبيهات التليجرام ومنع التكرار
# ==========================================
TG_LOG_FILE = "tg_alerts_log.json"

def get_secret_safe(key_name: str) -> str:
    try:
        return str(st.secrets.get(key_name, "")).strip()
    except Exception:
        return ""

def load_sent_tg_log() -> dict:
    if "sent_tg_alerts" in st.session_state:
        return st.session_state["sent_tg_alerts"]
    if os.path.exists(TG_LOG_FILE):
        try:
            with open(TG_LOG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    st.session_state["sent_tg_alerts"] = data
                    return data
        except Exception:
            pass
    st.session_state["sent_tg_alerts"] = {}
    return {}

def save_sent_tg_log(log_dict: dict):
    st.session_state["sent_tg_alerts"] = log_dict
    try:
        with open(TG_LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(log_dict, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def send_telegram_message(bot_token: str, chat_id: str, html_text: str) -> tuple:
    if not bot_token or not chat_id:
        return False, "بيانات البوت غير مكتملة"
    try:
        url = f"https://api.telegram.org/bot{bot_token.strip()}/sendMessage"
        payload = json.dumps({
            "chat_id": str(chat_id).strip(),
            "text": html_text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            if res.get("ok"):
                return True, "تم الإرسال بنجاح"
            return False, res.get("description", "خطأ من تليجرام")
    except Exception as e:
        return False, str(e)

def detect_telegram_chat_id(bot_token: str) -> tuple:
    if not bot_token:
        return None, "أدخل Bot Token أولاً"
    try:
        url = f"https://api.telegram.org/bot{bot_token.strip()}/getUpdates"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            updates = res.get("result", [])
            for upd in reversed(updates):
                msg = upd.get("message") or upd.get("channel_post") or {}
                chat = msg.get("chat", {})
                if chat.get("id"):
                    return str(chat["id"]), "تم العثور على Chat ID بنجاح!"
            return None, "لم تصل رسائل للبوت بعد. افتح البوت في تليجرام واضغط Start ثم حاول مرة أخرى."
    except Exception as e:
        return None, f"تعذر الاتصال بتليجرام: {e}"

# ==========================================
# إدارة حفظ وتحميل المحفظة الشخصية
# ==========================================
PORTFOLIO_FILE = "my_egx_portfolio.json"

def load_portfolio() -> list:
    if "my_portfolio" in st.session_state:
        return st.session_state["my_portfolio"]
    if os.path.exists(PORTFOLIO_FILE):
        try:
            with open(PORTFOLIO_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    st.session_state["my_portfolio"] = data
                    return data
        except Exception:
            pass
    st.session_state["my_portfolio"] = []
    return []

def save_portfolio(portfolio_list: list):
    st.session_state["my_portfolio"] = portfolio_list
    try:
        with open(PORTFOLIO_FILE, "w", encoding="utf-8") as f:
            json.dump(portfolio_list, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

# ==========================================
# دالة تحديد حالة جلسة البورصة المصرية بتوقيت القاهرة
# ==========================================
def get_egx_session_status() -> str:
    cairo_tz = timezone(timedelta(hours=2))
    now_cairo = datetime.now(cairo_tz)
    weekday = now_cairo.weekday()
    is_trading_day = weekday in [6, 0, 1, 2, 3]
    current_minutes = now_cairo.hour * 60 + now_cairo.minute
    if is_trading_day and (10 * 60 <= current_minutes <= 14 * 60 + 30):
        return f"🟢 الجلسة مفتوحة الآن ({now_cairo.strftime('%H:%M')} القاهرة)"
    return f"🌙 الجلسة مغلقة ({now_cairo.strftime('%H:%M')} القاهرة)"

# ==========================================
# محرك جلب كل أسهم البورصة المصرية ديناميكياً + أسعار بديلة
# ==========================================
LEADERS_EGX_TICKERS = [
    "COMI.CA", "TMGH.CA", "SWDY.CA", "ETEL.CA", "EFIH.CA", "FWRY.CA",
    "HRHO.CA", "ABUK.CA", "ORAS.CA", "EAST.CA", "ESRS.CA", "EKHO.CA",
    "HELI.CA", "PHDC.CA", "ORWE.CA", "CLHO.CA", "ISPH.CA", "JUFO.CA",
    "OBRI.CA", "DSCW.CA", "ECAP.CA", "ATLC.CA", "AMOC.CA", "SKPC.CA",
    "MFPC.CA", "ADIB.CA", "CIEB.CA", "FAIT.CA", "EMFD.CA", "OCDI.CA",
    "EGAL.CA", "GBCO.CA", "MCQE.CA", "ARCC.CA", "CIRA.CA", "RMDA.CA",
    "ZMID.CA", "ELSH.CA", "MTIE.CA", "RAYA.CA", "BTFH.CA", "ASPI.CA",
    "TAQA.CA", "VLMR.CA", "PHAR.CA", "ALCN.CA", "CSAG.CA", "EGTS.CA",
    "MASR.CA", "EFID.CA", "ORHD.CA", "BINV.CA", "CCAP.CA", "HDBK.CA",
    "BONY.CA"
]

FALLBACK_EGX_TICKERS = sorted(list(set(LEADERS_EGX_TICKERS + [
    "ACAMD.CA", "ACAP.CA", "ACGC.CA", "ACRO.CA", "ACTF.CA", "ADCI.CA",
    "ADPC.CA", "ADRI.CA", "AFDI.CA", "AFMC.CA", "AIFI.CA", "AIH.CA",
    "AJWA.CA", "ALUM.CA", "AMER.CA", "AMIA.CA", "AMPI.CA", "ANFI.CA",
    "APSW.CA", "ARAB.CA", "AREH.CA", "ARPI.CA", "ARVA.CA", "ASCM.CA",
    "ATQA.CA", "AXPH.CA", "BCAP.CA", "BIGP.CA", "BIOC.CA", "BLOM.CA",
    "BONY.CA", "CAED.CA", "CANA.CA", "CCRS.CA", "CEFM.CA", "CERA.CA",
    "CFGH.CA", "CICH.CA", "CNFN.CA", "COPR.CA", "COSG.CA", "CRST.CA",
    "DAPH.CA", "DCRC.CA", "DEVP.CA", "DICC.CA", "DOMT.CA", "DYST.CA",
    "EALR.CA", "EBSC.CA", "EDBM.CA", "EEII.CA", "EFIC.CA", "EGAS.CA",
    "EGBE.CA", "EGCH.CA", "EGSA.CA", "EHDR.CA", "EIUD.CA", "EKHOA.CA",
    "ELKA.CA", "ELNA.CA", "ELWA.CA", "ENGC.CA", "EPCO.CA", "EPPK.CA",
    "ESGI.CA", "ETRS.CA", "EXPA.CA", "FAITA.CA", "GADW.CA", "GDWA.CA",
    "GGCC.CA", "GIHD.CA", "GMCI.CA", "GOCO.CA", "GRCA.CA", "GSSC.CA",
    "GTWL.CA", "IBCT.CA", "ICFC.CA", "ICID.CA", "ICMI.CA", "IDRE.CA",
    "IFAP.CA", "INFI.CA", "IRON.CA", "ISMQ.CA", "ITSY.CA", "KABO.CA",
    "KWIN.CA", "KZPC.CA", "LCSW.CA", "MAAL.CA", "MBSC.CA", "MCRO.CA",
    "MEPA.CA", "MENA.CA", "MFSC.CA", "MHOT.CA", "MICH.CA", "MILA.CA",
    "MIPH.CA", "MKIT.CA", "MMAT.CA", "MOED.CA", "MOIL.CA", "MOIN.CA",
    "MOSC.CA", "MPCI.CA", "MPCO.CA", "MRCO.CA", "NAHO.CA", "NAPR.CA",
    "NCCW.CA", "NDRL.CA", "NHPS.CA", "NINH.CA", "NIPH.CA", "NOAF.CA",
    "NRPD.CA", "OCPH.CA", "ODID.CA", "OFH.CA", "OIH.CA", "OLFI.CA",
    "PACH.CA", "POUL.CA", "PRCL.CA", "PRDC.CA", "PRMH.CA", "PTCC.CA",
    "QNBA.CA", "RAKT.CA", "REAC.CA", "RIVA.CA", "ROTO.CA", "RREI.CA",
    "RTVC.CA", "RUBX.CA", "SAIB.CA", "SAUD.CA", "SCEM.CA", "SCFM.CA",
    "SDTI.CA", "SEIG.CA", "SIPC.CA", "SMFR.CA", "SNFC.CA", "SPHT.CA",
    "SPIN.CA", "SPMD.CA", "SUCE.CA", "SUGR.CA", "SVCE.CA", "TANM.CA",
    "TRTO.CA", "UASG.CA", "UEFM.CA", "UEGC.CA", "UNBE.CA", "UNIP.CA",
    "UNIT.CA", "UPMS.CA", "UTOP.CA", "VALU.CA", "VERT.CA", "VLMRA.CA",
    "WCDF.CA", "WKOL.CA", "ZEOT.CA"
])))

@st.cache_data(ttl=43200, show_spinner=False)
def fetch_dynamic_egx_universe() -> tuple:
    dynamic_symbols = set()
    names_map = {"BONY": "Bonyan for Development and Trade"}
    source_status = "قاعدة احتياطية"

    try:
        url = "https://scanner.tradingview.com/egypt/scan"
        payload = json.dumps({
            "filter": [{"left": "type", "operation": "in_range", "right": ["stock", "dr", "fund"]}],
            "options": {"lang": "en"},
            "markets": ["egypt"],
            "symbols": {"query": {"types": []}, "tickers": []},
            "columns": ["name", "description"],
            "sort": {"sortBy": "name", "sortOrder": "asc"},
            "range": [0, 500]
        }).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            res_json = json.loads(resp.read().decode("utf-8"))
            for row in res_json.get("data", []):
                full_s = row.get("s", "")
                if ":" in full_s:
                    sym = full_s.split(":")[1].strip().upper()
                    if re.match(r"^[A-Z0-9]{2,12}$", sym):
                        ca_sym = f"{sym}.CA"
                        dynamic_symbols.add(ca_sym)
                        d_vals = row.get("d", [])
                        if len(d_vals) > 1 and d_vals[1]:
                            names_map[sym] = str(d_vals[1])
        if len(dynamic_symbols) >= 150:
            source_status = f"مباشر وديناميكي ({len(dynamic_symbols)} سهم من السوق)"
    except Exception:
        pass

    if len(dynamic_symbols) < 150:
        try:
            req2 = urllib.request.Request(
                "https://stockanalysis.com/list/egyptian-exchange/",
                headers={"User-Agent": "Mozilla/5.0"}
            )
            with urllib.request.urlopen(req2, timeout=8) as resp2:
                html_txt = resp2.read().decode("utf-8", errors="ignore")
                found_syms = re.findall(r"/quote/egx/([A-Za-z0-9]+)/", html_txt)
                for s in found_syms:
                    sym = s.strip().upper()
                    if re.match(r"^[A-Z0-9]{2,12}$", sym):
                        dynamic_symbols.add(f"{sym}.CA")
            if len(dynamic_symbols) >= 150:
                source_status = f"مباشر وديناميكي ({len(dynamic_symbols)} سهم من السوق)"
        except Exception:
            pass

    merged_list = sorted(list(dynamic_symbols.union(set(FALLBACK_EGX_TICKERS))))
    return merged_list, names_map, source_status

@st.cache_data(ttl=600, show_spinner=False)
def fetch_tv_fallback_quotes(clean_symbols: tuple) -> dict:
    """جلب السعر اللحظي والـ ATR من TradingView للأسهم حديثة الإدراج غير المتوفرة على Yahoo Finance"""
    quotes = {}
    if not clean_symbols:
        return quotes
    try:
        url = "https://scanner.tradingview.com/egypt/scan"
        payload = json.dumps({
            "symbols": {
                "tickers": [f"EGX:{s.upper().replace('.CA', '')}" for s in clean_symbols],
                "query": {"types": []}
            },
            "columns": ["name", "close", "change", "volume", "ATR"]
        }).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            res_json = json.loads(resp.read().decode("utf-8"))
            for row in res_json.get("data", []):
                full_s = row.get("s", "")
                d = row.get("d", [])
                if ":" in full_s and len(d) >= 2 and d[1] is not None:
                    sym = full_s.split(":")[1].strip().upper()
                    close_val = float(d[1])
                    chg_val = float(d[2]) if len(d) > 2 and d[2] is not None else 0.0
                    vol_val = float(d[3]) if len(d) > 3 and d[3] is not None else 0.0
                    atr_val = float(d[4]) if len(d) > 4 and d[4] is not None and d[4] > 0 else (close_val * 0.025)
                    quotes[sym] = {
                        "close": close_val,
                        "change": chg_val,
                        "volume": vol_val,
                        "atr": atr_val
                    }
    except Exception:
        pass
    return quotes

# ==========================================
# محرك الحسابات الفلكية ومعادلات جان
# ==========================================
ZODIAC_SIGNS_AR = [
    "♈ الحمل", "♉ الثور", "♊ الجوزاء", "♋ السرطان",
    "♌ الأسد", "♍ العذراء", "♎ الميزان", "♏ العقرب",
    "♐ القوس", "♑ الجدي", "♒ الدلو", "♓ الحوت"
]

ORBITAL_ELEMENTS = {
    "Mercury": (0.38709927, 0.00000037, 0.20563593, 0.00001906, 7.00497902, -0.00594749, 252.25032350, 149472.67411175, 77.45779628, 0.16047689, 48.33076593, -0.12534081),
    "Venus":   (0.72333566, 0.00000390, 0.00677672, -0.00004107, 3.39467605, -0.00078890, 181.97909950, 58517.81538729, 131.60246718, 0.00268329, 76.67984255, -0.27769418),
    "Earth":   (1.00000261, 0.00000562, 0.01671123, -0.00004392, -0.00001531, -0.01294668, 100.46457166, 35999.37244981, 102.93768193, 0.32327364, 0.0, 0.0),
    "Mars":    (1.52371034, 0.00001847, 0.09339410, 0.00007882, 1.84969142, -0.00813131, -4.55343205, 19140.30268499, -23.94362959, 0.44441088, 49.55953891, -0.29257343),
    "Jupiter": (5.20288700, -0.00011607, 0.04838624, -0.00013253, 1.30439695, -0.00183714, 34.39644051, 3034.74612775, 14.72847983, 0.21252668, 100.47390909, 0.20469106),
    "Saturn":  (9.53667594, -0.00125060, 0.05386179, -0.00050991, 2.48599187, 0.00193609, 49.95424423, 1222.49362201, 92.59887831, -0.41897216, 113.66242448, -0.28867794),
}

def _julian_centuries(dt: datetime) -> float:
    jd = dt.toordinal() + 1721424.5 + (dt.hour + dt.minute / 60.0) / 24.0
    return (jd - 2451545.0) / 36525.0

def _heliocentric_xyz(planet_name: str, T: float) -> tuple:
    a0, da, e0, de, I0, dI, L0, dL, w0, dw, O0, dO = ORBITAL_ELEMENTS[planet_name]
    a = a0 + da * T
    e = e0 + de * T
    I = math.radians(I0 + dI * T)
    L = (L0 + dL * T) % 360.0
    w_bar = (w0 + dw * T) % 360.0
    O = math.radians((O0 + dO * T) % 360.0)
    w = math.radians((w_bar - math.degrees(O)) % 360.0)
    M = math.radians((L - w_bar) % 360.0)

    E = M + e * math.sin(M)
    for _ in range(6):
        dE = (E - e * math.sin(E) - M) / (1.0 - e * math.cos(E))
        E -= dE

    x_p = a * (math.cos(E) - e)
    y_p = a * math.sqrt(max(0.0, 1.0 - e * e)) * math.sin(E)

    cos_O, sin_O = math.cos(O), math.sin(O)
    cos_w, sin_w = math.cos(w), math.sin(w)
    cos_I, sin_I = math.cos(I), math.sin(I)

    x = (cos_O * cos_w - sin_O * sin_w * cos_I) * x_p + (-cos_O * sin_w - sin_O * cos_w * cos_I) * y_p
    y = (sin_O * cos_w + cos_O * sin_w * cos_I) * x_p + (-sin_O * sin_w + cos_O * cos_w * cos_I) * y_p
    z = (sin_w * sin_I) * x_p + (cos_w * sin_I) * y_p
    return x, y, z

def get_planetary_longitudes(dt: datetime) -> dict:
    T = _julian_centuries(dt)
    xe, ye, ze = _heliocentric_xyz("Earth", T)
    sun_lon = math.degrees(math.atan2(-ye, -xe)) % 360.0

    Lp = (218.3164477 + 481267.88123421 * T) % 360.0
    D = math.radians((297.8501921 + 445267.1114034 * T) % 360.0)
    M = math.radians((357.5291092 + 35999.0502909 * T) % 360.0)
    Mp = math.radians((134.9633964 + 477198.8675055 * T) % 360.0)
    F = math.radians((93.2720950 + 483202.0175233 * T) % 360.0)
    moon_lon = (
        Lp
        + 6.289 * math.sin(Mp)
        + 1.274 * math.sin(2 * D - Mp)
        + 0.658 * math.sin(2 * D)
        + 0.214 * math.sin(2 * Mp)
        - 0.186 * math.sin(M)
        - 0.114 * math.sin(2 * F)
    ) % 360.0

    positions = {"☀️ الشمس": sun_lon, "🌙 القمر": moon_lon}
    ar_names = {
        "Mercury": "☿ عطارد", "Venus": "♀ الزهرة",
        "Mars": "♂ المريخ", "Jupiter": "♃ المشتري", "Saturn": "♄ زحل",
    }
    for p_en, p_ar in ar_names.items():
        xp, yp, zp = _heliocentric_xyz(p_en, T)
        geo_lon = math.degrees(math.atan2(yp - ye, xp - xe)) % 360.0
        positions[p_ar] = geo_lon
    return positions

def deg_to_zodiac(deg: float) -> str:
    idx = int(deg // 30) % 12
    deg_in_sign = deg % 30
    return f"{ZODIAC_SIGNS_AR[idx]} ({deg_in_sign:.1f}°)"

def convert_deg_to_price(deg: float, ref_price: float) -> float:
    if ref_price <= 0:
        return round(deg, 2)
    scale = 1.0
    while (360.0 / scale) > ref_price * 2.2:
        scale *= 10.0
    while (360.0 / scale) < ref_price * 0.25:
        scale /= 10.0
    step = 360.0 / scale
    base_val = deg / scale
    n = round((ref_price - base_val) / step)
    price_lvl = base_val + n * step
    if price_lvl <= 0:
        price_lvl += step
    return round(price_lvl, 2)

def add_egx_trading_days(start_dt: date, trading_days: int) -> date:
    curr = start_dt
    added = 0
    while added < trading_days:
        curr += timedelta(days=1)
        if curr.weekday() in [6, 0, 1, 2, 3]:
            added += 1
    return curr

def compute_gann_and_planetary(pivot_date: date, pivot_price: float, is_pivot_low: bool, current_price: float, use_trading_days: bool):
    sqrt_p = math.sqrt(max(0.01, pivot_price))
    angles = [45, 90, 135, 180, 270, 360]

    sq9_prices = []
    for ang in angles:
        step = ang / 180.0
        if is_pivot_low:
            target_p = (sqrt_p + step) ** 2
            direction = "مقاومة هندسية ⬆️"
        else:
            target_p = (max(0.1, sqrt_p - step)) ** 2
            direction = "دعم هندسي ⬇️"
        sq9_prices.append({
            "الزاوية": f"{ang}°",
            "المستوى السعري": round(target_p, 2),
            "النوع": direction,
            "البعد عن السعر الحالي %": round(((target_p - current_price) / current_price) * 100, 1)
        })

    price_time_sq = max(15, int(round(sqrt_p * 10)))
    classic_cycles = sorted(list(set([45, 60, 90, 120, 144, 180, 270, 360, price_time_sq])))
    today = datetime.now().date()

    time_targets = []
    for cyc in classic_cycles:
        target_dt = add_egx_trading_days(pivot_date, cyc) if use_trading_days else (pivot_date + timedelta(days=cyc))
        diff_days = (target_dt - today).days
        if -15 <= diff_days <= 120:
            label = f"تربيع السعر ({cyc})" if cyc == price_time_sq else f"دورة جان ({cyc})"
            status = "🔥 نافذة انعكاس نشطة الآن!" if abs(diff_days) <= 3 else (f"بعد {diff_days} يوم" if diff_days > 0 else f"مضى منذ {abs(diff_days)} يوم")
            time_targets.append({
                "الدورة / المعادلة": label,
                "العدد": cyc,
                "تاريخ الانعكاس المتوقع": target_dt,
                "الحالة الزمنية": status,
                "diff": diff_days
            })

    aspect_defs = [
        (0, "اقتران ☌ (0°)", 1.5),
        (60, "تسديس ⚹ (60°)", 1.2),
        (90, "تربيع □ (90°)", 1.5),
        (120, "تثليث △ (120°)", 1.5),
        (180, "تقابل ☍ (180°)", 1.5),
    ]
    key_pairs = [
        ("☀️ الشمس", "🌙 القمر"), ("☀️ الشمس", "♂ المريخ"),
        ("☀️ الشمس", "♃ المشتري"), ("☀️ الشمس", "♄ زحل"),
        ("☿ عطارد", "♀ الزهرة"), ("♂ المريخ", "♃ المشتري"),
        ("♂ المريخ", "♄ زحل"), ("♃ المشتري", "♄ زحل"),
    ]

    upcoming_aspects = []
    seen_pairs = set()
    for d_offset in range(0, 31):
        check_dt = datetime.combine(today + timedelta(days=d_offset), datetime.min.time()) + timedelta(hours=12)
        pos = get_planetary_longitudes(check_dt)
        for p1, p2 in key_pairs:
            diff_deg = abs(pos[p1] - pos[p2]) % 360.0
            if diff_deg > 180.0:
                diff_deg = 360.0 - diff_deg
            for target_ang, asp_name, orb in aspect_defs:
                if abs(diff_deg - target_ang) <= orb:
                    pair_key = f"{p1}-{p2}-{target_ang}"
                    if pair_key not in seen_pairs:
                        seen_pairs.add(pair_key)
                        if p1 == "☀️ الشمس" and p2 == "🌙 القمر" and target_ang == 0:
                            asp_label = "🌑 محاق (New Moon)"
                        elif p1 == "☀️ الشمس" and p2 == "🌙 القمر" and target_ang == 180:
                            asp_label = "🌕 بدر مكتمل (Full Moon)"
                        else:
                            asp_label = asp_name
                        upcoming_aspects.append({
                            "التاريخ": (today + timedelta(days=d_offset)),
                            "الكوكبان": f"{p1} × {p2}",
                            "الزاوية الفلكية": asp_label,
                            "متبقي": "اليوم 🔴" if d_offset == 0 else f"بعد {d_offset} يوم"
                        })

    return sq9_prices, time_targets, upcoming_aspects

# ==========================================
# 1. محرك جلب البيانات التاريخية
# ==========================================
@st.cache_data(ttl=900, show_spinner=False)
def fetch_all_market_data(tickers: tuple) -> dict:
    data_map = {}
    tickers_list = list(tickers)
    batch_size = 65

    for i in range(0, len(tickers_list), batch_size):
        batch = tickers_list[i:i + batch_size]
        try:
            raw = yf.download(
                batch,
                period="2y",
                interval="1d",
                group_by="ticker",
                threads=True,
                progress=False,
                auto_adjust=True
            )
            if raw is None or raw.empty:
                continue

            if len(batch) == 1:
                t = batch[0]
                df_t = raw.copy()
                if isinstance(df_t.columns, pd.MultiIndex):
                    df_t.columns = df_t.columns.get_level_values(0)
                df_t = df_t.dropna(subset=["Close", "High", "Low", "Open", "Volume"])
                if not df_t.empty:
                    data_map[t] = df_t
            else:
                lvl0 = raw.columns.get_level_values(0)
                for t in batch:
                    if t in lvl0:
                        df_t = raw[t].copy()
                        df_t = df_t.dropna(subset=["Close", "High", "Low", "Open", "Volume"])
                        if not df_t.empty:
                            data_map[t] = df_t
        except Exception:
            continue

    return data_map

# ==========================================
# 2. المحرك الفني المتقدم (Wyckoff + SMC + RS)
# ==========================================
def compute_advanced_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["EMA20"] = df["Close"].ewm(span=20, adjust=False).mean()
    df["EMA50"] = df["Close"].ewm(span=50, adjust=False).mean()
    df["EMA200"] = df["Close"].ewm(span=200, adjust=False).mean()

    prev_close = df["Close"].shift(1)
    tr = pd.concat([
        df["High"] - df["Low"],
        (df["High"] - prev_close).abs(),
        (df["Low"] - prev_close).abs()
    ], axis=1).max(axis=1