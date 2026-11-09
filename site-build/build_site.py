"""Build the static portfolio site into <repo>/docs from the markdown sources.

AI-assisted (Claude). Usage: python3 build_site.py <repo_root>
Every content page is rendered from the same markdown the PDFs come from.
"""
import html, os, re, shutil, sys
import markdown

ROOT = os.path.abspath(sys.argv[1])
OUT = os.path.join(ROOT, "docs")
GH = "https://github.com/mckamw99/mckamw99.github.io"
SITE_NAME = "Matthew McKay, Ph.D."
EMAIL = "mckamw99@aequitasnetwork.com"
LINKEDIN = "https://www.linkedin.com/in/matthewmckayphd"
FORM = "#contact"  # TODO: Google Form link from Matt
DISCLAIMER = ("Personal project. All data is synthetic or public, and the company is fictional. "
              "Views are my own and not affiliated with or endorsed by any current or former employer.")

# ---- which markdown files become pages (source path -> output path, both repo-relative)
CASES = [
    ("a-what-complete-means", "A", "Learning analytics", ["metric_definitions", "dq_checklist", "disputed_kpi"]),
    ("d-governed-reporting", "D", "Data governance", ["access_model", "report_rationalization", "architecture", "dashboard_mockup"]),
    ("b-training-and-outcomes", "B", "Workforce analytics", ["metric_tree"]),
    ("c-agency-vs-staff", "C", "Workforce cost", ["calculator"]),
]
LIBRARY = ["lib-17-measurement-plan", "lib-44-first-90-days", "lib-45-vendor-scorecard", "lib-41-how-i-work"]

PAGES = {}  # src -> out
for slug, *_rest, docs in CASES:
    PAGES[f"case-studies/{slug}/README.md"] = f"case-studies/{slug}/index.html"
    for d in docs:
        PAGES[f"case-studies/{slug}/{d}.md"] = f"case-studies/{slug}/{d}.html"
for l in LIBRARY:
    PAGES[f"library/{l}.md"] = f"library/{l}.html"
PAGES["generator/README.md"] = "generator/index.html"
PAGES["generator/ASSUMPTIONS.md"] = "generator/assumptions.html"
PAGES["generator/DATA_DICTIONARY.md"] = "generator/data-dictionary.html"
COPIED = {"case-studies/c-agency-vs-staff/calculator.html": "case-studies/c-agency-vs-staff/calculator-app.html"}

# ---- tartan band: full sett from half-sett DB/24 G24 DB4 G24 K24 DB24 W6 R/12, 0.5 px per thread
C = dict(DB="#1c2850", G="#1e5834", K="#121212", W="#eeece6", R="#b01e23")
SETT = [("DB",24),("G",24),("DB",4),("G",24),("K",24),("DB",24),("W",6),("R",12),("W",6),("DB",24),("K",24),("G",24),("DB",4),("G",24)]
stops, x = [], 0.0
for c, n in SETT:
    stops.append(f"{C[c]} {x:g}px {x+n/2:g}px"); x += n / 2
BAND = "repeating-linear-gradient(90deg, " + ", ".join(stops) + ")"

