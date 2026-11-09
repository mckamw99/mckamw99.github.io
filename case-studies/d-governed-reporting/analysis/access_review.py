"""
Case study D, part 2: audit BI access against the role-based access model (LIB-07).
AI-assisted (Claude). Synthetic data only.
Usage: python access_review.py
"""
from pathlib import Path

import pandas as pd

DATA = Path(__file__).resolve().parents[3] / "generator" / "data"
OUT = Path(__file__).resolve().parents[1] / "outputs"
AS_OF = pd.Timestamp("2025-12-31")

roles = pd.read_csv(DATA / "bi_access_roles.csv").set_index("bi_role")
bu = pd.read_csv(DATA / "bi_users.csv", parse_dates=["granted_date", "revoked_date"])
emp = pd.read_csv(DATA / "employees.csv", parse_dates=["hire_date", "termination_date"]).set_index("employee_id")
bu = bu.join(emp[["role_code", "termination_date", "current_unit_id"]], on="employee_id")
active = bu[bu.revoked_date.isna() | (bu.revoked_date > AS_OF)]

findings = []


def add(rule, desc, rows, fix):
    for _, r in rows.iterrows():
        findings.append(dict(rule=rule, finding=desc, bi_user_id=r.bi_user_id, employee_id=r.employee_id,
                             bi_role=r.bi_role, scope=f"{r.scope_type}:{r.scope_value}", fix=fix))


# R1 Leavers: access ends within 2 business days of termination
add("R1", "Access still active after the person left", active[active.termination_date.notna()],
    "Revoke now; add the BI tool to the HR leaver workflow")
late = bu[bu.termination_date.notna() & bu.revoked_date.notna()
          & ((bu.revoked_date - bu.termination_date).dt.days > 2)]
add("R1", "Access revoked more than 2 days after leaving", late, "Tighten the leaver workflow")
# R2 Scope must match the role's allowed scope
add("R2", "Scope wider than the role allows",
    active[active.scope_type != active.bi_role.map(roles.allowed_scope)], "Reset scope to the role's allowed scope")
# R3 Person-level detail only where the role allows it
add("R3", "Person-level detail on a role that's aggregate only",
    active[active.person_level_detail & ~active.bi_role.map(roles.person_level_detail).astype(bool)],
    "Remove person-level detail, or move the user to a role that has it, with approval")
# R4 Movers: unit scope follows the person's current unit
unit = active[(active.scope_type == "unit") & (active.scope_value != active.current_unit_id)]
add("R4", "Unit scope no longer matches the person's unit", unit, "Update scope at transfer")

f = pd.DataFrame(findings, columns=["rule", "finding", "bi_user_id", "employee_id", "bi_role", "scope", "fix"])
f.to_csv(OUT / "access_findings.csv", index=False)

# Least-privilege profile of active access
prof = active.groupby(["bi_role", "scope_type", "person_level_detail"]).size().rename("active_users").reset_index()
prof.to_csv(OUT / "access_profile.csv", index=False)
sys_person = active[(active.scope_type == "system") & active.person_level_detail]
print(f"{len(active)} active BI users on {AS_OF.date()}; {len(f)} findings\n")
print(f.to_string(index=False)); print(); print(prof.to_string(index=False))
print(f"\nUsers who can see every person in the system: {len(sys_person)}")
