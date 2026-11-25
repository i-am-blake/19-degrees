"""Look only: data for two tool previews (beach season calendar, rain watch). Changes nothing on the site.
Calendar: NOAA OISST v2.1 daily (NOAA PSL OPeNDAP), days at 19 C or warmer each July-June season, 1982-83 to 2025-26.
Rain: GHCN-Daily rain gauges (NOAA NCEI) inside each river's HydroBASINS catchment; rule from Werry et al. 2018
(100 mm or more across the catchment, bull shark catch up 1-8 days later, Gold Coast)."""
import concurrent.futures as cf, csv, datetime as dt, io, json, math, os, sys, time, urllib.request, zipfile
from collections import defaultdict
import numpy as np
UA = {"User-Agent": "19-degrees/1.0 (+https://19-degrees.org)"}
def get(u, t=300):
    for k in range(4):
        try: return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=t).read()
        except Exception as e:
            if "404" in str(e): raise
            time.sleep(5 * (k + 1))
    raise RuntimeError("could not fetch " + u)
B = {  # name: (sea point, river point, river)
    "Gold Coast": ((-28.0, 153.55), (-27.99, 153.39), "Nerang"),
    "Ballina": ((-28.87, 153.7), (-28.86, 153.55), "Richmond"),
    "Coffs Harbour": ((-30.3, 153.3), (-30.29, 153.12), "Coffs Creek"),
    "Port Macquarie": ((-31.45, 153.05), (-31.43, 152.88), "Hastings"),
    "Newcastle": ((-32.95, 151.9), (-32.88, 151.70), "Hunter"),
    "Sydney": ((-33.9, 151.35), (-33.83, 151.10), "Parramatta"),
    "Wollongong": ((-34.45, 151.0), (-34.53, 150.80), "Lake Illawarra"),
    "Jervis Bay": ((-35.1, 150.85), (-34.88, 150.65), "Shoalhaven"),
    "Batemans Bay": ((-35.75, 150.35), (-35.70, 150.15), "Clyde"),
    "Eden": ((-37.05, 150.05), (-37.10, 149.86), "Towamba"),
}
OUT = {"made": dt.date.today().isoformat()}

def calendar():
    import xarray as xr
    days = {n: {} for n in B}; cell = {}
    E = ("https://coastwatch.pfeg.noaa.gov/erddap/griddap/ncdcOisst21Agg_LonPM180.nc?sst[({a}):1:({b})][(0.0)][(-37.375):1:(-27.625)][(149.875):1:(153.875)]")
    for y in range(1982, dt.date.today().year + 1):
        box = None
        for k in range(6):
            try:
                ds = xr.open_dataset(f"https://psl.noaa.gov/thredds/dodsC/Datasets/noaa.oisst.v2.highres/sst.day.mean.{y}.nc")
                box = ds.sst.sel(lat=slice(-37.4, -27.6), lon=slice(149.8, 154.0)).load(); break
            except Exception as e: print(y, "PSL retry", repr(e)[:120], flush=True); time.sleep(5)
            try:
                b = min(dt.date(y, 12, 31), dt.date.today() - dt.timedelta(9))
                open("oi.nc", "wb").write(get(E.format(a=f"{y}-01-01", b=b.isoformat()), 900))
                box = xr.open_dataset("oi.nc").sst.isel(zlev=0).rename(latitude="lat", longitude="lon").load(); break
            except Exception as e: print(y, "ERDDAP retry", repr(e)[:120], flush=True); time.sleep(20)
        if box is None: raise RuntimeError(f"OISST {y}")
        for n, (sea, _, _) in B.items():
            if n not in cell:  # nearest ocean cell
                la, lo = box.lat.values, box.lon.values; v = box.isel(time=0).values
                best = min(((math.hypot(la[i] - sea[0], (lo[j] - sea[1]) * math.cos(math.radians(sea[0]))), i, j)
                            for i in range(len(la)) for j in range(len(lo)) if not np.isnan(v[i, j])))
                cell[n] = (best[1], best[2], float(la[best[1]]), float(lo[best[2]]))
            i, j = cell[n][:2]
            for t, x in zip(box.time.values, box.values[:, i, j]):
                if not np.isnan(x): days[n][str(t)[:10]] = float(x)
        print("OISST", y, "ok", flush=True)
    from scipy import stats
    res = {}
    for n, d in days.items():
        def season(y):  # July y to June y+1
            a = dt.date(y, 7, 1); return [d.get((a + dt.timedelta(k)).isoformat()) for k in range((dt.date(y + 1, 7, 1) - a).days)]
        yrs = [y for y in range(1982, 2026) if all(v is not None for v in season(y))]
        cnt = {y: sum(v >= 19 for v in season(y)) for y in yrs}
        def clim(ys):  # mean temperature for each day of the season, smoothed over 15 days
            m = np.array([season(y)[:365] for y in ys]).mean(0); p = np.concatenate([m[-7:], m, m[:7]])
            s = np.convolve(p, np.ones(15) / 15, "valid"); on = np.where(s >= 19)[0]
            if len(on) == 0: return {"days": 0}
            if len(on) == 365: return {"days": 365, "all_year": True}
            f = lambda k: (dt.date(2001, 7, 1) + dt.timedelta(int(k))).strftime("%d %b")
            return {"days": int(len(on)), "start": f(on[0]), "end": f(on[-1]), "min": round(float(s.min()), 1), "max": round(float(s.max()), 1)}
        lr = stats.linregress(yrs, [cnt[y] for y in yrs])
        last = sorted(d)[-1]; wk = [d[k] for k in sorted(d)[-7:]]
        res[n] = {"cell": cell[n][2:], "then": clim([y for y in yrs if y <= 1991]), "now": clim([y for y in yrs if y >= 2016]),
                  "per_decade": round(lr.slope * 10, 1), "p": round(lr.pvalue, 4), "seasons": len(yrs),
                  "by_season": cnt, "latest": last, "latest_week": round(sum(wk) / len(wk), 1)}
        print(n, json.dumps({k: v for k, v in res[n].items() if k != "by_season"}), flush=True)
    return res

