"""
Case study C: agency vs. staff nurses. Where would converting agency hours to staff
positions pay off, by how much, and how sure can we be?
AI-assisted (Claude). Synthetic staffing data; cost inputs are public benchmarks or
labeled assumptions (see ASSUMPTIONS below). Results are a method demonstration.

Method
  1. Cost per worked hour for staff, overtime and agency, by year.
  2. Split each unit's daily agency hours into "base" (steady) and "peak". A converted
     staff position covers one slice of the base; its utilization is measured from
     the daily data, not assumed.
  3. Simulate each candidate position for 3 years, day by day: hiring lag, orientation,
     ramp to proficiency, exits and refills, with agency covering every gap. Compare
     with leaving the hours on agency. 400 runs per position, with uncertain inputs
     drawn from ranges.
  4. Sensitivity (tornado) for one representative position.
Usage: python convert.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

DATA = Path(__file__).resolve().parents[3] / "generator" / "data"
OUT = Path(__file__).resolve().parents[1] / "outputs"
OUT.mkdir(exist_ok=True)
rng = np.random.default_rng(20261108)

cost = pd.read_csv(DATA / "cost_assumptions.csv")
C = {(r.assumption, None if pd.isna(r.year) else int(r.year)): r.value for r in cost.itertuples()}
units = pd.read_csv(DATA / "units.csv").set_index("unit_id")
fac = pd.read_csv(DATA / "facilities.csv").set_index("facility_id").facility_group
s = pd.read_csv(DATA / "unit_staffing_daily.csv", parse_dates=["date"])
emp = pd.read_csv(DATA / "employees.csv", parse_dates=["hire_date", "termination_date"])
prof = pd.read_csv(DATA / "proficiency.csv")
contracts = pd.read_csv(DATA / "agency_contracts.csv", parse_dates=["start_date", "end_date"])

# ASSUMPTIONS (not from a public benchmark; each is varied in the sensitivity analysis)
WORKED_HOURS_PER_FTE = 1700            # 36 h/week x 52, less paid leave
OT_PAYROLL_LOAD = 0.0765               # employer payroll tax on overtime pay; other benefits not driven by OT
HIRE_COST = (12000, 6000, 20000)       # recruiting, onboarding admin, preceptor time per staff hire (base, low, high)
RAMP_PRODUCTIVITY = (0.5, 0.3, 0.7)    # share of a fully proficient nurse's output between orientation and proficiency
ORIENTATION_DAYS = 14                  # matches the generator: no productive hours
IDLE_REDEPLOY_VALUE = (0.0, 0.0, 0.5)  # share of a converted nurse's unneeded hours usefully floated elsewhere

# 1. Cost per worked hour --------------------------------------------------------
rows = []
for y in (2023, 2024, 2025):
    w = C[("staff_rn_wage_per_hour_worked", y)]
    load = C[("benefits_load_on_wages_pct", None)]
    ag = C[("agency_rn_bill_rate", y)]
    orient = C[("agency_orientation_cost_per_contract", None)] / (13 * 36)
    rows.append(dict(year=y, staff_loaded=round(w * (1 + load), 2), overtime=round(w * 1.5 * (1 + OT_PAYROLL_LOAD), 2),
                     agency=round(ag + orient, 2), agency_premium_pct=round(100 * ((ag + orient) / (w * (1 + load)) - 1), 1)))
rates = pd.DataFrame(rows)
rates.to_csv(OUT / "cost_per_hour.csv", index=False)

# Spend by year
s["year"] = s.date.dt.year
spend = s.groupby("year")[["staff_rn_hours", "overtime_rn_hours", "agency_rn_hours", "unfilled_rn_hours"]].sum()
r_ = rates.set_index("year")
spend["agency_spend"] = spend.agency_rn_hours * r_.agency
spend["overtime_spend"] = spend.overtime_rn_hours * r_.overtime
spend["agency_fte"] = spend.agency_rn_hours / WORKED_HOURS_PER_FTE
spend.round(0).to_csv(OUT / "spend_by_year.csv")

# 2. Inputs from the data ------------------------------------------------------------
rn = emp[emp.role_code == "RN"].copy()
rn["tier"] = rn.hire_unit_id.map(units.turnover_tier)
rn["kind"] = rn.hire_unit_id.map(units.unit_kind)
rn = rn[rn.kind == "inpatient"]
new = rn[rn.hire_date.between("2023-01-01", "2024-12-31") & ~rn.new_grad_flag]
new_t = (new.termination_date - new.hire_date).dt.days
p1 = new.assign(y1=new_t.le(365)).groupby("tier").y1.mean()          # experienced hires: exit in year 1
est = rn[(rn.hire_date <= "2023-01-01") & (rn.termination_date.isna() | (rn.termination_date >= "2024-01-01"))]
p2 = est.assign(left=est.termination_date.between("2024-01-01", "2024-12-31")).groupby("tier").left.mean()
ttp = prof[(prof.pathway == "experienced_hire") & ~prof.censored].assign(
    special=lambda x: x.unit_id.map(units.unit_name).isin(["Intensive Care", "Emergency Department", "Step-Down"]))
ttp_days = ttp.groupby("special").days_to_proficiency.median()
# Agency nurses ramp up too: each new agency nurse is partly productive until proficient.
assign_days = contracts.groupby("agency_worker_id").apply(
    lambda c: (c.end_date - c.start_date).dt.days.add(1).sum(), include_groups=False).mean()
agency_ttp = prof[(prof.pathway == "agency") & ~prof.censored].days_to_proficiency.median()
fill_days = {"high": 95, "medium": 75, "low": 75}   # generator inputs; NSI 2026: 78 days to recruit (range 56-102)
inputs = pd.DataFrame({"first_year_exit": p1.round(3), "later_annual_exit": p2.round(3)})
inputs["days_to_proficiency_specialty"] = ttp_days[True]
inputs["days_to_proficiency_other"] = ttp_days[False]
inputs["fill_days"] = pd.Series(fill_days)
inputs["agency_assignment_days_avg"] = round(assign_days, 1)
inputs["agency_days_to_proficiency"] = agency_ttp
inputs.to_csv(OUT / "model_inputs_from_data.csv")

# 3. Simulation --------------------------------------------------------------------------
Y = 2025
cap = WORKED_HOURS_PER_FTE / 365     # worked hours per day for one FTE


def simulate(daily_need, tier, special, n=400, fixed=None):
    """Net savings over 3 years of one converted position vs. leaving its hours on agency."""
    f = fixed or {}
    days = len(daily_need)

    def draw(name, base, lo, hi):
        if name in f:
            return np.full(n, f[name])
        return rng.triangular(lo, base, hi, n)

    ag = draw("agency_rate", rates.set_index("year").agency[Y], rates.set_index("year").agency[Y] * 0.85,
              rates.set_index("year").agency[2023])
    load = draw("benefits_load", C[("benefits_load_on_wages_pct", None)], 0.45, 0.65)
    staff = C[("staff_rn_wage_per_hour_worked", Y)] * (1 + load)
    hire = draw("hire_cost", *HIRE_COST)
    ramp = draw("ramp_productivity", *RAMP_PRODUCTIVITY)
    idle = draw("idle_value", *IDLE_REDEPLOY_VALUE)
    q1 = draw("first_year_exit", p1[tier], p1[tier] * 0.5, min(0.6, p1[tier] * 1.5))
    q2 = draw("later_annual_exit", p2[tier], p2[tier] * 0.5, min(0.5, p2[tier] * 1.5))
    t_prof = draw("days_to_proficiency", ttp_days[special], ttp_days[special] * 0.7, ttp_days[special] * 1.6)
    fill = draw("fill_days", fill_days[tier], 56, 140)
    h1 = -np.log(1 - q1) / 365
    h2 = -np.log(1 - q2) / 365
    # effective agency cost per productive hour: the ramp share of each assignment is bought but not fully productive
    ag = ag / (1 - agency_ttp * (1 - ramp) / assign_days)
    total_base = np.zeros(n)
    total_conv = np.zeros(n)
    vacant_until = rng.gamma(2, fill / 2)             # initial recruiting time
    tenure = np.full(n, -1.0)                          # -1 = vacant
    total_conv += hire
    for t in range(days):
        need = daily_need[t]
        total_base += need * ag
        filled = tenure >= 0
        newly = (~filled) & (t >= vacant_until)
        tenure[newly] = 0
        filled = tenure >= 0
        prod = np.where(tenure < ORIENTATION_DAYS, 0.0, np.where(tenure < t_prof, ramp, 1.0)) * cap
        covered = np.where(filled, np.minimum(need, prod), 0.0)
        idle_hours = np.where(filled, np.maximum(prod - need, 0.0), 0.0)
        total_conv += np.where(filled, cap * staff, 0.0) + (need - covered) * ag - idle_hours * idle * ag
        # exits
        hz = np.where(tenure < 365, h1, h2)
        leave = filled & (rng.random(n) < hz)
        tenure[filled] += 1
        tenure[leave] = -1
        vacant_until[leave] = t + rng.gamma(2, fill[leave] / 2)
        total_conv[leave] += hire[leave]
    return total_base - total_conv


results = []
paths = []
s25 = s[s.year == Y]
for uid, g in s25.groupby("unit_id"):
    u = units.loc[uid]
    if u.turnover_tier not in ("high", "medium") or g.agency_rn_hours.sum() == 0:
        continue
    special = u.unit_name in ("Intensive Care", "Emergency Department", "Step-Down")
    a = g.sort_values("date").agency_rn_hours.to_numpy()
    a3 = np.tile(a, 3)
    k = 1
    while True:
        slice_ = np.clip(a3 - (k - 1) * cap, 0, cap)
        util = slice_.sum() / (cap * len(slice_))
        if util < 0.5:
            break
        sav = simulate(slice_, u.turnover_tier, special)
        results.append(dict(unit_id=uid, unit=f"{u.unit_name} ({fac[u.facility_id]})", tier=u.turnover_tier,
                            position=k, utilization=round(util, 3), mean_3yr=round(sav.mean()),
                            p10=round(np.percentile(sav, 10)), p90=round(np.percentile(sav, 90)),
                            prob_positive=round((sav > 0).mean(), 3)))
        k += 1
res = pd.DataFrame(results)
res["recommend"] = np.select([res.prob_positive >= 0.8, (res.prob_positive >= 0.6) & (res.mean_3yr > 0)],
                             ["convert", "pilot"], "keep on agency")
res.to_csv(OUT / "conversion_by_position.csv", index=False)

by_unit = res[res.recommend != "keep on agency"].groupby(["unit", "tier"]).agg(positions=("position", "size"),
                                                           mean_3yr=("mean_3yr", "sum"),
                                                           p10=("p10", "sum"), p90=("p90", "sum")).reset_index()
by_unit = by_unit.sort_values("mean_3yr", ascending=False)
by_unit.to_csv(OUT / "conversion_by_unit.csv", index=False)

# 4. Tornado: first position on the unit with the most agency use, inputs one at a time
top = s25.groupby("unit_id").agency_rn_hours.sum().idxmax()
tu = units.loc[top]
tspecial = tu.unit_name in ("Intensive Care", "Emergency Department", "Step-Down")
ta = np.tile(s25[s25.unit_id == top].sort_values("date").agency_rn_hours.to_numpy(), 3)
tslice = np.clip(ta, 0, cap)
base = dict(agency_rate=rates.set_index("year").agency[Y], benefits_load=C[("benefits_load_on_wages_pct", None)],
            hire_cost=HIRE_COST[0], ramp_productivity=RAMP_PRODUCTIVITY[0], idle_value=0.0,
            first_year_exit=p1[tu.turnover_tier], later_annual_exit=p2[tu.turnover_tier],
            days_to_proficiency=ttp_days[tspecial], fill_days=fill_days[tu.turnover_tier])
ranges = {
    "agency_rate": (base["agency_rate"] * 0.85, rates.set_index("year").agency[2023], "Agency bill rate (2025 -15% to 2023 level)"),
    "benefits_load": (0.45, 0.65, "Benefits load on wages (45% to 65%)"),
    "hire_cost": (HIRE_COST[1], HIRE_COST[2], "Cost per staff hire ($6k to $20k)"),
    "ramp_productivity": (RAMP_PRODUCTIVITY[1], RAMP_PRODUCTIVITY[2], "Productivity while ramping (30% to 70%)"),
    "first_year_exit": (base["first_year_exit"] * 0.5, min(0.6, base["first_year_exit"] * 1.5), "First-year exit (half to 1.5x)"),
    "later_annual_exit": (base["later_annual_exit"] * 0.5, min(0.5, base["later_annual_exit"] * 1.5), "Later annual exit (half to 1.5x)"),
    "days_to_proficiency": (base["days_to_proficiency"] * 0.7, 168, "Days to proficiency (experienced fast to new-grad median)"),
    "fill_days": (56, 140, "Days to fill a vacancy (56 to 140)"),
    "idle_value": (0.0, 0.5, "Value of unneeded hours floated elsewhere (0% to 50%)"),
}
mid = simulate(tslice, tu.turnover_tier, tspecial, n=2000, fixed=base).mean()
tor = []
for kname, (lo, hi, label) in ranges.items():
    vlo = simulate(tslice, tu.turnover_tier, tspecial, n=2000, fixed={**base, kname: lo}).mean()
    vhi = simulate(tslice, tu.turnover_tier, tspecial, n=2000, fixed={**base, kname: hi}).mean()
    tor.append(dict(input=label, low_value=lo, high_value=hi, savings_at_low=round(vlo), savings_at_high=round(vhi),
                    swing=round(abs(vhi - vlo))))
tor = pd.DataFrame(tor).sort_values("swing", ascending=False)
tor["base_case"] = round(mid)
tor["unit"] = f"{tu.unit_name} ({fac[tu.facility_id]}), position 1"
tor.to_csv(OUT / "tornado.csv", index=False)

# Scenario: on-time onboarding fix from case study B (first-year exits x 0.77)
fixed_b = {**base, "first_year_exit": base["first_year_exit"] * 0.77}
with_b = simulate(tslice, tu.turnover_tier, tspecial, n=2000, fixed=fixed_b).mean()
# Break-even agency bill rate for this position (bisection on the mean)
lo_r, hi_r = 60.0, 140.0
for _ in range(25):
    m_r = (lo_r + hi_r) / 2
    # the bill rate here is before the orientation fee and agency ramp adjustment, like the published benchmark
    v = simulate(tslice, tu.turnover_tier, tspecial, n=2000,
                 fixed={**base, "agency_rate": m_r + C[("agency_orientation_cost_per_contract", None)] / (13 * 36)}).mean()
    lo_r, hi_r = (lo_r, m_r) if v > 0 else (m_r, hi_r)
breakeven_bill = round((lo_r + hi_r) / 2, 2)
at2023 = simulate(tslice, tu.turnover_tier, tspecial, n=2000, fixed={**base, "agency_rate": rates.set_index("year").agency[2023]}).mean()
pd.DataFrame([dict(scenario="Base case (2025 rates)", mean_3yr=round(mid)),
              dict(scenario="Agency at the 2023 national rate", mean_3yr=round(at2023)),
              dict(scenario=f"Break-even agency bill rate: ${breakeven_bill}/hour (2025 benchmark $90.54)", mean_3yr=0),
              dict(scenario="First-year exits x 0.77 (case study B onboarding link, if causal)", mean_3yr=round(with_b))]
             ).to_csv(OUT / "scenario_onboarding.csv", index=False)  # file holds all scenarios

pd.set_option("display.width", 220)
print(rates.to_string(index=False)); print(); print(spend.round(0).to_string()); print(); print(inputs.to_string())
print(); print(res.to_string(index=False)); print(); print(by_unit.to_string(index=False))
print(f"\nTotal recommended positions: {by_unit.positions.sum()}, mean 3-yr {by_unit.mean_3yr.sum():,.0f} "
      f"(sum of P10 {by_unit.p10.sum():,.0f} to sum of P90 {by_unit.p90.sum():,.0f})")
print(); print(tor.to_string(index=False)); print(pd.read_csv(OUT / "scenario_onboarding.csv").to_string(index=False))
print(res.recommend.value_counts().to_string())
