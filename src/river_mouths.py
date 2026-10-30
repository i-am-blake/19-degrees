"""List river mouths on Australia's east coast from OpenStreetMap, for claim C6.
Usage: python3 river_mouths.py <overpass.json> <ne_10m_coastline.geojson> <out.csv>
A river mouth is the end of an OpenStreetMap river (waterway=river) lying within 3 km of the Natural Earth coastline.
Data: OpenStreetMap contributors, ODbL 1.0 (https://www.openstreetmap.org/copyright); Natural Earth, public domain."""
import sys, json, csv, math, bisect
osm, ne, out = sys.argv[1:4]
coast = []
for f in json.load(open(ne))["features"]:
    g = f["geometry"]; cs = g["coordinates"] if g["type"] == "MultiLineString" else [g["coordinates"]]
    for c in cs: coast += [p for p in c if 145 < p[0] < 156 and -40 < p[1] < -20]
coast.sort(key=lambda p: p[1]); cy = [p[1] for p in coast]
def km(a, b): return math.hypot((a[0] - b[0]) * 111.32 * math.cos(math.radians((a[1] + b[1]) / 2)), (a[1] - b[1]) * 110.57)
def dc(p):
    i = bisect.bisect_left(cy, p[1] - 0.1); j = bisect.bisect_right(cy, p[1] + 0.1)
    return min((km(p, q) for q in coast[i:j]), default=999)
mouths = {}
for e in json.load(open(osm))["elements"]:
    g = e.get("geometry") or []
    if len(g) < 2: continue
    for p in ((g[0]["lon"], g[0]["lat"]), (g[-1]["lon"], g[-1]["lat"])):
        d = dc(p)
        if d <= 3:
            name = e.get("tags", {}).get("name", "")
            key = (round(p[0], 3), round(p[1], 3))
            if key not in mouths: mouths[key] = (name, round(d, 2), e["id"])
w = csv.writer(open(out, "w")); w.writerow(["lon", "lat", "name", "km_to_coastline", "osm_way"])
for (x, y), (n, d, i) in sorted(mouths.items(), key=lambda k: k[0][1]): w.writerow([x, y, n, d, i])
print("river ends near the coast:", len(mouths))
