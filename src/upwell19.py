"""Claim C29: does cold upwelling bring white sharks close to California's beaches?
Usage: python3 -I upwell19.py <cuti_daily.csv[.gz]> <CDFW SharkIncidents xlsx> <out upwelling.json>
Upwelling: NOAA's Coastal Upwelling Transport Index (CUTI; Jacox et al. 2018), daily, by degree of latitude, 1988 on; free
to use and redistribute. Strong upwelling brings cold, nutrient-rich water (and the food chain that follows) to the coast.
Ryan et al. (2019) found Australian white shark bites where the sea was cooler than its surroundings.
For each white shark incident since 1988, mean upwelling over the 7 days before it at the nearest whole degree of latitude
is ranked against the same 7-day means at that latitude within 15 days of the same date, in the 5 years either side. With
no link, a quarter of incidents follow a week in the strongest-upwelling quarter. One-sided binomial test against a quarter;
the weakest quarter is reported too."""
import csv, datetime as dt, gzip, json, math, sys
from collections import defaultdict
import openpyxl

CUTI, CA, OUT = sys.argv[1:4]
op = gzip.open if CUTI.endswith(".gz") else open
up = defaultdict(dict)  # lat -> date -> value
with op(CUTI, "rt") as f:
    rows = list(csv.reader(f))
head = rows[0]; it, il, iv = head.index("time"), head.index("latitude"), head.index("CUTI")
for r in rows[2:]:
    try: up[round(float(r[il]))][dt.date.fromisoformat(r[it][:10])] = float(r[iv])
    except ValueError: pass

def week(lat, d):
    xs = [up[lat].get(d - dt.timedelta(i)) for i in range(1, 8)]
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if len(xs) >= 5 else None
def rank(lat, d):
    x = week(lat, d)
    if x is None: return None
    others = []
    for y in range(d.year - 5, d.year + 6):
        try: c = d.replace(year=y)
        except ValueError: c = d.replace(year=y, day=28)
        for i in range(-15, 16):
            o = c + dt.timedelta(i)
            if o != d and (v := week(lat, o)) is not None: others.append(v)
    if len(others) < 150: return None
    return (sum(v < x for v in others) + 0.5 * sum(v == x for v in others)) / len(others)

ws = openpyxl.load_workbook(CA, read_only=True, data_only=True)["Attacks_1950_2021"]
rows = list(ws.iter_rows(values_only=True)); ix = {k: i for i, k in enumerate(rows[0])}
rs = []
for r in rows[1:]:
    d, lat, sp = r[ix["Date"]], r[ix["Latitude"]], r[ix["Species"]]
    if not (hasattr(d, "year") and lat and sp and str(sp).strip().lower() == "white" and d.year >= 1988): continue
    L = min(max(round(float(lat)), 31), 47)
    if (k := rank(L, d.date())) is not None: rs.append(k)

def binom_ge(k, n, p=0.25):
    return round(sum(math.comb(n, x) * p ** x * (1 - p) ** (n - x) for x in range(k, n + 1)), 3)
n = len(rs); hi = sum(x >= 0.75 for x in rs); lo = sum(x < 0.25 for x in rs)
out = dict(n=n, strongest_quarter=hi, strongest_pct=round(100 * hi / n), p=binom_ge(hi, n), weakest_quarter=lo, weakest_pct=round(100 * lo / n),
           p_weak=binom_ge(lo, n), mean_rank=round(sum(rs) / n, 2))
json.dump(out, open(OUT, "w"), indent=1)
print("upwelling", json.dumps(out))
