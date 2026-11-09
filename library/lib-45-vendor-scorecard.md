# LMS / LXP vendor selection scorecard (LIB-45)

**Purpose:** a vendor-neutral scorecard for a learning technology leader choosing a learning platform. It covers the criteria and weights, the knock-out requirements, a scripted demo, and reference-check questions, so the decision rests on the organization's needs rather than on the best demo.

*Worked example at Tessaly Health, a fictional health system. Vendors are fictional (A, B, C). All prices are invented.*

---

## 1. Knock-out requirements (pass or fail, checked before scoring)

A vendor that fails any of these is out, however well it scores elsewhere.

| # | Requirement | Evidence to ask for |
|---|---|---|
| K1 | Accessibility conformance to WCAG 2.1 AA for the learner interface | A current accessibility conformance report, plus a test with a screen reader during the demo |
| K2 | Full export of our data (users, enrollments, attempts, completions, history) at any time and at contract end, in a documented format, at no extra fee | Contract language and a sample export file |
| K3 | Single sign-on with our identity provider | Supported standards (SAML 2.0 or OpenID Connect) |
| K4 | Independent security attestation | Current SOC 2 Type II report or equivalent |

## 2. Weighted criteria

| Criterion | Weight | What a 4 looks like |
|---|---:|---|
| Learner experience and accessibility | 15 | Works on a phone for staff without desks; finds the right course in two clicks; passes our accessibility test |
| Administration and content management | 15 | Rule-based assignments by role and unit; course versioning; instructor-led session management; bulk actions with an audit trail |
| Compliance and audit | 15 | Due dates, recertification cycles, exemptions with expiry dates, attestation, and a record of who changed what |
| Data access and reporting | 15 | Event-level data available to our warehouse daily; documented data dictionary; reporting doesn't depend on the vendor's services team |
| Integration | 10 | HR feed with error reporting; automated user provisioning; supports SCORM, xAPI and LTI content |
| Security and privacy | 10 | Role-based administration with least privilege; admin audit logs; data residency stated in the contract |
| Total cost of ownership (5 years) | 10 | Lowest total of licenses, implementation, services, internal staff time and exit cost |
| AI features and governance | 5 | AI features can be turned off by function; our data isn't used to train shared models without consent; AI output is labeled |
| Vendor viability and support | 5 | Stable finances; a support model with named contacts and service levels; customers like us as references |

**Scale:** 0 = absent, 1 = weak or workaround only, 2 = meets some needs, 3 = meets needs, 4 = strong and shown in the demo. Each criterion's score is the panel's agreed score, not an average of private scores, and the panel writes one line of evidence for each.

## 3. Scripted demo (same script for every vendor, 2 hours)

Vendors run these scenarios live, on their platform, with our sample data. No slides during this part.

1. A nurse is hired, transfers units after three months, leaves, and is rehired a year later. Show their account, assignments and history at each step.
2. Assign the five annual compliance modules to all staff, due in 90 days, with an exemption for someone on leave that expires automatically.
3. Publish a new version of one module mid-cycle. Show who's affected and how completions on the old version are treated.
4. Produce the compliance rate for one facility as of a past date, then show the underlying records that make up the number.
5. Add a contractor who isn't in the HR system, then remove their access on their last day.
6. Export every enrollment and attempt for the last year as a file, now, in front of us.
7. A unit manager logs in: show exactly what they can and can't see.
8. Show the AI features, then turn each one off.

Scenario 6 is where vendors most often hesitate. It's also the one that decides whether you can measure anything later.

## 4. Reference questions

Ask references the vendor didn't pick as well as the ones it did.

1. How long did implementation take, against the plan?
2. What did you have to buy in services that you expected to be included?
3. How do you get your data out, and how often?
4. When something breaks, how long until a person who can fix it responds?
5. What does the vendor's roadmap promise that you're still waiting for?
6. How did renewal pricing compare with the first contract?
7. What would you check more carefully if you were choosing again?

## 5. Worked example: Tessaly Health (synthetic)

| Criterion | Weight | A | B | C |
|---|---:|---:|---:|---:|
| Learner experience and accessibility | 15 | 3 | 4 | 4 |
| Administration and content management | 15 | 3 | 3 | 4 |
| Compliance and audit | 15 | 4 | 3 | 3 |
| Data access and reporting | 15 | 3 | 2 | 1 |
| Integration | 10 | 3 | 3 | 3 |
| Security and privacy | 10 | 4 | 3 | 3 |
| Total cost of ownership (5 years) | 10 | 2 | 3 | 4 |
| AI features and governance | 5 | 2 | 3 | 3 |
| Vendor viability and support | 5 | 3 | 3 | 2 |
| **Weighted score (out of 100)** | | **77.5** | **75.0** | **76.2** |
| Knock-out requirements | | All pass | All pass | **Fails K2** |
| Invented 5-year cost | | $1.42M | $1.18M | $0.96M |

*Weighted score = sum of (weight × score ÷ 4).*

**Vendor C** gave the best demo and had the lowest price, and it's out. In scenario 6 it couldn't export attempt-level history without a paid services request, and its contract charged a fee for data at exit. Every case study on this site depends on that data.

**Vendors A and B** are 2.5 points apart, which is inside the panel's scoring error. So the decision moves to the evidence behind the scores. A is stronger on compliance, audit and data access, the areas behind Tessaly's open problems (case studies A and D). B is better for learners and $240,000 cheaper over five years.

**Recommendation:** Vendor A, if negotiation brings the five-year cost within $100,000 of B's. Otherwise, take B with two contract conditions: a daily data feed to the warehouse, and exemption expiry delivered by a named date. The panel puts this to the sponsor as a choice with its tradeoffs, not as a winner.

## Why it's built this way

Knock-outs come before scoring, because no weighted total should be able to buy back a missing accessibility report or a locked-in data contract. Data access carries the same weight as the learner experience. A platform that hides its data makes every later measurement project expensive, and that cost doesn't show up in a demo. The scripted demo uses our own awkward cases (rehires, version changes, contractors), because vendors' own demos show the paths that work. When two vendors land within scoring error, the scorecard says so plainly and hands the sponsor a tradeoff instead of a false precision.

*Format: PDF, generated from this page.*

---
*Personal project. All data is synthetic or public, and the company is fictional. Views are my own and not affiliated with or endorsed by any current or former employer.*
