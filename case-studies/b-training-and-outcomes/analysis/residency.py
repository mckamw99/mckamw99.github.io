"""
Case study B, part 2: nurse residency and first-year retention, and time to proficiency.
AI-assisted (Claude). Synthetic data only.

1. The naive comparison (completers vs. non-completers) and why it's biased.
2. A landmark analysis: exposure = early attendance (3+ of the first 4 sessions),
   measured before the outcome window, among residents still employed at session 4.
3. Time to proficiency by early attendance (Mann-Whitney), with a censoring check.
Usage: python residency.py
"""
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

warnings.filterwarnings("ignore")
DATA = Path(__file__).resolve().parents[3] / "generator" / "data"
OUT = Path(__file__).resolve().parents[1] / "outputs"
emp = pd.read_csv(DATA / "employees.csv", parse_dates=["hire_date", "termination_date"])
mem = pd.read_csv(DATA / "residency_cohort_members.csv")
att = pd.read_csv(DATA / "residency_attendance.csv", parse_dates=["session_date"])
prof = pd.read_csv(DATA / "proficiency.csv", parse_dates=["start_date", "proficient_date"])

r = mem.merge(emp, on="employee_id")
r = r[r.hire_date <= "2024-12-31"].copy()           # full 12 months of follow-up
r["tenure"] = (r.termination_date - r.hire_date).dt.days
r["left_vol"] = ((r.termination_type == "voluntary") & (r.tenure <= 365)).astype(int)


def two_by_two(df, expo, out="left_vol"):
    a = int(df[df[expo] == 1][out].sum()); n1 = int((df[expo] == 1).sum())
    c = int(df[df[expo] == 0][out].sum()); n0 = int((df[expo] == 0).sum())
    odds, p = stats.fisher_exact([[a, n1 - a], [c, n0 - c]])
    rr = (a / n1) / (c / n0) if c else np.nan
    if a and c:
        se = np.sqrt(1 / a - 1 / n1 + 1 / c - 1 / n0)
        ci = f"{rr * np.exp(-1.96 * se):.2f}-{rr * np.exp(1.96 * se):.2f}"
    else:
        ci = "undefined (a zero cell)"
    return dict(n=n1 + n0, exposed=n1, exposed_exits=a, exposed_rate_pct=round(100 * a / n1, 1),
                unexposed=n0, unexposed_exits=c, unexposed_rate_pct=round(100 * c / n0, 1),
                rr=round(rr, 2) if rr == rr else None, rr_ci=ci, fisher_p=float(f"{p:.2g}"))


rows = []
r["completed"] = r.residency_completed.astype(int)
rows.append(dict(analysis="Naive: completed residency vs. didn't", **two_by_two(r, "completed")))

# Landmark at session 4: still employed on that date, 4 sessions held
first4 = att[att.session_no <= 4].groupby("employee_id").agg(held=("attended", "size"), attended=("attended", "sum"),
                                                                landmark=("session_date", "max"))
lm = r.merge(first4, left_on="employee_id", right_index=True)
lm = lm[(lm.held == 4) & (lm.termination_date.isna() | (lm.termination_date > lm.landmark))].copy()
lm["early_attender"] = (lm.attended >= 3).astype(int)
rows.append(dict(analysis="Landmark: 3+ of first 4 sessions vs. fewer", **two_by_two(lm, "early_attender")))
res = pd.DataFrame(rows)
res.to_csv(OUT / "residency_results.csv", index=False)

# Why the naive comparison is biased: completion requires staying 12 months
months_to_complete = 12 + (pd.to_datetime(r.cohort_start_date) - r.hire_date).dt.days.mean() / 30.4
# Minimum detectable risk ratio for the landmark sample (two-proportion, 80% power, alpha .05)
p0 = lm[lm.early_attender == 0].left_vol.mean(); n1 = lm.early_attender.sum(); n0 = len(lm) - n1
z = stats.norm.ppf(0.975) + stats.norm.ppf(0.8)
mde = next((x for x in np.arange(0.99, 0.0, -0.01)
            if abs(p0 - p0 * x) / np.sqrt(p0 * x * (1 - p0 * x) / n1 + p0 * (1 - p0) / n0) >= z), None)
# Even a risk ratio of 0 (no exits at all among early attenders): is it detectable?
z_at_zero = p0 / np.sqrt(p0 * (1 - p0) / n0)
# Sample needed for a 0.65 risk ratio at this baseline
need = int(np.ceil(2 * (z ** 2) * (p0 * (1 - p0) + p0 * 0.65 * (1 - p0 * 0.65)) / (p0 - p0 * 0.65) ** 2))
power = pd.DataFrame([dict(landmark_n=len(lm), baseline_rate=round(p0, 3),
                           min_detectable_rr=round(mde, 2) if mde else "none: even zero exits would not reach 80% power",
                           power_if_no_exposed_exits=round(float(stats.norm.cdf(z_at_zero - stats.norm.ppf(0.975))), 2),
                           n_per_group_for_rr_065=need, residents_per_year=round(len(mem) / 3))])
power.to_csv(OUT / "residency_power.csv", index=False)

# Time to proficiency: new grads by early attendance (Mann-Whitney), experienced hires for context
p = prof[prof.subject_type == "staff"].merge(lm[["employee_id", "early_attender"]], left_on="subject_id",
                                             right_on="employee_id", how="left")
ng = p[p.pathway == "new_grad"].dropna(subset=["early_attender"])
cens = ng.groupby("early_attender").censored.mean().round(3).to_dict()
done = ng[~ng.censored]
x1 = done[done.early_attender == 1].days_to_proficiency; x0 = done[done.early_attender == 0].days_to_proficiency
u, pv = stats.mannwhitneyu(x1, x0, alternative="two-sided")
rb = 1 - 2 * u / (len(x1) * len(x0))  # rank-biserial; positive = first group tends to be faster (fewer days)
exp_ = p[(p.pathway == "experienced_hire") & ~p.censored].days_to_proficiency
u2, pv2 = stats.mannwhitneyu(done.days_to_proficiency, exp_, alternative="two-sided")
tp = pd.DataFrame([
    dict(comparison="New grads: early attenders vs. not", n1=len(x1), n0=len(x0), median1=x1.median(), median0=x0.median(),
         U=u, p_value=float(f"{pv:.2g}"), rank_biserial=round(rb, 2), p_first_faster=round(1 - u / (len(x1) * len(x0)), 2),
         censored_share=f"{cens.get(1.0, np.nan):.0%} vs {cens.get(0.0, np.nan):.0%}"),
    dict(comparison="New grads vs. experienced hires", n1=len(done), n0=len(exp_), median1=done.days_to_proficiency.median(),
         median0=exp_.median(), U=u2, p_value=float(f"{pv2:.2g}"),
         rank_biserial=round(1 - 2 * u2 / (len(done) * len(exp_)), 2),
         p_first_faster=round(1 - u2 / (len(done) * len(exp_)), 2), censored_share=""),
])
tp.to_csv(OUT / "proficiency_results.csv", index=False)
lm.to_csv(OUT / "residency_landmark_cohort.csv", index=False)

pd.set_option("display.width", 250)
print(res.to_string(index=False)); print(); print(power.to_string(index=False)); print(); print(tp.to_string(index=False))
print(f"\nAverage months from hire to residency completion: {months_to_complete:.1f}")
