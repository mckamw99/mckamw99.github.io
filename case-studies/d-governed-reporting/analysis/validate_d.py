"""
Validation for case study D. AI-assisted (Claude).
Compares what the analysis found with the generator's answer key (opened only
after the analysis was done), and checks the mockup's numbers against case study A.
Usage: python validate_d.py   (exit 1 on any FAIL)
"""
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parents[1] / "outputs"
gt = pd.read_csv(ROOT / "generator" / "ground_truth" / "planted_issues.csv").set_index("issue_id")
res = []


def check(name, ok, detail=""):
    res.append(("PASS" if ok else "FAIL", name, detail))


diag = pd.read_csv(OUT / "mismatch_diagnosis.csv")
check("Every mismatch has a tested explanation", not diag.diagnosis.str.contains("UNEXPLAINED").any(),
      f"{len(diag)} mismatched facility-months")
months = {m: set(g.facility_group) for m, g in diag.groupby("report_month")}
check("Mismatched months are exactly the planted ones (PI-01..03)", sorted(months) == ["2024-08", "2025-03", "2025-10"],
      str(sorted(months)))
check("PI-02 diagnosed as a double load at Community North",
      months.get("2025-03") == {"Community North"} and diag[diag.report_month == "2025-03"].diagnosis.str.contains("Double load").all())
check("PI-03 diagnosed as agency accounts at Flagship Hospital",
      months.get("2025-10") == {"Flagship Hospital"} and diag[diag.report_month == "2025-10"].diagnosis.str.contains("agency").all())
check("PI-01 diagnosed as stale data, 4 days", diag[diag.report_month == "2024-08"].diagnosis.str.contains("4 days").all(),
      f"{len(months.get('2024-08', []))} facilities differed; answer key lists {gt.loc['PI-01', 'rows_affected']} rows "
      "(one facility had no activity in the stale window, so its numbers didn't change)")
f = pd.read_csv(OUT / "access_findings.csv")
check("Access review finds the planted issues AX-01..03 and nothing else",
      (f.rule == "R1").sum() == gt.loc["AX-01", "rows_affected"] and (f.rule == "R2").sum() == gt.loc["AX-02", "rows_affected"]
      and (f.rule == "R3").sum() == gt.loc["AX-03", "rows_affected"] and len(f) == 4, f"{len(f)} findings")
a = pd.read_csv(ROOT / "case-studies" / "a-what-complete-means" / "outputs" / "bridge_2025.csv")
mk = pd.read_csv(OUT / "lib03_numbers.csv").iloc[0]
check("Mockup numbers equal case study A's governed results (M1, M2, overdue)",
      mk.m1_pct == a.rate_pct.iloc[-1] and mk.m2_pct == a.rate_pct.iloc[-2]
      and mk.overdue == a.denominator.iloc[-2] - a.numerator.iloc[-2],
      f"mockup {mk.m1_pct}% / {mk.m2_pct}% / {mk.overdue}; A {a.rate_pct.iloc[-1]}% / {a.rate_pct.iloc[-2]}% / {a.denominator.iloc[-2] - a.numerator.iloc[-2]}")
out = pd.DataFrame(res, columns=["result", "check", "detail"])
(OUT / "validation_d.md").write_text("# Case study D validation\n\nSynthetic data.\n\n" + out.to_markdown(index=False) + "\n")
print(out.to_string(index=False, max_colwidth=120))
sys.exit(1 if (out.result == "FAIL").any() else 0)
