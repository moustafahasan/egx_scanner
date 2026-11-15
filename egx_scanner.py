import os
import re
import math
import json
from zoneinfo import ZoneInfo

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
    page_title="EGX Whale Hunter Pro V7.3",
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
# التوقيت المحلي للقاهرة
# ==========================================
def get_cairo_now() -> datetime:
    try:
        return datetime.now(ZoneInfo("Africa/Cairo"))
    except Exception:
        return datetime.now(timezone(timedelta(hours=2)))

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
    now_cairo = get_cairo_now()
    weekday = now_cairo.weekday()
    is_trading_day = weekday in [6, 0, 1, 2, 3]
    current_minutes = now_cairo.hour * 60 + now_cairo.minute
    if is_trading_day and (10 * 60 <= current_minutes <= 14 * 60 + 30):
        return f"🟢 الجلسة مفتوحة الآن ({now_cairo.strftime('%H:%M')} القاهرة)"
    return f"🌙 الجلسة مغلقة ({now_cairo.strftime('%H:%M')} القاهرة)"

# ==========================================
# محرك جلب كل أسهم البورصة المصرية ديناميكياً + أسعار TradingView اللحظية
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

@st.cache_data(ttl=60, show_spinner=False)
def fetch_tv_live_quotes(clean_symbols: tuple) -> tuple:
    """جلب الأسعار اللحظية لجميع الأسهم من TradingView كل 60 ثانية"""
    quotes = {}
    fetched_time = get_cairo_now().strftime("%H:%M:%S")
    if not clean_symbols:
        return quotes, fetched_time
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
    return quotes, fetched_time

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
    today = get_cairo_now().date()

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
    ], axis=1).max(axis=1)
    df["ATR14"] = tr.ewm(alpha=1/14, adjust=False).mean()

    sma20 = df["Close"].rolling(20).mean()
    std20 = df["Close"].rolling(20).std()
    df["BB_Upper"] = sma20 + 2 * std20
    df["BB_Lower"] = sma20 - 2 * std20
    df["BB_Width"] = (df["BB_Upper"] - df["BB_Lower"]) / sma20
    df["BB_Width_Pct"] = df["BB_Width"].rolling(120).rank(pct=True)

    df["VolSMA20"] = df["Volume"].rolling(20).mean()
    df["High20_Prev"] = df["High"].rolling(20).max().shift(1)
    df["Low20_Prev"] = df["Low"].rolling(20).min().shift(1)
    df["Pct_Change"] = df["Close"].pct_change()
    df["Turnover"] = df["Close"] * df["Volume"]

    df["Bull_FVG"] = (df["Low"] > df["High"].shift(2)) & ((df["Close"].shift(1) - df["Open"].shift(1)) > 1.1 * df["ATR14"].shift(1))
    return df

