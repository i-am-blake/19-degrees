"""First tests of seven claims with free data (C32 natural-only runs, C33, C34, C35, C42, and the sea temperature part of C45).
Usage: python3 -I freetests19.py <asid.csv> <ocean-data dir> <imos-data dir> <out freetests.json>
Run monthly by fetch-freetests.yml; the weekly update reads the saved result. Each part keeps its last result if a source
is down. All tests are exploratory: the tests were set out on each claim card before these data were looked at, but the
details below (distances, periods, thresholds) were chosen by this script's author.
C32  CMIP6 sea temperature off Sydney (Pangeo public archive, CC BY 4.0): months a year at 19C or warmer in 1991-2014 in
     runs with all forcings ('historical') against natural forcings only ('hist-nat'), each model's change from 1950-79
     added to HadISST's 1950-79 average year.
C33  Queensland Shark Control Program catch (CC BY 4.0) by program area and month; daily flow at the main river's gauge
     with the largest catchment and 10+ years since 1996 (Water Data Online, BoM, CC BY 3.0 AU); the gauge's catchment
     from HydroBASINS level 8 (HydroSHEDS; free to use with citation of Lehner and Grill 2013) and its land cover from ESA WorldCover 2021 (CC BY 4.0). Rise = bull
     sharks caught per month in the river's highest-flow quarter of each calendar month, over other months.
C34  Unprovoked bites (Australian Shark-Incident Database) against 20 random beaches within 50 km: distance to the
     nearest boat ramp or fish-cleaning table (OpenStreetMap, ODbL). Two-sided sign test against a half.
C35  IMOS Animal Tracking (CC BY 4.0): share of receiver-months with a tagged bull shark, built-up estuaries against
     natural estuaries on the NSW and southeast Queensland coast (Fisher's exact test). Which estuary is which is set below.
C42  Atlas of Living Australia (CC BY 4.0, per record): ten tropical reef fish off eastern Australia (150-155E, 24-38S); per
     period and 1-degree band, records of the species per record of any fish (allowing for where people look); the
     southern limit is the southernmost band at 5% or more of the species' peak rate. Median over species.
C45  Hawaii DLNR incidents and NOAA OISST around five islands: share of tiger shark incidents in September-November in
     years with a warmer than median autumn sea against cooler ones (Fisher's exact test)."""
import csv, glob, gzip, io, json, math, os, random, statistics as st, sys, time, urllib.parse, urllib.request, zipfile, datetime as dt
from collections import defaultdict
ASID, OCEAN, IMOS, OUT = sys.argv[1:5]
from scipy.stats import binomtest, fisher_exact, spearmanr
UA = {"User-Agent": "19-degrees/1.0 (+https://19-degrees.org)"}
UAB = {"User-Agent": "Mozilla/5.0 (19-degrees.org open data)"}
def get(u, data=None, t=600, h=None):
    for k in range(4):
        try: return urllib.request.urlopen(urllib.request.Request(u, data=data, headers=h or UA), timeout=t).read()
        except Exception as e:
            err = e; time.sleep(20 * (k + 1))
    raise err
def km(a, b, c, d): return math.hypot((a - c) * 111, (b - d) * 111 * math.cos(math.radians((a + c) / 2)))
def pr(x): return round(float(x), 4)
OUTD = json.load(open(OUT)) if os.path.exists(OUT) else {}
ASIDROWS = [r for r in csv.DictReader(open(ASID, encoding="utf-8")) if r["Provoked/unprovoked"].strip() == "unprovoked"]

