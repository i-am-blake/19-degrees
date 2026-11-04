"""Two checks from fields the bite database already records for some bites.
Usage: python3 -I fieldnotes19.py <asid.csv> <out fieldnotes.json>
- Water temperature measured or reported at the bite (Water.temperature.°C): an independent check of the 19°C line,
  which the page otherwise tests with monthly open-sea averages.
- Time of day (Time.of.incident, 24-hour clock): the share of bites at dawn (05:00-07:59), dusk (17:00-19:59) or at night
  (20:00-04:59), by species. Bull sharks are compared with white and tiger sharks. There's no count of people in the water
  by hour, so this compares species, not chance; it backs claim C21 (drumlines at dawn and dusk) only indirectly."""
import csv, json, math, re, sys

SRC, OUT = sys.argv[1:3]
rows = list(csv.DictReader(open(SRC, encoding="utf-8")))

def species(x):
    n = x["Shark.common.name"].lower()
    return "bull" if "bull" in n else "white" if "white" in n else "tiger" if "tiger" in n else None

def hour(t):
    t = t.strip()
    return int(t.zfill(4)[:2]) if re.fullmatch(r"\d{3,4}", t) and int(t.zfill(4)[:2]) < 24 else None

def band(h):
    return "dawn" if 5 <= h < 8 else "dusk" if 17 <= h < 20 else "night" if (h >= 20 or h < 5) else "day"

def fisher(a, b, c, d):
    n, r1, c1 = a + b + c + d, a + b, a + c
    p = lambda x: math.comb(r1, x) * math.comb(n - r1, c1 - x) / math.comb(n, c1)
    obs = p(a); lo, hi = max(0, c1 - (n - r1)), min(r1, c1)
    return round(min(1.0, sum(p(x) for x in range(lo, hi + 1) if p(x) <= obs * (1 + 1e-9))), 3)

out = {"water": {}, "time": {}}
for s in ("bull", "tiger", "white"):
    w = [float(x["Water.temperature.°C"]) for x in rows if species(x) == s and re.fullmatch(r"\d+(\.\d+)?", x["Water.temperature.°C"].strip())]
    out["water"][s] = dict(n=len(w), min=min(w) if w else None, below19=sum(v < 19 for v in w))
    hs = [h for h in (hour(x["Time.of.incident"]) for x in rows if species(x) == s) if h is not None]
    b = {k: sum(band(h) == k for h in hs) for k in ("dawn", "day", "dusk", "night")}
    low = b["dawn"] + b["dusk"] + b["night"]
    out["time"][s] = dict(n=len(hs), **b, low=low, low_pct=round(100 * low / len(hs)) if hs else None)
bt, ot = out["time"]["bull"], [out["time"][k] for k in ("white", "tiger")]
on, ol = sum(x["n"] for x in ot), sum(x["low"] for x in ot)
out["time"]["others"] = dict(n=on, low=ol, low_pct=round(100 * ol / on))
out["time"]["p"] = fisher(bt["low"], bt["n"] - bt["low"], ol, on - ol)
onight = sum(x["night"] for x in ot)
out["time"]["others"].update(night=onight, night_pct=round(100 * onight / on))
out["time"]["bull"]["night_pct"] = round(100 * bt["night"] / bt["n"])
out["time"]["p_night"] = fisher(bt["night"], bt["n"] - bt["night"], onight, on - onight)
json.dump(out, open(OUT, "w"), indent=1)
print("fieldnotes", json.dumps(out))
