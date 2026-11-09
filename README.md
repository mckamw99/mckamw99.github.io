# Matthew McKay, Ph.D. · Portfolio source

Source for my portfolio site: case studies and library items set at **Tessaly Health**, a fictional nonprofit health system, using synthetic data only.

| Folder | Contents |
|---|---|
| `generator/` | LIB-23: the seeded synthetic data generator every case study uses |
| `case-studies/a-what-complete-means/` | Case study A: defining and auditing training compliance metrics |
| `case-studies/d-governed-reporting/` | Case study D: lineage, reconciliation and access control for an executive report |
| `case-studies/b-training-and-outcomes/` | Case study B: linking training timing and attendance to retention, with caveats |
| `case-studies/c-agency-vs-staff/` | Case study C: agency vs. staff nurse cost model with sensitivity, plus a calculator |
| `library/` | Library pages: LIB-17, 44 (+48), 45, 14 (draft, attorney review), 41 (draft), 34 (template) |

```
pip install -r requirements.txt
cd generator && python generate.py && python validate.py
```

Code in this repo is AI-assisted (Claude). Each item's README says what I designed and how the output was validated.

See `CHANGELOG.md` and `SANITIZATION_LOG.md` for the build record. Code: MIT. Synthetic data: CC0 1.0.

---
*Personal project. All data is synthetic or public, and the company is fictional. Views are my own and not affiliated with or endorsed by any current or former employer.*
