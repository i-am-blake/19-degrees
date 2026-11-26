"""Look only: GBIF record counts for bull sharks in a few rivers and lakes people ask about. Changes nothing on the site."""
import json, time, urllib.parse, urllib.request
UA = {"User-Agent": "Mozilla/5.0 (compatible; 19-degrees research; +https://19-degrees.org)"}
def get(u):
    for k in range(3):
        try: return json.loads(urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=30).read())
        except Exception as e: err = repr(e)[:120]; time.sleep(5)
    return {"error": err}
def box(w, s, e, n): return f"POLYGON(({w} {s},{e} {s},{e} {n},{w} {n},{w} {s}))"
BOX = {"Great Lakes": box(-92.5, 41, -75.5, 49.5), "Mississippi above St. Louis": box(-96, 38.7, -89, 47.5),
       "Murray-Darling basin (inland NSW, Victoria, SA)": box(139.5, -37.5, 148.5, -26), "Brisbane River (city and upstream)": box(152.7, -27.65, 153.06, -27.3),
       "Lake Nicaragua": box(-86.2, 10.9, -84.6, 12.3), "Amazon at Iquitos": box(-74, -4.5, -72.5, -3)}
out = {"made": time.strftime("%Y-%m-%d")}
for sp in ("Carcharhinus leucas", "Carcharodon carcharias"):
    k = get("https://api.gbif.org/v1/species/match?name=" + urllib.parse.quote(sp)).get("usageKey"); out[sp] = {"key": k}
    out[sp]["all_with_coords"] = get(f"https://api.gbif.org/v1/occurrence/search?limit=0&hasCoordinate=true&taxonKey={k}").get("count")
    if sp == "Carcharhinus leucas":
        for name, g in BOX.items():
            j = get("https://api.gbif.org/v1/occurrence/search?" + urllib.parse.urlencode({"taxonKey": k, "hasCoordinate": "true", "geometry": g, "limit": 50}))
            out[sp][name] = {"count": j.get("count"), "records": [{f: x.get(f) for f in ("decimalLatitude", "decimalLongitude", "year", "locality", "waterBody", "basisOfRecord", "datasetName", "institutionCode")} for x in j.get("results", [])]}
            print(sp, name, j.get("count"), flush=True); time.sleep(1)
print(out["Carcharhinus leucas"]["all_with_coords"], out["Carcharodon carcharias"]["all_with_coords"])
json.dump(out, open("../counts.json", "w"))
