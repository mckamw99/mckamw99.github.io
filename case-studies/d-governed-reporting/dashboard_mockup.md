# Governed weekly compliance view (LIB-03)

**Purpose:** a mockup of the weekly view a learning operations leader would use during an annual compliance campaign. It shows the numbers they act on, with the definition and data status stated on the page.

*Mockup on synthetic data for Tessaly Health, a fictional health system. A layout I designed for this portfolio.*

---

![Dashboard mockup titled "Annual compliance training: weekly view," as of 30 Apr 2025, definition v1.0. Six tiles: people fully compliant 67.3%, requirements met 81.6%, overdue requirements 3,376, requirements exempted 511, people in scope 3,666, unresolved accounts 33. A line chart shows people fully compliant rising from 8.7% on 7 Feb to 67.3% on 30 Apr. A bar chart shows the rate by facility, from 64.8% at Flagship Hospital to 70.8% at Community South. A list shows the five units with the most overdue requirements, led by Intensive Care at Flagship Hospital with 123.](outputs/lib03_dashboard_mockup.png)

## What's on it and why

| Element | Why it's there |
|---|---|
| Definition version, as-of date, feed status, check status (header) | A number without its definition and date can't be compared or trusted. These four facts answer "can I use this?" before anyone reads a figure. |
| People fully compliant (headline) | The question leaders actually ask. Defined in case study A as M1. |
| Requirements met | Shows how close the gap is to closing. 81.6% of requirements but 67.3% of people means many people are one module short. |
| Overdue requirements | The workload. Drives manager follow-up. |
| Exemptions | Shown beside the rate so the rate can't be raised quietly by exempting people. |
| Unresolved accounts | Open data problems that could move the number. |
| Campaign progress by week | Tells the leader whether to send reminders now or wait. |
| By facility | Where to focus. One color: the bars compare facilities, they don't need separate identities. |
| Most overdue by unit | The follow-up list. Unit managers see names for their own unit only. |

All numbers on the mockup are computed from the synthetic data by `analysis/visuals.py`. They match case study A's governed results exactly; `validate_d.py` checks that.

## Why it's built this way

I limited it to six numbers, because a weekly view that needs explaining every week won't get read. The header carries the governance (definition, date, freshness, checks), so the trust question is answered in one line instead of a footnote. Rates are paired with the counts behind them, since a rate alone hides how much work is left. The page is static here. In a live BI tool, each tile would link to its definition and every chart would have a table view.

*Format: image (PNG and SVG in `outputs/`).*

---
*Personal project. All data is synthetic or public, and the company is fictional. Views are my own and not affiliated with or endorsed by any current or former employer.*
