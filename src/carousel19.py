"""Build a LinkedIn document carousel (PDF, 1080 x 1350 slides) for 19 Degrees from the built page's data.
Usage: python3 -I carousel19.py <19-degrees.html> <out_dir>   (needs Playwright, Pillow and the page fonts)
Writes slide-1.png ... slide-8.png and 19-degrees-linkedin.pdf. Upload the PDF as a LinkedIn "document" post."""
import sys, re, json, subprocess, tempfile, os
from PIL import Image
page, out = sys.argv[1:3]
os.makedirs(out, exist_ok=True)
d = json.loads(re.search(r'id="n19-data">(.*?)</script>', open(page).read(), re.S).group(1))
here = os.path.dirname(os.path.abspath(__file__))
logo = open(os.path.join(here, "logo_shark19.svg")).read()
syd = next(b for b in d["beaches"] if b["key"] == "sydney"); bull = d["species"]["bull"]
O = d["bull_open"]["aus"]["eras"]; E = d["bull_open"]["eras"]; Z = d["zones"]; W = d["wa_spike"]; R = d["ratio"]
pct = lambda e: round(e[1] / e[0] * 100)
km = round((Z["line"][0] - Z["line"][-1]) * 111)
inc = round((syd["recent"] / syd["base"] - 1) * 100)

# east-coast map, dark style
C = d["coast"]
X = lambda lon: (lon - C["lon0"]) / (C["lon1"] - C["lon0"]) * C["w"]
Y = lambda lat: (C["lat0"] - lat) / (C["lat0"] - C["lat1"]) * C["h"]
vx, vy, vw, vh = X(145.5), Y(-27.5), X(157.0) - X(145.5), Y(-38.6) - Y(-27.5)
sc = vw / 200
def ln(lat, col, lab, dash=""):
    y = Y(lat)
    return (f'<line x1="{X(149.6):.1f}" x2="{vx+vw-sc*3:.1f}" y1="{y:.1f}" y2="{y:.1f}" stroke="{col}" stroke-width="{sc*1.6:.2f}" {dash}/>'
            f'<text x="{vx+vw-sc*4:.1f}" y="{y-sc*2.6:.1f}" text-anchor="end" font-size="{sc*6:.2f}" font-weight="700" fill="{col}" font-family="Martian Mono">{lab}</text>')
towns = "".join(f'<circle cx="{X(lo):.1f}" cy="{Y(la):.1f}" r="{sc*1.4:.2f}" fill="#E8F1F2"/><text x="{X(lo)-sc*4:.1f}" y="{Y(la)+sc*2.2:.1f}" text-anchor="end" font-size="{sc*5.6:.2f}" fill="#C9DCE4" font-family="Figtree">{n}</text>'
                for n, la, lo in (("Coffs Harbour", -30.3, 153.11), ("Sydney", -33.87, 151.21), ("Eden", -37.07, 149.91)))
MAP = f"""<svg viewBox="{vx:.1f} {vy:.1f} {vw:.1f} {vh:.1f}" style="width:100%;height:auto;display:block">
<rect x="{vx:.1f}" y="{vy:.1f}" width="{vw:.1f}" height="{vh:.1f}" fill="#0B2C46"/>
<path d="{C['d']}" fill="#123E5E" stroke="#8DADBD" stroke-width="{sc*0.6:.2f}" stroke-linejoin="round"/>
{ln(Z['line'][0], '#7CC7F0', '1950–79', 'stroke-dasharray="8 6"')}{ln(Z['line'][-1], '#F5B061', 'NOW')}{towns}</svg>"""

