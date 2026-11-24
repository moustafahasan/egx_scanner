"""
EGX Whale Hunter — مكونات الواجهة الجديدة (V11.5): غرفة القيادة + كروت الفرص.
دوال HTML نقية (من غير Streamlit) عشان تتختبر لوحدها؛ الألوان كلها CSS variables من egx_theme.
"""
from html import escape

NAV = {
    "command": "🛰️ القيادة",
    "opps": "🃏 الفرص",
    "portfolio": "💼 محفظتي",
    "lab": "🔬 السهم",
    "settings": "⚙️ الإعدادات",
}


def mood_score(breadth_pct: float, vwap_breadth_pct: float) -> int:
    """0..100: 60% نسبة الأسهم الخضرا + 40% نسبة الأسهم فوق VWAP."""
    return int(round(max(0.0, min(100.0, 0.6 * breadth_pct + 0.4 * vwap_breadth_pct))))


def mood_label(score: int) -> tuple:
    if score >= 60:
        return "إيجابي", "up"
    if score <= 40:
        return "سلبي", "down"
    return "محايد", "gold"


def gauge_svg(score: int, size: int = 150) -> str:
    """نصف دايرة من الأحمر للأخضر، والمؤشر عند السكور."""
    import math
    s = max(0, min(100, int(score)))
    ang = math.pi * (1 - s / 100.0)
    cx, cy, r = 75, 72, 58
    x, y = cx + r * math.cos(ang), cy - r * math.sin(ang)
    large = 0
    return (f'<svg viewBox="0 0 150 86" width="{size}" class="gauge" role="img" aria-label="مزاج السوق {s} من 100">'
            f'<defs><linearGradient id="gg" x1="0" x2="1"><stop offset="0" stop-color="var(--down)"/>'
            f'<stop offset=".5" stop-color="var(--gold)"/><stop offset="1" stop-color="var(--up)"/></linearGradient></defs>'
            f'<path d="M17 72 A58 58 0 0 1 133 72" stroke="var(--border)" stroke-width="12" fill="none" stroke-linecap="round"/>'
            f'<path d="M17 72 A58 58 0 {large} 1 {x:.1f} {y:.1f}" stroke="url(#gg)" stroke-width="12" fill="none" stroke-linecap="round"/>'
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="6.5" fill="var(--text)" stroke="var(--surface)" stroke-width="3"/>'
            f'<text x="75" y="70" text-anchor="middle" class="gauge-num">{s}</text></svg>')


def kpi(label: str, value: str, sub: str = "", tone: str = "") -> str:
    return (f'<div class="cc-kpi"><div class="cc-kpi-l">{label}</div>'
            f'<div class="cc-kpi-v {("t-" + tone) if tone else ""}">{value}</div>'
            f'<div class="cc-kpi-s">{sub}</div></div>')


def mood_card(score: int, breadth: float, vwap_b: float) -> str:
    lbl, tone = mood_label(score)
    return (f'<div class="cc-kpi cc-mood">{gauge_svg(score, 132)}<div><div class="cc-kpi-l">مزاج السوق</div>'
            f'<div class="cc-kpi-v t-{tone}" style="font-family:Cairo">{lbl}</div>'
            f'<div class="cc-kpi-s mono">Breadth {breadth:.0f}% • VWAP {vwap_b:.0f}%</div></div></div>')


def score_ring(score: int, size: int = 92) -> str:
    s = max(0, min(100, int(score)))
    tone = "var(--up)" if s >= 80 else ("var(--accent)" if s >= 65 else "var(--gold)")
    return (f'<div class="ring" style="--p:{s};--c:{tone};width:{size}px;height:{size}px">'
            f'<b class="mono">{s}</b></div>')


def _parts_bars(parts: dict) -> str:
    rows = []
    for name, val in (parts or {}).items():
        mx = 35 if "35" in name else 30
        lbl = name.split("(")[0].strip()
        pct = max(0, min(100, val / mx * 100))
        rows.append(f'<div class="pb"><span>{escape(lbl)}</span><i><em style="width:{pct:.0f}%"></em></i><b class="mono">{val}/{mx}</b></div>')
    return "".join(rows)


