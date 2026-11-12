"""Claim C16, cross-test: do bull sharks leave Sydney on a temperature cue or a calendar (day length) cue?
Usage: python3 -I cue19.py <imos_dir> <beachwatch_enterococci.csv.gz> <out cue.json>
Day length on a given date is the same every year; water temperature is not. So the two can be told apart.
Written down before the numbers were run:
- Departure: a tagged bull shark's last detection off Sydney in a year (33.6-34.2°S, January to September, 2010 on), as in
  claim C16, kept only when it falls on or after 1 March, so sharks that vanished in summer are not counted as autumn exits.
- Water: temperature measured by Harbourwatch at the 'Sydney Harbour' swim sites (NSW Government, CC BY), the mean of
  samples within 10 days either side of a date. A year's autumn warmth is the mean of its March, April and May means.
- Test 1, between years: the year's median departure day against that year's autumn warmth, for years with 5 or more
  departures. Both drift upward over time, so the test that counts removes each one's straight-line trend first.
  Temperature cue predicts later departures in warmer autumns (positive slope); a calendar cue predicts no link.
- Test 2, spread: if sharks leave at a fixed temperature, the temperature at departure varies little and the date varies;
  if they leave on a fixed date, the reverse. The temperature spread is turned into days with the average autumn cooling
  rate, and the smaller spread is the better cue.
- Check: the same on long-running stations only (listening March to August in 8 or more years), because the C16 trend
  itself nearly vanishes there."""
import sys, os, json, numpy as np, pandas as pd
from scipy import stats
imos_dir, bw, out = sys.argv[1:4]
lat, lon = "receiver_deployment_latitude", "receiver_deployment_longitude"
d = pd.read_csv(os.path.join(imos_dir, "BullShark_Carcharhinusleucas.csv.gz"), low_memory=False); d["t"] = pd.to_datetime(d.date_hour_UTC).dt.tz_localize(None)
sy = d[(d[lon] > 150) & (d[lat] < -33.6) & (d[lat] > -34.2)]; sy = sy[(sy.t.dt.month <= 9) & (sy.t.dt.year >= 2010)]

w = pd.read_csv(bw, usecols=["region", "date", "water_temperature_c"]); w = w[(w.region == "Sydney Harbour")].dropna()
w["date"] = pd.to_datetime(w.date); w = w[(w.water_temperature_c > 8) & (w.water_temperature_c < 32)]
daily = w.groupby("date").water_temperature_c.mean().sort_index()
full = daily.reindex(pd.date_range(daily.index.min(), daily.index.max()))
smooth = full.rolling(21, center=True, min_periods=3).mean()
mon = daily.groupby([daily.index.year, daily.index.month]).mean()
autumn = {y: float(np.mean([mon[(y, m)] for m in (3, 4, 5)])) for y in range(2010, int(daily.index.year.max()) + 1) if all((y, m) in mon.index for m in (3, 4, 5))}
# average autumn cooling rate, °C a day, 1 March to 31 July
s = smooth[(smooth.index.month >= 3) & (smooth.index.month <= 7) & (smooth.index.year >= 2010)].dropna()
cool = -stats.linregress(s.index.dayofyear, s.values).slope

def detrend(y, x): r = stats.linregress(x, y); return y - (r.intercept + r.slope * x)
def run(sub):
    last = sub.groupby([sub.t.dt.year.rename("yr"), "animal_id"]).t.max().reset_index()
    last = last[last.t.dt.month >= 3].copy(); last["doy"] = last.t.dt.dayofyear
    last["temp"] = smooth.reindex(last.t.dt.normalize()).values
    yr = last.groupby("yr").agg(n=("doy", "size"), doy=("doy", "median")).reset_index()
    yr["autumn"] = yr.yr.map(autumn); yr = yr[(yr.n >= 5) & yr.autumn.notna()]
    r = stats.linregress(yr.autumn, yr.doy); sp = stats.spearmanr(yr.autumn, yr.doy)
    dd, da = detrend(yr.doy.values, yr.yr.values), detrend(yr.autumn.values, yr.yr.values); rd = stats.linregress(da, dd)
    lt = last.dropna(subset=["temp"])
    return dict(departures=int(len(last)), sharks=int(last.animal_id.nunique()), years=int(len(yr)), y0=int(yr.yr.min()), y1=int(yr.yr.max()),
                raw=dict(days_per_degree=round(r.slope, 1), r=round(r.rvalue, 2), p=float(f"{r.pvalue:.2g}"), spearman=round(sp.statistic, 2), spearman_p=float(f"{sp.pvalue:.2g}")),
                detrended=dict(days_per_degree=round(rd.slope, 1), lo=round(rd.slope - 1.96 * rd.stderr, 1), hi=round(rd.slope + 1.96 * rd.stderr, 1), r=round(rd.rvalue, 2), p=float(f"{rd.pvalue:.2g}")),
                spread=dict(with_temperature=int(len(lt)), date_sd_days=round(float(lt.doy.std()), 1), temp_sd_c=round(float(lt.temp.std()), 2),
                            temp_sd_as_days=round(float(lt.temp.std() / cool), 1), median_temp_at_departure=round(float(lt.temp.median()), 1),
                            median_date=(pd.Timestamp("2021-01-01") + pd.Timedelta(days=float(lt.doy.median()) - 1)).strftime("%-d %B")),
                by_year=[dict(year=int(a.yr), n=int(a.n), median_day=float(a.doy), autumn_c=round(float(a.autumn), 2)) for a in yr.itertuples()])

# long-running stations, as in imos19.py
dcols = ["station_name", "receiver_deployment_datetime_UTC", "receiver_recovery_datetime_UTC", lat, lon]
dep = pd.concat([pd.read_csv(os.path.join(imos_dir, f), usecols=dcols, low_memory=False) for f in os.listdir(imos_dir) if f.endswith(".csv.gz")]).drop_duplicates()
dep = dep[(dep[lon] > 150) & (dep[lat] < -33.6) & (dep[lat] > -34.2)]
dep["a"] = pd.to_datetime(dep.receiver_deployment_datetime_UTC).dt.tz_localize(None)
dep["b"] = pd.to_datetime(dep.receiver_recovery_datetime_UTC, errors="coerce").dt.tz_localize(None).fillna(d.t.max())
yrs = range(2010, int(sy.t.dt.year.max()) + 1)
long_run = [st for st, x in dep.groupby("station_name") if sum(((x.a <= pd.Timestamp(y, 3, 1)) & (x.b >= pd.Timestamp(y, 8, 31))).any() for y in yrs) >= 8]
res = dict(water=dict(sites="Sydney Harbour", first=str(daily.index.min().date()), last=str(daily.index.max().date()), sample_days=int(len(daily)), cooling_c_per_day=round(float(cool), 3)),
           main=run(sy), long_run=dict(run(sy[sy.station_name.isin(long_run)]), stations=len(long_run)))
json.dump(res, open(out, "w"), indent=1); print(json.dumps(res, indent=1))
