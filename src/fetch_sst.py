"""Fetch HadISST monthly SST (1°, 1900–present) for each region's offshore point via NOAA ERDDAP.
Output one CSV per region: date,sst. If the grid cell is land/ice (NaN), step further offshore."""
import sys, os, urllib.request, csv, io, concurrent.futures as cf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from regions import REGIONS
OUT = sys.argv[1]
BASE = "https://coastwatch.pfeg.noaa.gov/erddap/griddap/erdHadISST.csv?sst"
OFFS = [(0, 0), (0, 1), (0, -1), (-1, 0), (1, 0), (-1, 1), (-1, -1), (1, 1), (1, -1)]

def get(lat, lon):
    url = f"{BASE}%5B(1900-01-16):1:(last)%5D%5B({lat})%5D%5B({lon})%5D"
    txt = urllib.request.urlopen(url, timeout=120).read().decode()
    return [(r[0][:7], r[3]) for r in list(csv.reader(io.StringIO(txt)))[2:]]

def fetch(region):
    name, _, _, lat, lon = region
    for dl, dn in OFFS:
        rows = get(lat + dl, lon + dn)
        good = [(d, v) for d, v in rows if v not in ("NaN", "")]
        if len(good) > 0.95 * len(rows):
            fn = os.path.join(OUT, name.replace(" ", "_").replace("&", "and") + ".csv")
            with open(fn, "w", newline="") as f:
                w = csv.writer(f); w.writerow(["date", "sst"]); w.writerows(good)
            return f"{name}: cell {lat+dl},{lon+dn}, {len(good)} months, last {good[-1][0]}"
    return f"NO OCEAN CELL {name}"

with cf.ThreadPoolExecutor(6) as ex:
    for msg in ex.map(fetch, REGIONS): print(msg, flush=True)
