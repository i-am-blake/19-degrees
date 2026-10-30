"""Claim C19 (hot spells): do shark bites cluster in unusually warm months?
Usage: python3 -I heat19.py <asid.csv> <sst_dir> [heat.json]
Each unprovoked bite's month is ranked by sea temperature (HadISST, the page's regional series) against the same calendar
month in the 10 years either side, on the same stretch of coast, so long-term warming is taken out. With no link, a tenth
of bites would fall in the warmest tenth of months. Writes heat.json beside this script; build19.py adds it as D.heat."""
import csv, json, math, os, sys, collections
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
from regions import REGIONS, region_of
asid, sdir = sys.argv[1:3]; out = sys.argv[3] if len(sys.argv) > 3 else os.path.join(here, "heat.json")
sst = {}
for name, *_ in REGIONS:
    for d, v in list(csv.reader(open(os.path.join(sdir, name.replace(" ", "_").replace("&", "and") + ".csv"))))[1:]:
        sst[(name, int(d[:4]), int(d[5:7]))] = float(v)
def rank(r, y, m, w=10):
    if (r, y, m) not in sst: return None
    c = [sst[(r, yy, m)] for yy in range(y - w, y + w + 1) if yy != y and (r, yy, m) in sst]
    if len(c) < 10: return None
    v = sst[(r, y, m)]; return (sum(x < v for x in c) + 0.5 * sum(x == v for x in c)) / len(c)
def tail(n, k, p): return sum(math.comb(n, j) * p ** j * (1 - p) ** (n - j) for j in range(k, n + 1))
R = collections.defaultdict(list)
for x in csv.DictReader(open(asid, encoding="utf-8")):
    g = {"white shark": "white", "tiger shark": "tiger", "bull shark": "bull"}.get(x["Shark.common.name"].strip().lower())
    if not g or x["Provoked/unprovoked"].strip() != "unprovoked": continue
    try: y = int(x["Incident.year"]); m = int(x["Incident.month"]); la, lo = float(x["Latitude"]), float(x["Longitude"])
    except ValueError: continue
    if y < 1900: continue
    p = rank(region_of(x["State"], la, lo), y, m)
    if p is not None: R[g].append(p)
res = {}
for g, ps in R.items():
    n = len(ps); t = sum(p >= 0.9 for p in ps); q = sum(p >= 0.75 for p in ps)
    res[g] = {"n": n, "t": t, "t_pct": round(100 * t / n), "t_p": round(tail(n, t, 0.1), 4), "q": q, "q_pct": round(100 * q / n), "q_p": round(tail(n, q, 0.25), 3)}
json.dump(res, open(out, "w"), indent=1); print(json.dumps(res))
