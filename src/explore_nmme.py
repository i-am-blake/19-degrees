"""Look only: can NOAA's NMME seasonal forecasts tell, months ahead, when the sea off NSW will be at or above 19 C?
Every NMME multi-model forecast issued since Aug 2011 (sea surface temperature anomaly, leads 1-6 months), at seven
offshore 1-degree points from Byron Bay to Eden, is checked against what HadISST then observed, and against two simple
rivals: persistence (last month's anomaly carries on) and the recent normal (the previous ten years' average for that month).
Prints a report; changes nothing."""
import csv, io, sys, time, urllib.request
import numpy as np, netCDF4
UA = {"User-Agent": "19-degrees-explore/1.0 (+https://19-degrees.org)"}
def get(u, t=180):
    for k in range(5):
        try: return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=t).read()
        except Exception:
            if k == 4: raise
            time.sleep(15 * (k + 1))
PTS = {"Byron Bay": (-28.5, 154.0), "Coffs Harbour": (-30.5, 153.5), "Port Macquarie": (-31.5, 153.2), "Newcastle": (-32.5, 152.8),
       "Sydney": (-33.5, 151.8), "Jervis Bay": (-35.5, 150.8), "Eden": (-37.5, 150.5)}
H = "https://coastwatch.pfeg.noaa.gov/erddap/griddap/erdHadISST.csv?sst"
obs = {}
for name, (la, lo) in PTS.items():
    t = get(f"{H}%5B(1981-01-16):1:(last)%5D%5B({la})%5D%5B({lo})%5D").decode()
    obs[name] = {r[0][:7]: float(r[3]) for r in list(csv.reader(io.StringIO(t)))[2:] if r[3] not in ("NaN", "")}
    time.sleep(1)
def ym(y, m): y += (m - 1) // 12; m = (m - 1) % 12 + 1; return f"{y}-{m:02d}"
def clim(name, mon, y0, y1):
    v = [obs[name].get(f"{y}-{mon:02d}") for y in range(y0, y1 + 1)]; v = [x for x in v if x is not None]
    return sum(v) / len(v) if len(v) >= 0.8 * (y1 - y0 + 1) else None
C91 = {n: {m: clim(n, m, 1991, 2020) for m in range(1, 13)} for n in PTS}
last_obs = max(max(d) for d in obs.values()); print(f"HadISST at the 7 points through {last_obs}")
B = "https://ftp.cpc.ncep.noaa.gov/NMME/realtime_anom/ENSMEAN/"
rows, shown = [], False
from concurrent.futures import ThreadPoolExecutor
ISS = [(y, m) for y in range(2011, 2027) for m in range(1, 13) if (y, m) >= (2011, 8) and ym(y, m) <= last_obs]
def fetch(ym_):
    y, m = ym_
    try: return ym_, get(B + f"{y}{m:02d}0800/NMME.tmpsfc.{y}{m:02d}.ENSMEAN.anom.nc", 300)
    except Exception as e: return ym_, e
