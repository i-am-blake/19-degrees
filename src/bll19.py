"""C25: bull and tiger shark catch against water temperature at the gear,
NOAA SEFSC Bottom Longline Survey (InPort 28636), 1995-2025.

Build the station table from the spreadsheet the survey team provided:
    python3 src/bll19.py path/to/NMFS_SEFSC_BLL_Data_1995-2025.xlsx
Rerun the summary from the published station table:
    python3 src/bll19.py
"""
import sys
import pandas as pd

OUT = "data/us-bottom-longline-stations.csv"
KEY = ["YEAR", "VESSEL", "CRUISE", "PASC"]

def build(xlsx):
    x = pd.read_excel(xlsx, sheet_name=None)
    s, l = x["Stations"], x["Lengths"]
    n = lambda taxon, name: l[l.TAXON == taxon].groupby(KEY).size().rename(name)
    m = (s.set_index(KEY).join(n("CARCHARHINUS LEUCAS", "bull"))
           .join(n("GALEOCERDO CUVIER", "tiger")).fillna({"bull": 0, "tiger": 0}).reset_index())
    m = m.rename(columns={"FLYLAST_OUTTIME": "time", "FLYLAST_OUTLAT": "lat", "FLYLAST_OUTLON": "lon",
                          "FLYLAST_OUTDEPTH (m)": "depth_m", "TEMP ©": "temp_c", "NUMBERHOOKS": "hooks"})
    m = m[KEY + ["time", "lat", "lon", "depth_m", "temp_c", "hooks", "bull", "tiger"]]
    m[["bull", "tiger"]] = m[["bull", "tiger"]].astype(int)
    m.to_csv(OUT, index=False)
    return m

def summary(m):
    m = m.dropna(subset=["temp_c"])
    cold = m.temp_c < 19
    print(f"sets with temperature: {len(m)}; share below 19C: {cold.mean():.1%}")
    for sp in ["bull", "tiger"]:
        print(f"{sp}: {m[sp].sum()} caught, {m.loc[cold, sp].sum()} below 19C, "
              f"coolest {m.loc[m[sp] > 0, 'temp_c'].min():.2f}C")
    bands = pd.cut(m.temp_c, [0, 17, 19, 21, 23, 25, 27, 40], right=False)
    g = m.groupby(bands, observed=True)[["hooks", "bull", "tiger"]].sum()
    g["bull_per_1000_hooks"] = (g.bull / g.hooks * 1000).round(2)
    print(g.to_string())
    sh = m[m.depth_m < 40]
    print(f"sets shallower than 40 m below 19C: {(sh.temp_c < 19).sum()}, bull sharks there: {sh.loc[sh.temp_c < 19, 'bull'].sum()}")

if __name__ == "__main__":
    summary(build(sys.argv[1]) if len(sys.argv) > 1 else pd.read_csv(OUT))
