"""Exploration for claim C25: on the day, were tagged and recorded bull sharks outside Australia in water of 19°C or warmer?
Usage: python3 -I explore_daily.py <ocean-data folder> <out json>
The C25 card matches each record to a monthly 1° sea temperature (HadISST). This matches each one to NOAA OISST v2.1 daily
sea temperature (0.25°, September 1981 on) for its own cell on its own day.
Written down before the data was fetched:
- Unit: a shark-day, one 0.25° cell on one date with at least one bull shark record (OBIS: tags, surveys, sightings).
- Measure: the cell's OISST temperature that day (nearest ocean cell within 0.5° when the cell is land or estuary).
- Baseline: the share of mid-month days (the 15th) below 19°C in the same cells over the same years, so "sharks avoid cold water" is not
  confused with "there was no cold water".
- Supports the claim if fewer than 5% of shark-days are below 19°C where at least 10% of available days are.
  Rules it out if the share of shark-days below 19°C is no lower than the baseline.
Tiger sharks are run the same way as a comparison."""
import csv, gzip, io, json, os, sys, time, urllib.request, collections
from concurrent.futures import ThreadPoolExecutor
SRC, OUT = sys.argv[1:3]
GROUPS = {"africa": ["obis_ponta_do_ouro.csv.gz", "obis_south_africa_bull.csv.gz", "obis_mozambique_bull.csv.gz", "obis_south_africa_tiger.csv.gz", "obis_mozambique_tiger.csv.gz"],
          "us": ["obis_us_east_gulf_bull.csv.gz", "obis_us_east_gulf_tiger.csv.gz"]}
SPECIES = {"Carcharhinus leucas": "bull", "Galeocerdo cuvier": "tiger"}
E_ = "https://coastwatch.pfeg.noaa.gov/erddap/griddap/ncdcOisst21Agg_LonPM180.csv?sst"
q = lambda v: round(float(v) * 4) / 4

def grid(date, la0, la1, lo0, lo1):
    """One day's temperatures for a box: {(lat, lon): sst}. One request reads one daily file, so it is quick."""
    url = f"{E_}%5B({date}T12:00:00Z)%5D%5B(0.0)%5D%5B({la0}):1:({la1})%5D%5B({lo0}):1:({lo1})%5D"
    for a in range(4):
        try:
            t = urllib.request.urlopen(url, timeout=90).read().decode()
            return {(round(float(r[2]) * 8) / 8, round(float(r[3]) * 8) / 8): float(r[4]) for r in list(csv.reader(io.StringIO(t)))[2:] if r[4] not in ("NaN", "")}
        except Exception as e:
            if a == 3: print("fail", date, str(e)[:80], flush=True); return None
            time.sleep(6 * (a + 1))

NEAR = [(0, 0), (0, .25), (0, -.25), (.25, 0), (-.25, 0), (.25, .25), (-.25, .25), (.25, -.25), (-.25, -.25), (0, .5), (0, -.5), (.5, 0), (-.5, 0)]
def at(g, c):
    """Temperature at the cell, or the nearest ocean cell within 0.5 degrees. OISST cell centres sit on .125/.375/.625/.875."""
    for dl, dn in NEAR:
        for k in ((c[0] + dl + .125, c[1] + dn + .125), (c[0] + dl - .125, c[1] + dn - .125), (c[0] + dl + .125, c[1] + dn - .125), (c[0] + dl - .125, c[1] + dn + .125)):
            if k in g: return g[k]
    return None

res = {}
for g, fs in GROUPS.items():
    days = collections.defaultdict(set)   # species -> {(cell, date)}
    for f in fs:
        p = os.path.join(SRC, f)
        if not os.path.exists(p): continue
        for x in csv.DictReader(gzip.open(p, "rt", encoding="utf-8")):
            sp = SPECIES.get(x["scientificName"].strip()); d = (x.get("eventDate") or "")[:10]
            if not sp or len(d) != 10 or d < "1981-09-01" or not x.get("decimalLatitude") or not x.get("decimalLongitude"): continue
            try: days[sp].add(((q(x["decimalLatitude"]), q(x["decimalLongitude"])), d))
            except ValueError: pass
    bydate = collections.defaultdict(set)
    for sp in days:
        for c, d in days[sp]: bydate[d].add(c)
    allc = {c for cs in bydate.values() for c in cs}
    box = lambda cs: (min(c[0] for c in cs) - .75, max(c[0] for c in cs) + .75, min(c[1] for c in cs) - .75, max(c[1] for c in cs) + .75)
    years = sorted({int(d[:4]) for d in bydate})
    base_dates = [f"{y}-{m:02d}-15" for y in years for m in range(1, 13) if "1981-09-01" <= f"{y}-{m:02d}-15" <= "2026-09-15"]
    print(g, {sp: len(v) for sp, v in days.items()}, "dates", len(bydate), "cells", len(allc), "baseline dates", len(base_dates), flush=True)
    with ThreadPoolExecutor(6) as ex:
        got = dict(zip(bydate, ex.map(lambda d: grid(d, *box(bydate[d])), list(bydate))))
        print(g, "record days fetched", flush=True)
        base = dict(zip(base_dates, ex.map(lambda d: grid(d, *box(allc)), base_dates)))
    res[g] = {}
    for sp, sd in days.items():
        temps = []; nodata = 0; cold = []
        for c, d in sd:
            v = at(got[d], c) if got.get(d) else None
            if v is None: nodata += 1; continue
            temps.append(v)
            if v < 19: cold.append((v, d, c))
        cy = collections.defaultdict(set)
        for c, d in sd: cy[c].add(d[:4])
        avail = below = 0
        for d, gr in base.items():
            if not gr: continue
            for c, ys in cy.items():
                if d[:4] in ys:
                    v = at(gr, c)
                    if v is not None: avail += 1; below += v < 19
        temps.sort(); n = len(temps)
        res[g][sp] = dict(shark_days=n, no_temperature=nodata, below19=len(cold), below19_pct=round(100 * len(cold) / n, 2) if n else None,
                          min=temps[0] if n else None, p01=temps[int(n * .01)] if n else None, median=temps[n // 2] if n else None,
                          cells=len(cy), y0=min(d[:4] for _, d in sd), y1=max(d[:4] for _, d in sd),
                          baseline_cell_months=avail, baseline_below19_pct=round(100 * below / avail, 1) if avail else None,
                          coldest=[dict(t=v, date=d, lat=c[0], lon=c[1]) for v, d, c in sorted(cold)[:12]],
                          cold_by_month=dict(sorted(collections.Counter(d[5:7] for _, d, _ in cold).items())),
                          cold_lat=[min(c[0] for _, _, c in cold), max(c[0] for _, _, c in cold)] if cold else None)
    print("PART " + json.dumps({g: res[g]}), flush=True)
json.dump(res, open(OUT, "w"), indent=1)
print("RESULT " + json.dumps(res))
