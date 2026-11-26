"""Pages generated from the same data as the home page, so they can never disagree with it:
  /data                 the downloads, the data dictionary and the notebook, with the dataset's structured description
  /changes, changes.xml every change to the claims, newest first, and the same as an Atom feed
  /claims/, /claims/cNN one page per claim, copied from its card on the Research page
  /safety-check/<group> the products in each group, each placed on the evidence ladder
  /questions/<slug>     plain answers to common questions (questions19.py) and to the questions people search (answers19.py)
Usage: python3 -I gen19.py <full index.html (before the tabs are split)> <out_dir>"""
import csv, datetime, html, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import shell19, tab_pages
from shell19 import SITE, page

src, out = sys.argv[1:3]
T = open(src, encoding="utf-8").read()
shell19.load(T)
D = json.loads(re.search(r'id="n19-data">(.*?)</script>', T, re.S).group(1))
HERE = os.path.dirname(os.path.abspath(__file__))
MON = "January February March April May June July August September October November December".split()
def long_date(iso): y, m, d = (int(x) for x in iso[:10].split("-")); return f"{d} {MON[m - 1]} {y}"
BUILT = D["built"]
def ym(v): return (MON[v["month"] - 1] + " " + str(v["year"])) if isinstance(v, dict) else (MON[int(v[5:7]) - 1] + " " + v[:4])
def esc(x): return html.escape(str(x), quote=True)
def text(h): return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", h))).strip()

# ---- where every id lives, so links copied from the home page still land in the right place --------------------------
SPANS = tab_pages.panel_spans(T)
WHERE = {}
for k, (a, b, c, d) in SPANS.items():
    for i in re.findall(r'\bid="([^"]+)"', T[b:c]): WHERE[i] = k
SLUG = {v: k for k, v in tab_pages.PANEL.items()}
CLAIMS = {}  # id -> dict
for m in re.finditer(r'<article class="claim" id="(c\d+)" data-status="(\w+)">(.*?)</article>', T, re.S):
    cid, status, body = m.groups()
    head = re.search(r'<span class="cid">(C\d+)</span><span class="subt">(.*?)</span><span class="(cstat[^"]*)">(.*?)</span></div><h4>(.*?)</h4>', body, re.S)
    if not head: sys.exit("could not read claim card " + cid)
    merged = re.search(r'<p class="merged">(.*?)</p>', body, re.S)
    cb = body[body.index('<div class="cbody">') + len('<div class="cbody">'):body.rindex("</div></details>")]
    cb = re.sub(r'<button\b.*?</button>', "", cb, flags=re.S)
    cb = re.sub(r'<section class="wts" id="wts-c\d+" hidden></section>', "", cb)
    CLAIMS[cid] = dict(id=cid, label=head.group(1), topic=text(head.group(2)), cls=head.group(3), grade=text(head.group(4)),
                       title=text(head.group(5)), merged=merged and text(merged.group(1)), status=status, body=cb, n=int(cid[1:]))
if len(CLAIMS) < 40: sys.exit(f"only {len(CLAIMS)} claim cards found")
MERGED = {"c2": "c16", "c37": "c6"}  # claim numbers aren't reused; old addresses point to the claim that absorbed them

def relink(h):
    """Links copied from the home page: claims go to their own page, other sections to the tab page that holds them."""
    def fix(m):
        x = m.group(1)
        if x in CLAIMS: return f'href="/claims/{x}"'
        if x in MERGED: return f'href="/claims/{MERGED[x]}"'
        if x in SLUG: return f'href="/{SLUG[x]}"'
        t = WHERE.get(x)
        if t: return f'href="/{SLUG[t]}#{x}"'
        return f'href="/#{x}"'
    h = re.sub(r'href="#([^"]+)"', fix, h)
    return re.sub(r'\sdata-tab="[^"]*"', "", h)

def h5_to_h2(h):
    """claim cards use h5 under the card title; on a claim page they sit under the page title, so h2 keeps the heading order"""
    return re.sub(r"<h5(\s|>)", r'<h2 class="h5"\1', h).replace("</h5>", "</h2>")
def badge(c): return f'<span class="{c["cls"]}">{esc(c["grade"])}</span>'
def write(path, doc):
    f = os.path.join(out, path + ("" if path.endswith((".html", ".xml")) else ".html"))
    os.makedirs(os.path.dirname(f), exist_ok=True)
    open(f, "w", encoding="utf-8").write(doc)
    return path
