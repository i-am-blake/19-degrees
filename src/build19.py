"""Build the data for the "19°" page and put it into the page.
Usage: python3 -I build19.py <asid.csv> <sst_dir> <beach_dir> <data.json> <page19.html> <out.html>
  beach_dir is the output of fetch_beaches.py (one CSV per beach plus beaches.json with today's readings).
  Run from the sharks-in-perspective folder after build.py and climate_analysis.py; reads regions.py, sharks.json and climate.json beside it.
  sip_data.json is the Sharks in Perspective build (for the drowning vs shark-death totals)."""
import csv, json, os, re, sys, collections
here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, here)
from regions import REGIONS, region_of
ASID, SST_DIR, BEACH_DIR, SIPDATA, PAGE, OUT = sys.argv[1:7]
sip = json.load(open(SIPDATA))

sst = {}
for name, *_ in REGIONS:
    fn = os.path.join(SST_DIR, name.replace(" ", "_").replace("&", "and") + ".csv")
    for d, v in list(csv.reader(open(fn)))[1:]:
        sst[(name, int(d[:4]), int(d[5:7]))] = float(v)

# water temperature (regional monthly mean) for every big-three incident since 1900 (HadISST starts in 1900)
SP = {"white shark": "white", "tiger shark": "tiger", "bull shark": "bull"}
temps = collections.defaultdict(list); temps_c = collections.defaultdict(list)
# sensitivity check: species identified by physical evidence (bite analysis, direct observation, tooth, DNA, photo or video),
# not only by where it happened, the shark's behaviour or a victim or witness account
EVID = ("bite analysis", "direct observation", "tooth", "dna", "video", "photograph")
confirmed = lambda x: any(k in (x["Shark.identification.method"] or "").lower() for k in EVID)
for x in csv.DictReader(open(ASID, encoding="utf-8")):
    g = SP.get((x["Shark.common.name"] or "").strip().lower())
    if not g: continue
    try:
        y = int(float(x["Incident.year"])); m = int(float(x["Incident.month"])); lat, lon = float(x["Latitude"]), float(x["Longitude"])
    except ValueError: continue
    if y < 1900: continue
    r = region_of(x["State"], lat, lon)
    if (r, y, m) in sst:
        temps[g].append(sst[(r, y, m)])
        if confirmed(x): temps_c[g].append(sst[(r, y, m)])
