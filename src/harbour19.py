"""Claim C6, shark-side test: are more tagged bull sharks in Sydney Harbour after its water tests dirtier than usual?
Usage: python3 -I harbour19.py <BullShark detections csv.gz> <beachwatch_enterococci.csv[.gz]> <out harbour.json>
Sharks: IMOS Animal Tracking acoustic detections (CC BY 4.0) on receivers inside Sydney Harbour (33.78-33.95°S,
151.05-151.32°E). Water: Harbourwatch enterococci (NSW Government, CC BY) at the 'Sydney Harbour' sites, gut bacteria
that rise when stormwater and sewage overflow wash in after rain.
Unit: the week (Monday to Sunday). Each week's water score is the mean of log10 enterococci over the harbour samples that
week. Sharks: the number of different tagged bull sharks detected in the harbour that week and the next, and the hours
with a detection (all receivers, and west of the Harbour Bridge). Weeks are compared only with other weeks in the same
month of the same year (above vs below that month's middle score), so the season, the year's receivers and the tagged
sharks at liberty are all held fixed. p-values from reshuffling the water scores within each month (two-sided).
Caveat: stormy, noisy water shortens how far receivers can hear a tag, which would lower detections after rain too."""
import csv, datetime as dt, gzip, json, math, random, sys
from collections import defaultdict

DET, BW, OUT = sys.argv[1:4]
op = lambda p: gzip.open(p, "rt") if p.endswith(".gz") else open(p)
monday = lambda d: d - dt.timedelta(days=d.weekday())

rows = []
for r in csv.DictReader(op(DET)):
    try: la, lo = float(r["receiver_deployment_latitude"]), float(r["receiver_deployment_longitude"])
    except ValueError: continue
    if -33.95 < la < -33.78 and 151.05 < lo < 151.32:
        rows.append((monday(dt.date.fromisoformat(r["date_hour_UTC"][:10])), r["animal_id"], lo))
water = defaultdict(list)
for r in csv.DictReader(op(BW)):
    if not r["region"].lower().startswith("sydney harbour"): continue
    try: v = math.log10(max(float(r["enterococci_cfu_100ml"]), 1)); d = dt.date.fromisoformat(r["date"])
    except ValueError: continue
    water[monday(d)].append(v)

def test(weekly):
    strata = defaultdict(list)
    for w, v in water.items():
        strata[(w.year, w.month)].append((sum(v) / len(v), weekly(w) + weekly(w + dt.timedelta(7))))
    strata = {s: v for s, v in strata.items() if len(v) >= 2 and any(n for _, n in v)}
    def diff(st):
        hi = lo = 0.0; nh = nl = 0
        for v in st.values():
            xs = sorted(x for x, _ in v); mid = (xs[(len(xs) - 1) // 2] + xs[len(xs) // 2]) / 2
            for x, n in v:
                if x > mid: hi += n; nh += 1
                elif x < mid: lo += n; nl += 1
        return hi / max(nh, 1), lo / max(nl, 1), nh, nl
    h, l, nh, nl = diff(strata); obs = h - l
    random.seed(19); more = 0; R = 10000
    for _ in range(R):
        sh = {s: list(zip(random.sample([x for x, _ in v], len(v)), [n for _, n in v])) for s, v in strata.items()}
        a, b, _, _ = diff(sh); more += abs(a - b) >= abs(obs) - 1e-12
    return dict(months=len(strata), weeks_dirtier=nh, weeks_cleaner=nl, after_dirtier=round(h, 1), after_cleaner=round(l, 1),
                ratio=round(h / l, 2) if l else None, p=round((more + 1) / (R + 1), 3))

sharks, hours, hours_west = defaultdict(set), defaultdict(int), defaultdict(int)
for w, a, lo in rows:
    sharks[w].add(a); hours[w] += 1; hours_west[w] += lo < 151.19
out = dict(first=min(water).isoformat(), last=max(water).isoformat(), animals=len({a for _, a, _ in rows}),
           sharks=test(lambda w: len(sharks.get(w, ()))), hours=test(lambda w: hours.get(w, 0)), hours_west=test(lambda w: hours_west.get(w, 0)))
json.dump(out, open(OUT, "w"), indent=1)
print("harbour", json.dumps(out))
