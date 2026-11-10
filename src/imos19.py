"""Check the 19°C line against IMOS acoustic tracking of tagged bull sharks in NSW.
Usage: python3 -I imos19.py <imos_dir> <sst_dir> [imos.json]
  imos_dir: the 'imos-data' branch of the repo (BullShark_Carcharhinusleucas.csv.gz etc.), refreshed monthly by
            .github/workflows/fetch-imos.yml from IMOS Animal Tracking (acoustic detections QC summary, CC BY 4.0).
  sst_dir:  regional HadISST monthly series from fetch_sst.py.
  imos.json (optional): writes the numbers the page shows; build19.py reads it from beside itself.
A 'shark-day' is one tagged shark detected on one day in one region."""
import sys, os, json, pandas as pd, numpy as np
imos_dir, sst_dir = sys.argv[1:3]; out = sys.argv[3] if len(sys.argv) > 3 else None
d = pd.read_csv(os.path.join(imos_dir, "BullShark_Carcharhinusleucas.csv.gz"), low_memory=False); d["t"] = pd.to_datetime(d.date_hour_UTC)
lat, lon = "receiver_deployment_latitude", "receiver_deployment_longitude"
n = d[(d[lon] > 150) & (d[lat] < -28.2) & (d[lat] > -37.6)].copy()
reg = lambda l: "NSW North Coast" if l > -31 else "Mid North Coast & Hunter" if l > -33.3 else "Sydney & Central Coast" if l > -34.2 else "NSW South Coast"
n["region"] = n[lat].map(reg); n["day"] = n.t.dt.strftime("%Y-%m-%d"); n["ym"] = n.t.dt.strftime("%Y-%m")
days = n.drop_duplicates(["animal_id", "day", "region"]).copy()
sst = {r: dict(pd.read_csv(os.path.join(sst_dir, r.replace(" & ", " and ").replace(" ", "_") + ".csv")).values) for r in days.region.unique()}
days["sst"] = [sst[r].get(m, np.nan) for r, m in zip(days.region, days.ym)]
k = days.dropna(subset=["sst"])
R = dict(days=int(len(k)), sharks=int(k.animal_id.nunique()), y0=int(k.t.min().year), y1=int(k.t.max().year),
         below=int((k.sst < 19).sum()), pct_warm=round(100 - (k.sst < 19).mean() * 100, 1), min_sst=round(float(k.sst.min()), 1), last=str(d.t.max().date()))
print(f"NSW tagged bull shark-days: {R['days']} ({R['sharks']} sharks, {R['y0']}-{R['y1']})")
print(f"in months below 19°C: {R['below']} ({100-R['pct_warm']:.1f}%); coolest month: {R['min_sst']}°C")
for r, key in [("Sydney & Central Coast", "syd"), ("NSW South Coast", "south")]:
    s = pd.Series(sst[r]); s = s[(s.index >= k.ym.min()) & (s.index <= k.ym.max())]
    kr = k[k.region == r]
    R[key + "_months_below"] = int(round((s < 19).mean() * 100)); R[key + "_days_below"] = round((kr.sst < 19).mean() * 100, 1)
    print(f"{r}: {R[key+'_months_below']}% of months below 19°C, {R[key+'_days_below']}% of shark-days")
sc = k[k.region == "NSW South Coast"].copy(); sc["season"] = np.where(sc.t.dt.month >= 7, sc.t.dt.year, sc.t.dt.year - 1)
g = sc.groupby("season").agg(days=("animal_id", "size"), sharks=("animal_id", "nunique"), receivers=("station_name", "nunique"))
print("South of Sydney by season (shark-days, sharks, receivers that detected a bull shark):"); print(g.to_string())
early, recent = g.loc[g.index <= 2012], g.loc[g.index >= 2019]
R["c2"] = dict(early_min=int(early.sharks.min()), early_max=int(early.sharks.max()), recent_min=int(recent.sharks.min()), recent_max=int(recent.sharks.max()),
               rec_peak=int(g.receivers.max()), rec_peak_season=int(g.receivers.idxmax()),
               rec_last3_min=int(g.tail(3).receivers.min()), rec_last3_max=int(g.tail(3).receivers.max()),
               months=sorted(int(m) for m in sc.t.dt.month.value_counts()[lambda x: x >= 5].index))