def analyze_stock_pro(ticker: str, df: pd.DataFrame, market_median_ret20: float, min_turnover: float, capital: float, risk_pct: float, fee_rate: float, force_include: bool = False) -> dict:
    min_bars = 1 if force_include else 205
    if len(df) < min_bars:
        return None

    df = compute_advanced_indicators(df)
    last = df.iloc[-1]
    prev = df.iloc[-2] if len(df) >= 2 else last

    close = float(last["Close"])
    open_p = float(last["Open"])
    high = float(last["High"])
    low = float(last["Low"])
    vol = float(last["Volume"])
    ema50 = float(last["EMA50"])
    ema200 = float(last["EMA200"])
    ema200_10d = float(df["EMA200"].iloc[-11]) if len(df) >= 12 else ema200
    atr14 = float(last["ATR14"]) if pd.notna(last["ATR14"]) and last["ATR14"] > 0 else close * 0.025
    vol_sma20 = float(last["VolSMA20"]) if pd.notna(last["VolSMA20"]) and last["VolSMA20"] > 0 else max(1.0, vol)
    high20_prev = float(last["High20_Prev"]) if pd.notna(last["High20_Prev"]) else high
    pct_change = float(last["Pct_Change"]) if pd.notna(last["Pct_Change"]) else 0.0

    avg_turnover = float(df["Turnover"].tail(20).mean())
    if not force_include and avg_turnover < min_turnover:
        return None

    max_abs_move_60d = df["Pct_Change"].tail(60).abs().max()
    data_warning = "⚠️ فحص تجزئة" if (pd.notna(max_abs_move_60d) and max_abs_move_60d > 0.22) else "✅ نظيفة"

    if not force_include and pct_change >= 0.195:
        return None

    pts_trend = 0
    pts_wyckoff = 0
    pts_smc = 0
    pts_rs = 0
    tags = []
    setup_type = "👀 مراقبة"

    if close > ema200:
        pts_trend += 20
        tags.append("فوق EMA200")
        if ema200 > ema200_10d:
            pts_trend += 10
    else:
        tags.append("تحت EMA200")

    vol_ratio = vol / vol_sma20
    candle_range = high - low
    close_pos = (close - low) / candle_range if candle_range > 0 else 0.5
    is_breakout = close > high20_prev

    if is_breakout and vol_ratio >= 1.5:
        pts_wyckoff = 35
        tags.append(f"اختراق وايكوف ({vol_ratio:.1f}x)")
        setup_type = "🚀 اختراق مؤكد"
    elif vol_ratio >= 1.5 and candle_range < (0.75 * atr14) and close_pos >= 0.5:
        pts_wyckoff = 30
        tags.append(f"امتصاص مؤسسي ({vol_ratio:.1f}x)")
        setup_type = "🐋 امتصاص حيتان"
    elif close < prev["Close"] and vol_ratio <= 0.70 and candle_range < (0.8 * atr14) and close > ema50:
        pts_wyckoff = 25
        tags.append(f"جفاف عرض ({vol_ratio:.1f}x)")
        setup_type = "🎯 تصحيح بلا بائع"
    elif vol_ratio >= 1.3 and close > open_p:
        pts_wyckoff = 15
        tags.append(f"سيولة شرائية ({vol_ratio:.1f}x)")
        setup_type = "📈 زخم سيولة"
    elif is_breakout and vol_ratio < 1.0:
        tags.append("⚠️ كسر بفوليوم ضعيف")

    if close > ema50 and ema50 > ema200:
        pts_smc += 10
        tags.append("ترتيب متوسطات صاعد")
    if df["Bull_FVG"].tail(5).any():
        pts_smc += 10
        tags.append("فجوة سيولة FVG")

    ret_20d = (close / float(df["Close"].iloc[-21])) - 1.0 if len(df) >= 22 else 0.0
    rs_alpha = (ret_20d - market_median_ret20) * 100
    if rs_alpha > 2.0:
        pts_rs = 15
        tags.append(f"قوة نسبية (+{rs_alpha:.1f}%)")
    elif rs_alpha > 0:
        pts_rs = 7

    score = pts_trend + pts_wyckoff + pts_smc + pts_rs

    squeeze_series = (df["BB_Width_Pct"] < 0.25).astype(int)
    squeeze_days = 0
    for val in reversed(squeeze_series.tolist()):
        if val == 1:
            squeeze_days += 1
        else:
            break

    entry = close
    stop_loss = max(0.01, entry - (2.0 * atr14))
    risk_per_share = entry - stop_loss

    tp1 = entry + (1.618 * risk_per_share)
    tp2 = entry + (2.618 * risk_per_share)
    tp3 = entry + (3.618 * risk_per_share)

    risk_amount = capital * (risk_pct / 100.0)
    shares = int(risk_amount // risk_per_share) if risk_per_share > 0 else 0
    position_value = shares * entry

    gross_profit_tp1 = shares * (tp1 - entry)
    round_trip_fees = position_value * fee_rate
    net_profit_tp1 = gross_profit_tp1 - round_trip_fees

    clean_symbol = ticker.replace(".CA", "")
    tv_url = f"https://www.tradingview.com/chart/?symbol=EGX:{clean_symbol}"

    return {
        "الرمز": clean_symbol,
        "Ticker": ticker,
        "السكور": score,
        "نوع الإشارة": setup_type,
        "الإغلاق": round(close, 2),
        "ATR14": round(atr14, 3),
        "التغير %": round(pct_change * 100, 2),
        "الفوليوم": round(vol_ratio, 2),
        "القوة النسبية %": round(rs_alpha, 1),
        "السيولة (مليون)": round(avg_turnover / 1_000_000, 2),
        "انضغاط زمني (يوم)": squeeze_days,
        "الوقف (2xATR)": round(stop_loss, 2),
        "TP1": round(tp1, 2),
        "TP2": round(tp2, 2),
        "TP3": round(tp3, 2),
        "الأسهم": shares,
        "قيمة الصفقة": round(position_value, 0),
        "صافي TP1": round(net_profit_tp1, 0),
        "التشخيص الفني": " | ".join(tags) if tags else "لا يوجد زخم",
        "البيانات": data_warning,
        "score_parts": {"الاتجاه (30)": pts_trend, "وايكوف (35)": pts_wyckoff, "هيكل SMC (20)": pts_smc, "القوة النسبية (15)": pts_rs},
        "TradingView": tv_url,
        "df": df
    }

# ==========================================
# 3. محرك التحليل المالي (Piotroski F-Score)
# ==========================================
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_fundamental_analysis(ticker: str) -> dict:
    try:
        t = yf.Ticker(ticker)
        info = t.info or {}
        fin = t.financials
        bs = t.balance_sheet
        cf = t.cashflow

        f_score = 0
        tests_available = 0
        breakdown = []

        def get_val(df_stmt, keys, col_idx=0):
            if df_stmt is None or df_stmt.empty or df_stmt.shape[1] <= col_idx:
                return None
            for k in keys:
                if k in df_stmt.index:
                    val = df_stmt.loc[k].iloc[col_idx]
                    if pd.notna(val):
                        return float(val)
            return None

        net_inc_0 = get_val(fin, ["Net Income", "Net Income Common Stockholders"], 0)
        net_inc_1 = get_val(fin, ["Net Income", "Net Income Common Stockholders"], 1)
        tot_assets_0 = get_val(bs, ["Total Assets"], 0)
        tot_assets_1 = get_val(bs, ["Total Assets"], 1)
        ocf_0 = get_val(cf, ["Operating Cash Flow", "Total Cash From Operating Activities"], 0)
        lt_debt_0 = get_val(bs, ["Long Term Debt", "Total Debt"], 0)
        lt_debt_1 = get_val(bs, ["Long Term Debt", "Total Debt"], 1)
        curr_assets_0 = get_val(bs, ["Current Assets", "Total Current Assets"], 0)
        curr_liab_0 = get_val(bs, ["Current Liabilities", "Total Current Liabilities"], 0)
        curr_assets_1 = get_val(bs, ["Current Assets", "Total Current Assets"], 1)
        curr_liab_1 = get_val(bs, ["Current Liabilities", "Total Current Liabilities"], 1)
        rev_0 = get_val(fin, ["Total Revenue", "Operating Revenue"], 0)
        rev_1 = get_val(fin, ["Total Revenue", "Operating Revenue"], 1)
        gp_0 = get_val(fin, ["Gross Profit"], 0)
        gp_1 = get_val(fin, ["Gross Profit"], 1)

        if net_inc_0 is not None and tot_assets_0 and tot_assets_0 > 0:
            tests_available += 1
            roa_0 = net_inc_0 / tot_assets_0
            passed = roa_0 > 0
            if passed: f_score += 1
            breakdown.append(("1. ربحية الأصول (ROA > 0)", f"{roa_0*100:.1f}%", passed))

        if ocf_0 is not None:
            tests_available += 1
            passed = ocf_0 > 0
            if passed: f_score += 1
            breakdown.append(("2. التدفق النقدي التشغيلي > 0", f"{ocf_0/1e6:,.1f}M", passed))

        if net_inc_0 is not None and net_inc_1 is not None and tot_assets_0 and tot_assets_1:
            tests_available += 1
            roa_0 = net_inc_0 / tot_assets_0
            roa_1 = net_inc_1 / tot_assets_1
            passed = roa_0 > roa_1
            if passed: f_score += 1
            breakdown.append(("3. نمو العائد على الأصول (ΔROA)", f"{(roa_0-roa_1)*100:+.1f}%", passed))

        if ocf_0 is not None and net_inc_0 is not None:
            tests_available += 1
            passed = ocf_0 > net_inc_0
            if passed: f_score += 1
            breakdown.append(("4. جودة الأرباح (OCF > Net Income)", "نقدي حقيقي" if passed else "دفترية", passed))

        if lt_debt_0 is not None and lt_debt_1 is not None and tot_assets_0 and tot_assets_1:
            tests_available += 1
            lev_0 = lt_debt_0 / tot_assets_0
            lev_1 = lt_debt_1 / tot_assets_1
            passed = lev_0 <= lev_1
            if passed: f_score += 1
            breakdown.append(("5. انخفاض الرفع المالي (الديون/الأصول)", f"{lev_0*100:.1f}%", passed))

        if all(v is not None and v > 0 for v in [curr_assets_0, curr_liab_0, curr_assets_1, curr_liab_1]):
            tests_available += 1
            cr_0 = curr_assets_0 / curr_liab_0
            cr_1 = curr_assets_1 / curr_liab_1
            passed = cr_0 > cr_1
            if passed: f_score += 1
            breakdown.append(("6. تحسن السيولة الجارية (Current Ratio)", f"{cr_0:.2f}x", passed))

        if all(v is not None and v > 0 for v in [gp_0, rev_0, gp_1, rev_1]):
            tests_available += 1
            gm_0 = gp_0 / rev_0
            gm_1 = gp_1 / rev_1
            passed = gm_0 > gm_1
            if passed: f_score += 1
            breakdown.append(("7. تحسن هامش مجمل الربح", f"{gm_0*100:.1f}%", passed))

        if all(v is not None and v > 0 for v in [rev_0, tot_assets_0, rev_1, tot_assets_1]):
            tests_available += 1
            at_0 = rev_0 / tot_assets_0
            at_1 = rev_1 / tot_assets_1
            passed = at_0 > at_1
            if passed: f_score += 1
            breakdown.append(("8. كفاءة دوران الأصول", f"{at_0:.2f}x", passed))

        return {
            "name": info.get("longName") or info.get("shortName") or ticker,
            "sector": info.get("sector", "غير محدد"),
            "industry": info.get("industry", "غير محدد"),
            "pe": info.get("trailingPE"),
            "pb": info.get("priceToBook"),
            "roe": info.get("returnOnEquity"),
            "div_yield": info.get("dividendYield"),
            "market_cap": info.get("marketCap"),
            "f_score": f_score,
            "tests_available": tests_available,
            "breakdown": breakdown
        }
    except Exception as e:
        return {"error": str(e)}

# ==========================================
# 4. محرك التحليل الخبري وتحليل المشاعر
# ==========================================
POS_WORDS = ["أرباح", "نمو", "توزيعات", "كوبون", "استحواذ", "ارتفاع", "قفزة", "توسعات", "عقد", "صفقة", "فائض", "توصية بالشراء", "profit", "growth", "dividend", "surge", "acquisition", "beat", "expansion"]
NEG_WORDS = ["خسائر", "تراجع", "هبوط", "إيقاف", "شطب", "غرامة", "مديونية", "عجز", "انخفاض", "تحقيق", "تصفية", "loss", "decline", "drop", "suspend", "fine", "debt", "miss"]

def score_headline(text: str) -> tuple:
    t_lower = text.lower()
    pos_hits = sum(1 for w in POS_WORDS if w in t_lower)
    neg_hits = sum(1 for w in NEG_WORDS if w in t_lower)
    if pos_hits > neg_hits:
        return "إيجابي 🟢", "badge-bull", 1
    elif neg_hits > pos_hits:
        return "سلبي 🔴", "badge-bear", -1
    return "محايد ⚪", "badge-warn", 0

@st.cache_data(ttl=1800, show_spinner=False)
def fetch_stock_news(symbol_clean: str) -> list:
    news_list = []
    try:
        yf_news = yf.Ticker(f"{symbol_clean}.CA").news or []
        for item in yf_news[:6]:
            content = item.get("content", item)
            title = content.get("title", "")
            pub = content.get("provider", {}).get("displayName", "Yahoo Finance") if isinstance(content.get("provider"), dict) else "Yahoo Finance"
            link = content.get("canonicalUrl", {}).get("url", "#") if isinstance(content.get("canonicalUrl"), dict) else item.get("link", "#")
            if title:
                sent_label, badge_cls, score_val = score_headline(title)
                news_list.append({"title": title, "source": pub, "link": link, "sentiment": sent_label, "badge": badge_cls, "score": score_val})
    except Exception:
        pass

    try:
        query = urllib.parse.quote(f"{symbol_clean} البورصة المصرية")
        rss_url = f"https://news.google.com/rss/search?q={query}&hl=ar&gl=EG&ceid=EG:ar"
        req = urllib.request.Request(rss_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=6) as resp:
            xml_data = resp.read()
        root = ET.fromstring(xml_data)
        for item in root.findall(".//item")[:8]:
            title = item.find("title").text if item.find("title") is not None else ""
            link = item.find("link").text if item.find("link") is not None else "#"
            pub_date = item.find("pubDate").text[:16] if item.find("pubDate") is not None else ""
            if title:
                sent_label, badge_cls, score_val = score_headline(title)
                news_list.append({"title": title, "source": f"Google News ({pub_date})", "link": link, "sentiment": sent_label, "badge": badge_cls, "score": score_val})
    except Exception:
        pass

    return news_list

# ==========================================
# تحميل المحفظة + جلب قائمة البورصة الديناميكية
# ==========================================
my_portfolio = load_portfolio()
portfolio_clean_syms = [
    item["symbol"].upper().replace(".CA", "").strip()
    for item in my_portfolio if item.get("symbol")
]
portfolio_tickers = [f"{s}.CA" for s in portfolio_clean_syms]

all_egx_dynamic, ticker_names_map, universe_status = fetch_dynamic_egx_universe()

# ==========================================
# الشريط الجانبي (إعدادات السكانر والتليجرام)
# ==========================================
with st.sidebar:
    st.markdown("## 📲 ربط تنبيهات التليجرام")
    default_token = st.session_state.get("tg_token_val", get_secret_safe("TELEGRAM_BOT_TOKEN"))
    default_chat = st.session_state.get("tg_chat_val", get_secret_safe("TELEGRAM_CHAT_ID"))

    tg_token = st.text_input("🔑 Bot Token:", value=default_token, type="password", placeholder="7123456:AAH...")
    st.session_state["tg_token_val"] = tg_token

    tg_col1, tg_col2 = st.columns([1.3, 1])
    with tg_col1:
        tg_chat_id = st.text_input("🆔 Chat ID:", value=default_chat, placeholder="123456789")
        st.session_state["tg_chat_val"] = tg_chat_id
    with tg_col2:
        st.write("")
        st.write("")
        if st.button("🔍 جلب ID", use_container_width=True, help="اضغط Start في بوتك أولاً ثم اضغط هنا"):
            found_id, info_msg = detect_telegram_chat_id(tg_token)
            if found_id:
                st.session_state["tg_chat_val"] = found_id
                st.success(f"ID: {found_id}")
                st.rerun()
            else:
                st.warning(info_msg)

    tg_auto_port = st.checkbox("🔔 إرسال تنبيهات المحفظة تلقائياً", value=True)
    tg_auto_whales = st.checkbox("🐋 إرسال تنبيه عند رصد صفقة حيتان (سكور 80+)", value=False)

    if st.button("🧪 إرسال رسالة تجريبية لتليجرام", use_container_width=True):
        ok, res_msg = send_telegram_message(
            tg_token,
            tg_chat_id,
            "🦅 <b>EGX Whale Hunter Pro V7.3</b>\n✅ تم ربط بوت التليجرام بنجاح! ستصلك تنبيهات المحفظة هنا فوراً."
        )
        if ok:
            st.success("✅ وصلت الرسالة التجريبية لتليجرام!")
        else:
            st.error(f"❌ فشل الإرسال: {res_msg}")

    st.divider()
    st.markdown("## 🎛️ إعدادات السكانر")
    st.caption(f"📡 القائمة: {universe_status}")
    market_scope = st.radio(
        "🌐 نطاق المسح:",
        options=[
            f"كل أسهم البورصة الديناميكية ({len(all_egx_dynamic)} سهم)",
            f"الأسهم القيادية والنشطة ({len(LEADERS_EGX_TICKERS)} سهم)"
        ],
        index=0
    )
    base_list = all_egx_dynamic if "كل أسهم" in market_scope else LEADERS_EGX_TICKERS

    extra_tickers = st.text_input("➕ إضافة رموز إضافية للمسح:", placeholder="مثال: VALU, ACTF")
    added = []
    if extra_tickers.strip():
        added = [t.strip().upper() if t.strip().upper().endswith(".CA") else f"{t.strip().upper()}.CA" for t in extra_tickers.split(",") if t.strip()]

    tickers_list = sorted(list(set(base_list + added + portfolio_tickers)))

    capital = st.number_input("💰 رأس المال للمقترحات (ج.م)", min_value=5000, value=100000, step=5000)
    risk_pct = st.slider("🛡️ المخاطرة في الصفقة (%)", min_value=0.5, max_value=5.0, value=1.5, step=0.25)
    min_turnover_m = st.number_input("💧 الحد الأدنى للسيولة (مليون)", min_value=0.1, value=3.0, step=0.5)

    fee_tier = st.radio(
        "💳 شريحة Thndr Trader:",
        options=[
            "أول 50 صفقة بالشهر (~0.16%)",
            "أكثر من 50 صفقة / عادي (~0.37%)"
        ]
    )
    fee_rate = 0.0016 if "0.16%" in fee_tier else 0.0037

    min_score = st.slider("🎯 الحد الأدنى للسكور بالسكانر", min_value=0, max_value=100, value=55, step=5)
    alert_buffer_pct = st.slider("🔔 حساسية تنبيه قرب الهدف/الوقف (%)", min_value=0.5, max_value=8.0, value=2.5, step=0.5)

    if st.button("🔄 تحديث القائمة والأسعار الآن", type="primary", use_container_width=True):
        fetch_dynamic_egx_universe.clear()
        fetch_all_market_data.clear()
        fetch_tv_live_quotes.clear()
        st.rerun()

# ==========================================
# البانر الافتتاحي المضيء (Hero Banner)
# ==========================================
session_badge = get_egx_session_status()
tg_status_txt = "📲 تليجرام متصل" if (tg_token and tg_chat_id) else "📴 تليجرام غير مربوط"
st.markdown(f"""
<div class="hero-banner">
    <div>
        <div class="hero-title">🦅 <span class="hero-accent">EGX WHALE HUNTER</span> PRO <span style="font-size:13px;color:#FACC15;">V7.3</span></div>
        <div class="hero-sub">🌐 {len(all_egx_dynamic)} سهم ديناميكي • 💼 محفظتي ({len(portfolio_clean_syms)}) • {tg_status_txt} • 🪐 جان والكواكب</div>
    </div>
    <div class="session-pill">{session_badge}</div>
</div>
""", unsafe_allow_html=True)

with st.spinner(f"🚀 جاري سحب وتحليل بيانات السوق ({len(tickers_list)} سهم)..."):
    market_data_map = fetch_all_market_data(tuple(tickers_list))

ret20_list = []
for df_tmp in market_data_map.values():
    if len(df_tmp) >= 22:
        ret20_list.append((float(df_tmp["Close"].iloc[-1]) / float(df_tmp["Close"].iloc[-21])) - 1.0)
market_median_ret20 = float(np.median(ret20_list)) if ret20_list else 0.0

all_analyzed_map = {}
scanner_results = []

for ticker, df_stock in market_data_map.items():
    is_in_port = ticker in portfolio_tickers
    res = analyze_stock_pro(
        ticker=ticker,
        df=df_stock,
        market_median_ret20=market_median_ret20,
        min_turnover=min_turnover_m * 1_000_000,
        capital=capital,
        risk_pct=risk_pct,
        fee_rate=fee_rate,
        force_include=is_in_port
    )
    if res is not None:
        all_analyzed_map[res["الرمز"]] = res
        avg_t = res["السيولة (مليون)"] * 1_000_000
        if avg_t >= (min_turnover_m * 1_000_000) and len(df_stock) >= 205 and res["التغير %"] < 19.5:
            scanner_results.append(res)

# سحب الأسعار اللحظية من TradingView لجميع أسهم المحفظة + أفضل 40 سهم في الرادار (تتجدد كل 60 ثانية)
top_radar_syms = [r["الرمز"] for r in sorted(scanner_results, key=lambda x: x["السكور"], reverse=True)[:40]]
live_query_syms = tuple(sorted(list(set(portfolio_clean_syms + top_radar_syms))))
tv_live_map, last_live_sync = fetch_tv_live_quotes(live_query_syms)

# دمج السعر اللحظي من TradingView فوق بيانات Yahoo Finance المتأخرة أثناء الجلسة
for sym, tv_q in tv_live_map.items():
    if tv_q.get("close", 0) > 0 and sym in all_analyzed_map:
        live_c = round(tv_q["close"], 2)
        all_analyzed_map[sym]["الإغلاق"] = live_c
        all_analyzed_map[sym]["التغير %"] = round(tv_q["change"], 2)
        atr_u = all_analyzed_map[sym]["ATR14"]
        sl_u = round(max(0.01, live_c - (2.0 * atr_u)), 2)
        r_u = max(0.01, live_c - sl_u)
        all_analyzed_map[sym]["الوقف (2xATR)"] = sl_u
        all_analyzed_map[sym]["TP1"] = round(live_c + (1.618 * r_u), 2)
        all_analyzed_map[sym]["TP2"] = round(live_c + (2.618 * r_u), 2)
        all_analyzed_map[sym]["TP3"] = round(live_c + (3.618 * r_u), 2)

# إضافة أي سهم في المحفظة غير متوفر على Yahoo Finance (مثل BONY)
missing_port_syms = [s for s in portfolio_clean_syms if s not in all_analyzed_map]
for m_sym in missing_port_syms:
    tv_q = tv_live_map.get(m_sym)
    p_entry_item = next((x for x in my_portfolio if x["symbol"].upper().replace(".CA", "").strip() == m_sym), {})
    fallback_buy = float(p_entry_item.get("buy_price", 0.0))

    if tv_q and tv_q.get("close", 0) > 0:
        c_val = round(tv_q["close"], 2)
        atr_val = round(tv_q["atr"], 3)
        diag_txt = "📡 بيانات لحظية من TradingView (سهم حديث الإدراج)"
    else:
        c_val = round(fallback_buy, 2)
        atr_val = round(max(0.01, c_val * 0.025), 3)
        diag_txt = "⏳ بانتظار بيانات التداول (يُعرض سعر الشراء مؤقتاً)"

    sl_val = round(max(0.01, c_val - 2.0 * atr_val), 2)
    r_share = max(0.01, c_val - sl_val)
    all_analyzed_map[m_sym] = {
        "الرمز": m_sym,
        "Ticker": f"{m_sym}.CA",
        "السكور": 0,
        "نوع الإشارة": "🆕 إدراج حديث",
        "الإغلاق": c_val,
        "ATR14": atr_val,
        "التغير %": round(tv_q["change"], 2) if tv_q else 0.0,
        "الفوليوم": 0.0,
        "القوة النسبية %": 0.0,
        "السيولة (مليون)": 0.0,
        "انضغاط زمني (يوم)": 0,
        "الوقف (2xATR)": sl_val,
        "TP1": round(c_val + 1.618 * r_share, 2),
        "TP2": round(c_val + 2.618 * r_share, 2),
        "TP3": round(c_val + 3.618 * r_share, 2),
        "الأسهم": 0,
        "قيمة الصفقة": 0,
        "صافي TP1": 0,
        "التشخيص الفني": diag_txt,
        "البيانات": "🆕 TradingView",
        "score_parts": {"الاتجاه (30)": 0, "وايكوف (35)": 0, "هيكل SMC (20)": 0, "القوة النسبية (15)": 0},
        "TradingView": f"https://www.tradingview.com/chart/?symbol=EGX:{m_sym}",
        "df": None
    }

scanner_results.sort(key=lambda x: x["السكور"], reverse=True)
filtered_results = [r for r in scanner_results if r["السكور"] >= min_score]

# ==========================================
# معالجة محفظتي وتوليد الإشعارات الفورية + إرسالها لتليجرام
# ==========================================
portfolio_rows = []
active_alerts = []
total_port_cost = 0.0
total_port_val = 0.0

sent_tg_log = load_sent_tg_log()
today_str = get_cairo_now().strftime("%Y-%m-%d")
log_changed = False

for item in my_portfolio:
    sym = item["symbol"].upper().replace(".CA", "").strip()
    shares = int(item.get("shares", 0))
    buy_p = float(item.get("buy_price", 0.0))
    user_sl = float(item.get("stop_loss", 0.0))
    user_tp1 = float(item.get("tp1", 0.0))
    user_tp2 = float(item.get("tp2", 0.0))

    if not sym or shares <= 0 or buy_p <= 0:
        continue

    stock_info = all_analyzed_map.get(sym)
    curr_p = stock_info["الإغلاق"] if (stock_info and stock_info["الإغلاق"] > 0) else buy_p
    atr14 = stock_info["ATR14"] if stock_info else round(buy_p * 0.025, 3)

    sl = user_sl if user_sl > 0 else round(max(0.01, buy_p - 2.0 * atr14), 2)
    risk_unit = max(0.01, buy_p - sl)
    tp1 = user_tp1 if user_tp1 > 0 else round(buy_p + 1.618 * risk_unit, 2)
    tp2 = user_tp2 if user_tp2 > 0 else round(buy_p + 2.618 * risk_unit, 2)

    cost_val = shares * buy_p
    mkt_val = shares * curr_p
    fees_est = mkt_val * fee_rate
    net_pnl = (mkt_val - cost_val) - fees_est
    net_pnl_pct = (net_pnl / cost_val) * 100

    total_port_cost += cost_val
    total_port_val += mkt_val

    dist_sl_pct = ((curr_p - sl) / curr_p) * 100
    dist_tp1_pct = ((tp1 - curr_p) / curr_p) * 100

    alert_status = "⏳ داخل النطاق الآمن"
    alert_code = None
    tg_msg_body = None

    if curr_p <= sl:
        alert_status = "🚨 كسر وقف الخسارة!"
        alert_code = "HIT_SL"
        active_alerts.append(("danger", f"🚨 <b>تنبيه عاجل ({sym}):</b> السعر الحالي (<b>{curr_p}</b>) كسر وقف الخسارة (<b>{sl}</b>)!"))
        tg_msg_body = f"🚨 <b>كسر وقف الخسارة — {sym}</b>\nالسعر الحالي: <b>{curr_p} ج.م</b>\nوقف الخسارة: <b>{sl} ج.م</b>\nصافي المركز: {net_pnl:+,.0f} ج.م ({net_pnl_pct:+.1f}%)"
    elif 0 < dist_sl_pct <= alert_buffer_pct:
        alert_status = f"⚠️ قرب الوقف ({dist_sl_pct:.1f}%)"
        alert_code = "NEAR_SL"
        active_alerts.append(("warn", f"⚠️ <b>تحذير ({sym}):</b> السهم على بُعد <b>{dist_sl_pct:.1f}%</b> فقط من وقف الخسارة (السعر: {curr_p} | الوقف: {sl})."))
        tg_msg_body = f"⚠️ <b>اقتراب من وقف الخسارة — {sym}</b>\nالسعر الحالي: <b>{curr_p} ج.م</b> (يبعد {dist_sl_pct:.1f}% عن الوقف <b>{sl}</b>)"
    elif curr_p >= tp2:
        alert_status = "🏆 تحقق TP2!"
        alert_code = "HIT_TP2"
        active_alerts.append(("success", f"🏆 <b>مبروك ({sym}):</b> السهم حقق الهدف الثاني <b>TP2 ({tp2})</b>! السعر الحالي: <b>{curr_p}</b>."))
        tg_msg_body = f"🏆 <b>تحقق الهدف الثاني TP2 — {sym}</b>\nالسعر الحالي: <b>{curr_p} ج.م</b> | الهدف TP2: <b>{tp2}</b>\nصافي الربح: <b>{net_pnl:+,.0f} ج.م ({net_pnl_pct:+.1f}%)</b>"
    elif curr_p >= tp1:
        alert_status = "🎯 تحقق TP1!"
        alert_code = "HIT_TP1"
        active_alerts.append(("success", f"🎯 <b>تحقق الهدف ({sym}):</b> السهم وصل إلى <b>TP1 ({tp1})</b>! السعر الحالي: <b>{curr_p}</b>."))
        tg_msg_body = f"🎯 <b>تحقق الهدف الأول TP1 — {sym}</b>\nالسعر الحالي: <b>{curr_p} ج.م</b> | الهدف TP1: <b>{tp1}</b>\nصافي الربح: <b>{net_pnl:+,.0f} ج.م ({net_pnl_pct:+.1f}%)</b>"
    elif 0 < dist_tp1_pct <= alert_buffer_pct:
        alert_status = f"🔔 قرب TP1 ({dist_tp1_pct:.1f}%)"
        alert_code = "NEAR_TP1"
        active_alerts.append(("success", f"🔔 <b>اقترب الهدف ({sym}):</b> السهم على بُعد <b>{dist_tp1_pct:.1f}%</b> من الهدف الأول <b>TP1 ({tp1})</b> (السعر الحالي: {curr_p})."))
        tg_msg_body = f"🔔 <b>اقتراب من الهدف TP1 — {sym}</b>\nالسعر الحالي: <b>{curr_p} ج.م</b> (يبعد {dist_tp1_pct:.1f}% عن الهدف <b>{tp1}</b>)"

    if alert_code and tg_msg_body and tg_auto_port and tg_token and tg_chat_id:
        dedup_key = f"{today_str}_{sym}_{alert_code}"
        if dedup_key not in sent_tg_log:
            ok, _ = send_telegram_message(tg_token, tg_chat_id, tg_msg_body)
            if ok:
                sent_tg_log[dedup_key] = get_cairo_now().strftime("%H:%M")
                log_changed = True

    span = max(0.01, tp1 - sl)
    progress_ratio = min(1.0, max(0.0, (curr_p - sl) / span))

    portfolio_rows.append({
        "الرمز": sym,
        "حالة التنبيه": alert_status,
        "السكور الفني": stock_info["السكور"] if stock_info else 0,
        "الكمية": shares,
        "متوسط الشراء": round(buy_p, 2),
        "السعر الحالي": curr_p,
        "تغير اليوم %": stock_info["التغير %"] if stock_info else 0.0,
        "صافي الربح/الخسارة": round(net_pnl, 0),
        "العائد %": round(net_pnl_pct, 2),
        "وقف الخسارة": sl,
        "بُعد الوقف %": round(dist_sl_pct, 1),
        "TP1": tp1,
        "بُعد TP1 %": round(dist_tp1_pct, 1),
        "TP2": tp2,
        "التشخيص الفني": stock_info["التشخيص الفني"] if stock_info else "بانتظار البيانات",
        "progress_ratio": progress_ratio,
        "TradingView": f"https://www.tradingview.com/chart/?symbol=EGX:{sym}",
        "stock_info": stock_info
    })

if tg_auto_whales and tg_token and tg_chat_id:
    for r in filtered_results:
        if r["السكور"] >= 80:
            w_key = f"{today_str}_WHALE_{r['الرمز']}"
            if w_key not in sent_tg_log:
                w_msg = (
                    f"🐋 <b>إشارة حيتان جديدة — {r['الرمز']}</b>\n"
                    f"السكور: <b>{r['السكور']}/100</b> ({r['نوع الإشارة']})\n"
                    f"السعر: <b>{r['الإغلاق']}</b> | الوقف: <b>{r['الوقف (2xATR)']}</b> | TP1: <b>{r['TP1']}</b>"
                )
                ok, _ = send_telegram_message(tg_token, tg_chat_id, w_msg)
                if ok:
                    sent_tg_log[w_key] = get_cairo_now().strftime("%H:%M")
                    log_changed = True

if log_changed:
    save_sent_tg_log(sent_tg_log)

if active_alerts:
    for level, msg in active_alerts:
        st.markdown(f'<div class="alert-box-{level}">{msg}</div>', unsafe_allow_html=True)

# ==========================================
# شريط التحديث اللحظي السريع (متاح على الهاتف مباشرة)
# ==========================================
ref_c1, ref_c2 = st.columns([2, 1])
with ref_c1:
    st.caption(f"📡 مصدر الأسعار اللحظية: **TradingView مباشر** | آخر تحديث: **{last_live_sync}** بتوقيت القاهرة (يتحدث تلقائياً كل 60 ثانية)")
with ref_c2:
    if st.button("🔄 تحديث الأسعار اللحظية الآن", use_container_width=True):
        fetch_tv_live_quotes.clear()
        st.rerun()

# ==========================================
# زر التنقل الرئيسي البارز
# ==========================================
main_view = st.radio(
    "🧭 اختر القسم:",
    options=[
        f"💼 محفظتي الشخصية والتنبيهات ({len(portfolio_rows)})",
        f"🎯 رادار صفقات السوق ({len(filtered_results)})"
    ],
    horizontal=True,
    label_visibility="collapsed"
)

st.divider()

# ==============================================================================
# القسم الأول: محفظتي الشخصية وإضافة الأسهم والتنبيهات
# ==============================================================================
if "محفظتي" in main_view:
    st.markdown("### 💼 محفظتي الشخصية والتنبيهات الفورية")

    if st.session_state.get("last_port_msg"):
        st.success(st.session_state["last_port_msg"])

    total_net_pnl = total_port_val - total_port_cost - (total_port_val * fee_rate)
    total_pnl_pct = ((total_net_pnl / total_port_cost) * 100) if total_port_cost > 0 else 0.0
    pnl_cls = "txt-green" if total_net_pnl >= 0 else "txt-red"

    pk1, pk2, pk3, pk4 = st.columns(4)
    pk1.markdown(f'<div class="kpi-card"><div class="kpi-label">💵 إجمالي التكلفة</div><div class="kpi-val">{total_port_cost:,.0f} ج.م</div></div>', unsafe_allow_html=True)
    pk2.markdown(f'<div class="kpi-card"><div class="kpi-label">💰 القيمة الحالية</div><div class="kpi-val txt-cyan">{total_port_val:,.0f} ج.م</div></div>', unsafe_allow_html=True)
    pk3.markdown(f'<div class="kpi-card"><div class="kpi-label">📈 صافي الربح/الخسارة</div><div class="kpi-val {pnl_cls}">{total_net_pnl:+,.0f} ({total_pnl_pct:+.1f}%)</div></div>', unsafe_allow_html=True)
    pk4.markdown(f'<div class="kpi-card" style="border-top-color:#FACC15;"><div class="kpi-label">🔔 تنبيهات نشطة</div><div class="kpi-val txt-gold">{len(active_alerts)}</div></div>', unsafe_allow_html=True)

    st.write("")

    if portfolio_rows:
        if st.button("📲 إرسال تقرير محفظتي الكامل الآن إلى تليجرام", use_container_width=True):
            if not tg_token or not tg_chat_id:
                st.warning("⚠️ افتح القائمة الجانبية (>) وأدخل Bot Token و Chat ID أولاً.")
            else:
                lines = [f"📊 <b>تقرير محفظتك في البورصة المصرية</b>", f"القيمة: <b>{total_port_val:,.0f} ج.م</b> | الصافي: <b>{total_net_pnl:+,.0f} ج.م ({total_pnl_pct:+.1f}%)</b>", ""]
                for pr in portfolio_rows:
                    lines.append(
                        f"• <b>{pr['الرمز']}</b>: السعر {pr['السعر الحالي']} ({pr['العائد %']:+.1f}%) | "
                        f"SL: {pr['وقف الخسارة']} | TP1: {pr['TP1']} — {pr['حالة التنبيه']}"
                    )
                ok, r_msg = send_telegram_message(tg_token, tg_chat_id, "\n".join(lines))
                if ok:
                    st.success("✅ تم إرسال تقرير المحفظة إلى بوت التليجرام!")
                else:
                    st.error(f"❌ تعذر الإرسال: {r_msg}")

    st.markdown("#### ➕ إضافة سهم جديد أو تحديث مركز في محفظتي")
    with st.form("add_stock_form", clear_on_submit=True):
        fc1, fc2, fc3 = st.columns(3)
        with fc1:
            in_sym_raw = st.text_input(
                "اكتب رمز السهم مباشرة:",
                placeholder="مثال: BONY أو COMI",
                help="اكتب كود السهم في البورصة المصرية بدون .CA"
            )
        with fc2:
            in_shares = st.number_input("عدد الأسهم (الكمية)", min_value=1, value=100, step=10)
        with fc3:
            in_buy = st.number_input("متوسط سعر الشراء (ج.م)", min_value=0.01, value=5.0, step=0.1)

        fc4, fc5, fc6 = st.columns(3)
        with fc4:
            in_sl = st.number_input("وقف الخسارة (0 = آلي 2×ATR)", min_value=0.0, value=0.0, step=0.1)
        with fc5:
            in_tp1 = st.number_input("الهدف الأول TP1 (0 = آلي)", min_value=0.0, value=0.0, step=0.1)
        with fc6:
            in_tp2 = st.number_input("الهدف الثاني TP2 (0 = آلي)", min_value=0.0, value=0.0, step=0.1)

        submitted = st.form_submit_button("💾 حفظ السهم في محفظتي وتفعيل التنبيهات", type="primary", use_container_width=True)
        if submitted:
            clean_in = re.sub(r"[^A-Z0-9]", "", in_sym_raw.upper().replace(".CA", ""))
            if not clean_in:
                st.error("⚠️ من فضلك اكتب رمز السهم أولاً (مثل BONY).")
            else:
                updated_list = [p for p in my_portfolio if p["symbol"].upper().replace(".CA", "").strip() != clean_in]
                updated_list.append({
                    "symbol": clean_in,
                    "shares": int(in_shares),
                    "buy_price": float(in_buy),
                    "stop_loss": float(in_sl),
                    "tp1": float(in_tp1),
                    "tp2": float(in_tp2)
                })
                save_portfolio(updated_list)
                st.session_state["last_port_msg"] = f"✅ تم حفظ سهم ({clean_in}) بنجاح! إجمالي الأسهم في محفظتك الآن: {len(updated_list)} أسهم."
                st.rerun()

    if not portfolio_rows:
        st.info("📌 اكتب رمز السهم في المربع الأول (مثل BONY) ثم الكمية وسعر الشراء واضغط حفظ، وسيظهر فوراً في الجدول بالأسفل.")
    else:
        st.markdown(f"#### 📋 جدول متابعة أسهم المحفظة ({len(portfolio_rows)} أسهم)")
        p_cols = [
            "الرمز", "حالة التنبيه", "السكور الفني", "الكمية", "متوسط الشراء",
            "السعر الحالي", "تغير اليوم %", "صافي الربح/الخسارة", "العائد %",
            "وقف الخسارة", "بُعد الوقف %", "TP1", "بُعد TP1 %", "TP2", "TradingView"
        ]
        st.dataframe(
            pd.DataFrame(portfolio_rows)[p_cols],
            use_container_width=True,
            hide_index=True,
            column_config={
                "TradingView": st.column_config.LinkColumn("شارت TV", display_text="فتح ↗"),
                "السكور الفني": st.column_config.ProgressColumn("السكور", min_value=0, max_value=100, format="%d"),
            }
        )

        st.divider()
        p_sel_col, p_del_col = st.columns([2, 1])
        with p_sel_col:
            port_selected_sym = st.selectbox(
                "🔍 اختر سهماً من محفظتك لعرض الشارت ومقياس الهدف والوقف:",
                options=[r["الرمز"] for r in portfolio_rows],
                key="port_stock_select"
            )
        with p_del_col:
            st.write("")
            st.write("")
            if st.button(f"🗑️ حذف {port_selected_sym} من المحفظة", use_container_width=True):
                new_p = [p for p in my_portfolio if p["symbol"].upper().replace(".CA", "").strip() != port_selected_sym]
                save_portfolio(new_p)
                st.session_state["last_port_msg"] = f"🗑️ تم حذف سهم ({port_selected_sym}) من محفظتك."
                st.rerun()

        p_item = next(r for r in portfolio_rows if r["الرمز"] == port_selected_sym)
        p_sinfo = p_item["stock_info"]

        pc_chart, pc_info = st.columns([2.1, 1])
        with pc_chart:
            if p_sinfo is not None and p_sinfo.get("df") is not None and not p_sinfo["df"].empty:
                df_pchart = p_sinfo["df"].tail(100)
                fig_p = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.04, row_heights=[0.75, 0.25])
                fig_p.add_trace(go.Candlestick(
                    x=df_pchart.index, open=df_pchart["Open"], high=df_pchart["High"],
                    low=df_pchart["Low"], close=df_pchart["Close"], name="السعر"
                ), row=1, col=1)
                fig_p.add_trace(go.Scatter(x=df_pchart.index, y=df_pchart["EMA50"], line=dict(color="#38BDF8", width=1.5), name="EMA 50"), row=1, col=1)
                fig_p.add_trace(go.Scatter(x=df_pchart.index, y=df_pchart["EMA200"], line=dict(color="#F59E0B", width=2.2), name="EMA 200"), row=1, col=1)

                fig_p.add_hline(y=p_item["متوسط الشراء"], line_dash="dot", line_color="#FACC15", annotation_text=f"شرائك: {p_item['متوسط الشراء']}", row=1, col=1)
                fig_p.add_hline(y=p_item["وقف الخسارة"], line_dash="dash", line_color="#F87171", annotation_text=f"SL: {p_item['وقف الخسارة']}", row=1, col=1)
                fig_p.add_hline(y=p_item["TP1"], line_dash="dash", line_color="#4ADE80", annotation_text=f"TP1: {p_item['TP1']}", row=1, col=1)
                fig_p.add_hline(y=p_item["TP2"], line_dash="dash", line_color="#10B981", annotation_text=f"TP2: {p_item['TP2']}", row=1, col=1)

                v_cols = ["#4ADE80" if c >= o else "#F87171" for c, o in zip(df_pchart["Close"], df_pchart["Open"])]
                fig_p.add_trace(go.Bar(x=df_pchart.index, y=df_pchart["Volume"], marker_color=v_cols, name="الفوليوم"), row=2, col=1)

                fig_p.update_layout(
                    title=dict(text=f"📊 متابعة مركزك في {port_selected_sym}", font=dict(color="#FFFFFF", size=15)),
                    height=500, xaxis_rangeslider_visible=False, template="plotly_dark",
                    paper_bgcolor="#0B0F19", plot_bgcolor="#131C31", font=dict(color="#FFFFFF"),
                    margin=dict(l=10, r=10, t=40, b=10)
                )
                st.plotly_chart(fig_p, use_container_width=True)
            else:
                st.info(f"ℹ️ الرسم البياني التاريخي لـ **{port_selected_sym}** غير متوفر بعد على Yahoo Finance (سهم حديث الإدراج). يتم تحديث السعر اللحظي ومستويات الوقف والأهداف من TradingView تلقائياً.")

        with pc_info:
            item_pnl_cls = "txt-green" if p_item["صافي الربح/الخسارة"] >= 0 else "txt-red"
            st.markdown(f"""
            <div class="pro-card">
                <h4 class="txt-cyan" style="margin-top:0;">💼 بطاقة السهم: {port_selected_sym}</h4>
                <p><span class="badge-bull">{p_item['حالة التنبيه']}</span></p>
                <p class="txt-white"><b>السكور الفني الحالي:</b> {p_item['السكور الفني']}/100</p>
                <p class="txt-muted" style="font-size:13px;">{p_item['التشخيص الفني']}</p>
                <hr style="border-color:#26334D;">
                <p class="txt-white"><b>الكمية:</b> {p_item['الكمية']:,} سهم</p>
                <p class="txt-white"><b>متوسط الشراء:</b> {p_item['متوسط الشراء']} ج.م</p>
                <p class="txt-white"><b>السعر الحالي:</b> {p_item['السعر الحالي']} ج.م ({p_item['تغير اليوم %']:+.2f}% اليوم)</p>
                <p class="txt-white"><b>صافي الربح/الخسارة:</b> <span class="{item_pnl_cls}" style="font-weight:bold;">{p_item['صافي الربح/الخسارة']:+,.0f} ج.م ({p_item['العائد %']:+.2f}%)</span></p>
                <hr style="border-color:#26334D;">
                <p class="txt-white"><b>وقف الخسارة:</b> <span class="txt-red">{p_item['وقف الخسارة']}</span> (يبعد {p_item['بُعد الوقف %']}%)</p>
                <p class="txt-white"><b>الهدف الأول TP1:</b> <span class="txt-green">{p_item['TP1']}</span> (يبعد {p_item['بُعد TP1 %']}%)</p>
                <p class="txt-white"><b>الهدف الثاني TP2:</b> <span class="txt-green">{p_item['TP2']}</span></p>
            </div>
            """, unsafe_allow_html=True)

            st.caption("📍 مقياس موقع السعر بين الوقف (0%) والهدف الأول (100%):")
            st.progress(p_item["progress_ratio"])
            st.link_button("🚀 افتح السهم على TradingView ↗", p_item["TradingView"], use_container_width=True)

    with st.expander("💾 حفظ / استعادة نسخة احتياطية من المحفظة (Backup)"):
        b_col1, b_col2 = st.columns(2)
        with b_col1:
            json_str = json.dumps(my_portfolio, ensure_ascii=False, indent=2)
            st.download_button(
                label="⬇️ تحميل ملف المحفظة (JSON)",
                data=json_str,
                file_name="my_egx_portfolio.json",
                mime="application/json",
                use_container_width=True
            )
        with b_col2:
            uploaded_file = st.file_uploader("⬆️ استعادة المحفظة من ملف", type=["json"], label_visibility="collapsed")
            if uploaded_file is not None:
                try:
                    restored = json.load(uploaded_file)
                    if isinstance(restored, list):
                        save_portfolio(restored)
                        st.success("✅ تمت استعادة المحفظة بنجاح!")
                        st.rerun()
                except Exception:
                    st.error("⚠️ ملف غير صالح.")

