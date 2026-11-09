"""
Validation for case study A. AI-assisted (Claude).

1. Read-back: the published-definition step reproduces the published scorecard.
2. Independent recompute: the governed 2025 result rebuilt in SQL (DuckDB) from
   the raw CSVs must match the pandas result exactly, by facility.
3. Answer key: identity matches and data-quality checks compared with the
   generator's ground truth (read only after the analysis was done).
4. Trace: five people followed end to end, for a human read.
Usage: python validate_a.py   (exit 1 on any FAIL)
"""
import sys

import duckdb
import pandas as pd

from common import DATA, GT, OUT, load, resolve_identity

T = load()
res = []


def check(name, ok, detail=""):
    res.append(("PASS" if ok else "FAIL", name, detail))


# 1. Read-back against the published scorecard ---------------------------
b = pd.read_csv(OUT / "bridge_2025.csv")
pub = T["report_published_values"]
apr = pub[pub.report_month == "2025-04"]
check("Step 0 equals the published April 2025 scorecard",
      (b.numerator[0], b.denominator[0]) == (apr.numerator.sum(), apr.denominator.sum()),
      f"bridge {b.numerator[0]}/{b.denominator[0]} vs published {apr.numerator.sum()}/{apr.denominator.sum()}")

# 2. Independent SQL recompute ---------------------------------------------
ident = resolve_identity(T)
con = duckdb.connect()
for t in ("employees", "enrollments", "attempts", "exemptions", "employee_unit_history", "units", "facilities"):
    con.execute(f"create view {t} as select * from read_csv_auto('{DATA / (t + '.csv')}', all_varchar=true)")
con.register("ident", ident)
sql = """
with pop as (
  select distinct on (person_id) employee_id, person_id from employees
  where hire_date <= '2025-02-01' and (termination_date is null or termination_date >= '2025-04-30')),
req as (select p.*, f.family, f.family || '-2025' as course_id
        from pop p cross join (values ('AC-01'),('AC-02'),('AC-03'),('AC-04'),('AC-05')) f(family)),
ev as (select distinct i.person_id, a.course_id from attempts a
       join ident i using (lms_user_id)
       where a.result = 'passed' and a.finished_at <= '2025-04-30' and i.person_id is not null),
exm as (select distinct i.person_id, x.course_family_id from exemptions x join ident i using (lms_user_id)
        where x.cycle_year = '2025' and x.granted_date <= '2025-04-30'
          and (x.expires_date is null or x.expires_date >= '2025-04-30')),
m as (select r.*, (ev.person_id is not null) as ok
      from req r left join ev on ev.person_id = r.person_id and ev.course_id = r.course_id
      where not exists (select 1 from exm where exm.person_id = r.person_id
                        and (exm.course_family_id = 'AC-ALL' or exm.course_family_id = r.family))),
per as (select employee_id, person_id, bool_and(ok) as compliant from m group by 1, 2),
fac as (select h.employee_id, f.facility_group from employee_unit_history h
        join units u using (unit_id) join facilities f using (facility_id)
        where h.start_date <= '2025-04-30' and (h.end_date is null or h.end_date >= '2025-04-30'))
select facility_group, count(*) as people, sum(compliant::int) as compliant
from per join fac using (employee_id) group by 1 order by 1
"""
q = con.execute(sql).df().set_index("facility_group")
py = pd.read_csv(OUT / "compliance_by_facility_2025.csv").set_index("facility_group")[["people", "compliant"]].sort_index()
same = (q[["people", "compliant"]].astype(int).sort_index().values == py.values).all()
check("SQL recompute matches pandas by facility (2025)", bool(same),
      f"SQL {int(q.compliant.sum())}/{int(q.people.sum())} vs pandas {int(py.compliant.sum())}/{int(py.people.sum())}")

# 3. Answer key ------------------------------------------------------------
key = pd.read_csv(GT / "manual_account_owners.csv")
linked = ident[ident.match_rule.isin(["name_and_employment", "name_and_complementary_records"])].merge(key, on="lms_user_id", how="left")
correct = (linked.person_id == linked.true_person_id).sum()
check("Every linked manual account went to the right person", correct == len(linked),
      f"{correct} of {len(linked)} correct; {len(key) - len(linked)} of {len(key)} left unresolved")
