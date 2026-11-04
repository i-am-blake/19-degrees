"""Claim C26: do Western Australia's shark bites come more often when the Indian Ocean Dipole is positive?
Usage: python3 -I iod19.py <asid.csv> <iod_dmi_hadisst.txt> <out iod.json>
The Dipole Mode Index (NOAA PSL, from HadISST) is the Indian Ocean's El Niño: positive means cooler water off Indonesia
and Western Australia and drier springs in southern Australia; negative the reverse. A month counts as positive at
+0.4 or above and negative at -0.4 or below. Each unprovoked WA bite since 1950 is compared with the same calendar
month in the same decade (the decade's other years), so the season and long-term trends in both bites and the index
cancel out. Expected counts and a permutation p-value (each bite's year reshuffled within its decade, 20,000 times)."""
import csv, json, random, sys

ASID, IODF, OUT = sys.argv[1:4]
iod = {}
for line in open(IODF).read().splitlines()[1:]:
    p = line.split()
    if len(p) == 13 and p[0].isdigit():
        for m, v in enumerate(p[1:], 1):
            if float(v) > -99: iod[(int(p[0]), m)] = float(v)
last = max(iod)

def sp(x):
    n = x["Shark.common.name"].lower()
    return "bull" if "bull" in n else "white" if "white" in n else "tiger" if "tiger" in n else "other"

bites = []
for x in csv.DictReader(open(ASID, encoding="utf-8")):
    if x["State"].strip() != "WA" or x["Provoked/unprovoked"].strip() != "unprovoked": continue
    if not x["Incident.month"].strip() or not x["Incident.year"].isdigit(): continue
    y, m = int(x["Incident.year"]), int(x["Incident.month"])
    if y >= 1950 and (y, m) in iod: bites.append((y, m, sp(x)))

def pool(y, m):
    d = y // 10 * 10
    return [yy for yy in range(d, d + 10) if (yy, m) in iod]

def stats(sel):
    k_pos = sum(iod[(y, m)] >= 0.4 for y, m, _ in sel); k_neg = sum(iod[(y, m)] <= -0.4 for y, m, _ in sel)
    e_pos = sum(sum(iod[(yy, m)] >= 0.4 for yy in pool(y, m)) / len(pool(y, m)) for y, m, _ in sel)
    e_neg = sum(sum(iod[(yy, m)] <= -0.4 for yy in pool(y, m)) / len(pool(y, m)) for y, m, _ in sel)
    random.seed(26); hits = 0; N = 20000
    for _ in range(N):
        sim = sum(iod[(random.choice(pool(y, m)), m)] >= 0.4 for y, m, _ in sel)
        hits += abs(sim - e_pos) >= abs(k_pos - e_pos) - 1e-9
    return dict(n=len(sel), pos=k_pos, pos_exp=round(e_pos, 1), neg=k_neg, neg_exp=round(e_neg, 1),
                ratio=round(k_pos / e_pos, 2) if e_pos else None, p=round((hits + 1) / (N + 1), 3))

out = {"last": f"{last[0]}-{last[1]:02d}", "all": stats(bites)}
for s in ("white", "bull", "tiger"):
    sel = [b for b in bites if b[2] == s]
    if len(sel) >= 8: out[s] = stats(sel)
early = [b for b in bites if b[0] < 1990]; late = [b for b in bites if b[0] >= 1990]
out["before1990"] = stats(early) if early else None; out["since1990"] = stats(late)
json.dump(out, open(OUT, "w"), indent=1)
print("iod", json.dumps(out))
