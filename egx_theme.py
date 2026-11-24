"""
EGX Whale Hunter — نظام التصميم (V11.5)
وضعين: داكن (Terminal) وفاتح (Fintech). كل الألوان tokens في مكان واحد،
والـ CSS والشارتات بيقروا منها، فأي تعديل في لون بيتطبق على البرنامج كله.
"""
import copy

PALETTES = {
    "dark": {  # Terminal: كحلي عميق + سيان، أرقام mono
        "bg": "#060A13", "bg2": "#0A1120", "surface": "#0D1526", "surface2": "#121C30",
        "border": "#1C2940", "border2": "#2A3A57", "text": "#E7EEF8", "muted": "#8496B0",
        "accent": "#22D3EE", "accent2": "#818CF8", "on_accent": "#04111A",
        "up": "#34D399", "down": "#FB7185", "gold": "#FBBF24",
        "up_bg": "rgba(52,211,153,.12)", "down_bg": "rgba(251,113,133,.12)", "gold_bg": "rgba(251,191,36,.12)",
        "glow": "rgba(34,211,238,.16)", "grid": "rgba(148,163,184,.045)",
        "shadow": "0 10px 30px rgba(0,0,0,.45)", "plotly_base": "plotly_dark",
    },
    "light": {  # Fintech: أبيض نظيف + نيلي
        "bg": "#F4F6FB", "bg2": "#EAEFF8", "surface": "#FFFFFF", "surface2": "#F6F8FC",
        "border": "#E3E8F0", "border2": "#CBD5E1", "text": "#0B1220", "muted": "#5B6B82",
        "accent": "#4F46E5", "accent2": "#0891B2", "on_accent": "#FFFFFF",
        "up": "#047857", "down": "#DC2626", "gold": "#B45309",
        "up_bg": "#ECFDF5", "down_bg": "#FEF2F2", "gold_bg": "#FFFBEB",
        "glow": "rgba(79,70,229,.10)", "grid": "rgba(15,23,42,.035)",
        "shadow": "0 8px 24px rgba(15,23,42,.07)", "plotly_base": "plotly_white",
    },
}

FONT_URL = "https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800;900&family=IBM+Plex+Mono:wght@500;600;700&display=swap"


def palette(mode: str) -> dict:
    return PALETTES["dark" if mode == "dark" else "light"]


