"""Checks the finished site folder after make_site.py: every page, link and generated number agrees with the home page.
Usage: python3 -I check_site19.py <site_dir>. Stops (exit 1) on any problem, so a broken site is never published."""
import html, json, os, re, sys
import xml.etree.ElementTree as ET
root = sys.argv[1]; bad = []; n = 0
def check(label, ok):
    global n; n += 1
    if not ok: bad.append(label)
def read(p): return open(os.path.join(root, p), encoding="utf-8").read()
def text(h): return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", h))).strip()
pages = sorted(os.path.relpath(os.path.join(d, f), root) for d, _, fs in os.walk(root) for f in fs if f.endswith(".html"))
ids = {p: set(re.findall(r'\bid="([^"]+)"', read(p))) for p in pages}
def resolve(u):
    q = u.split("#")[0].split("?")[0].lstrip("/")
    for c in ((q or "index.html"), q + ".html", q.rstrip("/") + "/index.html"):
        if c and os.path.isfile(os.path.join(root, c)): return c
# 1. every internal link lands on a page, and on an id that page has
TABS = {"story", "works", "research", "students", "media", "home"}
for p in pages:
    s = re.sub(r'<script\b(?![^>]*ld\+json).*?</script>', "", read(p), flags=re.S)
    for u in set(re.findall(r'href="([^"]+)"', s)):
        u = html.unescape(u)
        if u.startswith(("http", "mailto:", "tel:")): continue
        if u.startswith("#"):
            check(f"{p}: link {u} has no target", not u[1:] or u[1:] in ids[p] or u[1:] in TABS); continue
        if not u.startswith("/"): u = "/" + os.path.normpath(os.path.join(os.path.dirname(p), u))
        t = resolve(u)
        check(f"{p}: link {u} goes nowhere", t is not None)
        if t and "#" in u: check(f"{p}: link {u} has no target in {t}", u.split("#", 1)[1] in ids[t])
    for j in re.findall(r'<script type="application/ld\+json">(.*?)</script>', read(p), re.S):
        try: json.loads(j)
        except ValueError: check(f"{p}: structured data isn't valid JSON", False)
    check(f"{p}: no title", re.search(r"<title>[^<]{5,}</title>", read(p)) is not None)
# 2. every page in the sitemap exists
sm = read("sitemap.xml")
for u in re.findall(r"<loc>https://19-degrees\.org/([^<]*)</loc>", sm): check(f"sitemap: {u or '/'} has no page", resolve("/" + u) is not None)
# 3. each tab page has its own title, description and address; descriptions are unique across the site
desc = {}
for p in pages:
    m = re.search(r'<meta name="description" content="([^"]+)"', read(p))
    if m and "refresh" not in read(p): desc.setdefault(m.group(1), []).append(p)
for d, ps in desc.items(): check("same description on " + ", ".join(ps), len(ps) == 1)
for p in ("story.html", "safety.html", "research.html", "schools.html", "media.html"):
    s = read(p); slug = p[:-5]
    check(f"{p}: address", f'<link rel="canonical" href="https://19-degrees.org/{slug}">' in s)
    check(f"{p}: has its own content only", s.count('data-elsewhere="1"') == 5)
check("index.html: has the home content only", read("index.html").count('data-elsewhere="1"') == 5)
# 4. claim pages match the claim cards on the Research page
R = read("research.html")
cards = re.findall(r'<article class="claim" id="(c\d+)" data-status="\w+"><details><summary><div class="chead"><span class="cid">C\d+</span><span class="subt">.*?</span><span class="cstat[^"]*">(.*?)</span></div><h4>(.*?)</h4>', R, re.S)
check("research.html: claim cards found", len(cards) >= 40)
for cid, grade, title in cards:
    f = f"claims/{cid}.html"
    if not os.path.exists(os.path.join(root, f)): check(f"{f} missing", False); continue
    s = read(f)
    check(f"{f}: title differs from the card", f"<h1>{html.escape(text(title))}</h1>" in s)
    check(f"{f}: grade differs from the card", re.search(r'<p class="meta">Grade <span class="cstat[^"]*">' + re.escape(html.escape(text(grade))) + "</span>", s) is not None)
