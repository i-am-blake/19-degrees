"""Fetch monthly rainfall from the nearest long-running rain gauge to each bite site (claim C6).
Usage: python3 gauge_fetch.py <rain_points.csv> <ghcnd-inventory.txt> <ghcnd-stations.txt> <out_dir> [max_sites]
Gauges: NOAA GHCN (Global Historical Climatology Network), Australian stations from the Bureau of Meteorology.
Monthly totals come from NOAA's Global Summary of the Month service (no account needed), PRCP only."""
import csv, math, os, sys, time, urllib.request, urllib.error
pts_file, inv_file, sta_file, out = sys.argv[1:5]; LIMIT = int(sys.argv[5]) if len(sys.argv) > 5 and sys.argv[5] else 10**6
os.makedirs(out, exist_ok=True); log = open(os.path.join(out, "log.txt"), "w")
names = {l[:11]: l[41:71].strip() for l in open(sta_file) if l.startswith("ASN")}
inv = {}
for l in open(inv_file):
    if l.startswith("ASN") and l[31:35] == "PRCP":
        inv[l[:11]] = (float(l[12:20]), float(l[21:30]), int(l[36:40]), int(l[41:45]))
log.write(f"Australian gauges with rainfall: {len(inv)}\n")
def km(a, b, c, d): return 6371 * math.acos(min(1, math.sin(math.radians(a)) * math.sin(math.radians(c)) + math.cos(math.radians(a)) * math.cos(math.radians(c)) * math.cos(math.radians(d - b))))
sites = list(csv.DictReader(open(pts_file)))[:LIMIT]; pick = {}
w = csv.writer(open(os.path.join(out, "sites.csv"), "w")); w.writerow(["lat", "lon", "station", "name", "km", "first", "last"])
for s in sites:
    a, b = float(s["lat"]), float(s["lon"])
    c = [(km(a, b, la, lo), i) for i, (la, lo, f, e) in inv.items() if abs(la - a) < 0.5 and abs(lo - b) < 0.5 and e - f >= 30]
    c = [x for x in c if x[0] <= 25]
    if not c: w.writerow([a, b, "", "", "", "", ""]); continue
    d, i = min(c); pick[i] = 1; w.writerow([a, b, i, names.get(i, ""), round(d, 1), inv[i][2], inv[i][3]])
log.write(f"sites {len(sites)}, with a gauge within 25 km: {sum(1 for _ in pick)} gauges\n"); log.flush()
end = time.strftime("%Y-12-31"); w2 = csv.writer(open(os.path.join(out, "gauge_monthly.csv"), "w")); w2.writerow(["station", "year", "month", "prcp_mm"])
for k, i in enumerate(sorted(pick)):
    u = ("https://www.ncei.noaa.gov/access/services/data/v1?dataset=global-summary-of-the-month&dataTypes=PRCP&units=metric"
         f"&format=csv&startDate=1900-01-01&endDate={end}&stations={i}")
    t = None
    for tries in range(2):
        try: t = urllib.request.urlopen(u, timeout=60).read().decode(); break
        except urllib.error.HTTPError as e: err = f"{e.code} {e.read()[:200]!r}"
        except Exception as e: err = str(e)
        time.sleep(2)
    if t is None: log.write(f"{i} failed: {err}\n"); log.flush(); continue
    rows = list(csv.DictReader(t.splitlines()))
    if k < 2: log.write(f"SAMPLE {i}: {t[:300]!r}\n")
    n = 0
    for r in rows:
        if r.get("PRCP", "").strip():
            y, m = r["DATE"][:4], r["DATE"][5:7]; w2.writerow([i, y, int(m), r["PRCP"].strip()]); n += 1
    log.write(f"{i} {names.get(i,'')}: {n} months\n"); log.flush(); time.sleep(0.5)
