"""Exploration for claim C25: on the day, were tagged and recorded bull sharks outside Australia in water of 19°C or warmer?
Usage: python3 -I explore_daily.py <ocean-data folder> <out json>
The C25 card matches each record to a monthly 1° sea temperature (HadISST). This matches each one to NOAA OISST v2.1 daily
sea temperature (0.25°, September 1981 on) for its own cell on its own day.
Written down before the data was fetched:
- Unit: a shark-day, one 0.25° cell on one date with at least one bull shark record (OBIS: tags, surveys, sightings).
- Measure: the cell's OISST temperature that day (nearest ocean cell within 0.5° when the cell is land or estuary).
- Baseline: the share of all days below 19°C in the same cells over the same years, so "sharks avoid cold water" is not
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

def fetch(la, lo, y0, y1):
    t0 = f"{y0}-01-01" if y0 > 1981 else "1981-09-01"
    url = f"{E_}%5B({t0}T12:00:00Z):1:({y1}-12-31T12:00:00Z)%5D%5B(0.0)%5D%5B({la})%5D%5B({lo})%5D"
    for a in range(5):
        try:
            t = urllib.request.urlopen(url, timeout=180).read().decode()
            return {r[0][:10]: float(r[4]) for r in list(csv.reader(io.StringIO(t)))[2:] if r[4] not in ("NaN", "")}
        except Exception as e:
            if "400" in str(e) and y1 >= 2026: y1 -= 0  # the newest year may be short; ERDDAP clips "(last)" itself below
            if a == 4: print("fail", la, lo, y0, y1, str(e)[:80]); return None
            time.sleep(8 * (a + 1))

LAST = None
def series(cell, years):
    """Daily series for the cell (or nearest ocean cell), in 6-year requests covering the years needed."""
    ys = sorted(years); spans = []
    for y in ys:
        if spans and y <= spans[-1][1]: continue
        spans.append((y, min(y + 5, 2026)))
    for dl, dn in [(0, 0), (0, .25), (0, -.25), (.25, 0), (-.25, 0), (.25, .25), (-.25, .25), (.25, -.25), (-.25, -.25), (0, .5), (0, -.5), (.5, 0), (-.5, 0)]:
        out = {}; bad = False
        for y0, y1 in spans:
            url_y1 = y1
            s = fetch(cell[0] + dl, cell[1] + dn, y0, url_y1)
            if s is None and y1 >= 2026:   # ask up to the last day on the server instead
                s = fetch_last(cell[0] + dl, cell[1] + dn, y0)
            if s is None: bad = True; break
            out.update(s)
        if not bad and len(out) > 200: return out, (dl, dn)
    return {}, None

def fetch_last(la, lo, y0):
    url = f"{E_}%5B({y0}-01-01T12:00:00Z):1:(last)%5D%5B(0.0)%5D%5B({la})%5D%5B({lo})%5D"
    for a in range(4):
        try:
            t = urllib.request.urlopen(url, timeout=180).read().decode()
            return {r[0][:10]: float(r[4]) for r in list(csv.reader(io.StringIO(t)))[2:] if r[4] not in ("NaN", "")}
        except Exception as e:
            if a == 3: print("fail last", la, lo, y0, str(e)[:80]); return None
            time.sleep(8 * (a + 1))

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
    need = collections.defaultdict(set)
    for sp in days:
        for c, d in days[sp]: need[c].add(int(d[:4]))
    print(g, {sp: len(v) for sp, v in days.items()}, "cells", len(need), flush=True)
    with ThreadPoolExecutor(4) as ex:
        got = dict(zip(need, ex.map(lambda c: series(c, need[c]), need)))
    res[g] = {}
    for sp, sd in days.items():
        temps = []; nodata = 0; cold = []
        for c, d in sd:
            v = got[c][0].get(d)
            if v is None: nodata += 1; continue
            temps.append(v)
            if v < 19: cold.append((v, d, c))
        cells = {c for c, _ in sd}; avail = below = 0
        for c in cells:
            yrs = {int(d[:4]) for cc, d in sd if cc == c}
            for d, v in got[c][0].items():
                if int(d[:4]) in yrs: avail += 1; below += v < 19
        temps.sort(); n = len(temps)
        res[g][sp] = dict(shark_days=n, no_temperature=nodata, below19=len(cold), below19_pct=round(100 * len(cold) / n, 2) if n else None,
                          min=temps[0] if n else None, p01=temps[int(n * .01)] if n else None, median=temps[n // 2] if n else None,
                          cells=len(cells), moved_cells=sum(1 for c in cells if got[c][1] not in (None, (0, 0))), y0=min(d[:4] for _, d in sd), y1=max(d[:4] for _, d in sd),
                          available_days=avail, available_below19_pct=round(100 * below / avail, 1) if avail else None,
                          coldest=[dict(t=v, date=d, lat=c[0], lon=c[1]) for v, d, c in sorted(cold)[:12]],
                          cold_by_month=dict(sorted(collections.Counter(d[5:7] for _, d, _ in cold).items())),
                          cold_lat=[min(c[0] for _, _, c in cold), max(c[0] for _, _, c in cold)] if cold else None)
json.dump(res, open(OUT, "w"), indent=1)
print("RESULT " + json.dumps(res))
