# Learning measurement plan: new-hire onboarding redesign (LIB-17)

**Purpose:** a measurement plan written *before* a program launches. It's for learning and HR leaders who want to know in advance what the program has to show, how, by when, and what they'll do with the answer.

*Worked example at Tessaly Health, a fictional health system. Baselines come from synthetic data (see case studies B and A). Not a real program.*

---

## 1. The program

Tessaly is redesigning new-hire onboarding for all roles. Two changes:

1. **Manager check-ins on day 14 and day 25.** A prompt goes to the hiring manager with the new hire's onboarding progress and three conversation questions.
2. **A shorter role onboarding module.** The current 30-day module is split into two parts, and anything not needed in the first month moves to day 60.

**Why now:** case study B found that people who finish role onboarding within 30 days leave less often in their first year (adjusted risk ratio 0.77). That's an association. This plan is built to find out whether changing onboarding *changes* retention.

## 2. Questions the plan must answer

| # | Question | Who needs the answer | When |
|---|---|---|---|
| Q1 | Do more new hires finish role onboarding within 30 days? | Learning operations | Month 6 |
| Q2 | Do new hires feel ready for the job at day 45? | Hiring managers, learning design | Month 6 |
| Q3 | Do fewer new hires leave in their first 90 days, and in their first year? | HR leadership, finance | Months 9 and 24 |
| Q4 | Do new RNs reach proficiency sooner? | Nursing leadership | Month 12 |
| Q5 | Did managers actually hold the check-ins? | Learning operations | Monthly |

Q5 comes first in practice: if the check-ins didn't happen, Q1–Q4 can't be credited to them.

## 3. Measures

Organized by the four levels of the Kirkpatrick model, a public evaluation framework, plus a delivery check.

| Level | Measure | Definition | Source | Baseline (synthetic) |
|---|---|---|---|---|
| Delivery | Check-in completion | Share of new hires whose manager recorded both check-ins within 3 days of the prompt | Check-in form in the LMS | New measure |
| Reaction | Day-45 readiness | Share answering 4 or 5 to "I have what I need to do my job" (1–5 scale) | Day-45 pulse survey | New measure |
| Learning | On-time role onboarding | Passed attempt on role onboarding within 30 days of hire, among those still employed on day 30. Same evidence rule as case study A | LMS attempts, HR hire date | 70.5% |
| Behavior | Days to proficiency (RNs) | Days from hire to unit proficiency sign-off; people who leave first are counted as censored, not dropped | Proficiency records | Median 74 (experienced), 168 (new graduate) |
| Results | 90-day exit | Any exit within 90 days of hire | HR system | 6.8% |
| Results | First-year voluntary exit | Voluntary exit within 365 days of hire | HR system | 22.1% |

Every measure uses the governed definitions in the compliance metric sheet (LIB-01) where they overlap: the same population rules, evidence rule and as-of dates.

## 4. Design: staggered rollout

A before-and-after comparison wouldn't work here. Turnover moves with the job market, so a drop after launch could be the market, not the program. Instead:

- **Six unit groups start in a random order, one per month**, over six months. At any point, some groups have the new onboarding and some don't, so they're compared over the same period.
- **The order is drawn once, by lottery, and recorded before launch.** Nobody chooses which units go first.
- **Analysis:** compare outcomes for hires who got the new onboarding with hires in the same months who didn't, adjusting for unit and role (the confounders found in case study B).

Leaders get a fair comparison, and every unit has the program within six months.

## 5. What the data can and can't detect

About 850 people are hired per year. At 80% power, with half of each period's hires on the new onboarding:

| Measure | Smallest change detectable | When |
|---|---|---|
| On-time role onboarding (baseline 70.5%) | +11.6 points after 6 months; +8.5 points after 12 | Q1: month 6 |
| First-year voluntary exit (baseline 22.1%) | Risk ratio 0.66 after 12 months of hires; 0.75 after 24 | Q3: month 24 |

**So the decision at month 6 rests on the leading indicators** (delivery, readiness, on-time onboarding). Retention is reported at month 24 with its interval, and a "no difference" result before then will be labeled underpowered, not negative.

## 6. Decision rules, agreed before launch

| At | If | Then |
|---|---|---|
| Month 3 | Check-in completion is below 60% | Fix delivery before judging anything else |
| Month 6 | On-time onboarding up 8+ points and readiness at least as high | Keep both changes; finish the rollout |
| Month 6 | No change in on-time onboarding | Review the module split; keep the check-ins if readiness improved |
| Month 24 | First-year exit risk ratio below 1 with an interval that excludes 1 | Report as a retention effect and fund it as standard practice |
| Month 24 | Interval includes 1 | Report as "not shown"; keep the program only if the leading indicators justify it on their own |

## 7. Data, roles and reporting

| Item | Owner |
|---|---|
| Plan, analysis, and the month-6 and month-24 reports | Learning analytics |
| Rollout order lottery and record | Learning operations, witnessed by HR |
| Check-in form and pulse survey | Learning operations |
| HR and proficiency data | HR systems team, nursing education |
| Decision at each checkpoint | VP of HR and the CNO's designee |

Survey responses are reported only for groups of 5 or more people. Monthly results go in the governed weekly view (see case study D) as a separate tile, with the definition version stated.

## 8. Risks

- **Managers skip the check-ins.** Delivery is tracked monthly and comes before any outcome claim.
- **Other changes during the rollout** (a pay increase, a new recruiting source). Logged as they happen; the staggered design absorbs changes that hit all units at once.
- **Measuring what's easy.** Completion of the new module is not on the measure list on purpose. It shows the module was taken, not that anything changed.

## Why it's built this way

The plan fixes the questions, measures, comparison and decision rules before the first hire goes through, so the result can't be argued into whatever someone hoped for. A staggered rollout gives a fair comparison without holding the program back from anyone for long. Sizing the detectable effect up front is the step most plans skip. It shows that retention takes two years to judge, so the six-month decision has to rest on leading indicators, and everyone knows that before launch. Delivery is measured first, because a program that wasn't delivered can't be credited or blamed.

*Format: PDF, generated from this page.*

---
*Personal project. All data is synthetic or public, and the company is fictional. Views are my own and not affiliated with or endorsed by any current or former employer.*
