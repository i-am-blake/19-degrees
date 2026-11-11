"""Press charts: three figures journalists can reuse, built from the site's own data files.

Writes press/index.html (all three charts, the numbers behind them and the credits) and,
with --png, press/*.png at 1600 x 1000 for print and web. Run from the repo root.
"""
import csv, json, os, sys, html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "press")
ORANGE, BLUE, INK, INK2, MUTED, GRID, BG = "#d9741c", "#2f7fc4", "#0b2a40", "#3d5566", "#6b7f8c", "#e3e8ec", "#fcfcfb"
W, H = 1600, 1000
L, R, T, B = 150, 70, 250, 170          # plot margins inside each figure


def rows(name):
    return list(csv.DictReader(open(os.path.join(ROOT, "data", name))))


def esc(s):
    return html.escape(str(s))


def frame(title, sub, source, body):
    """One figure: title block, plot body and source line, all inside a W x H svg."""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{esc(title)}">
<rect width="{W}" height="{H}" fill="{BG}"/>
<text x="{L}" y="92" class="t">{esc(title)}</text>
<text x="{L}" y="150" class="s">{esc(sub)}</text>
{body}
<text x="{L}" y="{H - 64}" class="src">Source: {esc(source)}</text>
<text x="{L}" y="{H - 34}" class="src">Chart: 19 Degrees, 19-degrees.org · free to use with credit (CC BY 4.0)</text>
</svg>"""


def fig_line():
    """Bite-month sea temperature, by species: bull shark bites stop at 19°C."""
    data = {}
    for r in rows("bite-temperatures.csv"):
        data.setdefault(r["species"], []).append(float(r["sea_temp_c"]))
    lo, hi = 12, 30
    x0, x1 = L + 300, W - R
    sx = lambda t: x0 + (t - lo) / (hi - lo) * (x1 - x0)
    order = [("bull", "Bull shark", ORANGE), ("tiger", "Tiger shark", BLUE), ("white", "White shark", BLUE)]
    band = (H - T - B) / 3
    out = []
    for i, (k, name, col) in enumerate(order):
        v = data[k]
        top = T + i * band
        base = top + band - 34
        counts = [sum(1 for t in v if b <= t < b + 1) for b in range(lo, hi)]
        peak = max(counts)
        h = band - 70
        for j, c in enumerate(counts):
            if not c:
                continue
            xa, xb = sx(lo + j) + 1, sx(lo + j + 1) - 1          # 2px gap between bars
            bh = c / peak * h
            out.append(f'<path d="M{xa:.1f},{base} V{base - bh + 4:.1f} Q{xa:.1f},{base - bh:.1f} {xa + 4:.1f},{base - bh:.1f} '
                       f'H{xb - 4:.1f} Q{xb:.1f},{base - bh:.1f} {xb:.1f},{base - bh + 4:.1f} V{base} Z" fill="{col}"><title>{name}: {c} bites at {lo + j}–{lo + j + 1}°C</title></path>')
        out.append(f'<line x1="{x0}" x2="{x1}" y1="{base}" y2="{base}" stroke="{GRID}" stroke-width="2"/>')
        below = sum(1 for t in v if t < 19)
        out.append(f'<text x="{L}" y="{base - 52}" class="lab">{name}</text>')
        out.append(f'<text x="{L}" y="{base - 16}" class="note">{len(v)} bites · {below} below 19°C</text>')
    for t in range(lo, hi + 1, 2):
        out.append(f'<text x="{sx(t):.1f}" y="{H - B + 36}" class="ax" text-anchor="middle">{t}°C</text>')
    xl = sx(19)
    out.append(f'<line x1="{xl:.1f}" x2="{xl:.1f}" y1="{T - 30}" y2="{H - B + 8}" stroke="{INK}" stroke-width="2" stroke-dasharray="6 6"/>')
    out.append(f'<text x="{xl + 12:.1f}" y="{T - 36}" class="lab">19°C</text>')
    nb = sum(1 for t in data["bull"] if t < 19)
    return frame(f"{len(data['bull'])} bull shark bites. {'Not one' if nb == 0 else nb} below 19°C.",
                 "Sea temperature in the month of each recorded bite in Australia, by shark species",
                 "Australian Shark-Incident Database, 1900 to June 2026 · HadISST sea temperature", "\n".join(out))


def fig_season():
    """Months a year at or above 19°C, by decade, on the NSW coast, with the 2050 outlook."""
    beaches = ["Newcastle", "Sydney", "Wollongong", "Eden"]
    shades = {"Newcastle": "#7fb0dc", "Sydney": ORANGE, "Wollongong": "#2f7fc4", "Eden": "#14456f"}
    dec = {b: [] for b in beaches}
    for r in rows("beach-seasons-by-decade.csv"):
        if r["beach"] in dec:
            dec[r["beach"]].append((int(r["decade"]) + 5, float(r["months_at_or_above_19c"])))
    out2050 = {r["beach"]: int(r["months_2050_at_recent_pace"]) for r in rows("beach-outlook-2050.csv")}
    x0, x1 = L, W - R - 240
    sx = lambda y: x0 + (y - 1900) / (2055 - 1900) * (x1 - x0)
    sy = lambda m: (H - B) - m / 12 * (H - B - T)
    out = []
    for m in range(0, 13, 3):
        out.append(f'<line x1="{x0}" x2="{x1}" y1="{sy(m):.1f}" y2="{sy(m):.1f}" stroke="{GRID}" stroke-width="1"/>')
        out.append(f'<text x="{x0 - 16}" y="{sy(m) + 8:.1f}" class="ax" text-anchor="end">{m}</text>')
    for y in range(1900, 2051, 25):
        out.append(f'<text x="{sx(y):.1f}" y="{H - B + 40}" class="ax" text-anchor="middle">{y}</text>')
    out.append(f'<text x="{x0 - 16}" y="{T - 30}" class="ax" text-anchor="end">months</text>')
    for b in beaches:
        pts = dec[b]
        col = shades[b]
        d = " ".join(f"{'M' if i == 0 else 'L'}{sx(x):.1f},{sy(m):.1f}" for i, (x, m) in enumerate(pts))
        out.append(f'<path d="{d}" fill="none" stroke="{col}" stroke-width="{4 if b == "Sydney" else 3}" stroke-linejoin="round"/>')
        lx, lm = pts[-1]
        out.append(f'<path d="M{sx(lx):.1f},{sy(lm):.1f} L{sx(2050):.1f},{sy(out2050[b]):.1f}" fill="none" stroke="{col}" stroke-width="3" stroke-dasharray="4 8" stroke-linecap="round"/>')
        out.append(f'<circle cx="{sx(lx):.1f}" cy="{sy(lm):.1f}" r="7" fill="{col}" stroke="{BG}" stroke-width="2"><title>{b}, 2020s: {lm} months</title></circle>')
        out.append(f'<circle cx="{sx(2050):.1f}" cy="{sy(out2050[b]):.1f}" r="7" fill="{BG}" stroke="{col}" stroke-width="3"><title>{b}, 2050 at the recent pace: {out2050[b]} months</title></circle>')
    # direct labels at the right, nudged apart where 2050 values coincide
    ys = {b: sy(out2050[b]) for b in beaches}
    placed = []
    for b in sorted(beaches, key=lambda b: ys[b]):
        y = ys[b]
        while any(abs(y - p) < 34 for p in placed):
            y += 34
        placed.append(y)
        out.append(f'<line x1="{sx(2050) + 20:.1f}" x2="{sx(2050) + 44:.1f}" y1="{y:.1f}" y2="{y:.1f}" stroke="{shades[b]}" stroke-width="6" stroke-linecap="round"/>')
        out.append(f'<text x="{sx(2050) + 56:.1f}" y="{y + 9:.1f}" class="lab">{b} {out2050[b]}</text>')
    syd_then = dec["Sydney"][0][1]; syd_now = dec["Sydney"][-1][1]
    out.append(f'<text x="{sx(2027):.1f}" y="{sy(0.9):.1f}" class="note" text-anchor="middle">dashed: 2050 if the</text>')
    out.append(f'<text x="{sx(2027):.1f}" y="{sy(0.25):.1f}" class="note" text-anchor="middle">1980–2025 trend holds</text>')
    return frame("Off NSW, the sea spends more of each year above 19°C",
                 f"Months a year the sea averages 19°C or warmer, by decade. Sydney: {syd_then:.0f} in the 1900s, {syd_now:.0f} in the 2020s",
                 "HadISST sea temperature, 1900–2025 · 2050 extends each beach's 1980–2025 trend", "\n".join(out))


def fig_rivers():
    """Queensland shark-control catches per month, high-river months against others."""
    q = json.load(open(os.path.join(ROOT, "src", "tigerqld.json")))
    groups = [("bull", "Bull sharks"), ("tiger", "Tiger sharks"), ("other_sharks", "All other sharks")]
    vmax = 2.4
    x0, x1 = L + 300, W - R - 120
    sx = lambda v: x0 + v / vmax * (x1 - x0)
    band = (H - T - B) / 3
    out = []
    for v in (0, 0.5, 1, 1.5, 2):
        out.append(f'<line x1="{sx(v):.1f}" x2="{sx(v):.1f}" y1="{T - 10}" y2="{H - B}" stroke="{GRID}" stroke-width="1"/>')
        out.append(f'<text x="{sx(v):.1f}" y="{H - B + 40}" class="ax" text-anchor="middle">{v:g}</text>')
    out.append(f'<text x="{x1 + 110}" y="{H - B + 40}" class="ax" text-anchor="end">a month</text>')
    for i, (k, name) in enumerate(groups):
        g = q[k]
        top = T + i * band + 10
        bh = 46
        for j, (val, col, lab) in enumerate([(g["per_month_other"], BLUE, "other months"), (g["per_month_high"], ORANGE, "rivers running high")]):
            y = top + j * (bh + 4)
            w = sx(val) - x0
            out.append(f'<path d="M{x0},{y} H{x0 + w - 4:.1f} Q{x0 + w:.1f},{y} {x0 + w:.1f},{y + 4} V{y + bh - 4} Q{x0 + w:.1f},{y + bh} {x0 + w - 4:.1f},{y + bh} H{x0} Z" fill="{col}"><title>{name}, {lab}: {val:.2f} a month</title></path>')
            out.append(f'<text x="{x0 + w + 14:.1f}" y="{y + bh / 2 + 9:.1f}" class="val">{val:.2f}</text>')
        out.append(f'<text x="{L}" y="{top + 40}" class="lab">{name}</text>')
        out.append(f'<text x="{L}" y="{top + 78}" class="note">{g["ratio"]:.2f} times as many</text>')
    # legend
    lx = L
    for col, lab in [(ORANGE, "Months when nearby rivers ran in their highest quarter"), (BLUE, "Other months, same calendar month and place")]:
        out.append(f'<rect x="{lx}" y="{T - 62}" width="22" height="22" rx="4" fill="{col}"/>')
        out.append(f'<text x="{lx + 34}" y="{T - 43}" class="note">{lab}</text>')
        lx += 720
    b = q["bull"]
    return frame(f"When rivers run high, {b['ratio']:.1f} times as many bull sharks",
                 f"Queensland shark-control catches, Gold Coast to Bundaberg, 1996–2025 ({b['caught_high'] + b['caught_other']} bull sharks); higher in {b['areas_higher']} of {b['areas_tested']} areas",
                 "Queensland Shark Control Program · Water Data Online (Bureau of Meteorology) river gauges", "\n".join(out))


CSS = """
@font-face{font-family:Bricolage;src:url(FONTS/bricolage.woff) format('woff')}
@font-face{font-family:Figtree;src:url(FONTS/figtree.woff) format('woff')}
@font-face{font-family:Martian;src:url(FONTS/martian-mono.woff) format('woff')}
svg .t{font:700 54px Bricolage,sans-serif;fill:#0b2a40;letter-spacing:-1px}
svg .s{font:400 28px Figtree,sans-serif;fill:#3d5566}
svg .lab{font:700 30px Figtree,sans-serif;fill:#0b2a40}
svg .val{font:700 28px Figtree,sans-serif;fill:#0b2a40}
svg .note{font:400 24px Figtree,sans-serif;fill:#3d5566}
svg .ax{font:400 22px Martian,monospace;fill:#6b7f8c}
svg .src{font:400 18px Martian,monospace;fill:#6b7f8c}
"""


def page(figs, fonts):
    css = CSS.replace("FONTS", fonts)
    blocks = "\n".join(f'<figure id="{k}">{svg}<figcaption><a href="{k}.png" download>Download PNG</a></figcaption></figure>' for k, svg in figs)
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>19 Degrees press charts</title><style>{css}
:root{{--bg:#fcfcfb;--ink:#0b2a40;--ink2:#3d5566;--line:#e3e8ec}}
body{{margin:0;background:var(--bg);color:var(--ink);font:400 17px/1.55 Figtree,system-ui,sans-serif}}
main{{max-width:1000px;margin:0 auto;padding:40px 16px 80px}}
h1{{font:700 40px/1.1 Bricolage,sans-serif;margin:0 0 12px}}
p{{color:var(--ink2);max-width:62ch}}
figure{{margin:40px 0 0;border:1px solid var(--line);border-radius:10px;overflow:hidden;background:#fff}}
figure svg{{display:block;width:100%;height:auto}}
figcaption{{padding:10px 16px;border-top:1px solid var(--line);font-size:15px}}
a{{color:#1d63a3}}
</style></head><body><main>
<h1>Press charts</h1>
<p>Free to use with credit: <b>19 Degrees (19-degrees.org), CC BY 4.0</b>. Each chart is built from the public data on the site, and the source sits on the chart itself. For the methods and every caveat, see the claims on <a href="https://19-degrees.org">19-degrees.org</a>.</p>
{blocks}
</main></body></html>"""


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    figs = [("bites-by-temperature", fig_line()), ("season-length-nsw", fig_season()), ("rivers-and-bull-sharks", fig_rivers())]
    open(os.path.join(OUT, "index.html"), "w").write(page(figs, "../fonts"))
    if "--png" in sys.argv:
        from playwright.sync_api import sync_playwright
        fonts = "file://" + os.path.join(ROOT, "fonts")
        with sync_playwright() as p:
            b = p.chromium.launch()
            pg = b.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
            for k, svg in figs:
                tmp = os.path.join(OUT, "_tmp.html")
                open(tmp, "w").write(f"<html><head><style>{CSS.replace('FONTS', fonts)} body{{margin:0}}</style></head><body>{svg}</body></html>")
                pg.goto("file://" + tmp)
                pg.evaluate("document.fonts.ready")
                pg.wait_for_timeout(300)
                pg.locator("svg").screenshot(path=os.path.join(OUT, f"{k}.png"))
            b.close()
            os.remove(os.path.join(OUT, "_tmp.html"))
    print("press charts written")