def opp_card(r: dict, rank: int = 0, in_portfolio: bool = False) -> str:
    """كارت فرصة: الهيدر + حلقة السكور + مكونات السكور + سلم الأسعار."""
    sym, name = escape(str(r["الرمز"])), escape(str(r["اسم الشركة"]))
    ch = float(r.get("التغير %") or 0)
    tags = [t.strip() for t in str(r.get("التشخيص الفني", "")).split("|") if t.strip()][:3]
    chips = "".join(f'<span class="chip">{escape(t)}</span>' for t in tags) or '<span class="chip">حركة هادئة</span>'
    medal = ["👑", "🔥", "⚡"][rank] if rank < 3 else ""
    owned = '<span class="own">💼 في محفظتك</span>' if in_portfolio else ""
    return f"""<div class="opp {'opp-top' if rank == 0 else ''}">
  <div class="opp-h"><div><div class="opp-sym">{medal} {sym}</div><div class="opp-name">{name}</div></div>
    <div class="opp-ch mono {'t-up' if ch >= 0 else 't-down'}">{ch:+.2f}%</div></div>
  <div class="opp-mid">{score_ring(r.get('السكور', 0))}<div class="opp-parts">{_parts_bars(r.get('score_parts'))}</div></div>
  <div class="chips">{chips}{owned}</div>
  <div class="lad mono">
    <div><span class="t-up">🎯 TP1</span><b>{r['TP1']}</b></div>
    <div><span>⚡ دخول</span><b>{r['الإغلاق']}</b></div>
    <div><span class="t-down">🛑 وقف</span><b>{r['الوقف (2xATR)']}</b></div>
  </div>
  <div class="opp-f"><span>{escape(str(r.get('الرأي اللحظي', '')))}</span><span class="mono">{int(r.get('الأسهم') or 0):,} سهم • صافي {float(r.get('صافي TP1') or 0):,.0f}</span></div>
</div>"""


def feed_html(events: list) -> str:
    """events: [(tone, title, body)] tone in up/down/gold/accent."""
    if not events:
        return '<div class="feed-empty">مفيش أحداث لحد دلوقتي — البث بيتحدث مع كل تحديث للأسعار.</div>'
    return "".join(f'<div class="ev ev-{t}"><b>{title}</b><div>{body}</div></div>' for t, title, body in events)


def positions_html(rows: list) -> str:
    """شريط لكل مركز من الوقف للهدف، والعلامة مكان السعر الحالي."""
    if not rows:
        return '<div class="feed-empty">محفظتك فاضية — ضيف سهم من كروت الفرص (➕) أو من تبويب محفظتي.</div>'
    out = []
    for p in rows:
        ratio = float(p.get("progress_ratio", 0) or 0)
        pct = float(p.get("العائد %", 0) or 0)
        out.append(f"""<div class="pos">
  <div class="pos-h"><b>{escape(str(p['الرمز']))}</b><span class="mono {'t-up' if pct >= 0 else 't-down'}">{pct:+.2f}%</span></div>
  <div class="track"><i style="inset-inline-start:{ratio * 100:.0f}%"></i></div>
  <div class="pos-f mono"><span>SL {p['وقف الخسارة']}</span><span>{p['السعر الحالي']}</span><span>TP1 {p['TP1']}</span></div>
  <div class="pos-s">{escape(str(p.get('حالة التنبيه', '')))}</div>
</div>""")
    return '<div class="pos-grid">' + "".join(out) + "</div>"


def resolve_symbol(q: str, analyzed: dict) -> str:
    """الرمز بالظبط، أو أول رمز بيبدأ بيه، أو أول شركة اسمها فيه الكلمة."""
    q = (q or "").strip()
    if not q:
        return ""
    up = q.upper().replace(".CA", "")
    if up in analyzed:
        return up
    starts = sorted(s for s in analyzed if s.startswith(up))
    if starts:
        return starts[0]
    for s, d in analyzed.items():
        if q in str(d.get("اسم الشركة", "")):
            return s
    return ""


