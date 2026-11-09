"""
Case study D, part 4: figures.
  chart1  Community North 2025: published vs. reconciled (the double load)
  LIB-46  Generic learning-data architecture with control points
  LIB-03  Governed weekly compliance view (mockup on synthetic data)
AI-assisted (Claude). Synthetic data only.
Usage: python visuals.py   (run reconcile.py first)
"""
import sys
import textwrap
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "a-what-complete-means" / "analysis"))
from common import AC_FAMILIES, load, resolve_identity  # noqa: E402

OUT = HERE.parent / "outputs"
BLUE, GREEN, RED, GREY, LIGHT, TEXT, BG = "#1F2A4A", "#24563A", "#A61E2D", "#8A8F98", "#E6E3DA", "#1C1F26", "#FAF8F3"
plt.rcParams.update({"font.family": "Inter", "font.size": 10, "axes.edgecolor": LIGHT, "axes.labelcolor": TEXT,
                     "xtick.color": TEXT, "ytick.color": TEXT, "axes.facecolor": BG, "figure.facecolor": BG,
                     "axes.grid": False})
FOOT = "Synthetic data. Tessaly Health is fictional."


def clean(ax):
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)


# Chart 1 ---------------------------------------------------------------------
rec = pd.read_csv(OUT / "reconciliation_all_months.csv")
cn = rec[(rec.facility_group == "Community North") & rec.report_month.str.startswith("2025")
         & (rec.report_month >= "2025-02")]
x = range(len(cn))
fig, ax = plt.subplots(figsize=(7.5, 3.8), dpi=150)
ax.plot(x, cn.src_pct, color=BLUE, lw=2, marker="o", ms=6, label="Reconciled to source", zorder=2)
ax.plot(x, cn.pub_pct, color=RED, lw=1.5, marker="o", ms=5, label="Published", zorder=3,
        markeredgecolor=BG, markeredgewidth=1.5)
i = list(cn.report_month).index("2025-03")
ax.annotate(f"March: published {cn.pub_pct.iloc[i]:.1f}%\nsource {cn.src_pct.iloc[i]:.1f}%  (double load)",
            xy=(i, cn.pub_pct.iloc[i]), xytext=(i + 0.6, 30), fontsize=9, color=TEXT,
            arrowprops=dict(arrowstyle="-", color=GREY, lw=1))
ax.set_xticks(list(x), [pd.Timestamp(m + "-01").strftime("%b") for m in cn.report_month])
ax.set_xlabel("Month end, 2025")
ax.set_ylabel("Compliance, scorecard definition (%)")
ax.set_ylim(0, 100)
ax.yaxis.grid(True, color=LIGHT, lw=0.8)
ax.set_axisbelow(True)
clean(ax)
ax.legend(frameon=False, fontsize=9, loc="lower right")
fig.suptitle("Community North: one month published 12.8 points too high", x=0.01, ha="left", fontsize=11, color=TEXT)
fig.text(0.01, 0.01, FOOT, fontsize=8, color=GREY)
fig.tight_layout(rect=(0, 0.03, 1, 1))
fig.savefig(OUT / "chart1_community_north_2025.png")
fig.savefig(OUT / "chart1_community_north_2025.svg")
plt.close(fig)

# LIB-46 architecture ----------------------------------------------------------
stages = ["HR system", "Nightly HR feed", "Enterprise LMS", "Warehouse staging", "Compliance fact table",
          "BI scorecard", "Readers by role"]
controls = [  # (between stage i and i+1, text, existed before?)
    "Extract vs. load row counts", "Rejected rows reviewed (existing). Added: freshness gate, no failed run in the last 3 days",
    "Source vs. staging row counts", "Data-quality checks C01-C15\nIdentity map, one row per requirement",
    "Full reconciliation to source\nNumerator vs. month's completions\nStaff-only population check",
    "Quarterly access review against the role model; leaver revocation"]
