# Changelog

## 0.8.0 (2026-11-09)
- Site build: static HTML/CSS in `docs/`, generated from the markdown sources by `site-build/build_site.py`; PDFs printed from the same pages by `site-build/make_pdfs.py`. Pages: Start here, Case studies index, four case studies and their templates, Library index and four library items, synthetic data generator pages, About.
- Pre-publish checks run: every page carries the footer disclaimer, every image has alt text, no broken internal links, no employer or pen-name terms. LIB-41 rewritten with Matt's wording; its AI principle is held back until the attorney clears LIB-28.
- Held back from the repo: LIB-14 (attorney review) and the internal sign-off summaries.

## 0.7.1 (2026-11-09)
- LIB-34 dissertation summary dropped at Matt's direction; page removed. The Ph.D. appears only on the About page: Ph.D., Urban Education, Indiana University, December 2024 (date confirmed by Matt 2026-11-09). No dissertation title, topic or link on the site.

## 0.7.0 · 2026-11-08
- Library pages: LIB-17 measurement plan; LIB-44 first-90-days plan with LIB-48 roadmap appendix; LIB-45 vendor scorecard; LIB-14 AI acceptable-use policy (draft, held for attorney review); LIB-41 how I work (draft for Matt's rewrite, LIB-37 section open); LIB-34 dissertation summary (template awaiting Matt's input). Impact summaries for each.

## 0.6.0 · 2026-11-08
- Case study C, "Agency nurses vs. staff nurses": cost per worked hour from public benchmarks (with agency ramp-up), base-load slicing of daily agency hours, 3-year day-by-day simulation per position, convert/pilot/keep classification, tornado sensitivity, break-even rate, onboarding scenario; LIB-26 calculator page; validation (hand calculation, benchmark read-back, coverage, seed stability, calculator vs. model).

## 0.5.0 · 2026-11-08
- Case study B, "Does the training change outcomes?": onboarding timing vs. first-year retention (chi-square, risk ratios, Mantel-Haenszel, adjusted model with bootstrap, sensitivity, negative control, power), residency naive vs. landmark analysis (Fisher's exact, power), Mann-Whitney on time to proficiency, metric tree (LIB-05), validation against the answer key with a permutation test.

## 0.4.0 · 2026-11-08
- Case study D, "Governed reporting": reconciliation of 208 published facility-months, hypothesis-tested diagnosis, five-control backtest, access review (LIB-07), report rationalization (LIB-51), architecture diagram (LIB-46), governed weekly view mockup (LIB-03), validation against the answer key and case study A.

## 0.3.0 · 2026-11-08
- Repo restructured: generator/ (LIB-23) and case-studies/.
- Case study A, "What does 'complete' mean?": data-quality checks (LIB-04, LIB-27), metric definition sheet (LIB-01), compliance bridge and charts (LIB-24), disputed-KPI process (LIB-50), validation (read-back, SQL rebuild, answer key, trace).
- Generator: added ground_truth/manual_account_owners.csv (answer key only; data unchanged).

## 0.2.0 · 2026-11-08
- Recalibrated turnover, first-year turnover, RN vacancy and time to fill against NSI 2025 and 2026 reports.
- Costs replaced with public benchmarks: BLS ECEC wage and benefits load, SIA/NATHO agency bill rates, NSI cost per RN turnover.
- Added chronic RN vacancies (positions open all window) to match national vacancy; removed the structural demand shortfall.
- Fixed nondeterminism in transfer selection (output now identical across runs).
- validate.py: added all-RN turnover, first-year RN exits, RN position vacancy.
- Licenses: MIT (code), CC0 1.0 (data).

## 0.1.0 · 2026-11-08
- LIB-23 first build: seeded generator (seed 20261108), 25 tables covering 2023–2025.
- Supports case studies A, D, B and C; feeds LIB-03, LIB-24 and LIB-27.
- validate.py: integrity, calibration and recovery checks; all integrity checks pass.
- Assumptions are draft defaults pending Matt's review (marked "confirm" in ASSUMPTIONS.md).
