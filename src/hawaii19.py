"""Hawaii: what the state's incident list says about water clarity (claim C6) and species.
Usage: python3 -I hawaii19.py <hawaii_incidents.csv> <out hawaii.json>
The incident facts come from Hawaii DLNR (date and time, place, activity, water clarity and depth, shark). There are no
clarity records for days without a bite, so, as for Réunion and New Caledonia, this compares species, not chance:
the share of tiger shark bites in turbid or muddy water against bites by other identified sharks. Fisher's exact test, two-sided."""
import csv, json, math, re, sys
from collections import Counter

SRC, OUT = sys.argv[1:3]
rows = list(csv.DictReader(open(SRC, encoding="utf-8")))

def year(r):
    m = re.match(r"\s*(\d{4})/", r["Date and Time"]); return int(m.group(1)) if m else None
def month(r):
    m = re.match(r"\s*\d{4}/(\d{1,2})/", r["Date and Time"]); return int(m.group(1)) if m else None
def species(r):
    s = r["Shark"].lower()
    if "tiger" in s: return "tiger"
    if not s.strip() or "unknown" in s or "unidentified" in s: return "unknown"
    return "other"
def murky(r):
    c = r["Water Clarity"].strip().lower()
    return True if c in ("turbid", "muddy", "murky") else False if c == "clear" else None

def fisher(a, b, c, d):  # 2x2 [[a, b], [c, d]], two-sided
    n, r1, c1 = a + b + c + d, a + b, a + c
    p = lambda x: math.comb(r1, x) * math.comb(n - r1, c1 - x) / math.comb(n, c1)
    p0 = p(a); lo, hi = max(0, c1 - (n - r1)), min(r1, c1)
    return round(min(1.0, sum(p(x) for x in range(lo, hi + 1) if p(x) <= p0 * (1 + 1e-9))), 2)

def clar(sp):
    k = [murky(r) for r in rows if species(r) == sp and murky(r) is not None]
    return sum(k), len(k)

tm, tn = clar("tiger"); om, on = clar("other")
yrs = [y for r in rows if (y := year(r))]
out = dict(n=len(rows), first=min(yrs), last=max(yrs), tiger=sum(species(r) == "tiger" for r in rows),
           tiger_murky=tm, tiger_clarity_n=tn, tiger_murky_pct=round(100 * tm / tn) if tn else None,
           other_murky=om, other_clarity_n=on, other_murky_pct=round(100 * om / on) if on else None,
           p_murky=fisher(tm, tn - tm, om, on - om),
           by_month=[sum(month(r) == m for r in rows) for m in range(1, 13)],
           activity=Counter(r["Activity"].strip().lower() for r in rows).most_common(5))
json.dump(out, open(OUT, "w"), indent=1)
print("hawaii", json.dumps(out))
