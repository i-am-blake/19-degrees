"""Claim C23: have California's white shark incidents moved north as the coast warmed?
Usage: python3 -I california19.py <CDFW SharkIncidents xlsx> <out california.json>
Data: California Department of Fish and Wildlife shark incident database (sheet "Attacks_1950_2021"), CC BY,
https://lab.data.ca.gov/dataset/shark-incident-database-california (fetched monthly to the ocean-data branch).
Counts white shark incidents with a recorded place by era, the median latitude of each era, and how many were south of
Point Conception (34.45°N), where the coast turns east and the water is warmer. Compares 2014 on (the 2014-16 marine
heatwave and after) with 1990-2013 by a permutation test on the median latitude."""
import json, random, statistics, sys
import openpyxl

SRC, OUT = sys.argv[1:3]
CONCEPTION = 34.45
ws = openpyxl.load_workbook(SRC, read_only=True, data_only=True)["Attacks_1950_2021"]
rows = list(ws.iter_rows(values_only=True)); ix = {k: i for i, k in enumerate(rows[0])}
w = [(r[ix["Date"]].year, float(r[ix["Latitude"]])) for r in rows[1:]
     if r[ix["Species"]] and str(r[ix["Species"]]).strip().lower() == "white" and r[ix["Latitude"]] and hasattr(r[ix["Date"]], "year")]
y1 = max(y for y, _ in w)
eras = [(1950, 1979), (1980, 1999), (2000, 2013), (2014, y1)]
out = dict(y0=min(y for y, _ in w), y1=y1, n=len(w), eras=[])
for a, b in eras:
    l = [la for y, la in w if a <= y <= b]
    out["eras"].append(dict(era=[a, b], n=len(l), median_lat=round(statistics.median(l), 1), south=sum(x < CONCEPTION for x in l)))
pre = [la for y, la in w if 1990 <= y <= 2013]; post = [la for y, la in w if y >= 2014]
d = statistics.median(post) - statistics.median(pre); pool = pre + post; random.seed(19); hits, N = 0, 20000
for _ in range(N):
    random.shuffle(pool)
    hits += abs(statistics.median(pool[len(pre):]) - statistics.median(pool[:len(pre)])) >= abs(d)
out["test"] = dict(pre=[1990, 2013], pre_n=len(pre), pre_lat=round(statistics.median(pre), 1), post_n=len(post),
                   post_lat=round(statistics.median(post), 1), shift_km=round(d * 111), p=round((hits + 1) / (N + 1), 3))
json.dump(out, open(OUT, "w"), indent=1)
print("california", json.dumps(out))
