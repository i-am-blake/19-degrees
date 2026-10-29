"""Build an El Niño / La Niña index from HadISST (same record as the rest of the page) via NOAA ERDDAP.
Niño 3.4 box (5°S–5°N, 170°W–120°W), monthly mean SST, anomaly against each month's 1991–2020 average,
3-month running mean (like NOAA's Oceanic Niño Index). Output: <sst_dir>/nino34.csv with date,oni.
Usage: python3 -I fetch_nino34.py <sst_dir>"""
import sys, os, csv, io, urllib.request, collections
out = os.path.join(sys.argv[1], "nino34.csv")
url = ("https://coastwatch.pfeg.noaa.gov/erddap/griddap/erdHadISST.csv?sst"
       "%5B(1950-01-16):1:(last)%5D%5B(4.5):1:(-4.5)%5D%5B(-169.5):1:(-120.5)%5D")
txt = urllib.request.urlopen(url, timeout=300).read().decode()
acc = collections.defaultdict(list)
for i, r in enumerate(csv.reader(io.StringIO(txt))):
    if i < 2 or not r[3] or r[3] == "NaN": continue
    acc[r[0][:7]].append(float(r[3]))
mm = {k: sum(v) / len(v) for k, v in acc.items()}
keys = sorted(mm)
clim = {m: sum(mm[k] for k in keys if k[5:7] == m and 1991 <= int(k[:4]) <= 2020) / 30 for m in [f"{i:02d}" for i in range(1, 13)]}
an = [mm[k] - clim[k[5:7]] for k in keys]
with open(out, "w", newline="") as f:
    w = csv.writer(f); w.writerow(["date", "oni"])
    for i in range(1, len(keys) - 1): w.writerow([keys[i], round((an[i - 1] + an[i] + an[i + 1]) / 3, 3)])
print("wrote", out, len(keys) - 2, "months, last", keys[-2])
