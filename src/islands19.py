"""Réunion and New Caledonia (claims C6 and C22): day-dated shark bites from the University of Reunion Island.
Usage: python3 -I islands19.py <Shark_Attacks_NC_RUN.csv> <out islands.json>
Data: Taglioni, Guiltat and Delsaut, "Datasets of Human-shark interactions in New Caledonia and Reunion Island
(1980-2022)", Zenodo, doi:10.5281/zenodo.12549370, CC BY 4.0. Each bite has its date, the 3-day rainfall and the water's
turbidity as recorded in the dataset, and the shark type when identified.
- C6 (rain): bull shark bites are compared with bites by other identified sharks at the same islands. Without rain on
  days with no bite this is a comparison between species, not against chance.
- C22 (19°C): each bite month's HadISST sea temperature (NOAA ERDDAP) for the open sea off each island, and the
  coldest month there since 1980. If the sea never falls to 19°C the line can't be tested there."""
import csv, io, json, math, statistics, sys, time, urllib.request

SRC, OUT = sys.argv[1:3]
CELLS = {"Reunion": (-21.5, 55.5), "New Caledonia": (-22.5, 166.5)}  # 1° open-sea cells off the bite coasts
OFFS = [(0, 0), (0, -1), (0, 1), (-1, 0), (1, 0)]
MON = {m: i + 1 for i, m in enumerate("Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split())}
TURBID = ("Turbid", "Highly turbid")

raw = open(SRC, "rb").read().decode("utf-8", "replace").splitlines()
rows = list(csv.DictReader(raw, delimiter=";" if raw[0].count(";") > raw[0].count(",") else ","))

def sst(lat, lon):
    url = (f"https://coastwatch.pfeg.noaa.gov/erddap/griddap/erdHadISST.csv?sst%5B(1980-01-16):1:(2022-12-16)%5D"
           f"%5B({lat})%5D%5B({lon})%5D")
    for a in range(6):
        try: txt = urllib.request.urlopen(url, timeout=120).read().decode(); break
        except Exception:
            if a == 5: raise
            time.sleep(15 * (a + 1))
    out = {}
    for r in list(csv.reader(io.StringIO(txt)))[2:]:
        if r[3] not in ("NaN", ""): out[(int(r[0][:4]), int(r[0][5:7]))] = float(r[3])
    return out

def fisher(a, b, c, d):
    """Two-sided Fisher exact test for [[a, b], [c, d]]."""
    n, r1, c1 = a + b + c + d, a + b, a + c
    p = lambda x: math.comb(r1, x) * math.comb(n - r1, c1 - x) / math.comb(n, c1)
    obs = p(a); lo, hi = max(0, c1 - (n - r1)), min(r1, c1)
    return round(min(1.0, sum(p(x) for x in range(lo, hi + 1) if p(x) <= obs * (1 + 1e-9))), 3)

def num(x):
    try: return float(x)
    except ValueError: return None

res = {"source": "doi:10.5281/zenodo.12549370", "y0": min(int(r["YEAR"]) for r in rows), "y1": max(int(r["YEAR"]) for r in rows),
       "n": len(rows), "islands": {}}
for isl, (lat, lon) in CELLS.items():
    for dl, dn in OFFS:
        s = sst(lat + dl, lon + dn)
        if len(s) > 400: break
    bites = [r for r in rows if r["SITE"] == isl]
    sp = {}
    for k in ("Bull", "Tiger"):
        t = [s[(int(r["YEAR"]), MON[r["MONTH"]])] for r in bites if r["SHARKTYPE"] == k and (int(r["YEAR"]), MON.get(r["MONTH"])) in s]
        if t: sp[k.lower()] = dict(n=len(t), min=round(min(t), 1), median=round(statistics.median(t), 1), below19=sum(x < 19 for x in t))
    res["islands"][isl] = dict(n=len(bites), cell=[lat + dl, lon + dn], sea_min=round(min(s.values()), 1),
                               sea_max=round(max(s.values()), 1), months_below19=sum(v < 19 for v in s.values()), months=len(s), species=sp)

ident = [r for r in rows if r["SHARKTYPE"] not in ("NA", "")]
def group(sel):
    rain = [num(r["RAINJ3"]) for r in sel]; rain = [x for x in rain if x is not None]
    tb = [r for r in sel if r["TURB"] not in ("NA", "")]
    return dict(n=len(sel), rain_n=len(rain), wet=sum(x >= 50 for x in rain), median_rain=statistics.median(rain) if rain else None,
                turb_n=len(tb), turbid=sum(r["TURB"] in TURBID for r in tb))
bull, other = group([r for r in ident if r["SHARKTYPE"] == "Bull"]), group([r for r in ident if r["SHARKTYPE"] != "Bull"])
for g in (bull, other):
    g["wet_pct"] = round(100 * g["wet"] / g["rain_n"]) if g["rain_n"] else None
    g["turbid_pct"] = round(100 * g["turbid"] / g["turb_n"]) if g["turb_n"] else None
res["c6"] = dict(bull=bull, other=other,
                 p_wet=fisher(bull["wet"], bull["rain_n"] - bull["wet"], other["wet"], other["rain_n"] - other["wet"]),
                 p_turbid=fisher(bull["turbid"], bull["turb_n"] - bull["turbid"], other["turbid"], other["turb_n"] - other["turbid"]))
json.dump(res, open(OUT, "w"), indent=1)
print("islands", json.dumps(res))
