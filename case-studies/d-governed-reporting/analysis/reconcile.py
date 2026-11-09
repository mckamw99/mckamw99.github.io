"""
Case study D, part 1: reconcile the published executive scorecard to source,
diagnose every mismatch, and backtest which controls would have caught it.
AI-assisted (Claude). Synthetic data only.
Usage: python reconcile.py
"""
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "a-what-complete-means" / "analysis"))
from common import DATA, load  # noqa: E402  (shared loader from case study A)

OUT = HERE.parent / "outputs"
OUT.mkdir(exist_ok=True)
T = load()
pub = T["report_published_values"].copy()
feed = pd.read_csv(DATA / "hr_feed_runs.csv", parse_dates=["run_date"])
lu, en = T["lms_users"], T["enrollments"]
fac = T["units"].set_index("unit_id").facility_id.map(T["facilities"].set_index("facility_id").facility_group)
lu = lu.assign(fgroup=lu.unit_id.map(fac).fillna("Unassigned"))
ac = en[en.course_id.str.startswith("AC-")].merge(lu[["lms_user_id", "fgroup", "user_source"]], on="lms_user_id")
ac = ac[ac.fgroup != "Unassigned"]


def scorecard(month_end, sources=("hr_feed",), as_of=None):
    """The scorecard's documented definition (report_lineage steps 4-5), rebuilt from source."""
    as_of = as_of or month_end
    s = ac[(ac.cycle_year == month_end.year) & ac.user_source.isin(sources) & (ac.assigned_date <= as_of)]
    done = (s.status == "completed") & (s.completion_date <= as_of)
    return pd.DataFrame({"denominator": s.groupby("fgroup").size(), "numerator": done.groupby(s.fgroup).sum()})


# 1. Reconcile every published facility-month --------------------------------
rows = []
for m, grp in pub.groupby("report_month"):
    me = pd.Period(m).to_timestamp(how="end").normalize()
    rc = scorecard(me)
    for _, r in grp.iterrows():
        n, dd = rc.loc[r.facility_group, ["numerator", "denominator"]]
        rows.append(dict(report_month=m, facility_group=r.facility_group, pub_num=r.numerator, pub_den=r.denominator,
                         src_num=int(n), src_den=int(dd)))
rec = pd.DataFrame(rows)
rec["match"] = (rec.pub_num == rec.src_num) & (rec.pub_den == rec.src_den)
rec["pub_pct"] = (100 * rec.pub_num / rec.pub_den).round(1)
rec["src_pct"] = (100 * rec.src_num / rec.src_den).round(1)
rec.to_csv(OUT / "reconciliation_all_months.csv", index=False)
bad = rec[~rec.match].copy()

# 2. Diagnose each mismatch by testing explanations against source -----------
diag = []
stale_lag = {}
for (m, fg), r in bad.set_index(["report_month", "facility_group"]).iterrows():
    me = pd.Period(m).to_timestamp(how="end").normalize()
    found = []
    if m not in stale_lag:
        g = pub[pub.report_month == m].set_index("facility_group")[["numerator", "denominator"]]
        stale_lag[m] = next((k for k in range(1, 15)
                             if scorecard(me, as_of=me - pd.Timedelta(days=k)).loc[g.index, ["numerator", "denominator"]].astype(int).equals(g.astype(int))), None)
    if stale_lag[m]:
        found.append(f"Stale data: every facility that month matches source as of {stale_lag[m]} days before month end")
    s = scorecard(me, sources=("hr_feed", "agency_manual")).loc[fg]
    if (s.numerator, s.denominator) == (r.pub_num, r.pub_den):
        found.append("Wrong population: matches source only if agency accounts are included")
    month_done = ac[(ac.fgroup == fg) & (ac.user_source == "hr_feed") & (ac.cycle_year == me.year)
                    & (ac.status == "completed") & (ac.completion_date.dt.strftime("%Y-%m") == m)]
    if r.pub_den == r.src_den and r.pub_num - r.src_num == len(month_done):
        found.append(f"Double load: numerator is over by exactly this month's {len(month_done)} completions")
    diag.append(dict(report_month=m, facility_group=fg, published=f"{r.pub_num}/{r.pub_den} ({r.pub_pct}%)",
                     source=f"{r.src_num}/{r.src_den} ({r.src_pct}%)", gap_pts=round(r.pub_pct - r.src_pct, 1),
                     diagnosis="; ".join(found) or "UNEXPLAINED"))
