"""Projected sea temperature change by 2050 at each beach's sea patch, from CMIP6 climate models (claim C3).
Usage: python3 cmip_sst.py <out.csv> [max_models] [experiment]
Reads the public CMIP6 archive on Google Cloud (Pangeo), monthly sea surface temperature (tos), first ensemble member of each
model, and for every beach patch finds the nearest ocean cell. Writes each model's change per calendar month:
mean 2040-2059 under the chosen scenario (default ssp245) minus mean 1995-2014 (historical run), in degrees C.
The page adds that change to each beach's observed 2016-2025 months (HadISST) to count months at 19 C or more around 2050."""
import sys, csv, numpy as np, pandas as pd, xarray as xr, gcsfs
out = sys.argv[1]; MAXM = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2] else 99; EXP = sys.argv[3] if len(sys.argv) > 3 else "ssp245"
PTS = {"goldcoast": (-28.0, 153.9), "byron": (-28.6, 154.0), "newcastle": (-32.9, 152.3), "sydney": (-33.9, 151.5), "wollongong": (-34.4, 151.3),
       "eden": (-37.1, 150.4), "exmouth": (-21.5, 113.5), "geraldton": (-28.5, 113.5), "perth": (-31.9, 115.2), "mandurah": (-32.5, 115.2),
       "margaret": (-33.9, 114.5), "albany": (-35.5, 117.9)}
cat = pd.read_csv("https://storage.googleapis.com/cmip6/pangeo-cmip6.csv")
c = cat[(cat.variable_id == "tos") & (cat.table_id == "Omon") & (cat.member_id == "r1i1p1f1")]
h = c[c.experiment_id == "historical"]; f = c[c.experiment_id == EXP]
models = sorted(set(h.source_id) & set(f.source_id))[:MAXM]
fs = gcsfs.GCSFileSystem(token="anon")
def opn(row): return xr.open_zarr(fs.get_mapper(row.zstore), consolidated=True)
w = csv.writer(open(out, "w")); w.writerow(["model", "beach", "month", "delta_c", "cell_lat", "cell_lon"])
for m in models:
    try:
        rh = h[h.source_id == m].iloc[0]; rf = f[f.source_id == m].iloc[0]
        dh, df = opn(rh), opn(rf)
        lat = next(dh[n] for n in ("lat", "latitude", "nav_lat") if n in dh.variables)
        lon = next(dh[n] for n in ("lon", "longitude", "nav_lon") if n in dh.variables)
        if lat.ndim == 1: LA, LO = np.meshgrid(lat.values, lon.values, indexing="ij")
        else: LA, LO = lat.values, lon.values
        LO = np.where(LO < 0, LO + 360, LO)
        ok = np.isfinite(dh.tos.isel(time=0).values)
        sp = [d for d in dh.tos.dims if d != "time"]
        for b, (a, o) in PTS.items():
            d2 = np.where(ok, (LA - a) ** 2 + ((LO - o) * np.cos(np.radians(a))) ** 2, np.inf)
            i, j = np.unravel_index(np.argmin(d2), d2.shape)
            if d2[i, j] > 4: continue
            sel = {sp[0]: i, sp[1]: j}
            th = dh.tos.isel(**sel).sel(time=slice("1995", "2014")).load(); tf = df.tos.isel(**sel).sel(time=slice("2040", "2059")).load()
            for mo in range(1, 13):
                dv = float(tf[tf["time.month"] == mo].mean() - th[th["time.month"] == mo].mean())
                w.writerow([m, b, mo, round(dv, 3), round(float(LA[i, j]), 2), round(float(LO[i, j]), 2)])
        print("ok", m, flush=True)
    except Exception as e:
        print("skip", m, type(e).__name__, str(e)[:120], flush=True)
