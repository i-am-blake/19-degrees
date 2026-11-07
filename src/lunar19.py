"""Claim C24: do shark bites cluster around the full or new moon?
Usage: python3 -I lunar19.py <islands_nc_run.csv> <CDFW SharkIncidents xlsx> [hawaii_incidents.csv] <out lunar.json>
Needs the day of each bite, so it uses the regions that record it: California (CDFW, white sharks, CC BY) and Réunion and
New Caledonia (University of Reunion Island, CC BY 4.0), and Hawaii (DLNR) when given. The Australian database gives the month only.
Moon phase is calculated from the date (mean synodic month from the new moon of 6 January 2000, 18:14 UTC); dates are
local, so the phase is right to within about a day. "Near full or new" is within 3.7 days of either, half of every
lunar month, so with no moon effect about half of all bites would fall there. Two-sided binomial test against one half."""
import csv, datetime as dt, json, math, sys
import openpyxl

ISL, CA = sys.argv[1:3]; HI = sys.argv[3] if len(sys.argv) == 5 else None; OUT = sys.argv[-1]
SYN, NEW0 = 29.530588853, dt.datetime(2000, 1, 6, 18, 14)

def age(d):  # days since the last new moon
    return ((dt.datetime(d.year, d.month, d.day, 12) - NEW0).total_seconds() / 86400) % SYN

def near(d):
    a = age(d); return min(a, SYN - a) <= SYN / 8 or abs(a - SYN / 2) <= SYN / 8

def binom(k, n):
    p = lambda x: math.comb(n, x) / 2 ** n
    return round(min(1.0, sum(p(x) for x in range(n + 1) if p(x) <= p(k) * (1 + 1e-9))), 3)

def summary(dates):
    k = sum(near(d) for d in dates); n = len(dates)
    full = sum(abs(age(d) - SYN / 2) <= SYN / 8 for d in dates)
    return dict(n=n, near=k, near_pct=round(100 * k / n) if n else None, full=full, new=k - full, p=binom(k, n) if n else None)

raw = open(ISL, "rb").read().decode("utf-8", "replace").splitlines()
isl = list(csv.DictReader(raw, delimiter=";" if raw[0].count(";") > raw[0].count(",") else ","))
def d_isl(r):
    try: return dt.date.fromisoformat(r["DATE"])
    except ValueError: return None
ws = openpyxl.load_workbook(CA, read_only=True, data_only=True)["Attacks_1950_2021"]
rows = list(ws.iter_rows(values_only=True)); ix = {k: i for i, k in enumerate(rows[0])}
ca = [r[ix["Date"]].date() for r in rows[1:] if hasattr(r[ix["Date"]], "year") and r[ix["Species"]] and str(r[ix["Species"]]).strip().lower() == "white"]
groups = {"california_white": ca,
          "islands_bull": [d for r in isl if r["SHARKTYPE"] == "Bull" and (d := d_isl(r))],
          "islands_tiger": [d for r in isl if r["SHARKTYPE"] == "Tiger" and (d := d_isl(r))],
          "islands_all": [d for r in isl if (d := d_isl(r))]}
hi = []
if HI:
    import re
    for r in csv.DictReader(open(HI, encoding="utf-8")):
        m = re.match(r"\s*(\d{4})/(\d{1,2})/(\d{1,2})", r.get("Date and Time", ""))
        if m:
            try: hi.append((dt.date(*map(int, m.groups())), "tiger" in r.get("Shark", "").lower()))
            except ValueError: pass
groups["hawaii_all"] = [d for d, _ in hi]; groups["hawaii_tiger"] = [d for d, t in hi if t]
out = {k: summary(v) for k, v in groups.items()}
out["all"] = summary(groups["california_white"] + groups["islands_all"])
json.dump(out, open(OUT, "w"), indent=1)
print("lunar", json.dumps(out))