by_rule = linked.groupby("match_rule").apply(lambda x: f"{(x.person_id == x.true_person_id).sum()}/{len(x)}", include_groups=False)
res.append(("INFO", "Identity matches by rule", by_rule.to_dict()))

dq = pd.read_csv(OUT / "dq_results.csv").set_index("check_id").rows_flagged
gt = pd.read_csv(GT / "planted_issues.csv").set_index("issue_id").rows_affected
pairs = {"C13": "DQ-01", "C12": "DQ-02", "C07": "DQ-03", "C08": "DQ-04", "C10": "DQ-06", "C01": "DQ-08",
         "C14": "DQ-09", "C04": "DQ-10"}
for c, g in pairs.items():
    check(f"{c} finds exactly the planted {g} rows", dq[c] == gt[g], f"{dq[c]} vs {gt[g]}")
check("C02 + C03 account for every planted duplicate account (DQ-07)", dq["C02"] + dq["C03"] == gt["DQ-07"],
      f"{dq['C02']} + {dq['C03']} vs {gt['DQ-07']}")
en = T["enrollments"].merge(ident, on="lms_user_id")
r = en[(en.course_id == "AC-04-2024") & (en.assignment_rule == "annual_campaign")]
reload = r.groupby("person_id").size()
check("C06 catches the planted 2024 reload (DQ-05)", (reload > 1).sum() >= gt["DQ-05"],
      f"{(reload > 1).sum()} people with a repeated AC-04-2024 campaign row vs {gt['DQ-05']} planted")

# 4. Trace five people -------------------------------------------------------
per = pd.read_csv(OUT / "person_compliance_2025.csv")
dup_people = set(ident[ident.match_rule.isin(["name_and_employment", "name_and_complementary_records"])].person_id)
man25 = T["enrollments"][T["enrollments"].assignment_rule.eq("manual_roster") & T["enrollments"].course_id.str.endswith("-2025")]
dup25 = set(ident[ident.lms_user_id.isin(man25.lms_user_id)].person_id) & dup_people
sample = pd.concat([per[per.person_id.isin(dup25)].head(2), per[~per.satisfied].head(2), per[per.satisfied].head(1)])
lines = []
for _, p in sample.iterrows():
    accts = ident[ident.person_id == p.person_id].lms_user_id.tolist()
    e = T["enrollments"][T["enrollments"].lms_user_id.isin(accts) & T["enrollments"].course_id.str.endswith("-2025")
                         & T["enrollments"].course_id.str.startswith("AC-")]
    a = T["attempts"][T["attempts"].enrollment_id.isin(e.enrollment_id) & (T["attempts"].result == "passed")].copy()
    e = e.copy()
    for c in ("completion_date", "due_date"):
        e[c] = e[c].dt.date
    a["finished_at"] = a.finished_at.dt.date
    lines.append(f"### {p.person_id} ({p.facility_group}): governed = {'compliant' if p.satisfied else 'not compliant'}\n"
                 f"Accounts: {', '.join(accts)}\n\n"
                 + e[["lms_user_id", "course_id", "assignment_rule", "status", "completion_date", "due_date"]].to_markdown(index=False)
                 + "\n\nPassed attempts:\n\n" + (a[["course_id", "finished_at"]].to_markdown(index=False) if len(a) else "none") + "\n")
(OUT / "trace_sample.md").write_text("# Traced sample (2025 cycle)\n\nSynthetic data.\n\n" + "\n".join(lines))
res.append(("INFO", "Trace written for human review", "outputs/trace_sample.md"))

out = pd.DataFrame(res, columns=["result", "check", "detail"])
(OUT / "validation_a.md").write_text("# Case study A validation\n\nSynthetic data.\n\n" + out.to_markdown(index=False) + "\n")
print(out.to_string(index=False, max_colwidth=110))
sys.exit(1 if (out.result == "FAIL").any() else 0)
