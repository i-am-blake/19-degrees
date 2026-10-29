"""Does unusually warm water line up with more shark incidents?

For every region-month from 1970 to 2025:
  anomaly = sea temperature minus the average of the same calendar month in the surrounding
            +/-5 years (that year excluded). This removes the seasonal cycle and the slow
            long-term trend, which also carries slow changes in how many people use the water.
Then compare incident rates in each region's warmest third of months with its coolest third.
Confidence intervals: bootstrap over region-months (2,000 resamples).

Usage: python3 -I climate_analysis.py <asid.csv> <sst_dir> <out.json>
"""
import csv, json, os, sys, random, statistics as st, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from regions import REGIONS, region_of

ASID, SST_DIR, OUT = sys.argv[1:4]
Y0, Y1 = 1970, 2025
random.seed(7)

# --- sea temperature per region-month
sst = {}
for name, *_ in REGIONS:
    fn = os.path.join(SST_DIR, name.replace(" ", "_").replace("&", "and") + ".csv")
    for d, v in list(csv.reader(open(fn)))[1:]:
        sst[(name, int(d[:4]), int(d[5:7]))] = float(v)

cells = []  # (region, year, month, anomaly, raw sst)
for name, *_ in REGIONS:
    for y in range(Y0, Y1 + 1):
        for m in range(1, 13):
            if (name, y, m) not in sst: continue
            ref = [sst[(name, yy, m)] for yy in range(y - 5, y + 6) if yy != y and (name, yy, m) in sst]
            cells.append((name, y, m, sst[(name, y, m)] - st.mean(ref), sst[(name, y, m)]))

# --- incidents per region-month
inc = collections.defaultdict(lambda: collections.Counter())
for x in csv.DictReader(open(ASID, encoding="utf-8")):
    try:
        y = int(float(x["Incident.year"])); m = int(float(x["Incident.month"]))
        lat, lon = float(x["Latitude"]), float(x["Longitude"])
    except ValueError:
        continue
    if not Y0 <= y <= Y1: continue
    r = region_of(x["State"], lat, lon)
    sp = (x["Shark.common.name"] or "").strip().lower()
    group = "bull" if sp == "bull shark" else "tiger" if sp == "tiger shark" else "white" if sp == "white shark" else "other"
    unprov = x["Provoked/unprovoked"].strip().lower() == "unprovoked"
    key = (r, y, m)
    inc[key]["all"] += 1
    if unprov: inc[key]["unprov"] += 1
    inc[key][group] += 1
    if x["Victim.injury"].strip().lower() == "fatal": inc[key]["fatal"] += 1

# --- terciles of anomaly within each region (so every region contributes equally to each bin)
by_region = collections.defaultdict(list)
for c in cells: by_region[c[0]].append(c)
binned = []  # (region, year, month, anomaly, bin)
for r, cs in by_region.items():
    a = sorted(c[3] for c in cs)
    lo, hi = a[len(a) // 3], a[2 * len(a) // 3]
    for c in cs:
        b = "cool" if c[3] < lo else "warm" if c[3] >= hi else "normal"
        binned.append((r, c[1], c[2], c[3], b))

def rate_ratio(field, rows):
    """incidents per region-month in warm third / cool third, with bootstrap 95% CI"""
    warm = [inc[(r, y, m)][field] for r, y, m, a, b in rows if b == "warm"]
    cool = [inc[(r, y, m)][field] for r, y, m, a, b in rows if b == "cool"]
    if sum(cool) == 0: return None
    point = (sum(warm) / len(warm)) / (sum(cool) / len(cool))
    boots = []
    for _ in range(2000):
        w = [random.choice(warm) for _ in warm]; c = [random.choice(cool) for _ in cool]
        if sum(c): boots.append((sum(w) / len(w)) / (sum(c) / len(c)))
    boots.sort()
    return dict(ratio=round(point, 2), lo=round(boots[int(.025 * len(boots))], 2), hi=round(boots[int(.975 * len(boots))], 2),
                warm=sum(warm), cool=sum(cool), months_each=len(warm))

EAST_WARM = {"NSW North Coast", "Mid North Coast & Hunter", "Sydney & Central Coast", "NSW South Coast",
             "Gold Coast", "Sunshine Coast & Moreton Bay"}
results = dict(
    method=dict(years=f"{Y0}–{Y1}", region_months=len(binned)),
    overall={f: rate_ratio(f, binned) for f in ["all", "unprov", "fatal", "bull", "tiger", "white"]},
    east_coast={f: rate_ratio(f, [b for b in binned if b[0] in EAST_WARM]) for f in ["all", "bull", "tiger", "white"]},
    by_region={r: rate_ratio("all", [b for b in binned if b[0] == r]) for r in by_region},
)

# --- anomaly at incident time vs all months, by species (mean °C anomaly)
def mean_anom(field):
    v = []
    for r, y, m, a, b in binned:
        v += [a] * inc[(r, y, m)][field]
    return dict(n=len(v), mean=round(st.mean(v), 3)) if v else None
results["mean_anomaly_at_incident"] = {f: mean_anom(f) for f in ["all", "bull", "tiger", "white"]}

# --- warm-season edges: east-coast bull shark incidents vs months at or above 19°C
bull_months = collections.Counter()
for r, y, m, a, b in binned:
    if r in EAST_WARM:
        raw = sst[(r, y, m)]
        k = ">=19" if raw >= 19 else "<19"
        bull_months[k + "_months"] += 1
        bull_months[k + "_bull"] += inc[(r, y, m)]["bull"]
results["bull_19"] = dict(bull_months)

json.dump(results, open(OUT, "w"), indent=1)
print(json.dumps(results, indent=1))

# --- control: do other species still bite in the sub-19°C months? (people are still in the water)
ctrl = collections.Counter()
for r, y, m, a, b in binned:
    if r in EAST_WARM:
        k = ">=19" if sst[(r, y, m)] >= 19 else "<19"
        ctrl[k + "_white"] += inc[(r, y, m)]["white"]
        ctrl[k + "_other"] += inc[(r, y, m)]["other"]
        ctrl[k + "_all"] += inc[(r, y, m)]["all"]
results["control_19"] = dict(ctrl)

# --- the 19°C window over time in the southern east-coast regions, with bull shark incidents
SOUTH = ["Mid North Coast & Hunter", "Sydney & Central Coast", "NSW South Coast"]
win = []
for d0 in range(1970, 2030, 10):
    months = {r: sum(1 for y in range(d0, min(d0 + 10, 2026)) for m in range(1, 13)
                     if (r, y, m) in sst and sst[(r, y, m)] >= 19) / len([y for y in range(d0, min(d0 + 10, 2026)) if (r, y, 1) in sst])
              for r in SOUTH}
    bulls = sum(inc[(r, y, m)]["bull"] for r in SOUTH for y in range(d0, d0 + 10) for m in range(1, 13))
    win.append(dict(decade=d0, warm_months={r: round(v, 1) for r, v in months.items()}, bull=bulls))
results["window_19"] = win
json.dump(results, open(OUT, "w"), indent=1)
print(json.dumps(dict(control_19=results["control_19"], window_19=win), indent=1))
