import os
import re
import math
import json
import time
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
    page_title="EGX Whale Hunter Pro V8.5",
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
# التوقيت المحلي للقاهرة وحساب تقدم الجلسة
# ==========================================
def get_cairo_now() -> datetime:
    try:
        return datetime.now(ZoneInfo("Africa/Cairo"))
    except Exception:
        return datetime.now(timezone(timedelta(hours=2)))

def get_egx_session_metrics() -> dict:
    now_cairo = get_cairo_now()
    weekday = now_cairo.weekday()
    is_trading_day = weekday in [6, 0, 1, 2, 3]
    current_minutes = now_cairo.hour * 60 + now_cairo.minute
    start_m = 10 * 60        # 10:00 AM
    end_m = 14 * 60 + 30     # 02:30 PM (270 دقيقة)

    if is_trading_day and (start_m <= current_minutes <= end_m):
        elapsed = current_minutes - start_m
        effective_elapsed = max(12.0, float(elapsed))
        progress = min(1.0, effective_elapsed / 270.0)
        return {
            "is_open": True,
            "elapsed_mins": elapsed,
            "progress": progress,
            "badge": f"🟢 الجلسة مفتوحة ({now_cairo.strftime('%H:%M')} • مضى {elapsed} د من 270)"
        }
    return {
        "is_open": False,
        "elapsed_mins": 270,
        "progress": 1.0,
        "badge": f"🌙 الجلسة مغلقة ({now_cairo.strftime('%H:%M')} القاهرة)"
    }

def _safe_f(arr, idx: int, default: float = 0.0) -> float:
    if len(arr) > idx and arr[idx] is not None:
        try:
            val = float(arr[idx])
            return val if not math.isnan(val) else default
        except Exception:
            return default
    return default

def get_secret_safe(key_name: str) -> str:
    try:
        val = st.secrets.get(key_name, "")
        if val:
            return str(val).strip()
    except Exception:
        pass
    return str(os.environ.get(key_name, "")).strip()

# ==========================================
# محرك المزامنة السحابية (Supabase REST API + نسخة محلية احتياطية)
# ==========================================
PORTFOLIO_FILE = "my_egx_portfolio.json"
TRADES_FILE = "my_egx_trades_history.json"
TG_LOG_FILE = "tg_alerts_log.json"

def get_supabase_creds() -> tuple:
    url = st.session_state.get("sb_url_val", get_secret_safe("SUPABASE_URL")).strip().rstrip("/")
    key = st.session_state.get("sb_key_val", get_secret_safe("SUPABASE_KEY")).strip()
    return url, key

def _sb_request(method: str, endpoint: str, payload=None, extra_headers: dict = None) -> tuple:
    sb_url, sb_key = get_supabase_creds()
    if not sb_url or not sb_key:
        return False, "بيانات Supabase غير مُدخلة"
    full_url = f"{sb_url}/rest/v1/{endpoint}"
    headers = {
        "apikey": sb_key,
        "Authorization": f"Bearer {sb_key}",
        "Content-Type": "application/json",
    }
    if extra_headers:
        headers.update(extra_headers)
    data_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8") if payload is not None else None
    try:
        req = urllib.request.Request(full_url, data=data_bytes, headers=headers, method=method)
        with urllib.request.urlopen(req, timeout=8) as resp:
            raw = resp.read().decode("utf-8")
            return True, (json.loads(raw) if raw else [])
    except Exception as e:
        return False, str(e)

def test_supabase_connection() -> tuple:
    ok, res = _sb_request("GET", "egx_portfolio?select=symbol&limit=1")
    if ok:
        return True, "✅ متصل بقاعدة بيانات Supabase السحابية بنجاح!"
    return False, f"❌ تعذر الاتصال بـ Supabase: {res}"