# ==============================================================================
# القسم الثاني: رادار صفقات السوق والتحليل الشامل
# ==============================================================================
else:
    m1, m2, m3, m4 = st.columns(4)
    m1.markdown(f'<div class="kpi-card"><div class="kpi-label">📡 أسهم مفحوصة</div><div class="kpi-val">{len(market_data_map)} / {len(tickers_list)}</div></div>', unsafe_allow_html=True)
    m2.markdown(f'<div class="kpi-card"><div class="kpi-label">🎯 صفقات مرشحة</div><div class="kpi-val txt-green">{len(filtered_results)}</div></div>', unsafe_allow_html=True)
    ret_color_cls = "txt-green" if market_median_ret20 >= 0 else "txt-red"
    m3.markdown(f'<div class="kpi-card"><div class="kpi-label">📈 أداء السوق (20 يوم)</div><div class="kpi-val {ret_color_cls}">{market_median_ret20*100:+.1f}%</div></div>', unsafe_allow_html=True)
    m4.markdown(f'<div class="kpi-card" style="border-top-color:#FACC15;"><div class="kpi-label">🛡️ المخاطرة المقترحة</div><div class="kpi-val txt-gold">{capital*(risk_pct/100):,.0f} ج.م</div></div>', unsafe_allow_html=True)

    st.write("")

    if filtered_results:
        st.markdown("### 🏆 أقوى الفرص المرصودة اليوم (Top 3 Radar)")
        top_n = filtered_results[:3]
        top_cols = st.columns(len(top_n))
        medals = ["👑 المركز #1", "🔥 المركز #2", "⚡ المركز #3"]

        for idx, (col_box, item) in enumerate(zip(top_cols, top_n)):
            card_extra = "top-card top-card-gold" if idx == 0 else "top-card"
            chg_cls = "txt-green" if item["التغير %"] >= 0 else "txt-red"
            col_box.markdown(f"""
            <div class="{card_extra}">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                    <span class="txt-gold" style="font-weight:800;font-size:14px;">{medals[idx]}</span>
                    <span class="badge-bull">{item['نوع الإشارة']}</span>
                </div>
                <div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:6px;">
                    <span class="txt-white" style="font-size:24px;font-weight:900;">{item['الرمز']}</span>
                    <span class="txt-cyan" style="font-size:18px;font-weight:800;">السكور: {item['السكور']}/100</span>
                </div>
                <div style="font-size:13px;margin-bottom:8px;" class="txt-muted">
                    السعر: <b class="txt-white">{item['الإغلاق']} ج.م</b> (<span class="{chg_cls}">{item['التغير %']:+.2f}%</span>) • فوليوم: <b class="txt-white">{item['الفوليوم']}x</b>
                </div>
                <div style="display:flex;justify-content:space-between;background:#0B0F19;padding:8px 10px;border-radius:8px;font-size:12px;">
                    <span>🛑 الوقف: <b class="txt-red">{item['الوقف (2xATR)']}</b></span>
                    <span>🎯 TP1: <b class="txt-green">{item['TP1']}</b></span>
                    <span>💰 صافي: <b class="txt-green">{item['صافي TP1']:,.0f}</b></span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown(f"#### 📋 جدول الصفقات المحتملة ({len(filtered_results)} سهم)")
        display_cols = [
            "الرمز", "السكور", "نوع الإشارة", "الإغلاق", "التغير %",
            "الفوليوم", "القوة النسبية %", "السيولة (مليون)",
            "الوقف (2xATR)", "TP1", "TP2", "الأسهم", "صافي TP1",
            "البيانات", "TradingView"
        ]
        st.dataframe(
            pd.DataFrame(filtered_results)[display_cols],
            use_container_width=True,
            hide_index=True,
            height=290,
            column_config={
                "TradingView": st.column_config.LinkColumn("شارت TV", display_text="فتح ↗"),
                "السكور": st.column_config.ProgressColumn("السكور", min_value=0, max_value=100, format="%d"),
            }
        )
    else:
        st.warning("⚠️ لا توجد أسهم تطابق شروط السكانر الحالية. افتح القائمة الجانبية (>) لتقليل الحد الأدنى للسكور أو السيولة.")

# ==============================================================================
# الدراسة العميقة المشتركة (تعمل على أي سهم في محفظتك أو في السوق)
# ==============================================================================
combined_symbols = sorted(list(set([r["الرمز"] for r in portfolio_rows] + [r["الرمز"] for r in filtered_results])))
if not combined_symbols and all_analyzed_map:
    combined_symbols = sorted(list(all_analyzed_map.keys()))

if combined_symbols:
    st.divider()
    sel_col1, _ = st.columns([1.5, 1])
    with sel_col1:
        selected_symbol = st.selectbox(
            "🔬 اختر أي سهم (من محفظتك أو من السوق) للدراسة الفنية والمالية والزمنية والخبرية:",
            options=combined_symbols,
            format_func=lambda sym: f"{'💼 [محفظتي] ' if sym in [p['الرمز'] for p in portfolio_rows] else '🎯 '}{sym}  |  السكور: {all_analyzed_map[sym]['السكور']}/100"
        )
    selected_data = all_analyzed_map[selected_symbol]
    has_hist_df = selected_data.get("df") is not None and not selected_data["df"].empty

    sub_view = st.radio(
        "📑 اختر نوع التحليل التفصيلي:",
        options=[
            "📈 الشارت الفني وخطة التنفيذ",
            "📊 التحليل المالي (F-Score)",
            "🪐 التحليل الزمني (جان والكواكب)",
            "📰 الرادار الخبري"
        ],
        horizontal=True
    )

    if "الشارت الفني" in sub_view:
        if not has_hist_df:
            st.info(f"ℹ️ السهم **{selected_symbol}** حديث الإدراج ولا يمتلك شموعاً تاريخية على Yahoo Finance بعد. السعر اللحظي الحالي من TradingView: **{selected_data['الإغلاق']} ج.م**.")
            st.link_button(f"🚀 افتح شارت {selected_symbol} على TradingView ↗", selected_data["TradingView"], use_container_width=True)
        else:
            c_chart, c_plan = st.columns([2.1, 1])
            with c_chart:
                df_chart = selected_data["df"].tail(120)
                fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.04, row_heights=[0.74, 0.26])
                fig.add_trace(go.Candlestick(
                    x=df_chart.index, open=df_chart["Open"], high=df_chart["High"],
                    low=df_chart["Low"], close=df_chart["Close"], name="السعر"
                ), row=1, col=1)
                fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart["EMA20"], line=dict(color="#A855F7", width=1.3), name="EMA 20"), row=1, col=1)
                fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart["EMA50"], line=dict(color="#38BDF8", width=1.6), name="EMA 50"), row=1, col=1)
                fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart["EMA200"], line=dict(color="#F59E0B", width=2.3), name="EMA 200"), row=1, col=1)

                fig.add_hline(y=selected_data["الإغلاق"], line_dash="dot", line_color="#FFFFFF", annotation_text="Entry", row=1, col=1)
                fig.add_hline(y=selected_data["الوقف (2xATR)"], line_dash="dash", line_color="#F87171", annotation_text="SL", row=1, col=1)
                fig.add_hline(y=selected_data["TP1"], line_dash="dash", line_color="#4ADE80", annotation_text="TP1", row=1, col=1)
                fig.add_hline(y=selected_data["TP2"], line_dash="dash", line_color="#10B981", annotation_text="TP2", row=1, col=1)

                vol_colors = ["#4ADE80" if c >= o else "#F87171" for c, o in zip(df_chart["Close"], df_chart["Open"])]
                fig.add_trace(go.Bar(x=df_chart.index, y=df_chart["Volume"], marker_color=vol_colors, name="الفوليوم"), row=2, col=1)
                fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart["VolSMA20"], line=dict(color="#F59E0B", width=1.4), name="متوسط الفوليوم 20"), row=2, col=1)

                fig.update_layout(
                    title=dict(text=f"📈 الشارت الفني ومستويات التنفيذ: {selected_symbol}", font=dict(color="#FFFFFF", size=16)),
                    height=540, xaxis_rangeslider_visible=False, template="plotly_dark",
                    paper_bgcolor="#0B0F19", plot_bgcolor="#131C31", font=dict(color="#FFFFFF"),
                    margin=dict(l=10, r=10, t=45, b=10),
                    legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="right", x=1, font=dict(color="#FFFFFF"))
                )
                st.plotly_chart(fig, use_container_width=True)

            with c_plan:
                st.markdown(f"""
                <div class="pro-card">
                    <h4 class="txt-cyan" style="margin-top:0;">📌 خطة التنفيذ: {selected_symbol}</h4>
                    <p><span class="badge-bull">{selected_data['نوع الإشارة']}</span> &nbsp; <b class="txt-white">السكور: {selected_data['السكور']}/100</b></p>
                    <p class="txt-muted" style="font-size:13px;"><b class="txt-white">التشخيص:</b> {selected_data['التشخيص الفني']}</p>
                    <hr style="border-color:#26334D;">
                    <p class="txt-white"><b>سعر الدخول المرجعي:</b> {selected_data['الإغلاق']} ج.م</p>
                    <p class="txt-white"><b>وقف الخسارة (2×ATR):</b> <span class="txt-red" style="font-weight:bold;">{selected_data['الوقف (2xATR)']} ج.م</span></p>
                    <p class="txt-white"><b>الهدف الأول TP1:</b> <span class="txt-green" style="font-weight:bold;">{selected_data['TP1']} ج.م</span></p>
                    <p class="txt-white"><b>الهدف الثاني TP2:</b> <span class="txt-green" style="font-weight:bold;">{selected_data['TP2']} ج.م</span></p>
                    <p class="txt-white"><b>الهدف الثالث TP3:</b> <span class="txt-green" style="font-weight:bold;">{selected_data['TP3']} ج.م</span></p>
                    <hr style="border-color:#26334D;">
                    <p class="txt-white"><b>حجم الصفقة المقترح:</b> {selected_data['الأسهم']:,} سهم ({selected_data['قيمة الصفقة']:,.0f} ج.م)</p>
                    <p class="txt-white"><b>صافي ربح TP1:</b> <span class="txt-green" style="font-weight:bold;">{selected_data['صافي TP1']:,.0f} ج.م</span></p>
                </div>
                """, unsafe_allow_html=True)

                parts = selected_data["score_parts"]
                fig_score = go.Figure(go.Bar(
                    x=list(parts.values()), y=list(parts.keys()), orientation="h",
                    marker_color=["#F59E0B", "#38BDF8", "#A855F7", "#4ADE80"],
                    text=[f"{v} نقطة" for v in parts.values()], textposition="auto", textfont=dict(color="#FFFFFF")
                ))
                fig_score.update_layout(
                    title=dict(text="🧩 تفكيك نقاط السكور", font=dict(color="#FFFFFF", size=14)),
                    height=210, template="plotly_dark", paper_bgcolor="#131C31", plot_bgcolor="#131C31",
                    font=dict(color="#FFFFFF"), xaxis=dict(range=[0, 40], showgrid=False, visible=False),
                    margin=dict(l=10, r=10, t=35, b=10)
                )
                st.plotly_chart(fig_score, use_container_width=True)
                st.link_button("🚀 افتح على TradingView ↗", selected_data["TradingView"], use_container_width=True)

    elif "التحليل المالي" in sub_view:
        st.markdown(f"#### 📊 التحليل المالي والأساسي (Piotroski F-Score): {selected_symbol}")
        with st.spinner("⏳ جاري استخراج القوائم المالية ومؤشرات التقييم..."):
            fund_data = fetch_fundamental_analysis(selected_data["Ticker"])

        if "error" in fund_data:
            st.warning("⚠️ تعذر جلب البيانات المالية التفصيلية لهذا السهم من Yahoo Finance.")
        else:
            f_col1, f_col2 = st.columns([1, 1.5])
            with f_col1:
                pe_txt = f"{fund_data['pe']:.1f}x" if fund_data.get("pe") else "غير متاح"
                pb_txt = f"{fund_data['pb']:.2f}x" if fund_data.get("pb") else "غير متاح"
                roe_txt = f"{fund_data['roe']*100:.1f}%" if fund_data.get("roe") else "غير متاح"
                div_txt = f"{fund_data['div_yield']*100:.1f}%" if fund_data.get("div_yield") else "لا يوجد / غير متاح"
                mcap_txt = f"{fund_data['market_cap']/1e9:,.2f} مليار ج.م" if fund_data.get("market_cap") else "غير متاح"

                avail = fund_data["tests_available"]
                f_val = fund_data["f_score"]
                f_badge = "badge-bull" if (avail > 0 and f_val / avail >= 0.7) else ("badge-bear" if (avail > 0 and f_val / avail <= 0.35) else "badge-warn")

                st.markdown(f"""
                <div class="pro-card">
                    <h4 class="txt-cyan" style="margin-top:0;">🏢 بطاقة الشركة والتقييم</h4>
                    <p class="txt-white"><b>الاسم:</b> {fund_data['name']}</p>
                    <p class="txt-white"><b>القطاع:</b> {fund_data['sector']} ({fund_data['industry']})</p>
                    <p class="txt-white"><b>القيمة السوقية:</b> {mcap_txt}</p>
                    <hr style="border-color:#26334D;">
                    <p class="txt-white"><b>درجة المتانة المالية:</b> <span class="{f_badge}">{f_val} / {avail} اختبارات متاحة</span></p>
                    <p class="txt-white"><b>مكرر الربحية (P/E):</b> {pe_txt}</p>
                    <p class="txt-white"><b>مضاعف القيمة الدفترية (P/B):</b> {pb_txt}</p>
                    <p class="txt-white"><b>العائد على حقوق الملكية (ROE):</b> {roe_txt}</p>
                    <p class="txt-white"><b>عائد التوزيعات النقدية:</b> {div_txt}</p>
                </div>
                """, unsafe_allow_html=True)

            with f_col2:
                st.markdown("##### 🧾 تفصيل اختبارات Piotroski F-Score من القوائم المالية")
                if fund_data["breakdown"]:
                    df_f = pd.DataFrame(fund_data["breakdown"], columns=["المعيار المالي", "القيمة", "النتيجة"])
                    df_f["النتيجة"] = df_f["النتيجة"].map({True: "✅ ناجح (+1)", False: "❌ لم يتحقق (0)"})
                    st.dataframe(df_f, use_container_width=True, hide_index=True)
                else:
                    st.info("ℹ️ القوائم المالية التفصيلية غير مكتملة لهذا الرمز في قاعدة بيانات Yahoo Finance.")

    elif "التحليل الزمني" in sub_view:
        if not has_hist_df:
            st.info(f"ℹ️ السهم **{selected_symbol}** حديث الإدراج ولا يمتلك تاريخاً سعرياً كافياً لرسم خريطة جان بعد.")
        else:
            st.markdown(f"#### 🪐 التحليل الزمني والفلكي (Gann Squaring + Planetary Cycles): {selected_symbol}")
            df_time = selected_data["df"].copy()
            curr_p = selected_data["الإغلاق"]

            recent_90 = df_time.tail(90)
            auto_low_idx = recent_90["Low"].idxmin()
            auto_low_price = float(recent_90.loc[auto_low_idx, "Low"])
            auto_low_date = auto_low_idx.date()

            auto_high_idx = recent_90["High"].idxmax()
            auto_high_price = float(recent_90.loc[auto_high_idx, "High"])
            auto_high_date = auto_high_idx.date()

            g_col1, g_col2, g_col3, g_col4 = st.columns([1.2, 1, 1, 1.2])
            with g_col1:
                pivot_mode = st.selectbox(
                    "📍 نقطة الارتكاز لحسابات جان:",
                    options=[
                        f"أقل قاع (90 جلسة): {auto_low_price:.2f} ({auto_low_date})",
                        f"أعلى قمة (90 جلسة): {auto_high_price:.2f} ({auto_high_date})",
                        "إدخال قاع/قمة مخصصة يدوياً"
                    ]
                )
            with g_col2:
                if "أقل قاع" in pivot_mode:
                    piv_date = st.date_input("تاريخ الارتكاز", value=auto_low_date, disabled=True)
                    piv_price = auto_low_price
                    is_piv_low = True
                elif "أعلى قمة" in pivot_mode:
                    piv_date = st.date_input("تاريخ الارتكاز", value=auto_high_date, disabled=True)
                    piv_price = auto_high_price
                    is_piv_low = False
                else:
                    piv_date = st.date_input("تاريخ الارتكاز المخصص", value=auto_low_date)
            with g_col3:
                if "مخصصة" in pivot_mode:
                    piv_price = st.number_input("سعر الارتكاز المخصص", min_value=0.01, value=auto_low_price, step=0.1)
                    is_piv_low = st.radio("نوع الارتكاز:", ["قاع (صاعد)", "قمة (هابط)"], horizontal=True) == "قاع (صاعد)"
                else:
                    st.metric("سعر الارتكاز المعتمد", f"{piv_price:.2f} ج.م")
            with g_col4:
                day_type = st.radio(
                    "⏱️ وحدة الزمن:",
                    options=["أيام تقويمية (Calendar)", "جلسات تداول مصرية (Trading)"],
                    index=0
                )
                use_trading = "جلسات" in day_type

            sq9_list, gann_time_list, planetary_aspects = compute_gann_and_planetary(
                pivot_date=piv_date, pivot_price=piv_price, is_pivot_low=is_piv_low,
                current_price=curr_p, use_trading_days=use_trading
            )

            today_dt = get_cairo_now().replace(tzinfo=None)
            today_planets = get_planetary_longitudes(today_dt)
            planet_rows = []
            for p_name, deg_val in today_planets.items():
                p_price = convert_deg_to_price(deg_val, curr_p)
                dist_pct = ((p_price - curr_p) / curr_p) * 100
                planet_rows.append({
                    "الجرم السماوي": p_name,
                    "الدرجة الفلكية": f"{deg_val:.1f}°",
                    "البرج الفلكي": deg_to_zodiac(deg_val),
                    "خط السعر الفلكي": p_price,
                    "البعد عن السعر %": f"{dist_pct:+.1f}%"
                })

            fig_gann = go.Figure()
            df_g_chart = df_time.tail(100)
            fig_gann.add_trace(go.Candlestick(
                x=df_g_chart.index, open=df_g_chart["Open"], high=df_g_chart["High"],
                low=df_g_chart["Low"], close=df_g_chart["Close"], name="السعر"
            ))

            for item in sq9_list[:4]:
                fig_gann.add_hline(y=item["المستوى السعري"], line_dash="dot", line_color="#FACC15", annotation_text=f"Gann {item['الزاوية']}: {item['المستوى السعري']}", annotation_font_color="#FACC15")

            for prow in planet_rows:
                if any(k in prow["الجرم السماوي"] for k in ["الشمس", "المشتري", "زحل"]):
                    fig_gann.add_hline(y=prow["خط السعر الفلكي"], line_dash="dashdot", line_color="#C084FC", annotation_text=f"{prow['الجرم السماوي']}: {prow['خط السعر الفلكي']}", annotation_font_color="#C084FC")

            for t_item in gann_time_list[:4]:
                dt_str = str(t_item["تاريخ الانعكاس المتوقع"])
                fig_gann.add_shape(type="line", x0=dt_str, x1=dt_str, y0=0, y1=1, yref="paper", line=dict(color="#38BDF8", width=1.8, dash="dash"))
                fig_gann.add_annotation(x=dt_str, y=0.98, yref="paper", text=f"⏳ {t_item['الدورة / المعادلة']}", showarrow=False, font=dict(color="#38BDF8", size=11), bgcolor="#0B0F19")

            for asp in planetary_aspects[:3]:
                dt_str = str(asp["التاريخ"])
                fig_gann.add_shape(type="line", x0=dt_str, x1=dt_str, y0=0, y1=1, yref="paper", line=dict(color="#4ADE80", width=1.5, dash="dot"))
                fig_gann.add_annotation(x=dt_str, y=0.06, yref="paper", text=f"🪐 {asp['الزاوية الفلكية']}", showarrow=False, font=dict(color="#4ADE80", size=11), bgcolor="#0B0F19")

            fig_gann.update_layout(
                title=dict(text=f"🧭 خريطة الزمن والسعر (جان + الكواكب): {selected_symbol}", font=dict(color="#FFFFFF", size=15)),
                height=480, xaxis_rangeslider_visible=False, template="plotly_dark",
                paper_bgcolor="#0B0F19", plot_bgcolor="#131C31", font=dict(color="#FFFFFF"),
                margin=dict(l=10, r=10, t=45, b=10)
            )
            st.plotly_chart(fig_gann, use_container_width=True)

            gp_col1, gp_col2 = st.columns(2)
            with gp_col1:
                st.markdown("##### 📐 معادلات جان (تربيع الزمن + مربع التسعة)")
                if gann_time_list:
                    st.dataframe(pd.DataFrame(gann_time_list)[["الدورة / المعادلة", "تاريخ الانعكاس المتوقع", "الحالة الزمنية"]], use_container_width=True, hide_index=True)
                st.dataframe(pd.DataFrame(sq9_list), use_container_width=True, hide_index=True)
            with gp_col2:
                st.markdown("##### 🪐 مواقع الكواكب اليوم وخطوطها السعرية")
                st.dataframe(pd.DataFrame(planet_rows), use_container_width=True, hide_index=True)
                st.markdown("##### ✨ رادار الزوايا الفلكية القادمة (30 يوماً)")
                if planetary_aspects:
                    st.dataframe(pd.DataFrame(planetary_aspects), use_container_width=True, hide_index=True)

    elif "الرادار الخبري" in sub_view:
        st.markdown(f"#### 📰 الرادار الخبري وتحليل المشاعر: {selected_symbol}")
        with st.spinner("🔍 جاري البحث عن أحدث الأخبار وتحليل المشاعر..."):
            news_items = fetch_stock_news(selected_symbol)

        if not news_items:
            st.info("ℹ️ لم يتم العثور على أخبار حديثة منشورة لهذا السهم في المصادر المفتوحة حالياً.")
        else:
            net_sentiment = sum(n["score"] for n in news_items)
            sent_summary = "إيجابي إجمالاً 🟢" if net_sentiment > 0 else ("سلبي إجمالاً 🔴" if net_sentiment < 0 else "محايد / متوازن ⚪")
            st.markdown(f"**📊 محصلة المشاعر الإخبارية للسهم:** {sent_summary} (من إجمالي {len(news_items)} خبر مرصود)")
            st.write("")
            for n in news_items:
                st.markdown(f"""
                <div class="news-item">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
                        <span class="{n['badge']}">{n['sentiment']}</span>
                        <span class="txt-muted" style="font-size:12px;">{n['source']}</span>
                    </div>
                    <a href="{n['link']}" target="_blank" class="txt-white" style="text-decoration:none;font-size:15px;font-weight:700;">
                        {n['title']} ↗
                    </a>
                </div>
                """, unsafe_allow_html=True)