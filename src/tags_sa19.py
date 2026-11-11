"""Claim C25, measured on the sharks: water temperature recorded by pop-up satellite tags on five bull sharks tagged in
South Africa's Breede River (Lubitz et al. 2024, Nature Climate Change; data on Dryad, doi:10.5061/dryad.xd2547dn1, CC0).
Usage: python3 -I tags_sa19.py <folder with SharkID1.csv ... SharkID5.csv> <out tags_sa.json>
Dryad blocks automated downloads, so the files are downloaded by hand from the Dryad page. Each record is averaged into
10-minute bins (the transmitted tags already are; shark 3's archival record is every 5 s). Reports the share of time at
19°C or warmer, shark-days whose average was below 19°C, and the coldest reading. The tags don't record position."""
import json, os, sys
import pandas as pd

SRC, OUT = sys.argv[1:3]
per, bins, below, days, dbelow, coldest = {}, 0, 0, 0, 0, 99
for i in range(1, 6):
    f = os.path.join(SRC, f"SharkID{i}.csv")
    if i == 3:
        df = pd.read_csv(f, usecols=["Time", "Depth", "Temperature"])
        df["t"] = pd.to_datetime(df["Time"], format="%H:%M:%S %d-%b-%Y", errors="coerce")
    else:
        df = pd.read_csv(f)
        df["t"] = pd.to_datetime(df["Day"] + " " + df["Time"], format="%d-%b-%y %H:%M:%S", errors="coerce")
    r = df.dropna(subset=["t", "Temperature"]).set_index("t").sort_index()[["Temperature", "Depth"]].resample("10min").mean().dropna(subset=["Temperature"])
    T = r["Temperature"]; day = T.resample("1D").mean().dropna()
    per[f"shark{i}"] = dict(days=int(len(day)), pct_below19=round(100 * (T < 19).mean(), 1), min=round(float(T.min()), 1))
    bins += len(T); below += int((T < 19).sum()); days += len(day); dbelow += int((day < 19).sum()); coldest = min(coldest, float(T.min()))
out = dict(sharks=len(per), years="2019–2020", bins_10min=bins, pct_time_19_or_warmer=round(100 * (1 - below / bins), 1),
           shark_days=days, days_mean_below19=dbelow, coldest=round(coldest, 1),
           days_range=[min(v["days"] for v in per.values()), max(v["days"] for v in per.values())], per_shark=per)
old = json.load(open(OUT)) if os.path.exists(OUT) else {}
out["cold_week"] = old.get("cold_week", "")
json.dump(out, open(OUT, "w"), indent=1, ensure_ascii=False)
print("tags_sa", json.dumps(out))