def build_feed(active_alerts: list, filtered: list, sent_keys: set, watch_alerts: list, limit: int = 12) -> list:
    """بث الأحداث: تنبيهات المحفظة الحالية، تنبيهات المراقبة، إشارات الحيتان اللي اتبعتت النهارده، وأقوى إشارات دلوقتي."""
    ev = []
    tone_map = {"danger": "down", "warn": "gold", "success": "up"}
    for lvl, msg in active_alerts:
        ev.append((tone_map.get(lvl, "accent"), "💼 محفظتي", msg))
    for sym, msg in watch_alerts:
        ev.append(("accent", f"📌 {escape(sym)}", msg))
    sent_whales = {k.split("_WHALE_")[-1] for k in (sent_keys or set()) if "_WHALE_" in k}
    for r in filtered:
        if len(ev) >= limit:
            break
        if r.get("السكور", 0) < 70:
            continue
        flag = " • 📲 اتبعتت" if r["الرمز"] in sent_whales else ""
        ev.append(("accent", f"🐋 {escape(str(r['الرمز']))} <span class='mono t-up'>{float(r['التغير %']):+.2f}%</span>",
                   f"سكور {r['السكور']} • سيولة {r['الفوليوم']}x • {escape(str(r['نوع الإشارة']))}{flag}"))
    return ev[:limit]


