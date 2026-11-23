"""Look only: can the runner reach four new open sources, and what do they hold? Prints a report; changes nothing.
1. IMOS satellite sea temperature, monthly, about 2 km (L3S-1m), at each Australian bull and tiger shark bite
2. ABS estimated resident population by small area (SA2), 2001-2024
3. River flow: WaterNSW and Queensland water monitoring (Kisters web service)
Usage: python3 -I explore_newdata.py asid.csv"""
import csv, json, re, sys, time, urllib.parse, urllib.request, statistics as st
UA = {"User-Agent": "19-degrees-explore/1.0 (+https://19-degrees.org)"}
def get(u, t=120):
    return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=t).read()
def safe(name, f):
    print(f"\n## {name}\n")
    try: f()
    except Exception as e: print(f"**Failed:** {type(e).__name__}: {str(e)[:400]}")
rows = [r for r in csv.DictReader(open(sys.argv[1], encoding="utf-8")) if r.get("Provoked/unprovoked", "").strip() == "unprovoked"]
def num(x):
    try: return float(x)
    except (TypeError, ValueError): return None

# ---------- 1. IMOS L3S-1m ----------
TH = "https://thredds.aodn.org.au/thredds"
def imos():
    base = "IMOS/SRS/SST/ghrsst/L3S-1m/dn"
    cat = get(f"{TH}/catalog/{base}/catalog.xml").decode()
    years = sorted(set(re.findall(r'catalogRef[^>]*xlink:title="(\d{4})"', cat)))
    print(f"- Years in the monthly 2 km record: {years[0]}–{years[-1]} ({len(years)})")
    files = {}
    for y in years:
        c = get(f"{TH}/catalog/{base}/{y}/catalog.xml").decode()
        for p in re.findall(r'urlPath="([^"]+\.nc)"', c):
            m = re.search(r"/(\d{6})\d{2}\d+-", p)
            if m: files[m.group(1)] = p
        time.sleep(0.2)
    ks = sorted(files); print(f"- Monthly files: {len(ks)} ({ks[0]} to {ks[-1]}); example: `{files[ks[-1]]}`")
    DO = f"{TH}/dodsC/"
    das = get(DO + files[ks[-1]] + ".das").decode()
    blk = das[das.index("sea_surface_temperature"):][:1500]
    sf = float(re.search(r"scale_factor\s+([-\d.eE]+)", blk).group(1)); ao = float(re.search(r"add_offset\s+([-\d.eE]+)", blk).group(1))
    fv = re.search(r"_FillValue\s+(-?\d+)", blk); fv = int(fv.group(1)) if fv else -32768
    print(f"- Scale {sf}, offset {ao}, fill {fv}")
    def axis(path, name):
        t = get(DO + path + f".ascii?{name}", 180).decode()
        return [float(x) for x in t.split("\n", 2)[-1].replace(",", " ").split() if re.match(r"^-?\d", x)]
    LAT = axis(files[ks[-1]], "lat"); LON = axis(files[ks[-1]], "lon")
    print(f"- Grid: {len(LAT)} x {len(LON)}, lat {LAT[0]:.2f} to {LAT[-1]:.2f}, step {LAT[1]-LAT[0]:.3f}°")
    def idx(arr, v): return min(range(len(arr)), key=lambda k: abs(arr[k] - v))
    LI = {}; LJ = {}
    def point(path, la, lo):
        i = LI.setdefault(round(la, 3), idx(LAT, la)); j = LJ.setdefault(round(lo, 3), idx(LON, lo))
        q = f"sea_surface_temperature[0][{max(i-4,0)}:{i+4}][{max(j-4,0)}:{j+8}]"
        t = get(DO + path + ".ascii?" + q, 90).decode()
        grid = []
        for line in t.split("\n"):
            m = re.match(r"^sea_surface_temperature\.sea_surface_temperature\[0\]\[(\d+)\], (.*)$", line) or re.match(r"^\[0\]\[(\d+)\], (.*)$", line)
            if m: grid.append([int(x) for x in m.group(2).split(",")])
        best = None
        for a, row in enumerate(grid):
            for c, v in enumerate(row):
                if v == fv: continue
                d = (a - 4) ** 2 + (c - 4) ** 2
                if best is None or d < best[0]: best = (d, v * sf + ao)
        if best is None: return None
        k = best[1]; return k - 273.15 if k > 200 else k
    v = point(files[ks[-1]], -33.89, 151.29); print(f"- Test point off Bondi, {ks[-1]}: {v}")
    for sp in ("bull", "tiger"):
        out = []
        for r in rows:
            if sp not in (r.get("Shark.common.name") or "").lower(): continue
            y, mo, la, lo = num(r.get("Incident.year")), num(r.get("Incident.month")), num(r.get("Latitude")), num(r.get("Longitude"))
            if None in (y, mo, la, lo): continue
            k = f"{int(y)}{int(mo):02d}"
            if k not in files: continue
            t = point(files[k], la, lo)  # nearest sea cell with a value within about 10 km
            out.append((k, la, lo, t)); time.sleep(0.15)
        ok = [o for o in out if o[3] is not None and o[3] == o[3]]
        if not ok: print(f"- {sp}: no values"); continue
        ts = sorted(o[3] for o in ok)
        print(f"- **{sp}**: {len(out)} bites in the 2 km record, {len(ok)} with a value; below 19°C: {sum(1 for t in ts if t < 19)}; "
              f"coolest {ts[0]:.1f}, median {st.median(ts):.1f}, warmest {ts[-1]:.1f}")
        for k, la, lo, t in sorted(ok, key=lambda o: o[3])[:6]: print(f"    - {k} {la:.2f},{lo:.2f}: {t:.1f}°C")

