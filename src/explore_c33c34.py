"""Look only: finishing two first tests. Prints a report; changes nothing.
C34, fairer control: are bites closer to boat ramps than random BEACHES on the same stretch of coast (where people swim),
not just random coastline? Beaches and ramps: OpenStreetMap (ODbL).
C33: at Queensland shark-control beaches, is the rise in bull shark catch in high-river months larger where the river's
catchment is more cleared, farmed or built up? Catch: Queensland Shark Control Program (CC BY 4.0). Flow: Water Data
Online (BoM, CC BY 3.0 AU). Catchments: HydroBASINS level 8 (WWF/HydroSHEDS). Land cover: ESA WorldCover 2021 (CC BY 4.0).
Usage: python3 explore_c33c34.py asid.csv scp-numbers-caught.xlsx shark-gear-locations.xlsx river_gauges.csv river_flow_daily.csv.gz"""
import csv, gzip, io, json, math, random, statistics as st, sys, time, urllib.parse, urllib.request, zipfile, datetime as dt
from collections import defaultdict
ASID, SCP, GEAR, GAUGES, FLOW = sys.argv[1:6]
UA = {"User-Agent": "Mozilla/5.0 (19-degrees.org open data)"}
def get(u, data=None, t=600):
    for k in range(4):
        try: return urllib.request.urlopen(urllib.request.Request(u, data=data, headers=UA), timeout=t).read()
        except Exception as e:
            err = e; time.sleep(20 * (k + 1))
    raise err
def km(a, b, c, d): return math.hypot((a - c) * 111, (b - d) * 111 * math.cos(math.radians((a + c) / 2)))
def overpass(q): return json.loads(get("https://overpass-api.de/api/interpreter", data=urllib.parse.urlencode({"data": q}).encode()))["elements"]
def ctr(e): return (e.get("lat") or e["center"]["lat"], e.get("lon") or e["center"]["lon"])

def c34():
    print("\n## C34 with beaches as the control\n")
    A = '[out:json][timeout:900];area["ISO3166-1"="AU"][admin_level=2]->.a;'
    ramps = [ctr(e) for e in overpass(A + '(nwr["leisure"="slipway"](area.a);nwr["amenity"~"fish_clean"](area.a);nwr["man_made"~"fish_clean"](area.a););out center;')]
    beaches = [ctr(e) for e in overpass(A + 'nwr["natural"="beach"](area.a);out center;')]
    print(f"- {len(ramps)} ramps and cleaning tables, {len(beaches)} beaches")
    grid = defaultdict(list)
    for la, lo in ramps: grid[(round(la), round(lo))].append((la, lo))
    def near(la, lo):
        return min((km(la, lo, a, b) for i in (-1, 0, 1) for j in (-1, 0, 1) for a, b in grid.get((round(la) + i, round(lo) + j), [])), default=1e9)
    bgrid = defaultdict(list)
    for la, lo in beaches: bgrid[(round(la), round(lo))].append((la, lo))
    rows = [r for r in csv.DictReader(open(ASID, encoding="utf-8")) if r["Provoked/unprovoked"].strip() == "unprovoked" and r["Latitude"].strip() not in ("", "NA")]
    random.seed(19)
    from scipy.stats import binomtest
    for lab, f in (("all unprovoked", lambda r: True), ("bull shark", lambda r: "bull" in r["Shark.common.name"].lower()),
                   ("open coast only (site: coastal)", lambda r: r["Site.category"].strip().startswith("coastal")),
                   ("bull shark, open coast only", lambda r: "bull" in r["Shark.common.name"].lower() and r["Site.category"].strip().startswith("coastal"))):
        closer = n = 0; db_, dr_ = [], []
        for r in filter(f, rows):
            la, lo = float(r["Latitude"]), float(r["Longitude"])
            loc = [b for i in (-1, 0, 1) for j in (-1, 0, 1) for b in bgrid.get((round(la) + i, round(lo) + j), []) if km(la, lo, *b) <= 50]
            if len(loc) < 10: continue
            rnd = st.median(near(*b) for b in random.sample(loc, min(20, len(loc))))
            d = near(la, lo)
            if d > 100 or rnd > 100: continue
            n += 1; closer += d < rnd; db_.append(d); dr_.append(rnd)
        if n: print(f"- {lab}: {n} bites; median {st.median(db_):.1f} km to the nearest ramp vs {st.median(dr_):.1f} km for random beaches nearby; "
                    f"closer: {closer}/{n} ({closer/n:.0%}), p={binomtest(closer, n, 0.5).pvalue:.3f}")

