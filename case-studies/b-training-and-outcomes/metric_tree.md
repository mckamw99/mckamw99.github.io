# Workforce analytics metric tree: training to retention (LIB-05)

**Purpose:** a one-page map, for learning and HR leaders, of how training is supposed to reach business outcomes, and how strong the evidence is for each link. Use it before anyone claims a training ROI.

*Worked example at Tessaly Health, a fictional health system, using synthetic data from case study B.*

---

![Metric tree with four columns: training, leading indicator, workforce outcome, business outcomes. Link 1, role onboarding finished within 30 days to 12-month voluntary retention, is thick blue: tested and holds, adjusted risk ratio 0.77 (95% CI 0.64 to 0.94). Links 2 and 3, from residency attendance to time to proficiency and to retention, are thin blue: tested but not established. Link 4, retention to turnover cost, is dark grey: true by arithmetic. Links 5 and 6, from retention and from time to proficiency to agency hours and cost, are light grey: plausible, modeled in case study C. Annual compliance on time has no link, with a note that it has no plausible path to retention.](outputs/lib05_metric_tree.png)

## How to read and use it

| Link strength | Meaning | What you can say |
|---|---|---|
| Tested and holds | Association found, survives adjustment and sensitivity checks | "Linked to"; size it with the interval, and don't call it cause |
| Tested, not established | Right direction, interval includes no effect | "We can't tell yet"; say why (usually sample size) |
| Arithmetic | True by definition once the inputs are known | State the formula and the assumed inputs |
| Plausible, not yet tested | A mechanism exists, no evidence here | Name it as a hypothesis, and plan the test |
| No link | No credible mechanism | Don't draw it, even if a correlation turns up |

To build one for another program: list the training exposures on the left and the business outcomes on the right. Draw only the links with a mechanism you can say in one sentence. Then label each by the evidence you actually have, not the evidence you expect.

## Why it's built this way

Training ROI claims usually fail at a missing middle link: a course is credited with a cost saving that depends on two untested steps. Drawing the whole chain makes those steps visible, and labeling each link's evidence keeps a strong result on one link from lending credibility to the rest. I left compliance training unconnected on purpose. Compliance modules exist to meet obligations, not to retain people, and drawing a line there would invite someone to find a spurious correlation and report it. The tree also tells case study C which links it has to model rather than assume.

*Format: image (PNG and SVG in `outputs/`), with this page.*

---
*Personal project. All data is synthetic or public, and the company is fictional. Views are my own and not affiliated with or endorsed by any current or former employer.*
