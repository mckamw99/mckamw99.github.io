"""
Case study B, part 1: is finishing role onboarding on time linked to first-year retention?
AI-assisted (Claude). Synthetic data only; results are a method demonstration.

Design: hires from 2023-2024 (so everyone has 12 months of follow-up), landmark at
day 30 (you can't be "on time" if you left before day 30), outcome = voluntary
exit within 12 months of hire. Unit risk group is the main suspected confounder.
Usage: python onboarding.py
"""
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy import stats
from statsmodels.stats.contingency_tables import StratifiedTable

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "a-what-complete-means" / "analysis"))
from common import load, resolve_identity  # noqa: E402

OUT = HERE.parent / "outputs"
OUT.mkdir(exist_ok=True)
T = load()
ident = resolve_identity(T)
emp, en, at, units = T["employees"], T["enrollments"], T["attempts"], T["units"].set_index("unit_id")


def build(landmark=30, window=("2023-01-01", "2024-12-31")):
    h = emp[emp.hire_date.between(*window)].copy()
    h["tenure_days"] = (h.termination_date - h.hire_date).dt.days
    h = h[h.tenure_days.isna() | (h.tenure_days > landmark)]
    # exposure: passed role onboarding (ON-02-*) within 30 days, on the enrollment created at this hire
    ob = en[en.course_id.str.startswith("ON-02")].merge(ident[["lms_user_id", "person_id"]], on="lms_user_id")
    ob = ob.merge(at[at.result == "passed"][["enrollment_id", "finished_at"]], on="enrollment_id", how="left")
    ob = ob.groupby(["person_id", "assigned_date"]).finished_at.min().reset_index()
    h = h.merge(ob, left_on=["person_id", "hire_date"], right_on=["person_id", "assigned_date"], how="left")
    h["on_time"] = ((h.finished_at - h.hire_date).dt.days <= 30).astype(int)
    h["left_vol"] = ((h.termination_type == "voluntary") & (h.tenure_days <= 365)).astype(int)
    h["left_invol"] = ((h.termination_type == "involuntary") & (h.tenure_days <= 365)).astype(int)
    h["left_any"] = (h.tenure_days <= 365).fillna(False).astype(int)
    u = units.reindex(h.hire_unit_id)
    kind = np.where(u.unit_kind.values == "inpatient", "inpatient " + u.turnover_tier.fillna("").values, u.unit_kind.values)
    h["unit_group"] = pd.Series(kind, index=h.index).replace({"department": "non-nursing department", "admin": "nursing admin"})
    h["role_group"] = h.role_code.map(lambda r: "RN" if r == "RN" else "LPN/NA" if r in ("LPN", "NA") else "other")
    h["stratum"] = h.role_group + " | " + h.unit_group
    return h


def rr_ci(a, n1, c, n0):
    p1, p0 = a / n1, c / n0
    rr = p1 / p0
    se = np.sqrt(1 / a - 1 / n1 + 1 / c - 1 / n0)
    return rr, rr * np.exp(-1.96 * se), rr * np.exp(1.96 * se)


def mh_rr(df, out):
    num = den = 0.0
    for _, g in df.groupby("stratum"):
        n = len(g)
        a = g[(g.on_time == 1)][out].sum(); n1 = (g.on_time == 1).sum()
        c = g[(g.on_time == 0)][out].sum(); n0 = (g.on_time == 0).sum()
        num += a * n0 / n
        den += c * n1 / n
    return num / den