CSS = """
:root{--navy-deep:#1c2850;--navy:#2b3d7a;--green:#1e5834;--red:#b01e23;--cream:#eeece6;--ink:#1d2230;--muted:#575c68;--tint:#e4e7f2;--border:#d9d8d2;
--serif:"Source Serif 4",Cambria,Georgia,serif;--sans:"Source Sans 3",Calibri,"Segoe UI",system-ui,sans-serif}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:#fff;color:var(--ink);font:16px/26px var(--sans)}
a{color:var(--navy);text-underline-offset:3px}a:hover{color:var(--navy-deep)}
a:focus-visible,button:focus-visible{outline:3px solid var(--red);outline-offset:2px}
.skip{position:absolute;left:-9999px}.skip:focus{left:16px;top:16px;background:#fff;padding:8px 12px;z-index:9}
.band{height:10px;background:BAND}
.wrap{max-width:1120px;margin:0 auto;padding:0 32px}
@media (max-width:600px){.wrap{padding:0 16px}}
.site-header{border-bottom:1px solid var(--border)}
.site-header .wrap{display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:8px 32px;padding-top:16px;padding-bottom:16px}
.name{font:600 24px/32px var(--serif);color:var(--navy-deep);text-decoration:none}
.site-header nav ul{list-style:none;margin:0;padding:0;display:flex;flex-wrap:wrap;gap:4px 24px}
.site-header nav a{display:inline-flex;align-items:center;min-height:44px;padding:0 4px;color:var(--ink);font-weight:600;text-decoration:none}
.site-header nav a[aria-current=page]{color:var(--navy-deep);text-decoration:underline;text-decoration-thickness:2px;text-underline-offset:6px}
.label{margin:0;font-size:12px;line-height:16px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:var(--green)}
.label.navy{color:var(--navy)}.label.muted{color:var(--muted)}
h1,h2,h3{color:var(--ink)}
h1{font:600 40px/48px var(--serif);margin:0 0 16px}
@media (max-width:600px){h1{font-size:32px;line-height:40px}}
.section-title{font:600 28px/36px var(--serif);margin:0}
.lead{font-size:18px;line-height:28px;max-width:720px;margin:0}
.muted{color:var(--muted)}
.btn{display:inline-flex;align-items:center;min-height:44px;padding:0 20px;border-radius:4px;font-weight:700;text-decoration:none}
.btn-cream{background:var(--cream);color:var(--navy-deep)}.btn-navy{background:var(--navy-deep);color:#fff}
.btn-navy:hover{color:#fff}
/* hero */
.hero{background:var(--navy-deep);color:#fff}
.hero .wrap{display:flex;flex-wrap:wrap;align-items:flex-end;justify-content:space-between;gap:48px;padding-top:64px;padding-bottom:64px}
.hero h1{color:#fff;font-size:44px;line-height:52px;margin:0}
@media (max-width:600px){.hero h1{font-size:34px;line-height:42px}}
.hero .rule{width:48px;height:4px;background:var(--red)}
.hero a:not(.btn){color:#fff}
.bars{display:flex;align-items:flex-end;gap:12px;padding:0 12px}.bars div{width:36px}
@media (max-width:600px){.hero-art{display:none}}
.pin{height:2px;background:var(--cream)}.pin.r{height:4px;background:var(--red)}
/* cards */
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,420px),1fr));gap:32px}
.grid.sm{grid-template-columns:repeat(auto-fit,minmax(min(100%,300px),1fr));gap:24px}
.card{background:var(--cream);border-radius:8px;padding:32px;display:flex;flex-direction:column;gap:14px}
.card.line{background:#fff;border:1px solid var(--border);padding:28px}
.card h2,.card h3{margin:0;font:600 24px/32px var(--serif)}
.card.line h2{font-size:22px;line-height:30px}
.card p{margin:0}
.tags{display:flex;flex-wrap:wrap;gap:8px;list-style:none;margin:0;padding:0}
.tags li{font-size:13px;line-height:20px;padding:2px 8px;border-radius:4px;background:#fff;border:1px solid var(--border)}
.card-foot{display:flex;flex-wrap:wrap;justify-content:space-between;align-items:center;gap:8px;margin-top:auto;padding-top:8px;border-top:1px solid var(--border)}
.card-foot a{font-weight:600;min-height:44px;display:inline-flex;align-items:center}
.pill{font-size:13px;line-height:20px;padding:2px 8px;border-radius:4px;background:var(--tint);color:var(--navy);font-weight:600}
.callout{background:var(--tint);border-radius:8px;padding:32px}
.liblist{list-style:none;margin:0;padding:0;border-top:1px solid var(--border)}
.liblist li{display:flex;flex-wrap:wrap;gap:8px 24px;align-items:baseline;padding:20px 0;border-bottom:1px solid var(--border)}
.liblist .t{flex:1 1 300px;font-weight:600;font-size:18px}.liblist .d{flex:2 1 380px}.liblist .f{flex:0 0 auto;font-size:14px;color:var(--muted)}
section.block{padding-top:64px;display:flex;flex-direction:column;gap:24px}
/* article pages */
.crumbs{margin:32px 0 16px;font-size:14px;line-height:22px}
.layout{display:flex;flex-wrap:wrap;gap:48px;align-items:flex-start}
.toc{flex:1 1 200px;max-width:260px;font-size:15px}
.toc ol,.toc ul{list-style:none;margin:8px 0 0;padding:0}
.toc a{display:inline-flex;min-height:36px;align-items:center;color:var(--ink);text-decoration:none}
.toc a:hover{text-decoration:underline}
.toc .pdf{margin-top:16px;font-weight:600;min-height:44px}
article{flex:999 1 560px;min-width:0;max-width:780px}
article h1{margin-top:0}
article h2{font-size:22px;line-height:30px;font-weight:600;margin:40px 0 12px;padding-top:24px;border-top:1px solid var(--border)}
article h3{font-size:18px;line-height:26px;font-weight:600;margin:28px 0 8px}
article p,article ul,article ol{margin:0 0 16px}
article li{margin-bottom:6px}
article blockquote{margin:0 0 16px;background:var(--tint);border-radius:8px;padding:12px 16px}
article blockquote p:last-child{margin:0}
article hr{display:none}
article img{max-width:100%;height:auto;border:1px solid var(--border);border-radius:8px;display:block;margin:8px 0 16px}
.tablewrap{overflow-x:auto;margin:0 0 20px}
article table{border-collapse:collapse;width:100%;font-size:15px;line-height:22px}
article th{text-align:left;padding:10px 12px;border-bottom:2px solid var(--ink);font-weight:600;vertical-align:bottom}
article td{padding:10px 12px;border-bottom:1px solid var(--border);vertical-align:top}
article code{font-size:14px;background:#f4f3ef;padding:1px 4px;border-radius:4px}
article pre{background:#f4f3ef;padding:12px 16px;border-radius:8px;overflow-x:auto}article pre code{padding:0;background:none}
.notice{background:var(--tint);border-radius:8px;padding:12px 16px;margin:0 0 24px;font-size:15px;line-height:22px}
/* footer */
.site-footer{margin-top:64px}
.site-footer .inner{background:var(--navy-deep);color:#fff}
.site-footer .wrap{display:flex;flex-wrap:wrap;gap:32px;justify-content:space-between;padding-top:48px;padding-bottom:48px}
.site-footer p{margin:0;font-size:14px;line-height:22px;max-width:540px}
.site-footer .fname{font:600 22px/30px var(--serif);margin-bottom:8px}
.site-footer ul{list-style:none;margin:0;padding:0}
.site-footer a{color:#fff;font-weight:600;min-height:44px;display:inline-flex;align-items:center}
.about{display:flex;flex-wrap:wrap;gap:48px;align-items:flex-start;padding-top:48px}
.about figure{margin:0;flex:0 0 240px}.about img{width:240px;height:300px;object-fit:cover;border-radius:8px;display:block}
.about figcaption{font-size:14px;line-height:22px;color:var(--muted);margin-top:8px}
.about .text{flex:999 1 520px;min-width:0;max-width:720px;display:flex;flex-direction:column;gap:20px}
.about .text p{margin:0}.about h2{font:600 28px/36px var(--serif);margin:8px 0 0}
@media print{.band,.site-header nav,.toc,.crumbs,.skip{display:none!important}
 .site-footer{margin-top:24px}.site-footer .inner{background:none;color:var(--ink)}.site-footer a{color:var(--ink)}
 .site-footer ul{display:none}.layout{display:block}article{max-width:none}
 body{font-size:11pt;line-height:1.45}article h2{break-after:avoid}img,table,tr{break-inside:avoid}
 a{color:var(--ink);text-decoration:none}}
""".replace("BAND", BAND)

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@400;600;700&amp;family=Source+Serif+4:opsz,wght@8..60,600&amp;display=swap">')

