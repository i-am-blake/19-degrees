"""Check the 19°C line against IMOS acoustic tracking of tagged bull sharks in NSW.
Usage: python3 -I imos19.py <BullShark_Carcharhinusleucas.csv.gz> <sst_dir>
Input: IMOS Animal Tracking QC summary (CC BY 4.0), fetched by .github/workflows/fetch-imos.yml (branch imos-data).
Counts 'shark-days' (one tagged shark detected on one day in one region) and the month's HadISST sea temperature for that region."""
import sys, pandas as pd, numpy as np
src, sst_dir = sys.argv[1:3]
d = pd.read_csv(src, low_memory=False); d["t"] = pd.to_datetime(d.date_hour_UTC)
lat, lon = "receiver_deployment_latitude", "receiver_deployment_longitude"
n = d[(d[lon] > 150) & (d[lat] < -28.2) & (d[lat] > -37.6)].copy()
reg = lambda l: "NSW North Coast" if l > -31 else "Mid North Coast & Hunter" if l > -33.3 else "Sydney & Central Coast" if l > -34.2 else "NSW South Coast"
n["region"] = n[lat].map(reg); n["day"] = n.t.dt.strftime("%Y-%m-%d"); n["ym"] = n.t.dt.strftime("%Y-%m")
days = n.drop_duplicates(["animal_id", "day", "region"]).copy()
sst = {r: dict(pd.read_csv(f"{sst_dir}/{r.replace(' & ', ' and ').replace(' ', '_')}.csv").values) for r in days.region.unique()}
days["sst"] = [sst[r].get(m, np.nan) for r, m in zip(days.region, days.ym)]
k = days.dropna(subset=["sst"])
print(f"NSW tagged bull shark-days: {len(k)} ({k.animal_id.nunique()} sharks, {k.t.min():%Y}-{k.t.max():%Y})")
print(f"in months below 19°C: {(k.sst < 19).sum()} ({(k.sst < 19).mean()*100:.1f}%); coolest month: {k.sst.min():.2f}°C")
for r in ["Sydney & Central Coast", "NSW South Coast"]:
    s = pd.Series(sst[r]); s = s[(s.index >= k.ym.min()) & (s.index <= k.ym.max())]
    kr = k[k.region == r]
    print(f"{r}: {(s < 19).mean()*100:.0f}% of months below 19°C, {(kr.sst < 19).mean()*100:.1f}% of shark-days")
sc = k[k.region == "NSW South Coast"].copy(); sc["season"] = np.where(sc.t.dt.month >= 7, sc.t.dt.year, sc.t.dt.year - 1)
print("South of Sydney by season (shark-days, sharks, receivers that detected a bull shark):")
print(sc.groupby("season").agg(days=("animal_id", "size"), sharks=("animal_id", "nunique"), receivers=("station_name", "nunique")).to_string())