def gear_coords():
    import openpyxl
    out = {}
    for ws in openpyxl.load_workbook(GEAR, read_only=True, data_only=True).worksheets[1:]:
        name = None
        for row in ws.iter_rows(values_only=True):
            if isinstance(row[0], str) and row[0].strip() and row[0].strip() not in ("Area", "Location", "Mackay"): name = row[0].strip()
            nums = [x for x in row[2:] if isinstance(x, (int, float))]
            if name and len(nums) >= 4 and 9 < nums[-4 if len(nums) < 8 else 1] < 30 if False else None: pass
            vals = [x for x in row[3:] if isinstance(x, (int, float))]
            if name and len(vals) >= 4 and 9 <= vals[0] <= 30 and 140 <= vals[2] <= 155:
                out.setdefault(name.lower(), []).append((-(vals[0] + vals[1] / 60), vals[2] + vals[3] / 60))
    return {k: (st.mean(p[0] for p in v), st.mean(p[1] for p in v)) for k, v in out.items()}

def c33():
    print("\n## C33 catchment land use and the high-river rise in bull shark catch (Queensland)\n")
    import openpyxl
    rows = [r for r in openpyxl.load_workbook(SCP, read_only=True).worksheets[0].iter_rows(min_row=2, values_only=True)]
    bull = defaultdict(lambda: defaultdict(int))
    for r in rows:
        if r[9] == "BULL WHALER": bull[r[4]][(r[0], r[1])] += 1
    beachmonths = defaultdict(set)
    for r in rows: beachmonths[r[4]].add((r[0], r[1]))  # months the beach caught anything: gear was set
    G = gear_coords()
    def where(b):
        k = b.lower().replace("(", "").replace(")", "")
        for g, ll in G.items():
            if k.split()[0] in g or g.split()[0] in k: return ll
    beaches = {b: where(b) for b, v in bull.items() if sum(v.values()) >= 15}
    miss = [b for b, ll in beaches.items() if not ll]
    beaches = {b: ll for b, ll in beaches.items() if ll}
    print(f"- beaches with 15+ bull sharks caught: {len(beaches) + len(miss)}; located from the gear file: {len(beaches)}" + (f"; not located: {', '.join(miss)}" if miss else ""))
    gauges = {r["station_no"]: (float(r["lat"]), float(r["lon"])) for r in csv.DictReader(open(GAUGES))}
    flow = defaultdict(list)
    with gzip.open(FLOW, "rt") as f:
        for r in csv.DictReader(f):
            if r["date"] >= "1996":
                try: flow[(r["station_no"], int(r["date"][:4]), int(r["date"][5:7]))].append(float(r["flow_m3s"]))
                except ValueError: pass
    # gauges north of K'gari, fetched here for the beaches the stored set doesn't reach
    B = "http://www.bom.gov.au/waterdata/services?"
    def q(**p): return json.loads(get(B + urllib.parse.urlencode({"service": "kisters", "type": "queryServices", "format": "json", **p}), t=300))
    try:
        stl = q(request="getStationList", parametertype_name="Water Course Discharge", returnfields="station_no,station_name,station_latitude,station_longitude", bBox="145.0,-24.6,153.0,-16.4")
        cand = [dict(zip(stl[0], r)) for r in stl[1:]]
        want = set()
        for b, (la, lo) in beaches.items():
            if la > -24.6:
                near = sorted(cand, key=lambda s: km(la, lo, float(s["station_latitude"]), float(s["station_longitude"])))[:4]
                want |= {s["station_no"] for s in near if km(la, lo, float(s["station_latitude"]), float(s["station_longitude"])) < 60}
        for s in cand:
            if s["station_no"] not in want: continue
            try:
                ts = q(request="getTimeseriesList", station_no=s["station_no"], parametertype_name="Water Course Discharge", ts_name="DMQaQc.Merged.DailyMean.24HR", returnfields="ts_id")
                if len(ts) < 2: continue
                v = q(request="getTimeseriesValues", ts_id=ts[1][0], **{"from": "1996-01-01", "to": dt.date.today().isoformat()}, returnfields="Timestamp,Value")
                data = v[0]["data"] if isinstance(v, list) else v["data"]
                good = [(t[:10], x) for t, x in data if x is not None]
                if len(good) < 3650: continue
                gauges[s["station_no"]] = (float(s["station_latitude"]), float(s["station_longitude"]))
                for t, x in good: flow[(s["station_no"], int(t[:4]), int(t[5:7]))].append(float(x))
                time.sleep(1)
            except Exception as e: print(f"  - gauge {s['station_no']}: {type(e).__name__}")
        print(f"- extra gauges fetched north of K'gari: {len(want)} wanted")
    except Exception as e:
        print(f"- northern gauge list failed: {type(e).__name__} {str(e)[:150]}")
    mflow = {k: sum(v) / len(v) for k, v in flow.items() if len(v) >= 20}
    # catchments
    z = zipfile.ZipFile(io.BytesIO(get("https://data.hydrosheds.org/file/HydroBASINS/standard/hybas_au_lev08_v1c.zip")))
    z.extractall("hb")
    import geopandas as gpd, numpy as np, rasterio, rasterio.mask
    from shapely.geometry import Point
    from shapely.ops import unary_union
    hb = gpd.read_file([f"hb/{n}" for n in z.namelist() if n.endswith(".shp")][0])
    nxt = dict(zip(hb.HYBAS_ID, hb.NEXT_DOWN)); up = defaultdict(list)
    for a, b in nxt.items(): up[b].append(a)
    geom = dict(zip(hb.HYBAS_ID, hb.geometry))
    sindex = hb.sindex
    def catchment(la, lo):
        p = Point(lo, la); ids = [hb.HYBAS_ID.iloc[i] for i in sindex.query(p) if hb.geometry.iloc[i].contains(p)]
        if not ids: return None
        todo, seen = [ids[0]], set()
        while todo:
            x = todo.pop(); seen.add(x); todo += [u for u in up[x] if u not in seen]
        return unary_union([geom[i] for i in seen])
    def cover(poly):
        minx, miny, maxx, maxy = poly.bounds; counts = defaultdict(int)
        for ty in range(int(math.floor(miny / 3) * 3), int(maxy) + 1, 3):
            for tx in range(int(math.floor(minx / 3) * 3), int(maxx) + 1, 3):
                tile = f"{'S' if ty < 0 else 'N'}{abs(ty + (3 if ty < 0 else 0)):02d}E{tx:03d}"
                url = f"https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_{tile}_Map.tif"
                try:
                    with rasterio.open(url, overview_level=4) as src:
                        img, _ = rasterio.mask.mask(src, [poly], crop=True, nodata=0)
                        vals, cnt = np.unique(img[img > 0], return_counts=True)
                        for v, c in zip(vals, cnt): counts[int(v)] += int(c)
                except Exception as e:
                    pass
        tot = sum(counts.values())
        return None if not tot else sum(counts[c] for c in (30, 40, 50, 60)) / tot
    res = []
    for b, (la, lo) in sorted(beaches.items(), key=lambda x: x[1][0]):
        gs = sorted(((km(la, lo, *ll), s) for s, ll in gauges.items() if km(la, lo, *ll) <= 60), key=lambda x: x[0])
        gs = [(d, s) for d, s in gs if sum(1 for k in mflow if k[0] == s) >= 120]
        if not gs: print(f"  - {b}: no gauge with 10+ years within 60 km"); continue
        d, s = gs[0]
        months = sorted(m for m in beachmonths[b] if (s, *m) in mflow)
        if len(months) < 60: print(f"  - {b}: only {len(months)} months overlap"); continue
        hi = set()
        for mo in range(1, 13):
            v = sorted(mflow[(s, y, mo)] for (y, m) in months if m == mo)
            if not v: continue
            cut = v[int(0.75 * len(v))] if len(v) > 3 else 1e18
            hi |= {(y, m) for (y, m) in months if m == mo and mflow[(s, y, m)] >= cut}
        ch = sum(bull[b][m] for m in hi); co = sum(bull[b][m] for m in months if m not in hi)
        nh, no = len(hi), len(months) - len(hi)
        if co == 0 or nh == 0: continue
        rr = (ch / nh) / (co / no)
        poly = catchment(*gauges[s]); cl = cover(poly) if poly is not None else None
        res.append((b, sum(bull[b].values()), s, round(d), rr, cl, poly.area * 111 * 111 if poly is not None else None))
        print(f"  - {b} ({la:.2f}): {sum(bull[b].values())} bull sharks; gauge {s} {d:.0f} km; high-flow rate ratio {rr:.2f}; catchment {'' if poly is None else f'{poly.area*111*111*math.cos(math.radians(la)):.0f} km², '}cleared/farmed/built {'?' if cl is None else f'{cl:.0%}'}")
    ok = [r for r in res if r[5] is not None]
    if len(ok) >= 5:
        from scipy.stats import spearmanr
        rho = spearmanr([r[5] for r in ok], [r[4] for r in ok])
        med = st.median(r[5] for r in ok)
        hiC = [r[4] for r in ok if r[5] > med]; loC = [r[4] for r in ok if r[5] <= med]
        print(f"- {len(ok)} beaches: Spearman (cleared share vs high-flow rise) rho={rho.statistic:.2f}, p={rho.pvalue:.3f}; "
              f"median rise {st.median(hiC):.2f} where catchments are more cleared, {st.median(loC):.2f} where less")

for name, f in (("C34", c34), ("C33", c33)):
    try: f()
    except Exception as e:
        import traceback; traceback.print_exc(); print(f"\n{name} failed: {type(e).__name__}: {str(e)[:300]}")