t0 = time.time(); _, b0 = fetch(ISS[-1]); print(f"one file: {len(b0) if isinstance(b0, bytes) else b0} bytes in {time.time()-t0:.0f}s", flush=True)
with ThreadPoolExecutor(8) as ex: FILES = dict(ex.map(fetch, ISS))
print(f"downloaded {sum(isinstance(v, bytes) for v in FILES.values())}/{len(ISS)} in {time.time()-t0:.0f}s", flush=True)
for (y, m) in ISS:
        b = FILES[(y, m)]
        if not isinstance(b, bytes): print(f"- {y}-{m:02d}: {type(b).__name__}"); continue
        ds = netCDF4.Dataset("x", memory=b)
        if not shown:
            print("File layout:", {k: (v.dimensions, v.shape) for k, v in ds.variables.items()}); shown = True
        var = [v for v in ds.variables.values() if len(v.dimensions) >= 3][0]
        dims = var.dimensions; lat = ds.variables[[d for d in dims if "lat" in d.lower()][0]][:]; lon = ds.variables[[d for d in dims if "lon" in d.lower()][0]][:]
        a = np.ma.filled(var[:].astype(float), np.nan)
        while a.ndim > 3: a = a[0]          # drop a single initial-time axis if present
        nlead = a.shape[0]
        for name, (la, lo) in PTS.items():
            lo360 = lo % 360
            best = None
            for di in range(-1, 2):          # nearest model cell with a value, within a degree
                for dj in range(-1, 2):
                    i = int(np.argmin(abs(lat - la))) + di; j = int(np.argmin(abs(lon - lo360))) + dj
                    if 0 <= i < len(lat) and 0 <= j < len(lon) and not np.isnan(a[0, i, j]):
                        d = (lat[i] - la) ** 2 + (lon[j] - lo360) ** 2
                        if best is None or d < best[0]: best = (d, i, j)
            if not best: continue
            _, i, j = best
            prev = ym(y, m - 1); pa = obs[name].get(prev); pa = pa - C91[name][int(prev[5:])] if pa is not None else None
            for L in range(min(nlead, 6)):   # lead 0 = the issue month itself
                tg = ym(y, m + L); mo = int(tg[5:]); o = obs[name].get(tg)
                if o is None: continue
                c = C91[name][mo]; rec = clim(name, mo, int(tg[:4]) - 10, int(tg[:4]) - 1)
                rows.append(dict(p=name, issue=f"{y}-{m:02d}", target=tg, lead=L + 1, obs=o, nmme=c + a[L, i, j],
                                 persist=c + pa if pa is not None else None, recent=rec))
print(f"\n{len(rows)} forecast-target pairs\n")
def score(sel, k):
    s = [r for r in sel if r[k] is not None]
    e = np.array([r[k] - r["obs"] for r in s])
    hit = np.mean([(r[k] >= 19) == (r["obs"] >= 19) for r in s])
    edge = [r for r in s if abs(r["obs"] - 19) <= 1.5]
    he = np.mean([(r[k] >= 19) == (r["obs"] >= 19) for r in edge]) if edge else float("nan")
    return f"{np.sqrt(np.mean(e ** 2)):.2f} / {hit:.0%} / {he:.0%}"
print("## Error and 19°C calls by lead (RMSE °C / months called right / right when within 1.5°C of 19)\n")
print("| Lead | NMME | Persistence | Recent normal | n |\n|---|---|---|---|---|")
for L in range(1, 7):
    s = [r for r in rows if r["lead"] == L]
    print(f"| {L} | {score(s, 'nmme')} | {score(s, 'persist')} | {score(s, 'recent')} | {len(s)} |")
print("\n## By place, leads 2–4\n\n| Place | NMME | Persistence | Recent normal |\n|---|---|---|---|")
for n in PTS:
    s = [r for r in rows if r["p"] == n and 2 <= r["lead"] <= 4]
    if s: print(f"| {n} | {score(s, 'nmme')} | {score(s, 'persist')} | {score(s, 'recent')} |")
# Season length: forecasts issued in October, months at or above 19 C from October to March
print("\n## Warm months Oct–Mar, forecast issued in October (observed / NMME / persistence / recent normal)\n")
for n in ("Port Macquarie", "Sydney", "Jervis Bay", "Eden"):
    out = []
    for y in range(2011, 2026):
        s = [r for r in rows if r["p"] == n and r["issue"] == f"{y}-10"]
        if len(s) < 6: continue
        cnt = lambda k: sum(1 for r in s if r[k] is not None and r[k] >= 19)
        out.append((y, cnt("obs"), cnt("nmme"), cnt("persist"), cnt("recent")))
    if out:
        mae = lambda k: np.mean([abs(o[k] - o[1]) for o in out])
        print(f"- **{n}**: " + "; ".join(f"{o[0]}: {o[1]}/{o[2]}/{o[3]}/{o[4]}" for o in out) + f"  \n  mean miss: NMME {mae(2):.2f}, persistence {mae(3):.2f}, recent normal {mae(4):.2f} months")
