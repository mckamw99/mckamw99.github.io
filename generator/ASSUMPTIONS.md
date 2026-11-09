# Assumptions and distributions

The values live in `config.py`; change them there and rerun. "Realized" comes from `validate.py` on seed 20261108. Where a public benchmark exists, the parameter was tuned so the realized rate lands near it. Where none was found, the value is my own assumption and is marked **assumption**.

Tessaly Health is fictional and sits in an unnamed region, so it uses **national** averages. No local market and no employer data were used.

## Sources

| Key | Source | Used for |
|---|---|---|
| NSI-26 | NSI Nursing Solutions, *2026 National Health Care Retention & RN Staffing Report* (calendar 2025; 527 hospitals) | RN and hospital turnover, first-year turnover, vacancy, time to recruit, cost per turnover |
| NSI-25 | NSI Nursing Solutions, *2025 National Health Care Retention & RN Staffing Report* (calendar 2024; 450 hospitals) | Same measures for 2024, turnover by specialty |
| ECEC | BLS, Employer Costs for Employee Compensation, RNs in private hospitals, Dec 2024 (TED article, May 2025) | Wage per hour worked and benefits load |
| OEWS | BLS, Occupational Employment and Wage Statistics, SOC 29-1141, May 2024 and May 2025 | Wage growth year to year |
| SIA | SIA/NATHO Travel Nurse Benchmarking Survey, selected findings 2025 and 2026 | Agency bill rates |
| NRP | Vizient/AACN Nurse Residency Program outcomes, as reported by Vizient (2025) | Residency retention check |

## 1. Company and window

| Assumption | Value | Benchmark | Realized |
|---|---|---|---|
| Window | 1 Jan 2023 to 31 Dec 2025 | | |
| Facilities | 1 flagship hospital, 2 community hospitals, 20 clinics, home health, system office | locked decision | 25 |
| Units and departments | 41 nursing units, 79 non-nursing departments | | 120 |
| Budgeted positions | 4,122 | "about 4,000 staff" | 3,888 to 3,938 filled |
| Nursing share | RNs, LPNs, nursing assistants, nurse managers | "roughly half" | 49% |
| RN position vacancy | 8%/5%/3% open on day 1 by tier, plus 6%/4%/2% of RN positions that stay open all window (hard to fill) | NSI-26: 8.6% national RN vacancy | 8.8–8.9% |

Turnover tiers follow NSI's specialty ranking. **High:** Behavioral Health, Emergency, Step-Down, Medical-Surgical (NSI-26: 22.5%, 20.7%, 19.0%, 18.1%). **Low:** Perioperative, Women and Infants (NSI-26: 14.9%, 15.0%), plus clinics and Nursing Administration. **Medium:** Intensive Care, Float Pool, Home Health.

## 2. Workforce flow

| Assumption | Value | Benchmark | Realized (2023 / 2024 / 2025) |
|---|---|---|---|
| Voluntary turnover, year 2+ | RN high 17%, medium 13%, low 10%; LPN/NA 15–22%; clinical support 14%; administrative 12%; facilities/EVS 22%; managers 7% | | see next rows |
| All RNs | | NSI-25: 16.4% (2024); NSI-26: 17.6% (2025) | 19.1% / 16.4% / 15.4% |
| High-tier RNs | | NSI-26 high specialties: 18.1–22.5% | 23.7% / 20.9% / 21.9% |
| Low-tier RNs | | NSI-26 low specialties: 13.4–15.0% | 14.6% / 10.1% / 10.9% |
| All hospital staff | | NSI-25: 18.3%; NSI-26: 18.5% | 20.1% / 17.8% / 18.3% |
| First-year multiplier | Year-1 hazard × 2.0 | NSI-26: 22.7% of new RNs leave within a year | 21.5% (2023 hires), 17.4% (2024 hires) |
| Involuntary turnover | 2% per year | **assumption** | |
| Time to fill | Gamma(shape 2); mean 95 days high-tier RN, 75 other RN, 45 everyone else | NSI-26: 78 days to recruit an experienced RN (range 56–102) | |
| Starting tenure | Gamma(shape 1.3, scale 5 years), capped at 35 | **assumption** | |
| FTE | 1.0 (62%), 0.9 (14%), 0.75 (10%), 0.6 (9%), 0.5 (5%) | **assumption** | |
| Internal transfer fills | 10% of RN fills, 6% of others | **assumption** | 161 transfers |
| Rehires | 5% of external fills | **assumption** | 103 |
| New-grad RNs | 35% of inpatient RN hires, 5% elsewhere | **assumption** | 197 residents |

Low-tier RN turnover runs a little under NSI's lowest specialties. Clinics and administration are mixed into that tier, and NSI surveys hospitals only.

## 3. Planted effects (case study B)

These are the true answers an analysis should try to recover. They're in `ground_truth/planted_effects.csv`.

| ID | Planted effect | Built-in trap |
|---|---|---|
| E-01 | Year-1 voluntary exit hazard × 0.70 if role onboarding is finished within 30 days. Sized to be detectable with about 2,500 hires (**assumption**) | On-time rate is 80% normally, 65% on high-turnover units, which also lose more people. Naive ratio on this seed: 0.74. |
| E-02 | Year-1 hazard × 0.65 for new-grad RNs with attendance propensity of 0.80 or higher (Beta(5, 2), minus 0.10 on high-turnover units) (**assumption**) | Completers must stay 12 months, so they show 0% year-1 exits: immortal-time bias. About 130 residents have a full year of follow-up, with about two dozen first-year exits, so any honest estimate is noisy. Realized resident first-year exit is 20%, above the NRP-reported 11% (89% retention). NRP's figure covers participating programs, so it's likely a favorable comparison; I kept the gap rather than tune to it. |
| E-04 | Days to proficiency: new grad Gamma(mean 140, sd 35) if high attender, (170, 45) if not; experienced (75, 25); agency (12, 4); × 1.2 on ICU, ED, Step-Down (**assumption**) | Nurses who leave first are censored, not missing. |