species = {}
for g, v in temps.items():
    v.sort(); n = len(v)
    species[g] = dict(n=n, below=sum(t < 19 for t in v), min=round(v[0], 1), median=round(v[n // 2], 1), max=round(v[-1], 1), t=[round(t, 3) for t in v])
    vc = sorted(temps_c[g]); nc = len(vc)
    species[g]["conf"] = dict(n=nc, below=sum(t < 19 for t in vc), min=round(vc[0], 1), median=round(vc[nc // 2], 1), max=round(vc[-1], 1), t=[round(t, 3) for t in vc])

# the 19°C season by decade: share of years in which each calendar month averaged 19°C or more
def season(r):
    yrs = sorted({y for (rr, y, m) in sst if rr == r and all((r, y, mm) in sst for mm in range(1, 13))})
    rows = []
    for d0 in range(yrs[0] // 10 * 10, yrs[-1] + 1, 10):
        ys = [y for y in yrs if d0 <= y < d0 + 10]
        if not ys: continue
        share = [round(sum(sst[(r, y, m)] >= 19 for y in ys) / len(ys), 2) for m in range(1, 13)]
        rows.append(dict(decade=d0, years=len(ys), share=share, months=round(sum(share), 1)))
    last = max(y for (rr, y, m) in sst if rr == r)
    partial = [round(sst[(r, last, m)], 1) if (r, last, m) in sst else None for m in range(1, 13)]
    years = [[y, sum(sst[(r, y, m)] >= 19 for m in range(1, 13)), round(sum(sst[(r, y, m)] for m in range(1, 13)) / 12, 2)] for y in yrs]
    return dict(rows=rows, last_year=last, last_temps=partial, years=years)

d = dict(
    built=sip.get("built"), sst_last=sip.get("sst_last"), asid_last=sip.get("asid_last"),
    ratio=dict(drown=sip["totals"]["d10"], shark=sip["totals"]["fatal"], window=sip["window"]),
    species=species,
    sydney=season("Sydney & Central Coast"),
    south=season("NSW South Coast"),
)
_clim = json.load(open(os.path.join(here, "climate.json")))
d["anomaly"] = dict(all=_clim["overall"]["all"], bull=_clim["overall"].get("bull"))
d["nsw_bull"] = [dict(decade=r["decade"], bull=r["bull"]) for r in json.load(open(os.path.join(here, "climate.json")))["window_19"]]
# beaches, north to south: 19°C season by decade, months per year, today's reading
from beaches import BEACHES
bmeta = json.load(open(os.path.join(BEACH_DIR, "beaches.json")))
def season_series(path):
    """Season-years run July to June (the 2025–26 season is Jul 2025 to Jun 2026), so the newest half-year counts."""
    s = {}
    for dd, v in list(csv.reader(open(path)))[1:]:
        s[(int(dd[:4]), int(dd[5:7]))] = float(v)
    ym = lambda sy, m: (sy if m >= 7 else sy + 1, m)            # calendar (year, month) of month m in season sy
    starts = sorted({y for (y, m) in s} | {y - 1 for (y, m) in s})
    full = [sy for sy in starts if all(ym(sy, m) in s for m in range(1, 13))]
    rows = []
    for d0 in range(full[0] // 10 * 10, full[-1] + 1, 10):
        ys = [y for y in full if d0 <= y < d0 + 10]
        if not ys: continue
        share = [round(sum(s[ym(y, m)] >= 19 for y in ys) / len(ys), 2) for m in range(1, 13)]
        rows.append(dict(decade=d0, years=len(ys), share=share, months=round(sum(share), 1)))
    per = {y: sum(s[ym(y, m)] >= 19 for m in range(1, 13)) for y in full}
    mean = {y: round(sum(s[ym(y, m)] for m in range(1, 13)) / 12, 2) for y in full}
    last_cal = max(y for (y, m) in s)
    lm = max(m for (y, m) in s if y == last_cal)
    cur = last_cal if lm >= 7 else last_cal - 1                     # season holding the newest month
    cur_temps = [round(s[ym(cur, m)], 1) if ym(cur, m) in s else None for m in range(1, 13)]
    base = [y for y in full if y < 1930]; recent = full[-10:]
    lab = lambda y: f"{y}–{str(y + 1)[2:]}"
    return dict(rows=rows, years=[[y, per[y], mean[y]] for y in full],
                base=round(sum(per[y] for y in base) / len(base), 1), recent=round(sum(per[y] for y in recent) / len(recent), 1),
                base_span=[lab(base[0]), lab(base[-1])], recent_span=[lab(recent[0]), lab(recent[-1])],
                last_year=last_cal, season=cur, season_label=lab(cur), season_temps=cur_temps)
d["beaches"] = []
for key, name, blat, blon, plat, plon, coast in BEACHES:
    m = bmeta[key]
    d["beaches"].append(dict(key=key, name=name, coast=coast, beach=m["beach"], patch=m["patch"], today=m.get("today"),
                             **season_series(os.path.join(BEACH_DIR, key + ".csv"))))
# bites by species on each coast since 1900 (east = Queensland + NSW, west = Western Australia)
cs = {"east": collections.Counter(), "west": collections.Counter()}
for x in csv.DictReader(open(ASID, encoding="utf-8")):
    try: y = int(float(x["Incident.year"]))
    except ValueError: continue
    if y < 1900: continue
    st = x["State"].strip().upper(); k = "east" if st in ("QLD", "NSW") else "west" if st == "WA" else None
    g = SP.get((x["Shark.common.name"] or "").strip().lower())
    if k and g: cs[k][g] += 1
d["coast_species"] = {k: dict(v) for k, v in cs.items()}
# bull shark bites by decade: southern NSW (Mid North Coast to the Victorian border) and Western Australia,
# with how many were in a harbour, river, lake, creek, estuary or bay
SOUTH = {"Mid North Coast & Hunter", "Sydney & Central Coast", "NSW South Coast"}
bd = {"nsw_south": collections.defaultdict(lambda: [0, 0]), "wa": collections.defaultdict(lambda: [0, 0])}
for x in csv.DictReader(open(ASID, encoding="utf-8")):
    if (x["Shark.common.name"] or "").strip().lower() != "bull shark": continue
    try: y = int(float(x["Incident.year"])); lat, lon = float(x["Latitude"]), float(x["Longitude"])
    except ValueError: continue
    if y < 1900: continue
    st = x["State"].strip().upper()
    k = "wa" if st == "WA" else "nsw_south" if region_of(x["State"], lat, lon) in SOUTH else None
    if not k: continue
    # inshore: the record's site type is river or estuary/harbour, or the place name has harbour, river, creek, lake or estuary
    # (not "bay": Coral Bay, Jurien Bay and Crowdy Bay are open coast)
    inshore = x["Site.category"].strip().lower() in ("river", "estuary/harbour") or any(
        w in x["Location"].lower() for w in ("harbour", "river", "creek", "lake", "estuary"))
    bd[k][y // 10 * 10][0] += 1
    bd[k][y // 10 * 10][1] += inshore
d["bull_decades"] = {k: {str(dd): v for dd, v in sorted(t.items())} for k, t in bd.items()}
# Western Australia: is the 2020s jump in bull shark bites more than chance?
# (1) Poisson: 2020s count against the 1900-2019 yearly rate; (2) one-sided Fisher exact test on the bull share of
# all WA shark bites, 2000-19 against 2020 on (controls for more people in the water and better reporting)
import math
wa = dict(pre=0, post=0, all_0019=0, bull_0019=0, all_post=0, north=0, south=0)
for x in csv.DictReader(open(ASID, encoding="utf-8")):
    if x["State"].strip().upper() != "WA": continue
    try: y = int(float(x["Incident.year"]))
    except ValueError: continue
    bull = (x["Shark.common.name"] or "").strip().lower() == "bull shark"
    if 2000 <= y <= 2019: wa["all_0019"] += 1; wa["bull_0019"] += bull
    if y >= 2020:
        wa["all_post"] += 1
        if bull:
            wa["post"] += 1
            try: wa["north" if float(x["Latitude"]) > -26 else "south"] += 1
            except ValueError: pass
    elif y >= 1900 and bull: wa["pre"] += 1
al = d.get("asid_last") or {"year": 2026, "month": 6}
yrs_post = (al["year"] - 2020) + al["month"] / 12
lam = wa["pre"] / 120 * yrs_post
wa["p_poisson"] = 1 - sum(math.exp(-lam) * lam ** k / math.factorial(k) for k in range(wa["post"]))
A, B, C, Dn = wa["post"], wa["all_post"] - wa["post"], wa["bull_0019"], wa["all_0019"] - wa["bull_0019"]
N, K, n = A + B + C + Dn, A + C, A + B
wa["p_fisher"] = sum(math.comb(K, i) * math.comb(N - K, n - i) for i in range(A, min(K, n) + 1)) / math.comb(N, n)
wa["years_post"] = round(yrs_post, 1)
d["wa_spike"] = wa
# the bite season: bull shark bites by calendar month in three eras, south of Port Macquarie (east) and in Western Australia (west)
BM_ERAS = [(1900, 1959), (1960, 1999), (2000, 2100)]
bm = {"east": [[0] * 12 for _ in BM_ERAS], "west": [[0] * 12 for _ in BM_ERAS]}
for x in csv.DictReader(open(ASID, encoding="utf-8")):
    if (x["Shark.common.name"] or "").strip().lower() != "bull shark": continue
    try: y = int(float(x["Incident.year"])); mo = int(float(x["Incident.month"])); lat, lon = float(x["Latitude"]), float(x["Longitude"])
    except ValueError: continue
    k = "west" if x["State"].strip().upper() == "WA" else "east" if region_of(x["State"], lat, lon) in SOUTH else None
    if not k: continue
    for i, (a0, z0) in enumerate(BM_ERAS):
        if a0 <= y <= z0: bm[k][i][mo - 1] += 1
d["bite_months"] = dict(eras=[[a0, z0] for a0, z0 in BM_ERAS], counts=bm)
# bite zones on the east coast (Queensland and NSW) by era, and where the sea stays at 19°C or more for half the year
ERAS = [(1950, 1979), (1980, 1999), (2000, 2014), (2015, 2026)]
east = lambda la, lo: lo >= 144 and -37.6 < la < -10.5
zones = {}
for sp in ("bull", "tiger", "white"):
    zones[sp] = []
    for a, z in ERAS:
        P = sorted(((i[1], i[2]) for i in sip["incidents"] if i[3] == sp and a <= i[0] <= z and east(i[1], i[2]) and not i[5]), key=lambda p: p[0])
        L = [p[0] for p in P]
        q = (lambda p: L[min(len(L) - 1, int(p * len(L)))]) if L else (lambda p: None)
        zones[sp].append(dict(era=[a, z], n=len(L), north=q(.9), mid=q(.5), south=q(.1), pts=[[round(la, 2), round(lo, 2)] for la, lo in P]))
eb = [x for x in d["beaches"] if x["coast"] == "east"]
def half_year_line(a, z):
    m = [(x["patch"][0], sum(r[1] for r in x["years"] if a <= r[0] <= z) / max(1, sum(1 for r in x["years"] if a <= r[0] <= z))) for x in eb]
    for (l1, m1), (l2, m2) in zip(m, m[1:]):
        if m1 >= 6 > m2: return round(l1 + (6 - m1) / (m2 - m1) * (l2 - l1), 2)
    return None
d["zones"] = dict(eras=[list(e) for e in ERAS], species=zones, line=[half_year_line(a, z) for a, z in ERAS], line_1900=half_year_line(1900, 1929))
# a look ahead, not a climate model: each beach's warming trend since 1980 (least squares on complete calendar years),
# added to its 2016-2025 average month; how many months of an average year would reach 19°C by 2050 at that pace
def ahead(key):
    yrs = collections.defaultdict(list)
    for r in csv.DictReader(open(os.path.join(BEACH_DIR, key + ".csv"))):
        if r["sst"]: yrs[int(r["date"][:4])].append(float(r["sst"]))
    ys = [y for y in range(1980, 2026) if len(yrs[y]) == 12]; an = [sum(yrs[y]) / 12 for y in ys]
    my, ma = sum(ys) / len(ys), sum(an) / len(an)
    tr = sum((y - my) * (v - ma) for y, v in zip(ys, an)) / sum((y - my) ** 2 for y in ys)
    clim = [sum(yrs[y][m] for y in range(2016, 2026)) / 10 for m in range(12)]
    return round(tr * 10, 2), sum(c >= 19 for c in clim), sum(c + tr * 30 >= 19 for c in clim)
for x in d["beaches"]:
    x["trend"], x["months_now"], x["months_2050"] = ahead(x["key"])
m50 = [(x["patch"][0], x["months_2050"]) for x in eb]
line_2050 = None
for (l1, m1), (l2, m2) in zip(m50, m50[1:]):
    if m1 >= 6 > m2: line_2050 = round(l1 + (6 - m1) / (m2 - m1) * (l2 - l1), 2)
d["zones"]["line_2050"] = line_2050          # None: past the southernmost beach (Eden), so past the Victorian border
d["zones"]["south_beach"] = dict(name=eb[-1]["name"], months_2050=eb[-1]["months_2050"], trend=eb[-1]["trend"])
# looking ahead to 2050 on each coast: range (the half-year 19°C line), season (months a year at 19°C or more)
# and a bite scenario: bull shark bites since 2015 in the cooler south of each coast, scaled by how many more
# warm months its beaches would have if bites per warm month stayed the same (an illustration, not a forecast)
def cross(pairs):
    for (l1, m1), (l2, m2) in zip(pairs, pairs[1:]):
        if m1 >= 6 > m2: return round(l1 + (6 - m1) / (m2 - m1) * (l2 - l1), 2)
    return None
def pois_ci(n, conf=.8):
    try:
        from scipy.stats import chi2
        a = (1 - conf) / 2
        return (chi2.ppf(a, 2 * n) / 2 if n else 0.0), chi2.ppf(1 - a, 2 * n + 2) / 2
    except ImportError:
        return max(0.0, n - 1.28 * n ** .5), n + 1.28 * n ** .5 + 1
ahead = {}
for c, south_keys, inregion in (
        ("east", ("newcastle", "sydney", "wollongong", "eden"), lambda x, la, lo: x["State"].strip().upper() != "WA" and region_of(x["State"], la, lo) in SOUTH),
        ("west", ("geraldton", "perth", "mandurah", "margaret"), lambda x, la, lo: x["State"].strip().upper() == "WA" and la <= -26)):
    bs = [x for x in d["beaches"] if x["coast"] == c]
    n = 0
    for x in csv.DictReader(open(ASID, encoding="utf-8")):
        if (x["Shark.common.name"] or "").strip().lower() != "bull shark": continue
        try: y = int(float(x["Incident.year"])); la, lo = float(x["Latitude"]), float(x["Longitude"])
        except ValueError: continue
        if y >= 2015 and inregion(x, la, lo): n += 1
    yrs = (al["year"] - 2015) + al["month"] / 12
    sb = [x for x in bs if x["key"] in south_keys]
    mn, m5 = sum(x["months_now"] for x in sb) / len(sb), sum(x["months_2050"] for x in sb) / len(sb)
    lo_, hi_ = pois_ci(n)
    k = m5 / mn
    ahead[c] = dict(
        line_now=cross([(x["patch"][0], x["months_now"]) for x in bs]), line_2050=cross([(x["patch"][0], x["months_2050"]) for x in bs]),
        south_name=bs[-1]["name"],
        beaches=[dict(name=x["name"], now=x["months_now"], y2050=x["months_2050"], trend=x["trend"]) for x in bs],
        bites=dict(n=n, years=round(yrs, 1), rate=round(n / yrs, 2), lo=round(lo_ / yrs, 2), hi=round(hi_ / yrs, 2),
                   months_now=round(mn, 1), months_2050=round(m5, 1), scale=round(k, 2),
                   rate_2050=round(n / yrs * k, 2), lo_2050=round(lo_ / yrs * k, 2), hi_2050=round(hi_ / yrs * k, 2),
                   beaches=[x["name"] for x in sb]))
d["ahead"] = ahead
# where bull shark bites happen: open coast vs harbor, river, lake or estuary (same rule as bull_decades), by era,
# for all of Australia and for southern NSW; one-sided Fisher exact test of the open-coast share, before 2000 vs 2015 on
H_ERAS = [(1900, 1959), (1960, 1999), (2000, 2014), (2015, 2100)]
def fisher_greater(a, b, c, dd):
    N, K, n = a + b + c + dd, a + c, a + b
    return sum(math.comb(K, i) * math.comb(N - K, n - i) for i in range(a, min(K, n) + 1)) / math.comb(N, n)
bo = {k: [[0, 0] for _ in H_ERAS] for k in ("aus", "nsw_south", "aus_conf", "nsw_south_conf")}
acts = collections.Counter(); idq = collections.Counter()
for x in csv.DictReader(open(ASID, encoding="utf-8")):
    if (x["Shark.common.name"] or "").strip().lower() != "bull shark": continue
    try: y = int(float(x["Incident.year"])); la, lo = float(x["Latitude"]), float(x["Longitude"])
    except ValueError: continue
    if y < 1900: continue
    inshore = x["Site.category"].strip().lower() in ("river", "estuary/harbour") or any(
        w in x["Location"].lower() for w in ("harbour", "river", "creek", "lake", "estuary"))
    keys = ["aus"] + (["nsw_south"] if x["State"].strip().upper() != "WA" and region_of(x["State"], la, lo) in SOUTH else [])
    if confirmed(x): keys += [k + "_conf" for k in keys]
    for i, (a0, z0) in enumerate(H_ERAS):
        if a0 <= y <= z0:
            for k in keys: bo[k][i][0] += 1; bo[k][i][1] += (not inshore)
    if y >= 2015 and not inshore: acts[(x["Victim.activity"] or "").strip().lower() or "unknown"] += 1
    m = (x["Shark.identification.method"] or "").strip().lower()
    if y < 1960 and inshore: idq["early_in"] += 1; idq["early_in_geo"] += "geograph" in m
    if y >= 2015 and not inshore: idq["recent_open"] += 1; idq["recent_open_blank"] += (m == "")
bull_open = dict(eras=[[a0, min(z0, al["year"])] for a0, z0 in H_ERAS], acts=dict(acts.most_common(6)), idq=dict(idq))
for k, v in bo.items():
    pn, po = sum(r[0] for r in v[:2]), sum(r[1] for r in v[:2]); ln, lo_ = v[-1]
    bull_open[k] = dict(eras=v, p=fisher_greater(lo_, ln - lo_, po, pn - po))
d["bull_open"] = bull_open
# white sharks on the NSW north coast (28.1–31.6°S): share of bites in June–November, when humpbacks migrate past,
# against all other bites on the same coast (a stand-in for when people are in the water); one-sided Fisher test, 2000 on
wnc = {"white": [0] * 12, "other": [0] * 12}
for x in csv.DictReader(open(ASID, encoding="utf-8")):
    try: y = int(float(x["Incident.year"])); mo = int(float(x["Incident.month"])); la = float(x["Latitude"])
    except ValueError: continue
    if x["State"].strip().upper() != "NSW" or not (-31.6 < la < -28.1) or y < 2000: continue
    wnc["white" if (x["Shark.common.name"] or "").strip().lower() == "white shark" else "other"][mo - 1] += 1
jn = lambda v: sum(v[5:11])
wnc["p"] = fisher_greater(jn(wnc["white"]), sum(wnc["white"]) - jn(wnc["white"]), jn(wnc["other"]), sum(wnc["other"]) - jn(wnc["other"]))
d["white_nc"] = wnc
print("white_nc", json.dumps(wnc))
# El Niño / La Niña: bites per month in each phase since 1950 (index from fetch_nino34.py; >= +0.5 El Niño, <= -0.5 La Niña),
# and a two-sided binomial test of the La Niña share against La Niña's share of months
enso_f = os.path.join(SST_DIR, "nino34.csv")
if os.path.exists(enso_f):
    oni = {r["date"]: float(r["oni"]) for r in csv.DictReader(open(enso_f))}
    ph = lambda v: "nino" if v >= .5 else "nina" if v <= -.5 else "neutral"
    months = collections.Counter(ph(v) for v in oni.values())
    cnt = collections.defaultdict(collections.Counter); recent_nina = collections.Counter()
    for x in csv.DictReader(open(ASID, encoding="utf-8")):
        try: y = int(float(x["Incident.year"])); mo = int(float(x["Incident.month"]))
        except ValueError: continue
        k = f"{y}-{mo:02d}"
        if k not in oni: continue
        st = x["State"].strip().upper(); c = "east" if st in ("QLD", "NSW") else "west" if st == "WA" else None
        sp = (x["Shark.common.name"] or "").strip().lower()
        if c and sp == "bull shark":
            cnt[c][ph(oni[k])] += 1
            if y >= 2020 and ph(oni[k]) == "nina": recent_nina[c] += 1
    def binom2(k, n, p):
        pk = [math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(n + 1)]
        return min(1.0, sum(q for q in pk if q <= pk[k] * (1 + 1e-9)))
    tot_m = sum(months.values()); enso = dict(months=dict(months), first=min(oni), last=max(oni))
    for c, v in cnt.items():
        n = sum(v.values())
        enso[c] = dict(counts=dict(v), per10y={p: round(v[p] / months[p] * 120, 1) for p in months},
                       ratio=round((v["nina"] / months["nina"]) / ((n - v["nina"]) / (tot_m - months["nina"])), 2),
                       p=round(binom2(v["nina"], n, months["nina"] / tot_m), 3),
                       nina_since_2020=recent_nina[c])
    d["enso"] = enso
    print("enso", json.dumps(enso))
print("bull_open", json.dumps(bull_open))
print("ahead", json.dumps(ahead["east"]["bites"]), json.dumps(ahead["west"]["bites"]), ahead["east"]["line_now"], ahead["east"]["line_2050"], ahead["west"]["line_now"], ahead["west"]["line_2050"])
# Australian population by decade (millions), shared with the Swim South build, for per-capita rates
import ast
_src = open(os.path.join(here, "build.py")).read()
_i = _src.index("POP_MID = "); _j = _src.index("}", _i) + 1
d["pop_mid"] = {str(k): v for k, v in ast.literal_eval(_src[_i + len("POP_MID = "):_j]).items()}
coast = json.load(open(os.path.join(here, "coast.json")))
d["coast"] = {k: coast[k] for k in ("w", "h", "lon0", "lon1", "lat0", "lat1", "d")}
sj = json.load(open(os.path.join(here, "sharks.json")))
d["sharks"] = dict(viewBox=sj["viewBox"], species={x["key"]: dict(name=x["name"], shapes=x["shapes"], source=x.get("source")) for x in sj["species"] if x["key"] in ("white", "tiger", "bull")})
# IMOS tag-tracking check (imos19.py writes imos.json beside this script; optional)
_imos = os.path.join(here, "imos.json")
if os.path.exists(_imos):
    d["imos"] = json.load(open(_imos)); print("imos", d["imos"]["days"], d["imos"]["pct_warm"], d["imos"]["c2"])
blob = json.dumps(d, separators=(",", ":")).replace("</", "<\\/")
html = open(PAGE).read()
pat = re.compile(r'(<script type="application/json" id="n19-data">)(.*?)(</script>)', re.S)
assert pat.search(html), "data block not found"
open(OUT, "w").write(pat.sub(lambda m: m.group(1) + blob + m.group(3), html, count=1))
print("wrote", OUT, len(blob), "bytes")
for bb in d["beaches"]: print(bb["name"], "patch", bb["patch"], "months a year", bb["base"], "->", bb["recent"], "today", bb["today"] and bb["today"]["sst"])
for g, s in species.items(): print(g, s["n"], "below 19:", s["below"], "range", s["min"], s["max"])
for r in d["sydney"]["rows"]: print(r["decade"], r["months"])
print(d["sydney"]["last_year"], d["sydney"]["last_temps"])
