"""List river mouths around Australia from HydroRIVERS, for claim C6.
Usage: python3 river_mouths.py <HydroRIVERS .shp> <out.csv> [min_catchment_km2]
Keeps river segments that end at the sea (NEXT_DOWN = 0, not endorheic) and writes the downstream end point with
catchment area (km2) and average discharge (m3/s). HydroRIVERS v1.0, Lehner & Grill (2013), CC BY 4.0."""
import sys, csv, shapefile
shp, out = sys.argv[1:3]; MIN = float(sys.argv[3]) if len(sys.argv) > 3 else 20
r = shapefile.Reader(shp); f = [x[0] for x in r.fields[1:]]
w = csv.writer(open(out, "w")); w.writerow(["lon", "lat", "catchment_km2", "discharge_m3s", "hyriv_id"]); n = 0
for sr in r.iterShapeRecords():
    d = dict(zip(f, sr.record))
    if d["NEXT_DOWN"] != 0 or d["ENDORHEIC"] != 0 or d["UPLAND_SKM"] < MIN: continue
    x, y = sr.shape.points[-1]
    if not (105 < x < 160 and -45 < y < -9): continue
    w.writerow([round(x, 4), round(y, 4), round(d["UPLAND_SKM"], 1), round(d["DIS_AV_CMS"], 2), d["HYRIV_ID"]]); n += 1
print("river mouths:", n)
