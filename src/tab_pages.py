"""Each tab of the site is its own page: index.html (Home), story.html, safety.html, research.html, schools.html and
media.html (GitHub Pages serves story.html at /story). Each page keeps the shared header, footer, contact form and
page data, and only its own tab's content; the other tabs are left as empty shells, so the tab bar still works and
a click on another tab opens that page. Links to a section of another tab become links to that page.
Usage: python3 -I tab_pages.py <full index.html> <out_dir>"""
import html, json, os, re, sys
SITE = "https://19-degrees.org/"
TABS = (("story", "Story"), ("safety", "Safety"), ("research", "Research"), ("schools", "Schools"), ("media", "News and media"))
PANEL = {"": "home", "story": "story", "safety": "works", "research": "research", "schools": "students", "media": "media"}
DOORS = ("discover", "investigate", "contribute")  # /schools#investigate opens a door on the Schools page

def panel_spans(s):
    """{panel: (start of opening tag, end of opening tag, start of closing </div>, end)} by counting nested divs."""
    spans, tok = {}, re.compile(r'<script\b.*?</script>|<div\b|</div>', re.S)
    for m in re.finditer(r'<div role="tabpanel" id="panel-([a-z]+)"[^>]*>', s):
        depth = 1
        for t in tok.finditer(s, m.end()):
            g = t.group(0)
            if g.startswith("<script"): continue
            depth += 1 if g == "<div" else -1
            if depth == 0: spans[m.group(1)] = (m.start(), m.end(), t.start(), t.end()); break
    return spans

def titles(doc):
    d = json.loads(re.search(r'id="n19-data">(.*?)</script>', doc, re.S).group(1))
    n = len(re.findall(r'<article class="claim" id="c\d+"', doc))
    if n < 10: sys.exit("could not count the claims for the Research page description")
    b = d["species"]["bull"]["n"]
    return {
        "story": ("Sea temperature and shark bites in Australia",
                  f"{b} bull shark bites in Australia since 1900, and not one in a month when the sea was cooler than 19°C (66°F). How warming seas are lengthening the bull shark season and moving it south."),
        "safety": ("Shark safety: what the evidence says",
                   "Shark nets, drumlines, drones and personal deterrents, each checked against published independent tests: what has been shown to reduce bites, what hasn't, and what is still untested."),
        "research": (f"{n} testable claims about sharks and a warming ocean",
                     f"{n} claims about sharks and a warming ocean, each with a test set in advance and what would rule it out. Results as they come in, open data, and how to help test the next one."),
        "schools": ("Free shark and climate lessons for schools",
                    "Free classroom sheets for ages 8 to 11, 12 to 15 and 16 and up: a real climate story told with the same sea temperature and shark records scientists use, with teacher notes and curriculum links."),
        "media": ("News and media: findings, figures and images",
                  "Key findings, story angles and checked figures on sharks and a warming ocean, free to use with credit, plus guidance on reporting shark bites accurately."),
    }

def write(doc, out):
    sp = panel_spans(doc)
    if set(sp) != set(PANEL.values()): sys.exit("tab panels not found: " + ", ".join(sorted(sp)))
    # which tab each id lives in, so a link or an old address to it can open the right page
    where = {}
    for k, (a, b, c, d) in sp.items():
        for i in re.findall(r'\bid="([^"]+)"', doc[b:c]): where[i] = k
    for i in DOORS: where[i] = "students"
    slug_of = {v: k for k, v in PANEL.items()}
    ids = {slug_of[k]: " ".join(i for i, t in where.items() if t == k) for k in sp if k != "home"}
    T = titles(doc)
    for slug, keep in PANEL.items():
        d = doc
        for k, (a, b, c, e) in sorted(sp.items(), key=lambda x: -x[1][0]):
            if k != keep: d = d[:b] + d[c:]  # keep the empty panel shell
        # scripts that only draw into tabs that aren't on this page are left out
        def drop(m):
            js = m.group(1)
            used = set(re.findall(r'getElementById\("([^"]+)"\)', js)) | set(re.findall(r'querySelector(?:All)?\("#([\w-]+)', js))
            tabs = {where.get(i, "shared") for i in used}
            return "" if used and keep not in tabs and "shared" not in tabs else m.group(0)
        d = re.sub(r'<script>(.*?)</script>\n?', drop, d, flags=re.S)
        d = re.sub(r'(<div role="tabpanel" id="panel-)([a-z]+)"', lambda m: m.group(0) + ("" if m.group(2) == keep else ' data-elsewhere="1"'), d)
        # links to a section of another tab go to that tab's page
        def fix(m):
            h = m.group(1)
            if h in slug_of:  # a link to a whole tab (#research, #works)
                return m.group(0) if h == keep else f'href="/{slug_of[h]}"'
            t = where.get(h)
            if not t or t == keep or t == "home" and keep == "home": return m.group(0)
            return f'href="/{slug_of[t]}#{h}"' if t != "home" else f'href="/#{h}"'
        d = re.sub(r'href="#([^"]+)"', fix, d)
        if keep == "research":  # each claim card links to the claim's own page (/claims/c16), built by gen19.py
            d = re.sub(r'(<article class="claim" id="(c\d+)".*?)(<button type="button" class="ctabtn")',
                       lambda m: (sys.exit("claim card without a button: " + m.group(2)) if "</article>" in m.group(1) else m.group(1)) + f'<p class="clink"><a href="/claims/{m.group(2)}">This claim on its own page →</a></p>' + m.group(3), d, flags=re.S)
        if keep == "works":  # the product table links to the evidence ladder pages
            d = d.replace('<div class="ptwrap">', '<p class="clink"><a href="/safety-check/">Each group on the evidence ladder, from lab test to real-world use →</a></p><div class="ptwrap">', 1)
        d, n = re.subn(r'<script[^>]*id="n19-data"', lambda m: '<script type="application/json" id="n19-ids">' + json.dumps(ids, separators=(",", ":")) + '</script>\n' + m.group(0), d, count=1)
        if n != 1: sys.exit("page data not found")
        if slug:
            title, desc = T[slug]
            d = d.replace(f'<link rel="canonical" href="{SITE}">', f'<link rel="canonical" href="{SITE}{slug}">', 1)
            d = d.replace(f'<meta property="og:url" content="{SITE}">', f'<meta property="og:url" content="{SITE}{slug}">', 1)
            d, n = re.subn(r'<title>[^<]*</title>', f'<title>{html.escape(title)} · 19 Degrees</title>', d, count=1)
            for pat in (r'(<meta name="description" content=")[^"]*', r'(<meta property="og:description" content=")[^"]*', r'(<meta name="twitter:description" content=")[^"]*'):
                d, k = re.subn(pat, lambda m: m.group(1) + html.escape(desc), d, count=1); n += k
            for pat in (r'(<meta property="og:title" content=")[^"]*', r'(<meta name="twitter:title" content=")[^"]*'):
                d, k = re.subn(pat, lambda m: m.group(1) + html.escape(title), d, count=1); n += k
            d = re.sub(r'<!-- Search engines:[^\n]*-->\n<script type="application/ld\+json">.*?</script>\n?', "", d, count=1, flags=re.S)  # the site's description stays on the home page
            if n != 6 or f'href="{SITE}{slug}"' not in d: sys.exit("could not set the address and description for " + slug)
        open(os.path.join(out, (slug or "index") + ".html"), "w", encoding="utf-8").write(d)

if __name__ == "__main__":
    write(open(sys.argv[1], encoding="utf-8").read(), sys.argv[2])
