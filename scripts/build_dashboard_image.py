import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.patches import FancyBboxPatch

EXPORT = "/Users/pallakkhullar/Desktop/nyc-taxi-analysis/exports"

df = pd.read_csv(f"{EXPORT}/tableau_extract.csv")
def trunc(s, n=20):
    return s if len(s) <= n else s[:n - 1] + "…"

rev_zone = pd.read_csv(f"{EXPORT}/top_zones_by_revenue.csv").sort_values("total_revenue")
vol_zone = pd.read_csv(f"{EXPORT}/top_zones_by_volume.csv").sort_values("trip_count")
rev_zone["zone"] = rev_zone["zone"].map(trunc)
vol_zone["zone"] = vol_zone["zone"].map(trunc)

total_trips = df["trip_count"].sum()
total_revenue = df["total_revenue"].sum()
avg_fare = total_revenue / total_trips

heat = df.groupby(["day_name", "pickup_hour"])["trip_count"].sum().unstack()
monthly = df.groupby("month_name")["total_revenue"].sum().sort_index()
pay = df.groupby("payment_label").agg(tip=("tip_revenue", "sum"), fare=("fare_revenue", "sum"))
pay["tip_pct"] = pay["tip"] / pay["fare"] * 100
pay = pay[pay["fare"] > 0].sort_values("tip_pct")

# ---- design system ----
NAVY = "#0B2545"
TEAL = "#1B998B"
GOLD = "#E8A33D"
GRAY = "#8A94A6"
LIGHT = "#F4F6FA"
CARD_BG = "#FFFFFF"
GRID = "#E6E9F0"

def fmt_money(x):
    if abs(x) >= 1e9: return f"${x/1e9:.2f}B"
    if abs(x) >= 1e6: return f"${x/1e6:.1f}M"
    return f"${x:,.0f}"

def fmt_num(x):
    if abs(x) >= 1e6: return f"{x/1e6:.1f}M"
    if abs(x) >= 1e3: return f"{x/1e3:.0f}K"
    return f"{x:,.0f}"

def clean_ax(ax, grid_axis="x"):
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(colors=GRAY, labelsize=9, length=0)
    ax.grid(axis=grid_axis, color=GRID, linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Helvetica Neue", "Arial", "DejaVu Sans"],
    "text.color": NAVY, "axes.labelcolor": GRAY, "axes.edgecolor": GRID,
})

fig = plt.figure(figsize=(18, 15), facecolor=LIGHT)
gs = gridspec.GridSpec(4, 2, height_ratios=[0.5, 1.3, 1.5, 1.4], hspace=0.65, wspace=0.22,
                        left=0.09, right=0.97, top=0.92, bottom=0.04)

fig.text(0.09, 0.965, "NYC Taxi Mobility Dashboard", fontsize=26, fontweight="bold", color=NAVY)
fig.text(0.09, 0.945, "Demand, Revenue & Operational Efficiency  ·  Yellow + Green Taxi, Full Year 2023",
         fontsize=12, color=GRAY)

# ---- KPI cards ----
kpis = [("TOTAL TRIPS", fmt_num(total_trips), TEAL),
        ("TOTAL REVENUE", fmt_money(total_revenue), NAVY),
        ("AVG FARE / TRIP", f"${avg_fare:,.2f}", GOLD)]
gs_kpi = gridspec.GridSpecFromSubplotSpec(1, 3, subplot_spec=gs[0, :], wspace=0.06)
for i, (label, val, color) in enumerate(kpis):
    ax = fig.add_subplot(gs_kpi[i]); ax.axis("off")
    ax.add_patch(FancyBboxPatch((0.02, 0.05), 0.96, 0.9, boxstyle="round,pad=0,rounding_size=0.06",
                                 transform=ax.transAxes, facecolor=CARD_BG, edgecolor=GRID, linewidth=1))
    ax.add_patch(FancyBboxPatch((0.02, 0.05), 0.03, 0.9, boxstyle="round,pad=0,rounding_size=0.015",
                                 transform=ax.transAxes, facecolor=color, edgecolor="none"))
    ax.text(0.12, 0.58, val, fontsize=28, fontweight="bold", color=NAVY, va="center")
    ax.text(0.12, 0.25, label, fontsize=10.5, color=GRAY, va="center", fontweight="medium")

