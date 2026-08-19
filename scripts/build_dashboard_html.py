import json

with open("scripts/_dashboard_data.json") as f:
    D = json.load(f)

# Enterprise BI palette (Power BI-style): one primary, one accent, neutrals only
INK = "#201F1E"
SUB = "#605E5C"
BLUE = "#2568EF"
BLUE_DK = "#123E9E"
TEAL = "#00B7C3"
BORDER = "#E1E1E1"
BG = "#F3F2F1"
CARD = "#FFFFFF"

def fmt_m(x):
    if x >= 1e9: return f"${x/1e9:.2f}B"
    if x >= 1e6: return f"${x/1e6:.1f}M"
    return f"${x:,.0f}"

def fmt_n(x):
    if x >= 1e6: return f"{x/1e6:.1f}M"
    if x >= 1e3: return f"{x/1e3:.0f}K"
    return f"{x:,.0f}"

# ---- KPI cards (no icons, single accent bar, clean stat tile) ----
kpis = [
    ("TOTAL TRIPS", fmt_n(D["total_trips"])),
    ("TOTAL REVENUE", fmt_m(D["total_revenue"])),
    ("AVERAGE FARE", f"${D['avg_fare']:.2f}"),
    ("TOTAL TIPS", fmt_m(D["total_tips"])),
]
kpi_html = "".join(f"""
<div class="kpi-card">
  <div class="kpi-accent"></div>
  <div class="kpi-label">{l}</div>
  <div class="kpi-value">{v}</div>
</div>""" for l, v in kpis)

# ---- Heatmap grid (single-hue blue sequential) ----
heat = D["heat"]; days = D["heat_days"]
maxv = max(max(row) for row in heat)
def heat_color(v):
    t = v / maxv
    r = int(233 - t*(233-18)); g = int(238 - t*(238-62)); b = int(250 - t*(250-158))
    return f"rgb({r},{g},{b})"

heat_rows = ""
for d, row in zip(days, heat):
    cells = "".join(f'<div class="hcell" style="background:{heat_color(v)}"></div>' for v in row)
    heat_rows += f'<div class="hrow"><span class="hday">{d.split("-")[1]}</span><div class="hcells">{cells}</div></div>'
hour_labels = "".join(f'<span>{h}</span>' for h in range(0, 24, 3))

# ---- Zone bars (single accent color; top item in darker shade) ----
def bar_list(items, fmt):
    mx = max(v for _, v in items)
    rows = ""
    for i, (name, v) in enumerate(items):
        pct = v / mx * 100
        color = BLUE_DK if i == 0 else BLUE
        rows += f"""<div class="barrow">
          <span class="barlabel">{name}</span>
          <div class="bartrack"><div class="barfill" style="width:{pct:.1f}%;background:{color}"></div></div>
          <span class="barval">{fmt(v)}</span>
        </div>"""
    return rows

rev_bars = bar_list(D["rev_zone"], fmt_m)
vol_bars = bar_list(D["vol_zone"], fmt_n)

# ---- Monthly line chart (SVG, blue) ----
mv = D["monthly_values"]; ml = D["monthly_labels"]
W, H = 460, 160
pad = 26
mn, mx = min(mv), max(mv)
pts = []
for i, v in enumerate(mv):
    x = pad + i * (W - 2*pad) / (len(mv) - 1)
    y = H - pad - (v - mn) / (mx - mn) * (H - 2*pad)
    pts.append((x, y))
poly = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
area = poly + f" {pts[-1][0]:.1f},{H-pad} {pts[0][0]:.1f},{H-pad}"
dots = "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.5" fill="{BLUE_DK}"/>' for x, y in pts)
month_labels = "".join(f'<span>{m.split("-")[1]}</span>' for m in ml)

# ---- Donut: service type share (2-color brand palette) ----
service = D["service"]
total_s = sum(v for _, v in service)
donut_colors = [BLUE, TEAL]
circumf = 2 * 3.14159265 * 55
offset = 0
donut_segs = ""
for (name, v), c in zip(service, donut_colors):
    frac = v / total_s
    dash = frac * circumf
    donut_segs += f'<circle r="55" cx="80" cy="80" fill="transparent" stroke="{c}" stroke-width="22" stroke-dasharray="{dash:.1f} {circumf:.1f}" stroke-dashoffset="{-offset:.1f}" transform="rotate(-90 80 80)"/>'
    offset += dash
donut_legend = "".join(
    f'<div class="legend-item"><span class="dot" style="background:{c}"></span>{name.title()} &nbsp;<b>{v/total_s*100:.1f}%</b></div>'
    for (name, v), c in zip(service, donut_colors)
)

pay = sorted(D["pay"], key=lambda x: -x[2])[:5]
pay_bars = bar_list([(n, t) for n, t, _ in pay], lambda v: f"{v:.1f}%")

