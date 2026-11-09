"""
Case study A: the published compliance number vs. the governed definition.
AI-assisted (Claude). Synthetic data only; results are a method demonstration.

Builds a step-by-step bridge from the number the executive scorecard publishes
to the governed number defined in metric_definitions.md, then repeats the
calculation by year and by facility.
Usage: python compliance.py
"""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from common import AC_FAMILIES, OUT, employed_on, facility_on, load, resolve_identity

T = load()
ident = resolve_identity(T)
emp, en, at, ex, lu = T["employees"], T["enrollments"], T["attempts"], T["exemptions"], T["lms_users"]
fac_of_unit = T["units"].set_index("unit_id").facility_id.map(T["facilities"].set_index("facility_id").facility_group)
lu_fac = lu.set_index("lms_user_id").unit_id.map(fac_of_unit)

en = en.merge(ident[["lms_user_id", "person_id", "user_source"]], on="lms_user_id")
en["family"] = en.course_id.str[:5]
ac = en[en.family.isin(AC_FAMILIES)].copy()
at_p = at[at.result == "passed"].merge(ident[["lms_user_id", "person_id"]], on="lms_user_id")
ex_p = ex.merge(ident[["lms_user_id", "person_id"]], on="lms_user_id")


def campaign_population(y):
    a, d = pd.Timestamp(f"{y}-02-01"), pd.Timestamp(f"{y}-04-30")
    e = emp[(emp.hire_date <= a) & (emp.termination_date.isna() | (emp.termination_date >= d))]
    return e[["employee_id", "person_id"]].drop_duplicates("person_id")


def grid(y, pop):
    g = pop.assign(k=1).merge(pd.DataFrame({"family": AC_FAMILIES, "k": 1}), on="k").drop(columns="k")
    g["course_id"] = g.family + f"-{y}"
    return g


def status_done(rows, d):
    return (rows.status == "completed") & (rows.completion_date <= d)


def run_year(y, keep_steps=False):
    d = pd.Timestamp(f"{y}-04-30")
    steps = []
    # S0: published definition (LMS status over all enrollments, feed accounts with a unit)
    s = ac[(ac.cycle_year == y) & (ac.user_source == "hr_feed") & lu_fac.reindex(ac.lms_user_id).notna().values
           & (ac.assigned_date <= d)]
    steps.append(("Published scorecard definition", status_done(s, d).sum(), len(s)))
    # S1: drop people who had left by the as-of date
    alive = set(employed_on(emp, d).person_id)
    s = s[s.person_id.isin(alive)]
    steps.append(("Remove people who had left", status_done(s, d).sum(), len(s)))
    # S2: campaign population only (employed 1 Feb through 30 Apr)
    pop = campaign_population(y)
    s = s[s.person_id.isin(pop.person_id)]
    steps.append(("Keep the campaign population only", status_done(s, d).sum(), len(s)))
    # S3: one requirement per person and module (feed accounts only, status evidence)
    g = grid(y, pop)
    feed = ac[(ac.cycle_year == y) & (ac.user_source == "hr_feed")]
    sat = set(map(tuple, feed[status_done(feed, d)][["person_id", "course_id"]].values))
    g["s3"] = [(p, c) in sat for p, c in zip(g.person_id, g.course_id)]
    steps.append(("One requirement per person and module", g.s3.sum(), len(g)))
    # S4: include records on duplicate accounts linked to the same person
    allacc = ac[(ac.cycle_year == y) & ac.person_id.notna() & (ac.user_source != "test")]
    sat = set(map(tuple, allacc[status_done(allacc, d)][["person_id", "course_id"]].values))
    g["s4"] = [(p, c) in sat for p, c in zip(g.person_id, g.course_id)]
    steps.append(("Merge duplicate accounts", g.s4.sum(), len(g)))
    # S5: require a passed attempt on the current version by the due date
    ev = at_p[(at_p.finished_at <= d) & at_p.course_id.isin(g.course_id.unique())]
    sat = set(map(tuple, ev[["person_id", "course_id"]].values))
    g["satisfied"] = [(p, c) in sat for p, c in zip(g.person_id, g.course_id)]
    steps.append(("Require a passed attempt (evidence)", g.satisfied.sum(), len(g)))
    # S6: valid exemptions leave the denominator
    e = ex_p[(ex_p.cycle_year == y) & (ex_p.granted_date <= d) & (ex_p.expires_date.isna() | (ex_p.expires_date >= d))]
    exall = set(e[e.course_family_id == "AC-ALL"].person_id)
    ex03 = set(e[e.course_family_id == "AC-03"].person_id)
    g["exempt"] = [(p in exall) or (f == "AC-03" and p in ex03) for p, f in zip(g.person_id, g.family)]
    gm = g[~g.exempt]
    steps.append(("Remove valid exemptions", gm.satisfied.sum(), len(gm)))
    # Person level: every non-exempt module satisfied
    per = gm.groupby(["person_id", "employee_id"]).satisfied.all().reset_index()
    late = allacc[(allacc.status == "completed") & (allacc.completion_date <= pd.Timestamp(f"{y}-12-31"))]
    sat_ye = set(map(tuple, late[["person_id", "course_id"]].values))
    gm = gm.assign(done_ye=[(p, c) in sat_ye for p, c in zip(gm.person_id, gm.course_id)])
    per["completed_by_year_end"] = gm.groupby(["person_id", "employee_id"]).done_ye.all().values
    per["facility_group"] = per.employee_id.map(facility_on(T, per.employee_id, d))
    steps.append(("Person level: all required modules", per.satisfied.sum(), len(per)))
    b = pd.DataFrame(steps, columns=["step", "numerator", "denominator"])
    b["rate_pct"] = (100 * b.numerator / b.denominator).round(1)
    return b, per, s