# ---- Heatmap ----
ax1 = fig.add_subplot(gs[1, :])
im = ax1.imshow(heat.values, cmap="YlGnBu", aspect="auto")
ax1.set_yticks(range(len(heat.index))); ax1.set_yticklabels([d.split("-")[1] for d in heat.index], fontsize=9)
ax1.set_xticks(range(0, 24, 2)); ax1.set_xticklabels(range(0, 24, 2), fontsize=9)
ax1.set_xlabel("Hour of Day", fontsize=10)
ax1.set_title("Demand Concentration — Day of Week x Hour", fontsize=13, fontweight="bold", color=NAVY, loc="left", pad=10)
for s in ax1.spines.values(): s.set_visible(False)
ax1.tick_params(length=0)
cbar = fig.colorbar(im, ax=ax1, fraction=0.015, pad=0.008)
cbar.ax.tick_params(labelsize=8, colors=GRAY, length=0)
cbar.outline.set_visible(False)

# ---- Revenue / Volume by zone ----
def hbar(ax, data, xcol, ycol, color, title, fmt):
    ax.barh(data[ycol], data[xcol], color=color, height=0.65, zorder=3)
    for y, v in zip(data[ycol], data[xcol]):
        ax.text(v * 1.02, y, fmt(v), va="center", fontsize=8, color=NAVY)
    ax.set_title(title, fontsize=12, fontweight="bold", color=NAVY, loc="left", pad=8)
    ax.set_xlim(0, data[xcol].max() * 1.28)
    ax.set_xticks([])
    ax.tick_params(axis="y", labelsize=8.3)
    for lbl in ax.get_yticklabels():
        lbl.set_ha("right")
    for s in ax.spines.values(): s.set_visible(False)

ax2 = fig.add_subplot(gs[2, 0])
hbar(ax2, rev_zone, "total_revenue", "zone", TEAL, "Revenue by Pickup Zone — Top 15", fmt_money)
ax3 = fig.add_subplot(gs[2, 1])
hbar(ax3, vol_zone, "trip_count", "zone", NAVY, "Trip Volume by Pickup Zone — Top 15", fmt_num)

# ---- Monthly trend ----
ax4 = fig.add_subplot(gs[3, 0])
x = range(len(monthly))
ax4.plot(x, monthly.values, color=GOLD, linewidth=2.5, marker="o", markersize=5, zorder=3)
ax4.fill_between(x, monthly.values, monthly.values.min()*0.9, color=GOLD, alpha=0.12, zorder=2)
ax4.set_xticks(x); ax4.set_xticklabels([m.split("-")[1] for m in monthly.index], fontsize=8.5)
ax4.set_title("Monthly Revenue Trend", fontsize=12, fontweight="bold", color=NAVY, loc="left", pad=8)
ax4.set_ylabel("Revenue ($)", fontsize=9)
ax4.yaxis.set_major_formatter(lambda v, p: fmt_money(v))
clean_ax(ax4, grid_axis="y")

# ---- Payment / tip ----
ax5 = fig.add_subplot(gs[3, 1])
colors5 = [TEAL if v == pay["tip_pct"].max() else GRAY for v in pay["tip_pct"]]
ax5.barh(pay.index, pay["tip_pct"], color=colors5, height=0.6, zorder=3)
for y, v in zip(pay.index, pay["tip_pct"]):
    ax5.text(v + 0.4, y, f"{v:.1f}%", va="center", fontsize=8.5, color=NAVY)
ax5.set_title("Average Tip % by Payment Type", fontsize=12, fontweight="bold", color=NAVY, loc="left", pad=8)
ax5.set_xlim(0, pay["tip_pct"].max() * 1.25)
clean_ax(ax5, grid_axis="x")

fig.text(0.05, 0.008, "Source: NYC TLC Trip Record Data · 39.1M cleaned trips · SQL + Python pipeline",
          fontsize=8.5, color=GRAY)

out = f"{EXPORT}/../tableau/nyc_taxi_dashboard.png"
plt.savefig(out, dpi=170, facecolor=LIGHT)
print("saved", out)