CSS = """body{margin:0;width:1080px;height:1350px;color:#E8F1F2;font-family:Figtree,sans-serif;overflow:hidden;background:linear-gradient(180deg,#0F5677 0,#0F5677 258px,#0B4566 55%,#072F4D 78%,#041A2C 100%)}
.surf{position:absolute;inset:0 0 auto 0;height:258px;background:linear-gradient(180deg,#3395BE,#2A86AE)}
.surf svg.w{position:absolute;left:0;bottom:-1px;width:100%;height:50px}
.logo{position:absolute;left:72px;top:56px;width:270px;color:#fff}.logo svg{width:100%;height:auto;display:block}
.prog{display:grid;grid-auto-flow:column;grid-auto-columns:1fr;gap:8px;margin-top:auto}.prog i{height:6px;border-radius:3px;background:rgba(232,241,242,.18)}.prog i.done{background:rgba(245,176,97,.45)}.prog i.on{background:#F5B061}
.p{position:absolute;inset:312px 72px 70px 72px;display:flex;flex-direction:column;gap:30px}
.k{font-family:'Martian Mono';font-size:22px;letter-spacing:.14em;text-transform:uppercase;color:#9DB7C3}
h1{font-family:'Bricolage Grotesque';font-weight:800;font-size:84px;line-height:1;letter-spacing:-.035em;margin:0}
em{font-style:normal;color:#F5B061}.c{color:#7CC7F0}
p{font-size:36px;line-height:1.3;margin:0;color:#DCE8ED}
.f{margin-top:18px;display:flex;justify-content:space-between;align-items:flex-end;font-family:'Martian Mono';font-size:17px;color:#9DB7C3;line-height:1.5}
.next{font-family:'Martian Mono';font-size:22px;color:#F5B061}
.big{font-family:'Bricolage Grotesque';font-weight:800;font-size:200px;line-height:.9;letter-spacing:-.04em;color:#F5B061}
.row{display:grid;grid-template-columns:190px 1fr 120px;gap:20px;align-items:center;font-family:'Martian Mono';font-size:26px}
.bar{height:44px;background:#0B2C46;position:relative}.bar i{position:absolute;left:0;top:0;bottom:0;background:#F5B061}
.row b{font-family:'Bricolage Grotesque';font-size:44px;text-align:right}
.strip{display:grid;grid-template-columns:150px repeat(12,1fr);gap:6px;align-items:center;font-family:'Martian Mono';font-size:22px}
.strip i{height:54px;background:#0B2C46}.strip i.on{background:#F5B061}
.dots{display:grid;grid-template-columns:repeat(20,1fr);gap:10px}.dots i{aspect-ratio:1;border-radius:50%;background:#F5B061}.dots i.off{background:transparent;border:2px dashed rgba(232,241,242,.28)}
.two{display:grid;grid-template-columns:300px 1fr;gap:44px;align-items:center}.stat{display:grid;gap:6px}.stat b{font-family:'Bricolage Grotesque';font-weight:800;font-size:64px;line-height:1;letter-spacing:-.02em}.stat span{font-size:26px;color:#C9DCE4;line-height:1.3}
.flag{display:inline-block;width:46px;height:30px;background:linear-gradient(#D7262E 0 50%,#F6C915 50% 100%);vertical-align:middle;margin-right:14px}"""
WAVE = '<div class="surf"><svg class="w" viewBox="0 0 1200 30" preserveAspectRatio="none"><path d="M0,14 C150,4 300,24 450,14 S750,4 900,14 1050,24 1200,12 L1200,30 L0,30 Z" fill="#0F5677"/><path d="M0,14 C150,4 300,24 450,14 S750,4 900,14 1050,24 1200,12" fill="none" stroke="rgba(255,255,255,.6)" stroke-width="3" vector-effect="non-scaling-stroke"/></svg></div>'
N = 8
def slide(i, kicker, h1, body="", visual="", foot="Swipe →"):
    return f"""<style>{CSS}</style>{WAVE}<div class="logo">{logo}</div>
<div class="p"><div class="k">{kicker}</div><h1>{h1}</h1>{visual}{f'<p>{body}</p>' if body else ''}<div class="prog" aria-hidden="true">{''.join('<i class="'+('on' if k==i else 'done' if k<i else '')+'"></i>' for k in range(1,N+1))}</div><div class="f"><span>19 Degrees · © 2026 Blake Erickson</span><span class="next">{foot}</span></div></div>"""

def months_row(label, share):
    on = [s >= 0.5 for s in share]
    order = [6, 7, 8, 9, 10, 11, 0, 1, 2, 3, 4, 5]
    return f'<div class="strip"><span>{label}</span>' + "".join(f'<i class="{"on" if on[m] else ""}"></i>' for m in order) + "</div>"