def c34():
    A = '[out:json][timeout:900];area["ISO3166-1"="AU"][admin_level=2]->.a;'
    ov = lambda q: json.loads(get("https://overpass-api.de/api/interpreter", data=urllib.parse.urlencode({"data": A + q}).encode()))["elements"]
    ctr = lambda e: (e.get("lat") or e["center"]["lat"], e.get("lon") or e["center"]["lon"])
    ramps = [ctr(e) for e in ov('(nwr["leisure"="slipway"](area.a);nwr["amenity"~"fish_clean"](area.a);nwr["man_made"~"fish_clean"](area.a););out center;')]
    beaches = [ctr(e) for e in ov('nwr["natural"="beach"](area.a);out center;')]
    if len(ramps) < 1000 or len(beaches) < 3000: raise RuntimeError(f"too few ramps or beaches ({len(ramps)}, {len(beaches)})")
    rg, bg = defaultdict(list), defaultdict(list)
    for p in ramps: rg[(round(p[0]), round(p[1]))].append(p)
    for p in beaches: bg[(round(p[0]), round(p[1]))].append(p)
    def near(la, lo): return min((km(la, lo, *p) for i in (-1, 0, 1) for j in (-1, 0, 1) for p in rg.get((round(la) + i, round(lo) + j), [])), default=1e9)
    random.seed(19); out = {"ramps": len(ramps), "beaches": len(beaches)}
    rows = [r for r in ASIDROWS if r["Latitude"].strip() not in ("", "NA")]
    bull = lambda r: "bull" in r["Shark.common.name"].lower(); coast = lambda r: r["Site.category"].strip().startswith("coastal")
    for key, f in (("all", lambda r: True), ("bull", bull), ("open_coast", coast), ("bull_open_coast", lambda r: bull(r) and coast(r))):
        closer = n = 0; db, dr = [], []
        for r in filter(f, rows):
            la, lo = float(r["Latitude"]), float(r["Longitude"])
            loc = [p for i in (-1, 0, 1) for j in (-1, 0, 1) for p in bg.get((round(la) + i, round(lo) + j), []) if km(la, lo, *p) <= 50]
            if len(loc) < 10: continue
            rnd = st.median(near(*p) for p in random.sample(loc, min(20, len(loc)))); d = near(la, lo)
            if d > 100 or rnd > 100: continue
            n += 1; closer += d < rnd; db.append(d); dr.append(rnd)
        out[key] = dict(n=n, closer=closer, pct=round(100 * closer / n), p=pr(binomtest(closer, n, 0.5).pvalue), bite_km=round(st.median(db), 1), beach_km=round(st.median(dr), 1))
    return out

def c35():
    BUILT = ["Sydney Harbour", "Chowder Bay", "Quarantine", "Georges River", "Port Hacking", "Port Hacking Gate", "Logan", "Upper Logan River", "Sunshine Coast Rivers"]
    NATURAL = ["Clarence River", "Clarence River Array", "Clarence Array", "Kalang-Bellinger Array", "Shoalhaven River", "Wallis Lake"]
    dep, det = defaultdict(set), defaultdict(set)
    for f in glob.glob(os.path.join(IMOS, "*.csv.gz")):
        seen = set()
        for r in csv.DictReader(gzip.open(f, "rt")):
            k = r["installation_name"]
            if k not in BUILT + NATURAL: continue
            if "Bull" in r["species_common_name"]: det[k].add(r["date_hour_UTC"][:7])
            key = (k, r["receiver_deployment_id"])
            if key in seen: continue
            seen.add(key)
            try: a, b = dt.date.fromisoformat(r["receiver_deployment_datetime_UTC"][:10]), dt.date.fromisoformat(r["receiver_recovery_datetime_UTC"][:10])
            except ValueError: continue
            y, m = a.year, a.month
            while (y, m) <= (b.year, b.month): dep[k].add(f"{y}-{m:02d}"); m += 1; y += m > 12; m = (m - 1) % 12 + 1
    g = {}
    for lab, S in (("built", BUILT), ("natural", NATURAL)):
        months = sum(len(dep[k]) for k in S); hit = sum(len(det[k] & dep[k]) for k in S)
        g[lab] = dict(sites=[k for k in S if dep[k]], months=months, with_bull=hit, pct=round(100 * hit / months) if months else None)
    b, n = g["built"], g["natural"]
    if b["months"] < 100 or n["months"] < 60: raise RuntimeError("too few receiver-months")
    g["p"] = pr(fisher_exact([[b["with_bull"], b["months"] - b["with_bull"]], [n["with_bull"], n["months"] - n["with_bull"]]])[1])
    return g

