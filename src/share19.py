"""Render the 19 Degrees share images from the built page's data.
Usage: python3 -I share19.py <19-degrees.html> <out_dir>   (needs Playwright + the page fonts installed locally)
Writes four 1080 x 1350 cards (Instagram, LinkedIn, Facebook), one per finding, and a 1200 x 630 link card:
  card-1-line.png, card-2-beaches.png, card-3-not-more-sharks.png, card-4-2050.png, link-card.png"""
import sys, re, json, subprocess, tempfile, os
page, outdir = sys.argv[1:3]
os.makedirs(outdir, exist_ok=True)
d = json.loads(re.search(r'id="n19-data">(.*?)</script>', open(page).read(), re.S).group(1))
syd = next(b for b in d["beaches"] if b["key"] == "sydney")
bull = d["species"]["bull"]
O = d["bull_open"]["aus"]["eras"]; E = d["bull_open"]["eras"]
pct = lambda e: round(e[1] / e[0] * 100)
A = d["ahead"]["east"]; sydA = next(b for b in A["beaches"] if b["name"] == "Sydney")
W = ["zero","one","two","three","four","five","six","seven","eight","nine","ten","eleven","twelve"]
words = lambda n: W[round(n)]
last = d["asid_last"]
logo = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo_shark19.svg")).read()
SRC = f"Australian Shark-Incident Database, 1900 to {['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][last['month']-1]} {last['year']} · HadISST sea temperature"
CSS = """body{margin:0;color:#E8F1F2;font-family:Figtree,sans-serif;overflow:hidden;background:linear-gradient(180deg,#0F5677 0,#0F5677 var(--s),#0B4566 55%,#072F4D 78%,#041A2C 100%)}
.surf{position:absolute;inset:0 0 auto 0;height:var(--s);background:linear-gradient(180deg,#3395BE,#2A86AE)}
.surf svg.w{position:absolute;left:0;bottom:-1px;width:100%;height:56px}
.logo{position:absolute;color:#fff}.logo svg{width:100%;height:auto;display:block}
.k{font-family:'Martian Mono';font-size:22px;letter-spacing:.14em;text-transform:uppercase;color:#9DB7C3}
h1{font-family:'Bricolage Grotesque';font-weight:800;line-height:1;letter-spacing:-.035em;margin:0}
em{font-style:normal;color:#F5B061}.c{color:#7CC7F0}
p{line-height:1.3;margin:0}
.f{font-family:'Martian Mono';font-size:15px;letter-spacing:.04em;color:#9DB7C3;line-height:1.6}
.bar{height:44px;background:#0B2C46;position:relative;margin-top:8px}.bar i{position:absolute;left:0;top:0;bottom:0;background:#F5B061}
.row{display:grid;grid-template-columns:200px 1fr 120px;gap:20px;align-items:center;font-family:'Martian Mono';font-size:26px}
.row b{font-family:'Bricolage Grotesque';font-size:44px;text-align:right}"""
WAVE = '<div class="surf"><svg class="w" viewBox="0 0 1200 30" preserveAspectRatio="none"><path d="M0,14 C150,4 300,24 450,14 S750,4 900,14 1050,24 1200,12 L1200,30 L0,30 Z" fill="#0F5677"/><path d="M0,14 C150,4 300,24 450,14 S750,4 900,14 1050,24 1200,12" fill="none" stroke="rgba(255,255,255,.6)" stroke-width="3" vector-effect="non-scaling-stroke"/></svg></div>'

def card(kicker, h1, body, extra=""):
    return f"""<style>:root{{--s:305px}}body{{width:1080px;height:1350px}}{CSS}
.logo{{left:72px;top:58px;width:360px}}.p{{position:absolute;inset:360px 72px 64px 72px;display:flex;flex-direction:column;gap:30px}}
h1{{font-size:88px}}p{{font-size:36px}}</style>{WAVE}<div class="logo">{logo}</div>
<div class="p"><div class="k">{kicker}</div><h1>{h1}</h1>{extra}<p>{body}</p><div class="f" style="margin-top:auto">{SRC}<br>19 Degrees · sea temperature and shark bites in Australia</div></div>"""

