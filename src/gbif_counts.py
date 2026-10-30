"""Count shark records by year along Australia's east coast from GBIF, for claim C2 (are bull sharks turning up further south?).
Usage: python3 gbif_counts.py <out.json>
Only yearly counts are fetched (GBIF facets), not records. Sightings and specimens only: tag detections (machine observations)
are left out so tracking studies don't swamp the count. Bands: north (28-34 S) and south of Sydney (34-38 S), east of 145 E.
Source: GBIF.org occurrence data, which brings together records from the Atlas of Living Australia, OBIS, museums and citizen science."""
import json, sys, urllib.request, urllib.parse, time
API = "https://api.gbif.org/v1/"
def get(path, **q):
    u = API + path + "?" + urllib.parse.urlencode(q, doseq=True)
    for t in range(3):
        try: return json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "19-degrees/1.0 (+https://19-degrees.org)"}), timeout=60))
        except Exception as e: err = e; time.sleep(3)
    raise err
taxa = {}
for name, rank in (("Carcharhinus leucas", "SPECIES"), ("Galeocerdo cuvier", "SPECIES"), ("Carcharodon carcharias", "SPECIES"), ("Carcharhinidae", "FAMILY")):
    m = get("species/match", name=name, rank=rank); taxa[name] = m["usageKey"]
bands = {"north 28-34S": "-34,-28", "south 34-38S": "-38,-34"}
out = {"taxa": taxa, "counts": {}}
for name, key in taxa.items():
    for band, lat in bands.items():
        r = get("occurrence/search", taxonKey=key, country="AU", decimalLatitude=lat, decimalLongitude="145,160",
                basisOfRecord=["HUMAN_OBSERVATION", "PRESERVED_SPECIMEN", "OCCURRENCE", "MATERIAL_SAMPLE"],
                facet="year", **{"year.facetLimit": 300}, limit=0)
        out["counts"][f"{name} | {band}"] = {"total": r["count"], "by_year": {f["name"]: f["count"] for f in r["facets"][0]["counts"]} if r.get("facets") else {}}
        print(name, band, r["count"])
out["fetched"] = time.strftime("%Y-%m-%d")
json.dump(out, open(sys.argv[1], "w"), indent=1)
