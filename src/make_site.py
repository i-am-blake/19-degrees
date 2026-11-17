"""Assemble the GitHub Pages site: python3 -I make_site.py <built 19-degrees.html> <pub_dir> <out_dir>
Wraps the built page in a full HTML document with launch/head.html (link previews, icons) and copies
the classroom sheets, data/, share/ and launch files. Fails if the address placeholder or a personal email is left in."""
import json, os, re, shutil, subprocess, sys
page, pub, out = sys.argv[1:4]
SITE = "https://19-degrees.org/"
body = open(page).read()
body = re.sub(r'<title>.*?</title>\n?', '', body, count=1)
# fonts: served from this site instead of Google, so no visitor data goes to Google
body, nf = re.subn(r'<link rel="preconnect" href="https://fonts\.googleapis\.com">\n<link rel="preconnect" href="https://fonts\.gstatic\.com" crossorigin>\n<link rel="stylesheet" href="https://fonts\.googleapis\.com/css2[^"]*">',
                   '<link rel="stylesheet" href="fonts/fonts.css">', body)
if nf != 1: sys.exit("Google Fonts tags not found")
# security: the page may only load its own files, talk to GoatCounter (visit counts) and Web3Forms (contact form),
# and frame Ko-fi's tip panel (loaded only after a Donate click)
GC = re.search(r'GOATCOUNTER:\s*"([^"]*)"', body).group(1)
gc = f" https://{GC}.goatcounter.com" if GC else ""
CSP = ("default-src 'self'; script-src 'self' 'unsafe-inline'" + (" https://gc.zgo.at" if GC else "") +
       "; style-src 'self' 'unsafe-inline'; font-src 'self'; img-src 'self' data: blob:" + gc +
       "; connect-src 'self' https://api.web3forms.com" + gc + "; object-src 'none'; base-uri 'self'; form-action 'self'; frame-src https://ko-fi.com")
SEC = f'<meta http-equiv="Content-Security-Policy" content="{CSP}">\n<meta name="referrer" content="strict-origin-when-cross-origin">\n'
SEC_STATIC = ('<meta http-equiv="Content-Security-Policy" content="default-src \'self\'; script-src \'self\' \'unsafe-inline\'; style-src \'self\' \'unsafe-inline\'; img-src \'self\' data:; '
              'object-src \'none\'; base-uri \'self\'; form-action \'none\'; frame-src \'none\'">\n')
head = open(os.path.join(pub, "launch", "head.html")).read().replace("https://YOUR-SITE/", SITE)
head = re.sub(r'<!-- 19 Degrees: paste inside.*?-->\n', '', head, count=1)
# link-card version: social sites cache preview images by URL, so a new image needs a new URL
import hashlib
_lc = os.path.join(pub, "share", "link-card.png")
if os.path.exists(_lc):
    head = head.replace("share/link-card.png", "share/link-card.png?v=" + hashlib.sha1(open(_lc, "rb").read()).hexdigest()[:8])
doc = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
       '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n' + SEC + head + '\n' + body + '\n</html>\n')
if os.path.exists(out): shutil.rmtree(out)
os.makedirs(out)
open(os.path.join(out, "index.html"), "w").write(doc)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import tab_pages
open(os.path.join(out, "CNAME"), "w").write(SITE.split("//")[1].strip("/") + "\n")  # GitHub Pages custom domain
for f in os.listdir(pub):
    if re.match(r"classroom.*\.html$", f):
        t = open(os.path.join(pub, f)).read()
        t, n = re.subn(r'(<meta charset="utf-8">)', r'\1' + SEC_STATIC.replace('\\', '\\\\'), t, count=1)
        if n != 1: sys.exit("no charset meta in " + f)
        open(os.path.join(out, f), "w").write(t)
shutil.copytree(os.path.join(pub, "data"), os.path.join(out, "data"))
shutil.copytree(os.path.join(pub, "fonts"), os.path.join(out, "fonts"))
shutil.copytree(os.path.join(pub, "share"), os.path.join(out, "share"), ignore=shutil.ignore_patterns("classroom-preview.png"))
for f in ["favicon.ico", "favicon.svg", "apple-touch-icon.png", "icon-32.png", "icon-192.png", "icon-512.png", "site.webmanifest", "LICENSE"]:
    shutil.copy(os.path.join(pub, "launch", f), out)
# page-not-found page, built from the finished index.html so its logo and wave always match
_m404 = os.path.join(os.path.dirname(os.path.abspath(__file__)), "make_404.py")
if os.path.exists(_m404):
    subprocess.run([sys.executable, "-I", _m404, os.path.join(out, "index.html"), os.path.join(out, "404.html")], check=True)
