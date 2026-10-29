"""Fetch HadISST monthly sea temperature (1900–present) for each beach's offshore 1° patch,
and today's sea temperature at the beach from Open-Meteo marine.
Usage: python3 -I fetch_beaches.py <out_dir>
Writes <out_dir>/<key>.csv (date,sst) and <out_dir>/beaches.json (patch centre used, today's reading)."""
import sys, os, csv, io, json, time, urllib.request
def fetch(url, tries=5):
    for i in range(tries):
        try:
            return urllib.request.urlopen(url, timeout=120).read().decode()
        except Exception as e:
            if i == tries - 1: raise
            time.sleep(10 * (i + 1))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from beaches import BEACHES
OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
BASE = "https://coastwatch.pfeg.noaa.gov/erddap/griddap/erdHadISST.csv?sst"
OFFS = [(0, 0), (0, 1), (-1, 1), (1, 1), (0, 2)]
meta = {}
for key, name, blat, blon, lat, lon, coast in BEACHES:
    for dl, dn in OFFS:
        url = f"{BASE}%5B(1900-01-16):1:(last)%5D%5B({lat+dl})%5D%5B({lon+dn})%5D"
        rows = list(csv.reader(io.StringIO(fetch(url))))[2:]
        good = [(r[0][:7], r[3]) for r in rows if r[3] not in ("NaN", "")]
        if len(good) > 0.95 * len(rows):
            with open(os.path.join(OUT, key + ".csv"), "w", newline="") as f:
                w = csv.writer(f); w.writerow(["date", "sst"]); w.writerows(good)
            meta[key] = dict(name=name, coast=coast, beach=[blat, blon], patch=[float(rows[0][1]), float(rows[0][2])], last=good[-1][0])
            break
    else:
        raise SystemExit(f"no ocean cell for {name}")
    m = meta[key]
    try:
        u = (f"https://marine-api.open-meteo.com/v1/marine?latitude={blat}&longitude={blon}"
             "&current=sea_surface_temperature&daily=sea_surface_temperature_max&past_days=6&forecast_days=1&timezone=Australia%2FSydney")
        j = json.loads(fetch(u))
        m["today"] = dict(time=j["current"]["time"], sst=j["current"]["sea_surface_temperature"],
                          week=list(zip(j["daily"]["time"], j["daily"]["sea_surface_temperature_max"])))
    except Exception as e:
        m["today"] = None; print("open-meteo failed for", name, e)
    print(key, "patch", m["patch"], "last", m["last"], "today", m["today"] and m["today"]["sst"], flush=True)
json.dump(meta, open(os.path.join(OUT, "beaches.json"), "w"), indent=1)
