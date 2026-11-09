# LMS data-quality checklist (LIB-04) and check script (LIB-27)

**Purpose:** a pre-publication checklist that a learning operations or reporting team runs before any compliance number leaves the building. The script runs it automatically.

*Results below are from synthetic data at Tessaly Health, a fictional health system. They show the method, not real results.*

---

## The checklist

Run in this order: accounts first, because every later check depends on knowing who a record belongs to.

### Accounts
- [ ] **C01** Test and training accounts are tagged and excluded.
- [ ] **C02** Manual accounts with no HR ID are matched to a person, with the rule that matched them recorded.
- [ ] **C03** Manual accounts that can't be matched are listed for an administrator, not guessed.
- [ ] **C04** Contractor and agency accounts carry the external ID that links them to their roster.
- [ ] **C05** Accounts for people who've left are deactivated within 7 days.

### Enrollments
- [ ] **C06** One requirement per person, module and cycle (repeated assignments collapsed).
- [ ] **C07** Every "completed" status has an attempt or attendance record behind it.
- [ ] **C08** Due dates fall on or after assigned dates.
- [ ] **C09** Completion dates fall on or after assigned dates.
- [ ] **C10** Priority labels on enrollments match the course catalog.
- [ ] **C11** Open enrollments on inactive accounts are identified so leavers don't show as overdue.

### Attempts
- [ ] **C12** Duplicate attempt rows are counted once.
- [ ] **C13** Passes on a prior year's version are not credited to the current year.

### Catalog
- [ ] **C14** Every active course has an owner.
- [ ] **C15** Every active course was reviewed in the last 3 years.

## Results at Tessaly Health (synthetic)

| Check | What it found | Rows | Severity | What the metric does with them |
|---|---|---:|---|---|
| C01 | Test accounts | 6 | high | Excluded from every metric |
| C02 | Manual accounts linked to one person | 66 | high | Merged into that person's record |
| C03 | Manual accounts that can't be linked to one person | 33 | high | Held out; listed for an administrator |
| C04 | Agency accounts with no agency ID | 126 | medium | Out of the staff metric; can't be linked to the agency roster |
| C05 | Accounts active more than 7 days after termination | 118 | medium | Access risk; no metric effect once termination is applied |
| C06 | Rows in a repeated person-module-year enrollment | 3,218 | high | Collapsed to one requirement |
| C07 | "Completed" with no attempt | 164 | high | Not counted; sent for evidence follow-up |
| C08 | Due date before assigned date | 281 | medium | Due date rebuilt from the assignment rule |
| C09 | Completion before assignment | 0 | low | None found |
| C10 | Priority label disagrees with catalog | 740 | medium | Catalog wins |
| C11 | Open enrollments on inactive accounts | 3,280 | medium | Removed if the person had left by the as-of date |
| C12 | Duplicate passed-attempt rows | 328 | low | Counted once |
| C13 | Prior-year version passed in a later year | 69 | high | Not credited |
| C14 | Courses with no owner | 2 | medium | Owner assigned before next cycle |
| C15 | Courses not reviewed in 3+ years | 9 | low | Review scheduled |

**How I know the checks work.** The synthetic data generator plants known defects and records them in an answer key. I ran the checks first and opened the answer key afterward. Every check with a matching planted defect found exactly the planted number of rows. All 66 manual accounts the matching rules linked went to the right person. The 33 they couldn't link are the ones a person needs to look at.

## The script

`analysis/dq_checks.py` runs all 15 checks and writes two files:
- `outputs/dq_results.csv`: one row per check, with counts, severity and handling
- `outputs/dq_flagged_records.csv`: every flagged record ID, so nothing is dropped silently

*Code is AI-assisted (Claude). I specified the checks and the handling rules and validated the output against the answer key.*

## Why it's built this way

Checks report and route; they don't delete. A flagged record goes to a list with a stated handling rule, so the number can be explained and the source can be fixed. Identity comes first because a duplicate account quietly turns one compliant person into two half-compliant ones, and no later check can see that. I stopped the matching rules where they'd start guessing. The 33 unresolved accounts are cheaper for an administrator to settle than a wrong match is to defend. Severity reflects effect on the published number, not effort to fix, so the high items get done before publication and the rest go on the backlog.

*Format: PDF checklist (generated from this page) plus the script in the repo.*

---
*Personal project. All data is synthetic or public, and the company is fictional. Views are my own and not affiliated with or endorsed by any current or former employer.*