NAV = [("Start here", "index.html"), ("Case studies", "case-studies/index.html"),
       ("Library", "library/index.html"), ("About", "about.html")]


def rel(frm, to):
    """Relative URL from output page `frm` to output path `to` (both repo/docs-relative)."""
    r = os.path.relpath(to, os.path.dirname(frm) or ".")
    return r.replace(os.sep, "/")


def shell(out_path, title, body, section, description):
    navhtml = "".join(
        f'<li><a href="{rel(out_path, h)}"{" aria-current=\"page\"" if n == section else ""}>{n}</a></li>' for n, h in NAV)
    navhtml += f'<li><a href="#contact">Contact</a></li>'
    full_title = title if title == SITE_NAME else f"{title} · {SITE_NAME}"
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(full_title)}</title>
<meta name="description" content="{html.escape(description)}">
{FONTS}
<link rel="stylesheet" href="{rel(out_path, 'assets/site.css')}">
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<div class="band" aria-hidden="true"></div>
<header class="site-header"><div class="wrap">
<a class="name" href="{rel(out_path, 'index.html')}">{SITE_NAME}</a>
<nav aria-label="Main"><ul>{navhtml}</ul></nav>
</div></header>
<main id="main">
{body}
</main>
<footer class="site-footer" id="contact">
<div class="band" aria-hidden="true"></div>
<div class="inner"><div class="wrap">
<div><p class="fname">{SITE_NAME}</p><p>{DISCLAIMER}</p></div>
<ul>
<li><a href="mailto:{EMAIL}">{EMAIL}</a></li>
<li><a href="{LINKEDIN}">LinkedIn</a></li>
<li><a href="{FORM}">Contact form</a></li>
<li><a href="{GH}">Code and data on GitHub</a></li>
</ul>
</div></div>
</footer>
</body>
</html>
"""


# ---------- markdown pages
def resolve_link(src, target, out_path):
    if re.match(r"^(https?:|mailto:|#)", target):
        return target
    path, _, frag = target.partition("#")
    frag = ("#" + frag) if frag else ""
    abs_src = os.path.normpath(os.path.join(os.path.dirname(src), path))
    if abs_src in PAGES:
        return rel(out_path, PAGES[abs_src]) + frag
    if abs_src in COPIED:
        return rel(out_path, COPIED[abs_src]) + frag
    readme = os.path.join(abs_src, "README.md")
    if readme in PAGES:
        return rel(out_path, PAGES[readme]) + frag
    if re.search(r"\.(png|svg|jpg)$", abs_src):
        IMAGES.add(abs_src)
        return rel(out_path, abs_src)
    kind = "tree" if os.path.isdir(os.path.join(ROOT, abs_src)) else "blob"
    return f"{GH}/{kind}/main/{abs_src}{frag}"


IMAGES = set()
TITLES = {}


def render_md(src):
    out_path = PAGES[src]
    text = open(os.path.join(ROOT, src), encoding="utf-8").read()
    # drop the per-file disclaimer: the page footer carries it
    text = re.sub(r"\n-{3,}\s*\n\*Personal project\..*?\*\s*$", "\n", text.rstrip() + "\n", flags=re.S)
    text = re.sub(r"\n\*Personal project\..*?\*\s*$", "\n", text, flags=re.S)
    m = re.search(r"^# (.+)$", text, flags=re.M)
    title = re.sub(r"[*_`]", "", m.group(1)).strip() if m else src
    md = markdown.Markdown(extensions=["tables", "fenced_code", "toc", "sane_lists", "smarty"],
                           extension_configs={"toc": {"toc_depth": "2-2"}})
    body = md.convert(text)
    # links and images
    def fix_attr(mo):
        attr, val = mo.group(1), html.unescape(mo.group(2))
        return f'{attr}="{html.escape(resolve_link(src, val, out_path), quote=True)}"'
    body = re.sub(r'(href|src)="([^"]+)"', fix_attr, body)
    def nice(mo):
        href, inner = mo.group(1), mo.group(2)
        target = os.path.normpath(os.path.join(os.path.dirname(src), inner))
        if target in PAGES:
            return f'<a href="{href}">{TITLES[target]}</a>'
        return mo.group(0)
    body = re.sub(r'<a href="([^"]+)"><code>([^<]+\.md)</code></a>', nice, body)
    def codelink(mo):
        txt = mo.group(1)
        if "/" not in txt and "." not in txt:
            return mo.group(0)
        cand = os.path.normpath(os.path.join(os.path.dirname(src), txt.rstrip("/")))
        if cand.startswith("..") or not os.path.exists(os.path.join(ROOT, cand)):
            return mo.group(0)
        return f'<a href="{html.escape(resolve_link(src, txt.rstrip("/"), out_path))}"><code>{txt}</code></a>'
    def skip_or_link(mo):
        return mo.group(0) if mo.group(1) else codelink(re.match(r"<code>(.*)</code>", mo.group(0)))
    body = re.sub(r'(<a\b[^>]*>.*?</a>)|<code>[^<\s]+</code>', skip_or_link, body, flags=re.S)
    body = re.sub(r"<table>", '<div class="tablewrap"><table>', body).replace("</table>", "</table></div>")
    toc_items = getattr(md, "toc_tokens", [])
    flat = []
    for t in toc_items:
        if t["level"] == 2:
            flat.append(t)
        for c in t.get("children", []):
            if c["level"] == 2:
                flat.append(c)
    toc = "".join(f'<li><a href="#{t["id"]}">{t["name"]}</a></li>' for t in flat)
    pdf = rel(out_path, f"pdf/{pdf_name(out_path)}")
    crumbs = crumb(src, out_path)
    section = "Library" if src.startswith("library/") else ("Case studies" if src.startswith("case-studies/") else "")
    desc = first_para(text)
    page = f"""<div class="wrap">