base_share = [sum(r["share"][m] * r["years"] for r in syd["rows"][:3]) / sum(r["years"] for r in syd["rows"][:3]) for m in range(12)]
now_share = [sum(r["share"][m] * r["years"] for r in syd["rows"][-2:]) / sum(r["years"] for r in syd["rows"][-2:]) for m in range(12)]
strip = f'<div style="display:grid;gap:14px">{months_row("1900s", base_share)}{months_row("now", now_share)}<div class="strip" style="color:#9DB7C3;font-size:18px"><span></span>' + "".join(f"<span style='text-align:center'>{m}</span>" for m in "JASONDJFMAMJ") + "</div></div>"
bars = "".join(f'<div class="row"><span>{e[0]}–{str(e[1])[2:] if e[1] < 2026 else "now"}</span><div class="bar"><i style="width:{pct(o)}%"></i></div><b>{pct(o)}%</b></div>' for e, o in zip(E, O))
# the twist: dots filling a bull shark outline (head first); 29% solid for the sharks left, 71% dashed for those gone
_P = [tuple(map(float, m)) for m in re.findall(r'(-?[\d.]+),(-?[\d.]+)', d["sharks"]["species"]["bull"]["shapes"][0]["d"])]
def _inside(x, y):
    c = False
    for k in range(len(_P)):
        (x1, y1), (x2, y2) = _P[k], _P[(k + 1) % len(_P)]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1: c = not c
    return c
def _grid(st, ox=0.0, oy=0.0):
    return [(x, y) for y in [oy + i * st + st / 2 for i in range(int(64 / st) + 1)] for x in [ox + j * st + st / 2 for j in range(int(160 / st) + 1)] if _inside(x, y)]
_st = 2.6
_g = _grid(_st, .9, .9)
_solid = set(sorted(range(len(_g)), key=lambda k: _g[k][0])[:round(len(_g) * .29)])
_r = _st * .36
dots = ('<svg viewBox="0 0 160 64" style="width:100%;height:auto;display:block">' +
        "".join(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{_r:.2f}" fill="#F5B061"/>' if k in _solid else
                f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{_r * .88:.2f}" fill="none" stroke="rgba(232,241,242,.35)" stroke-width="{_st * .07:.2f}" stroke-dasharray="{_st * .16:.2f} {_st * .12:.2f}"/>'
                for k, (x, y) in enumerate(_g)) + "</svg>")