def rain():
    import geopandas as gpd
    from shapely.geometry import Point
    from shapely.ops import unary_union
    z = zipfile.ZipFile(io.BytesIO(get("https://data.hydrosheds.org/file/HydroBASINS/standard/hybas_au_lev08_v1c.zip"))); z.extractall("hb")
    hb = gpd.read_file([f"hb/{n}" for n in z.namelist() if n.endswith(".shp")][0])
    up = defaultdict(list)
    for a, b in zip(hb.HYBAS_ID, hb.NEXT_DOWN): up[b].append(a)
    geom = dict(zip(hb.HYBAS_ID, hb.geometry)); six = hb.sindex
    def catchment(la, lo):
        for dx in (0, -0.02, -0.04, -0.06, -0.08, -0.1):
            p = Point(lo + dx, la); ids = [hb.HYBAS_ID.iloc[i] for i in six.query(p) if hb.geometry.iloc[i].contains(p)]
            if ids: break
        else: return None
        todo, seen = [ids[0]], set()
        while todo: x = todo.pop(); seen.add(x); todo += [u for u in up[x] if u not in seen]
        return unary_union([geom[i] for i in seen])
    G = "https://www.ncei.noaa.gov/pub/data/ghcn/daily/"
    st = {l[:11]: (float(l[12:20]), float(l[21:30]), l[41:71].strip()) for l in get(G + "ghcnd-stations.txt").decode().splitlines() if l.startswith("ASN")}
    inv = {l[:11]: int(l[41:45]) for l in get(G + "ghcnd-inventory.txt").decode().splitlines() if l.startswith("ASN") and l[31:35] == "PRCP"}
    res = {}
    for n, (_, rp, river) in B.items():
        poly = catchment(*rp)
        if poly is None: res[n] = {"river": river, "error": "no catchment"}; print(n, "no catchment"); continue
        area = round(gpd.GeoSeries([poly], crs=4326).to_crs(3577).area.iloc[0] / 1e6)
        ids = [s for s, (la, lo, _) in st.items() if inv.get(s, 0) >= 2026 and poly.buffer(0.02).contains(Point(lo, la))]
        def one(s):
            try: return s, list(csv.DictReader(io.StringIO(get(f"https://www.ncei.noaa.gov/data/global-historical-climatology-network-daily/access/{s}.csv", 120).decode())))
            except Exception: return s, []
        daily = defaultdict(list)
        with cf.ThreadPoolExecutor(8) as ex:
            for s, rows in ex.map(one, ids[:60]):
                for r in rows:
                    v = (r.get("PRCP") or "").strip()
                    if v and r["DATE"] >= "1990-01-01": daily[r["DATE"]].append(float(v) / 10)  # tenths of mm
        mean = {k: sum(v) / len(v) for k, v in daily.items() if len(v) >= max(1, len(ids[:60]) // 4)}
        if not mean: res[n] = {"river": river, "area_km2": area, "stations": len(ids), "error": "no data"}; print(n, "no rain data"); continue
        ks = sorted(mean); last = ks[-1]; L = dt.date.fromisoformat(last)
        D = lambda k: mean.get((L - dt.timedelta(k)).isoformat(), 0.0)
        wk = lambda e: sum(mean.get((e - dt.timedelta(k)).isoformat(), 0.0) for k in range(7))
        events, k0 = [], dt.date(2000, 1, 1); e = k0; prev = None
        while e <= L:  # weeks with 100 mm or more, counted once per rain event
            if wk(e) >= 100 and (prev is None or (e - prev).days > 7): events.append(e.isoformat())
            if wk(e) >= 100: prev = e
            e += dt.timedelta(1)
        yrs = [int(k[:4]) for k in ks if "2000-01-01" <= k <= "2025-12-31"]
        ann = {y: 0.0 for y in set(yrs)}
        for k in ks:
            if "2000" <= k[:4] <= "2025": ann[int(k[:4])] += mean[k]
        res[n] = {"river": river, "area_km2": area, "stations": len(ids), "stations_used": len(ids[:60]), "latest": last,
                  "last8": [round(D(k), 1) for k in range(7, -1, -1)], "week_total": round(wk(L), 1),
                  "last_100mm_week_ended": events[-1] if events else None, "events_per_year_2000_25": round(len([x for x in events if x[:4] <= "2025"]) / 26, 1),
                  "annual_mm_2000_25": round(sum(ann.values()) / max(1, len(ann)))}
        print(n, json.dumps(res[n]), flush=True)
    return res

def wdo():  # is there current daily rain from Water Data Online (BoM)?
    import urllib.parse
    B = "http://www.bom.gov.au/waterdata/services?"
    q = lambda **p: json.loads(get(B + urllib.parse.urlencode({"service": "kisters", "type": "queryServices", "format": "json", **p}), 300))
    res = {}
    for par in ("Rainfall", "Water Course Discharge"):
        stl = q(request="getStationList", parametertype_name=par, returnfields="station_no,station_name,station_latitude,station_longitude", bBox="149.5,-37.5,153.7,-27.8")
        cand = [dict(zip(stl[0], r)) for r in stl[1:]]; print(par, len(cand), "stations", flush=True); out = {}
        for n, (_, rp, river) in B_.items():
            near = sorted(cand, key=lambda s: math.hypot(float(s["station_latitude"]) - rp[0], float(s["station_longitude"]) - rp[1]))[:2]
            for s in near:
                try:
                    ts = q(request="getTimeseriesList", station_no=s["station_no"], parametertype_name=par, returnfields="ts_id,ts_name")
                    names = [r[1] for r in ts[1:]]; pick = next((r for r in ts[1:] if "Daily" in r[1] and ("Total" in r[1] or "Mean" in r[1])), None)
                    last = None
                    if pick:
                        v = q(request="getTimeseriesValues", ts_id=pick[0], **{"from": (dt.date.today() - dt.timedelta(20)).isoformat(), "to": dt.date.today().isoformat()}, returnfields="Timestamp,Value")
                        d = v[0]["data"] if isinstance(v, list) else v["data"]; last = [(t[:10], x) for t, x in d if x is not None][-3:]
                    out.setdefault(n, []).append({"station": s["station_name"], "no": s["station_no"], "ts": names[:8], "used": pick[1] if pick else None, "last": last})
                    print(par, n, json.dumps(out[n][-1])[:400], flush=True); time.sleep(1)
                except Exception as e: print(par, n, s["station_name"], "error", repr(e)[:150], flush=True)
        res[par] = out
    return res
B_ = B
PARTS = sys.argv[1].split(",") if len(sys.argv) > 1 else ["rain", "calendar"]
for k, f in (("wdo", wdo), ("rain", rain), ("calendar", calendar)):
    if k not in PARTS: continue
    try: OUT[k] = f()
    except Exception as e: print(k, "failed:", repr(e)[:300])
json.dump(OUT, open("../tools.json", "w"), indent=1)