<p class="crumbs">{crumbs}</p>
<div class="layout">
<nav class="toc" aria-label="On this page"><p class="label muted">On this page</p><ol>{toc}</ol>
<a class="pdf" href="{pdf}">Download PDF</a></nav>
<article>
{body}
</article>
</div></div>"""
    return out_path, title, page, section, desc


def first_para(text):
    for para in text.split("\n\n"):
        p = para.strip()
        if p and not p.startswith(("#", ">", "---", "|", "!")):
            return re.sub(r"[*_`\[\]]|\(.*?\)", "", p)[:180]
    return SITE_NAME


def pdf_name(out_path):
    return out_path.replace("/index.html", "").replace(".html", "").replace("/", "_") + ".pdf"


def crumb(src, out_path):
    parts = [f'<a href="{rel(out_path, "index.html")}">Start here</a>']
    if src.startswith("case-studies/"):
        parts.append(f'<a href="{rel(out_path, "case-studies/index.html")}">Case studies</a>')
        slug = src.split("/")[1]
        if not src.endswith("README.md"):
            letter = [c[1] for c in CASES if c[0] == slug][0]
            parts.append(f'<a href="{rel(out_path, PAGES[f"case-studies/{slug}/README.md"])}">Case study {letter}</a>')
    elif src.startswith("library/"):
        parts.append(f'<a href="{rel(out_path, "library/index.html")}">Library</a>')
    elif src.startswith("generator/") and not src.endswith("README.md"):
        parts.append(f'<a href="{rel(out_path, "generator/index.html")}">Synthetic data generator</a>')
    return " / ".join(parts)


# ---------- hand-built pages
CASE_CARDS = [
    ("a-what-complete-means", "A", "Learning analytics", "What does “complete” mean?",
     "The scorecard said 77.5% of compliance training was complete. Counted by person instead of enrollment row, 67.3% of staff were fully compliant.",
     ["Metric definitions", "Data-quality checks", "SQL reconciliation"]),
    ("d-governed-reporting", "D", "Data governance", "Governed reporting",
     "Reconciled 208 facility-months of an executive scorecard back to source, found three bad months, and designed the controls that would have caught each one.",
     ["Data lineage", "Reconciliation", "Role-based access"]),
    ("b-training-and-outcomes", "B", "Workforce analytics", "Does the training change outcomes?",
     "On-time onboarding went with fewer first-year exits (adjusted risk ratio 0.77). The residency's head start shrank under a fair comparison and stayed unproven.",
     ["Chi-square", "Mann-Whitney", "Effect sizes"]),
    ("c-agency-vs-staff", "C", "Workforce cost", "Agency nurses vs. staff nurses",
     "A three-year simulation for each position found 8 worth piloting as staff conversions: about $96k in identified savings opportunities, with ranges.",
     ["Cost model", "Simulation", "Sensitivity"]),
]
LIB_CARDS = [
    ("Measurement", "LIB-17", "Learning measurement plan", "lib-17-measurement-plan",
     "For learning and HR leaders who want to know, before launch, what a program has to show and what they'll do with the answer.", "Web page + PDF", None),
    ("Leadership", "LIB-44", "First 90 days: Director of Learning Operations", "lib-44-first-90-days",
     "How I'd diagnose, set priorities, build trust and deliver early results in a new role, with a one-page roadmap.", "Web page + PDF", None),
    ("Technology", "LIB-45", "LMS/LXP vendor selection scorecard", "lib-45-vendor-scorecard",
     "Criteria and weights, knock-out requirements, a scripted demo and reference questions, so the decision rests on needs, not the best demo.", "Web page + PDF", None),
    ("Working style", "LIB-41", "How I work", "lib-41-how-i-work",
     "One page on how I scope, govern, build and hand off work.", "Web page", None),
    ("Governance", "LIB-14", "AI acceptable-use policy for a learning team", None,
     "What's allowed, what a person has to check, and what has to be disclosed.", "Web page + PDF", "Coming soon"),
]


def case_cards(out_path):
    s = ""
    for slug, k, lane, t, d, tags in CASE_CARDS:
        href = rel(out_path, f"case-studies/{slug}/index.html")
        tg = "".join(f"<li>{x}</li>" for x in tags)
        s += f"""<article class="card">