WRITTEN = []
ORG = {"@type": "Organization", "@id": SITE + "#org", "name": "19 Degrees", "url": SITE}

# ---- /data -------------------------------------------------------------------------------------------------------------
dd = os.path.join(out, "data")
files = sorted(f for f in os.listdir(dd) if not f.startswith(".") and f != "index.html")
DICT = list(csv.DictReader(open(os.path.join(dd, "data-dictionary.csv"), encoding="utf-8"))) if "data-dictionary.csv" in files else []
FILE_NOTE = {
 "bite-temperatures.csv": "Every bull, tiger and white shark bite in Australia since 1900 with a known month and place, and the sea temperature that month.",
 "bite-temperature-summary.csv": "Bites below 19°C, and the coolest, median and warmest sea temperature, for each species: all bites and species-confirmed bites.",
 "beach-seasons-by-decade.csv": "How many months a year the sea off each reference beach averaged 19°C or more, decade by decade since 1900.",
 "beach-outlook-2050.csv": "Each beach's warming trend since 1980, and the warm months a year it would have by about 2050 at that pace (an extrapolation, not a climate model).",
 "bull-bites-open-coast.csv": "Bull shark bites in coastal waters versus harbors, rivers and estuaries, by era.",
 "bull-bites-by-decade.csv": "Bull shark bites by decade for southern NSW and Western Australia, with Australia's population.",
 "bull-bites-enso.csv": "Bull shark bites in El Niño, La Niña and neutral months since 1950.",
 "zones-by-era.csv": "Where each species' bites fall along the east coast, by era, beside the half-year 19°C line.",
 "data-dictionary.csv": "What every column in every file means.",
 "19-degrees-data.json": "Everything the site's charts are drawn from, in one file.",
 "19-degrees-starter.ipynb": "A Python notebook that loads the files and redraws the headline results. Opens in Jupyter, VS Code or Google Colab.",
}
def size(f):
    n = os.path.getsize(os.path.join(dd, f))
    return f"{n:,} bytes" if n < 1024 else f"{n / 1024:.0f} KB" if n < 1024 * 1024 else f"{n / 1024 / 1024:.1f} MB"
def fmt_of(f): return {"csv": "CSV", "json": "JSON", "ipynb": "Notebook"}.get(f.rsplit(".", 1)[-1], f.rsplit(".", 1)[-1].upper())
undescribed = [f for f in files if f not in FILE_NOTE]
if undescribed: sys.exit("gen19.py: add a line to FILE_NOTE for " + ", ".join(undescribed))
doi = None
try:
    cff = open(os.path.join(HERE, "..", "CITATION.cff"), encoding="utf-8").read()
    m = re.search(r'^doi:\s*"?(10\.\d+/[^\s"]+)', cff, re.M); doi = m and m.group(1)
except OSError:
    pass
asid_to = ym(D["asid_last"]); sst_to = ym(D["sst_last"])
cov_end = (f'{D["asid_last"]["year"]}-{D["asid_last"]["month"]:02d}' if isinstance(D["asid_last"], dict) else D["asid_last"][:7])
dataset = {"@context": "https://schema.org", "@type": "Dataset", "@id": SITE + "open-data#dataset",
  "name": "19 Degrees: sea temperature and shark bites in Australia, 1900 to today",
  "description": ("Every Australian bull, tiger and white shark bite since 1900 with a known month and place, matched to that month's "
                  "HadISST sea surface temperature, with derived tables on the 19°C season at reference beaches, bites in coastal waters "
                  "versus rivers and harbors, bite zones by era and El Niño phases. Rebuilt weekly from the public sources."),
  "url": SITE + "open-data", "license": "https://creativecommons.org/licenses/by/4.0/", "isAccessibleForFree": True,
  "creator": {"@type": "Person", "name": "Blake Erickson"}, "publisher": ORG, "dateModified": BUILT,
  "temporalCoverage": f"1900-01/{cov_end}", "inLanguage": "en",
  "spatialCoverage": {"@type": "Place", "name": "Australia", "geo": {"@type": "GeoShape", "box": "-44 112 -10 154"}},
  "keywords": ["sharks", "shark bites", "bull shark", "tiger shark", "white shark", "sea surface temperature", "climate change", "Australia", "HadISST"],
  "variableMeasured": ["sea surface temperature (°C)", "shark bites", "months a year at or above 19°C"],
  "isBasedOn": ["https://zenodo.org/records/18752301", "https://www.metoffice.gov.uk/hadobs/hadisst/"],
  "distribution": [{"@type": "DataDownload", "name": f, "encodingFormat": {"csv": "text/csv", "json": "application/json", "ipynb": "application/x-ipynb+json"}[f.rsplit(".", 1)[-1]],
                    "contentUrl": SITE + "data/" + f} for f in files]}