grade_of = {cid: text(g) for cid, g, _ in cards}
check("claims/index.html lists every claim", all(f'href="/claims/{c}"' in read("claims/index.html") for c in grade_of))
# 5. claim grades quoted on question pages match the cards
for p in [p for p in pages if p.startswith("questions/")]:
    s = read(p)
    for cid, g in re.findall(r'<a href="/claims/(c\d+)"><b>C\d+: [^<]*</b></a> <span class="cstat[^"]*">([^<]*)</span>', s):
        check(f"{p}: {cid} grade '{g}' differs from the card ('{grade_of.get(cid)}')", grade_of.get(cid) == text(g))
    for g in re.findall(r'graded "([^"]+)"', html.unescape(s)): check(f"{p}: graded '{g}' is not a grade", g in set(grade_of.values()))
    if not p.endswith("index.html"): check(f"{p}: answer first", 'class="answer"' in s and s.index('class="answer"') < s.index("<h2>"))
# 6. the numbers in the answers match the page data
D = json.loads(re.search(r'id="n19-data">(.*?)</script>', read("index.html"), re.S).group(1))
B = D["species"]["bull"]; Z = D["zones"]
q1 = read("questions/what-is-the-19c-line.html")
check("19°C line page: bull shark bite count", f"Australia's {B['n']} recorded bull shark bites" in html.unescape(q1))
check("19°C line page: distance the line moved", f"moved about {round((Z['line'][0] - Z['line'][-1]) * 111)} km south" in q1)
check("bull shark temperature page: coolest month", f"{B['min']:.1f}°C or more" in read("questions/what-temperature-do-bull-sharks-prefer.html"))
ws = D["wa_spike"]; q5 = read("questions/are-shark-bites-increasing.html")
check("bites page: Western Australia counts", f"since 2020 ({ws['post']})" in q5 and f"before ({ws['pre']})" in q5)
# 7. the safety ladder lists every product on the Safety page, each once
S = read("safety.html")
prods = [text(re.sub(r"<span>.*?</span>", "", x)) for x in re.findall(r'<tr><th scope="row">(.*?)</th>', S[S.index('<table class="ptab">'):S.index("</table>", S.index('<table class="ptab">'))], re.S)]
lad = "".join(read(p) for p in pages if p.startswith("safety-check/") and not p.endswith("index.html"))
for pr in prods: check(f"safety ladder: '{pr}' appears {lad.count('<h3>' + html.escape(pr) + '</h3>')} times", lad.count("<h3>" + html.escape(pr) + "</h3>") == 1)
check("safety ladder: a deterrent claims real-world protection", "Reached: </span>Shown to protect people" not in lad)
# 8. the change log and its feed
ch = read("changes.html"); n_log = len(re.findall(r"<li><time>", read("research.html").split('<ol class="chlog">')[1].split("</ol>")[0]))
check("changes page: every change log entry", ch.count('<li id="d') == n_log)
try:
    feed = ET.parse(os.path.join(root, "changes.xml")).getroot()
    check("feed: entries", len(feed.findall("{http://www.w3.org/2005/Atom}entry")) == min(30, n_log))
except ET.ParseError as e: check(f"feed isn't valid XML: {e}", False)
# 9. the data page lists every download and dates the dataset to this build
dp = read("data/index.html")
for f in os.listdir(os.path.join(root, "data")):
    if f != "index.html": check(f"data page doesn't list {f}", f'href="/data/{f}"' in dp)
ld = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', dp, re.S).group(1))
ds = next(x for x in (ld if isinstance(ld, list) else [ld]) if x.get("@type") == "Dataset")
check("dataset date matches the build", ds["dateModified"] == D["built"])
print(f"check_site19: {n} checks on {len(pages)} pages, {len(bad)} problems")
for b in bad[:60]: print("  PROBLEM:", b)
sys.exit(1 if bad else 0)