<p class="label">Case study {k} · {lane}</p>
<h3><a href="{href}" style="color:inherit;text-decoration:none">{t}</a></h3>
<p>{d}</p>
<ul class="tags" aria-label="Methods">{tg}</ul>
<div class="card-foot"><span class="muted" style="font-size:14px">Synthetic data · fictional company</span><a href="{href}">Read case study {k}</a></div>
</article>"""
    return f'<div class="grid">{s}</div>'


def home():
    out = "index.html"
    bars = "".join(f'<div style="height:{h}px;background:{c}"></div>' for h, c in
                   [(48, "#2b3d7a"), (72, "#1e5834"), (96, "#2b3d7a"), (124, "#1e5834"), (160, "#b01e23")])
    lib = ""
    for cat, i, t, f, d, fmt, st in LIB_CARDS:
        name = f'<a class="t" href="library/{f}.html">{t}</a>' if f else f'<span class="t">{t}</span>'
        lib += f'<li>{name}<span class="d">{d}</span><span class="f">{fmt}{" · " + st if st else ""}</span></li>'
    body = f"""<section class="hero"><div class="wrap">
<div style="flex:1 1 520px;max-width:680px;display:flex;flex-direction:column;gap:20px">
<p class="label" style="color:#fff">Learning technology · Learning operations · Workforce analytics · Data governance</p>
<div class="rule" aria-hidden="true"></div>
<h1>Turning learning and workforce data into decisions leaders trust.</h1>
<p class="lead">Four case studies and a set of working templates, all built at one fictional health system with synthetic data. Each one shows the method, the checks I ran, and what I’d do with the answer.</p>
<div style="display:flex;flex-wrap:wrap;gap:16px;padding-top:8px">
<a class="btn btn-cream" href="#case-studies">See the case studies</a>
<a href="#read-this" style="font-weight:600;min-height:44px;display:inline-flex;align-items:center">How to read this site</a>
</div></div>
<div class="hero-art" aria-hidden="true"><div class="bars">{bars}</div><div class="pin"></div><div class="pin r"></div><div class="pin"></div></div>
</div></section>
<div class="wrap">
<section class="block" id="case-studies">
<div style="display:flex;flex-direction:column;gap:8px"><p class="label navy">Case studies</p>
<h2 class="section-title">Four questions a health system’s leaders actually asked</h2>
<p class="muted" style="margin:0;max-width:720px">Each follows the same order: the question, the data, the approach, how I checked it, what it found, and what I’d do in practice.</p></div>
{case_cards(out)}
</section>
<section class="block">
<div style="display:flex;flex-direction:column;gap:8px"><p class="label navy">Library</p>
<h2 class="section-title">Working templates</h2>
<p class="muted" style="margin:0;max-width:720px">Shorter pieces a team could pick up and use, each with a worked example and a note on why it’s built the way it is.</p></div>
<ul class="liblist">{lib}</ul>
</section>
<section class="block" id="read-this">
<div class="callout" style="display:flex;flex-direction:column;gap:24px">
<h2 class="section-title">How to read this site</h2>
<div class="grid sm" style="gap:32px">
<div><h3 style="margin:0 0 8px;font-size:20px;line-height:28px">One fictional company</h3><p style="margin:0">Every piece is set at Tessaly Health, an invented nonprofit regional health system with about 4,000 staff. It isn’t modeled on any real employer.</p></div>
<div><h3 style="margin:0 0 8px;font-size:20px;line-height:28px">Synthetic data, real methods</h3><p style="margin:0">The data comes from a <a href="generator/index.html">seeded generator</a> anyone can rerun. Results show how a method works. They aren’t findings about real people.</p></div>
<div><h3 style="margin:0 0 8px;font-size:20px;line-height:28px">AI-assisted code, checked by hand</h3><p style="margin:0">I write the analysis with Claude and label the code that way. What I’m showing is the checking: reconciliations, read-backs and assumption tests.</p></div>
</div></div>
</section>
</div>"""
    return out, SITE_NAME, body, "Start here", "Case studies and working templates on learning and workforce data, built at a fictional health system with synthetic data."


def cases_index():
    out = "case-studies/index.html"
    body = f"""<div class="wrap"><section class="block" style="padding-top:48px">