def c42():
    B = "https://biocache-ws.ala.org.au/ws/occurrences/search?"
    SP = ["Abudefduf vaigiensis", "Abudefduf sexfasciatus", "Abudefduf whitleyi", "Acanthurus triostegus", "Acanthurus nigrofuscus",
          "Chaetodon auriga", "Chaetodon flavirostris", "Pomacentrus coelestis", "Zanclus cornutus", "Heniochus acuminatus"]
    def cells(q, y0, y1):
        p = {"q": q, "fq": [f"year:[{y0} TO {y1}]", "decimalLatitude:[-38 TO -24]", "decimalLongitude:[150 TO 155]"], "facets": "point-1", "flimit": "-1", "pageSize": "0"}
        o = {}
        for fr in (json.loads(get(B + urllib.parse.urlencode(p, doseq=True))).get("facetResults") or [{}])[0].get("fieldResult", []):
            try: la, lo = map(float, fr["label"].split(",")); o[round(la)] = o.get(round(la), 0) + fr["count"]
            except Exception: pass
        return o
    per = []
    for y0, y1 in ((1995, 2004), (2005, 2014), (2015, 2025)):
        eff = cells("class:Actinopterygii", y0, y1); lims = []; recs = 0
        for s in SP:
            c = cells(f'taxon_name:"{s}"', y0, y1); recs += sum(c.values())
            rate = {la: c.get(la, 0) / eff[la] for la in eff if eff[la] >= 200}
            if rate and max(rate.values()) > 0:
                top = max(rate.values()); lims.append(min(la for la, v in rate.items() if v >= 0.05 * top))
        per.append(dict(years=f"{y0}–{y1}", species=len(lims), records=recs, effort=sum(eff.values()), median_limit=st.median(lims) if lims else None))
        time.sleep(1)
    if not all(x["median_limit"] for x in per): raise RuntimeError("missing limits")
    return dict(periods=per, species=len(SP))

def c45():
    inc = []
    for r in csv.DictReader(open(os.path.join(OCEAN, "hawaii_incidents.csv"), encoding="utf-8")):
        d = r["Date and Time"].strip()[:10].split("/")
        if len(d) == 3 and d[0].isdigit() and "tiger" in r["Shark"].lower(): inc.append((int(d[0]), int(d[1])))
    sst = defaultdict(list)
    for f in glob.glob(os.path.join(OCEAN, "oisst_hawaii_*.csv")):
        for r in csv.DictReader(open(f)):
            if r["time"][5:7] in ("09", "10", "11"): sst[int(r["time"][:4])].append(float(r["sst"]))
    aut = {y: st.mean(v) for y, v in sst.items() if len(v) > 300}
    ys = sorted({y for y, _ in inc if y in aut}); med = st.median(aut[y] for y in ys)
    son = lambda s: sum(m in (9, 10, 11) for _, m in s)
    w = [x for x in inc if x[0] in aut and aut[x[0]] > med]; c = [x for x in inc if x[0] in aut and aut[x[0]] <= med]
    return dict(n=len(w) + len(c), warm=dict(n=len(w), son=son(w), pct=round(100 * son(w) / len(w))), cool=dict(n=len(c), son=son(c), pct=round(100 * son(c) / len(c))),
                p=pr(fisher_exact([[son(w), len(w) - son(w)], [son(c), len(c) - son(c)]])[1]), years=len(ys))

def c32():
    import numpy as np, pandas as pd, xarray as xr, gcsfs
    cat = pd.read_csv("https://storage.googleapis.com/cmip6/pangeo-cmip6.csv")
    cat = cat[(cat.variable_id == "tos") & (cat.table_id == "Omon") & (cat.experiment_id.isin(["historical", "hist-nat"]))]
    both = sorted(set(cat[cat.experiment_id == "hist-nat"].source_id) & set(cat[cat.experiment_id == "historical"].source_id))
    obs = defaultdict(list)
    t = get("https://coastwatch.pfeg.noaa.gov/erddap/griddap/erdHadISST.csv?sst%5B(1950-01-16):1:(2014-12-16)%5D%5B(-33.5)%5D%5B(151.8)%5D").decode()
    rec = []
    for r in list(csv.reader(t.splitlines()))[2:]:
        if r[3] in ("NaN", ""): continue
        if r[0] < "1980": obs[int(r[0][5:7])].append(float(r[3]))
        elif r[0] >= "1991": rec.append(float(r[3]))
    clim = {m: st.mean(v) for m, v in obs.items()}
    fs = gcsfs.GCSFileSystem(token="anon"); res = []
    for src in both:
        o = {}
        for exp in ("historical", "hist-nat"):
            z = cat[(cat.source_id == src) & (cat.experiment_id == exp)].sort_values("member_id")
            ds = xr.open_zarr(fs.get_mapper(z.zstore.iloc[0]), consolidated=True)
            la = [v for v in ds.coords if v.lower() in ("lat", "latitude", "nav_lat")][0]; lo = [v for v in ds.coords if v.lower() in ("lon", "longitude", "nav_lon")][0]
            s = ds.tos; d = ((ds[la] + 33.5) ** 2 + (((ds[lo] % 360) - 151.8) * math.cos(math.radians(33.5))) ** 2).where(s.isel(time=0).notnull())
            idx = np.unravel_index(int(np.nanargmin(d.values)), d.shape)
            x = s.isel({k: i for k, i in zip(d.dims, idx)}).load().to_series()
            x.index = pd.to_datetime([str(v)[:10] for v in x.index.astype(str)])
            if x.mean() > 100: x = x - 273.15
            base = x["1950":"1979"].groupby(x["1950":"1979"].index.month).mean(); r_ = x["1991":"2014"]
            o[exp] = sum(clim[d0.month] + a >= 19 for d0, a in (r_ - base.reindex(r_.index.month).values).items()) / (len(r_) / 12)
        res.append(dict(model=src, all=round(o["historical"], 1), natural=round(o["hist-nat"], 1)))
    if len(res) < 3: raise RuntimeError("fewer than 3 models")
    return dict(models=res, base=sum(clim[m] >= 19 for m in range(1, 13)), observed=round(sum(v >= 19 for v in rec) / (len(rec) / 12), 1),
                all=round(st.median(r["all"] for r in res), 1), natural=round(st.median(r["natural"] for r in res), 1))

