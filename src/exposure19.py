"""Claim C18: are more bites about more people in the water? Weekends and public holidays, when beaches are busiest.
Usage: python3 -I exposure19.py <islands_nc_run.csv> <CDFW SharkIncidents xlsx> [hawaii_incidents.csv] <out exposure.json>
Uses the coasts that record the day of each bite: California (CDFW), Réunion and New Caledonia (University of Reunion
Island), Hawaii (DLNR). Sharks don't keep calendars, so if bites follow people, weekends and public holidays should get more
than their share of days. The expected share is the share of such days in the same years at the same place (public holidays
from the open-source 'holidays' package: US federal plus California or Hawaii; France plus Réunion or New Caledonia).
Reports bites per busy day against bites per working day, with an exact two-sided binomial test.
Holidays fall partly in summer, so the holiday figure carries a little season; the weekend-only figure doesn't."""
import csv, datetime as dt, json, math, re, sys
import holidays, openpyxl

args = sys.argv[1:]; ISL, CA = args[:2]; HI = args[2] if len(args) == 4 else None; OUT = args[-1]
bites = {"california": [], "reunion": [], "new_caledonia": [], "hawaii": []}
ws = openpyxl.load_workbook(CA, read_only=True, data_only=True)["Attacks_1950_2021"]
rows = list(ws.iter_rows(values_only=True)); ix = {k: i for i, k in enumerate(rows[0])}
for r in rows[1:]:
    if hasattr(r[ix["Date"]], "year"): bites["california"].append(r[ix["Date"]].date())
raw = open(ISL, "rb").read().decode("utf-8", "replace").splitlines()
for r in csv.DictReader(raw, delimiter=";" if raw[0].count(";") > raw[0].count(",") else ","):
    try: d = dt.date.fromisoformat(r["DATE"])
    except ValueError: continue
    bites["new_caledonia" if r["SITE"].startswith("New") else "reunion"].append(d)
if HI:
    for r in csv.DictReader(open(HI, encoding="utf-8")):
        m = re.match(r"\s*(\d{4})/(\d{1,2})/(\d{1,2})", r.get("Date and Time", ""))
        if m:
            try: bites["hawaii"].append(dt.date(*map(int, m.groups())))
            except ValueError: pass
CAL = {"california": lambda ys: holidays.US(subdiv="CA", years=ys), "hawaii": lambda ys: holidays.US(subdiv="HI", years=ys),
       "reunion": lambda ys: holidays.France(subdiv="RE", years=ys), "new_caledonia": lambda ys: holidays.France(subdiv="NC", years=ys)}

def binom_two(k, n, p):
    pk = math.comb(n, k) * p ** k * (1 - p) ** (n - k)
    return round(min(1.0, sum(q for x in range(n + 1) if (q := math.comb(n, x) * p ** x * (1 - p) ** (n - x)) <= pk * (1 + 1e-9))), 3)

def test(groups, busy_kind):
    k = n = 0; expd = 0.0
    for place, ds in groups:
        if not ds: continue
        ys = range(min(ds).year, max(ds).year + 1); hol = CAL[place](list(ys))
        busy = (lambda d: d.weekday() >= 5) if busy_kind == "weekend" else (lambda d: d.weekday() >= 5 or d in hol)
        days = [dt.date(ys[0], 1, 1) + dt.timedelta(i) for i in range((dt.date(ys[-1], 12, 31) - dt.date(ys[0], 1, 1)).days + 1)]
        share = sum(map(busy, days)) / len(days)
        k += sum(map(busy, ds)); n += len(ds); expd += share * len(ds)
    p = expd / n
    ratio = (k / p) / ((n - k) / (1 - p))  # bites per busy day over bites per working day
    return dict(n=n, busy=k, pct=round(100 * k / n), expected_pct=round(100 * p), ratio=round(ratio, 2), p=binom_two(k, n, p))

out = {}
for kind in ("weekend", "weekend_or_holiday"):
    out[kind] = {pl: test([(pl, bites[pl])], kind) for pl in bites if bites[pl]}
    out[kind]["all"] = test([(pl, bites[pl]) for pl in bites], kind)
json.dump(out, open(OUT, "w"), indent=1)
print("exposure", json.dumps(out))