# Sources, Legal and Privacy pages, built the same way
_mp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "make_pages.py")
if os.path.exists(_mp):
    subprocess.run([sys.executable, "-I", _mp, os.path.join(out, "index.html"), out] + [d + "=" + b for d, b in (("ocean", "ocean-data"), ("imos", "imos-data")) if os.path.isdir(d)], check=True)
# Funder summary PDF: rebuilt every time from the same index.html as funders.html, so its numbers always match the site
_ms = os.path.join(os.path.dirname(os.path.abspath(__file__)), "make_summary.py")
_chrome = shutil.which("google-chrome") or shutil.which("chromium") or shutil.which("chromium-browser")
if os.path.exists(_ms):
    _sh = os.path.join(out, "_summary.html"); _pdf = os.path.join(out, "19-degrees-summary.pdf")
    subprocess.run([sys.executable, "-I", _ms, os.path.join(out, "index.html"), _sh], check=True)
    if not _chrome: sys.exit("::error::No Chrome to build 19-degrees-summary.pdf; not publishing a PDF with old numbers.")
    subprocess.run([_chrome, "--headless=new", "--no-sandbox", "--disable-gpu", "--no-pdf-header-footer", "--print-to-pdf=" + _pdf, "file://" + os.path.abspath(_sh)], check=True, timeout=120, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    os.remove(_sh)
    _pages = re.findall(rb"/Type\s*/Page[^s]", open(_pdf, "rb").read())
    if len(_pages) != 1: sys.exit(f"::error::Funder summary PDF is {len(_pages)} pages, not 1.")
# the funder page and its PDF must show the same numbers as the home page
_ix = open(os.path.join(out, "index.html"), encoding="utf-8").read()
_fp = os.path.join(out, "funders.html")
if os.path.exists(_fp):
    _fu = open(_fp, encoding="utf-8").read()
    for _lab, _fl in (("Data sources joined", "Data sources joined"), ("Products checked", "Safety products checked")):
        _n = re.search(r'<span class="lab">' + _lab + r'</span><span class="big"[^>]*>(\d+)<', _ix).group(1)
        if f"<b>{_n}</b><span>{_fl}</span>" not in _fu: sys.exit(f"::error::funders.html {_fl} does not match the home page ({_n}).")
    _d = re.search(r"(\d+) / (\d+)</span> claims with a first look or a result", _ix)
    if f"{_d.group(1)} of {_d.group(2)} claims have a first look" not in _fu: sys.exit("::error::funders.html claim count does not match the Research page.")
    print("funder page and PDF: numbers match the home page")
# Generated pages: data, changes and its feed, one page per claim, the safety evidence ladder, questions
_gp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gen19.py")
subprocess.run([sys.executable, "-I", _gp, os.path.join(out, "index.html"), out], check=True)
_gen = json.load(open(os.path.join(out, ".generated.json"))); os.remove(os.path.join(out, ".generated.json"))
# sitemap and robots.txt, so search engines find every page (merged-claim pages that only send readers on are left out)
import datetime as _dt
_today = _dt.date.today().isoformat()
_urls = [SITE] + [SITE + _s for _s, _ in tab_pages.TABS] + [SITE + f for f in ("classroom.html", "classroom-primary.html", "classroom-middle.html", "classroom-senior.html", "sources.html", "legal.html", "privacy.html", "funders.html")]
_urls += [SITE + re.sub(r"(^|/)index$", r"\1", g) for g in _gen if not g.endswith(".xml") and g not in ("claims/c2", "claims/c37")]
open(os.path.join(out, "sitemap.xml"), "w").write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "".join(f"  <url><loc>{u}</loc><lastmod>{_today}</lastmod></url>\n" for u in _urls) + "</urlset>\n")
open(os.path.join(out, "robots.txt"), "w").write(f"User-agent: *\nAllow: /\nSitemap: {SITE}sitemap.xml\n")
# each tab is its own page (/, /story, /safety, ...): split last, because the pages above read the full index.html
tab_pages.write(doc, out)
bad = []
for root, _, files in os.walk(out):
    for f in files:
        t = open(os.path.join(root, f), "rb").read()
        if f.endswith((".html", ".css")) and (b"fonts.googleapis" in t or b"fonts.gstatic" in t): bad.append(f + " (Google Fonts)")
        if b"YOUR-SITE" in t or b"YOUR-DOMAIN" in t or re.search(rb"[\w.+-]+@gmail\.com", t) or re.search(rb"(?i)\bcl[a]ude\b", t): bad.append(f)
if bad: sys.exit("placeholder, personal email or tool name left in: " + ", ".join(bad))
print("site written to", out)