# C16: last detection off Sydney each year (Jan-Sep), per shark
from scipy import stats
sy = d[(d[lon] > 150) & (d[lat] < -33.6) & (d[lat] > -34.2)].copy(); sy["t"] = sy.t.dt.tz_localize(None)
sy = sy[(sy.t.dt.month <= 9) & (sy.t.dt.year >= 2010)]
last = sy.groupby([sy.t.dt.year.rename("yr"), "animal_id"]).t.max().reset_index(); last["doy"] = last.t.dt.dayofyear
lr = stats.linregress(last.yr, last.doy); y1 = int(last.yr.max())
md = lambda a, b: (pd.Timestamp("2021-01-01") + pd.Timedelta(days=float(last[(last.yr >= a) & (last.yr <= b)].doy.median()) - 1)).strftime("%-d %B")
R["c16"] = dict(early=md(2010, 2013), recent=md(y1 - 4, y1), recent_from=y1 - 4, recent_to=y1, slope=round(lr.slope, 1), lo=round(lr.slope - 1.96 * lr.stderr, 1), hi=round(lr.slope + 1.96 * lr.stderr, 1),
                p=float(lr.pvalue), n=int(len(last)), sharks=int(last.animal_id.nunique()))
print("C16 leaving Sydney:", R["c16"])
# C16 held to listening stations: a later "last detection" could just mean receivers stayed in the water longer. Each
# station's deployments come from every species file on the imos-data branch (a station shows up once anything was heard).
dcols = ["station_name", "receiver_deployment_datetime_UTC", "receiver_recovery_datetime_UTC", lat, lon]
files = [f for f in os.listdir(imos_dir) if f.endswith(".csv.gz")]
dep = pd.concat([pd.read_csv(os.path.join(imos_dir, f), usecols=dcols, low_memory=False) for f in files]).drop_duplicates()
dep = dep[(dep[lon] > 150) & (dep[lat] < -33.6) & (dep[lat] > -34.2)]
dep["a"] = pd.to_datetime(dep.receiver_deployment_datetime_UTC).dt.tz_localize(None)
dep["b"] = pd.to_datetime(dep.receiver_recovery_datetime_UTC, errors="coerce").dt.tz_localize(None).fillna(d.t.max().tz_localize(None))
yrs = range(2010, y1 + 1); win = {}
for st, x in dep.groupby("station_name"):
    win[st] = {y for y in yrs if ((x.a <= pd.Timestamp(y, 3, 1)) & (x.b >= pd.Timestamp(y, 8, 31))).any()}  # listening March to August
def fit(sub):
    l2 = sub.groupby([sub.t.dt.year.rename("yr"), "animal_id"]).t.max().reset_index(); l2["doy"] = l2.t.dt.dayofyear
    r = stats.linregress(l2.yr, l2.doy)
    return dict(slope=round(r.slope, 1), lo=round(r.slope - 1.96 * r.stderr, 1), hi=round(r.slope + 1.96 * r.stderr, 1), p=float(r.pvalue), n=int(len(l2)), sharks=int(l2.animal_id.nunique()))
on = sy[[y in win.get(s, ()) for s, y in zip(sy.station_name, sy.t.dt.year)]]
long_run = [s for s, w in win.items() if len(w) >= 8]
R["c16"]["listening"] = fit(on)
R["c16"]["long_run"] = dict(fit(sy[sy.station_name.isin(long_run)]), stations=len(long_run), years=len(yrs))
print("C16 held to stations:", R["c16"]["listening"], R["c16"]["long_run"])
# C30: how much the public data says about young white sharks (under 3 m total length) off the Central Coast and Newcastle
w = pd.read_csv(os.path.join(imos_dir, "WhiteShark_Carcharodoncarcharias.csv.gz"), low_memory=False); w["t"] = pd.to_datetime(w.date_hour_UTC)
def tl(m):
    import re
    x = re.search(r"TOTAL LENGTH = ([\d.]+) (mm|cm|m)", str(m)) or re.search(r"LENGTH = ([\d.]+) (mm|cm|m)", str(m))
    if not x: return np.nan
    v = float(x[1]) / {"mm": 1000, "cm": 100, "m": 1}[x[2]]
    return v * 10 if v < 1 else v  # a few lengths are entered in mm by mistake (e.g. "188 mm" for 188 cm)
w["tl"] = w.measurement.map(tl)
j = w[(w.tl < 3) & (w[lon] > 150) & (w[lat] < -32.3) & (w[lat] > -34.2)]
R["c30"] = dict(sharks=int(j.animal_id.nunique()), days=int(j.t.dt.date.nunique()), y0=int(j.t.dt.year.min()), y1=int(j.t.dt.year.max()),
                years=int(j.t.dt.year.nunique()), all_white=int(w.animal_id.nunique()))
print("C30 young white sharks:", R["c30"])
if out: json.dump(R, open(out, "w"), indent=1); print("wrote", out)
