"""Claim C6, water quality version: were NSW bites in months when the nearby water was dirtier than usual?
Usage: python3 -I beach19.py <asid.csv> <beachwatch_enterococci.csv[.gz]> <out beachwatch.json>
Beachwatch (NSW Government, CC BY) tests beaches for enterococci, gut bacteria that rise when stormwater and sewage
overflow wash into the sea after rain: a direct sign that a runoff plume reached that beach.
For each NSW bite since 1992 with a Beachwatch site within 5 km, the bite month's bacteria level there (geometric mean of
that month's samples, averaged over the nearby sites) is ranked against the same calendar month in the 10 years either
side at the same sites. With no link, ranks are spread evenly: a quarter fall in the dirtiest quarter. The bite database
gives the month only, so this is a monthly test. One-sided binomial test against one quarter; mean rank also reported."""
import csv, gzip, json, math, sys
from collections import defaultdict

ASID, BW, OUT = sys.argv[1:4]
op = gzip.open if BW.endswith(".gz") else open
sites, month = {}, defaultdict(list)  # site -> (lat, lon); (site, year, month) -> log10 counts
with op(BW, "rt") as f:
    for r in csv.DictReader(f):
        try:
            v = float(r["enterococci_cfu_100ml"]); y, m = int(r["date"][:4]), int(r["date"][5:7])
            sites[r["swim_site"]] = (float(r["latitude"]), float(r["longitude"]))
        except (ValueError, KeyError): continue
        month[(r["swim_site"], y, m)].append(math.log10(max(v, 1)))
gm = {k: sum(v) / len(v) for k, v in month.items()}

def km(a, b):
    p = math.pi / 180
    return 6371 * math.acos(min(1, math.sin(a[0] * p) * math.sin(b[0] * p) + math.cos(a[0] * p) * math.cos(b[0] * p) * math.cos((a[1] - b[1]) * p)))

def level(near, y, m):
    v = [gm[(s, y, m)] for s in near if (s, y, m) in gm]
    return sum(v) / len(v) if v else None

def binom_ge(k, n, p):
    return round(sum(math.comb(n, x) * p ** x * (1 - p) ** (n - x) for x in range(k, n + 1)), 3)

res = defaultdict(list)
for r in csv.DictReader(open(ASID, encoding="utf-8", errors="replace")):
    try:
        y, m, lat, lon = int(r["Incident.year"]), int(r["Incident.month"]), float(r["Latitude"]), float(r["Longitude"])
    except ValueError: continue
    if r["State"].strip().upper() != "NSW" or y < 1992 or r["Provoked/unprovoked"].strip().lower() != "unprovoked": continue
    near = [s for s, ll in sites.items() if km((lat, lon), ll) <= 5]
    x = level(near, y, m) if near else None
    if x is None: continue
    others = [v for yy in range(y - 10, y + 11) if yy != y and (v := level(near, yy, m)) is not None]
    if len(others) < 5: continue
    rank = (sum(o < x for o in others) + 0.5 * sum(o == x for o in others)) / len(others)
    sp = r["Shark.common.name"].strip().lower()
    for g in ("all", "bull shark" if "bull" in sp else "white shark" if "white" in sp else "other"):
        res[g].append(rank)

out = {}
for g, ranks in res.items():
    n = len(ranks); k = sum(x >= 0.75 for x in ranks)
    out[g.replace(" shark", "")] = dict(n=n, dirtiest_quarter=k, pct=round(100 * k / n), mean_rank=round(sum(ranks) / n, 2), p=binom_ge(k, n, 0.25))
out["sites"] = len(sites)
json.dump(out, open(OUT, "w"), indent=1)
print("beachwatch", json.dumps(out))
