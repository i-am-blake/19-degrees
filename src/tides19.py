"""Tides: do bites cluster at a stage of the tide? A long-standing fishing belief, tested on bites with a known time.
Usage: python3 -I tides19.py <tides_hilo.csv> <CDFW SharkIncidents xlsx> [hawaii_incidents.csv] <out tides.json>
Tide times: NOAA CO-OPS predictions of high and low water (local time, public domain) at the nearest station.
Each bite is placed in the tide cycle: around low water, rising, around high water or falling (each a quarter of the
time from one low to the next). With no link, a quarter of bites fall in each. Chi-square test (3 degrees of freedom)."""
import bisect, csv, datetime as dt, json, math, re, sys, unicodedata
from collections import defaultdict
import openpyxl

args = sys.argv[1:]; TIDE, CA = args[:2]; HI = args[2] if len(args) == 4 else None; OUT = args[-1]
ext = defaultdict(list)
for r in csv.DictReader(open(TIDE)):
    ext[r["station"]].append((dt.datetime.strptime(r["time_local"], "%Y-%m-%d %H:%M"), r["type"]))
for s in ext: ext[s].sort()
times = {s: [t for t, _ in v] for s, v in ext.items()}

def stage(st, when):
    v, ts = ext.get(st), times.get(st)
    if not v: return None
    i = bisect.bisect_right(ts, when)
    if i == 0 or i >= len(v): return None
    (t0, k0), (t1, k1) = v[i - 1], v[i]
    if k0 == k1 or (t1 - t0) > dt.timedelta(hours=10): return None
    f = (when - t0) / (t1 - t0)  # 0 at the last extreme, 1 at the next
    rising = k0 == "L"
    if f < 0.25: return "low" if rising else "high"
    if f >= 0.75: return "high" if rising else "low"
    return "rising" if rising else "falling"

def clock(t):
    if isinstance(t, dt.time): return t
    m = re.search(r"(\d{1,2}):(\d{2})\s*([ap])\.?m", str(t).lower())
    if m:
        h = int(m.group(1)) % 12 + (12 if m.group(3) == "p" else 0); return dt.time(h, int(m.group(2)))
    m = re.search(r"\b(\d{1,2})(\d{2})\b", str(t))
    if m and int(m.group(1)) < 24 and int(m.group(2)) < 60: return dt.time(int(m.group(1)), int(m.group(2)))
    return None

CA_ST = [(32.71, "9410170"), (34.01, "9410840"), (34.40, "9411340"), (36.60, "9413450"), (37.81, "9414290"), (40.77, "9418767")]
bites = []  # (place, station, datetime)
ws = openpyxl.load_workbook(CA, read_only=True, data_only=True)["Attacks_1950_2021"]
rows = list(ws.iter_rows(values_only=True)); ix = {k: i for i, k in enumerate(rows[0])}
for r in rows[1:]:
    d, t, lat = r[ix["Date"]], clock(r[ix["Time"]]), r[ix["Latitude"]]
    if hasattr(d, "year") and t and lat and d.year >= 1980:
        bites.append(("california", min(CA_ST, key=lambda s: abs(s[0] - float(lat)))[1], dt.datetime.combine(d.date(), t)))
if HI:
    norm = lambda s: re.sub(r"[^a-z ,]", "", unicodedata.normalize("NFKD", s.lower()))
    for r in csv.DictReader(open(HI, encoding="utf-8")):
        m = re.match(r"\s*(\d{4})/(\d{1,2})/(\d{1,2})", r.get("Date and Time", "")); t = clock(r.get("Date and Time", "")[10:])
        if not m or not t: continue
        try: d = dt.date(*map(int, m.groups()))
        except ValueError: continue
        loc = norm(r.get("Location", ""))
        if loc.startswith("oahu"): st = "1612480" if any(w in loc for w in ("kaneohe", "kailua", "lanikai", "waimanalo", "kahana", "kualoa", "laie", "hauula", "punaluu")) else "1612340"
        elif loc.startswith(("maui", "molokai", "lanai")): st = "1615680"
        elif loc.startswith("kauai"): st = "1611400"
        elif loc.startswith("hawaii"): st = "1617760" if any(w in loc for w in ("hilo", "puna", "kapoho", "honoli", "hamakua", "keaukaha")) else "1617433"
        else: continue
        bites.append(("hawaii", st, dt.datetime.combine(d, t)))

def chi(counts):
    n = sum(counts); e = n / 4; x2 = sum((c - e) ** 2 / e for c in counts)
    # survival function of chi-square with 3 degrees of freedom
    p = math.erfc(math.sqrt(x2 / 2)) + math.sqrt(2 * x2 / math.pi) * math.exp(-x2 / 2)
    return round(x2, 2), round(min(1.0, p), 3)

out = {}
for g in ("california", "hawaii", "all"):
    st = [stage(s, t) for pl, s, t in bites if g in ("all", pl)]
    st = [x for x in st if x]
    c = [st.count(k) for k in ("low", "rising", "high", "falling")]
    if sum(c) == 0: out[g] = dict(n=0); continue
    x2, p = chi(c)
    out[g] = dict(n=sum(c), low=c[0], rising=c[1], high=c[2], falling=c[3], pct=[round(100 * x / sum(c)) for x in c], chi2=x2, p=p)
json.dump(out, open(OUT, "w"), indent=1)
print("tides", json.dumps(out))
