"""Look only: first tests of three open claims with free data. Prints a report; changes nothing.
C34 bites vs boat ramps (OpenStreetMap slipways) against random points on the same stretch of coast.
C42 southern limits of tropical reef fish off eastern Australia by decade (Atlas of Living Australia), allowing for effort.
C32 months at 19C or warmer off Sydney in CMIP6 runs with all forcings vs natural forcings only (Pangeo archive)."""
import csv, json, math, random, statistics as st, sys, time, urllib.parse, urllib.request
UA = {"User-Agent": "19-degrees-explore/1.0 (+https://19-degrees.org)"}
def get(u, data=None, t=300):
    for k in range(4):
        try: return urllib.request.urlopen(urllib.request.Request(u, data=data, headers=UA), timeout=t).read()
        except Exception as e:
            if k == 3: raise
            time.sleep(20 * (k + 1))
def km(a, b, c, d): return math.hypot((a - c) * 111, (b - d) * 111 * math.cos(math.radians((a + c) / 2)))

def c34():
    print("\n## C34 bites and boat ramps\n")
    q = '[out:json][timeout:600];area["ISO3166-1"="AU"][admin_level=2]->.a;(nwr["leisure"="slipway"](area.a);nwr["amenity"~"fish_clean"](area.a);nwr["man_made"~"fish_clean"](area.a););out center tags;'
    els = json.loads(get("https://overpass-api.de/api/interpreter", data=urllib.parse.urlencode({"data": q}).encode()))["elements"]
    pts = [((e.get("lat") or e["center"]["lat"]), (e.get("lon") or e["center"]["lon"]), "slip" if e["tags"].get("leisure") == "slipway" else "fish") for e in els]
    print(f"- OpenStreetMap: {sum(p[2]=='slip' for p in pts)} boat ramps, {sum(p[2]=='fish' for p in pts)} fish-cleaning tables in Australia")
    coast = []
    for f in json.loads(get("https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_10m_coastline.geojson"))["features"]:
        g = f["geometry"]; lines = g["coordinates"] if g["type"] == "MultiLineString" else [g["coordinates"]]
        for ln in lines: coast += [(la, lo) for lo, la in ln if -45 < la < -9 and 112 < lo < 155]
    rows = [r for r in csv.DictReader(open("asid.csv", encoding="utf-8")) if r["Provoked/unprovoked"].strip() == "unprovoked" and r["Latitude"].strip() not in ("", "NA")]
    grid = {}
    for la, lo, _ in pts: grid.setdefault((round(la), round(lo)), []).append((la, lo))
    def near(la, lo):
        best = 1e9
        for i in (-1, 0, 1):
            for j in (-1, 0, 1):
                for a, b in grid.get((round(la) + i, round(lo) + j), []): best = min(best, km(la, lo, a, b))
        return best
    random.seed(19)
    for lab, sel in (("all unprovoked", rows), ("bull shark", [r for r in rows if "bull" in r["Shark.common.name"].lower()]),
                     ("since 2000", [r for r in rows if r["Incident.year"].isdigit() and int(r["Incident.year"]) >= 2000])):
        closer = n = 0; d_b, d_r = [], []
        for r in sel:
            la, lo = float(r["Latitude"]), float(r["Longitude"])
            loc = [c for c in coast if abs(c[0] - la) < 0.5 and abs(c[1] - lo) < 0.6 and km(la, lo, *c) <= 50]
            if len(loc) < 10: continue
            rnd = [near(*c) for c in random.sample(loc, min(20, len(loc)))]
            db = near(la, lo)
            if db > 100 or st.median(rnd) > 100: continue
            n += 1; closer += db < st.median(rnd); d_b.append(db); d_r.append(st.median(rnd))
        from scipy.stats import binomtest
        print(f"- {lab}: {n} bites; median distance to the nearest ramp or table {st.median(d_b):.1f} km vs {st.median(d_r):.1f} km for random coast nearby; "
              f"closer than their local random points: {closer}/{n} ({closer/n:.0%}), p={binomtest(closer, n, 0.5).pvalue:.3f}")

def c42():
    print("\n## C42 tropical reef fish limits off eastern Australia\n")
    B = "https://biocache-ws.ala.org.au/ws/occurrences/search?"
    SP = ["Abudefduf vaigiensis", "Abudefduf sexfasciatus", "Abudefduf whitleyi", "Acanthurus triostegus", "Acanthurus nigrofuscus",
          "Chaetodon auriga", "Chaetodon flavirostris", "Pomacentrus coelestis", "Zanclus cornutus", "Heniochus acuminatus"]
    DEC = [(1980, 1994), (1995, 2004), (2005, 2014), (2015, 2025)]
    def cells(q, y0, y1):
        p = {"q": q, "fq": [f"year:[{y0} TO {y1}]", "decimalLatitude:[-38 TO -24]", "decimalLongitude:[150 TO 155]"], "facets": "point-1", "flimit": "-1", "pageSize": "0"}
        j = json.loads(get(B + urllib.parse.urlencode(p, doseq=True)))
        out = {}
        for fr in (j.get("facetResults") or [{}])[0].get("fieldResult", []):
            try: la, lo = map(float, fr["label"].split(",")); out[round(la)] = out.get(round(la), 0) + fr["count"]
            except Exception: pass
        return out
    for y0, y1 in DEC:
        eff = cells("class:Actinopterygii", y0, y1)
        lims = []
        for s in SP:
            c = cells(f'taxon_name:"{s}"', y0, y1)
            rate = {la: c.get(la, 0) / eff[la] for la in eff if eff[la] >= 200}
            if not rate or max(rate.values()) == 0: continue
            # southern limit: southernmost 1-degree band where the species is at least 5% of its peak effort-adjusted rate
            top = max(rate.values()); south = min(la for la, v in rate.items() if v >= 0.05 * top)
            lims.append((s, south, sum(c.values())))
        print(f"- {y0}–{y1}: effort (all fish records) {sum(eff.values())}; limits " + "; ".join(f"{s.split()[0][:4]}. {s.split()[1]} {la}° ({n})" for s, la, n in lims)
              + (f"; median limit {st.median(l[1] for l in lims)}°" if lims else ""))
        time.sleep(1)

