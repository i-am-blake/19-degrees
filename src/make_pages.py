"""Build the Sources and methods, Legal and Privacy pages from the built index.html, reusing its logo and wave
(like make_404.py) so they always match. Usage: python3 -I make_pages.py <index.html> <out_dir> [folder=branch ...]
Writes sources.html (from sources.json, plus any new data-branch README not yet in it), legal.html and privacy.html."""
import html, json, os, re, sys

src, out = sys.argv[1:3]
DATA_DIRS = sys.argv[3:]  # "folder=branch-name" pairs, e.g. ocean=ocean-data imos=imos-data
t = open(src, encoding="utf-8").read()
logo = re.search(r'<svg class="mark"[^>]*>.*?</svg>', t, re.S).group(0)
wave = re.search(r'<div class="barwave"[^>]*>.*?</svg></div>', t, re.S).group(0)

def a(label, url):
    return f'<a href="{html.escape(url)}" target="_blank" rel="noopener">{label}</a>'

CSS = """:root{--ink:#E8F1F2;--muted:#8DADBD;--warm:#F0A04B;--cold:#5AB4E5;--sea:#0B2C46;--rule:rgba(232,241,242,.16);--lpad:24px;--logo-h:clamp(36px,1.25vw + 30px,46px);
  --f-display:"Bricolage Grotesque","Arial Narrow",system-ui,sans-serif;--f-body:"Figtree",system-ui,sans-serif;--f-data:"Martian Mono",ui-monospace,Menlo,monospace}
*{box-sizing:border-box}
html,body{margin:0;min-height:100%}
body{min-height:100vh;background:linear-gradient(180deg,#0F5677 0,#0F5677 110px,#0B4566 380px,#072F4D 700px,#031628 100%);color:var(--ink);font:400 17px/1.6 var(--f-body);-webkit-font-smoothing:antialiased}
a{color:var(--cold)}a:hover{color:var(--ink)}
.bar{position:relative;background:#0F5677;padding:var(--lpad);display:flex;align-items:center;gap:12px;z-index:2}
.lockup{display:block;line-height:0;color:#FFFFFF}
.lockup .mark{height:var(--logo-h);width:auto;display:block}
.bar nav{margin-left:auto;display:flex;gap:4px;flex-wrap:wrap}
.bar nav a{font-size:15px;font-weight:600;color:#FFFFFF;text-decoration:none;border:1.5px solid transparent;padding:10px 14px;min-height:44px;display:inline-flex;align-items:center;border-radius:999px}
.bar nav a:hover,.bar nav a[aria-current]{border-color:rgba(255,255,255,.85)}
.barwave{position:absolute;left:0;right:0;top:100%;height:19.5px;overflow:hidden;pointer-events:none}
.barwave svg{display:block;width:200%;height:19.5px;animation:ripple 6.3s linear infinite reverse}
@keyframes ripple{to{transform:translateX(-50%)}}
main{max-width:860px;margin:0 auto;padding:72px 24px 96px}
.kicker{font:500 13px/1.4 var(--f-data);letter-spacing:.16em;text-transform:uppercase;color:var(--warm);margin-bottom:12px}
h1{font:800 clamp(36px,6vw,60px)/1.05 var(--f-display);letter-spacing:-.02em;margin:0 0 16px}
h2{font:700 24px/1.25 var(--f-display);margin:40px 0 12px}
p,li{color:#C9DCE3;max-width:44em}
.lead{font-size:19px;color:var(--ink)}
.tbl{overflow-x:auto;margin:12px 0}
table{border-collapse:collapse;width:100%;min-width:640px;font-size:15px}
th,td{text-align:left;vertical-align:top;padding:10px 12px;border-bottom:1px solid var(--rule)}
th{font:500 12px/1.4 var(--f-data);letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
td:last-child{color:var(--muted)}
.foot{margin-top:56px;padding-top:20px;border-top:1px solid var(--rule);font-size:14px;color:var(--muted)}
a:focus-visible{outline:2px solid var(--ink);outline-offset:3px}
@media (max-width:620px){.bar nav{display:none}}
@media (prefers-reduced-motion:reduce){.barwave svg{animation:none}}"""