def _save_local_portfolio_cache(portfolio_list: list):
    st.session_state["my_portfolio"] = portfolio_list
    try:
        with open(PORTFOLIO_FILE, "w", encoding="utf-8") as f:
            json.dump(portfolio_list, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def _load_local_portfolio_file() -> list:
    if os.path.exists(PORTFOLIO_FILE):
        try:
            with open(PORTFOLIO_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
        except Exception:
            pass
    return []

def load_portfolio(force_cloud_refresh: bool = False) -> tuple:
    sb_url, sb_key = get_supabase_creds()
    has_creds = bool(sb_url and sb_key)

    if not force_cloud_refresh and "my_portfolio" in st.session_state:
        return st.session_state["my_portfolio"], st.session_state.get("cloud_sync_ok", False)

    if has_creds:
        ok, res = _sb_request(
            "GET",
            "egx_portfolio?select=symbol,shares,buy_price,stop_loss,tp1,tp2,trailing_enabled,trailing_stage&order=symbol.asc"
        )
        if not ok:
            ok, res = _sb_request("GET", "egx_portfolio?select=symbol,shares,buy_price,stop_loss,tp1,tp2&order=symbol.asc")
        if ok and isinstance(res, list):
            cleaned = []
            for row in res:
                sym = str(row.get("symbol", "")).upper().replace(".CA", "").strip()
                if sym:
                    cleaned.append({
                        "symbol": sym,
                        "shares": int(row.get("shares", 0)),
                        "buy_price": float(row.get("buy_price", 0.0)),
                        "stop_loss": float(row.get("stop_loss", 0.0)),
                        "tp1": float(row.get("tp1", 0.0)),
                        "tp2": float(row.get("tp2", 0.0)),
                        "trailing_enabled": bool(row.get("trailing_enabled", True)),
                        "trailing_stage": int(row.get("trailing_stage", 0)),
                    })
            st.session_state["cloud_sync_ok"] = True
            _save_local_portfolio_cache(cleaned)
            return cleaned, True

    st.session_state["cloud_sync_ok"] = False
    local_data = _load_local_portfolio_file()
    st.session_state["my_portfolio"] = local_data
    return local_data, False

def upsert_portfolio_item(item: dict) -> tuple:
    clean_sym = re.sub(r"[^A-Z0-9]", "", str(item["symbol"]).upper().replace(".CA", ""))
    record = {
        "symbol": clean_sym,
        "shares": int(item.get("shares", 0)),
        "buy_price": float(item.get("buy_price", 0.0)),
        "stop_loss": float(item.get("stop_loss", 0.0)),
        "tp1": float(item.get("tp1", 0.0)),
        "tp2": float(item.get("tp2", 0.0)),
        "trailing_enabled": bool(item.get("trailing_enabled", True)),
        "trailing_stage": int(item.get("trailing_stage", 0)),
    }

    current_list = [p for p in st.session_state.get("my_portfolio", []) if p["symbol"].upper().replace(".CA", "").strip() != clean_sym]
    current_list.append(record)
    _save_local_portfolio_cache(current_list)

    sb_url, sb_key = get_supabase_creds()
    if sb_url and sb_key:
        ok, err = _sb_request(
            "POST",
            "egx_portfolio?on_conflict=symbol",
            payload=record,
            extra_headers={"Prefer": "resolution=merge-duplicates,return=minimal"}
        )
        if not ok:
            base_rec = {k: v for k, v in record.items() if k not in ["trailing_enabled", "trailing_stage"]}
            ok, err = _sb_request(
                "POST",
                "egx_portfolio?on_conflict=symbol",
                payload=base_rec,
                extra_headers={"Prefer": "resolution=merge-duplicates,return=minimal"}
            )
        if ok:
            st.session_state["cloud_sync_ok"] = True
            return True, "☁️ محفوظ سحابياً"
        return False, f"⚠️ حُفظ محلياً فقط (خطأ سحابي: {err})"
    return True, "💾 محفوظ محلياً"

def delete_portfolio_item(symbol: str) -> tuple:
    clean_sym = re.sub(r"[^A-Z0-9]", "", str(symbol).upper().replace(".CA", ""))
    current_list = [p for p in st.session_state.get("my_portfolio", []) if p["symbol"].upper().replace(".CA", "").strip() != clean_sym]
    _save_local_portfolio_cache(current_list)

    sb_url, sb_key = get_supabase_creds()
    if sb_url and sb_key:
        ok, err = _sb_request("DELETE", f"egx_portfolio?symbol=eq.{urllib.parse.quote(clean_sym)}")
        if ok:
            st.session_state["cloud_sync_ok"] = True
            return True, "☁️ تم الحذف من السحابة"
        return False, f"⚠️ حُذف محلياً فقط ({err})"
    return True, "💾 تم الحذف محلياً"

def sync_full_portfolio_to_cloud(portfolio_list: list) -> tuple:
    sb_url, sb_key = get_supabase_creds()
    if not sb_url or not sb_key:
        return False, "أدخل بيانات Supabase أولاً"
    records = []
    for p in portfolio_list:
        clean_sym = re.sub(r"[^A-Z0-9]", "", str(p.get("symbol", "")).upper().replace(".CA", ""))
        if clean_sym and int(p.get("shares", 0)) > 0:
            records.append({
                "symbol": clean_sym,
                "shares": int(p["shares"]),
                "buy_price": float(p["buy_price"]),
                "stop_loss": float(p.get("stop_loss", 0.0)),
                "tp1": float(p.get("tp1", 0.0)),
                "tp2": float(p.get("tp2", 0.0)),
                "trailing_enabled": bool(p.get("trailing_enabled", True)),
                "trailing_stage": int(p.get("trailing_stage", 0)),
            })
    if not records:
        _save_local_portfolio_cache([])
        return True, "المحفظة فارغة"
    ok, err = _sb_request(
        "POST",
        "egx_portfolio?on_conflict=symbol",
        payload=records,
        extra_headers={"Prefer": "resolution=merge-duplicates,return=minimal"}
    )
    if not ok:
        base_recs = [{k: v for k, v in r.items() if k not in ["trailing_enabled", "trailing_stage"]} for r in records]
        ok, err = _sb_request(
            "POST",
            "egx_portfolio?on_conflict=symbol",
            payload=base_recs,
            extra_headers={"Prefer": "resolution=merge-duplicates,return=minimal"}
        )
    if ok:
        st.session_state["cloud_sync_ok"] = True
        _save_local_portfolio_cache(records)
        return True, f"✅ تمت مزامنة {len(records)} أسهم إلى السحابة بنجاح!"
    return False, f"❌ فشلت المزامنة: {err}"

# ==========================================
# سجل الصفقات المغلقة (Closed Trades Journal)
# ==========================================
def load_closed_trades(force_refresh: bool = False) -> list:
    if not force_refresh and "closed_trades_list" in st.session_state:
        return st.session_state["closed_trades_list"]

    trades = []
    sb_url, sb_key = get_supabase_creds()
    if sb_url and sb_key:
        ok, res = _sb_request(
            "GET",
            "egx_trades_history?select=symbol,shares,buy_price,sell_price,net_pnl,pnl_pct,closed_at&order=closed_at.desc&limit=100"
        )
        if ok and isinstance(res, list):
            trades = res
            st.session_state["closed_trades_list"] = trades
            try:
                with open(TRADES_FILE, "w", encoding="utf-8") as f:
                    json.dump(trades, f, ensure_ascii=False, indent=2)
            except Exception:
                pass
            return trades

    if os.path.exists(TRADES_FILE):
        try:
            with open(TRADES_FILE, "r", encoding="utf-8") as f:
                local_t = json.load(f)
                if isinstance(local_t, list):
                    trades = local_t
        except Exception:
            pass
    st.session_state["closed_trades_list"] = trades
    return trades

def record_closed_trade(symbol: str, shares: int, buy_price: float, sell_price: float, fee_rate: float) -> tuple:
    cost = shares * buy_price
    proceeds = shares * sell_price
    fees = (cost + proceeds) * fee_rate
    net_pnl = round((proceeds - cost) - fees, 2)
    pnl_pct = round((net_pnl / max(0.01, cost)) * 100.0, 2)
    now_iso = get_cairo_now().isoformat()

    trade_rec = {
        "symbol": symbol,
        "shares": int(shares),
        "buy_price": float(buy_price),
        "sell_price": float(sell_price),
        "net_pnl": net_pnl,
        "pnl_pct": pnl_pct,
        "closed_at": now_iso,
    }

    existing = load_closed_trades(force_refresh=False)
    updated_list = [trade_rec] + existing
    st.session_state["closed_trades_list"] = updated_list
    try:
        with open(TRADES_FILE, "w", encoding="utf-8") as f:
            json.dump(updated_list, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

    sb_url, sb_key = get_supabase_creds()
    if sb_url and sb_key:
        _sb_request(
            "POST",
            "egx_trades_history",
            payload=trade_rec,
            extra_headers={"Prefer": "return=minimal"}
        )

    delete_portfolio_item(symbol)
    return net_pnl, pnl_pct

# ==========================================
# سجل إشعارات التليجرام السحابي
# ==========================================
def load_sent_tg_log(today_str: str, force_refresh: bool = False) -> dict:
    if not force_refresh and "sent_tg_alerts" in st.session_state:
        return st.session_state["sent_tg_alerts"]

    log_map = {}
    if os.path.exists(TG_LOG_FILE):
        try:
            with open(TG_LOG_FILE, "r", encoding="utf-8") as f:
                local_d = json.load(f)
                if isinstance(local_d, dict):
                    log_map.update(local_d)
        except Exception:
            pass

    sb_url, sb_key = get_supabase_creds()
    if sb_url and sb_key:
        q_prefix = urllib.parse.quote(f"{today_str}%")
        ok, res = _sb_request("GET", f"egx_alerts_log?select=alert_key,sent_time&alert_key=like.{q_prefix}")
        if ok and isinstance(res, list):
            for row in res:
                if row.get("alert_key"):
                    log_map[row["alert_key"]] = row.get("sent_time", "")

    st.session_state["sent_tg_alerts"] = log_map
    return log_map

def record_sent_tg_alert(alert_key: str, sent_time: str, current_log: dict):
    current_log[alert_key] = sent_time
    st.session_state["sent_tg_alerts"] = current_log
    try:
        with open(TG_LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(current_log, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

    sb_url, sb_key = get_supabase_creds()
    if sb_url and sb_key:
        _sb_request(
            "POST",
            "egx_alerts_log?on_conflict=alert_key",
            payload={"alert_key": alert_key, "sent_time": sent_time},
            extra_headers={"Prefer": "resolution=merge-duplicates,return=minimal"}
        )

# ==========================================
# محرك موجات إليوت (ZigZag + قواعد إليوت + أهداف فيبوناتشي)
# ==========================================
def detect_zigzag_pivots(df: pd.DataFrame, pct_thresh: float = 0.05) -> list:
    if df is None or len(df) < 15:
        return []

    highs = df["High"].values
    lows = df["Low"].values
    dates = df.index

    pivots = []
    trend = 0
    last_idx = 0
    last_price = float(lows[0])

    init_high = float(highs[0])
    init_low = float(lows[0])
    init_h_idx = 0
    init_l_idx = 0

    start_i = 1
    for i in range(1, len(df)):
        h = float(highs[i])
        l = float(lows[i])
        if h > init_high:
            init_high = h
            init_h_idx = i
        if l < init_low:
            init_low = l
            init_l_idx = i

        if init_high >= init_low * (1.0 + pct_thresh):
            if init_h_idx > init_l_idx:
                pivots.append({"idx": init_l_idx, "date": dates[init_l_idx], "price": init_low, "type": "L"})
                trend = 1
                last_idx = init_h_idx
                last_price = init_high
            else:
                pivots.append({"idx": init_h_idx, "date": dates[init_h_idx], "price": init_high, "type": "H"})
                trend = -1
                last_idx = init_l_idx
                last_price = init_low
            start_i = i + 1
            break

    if trend == 0:
        return []

    for i in range(start_i, len(df)):
        h = float(highs[i])
        l = float(lows[i])
        if trend == 1:
            if h >= last_price:
                last_price = h
                last_idx = i
            elif l <= last_price * (1.0 - pct_thresh):
                pivots.append({"idx": last_idx, "date": dates[last_idx], "price": last_price, "type": "H"})
                trend = -1
                last_price = l
                last_idx = i
        else:
            if l <= last_price:
                last_price = l
                last_idx = i
            elif h >= last_price * (1.0 + pct_thresh):
                pivots.append({"idx": last_idx, "date": dates[last_idx], "price": last_price, "type": "L"})
                trend = 1
                last_price = h
                last_idx = i

    pivots.append({
        "idx": last_idx,
        "date": dates[last_idx],
        "price": last_price,
        "type": "H" if trend == 1 else "L",
        "active": True
    })
    return pivots


def analyze_elliott_waves(df: pd.DataFrame, pct_thresh: float = 0.05) -> dict:
    pivots = detect_zigzag_pivots(df, pct_thresh=pct_thresh)
    curr_close = float(df["Close"].iloc[-1])

    if len(pivots) < 4:
        return {
            "status": "insufficient",
            "wave_name": "⚪ بيانات غير كافية للترقيم",
            "pattern_type": "غير محدد",
            "badge_cls": "badge-warn",
            "invalidation": round(curr_close * 0.9, 2),
            "target_1": round(curr_close * 1.1, 2),
            "target_2": round(curr_close * 1.2, 2),
            "summary": "جرب تقليل نسبة حساسية الموجات (مثلاً 3%) لإظهار الموجات الفرعية.",
            "rules_check": [],
            "labeled_pivots": []
        }

    if len(pivots) >= 5 and pivots[-5]["type"] == "L":
        p0, p1, p2, p3, p4 = pivots[-5], pivots[-4], pivots[-3], pivots[-2], pivots[-1]
        w1 = p1["price"] - p0["price"]
        w3 = p3["price"] - p2["price"]
        rule1 = p2["price"] > p0["price"]
        rule2 = (p3["price"] > p1["price"]) and (w3 >= w1 * 0.85)
        rule3 = p4["price"] > p1["price"]

        if w1 > 0 and rule1 and rule2 and rule3:
            t1 = round(p4["price"] + w1, 2)
            t2 = round(p4["price"] + 0.618 * (p3["price"] - p0["price"]), 2)
            inv = round(p1["price"], 2)
            if curr_close > p4["price"] * 1.015:
                w_name = "🌊 الموجة الخامسة الصاعدة (Wave 5)"
                summary = f"أنهى السهم تصحيح الموجة الرابعة عند ({p4['price']:.2f}) وبدأ الانطلاق في الموجة الخامسة الأخيرة نحو ({t1}) ثم ({t2})."
                b_cls = "badge-bull"
            else:
                w_name = "⏳ الموجة الرابعة التصحيحية (Wave 4)"
                summary = f"السهم في استراحة جني أرباح ضمن الموجة الرابعة؛ الثبات أعلى قمة الأولى ({inv}) يبقي سيناريو الموجة الخامسة الصاعدة قائماً."
                b_cls = "badge-warn"

            labels = ["(0)", "(1)", "(2)", "(3)", "(4)"]
            labeled = [dict(p, label=lbl) for p, lbl in zip([p0, p1, p2, p3, p4], labels)]
            return {
                "status": "ok",
                "wave_name": w_name,
                "pattern_type": "موجة دافعة صاعدة (Bullish Impulse 1-5)",
                "badge_cls": b_cls,
                "invalidation": inv,
                "target_1": t1,
                "target_2": max(t1, t2),
                "summary": summary,
                "rules_check": [
                    ("1. الموجة (2) لم تكسر بداية (1)", f"{p2['price']:.2f} > {p0['price']:.2f}", True),
                    ("2. الموجة (3) ممتدة وليست الأقصر", f"طول (3) = {w3:.2f} مقابل (1) = {w1:.2f}", True),
                    ("3. الموجة (4) لم تتداخل مع قمة (1)", f"{p4['price']:.2f} > {p1['price']:.2f}", True),
                ],
                "labeled_pivots": labeled
            }

    if len(pivots) >= 6 and pivots[-6]["type"] == "L":
        p0, p1, p2, p3, p4, p5 = pivots[-6], pivots[-5], pivots[-4], pivots[-3], pivots[-2], pivots[-1]
        w1 = p1["price"] - p0["price"]
        w3 = p3["price"] - p2["price"]
        w5 = p5["price"] - p4["price"]
        if w1 > 0 and p2["price"] > p0["price"] and p3["price"] > p1["price"] and p4["price"] > p1["price"] and p5["price"] > p3["price"]:
            if curr_close < p5["price"] * 0.985:
                t1 = round(p5["price"] - 0.382 * (p5["price"] - p0["price"]), 2)
                t2 = round(p4["price"], 2)
                inv = round(p5["price"], 2)
                labels = ["(0)", "(1)", "(2)", "(3)", "(4)", "(5) / بداية A"]
                labeled = [dict(p, label=lbl) for p, lbl in zip([p0, p1, p2, p3, p4, p5], labels)]
                return {
                    "status": "ok",
                    "wave_name": "🔻 بداية الموجة التصحيحية (Wave A)",
                    "pattern_type": "اكتمال 5 موجات صاعدة → تصحيح (A-B-C)",
                    "badge_cls": "badge-bear",
                    "invalidation": inv,
                    "target_1": t1,
                    "target_2": t2,
                    "summary": f"أكمل السهم 5 موجات دافعة صاعدة عند القمة ({p5['price']:.2f}) وبدأ موجة جني أرباح تصحيحية (A) تستهدف مناطق ({t1}) ثم قاع الرابعة ({t2}).",
                    "rules_check": [
                        ("1. الموجة (2) فوق بداية (1)", f"{p2['price']:.2f} > {p0['price']:.2f}", True),
                        ("2. الموجة (3) ليست الأقصر", f"طول (3)={w3:.2f} | (1)={w1:.2f} | (5)={w5:.2f}", w3 >= min(w1, w5)),
                        ("3. عدم تداخل (4) مع (1)", f"{p4['price']:.2f} > {p1['price']:.2f}", True),
                    ],
                    "labeled_pivots": labeled
                }
            else:
                t1 = round(p4["price"] + w1, 2)
                t2 = round(p4["price"] + 1.618 * w1, 2)
                inv = round(p4["price"], 2)
                labels = ["(0)", "(1)", "(2)", "(3)", "(4)", "(5) نشطة"]
                labeled = [dict(p, label=lbl) for p, lbl in zip([p0, p1, p2, p3, p4, p5], labels)]
                return {
                    "status": "ok",
                    "wave_name": "🚀 الموجة الخامسة الدافعة (Wave 5 نشطة)",
                    "pattern_type": "موجة دافعة صاعدة (Bullish Impulse 1-5)",
                    "badge_cls": "badge-bull",
                    "invalidation": inv,
                    "target_1": max(t1, round(p5["price"] * 1.03, 2)),
                    "target_2": max(t2, round(p5["price"] * 1.08, 2)),
                    "summary": f"السهم يتداول في قمة الموجة الخامسة الصاعدة؛ يُنصح برفع وقف حماية الأرباح أسفل قاع الرابعة ({inv}).",
                    "rules_check": [
                        ("1. الموجة (2) فوق بداية (1)", f"{p2['price']:.2f} > {p0['price']:.2f}", True),
                        ("2. الموجة (3) ليست الأقصر", f"طول (3)={w3:.2f} | (1)={w1:.2f} | (5)={w5:.2f}", w3 >= min(w1, w5)),
                        ("3. عدم تداخل (4) مع (1)", f"{p4['price']:.2f} > {p1['price']:.2f}", True),
                    ],
                    "labeled_pivots": labeled
                }

    if len(pivots) >= 4 and pivots[-4]["type"] == "L":
        p0, p1, p2, p3 = pivots[-4], pivots[-3], pivots[-2], pivots[-1]
        w1 = p1["price"] - p0["price"]
        w3 = p3["price"] - p2["price"]
        if w1 > 0 and p2["price"] > p0["price"] and p3["price"] > p1["price"]:
            t1 = round(p2["price"] + 1.618 * w1, 2)
            t2 = round(p2["price"] + 2.618 * w1, 2)
            inv = round(p2["price"], 2)
            if curr_close >= p3["price"] * 0.985:
                w_name = "🔥 الموجة الثالثة الدافعة (Wave 3)"
                summary = f"السهم في قلب الموجة الثالثة الصاعدة (أقوى موجات إليوت) بعد اختراق قمة الأولى ({p1['price']:.2f})، بأهداف فيبوناتشي عند ({t1}) ثم ({t2})."
                b_cls = "badge-bull"
            else:
                w_name = "⏳ بداية الموجة الرابعة التصحيحية (Wave 4)"
                t1 = round(p3["price"] - 0.382 * w3, 2)
                t2 = round(p1["price"] + 0.01, 2)
                inv = round(p1["price"], 2)
                summary = f"بعد صعود قوي في الموجة الثالثة حتى ({p3['price']:.2f})، يهدئ السهم في الموجة الرابعة نحو ({t1}) بشرط عدم كسر ({inv})."
                b_cls = "badge-warn"

            labels = ["(0)", "(1)", "(2)", "(3)"]
            labeled = [dict(p, label=lbl) for p, lbl in zip([p0, p1, p2, p3], labels)]
            return {
                "status": "ok",
                "wave_name": w_name,
                "pattern_type": "موجة دافعة صاعدة قيد التكوين (Waves 1-2-3)",
                "badge_cls": b_cls,
                "invalidation": inv,
                "target_1": t1,
                "target_2": t2,
                "summary": summary,
                "rules_check": [
                    ("1. الموجة (2) لم تكسر بداية (1)", f"{p2['price']:.2f} > {p0['price']:.2f}", True),
                    ("2. الموجة (3) اخترقت قمة (1)", f"{p3['price']:.2f} > {p1['price']:.2f}", True),
                    ("3. نسبة امتداد (3) إلى (1)", f"{(w3/w1)*100:.0f}%", w3 >= w1),
                ],
                "labeled_pivots": labeled
            }

    if len(pivots) >= 4 and pivots[-4]["type"] == "H":
        p0, p1, p2, p3 = pivots[-4], pivots[-3], pivots[-2], pivots[-1]
        wa = p0["price"] - p1["price"]
        wc = p2["price"] - p3["price"]
        if wa > 0 and p2["price"] < p0["price"] and p3["price"] < p1["price"]:
            if curr_close > p3["price"] * 1.02:
                t1 = round(p2["price"], 2)
                t2 = round(p0["price"], 2)
                inv = round(p3["price"], 2)
                w_name = "🌱 بداية موجة صاعدة جديدة (Wave 1 بعد اكتمال C)"
                summary = f"أنهى السهم التصحيح الثلاثي (A-B-C) عند القاع ({p3['price']:.2f}) وبدأ دورة صعود جديدة؛ الإلغاء بكسر ({inv})."
                b_cls = "badge-bull"
            else:
                t1 = round(p2["price"] - wa, 2)
                t2 = round(p2["price"] - 1.272 * wa, 2)
                inv = round(p2["price"], 2)
                w_name = "📉 الموجة التصحيحية الهابطة (Wave C)"
                summary = f"السهم يتحرك داخل الموجة (C) الهابطة بعد فشل تجاوز قمة (B) عند ({inv})، وتقع مناطق اكتمال التصحيح قرب ({max(0.01, t1)})."
                b_cls = "badge-bear"

            labels = ["(0)", "(A)", "(B)", "(C)"]
            labeled = [dict(p, label=lbl) for p, lbl in zip([p0, p1, p2, p3], labels)]
            return {
                "status": "ok",
                "wave_name": w_name,
                "pattern_type": "نموذج تصحيحي متعرج (ZigZag A-B-C)",
                "badge_cls": b_cls,
                "invalidation": inv,
                "target_1": max(0.01, t1),
                "target_2": max(0.01, t2),
                "summary": summary,
                "rules_check": [
                    ("1. قمة الموجة (B) أدنى من بداية (A)", f"{p2['price']:.2f} < {p0['price']:.2f}", True),
                    ("2. الموجة (C) كسرت قاع (A)", f"{p3['price']:.2f} < {p1['price']:.2f}", True),
                    ("3. نسبة طول (C) إلى (A)", f"{(wc/wa)*100:.0f}%", True),
                ],
                "labeled_pivots": labeled
            }

    p0, p1, p2 = pivots[-3], pivots[-2], pivots[-1]
    if p0["type"] == "L" and p1["type"] == "H" and p2["type"] == "L" and p2["price"] > p0["price"]:
        w1 = p1["price"] - p0["price"]
        ret_pct = ((p1["price"] - p2["price"]) / w1) * 100.0
        t1 = round(p2["price"] + 1.618 * w1, 2)
        t2 = round(p2["price"] + 2.618 * w1, 2)
        inv = round(p0["price"], 2)
        labels = ["(0)", "(1)", "(2)"]
        labeled = [dict(p, label=lbl) for p, lbl in zip([p0, p1, p2], labels)]
        return {
            "status": "ok",
            "wave_name": "🎯 الموجة الثانية التصحيحية (Wave 2 — منطقة تجميع)",
            "pattern_type": "بداية دورة دافعة (Waves 1-2)",
            "badge_cls": "badge-bull" if curr_close > p2["price"] * 1.01 else "badge-warn",
            "invalidation": inv,
            "target_1": t1,
            "target_2": t2,
            "summary": f"صحح السهم {ret_pct:.1f}% من الموجة الأولى عند ({p2['price']:.2f})؛ اختراق ({p1['price']:.2f}) يؤكد انطلاق الموجة الثالثة نحو ({t1}).",
            "rules_check": [
                ("1. الموجة (2) فوق قاع (0)", f"{p2['price']:.2f} > {p0['price']:.2f}", True),
                ("2. نسبة تصحيح فيبوناتشي", f"{ret_pct:.1f}% (المثالي 50% - 61.8%)", 30.0 <= ret_pct <= 78.6),
                ("3. مستوى تأكيد الموجة (3)", f"اختراق {p1['price']:.2f}", curr_close >= p1["price"]),
            ],
            "labeled_pivots": labeled
        }

    last_4 = pivots[-4:]
    labels = ["(W1)", "(W2)", "(W3)", "(W4)"]
    labeled = [dict(p, label=lbl) for p, lbl in zip(last_4, labels)]
    is_up = last_4[-1]["price"] > last_4[-2]["price"]
    return {
        "status": "ok",
        "wave_name": "🔄 موجة تجميع عرضية (Complex Correction)",
        "pattern_type": "نموذج تصحيحي مركب (W-X-Y)",
        "badge_cls": "badge-warn",
        "invalidation": round(min(p["price"] for p in last_4), 2),
        "target_1": round(max(p["price"] for p in last_4), 2),
        "target_2": round(max(p["price"] for p in last_4) * 1.08, 2),
        "summary": "يتحرك السهم في موجة تصحيحية عرضية متداخلة؛ يُفضّل انتظار اختراق قمة الموجة (X) لتأكيد الاتجاه الجديد.",
        "rules_check": [
            ("1. الاتجاه اللحظي للضلع الأخير", "صاعد 🟢" if is_up else "هابط 🔴", is_up),
            ("2. سقف النطاق العرضي", f"{max(p['price'] for p in last_4):.2f}", True),
            ("3. قاع النطاق العرضي", f"{min(p['price'] for p in last_4):.2f}", True),
        ],
        "labeled_pivots": labeled
    }


# ==========================================
# محرك تحليل التدفق اللحظي
# ==========================================
def analyze_intraday_flow(tv_q: dict, fallback_close: float = 0.0, session_progress: float = 1.0) -> dict:
    close_p = tv_q.get("close", 0.0) if tv_q else fallback_close
    if close_p <= 0:
        return {
            "verdict": "⚪ بانتظار التداول",
            "short_verdict": "⚪ انتظار",
            "badge_cls": "badge-warn",
            "flow_score": 0,
            "vwap": 0.0,
            "vwap_diff_pct": 0.0,
            "bid": 0.0,
            "ask": 0.0,
            "spread_pct": 0.0,
            "ba_pressure": "غير متاح خارج الجلسة",
            "rsi15": 50.0,
            "macd15": 0.0,
            "macds15": 0.0,
            "clv_pct": 50.0,
            "rel_vol": 1.0,
            "reasons": ["لا توجد بيانات لحظية كافية حالياً."],
            "action_hint": "انتظر افتتاح الجلسة لتقييم السيولة اللحظية."
        }

    high_p = tv_q.get("high", close_p) or close_p
    low_p = tv_q.get("low", close_p) or close_p
    daily_chg = tv_q.get("change", 0.0)
    vol = tv_q.get("volume", 0.0)
    avg_vol10 = tv_q.get("avg_vol10", 0.0)
    bid = tv_q.get("bid", 0.0)
    ask = tv_q.get("ask", 0.0)
    rsi15 = tv_q.get("rsi15", 50.0)
    macd15 = tv_q.get("macd15", 0.0)
    macds15 = tv_q.get("macds15", 0.0)

    raw_vwap = tv_q.get("vwap", 0.0)
    if raw_vwap > 0:
        vwap = raw_vwap
    elif high_p > 0 and low_p > 0:
        vwap = (high_p + low_p + close_p) / 3.0
    else:
        vwap = close_p

    vwap_diff_pct = ((close_p - vwap) / vwap * 100.0) if vwap > 0 else 0.0
    clv = ((close_p - low_p) / (high_p - low_p)) if (high_p > low_p) else 0.5

    expected_vol_now = max(1.0, avg_vol10 * max(0.04, session_progress)) if avg_vol10 > 0 else 0.0
    pace_rvol = (vol / expected_vol_now) if (expected_vol_now > 0 and vol > 0) else 0.0

    score = 0
    reasons = []

    if close_p > vwap * 1.003:
        score += 30
        reasons.append(f"✅ السعر ({close_p}) يتداول أعلى متوسط السيولة VWAP ({vwap:.2f}) بفارق {vwap_diff_pct:+.2f}% (سيطرة مشترين).")
    elif close_p < vwap * 0.997:
        score -= 30
        reasons.append(f"🔻 السعر ({close_p}) يتداول أسفل متوسط السيولة VWAP ({vwap:.2f}) بفارق {vwap_diff_pct:+.2f}% (ضغط بيعي).")
    else:
        reasons.append(f"⚖️ السعر ({close_p}) ملاصق لخط VWAP ({vwap:.2f}) في منطقة توازن.")

    if clv >= 0.70:
        score += 25
        reasons.append(f"📈 السهم يتماسك في الثلث العلوي لمدى الجلسة ({clv*100:.0f}% من القاع للقمة).")
    elif clv <= 0.30:
        score -= 25
        reasons.append(f"📉 السهم يضغط قرب قاع الجلسة ({clv*100:.0f}% من مدى اليوم).")

    spread_pct = 0.0
    if bid > 0 and ask > 0 and ask >= bid:
        spread_pct = ((ask - bid) / close_p) * 100.0
        ba_span = ask - bid
        ba_pos = ((close_p - bid) / ba_span) if ba_span > 0 else 0.5
        if close_p >= ask or ba_pos >= 0.65:
            score += 15
            ba_pressure = f"🟢 تنفيذ على العروض (طلب {bid} / عرض {ask})"
            reasons.append(f"⚡ الصفقات تُنفَّذ قرب سعر العرض ({ask}) ما يعكس رغبة شراء ماركت.")
        elif close_p <= bid or ba_pos <= 0.35:
            score -= 15
            ba_pressure = f"🔴 ضغط على الطلبات (طلب {bid} / عرض {ask})"
            reasons.append(f"⚠️ الصفقات تُنفَّذ قرب سعر الطلب ({bid}) ما يعكس تسارع البيع.")
        else:
            ba_pressure = f"⚪ متوازن (طلب {bid} / عرض {ask})"
    else:
        if clv >= 0.65 and daily_chg > 0:
            score += 10
            ba_pressure = "🟢 تداول قرب قمة الجلسة"
        elif clv <= 0.35 and daily_chg < 0:
            score -= 10
            ba_pressure = "🔴 تداول قرب قاع الجلسة"
        else:
            ba_pressure = "⚪ لا توجد عروض حية حالياً"

    if rsi15 >= 56:
        score += 15
        reasons.append(f"🔥 زخم 15 دقيقة إيجابي (RSI 15m = {rsi15:.1f}).")
    elif rsi15 <= 44:
        score -= 15
        reasons.append(f"❄️ زخم 15 دقيقة سلبي (RSI 15m = {rsi15:.1f}).")

    if macd15 > macds15:
        score += 15
    elif macd15 < macds15:
        score -= 15

    if pace_rvol >= 1.40:
        score = int(max(-100, min(100, round(score * 1.2))))
        reasons.append(f"💧 وتيرة السيولة اللحظية متسارعة ({pace_rvol:.1f}x من المعتاد في نفس هذا التوقيت).")
    elif 0 < pace_rvol < 0.55:
        reasons.append(f"💤 وتيرة السيولة هادئة حالياً ({pace_rvol:.1f}x من المعتاد في نفس التوقيت).")

    score = max(-100, min(100, score))

    if score >= 30:
        verdict = "🟢 مرشح للصعود (ضغط شرائي)"
        short_verdict = "🟢 صعود"
        badge_cls = "badge-bull"
        action_hint = "المشترون يسيطرون فوق VWAP؛ الوضع يدعم الاحتفاظ أو الدخول مع الالتزام بوقف الخسارة."
    elif score <= -30:
        verdict = "🔴 مرشح للهبوط (ضغط بيعي)"
        short_verdict = "🔴 هبوط"
        badge_cls = "badge-bear"
        action_hint = "البائعون يضغطون أسفل VWAP؛ يُنصح بالحذر وتأمين الأرباح أو تأجيل الشراء حتى استعادة VWAP."
    else:
        verdict = "🟡 تذبذب عرضي (انتظار)"
        short_verdict = "🟡 تذبذب"
        badge_cls = "badge-warn"
        action_hint = "تعادل بين العرض والطلب؛ الأفضل انتظار اختراق واضح لـ VWAP بسيولة شرائية."

    return {
        "verdict": verdict,
        "short_verdict": short_verdict,
        "badge_cls": badge_cls,
        "flow_score": score,
        "vwap": round(vwap, 2),
        "vwap_diff_pct": round(vwap_diff_pct, 2),
        "bid": bid,
        "ask": ask,
        "spread_pct": round(spread_pct, 2),
        "ba_pressure": ba_pressure,
        "rsi15": round(rsi15, 1),
        "macd15": round(macd15, 4),
        "macds15": round(macds15, 4),
        "clv_pct": round(clv * 100, 1),
        "rel_vol": round(pace_rvol, 2),
        "reasons": reasons,
        "action_hint": action_hint
    }

# ==========================================
# محرك إرسال تنبيهات التليجرام
# ==========================================
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
# محرك المسح الشامل المباشر لجميع أسهم البورصة
# ==========================================
LEADERS_EGX_SYMBOLS = {
    "COMI", "TMGH", "SWDY", "ETEL", "EFIH", "FWRY", "HRHO", "ABUK", "ORAS",
    "EAST", "ESRS", "EKHO", "HELI", "PHDC", "ORWE", "CLHO", "ISPH", "JUFO",
    "OBRI", "DSCW", "ECAP", "ATLC", "AMOC", "SKPC", "MFPC", "ADIB", "CIEB",
    "FAIT", "EMFD", "OCDI", "EGAL", "GBCO", "MCQE", "ARCC", "CIRA", "RMDA",
    "ZMID", "ELSH", "MTIE", "RAYA", "BTFH", "ASPI", "TAQA", "VLMR", "PHAR",
    "ALCN", "CSAG", "EGTS", "MASR", "EFID", "ORHD", "BINV", "CCAP", "HDBK",
    "BONY", "QNBA", "VALU", "ACTF"
}

@st.cache_data(ttl=60, show_spinner=False)
def fetch_full_egx_tv_scanner(cache_buster: int = 0) -> tuple:
    stocks_dict = {}
    fetched_time = get_cairo_now().strftime("%H:%M:%S")
    url = f"https://scanner.tradingview.com/egypt/scan?t={int(time.time())}"

    full_cols = [
        "name", "description", "close", "change", "open", "high", "low",
        "volume", "average_volume_10d_calc", "average_volume_30d_calc",
        "ATR", "EMA20", "EMA50", "EMA200", "High.1M", "Perf.1M",
        "RSI", "RSI|15", "MACD.macd|15", "MACD.signal|15", "VWAP", "bid", "ask"
    ]

    try:
        payload = json.dumps({
            "filter": [{"left": "type", "operation": "in_range", "right": ["stock", "dr", "fund"]}],
            "options": {"lang": "en"},
            "markets": ["egypt"],
            "symbols": {"query": {"types": []}, "tickers": []},
            "columns": full_cols,
            "sort": {"sortBy": "volume", "sortOrder": "desc"},
            "range": [0, 500]
        }).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0",
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache"
            }
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            res_json = json.loads(resp.read().decode("utf-8"))
            for row in res_json.get("data", []):
                full_s = row.get("s", "")
                d = row.get("d", [])
                if ":" not in full_s or len(d) < 4:
                    continue
                sym = full_s.split(":")[1].strip().upper()
                if not re.match(r"^[A-Z0-9]{2,12}$", sym):
                    continue
                close_val = _safe_f(d, 2, 0.0)
                if close_val <= 0:
                    continue
                atr_raw = _safe_f(d, 10, 0.0)
                ema20_v = _safe_f(d, 11, close_val)
                ema50_v = _safe_f(d, 12, close_val)
                ema200_v = _safe_f(d, 13, 0.0)
                high1m_v = _safe_f(d, 14, close_val)

                stocks_dict[sym] = {
                    "symbol": sym,
                    "name": str(d[1]) if len(d) > 1 and d[1] else sym,
                    "close": close_val,
                    "change": _safe_f(d, 3, 0.0),
                    "open": _safe_f(d, 4, close_val),
                    "high": _safe_f(d, 5, close_val),
                    "low": _safe_f(d, 6, close_val),
                    "volume": _safe_f(d, 7, 0.0),
                    "avg_vol10": _safe_f(d, 8, 0.0),
                    "avg_vol30": _safe_f(d, 9, 0.0),
                    "atr": atr_raw if atr_raw > 0 else (close_val * 0.025),
                    "ema20": ema20_v if ema20_v > 0 else close_val,
                    "ema50": ema50_v if ema50_v > 0 else close_val,
                    "ema200": ema200_v,
                    "high_1m": high1m_v if high1m_v > 0 else close_val,
                    "perf_1m": _safe_f(d, 15, 0.0),
                    "rsi": _safe_f(d, 16, 50.0),
                    "rsi15": _safe_f(d, 17, 50.0),
                    "macd15": _safe_f(d, 18, 0.0),
                    "macds15": _safe_f(d, 19, 0.0),
                    "vwap": _safe_f(d, 20, 0.0),
                    "bid": _safe_f(d, 21, 0.0),
                    "ask": _safe_f(d, 22, 0.0),
                }
    except Exception:
        pass

    return stocks_dict, fetched_time

def score_stock_from_tv(
    q: dict,
    market_median_perf1m: float,
    capital: float,
    risk_pct: float,
    fee_rate: float,
    session_progress: float = 1.0
) -> dict:
    sym = q["symbol"]
    close = q["close"]
    open_p = q["open"] if q["open"] > 0 else close
    high = q["high"] if q["high"] > 0 else close
    low = q["low"] if q["low"] > 0 else close
    vol = q["volume"]
    avg_vol = q["avg_vol10"] if q["avg_vol10"] > 0 else (q["avg_vol30"] if q["avg_vol30"] > 0 else max(1.0, vol))
    atr14 = q["atr"] if q["atr"] > 0 else (close * 0.025)
    ema20 = q["ema20"]
    ema50 = q["ema50"]
    ema200 = q["ema200"]
    high_1m = q["high_1m"]
    pct_change = q["change"]
    perf_1m = q["perf_1m"]

    expected_vol_now = max(1.0, avg_vol * max(0.04, session_progress)) if avg_vol > 0 else 1.0
    pace_rvol = (vol / expected_vol_now) if vol > 0 else 0.0

    candle_range = max(0.0, high - low)
    close_pos = ((close - low) / candle_range) if candle_range > 0 else 0.5

    flow_res = analyze_intraday_flow(q, fallback_close=close, session_progress=session_progress)

    exec_price = flow_res["vwap"] if flow_res["vwap"] > 0 else close
    effective_turnover_m = ((vol * exec_price) / 1_000_000) if vol > 0 else 0.0

    pts_trend = 0
    pts_wyckoff = 0
    pts_intraday = 0
    tags = []
    setup_type = "👀 مراقبة"

    if ema200 > 0:
        if close > ema200:
            pts_trend += 12
            tags.append("فوق EMA200")
            if ema50 > ema200:
                pts_trend += 6
        else:
            tags.append("تحت EMA200")
    elif close > ema50:
        pts_trend += 10
        tags.append("فوق EMA50")

    if close > ema20 and ema20 > ema50:
        pts_trend += 6
        tags.append("ترتيب متوسطات صاعد")

    rs_alpha = perf_1m - market_median_perf1m
    if rs_alpha > 2.0:
        pts_trend += 6
        tags.append(f"قوة نسبية (+{rs_alpha:.1f}%)")
    elif rs_alpha > 0:
        pts_trend += 3

    is_breakout = (close >= high_1m * 0.994) and (high_1m > 0) and (pct_change > 0.4)
    if is_breakout and pace_rvol >= 1.35:
        pts_wyckoff = 35
        tags.append(f"اختراق قمة شهرية ({pace_rvol:.1f}x)")
        setup_type = "🚀 اختراق مؤكد"
    elif pace_rvol >= 1.65 and candle_range < (0.95 * atr14) and close_pos >= 0.55:
        pts_wyckoff = 30
        tags.append(f"امتصاص مؤسسي ({pace_rvol:.1f}x)")
        setup_type = "🐋 امتصاص حيتان"
    elif pace_rvol >= 1.45 and pct_change > 0.3 and close >= open_p:
        pts_wyckoff = 26
        tags.append(f"انفجار سيولة ({pace_rvol:.1f}x)")
        setup_type = "🔥 تدفق سيولة"
    elif pace_rvol >= 1.15 and pct_change > 0:
        pts_wyckoff = 16
        tags.append(f"سيولة نشطة ({pace_rvol:.1f}x)")
        setup_type = "📈 زخم سيولة"
    elif session_progress >= 0.75 and pct_change < 0 and 0 < pace_rvol <= 0.65 and close > ema50:
        pts_wyckoff = 20
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

# ==========================================
# سحب الشموع التاريخية عند الطلب لسهم واحد فقط
# ==========================================
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
    y = (sin_O * cos_w + cos_O * sin_w * cos_I) * x_p + (-sin_O * sin_w + cos_O * sin_w * cos_I) * y_p
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
# محرك التحليل المالي (Piotroski F-Score)
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
# محرك التحليل الخبري وتحليل المشاعر
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
# تحميل المحفظة السحابية + حساب الجلسة + المسح اللحظي
# ==========================================
force_sync = st.session_state.pop("force_cloud_sync", False)
my_portfolio, cloud_connected = load_portfolio(force_cloud_refresh=force_sync)
closed_trades = load_closed_trades(force_refresh=force_sync)
portfolio_clean_syms = [
    item["symbol"].upper().replace(".CA", "").strip()
    for item in my_portfolio if item.get("symbol")
]

session_info = get_egx_session_metrics()
refresh_nonce = st.session_state.get("refresh_nonce", 0)

with st.spinner("🚀 جاري مسح جميع أسهم البورصة وتحديث السيولة اللحظية..."):
    raw_egx_tv_map, last_live_sync = fetch_full_egx_tv_scanner(refresh_nonce)

# ==========================================
# الشريط الجانبي (إعدادات السحابة والتليجرام والسكانر)
# ==========================================
with st.sidebar:
    st.markdown("## ☁️ المزامنة السحابية (Supabase)")
    default_sb_url = st.session_state.get("sb_url_val", get_secret_safe("SUPABASE_URL"))
    default_sb_key = st.session_state.get("sb_key_val", get_secret_safe("SUPABASE_KEY"))

    sb_url_in = st.text_input("🌐 Supabase URL:", value=default_sb_url, placeholder="https://xxxx.supabase.co")
    st.session_state["sb_url_val"] = sb_url_in

    sb_key_in = st.text_input("🔐 Supabase Key:", value=default_sb_key, type="password", placeholder="eyJhbGci...")
    st.session_state["sb_key_val"] = sb_key_in

    sb_c1, sb_c2 = st.columns(2)
    with sb_c1:
        if st.button("🔌 فحص الاتصال", use_container_width=True):
            ok_sb, msg_sb = test_supabase_connection()
            if ok_sb:
                st.session_state["force_cloud_sync"] = True
                st.success(msg_sb)
                st.rerun()
            else:
                st.error(msg_sb)
    with sb_c2:
        if st.button("⬆️ رفع المحلي للسحابة", use_container_width=True, help="يرفع الأسهم المحفوظة محلياً إلى Supabase"):
            local_items = _load_local_portfolio_file() or my_portfolio
            ok_up, msg_up = sync_full_portfolio_to_cloud(local_items)
            if ok_up:
                st.success(msg_up)
                st.rerun()
            else:
                st.error(msg_up)

    st.divider()
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
            "🦅 <b>EGX Whale Hunter Pro V8.5</b>\n✅ النظام السحابي وسجل الصفقات وتنبيهات الخلفية تعمل بنجاح!"
        )
        if ok:
            st.success("✅ وصلت الرسالة التجريبية لتليجرام!")
        else:
            st.error(f"❌ فشل الإرسال: {res_msg}")

    st.divider()
    st.markdown("## 🎛️ إعدادات السكانر")
    market_scope = st.radio(
        "🌐 نطاق جدول الرادار:",
        options=[
            f"كل أسهم البورصة المصرية ({len(raw_egx_tv_map)} سهم)",
            f"الأسهم القيادية والنشطة فقط ({len(LEADERS_EGX_SYMBOLS)} سهم)"
        ],
        index=0
    )

    capital = st.number_input("💰 رأس المال للمقترحات (ج.م)", min_value=5000, value=100000, step=5000)
    risk_pct = st.slider("🛡️ المخاطرة في الصفقة (%)", min_value=0.5, max_value=5.0, value=1.5, step=0.25)
    min_turnover_m = st.number_input("💧 الحد الأدنى للسيولة الفعلية (مليون ج.م)", min_value=0.0, value=0.5, step=0.25)

    fee_tier = st.radio(
        "💳 شريحة Thndr Trader:",
        options=[
            "أول 50 صفقة بالشهر (~0.16%)",
            "أكثر من 50 صفقة / عادي (~0.37%)"
        ]
    )
    fee_rate = 0.0016 if "0.16%" in fee_tier else 0.0037

    min_score = st.slider("🎯 الحد الأدنى للسكور بجدول الرادار", min_value=0, max_value=100, value=45, step=5)
    alert_buffer_pct = st.slider("🔔 حساسية تنبيه قرب الهدف/الوقف (%)", min_value=0.5, max_value=8.0, value=2.5, step=0.5)

    if st.button("🔄 تحديث جميع الأسهم والسحابة الآن", type="primary", use_container_width=True):
        st.session_state["refresh_nonce"] = refresh_nonce + 1
        st.session_state["force_cloud_sync"] = True
        fetch_full_egx_tv_scanner.clear()
        fetch_single_stock_history.clear()
        st.rerun()

# ==========================================
# البانر الافتتاحي المضيء (Hero Banner)
# ==========================================
tg_status_txt = "📲 تليجرام متصل" if (tg_token and tg_chat_id) else "📴 تليجرام غير مربوط"
cloud_status_txt = "☁️ سحابة Supabase متصلة" if cloud_connected else "💾 حفظ محلي"

st.markdown(f"""
<div class="hero-banner">
    <div>
        <div class="hero-title">🦅 <span class="hero-accent">EGX WHALE HUNTER</span> PRO <span style="font-size:13px;color:#FACC15;">V8.5</span></div>
        <div class="hero-sub">🌐 تغطية كاملة ({len(raw_egx_tv_map)} سهم) • {cloud_status_txt} • 💼 محفظتي ({len(portfolio_clean_syms)}) • {tg_status_txt}</div>
    </div>
    <div class="session-pill">{session_info['badge']}</div>
</div>
""", unsafe_allow_html=True)

perf1m_list = [q["perf_1m"] for q in raw_egx_tv_map.values() if q.get("volume", 0) > 0]
market_median_perf1m = float(np.median(perf1m_list)) if perf1m_list else 0.0

all_analyzed_map = {}
scanner_results = []
only_leaders = "الأسهم القيادية" in market_scope

for sym, q_data in raw_egx_tv_map.items():
    analyzed = score_stock_from_tv(
        q=q_data,
        market_median_perf1m=market_median_perf1m,
        capital=capital,
        risk_pct=risk_pct,
        fee_rate=fee_rate,
        session_progress=session_info["progress"]
    )
    all_analyzed_map[sym] = analyzed

    if only_leaders and sym not in LEADERS_EGX_SYMBOLS:
        continue
    if analyzed["السيولة (مليون)"] >= min_turnover_m and analyzed["التغير %"] < 19.5:
        scanner_results.append(analyzed)

for m_sym in portfolio_clean_syms:
    if m_sym not in all_analyzed_map:
        p_entry_item = next((x for x in my_portfolio if x["symbol"].upper().replace(".CA", "").strip() == m_sym), {})
        c_val = round(float(p_entry_item.get("buy_price", 0.0)), 2)
        atr_val = round(max(0.01, c_val * 0.025), 3)
        sl_val = round(max(0.01, c_val - 2.0 * atr_val), 2)
        r_share = max(0.01, c_val - sl_val)
        all_analyzed_map[m_sym] = {
            "الرمز": m_sym,
            "اسم الشركة": m_sym,
            "Ticker": f"{m_sym}.CA",
            "السكور": 0,
            "نوع الإشارة": "🆕 إدراج حديث",
            "الرأي اللحظي": "⚪ انتظار",
            "الإغلاق": c_val,
            "ATR14": atr_val,
            "EMA20": c_val,
            "التغير %": 0.0,
            "الفوليوم": 0.0,
            "فرق VWAP %": 0.0,
            "القوة النسبية %": 0.0,
            "السيولة (مليون)": 0.0,
            "الوقف (2xATR)": sl_val,
            "TP1": round(c_val + 1.618 * r_share, 2),
            "TP2": round(c_val + 2.618 * r_share, 2),
            "TP3": round(c_val + 3.618 * r_share, 2),
            "الأسهم": 0,
            "قيمة الصفقة": 0,
            "صافي TP1": 0,
            "التشخيص الفني": "⏳ بانتظار بيانات التداول",
            "score_parts": {"الاتجاه اليومي (30)": 0, "وتيرة السيولة ووايكوف (35)": 0, "التدفق اللحظي VWAP (35)": 0},
            "intraday_flow": analyze_intraday_flow({}, fallback_close=c_val, session_progress=session_info["progress"]),
            "tv_raw": {},
            "TradingView": f"https://www.tradingview.com/chart/?symbol=EGX:{m_sym}"
        }

scanner_results.sort(
    key=lambda x: (
        x["السكور"],
        x["intraday_flow"]["flow_score"],
        x["الفوليوم"],
        x["التغير %"]
    ),
    reverse=True
)
filtered_results = [r for r in scanner_results if r["السكور"] >= min_score]

# ==========================================
# معالجة محفظتي + محرك الوقف المتحرك الآلي
# ==========================================
portfolio_rows = []
active_alerts = []
total_port_cost = 0.0
total_port_val = 0.0
total_open_risk = 0.0

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

    stock_info = all_analyzed_map.get(sym)
    curr_p = stock_info["الإغلاق"] if (stock_info and stock_info["الإغلاق"] > 0) else buy_p
    atr14 = stock_info["ATR14"] if stock_info else round(buy_p * 0.025, 3)
    ema20 = stock_info.get("EMA20", curr_p) if stock_info else curr_p
    vwap_val = stock_info["intraday_flow"].get("vwap", curr_p) if stock_info else curr_p
    short_opinion = stock_info["الرأي اللحظي"] if stock_info else "⚪ انتظار"

    sl = user_sl if user_sl > 0 else round(max(0.01, buy_p - 2.0 * atr14), 2)
    risk_unit = max(0.01, buy_p - sl)
    tp1 = user_tp1 if user_tp1 > 0 else round(buy_p + 1.618 * risk_unit, 2)
    tp2 = user_tp2 if user_tp2 > 0 else round(buy_p + 2.618 * risk_unit, 2)

    sl_updated = False
    if trailing_on:
        be_price = round(buy_p * (1.0 + fee_rate * 2.0), 2)
        if curr_p >= tp1 and trailing_stage < 1 and be_price < curr_p:
            new_sl = max(sl, be_price)
            sl = new_sl
            trailing_stage = 1
            sl_updated = True
            active_alerts.append(("success", f"🛡️ <b>تأمين الصفقة آلياً ({sym}):</b> بعد تحقق <b>TP1</b> تم رفع وقف الخسارة لنقطة التعادل (<b>{new_sl} ج.م</b>)."))
            tr_key = f"{today_str}_{sym}_TRAIL_BE"
            if tr_key not in sent_tg_log and tg_auto_port and tg_token and tg_chat_id:
                ok_t, _ = send_telegram_message(
                    tg_token, tg_chat_id,
                    f"🛡️ <b>تأمين الصفقة آلياً (Breakeven) — {sym}</b>\nالسعر حقق <b>TP1 ({tp1})</b>، وتم رفع وقف الخسارة تلقائياً لنقطة التعادل: <b>{new_sl} ج.م</b>."
                )
                if ok_t:
                    record_sent_tg_alert(tr_key, get_cairo_now().strftime("%H:%M"), sent_tg_log)

        if curr_p >= tp2:
            anchor = max(vwap_val, ema20) if (vwap_val > 0 and ema20 > 0) else curr_p
            cand_sl = round(min(curr_p - 0.5 * atr14, anchor * 0.992), 2)
            if cand_sl > sl * 1.003 and cand_sl < curr_p:
                sl = cand_sl
                trailing_stage = 2
                sl_updated = True
                active_alerts.append(("success", f"🚀 <b>ملاحقة الأرباح ({sym}):</b> تم رفع وقف حماية الأرباح آلياً إلى <b>{cand_sl} ج.م</b> خلف خط السيولة."))
                tr2_key = f"{today_str}_{sym}_TRAIL_{int(cand_sl * 100)}"
                if tr2_key not in sent_tg_log and tg_auto_port and tg_token and tg_chat_id:
                    ok_t2, _ = send_telegram_message(
                        tg_token, tg_chat_id,
                        f"🚀 <b>ملاحقة الأرباح (Trailing Stop) — {sym}</b>\nالسعر الحالي: <b>{curr_p} ج.م</b> | تم رفع وقف حماية الأرباح إلى: <b>{cand_sl} ج.م</b>."
                    )
                    if ok_t2:
                        record_sent_tg_alert(tr2_key, get_cairo_now().strftime("%H:%M"), sent_tg_log)

    if sl_updated:
        upsert_portfolio_item({
            "symbol": sym,
            "shares": shares,
            "buy_price": buy_p,
            "stop_loss": sl,
            "tp1": tp1,
            "tp2": tp2,
            "trailing_enabled": trailing_on,
            "trailing_stage": trailing_stage,
        })

    if not trailing_on:
        trail_badge = "⏸️ معطّل"
    elif trailing_stage >= 2:
        trail_badge = "🚀 ملاحقة TP2"
    elif trailing_stage == 1:
        trail_badge = "🛡️ مؤمّن (تعادل)"
    else:
        trail_badge = "⏳ بانتظار TP1"

    cost_val = shares * buy_p
    mkt_val = shares * curr_p
    fees_est = mkt_val * fee_rate
    net_pnl = (mkt_val - cost_val) - fees_est
    net_pnl_pct = (net_pnl / cost_val) * 100
    pos_risk = max(0.0, shares * (curr_p - sl))

    total_port_cost += cost_val
    total_port_val += mkt_val
    total_open_risk += pos_risk

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
                record_sent_tg_alert(dedup_key, get_cairo_now().strftime("%H:%M"), sent_tg_log)

    span = max(0.01, tp1 - sl)
    progress_ratio = min(1.0, max(0.0, (curr_p - sl) / span))

    portfolio_rows.append({
        "الرمز": sym,
        "الرأي اللحظي": short_opinion,
        "حالة التنبيه": alert_status,
        "الوقف المتحرك": trail_badge,
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
        "trailing_enabled": trailing_on,
        "trailing_stage": trailing_stage,
        "TradingView": f"https://www.tradingview.com/chart/?symbol=EGX:{sym}",
        "stock_info": stock_info
    })

if tg_auto_whales and tg_token and tg_chat_id:
    for r in filtered_results:
        if r["السكور"] >= 80:
            w_key = f"{today_str}_WHALE_{r['الرمز']}"
            if w_key not in sent_tg_log:
                w_msg = (
                    f"🐋 <b>إشارة حيتان جديدة — {r['الرمز']}</b> ({r['الرأي اللحظي']})\n"
                    f"السكور: <b>{r['السكور']}/100</b> ({r['نوع الإشارة']} | وتيرة {r['الفوليوم']}x)\n"
                    f"السعر: <b>{r['الإغلاق']}</b> | الوقف: <b>{r['الوقف (2xATR)']}</b> | TP1: <b>{r['TP1']}</b>"
                )
                ok, _ = send_telegram_message(tg_token, tg_chat_id, w_msg)
                if ok:
                    record_sent_tg_alert(w_key, get_cairo_now().strftime("%H:%M"), sent_tg_log)

if active_alerts:
    for level, msg in active_alerts:
        st.markdown(f'<div class="alert-box-{level}">{msg}</div>', unsafe_allow_html=True)

# ==========================================
# شريط التحديث اللحظي
# ==========================================
ref_c1, ref_c2, ref_c3 = st.columns([1.8, 1, 1])
with ref_c1:
    st.caption(f"📡 **TradingView مباشر ({len(raw_egx_tv_map)} سهم)** | آخر سحب: **{last_live_sync}** | وتيرة السيولة معايرة على **{session_info['progress']*100:.0f}%** من الجلسة")
with ref_c2:
    live_auto = st.checkbox("⚡ تحديث تلقائي كل 5 دقائق", value=False)
with ref_c3:
    if st.button("🔄 سحب الأسعار والمزامنة الآن", use_container_width=True):
        st.session_state["refresh_nonce"] = refresh_nonce + 1
        st.session_state["force_cloud_sync"] = True
        fetch_full_egx_tv_scanner.clear()
        st.rerun()

# ==========================================
# زر التنقل الرئيسي
# ==========================================
main_view = st.radio(
    "🧭 اختر القسم:",
    options=[
        f"🎯 رادار صفقات السوق والسيولة الحية ({len(filtered_results)})",
        f"💼 محفظتي الشخصية وسجل الصفقات ({len(portfolio_rows)})"
    ],
    horizontal=True,
    label_visibility="collapsed"
)

st.divider()

# ==============================================================================
# القسم الأول: رادار صفقات السوق والسيولة الحية
# ==============================================================================
if "رادار" in main_view:
    m1, m2, m3, m4 = st.columns(4)
    m1.markdown(f'<div class="kpi-card"><div class="kpi-label">📡 أسهم مفحوصة</div><div class="kpi-val">{len(all_analyzed_map)} / {len(raw_egx_tv_map)}</div></div>', unsafe_allow_html=True)
    m2.markdown(f'<div class="kpi-card"><div class="kpi-label">🎯 صفقات نشطة الآن</div><div class="kpi-val txt-green">{len(filtered_results)}</div></div>', unsafe_allow_html=True)
    ret_color_cls = "txt-green" if market_median_perf1m >= 0 else "txt-red"
    m3.markdown(f'<div class="kpi-card"><div class="kpi-label">📈 أداء السوق (شهر)</div><div class="kpi-val {ret_color_cls}">{market_median_perf1m:+.2f}%</div></div>', unsafe_allow_html=True)
    m4.markdown(f'<div class="kpi-card" style="border-top-color:#FACC15;"><div class="kpi-label">🛡️ المخاطرة المقترحة</div><div class="kpi-val txt-gold">{capital*(risk_pct/100):,.0f} ج.م</div></div>', unsafe_allow_html=True)

    st.write("")

    if filtered_results:
        st.markdown("### 🏆 أقوى الفرص حسب السيولة والتدفق اللحظي الآن (Top 3 Radar)")
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
                    السعر: <b class="txt-white">{item['الإغلاق']} ج.م</b> (<span class="{chg_cls}">{item['التغير %']:+.2f}%</span>) • السيولة: <b class="txt-cyan">{item['السيولة (مليون)']:.2f} م.ج</b> (<b class="txt-gold">{item['الفوليوم']}x</b>) • {item['الرأي اللحظي']}
                </div>
                <div style="display:flex;justify-content:space-between;background:#0B0F19;padding:8px 10px;border-radius:8px;font-size:12px;">
                    <span>🛑 الوقف: <b class="txt-red">{item['الوقف (2xATR)']}</b></span>
                    <span>🎯 TP1: <b class="txt-green">{item['TP1']}</b></span>
                    <span>💰 صافي: <b class="txt-green">{item['صافي TP1']:,.0f}</b></span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown(f"#### 📋 جدول الصفقات المحتملة المرتب بالسيولة والزخم ({len(filtered_results)} سهم)")
        display_cols = [
            "الرمز", "السكور", "الرأي اللحظي", "نوع الإشارة", "الإغلاق", "التغير %",
            "الفوليوم", "فرق VWAP %", "السيولة (مليون)",
            "الوقف (2xATR)", "TP1", "TP2", "الأسهم", "صافي TP1",
            "TradingView"
        ]
        st.dataframe(
            pd.DataFrame(filtered_results)[display_cols],
            use_container_width=True,
            hide_index=True,
            height=340,
            column_config={
                "TradingView": st.column_config.LinkColumn("شارت TV", display_text="فتح ↗"),
                "السكور": st.column_config.ProgressColumn("السكور", min_value=0, max_value=100, format="%d"),
                "الفوليوم": st.column_config.NumberColumn("وتيرة السيولة", format="%.2fx"),
                "السيولة (مليون)": st.column_config.NumberColumn("السيولة الفعلية (مليون ج.م)", format="%.2f"),
            }
        )
    else:
        st.warning("⚠️ لا توجد أسهم تطابق شروط السكانر الحالية. افتح القائمة الجانبية (>) لتقليل الحد الأدنى للسكور أو السيولة الفعلية.")

# ==============================================================================
# القسم الثاني: محفظتي الشخصية وسجل الصفقات المغلقة
# ==============================================================================
else:
    st.markdown("### 💼 محفظتي الشخصية وإدارة المخاطر الآلية")

    if st.session_state.get("last_port_msg"):
        st.success(st.session_state["last_port_msg"])

    total_net_pnl = total_port_val - total_port_cost - (total_port_val * fee_rate)
    total_pnl_pct = ((total_net_pnl / total_port_cost) * 100) if total_port_cost > 0 else 0.0
    pnl_cls = "txt-green" if total_net_pnl >= 0 else "txt-red"
    open_risk_pct = (total_open_risk / max(1.0, total_port_val)) * 100.0 if total_port_val > 0 else 0.0

    pk1, pk2, pk3, pk4 = st.columns(4)
    pk1.markdown(f'<div class="kpi-card"><div class="kpi-label">💵 إجمالي التكلفة</div><div class="kpi-val">{total_port_cost:,.0f} ج.م</div></div>', unsafe_allow_html=True)
    pk2.markdown(f'<div class="kpi-card"><div class="kpi-label">💰 القيمة الحالية</div><div class="kpi-val txt-cyan">{total_port_val:,.0f} ج.م</div></div>', unsafe_allow_html=True)
    pk3.markdown(f'<div class="kpi-card"><div class="kpi-label">📈 صافي الربح/الخسارة</div><div class="kpi-val {pnl_cls}">{total_net_pnl:+,.0f} ({total_pnl_pct:+.1f}%)</div></div>', unsafe_allow_html=True)
    pk4.markdown(f'<div class="kpi-card" style="border-top-color:#FACC15;"><div class="kpi-label">🛡️ المخاطرة المفتوحة</div><div class="kpi-val txt-gold">{total_open_risk:,.0f} ({open_risk_pct:.1f}%)</div></div>', unsafe_allow_html=True)

    st.write("")

    if portfolio_rows:
        if st.button("📲 إرسال تقرير محفظتي ونبض التدفق اللحظي الآن إلى تليجرام", use_container_width=True):
            if not tg_token or not tg_chat_id:
                st.warning("⚠️ افتح القائمة الجانبية (>) وأدخل Bot Token و Chat ID أولاً.")
            else:
                lines = [
                    "📊 <b>تقرير محفظتك ونبض التدفق اللحظي</b>",
                    f"القيمة: <b>{total_port_val:,.0f} ج.م</b> | الصافي: <b>{total_net_pnl:+,.0f} ج.م ({total_pnl_pct:+.1f}%)</b>",
                    ""
                ]
                for pr in portfolio_rows:
                    lines.append(
                        f"• <b>{pr['الرمز']}</b> ({pr['الرأي اللحظي']}): السعر {pr['السعر الحالي']} ({pr['العائد %']:+.1f}%) | "
                        f"SL: {pr['وقف الخسارة']} ({pr['الوقف المتحرك']}) | TP1: {pr['TP1']}"
                    )
                ok, r_msg = send_telegram_message(tg_token, tg_chat_id, "\n".join(lines))
                if ok:
                    st.success("✅ تم إرسال التقرير إلى بوت التليجرام!")
                else:
                    st.error(f"❌ تعذر الإرسال: {r_msg}")

    st.markdown("#### ➕ إضافة سهم جديد أو تحديث مركز في محفظتي")
    with st.form("add_stock_form", clear_on_submit=True):
        fc1, fc2, fc3 = st.columns(3)
        with fc1:
            in_sym_raw = st.text_input(
                "اكتب رمز السهم مباشرة:",
                placeholder="مثال: ABUK أو SKPC أو MFPC",
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

        in_trailing = st.checkbox(
            "🛡️ تفعيل الوقف المتحرك الآلي (تأمين التعادل شامل العمولة عند TP1 وملاحقة الربح بعد TP2)",
            value=True
        )

        submitted = st.form_submit_button("💾 حفظ السهم في محفظتي وتفعيل الحماية", type="primary", use_container_width=True)
        if submitted:
            clean_in = re.sub(r"[^A-Z0-9]", "", in_sym_raw.upper().replace(".CA", ""))
            if not clean_in:
                st.error("⚠️ من فضلك اكتب رمز السهم أولاً (مثل ABUK).")
            else:
                _, save_status = upsert_portfolio_item({
                    "symbol": clean_in,
                    "shares": int(in_shares),
                    "buy_price": float(in_buy),
                    "stop_loss": float(in_sl),
                    "tp1": float(in_tp1),
                    "tp2": float(in_tp2),
                    "trailing_enabled": bool(in_trailing),
                    "trailing_stage": 0,
                })
                st.session_state["last_port_msg"] = f"✅ تم حفظ سهم ({clean_in}) بنجاح ({save_status})!"
                st.rerun()

    if not portfolio_rows:
        st.info("📌 اكتب رمز السهم في المربع الأول (مثل ABUK) ثم الكمية وسعر الشراء واضغط حفظ، وسيظهر فوراً في الجدول بالأسفل.")
    else:
        st.markdown(f"#### 📋 جدول متابعة أسهم المحفظة ({len(portfolio_rows)} أسهم)")
        p_cols = [
            "الرمز", "الرأي اللحظي", "حالة التنبيه", "الوقف المتحرك", "السكور الفني", "الكمية",
            "متوسط الشراء", "السعر الحالي", "صافي الربح/الخسارة", "العائد %",
            "وقف الخسارة", "بُعد الوقف %", "TP1", "TP2", "TradingView"
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
        p_sel_col, p_be_col, p_del_col = st.columns([1.8, 1.1, 1])
        with p_sel_col:
            port_selected_sym = st.selectbox(
                "🔍 اختر سهماً من محفظتك للتحكم والشارت:",
                options=[r["الرمز"] for r in portfolio_rows],
                key="port_stock_select"
            )
        p_item = next(r for r in portfolio_rows if r["الرمز"] == port_selected_sym)

        with p_be_col:
            st.write("")
            st.write("")
            if st.button(f"🛡️ تأمين {port_selected_sym} للتعادل الآن", use_container_width=True, help="يرفع وقف الخسارة لسعر الشراء + العمولات"):
                be_val = round(p_item["متوسط الشراء"] * (1.0 + fee_rate * 2.0), 2)
                if p_item["السعر الحالي"] <= be_val:
                    st.warning(f"⚠️ السعر الحالي ({p_item['السعر الحالي']}) أقل من أو يساوي نقطة التعادل ({be_val}).")
                else:
                    _, st_be = upsert_portfolio_item({
                        "symbol": port_selected_sym,
                        "shares": p_item["الكمية"],
                        "buy_price": p_item["متوسط الشراء"],
                        "stop_loss": be_val,
                        "tp1": p_item["TP1"],
                        "tp2": p_item["TP2"],
                        "trailing_enabled": p_item["trailing_enabled"],
                        "trailing_stage": max(1, p_item["trailing_stage"]),
                    })
                    st.session_state["last_port_msg"] = f"🛡️ تم رفع وقف {port_selected_sym} لنقطة التعادل ({be_val} ج.م) ({st_be})."
                    st.rerun()

        with p_del_col:
            st.write("")
            st.write("")
            if st.button(f"🗑️ حذف {port_selected_sym} (بدون تسجيل)", use_container_width=True):
                _, del_status = delete_portfolio_item(port_selected_sym)
                st.session_state["last_port_msg"] = f"🗑️ تم حذف سهم ({port_selected_sym}) ({del_status})."
                st.rerun()

        # شريط إغلاق الصفقة الفعلي وتسجيلها في دفتر الأداء
        cl_c1, cl_c2 = st.columns([1.4, 1.6])
        with cl_c1:
            actual_exit_price = st.number_input(
                f"💵 سعر البيع الفعلي لإغلاق صفقة {port_selected_sym} (ج.م):",
                min_value=0.01,
                value=float(p_item["السعر الحالي"]),
                step=0.05,
                key=f"exit_p_{port_selected_sym}"
            )
        with cl_c2:
            st.write("")
            st.write("")
            if st.button(f"💰 إغلاق صفقة {port_selected_sym} وتسجيل الربح/الخسارة في السجل", type="primary", use_container_width=True):
                net_res, pct_res = record_closed_trade(
                    symbol=port_selected_sym,
                    shares=p_item["الكمية"],
                    buy_price=p_item["متوسط الشراء"],
                    sell_price=actual_exit_price,
                    fee_rate=fee_rate
                )
                st.session_state["last_port_msg"] = f"✅ تم إغلاق صفقة ({port_selected_sym}) بسعر {actual_exit_price} ج.م وتسجيل صافي {net_res:+,.0f} ج.م ({pct_res:+.1f}%)!"
                st.rerun()

        p_sinfo = p_item["stock_info"]

        pc_chart, pc_info = st.columns([2.1, 1])
        with pc_chart:
            df_p_hist = fetch_single_stock_history(f"{port_selected_sym}.CA")
            if not df_p_hist.empty:
                df_pchart = df_p_hist.tail(100)
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
                st.info(f"ℹ️ الرسم البياني التاريخي لـ **{port_selected_sym}** غير متوفر بعد على Yahoo Finance. يتم تحديث السعر والتدفق اللحظي من TradingView تلقائياً.")

        with pc_info:
            item_pnl_cls = "txt-green" if p_item["صافي الربح/الخسارة"] >= 0 else "txt-red"
            flow_obj = p_sinfo["intraday_flow"] if p_sinfo else {}
            st.markdown(f"""
            <div class="pro-card">
                <h4 class="txt-cyan" style="margin-top:0;">💼 بطاقة السهم: {port_selected_sym}</h4>
                <p><span class="{flow_obj.get('badge_cls', 'badge-warn')}">{flow_obj.get('verdict', p_item['الرأي اللحظي'])}</span></p>
                <p><span class="badge-bull">{p_item['حالة التنبيه']}</span> &nbsp; <span class="badge-warn">{p_item['الوقف المتحرك']}</span></p>
                <p class="txt-white"><b>السكور الفني:</b> {p_item['السكور الفني']}/100 | <b>VWAP:</b> {flow_obj.get('vwap', p_item['السعر الحالي'])}</p>
                <hr style="border-color:#26334D;">
                <p class="txt-white"><b>الكمية:</b> {p_item['الكمية']:,} سهم | <b>متوسط الشراء:</b> {p_item['متوسط الشراء']} ج.م</p>
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

    # ==========================================
    # سجل الصفقات المغلقة وإحصائيات الأداء (Closed Trades Analytics)
    # ==========================================
    st.divider()
    st.markdown("### 📜 سجل الصفقات المغلقة وإحصائيات الأداء الفعلي")
    if not closed_trades:
        st.info("📘 لا توجد صفقات مغلقة مسجلة بعد. عند بيع أي سهم من محفظتك باستخدام زر **إغلاق صفقة وتسجيل الربح/الخسارة**، سيظهر هنا مع حساب نسبة النجاح ومعامل الربح تلقائياً.")
    else:
        wins = [t for t in closed_trades if float(t.get("net_pnl", 0)) > 0]
        losses = [t for t in closed_trades if float(t.get("net_pnl", 0)) <= 0]
        win_rate = (len(wins) / len(closed_trades)) * 100.0
        gross_wins = sum(float(t.get("net_pnl", 0)) for t in wins)
        gross_losses = abs(sum(float(t.get("net_pnl", 0)) for t in losses))
        profit_factor = (gross_wins / gross_losses) if gross_losses > 0 else (99.9 if gross_wins > 0 else 0.0)
        realized_total = sum(float(t.get("net_pnl", 0)) for t in closed_trades)
        realized_cls = "txt-green" if realized_total >= 0 else "txt-red"

        tk1, tk2, tk3, tk4 = st.columns(4)
        tk1.markdown(f'<div class="kpi-card"><div class="kpi-label">📊 إجمالي الصفقات</div><div class="kpi-val">{len(closed_trades)} صفقة</div></div>', unsafe_allow_html=True)
        tk2.markdown(f'<div class="kpi-card"><div class="kpi-label">🎯 نسبة النجاح (Win Rate)</div><div class="kpi-val txt-cyan">{win_rate:.1f}%</div></div>', unsafe_allow_html=True)
        tk3.markdown(f'<div class="kpi-card"><div class="kpi-label">⚖️ معامل الربح (Profit Factor)</div><div class="kpi-val txt-gold">{profit_factor:.2f}x</div></div>', unsafe_allow_html=True)
        tk4.markdown(f'<div class="kpi-card"><div class="kpi-label">💰 صافي الأرباح المحققة</div><div class="kpi-val {realized_cls}">{realized_total:+,.0f} ج.م</div></div>', unsafe_allow_html=True)

        st.write("")
        hist_rows = []
        for t in closed_trades:
            hist_rows.append({
                "الرمز": t.get("symbol", ""),
                "الكمية": int(t.get("shares", 0)),
                "سعر الشراء": round(float(t.get("buy_price", 0)), 2),
                "سعر البيع": round(float(t.get("sell_price", 0)), 2),
                "صافي الربح/الخسارة": round(float(t.get("net_pnl", 0)), 0),
                "العائد %": round(float(t.get("pnl_pct", 0)), 2),
                "تاريخ الإغلاق": str(t.get("closed_at", ""))[:16].replace("T", " "),
            })
        st.dataframe(pd.DataFrame(hist_rows), use_container_width=True, hide_index=True)

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
                        ok_r, msg_r = sync_full_portfolio_to_cloud(restored)
                        if not ok_r:
                            _save_local_portfolio_cache(restored)
                            st.success("✅ تمت استعادة المحفظة محلياً بنجاح!")
                        else:
                            st.success(msg_r)
                        st.rerun()
                except Exception:
                    st.error("⚠️ ملف غير صالح.")

# ==============================================================================
# الدراسة العميقة الشاملة (متاحة لجميع أسهم البورصة بالكامل)
# ==============================================================================
if all_analyzed_map:
    st.divider()
    port_set = set([p["الرمز"] for p in portfolio_rows])
    radar_set = set([r["الرمز"] for r in filtered_results])

    ordered_symbols = (
        sorted(list(port_set))
        + [r["الرمز"] for r in filtered_results if r["الرمز"] not in port_set]
        + sorted([s for s in all_analyzed_map.keys() if s not in port_set and s not in radar_set])
    )

    def _format_sym_option(sym: str) -> str:
        info = all_analyzed_map[sym]
        prefix = "💼 [محفظتي] " if sym in port_set else ("🎯 [رادار] " if sym in radar_set else "📌 ")
        return f"{prefix}{sym} ({info['اسم الشركة'][:24]})  |  {info['الرأي اللحظي']}  |  السكور: {info['السكور']}/100"

    sel_col1, _ = st.columns([1.8, 1])
    with sel_col1:
        selected_symbol = st.selectbox(
            f"🔬 اختر أي سهم من البورصة ({len(ordered_symbols)} سهم متاح — اكتب الرمز للبحث الفوري):",
            options=ordered_symbols,
            format_func=_format_sym_option
        )
    selected_data = all_analyzed_map[selected_symbol]

    sub_view = st.radio(
        "📑 اختر نوع التحليل التفصيلي:",
        options=[
            "⚡ التدفق اللحظي وعمق السوق",
            "🌊 موجات إليوت (Elliott Wave)",
            "📈 الشارت الفني وخطة التنفيذ",
            "📊 التحليل المالي (F-Score)",
            "🪐 التحليل الزمني (جان والكواكب)",
            "📰 الرادار الخبري"
        ],
        horizontal=True
    )

    if "التدفق اللحظي" in sub_view:
        flow = selected_data["intraday_flow"]
        tv_r = selected_data.get("tv_raw", {})
        st.markdown(f"#### ⚡ تحليل التدفق اللحظي ورأي الاتجاه أثناء الجلسة: {selected_symbol}")

        fk1, fk2, fk3, fk4 = st.columns(4)
        vwap_cls = "txt-green" if flow["vwap_diff_pct"] >= 0 else "txt-red"
        fk1.markdown(f'<div class="kpi-card"><div class="kpi-label">🧭 القرار اللحظي</div><div class="kpi-val" style="font-size:16px;">{flow["short_verdict"]} ({flow["flow_score"]:+d})</div></div>', unsafe_allow_html=True)
        fk2.markdown(f'<div class="kpi-card"><div class="kpi-label">⚖️ متوسط السيولة VWAP</div><div class="kpi-val {vwap_cls}">{flow["vwap"]} ({flow["vwap_diff_pct"]:+.2f}%)</div></div>', unsafe_allow_html=True)
        fk3.markdown(f'<div class="kpi-card"><div class="kpi-label">⏱️ زخم 15 دقيقة (RSI)</div><div class="kpi-val txt-cyan">{flow["rsi15"]}</div></div>', unsafe_allow_html=True)
        fk4.markdown(f'<div class="kpi-card" style="border-top-color:#FACC15;"><div class="kpi-label">💧 وتيرة السيولة الآن</div><div class="kpi-val txt-gold">{flow["rel_vol"]}x</div></div>', unsafe_allow_html=True)

        st.write("")
        fl_col1, fl_col2 = st.columns([1.2, 1])

        with fl_col1:
            reasons_html = "".join([f"<li style='margin-bottom:6px;'>{r_txt}</li>" for r_txt in flow["reasons"]])
            st.markdown(f"""
            <div class="pro-card">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
                    <h4 class="txt-cyan" style="margin:0;">🩺 التشخيص اللحظي: {selected_symbol}</h4>
                    <span class="{flow['badge_cls']}">{flow['verdict']}</span>
                </div>
                <p class="txt-white"><b>أفضل طلب وعرض:</b> {flow['ba_pressure']} (السبريد: {flow['spread_pct']}%)</p>
                <p class="txt-white"><b>مؤشر MACD (15 دقيقة):</b> {flow['macd15']} مقابل الإشارة {flow['macds15']}</p>
                <hr style="border-color:#26334D;">
                <ul class="txt-white" style="padding-right:18px;font-size:14px;">
                    {reasons_html}
                </ul>
                <div style="background:#0B0F19;padding:10px 12px;border-radius:8px;border-right:4px solid #38BDF8;margin-top:10px;">
                    <b class="txt-gold">💡 الخلاصة التنفيذية:</b> <span class="txt-white">{flow['action_hint']}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with fl_col2:
            st.markdown("""
            <div class="pro-card" style="border-right-color:#FACC15;">
                <h4 class="txt-gold" style="margin-top:0;">📖 حاسبة اختلال عمق السوق (Order Book Imbalance)</h4>
                <p class="txt-muted" style="font-size:13px;">أدخل إجمالي كمية الطلبات والعروض الظاهرة أمامك على شاشة Thndr أو مباشر لكشف السيولة الحقيقية من الجدران الوهمية:</p>
            </div>
            """, unsafe_allow_html=True)

            ob_c1, ob_c2 = st.columns(2)
            with ob_c1:
                bid_qty = st.number_input("🟢 إجمالي كمية الطلبات (Bid Qty):", min_value=0, value=150000, step=10000, key=f"bid_q_{selected_symbol}")
            with ob_c2:
                ask_qty = st.number_input("🔴 إجمالي كمية العروض (Ask Qty):", min_value=0, value=80000, step=10000, key=f"ask_q_{selected_symbol}")

            top_wall_qty = st.number_input("🧱 أكبر كمية معلقة على سعر واحد (اختياري لكشف التلاعب):", min_value=0, value=0, step=10000, key=f"wall_q_{selected_symbol}")

            total_ob = bid_qty + ask_qty
            if total_ob > 0:
                imb_pct = ((bid_qty - ask_qty) / total_ob) * 100.0
                ba_ratio = bid_qty / max(1, ask_qty)
                avg_v10 = tv_r.get("avg_vol10", 0.0)

                wall_warning = ""
                if top_wall_qty > 0 and avg_v10 > 0 and top_wall_qty >= (avg_v10 * 0.25):
                    wall_warning = f"<p class='txt-gold' style='margin-top:8px;'>⚠️ <b>تنبيه جدار ضخم (Spoofing المحتمل):</b> الكمية المعلقة ({top_wall_qty:,}) تمثل أكثر من 25% من متوسط تداول السهم اليومي؛ راقب هل تُسحب عند اقتراب السعر أم تُنفَّذ.</p>"

                if imb_pct >= 20.0:
                    ob_verdict = "🟢 تفوق شرائي واضح في العمق (الطلبات تبتلع العروض)"
                    ob_cls = "txt-green"
                elif imb_pct <= -20.0:
                    ob_verdict = "🔴 ضغط بيعي واضح في العمق (العروض تتفوق على الطلبات)"
                    ob_cls = "txt-red"
                else:
                    ob_verdict = "🟡 توازن نسبي في عمق الطلبات والعروض"
                    ob_cls = "txt-gold"

                if imb_pct >= 20.0 and flow["flow_score"] >= 20:
                    combined_call = "🚀 <b>توافق صعودي قوي:</b> السعر فوق VWAP والطلبات تتفوق في العمق."
                elif imb_pct <= -20.0 and flow["flow_score"] <= -20:
                    combined_call = "🚨 <b>توافق هبوطي:</b> كسر VWAP مع ضغط عروض بيعية في العمق."
                elif imb_pct <= -25.0 and flow["flow_score"] >= 25:
                    combined_call = "🐋 <b>احتمال امتصاص حيتان:</b> عروض كبيرة في العمق لكن السعر صامد أعلى VWAP (قد تكون عروض تخويف للتجميع)."
                else:
                    combined_call = "⚖️ <b>قراءة متباينة:</b> راقب سرعة تنفيذ الصفقات على العروض قبل زيادة الكمية."

                st.markdown(f"""
                <div class="pro-card">
                    <p class="txt-white"><b>نسبة اختلال العمق (Imbalance):</b> <span class="{ob_cls}" style="font-size:17px;font-weight:bold;">{imb_pct:+.1f}%</span> (نسبة الطلب/العرض: {ba_ratio:.2f}x)</p>
                    <p class="{ob_cls}"><b>تقييم العمق:</b> {ob_verdict}</p>
                    {wall_warning}
                    <hr style="border-color:#26334D;">
                    <p class="txt-white" style="margin-bottom:0;">{combined_call}</p>
                </div>
                """, unsafe_allow_html=True)

    elif "موجات إليوت" in sub_view:
        df_ew_hist = fetch_single_stock_history(selected_data["Ticker"])
        st.markdown(f"#### 🌊 الترقيم الموجي الآلي وفق نظرية إليوت (Elliott Wave): {selected_symbol}")

        if df_ew_hist.empty or len(df_ew_hist) < 20:
            st.info(f"ℹ️ الشموع التاريخية للسهم **{selected_symbol}** غير كافية على Yahoo Finance لترقيم موجات إليوت بعد.")
        else:
            ew_ctrl1, ew_ctrl2 = st.columns([1.4, 1])
            with ew_ctrl1:
                wave_degree = st.radio(
                    "🎚️ درجة الموجات (حساسية ZigZag):",
                    options=[
                        "موجات متوسطة (Intermediate — 5%)",
                        "موجات قصيرة/فرعية (Minor — 3%)",
                        "موجات رئيسية (Primary — 8%)"
                    ],
                    horizontal=True,
                    key=f"ew_deg_{selected_symbol}"
                )
            with ew_ctrl2:
                ew_lookback = st.selectbox(
                    "📅 المدى الزمني للترقيم:",
                    options=[120, 180, 260, 450],
                    index=1,
                    format_func=lambda d: f"آخر {d} جلسة تداول",
                    key=f"ew_lb_{selected_symbol}"
                )

            pct_val = 0.03 if "3%" in wave_degree else (0.08 if "8%" in wave_degree else 0.05)
            df_ew = df_ew_hist.tail(ew_lookback)
            ew_res = analyze_elliott_waves(df_ew, pct_thresh=pct_val)

            ek1, ek2, ek3, ek4 = st.columns(4)
            ek1.markdown(f'<div class="kpi-card"><div class="kpi-label">🌊 الموجة الحالية</div><div class="kpi-val" style="font-size:15px;">{ew_res["wave_name"]}</div></div>', unsafe_allow_html=True)
            ek2.markdown(f'<div class="kpi-card" style="border-top-color:#EF4444;"><div class="kpi-label">🛑 نقطة إلغاء الترقيم</div><div class="kpi-val txt-red">{ew_res["invalidation"]} ج.م</div></div>', unsafe_allow_html=True)
            ek3.markdown(f'<div class="kpi-card" style="border-top-color:#22C55E;"><div class="kpi-label">🎯 هدف فيبوناتشي #1</div><div class="kpi-val txt-green">{ew_res["target_1"]} ج.م</div></div>', unsafe_allow_html=True)
            ek4.markdown(f'<div class="kpi-card" style="border-top-color:#FACC15;"><div class="kpi-label">🏆 هدف فيبوناتشي #2</div><div class="kpi-val txt-gold">{ew_res["target_2"]} ج.م</div></div>', unsafe_allow_html=True)

            st.write("")
            ew_c1, ew_c2 = st.columns([2.1, 1])

            with ew_c1:
                fig_ew = go.Figure()
                fig_ew.add_trace(go.Candlestick(
                    x=df_ew.index, open=df_ew["Open"], high=df_ew["High"],
                    low=df_ew["Low"], close=df_ew["Close"], name="السعر"
                ))

                lp = ew_res["labeled_pivots"]
                if lp:
                    piv_x = [p["date"] for p in lp]
                    piv_y = [p["price"] for p in lp]
                    piv_txt = [f"{p['label']}<br>{p['price']:.2f}" for p in lp]
                    piv_pos = ["top center" if p["type"] == "H" else "bottom center" for p in lp]

                    fig_ew.add_trace(go.Scatter(
                        x=piv_x, y=piv_y,
                        mode="lines+markers+text",
                        line=dict(color="#38BDF8", width=2.8),
                        marker=dict(size=10, color="#FACC15", line=dict(color="#0B0F19", width=1.5)),
                        text=piv_txt,
                        textposition=piv_pos,
                        textfont=dict(color="#FFFFFF", size=12, family="Arial Black"),
                        name="ترقيم إليوت"
                    ))

                fig_ew.add_hline(y=ew_res["invalidation"], line_dash="dash", line_color="#F87171", annotation_text=f"إلغاء الترقيم: {ew_res['invalidation']}", annotation_font_color="#F87171")
                fig_ew.add_hline(y=ew_res["target_1"], line_dash="dot", line_color="#4ADE80", annotation_text=f"هدف 1: {ew_res['target_1']}", annotation_font_color="#4ADE80")
                fig_ew.add_hline(y=ew_res["target_2"], line_dash="dot", line_color="#FACC15", annotation_text=f"هدف 2: {ew_res['target_2']}", annotation_font_color="#FACC15")

                fig_ew.update_layout(
                    title=dict(text=f"🌊 خريطة موجات إليوت على شارت {selected_symbol}", font=dict(color="#FFFFFF", size=16)),
                    height=520, xaxis_rangeslider_visible=False, template="plotly_dark",
                    paper_bgcolor="#0B0F19", plot_bgcolor="#131C31", font=dict(color="#FFFFFF"),
                    margin=dict(l=10, r=10, t=45, b=10)
                )
                st.plotly_chart(fig_ew, use_container_width=True)

            with ew_c2:
                st.markdown(f"""
                <div class="pro-card">
                    <h4 class="txt-cyan" style="margin-top:0;">🧭 القراءة الموجية: {selected_symbol}</h4>
                    <p><span class="{ew_res['badge_cls']}">{ew_res['wave_name']}</span></p>
                    <p class="txt-white"><b>النمط الموجي:</b> {ew_res['pattern_type']}</p>
                    <hr style="border-color:#26334D;">
                    <p class="txt-white" style="font-size:14px;line-height:1.6;">{ew_res['summary']}</p>
                    <hr style="border-color:#26334D;">
                    <p class="txt-white"><b>نقطة إلغاء السيناريو:</b> <span class="txt-red">{ew_res['invalidation']} ج.م</span></p>
                    <p class="txt-white"><b>المستهدف الأول:</b> <span class="txt-green">{ew_res['target_1']} ج.م</span></p>
                    <p class="txt-white"><b>المستهدف الثاني:</b> <span class="txt-gold">{ew_res['target_2']} ج.م</span></p>
                </div>
                """, unsafe_allow_html=True)

                if ew_res["rules_check"]:
                    st.markdown("##### ✅ فحص قواعد إليوت الحاكمة")
                    df_rules = pd.DataFrame(ew_res["rules_check"], columns=["القاعدة / المعيار", "القيمة", "الحالة"])
                    df_rules["الحالة"] = df_rules["الحالة"].map({True: "✅ محقق", False: "⚠️ مراقبة"})
                    st.dataframe(df_rules, use_container_width=True, hide_index=True)

                if lp:
                    st.markdown("##### 📍 إحداثيات القمم والقيعان المرقّمة")
                    piv_rows = [
                        {
                            "الموجة": p["label"],
                            "النوع": "قمة ⬆️" if p["type"] == "H" else "قاع ⬇️",
                            "التاريخ": str(p["date"])[:10],
                            "السعر": round(p["price"], 2)
                        }
                        for p in lp
                    ]
                    st.dataframe(pd.DataFrame(piv_rows), use_container_width=True, hide_index=True)

    elif "الشارت الفني" in sub_view:
        df_hist_sel = fetch_single_stock_history(selected_data["Ticker"])
        c_chart, c_plan = st.columns([2.1, 1])
        with c_chart:
            if df_hist_sel.empty:
                st.info(f"ℹ️ الشموع التاريخية للسهم **{selected_symbol}** غير متوفرة حالياً على Yahoo Finance. السعر اللحظي الحالي من TradingView: **{selected_data['الإغلاق']} ج.م**.")
                st.link_button(f"🚀 افتح شارت {selected_symbol} على TradingView ↗", selected_data["TradingView"], use_container_width=True)
            else:
                df_chart = df_hist_sel.tail(120)
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
                marker_color=["#F59E0B", "#38BDF8", "#4ADE80"],
                text=[f"{v} نقطة" for v in parts.values()], textposition="auto", textfont=dict(color="#FFFFFF")
            ))
            fig_score.update_layout(
                title=dict(text="🧩 تفكيك نقاط السكور الديناميكي", font=dict(color="#FFFFFF", size=14)),
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
        df_time = fetch_single_stock_history(selected_data["Ticker"])
        if df_time.empty:
            st.info(f"ℹ️ الشموع التاريخية للسهم **{selected_symbol}** غير متوفرة حالياً لرسم خريطة جان.")
        else:
            st.markdown(f"#### 🪐 التحليل الزمني والفلكي (Gann Squaring + Planetary Cycles): {selected_symbol}")
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

# ==========================================
# حلقة التحديث التلقائي الحي كل 5 دقائق عند التفعيل
# ==========================================
if live_auto:
    time.sleep(300)
    st.session_state["refresh_nonce"] = refresh_nonce + 1
    st.session_state["force_cloud_sync"] = True
    fetch_full_egx_tv_scanner.clear()
    st.rerun()