## 4. Staffing and cost (case study C)

| Assumption | Value | Benchmark | Realized |
|---|---|---|---|
| Required RN hours | Budgeted RNs × mean FTE × 36 h/week ÷ 7 × (1 − 7% absence) | **assumption** | |
| Demand variation | +6% Dec–Feb, −3% Jul–Aug, daily noise sd 4% | **assumption** | |
| Coverage order | Overtime (25–40% of the gap, capped at 12% of required; 60–80% where no agency), then agency, then unfilled | **assumption**; no public US benchmark found for overtime share | High tier: agency 6.4%, OT 4.4%, unfilled 2.8% |
| Agency booking | Monthly, 13-week contracts covering 90% of the past 28 days' gap, 14-day lead, 25% extension chance | **assumption**; 13 weeks is the standard travel contract | 497 agency nurses, 634 segments |
| Staff RN wage per hour worked | $49.10 / $51.09 / $53.24 (2023–25) | ECEC: $51.09 in Dec 2024. Other years scaled about 4% a year from OEWS growth (approximate) | |
| Benefits load on wages | 56% | ECEC: benefits $28.43 vs. wages $51.09 per hour worked | Fully loaded staff RN about $79.70 in 2024 |
| Overtime premium | 1.5 × wage | federal minimum overtime premium | |
| Agency bill rate | $106.63 / $90.13 / $90.54 | SIA national aggregate | 2024 agency premium over a fully loaded staff hour: about 13% |
| Cost per RN turnover | $61,110 (2024), $60,090 (2025) | NSI-25, NSI-26 | |
| Agency orientation per contract | $1,200 | **assumption** | |

**What the benchmarks change for case C.** With public figures, an agency hour costs only about 13% more than a fully loaded staff hour in 2024. That's down from about 39% in 2023. So the case for converting agency nurses rests less on the hourly rate and more on turnover cost, orientation, time to proficiency and continuity. Also, NSI's turnover cost already includes some vacancy coverage, so adding it to agency hours would double-count. The case study has to pick one.

## 5. Learning records (case studies A and D)

No public benchmark was found for training completion behavior, so this whole section is **assumption**.

| Assumption | Value | Realized |
|---|---|---|
| Annual compliance | 5 modules, new version each year; assigned 1 Feb, due 30 Apr | |
| New-hire compliance | Hires from 15 Jan on get current modules at hire, due in 30 days | Hires 15 Jan–1 Feb get both: a natural duplicate |
| Completion behavior | Base 88% on time, with person (sd 0.6) and unit (sd 0.3) effects on the log-odds, −0.3 on high-turnover units; of the rest, 65% late (due + Exp(21 days)), 35% never; 4% skip one module | Raw on-time 74–77% of enrollments, before cleanup |
| Assessments | 7% fail first try, then retake; 10% of those fail twice | |
| Exemptions | 2.5% leave of absence per cycle; 1% equivalent credit for Workplace Safety | 302 and 102 |
| Certifications | Life Support (2 yr), Equipment (1 yr), Specialty Unit (2 yr), Hazardous Materials (1 yr); renewal 60 days before expiry; 85% on time, 10% late, 5% lapse | 19,247 records |
| Onboarding | Orientation due in 14 days, role onboarding in 30, nursing unit checklist in 60 | |
| Residency | Cohorts Feb, Jun, Sep; 12 monthly sessions; complete = 10+ attended and still employed at session 12 | 197 residents |
| LMS accounts | Nightly HR feed; 5% of deactivations lag 8–40 days; 30% of rehires get a new account; 2% of staff have a manual duplicate; agency accounts manual, 75% with an agency ID | 6,910 accounts |

## 6. Planted data-quality and pipeline issues (case studies A and D)

Listed with row counts in `ground_truth/planted_issues.csv`.

| ID | Issue |
|---|---|
| DQ-01 | Some 2025 learners completed the 2024 version of Information Security |
| DQ-02 | Exact duplicate passed-attempt rows |
| DQ-03 | Enrollments marked completed with no attempt |
| DQ-04 | Due date before assigned date |
| DQ-05 | 2024 Fire and Emergency campaign reloaded at Community North; duplicates never completed |
| DQ-06 | 2025 Respectful Workplace at the clinics labeled "Recommended" though the course is Required |
| DQ-07 | Manual duplicate accounts; one compliance cycle recorded on the duplicate |
| DQ-08 | Test accounts with completions |
| DQ-09 | Courses with no owner; one not reviewed since 2019 |
| DQ-10 | Agency accounts with no agency ID |
| PI-01 | Aug 2024 scorecard built from 4-day-old data after an HR feed outage |
| PI-02 | Mar 2025 Community North numerator double-counts March completions |
| PI-03 | Oct 2025 Flagship Hospital includes agency accounts |
| AX-01 to 03 | BI access: two terminated managers never revoked, one unit manager with system scope, one aggregate-only analyst with person-level detail |

## 7. Known limits

- Benchmarks are national survey averages. NSI surveys acute-care hospitals only, so clinic and home-health rates are extrapolated.
- 2023 and 2025 wages are scaled from one 2024 benchmark, so treat them as approximate.
- Only RN hours are simulated at the unit-day level.
- No patient, clinical or quality outcomes, no demographics, no pay by person.
- Names come from short lists of common names, so different people share names on purpose.
- The published scorecard uses one deliberately naive definition (LMS status "completed" over all enrollments). Case study A replaces it.