<div style="display:flex;flex-direction:column;gap:12px"><p class="label navy">Case studies</p>
<h1 style="margin:0">Case studies</h1>
<p class="lead">Four studies at Tessaly Health, a fictional health system. All numbers come from <a href="../generator/index.html">synthetic data</a> and show a method, not a real result.</p></div>
{case_cards(out)}
</section></div>"""
    return out, "Case studies", body, "Case studies", "Four case studies on learning and workforce data at a fictional health system."


def library_index():
    out = "library/index.html"
    cards = ""
    for cat, i, t, f, d, fmt, st in LIB_CARDS:
        action = (f'<span class="pill">{st}</span>' if st else f'<a href="{f}.html">Open</a>')
        title = f'<a href="{f}.html" style="color:inherit;text-decoration:none">{t}</a>' if f else t
        cards += f"""<article class="card line">
<div style="display:flex;justify-content:space-between;gap:8px;flex-wrap:wrap"><p class="label">{cat}</p><span class="muted" style="font-size:13px;line-height:16px">{i}</span></div>
<h2>{title}</h2><p>{d}</p>
<div class="card-foot" style="border-top:0"><span class="muted" style="font-size:14px">{fmt}</span>{action}</div>
</article>"""
    body = f"""<div class="wrap"><section class="block" style="padding-top:48px">
