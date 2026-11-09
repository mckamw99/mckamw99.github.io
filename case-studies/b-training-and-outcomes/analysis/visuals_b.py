"""
Case study B, part 3: figures. AI-assisted (Claude). Synthetic data only.
  chart1  First-year voluntary exit by onboarding timing, by unit group
  chart2  Residency: the naive comparison vs. the landmark comparison
  LIB-05  Metric tree from training to business outcomes, with evidence strength
Usage: python visuals_b.py   (run onboarding.py and residency.py first)
"""
import textwrap
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
import numpy as np
import pandas as pd
from statsmodels.stats.proportion import proportion_confint

OUT = Path(__file__).resolve().parents[1] / "outputs"
BLUE, GREY, LIGHT, TEXT, BG, DARK = "#1F2A4A", "#8A8F98", "#E6E3DA", "#1C1F26", "#FAF8F3", "#555B66"
plt.rcParams.update({"font.family": "Inter", "font.size": 10, "axes.edgecolor": LIGHT, "axes.labelcolor": TEXT,
                     "xtick.color": TEXT, "ytick.color": TEXT, "axes.facecolor": BG, "figure.facecolor": BG})
FOOT = "Synthetic data. Tessaly Health is fictional."


def clean(ax):
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)


# Chart 1 ---------------------------------------------------------------------
h = pd.read_csv(OUT / "onboarding_cohort.csv")
res = pd.read_csv(OUT / "onboarding_results.csv").iloc[0]
h = h[h.unit_group != "nursing admin"]
groups = ["All hires"] + h.groupby("unit_group").size().sort_values().index.tolist()[::-1]
fig, ax = plt.subplots(figsize=(8, 4.4), dpi=150)
for i, g in enumerate(groups):
    d = h if g == "All hires" else h[h.unit_group == g]
    for k, (val, col, off) in enumerate([(1, BLUE, -0.12), (0, GREY, 0.12)]):
        s = d[d.on_time == val]
        p = s.left_vol.mean() * 100
        lo, hi = proportion_confint(s.left_vol.sum(), len(s), method="wilson")
        y = len(groups) - 1 - i + off
        ax.plot([lo * 100, hi * 100], [y, y], color=col, lw=1.2, alpha=0.6)
        ax.plot(p, y, "o", color=col, ms=7, markeredgecolor=BG, markeredgewidth=1.5,
                label=("Finished onboarding within 30 days" if val else "Finished later or not at all") if i == 0 else None)
    n = len(d)
    ax.text(51, len(groups) - 1 - i, f"n={n:,}", va="center", fontsize=8, color=DARK)
ax.set_yticks(range(len(groups))[::-1], [g.replace("_", " ").capitalize() if g != "All hires" else g for g in groups])
ax.set_xlim(0, 55)
ax.set_xlabel("Left voluntarily within 12 months of hire (%), with 95% interval")
ax.xaxis.grid(True, color=LIGHT, lw=0.8)
ax.set_axisbelow(True)
ax.axhline(len(groups) - 1.5, color=LIGHT, lw=1)
clean(ax)
ax.legend(frameon=False, fontsize=8.5, loc="lower left", bbox_to_anchor=(0, 1.0), ncol=2)
fig.suptitle(f"On-time onboarding goes with lower first-year exits (adjusted risk ratio {res.adjusted_rr:.2f})",
             x=0.01, ha="left", fontsize=11, color=TEXT)
fig.text(0.01, 0.01, FOOT + " Hires from 2023-24 still employed at day 30.", fontsize=8, color=GREY)
fig.tight_layout(rect=(0, 0.03, 1, 1))
fig.savefig(OUT / "chart1_onboarding_exit.png")
fig.savefig(OUT / "chart1_onboarding_exit.svg")
plt.close(fig)

# Chart 2 ---------------------------------------------------------------------
rr = pd.read_csv(OUT / "residency_results.csv")
fig, axes = plt.subplots(1, 2, figsize=(8.5, 3.9), dpi=150, sharey=True)
titles = ["Naive: completed the residency?", "Landmark: attended 3+ of first 4 sessions?"]
for ax, (_, r), t in zip(axes, rr.iterrows(), titles):
    vals = [(r.exposed_exits, r.exposed, "Yes"), (r.unexposed_exits, r.unexposed, "No")]
    for j, (a, n, lab) in enumerate(vals):
        p = a / n * 100
        lo, hi = proportion_confint(a, n, method="wilson")
        ax.bar(j, p, width=0.5, color=BLUE if j == 0 else GREY)
        ax.plot([j, j], [lo * 100, hi * 100], color=TEXT, lw=1)
        ax.text(j + 0.08, hi * 100 + 1, f"{p:.1f}%\n{a} of {n}", ha="left", va="bottom", fontsize=8.5, color=TEXT)
    ax.set_xticks([0, 1], ["Yes", "No"])
    ax.set_title(t, loc="left", fontsize=9.5, color=TEXT)
    ax.set_ylim(0, 50)
    ax.yaxis.grid(True, color=LIGHT, lw=0.8)
    ax.set_axisbelow(True)
    clean(ax)
axes[0].set_ylabel("Left voluntarily within 12 months (%)")
axes[0].text(0.5, 44, "Biased: finishing requires\nstaying about 15 months", fontsize=8.5, color=DARK, ha="left")
axes[1].text(0.5, 44, f"Fisher p = {rr.fisher_p.iloc[1]:.2f}; only "
             f"{int(rr.exposed_exits.iloc[1] + rr.unexposed_exits.iloc[1])} exits", fontsize=8.5, color=DARK, ha="left")