print("shark dots:", len(_g), "solid", len(_solid))
# slide 1: every bull shark bite as a dot at its sea temperature, 1°C columns, with the 19°C line
T0, T1 = 14, 30
cnt = {}
for t in bull["t"]: cnt[int(t)] = cnt.get(int(t), 0) + 1
across = 3; mx = max(cnt.values()); rowsN = -(-mx // across)
cw, dr = 936 / (T1 - T0), 9.6
H = rowsN * dr * 2.15 + 70
xs = lambda t: (t - T0) * cw
circ = "".join(f'<circle cx="{xs(b) + (k % across + .5) * cw / across:.1f}" cy="{H - 52 - (k // across + .5) * dr * 2.15:.1f}" r="{dr:.1f}" fill="#F5B061"/>' for b, n in cnt.items() for k in range(n))
ticks = "".join(f'<text x="{xs(t):.1f}" y="{H - 14:.1f}" text-anchor="middle" font-family="Martian Mono" font-size="22" fill="#9DB7C3">{t}°</text>' for t in range(T0, T1 + 1, 2))
DOTPLOT = f"""<svg viewBox="-24 0 984 {H:.0f}" style="width:100%;height:auto;display:block">
<rect x="0" y="0" width="{xs(19):.1f}" height="{H - 46:.1f}" fill="rgba(124,199,240,.07)"/>
<text x="{xs(19) / 2:.1f}" y="{(H - 46) / 2:.1f}" text-anchor="middle" font-family="Bricolage Grotesque" font-weight="800" font-size="56" fill="#7CC7F0">0 bites</text>
<text x="{xs(19) / 2:.1f}" y="{(H - 46) / 2 + 38:.1f}" text-anchor="middle" font-family="Martian Mono" font-size="20" fill="#7CC7F0">below 19°C</text>
{circ}<line x1="{xs(19):.1f}" x2="{xs(19):.1f}" y1="0" y2="{H - 40:.1f}" stroke="#E8F1F2" stroke-width="3" stroke-dasharray="8 7"/>
<line x1="0" x2="936" y1="{H - 46:.1f}" y2="{H - 46:.1f}" stroke="rgba(232,241,242,.25)"/>{ticks}</svg>"""
safe = '<span class="flag"></span>Swim between the red and yellow flags. Stay out of murky water for a few days after heavy rain. Check the SharkSmart app.'
slides = [
 slide(1, "One rule, 126 years", f"Bull sharks have never bitten in water below <em>19°C</em>.", f"Each dot is one of {bull['n']} bites in Australia since 1900, placed at that month's sea temperature. Here's what's happening to that water.", DOTPLOT),
 slide(2, "More time", f"Off Sydney, that water now lasts <em>{inc}%</em> longer each year.", f"The sea is 19°C or warmer about {syd['recent']:.0f} months a year, up from {syd['base']:.0f} a century ago.", strip),
 slide(3, "More coastline", f"And it now reaches <em>{km}&nbsp;km</em> further down the coast.", "Where the sea stays 19°C or warmer for half the year: once near Jervis Bay, now near Eden.", f'<div style="width:330px;align-self:center">{MAP}</div>'),
 slide(4, "So the bites moved", "Out of the rivers, into <em>coastal waters</em>.", f"{pct(O[-1])}% of Australia's bull shark bites since 2015 were in coastal waters, up from {pct(O[0])}%. South of Port Macquarie, nearly half now come in autumn and winter.", f'<div style="display:grid;gap:18px">{bars}</div>'),
 slide(5, "The twist", "There are <em>71%</em> fewer sharks than in 1970.", f"Oceanic sharks and rays, worldwide. Yet since 2020, Western Australia has had more bull shark bites ({W['post']}) than in the 120 years before that combined ({W['pre']}). It isn't more sharks. It's where and when we meet them.", dots),
 slide(6, "It's not just Australia", "Ocean life is moving toward the poles <em>72 km</em> every decade.", "12 times faster than life on land. Tiger sharks off the US travel about 400 km further north for every 1°C of warming. The ocean has set a heat record nine years running."),
 slide(7, "Keep it in perspective", f"For every shark death, <em>{round(R['drown']/R['shark'])}</em> people drown.", "The biggest danger at the beach is still the water itself.<br><br>" + safe),
 slide(8, "Explore it yourself", "Free and <em>open source</em>.", "Every chart, method and number, with downloadable data and classroom sheets. Researchers: test the claims, add data and improve the methods. Link in the comments. What would you test next?", foot="Share it →"),
]
import glob
for f in glob.glob(os.path.join(out, "slide-*.png")): os.remove(f)
pngs = []
for i, body in enumerate(slides, 1):
    tmp = tempfile.NamedTemporaryFile("w", suffix=".html", delete=False); tmp.write('<!doctype html><meta charset="utf-8">' + body); tmp.close()
    png = os.path.abspath(os.path.join(out, f"slide-{i}.png"))
    js = f"""const {{chromium}}=require('playwright');(async()=>{{const b=await chromium.launch();const p=await b.newPage({{viewport:{{width:1080,height:1350}}}});
await p.goto('file://{tmp.name}');await p.evaluate(()=>document.fonts.ready);await p.waitForTimeout(250);await p.screenshot({{path:'{png}'}});await b.close();}})();"""
    subprocess.run(["node", "-e", js], check=True); os.unlink(tmp.name); pngs.append(png)
ims = [Image.open(f).convert("RGB") for f in pngs]
pdf = os.path.join(out, "19-degrees-linkedin.pdf")
ims[0].save(pdf, save_all=True, append_images=ims[1:], resolution=150)
print("wrote", len(pngs), "slides and", pdf)
