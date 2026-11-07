"""Claim C19, daily version: do shark bites cluster in marine heatwaves?
Usage: python3 -I mhw19.py <ocean dir> <islands_nc_run.csv> <CDFW SharkIncidents xlsx> [hawaii_incidents.csv] <out mhw.json>
Needs the day of each bite, so it uses the coasts that record it: California (CDFW, white sharks), Réunion and New Caledonia
(University of Reunion Island) and Hawaii (DLNR). The Australian database gives the month only (the monthly test is on the C19 card).
Sea temperature: NOAA OISST v2.1 daily, one 0.25° ocean cell off each coast (files oisst_<point>.csv in the ocean dir).
A marine heatwave follows Hobday et al. (2016): at least 5 days in a row above the 90th percentile for that time of year
(1982-2011 baseline where the record covers it, else all years; 11-day window, 31-day smoothing), with gaps of 2 days or
less joined. Each bite counts as "in a heatwave" if its day is in one. The chance for that bite is the share of heatwave
days at the same place within 15 days of the same date, in the 5 years either side, so the season and the warming trend
are both matched. Observed count against the sum of those chances; exact two-sided Poisson-binomial p-value."""
import csv, datetime as dt, glob, json, os, re, sys
import numpy as np
import openpyxl

args = sys.argv[1:]
OCEAN, ISL, CA = args[:3]; HI = args[3] if len(args) == 5 else None; OUT = args[-1]

def load_sst(path):
    d = {}
    for r in csv.DictReader(open(path)):
        try: d[dt.date.fromisoformat(r["time"][:10])] = float(r["sst"])
        except (ValueError, KeyError): pass
    return d

def doy(d):  # day of year on a 365-day calendar (29 Feb shares 28 Feb's slot)
    return min(d.timetuple().tm_yday - (1 if d.month > 2 and d.year % 4 == 0 else 0), 365) - 1

def heatwave_days(sst):
    days = sorted(sst); yrs = sorted({d.year for d in days})
    base = [y for y in yrs if 1982 <= y <= 2011]; base = base if len(base) >= 20 else yrs
    pool = [[] for _ in range(365)]
    for d in days:
        if d.year in base:
            for k in range(-5, 6): pool[(doy(d) + k) % 365].append(sst[d])
    thr = np.array([np.percentile(p, 90) if p else np.nan for p in pool])
    thr = np.convolve(np.r_[thr[-15:], thr, thr[:15]], np.ones(31) / 31, "valid")  # 31-day smoothing, wrapping the year
    hot = [d for d in days if sst[d] > thr[doy(d)]]
    runs, cur = [], []
    for d in hot:
        if cur and (d - cur[-1]).days == 1: cur.append(d)
        else:
            if cur: runs.append(cur)
            cur = [d]
    if cur: runs.append(cur)
    runs = [r for r in runs if len(r) >= 5]
    merged = []
    for r in runs:  # join events separated by 2 days or less
        if merged and (r[0] - merged[-1][1]).days <= 3: merged[-1][1] = r[-1]
        else: merged.append([r[0], r[-1]])
    mhw = set()
    for a, b in merged:
        mhw |= {a + dt.timedelta(i) for i in range((b - a).days + 1)}
    return mhw, set(days)

POINTS = {os.path.basename(f)[6:-4]: f for f in glob.glob(os.path.join(OCEAN, "oisst_*.csv"))}
HW = {k: heatwave_days(load_sst(f)) for k, f in POINTS.items()}

def chance(pt, d):
    mhw, have = HW[pt]; n = k = 0
    for y in range(d.year - 5, d.year + 6):
        try: c = d.replace(year=y)
        except ValueError: c = d.replace(year=y, day=28)
        for i in range(-15, 16):
            x = c + dt.timedelta(i)
            if x in have: n += 1; k += x in mhw
    return k / n if n >= 150 else None  # at least about 5 years of the same season

# bites: (date, point)
CA_PTS = [(32.625, "california_san_diego"), (34.375, "california_santa_barbara"), (36.625, "california_monterey"),
          (37.625, "california_san_francisco"), (40.875, "california_humboldt")]