def analyze(h, out="left_vol", label="main"):
    a = h[h.on_time == 1][out].sum(); n1 = (h.on_time == 1).sum()
    c = h[h.on_time == 0][out].sum(); n0 = (h.on_time == 0).sum()
    chi2, p, _, _ = stats.chi2_contingency([[a, n1 - a], [c, n0 - c]], correction=False)
    phi = np.sqrt(chi2 / len(h))
    rr, lo, hi = rr_ci(a, n1, c, n0)
    m = smf.logit(f"{out} ~ on_time + C(unit_group) + C(role_group)", data=h).fit(disp=0)
    p_on = m.predict(h.assign(on_time=1)).mean(); p_off = m.predict(h.assign(on_time=0)).mean()
    # bootstrap the standardized (adjusted) risk ratio
    rng = np.random.default_rng(20261108)
    boots = []
    for _ in range(300):
        b = h.sample(len(h), replace=True, random_state=int(rng.integers(1e9)))
        try:
            mb = smf.logit(f"{out} ~ on_time + C(unit_group) + C(role_group)", data=b).fit(disp=0)
            boots.append(mb.predict(b.assign(on_time=1)).mean() / mb.predict(b.assign(on_time=0)).mean())
        except Exception:
            pass
    tables = [np.array([[g[g.on_time == 1][out].sum(), (g.on_time == 1).sum() - g[g.on_time == 1][out].sum()],
                        [g[g.on_time == 0][out].sum(), (g.on_time == 0).sum() - g[g.on_time == 0][out].sum()]])
              for _, g in h.groupby("stratum") if g.on_time.nunique() == 2]
    st = StratifiedTable(tables)
    return dict(analysis=label, outcome=out, n=len(h), n_on_time=int(n1), n_late=int(n0),
                rate_on_time_pct=round(100 * a / n1, 1), rate_late_pct=round(100 * c / n0, 1),
                chi2=round(chi2, 2), p_value=float(f"{p:.2g}"), phi=round(phi, 3),
                crude_rr=round(rr, 2), crude_rr_ci=f"{lo:.2f}-{hi:.2f}",
                mh_rr=round(mh_rr(h, out), 2), homogeneity_p=float(f"{st.test_equal_odds().pvalue:.2g}"),
                adjusted_rr=round(p_on / p_off, 2),
                adjusted_rr_ci=f"{np.percentile(boots, 2.5):.2f}-{np.percentile(boots, 97.5):.2f}",
                adjusted_or=round(float(np.exp(m.params["on_time"])), 2))


h = build()
h.to_csv(OUT / "onboarding_cohort.csv", index=False)
rows = [analyze(h)]
# Confounding check: does unit group relate to both exposure and outcome?
conf = h.groupby("unit_group").agg(hires=("on_time", "size"), on_time_pct=("on_time", "mean"),
                                   left_vol_pct=("left_vol", "mean")).mul([1, 100, 100]).round(1)
conf.to_csv(OUT / "confounding_by_unit_group.csv")
# Sensitivity and negative control
rows.append(analyze(build(landmark=45), label="landmark day 45"))
rows.append(analyze(h[~h.rehire_flag], label="excluding rehires"))
rows.append(analyze(h[h.role_code == "RN"], label="RNs only"))
rows.append(analyze(h, out="left_any", label="any exit (voluntary or not)"))
rows.append(analyze(h, out="left_invol", label="negative control: involuntary exit"))
res = pd.DataFrame(rows)
res.to_csv(OUT / "onboarding_results.csv", index=False)

# Minimum detectable risk ratio at 80% power, alpha 0.05, for this sample
p0 = h[h.on_time == 0].left_vol.mean(); n1 = (h.on_time == 1).sum(); n0 = (h.on_time == 0).sum()
z = stats.norm.ppf(0.975) + stats.norm.ppf(0.8)
mde = next(r for r in np.arange(0.99, 0.3, -0.01)
           if abs(p0 - p0 * r) / np.sqrt(p0 * r * (1 - p0 * r) / n1 + p0 * (1 - p0) / n0) >= z)
pd.DataFrame([dict(baseline_late_rate=round(p0, 3), n_on_time=n1, n_late=n0, min_detectable_rr=round(mde, 2))]
             ).to_csv(OUT / "onboarding_power.csv", index=False)

pd.set_option("display.width", 250)
print(res.to_string(index=False)); print(); print(conf.to_string()); print(f"\nMinimum detectable RR: {mde:.2f}")