bars = "".join(f'<div class="row"><span>{e[0]}–{str(e[1])[2:] if e[1] < 2026 else "now"}</span><div class="bar"><i style="width:{pct(o)}%"></i></div><b>{pct(o)}%</b></div>' for e, o in zip(E, O))
cards = {
 "card-1-line.png": card("The line", f"{bull['n']} bull shark bites. Not one below <em>19°C</em>.",
   f"Sydney's sea now stays above 19°C (66°F) {words(syd['recent'])} months a year. A century ago it was {words(syd['base'])}."),
 "card-2-beaches.png": card("Out of the rivers", "Bull shark bites have moved out of the rivers, into <em>coastal waters</em>.",
   f"Share of Australia's bull shark bites in coastal waters, not in estuaries, harbors or rivers: {O[0][1]} of {O[0][0]} before 1960, {O[-1][1]} of {O[-1][0]} since 2015.",
   f'<div style="display:grid;gap:18px">{bars}</div>'),
 "card-3-not-more-sharks.png": card("It isn't more sharks", "Oceanic sharks are down <em>71%</em> since 1970.",
   f"Yet Western Australia has had more bull shark bites since 2020 ({d['wa_spike']['post']}) than in the 120 years preceding ({d['wa_spike']['pre']}). Fewer sharks, closer encounters."),
 "card-4-2050.png": card("Looking ahead", f"Sydney: <span class='c'>{sydA['now']}</span> → <em>{sydA['y2050']}</em> warm months a year by 2050.",
   f"If the sea keeps warming at its pace since 1980, the water bull sharks need would last almost all year off Sydney, and the half-year 19°C line would pass the Victorian border."),
}
cards_html = {k: (1080, 1350, v) for k, v in cards.items()}
cards_html["link-card.png"] = (1200, 630, f"""<style>:root{{--s:150px}}body{{width:1200px;height:630px}}{CSS}
.logo{{left:56px;top:34px;width:210px}}.p{{position:absolute;inset:176px 56px 40px 56px;display:flex;flex-direction:column;gap:18px}}
h1{{font-size:64px}}p{{font-size:26px;color:#C9DCE4}}
.mk{{font-family:"Martian Mono",monospace;font-size:15px;letter-spacing:.16em;text-transform:uppercase;color:#F5B061}}
.ft{{margin-top:auto;display:flex;justify-content:space-between;align-items:flex-end;font-family:"Martian Mono",monospace;font-size:17px;letter-spacing:.06em;color:#9FC3D3}}.ft b{{color:#E8F1F2;font-weight:500}}</style>{WAVE}<div class="logo">{logo}</div>
<div class="p"><div class="mk">Advancing shark and climate research worldwide</div><h1>{bull['n']} bull shark bites. Not one below <em>19°C</em>.</h1><p>The warm water bull sharks need is spreading south and lasting longer. Open data and code on a warming ocean, and on what actually keeps people safe.</p><div class="ft"><b>19-degrees.org</b><span>Free · Open source · Updated weekly</span></div></div>""")

for name, (w, h, body) in cards_html.items():
    tmp = tempfile.NamedTemporaryFile("w", suffix=".html", delete=False); tmp.write('<!doctype html><meta charset="utf-8">' + body); tmp.close()
    out = os.path.abspath(os.path.join(outdir, name))
    js = f"""const {{chromium}}=require('playwright');(async()=>{{const b=await chromium.launch();const p=await b.newPage({{viewport:{{width:{w},height:{h}}}}});
await p.goto('file://{tmp.name}');await p.evaluate(()=>document.fonts.ready);await p.waitForTimeout(300);await p.screenshot({{path:'{out}'}});await b.close();}})();"""
    subprocess.run(["node", "-e", js], check=True)
    os.unlink(tmp.name); print("wrote", out)
