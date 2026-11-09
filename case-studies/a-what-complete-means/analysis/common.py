"""Shared loading and identity resolution for case study A. AI-assisted (Claude)."""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "generator" / "data"
GT = ROOT / "generator" / "ground_truth"
OUT = Path(__file__).resolve().parents[1] / "outputs"
OUT.mkdir(exist_ok=True)

AC_FAMILIES = ["AC-01", "AC-02", "AC-03", "AC-04", "AC-05"]


def load():
    names = ["facilities", "units", "persons", "employees", "employee_unit_history", "lms_users",
             "courses", "enrollments", "attempts", "exemptions", "certifications",
             "report_published_values"]
    T = {n: pd.read_csv(DATA / f"{n}.csv", low_memory=False) for n in names}
    for t, cols in {"employees": ["hire_date", "termination_date"],
                    "employee_unit_history": ["start_date", "end_date"],
                    "lms_users": ["created_date", "deactivated_date"],
                    "enrollments": ["assigned_date", "due_date", "status_date", "completion_date"],
                    "attempts": ["started_at", "finished_at"],
                    "exemptions": ["granted_date", "expires_date"],
                    "certifications": ["issued_date", "expires_date"]}.items():
        for c in cols:
            T[t][c] = pd.to_datetime(T[t][c])
    return T


def resolve_identity(T):
    """Map every LMS account to a person.

    Rule 1: an account with an HR employee ID maps to that employee's person.
    Rule 2: a manual account with no HR ID maps to a person if exactly one
            employee with the same first and last name was employed on the day
            the account was created.
    Rule 3: if several namesakes qualify, keep the one whose own account is
            missing every module the manual account completed in that cycle
            (the records complement each other). If that still isn't unique,
            the account stays unresolved for an administrator.
    Test and agency accounts are not mapped to staff.
    """
    lu, emp, per = T["lms_users"], T["employees"], T["persons"]
    emp_p = emp.merge(per, on="person_id")
    m = lu[["lms_user_id", "hr_employee_id", "user_source", "first_name", "last_name", "created_date"]].copy()
    m = m.merge(emp[["employee_id", "person_id"]], left_on="hr_employee_id", right_on="employee_id", how="left")
    m["match_rule"] = m.person_id.notna().map({True: "hr_id", False: None})
    manual = m[(m.user_source == "manual") & m.person_id.isna()]
    en = T["enrollments"]
    hr_acct = m[m.person_id.notna()][["lms_user_id", "person_id"]]
    rows = []
    for _, r in manual.iterrows():
        c = emp_p[(emp_p.first_name == r.first_name) & (emp_p.last_name == r.last_name)
                  & (emp_p.hire_date <= r.created_date)
                  & (emp_p.termination_date.isna() | (emp_p.termination_date >= r.created_date))]
        people = list(c.person_id.unique())
        if len(people) == 1:
            rows.append((r.lms_user_id, people[0], "name_and_employment"))
            continue
        done = set(en[(en.lms_user_id == r.lms_user_id) & (en.status == "completed")].course_id)
        fits = []
        for p in people:
            accts = hr_acct[hr_acct.person_id == p].lms_user_id
            theirs = en[en.lms_user_id.isin(accts) & en.course_id.isin(done)]
            if done and len(theirs) and not (theirs.status == "completed").any():
                fits.append(p)
        if len(fits) == 1:
            rows.append((r.lms_user_id, fits[0], "name_and_complementary_records"))
        else:
            rows.append((r.lms_user_id, None, f"unresolved_{len(people)}_candidates"))
    fix = pd.DataFrame(rows, columns=["lms_user_id", "person_id_m", "rule_m"])
    m = m.merge(fix, on="lms_user_id", how="left")
    m["person_id"] = m.person_id.fillna(m.person_id_m)
    m["match_rule"] = m.match_rule.fillna(m.rule_m)
    m.loc[m.user_source.isin(["test", "agency_manual"]), "match_rule"] = m.user_source
    return m[["lms_user_id", "user_source", "person_id", "match_rule"]]


def employed_on(emp, day):
    day = pd.Timestamp(day)
    return emp[(emp.hire_date <= day) & (emp.termination_date.isna() | (emp.termination_date >= day))]


def facility_on(T, employee_ids, day):
    """Facility group of each employee's unit on a given day, from HR unit history."""
    day = pd.Timestamp(day)
    h = T["employee_unit_history"]
    h = h[(h.start_date <= day) & (h.end_date.isna() | (h.end_date >= day)) & h.employee_id.isin(employee_ids)]
    fac = T["units"].set_index("unit_id").facility_id.map(T["facilities"].set_index("facility_id").facility_group)
    return h.assign(facility_group=h.unit_id.map(fac)).drop_duplicates("employee_id").set_index("employee_id").facility_group
