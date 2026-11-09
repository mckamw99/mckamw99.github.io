"""
Validation for case study C. AI-assisted (Claude).
1. Closed-form check: with no exits and a fully used position, the simulation must match
   a hand calculation.
2. The loaded staff rate matches the BLS total-compensation benchmark it was built from.
3. Converted positions never cover more hours than the unit actually bought from agency.
4. Seed stability: the pilot list doesn't change with a different random seed.
Usage: python validate_c.py   (exit 1 on any FAIL)
"""
import sys

import numpy as np
import pandas as pd

import convert as M

res = []


def check(name, ok, detail=""):
    res.append(("PASS" if ok else "FAIL", name, detail))


# 1. Closed form
D = 365 * 3
cap = M.cap
need = np.full(D, cap)
f = dict(M.base)
f.update(first_year_exit=1e-9, later_annual_exit=1e-9, ramp_productivity=0.5, hire_cost=12000, benefits_load=0.56,
         days_to_proficiency=86, fill_days=90)
sim = M.simulate(need, "high", True, n=20000, fixed=f).mean()
staff = M.C[("staff_rn_wage_per_hour_worked", 2025)] * 1.56
ag = f["agency_rate"] / (1 - M.agency_ttp * 0.5 / M.assign_days)
tp, L = 86, 90
hand = (-12000 - M.ORIENTATION_DAYS * cap * staff + (tp - M.ORIENTATION_DAYS) * (cap * 0.5 * ag - cap * staff)
        + (D - L - tp) * (cap * ag - cap * staff))
check("Simulation matches the hand calculation (no exits, full use)", abs(sim - hand) / abs(hand) < 0.02,
      f"simulation {sim:,.0f} vs hand {hand:,.0f}")

# 2. Benchmark read-back
r24 = M.rates.set_index("year").loc[2024, "staff_loaded"]
check("2024 loaded staff rate within 0.5% of BLS ECEC total compensation ($79.53/hour worked)",
      abs(r24 - 79.53) / 79.53 < 0.005, f"model {r24}")

# 3. Coverage never exceeds agency hours bought
pos = pd.read_csv(M.OUT / "conversion_by_position.csv")
s25 = M.s25.groupby("unit_id").agency_rn_hours.sum()
over = []
for uid, g in pos.groupby("unit_id"):
    covered = sum(np.clip(M.s25[M.s25.unit_id == uid].agency_rn_hours.to_numpy() - (k - 1) * cap, 0, cap).sum()
                  for k in g.position)
    if covered > s25[uid] + 1e-6:
        over.append(uid)
check("Positions modeled never cover more than the agency hours bought", not over, f"{len(pos)} positions on {pos.unit_id.nunique()} units")

# 4. Seed stability
M.rng = np.random.default_rng(7)
alt = []
for _, r in pos.iterrows():
    u = M.units.loc[r.unit_id]
    a3 = np.tile(M.s25[M.s25.unit_id == r.unit_id].sort_values("date").agency_rn_hours.to_numpy(), 3)
    sav = M.simulate(np.clip(a3 - (r.position - 1) * cap, 0, cap), u.turnover_tier,
                     u.unit_name in ("Intensive Care", "Emergency Department", "Step-Down"))
    alt.append("convert" if (sav > 0).mean() >= 0.8 else "pilot" if ((sav > 0).mean() >= 0.6 and sav.mean() > 0) else "keep on agency")
same = (pos.recommend.values == np.array(alt)).mean()
check("Recommendations stable under a different random seed (at least 90% identical)", same >= 0.9,
      f"{same:.0%} identical; changed: {list(pos[pos.recommend.values != np.array(alt)].apply(lambda r: f'{r.unit_id}#{r.position}', axis=1))}")

# 5. The LIB-26 calculator (JavaScript) reproduces the Python model for the same inputs
import json, re, subprocess
html = (M.OUT.parent / "calculator.html").read_text()
js = re.search(r"<script>(.*?)</script>", html, re.S).group(1)
js = js[:js.index("const ids")]
p = dict(bill=90.54, fee=1200, attp=float(M.agency_ttp), aassign=float(M.assign_days), wage=53.24, load=56, hire=12000,
         orient=14, ttp=86, ramp=50, fill=95, p1=25.3, p2=18.8, util=100, years=3)
js += f"\nconsole.log(JSON.stringify(model({json.dumps(p)}, 4000)));"
jsv = json.loads(subprocess.run(["node", "-e", js], capture_output=True, text=True).stdout)["net"]
f2 = dict(M.base)
f2.update(first_year_exit=0.253, later_annual_exit=0.188, ramp_productivity=0.5, hire_cost=12000, benefits_load=0.56,
          days_to_proficiency=86, fill_days=95, idle_value=0)
pyv = M.simulate(np.full(1095, cap), "high", True, n=4000, fixed=f2).mean()
check("Calculator (JavaScript) matches the Python model within 10%", abs(jsv - pyv) / abs(pyv) < 0.10,
      f"calculator {jsv:,.0f} vs Python {pyv:,.0f}")

out = pd.DataFrame(res, columns=["result", "check", "detail"])
(M.OUT / "validation_c.md").write_text("# Case study C validation\n\nSynthetic data.\n\n" + out.to_markdown(index=False) + "\n")
print(out.to_string(index=False, max_colwidth=120))
sys.exit(1 if (out.result == "FAIL").any() else 0)