fig.suptitle("Residency: the obvious comparison is wrong, the right one is too small", x=0.01, ha="left",
             fontsize=11, color=TEXT)
fig.text(0.01, 0.01, FOOT + " New-grad RNs hired 2023-24. Bars show 95% intervals.", fontsize=8, color=GREY)
fig.tight_layout(rect=(0, 0.03, 1, 1))
fig.savefig(OUT / "chart2_residency.png")
fig.savefig(OUT / "chart2_residency.svg")
plt.close(fig)

# LIB-05 metric tree ------------------------------------------------------------
pr = pd.read_csv(OUT / "proficiency_results.csv").iloc[0]
cols = {0: "Training", 1: "Leading indicator", 2: "Workforce outcome", 3: "Business outcomes"}
nodes = {
    "ob": (0, 3.6, "Role onboarding finished within 30 days"),
    "res": (0, 1.9, "Residency attendance (new-grad RNs)"),
    "comp": (0, 0.2, "Annual compliance on time"),
    "ttp": (1, 1.9, "Time to proficiency"),
    "ret": (2, 3.6, "12-month voluntary retention"),
    "turn": (3, 3.6, "Turnover cost"),
    "agency": (3, 1.9, "Agency hours and cost"),
}
links = [  # from, to, strength, label
    ("ob", "ret", "tested", f"Tested in B: adjusted risk ratio {res.adjusted_rr:.2f} (95% CI {res.adjusted_rr_ci}). Holds after adjusting for unit and role."),
    ("res", "ttp", "weak", f"Tested in B: median {pr.median1:.0f} vs {pr.median0:.0f} days, Mann-Whitney p = {pr.p_value:.2f}. Right direction, not established."),
    ("res", "ret", "weak", "Tested in B: 7 exits in the landmark sample. Too few to tell."),
    ("ret", "turn", "arith", "True by arithmetic: fewer exits x cost per exit."),
    ("ret", "agency", "plaus", "Plausible: fewer exits, fewer vacancies to cover. Modeled in case study C."),
    ("ttp", "agency", "plaus", "Plausible: faster proficiency, shorter double coverage. Modeled in case study C."),
]
style = {"tested": (BLUE, 2.4), "weak": (BLUE, 1.1), "arith": (DARK, 1.6), "plaus": (GREY, 1.1)}
X = [0.3, 3.75, 7.2, 10.65]
W, H = 2.6, 0.95
fig, ax = plt.subplots(figsize=(13, 7.4), dpi=150)
ax.set_xlim(0, 13.4)
ax.set_ylim(-4.2, 5.4)
ax.axis("off")
for c, name in cols.items():
    ax.text(X[c] + W / 2, 4.85, name.upper(), ha="center", fontsize=9, color=DARK, fontweight="bold")
for k, (c, y, lab) in nodes.items():
    ax.add_patch(FancyBboxPatch((X[c], y), W, H, boxstyle="round,pad=0.02,rounding_size=0.08", fc="white",
                                ec=BLUE if k != "comp" else GREY, lw=1.3))
    ax.text(X[c] + W / 2, y + H / 2, "\n".join(textwrap.wrap(lab, 22)), ha="center", va="center", fontsize=9,
            color=TEXT if k != "comp" else DARK)
for n, (a, b, kind, lab) in enumerate(links, 1):
    ca, ya, _ = nodes[a]
    cb, yb, _ = nodes[b]
    col, lw = style[kind]
    p0, p1 = (X[ca] + W, ya + H / 2), (X[cb], yb + H / 2)
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle="-|>", mutation_scale=11, color=col, lw=lw))
    t = 0.5 if not (a == "ttp" and b == "agency") else 0.5
    mx, my = p0[0] + (p1[0] - p0[0]) * t, p0[1] + (p1[1] - p0[1]) * t
    ax.plot(mx, my, "o", ms=15, color="white", markeredgecolor=col, markeredgewidth=1.4, zorder=5)
    ax.text(mx, my, str(n), ha="center", va="center", fontsize=8.5, color=TEXT, zorder=6, fontweight="bold")
    ax.text(0.3, -0.75 - (n - 1) * 0.42, f"{n}", fontsize=9, color=TEXT, fontweight="bold")
    ax.text(0.7, -0.75 - (n - 1) * 0.42, lab, fontsize=9, color=TEXT)
ax.text(X[0] + W + 0.15, 0.67, "No link drawn: on-time compliance training has no plausible\npath to retention, so the tree doesn't claim one.",
        fontsize=8.5, color=DARK, va="center")
ax.text(0.3, -3.45, "Line weight: thick blue = tested and holds; thin blue = tested, not established; dark grey = arithmetic; "
        "light grey = plausible, not yet tested.", fontsize=8.5, color=DARK)
ax.text(0.3, -3.9, "Associations from observational data, not evidence of cause. " + FOOT, fontsize=8, color=GREY)
ax.text(0.3, 5.25, "From training to business outcomes: which links the evidence supports", fontsize=12, color=TEXT)
fig.savefig(OUT / "lib05_metric_tree.png", bbox_inches="tight")
fig.savefig(OUT / "lib05_metric_tree.svg", bbox_inches="tight")
