# Training compliance metric definitions (LIB-01)

**Purpose:** a shared definition sheet for compliance and leadership teams, so everyone who reports a training compliance number gets the same answer from the same data.

*Template plus a worked example at Tessaly Health, a fictional health system. All figures are from synthetic data and show the method, not real results.*

---

## 1. Shared rules (apply to every metric below)

| Rule | Definition |
|---|---|
| **Unit of measure** | A person, not an LMS account and not an enrollment row. Every account is mapped to one person before counting (see Identity). |
| **As-of date** | Every number states its as-of date. Compliance is judged on the due date; anything after that date is "late," even if it's complete. |
| **Population** | Employees on staff payroll who were employed on the assignment date and are still employed on the as-of date. Agency staff, students and test accounts are out of scope and reported separately. |
| **Requirement** | What's required comes from the course catalog's priority, not from the label on an individual enrollment. If they disagree, the catalog wins and the mismatch is logged. |
| **Evidence** | A requirement is met by a passed attempt (or recorded attendance for instructor-led sessions) on the **current version** of the course, on or before the as-of date. An LMS status of "completed" with no attempt behind it doesn't count. |
| **Versions** | Passing last year's version doesn't meet this year's requirement. |
| **Identity** | Accounts with an HR employee ID map to that person. A manual account maps to a person only if one employee with the same name was employed when the account was created, or, if there are several namesakes, only one of them has records that the manual account fills in. Anything else waits for an administrator. |
| **Duplicates** | One requirement per person, module and cycle, however many enrollment rows exist. Duplicate attempt rows count once. |
| **Exemptions** | A valid exemption (approved, in force on the as-of date) removes that requirement from the denominator. It is never counted as a completion. Exemption counts are reported alongside the rate. |
| **Leavers** | People who left before the as-of date are removed. Their open enrollments are not counted as overdue. |
| **Attribution** | People are reported under the facility of their HR unit on the as-of date, not the unit stored in the LMS. |

## 2. Metrics

| # | Metric | Numerator | Denominator | Use |
|---|---|---|---|---|
| M1 | **Annual compliance rate (people)**, the headline | People in the population who met every non-exempt annual module by the due date | People in the population with at least one non-exempt module | Board, executive and regulator reporting |
| M2 | Annual compliance rate (requirements) | Non-exempt person-module requirements met by the due date | All non-exempt person-module requirements | Operations: where the gaps are |
| M3 | Completion by year end (people) | People who completed every non-exempt module by 31 Dec, late or not | Same as M1 | Shows how much of the gap closes late. Not a compliance number. |
| M4 | Overdue requirements | Requirements past due, not met, not exempt, person still employed | (count) | Manager follow-up lists |
| M5 | New-hire compliance on time | New hires who met their at-hire modules within 30 days of hire | New hires still employed on day 30 | Onboarding quality |
| M6 | Certification currency | People in roles that need a certification who hold an unexpired one on the as-of date | People in those roles on the as-of date | Needs a role-to-certification requirements matrix. Defined here, not yet computed. |

## 3. Edge cases

| Situation | Rule |
|---|---|
| Rehired employee | Same person. Earlier completions don't carry into a new cycle; the current cycle's requirement applies from the rehire date. |
| Transferred mid-cycle | Counted once, under the unit held on the as-of date. |
| On leave on the due date | Covered by a leave exemption if one is in force; otherwise due like anyone else. |
| Left before the due date | Out of the population. |
| Hired after the campaign started | Measured by M5 on their own due date, not by M1 for that cycle. |
| Two enrollments for the same module (two rules fired, or a reload) | One requirement. Met if either has evidence. |
| Completion on a duplicate account | Counts once the account is linked to the person. Until then, it's listed as unresolved. |
| Failed, then passed | Met on the pass date. |
| Completed after the due date | Not compliant for M1 and M2; counts for M3. |
| Passed last year's version | Not met. |
| Status "completed," no attempt | Not met; sent for evidence follow-up. |
| Exemption expired before the due date | Not exempt. |
| Enrollment labeled "Recommended" for a Required course | Required. Fix the label at the source. |
| Agency or test account | Out of scope for M1–M5. |

## 4. Worked example: Tessaly Health, 2025 cycle (synthetic)

As of 30 Apr 2025, the due date for the five annual modules:

| Metric | Value |
|---|---|
| Published scorecard (old definition: LMS "completed" over all enrollment rows) | 77.5% (16,106 of 20,780 rows) |
| M2 Annual compliance rate (requirements) | 81.6% (14,923 of 18,299 requirements) |
| **M1 Annual compliance rate (people)** | **67.3% (2,469 of 3,666 people)** |
| M3 Completion by year end (people) | 76.3% |
| Requirements removed by exemptions | 511 |

The old number sat between the two governed numbers by accident. It counted leavers and duplicate rows, which pulled it down. It also judged rows rather than people, which pushed it up.

## 5. Ownership and change control

| Role | Responsibility |
|---|---|
| Definition owner (Compliance Office) | Approves this sheet and any change to it |
| Data steward (Learning Operations) | Maintains the identity map, catalog priorities and exemptions; runs the data-quality checks before each publication |
| Report owner (BI team) | Builds reports only from these definitions; shows the version and as-of date on every report |

Changes are versioned. A new version is applied to past periods too, so trends stay comparable, and the old number is shown next to the new one for one cycle.

## Why it's built this way

I made the person the unit because the risk sits with people: an auditor asks whether a named employee finished the training, not what share of enrollment rows are green. Requiring evidence rather than trusting a status field costs a few points but means every "compliant" can be shown to an auditor. Exemptions come out of the denominator instead of counting as completions, so the rate can't be raised by approving more exemptions, and the exemption count is published next to it. The tradeoff is a lower headline number than leaders are used to. That's why the sheet tells you to show the old and new numbers side by side for one cycle.

*Format: PDF, generated from this page.*

---
*Personal project. All data is synthetic or public, and the company is fictional. Views are my own and not affiliated with or endorsed by any current or former employer.*
