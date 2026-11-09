> **DRAFT for Matt to rewrite in his own words.** Every principle below is drawn from how the work on this site was done, with a link to where it shows. Section 6 (how learning works, LIB-37) needs Matt's own beliefs and is left as questions. Marked items: [CONFIRM] = check it's true for you; [YOUR WORDS] = replace with your own.

# How I work (LIB-41)

**Purpose:** one page for a hiring manager or new team on how I scope, govern, build and hand off work, so they know what working with me looks like before the first meeting.

---

## 1. I start with the decision, not the data

Before I build anything, I ask who will act on the answer and what they'll do differently. Then I write down the question and the definitions, and only then the query. Most "the numbers are wrong" problems are two teams answering different questions with the same word.

*Where it shows:* case study A writes the compliance definition before computing it ([metric definitions](../case-studies/a-what-complete-means/metric_definitions.md)).

## 2. I define, then govern

Every metric that leaves my team has a written definition, an owner, a version number and an as-of date. Definitions change through a stated process, and when they change I show the old number next to the new one for a cycle, with the reason. Data-quality problems get flagged and routed to whoever can fix the source; I don't quietly drop rows to make a number look clean.

*Where it shows:* the data-quality checklist ([LIB-04](../case-studies/a-what-complete-means/dq_checklist.md)) and the disputed-KPI process ([LIB-50](../case-studies/a-what-complete-means/disputed_kpi.md)).

## 3. I check results, not effort

A report isn't done when the query runs. It's done when I've reproduced the number another way and know why it differs from the last one: reconciling to source, rebuilding it independently, reading records back, tracing a few people end to end. When I test whether something works, I say up front how big an effect the data could detect, so "no difference" doesn't get mistaken for "no effect."

*Where it shows:* the validation section of every case study; the control backtest in [case study D](../case-studies/d-governed-reporting/README.md).

## 4. I build with AI and say so

I write SQL and Python with an AI assistant, and the code on this site is labeled that way. My part is the design, the definitions and the checks. I treat AI output the way I'd treat a new analyst's first draft: useful, fast, and not trusted until it reproduces a known answer.

[CONFIRM] Link to the "How I build with AI" page once it clears review (LIB-28).

## 5. I hand off so it runs without me

Work isn't finished until someone else can run it: a README, a reproducible script, a named owner, a schedule, and a list of what to check when it breaks. I'd rather retire a report than maintain one nobody reads.

*Where it shows:* each case study's Files section; the report rationalization worksheet ([LIB-51](../case-studies/d-governed-reporting/report_rationalization.md)).

## How I communicate

- **Plainly, with the tradeoff.** I'd rather give a direct answer with its limits than a hedged one.
- **Bad news early and in person.** If a number is about to drop because the definition changed, the owner hears it from me first.
- **Fewer priorities, finished.** Three things done beat ten started.

[CONFIRM] These match how you'd describe yourself; add anything colleagues regularly say about working with you. [YOUR WORDS]

## 6. How I think learning works (LIB-37)

[YOUR WORDS] Two or three short paragraphs. Questions to answer:

1. What do you believe makes workplace training actually change what people do?
2. What's one common L&D practice you think wastes people's time, and what do you do instead?
3. How does your teaching (adult learners, a community college classroom) shape how you design workplace learning? Keep it general: no course names, materials or students.

## Why it's built this way

[YOUR WORDS] Optional: 3–5 sentences on why you'd put this page in front of a hiring manager.

*Format: web page.*

---
*Personal project. All data is synthetic or public, and the company is fictional. Views are my own and not affiliated with or endorsed by any current or former employer.*
