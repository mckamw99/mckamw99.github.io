"""
Case study D, part 3: report rationalization worksheet (LIB-51).
AI-assisted (Claude). Synthetic data only. Criteria are applied in order; the
first one that fires decides. The metric-family grouping is my judgment,
recorded here so it can be reviewed.
Usage: python rationalize.py
"""
from pathlib import Path

import pandas as pd

DATA = Path(__file__).resolve().parents[3] / "generator" / "data"
OUT = Path(__file__).resolve().parents[1] / "outputs"
rc = pd.read_csv(DATA / "report_catalog.csv")

FAMILY = {  # report -> (metric family, source)
    "RPT-001": ("annual compliance", "LMS"), "RPT-002": ("annual compliance", "LMS"),
    "RPT-003": ("overdue training", "LMS"), "RPT-004": ("overdue training", "LMS"),
    "RPT-005": ("certification status", "LMS"), "RPT-006": ("certification status", "LMS"),
    "RPT-007": ("onboarding", "LMS"), "RPT-008": ("onboarding", "LMS"),
    "RPT-009": ("residency", "LMS"), "RPT-010": ("agency use", "staffing"),
    "RPT-011": ("agency use", "staffing"), "RPT-012": ("agency use", "staffing"),
    "RPT-013": ("annual compliance (raw)", "LMS"), "RPT-014": ("catalog", "LMS"),
    "RPT-015": ("elective usage", "LMS"), "RPT-016": ("turnover", "HR"), "RPT-017": ("turnover", "HR"),
    "RPT-018": ("proficiency", "HR + LMS"), "RPT-019": ("training hours", "LMS"),
    "RPT-020": ("LMS logins", "LMS"), "RPT-021": ("compliance by role", "LMS"),
    "RPT-022": ("compliance by role", "LMS"),
}
RUNS_PER_90 = {"daily": 90, "weekly": 13, "monthly": 3, "quarterly": 1}
rc["metric_family"] = rc.report_id.map(lambda r: FAMILY[r][0])
rc["source"] = rc.report_id.map(lambda r: FAMILY[r][1])
rc["views_per_run"] = (rc.views_last_90_days / rc.refresh_frequency.map(RUNS_PER_90)).round(1)
EXEC = {"Executive team"}

out = []
for _, r in rc.iterrows():
    peers = rc[(rc.metric_family == r.metric_family) & (rc.report_id != r.report_id) & (rc.catalog_status == "active")]
    if r.catalog_status == "duplicate":
        d, why, act = "Retire", "Catalog marks it a duplicate", \
            f"Point users to {peers.sort_values('views_last_90_days').report_id.iloc[-1]}"
    elif r.views_last_90_days == 0:
        d, why, act = "Retire", "No views in 90 days", "Retire in 30 days unless the owner names a decision it supports"
    elif len(peers):
        keep = pd.concat([peers, rc[rc.report_id == r.report_id]]).sort_values("views_last_90_days", ascending=False).iloc[0]
        d = "Keep (absorbs peers)" if keep.report_id == r.report_id else "Merge"
        why = f"Same metric and source as {', '.join(peers.report_id)}"
        act = "One report, role-based views by audience" if d.startswith("Keep") else f"Fold into {keep.report_id} as a view"
    elif r.metric_family.endswith("(raw)"):
        d, why, act = "Keep, restrict", "Row-level extract", "Analyst role only; replace with a governed dataset"
    elif r.views_per_run < 1:
        d, why, act = "Review", "Fewer views than runs", "Owner confirms use or it retires next quarter"
    else:
        d, why, act = "Keep", "Used, unique", ""
    gov = ("Governed definition and pre-publication checks required"
           if (r.primary_audience in EXEC or "compliance" in r.metric_family
            or (d.startswith("Keep") and peers.primary_audience.isin(EXEC).any())) and d not in ("Retire", "Merge") else "")
    out.append(dict(report_id=r.report_id, report_name=r.report_name, owner=r.owner_department,
                    audience=r.primary_audience, metric_family=r.metric_family, views_90d=r.views_last_90_days,
                    views_per_run=r.views_per_run, decision=d, reason=why, action=act, executive_control=gov))
ws = pd.DataFrame(out)
ws.to_csv(OUT / "report_rationalization.csv", index=False)
print(ws[["report_id", "report_name", "views_90d", "decision", "reason"]].to_string(index=False))
print(); print(ws.decision.value_counts().to_string())
