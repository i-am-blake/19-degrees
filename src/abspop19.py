"""Claim C18, second check: are bites in southern NSW rising faster than the number of people living right on that coast?
Usage: python3 -I abspop19.py <asid.csv> <out abspop.json> [coast.geojson]
Population: the Australian Bureau of Statistics' estimated resident population by small area (SA2, 2021 boundaries),
every year 2001-2021 and 2023-2024 (2022 is the average of its neighbors), from the ABS's public map services
(CC BY 4.0). Coast: small areas whose center is within 15 km of the coastline (Natural Earth 1:10m, public domain),
in the same three southern NSW regions as the first check (Port Macquarie south). This is much finer than the first
check's 1-degree boxes, and official counts rather than a satellite estimate.
Test: bites per resident-year in 2001-2010 against the latest ten years, two-sided exact binomial, as in grades19.g_c18."""
import csv, json, math, os, sys, urllib.parse, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from regions import REGIONS
from scipy.stats import binomtest

ASID, OUT = sys.argv[1:3]
COAST = sys.argv[3] if len(sys.argv) > 3 else "coast.geojson"
UA = {"User-Agent": "19-degrees/1.0 (+https://19-degrees.org)"}
def get(u): return json.loads(urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=180).read())
SOUTH = ["Mid North Coast & Hunter", "Sydney & Central Coast", "NSW South Coast"]
nsw = sorted([(la, name) for name, _, st, la, lo in REGIONS if st == "NSW"], reverse=True)
edges = [(nsw[i][0] + nsw[i + 1][0]) / 2 for i in range(len(nsw) - 1)]
def nsw_region(lat):
    for i, e in enumerate(edges):
        if lat > e: return nsw[i][1]
    return nsw[-1][1]

if not os.path.exists(COAST):
    urllib.request.urlretrieve("https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_10m_coastline.geojson", COAST)
pts = []
for f in json.load(open(COAST))["features"]:
    g = f["geometry"]; lines = g["coordinates"] if g["type"] == "MultiLineString" else [g["coordinates"]]
    for ln in lines:
        pts += [(la, lo) for lo, la in ln if -38.5 < la < -27.5 and 148.5 < lo < 154.5]
def km_to_coast(la, lo):
    return min(math.hypot((la - a) * 111.0, (lo - b) * 111.0 * math.cos(math.radians(la))) for a, b in pts)

base = "https://geo.abs.gov.au/arcgis/rest/services/Hosted/"
years = list(range(2001, 2022))
q = {"where": "sa2_code_2021 LIKE '1%'", "outFields": "sa2_code_2021,sa2_name_2021," + ",".join(f"erp_no_{y}" for y in years),
     "returnGeometry": "false", "returnCentroid": "true", "outSR": "4326", "f": "json", "resultRecordCount": 2000}
A = get(base + "ABS_ERP_2001_2021_SA2/FeatureServer/0/query?" + urllib.parse.urlencode(q))["features"]
late, off = {}, 0
while True:  # this layer pages at 2000 rows and stores the code as text or number, so page through all of it
    B = get(base + "SA2_RP_2024/FeatureServer/0/query?" + urllib.parse.urlencode({"where": "1=1", "outFields": "sa2_code_2021,pop_yr1,pop_yr2", "returnGeometry": "false",
              "f": "json", "resultOffset": off, "resultRecordCount": 2000, "orderByFields": "objectid"}))["features"]
    for x in B: late[str(x["attributes"]["sa2_code_2021"]).strip()] = x["attributes"]
    if len(B) < 2000: break
    off += 2000
if len(A) < 500 or len(late) < 2000: sys.exit(f"ABS service returned too few areas ({len(A)}, {len(late)})")
areas = []
for x in A:
    c = x.get("centroid"); a = x["attributes"]
    if not c or nsw_region(c["y"]) not in SOUTH or km_to_coast(c["y"], c["x"]) > 15: continue
    p = {y: a.get(f"erp_no_{y}") or 0 for y in years}
    l = late.get(str(a["sa2_code_2021"]).strip(), {}); p[2023] = l.get("pop_yr1") or 0; p[2024] = l.get("pop_yr2") or 0
    p[2022] = round((p[2021] + p[2023]) / 2)
    areas.append((a["sa2_name_2021"], p))
pop = {y: sum(p[y] for _, p in areas) for y in range(2001, 2025)}
if not pop[2024] or not pop[2023] or pop[2024] < 0.9 * pop[2021]: sys.exit(f"2023-24 population didn't join: {pop[2021]}, {pop[2023]}, {pop[2024]}")

rows = [x for x in csv.DictReader(open(ASID, encoding="utf-8")) if x["State"].strip() == "NSW" and x["Provoked/unprovoked"].strip() == "unprovoked"
        and x["Incident.year"].isdigit() and x["Latitude"].strip() not in ("", "NA") and nsw_region(float(x["Latitude"])) in SOUTH]
last = max(int(x["Incident.year"]) for x in rows)
last_month = max(int(x["Incident.month"]) for x in rows if int(x["Incident.year"]) == last and x["Incident.month"].strip().isdigit())  # the database runs to here: count only that part of the year
def window(y0, y1):
    sel = [x for x in rows if y0 <= int(x["Incident.year"]) <= y1]
    py = sum(pop[min(max(y, 2001), 2024)] * (last_month / 12 if y == last else 1) for y in range(y0, y1 + 1))  # resident-years; years after 2024 use 2024
    return dict(years=f"{y0}-{y1}", bites=len(sel), bull=sum("bull" in x["Shark.common.name"].lower() for x in sel),
                resident_years=round(py), rate=round(len(sel) / py * 1e6, 2))
a, z = window(2001, 2010), window(last - 9, last)
p = float(binomtest(z["bites"], a["bites"] + z["bites"], z["resident_years"] / (a["resident_years"] + z["resident_years"])).pvalue)
out = dict(areas=len(areas), pop_2001=pop[2001], pop_2024=pop[2024], pop_growth=round(pop[2024] / pop[2001], 2),
           early=a, late=z, rate_growth=round(z["rate"] / a["rate"], 1) if a["rate"] else None, p=round(p, 4), last_year=last, last_month=last_month)
json.dump(out, open(OUT, "w"), indent=1)
print("abspop", json.dumps(out))
