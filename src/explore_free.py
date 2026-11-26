"""Look only: free data to answer more of the questions people search. ISAF yearly summary (text), Hawaii DLNR incident list,
KwaZulu-Natal Sharks Board annual report (text), GBIF bull shark records far from the sea, OBIS/GBIF white shark records in the
Mediterranean. Changes nothing on the site."""
import io, json, math, re, time, urllib.parse, urllib.request, zipfile
UA = {"User-Agent": "Mozilla/5.0 (compatible; 19-degrees research; +https://19-degrees.org)"}
def get(u, t=90, binary=False):
    for k in range(3):
        try:
            b = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=t).read()
            return b if binary else b.decode("utf-8", "replace")
        except Exception as e: err = "ERR " + repr(e)[:150]; time.sleep(5 * (k + 1))
    return err
def text(h): return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", h, flags=re.S | re.I))).strip()
out = {"made": time.strftime("%Y-%m-%d"), "errors": {}}
# 1) ISAF yearly worldwide summary
h = get("https://www.floridamuseum.ufl.edu/shark-attacks/yearly-worldwide-summary/")
out["isaf"] = text(h)[:30000] if not h.startswith("ERR") else h; print("isaf", len(out["isaf"]), flush=True)
# 2) Hawaii DLNR incident list (HTML table)
h = get("https://dlnr.hawaii.gov/sharks/shark-incidents/incidents-list/")
rows = []
if not h.startswith("ERR"):
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", h, re.S | re.I):
        cells = [text(c) for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, re.S | re.I)]
        if cells: rows.append(cells)
out["hawaii"] = rows; print("hawaii rows", len(rows), rows[:3], flush=True)
# 3) KwaZulu-Natal Sharks Board annual report 2025 (lines about bites)
try:
    from pypdf import PdfReader
    b = get("https://shark.co.za/wp-content/uploads/simple-file-list/KZNSB-AR2025-web4.pdf", 180, True)
    r = PdfReader(io.BytesIO(b)); lines = []
    for p in r.pages:
        for ln in (p.extract_text() or "").splitlines():
            if re.search(r"bite|incident|attack|unprovoked", ln, re.I): lines.append(ln.strip())
    out["kzn"] = lines[:300]; print("kzn lines", len(lines), flush=True)
except Exception as e: out["errors"]["kzn"] = repr(e)[:150]
# land polygons for "how far from the sea"
import geopandas as gpd
from shapely.geometry import Point
land = None
try:
    z = zipfile.ZipFile(io.BytesIO(get("https://naciscdn.org/naturalearth/10m/physical/ne_10m_land.zip", 180, True))); z.extractall("ne")
    land = gpd.read_file("ne/ne_10m_land.shp").to_crs(3857); coast = land.boundary.union_all() if hasattr(land.boundary, "union_all") else land.boundary.unary_union
    landu = land.union_all() if hasattr(land, "union_all") else land.unary_union
except Exception as e: out["errors"]["land"] = repr(e)[:150]
def km_inland(lat, lon):
    p = gpd.GeoSeries([Point(lon, lat)], crs=4326).to_crs(3857).iloc[0]
    if not landu.contains(p): return 0.0
    return round(p.distance(coast) / 1000 * math.cos(math.radians(lat)), 1)  # web mercator scale correction
# 4) GBIF: bull shark records with coordinates, keep those well inland
def gbif(params, cap):
    recs, off = [], 0
    while off < cap:
        j = get("https://api.gbif.org/v1/occurrence/search?" + urllib.parse.urlencode({**params, "limit": 300, "offset": off}))
        if j.startswith("ERR"): out["errors"]["gbif_" + params.get("taxonKey", "")] = j; break
        d = json.loads(j); res = d.get("results", [])
        for x in res:
            if x.get("decimalLatitude") is None: continue
            recs.append({k: x.get(k) for k in ("decimalLatitude", "decimalLongitude", "year", "country", "stateProvince", "locality", "waterBody", "basisOfRecord", "datasetName", "institutionCode", "occurrenceStatus")})
        off += 300
        if d.get("endOfRecords"): break
        time.sleep(0.3)
    return recs
k = json.loads(get("https://api.gbif.org/v1/species/match?name=Carcharhinus%20leucas")).get("usageKey")
bull = gbif({"taxonKey": k, "hasCoordinate": "true", "hasGeospatialIssue": "false", "occurrenceStatus": "PRESENT"}, 30000)
print("gbif bull records", len(bull), flush=True)
inland = []
if land is not None:
    for r_ in bull:
        try: d_ = km_inland(r_["decimalLatitude"], r_["decimalLongitude"])
        except Exception: continue
        if d_ >= 20: inland.append({**r_, "km_inland": d_})
out["bull_total"] = len(bull); out["bull_inland"] = sorted(inland, key=lambda x: -x["km_inland"])[:400]
print("bull inland >=20 km", len(inland), flush=True)
# 5) White sharks in the Mediterranean: OBIS and GBIF
MED = "POLYGON((-5.6 30,36.5 30,36.5 46,-5.6 46,-5.6 30))"
o = get("https://api.obis.org/v3/occurrence?" + urllib.parse.urlencode({"scientificname": "Carcharodon carcharias", "geometry": MED, "size": 10000}), 180)
try:
    res = json.loads(o).get("results", [])
    out["med_obis"] = [{"lat": x.get("decimalLatitude"), "lon": x.get("decimalLongitude"), "year": x.get("date_year") or x.get("year"), "locality": x.get("locality"), "dataset": x.get("dataset_id")} for x in res]
    print("obis med white", len(res), flush=True)
except Exception as e: out["errors"]["obis"] = (o if isinstance(o, str) else "")[:150]
kw = json.loads(get("https://api.gbif.org/v1/species/match?name=Carcharodon%20carcharias")).get("usageKey")
out["med_gbif"] = gbif({"taxonKey": kw, "hasCoordinate": "true", "geometry": MED, "occurrenceStatus": "PRESENT"}, 6000); print("gbif med white", len(out["med_gbif"]), flush=True)
json.dump(out, open("../free.json", "w"))