def build_css(mode: str) -> str:
    p = palette(mode)
    v = "\n".join(f"  --{k.replace('_', '-')}: {val};" for k, val in p.items() if k != "plotly_base")
    dark = mode == "dark"
    grid_bg = (f"linear-gradient(var(--grid) 1px, transparent 1px) 0 0/28px 28px, "
               f"linear-gradient(90deg, var(--grid) 1px, transparent 1px) 0 0/28px 28px, ") if dark else ""
    return f"""
<style>
@import url('{FONT_URL}');
:root {{
{v}
  --radius: 14px; --mono: 'IBM Plex Mono', 'Cairo', ui-monospace, monospace;
}}
html, body, [class*="css"], .stApp, .stMarkdown, button, input, textarea, select {{ font-family: 'Cairo', sans-serif !important; }}

/* ---------- الخلفية ---------- */
.stApp, [data-testid="stAppViewContainer"] {{
  background:
    radial-gradient(1100px 520px at 100% -10%, var(--glow), transparent 60%),
    radial-gradient(900px 480px at -10% 0%, {"rgba(129,140,248,.10)" if dark else "rgba(8,145,178,.07)"}, transparent 55%),
    {grid_bg}var(--bg) !important;
  color: var(--text) !important;
}}
[data-testid="stHeader"] {{ background: transparent !important; }}
.block-container {{ direction: rtl; text-align: right; padding-top: 1rem; padding-bottom: 3rem; max-width: 1480px; }}
.stApp p, .stApp li, .stApp span, .stApp label, .stMarkdown, h1, h2, h3, h4, h5, h6 {{ color: var(--text); }}
h3, h4, h5 {{ font-weight: 800 !important; letter-spacing: .2px; }}
[data-testid="stCaptionContainer"], .stCaption, small {{ color: var(--muted) !important; }}
hr {{ border-color: var(--border) !important; }}
::selection {{ background: var(--accent); color: var(--on-accent); }}
::-webkit-scrollbar {{ width: 10px; height: 10px; }}
::-webkit-scrollbar-thumb {{ background: var(--border2); border-radius: 10px; border: 2px solid var(--bg); }}
::-webkit-scrollbar-track {{ background: transparent; }}

/* ---------- الهيدر ---------- */
.hero-banner {{
  position: relative; overflow: hidden;
  background: linear-gradient(135deg, var(--surface) 0%, var(--surface2) 100%);
  border: 1px solid var(--border); border-radius: 18px; padding: 18px 24px; margin-bottom: 12px;
  box-shadow: var(--shadow); display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;
}}
.hero-banner::before {{
  content: ""; position: absolute; inset: 0 0 auto 0; height: 3px;
  background: linear-gradient(90deg, var(--accent), var(--accent2), var(--gold));
}}
.hero-title {{ font-size: 26px; font-weight: 900; color: var(--text); letter-spacing: .4px; line-height: 1.25; }}
.hero-accent {{ background: linear-gradient(90deg, var(--accent), var(--accent2)); -webkit-background-clip: text; background-clip: text; color: transparent; }}
.hero-ver {{ font-family: var(--mono); font-size: 12px; color: var(--gold); border: 1px solid var(--gold); border-radius: 999px; padding: 1px 8px; vertical-align: middle; margin-right: 6px; }}
.hero-sub {{ font-size: 13px; color: var(--muted); margin-top: 4px; }}
.session-pill {{
  display: inline-flex; align-items: center; gap: 8px; background: var(--surface2);
  border: 1px solid var(--border2); color: var(--text); padding: 8px 16px; border-radius: 999px; font-weight: 800; font-size: 13px;
}}
.session-pill::before {{ content: ""; width: 8px; height: 8px; border-radius: 50%; background: var(--up); box-shadow: 0 0 0 0 var(--up); animation: pulse 1.8s infinite; }}
@keyframes pulse {{ 0% {{ box-shadow: 0 0 0 0 rgba(52,211,153,.55); }} 70% {{ box-shadow: 0 0 0 9px rgba(52,211,153,0); }} 100% {{ box-shadow: 0 0 0 0 rgba(52,211,153,0); }} }}

/* ---------- شريط الأسعار ---------- */
.ticker {{ direction: ltr; overflow: hidden; border: 1px solid var(--border); background: var(--surface); border-radius: 12px; margin-bottom: 14px; mask-image: linear-gradient(90deg, transparent, #000 6%, #000 94%, transparent); }}
.ticker-track {{ display: inline-flex; gap: 28px; padding: 9px 0; white-space: nowrap; animation: marquee 60s linear infinite; direction: ltr; }}
.ticker:hover .ticker-track {{ animation-play-state: paused; }}
.tk {{ font-family: var(--mono); font-size: 13px; color: var(--muted); }}
.tk b {{ color: var(--text); margin-right: 6px; font-weight: 700; }}
@keyframes marquee {{ from {{ transform: translateX(0); }} to {{ transform: translateX(-50%); }} }}
@media (prefers-reduced-motion: reduce) {{ .ticker-track, .session-pill::before {{ animation: none; }} }}

/* ---------- التبويبات ---------- */
.stTabs [data-baseweb="tab-list"], .stTabs [role="tablist"] {{
  gap: 6px; background: var(--surface); padding: 6px; border-radius: 14px; border: 1px solid var(--border);
  flex-wrap: wrap; box-shadow: var(--shadow);
}}
.stTabs [data-baseweb="tab"], .stTabs [data-testid="stTab"] {{
  height: 40px; background: transparent; border-radius: 10px; color: var(--muted) !important;
  font-weight: 700; font-size: 14px; padding: 0 14px; border: 1px solid transparent !important; box-shadow: none; transition: all .18s ease;
}}
.stTabs [data-testid="stTab"]::after, .stTabs [data-testid="stTab"]::before {{ display: none !important; }}
.stTabs > div:first-child {{ border: none !important; box-shadow: none !important; }}
.stTabs [data-baseweb="tab"] p, .stTabs [data-testid="stTab"] p {{ color: inherit !important; }}
.stTabs [data-baseweb="tab"]:hover, .stTabs [data-testid="stTab"]:hover {{ background: var(--surface2); color: var(--text) !important; border-color: var(--border); }}
.stTabs [aria-selected="true"], .stTabs [data-testid="stTab"][data-selected="true"] {{
  background: linear-gradient(135deg, var(--accent), var(--accent2)) !important; color: var(--on-accent) !important;
  border-color: transparent !important; box-shadow: 0 6px 18px var(--glow) !important;
}}
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] {{ display: none; }}

/* ---------- البطاقات ---------- */
.kpi-card {{
  position: relative; background: var(--surface); border: 1px solid var(--border); border-top: 3px solid var(--accent);
  border-radius: var(--radius); padding: 14px 16px; text-align: center; box-shadow: var(--shadow);
  transition: transform .18s ease, border-color .18s ease;
}}
.kpi-card:hover {{ transform: translateY(-2px); border-color: var(--border2); }}
.kpi-label {{ font-size: 12px; color: var(--muted); margin-bottom: 6px; font-weight: 700; }}
.kpi-val {{ font-family: var(--mono); font-size: 21px; font-weight: 700; color: var(--text); font-variant-numeric: tabular-nums; }}
.pro-card {{
  background: var(--surface); border: 1px solid var(--border); border-right: 4px solid var(--accent);
  border-radius: var(--radius); padding: 16px 18px; margin-bottom: 12px; box-shadow: var(--shadow);
}}
.top-card {{
  background: linear-gradient(180deg, var(--surface) 0%, var(--surface2) 100%); border: 1px solid var(--border);
  border-radius: 16px; padding: 16px; margin-bottom: 10px; box-shadow: var(--shadow); transition: transform .2s ease, box-shadow .2s ease;
}}
.top-card:hover {{ transform: translateY(-3px); box-shadow: 0 14px 34px var(--glow); }}
.top-card-gold {{ border: 1px solid var(--gold); box-shadow: 0 0 0 1px var(--gold-bg), 0 10px 30px var(--gold-bg); }}
.top-card-strip {{ display: flex; justify-content: space-between; background: var(--bg2); padding: 8px 10px; border-radius: 10px; font-size: 12px; font-family: var(--mono); }}
.stock-header-strip {{
  background: linear-gradient(90deg, var(--surface) 0%, var(--surface2) 100%); border: 1px solid var(--border);
  border-right: 5px solid var(--gold); border-radius: var(--radius); padding: 14px 20px; margin-bottom: 14px;
  display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px; box-shadow: var(--shadow);
}}
.news-item {{ background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 12px 15px; margin-bottom: 8px; transition: border-color .18s; }}
.news-item:hover {{ border-color: var(--accent); }}

/* ---------- الشارات والتنبيهات ---------- */
.badge-bull, .badge-bear, .badge-warn {{ padding: 3px 10px; border-radius: 999px; font-size: 12px; font-weight: 700; white-space: nowrap; }}
.badge-bull {{ background: var(--up-bg); color: var(--up); border: 1px solid var(--up); }}
.badge-bear {{ background: var(--down-bg); color: var(--down); border: 1px solid var(--down); }}
.badge-warn {{ background: var(--gold-bg); color: var(--gold); border: 1px solid var(--gold); }}
.alert-box-success, .alert-box-warn, .alert-box-danger {{ border-radius: 12px; padding: 12px 16px; margin-bottom: 10px; color: var(--text); animation: fadeIn .35s ease; border: 1px solid var(--border); }}
.alert-box-success {{ background: var(--up-bg); border-right: 5px solid var(--up); }}
.alert-box-warn {{ background: var(--gold-bg); border-right: 5px solid var(--gold); }}
.alert-box-danger {{ background: var(--down-bg); border-right: 5px solid var(--down); }}
@keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(4px); }} to {{ opacity: 1; transform: none; }} }}

.txt-green {{ color: var(--up) !important; }} .txt-red {{ color: var(--down) !important; }} .txt-gold {{ color: var(--gold) !important; }}
.txt-cyan {{ color: var(--accent) !important; }} .txt-white {{ color: var(--text) !important; }} .txt-muted {{ color: var(--muted) !important; }}
.num {{ font-family: var(--mono); font-variant-numeric: tabular-nums; }}

/* ---------- عناصر Streamlit ---------- */
div[data-baseweb="input"], div[data-baseweb="base-input"], div[data-baseweb="select"] > div, div[data-baseweb="textarea"], input, textarea {{
  background-color: var(--surface) !important; color: var(--text) !important; border-color: var(--border2) !important; border-radius: 10px !important;
}}
input::placeholder, textarea::placeholder {{ color: var(--muted) !important; }}
ul[data-baseweb="menu"], div[data-baseweb="popover"] > div {{ background: var(--surface) !important; color: var(--text) !important; }}
button[data-testid="stNumberInputStepDown"], button[data-testid="stNumberInputStepUp"] {{ background: var(--surface2) !important; color: var(--text) !important; }}
label, label p, [data-testid="stWidgetLabel"] p {{ color: var(--text) !important; font-weight: 600 !important; }}
.stButton > button, .stDownloadButton > button, .stLinkButton > a, [data-testid="stFormSubmitButton"] > button {{
  background: var(--surface) !important; color: var(--text) !important; border: 1px solid var(--border2) !important;
  border-radius: 11px !important; font-weight: 700 !important; transition: all .18s ease;
}}
.stButton > button:hover, .stDownloadButton > button:hover, .stLinkButton > a:hover, [data-testid="stFormSubmitButton"] > button:hover {{
  border-color: var(--accent) !important; color: var(--accent) !important; transform: translateY(-1px);
}}
.stButton > button[kind="primary"], [data-testid="stFormSubmitButton"] > button[kind="primaryFormSubmit"] {{
  background: linear-gradient(135deg, var(--accent), var(--accent2)) !important; color: var(--on-accent) !important;
  border: none !important; box-shadow: 0 6px 18px var(--glow);
}}
.stButton > button[kind="primary"]:hover {{ filter: brightness(1.08); color: var(--on-accent) !important; }}
[data-testid="stExpander"] details, [data-testid="stFileUploaderDropzone"], [data-testid="stForm"] {{
  background: var(--surface) !important; border: 1px solid var(--border) !important; border-radius: var(--radius) !important;
}}
[data-testid="stExpander"] summary:hover {{ color: var(--accent) !important; }}
[data-testid="stDataFrame"], [data-testid="stDataEditor"], [data-testid="stPlotlyChart"] {{
  border: 1px solid var(--border); border-radius: var(--radius); overflow: hidden; background: var(--surface);
}}
[data-testid="stPlotlyChart"] {{ padding: 6px; }}
[data-testid="stAlert"] {{ border-radius: 12px !important; }}
[data-testid="stMetricValue"] {{ font-family: var(--mono); }}
[data-testid="stSidebar"] {{ background: var(--surface) !important; border-left: 1px solid var(--border); }}
@media (max-width: 760px) {{
  .hero-title {{ font-size: 20px; }} .kpi-val {{ font-size: 17px; }} .block-container {{ padding-left: .8rem; padding-right: .8rem; }}
}}
</style>"""


