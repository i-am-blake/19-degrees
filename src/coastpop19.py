"""Claim C18 (first look): are bites in southern NSW rising faster than the number of people living on that coast?
Usage: python3 -I coastpop19.py <asid.csv> <population_coastal_ghsl.csv> <out coastpop.json>
Population: people within a 1° box around each region's sea point, from the EU's Global Human Settlement Layer
(GHS-POP R2023A, CC BY 4.0), every five years from 1975. Southern NSW = the page's Mid North Coast & Hunter, Sydney &
Central Coast and NSW South Coast regions. Bites: unprovoked bites there by decade (all sharks, and bull sharks), per
million coastal residents per year. Living on the coast is not the same as being in the water, so this stays a first look
until beach attendance is available."""
import csv, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from regions import REGIONS

ASID, POP, OUT = sys.argv[1:4]
SOUTH = ["Mid North Coast & Hunter", "Sydney & Central Coast", "NSW South Coast"]
pop = {}
for r in csv.DictReader(open(POP)):
    if r["region"] in SOUTH: pop[int(r["year"])] = pop.get(int(r["year"]), 0) + int(r["people_within_1deg_box"])

# NSW regions by latitude, from regions.py sea points (midpoints between neighbors)
nsw = sorted([(la, name) for name, _, st, la, lo in REGIONS if st == "NSW"], reverse=True)
edges = [(nsw[i][0] + nsw[i + 1][0]) / 2 for i in range(len(nsw) - 1)]
def nsw_region(lat):
    for i, e in enumerate(edges):
        if lat > e: return nsw[i][1]
    return nsw[-1][1]

rows = [x for x in csv.DictReader(open(ASID, encoding="utf-8")) if x["State"].strip() == "NSW" and x["Provoked/unprovoked"].strip() == "unprovoked"
        and x["Incident.year"].isdigit() and x["Latitude"].strip() not in ("", "NA")]
last_year = max(int(x["Incident.year"]) for x in rows)
out = {"decades": []}
for d in range(1980, last_year // 10 * 10 + 1, 10):
    yrs = min(10, last_year - d + 1)
    sel = [x for x in rows if d <= int(x["Incident.year"]) < d + 10 and nsw_region(float(x["Latitude"])) in SOUTH]
    p = sum(pop.get(y, 0) for y in (d, d + 5) if y in pop) / max(1, sum(1 for y in (d, d + 5) if y in pop))
    allb = len(sel); bull = sum("bull" in x["Shark.common.name"].lower() for x in sel)
    out["decades"].append(dict(decade=d, years=yrs, people=round(p), bites=allb, bull=bull,
                               rate=round(allb / (p / 1e6) / yrs, 2), bull_rate=round(bull / (p / 1e6) / yrs, 3)))
D = out["decades"]; a, b = next(x for x in D if x["decade"] == 1990), D[-1]  # 1990 on: the 1980s record is thin
out["base"] = a["decade"]
out["pop_growth"] = round(b["people"] / a["people"], 2)
out["rate_growth"] = round(b["rate"] / a["rate"], 1) if a["rate"] else None
out["bull_growth"] = round(b["bull_rate"] / a["bull_rate"], 1) if a["bull_rate"] else None
json.dump(out, open(OUT, "w"), indent=1)
print("coastpop", json.dumps(out))
