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
# Link preview (1200 x 630): a giant 19 sinking into a wave, with a shark fin where the degree sign would be.
FIN = ('<path d="M0,410 C100,384 200,384 300,404 S500,436 600,410 S800,378 900,400 S1100,436 1200,404 L1200,630 L0,630Z" fill="#0A3552" opacity=".92"/>'
       '<path d="M0,410 C100,384 200,384 300,404 S500,436 600,410 S800,378 900,400 S1100,436 1200,404" fill="none" stroke="#E8F6FC" stroke-width="4" stroke-linecap="round" opacity=".9"/>'
       '<path d="M0,436 C120,418 220,420 330,434 S520,456 620,438 S820,414 930,430 S1110,452 1200,432" fill="none" stroke="#E8F6FC" stroke-width="2" opacity=".35"/>'
       '<path d="M0,410 C100,384 200,384 300,404 S500,436 600,410 S800,378 900,400 S1100,436 1200,404 L1200,418 C1100,446 1000,414 900,412 S700,436 600,422 S400,414 300,416 S100,394 0,422Z" fill="#E8F6FC" opacity=".12"/>'
       '<g transform="translate(846,58) scale(.62)"><path d="M0,150 C30,110 70,40 120,0 C126,-4 132,0 130,8 C120,60 122,110 140,150Z" fill="#0B1D27"/>'
       '<path d="M-40,150 C30,138 120,162 200,150" stroke="#E8F6FC" stroke-width="6" fill="none" stroke-linecap="round"/>'
       '<path d="M-80,170 C10,160 150,180 250,168" stroke="#E8F6FC" stroke-width="4" fill="none" stroke-linecap="round" opacity=".55"/>'
       '<path d="M-110,190 C0,182 170,198 290,188" stroke="#E8F6FC" stroke-width="3" fill="none" stroke-linecap="round" opacity=".28"/></g>'
       '<filter id="grain"><feTurbulence type="fractalNoise" baseFrequency=".85" numOctaves="2" seed="5"/><feColorMatrix values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0 0 0 .06 0"/></filter>'
       '<rect width="1200" height="630" filter="url(#grain)"/>')
cards_html["link-card.png"] = (1200, 630, f"""<style>body{{margin:0;width:1200px;height:630px;overflow:hidden;background:radial-gradient(ellipse at 50% 28%,#2C8DB8 0,#16628A 50%,#0A3552 100%)}}
.big{{position:absolute;left:250px;top:-40px;font-family:'Bricolage Grotesque';font-weight:800;font-size:560px;line-height:1;letter-spacing:-.06em;color:#F4EFE4}}
.st{{position:absolute;left:0;right:0;bottom:44px;text-align:center;font-family:'Bricolage Grotesque';font-weight:800;font-size:42px;letter-spacing:-.03em;color:#fff;margin:0}}.st span{{color:#FFC27A}}</style>
<div class="big">19</div><svg width="1200" height="630" style="position:absolute;inset:0">{FIN}</svg>
<p class="st">A warming ocean is redrawing <span>where sharks and people meet.</span></p>""")

# Load the page fonts by file too, so cards render the same wherever Chromium doesn't pick up installed .woff fonts
_fd = next((d for d in (os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "fonts"), os.path.expanduser("~/.local/share/fonts"))
            if os.path.exists(os.path.join(d, "bricolage.woff"))), None)
FONTFACE = "" if not _fd else "<style>" + "".join(
    f"@font-face{{font-family:'{n}';{w}src:local('{n}'),url(file://{os.path.abspath(os.path.join(_fd, f))})}}"
    for n, w, f in (("Bricolage Grotesque", "font-weight:800;", "bricolage.woff"), ("Figtree", "", "figtree.woff"), ("Martian Mono", "", "martian-mono.woff"))) + "</style>"
# Designed images in share_static/ (the link preview and its other formats) are published as they are, in place of drawn ones
import shutil
STATIC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "share_static")
for f in (sorted(os.listdir(STATIC)) if os.path.isdir(STATIC) else []):
    shutil.copy(os.path.join(STATIC, f), os.path.join(outdir, f)); cards_html.pop(f, None); print("copied", f)
for name, (w, h, body) in cards_html.items():
    body = FONTFACE + body
    tmp = tempfile.NamedTemporaryFile("w", suffix=".html", delete=False); tmp.write('<!doctype html><meta charset="utf-8">' + body); tmp.close()
    out = os.path.abspath(os.path.join(outdir, name))
    js = f"""const {{chromium}}=require('playwright');(async()=>{{const b=await chromium.launch();const p=await b.newPage({{viewport:{{width:{w},height:{h}}}}});
await p.goto('file://{tmp.name}');await p.evaluate(()=>document.fonts.ready);await p.waitForTimeout(300);await p.screenshot({{path:'{out}'}});await b.close();}})();"""
    subprocess.run(["node", "-e", js], check=True)
    os.unlink(tmp.name); print("wrote", out)