UI_CSS = """
<style>
/* ===== V11.5 — غرفة القيادة + كروت الفرص ===== */
.block-container{padding-top:.6rem!important}
.cmd-brand{display:flex;align-items:center;gap:10px;height:100%}
.cmd-logo{width:40px;height:40px;border-radius:12px;display:grid;place-items:center;font-size:21px;background:linear-gradient(135deg,var(--accent),var(--accent2));box-shadow:0 6px 18px var(--glow)}
.cmd-name{font-weight:900;font-size:19px;line-height:1.1}.cmd-name span{background:linear-gradient(90deg,var(--accent),var(--accent2));-webkit-background-clip:text;background-clip:text;color:transparent}
.cmd-ver{font-family:var(--mono);font-size:11px;color:var(--muted)}
.pills{display:flex;gap:6px;flex-wrap:wrap;justify-content:flex-end;align-items:center;height:100%}
.pill{border:1px solid var(--border2);background:var(--surface);border-radius:999px;padding:5px 12px;font-size:12.5px;font-weight:700;white-space:nowrap}
.pill .dot{display:inline-block;width:7px;height:7px;border-radius:50%;background:var(--up);margin-inline-end:6px;animation:pulse 1.8s infinite}
.t-up{color:var(--up)!important}.t-down{color:var(--down)!important}.t-gold{color:var(--gold)!important}.t-accent{color:var(--accent)!important}
.mono{font-family:var(--mono);font-variant-numeric:tabular-nums}
div[data-testid="stSegmentedControl"] button, div[data-testid="stButtonGroup"] button{border-radius:999px!important;font-weight:800!important;padding:6px 18px!important}
/* KPI */
.cc-kpi{background:var(--surface);border:1px solid var(--border);border-radius:16px;padding:12px 16px;height:118px;box-shadow:var(--shadow);display:flex;flex-direction:column;justify-content:center}
.cc-kpi-l{font-size:12.5px;color:var(--muted);font-weight:700}.cc-kpi-v{font-family:var(--mono);font-size:26px;font-weight:700;margin:2px 0}
.cc-kpi-s{font-size:12px;color:var(--muted)}
.cc-mood{flex-direction:row;align-items:center;gap:12px;justify-content:flex-start}
.gauge-num{font-family:var(--mono);font-size:22px;font-weight:700;fill:var(--text)}
.sec-t{font-size:14px;color:var(--muted);font-weight:800;margin:6px 2px 8px}
/* feed */
.feed{max-height:560px;overflow:auto;padding-inline-end:4px}
.ev{background:var(--surface);border:1px solid var(--border);border-inline-start:3px solid var(--accent);border-radius:12px;padding:9px 12px;margin-bottom:8px;font-size:13px;animation:fadeIn .35s ease}
.ev b{font-size:14px}.ev div{color:var(--muted);margin-top:2px}.ev div b{font-size:13px;color:var(--text)}
.ev-up{border-inline-start-color:var(--up)}.ev-down{border-inline-start-color:var(--down);background:var(--down-bg)}.ev-gold{border-inline-start-color:var(--gold)}
.feed-empty{color:var(--muted);font-size:13px;padding:18px;text-align:center;border:1px dashed var(--border2);border-radius:12px}
/* positions */
.pos-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:10px}
.pos{background:var(--surface);border:1px solid var(--border);border-radius:14px;padding:11px 13px}
.pos-h{display:flex;justify-content:space-between;font-size:15px}
.track{position:relative;height:8px;border-radius:9px;margin:12px 0 6px;background:linear-gradient(90deg,var(--down) 0%,var(--gold) 38%,var(--up) 100%)}
[dir=rtl] .track,.block-container .track{background:linear-gradient(270deg,var(--down) 0%,var(--gold) 38%,var(--up) 100%)}
.track i{position:absolute;top:-5px;width:5px;height:18px;border-radius:3px;background:var(--text);box-shadow:0 0 0 3px var(--surface),0 0 12px var(--text);transform:translateX(50%)}
.pos-f{display:flex;justify-content:space-between;font-size:11px;color:var(--muted)}.pos-s{font-size:12px;margin-top:4px}
/* opportunity cards */
.opp{background:linear-gradient(180deg,var(--surface),var(--surface2));border:1px solid var(--border);border-radius:22px;padding:16px 16px 12px;box-shadow:var(--shadow);transition:transform .2s ease,box-shadow .2s ease,border-color .2s}
.opp:hover{transform:translateY(-3px);border-color:var(--accent);box-shadow:0 18px 40px var(--glow)}
.opp-top{border-color:var(--gold);box-shadow:0 0 0 1px var(--gold-bg),0 16px 40px var(--gold-bg)}
.opp-h{display:flex;justify-content:space-between;align-items:flex-start}
.opp-sym{font-size:24px;font-weight:900;line-height:1.1}.opp-name{color:var(--muted);font-size:13px;margin-top:2px;max-width:190px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.opp-ch{font-size:18px;font-weight:700}
.opp-mid{display:flex;align-items:center;gap:14px;margin:12px 0 8px}
.ring{flex:none;border-radius:50%;display:grid;place-items:center;background:conic-gradient(var(--c) calc(var(--p)*1%),var(--border) 0)}
.ring b{width:76%;height:76%;border-radius:50%;background:var(--surface);display:grid;place-items:center;font-size:24px;font-weight:700}
.opp-parts{flex:1}.pb{display:grid;grid-template-columns:70px 1fr 40px;align-items:center;gap:6px;font-size:11px;color:var(--muted);margin:5px 0}
.pb i{height:6px;border-radius:6px;background:var(--border);overflow:hidden;display:block}.pb em{display:block;height:100%;background:linear-gradient(90deg,var(--accent),var(--accent2));border-radius:6px}
.pb b{font-size:11px;color:var(--text);text-align:left}
.chips{display:flex;flex-wrap:wrap;gap:5px;min-height:28px}
.chip{font-size:11.5px;padding:3px 9px;border-radius:999px;background:var(--glow);border:1px solid var(--border2);white-space:nowrap}
.own{font-size:11.5px;padding:3px 9px;border-radius:999px;background:var(--gold-bg);color:var(--gold);border:1px solid var(--gold)}
.lad{margin-top:10px;display:grid;gap:5px}.lad div{display:flex;justify-content:space-between;padding:6px 10px;border-radius:10px;background:var(--bg2);font-size:13px}
.opp-f{display:flex;justify-content:space-between;gap:8px;font-size:11.5px;color:var(--muted);margin-top:9px}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.opp){border:none!important;padding:0!important;background:transparent!important}
@media (max-width: 760px){.cc-kpi{height:auto}.opp-sym{font-size:21px}.pills{justify-content:flex-start}.pills .pill:nth-child(n+3){display:none}.ticker{display:none}}
</style>
"""


def squarify(values: list, x: float, y: float, w: float, h: float) -> list:
    """تقسيم مستطيل لمستطيلات مساحتها بنسبة القيم (خوارزمية Bruls المربعة). بيرجع [(x, y, w, h)] بنفس الترتيب."""
    vals = [max(0.0, float(v)) for v in values]
    tot = sum(vals)
    if tot <= 0 or not vals:
        return [(x, y, 0.0, 0.0) for _ in vals]
    scale = w * h / tot
    areas = [v * scale for v in vals]
    out, i = [], 0

    def worst(row, side):
        s = sum(row)
        if s <= 0 or side <= 0:
            return float("inf")
        return max(max(side * side * r / (s * s), (s * s) / (side * side * r)) if r > 0 else float("inf") for r in row)

    while i < len(areas):
        side = min(w, h)
        row = [areas[i]]
        j = i + 1
        while j < len(areas) and worst(row + [areas[j]], side) <= worst(row, side):
            row.append(areas[j]); j += 1
        s = sum(row)
        if w >= h:  # عمود على الشمال
            cw = s / h if h else 0
            cy = y
            for a in row:
                rh = a / cw if cw else 0
                out.append((x, cy, cw, rh)); cy += rh
            x += cw; w -= cw
        else:       # صف فوق
            rh = s / w if w else 0
            cx = x
            for a in row:
                cw = a / rh if rh else 0
                out.append((cx, y, cw, rh)); cx += cw
            y += rh; h -= rh
        i = j
    return out