def plotly_template(mode: str):
    """قالب Plotly بخلفية شفافة وألوان النظام."""
    import plotly.io as pio
    p = palette(mode)
    name = f"egx_{mode}"
    if name not in pio.templates:
        t = copy.deepcopy(pio.templates[p["plotly_base"]])
        t.layout.paper_bgcolor = "rgba(0,0,0,0)"
        t.layout.plot_bgcolor = "rgba(0,0,0,0)"
        t.layout.font = dict(family="Cairo, sans-serif", color=p["text"], size=13)
        t.layout.colorway = [p["accent"], p["gold"], p["up"], p["down"], p["accent2"], "#F472B6", "#A3E635"]
        for ax in ("xaxis", "yaxis"):
            getattr(t.layout, ax).gridcolor = p["border"]
            getattr(t.layout, ax).zerolinecolor = p["border2"]
            getattr(t.layout, ax).linecolor = p["border2"]
        t.layout.hoverlabel = dict(bgcolor=p["surface2"], bordercolor=p["border2"], font=dict(color=p["text"], family="IBM Plex Mono, Cairo"))
        t.layout.legend = dict(bgcolor="rgba(0,0,0,0)")
        t.data.candlestick = [dict(increasing=dict(line=dict(color=p["up"]), fillcolor=p["up"]),
                                   decreasing=dict(line=dict(color=p["down"]), fillcolor=p["down"]))]
        pio.templates[name] = t
    return name


def ticker_html(items: list) -> str:
    """items: [(symbol, price, change%)] — بيتكرر مرتين عشان الحركة تبان متصلة."""
    if not items:
        return ""
    cells = "".join(
        f'<span class="tk"><b>{s}</b>{px:,.2f} <span class="{"txt-green" if ch >= 0 else "txt-red"}">{"▲" if ch >= 0 else "▼"} {ch:+.2f}%</span></span>'
        for s, px, ch in items)
    return f'<div class="ticker"><div class="ticker-track">{cells}{cells}</div></div>'
