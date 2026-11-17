"""Shared shell for the site's plain pages (Sources, Legal, Privacy, Funders, and the generated pages: claims,
questions, safety evidence, data, changes): the same logo, wave, fonts and colors as the home page, read from the
built index.html so they always match."""
import html, json, re
SITE = "https://19-degrees.org/"
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
.crumbs{font-size:14px;color:var(--muted);margin:-40px 0 28px}.crumbs a{color:var(--muted)}
.answer{font-size:20px;line-height:1.5;color:var(--ink);border-left:4px solid var(--warm);padding:4px 0 4px 18px;margin:8px 0 24px;max-width:40em}
h3{font:700 19px/1.3 var(--f-display);margin:28px 0 8px;color:var(--ink)}
dl.kv{display:grid;grid-template-columns:minmax(120px,190px) 1fr;gap:8px 18px;margin:12px 0}dl.kv dt{font:500 12px/1.6 var(--f-data);letter-spacing:.08em;text-transform:uppercase;color:var(--muted);padding-top:3px}dl.kv dd{margin:0;color:#C9DCE3}
@media (max-width:620px){dl.kv{grid-template-columns:1fr}dl.kv dd{margin-bottom:8px}}
.meta{font:500 13px/1.6 var(--f-data);letter-spacing:.04em;color:var(--muted)}
.cstat{display:inline-flex;align-items:center;justify-content:center;gap:6px;font:500 13px/1 var(--f-data);letter-spacing:.06em;text-transform:uppercase;border:1.5px solid #71858F;color:var(--muted);padding:6px 10px;white-space:nowrap;vertical-align:middle}
.cstat.early{border-color:#4FB286;color:#8FD9B6}.cstat.sup{background:#2E7D5B;border-color:#2E7D5B;color:#fff}.cstat.strong{background:var(--ink);border-color:var(--ink);color:#041A2C}
.cstat.unc{border-style:dashed;border-color:var(--muted);color:var(--ink)}.cstat.look{border-style:dotted;border-color:#7CC7F0;color:#A9DCF6}.cstat.no{border-color:#C9705F;color:#F0A493}
.cstat.ruled{background:#8A3B2E;border-color:#D97A66;color:#fff}
.agres,.note{color:#C9DCE3}.note{font-size:15px;color:var(--muted)}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,260px),1fr));gap:14px;margin:16px 0;padding:0;list-style:none}
.cards>li,.cards>a{border:1px solid var(--rule);padding:16px 18px;display:block;color:#C9DCE3;text-decoration:none;max-width:none}
.cards>a:hover{border-color:var(--cold)}.cards b{display:block;color:var(--ink);font:700 18px/1.3 var(--f-display);margin:6px 0}
.clist{list-style:none;padding:0;margin:12px 0}.clist li{display:grid;grid-template-columns:4.5em 1fr auto;gap:12px;align-items:center;padding:10px 0;border-bottom:1px solid var(--rule);max-width:none}
.clist .cid{font:500 14px/1 var(--f-data);color:var(--muted)}
@media (max-width:620px){.clist li{grid-template-columns:3.5em 1fr}.clist .cstat{grid-column:2;justify-self:start}}
.ladder{list-style:none;padding:0;margin:12px 0 4px;display:grid;grid-template-columns:repeat(4,1fr);gap:4px;max-width:none}
.ladder li{font-size:13px;line-height:1.35;padding:8px 10px;border:1px solid var(--rule);color:var(--muted);max-width:none}
.ladder li.on{background:rgba(90,180,229,.16);border-color:var(--cold);color:var(--ink)}
.ladder li.no{border-style:dashed}
.ladder.three{grid-template-columns:repeat(3,1fr)}
@media (max-width:620px){.ladder,.ladder.three{grid-template-columns:1fr}}
.ltab{min-width:620px}.ltab th[scope=row] a{color:var(--ink);font-weight:600}.ltab th[scope=row] span{display:block;font:400 13px/1.4 var(--f-body);color:var(--muted);text-transform:none;letter-spacing:0}.ltab th[scope=row]{font:inherit;text-transform:none;letter-spacing:0;color:var(--ink)}.ltab td.rg{text-align:center;color:var(--rule);font-size:20px;color:#3C5A6B}.ltab td.rg.on{color:var(--cold)}.ltab td:last-child{color:inherit}.ltab .cstat{font-size:11px;padding:4px 7px}
.prod{border-top:1px solid var(--rule);padding:20px 0 8px}.prod h3{margin:0 0 4px}.prod .use{color:var(--muted);font-size:15px}
.chlog{list-style:none;padding:0}.chlog li{padding:14px 0;border-bottom:1px solid var(--rule);max-width:none}.chlog time{font:500 13px/1.6 var(--f-data);color:var(--warm);letter-spacing:.06em}
code{font:400 14px var(--f-data);color:var(--ink)}
.sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
.claimbody dl{display:grid;grid-template-columns:minmax(120px,190px) 1fr;gap:8px 18px;margin:12px 0}.claimbody dt{font:500 12px/1.6 var(--f-data);letter-spacing:.08em;text-transform:uppercase;color:var(--muted);padding-top:3px}.claimbody dd{margin:0;color:#C9DCE3}.claimbody h5{font:700 19px/1.3 var(--f-display);margin:24px 0 4px;color:var(--ink)}.claimbody ul.hist{margin:0;padding-left:18px}
@media (max-width:620px){.claimbody dl{grid-template-columns:1fr}.claimbody dd{margin-bottom:8px}}
@media (max-width:620px){.bar{flex-wrap:wrap;row-gap:4px}.bar nav{margin-left:-14px;width:calc(100% + 14px);flex-wrap:nowrap;overflow-x:auto;scrollbar-width:none}.bar nav a{padding:8px 12px;min-height:44px;white-space:nowrap}}
@media (prefers-reduced-motion:reduce){.barwave svg{animation:none}}"""


_LOGO = _WAVE = None
def load(index_text):
    global _LOGO, _WAVE
    _LOGO = re.search(r'<svg class="mark"[^>]*>.*?</svg>', index_text, re.S).group(0)
    _WAVE = re.search(r'<div class="barwave"[^>]*>.*?</svg></div>', index_text, re.S).group(0)

NAV = (("/story", "Story"), ("/safety", "Safety"), ("/research", "Research"), ("/schools", "Schools"), ("/media", "Media"))

def page(path, title, kicker, body, h1=None, desc=None, jsonld=None, crumbs=None, head_extra=""):
    """path: the page's address without the leading slash ("sources.html", "claims/c16"). desc: the search and
    link-preview description (one or two sentences). jsonld: a schema.org object or list. crumbs: [(label, url)]."""
    if _LOGO is None: raise RuntimeError("call shell19.load(index_html) first")
    url = SITE + path
    cur = "/" + path.split("/")[0].replace(".html", "")
    nav = "".join(f'<a href="{u}"' + (' aria-current="page"' if u == cur else "") + f">{n}</a>" for u, n in NAV)
    meta = ""
    if desc:
        d = html.escape(desc, quote=True)
        meta = (f'<meta name="description" content="{d}">\n<link rel="canonical" href="{url}">\n'
                f'<meta property="og:type" content="article">\n<meta property="og:site_name" content="19 Degrees">\n'
                f'<meta property="og:title" content="{html.escape(title, quote=True)}">\n<meta property="og:description" content="{d}">\n'
                f'<meta property="og:url" content="{url}">\n<meta property="og:image" content="{SITE}share/link-card.png">\n'
                f'<meta name="twitter:card" content="summary_large_image">\n')
    if crumbs:
        bl = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": n, "item": SITE + u.lstrip("/")} for i, (n, u) in enumerate(crumbs + [(title, "/" + path)])]}
        jsonld = ([jsonld] if isinstance(jsonld, dict) else list(jsonld or [])) + [bl]
    if jsonld:
        meta += '<script type="application/ld+json">' + json.dumps(jsonld, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/") + "</script>\n"
    trail = ""
    if crumbs:
        trail = '<nav class="crumbs" aria-label="Breadcrumb">' + " › ".join(f'<a href="{u}">{html.escape(n)}</a>' for n, u in crumbs) + "</nav>\n  "
    return f"""<!doctype html>
<html lang="en-US">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)} · 19 Degrees</title>
{meta}<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="stylesheet" href="/fonts/fonts.css">
<style>
{CSS}
</style>
{head_extra}</head>
<body>
<div class="bar">
  <a class="lockup" href="/" aria-label="19 Degrees, home">{_LOGO}</a>
  <nav aria-label="Site"><a href="/">Home</a>{nav}</nav>
  {_WAVE}
</div>
<main>
  {trail}<div class="kicker">{kicker}</div>
  <h1>{html.escape(h1 or title)}</h1>
{body}
  <p class="foot">© 2026 19 Degrees · <a href="/">Home</a> · <a href="/sources.html">Sources</a> · <a href="/open-data">Open data</a> · <a href="/changes">Changes</a> · <a href="/legal.html">Legal</a> · <a href="/privacy.html">Privacy</a></p>
</main>
</body>
</html>
"""