<div style="display:flex;flex-direction:column;gap:12px"><p class="label navy">Library</p>
<h1 style="margin:0">Working templates</h1>
<p class="lead">Each item has a one-line purpose, the artifact itself, a worked example at Tessaly Health where it’s a template, and a short note on why it’s built the way it is.</p></div>
<div class="grid sm">{cards}</div>
<p class="muted" style="margin:0;font-size:14px;max-width:720px">Examples built on synthetic data demonstrate a method. They are not findings. Several case-study pages also hold templates: metric definitions, an access model and a report rationalization method.</p>
</section></div>"""
    return out, "Library", body, "Library", "Working templates for learning operations and learning data teams."


def about():
    out = "about.html"
    body = f"""<div class="wrap"><div class="about">
<figure><img src="assets/headshot.jpg" alt="Matthew McKay, smiling, in a dark top against a blue-grey background" width="240" height="300">
<figcaption>Photo retouched with AI.</figcaption></figure>
<div class="text">
<p class="label navy">About</p>
<h1 style="margin:0">Matthew McKay, Ph.D.</h1>
<p style="font-size:20px;line-height:30px">I’m a learning and data leader. I make learning systems and workforce data trustworthy, then turn them into decisions leaders act on.</p>
<p>My work sits where learning platforms and data meet. On the platform side, I’ve owned enterprise learning platforms and the operations that run on them: administration, HR system integrations, request intake and service governance. On the data side, I build the measurement and governance that make the numbers hold up: written metric definitions, data-quality checks, reconciliation to source, and role-based access.</p>
<p>I’ve done this work at a national services company, in the technology division of a large bank, as a director in higher education, and through my own consulting practice. I also teach data and information technology courses at a community college. I use AI to speed up analysis, and I show the checks that make the results safe to use.</p>
<p>I’m looking for a senior manager or director role leading learning technology or learning operations, in an organization that treats learning and workforce data as business infrastructure. I’m also open to workforce analytics and data governance leadership. I’m based in Western New York and open to remote roles.</p>
<p><a href="library/lib-41-how-i-work.html">How I work</a> has more on how I scope, build and hand off a project.</p>
<h2>Education</h2>
<p>Ph.D., Urban Education, Indiana University, 2024</p>
<h2>Get in touch</h2>
<div style="display:flex;flex-wrap:wrap;gap:16px;align-items:center">
<a class="btn btn-navy" href="mailto:{EMAIL}">Email me</a>
<a href="{LINKEDIN}" style="font-weight:600;min-height:44px;display:inline-flex;align-items:center">LinkedIn</a>
<a href="{FORM}" style="font-weight:600;min-height:44px;display:inline-flex;align-items:center">Contact form</a>
</div>
<p class="muted" style="font-size:14px;line-height:22px">Career history and credentials are on my resume and LinkedIn.</p>
</div></div></div>"""
    return out, "About", body, "About", "About Matthew McKay, Ph.D., a learning and data leader."


def write(out_path, title, body, section, desc):
    p = os.path.join(OUT, out_path)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w", encoding="utf-8").write(shell(out_path, title, body, section, desc))


def main():
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(os.path.join(OUT, "assets"))
    open(os.path.join(OUT, "assets/site.css"), "w").write(CSS)
    open(os.path.join(OUT, ".nojekyll"), "w").write("")
    shutil.copy(os.path.join(os.path.dirname(__file__), "headshot.jpg"), os.path.join(OUT, "assets/headshot.jpg"))
    for fn in (home, cases_index, library_index, about):
        write(*fn())
    for src in PAGES:
        t = open(os.path.join(ROOT, src), encoding="utf-8").read()
        m = re.search(r"^# (.+)$", t, flags=re.M)
        TITLES[src] = re.sub(r"[*_`]", "", m.group(1)).strip()
    for src in PAGES:
        write(*render_md(src))
    for src, dst in COPIED.items():
        os.makedirs(os.path.dirname(os.path.join(OUT, dst)), exist_ok=True)
        t = open(os.path.join(ROOT, src), encoding="utf-8").read().replace('href="README.md"', 'href="index.html"')
        open(os.path.join(OUT, dst), "w", encoding="utf-8").write(t)
    for img in IMAGES:
        d = os.path.join(OUT, img)
        os.makedirs(os.path.dirname(d), exist_ok=True)
        shutil.copy(os.path.join(ROOT, img), d)
    print(f"{len(PAGES) + 4} pages, {len(IMAGES)} images, {len(COPIED)} copied")


if __name__ == "__main__":
    main()