existed = [True, False, True, False, False, False]
DARK = "#555B66"
fig, ax = plt.subplots(figsize=(12, 5.2), dpi=150)
ax.set_xlim(0, 14)
ax.set_ylim(-0.6, 6)
ax.axis("off")
w, h, y = 1.55, 1.0, 3.9
xs = [0.25 + i * 1.98 for i in range(len(stages))]
for i, (s_, x0) in enumerate(zip(stages, xs)):
    ax.add_patch(FancyBboxPatch((x0, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08",
                                fc="white", ec=BLUE, lw=1.4))
    ax.text(x0 + w / 2, y + h / 2, s_.replace(" ", "\n", 1) if len(s_) > 14 else s_, ha="center", va="center",
            fontsize=9, color=TEXT)
    if i < len(stages) - 1:
        ax.add_patch(FancyArrowPatch((x0 + w, y + h / 2), (xs[i + 1], y + h / 2), arrowstyle="-|>",
                                     mutation_scale=10, color=GREY, lw=1.2))
        c = BLUE if not existed[i] else DARK
        cx = x0 + w + 0.215
        ty = 3.0 if i % 2 == 0 else 1.55
        ax.plot([cx] * 2, [y - 0.05, ty + 0.1], color=c, lw=1)
        ax.plot(cx, ty + 0.1, "o", color=c, ms=4)
        ax.text(cx, ty, "\n".join(textwrap.wrap(controls[i].replace("\n", "; "), 24)), ha="center", va="top",
                fontsize=7.8, color=c, fontweight="bold" if not existed[i] else "normal")
ax.text(0.25, 5.45, "Learning data path for the executive compliance scorecard, with control points", fontsize=11, color=TEXT)
ax.text(0.25, -0.15, "Grey: control in place before the review.   Blue, bold: control added after the review.", fontsize=8.5, color=TEXT)
ax.text(0.25, -0.5, "Generic tool categories; no products named. " + FOOT, fontsize=8, color=GREY)
fig.savefig(OUT / "lib46_architecture.png", bbox_inches="tight")
fig.savefig(OUT / "lib46_architecture.svg", bbox_inches="tight")
plt.close(fig)

# LIB-03 dashboard mockup --------------------------------------------------------
T = load()
ident = resolve_identity(T)
emp, at, ex = T["employees"], T["attempts"], T["exemptions"]
D, A = pd.Timestamp("2025-04-30"), pd.Timestamp("2025-02-01")
pop = emp[(emp.hire_date <= A) & (emp.termination_date.isna() | (emp.termination_date >= D))].drop_duplicates("person_id")
g = pop[["employee_id", "person_id"]].merge(pd.DataFrame({"family": AC_FAMILIES}), how="cross")
g["course_id"] = g.family + "-2025"
ev = at[at.result == "passed"].merge(ident[["lms_user_id", "person_id"]], on="lms_user_id")
first = ev.groupby(["person_id", "course_id"]).finished_at.min()
g["passed_on"] = [first.get((p, c)) for p, c in zip(g.person_id, g.course_id)]
e = ex.merge(ident[["lms_user_id", "person_id"]], on="lms_user_id")
e = e[(e.cycle_year == 2025) & (e.granted_date <= D) & (e.expires_date.isna() | (e.expires_date >= D))]
g["exempt"] = [(p in set(e[e.course_family_id == "AC-ALL"].person_id)) or
               (f == "AC-03" and p in set(e[e.course_family_id == "AC-03"].person_id)) for p, f in zip(g.person_id, g.family)]
n_exempt_req = int(g.exempt.sum())
g = g[~g.exempt]
h_ = T["employee_unit_history"]
h_ = h_[(h_.start_date <= D) & (h_.end_date.isna() | (h_.end_date >= D))].drop_duplicates("employee_id").set_index("employee_id")
units = T["units"].set_index("unit_id")
fac = units.facility_id.map(T["facilities"].set_index("facility_id").facility_group)
g["unit_id"] = g.employee_id.map(h_.unit_id)
g["facility"] = g.unit_id.map(fac)
g["met"] = g.passed_on.notna() & (g.passed_on <= D)
per = g.groupby(["person_id", "facility"]).met.all().reset_index()
m1, m2 = per.met.mean() * 100, g.met.mean() * 100
overdue = int((~g.met).sum())
weeks = pd.date_range("2025-02-07", D, freq="7D").append(pd.DatetimeIndex([D]))
trend = [g.assign(ok=g.passed_on.notna() & (g.passed_on <= w)).groupby("person_id").ok.all().mean() * 100 for w in weeks]
byfac = per.groupby("facility").met.mean().mul(100).sort_values()
pd.DataFrame({"week_ending": weeks.date, "people_fully_compliant_pct": [round(t, 1) for t in trend]}).to_csv(
    OUT / "lib03_campaign_trend.csv", index=False)
fname = units.facility_id.map(T["facilities"].set_index("facility_id").facility_name)
g["unit_label"] = g.unit_id.map(units.unit_name) + " (" + g.unit_id.map(fname).str.replace("Tessaly ", "") + ")"
top = g[~g.met].groupby("unit_label").size().sort_values(ascending=False).head(5)

fig = plt.figure(figsize=(12, 7.2), dpi=150)
fig.text(0.02, 0.955, "Annual compliance training: weekly view", fontsize=15, color=BLUE, fontweight="bold")
fig.text(0.02, 0.925, "As of 30 Apr 2025 (due date)  ·  Definition v1.0 (people fully compliant)  ·  HR feed: current  ·  "
         "Pre-publication checks: high-severity items cleared or explained", fontsize=9, color=TEXT)
tiles = [("People fully compliant", f"{m1:.1f}%", "M1 · headline"), ("Requirements met", f"{m2:.1f}%", "M2"),
         ("Overdue requirements", f"{overdue:,}", "M4 · not met, not exempt"),
         ("Requirements exempted", f"{n_exempt_req:,}", "Leave or equivalent credit"),
         ("People in scope", f"{len(per):,}", "Staff on payroll 1 Feb to 30 Apr"),
         ("Unresolved accounts", "33", "Awaiting an administrator")]
for i, (lab, val, sub) in enumerate(tiles):
    x0 = 0.02 + i * 0.163
    ax = fig.add_axes([x0, 0.75, 0.15, 0.14])
    ax.axis("off")
    ax.add_patch(FancyBboxPatch((0, 0), 1, 1, boxstyle="round,pad=0,rounding_size=0.06", fc="white", ec=LIGHT,
                                transform=ax.transAxes))
    ax.text(0.07, 0.75, lab, fontsize=9, color=TEXT, transform=ax.transAxes)
    ax.text(0.07, 0.38, val, fontsize=20, color=BLUE, fontweight="bold", transform=ax.transAxes)
    ax.text(0.07, 0.12, sub, fontsize=7.5, color=GREY, transform=ax.transAxes)
ax = fig.add_axes([0.06, 0.12, 0.38, 0.52])
ax.plot(range(len(weeks)), trend, color=BLUE, lw=2, marker="o", ms=4)
ax.set_xticks(range(len(weeks)), [w.strftime("%d %b") for w in weeks], rotation=45, ha="right", fontsize=8)
ax.set_ylim(0, 100)
ax.set_ylabel("People fully compliant (%)")
ax.yaxis.grid(True, color=LIGHT, lw=0.8)
ax.set_axisbelow(True)
ax.text(len(weeks) - 1, trend[-1] + 4, f"{trend[-1]:.1f}%", ha="center", fontsize=9, color=TEXT)
ax.set_title("Campaign progress, 2025", loc="left", fontsize=10.5, color=TEXT)
clean(ax)
ax = fig.add_axes([0.56, 0.42, 0.40, 0.24])
ax.barh(range(len(byfac)), byfac.values, color=BLUE, height=0.55)
for i, v in enumerate(byfac.values):
    ax.text(v + 1, i, f"{v:.1f}%", va="center", fontsize=8.5, color=TEXT)
ax.set_yticks(range(len(byfac)), byfac.index, fontsize=8.5)
ax.set_xlim(0, 100)
ax.set_title("People fully compliant by facility", loc="left", fontsize=10.5, color=TEXT)
clean(ax)
ax = fig.add_axes([0.56, 0.08, 0.40, 0.25])
ax.axis("off")
ax.set_title("Most overdue requirements by unit (manager follow-up)", loc="left", fontsize=10.5, color=TEXT)
for i, (u, n) in enumerate(top.items()):
    ax.text(0.0, 0.85 - i * 0.19, u, fontsize=9, color=TEXT, transform=ax.transAxes)
    ax.text(1.0, 0.85 - i * 0.19, f"{n:,}", fontsize=9, color=TEXT, ha="right", transform=ax.transAxes)
    ax.plot([0, 1], [0.79 - i * 0.19] * 2, color=LIGHT, lw=0.8, transform=ax.transAxes)
fig.text(0.02, 0.015, "Mockup. " + FOOT + " Person-level detail available to unit managers for their own unit only.",
         fontsize=8, color=GREY)
fig.savefig(OUT / "lib03_dashboard_mockup.png")
fig.savefig(OUT / "lib03_dashboard_mockup.svg")
pd.DataFrame([dict(m1_pct=round(m1, 1), m2_pct=round(m2, 1), overdue=overdue, exempt_requirements=n_exempt_req,
                   people=len(per))]).to_csv(OUT / "lib03_numbers.csv", index=False)
print(f"M1 {m1:.1f}  M2 {m2:.1f}  overdue {overdue}  people {len(per)}")
print(top)
