"""Claim C6, river version: were NSW and Queensland bull shark bites in months when nearby rivers ran higher than usual?
Usage: python3 -I rivers19.py <asid.csv> <river_gauges.csv> <river_flow_daily.csv[.gz]> <out rivers.json>
River flow: daily mean flow at coastal gauges, Water Data Online (Bureau of Meteorology, from the NSW and Queensland water
agencies; CC BY 3.0 AU). A river in flood pushes a muddy, fresh plume out to sea; this measures the plume at its source,
along the whole coast, not just at Sydney's tested beaches.
For each unprovoked bite since 1970 with a gauge within 60 km, each nearby gauge's mean flow in the bite month is ranked
against the same month in the 15 years either side at that gauge, and the ranks averaged. With no link, a quarter of bites
fall in the highest-flow quarter. Bull sharks are compared with white sharks, which share the beaches but not the theory
(Fisher's exact test, two-sided), and each against a quarter (one-sided binomial)."""
import csv, gzip, json, math, sys
from collections import defaultdict

ASID, GAUGES, FLOW, OUT = sys.argv[1:5]
g = {r["station_no"]: (float(r["lat"]), float(r["lon"])) for r in csv.DictReader(open(GAUGES))}
op = gzip.open if FLOW.endswith(".gz") else open
acc = defaultdict(list)
with op(FLOW, "rt") as f:
    for r in csv.DictReader(f):
        try: v = float(r["flow_m3s"])
        except ValueError: continue
        if v >= 0: acc[(r["station_no"], int(r["date"][:4]), int(r["date"][5:7]))].append(v)
mflow = {k: math.log10(sum(v) / len(v) + 0.01) for k, v in acc.items() if len(v) >= 20}

def km(a, b):
    p = math.pi / 180
    return 6371 * math.acos(min(1, math.sin(a[0] * p) * math.sin(b[0] * p) + math.cos(a[0] * p) * math.cos(b[0] * p) * math.cos((a[1] - b[1]) * p)))

def binom_ge(k, n, p=0.25):
    return round(sum(math.comb(n, x) * p ** x * (1 - p) ** (n - x) for x in range(k, n + 1)), 3)

def fisher(a, b, c, d):
    n, r1, c1 = a + b + c + d, a + b, a + c
    p = lambda x: math.comb(r1, x) * math.comb(n - r1, c1 - x) / math.comb(n, c1)
    p0 = p(a); lo, hi = max(0, c1 - (n - r1)), min(r1, c1)
    return round(min(1.0, sum(p(x) for x in range(lo, hi + 1) if p(x) <= p0 * (1 + 1e-9))), 3)

ranks = defaultdict(list)
for r in csv.DictReader(open(ASID, encoding="utf-8", errors="replace")):
    try: y, m, la, lo = int(r["Incident.year"]), int(r["Incident.month"]), float(r["Latitude"]), float(r["Longitude"])
    except ValueError: continue
    if y < 1970 or r["State"].strip().upper() not in ("NSW", "QLD") or r["Provoked/unprovoked"].strip().lower() != "unprovoked": continue
    rs = []
    for s, ll in g.items():
        if km((la, lo), ll) > 60 or (s, y, m) not in mflow: continue
        others = [mflow[(s, yy, m)] for yy in range(y - 15, y + 16) if yy != y and (s, yy, m) in mflow]
        if len(others) < 8: continue
        x = mflow[(s, y, m)]; rs.append((sum(o < x for o in others) + 0.5 * sum(o == x for o in others)) / len(others))
    if not rs: continue
    rk = sum(rs) / len(rs); sp = r["Shark.common.name"].strip().lower()
    for grp in ("all", "bull" if "bull" in sp else "white" if "white" in sp else "tiger" if "tiger" in sp else "other"):
        ranks[grp].append(rk)

out = {grp: dict(n=len(v), high_quarter=(k := sum(x >= 0.75 for x in v)), pct=round(100 * k / len(v)), mean_rank=round(sum(v) / len(v), 2), p=binom_ge(k, len(v)))
       for grp, v in ranks.items() if v}
if "bull" in out and "white" in out:
    b, w = out["bull"], out["white"]
    out["bull_vs_white_p"] = fisher(b["high_quarter"], b["n"] - b["high_quarter"], w["high_quarter"], w["n"] - w["high_quarter"])
out["gauges"] = len(g)
json.dump(out, open(OUT, "w"), indent=1)
print("rivers", json.dumps(out))
