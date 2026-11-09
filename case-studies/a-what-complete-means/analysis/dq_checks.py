"""
LMS data-quality checks (LIB-04 checklist, LIB-27 script) for case study A.
AI-assisted (Claude). Runs on the Tessaly Health synthetic data only.

Each check reports how many rows it flags and what the compliance metric does
with them. Nothing is deleted; every flagged row is written out for review.
Usage: python dq_checks.py
"""
import pandas as pd

from common import AC_FAMILIES, OUT, load, resolve_identity

T = load()
lu, en, at, co, emp = T["lms_users"], T["enrollments"], T["attempts"], T["courses"], T["employees"]
ident = resolve_identity(T)
WINDOW_END = pd.Timestamp("2025-12-31")
checks = []
flagged = []


def add(cid, area, name, rows, handling, severity, key="enrollment_id"):
    checks.append(dict(check_id=cid, area=area, check=name, rows_flagged=len(rows), severity=severity,
                       metric_handling=handling))
    if len(rows):
        flagged.append(pd.DataFrame({"check_id": cid, "record_id": rows[key].astype(str).values}))


# Accounts
add("C01", "accounts", "Test accounts", lu[lu.user_source == "test"],
    "Excluded from every metric", "high", "lms_user_id")
unres = ident[(ident.user_source == "manual") & ident.person_id.isna()]
res = ident[ident.match_rule.isin(["name_and_employment", "name_and_complementary_records"])]
add("C02", "accounts", "Manual accounts linked to one person (name, employment date, complementary records)", res,
    "Merged into that person's record", "high", "lms_user_id")
add("C03", "accounts", "Manual accounts that can't be linked to one person", unres,
    "Held out; listed for an administrator to resolve", "high", "lms_user_id")
add("C04", "accounts", "Agency accounts with no agency ID", lu[(lu.user_source == "agency_manual") & lu.external_id.isna()],
    "Out of staff metric; agency metric can't link them to the roster", "medium", "lms_user_id")
term = emp[emp.termination_date.notna()].merge(lu, left_on="employee_id", right_on="hr_employee_id")
lag = (term.deactivated_date.fillna(WINDOW_END + pd.Timedelta(days=1)) - term.termination_date).dt.days
add("C05", "accounts", "Accounts still active more than 7 days after termination", term[lag > 7],
    "Access risk; no metric effect once termination is applied", "medium", "lms_user_id")

# Enrollments
ac = en[en.course_id.str[:5].isin(AC_FAMILIES)].merge(co[["course_id", "course_family_id"]], on="course_id")
ac = ac.merge(ident[["lms_user_id", "person_id"]], on="lms_user_id")
dups = ac[ac.person_id.notna()].duplicated(["person_id", "course_id"], keep=False)
add("C06", "enrollments", "More than one enrollment for the same person, module and year",
    ac[ac.person_id.notna()][dups], "Collapsed to one requirement per person and module", "high")
add("C07", "enrollments", "Status 'completed' with no attempt on record",
    en[(en.status == "completed") & ~en.enrollment_id.isin(at.enrollment_id)],
    "Not counted as complete; sent for evidence follow-up", "high")
add("C08", "enrollments", "Due date earlier than assigned date", en[en.due_date < en.assigned_date],
    "Due date rebuilt from the assignment rule", "medium")
add("C09", "enrollments", "Completion date earlier than assigned date", en[en.completion_date < en.assigned_date],
    "Would be reviewed; none expected", "low")
pri = en.merge(co[["course_id", "catalog_priority"]], on="course_id")
add("C10", "enrollments", "Enrollment priority label disagrees with the course catalog",
    pri[pri.priority_label != pri.catalog_priority], "Catalog priority wins", "medium")
open_term = en.merge(ident, on="lms_user_id").merge(lu[["lms_user_id", "status"]].rename(columns={"status": "acct"}), on="lms_user_id")
add("C11", "enrollments", "Open enrollments on inactive accounts",
    open_term[(open_term.acct == "inactive") & open_term.status.isin(["not_started", "in_progress"])],
    "Removed from the denominator if the person had left by the as-of date", "medium")

# Attempts
passed = at[at.result == "passed"]
dup_at = passed[passed.duplicated(["enrollment_id", "finished_at", "result"], keep="first")]
add("C12", "attempts", "Duplicate passed-attempt rows", dup_at, "Counted once", "low", "attempt_id")
cur = at.merge(co[["course_id", "category", "version_year"]], on="course_id") \
    .merge(en[["enrollment_id", "assigned_date"]], on="enrollment_id")
oldv = cur[(cur.category == "annual_compliance") & (cur.result == "passed")
           & (cur.assigned_date.dt.year > cur.version_year)]
add("C13", "attempts", "Prior-year version of an annual module started and passed in a later year", oldv,
    "Doesn't satisfy the current year's requirement", "high", "attempt_id")

# Catalog
add("C14", "catalog", "Courses with no owner", co[co.owner_role.isna()], "Owner assigned before next cycle", "medium", "course_id")
stale = co[(pd.to_datetime(co.last_reviewed) < WINDOW_END - pd.DateOffset(years=3)) & co.retired_date.isna()]
add("C15", "catalog", "Active courses not reviewed in 3+ years", stale, "Content review scheduled", "low", "course_id")

res_df = pd.DataFrame(checks)
res_df.to_csv(OUT / "dq_results.csv", index=False)
pd.concat(flagged).to_csv(OUT / "dq_flagged_records.csv", index=False)
print(res_df.to_string(index=False))
