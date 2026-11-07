"""Claims C4 and C17: were Australian bites in months when the coastal water was greener (more plankton, more baitfish) than usual?
Usage: python3 -I chl19.py <asid.csv> <chlorophyll_regions.csv> <out chlorophyll.json>
Chlorophyll: NASA MODIS Aqua monthly chlorophyll-a, 2003-2022, in a 0.3° box at each region's sea point (NASA open data).
Each unprovoked bite from 2003 to 2022 goes to the nearest region in its state (within 300 km). Its month's chlorophyll
(mean of log values over the box) is ranked against the same month in the other years at that region. With no link,
a quarter of bites fall in the greenest quarter. One-sided binomial test against a quarter, by species."""
import csv, json, math, sys
from collections import defaultdict
sys.path.insert(0, __file__.rsplit("/", 1)[0] if "/" in __file__ else ".")
from regions import REGIONS

ASID, CHL, OUT = sys.argv[1:4]
v = defaultdict(list)
for r in csv.DictReader(open(CHL)):
    try: c = float(r["chlorophyll"])
    except ValueError: continue
    if c > 0: v[(r["region"], int(r["time"][:4]), int(r["time"][5:7]))].append(math.log10(c))
mean = {k: sum(x) / len(x) for k, x in v.items()}

def km(a, b):
    p = math.pi / 180
    return 6371 * math.acos(min(1, math.sin(a[0] * p) * math.sin(b[0] * p) + math.cos(a[0] * p) * math.cos(b[0] * p) * math.cos((a[1] - b[1]) * p)))

def binom_ge(k, n, p=0.25):
    return round(sum(math.comb(n, x) * p ** x * (1 - p) ** (n - x) for x in range(k, n + 1)), 3)

ranks = defaultdict(list)
for r in csv.DictReader(open(ASID, encoding="utf-8", errors="replace")):
    try: y, m, la, lo = int(r["Incident.year"]), int(r["Incident.month"]), float(r["Latitude"]), float(r["Longitude"])
    except ValueError: continue
    if not 2003 <= y <= 2022 or r["Provoked/unprovoked"].strip().lower() != "unprovoked": continue
    cand = [(km((la, lo), (rla, rlo)), name) for name, _, st, rla, rlo in REGIONS if st == r["State"].strip().upper()]
    if not cand: continue
    d, reg = min(cand)
    if d > 300 or (reg, y, m) not in mean: continue
    others = [mean[(reg, yy, m)] for yy in range(2003, 2023) if yy != y and (reg, yy, m) in mean]
    if len(others) < 8: continue
    x = mean[(reg, y, m)]; rk = (sum(o < x for o in others) + 0.5 * sum(o == x for o in others)) / len(others)
    sp = r["Shark.common.name"].strip().lower()
    for g in ("all", "bull" if "bull" in sp else "white" if "white" in sp else "tiger" if "tiger" in sp else "other"):
        ranks[g].append(rk)

out = {g: dict(n=len(rs), greenest_quarter=(k := sum(x >= 0.75 for x in rs)), pct=round(100 * k / len(rs)), mean_rank=round(sum(rs) / len(rs), 2), p=binom_ge(k, len(rs)))
       for g, rs in ranks.items() if rs}
json.dump(out, open(OUT, "w"), indent=1)
print("chlorophyll", json.dumps(out))
