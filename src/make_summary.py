"""One-page funder summary (print HTML) built from the live index.html counts; render to PDF with
headless Chrome (make_site.py does this every build). Usage: python3 -I make_summary.py <index.html> <out.html> [fonts.css href]"""
import re, sys
src, out = sys.argv[1:3]
FONTS = sys.argv[3] if len(sys.argv) > 3 else "fonts/fonts.css"
t = open(src, encoding="utf-8").read()
logo = re.search(r'<svg class="mark"[^>]*>.*?</svg>', t, re.S).group(0)
def tile(label):
    m = re.search(r'<span class="lab">' + label + r'</span><span class="big"[^>]*>(\d+)<', t)
    return m.group(1) if m else "?"
m_open = re.search(r"Pick one of the (?:<[^>]+>)?(\d+)", t)
m_done = re.search(r'(\d+) / (\d+)</span> claims with a first look or a result', t)
n_claims, n_sources, n_products = tile("Testable claims"), tile("Data sources joined"), tile("Products checked")
n_open = m_open.group(1) if m_open else "?"
n_done = m_done.group(1) if m_done else "?"
m_wait = re.search(r'(\d+) / \d+</span> claims waiting for data', t)
n_wait = m_wait.group(1) if m_wait else "?"
pct = round(100 * int(n_done) / int(n_claims)) if n_done.isdigit() and n_claims.isdigit() else 0
OPPS = [("Fund a claim", f"{n_wait} claims are waiting for data or a test. Each is tested in the open, with the method set before the result is known."),
        ("Open a dataset", "Fund the request, license or cleaning that makes a closed dataset usable for everyone."),
        ("Sponsor the schools program", "Free classroom sheets for three age ranges, tested with teachers."),
        ("Underwrite independent review", "Qualified scientists check methods and results, and mistakes are published.")]
html = f"""<!doctype html><html lang="en-US"><head><meta charset="utf-8"><title>19 Degrees · Funder summary</title>
<link rel="stylesheet" href="{FONTS}">
<style>@page{{size:Letter;margin:0}}*{{box-sizing:border-box}}
body{{margin:0;font:400 9.6pt/1.38 "Figtree",system-ui,sans-serif;color:#0B2C46;-webkit-print-color-adjust:exact;print-color-adjust:exact}}
.sheet{{width:8.5in;height:11in;padding:.5in .65in;display:flex;flex-direction:column;gap:8.5pt;background:#FBF8F2}}
.top{{display:flex;align-items:center;justify-content:space-between;background:#0F5677;margin:-.5in -.65in 0;padding:.2in .65in;color:#fff}}
.top .mark{{height:28pt;width:auto;color:#fff}}.top span{{font:500 9pt/1.3 "Martian Mono",monospace;letter-spacing:.14em;text-transform:uppercase;color:#F0A04B}}
h1{{font:800 21pt/1.08 "Bricolage Grotesque",sans-serif;margin:6pt 0 0;letter-spacing:-.01em;text-wrap:balance}}
h2{{font:700 12pt/1.2 "Bricolage Grotesque",sans-serif;margin:0 0 2pt}}p{{margin:0}}
.lead{{font-size:10.4pt}}
.goal .track{{height:9pt;background:#E1E8EC;margin:4pt 0 0}}.goal .fill{{height:100%;background:#F0A04B}}
.stats{{display:grid;grid-template-columns:repeat(4,1fr);gap:8pt}}.stats div{{border:1pt solid #C9D6DD;padding:6pt 9pt}}
.stats b{{display:block;font:800 17pt/1 "Bricolage Grotesque",sans-serif}}.stats span{{font:500 7.5pt/1.3 "Martian Mono",monospace;letter-spacing:.04em;line-height:1.25;text-transform:uppercase;color:#4A6A7C;display:block;margin-top:3pt}}
.opps{{display:grid;grid-template-columns:1fr 1fr;gap:8pt}}.opps div{{border-left:3pt solid #F0A04B;padding:2pt 0 2pt 9pt}}.opps b{{display:block}}
ul{{margin:0;padding-left:14pt}}li{{margin:1pt 0}}
.foot{{margin-top:auto;border-top:1pt solid #C9D6DD;padding-top:8pt;display:flex;justify-content:space-between;gap:20pt;font-size:10pt;color:#4A6A7C}}
.foot b{{color:#0B2C46}}</style></head><body><div class="sheet">
<div class="top">{logo}<span>Funder summary</span></div>
<h1>Give every coast answers built on evidence, not fear.</h1>
<p class="lead">As the ocean warms, the places and seasons where people and sharks meet are shifting. Councils are choosing safety measures, families are deciding where to swim, and scientists are racing to keep up, often without the data to know what works. 19 Degrees, an independent and open project, tests those questions in public and publishes every answer, including the surprising ones.</p>
<div class="goal"><b>The goal: an answer for every claim.</b> {n_done} of {n_claims} have a first look or a result. <span style="white-space:nowrap">Help answer the next {n_wait}.</span><div class="track"><div class="fill" style="width:{pct}%"></div></div></div>
<div class="stats"><div><b>Open</b><span>Code, data and methods</span></div><div><b>{n_sources}</b><span>Data sources joined</span></div><div><b>{n_products}</b><span>Safety products checked</span></div><div><b>Weekly</b><span>Data updates</span></div></div>
<div><h2>Why it matters now</h2><p>Shark and ocean-temperature research sits in datasets that rarely meet. As the water warms, where and when people and sharks overlap is changing faster than any one study can follow. 19 Degrees joins the evidence in one open place. Code is open source (MIT); content is reusable with credit (CC BY 4.0).</p></div>
<div><h2>Why this exists</h2><p>Blake Erickson is a freediver and surfer who has been obsessed with sharks since he was a little kid. He started 19 Degrees to give back to the ocean: an honest, open picture of how a warming sea is changing life for people and sharks.</p></div>
<div><h2>What you can fund</h2><div class="opps">""" + "".join(f"<div><b>{h}</b>{d}</div>" for h, d in OPPS) + """</div></div>
<div><h2>Independence policy</h2><ul>
<li>Funders get no say over methods, results, grades or wording.</li>
<li>Any funder's product or position is tested and graded like everyone else's.</li>
<li>Thanks, never influence: supporters named if they choose; claim sponsors credited on the claim; project partners listed, with a report when the work is done.</li>
<li>Neutral on contested measures such as nets and drumlines.</li></ul></div>
<div><h2>Status</h2><p>An independent project, not a registered charity; contributions are not tax-deductible. Open to working with a fiscal sponsor.</p></div>
<div class="foot"><div><b>19-degrees.org/funders</b><br>Contact form: choose "Funding or partnership"</div><div style="text-align:right"><b>ko-fi.com/19degrees</b><br>Give any amount</div></div>
</div></body></html>"""
open(out, "w", encoding="utf-8").write(html)
print("summary:", out)