ws = openpyxl.load_workbook(CA, read_only=True, data_only=True)["Attacks_1950_2021"]
rows = list(ws.iter_rows(values_only=True)); ix = {k: i for i, k in enumerate(rows[0])}
groups = {"california_white": [], "islands_bull": [], "islands_tiger": [], "hawaii_tiger": [], "hawaii_all": []}
for r in rows[1:]:
    d, lat, sp = r[ix["Date"]], r[ix["Latitude"]], r[ix["Species"]]
    if hasattr(d, "year") and lat and sp and str(sp).strip().lower() == "white":
        groups["california_white"].append((d.date(), min(CA_PTS, key=lambda p: abs(p[0] - float(lat)))[1]))
raw = open(ISL, "rb").read().decode("utf-8", "replace").splitlines()
for r in csv.DictReader(raw, delimiter=";" if raw[0].count(";") > raw[0].count(",") else ","):
    try: d = dt.date.fromisoformat(r["DATE"])
    except ValueError: continue
    pt = "new_caledonia_noumea" if r["SITE"].startswith("New") else "reunion_west"
    if r["SHARKTYPE"] == "Bull": groups["islands_bull"].append((d, pt))
    if r["SHARKTYPE"] == "Tiger": groups["islands_tiger"].append((d, pt))
def norm(t):
    import unicodedata
    t = unicodedata.normalize("NFKD", t.lower())
    return re.sub(r"[^a-z ,]", "", t)
def hawaii_date(t):  # DLNR writes "2026/09/07, 4:32 pm"
    m = re.match(r"\s*(\d{4})/(\d{1,2})/(\d{1,2})", t)
    try: return dt.date(*map(int, m.groups())) if m else None
    except ValueError: return None
if HI and os.path.exists(HI):
    ISLES = [("kauai", "hawaii_kauai"), ("maui", "hawaii_maui"), ("molokai", "hawaii_maui"), ("lanai", "hawaii_maui"),
             ("hawaii", "hawaii_big_island"), ("big island", "hawaii_big_island"), ("oahu", "hawaii_oahu_south")]
    NORTH = ("north shore", "haleiwa", "sunset", "waimea", "pipeline", "laie", "kahuku", "mokuleia", "kaena", "makaha", "waianae", "yokohama")
    for r in csv.DictReader(open(HI)):
        k = {h.lower().split()[0]: v for h, v in r.items()}
        d = hawaii_date(k.get("date", ""))
        if not d: continue
        loc = norm(k.get("location", ""))  # "O‘ahu", "Oʻahu" and "Oahu" all become "oahu"
        pt = next((p for name, p in ISLES if name in loc.split(",")[0] or loc.startswith(name)), None)
        if pt == "hawaii_oahu_south" and any(w in loc for w in NORTH): pt = "hawaii_oahu_north"
        if not pt: continue
        groups["hawaii_all"].append((d, pt))
        if "tiger" in k.get("shark", "").lower(): groups["hawaii_tiger"].append((d, pt))

def pbinom_p(ps, k):
    dist = np.zeros(len(ps) + 1); dist[0] = 1
    for p in ps: dist[1:] = dist[1:] * (1 - p) + dist[:-1] * p; dist[0] *= 1 - p
    return round(float(min(1.0, dist[dist <= dist[k] * (1 + 1e-9)].sum())), 3)

def summary(bites):
    used = [(d, pt, c) for d, pt in bites if pt in HW and d in HW[pt][1] and (c := chance(pt, d)) is not None]
    if not used: return dict(n=0)
    k = sum(d in HW[pt][0] for d, pt, _ in used); ps = [c for *_, c in used]
    return dict(n=len(used), in_heatwave=k, pct=round(100 * k / len(used)), expected_pct=round(100 * sum(ps) / len(ps)),
                ratio=round(k / sum(ps), 2) if sum(ps) else None, p=pbinom_p(ps, k), first=min(d for d, *_ in used).year, last=max(d for d, *_ in used).year)

out = {g: summary(b) for g, b in groups.items()}
out["all"] = summary(groups["california_white"] + groups["islands_bull"] + groups["islands_tiger"] + groups["hawaii_all"])
out["points"] = {k: dict(days=len(v[1]), heatwave_days=len(v[0]), first=min(v[1]).isoformat(), last=max(v[1]).isoformat()) for k, v in HW.items()}
json.dump(out, open(OUT, "w"), indent=1)
print("mhw", json.dumps({k: v for k, v in out.items() if k != "points"}))
