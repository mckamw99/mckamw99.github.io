# Agency-to-staff conversion calculator (LIB-26)

**Purpose:** a small web page for a nursing or finance leader to test, in a few minutes, whether converting one agency position to a staff position pays, using their own rates.

*Defaults use 2025 national benchmarks and the assumptions from case study C at Tessaly Health, a fictional health system.*

---

**The artifact:** [`calculator.html`](calculator.html), a single page that runs in any browser with no external code.

## Worked example (defaults)

| Output | Value |
|---|---:|
| Staff cost per worked hour | $83.05 |
| Agency cost per productive hour (bill rate, fee, ramp) | $98.63 |
| Savings per year once proficient | $26,480 |
| Cost of each hire (hire, orientation, ramp) | $34,969 |
| Expected hires over 3 years | 1.62 |
| **Expected net savings over 3 years** | **about $14,900** |
| Break-even agency bill rate | about $87.20 an hour |

Change the bill rate to the 2023 national level ($106.63) and the 3-year saving rises to about $84,000. Change days to proficiency to a new graduate's 168, and it turns into a loss.

## How it works

The page runs the same simulation as case study C: 2,000 runs of one position, day by day, with recruiting lag, orientation, a ramp to proficiency, exits and refills, and agency covering every gap. It uses a fixed random seed, so the same inputs always give the same answer. Unlike the case study, it assumes steady demand, so set "share of hours needed" below 100% for anything but a unit's steadiest base. `validate_c.py` checks that the page and the Python model agree for the same inputs.

## Why it's built this way

The usual version of this calculator compares two hourly rates and stops, which is how conversion programs get approved and then disappoint. This one makes the costs that come with each hire visible: hiring, the weeks before a new nurse is fully productive, and the chance they leave and the cycle repeats. It also counts the agency nurse's own ramp-up, so the comparison is fair in both directions. I show the break-even bill rate because that's the number a leader can act on in a negotiation. Every default is labeled as a benchmark or an assumption, so a user knows which ones to replace with their own.

*Format: web page.*

---
*Personal project. All data is synthetic or public, and the company is fictional. Views are my own and not affiliated with or endorsed by any current or former employer.*
