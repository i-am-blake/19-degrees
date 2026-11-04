"""Claim C25: outside Australia, are tagged and recorded bull sharks also found only in water of 19°C or warmer?
Usage: python3 -I obis19.py <ocean-data folder> <out obis.json>
Reads the OBIS shark records the monthly fetch saves to the ocean-data branch (fetch-obis.yml):
- Africa: the Ocean Tracking Network's Ponta do Ouro tracking dataset (bull and tiger sharks, Mozambique to the
  Western Cape, CC BY 4.0).
- US Gulf and Atlantic: every OBIS bull and tiger shark record with a date (tags, surveys, sightings; each dataset
  keeps its own licence).
Each record is placed in its 1° sea cell and month, and matched to that month's HadISST sea temperature (NOAA ERDDAP).
A "record-day" is one species seen in one cell on one day, so a single receiver logging a shark all day counts once.
The result: how many record-days fell in months below 19°C, against how many months in the same cells were below 19°C.
If the input files haven't changed since the last run (same fingerprint in the old obis.json), it keeps the last result
and skips the sea-temperature downloads."""
import csv, gzip, hashlib, io, json, math, os, sys, time, urllib.request

SRC, OUT = sys.argv[1:3]
GROUPS = {"africa": ["obis_ponta_do_ouro.csv.gz"], "us": ["obis_us_east_gulf_bull.csv.gz", "obis_us_east_gulf_tiger.csv.gz"]}
SPECIES = {"Carcharhinus leucas": "bull", "Galeocerdo cuvier": "tiger"}
OFFS = [(0, 0), (0, 1), (0, -1), (-1, 0), (1, 0), (-1, 1), (1, 1), (-1, -1), (1, -1)]

files = sorted({f for fs in GROUPS.values() for f in fs})
h = hashlib.sha256()
for f in files:
    p = os.path.join(SRC, f)
    if os.path.exists(p): h.update(open(p, "rb").read())
FP = h.hexdigest()[:16]
if os.path.exists(OUT):
    try:
        old = json.load(open(OUT))
        if old.get("fingerprint") == FP:
            print("obis: inputs unchanged, keeping", OUT); sys.exit(0)
    except Exception:
        pass

def sst(la, lo):
    url = f"https://coastwatch.pfeg.noaa.gov/erddap/griddap/erdHadISST.csv?sst%5B(1950-01-16):1:(last)%5D%5B({la})%5D%5B({lo})%5D"
    for a in range(6):
        try:
            t = urllib.request.urlopen(url, timeout=120).read().decode(); break
        except Exception:
            if a == 5: return {}
            time.sleep(10 * (a + 1))
    return {r[0][:7]: float(r[3]) for r in list(csv.reader(io.StringIO(t)))[2:] if r[3] not in ("NaN", "")}

cache = {}
def cell_sst(c):
    if c not in cache:
        cache[c] = {}
        for dl, dn in OFFS:
            s = sst(c[0] + dl, c[1] + dn)
            if len(s) > 100: cache[c] = s; break
    return cache[c]

out = {"fingerprint": FP, "groups": {}}
for g, fs in GROUPS.items():
    days = {}
    for f in fs:
        p = os.path.join(SRC, f)
        if not os.path.exists(p): continue
        for x in csv.DictReader(gzip.open(p, "rt", encoding="utf-8")):
            sp = SPECIES.get(x["scientificName"].strip())
            d = x["eventDate"][:10]
            if not sp or len(d) < 7 or not d[:4].isdigit() or not x["decimalLatitude"]: continue
            c = (math.floor(float(x["decimalLatitude"])) + 0.5, math.floor(float(x["decimalLongitude"])) + 0.5)
            days[(sp, d, c)] = None
    res = {}
    for sp in ("bull", "tiger"):
        keys = [k for k in days if k[0] == sp]
        vals = [t for t in (cell_sst(c).get(d[:7]) for _, d, c in keys) if t is not None]
        cells = {c for _, _, c in keys}
        months = [t for c in cells for t in cell_sst(c).values()]
        if not vals: continue
        res[sp] = dict(days=len(vals), below=sum(t < 19 for t in vals), pct_warm=round(100 * sum(t >= 19 for t in vals) / len(vals), 1),
                       min=round(min(vals), 1), cells=len(cells), y0=min(int(d[:4]) for _, d, _ in keys), y1=max(int(d[:4]) for _, d, _ in keys),
                       cell_months=len(months), cell_months_below=sum(t < 19 for t in months),
                       cell_months_below_pct=round(100 * sum(t < 19 for t in months) / len(months)) if months else None)
    out["groups"][g] = res
json.dump(out, open(OUT, "w"), indent=1)
print("obis", json.dumps(out))
