"""Claim C25, measured on Australian sharks: what water were tagged bull sharks in, and does it differ with their size?
Usage: python3 -I tagtemp19.py <imos_dir> <out tagtemp.json>
Reads BullShark_Carcharhinusleucas.csv.gz from the imos-data branch (IMOS Animal Tracking, acoustic detections QC summary,
CC BY 4.0). Some tags carry a temperature sensor; a reading is the raw value times the tag's slope plus its intercept.
Readings with no calibration, or raw values of 0 or 255 (the sensor's limits), are left out.
- A shark-day is one tagged shark on one date at one installation; its temperature is the mean of that day's readings.
- Sydney Harbour and the Clarence River are the two NSW sites with enough temperature-tag days to compare.
- Size split, Clarence River, all tags (not only temperature tags): sharks under 150 cm and sharks of 200 cm or more at
  tagging, and how many were detected there in winter (June to August). Length is recorded once, at tagging."""
import csv, gzip, json, os, re, sys, collections, statistics
SRC, OUT = sys.argv[1:3]
WINTER = ("06", "07", "08")
def length(m):
    r = re.search(r"TOTAL LENGTH = ([\d.]+) cm", m or "") or re.search(r"LENGTH = ([\d.]+) cm", m or "")
    return float(r.group(1)) if r else None

temp = collections.defaultdict(list); meas = {}; days = collections.defaultdict(set); nocal = used = 0
for x in csv.DictReader(gzip.open(os.path.join(SRC, "BullShark_Carcharhinusleucas.csv.gz"), "rt")):
    a, d, site = x["animal_id"], x["date_hour_UTC"][:10], x["installation_name"]
    meas[a] = x["measurement"]; days[(site, a)].add(d)
    if x["transmitter_sensor_type"] != "TEMPERATURE": continue
    try: raw, sl, ic = float(x["transmitter_sensor_mean_value"]), float(x["transmitter_sensor_slope"]), float(x["transmitter_sensor_intercept"])
    except ValueError: nocal += 1; continue
    if raw <= 0 or raw >= 255: nocal += 1; continue
    v = raw * sl + ic
    if not 0 < v < 40: nocal += 1; continue
    used += 1; temp[(site, a, d)].append(v)

def site_stats(site):
    sd = {(a, d): statistics.mean(v) for (s, a, d), v in temp.items() if s == site}
    animals = {a for a, _ in sd}; L = [length(meas[a]) for a in animals if length(meas[a])]
    w = [t for (a, d), t in sd.items() if d[5:7] in WINTER]
    wa = collections.Counter(a for (a, d) in sd if d[5:7] in WINTER)
    series = collections.Counter(tuple(sorted((d, round(t, 2)) for (b, d), t in sd.items() if b == a)) for a in animals)
    return dict(sharks=len(animals), shark_days=len(sd), below19=sum(t < 19 for t in sd.values()), coldest_day=round(min(sd.values()), 1),
                median_length_cm=round(statistics.median(L)) if L else None, with_length=len(L),
                winter_days=len(w), winter_below19=sum(t < 19 for t in w), winter_median=round(statistics.median(w), 1) if w else None,
                sharks_in_winter=len(wa), sharks_80_winter_days=sum(n >= 80 for n in wa.values()),
                identical_records=sum(n for n in series.values() if n > 1),
                y0=int(min(d[:4] for _, d in sd)), y1=int(max(d[:4] for _, d in sd)))

def size_split(site):
    out = {}
    for name, ok in (("small", lambda l: l < 150), ("large", lambda l: l >= 200)):
        g = [(a, ds) for (s, a), ds in days.items() if s == site and length(meas[a]) is not None and ok(length(meas[a]))]
        wd = [sum(d[5:7] in WINTER for d in ds) for _, ds in g]
        out[name] = dict(sharks=len(g), with_winter_day=sum(n > 0 for n in wd), with_20_winter_days=sum(n >= 20 for n in wd),
                         days=sum(len(ds) for _, ds in g), winter_days=sum(wd))
    return out

allsd = {(a, d) for (s, a, d) in temp}
res = dict(sharks=len({a for a, _ in allsd}), shark_days=len(temp), readings_used=used, readings_left_out=nocal,
           left_out_pct=round(100 * nocal / (used + nocal)), y0=int(min(d[:4] for _, d in allsd)), y1=int(max(d[:4] for _, d in allsd)),
           sydney=site_stats("Sydney Harbour"), clarence=site_stats("Clarence River"), clarence_size=size_split("Clarence River"))
json.dump(res, open(OUT, "w"), indent=1)
print("tagtemp", json.dumps(res))