html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
* {{ box-sizing: border-box; margin:0; padding:0; }}
body {{ background:{BG}; font-family:'Segoe UI',-apple-system,'Helvetica Neue',Arial,sans-serif; color:{INK}; width:1560px; }}
.topbar {{ background:{CARD}; border-bottom:1px solid {BORDER}; padding:18px 32px; display:flex; justify-content:space-between; align-items:center; }}
.topbar h1 {{ font-size:20px; font-weight:600; }}
.topbar p {{ color:{SUB}; font-size:12px; margin-top:2px; }}
.pill {{ background:{BG}; border:1px solid {BORDER}; border-radius:4px; padding:6px 14px; font-size:12px; color:{SUB}; font-weight:600; }}
.content {{ padding:24px 32px 32px; }}
.grid {{ display:grid; grid-template-columns: repeat(4, 1fr); gap:16px; margin-bottom:16px; }}
.kpi-card {{ background:{CARD}; border:1px solid {BORDER}; border-radius:4px; padding:18px 20px; position:relative; overflow:hidden; }}
.kpi-accent {{ position:absolute; top:0; left:0; width:100%; height:3px; background:{BLUE}; }}
.kpi-label {{ font-size:11px; color:{SUB}; font-weight:600; letter-spacing:0.6px; margin-bottom:8px; }}
.kpi-value {{ font-size:28px; font-weight:600; color:{INK}; }}
.card {{ background:{CARD}; border:1px solid {BORDER}; border-radius:4px; padding:20px 22px; }}
.card h3 {{ font-size:13px; font-weight:600; color:{INK}; margin-bottom:16px; text-transform:uppercase; letter-spacing:0.4px; }}
.row2 {{ display:grid; grid-template-columns: 1fr 1fr; gap:16px; margin-bottom:16px; }}
.row3 {{ display:grid; grid-template-columns: 1.2fr 1fr 1fr; gap:16px; }}
.hrow {{ display:flex; align-items:center; gap:8px; margin-bottom:4px; }}
.hday {{ width:32px; font-size:11px; color:{SUB}; font-weight:600; }}
.hcells {{ display:flex; gap:3px; flex:1; }}
.hcell {{ flex:1; height:18px; border-radius:2px; }}
.hourlabels {{ display:flex; justify-content:space-between; margin-left:40px; font-size:10px; color:{SUB}; margin-top:6px; }}
.barrow {{ display:flex; align-items:center; gap:10px; margin-bottom:11px; }}
.barlabel {{ width:150px; font-size:12px; color:{INK}; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.bartrack {{ flex:1; background:{BG}; border-radius:3px; height:12px; overflow:hidden; }}
.barfill {{ height:100%; border-radius:3px; }}
.barval {{ width:66px; font-size:11px; color:{SUB}; text-align:right; font-weight:600; }}
.monthlabels {{ display:flex; justify-content:space-between; font-size:10px; color:{SUB}; margin-top:6px; padding:0 26px; }}
.legend-item {{ font-size:13px; color:{INK}; margin-top:14px; display:flex; align-items:center; gap:8px; }}
.dot {{ width:10px; height:10px; border-radius:2px; display:inline-block; }}
.donut-wrap {{ display:flex; align-items:center; gap:20px; }}
.footer {{ color:{SUB}; font-size:11px; margin-top:20px; text-align:center; }}
</style></head>
<body>
<div class="topbar">
  <div>
    <h1>NYC Taxi Mobility Dashboard</h1>
    <p>Demand, Revenue &amp; Operational Efficiency &nbsp;·&nbsp; Yellow + Green Taxi</p>
  </div>
  <div class="pill">FULL YEAR 2023</div>
</div>

<div class="content">
<div class="grid">{kpi_html}</div>

<div class="card" style="margin-bottom:16px">
  <h3>Demand Concentration — Day of Week × Hour</h3>
  {heat_rows}
  <div class="hourlabels">{hour_labels}</div>
</div>

<div class="row2">
  <div class="card"><h3>Revenue by Pickup Zone</h3>{rev_bars}</div>
  <div class="card"><h3>Trip Volume by Pickup Zone</h3>{vol_bars}</div>
</div>

<div class="row3">
  <div class="card">
    <h3>Monthly Revenue Trend</h3>
    <svg class="linechart" viewBox="0 0 {W} {H}" width="100%">
      <polygon points="{area}" fill="{BLUE}15"/>
      <polyline points="{poly}" fill="none" stroke="{BLUE}" stroke-width="2.5"/>
      {dots}
    </svg>
    <div class="monthlabels">{month_labels}</div>
  </div>
  <div class="card"><h3>Avg Tip % by Payment Type</h3>{pay_bars}</div>
  <div class="card">
    <h3>Service Type Split</h3>
    <div class="donut-wrap">
      <svg width="160" height="160" viewBox="0 0 160 160">{donut_segs}</svg>
      <div>{donut_legend}</div>
    </div>
  </div>
</div>

</div>
</body></html>
"""

with open("tableau/nyc_taxi_dashboard.html", "w") as f:
    f.write(html)
print("wrote tableau/nyc_taxi_dashboard.html")