def c33():
    import openpyxl, geopandas as gpd, numpy as np, rasterio, rasterio.mask
    from shapely.geometry import Point
    from shapely.ops import unary_union
    AREA = {"Gold Coast": (-28.02, 153.43), "Nth Stradbroke Is.": (-27.43, 153.53), "Bribie Island": (-27.07, 153.20), "Sunshine Coast South": (-26.80, 153.13),
            "Sunshine Coast North": (-26.45, 153.08), "Rainbow Beach": (-25.90, 153.09), "Bundaberg": (-24.84, 152.45), "Gladstone": (-23.95, 151.37),
            "Capricorn Coast": (-23.15, 150.77), "Mackay": (-21.10, 149.20), "Townsville": (-19.25, 146.82), "Cairns": (-16.85, 145.75)}
    RIVER = {"Gold Coast": "Nerang", "Nth Stradbroke Is.": "Brisbane River", "Bribie Island": "Caboolture", "Sunshine Coast South": "Mooloolah",
             "Sunshine Coast North": "Maroochy", "Rainbow Beach": "Mary River", "Bundaberg": "Burnett", "Gladstone": "Boyne",
             "Capricorn Coast": "Fitzroy", "Mackay": "Pioneer", "Townsville": "Ross River", "Cairns": "Barron"}  # the main river at each area's coast
    bull, months_on = defaultdict(lambda: defaultdict(int)), defaultdict(set)
    for r in openpyxl.load_workbook(os.path.join(OCEAN, "scp-numbers-caught.xlsx"), read_only=True).worksheets[0].iter_rows(min_row=2, values_only=True):
        months_on[r[3]].add((r[0], r[1]))
        if r[9] == "BULL WHALER": bull[r[3]][(r[0], r[1])] += 1
    B = "http://www.bom.gov.au/waterdata/services?"
    q = lambda **p: json.loads(get(B + urllib.parse.urlencode({"service": "kisters", "type": "queryServices", "format": "json", **p}), t=300, h=UAB))
    stl = q(request="getStationList", parametertype_name="Water Course Discharge", returnfields="station_no,station_name,station_latitude,station_longitude", bBox="145.0,-28.6,153.7,-16.4")
    cand = [dict(zip(stl[0], r)) for r in stl[1:]]
    flow, pos = defaultdict(list), {}
    for a in AREA:
        for s in [s for s in cand if RIVER[a].lower() in s["station_name"].lower()]:
            pos[s["station_no"]] = (a, float(s["station_latitude"]), float(s["station_longitude"]))
            try:
                ts = q(request="getTimeseriesList", station_no=s["station_no"], parametertype_name="Water Course Discharge", ts_name="DMQaQc.Merged.DailyMean.24HR", returnfields="ts_id")
                if len(ts) < 2: continue
                v = q(request="getTimeseriesValues", ts_id=ts[1][0], **{"from": "1996-01-01", "to": dt.date.today().isoformat()}, returnfields="Timestamp,Value")
                for t, x in (v[0]["data"] if isinstance(v, list) else v["data"]):
                    if x is not None: flow[(s["station_no"], int(t[:4]), int(t[5:7]))].append(float(x))
                time.sleep(1)
            except Exception: pass
    mflow = {k: sum(v) / len(v) for k, v in flow.items() if len(v) >= 20}
    z = zipfile.ZipFile(io.BytesIO(get("https://data.hydrosheds.org/file/HydroBASINS/standard/hybas_au_lev08_v1c.zip"))); z.extractall("hb")
    hb = gpd.read_file([f"hb/{n}" for n in z.namelist() if n.endswith(".shp")][0])
    up = defaultdict(list)
    for a, b in zip(hb.HYBAS_ID, hb.NEXT_DOWN): up[b].append(a)
    geom = dict(zip(hb.HYBAS_ID, hb.geometry)); six = hb.sindex
    def catchment(la, lo):
        p = Point(lo, la); ids = [hb.HYBAS_ID.iloc[i] for i in six.query(p) if hb.geometry.iloc[i].contains(p)]
        if not ids: return None
        todo, seen = [ids[0]], set()
        while todo: x = todo.pop(); seen.add(x); todo += [u for u in up[x] if u not in seen]
        return unary_union([geom[i] for i in seen])
    def cleared(poly):
        x0, y0, x1, y1 = poly.bounds; cnt = defaultdict(int)
        for ty in range(int(math.floor(y0 / 3) * 3), int(y1) + 1, 3):
            for tx in range(int(math.floor(x0 / 3) * 3), int(x1) + 1, 3):
                u = f"https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_{'S' if ty < 0 else 'N'}{abs(ty):02d}E{tx:03d}_Map.tif"
                try:
                    with rasterio.open(u, overview_level=4) as s:
                        img, _ = rasterio.mask.mask(s, [poly], crop=True, nodata=0)
                        for v, c in zip(*np.unique(img[img > 0], return_counts=True)): cnt[int(v)] += int(c)
                except ValueError: pass  # the catchment doesn't reach this tile
        tot = sum(cnt.values()); return None if not tot else sum(cnt[c] for c in (30, 40, 50, 60)) / tot  # grassland, cropland, built-up, bare
    rows = []
    for a, (la, lo) in AREA.items():
        if sum(bull[a].values()) < 15: continue
        opts = [s for s, v in pos.items() if v[0] == a and sum(1 for k in mflow if k[0] == s) >= 120]
        if not opts: rows.append(dict(area=a, river=RIVER[a], skipped="no gauge with 10+ years since 1996")); continue
        polys = {o: catchment(*pos[o][1:]) for o in opts}
        s = max(opts, key=lambda o: polys[o].area if polys[o] is not None else 0)
        mo = sorted(m for m in months_on[a] if (s, *m) in mflow)
        if len(mo) < 60: rows.append(dict(area=a, river=RIVER[a], skipped=f"only {len(mo)} months with both catch and flow")); continue
        hi = set()
        for c in range(1, 13):
            v = sorted(mflow[(s, y, m)] for y, m in mo if m == c)
            if len(v) > 3: hi |= {(y, m) for y, m in mo if m == c and mflow[(s, y, m)] >= v[int(0.75 * len(v))]}
        ch = sum(bull[a][m] for m in hi); co = sum(bull[a][m] for m in mo if m not in hi)
        if not co or not hi: continue
        cl = cleared(polys[s])
        rows.append(dict(area=a, river=RIVER[a], gauge=s, km=round(km(la, lo, *pos[s][1:])), bull=sum(bull[a].values()), rise=round((ch / len(hi)) / (co / (len(mo) - len(hi))), 2),
                         cleared_pct=None if cl is None else round(100 * cl), catchment_km2=round(polys[s].area * 111 * 111 * math.cos(math.radians(pos[s][1])))))
    ok = [r for r in rows if r.get("cleared_pct") is not None]
    if len(ok) < 6: raise RuntimeError(f"only {len(ok)} areas")
    rho = spearmanr([r["cleared_pct"] for r in ok], [r["rise"] for r in ok]); med = st.median(r["cleared_pct"] for r in ok)
    return dict(areas=rows, n=len(ok), rho=round(float(rho.statistic), 2), p=pr(rho.pvalue), rise_more_cleared=st.median(r["rise"] for r in ok if r["cleared_pct"] > med),
                rise_less_cleared=st.median(r["rise"] for r in ok if r["cleared_pct"] <= med), rises=sum(r["rise"] > 1 for r in ok))

for k, f in (("c45", c45), ("c35", c35), ("c34", c34), ("c42", c42), ("c33", c33), ("c32", c32)):
    try: OUTD[k] = f(); OUTD[k]["updated"] = dt.date.today().isoformat(); print(k, "ok", json.dumps(OUTD[k])[:400])
    except Exception as e: print(f"{k} failed, keeping the last result: {type(e).__name__}: {str(e)[:300]}")
json.dump(OUTD, open(OUT, "w"), indent=1)
