"""
Validation for the Tessaly Health synthetic data (LIB-23).

AI-assisted (Claude). Three kinds of checks:
  1. Integrity: keys, foreign keys, date order.
  2. Calibration: does the output match the assumptions in config.py?
  3. Recovery: can the planted effects and planted issues be found again?

Usage: python validate.py [--data data]   Exit code 1 if any integrity check fails.
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

import config as C

ap = argparse.ArgumentParser()
ap.add_argument("--data", default="data")
DATA = Path(ap.parse_args().data)
T = {p.stem: pd.read_csv(p, low_memory=False) for p in DATA.glob("*.csv")}
results = []


def check(group, name, ok, detail=""):
    results.append((group, name, "PASS" if ok else "FAIL", detail))


def info(group, name, detail):
    results.append((group, name, "INFO", detail))


# 1. Integrity --------------------------------------------------------------
pk = {"facilities": "facility_id", "units": "unit_id", "persons": "person_id", "employees": "employee_id",
      "lms_users": "lms_user_id", "courses": "course_id", "enrollments": "enrollment_id",
      "attempts": "attempt_id", "certifications": "cert_record_id", "agency_workers": "agency_worker_id",
      "agency_contracts": "contract_id", "exemptions": "exemption_id"}
for t, k in pk.items():
    check("integrity", f"{t}.{k} unique", T[t][k].is_unique, f"{len(T[t]):,} rows")
fks = [("units", "facility_id", "facilities", "facility_id"),
       ("employees", "person_id", "persons", "person_id"),
       ("employees", "hire_unit_id", "units", "unit_id"),
       ("employee_unit_history", "employee_id", "employees", "employee_id"),
       ("enrollments", "lms_user_id", "lms_users", "lms_user_id"),
       ("enrollments", "course_id", "courses", "course_id"),
       ("attempts", "enrollment_id", "enrollments", "enrollment_id"),
       ("certifications", "employee_id", "employees", "employee_id"),
       ("agency_contracts", "agency_worker_id", "agency_workers", "agency_worker_id"),
       ("unit_staffing_daily", "unit_id", "units", "unit_id"),
       ("bi_users", "employee_id", "employees", "employee_id")]
for a, ac, b, bc in fks:
    missing = (~T[a][ac].dropna().isin(T[b][bc])).sum()
    check("integrity", f"{a}.{ac} -> {b}.{bc}", missing == 0, f"{missing} orphans")
e = T["employees"]
bad = (pd.to_datetime(e.termination_date) < pd.to_datetime(e.hire_date)).sum()
check("integrity", "termination on/after hire", bad == 0, f"{bad} rows")
s = T["unit_staffing_daily"]
parts = s.staff_rn_hours + s.overtime_rn_hours + s.agency_rn_hours + s.unfilled_rn_hours
check("integrity", "staffing hours add up to required (tolerance 0.5h)",
      (abs(parts - s.required_rn_hours) <= 0.5).all(),
      f"max diff {abs(parts - s.required_rn_hours).max():.2f}h")
en = T["enrollments"]
comp_no_date = ((en.status == "completed") & en.completion_date.isna()).sum()
check("integrity", "completed enrollments have a completion date", comp_no_date == 0, f"{comp_no_date}")

# 2. Calibration ------------------------------------------------------------
roles = T["roles"].set_index("role_code").role_family
h = T["employee_unit_history"]
for snap in ("2023-01-01", "2024-07-01", "2025-12-31"):
    act = e[(e.hire_date <= snap) & (e.termination_date.isna() | (e.termination_date >= snap))]
    nurse = act.role_code.map(roles).eq("nursing").mean()
    info("calibration", f"staff headcount on {snap}", f"{len(act):,} (nursing {nurse:.0%})")
    check("calibration", f"headcount near 4,000 on {snap}", 3600 <= len(act) <= 4300, "")

u = T["units"].set_index("unit_id")
e["tier"] = e.hire_unit_id.map(u.turnover_tier).fillna(e.hire_unit_id.map(u.unit_kind))
for yr in (2023, 2024, 2025):
    a, b = f"{yr}-01-01", f"{yr}-12-31"
    act = e[(e.hire_date <= b) & (e.termination_date.isna() | (e.termination_date >= a))]
    for grp, sub in (("RN all", act[act.role_code == "RN"]), ("RN high tier", act[(act.role_code == "RN") & (act.tier == "high")]),
                     ("RN low tier", act[(act.role_code == "RN") & (act.tier == "low")]),
                     ("all staff", act)):
        vt = ((sub.termination_type == "voluntary") & sub.termination_date.between(a, b)).sum()
        avg = len(sub) - 0.5 * sub.termination_date.between(a, b).sum() - 0.5 * sub.hire_date.between(a, b).sum()
        info("calibration", f"{yr} voluntary turnover, {grp}", f"{vt / avg:.1%}")

for yr in (2023, 2024):
    nh = e[(e.role_code == "RN") & e.hire_date.between(f"{yr}-01-01", f"{yr}-12-31")]
    tn = (pd.to_datetime(nh.termination_date) - pd.to_datetime(nh.hire_date)).dt.days
    info("calibration", f"RNs hired in {yr} who left within 12 months", f"{tn.le(365).mean():.1%} (n={len(nh)})")
# RN coverage gap: required hours not covered by staff straight time, hospital units
gap = 1 - s.staff_rn_hours.sum() / s.required_rn_hours.sum()
info("calibration", "RN hours not covered by staff straight time (vacancy-like gap)", f"{gap:.1%}")
rn_slots = u[u.department_type == "nursing"].budgeted_rn.sum()
for snap in ("2024-07-01", "2025-12-31"):
    hh = h[(h.start_date <= snap) & (h.end_date.isna() | (h.end_date >= snap))]
    rn = hh.merge(e[["employee_id", "role_code"]], on="employee_id")
    filled = (rn.role_code == "RN").sum()
    info("calibration", f"RN position vacancy on {snap}", f"{1 - filled / rn_slots:.1%}")
agg = s.merge(u[["turnover_tier"]], left_on="unit_id", right_index=True).groupby("turnover_tier")[
    ["required_rn_hours", "agency_rn_hours", "overtime_rn_hours", "unfilled_rn_hours"]].sum()
for tier, r in agg.iterrows():
    info("calibration", f"agency share of required RN hours, {tier} tier",
         f"agency {r.agency_rn_hours / r.required_rn_hours:.1%}, overtime {r.overtime_rn_hours / r.required_rn_hours:.1%}, "
         f"unfilled {r.unfilled_rn_hours / r.required_rn_hours:.1%}")

lu = T["lms_users"].set_index("lms_user_id")
camp = en[(en.assignment_rule == "annual_campaign") & en.course_id.str.startswith("AC-")]
for y in (2023, 2024, 2025):
    c = camp[camp.cycle_year == y]
    ontime = ((c.status == "completed") & (c.completion_date <= c.due_date)).mean()
    info("calibration", f"{y} campaign: share of enrollments completed by due date (raw, no cleanup)", f"{ontime:.1%}")
info("calibration", "lms_users by source", lu.user_source.value_counts().to_dict())

# 3. Recovery: planted effects (Case B) -------------------------------------
ob = en[en.course_id.str.startswith("ON-02")].merge(lu[["hr_employee_id"]], left_on="lms_user_id", right_index=True)
ob = ob.merge(e, left_on="hr_employee_id", right_on="employee_id")
ob = ob[ob.hire_date.between("2023-01-01", "2024-12-31")]
ob["on_time"] = (ob.status == "completed") & (pd.to_datetime(ob.completion_date) - pd.to_datetime(ob.hire_date)).dt.days.le(30)
# landmark at day 30: keep people still employed at day 30, outcome = voluntary exit by day 365
ten = (pd.to_datetime(ob.termination_date) - pd.to_datetime(ob.hire_date)).dt.days
ob = ob[ten.isna() | (ten > 30)]
ten = ten.loc[ob.index]
ob["left_y1"] = (ob.termination_type == "voluntary") & ten.le(365)
naive = ob.groupby("on_time").left_y1.mean()
info("recovery", "E-01 naive year-1 voluntary exit: on-time vs late onboarding",
     f"{naive.get(True, np.nan):.1%} vs {naive.get(False, np.nan):.1%} (ratio {naive.get(True) / naive.get(False):.2f}); "
     f"planted HR {C.HR_ONBOARDING_ON_TIME}, high-tier units have lower on-time rates")
strat = ob.groupby(["tier", "on_time"]).left_y1.mean().unstack()
ratios = (strat[True] / strat[False]).dropna()
info("recovery", "E-01 within-tier ratios (on-time / late)", {k: round(v, 2) for k, v in ratios.items()})

rc = T["residency_cohort_members"].merge(e, on="employee_id")
att = T["residency_attendance"]
early = att[att.session_no <= 4].groupby("employee_id").attended.agg(["mean", "size"])
early = early[early["size"] == 4]["mean"]
rc["early_att"] = rc.employee_id.map(early)
rten = (pd.to_datetime(rc.termination_date) - pd.to_datetime(rc.hire_date)).dt.days
rc = rc[(rc.hire_date <= "2024-12-31")]
rten = rten.loc[rc.index]
rc["left_y1"] = (rc.termination_type == "voluntary") & rten.le(365)
comp_grp = rc.groupby("residency_completed").left_y1.mean()
info("recovery", "E-02 naive: year-1 voluntary exit, residency completers vs non-completers",
     f"{comp_grp.get(True, np.nan):.1%} vs {comp_grp.get(False, np.nan):.1%} (immortal-time bias: completers had to stay 12 months)")
land = rc[rc.early_att.notna()]
hi = land.early_att >= 0.75
info("recovery", "E-02 landmark (attended 3+ of first 4 sessions vs fewer)",
     f"{land[hi].left_y1.mean():.1%} (n={hi.sum()}) vs {land[~hi].left_y1.mean():.1%} (n={(~hi).sum()}); "
     f"planted HR {C.HR_RESIDENCY_HIGH_ATTENDER}. Small sample: too few exits for a reliable estimate")

p = T["proficiency"]
info("recovery", "E-04 median days to proficiency by pathway",
     p.dropna(subset=["days_to_proficiency"]).groupby("pathway").days_to_proficiency.median().to_dict())

# 3b. Recovery: published scorecard reconciliation (Case D) -----------------
pub = T["report_published_values"]
ac = en[en.course_id.str.startswith("AC-")].copy()
fg = T["facilities"].set_index("facility_id").facility_group
lu["fgroup"] = lu.unit_id.map(u.facility_id).map(fg).fillna("Unassigned")
ac = ac.merge(lu[["fgroup", "user_source"]], left_on="lms_user_id", right_index=True)
ac = ac[(ac.user_source == "hr_feed") & (ac.fgroup != "Unassigned")]
mism = []
for _, r in pub.iterrows():
    me = (pd.Period(r.report_month) .to_timestamp(how="end")).strftime("%Y-%m-%d")
    y = int(r.report_month[:4])
    sub = ac[(ac.cycle_year == y) & (ac.fgroup == r.facility_group) & (ac.assigned_date <= me)]
    num = ((sub.status == "completed") & (sub.completion_date <= me)).sum()
    if num != r.numerator or len(sub) != r.denominator:
        mism.append(f"{r.report_month} {r.facility_group}")
months = sorted({m.split()[0] for m in mism})
check("recovery", "reconciliation flags exactly the planted months (2024-08, 2025-03, 2025-10)",
      months == ["2024-08", "2025-03", "2025-10"], f"{len(mism)} facility-months differ: {months}")

# Report --------------------------------------------------------------------
out = pd.DataFrame(results, columns=["group", "check", "result", "detail"])
(DATA.parent / "validation_report.md").write_text(
    "# Validation report\n\nGenerated by `validate.py`. Synthetic data only.\n\n" + out.to_markdown(index=False) + "\n")
print(out.to_string(index=False, max_colwidth=120))
sys.exit(1 if (out.result == "FAIL").any() else 0)