if doi: dataset["identifier"] = "https://doi.org/" + doi
rows = "".join(f'<tr><td><a href="/data/{esc(f)}">{esc(f)}</a></td><td>{fmt_of(f)}</td><td>{size(f)}</td><td>{esc(FILE_NOTE[f])}</td></tr>' for f in files)
dict_rows = "".join(f"<tr><td><code>{esc(r['file'])}</code></td><td><code>{esc(r['column'])}</code></td><td>{esc(r['meaning'])}</td></tr>" for r in DICT)
cite = (f'Erickson, B. ({BUILT[:4]}). <i>19 Degrees: sea temperature and shark bites in Australia, 1900 to today</i> [Data set]. 19 Degrees. '
        + (f'<a href="https://doi.org/{esc(doi)}">https://doi.org/{esc(doi)}</a>' if doi else f'{SITE}open-data'))
body = f"""  <p class="lead">Every number on 19 Degrees can be checked and reused. These files are rebuilt every week from the public sources, with the code that makes them on <a href="https://github.com/i-am-blake/19-degrees">GitHub</a>.</p>
  <dl class="kv"><dt>Updated</dt><dd>{long_date(BUILT)} (weekly)</dd><dt>Shark bites to</dt><dd>{asid_to}, from the <a href="https://zenodo.org/records/18752301">Australian Shark-Incident Database</a></dd>
  <dt>Sea temperature to</dt><dd>{sst_to}, monthly <a href="https://www.metoffice.gov.uk/hadobs/hadisst/">HadISST</a></dd><dt>License</dt><dd><a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a>: reuse freely, credit "19 Degrees" and the original sources</dd>
  <dt>Permanent copy</dt><dd>{f'<a href="https://doi.org/{esc(doi)}">doi.org/{esc(doi)}</a>' if doi else "A permanent archived copy with a DOI will be listed here once the first release is archived."}</dd></dl>
  <h2>Files</h2>
  <div class="tbl"><table><thead><tr><th>File</th><th>Format</th><th>Size</th><th>What it holds</th></tr></thead><tbody>{rows}</tbody></table></div>
  <h2>Start with the notebook</h2>
  <p><a href="/data/19-degrees-starter.ipynb">19-degrees-starter.ipynb</a> loads the files above and redraws the headline results, so you can check them or take them further. It needs Python with pandas and matplotlib, or open it in Google Colab with nothing installed.</p>
  <h2>Data dictionary</h2>
  <p>Every column, in every file. The same table is in <a href="/data/data-dictionary.csv">data-dictionary.csv</a>.</p>
  <div class="tbl"><table><thead><tr><th>File</th><th>Column</th><th>Meaning</th></tr></thead><tbody>{dict_rows}</tbody></table></div>
  <h2>How to cite</h2>
  <p>{cite}</p>
  <h2>Limits</h2>
  <ul><li>Sea temperature is the monthly average for the 1° patch of open sea nearest each bite or beach, about 110 km across. It describes the season, not the water a person was in.</li>
  <li>The shark database records the month and place of each bite. Bites reported in the news after {asid_to} are not in these files until the database covers them.</li>
  <li>The original sources keep their own licenses, listed on the <a href="/sources.html">sources page</a>.</li></ul>
  <p>Using the data for research, teaching or a story? <a href="/#contact">Say hello</a>: results that test a claim are credited on the claim.</p>
"""
WRITTEN.append(write("open-data", page("open-data", "Open data and downloads", "Data", body, h1="Open data, free to reuse",
    desc=f"Download the 19 Degrees data: Australian shark bites since 1900 matched to sea temperature, the 19°C season at reference beaches and more, as CSV and JSON with a data dictionary and a starter notebook. CC BY 4.0, updated weekly.",
    jsonld=dataset)))

# ---- /changes and changes.xml -------------------------------------------------------------------------------------------
log = re.search(r'<ol class="chlog">(.*?)</ol>', T, re.S)
if not log: sys.exit("change log not found")
ENTRIES = []
for m in re.finditer(r'<li><time>([^<]+)</time><p>(.*?)</p></li>', log.group(1), re.S):
    when = datetime.datetime.strptime(m.group(1).strip(), "%d %b %Y").date()
    ENTRIES.append((when, relink(m.group(2))))