def page(slug, title, kicker, body):
    cur = ' aria-current="page"'
    nav = "".join('<a href="/' + s + '.html"' + (cur if s == slug else "") + ">" + n + "</a>"
                  for s, n in (("sources", "Sources"), ("legal", "Legal"), ("privacy", "Privacy")))
    return f"""<!doctype html>
<html lang="en-US">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · 19 Degrees</title>
<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="stylesheet" href="/fonts/fonts.css">
<style>
{CSS}
</style>
</head>
<body>
<div class="bar">
  <a class="lockup" href="/" aria-label="19 Degrees, home">{logo}</a>
  <nav aria-label="Pages"><a href="/">Home</a>{nav}</nav>
  {wave}
</div>
<main>
  <div class="kicker">{kicker}</div>
  <h1>{title}</h1>
{body}
  <p class="foot">© 2026 Blake Erickson · <a href="/">19 Degrees</a> · <a href="/#contact">Contact</a></p>
</main>
</body>
</html>
"""

def table(rows):
    head = "<tr><th>Data</th><th>From</th><th>Used for</th><th>License</th></tr>"
    return '<div class="tbl"><table>' + head + "".join(f"<tr><td>{d}</td><td>{f}</td><td>{u}</td><td>{l}</td></tr>" for d, f, u, l in rows) + "</table></div>"

REG = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "sources.json"), encoding="utf-8"))

def cell(e):
    return a(html.escape(e["name"]), e["url"]) if e.get("url") else html.escape(e["name"])

def auto_rows():
    """Data saved by a fetch job with a README_*.txt that sources.json doesn't cover yet, listed from the README."""
    covered = set(REG.get("hide", [])) | {r for g in REG["groups"] for e in g["sources"] for r in e.get("readme", [])}
    rows = []
    for spec in DATA_DIRS:
        folder, label = spec.split("=", 1)
        if not os.path.isdir(folder): continue
        for f in sorted(os.listdir(folder)):
            key = label + "/" + f
            if re.fullmatch(r"README(_\w+)?\.txt", f) and key not in covered:
                txt = re.sub(r"\s+", " ", open(os.path.join(folder, f), encoding="utf-8", errors="replace").read()).strip()
                lic = re.search(r"\b(CC BY[\w .-]*?\d\.\d|CC BY|CC0|public domain|Open Government Licence)\b", txt, re.I)
                title = re.split(r"[,(.]", txt, maxsplit=1)[0][:90]
                rows.append((html.escape(title), html.escape(txt[:240] + ("…" if len(txt) > 240 else "")), "Recently added", html.escape(lic.group(1) if lic else "See source")))
                print("make_pages: listed new source automatically:", key)
    return rows

METHODS = [
 "Sea temperature is the monthly HadISST average for the 1° patch of open sea nearest each bite or beach, about 110 km across. It describes the season, not the water a person was in, and runs a little warmer than water at the beach.",
 "Many bull shark bites, especially before 2000, happened in harbors and rivers, where the water can be warmer than the open-sea patch it is measured against.",
 "The look ahead to 2050 adds each beach's 1980–2025 warming trend to its 2016–2025 average month. It is a simple extrapolation, not a climate model; claim C3 uses 27 climate models instead.",
 "Fewer people swim in cold water, but white sharks still bite there, so people are in the water when bull sharks are not.",
]
_D = json.loads(re.search(r'id="n19-data">(.*?)</script>', t, re.S).group(1))
_M = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()
_ym = lambda v: (_M[int(v[5:7]) - 1] + " " + v[:4]) if isinstance(v, str) else (_M[v["month"] - 1] + " " + str(v["year"]))
CURRENT = f'Updated {_D["built"]}. Monthly sea temperature to {_ym(_D["sst_last"])}; shark database to {_ym(_D["asid_last"])}. Today\'s beach readings refresh daily. Temperatures are in °C; 19°C is 66°F.'
src_body = '  <p class="lead">Everything on 19 Degrees is built from public data and published research. Each source keeps its own license. All code is on ' + a("GitHub", "https://github.com/i-am-blake/19-degrees") + ", so every result can be rerun.</p>\n  <p>" + CURRENT + "</p>\n"
for g in REG["groups"]:
    rows = [(cell(e), html.escape(e.get("from", "")), html.escape(e.get("used_for", "")), html.escape(e.get("license", ""))) for e in g["sources"]]
    src_body += f"  <h2>{html.escape(g['group'])}</h2>\n  {table(rows)}\n"
_auto = auto_rows()
if _auto:
    src_body += f"  <h2>Recently added</h2>\n  {table(_auto)}\n"
src_body += "  <h2>Method notes</h2>\n  <ul>" + "".join(f"<li>{m}</li>" for m in METHODS) + "</ul>\n"
src_body += "  <p>Naming a source doesn't mean it endorses this site. See the " + '<a href="/legal.html">legal page</a>' + ".</p>\n"

