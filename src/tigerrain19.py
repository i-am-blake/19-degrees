"""Claim C28, by the day: did tiger shark bites follow heavy rain in the days before?
Usage: python3 -I tigerrain19.py <ocean dir> <islands_nc_run.csv> [hawaii_incidents.csv] <out tigerrain.json>
Rain: Open-Meteo historical daily rain (ERA5; CC BY 4.0), files weather_<point>.csv in the ocean dir, at the coasts that
record the day of each bite: Hawaii (DLNR), Réunion and New Caledonia (University of Reunion Island).
For each bite, rain over the 3 days before it is ranked against the same 3-day totals at the same place within 15 days of
the same date, in the 5 years either side. With no link, a quarter of bites follow a 3-day spell in the wettest quarter.
Tiger shark bites are compared with bull shark and other bites at the same places (one-sided binomial against a quarter;
Fisher's exact test tiger vs the rest, two-sided)."""
import csv, datetime as dt, json, math, os, re, sys, unicodedata

args = sys.argv[1:]; OCEAN, ISL = args[:2]; HI = args[2] if len(args) == 4 else None; OUT = args[-1]
RAIN = {}
def rain(pt):
    if pt not in RAIN:
        p = os.path.join(OCEAN, f"weather_{pt}.csv"); d = {}
        if os.path.exists(p):
            for r in csv.DictReader(open(p)):
                if r.get("precipitation_sum") not in ("", None): d[dt.date.fromisoformat(r["date"])] = float(r["precipitation_sum"])
        RAIN[pt] = d
    return RAIN[pt]
def three(pt, d):
    s = rain(pt); xs = [s.get(d - dt.timedelta(i)) for i in (1, 2, 3)]
    return None if None in xs else sum(xs)
def rank(pt, d):
    x = three(pt, d)
    if x is None: return None
    others = []
    for y in range(d.year - 5, d.year + 6):
        try: c = d.replace(year=y)
        except ValueError: c = d.replace(year=y, day=28)
        for i in range(-15, 16):
            o = c + dt.timedelta(i)
            if o != d and (v := three(pt, o)) is not None: others.append(v)
    if len(others) < 150: return None
    return (sum(v < x for v in others) + 0.5 * sum(v == x for v in others)) / len(others)

bites = []  # (place, point, date, species)
raw = open(ISL, "rb").read().decode("utf-8", "replace").splitlines()
for r in csv.DictReader(raw, delimiter=";" if raw[0].count(";") > raw[0].count(",") else ","):
    try: d = dt.date.fromisoformat(r["DATE"])
    except ValueError: continue
    nc = r["SITE"].startswith("New")
    bites.append(("new_caledonia" if nc else "reunion", "new_caledonia_noumea" if nc else "reunion_west", d, r["SHARKTYPE"].strip().lower()))
if HI:
    norm = lambda t: re.sub(r"[^a-z ,]", "", unicodedata.normalize("NFKD", t.lower()))
    ISLES = [("kauai", "hawaii_kauai"), ("maui", "hawaii_maui"), ("molokai", "hawaii_maui"), ("lanai", "hawaii_maui"),
             ("hawaii", "hawaii_big_island"), ("oahu", "hawaii_oahu_south")]
    NORTH = ("north shore", "haleiwa", "sunset", "waimea", "pipeline", "laie", "kahuku", "mokuleia", "kaena", "makaha", "waianae", "yokohama")
    for r in csv.DictReader(open(HI, encoding="utf-8")):
        m = re.match(r"\s*(\d{4})/(\d{1,2})/(\d{1,2})", r.get("Date and Time", ""))
        if not m: continue
        try: d = dt.date(*map(int, m.groups()))
        except ValueError: continue
        loc = norm(r.get("Location", "")); pt = next((p for name, p in ISLES if name in loc.split(",")[0] or loc.startswith(name)), None)
        if pt == "hawaii_oahu_south" and any(w in loc for w in NORTH): pt = "hawaii_oahu_north"
        if pt: bites.append(("hawaii", pt, d, "tiger" if "tiger" in r.get("Shark", "").lower() else "other"))

def binom_ge(k, n, p=0.25):
    return round(sum(math.comb(n, x) * p ** x * (1 - p) ** (n - x) for x in range(k, n + 1)), 3)
def fisher(a, b, c, d):
    n, r1, c1 = a + b + c + d, a + b, a + c
    p = lambda x: math.comb(r1, x) * math.comb(n - r1, c1 - x) / math.comb(n, c1)
    p0 = p(a); lo, hi = max(0, c1 - (n - r1)), min(r1, c1)
    return round(min(1.0, sum(p(x) for x in range(lo, hi + 1) if p(x) <= p0 * (1 + 1e-9))), 3)

ranked = [(pl, sp, rk) for pl, pt, d, sp in bites if (rk := rank(pt, d)) is not None]
def summ(sel):
    n = len(sel); k = sum(r >= 0.75 for r in sel)
    return dict(n=n, wettest_quarter=k, pct=round(100 * k / n) if n else None, p=binom_ge(k, n) if n else None)
out = {}
for pl in ("hawaii", "reunion", "new_caledonia", "all"):
    sel = [x for x in ranked if pl in ("all", x[0])]
    t = [r for _, sp, r in sel if sp == "tiger"]; b = [r for _, sp, r in sel if sp == "bull"]; o = [r for _, sp, r in sel if sp not in ("tiger", "bull")]
    out[pl] = dict(tiger=summ(t), bull=summ(b), other=summ(o))
    rest = b + o
    if t and rest:
        tk, rk_ = sum(r >= 0.75 for r in t), sum(r >= 0.75 for r in rest)
        out[pl]["tiger_vs_rest_p"] = fisher(tk, len(t) - tk, rk_, len(rest) - rk_)
json.dump(out, open(OUT, "w"), indent=1)
print("tigerrain", json.dumps(out))
