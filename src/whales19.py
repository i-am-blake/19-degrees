"""Claim C5: do NSW white shark bites peak during the humpback whale migration?
Usage: python3 -I whales19.py <asid.csv> <obis_humpback_nsw.csv> <out whales.json>
Humpback timing: OBIS records off NSW by month (each dataset's own license). The migration months are the 4 months with
the most records. Who is in the water also changes by month, so white shark bites are compared with bull, tiger and other
whaler shark bites in NSW over the same years (Fisher's exact test, two-sided): if white sharks follow the whales, a larger
share of their bites falls in the migration months."""
import csv, json, math, sys
from collections import Counter

ASID, HB, OUT = sys.argv[1:4]
hm = Counter()
for r in csv.DictReader(open(HB)):
    try: m = int(float(r["month"])) if r["month"] else int(r["eventDate"][5:7])
    except (ValueError, IndexError): continue
    if 1 <= m <= 12: hm[m] += 1
top = sorted(sorted(hm, key=hm.get, reverse=True)[:4])

white, other = [], []
for r in csv.DictReader(open(ASID, encoding="utf-8", errors="replace")):
    try: y, m = int(r["Incident.year"]), int(r["Incident.month"])
    except ValueError: continue
    if r["State"].strip().upper() != "NSW" or y < 1980 or r["Provoked/unprovoked"].strip().lower() != "unprovoked": continue
    sp = r["Shark.common.name"].strip().lower()
    if "white" in sp: white.append(m)
    elif any(w in sp for w in ("bull", "tiger", "whaler")): other.append(m)

def fisher(a, b, c, d):
    n, r1, c1 = a + b + c + d, a + b, a + c
    p = lambda x: math.comb(r1, x) * math.comb(n - r1, c1 - x) / math.comb(n, c1)
    p0 = p(a); lo, hi = max(0, c1 - (n - r1)), min(r1, c1)
    return round(min(1.0, sum(p(x) for x in range(lo, hi + 1) if p(x) <= p0 * (1 + 1e-9))), 3)

wk, ok = sum(m in top for m in white), sum(m in top for m in other)
out = dict(humpback_records=sum(hm.values()), by_month=[hm.get(m, 0) for m in range(1, 13)], migration_months=top,
           white_n=len(white), white_in=wk, white_pct=round(100 * wk / len(white)) if white else None,
           other_n=len(other), other_in=ok, other_pct=round(100 * ok / len(other)) if other else None,
           p=fisher(wk, len(white) - wk, ok, len(other) - ok),
           white_by_month=[white.count(m) for m in range(1, 13)], other_by_month=[other.count(m) for m in range(1, 13)])
json.dump(out, open(OUT, "w"), indent=1)
print("whales", json.dumps(out))
