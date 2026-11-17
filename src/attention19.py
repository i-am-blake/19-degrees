"""Attention vs reality: does public interest in shark bites follow the bites, or the calendar?
Usage: python3 -I attention19.py <asid.csv> <hawaii.json> [attention.json]
Monthly English Wikipedia views of the "Shark attack" article (Wikimedia pageviews, human readers only, CC0) since July
2015, the first month the service has, compared with unprovoked bites in Australia over the same months (Australian
Shark-Incident Database) and with Hawaii's bites by calendar month (DLNR list). Each series is shown by calendar month as
a percent of its own monthly average, so they share one scale. Also the correlation of views with Australian bites month
by month. A context panel on the Safety page, not a claim. If Wikimedia can't be reached the page keeps its last numbers."""
import csv, json, math, os, sys, datetime, urllib.request
here = os.path.dirname(os.path.abspath(__file__))
asid, hawaii = sys.argv[1:3]; out = sys.argv[3] if len(sys.argv) > 3 else os.path.join(here, "attention.json")

today = datetime.date.today(); last = (today.replace(day=1) - datetime.timedelta(days=1)).replace(day=1)  # last full month
url = ("https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/user/Shark_attack/monthly/"
       f"2015070100/{last:%Y%m}0100")
req = urllib.request.Request(url, headers={"User-Agent": "19-degrees/1.0 (https://19-degrees.org; open research site)"})
views = {i["timestamp"][:6]: i["views"] for i in json.load(urllib.request.urlopen(req, timeout=60))["items"]}
if len(views) < 100: sys.exit(f"only {len(views)} months of views; keeping the last numbers")

bites = {}
for r in csv.DictReader(open(asid, encoding="utf-8")):
    if r.get("Provoked/unprovoked", "").strip() != "unprovoked": continue
    try: ym = f"{int(float(r['Incident.year'])):04d}{int(float(r['Incident.month'])):02d}"
    except (ValueError, KeyError): continue
    bites[ym] = bites.get(ym, 0) + 1
# compare only months the database covers (it lags a few months behind)
lastdb = max(bites); months = sorted(m for m in views if m <= lastdb)

def by_cal(series, ms):
    tot = [0] * 12; cnt = [0] * 12
    for m in ms: tot[int(m[4:]) - 1] += series.get(m, 0); cnt[int(m[4:]) - 1] += 1
    return [t / c if c else 0 for t, c in zip(tot, cnt)]
def index(xs):
    avg = sum(xs) / len(xs); return [round(100 * x / avg) for x in xs]
def corr(x, y):
    mx, my = sum(x) / len(x), sum(y) / len(y)
    sx = math.sqrt(sum((a - mx) ** 2 for a in x)); sy = math.sqrt(sum((b - my) ** 2 for b in y))
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / (sx * sy)

v_cal = by_cal(views, months); au_cal = by_cal(bites, months)
hi = json.load(open(hawaii))
r = corr([views[m] for m in months], [bites.get(m, 0) for m in months])
peak = max(range(12), key=lambda i: v_cal[i]); low = min(range(12), key=lambda i: v_cal[i])
d = dict(
    first=months[0], last=months[-1], n_months=len(months),
    views_month=[round(x) for x in v_cal], views_idx=index(v_cal),
    au_idx=index(au_cal), au_n=sum(bites.get(m, 0) for m in months),
    hi_idx=index(hi["by_month"]), hi_n=hi["n"], hi_first=hi["first"], hi_last=hi["last"],
    peak=peak + 1, low=low + 1, ratio=round(v_cal[peak] / v_cal[low], 1), r_au=round(r, 2),
    au_peak=max(range(12), key=lambda i: au_cal[i]) + 1, hi_peak=max(range(12), key=lambda i: hi["by_month"][i]) + 1)
json.dump(d, open(out, "w"), indent=1)
print("attention", {k: v for k, v in d.items() if not isinstance(v, list)})
