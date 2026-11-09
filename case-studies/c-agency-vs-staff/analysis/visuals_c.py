"""
Case study C figures. AI-assisted (Claude). Synthetic data only.
  chart1  Step-Down 2025: daily agency hours sorted high to low, with the slice each
          converted position would cover and how much of the year it would be needed
  chart2  Tornado: what moves the 3-year savings of the first converted position
Usage: python visuals_c.py   (run convert.py first)
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
DATA = HERE.parents[2] / "generator" / "data"
OUT = HERE.parent / "outputs"
BLUE, GREY, LIGHT, TEXT, BG, DARK, GREEN = "#1F2A4A", "#8A8F98", "#E6E3DA", "#1C1F26", "#FAF8F3", "#555B66", "#24563A"
plt.rcParams.update({"font.family": "Inter", "font.size": 10, "axes.edgecolor": LIGHT, "axes.labelcolor": TEXT,
                     "xtick.color": TEXT, "ytick.color": TEXT, "axes.facecolor": BG, "figure.facecolor": BG})
FOOT = "Synthetic data. Tessaly Health is fictional."
CAP = 1700 / 365


def clean(ax):
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)


s = pd.read_csv(DATA / "unit_staffing_daily.csv", parse_dates=["date"])
pos = pd.read_csv(OUT / "conversion_by_position.csv")
uid = pos.groupby("unit_id").position.max().idxmax()
name = pos[pos.unit_id == uid].unit.iloc[0]
a = np.sort(s[(s.unit_id == uid) & (s.date.dt.year == 2025)].agency_rn_hours.to_numpy())[::-1]
fig, ax = plt.subplots(figsize=(8, 4.4), dpi=150)
ax.fill_between(range(len(a)), a, color=LIGHT, step="mid", label="Agency hours used that day")
ax.plot(range(len(a)), a, color=DARK, lw=1.2, drawstyle="steps-mid")
p = pos[pos.unit_id == uid]
for _, r in p.iterrows():
    y0, y1 = (r.position - 1) * CAP, r.position * CAP
    col = GREEN if r.recommend == "pilot" else DARK
    ax.axhline(y1, color=col, lw=0.8, ls=(0, (2, 2)))
    ax.text(len(a) + 4, (y0 + y1) / 2, f"Position {r.position}: needed {r.utilization:.0%} of the time "
            f"({'pilot' if r.recommend == 'pilot' else 'keep on agency'})", va="center", fontsize=8, color=col)
ax.set_xlim(0, len(a))
ax.set_ylim(0, max(a) * 1.05)
ax.set_xlabel("Days of 2025, sorted from most agency hours to least")
ax.set_ylabel("Agency RN hours per day")
ax.yaxis.grid(True, color=LIGHT, lw=0.8)
ax.set_axisbelow(True)
clean(ax)
fig.suptitle(f"{name}: the steady base of agency use is where a staff position can pay off", x=0.01, ha="left",
             fontsize=11, color=TEXT)
fig.text(0.01, 0.01, FOOT + " Each band is one full-time position (about 4.7 worked hours a day).", fontsize=8, color=GREY)
fig.subplots_adjust(right=0.62, left=0.09, top=0.88, bottom=0.17)
fig.savefig(OUT / "chart1_agency_base_load.png")
fig.savefig(OUT / "chart1_agency_base_load.svg")
plt.close(fig)

t = pd.read_csv(OUT / "tornado.csv").sort_values("swing")
t["input"] = t.input.str.replace("$", r"\$", regex=False)


def money(v):
    return f"{'-' if v < 0 else ''}${abs(v) / 1000:,.0f}k"


base = t.base_case.iloc[0]
fig, ax = plt.subplots(figsize=(8.5, 4.6), dpi=150)
for i, r in enumerate(t.itertuples()):
    lo, hi = sorted([r.savings_at_low, r.savings_at_high])
    ax.barh(i, hi - lo, left=lo, color=BLUE, height=0.5)
    ax.text(lo - 1500, i, money(lo).replace("$", r"\$"), va="center", ha="right", fontsize=8, color=TEXT)
    ax.text(hi + 1500, i, money(hi).replace("$", r"\$"), va="center", ha="left", fontsize=8, color=TEXT)
ax.axvline(base, color=DARK, lw=1)
ax.axvline(0, color=TEXT, lw=1.2)
ax.text(base, len(t) - 0.35, "Base case " + money(base).replace("$", r"\$"), ha="left", fontsize=8.5, color=DARK)
ax.set_yticks(range(len(t)), t.input, fontsize=8.5)
ax.set_xlabel("Net 3-year savings per converted position (below 0 costs more)")
ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: money(v).replace("$", r"\$")))
ax.set_xlim(t[["savings_at_low", "savings_at_high"]].min().min() - 25000, t[["savings_at_low", "savings_at_high"]].max().max() + 25000)
clean(ax)
fig.suptitle("The agency bill rate decides the case; most other inputs only nudge it", x=0.01, ha="left",
             fontsize=11, color=TEXT)
fig.text(0.01, 0.01, FOOT + f" {t.unit.iloc[0]}. Each bar moves one input across its range.", fontsize=8, color=GREY)
fig.tight_layout(rect=(0, 0.03, 1, 1))
fig.savefig(OUT / "chart2_tornado.png")
fig.savefig(OUT / "chart2_tornado.svg")