def c32():
    print("\n## C32 human vs natural forcing, months at 19°C+ off Sydney\n")
    import numpy as np, pandas as pd, xarray as xr, gcsfs
    cat = pd.read_csv("https://storage.googleapis.com/cmip6/pangeo-cmip6.csv")
    cat = cat[(cat.variable_id == "tos") & (cat.table_id == "Omon") & (cat.experiment_id.isin(["historical", "hist-nat"]))]
    both = set(cat[cat.experiment_id == "hist-nat"].source_id) & set(cat[cat.experiment_id == "historical"].source_id)
    print(f"- models with both runs: {len(both)}: {', '.join(sorted(both))}")
    obs = {}
    t = get("https://coastwatch.pfeg.noaa.gov/erddap/griddap/erdHadISST.csv?sst%5B(1950-01-16):1:(1979-12-16)%5D%5B(-33.5)%5D%5B(151.8)%5D").decode()
    for r in list(csv.reader(t.splitlines()))[2:]:
        if r[3] not in ("NaN", ""): obs.setdefault(int(r[0][5:7]), []).append(float(r[3]))
    clim = {m: st.mean(v) for m, v in obs.items()}
    fs = gcsfs.GCSFileSystem(token="anon")
    res = []
    for src in sorted(both):
        out = {}
        for exp in ("historical", "hist-nat"):
            z = cat[(cat.source_id == src) & (cat.experiment_id == exp)].sort_values("member_id")
            if not len(z): continue
            try:
                ds = xr.open_zarr(fs.get_mapper(z.zstore.iloc[0]), consolidated=True)
                lat = [v for v in ds.coords if v.lower() in ("lat", "latitude", "nav_lat")]; lon = [v for v in ds.coords if v.lower() in ("lon", "longitude", "nav_lon")]
                LA, LO = ds[lat[0]], ds[lon[0]] % 360
                d = (LA + 33.5) ** 2 + ((LO - 151.8) * math.cos(math.radians(33.5))) ** 2
                s = ds.tos.where(ds.tos.notnull())
                d = d.where(s.isel(time=0).notnull())
                idx = np.unravel_index(int(np.nanargmin(d.values)), d.shape)
                x = s.isel({dd: i for dd, i in zip(d.dims, idx)}).load().to_series()
                x.index = pd.to_datetime([str(v)[:10] for v in x.index.astype(str)])
                if x.mean() > 100: x = x - 273.15
                base = x["1950":"1979"].groupby(x["1950":"1979"].index.month).mean()
                rec = x["1991":"2014"]
                anom = rec - base.reindex(rec.index.month).values
                warm = sum(1 for d0, a in anom.items() if clim[d0.month] + a >= 19) / (len(anom) / 12)
                out[exp] = warm
            except Exception as e:
                print(f"  - {src} {exp}: {type(e).__name__} {str(e)[:120]}")
        if len(out) == 2: res.append((src, out["historical"], out["hist-nat"])); print(f"  - {src}: all forcings {out['historical']:.1f}, natural only {out['hist-nat']:.1f} warm months a year, 1991–2014")
    base_warm = sum(1 for m in range(1, 13) if clim[m] >= 19)
    hc = [round(st.mean([v for d0, v in []]),1)] if False else None
    obs_rec = {}
    t = get("https://coastwatch.pfeg.noaa.gov/erddap/griddap/erdHadISST.csv?sst%5B(1991-01-16):1:(2014-12-16)%5D%5B(-33.5)%5D%5B(151.8)%5D").decode()
    vals = [float(r[3]) for r in list(csv.reader(t.splitlines()))[2:] if r[3] not in ("NaN", "")]
    print(f"- HadISST: {base_warm} warm months in the 1950–79 average year; observed 1991–2014: {sum(v >= 19 for v in vals) / (len(vals) / 12):.1f} a year")
    if res: print(f"- model median, 1991–2014: all forcings {st.median(r[1] for r in res):.1f}, natural only {st.median(r[2] for r in res):.1f} warm months a year ({len(res)} models)")

for name, f in (("C34", c34), ("C42", c42), ("C32", c32)):
    try: f()
    except Exception as e: print(f"\n{name} failed: {type(e).__name__}: {str(e)[:300]}")
