"""Projected warm-season sea temperature change by 2050 on a 2-degree world grid, from CMIP6 climate models.
Usage: python3 cmip_field.py <out.json> [max_models] [experiment] [future years, e.g. 2040-2059]
For every model (first ensemble member) it takes the warm-season month (February south of the equator, August north of it),
averages 2016-2025 and the future years from the scenario run, and samples the change at the nearest model ocean cell
to each 2-degree cell centre. Writes the median change across models per cell, in hundredths of a degree C (null on land),
plus each model's global list, so anyone can recompute the median. Used by the home page map of the 19 C coastline."""
import sys, json, numpy as np, pandas as pd, xarray as xr, gcsfs
from scipy.spatial import cKDTree
out = sys.argv[1]; MAXM = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2] else 99
EXP = sys.argv[3] if len(sys.argv) > 3 and sys.argv[3] else "ssp245"; FUT = sys.argv[4] if len(sys.argv) > 4 and sys.argv[4] else "2040-2059"
F0, F1 = FUT.split("-")
glat = np.repeat(89 - 2 * np.arange(90), 180); glon = np.tile(-179 + 2 * np.arange(180), 90)
def xyz(la, lo):
    la, lo = np.radians(la), np.radians(lo)
    return np.stack([np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)], -1)
G = xyz(glat, glon); south = glat < 0
cat = pd.read_csv("https://storage.googleapis.com/cmip6/pangeo-cmip6.csv")
c = cat[(cat.variable_id == "tos") & (cat.table_id == "Omon") & (cat.member_id == "r1i1p1f1")]
h = c[c.experiment_id == "historical"]; f = c[c.experiment_id == EXP]
models = sorted(set(h.source_id) & set(f.source_id))[:MAXM]
fs = gcsfs.GCSFileSystem(token="anon")
per = {}
for m in models:
    try:
        df = xr.open_zarr(fs.get_mapper(f[f.source_id == m].iloc[0].zstore), consolidated=True, use_cftime=True)
        lat = next(df[n] for n in ("lat", "latitude", "nav_lat") if n in df.variables)
        lon = next(df[n] for n in ("lon", "longitude", "nav_lon") if n in df.variables)
        if lat.ndim == 1: LA, LO = np.meshgrid(lat.values, lon.values, indexing="ij")
        else: LA, LO = lat.values, lon.values
        tos = df.tos
        d = {}
        for mo in (2, 8):
            a = tos.sel(time=slice("2016", "2025")); a = a.isel(time=(a["time.month"] == mo).values).mean("time").values
            b = tos.sel(time=slice(F0, F1)); b = b.isel(time=(b["time.month"] == mo).values).mean("time").values
            d[mo] = (b - a).ravel()
        ok = np.isfinite(d[2]) & np.isfinite(d[8]) & np.isfinite(LA.ravel()) & np.isfinite(LO.ravel())
        tree = cKDTree(xyz(LA.ravel()[ok], LO.ravel()[ok]))
        dist, idx = tree.query(G)
        v = np.where(south, d[2][ok][idx], d[8][ok][idx])
        v = np.where(dist < np.radians(2.5), v, np.nan)  # nearest ocean cell within about 2.5 degrees
        per[m] = v
        print("ok", m, flush=True)
    except Exception as e:
        print("skip", m, type(e).__name__, str(e)[:120], flush=True)
M = np.array(list(per.values()))
med = np.nanmedian(M, 0) if len(M) else np.full(len(G), np.nan)
enc = lambda a: [None if not np.isfinite(x) else int(round(x * 100)) for x in a]
json.dump({"about": "Median CMIP6 change in warm-season sea surface temperature (Feb south, Aug north), %s minus 2016-2025, %s, hundredths of a degree C, 2-degree grid from 89N/179W, row by row." % (FUT, EXP),
           "rows": 90, "cols": 180, "models": list(per), "median": enc(med), "per_model": {k: enc(v) for k, v in per.items()}}, open(out, "w"), separators=(",", ":"))