rows, bridges = [], {}
for y in (2023, 2024, 2025):
    b, per, s0 = run_year(y)
    bridges[y] = (b, per)
    rows.append(dict(cycle=y, published_pct=b.rate_pct.iloc[0], governed_module_pct=b.rate_pct.iloc[-2],
                     governed_person_pct=b.rate_pct.iloc[-1],
                     completed_by_year_end_person_pct=round(100 * per.completed_by_year_end.mean(), 1),
                     people_in_scope=len(per), people_compliant=int(per.satisfied.sum())))
by_year = pd.DataFrame(rows)
b25, per25 = bridges[2025]
b25.to_csv(OUT / "bridge_2025.csv", index=False)
per25.to_csv(OUT / "person_compliance_2025.csv", index=False)
by_year.to_csv(OUT / "compliance_by_year.csv", index=False)

# By facility, 2025: published value for April vs governed person-level
pub = T["report_published_values"]
pub = pub[pub.report_month == "2025-04"].set_index("facility_group").completion_rate_pct
fac = per25.groupby("facility_group").agg(people=("satisfied", "size"), compliant=("satisfied", "sum"))
fac["governed_person_pct"] = (100 * fac.compliant / fac.people).round(1)
fac["published_pct"] = pub
fac["gap_pts"] = (fac.published_pct - fac.governed_person_pct).round(1)
fac = fac.sort_values("governed_person_pct")
fac.to_csv(OUT / "compliance_by_facility_2025.csv")
unres = ident[ident.match_rule.str.startswith("unresolved", na=False)]
unres.to_csv(OUT / "unresolved_accounts.csv", index=False)

print(b25.to_string(index=False)); print(); print(by_year.to_string(index=False)); print(); print(fac.to_string())

# Charts -------------------------------------------------------------------
BLUE, GREEN, RED, GREY, TEXT = "#1F2A4A", "#24563A", "#A61E2D", "#8A8F98", "#1C1F26"
plt.rcParams.update({"font.family": "Inter", "font.size": 10, "axes.facecolor": "#FAF8F3", "figure.facecolor": "#FAF8F3", "axes.edgecolor": GREY,
                     "axes.labelcolor": TEXT, "xtick.color": TEXT, "ytick.color": TEXT})

fig, ax = plt.subplots(figsize=(8, 4.6), dpi=150)
labels = list(b25.step)
vals = list(b25.rate_pct)
colors = [BLUE] + [GREEN if vals[i] >= vals[i - 1] else RED for i in range(1, len(vals) - 1)] + [BLUE]
ax.barh(range(len(vals))[::-1], vals, color=colors, height=0.6)
for i, v in enumerate(vals):
    delta = "" if i == 0 else f"  ({v - vals[i - 1]:+.1f})"
    ax.text(v + 0.8, len(vals) - 1 - i, f"{v:.1f}%{delta}", va="center", color=TEXT, fontsize=9)
ax.set_yticks(range(len(vals))[::-1], labels)
ax.set_xlim(0, 105)
ax.set_xlabel("Annual compliance rate on 30 Apr 2025 (%)")
fig.suptitle("Published vs. governed compliance, one rule at a time", x=0.01, ha="left", color=TEXT, fontsize=11)
for sp in ("top", "right"):
    ax.spines[sp].set_visible(False)
fig.text(0.01, 0.01, "Synthetic data, Tessaly Health (fictional). Green raises the rate, red lowers it.", fontsize=8, color=GREY)
fig.tight_layout(rect=(0, 0.03, 1, 1))
fig.savefig(OUT / "chart1_bridge_2025.png")
fig.savefig(OUT / "chart1_bridge_2025.svg")

fig, ax = plt.subplots(figsize=(7, 4.2), dpi=150)
yy = range(len(fac))
ax.hlines(yy, fac.governed_person_pct, fac.published_pct, color=GREY, lw=2)
ax.scatter(fac.published_pct, yy, color=GREY, s=50, label="Published (enrollment-level status)", zorder=3)
ax.scatter(fac.governed_person_pct, yy, color=BLUE, s=50, label="Governed (people fully compliant)", zorder=3)
for i, (g, r) in enumerate(fac.iterrows()):
    ax.text(r.governed_person_pct - 1, i, f"{r.governed_person_pct:.0f}%", ha="right", va="center", fontsize=8, color=BLUE)
    ax.text(r.published_pct + 1, i, f"{r.published_pct:.0f}%", ha="left", va="center", fontsize=8, color=TEXT)
ax.set_yticks(list(yy), fac.index)
ax.set_xlim(40, 100)
ax.set_xlabel("Annual compliance on 30 Apr 2025 (%)")
fig.suptitle("Every facility looks better on the published scorecard", x=0.01, ha="left", color=TEXT, fontsize=11)
ax.legend(frameon=False, fontsize=8, loc="lower left", bbox_to_anchor=(0, 1.0), ncol=2)
for sp in ("top", "right"):
    ax.spines[sp].set_visible(False)
fig.text(0.01, 0.01, "Synthetic data, Tessaly Health (fictional).", fontsize=8, color=GREY)
fig.tight_layout(rect=(0, 0.03, 1, 1))
fig.savefig(OUT / "chart2_by_facility_2025.png")
fig.savefig(OUT / "chart2_by_facility_2025.svg")