def _mix(c1: str, c2: str, t: float) -> str:
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{int(round(x + (y - x) * t)):02x}" for x, y in zip(a, b))


def heat_color(chg: float, pal: dict) -> str:
    t = max(-1.0, min(1.0, chg / 4.0))
    return _mix(pal["surface2"], pal["up"] if t >= 0 else pal["down"], abs(t) ** 0.8)


def heatmap_figure(rows: list, pal: dict, template: str, height: int = 520):
    """rows: [(sym, sector, turnover, chg, price)]. خريطة بالقطاعات؛ كل مربع جواه نقطة شفافة بتتختار بالضغط."""
    import plotly.graph_objects as go
    W, H = 100.0, 100.0
    sectors = {}
    for r in rows:
        sectors.setdefault(r[1], []).append(r)
    sec_items = sorted(sectors.items(), key=lambda kv: -sum(x[2] for x in kv[1]))
    sec_rects = squarify([sum(x[2] for x in v) for _, v in sec_items], 0, 0, W, H)
    shapes, annos, px, py, cd, sizes = [], [], [], [], [], []
    for (sec, items), (sx, sy, sw, sh) in zip(sec_items, sec_rects):
        items = sorted(items, key=lambda x: -x[2])
        pad_top = 3.2 if sh > 12 and sw > 10 else 0.0
        inner = squarify([x[2] for x in items], sx + .25, sy + pad_top + .25, max(0, sw - .5), max(0, sh - pad_top - .5))
        if pad_top:
            annos.append(dict(x=sx + sw - .6, y=sy + 1.6, text=f"<b>{sec}</b>", showarrow=False, xanchor="right",
                              font=dict(size=11, color=pal["muted"], family="Cairo")))
        for (sym, _s, tv, chg, price), (x, y, w, h) in zip(items, inner):
            shapes.append(dict(type="rect", x0=x, y0=y, x1=x + w, y1=y + h, line=dict(color=pal["bg"], width=1.5),
                               fillcolor=heat_color(chg, pal), layer="below"))
            area = w * h
            if area > 6 and w > 3.2:
                fs = int(max(9, min(22, (area ** .5) * 1.6)))
                annos.append(dict(x=x + w / 2, y=y + h / 2, showarrow=False, align="center",
                                  text=f"<b>{sym}</b><br>{chg:+.2f}%" if h > 4.5 else f"<b>{sym}</b>",
                                  font=dict(size=fs, color=pal["text"], family="IBM Plex Mono, Cairo")))
            px.append(x + w / 2); py.append(y + h / 2); cd.append([sym, chg, price, sec])
            sizes.append(max(8.0, min(w, h) / 100 * height * .9))
    fig = go.Figure(go.Scatter(
        x=px, y=py, mode="markers", customdata=cd,
        marker=dict(size=sizes, symbol="square", color="rgba(0,0,0,0.01)", line=dict(width=0)),
        hovertemplate="<b>%{customdata[0]}</b> • %{customdata[3]}<br>السعر %{customdata[2]}<br>التغير %{customdata[1]:+.2f}%<extra></extra>",
        selected=dict(marker=dict(color="rgba(0,0,0,0.01)")), unselected=dict(marker=dict(opacity=1))))
    fig.update_layout(template=template, height=height, margin=dict(l=0, r=0, t=0, b=0), shapes=shapes, annotations=annos,
                      xaxis=dict(visible=False, range=[0, W], fixedrange=True), yaxis=dict(visible=False, range=[H, 0], fixedrange=True),
                      showlegend=False, dragmode=False, clickmode="event+select")
    return fig
