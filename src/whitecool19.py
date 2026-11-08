"""Claim C5: do white sharks follow the humpbacks, or the cool water that comes with them?
Usage: python3 -I whitecool19.py <scp-numbers-caught.xlsx> <hadisst gold_coast.csv> <hadisst sunshine_coast.csv> <out whitecool.json>
White sharks reach southern Queensland in winter, when humpbacks pass and the sea is coolest, so the season alone can't tell
the two apart. Two tests that can:
1. Numbers: east Australian humpbacks have grown roughly tenfold since the 1990s (Noad et al. 2019). If white sharks came for
   the whales, winter catches should have grown too. Reports the trend in catches per year (Poisson, log-linear).
2. Temperature: compares months of the same calendar month (May to November) in different years. If cool water brings
   white sharks, cooler-than-usual months (below that month's median at that place, 1996-2025) should catch more.
   Rate ratio, p-value by reshuffling within calendar months 10,000 times (two-sided).
Catches: Queensland Shark Control Program (CC BY 4.0), Gold Coast to Bundaberg. Sea temperature: HadISST (Met Office),
1° cells off the Gold Coast and the Sunshine Coast."""
import csv, json, math, random, sys
from collections import defaultdict
import openpyxl

SCP, GC, SC, OUT = sys.argv[1:5]
def sst(p):
    d = {}
    for l in open(p):
        t, _, _, v = l.strip().split(",")
        if v not in ("NaN", ""): d[(int(t[:4]), int(t[5:7]))] = float(v)
    return d
SST = {"gc": sst(GC), "sc": sst(SC)}
AREA = {"Gold Coast": "gc", "Nth Stradbroke Is.": "gc", "Bribie Island": "sc", "Sunshine Coast South": "sc",
        "Sunshine Coast North": "sc", "Rainbow Beach": "sc", "Bundaberg": "sc"}
ws = openpyxl.load_workbook(SCP, read_only=True, data_only=True)["Sheet1"]
catch = defaultdict(int); years = set()
for r in list(ws.iter_rows(values_only=True))[1:]:
    if r[3] not in AREA: continue
    y, m = int(r[0]), int(r[1]); years.add(y)
    if r[9] == "WHITE SHARK": catch[(r[3], y, m)] += r[14] or 0
Y = range(1996, 2026)

# 1. trend in winter (May-Nov) catches per year
per_year = [sum(catch.get((a, y, m), 0) for a in AREA for m in range(5, 12)) for y in Y]
def poisson_trend(ys, ns):  # log(mu) = a + b*(year-mean), Newton's method
    xb = sum(ys) / len(ys); x = [y - xb for y in ys]; a, b = math.log(max(sum(ns) / len(ns), 0.1)), 0.0
    for _ in range(50):
        mu = [math.exp(a + b * xi) for xi in x]
        g = [sum(n - m for n, m in zip(ns, mu)), sum((n - m) * xi for n, m, xi in zip(ns, mu, x))]
        h = [[sum(mu), sum(m * xi for m, xi in zip(mu, x))], [sum(m * xi for m, xi in zip(mu, x)), sum(m * xi * xi for m, xi in zip(mu, x))]]
        det = h[0][0] * h[1][1] - h[0][1] ** 2
        da = (h[1][1] * g[0] - h[0][1] * g[1]) / det; db = (h[0][0] * g[1] - h[0][1] * g[0]) / det
        a += da; b += db
    se = math.sqrt(h[0][0] / det)
    return b, se
b, se = poisson_trend(list(Y), per_year)
z = b / se; p_trend = math.erfc(abs(z) / math.sqrt(2))

# 2. cooler vs warmer months of the same calendar month
cells = defaultdict(list)  # calendar month -> [(anomaly, catch)]
for a, k in AREA.items():
    for m in range(5, 12):
        vals = [SST[k][(y, m)] for y in Y if (y, m) in SST[k]]
        med = sorted(vals)[len(vals) // 2]
        for y in Y:
            if (y, m) in SST[k]: cells[(a, m)].append((SST[k][(y, m)] - med, catch.get((a, y, m), 0)))
def ratio(st):
    c = w = nc = nw = 0
    for v in st.values():
        for an, n in v:
            if an < 0: c += n; nc += 1
            elif an > 0: w += n; nw += 1
    return (c / nc) / (w / nw), c, nc, w, nw
obs, c, nc, w, nw = ratio(cells)
random.seed(5); more = 0; R = 10000
for _ in range(R):
    sh = {k: list(zip(random.sample([an for an, _ in v], len(v)), [n for _, n in v])) for k, v in cells.items()}
    more += abs(math.log(ratio(sh)[0])) >= abs(math.log(obs)) - 1e-12
out = dict(total=sum(per_year), per_year=dict(zip(Y, per_year)), trend_pct_per_year=round(100 * (math.exp(b) - 1), 1),
           trend_p=round(p_trend, 3), first_half=sum(per_year[:15]), second_half=sum(per_year[15:]),
           cooler=dict(caught=c, months=nc, per_month=round(c / nc, 3)), warmer=dict(caught=w, months=nw, per_month=round(w / nw, 3)),
           cool_ratio=round(obs, 2), cool_p=round((more + 1) / (R + 1), 4))
json.dump(out, open(OUT, "w"), indent=1)
print("whitecool", json.dumps({k: v for k, v in out.items() if k != "per_year"}))
