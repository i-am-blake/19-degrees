"""Claim C28: do Queensland shark-control catches of tiger sharks rise when nearby rivers run high?
Usage: python3 -I tigerqld19.py <scp-numbers-caught.xlsx> <river_gauges.csv> <river_flow_daily.csv[.gz]> <out tigerqld.json>
Catches: Queensland Shark Control Program, numbers caught by beach, month and species, 1996 on (Queensland Government,
CC BY 4.0). River flow: Water Data Online daily flow at coastal gauges (Bureau of Meteorology, CC BY 3.0 AU), which reach
north to K'gari, so this covers the program areas from the Gold Coast to Bundaberg.
For each area and month, the flow score is the mean rank of that month's flow at gauges within 60 km of the area, against
the same month in the 15 years either side. A month is 'high flow' if its score is in the top quarter. Catches in high-flow
months are compared with catches in the other months of the same calendar month at the same area within the same 5 years,
which holds fixed the season, the gear in the water and the long-term fall in catches. Rate ratio for each species group;
p-values by reshuffling the flow scores within those groups 5,000 times (two-sided)."""
import csv, gzip, json, math, random, sys
from collections import defaultdict
import openpyxl

SCP, GAUGES, FLOW, OUT = sys.argv[1:5]
AREAS = {"Gold Coast": (-28.0, 153.43), "Nth Stradbroke Is.": (-27.43, 153.55), "Bribie Island": (-27.07, 153.20),
         "Sunshine Coast South": (-26.75, 153.13), "Sunshine Coast North": (-26.40, 153.09), "Rainbow Beach": (-25.90, 153.09),
         "Bundaberg": (-24.85, 152.42)}
GROUPS = {"tiger": ("TIGER SHARK",), "bull": ("BULL WHALER",)}

def km(a, b):
    p = math.pi / 180
    return 6371 * math.acos(min(1, math.sin(a[0] * p) * math.sin(b[0] * p) + math.cos(a[0] * p) * math.cos(b[0] * p) * math.cos((a[1] - b[1]) * p)))

g = {r["station_no"]: (float(r["lat"]), float(r["lon"])) for r in csv.DictReader(open(GAUGES))}
near = {a: {s for s, ll in g.items() if km(c, ll) <= 60} for a, c in AREAS.items()}
want = set().union(*near.values())
acc = defaultdict(list)
with (gzip.open if FLOW.endswith(".gz") else open)(FLOW, "rt") as f:
    for r in csv.DictReader(f):
        if r["station_no"] not in want: continue
        try: v = float(r["flow_m3s"])
        except ValueError: continue
        if v >= 0: acc[(r["station_no"], int(r["date"][:4]), int(r["date"][5:7]))].append(v)
mf = {k: math.log10(sum(v) / len(v) + 0.01) for k, v in acc.items() if len(v) >= 20}

def score(area, y, m):
    rs = []
    for s in near[area]:
        if (s, y, m) not in mf: continue
        o = [mf[(s, yy, m)] for yy in range(y - 15, y + 16) if yy != y and (s, yy, m) in mf]
        if len(o) < 8: continue
        x = mf[(s, y, m)]; rs.append((sum(v < x for v in o) + 0.5 * sum(v == x for v in o)) / len(o))
    return sum(rs) / len(rs) if rs else None

catch = defaultdict(lambda: defaultdict(int))  # (area, y, m) -> group -> n
ws = openpyxl.load_workbook(SCP, read_only=True, data_only=True)["Sheet1"]
for r in list(ws.iter_rows(values_only=True))[1:]:
    y, m, area, name, n = r[0], r[1], r[3], r[9], r[14] or 0
    if area not in AREAS: continue
    key = (area, int(y), int(m))
    grp = next((k for k, names in GROUPS.items() if name in names), "other sharks" if r[7] == "SHARK" else None)
    if grp: catch[key][grp] += n
    catch[key]["_any"] += 0
years = range(1996, max(k[1] for k in catch) + 1)
cells = []  # (stratum, score, counts)
for area in AREAS:
    for y in years:
        for m in range(1, 13):
            s = score(area, y, m)
            if s is None: continue
            cells.append(((area, m, (y - 1996) // 5), s, catch.get((area, y, m), {})))
strata = defaultdict(list)
for st, s, c in cells: strata[st].append((s, c))
strata = {k: v for k, v in strata.items() if len(v) >= 3}

def ratio(st, grp):
    hi = lo = nh = nl = 0
    for v in st.values():
        for s, c in v:
            if s >= 0.75: hi += c.get(grp, 0); nh += 1
            else: lo += c.get(grp, 0); nl += 1
    return (hi / nh) / (lo / nl) if nh and nl and lo else None, hi, nh, lo, nl

out = dict(areas=list(AREAS), months=sum(len(v) for v in strata.values()))
random.seed(28)
for grp in ("tiger", "bull", "other sharks"):
    obs, hi, nh, lo, nl = ratio(strata, grp)
    more = 0; R = 5000
    for _ in range(R):
        sh = {k: list(zip(random.sample([s for s, _ in v], len(v)), [c for _, c in v])) for k, v in strata.items()}
        r_ = ratio(sh, grp)[0]
        more += r_ is not None and abs(math.log(r_)) >= abs(math.log(obs)) - 1e-12
    by_area = {a: ratio({k: v for k, v in strata.items() if k[0] == a}, grp)[0] for a in AREAS}
    out[grp.replace(" ", "_")] = dict(ratio=round(obs, 2), caught_high=hi, months_high=nh, caught_other=lo, months_other=nl,
                                       per_month_high=round(hi / nh, 2), per_month_other=round(lo / nl, 2), p=round((more + 1) / (R + 1), 3),
                                       areas_higher=sum(r is not None and r > 1 for r in by_area.values()),
                                       areas_tested=sum(r is not None for r in by_area.values()))
json.dump(out, open(OUT, "w"), indent=1)
print("tigerqld", json.dumps(out))
