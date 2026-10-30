"""Claim C3: months a year at 19 C or more around 2050, from CMIP6 models (cmip_sst.py output) added to each beach's observed months.
Usage: python3 -I proj19.py <beach_dir> <cmip_tos_delta_ssp245.csv> [proj.json]
For each beach, the observed 2016-2025 average of each calendar month (HadISST patch, as on the page) plus each model's
projected change for that month (2040-2059 minus 2016-2025) gives a 2050 year; months at 19 C or more are counted (fractional,
by linear interpolation is not used: a month counts if its projected average is 19 C or more). Reports the model median and the
middle 80% of models, plus the page's simple trend figure for comparison."""
import csv, json, os, sys, statistics as st, collections
bdir, dfile = sys.argv[1:3]; out = sys.argv[3] if len(sys.argv) > 3 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "proj.json")
D = collections.defaultdict(dict)
for r in csv.DictReader(open(dfile)): D[(r["beach"], r["model"])][int(r["month"])] = float(r["delta_c"])
res = {}
for b in sorted({k[0] for k in D}):
    obs = collections.defaultdict(list)
    for d, v in list(csv.reader(open(os.path.join(bdir, b + ".csv"))))[1:]:
        if v and 2016 <= int(d[:4]) <= 2025: obs[int(d[5:7])].append(float(v))
    base = {m: sum(v) / len(v) for m, v in obs.items()}
    now = sum(base[m] >= 19 for m in range(1, 13))
    per = sorted(sum(base[m] + D[(b, mod)][m] >= 19 for m in range(1, 13)) for mod in {k[1] for k in D if k[0] == b} if len(D[(b, mod)]) == 12)
    n = len(per); lo = per[int(0.1 * (n - 1))]; hi = per[int(round(0.9 * (n - 1)))]
    warm = st.median([st.mean(D[(b, mod)].values()) for mod in {k[1] for k in D if k[0] == b}])
    res[b] = {"now": now, "median": st.median(per), "lo": lo, "hi": hi, "models": n, "warming_c": round(warm, 2)}
    print(f"{b:11s} now {now:2d} months -> 2050 median {st.median(per):4.1f} (middle 80% {lo}-{hi}), {n} models, warming {warm:.2f} C")
json.dump(res, open(out, "w"), indent=1)