diag = pd.DataFrame(diag)
diag.to_csv(OUT / "mismatch_diagnosis.csv", index=False)

# 3. Backtest candidate controls over all 35 months --------------------------
months = sorted(pub.report_month.unique())
ctl = []
failed = set(feed[feed.status == "failed"].run_date.dt.date)
for i, m in enumerate(months):
    me = pd.Period(m).to_timestamp(how="end").normalize()
    g = pub[pub.report_month == m].set_index("facility_group")
    # K1 freshness: any failed feed run in the last 3 days of the month
    k1 = any((me - pd.Timedelta(days=d)).date() in failed for d in range(0, 3))
    # K3 numerator increase can't exceed completions recorded in source that month
    k3 = []
    if i > 0 and months[i - 1][:4] == m[:4]:
        prev = pub[pub.report_month == months[i - 1]].set_index("facility_group")
        for fg in g.index.intersection(prev.index):
            inc = g.loc[fg, "numerator"] - prev.loc[fg, "numerator"]
            src = ((ac.fgroup == fg) & (ac.user_source == "hr_feed") & (ac.cycle_year == me.year)
                   & (ac.status == "completed") & (ac.completion_date.dt.strftime("%Y-%m") == m)).sum()
            if inc > src:
                k3.append(fg)
    # K4 population: published denominator can't exceed the staff-only assigned count
    k4 = []
    for fg in g.index:
        staff = ((ac.fgroup == fg) & (ac.user_source == "hr_feed") & (ac.cycle_year == me.year) & (ac.assigned_date <= me)).sum()
        if g.loc[fg, "denominator"] > staff:
            k4.append(fg)
    # K5 trend alarm: rate moves more than 3 points month over month, outside Feb-Apr
    k5 = []
    if i > 0 and m[5:] not in ("02", "03", "04", "05") and months[i - 1][:4] == m[:4]:
        prev = pub[pub.report_month == months[i - 1]].set_index("facility_group")
        k5 = [fg for fg in g.index.intersection(prev.index) if abs(g.loc[fg, "completion_rate_pct"] - prev.loc[fg, "completion_rate_pct"]) > 3]
    k2 = sorted(bad[bad.report_month == m].facility_group)
    ctl.append(dict(report_month=m, K1_freshness=k1, K2_full_reconciliation=", ".join(k2),
                    K3_numerator_vs_source=", ".join(k3), K4_population=", ".join(k4), K5_trend_alarm=", ".join(k5)))
ctl = pd.DataFrame(ctl)
ctl.to_csv(OUT / "control_backtest.csv", index=False)

bad_months = set(bad.report_month)
summary = []
for c in ["K1_freshness", "K2_full_reconciliation", "K3_numerator_vs_source", "K4_population", "K5_trend_alarm"]:
    flagged = set(ctl[ctl[c].astype(bool) & (ctl[c] != "")].report_month)
    summary.append(dict(control=c, months_flagged=len(flagged), caught=", ".join(sorted(flagged & bad_months)) or "none",
                        false_alarms=len(flagged - bad_months), missed=", ".join(sorted(bad_months - flagged)) or "none"))
summary = pd.DataFrame(summary)
summary.to_csv(OUT / "control_summary.csv", index=False)

print(f"{len(rec)} facility-months reconciled; {len(bad)} mismatches in {len(bad_months)} months\n")
print(diag.to_string(index=False)); print(); print(summary.to_string(index=False))
print("\nFeed failures:", sorted(str(x) for x in failed))