if len(ENTRIES) < 3: sys.exit("change log looks empty")
HIST = json.load(open(os.path.join(HERE, "grades_history.json"), encoding="utf-8"))
grade_rows = []
for cid, steps in HIST.items():
    for i, st in enumerate(steps):
        prev = steps[i - 1]["label"] if i else None
        grade_rows.append((st["date"], cid, prev, st["label"], st.get("why", "")))
grade_rows.sort(key=lambda r: (r[0], int(r[1][1:])), reverse=True)
def cname(cid):
    c = CLAIMS.get(cid) or CLAIMS.get(MERGED.get(cid, ""))
    lab = cid.upper()
    return f'<a href="/claims/{cid if cid in CLAIMS else MERGED.get(cid, cid)}">{lab}</a>' + (f" (now part of {MERGED[cid].upper()})" if cid in MERGED else "")
g_html = "".join(f'<tr><td>{long_date(d)}</td><td>{cname(c)}</td><td>{esc(p) + " → " if p else ""}<b>{esc(l)}</b></td><td>{esc(w)}</td></tr>' for d, c, p, l, w in grade_rows)
items = "".join(f'<li id="d{d.isoformat()}"><time datetime="{d.isoformat()}">{d.day} {MON[d.month - 1]} {d.year}</time><p>{h}</p></li>' for d, h in ENTRIES)
body = f"""  <p class="lead">Every change to a claim, newest first. Follow along in a feed reader with the <a href="/changes.xml">Atom feed</a>.</p>
  <ol class="chlog">{items}</ol>
  <h2>Every grade change</h2>
  <p>Each claim's grade history, with the reason for each change. The current grade and evidence are on each <a href="/claims/">claim's page</a>.</p>
  <div class="tbl"><table><thead><tr><th>Date</th><th>Claim</th><th>Grade</th><th>Why</th></tr></thead><tbody>{g_html}</tbody></table></div>
"""
WRITTEN.append(write("changes", page("changes", "What has changed", "Change log", body, h1="Results as they come in",
    desc="Every new result, grade change and new claim on 19 Degrees, newest first, with the reason for each change. Also available as an Atom feed.",
    head_extra='<link rel="alternate" type="application/atom+xml" title="19 Degrees: what has changed" href="/changes.xml">\n')))
def absolute(h): return re.sub(r'href="/', f'href="{SITE}', h)
feed = ['<?xml version="1.0" encoding="utf-8"?>', '<feed xmlns="http://www.w3.org/2005/Atom">',
        "  <title>19 Degrees: what has changed</title>", f'  <link href="{SITE}changes.xml" rel="self"/>', f'  <link href="{SITE}changes"/>',
        f"  <id>{SITE}changes</id>", f"  <updated>{ENTRIES[0][0].isoformat()}T00:00:00Z</updated>", "  <author><name>19 Degrees</name></author>"]
for d, h in ENTRIES[:30]:
    feed += ["  <entry>", f"    <title>{esc(text(h)[:90].rsplit(' ', 1)[0] + '…' if len(text(h)) > 90 else text(h))}</title>",
             f'    <link href="{SITE}changes#d{d.isoformat()}"/>', f"    <id>{SITE}changes#d{d.isoformat()}</id>",
             f"    <updated>{d.isoformat()}T00:00:00Z</updated>", f'    <content type="html">{esc(absolute(h))}</content>', "  </entry>"]
feed.append("</feed>")
WRITTEN.append(write("changes.xml", "\n".join(feed) + "\n"))

# ---- trails: every claim page links to the data it draws on, the claims that share it, and where it appears --------------
REG = json.load(open(os.path.join(HERE, "sources.json"), encoding="utf-8"))
SRC_BY = {}  # claim id -> [(name, url, group)]
for g in REG["groups"]:
    for e in g["sources"]:
        for n in re.findall(r"\bC(\d+)\b", e.get("used_for", "")):
            cid = MERGED.get(f"c{n}", f"c{n}")
            if cid in CLAIMS and e["name"] not in [x[0] for x in SRC_BY.get(cid, [])]: SRC_BY.setdefault(cid, []).append((e["name"], e.get("url", ""), g["group"]))
ALIAS = {"Australian Shark-Incident Database": "Shark-Incident Database", "HadISST monthly sea surface temperature": "HadISST",
         "NOAA OISST v2.1 daily sea surface temperature": "OISST", "ERSSTv5": "ERSST", "GHS-POP R2023A population grid": "GHS",
         "CMIP6 sea surface temperature, 27 models": "CMIP6", "IMOS Animal Tracking": "IMOS"}
