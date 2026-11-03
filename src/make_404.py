"""Build 404.html (the page GitHub Pages shows for an address that doesn't exist) from the built index.html,
reusing its logo and wave so the two always match. Usage: python3 -I make_404.py <index.html> <out 404.html>"""
import re, sys
src, out = sys.argv[1:3]
t = open(src, encoding="utf-8").read()
logo = re.search(r'<svg class="mark"[^>]*>.*?</svg>', t, re.S).group(0)
wave = re.search(r'<div class="barwave"[^>]*>.*?</svg></div>', t, re.S).group(0)
page = f"""<!doctype html>
<html lang="en-US">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Page not found · 19 Degrees</title>
<meta name="robots" content="noindex">
<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="stylesheet" href="/fonts/fonts.css">
<style>
:root{{--ink:#E8F1F2;--muted:#8DADBD;--warm:#F0A04B;--cold:#5AB4E5;--rule:rgba(232,241,242,.16);--lpad:24px;--logo-h:clamp(36px,1.25vw + 30px,46px);
  --f-display:"Bricolage Grotesque","Arial Narrow",system-ui,sans-serif;--f-body:"Figtree",system-ui,sans-serif;--f-data:"Martian Mono",ui-monospace,Menlo,monospace}}
*{{box-sizing:border-box}}
html,body{{margin:0;min-height:100%}}
body{{min-height:100vh;background:linear-gradient(180deg,#0F5677 0,#0F5677 110px,#0B4566 380px,#072F4D 700px,#031628 100%);color:var(--ink);font:400 18px/1.55 var(--f-body);-webkit-font-smoothing:antialiased}}
a{{color:inherit}}
.bar{{position:relative;background:#0F5677;padding:var(--lpad);display:flex;align-items:center;gap:12px;z-index:2}}
.lockup{{display:block;line-height:0;color:#FFFFFF}}
.lockup .mark{{height:var(--logo-h);width:auto;display:block}}
.bar nav{{margin-left:auto;display:flex;gap:4px;flex-wrap:wrap}}
.bar nav a{{font-size:15px;font-weight:600;color:#FFFFFF;text-decoration:none;border:1.5px solid transparent;padding:10px 14px;min-height:44px;display:inline-flex;align-items:center;border-radius:999px}}
.bar nav a:hover{{border-color:rgba(255,255,255,.85)}}
.barwave{{position:absolute;left:0;right:0;top:100%;height:19.5px;overflow:hidden;pointer-events:none}}
.barwave svg{{display:block;width:200%;height:19.5px;animation:ripple 6.3s linear infinite reverse}}
@keyframes ripple{{to{{transform:translateX(-50%)}}}}
main{{max-width:760px;margin:0 auto;padding:clamp(72px,12vh,140px) 24px 96px}}
.kicker{{font:500 13px/1.4 var(--f-data);letter-spacing:.16em;text-transform:uppercase;color:var(--warm);margin-bottom:16px}}
h1{{font:800 clamp(40px,7vw,72px)/1.02 var(--f-display);text-wrap:balance;letter-spacing:-.025em;margin:0 0 20px}}
p{{color:var(--muted);margin:0 0 32px;max-width:36em}}
.ctas{{display:flex;flex-wrap:wrap;gap:12px}}
.ctabtn,.ghbtn{{display:inline-flex;align-items:center;min-height:52px;padding:0 24px;border-radius:12px;font-weight:600;font-size:17px;text-decoration:none;transition:filter .15s,transform .15s,border-color .15s,background-color .15s}}
.ctabtn{{background:var(--warm);color:#0B2C46}}
.ctabtn:hover{{filter:brightness(1.08);transform:translateY(-1px)}}
.ghbtn{{border:1.5px solid rgba(232,241,242,.7);color:var(--ink)}}
.ghbtn:hover{{border-color:#3395BE;background:rgba(51,149,190,.14)}}
a:focus-visible{{outline:2px solid var(--ink);outline-offset:3px}}
@media (max-width:620px){{.bar nav{{display:none}}.ctas a{{width:100%;justify-content:center}}}}
@media (prefers-reduced-motion:reduce){{.barwave svg{{animation:none}}.ctabtn,.ghbtn{{transition:none}}}}
</style>
</head>
<body>
<div class="bar">
  <a class="lockup" href="/" aria-label="19 Degrees, home">{logo}</a>
  <nav aria-label="Sections"><a href="/">Home</a><a href="/#story">The story</a><a href="/#h-agenda">Researchers</a></nav>
  {wave}
</div>
<main>
  <div class="kicker">Page not found · 404</div>
  <h1>This page swam away.</h1>
  <p>The link may be old or mistyped.</p>
  <div class="ctas"><a class="ctabtn" href="/">Go to the home page →</a></div>
</main>
</body>
</html>
"""
open(out, "w", encoding="utf-8").write(page)
