"""Does a bull shark's size decide whether it stays in NSW through winter? (bears on claims C25, C16 and C38)
Usage: python3 -I size19.py <imos_dir> <out size.json>
Data: BullShark_Carcharhinusleucas.csv.gz from the imos-data branch (IMOS Animal Tracking, CC BY 4.0).
Written down before the numbers were run:
- Scope: receivers in NSW (south of 28.2°S); tagged bull sharks with a length at tagging. A shark-day is one shark on one date.
- Aging: length is recorded once, at tagging, so each shark is aged forward to the date of each detection with a published
  growth curve for Australian bull sharks: L = Linf - (Linf - L at tagging) * exp(-k * years since tagging), Linf 311.9 cm,
  k 0.158 a year (Tillett et al. 2011, Northern Territory). Sharks already above Linf are left at their tagged length.
- Classes by estimated length on the day: small under 150 cm, mid 150 to 200 cm, large 200 cm or more (about maturity).
- Test 1, by shark: of sharks tagged small and sharks tagged large, how many were ever detected in NSW in winter
  (June to August)? Fisher's exact test, two-sided. Predicted: more of the small sharks.
- Test 2, by day: the share of each class's shark-days that fall in winter, using estimated length on the day.
- Test 3, aging out: for sharks tagged small and detected in two or more winters, winter days in each winter after tagging.
- Checks: the same with a second growth curve (southern Gulf of Mexico, Linf 256.4 cm, k 0.1397, Cruz-Martinez et al. 2005);
  with no growth curve but counting a shark only for its first two years after tagging; and leaving out the Clarence River,
  to see whether one river carries the result."""
import csv, gzip, json, math, os, re, sys, collections, datetime as dt
SRC, OUT = sys.argv[1:3]
WIN = (6, 7, 8)
def length(m):
    r = re.search(r"TOTAL LENGTH = ([\d.]+) cm", m or "") or re.search(r"LENGTH = ([\d.]+) cm", m or "")
    return float(r.group(1)) if r else None
def cls(l): return "small" if l < 150 else "mid" if l < 200 else "large"
def fisher(a, b, c, d):
    """Two-sided Fisher's exact p for the table [[a, b], [c, d]]."""
    n = a + b + c + d; r1 = a + b; c1 = a + c
    f = lambda x: math.comb(c1, x) * math.comb(n - c1, r1 - x) / math.comb(n, r1)
    p0 = f(a); return min(1.0, sum(f(x) for x in range(max(0, r1 - (n - c1)), min(r1, c1) + 1) if f(x) <= p0 * (1 + 1e-9)))

S = {}   # animal -> dict(L0, tag date, days {date: installation})
nolen = set()
for x in csv.DictReader(gzip.open(os.path.join(SRC, "BullShark_Carcharhinusleucas.csv.gz"), "rt")):
    try: la = float(x["receiver_deployment_latitude"])
    except ValueError: continue
    if la > -28.2 or float(x["receiver_deployment_longitude"]) < 140: continue
    L = length(x["measurement"])
    if L is None: nolen.add(x["animal_id"]); continue
    try: tag = dt.date.fromisoformat(x["transmitter_deployment_datetime_UTC"][:10])
    except ValueError: continue
    s = S.setdefault(x["animal_id"], dict(L0=L, tag=tag, days={}))
    s["days"][dt.date.fromisoformat(x["date_hour_UTC"][:10])] = x["installation_name"]

def run(linf=311.9, k=0.158, window=None, drop=None):
    def est(s, d):
        yrs = max(0.0, (d - s["tag"]).days / 365.25)
        return s["L0"] if (linf is None or s["L0"] >= linf) else linf - (linf - s["L0"]) * math.exp(-k * yrs)
    sharks = {}
    for a, s in S.items():
        ds = {d: i for d, i in s["days"].items() if (drop is None or i != drop) and (window is None or (d - s["tag"]).days <= window * 365.25)}
        if ds: sharks[a] = (s, ds)
    by = {c: dict(sharks=0, winter_sharks=0) for c in ("small", "mid", "large")}
    for a, (s, ds) in sharks.items():
        c = cls(s["L0"]); by[c]["sharks"] += 1; by[c]["winter_sharks"] += any(d.month in WIN for d in ds)
    day = {c: dict(days=0, winter_days=0) for c in ("small", "mid", "large")}
    for a, (s, ds) in sharks.items():
        for d in ds:
            c = cls(est(s, d)); day[c]["days"] += 1; day[c]["winter_days"] += d.month in WIN
    for c in day: day[c]["winter_pct"] = round(100 * day[c]["winter_days"] / day[c]["days"], 1) if day[c]["days"] else None
    sm, lg = by["small"], by["large"]
    return dict(by_shark=by, by_day=day, p=float(f'{fisher(sm["winter_sharks"], sm["sharks"] - sm["winter_sharks"], lg["winter_sharks"], lg["sharks"] - lg["winter_sharks"]):.2g}'))

main = run()
# Test 3: sharks tagged small, winter by winter
aging = []
for a, s in S.items():
    if s["L0"] >= 150: continue
    w = collections.Counter(d.year for d in s["days"] if d.month in WIN)
    if len(w) < 2: continue
    rows = []
    for y in sorted(w):
        mid = dt.date(y, 7, 15); yrs = (mid - s["tag"]).days / 365.25
        rows.append(dict(year=y, winter_days=w[y], est_cm=round(311.9 - (311.9 - s["L0"]) * math.exp(-0.158 * yrs))))
    last = max(s["days"]); aging.append(dict(tagged_cm=s["L0"], winters=rows, last_seen=str(last), est_cm_last=round(311.9 - (311.9 - s["L0"]) * math.exp(-0.158 * (last - s["tag"]).days / 365.25))))
sites = collections.defaultdict(lambda: collections.Counter())
for a, s in S.items():
    for i in set(s["days"].values()): sites[i][cls(s["L0"])] += 1
res = dict(sharks_with_length=len(S), sharks_without_length=len(nolen - set(S)), main=main,
           checks=dict(gulf_curve=run(256.4, 0.1397), first_two_years_no_curve=run(None, None, window=2), without_clarence=run(drop="Clarence River")),
           aging=sorted(aging, key=lambda r: r["tagged_cm"]),
           sites={i: dict(c) for i, c in sorted(sites.items(), key=lambda x: -sum(x[1].values()))[:10]})
json.dump(res, open(OUT, "w"), indent=1)
print(json.dumps(res, indent=1))
