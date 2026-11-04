"""Claim C8: do turtle movements predict when tiger sharks arrive?
Usage: python3 -I turtles19.py <imos folder> <out turtles.json>
Uses the IMOS Animal Tracking files on the imos-data branch (green turtle and tiger shark detections, CC BY 4.0).
For every receiver installation (array) that detected both, it counts tagged animals of each kind detected per month,
and keeps months when that installation had at least one receiver logging either species. It then asks: does a rise in
turtles one month go with a rise in tiger sharks the NEXT month (turtles lead), more than the other way round (sharks lead)?
Both are counted on the same receivers, so listening effort moves both together; comparing the two directions cancels
most of that. Correlations are of month-to-month changes, pooled across installations; p from 10,000 shuffles."""
import csv, gzip, json, os, random, sys, collections

SRC, OUT = sys.argv[1:3]
def monthly(fn):
    c = collections.defaultdict(set)
    for r in csv.DictReader(gzip.open(os.path.join(SRC, fn), "rt", encoding="utf-8")):
        c[(r["installation_name"], r["date_hour_UTC"][:7])].add(r["animal_id"])
    return {k: len(v) for k, v in c.items()}
T = monthly("greenturtle_Cheloniamydas.csv.gz"); S = monthly("TigerShark_Galeocerdocuvier.csv.gz")
both = sorted({k[0] for k in T} & {k[0] for k in S})

def nxt(ym):
    y, m = int(ym[:4]), int(ym[5:7]); m += 1
    if m == 13: y, m = y + 1, 1
    return f"{y:04d}-{m:02d}"

pairs_lead, pairs_lag, n_months, sites = [], [], 0, []
for inst in both:
    # only the stretch when both kinds had tags being heard there, so a gap in one tagging program isn't read as absence
    tm = [k[1] for k in T if k[0] == inst]; sm = [k[1] for k in S if k[0] == inst]
    lo, hi = max(min(tm), min(sm)), min(max(tm), max(sm))
    months = sorted({k[1] for k in list(T) + list(S) if k[0] == inst and lo <= k[1] <= hi})
    if len(months) < 12: continue
    sites.append(inst)
    t = {m: T.get((inst, m), 0) for m in months}; s = {m: S.get((inst, m), 0) for m in months}
    dt = {m: t[nxt(m)] - t[m] for m in months if nxt(m) in t}; ds = {m: s[nxt(m)] - s[m] for m in months if nxt(m) in s}
    for m in dt:
        n_months += 1
        if nxt(m) in ds: pairs_lead.append((dt[m], ds[nxt(m)])); pairs_lag.append((ds[m], dt.get(nxt(m), 0)))

def corr(p):
    if len(p) < 3: return None
    xs, ys = zip(*p); mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    sxy = sum((x - mx) * (y - my) for x, y in p); sx = sum((x - mx) ** 2 for x in xs) ** .5; sy = sum((y - my) ** 2 for y in ys) ** .5
    return sxy / (sx * sy) if sx and sy else 0.0
r_lead, r_lag = corr(pairs_lead), corr(pairs_lag)
random.seed(8); hits = 0; N = 10000
ys = [y for _, y in pairs_lead]
for _ in range(N):
    random.shuffle(ys); hits += abs(corr(list(zip([x for x, _ in pairs_lead], ys)))) >= abs(r_lead)
out = dict(installations=len(sites), months=n_months, pairs=len(pairs_lead), turtles_lead=round(r_lead, 3) if r_lead is not None else None,
           sharks_lead=round(r_lag, 3) if r_lag is not None else None, p=round((hits + 1) / (N + 1), 3), sites=sites)
json.dump(out, open(OUT, "w"), indent=1)
print("turtles", json.dumps({k: v for k, v in out.items() if k != "sites"}))