# ---------- 2. ABS population by SA2 ----------
def abs_pop():
    u = "https://geo.abs.gov.au/arcgis/rest/services/Hosted/ABS_ERP_2001_2021_SA2/FeatureServer/0/query"
    q = {"where": "sa2_code_2021 LIKE '1%'", "outFields": "sa2_code_2021,sa2_name_2021,erp_no_2001,erp_no_2011,erp_no_2021", "returnGeometry": "false",
         "returnCentroid": "true", "outSR": "4326", "f": "json", "resultRecordCount": 2000}
    j = json.loads(get(u + "?" + urllib.parse.urlencode(q)))
    f = j.get("features", []); print(f"- NSW small areas (SA2): {len(f)}; centroid returned: {'centroid' in (f[0] if f else {})}")
    tot = lambda k: sum((x["attributes"].get(k) or 0) for x in f)
    print(f"- NSW total 2001 {tot('erp_no_2001'):,}, 2011 {tot('erp_no_2011'):,}, 2021 {tot('erp_no_2021'):,}")
    s = [x for x in f if x.get("centroid") and x["centroid"]["y"] < -31.43]
    print(f"- South of Port Macquarie (centroid): {len(s)} areas; examples: " + "; ".join(x["attributes"]["sa2_name_2021"] for x in s[:5]))
    u2 = "https://geo.abs.gov.au/arcgis/rest/services/Hosted/SA2_RP_2024/FeatureServer/0/query"
    j2 = json.loads(get(u2 + "?" + urllib.parse.urlencode({"where": "1=1", "outFields": "*", "returnGeometry": "false", "f": "json", "resultRecordCount": 5})))
    print(f"- 2023–24 layer raw: {json.dumps(j2)[:400]}")
    f2 = j2.get("features", []); print(f"- 2023–24 layer: {len(f2)} NSW areas; fields: {sorted(f2[0]['attributes'])[:12] if f2 else []}")
    lic = get("https://geo.abs.gov.au/arcgis/rest/services/Hosted/ABS_ERP_2001_2021_SA2/FeatureServer/0?f=json").decode()
    m = re.search(r'"licenseInfo"\s*:\s*"([^"]{0,200})', lic); print(f"- License field: {m.group(1) if m else 'not given in the service'}")

# ---------- 3. River flow ----------
def kisters(base, label, sites):
    for site in sites:
        q = {"function": "get_ts_traces", "version": "2", "params": {"site_list": site, "datasource": "A", "varfrom": "100.00", "varto": "141.00",
             "start_time": "20220101000000", "end_time": "20220401000000", "interval": "day", "multiplier": "1", "data_type": "mean"}}
        try:
            j = json.loads(get(base + "?" + urllib.parse.quote(json.dumps(q, separators=(",", ":"))), 90))
            tr = (j.get("_return") or {}).get("traces") or []
            pts = tr[0].get("trace", []) if tr else []
            vals = [num(p.get("v")) for p in pts if num(p.get("v")) is not None]
            print(f"- {label} {site}: error {j.get('error_num')}, {len(vals)} daily values, max {max(vals) if vals else None} ML/day; site: {tr[0].get('site_details', {}).get('name') if tr else '?'}")
        except Exception as e:
            print(f"- {label} {site}: {type(e).__name__}: {str(e)[:200]}")
        q2 = {"function": "get_variable_list", "version": "1", "params": {"site_list": site, "datasource": "A"}}
        try:
            j = json.loads(get(base + "?" + urllib.parse.quote(json.dumps(q2, separators=(",", ":"))), 60))
            v = (j.get("_return") or {}).get("sites", [{}])[0].get("variables", [])
            print(f"    - variables: " + "; ".join(f"{x.get('variable')} {x.get('name')} ({x.get('period_start','')[:4]}–{x.get('period_end','')[:4]})" for x in v[:8]))
        except Exception as e:
            print(f"    - variable list: {type(e).__name__}: {str(e)[:150]}")
def flow():
    kisters("https://realtimedata.waternsw.com.au/cgi/webservice.exe", "WaterNSW", ["204007", "203004", "212200", "215004"])
    kisters("https://water-monitoring.information.qld.gov.au/cgi/webservice.pl", "Queensland", ["145102B", "143001C", "130004A"])

safe("1. IMOS 2 km monthly sea temperature at each bite", imos)
safe("2. ABS population by small area", abs_pop)