LEGAL = [
 ("License", "Code: " + a("MIT License", "https://github.com/i-am-blake/19-degrees/blob/main/LICENSE") + ". Text, charts and images: " + a("CC BY 4.0", "https://creativecommons.org/licenses/by/4.0/") + '; credit "19 Degrees, Blake Erickson". Data keeps its own license, listed on the <a href="/sources.html">sources page</a>. The 19 Degrees name and logo are not licensed for reuse.'),
 ("General information only", "19 Degrees is an independent educational project. It summarizes public data and published research and may contain errors or be out of date. It is general information only, not safety, medical, legal or professional advice, and is provided \"as is\" without warranty of any kind."),
 ("Not a guide to whether or where to swim", "Don't rely on this site to decide whether or where to swim. Follow lifesavers, beach signs and local authorities. Results describe how often bites came under past conditions; they are not forecasts, and conditions don't cause bites on their own. In an emergency, call your local emergency number: 000 in Australia, 911 in the US and Canada, 999 in the UK, 112 across Europe and on most mobile phones worldwide."),
 ("First aid", "First-aid information summarizes published research. It is not a substitute for first-aid training or for help from emergency services."),
 ("No affiliation or endorsement", "19 Degrees is not affiliated with, sponsored by or endorsed by any organization, data provider, government agency, research group or company named on the site. Naming a source, citing a study or linking a page does not mean that organization has reviewed or approved this site."),
 ("Third-party data", "Results depend on data published by others, which can change, be corrected or contain errors. Bites reported in the news after the database's latest month are marked unconfirmed until the database covers them."),
 ("Products", "Product information summarizes published independent tests, which are linked. It is not the author's own testing, and it is not an endorsement or a criticism of any maker or product."),
 ("Links to other sites", "Links to other sites are provided for reference. The author does not control and is not responsible for their content, accuracy or availability."),
 ("Classroom materials", "Classroom sheets are intended for use under a teacher's or parent's supervision."),
 ("Support and donations", "Support sent through Venmo is a personal gift to the project's author to help keep it running. 19 Degrees is not a registered charity, gifts are not tax-deductible, and nothing is given in return."),
 ("Corrections, copyright and privacy requests", 'Report an error, a copyright concern, or a privacy concern (for example, from someone connected to a bite) through the <a href="/#contact">contact form</a>. Reports are reviewed and the page is corrected or the material removed where appropriate.'),
 ("Limitation of liability", "To the extent the law allows, the author accepts no liability for any loss or harm arising from use of this site, its data, its downloads or anything built from them. Nothing here limits rights that cannot be limited by law."),
]
leg_body = ""
leg_body += "".join(f"  <h2>{h}</h2>\n  <p>{p}</p>\n" for h, p in LEGAL)
leg_body += "  <p>Last updated 3 November 2026.</p>\n"

PRIV = [
 ("What this site collects", "No cookies, no ads and no tracking across sites. Visits and clicks are counted with " + a("GoatCounter", "https://www.goatcounter.com/") + ", which keeps aggregate counts and stores no personal data."),
 ("The contact form", "The form sends your name, email address and message to Blake through " + a("Web3Forms", "https://web3forms.com/") + ", which passes it on by email. They are used only to reply and are never sold or shared. Ask through the form to have a message deleted."),
 ("Hosting", "The site is hosted on GitHub Pages, which may keep server logs for security under " + a("GitHub's privacy statement", "https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement") + "."),
 ("Other sites", "Links such as Venmo, social media and data sources take you to other sites with their own privacy policies."),
 ("Children", "Under 13? Ask a parent, guardian or teacher to use the contact form for you."),
]
pri_body = '  <p class="lead">19 Degrees collects as little as possible.</p>\n' + "".join(f"  <h2>{h}</h2>\n  <p>{p}</p>\n" for h, p in PRIV) + "  <p>Last updated 3 November 2026.</p>\n"

os.makedirs(out, exist_ok=True)
for slug, title, kicker, body in (("sources", "Sources and methods", "Data and credits", src_body),
                                  ("legal", "Legal and disclaimer", "Terms of use", leg_body),
                                  ("privacy", "Privacy", "Your data", pri_body)):
    open(os.path.join(out, slug + ".html"), "w", encoding="utf-8").write(page(slug, title, kicker, body))
print("pages: sources.html, legal.html, privacy.html")
