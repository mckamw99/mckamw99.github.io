# Learning data architecture with governance points (LIB-46)

**Purpose:** a one-picture view of how learning data moves from the HR system to an executive report, and where each control sits. It's meant for a data governance lead or learning technology owner explaining the path to leaders and auditors.

*Generic tool categories, no products. Shown for Tessaly Health, a fictional health system.*

---

![Diagram of seven stages left to right: HR system, nightly HR feed, enterprise LMS, warehouse staging, compliance fact table, BI scorecard, readers by role. Under each hop is a control. Existing controls in grey: extract versus load row counts (HR system to feed) and source versus staging row counts (LMS to staging). Added controls in bold blue: a freshness gate on the feed, the 15 data-quality checks with the identity map before the fact table, full reconciliation and two targeted checks before the scorecard, and a quarterly access review before readers.](outputs/lib46_architecture.png)

## Control points

| Hop | Control | Status | What it catches |
|---|---|---|---|
| HR system → feed | Extract vs. load row counts | Existing | Dropped rows in transfer |
| Feed → LMS | Rejected rows reviewed next day | Existing | Records the LMS refused |
| Feed → LMS | Freshness gate: no failed run in the last 3 days of the period | **Added** | Stale data (the Aug 2024 problem) |
| LMS → staging | Source vs. staging row counts | Existing | Incomplete copies |
| Staging → fact table | 15 data-quality checks; identity map; one row per requirement | **Added** | Duplicates, unlinked accounts, missing evidence |
| Fact table → scorecard | Full reconciliation to source; numerator vs. the month's completions; staff-only population | **Added** | Double loads, wrong population (Mar and Oct 2025) |
| Scorecard → readers | Quarterly access review against the role model; leaver revocation | **Added** | Access that outlived the job |

## Why it's built this way

The existing controls all checked that data *moved*: row counts in equal row counts out. None checked that the number was *right*, and the two steps that turn rows into a compliance rate had no control at all. Two of the three defects in case study D happened in those two steps. The third, stale data after a feed outage, passed the row-count checks because the rows that did arrive matched. So the added controls sit where meaning is created, not where bytes move. The diagram uses tool categories rather than products, because the control design doesn't depend on which LMS or BI tool is in place.

*Format: image (PNG and SVG in `outputs/`).*

---
*Personal project. All data is synthetic or public, and the company is fictional. Views are my own and not affiliated with or endorsed by any current or former employer.*
