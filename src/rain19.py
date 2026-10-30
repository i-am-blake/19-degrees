"""Claim C6 (rain): are bull shark bites more likely in wetter-than-usual months at the place they happened?
Usage:
  python3 -I rain19.py fetch <asid.csv> <chirps_dir> [kd_dir]   download CHIRPS monthly rain (and, optionally, MODIS water clarity) at bite sites
  python3 -I rain19.py test  <asid.csv> <chirps_dir> [kd_dir] [rain.json]
Data: CHIRPS v2.0 monthly precipitation, 0.05 deg, 1981 to now (Funk et al. 2015, Scientific Data; public domain, CC0),
and MODIS Aqua Kd490 monthly water clarity, 2003-2022 (NASA Ocean Biology Processing Group), both via NOAA CoastWatch ERDDAP.
The bite database gives month and year, not the day, so this is a monthly test: for each bite, the bite month's rain is ranked
against the same calendar month in every other year (1982-2025) at the same 5 km cell. With no link, a quarter of bites would
fall in the wettest quarter. White shark bites are the comparison group."""
import csv, glob, json, math, os, sys, time, urllib.request
E = "https://coastwatch.pfeg.noaa.gov/erddap/griddap/"
def bites(asid, y0):
    for x in csv.DictReader(open(asid)):
        sp = x["Shark.common.name"].lower(); sp = "bull" if "bull" in sp else "white" if "white" in sp else None
        if not sp or x["Provoked/unprovoked"].strip() != "unprovoked" or not x["Latitude"].strip(): continue
        if not x["Incident.year"].isdigit() or not x["Incident.month"].strip() or int(x["Incident.year"]) < y0: continue
        yield sp, int(x["Incident.year"]), int(x["Incident.month"]), round(float(x["Latitude"]), 2), round(float(x["Longitude"]), 2), x["Site.category"].strip()
def get(url, fn):
    if os.path.exists(fn): return
    for t in range(3):
        try: open(fn, "wb").write(urllib.request.urlopen(url, timeout=180).read()); return
        except Exception: time.sleep(3)
    print("could not fetch", fn)
def series(fn, a, b):
    cells = {}
    for t, la, lo, v in list(csv.reader(open(fn)))[2:]:
        if v != "NaN": cells.setdefault((float(la), float(lo)), {})[(int(t[:4]), int(t[5:7]))] = float(v)
    if not cells: return {}
    return cells[min(cells, key=lambda k: (k[0] - a) ** 2 + (k[1] - b) ** 2)]
def rank(s, y, m, years):
    if (y, m) not in s: return None
    clim = [s[(yy, m)] for yy in years if yy != y and (yy, m) in s]
    if len(clim) < 8: return None
    v = s[(y, m)]; return (sum(c < v for c in clim) + 0.5 * sum(c == v for c in clim)) / len(clim)
def tail(n, k, p): return sum(math.comb(n, j) * p ** j * (1 - p) ** (n - j) for j in range(k, n + 1))
def summary(ps):
    n = len(ps); q = sum(p >= 0.75 for p in ps); t = sum(p >= 0.9 for p in ps)
    return {"n": n, "q": q, "q_pct": round(100 * q / n), "q_p": round(tail(n, q, 0.25), 3), "t": t, "t_pct": round(100 * t / n), "t_p": round(tail(n, t, 0.1), 3), "mean": round(sum(ps) / n, 2)}
mode, asid, cdir = sys.argv[1:4]; kdir = sys.argv[4] if len(sys.argv) > 4 else None
if mode == "fetch":
    os.makedirs(cdir, exist_ok=True)
    for a, b in sorted({(r[3], r[4]) for r in bites(asid, 1981)}):
        get(E + f"chirps20GlobalMonthlyP05.csv?precip%5B(1981-01-01):1:(last)%5D%5B({a-0.06}):1:({a+0.06})%5D%5B({b-0.06}):1:({b+0.06})%5D", os.path.join(cdir, f"{a}_{b}.csv"))
    if kdir:
        os.makedirs(kdir, exist_ok=True)
        for a, b in sorted({(r[3], r[4]) for r in bites(asid, 2003) if r[1] <= 2022}):
            get(E + f"erdMH1kd490mday.csv?k490%5B(2003-01-16):1:(2022-05-16)%5D%5B({a+0.15}):1:({a-0.15})%5D%5B({b-0.15}):1:({b+0.15})%5D", os.path.join(kdir, f"{a}_{b}.csv"))
    sys.exit()
out = sys.argv[5] if len(sys.argv) > 5 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "rain.json")
res = {"y0": 1982}; ps = {"bull": [], "white": []}; cats = {}
for sp, y, m, a, b, cat in bites(asid, 1982):
    fn = os.path.join(cdir, f"{a}_{b}.csv")
    if not os.path.exists(fn): continue
    s = series(fn, a, b); p = rank(s, y, m, range(1982, 2026))
    if p is None: continue
    ps[sp].append(p)
    if sp == "bull": cats.setdefault(cat, []).append(p)
    res["y1"] = max(res.get("y1", 0), y)
res["bull"] = summary(ps["bull"]); res["white"] = summary(ps["white"])
res["bull_cat"] = {k: summary(v) for k, v in cats.items() if len(v) >= 5}
if kdir:
    import statistics as st
    kp = []
    for sp, y, m, a, b, cat in bites(asid, 2003):
        fn = os.path.join(kdir, f"{a}_{b}.csv")
        if sp != "bull" or y > 2022 or not os.path.exists(fn): continue
        cells = {}
        for t, la, lo, v in list(csv.reader(open(fn)))[2:]:
            if v != "NaN": cells.setdefault((int(t[:4]), int(t[5:7])), []).append(float(v))
        s = {k: st.median(v) for k, v in cells.items()}; p = rank(s, y, m, range(2003, 2023))
        if p is not None: kp.append(p)
    if kp: res["kd"] = summary(kp)
json.dump(res, open(out, "w"), indent=1); print(json.dumps(res))
