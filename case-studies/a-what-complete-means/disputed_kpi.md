# Resolving a disputed KPI (LIB-50)

**Purpose:** a one-page process for when two teams report different numbers for the same metric and leadership wants to know which one is right.

*Worked example at Tessaly Health, a fictional health system, using synthetic data.*

---

## The process

**1. Freeze both numbers.** Record each figure with its source, query or report, as-of date and who produced it. Nobody reruns anything until both are captured.

**2. Write each definition out in full.** Fill the same template for both: population, unit of measure, numerator, denominator, as-of date, evidence, exclusions. Most disputes end here, because the two teams were measuring different things.

**3. Reconcile one rule at a time.** Start from one number and change one rule at a time until you reach the other. Record the effect of each change. This is the bridge: it shows exactly where the gap comes from and how big each piece is.

**4. Separate data defects from definition choices.** A duplicate account is a defect: fix it at the source and both numbers move. "Do exemptions count as complete?" is a choice: someone with authority has to decide it.

**5. Take choices to the definition owner.** Present each open choice with its effect on the number and the risk of each option. The owner decides; the decision goes into the metric definition sheet with a version number.

**6. Publish once, with a note.** Publish the agreed number with its definition version. For one cycle, show the old number beside it and a one-line explanation of the difference.

**7. Retire the other number.** The losing report is changed to the agreed definition or retired. Two live versions of one KPI is how the dispute started.

## Worked example: Tessaly Health, April 2025 (synthetic)

The executive scorecard showed **77.5%** annual compliance. The compliance office, counting people, believed it was much lower.

| Step | What happened |
|---|---|
| 1. Freeze | Scorecard: 77.5% (enrollment rows, LMS status, month end). Compliance office: a people count from their own tracker. |
| 2. Definitions | The scorecard counted enrollment rows, including leavers, duplicates and not-yet-due assignments, and trusted the LMS status. The compliance office counted people. |
| 3. Bridge | Removing leavers +1.5 pts; campaign population +0.0; one requirement per person and module +0.2; merging duplicate accounts +0.3; requiring evidence −0.1; removing exemptions +2.2. That gives 81.6% of requirements. Moving to the people level: 67.3%. |
| 4. Defects vs. choices | Defects: duplicate accounts, duplicate rows, statuses with no evidence, a 2024 reload that depressed that year's number. Choices: people or requirements as the unit; exemptions in or out. |
| 5. Decision | Headline metric is people fully compliant (M1); the requirement-level rate (M2) is kept for operations. Exemptions leave the denominator and are reported beside the rate. |
| 6. Publish | 67.3% (definition v1.0), with the old 77.5% shown once and explained. |
| 7. Retire | The old scorecard query is replaced; the legacy duplicate scorecard is retired. |

## Why it's built this way

Most KPI disputes are definition disputes wearing a data costume, so the process forces both definitions onto paper before anyone touches a query. The rule-by-rule bridge matters more than the final answer: it turns "your number is wrong" into "these four rules explain the gap," which people can agree on. Separating defects from choices keeps analysts from quietly making policy decisions in SQL. Retiring the losing number is the step teams skip, and it's the one that keeps the dispute from coming back next quarter.

*Format: PDF one-pager, generated from this page.*

---
*Personal project. All data is synthetic or public, and the company is fictional. Views are my own and not affiliated with or endorsed by any current or former employer.*