for g in REG["groups"]:  # a claim also draws on any source its own text names
    for e in g["sources"]:
        key = ALIAS.get(e["name"])
        if not key: continue
        for cid, c in CLAIMS.items():
            if key.lower() in text(c["body"]).lower() and e["name"] not in [x[0] for x in SRC_BY.get(cid, [])]:
                SRC_BY.setdefault(cid, []).append((e["name"], e.get("url", ""), g["group"]))
TABNAME = {"home": "Home", "story": "Story", "works": "Safety", "research": "Research", "students": "Schools", "media": "Media"}  # by panel id
SHOWN = {}  # claim id -> tab pages (other than Research) that link to it
for k, (a, b, c_, d) in SPANS.items():
    if k == "research": continue
    seg = T[b:c_]
    for m in re.finditer(r'href="#(c\d+)"', seg):
        cid = MERGED.get(m.group(1), m.group(1))
        ids = re.findall(r'\bid="([^"]+)"', seg[:m.start()])  # the nearest section above the link, so the trail lands on the spot
        if cid in CLAIMS and k not in [x[0] for x in SHOWN.get(cid, [])]: SHOWN.setdefault(cid, []).append((k, ids[-1] if ids else ""))
def trail(c):
    """Only what the page doesn't already show: sources and claims linked in the claim's own text, and links the shared
    header and footer carry (Research, Sources, Open data), are left out. Rows with nothing new are dropped."""
    cid = c["id"]; body = relink(c["body"])
    linked_urls = set(re.findall(r'href="([^"]+)"', body))
    linked_claims = {MERGED.get(x, x) for x in re.findall(r'href="/claims/(c\d+)"', body)}
    n0 = ordered.index(c); linked_claims |= {o["id"] for o in ordered[max(n0 - 1, 0):n0 + 2]}  # the previous/next links at the foot
    src = [x for x in SRC_BY.get(cid, []) if not (x[1] and x[1] in linked_urls)]
    names = {x[0] for x in SRC_BY.get(cid, [])}
    rel = [o for o in CLAIMS.values() if o["id"] != cid and o["id"] not in linked_claims
           and (names & {x[0] for x in SRC_BY.get(o["id"], [])} or o["topic"] == c["topic"])]
    rel.sort(key=lambda o: (-len(names & {x[0] for x in SRC_BY.get(o["id"], [])}), o["n"]))
    rows = []
    if src: rows.append(("Data used so far", " · ".join(f'<a href="{esc(u)}">{esc(n)}</a>' if u else esc(n) for n, u, g in src)))
    if rel: rows.append(("Related claims", "".join(f'<a class="trc" href="/claims/{o["id"]}"><b>{o["label"]}</b><span>{esc(o["title"])}</span></a>' for o in rel[:5])))
    tabs = [(k, a) for k, a in SHOWN.get(cid, []) if f'/{SLUG[k]}{"#" + a if a else ""}' not in linked_urls]
    if tabs: rows.append(("Also shown on", " · ".join(f'<a href="/{SLUG[k]}{"#" + a if a else ""}">{TABNAME[k]}</a>' for k, a in tabs)))
    if not rows: return ""
    return ('  <h2 id="trail">Trail</h2>\n  <dl class="trail">' + "".join(f"<dt>{t}</dt><dd>{v}</dd>" for t, v in rows) + "</dl>\n")

