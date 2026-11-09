"""
Validation for case study B. AI-assisted (Claude).
Compares the estimates with the effects planted in the generator (answer key opened
only after the analysis) and runs a permutation test as an independent check of the
main association. Usage: python validate_b.py   (exit 1 on any FAIL)
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parents[1] / "outputs"
eff = pd.read_csv(ROOT / "generator" / "ground_truth" / "planted_effects.csv").set_index("effect_id")
res = []


def check(name, ok, detail=""):
    res.append(("PASS" if ok else "FAIL", name, detail))


ob = pd.read_csv(OUT / "onboarding_results.csv").set_index("analysis")
main = ob.loc["main"]
hr = float(eff.loc["E-01", "true_value"])
p_late = main.rate_late_pct / 100
expected_rr = (1 - (1 - p_late) ** hr) / p_late   # 12-month risk ratio implied by the planted hazard ratio
lo, hi = map(float, main.adjusted_rr_ci.split("-"))
check("E-01: adjusted 95% CI contains the risk ratio implied by the planted hazard ratio",
      lo <= expected_rr <= hi, f"planted HR {hr} -> expected RR {expected_rr:.2f}; estimate {main.adjusted_rr} ({main.adjusted_rr_ci})")
check("E-01: the crude estimate is further from 1 than the adjusted one (confounding by unit, as planted)",
      main.crude_rr < main.adjusted_rr, f"crude {main.crude_rr}, adjusted {main.adjusted_rr}")
neg = ob.loc["negative control: involuntary exit"]
nlo, nhi = map(float, neg.adjusted_rr_ci.split("-"))
check("Negative control: no effect planted on involuntary exits, and the CI includes 1", nlo <= 1 <= nhi,
      f"{neg.adjusted_rr} ({neg.adjusted_rr_ci})")
sens = ob.drop(index=["main", "negative control: involuntary exit"])
check("Sensitivity analyses all point the same way", (sens.adjusted_rr < 1).all(), str(sens.adjusted_rr.to_dict()))

# Permutation test on the crude risk difference (independent of the chi-square)
h = pd.read_csv(OUT / "onboarding_cohort.csv")
obs = h[h.on_time == 1].left_vol.mean() - h[h.on_time == 0].left_vol.mean()
rng = np.random.default_rng(20261108)
perm = [(lambda s: h.left_vol[s == 1].mean() - h.left_vol[s == 0].mean())(rng.permutation(h.on_time.values))
        for _ in range(5000)]
p_perm = (np.abs(perm) >= abs(obs)).mean()
check("Permutation test agrees with the chi-square p-value (both < 0.05)", p_perm < 0.05 and main.p_value < 0.05,
      f"permutation p = {p_perm:.4f}, chi-square p = {main.p_value}")

r = pd.read_csv(OUT / "residency_results.csv").iloc[1]
check("E-02: landmark estimate points the planted direction", r.rr < 1,
      f"planted HR {eff.loc['E-02', 'true_value']}; estimate {r.rr} ({r.rr_ci}), not significant")
pr = pd.read_csv(OUT / "proficiency_results.csv").iloc[0]
check("E-04: early attenders reach proficiency faster, as planted", pr.median1 < pr.median0,
      f"medians {pr.median1} vs {pr.median0}; planted means 140 vs 170 (x1.2 on specialty units)")
out = pd.DataFrame(res, columns=["result", "check", "detail"])
(OUT / "validation_b.md").write_text("# Case study B validation\n\nSynthetic data.\n\n" + out.to_markdown(index=False) + "\n")
print(out.to_string(index=False, max_colwidth=120))
sys.exit(1 if (out.result == "FAIL").any() else 0)