# ---- /claims/ and /claims/cNN --------------------------------------------------------------------------------------------
ordered = sorted(CLAIMS.values(), key=lambda c: c["n"])
for c in ordered:
    lede = re.search(r"<dt>What came out</dt><dd>(.*?)</dd>", c["body"], re.S)
    supports = re.search(r"<dt>Supports it if</dt><dd>(.*?)</dd>", c["body"], re.S)
    desc = (f'{c["label"]}, graded "{c["grade"]}": ' + (text(lede.group(1)) if lede else ("Supports it if " + text(supports.group(1)) if supports else "")))
    desc = desc if len(desc) <= 300 else desc[:297].rsplit(" ", 1)[0] + "…"
    n0 = ordered.index(c)
    prev, nxt = ordered[n0 - 1] if n0 else None, ordered[n0 + 1] if n0 + 1 < len(ordered) else None
    nav = " · ".join(x for x in ((f'<a href="/claims/{prev["id"]}">← {prev["label"]}</a>' if prev else ""), '<a href="/claims/">All claims</a>',
                                 (f'<a href="/claims/{nxt["id"]}">{nxt["label"]} →</a>' if nxt else "")) if x)
    body = (f'  <p class="meta">Grade {badge(c)} · updated {long_date(BUILT)}</p>\n'
            + (f'  <p class="note">{esc(c["merged"])}</p>\n' if c["merged"] else "")
            + f'  <div class="claimbody">{h5_to_h2(relink(c["body"]))}</div>\n'
            + trail(c)
            + '  <h2>Help test it</h2>\n  <p>Every claim says in advance what would support it and what would rule it out. Have data, a method or a result? '
            + f'<a href="/#contact">Get in touch</a>; whoever tests a claim is credited here and on the <a href="/research#{c["id"]}">Research page</a>. How grades work: <a href="/research#h-agenda">the grade key</a>.</p>\n'
            + f'  <p class="foot" style="margin-top:28px">{nav}</p>\n')
    ld = {"@context": "https://schema.org", "@type": "WebPage", "name": f'{c["label"]}: {c["title"]}', "dateModified": BUILT, "publisher": ORG,
          "isPartOf": {"@type": "WebSite", "@id": SITE + "#site"}}
    WRITTEN.append(write(f'claims/{c["id"]}', page(f'claims/{c["id"]}', f'{c["label"]}: {c["title"]}', f'Claim {c["label"]} · {c["topic"]}', body,
                   h1=c["title"], desc=desc, jsonld=ld, crumbs=[("Research", "/research"), ("Claims", "/claims/")])))
# old claim numbers: a small page that sends readers on (GitHub Pages can't redirect)
for old, new in MERGED.items():
    to = f"/claims/{new}"
    WRITTEN.append(write(f"claims/{old}", f'<!doctype html><html lang="en-US"><head><meta charset="utf-8"><title>{old.upper()} is now part of {new.upper()} · 19 Degrees</title>'
                         f'<link rel="canonical" href="{SITE}claims/{new}"><meta name="robots" content="noindex"><meta http-equiv="refresh" content="0; url={to}"></head>'
                         f'<body><p>Claim {old.upper()} was merged into <a href="{to}">{new.upper()}</a>.</p></body></html>\n'))
groups = {}
for c in ordered: groups.setdefault(c["topic"], []).append(c)
counts = {}
for c in ordered: counts[c["grade"]] = counts.get(c["grade"], 0) + 1
lst = "".join(f'<li><span class="cid">{c["label"]}</span><a href="/claims/{c["id"]}">{esc(c["title"])}</a>{badge(c)}</li>' for c in ordered)
body = (f'  <p class="lead">{len(ordered)} claims about sharks and a warming ocean, each with a test set in advance and what would rule it out. '
        f'Grades follow the <a href="/research#h-agenda">grade key</a>; every change is on the <a href="/changes">change log</a>.</p>\n'
        f'  <ul class="clist">{lst}</ul>\n  <p class="note">Claim numbers are never reused: C2 is now part of C16, and C37 part of C6.</p>\n')
WRITTEN.append(write("claims/index", page("claims/", "All claims", "Research", body, h1=f"{len(ordered)} testable claims",
    desc=f"All {len(ordered)} 19 Degrees claims about sharks and a warming ocean, each with its current grade, the test set in advance and what would rule it out.",
    crumbs=[("Research", "/research")])))

# ---- /safety-check/<group>: the evidence ladder -------------------------------------------------------------------------
import ladder19
WRITTEN += ladder19.build(T, out, write, page, relink, esc, text, BUILT, long_date)

# ---- /questions/<slug> --------------------------------------------------------------------------------------------------
# Paused until the answers' wording is reviewed: set QUESTIONS = True to build them again
QUESTIONS = False
if QUESTIONS:
    import questions19
    WRITTEN += questions19.build(T, D, CLAIMS, out, write, page, relink, esc, text, BUILT, long_date, ym)
# /questions/ itself, and the answers to the questions people search (answers19.json), linking to the pages above when they're on
import answers19
WRITTEN += answers19.build(T, D, CLAIMS, write, page, long_date, written_long=[w for w in WRITTEN if w.startswith("questions/")])

json.dump(sorted(WRITTEN), open(os.path.join(out, ".generated.json"), "w"))
print(f"generated pages: {len(WRITTEN)} (data, changes, {len(CLAIMS)} claims, safety-check, answers" + (", questions" if QUESTIONS else "") + ")")
