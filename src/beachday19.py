"""Beach weather and surf on the day of each bite (claims C18 and C19).
Usage: python3 -I beachday19.py <ocean dir> <islands_nc_run.csv> <CDFW SharkIncidents xlsx> [hawaii_incidents.csv] <out beachday.json>
Weather and waves: Open-Meteo historical data (ERA5; CC BY 4.0), files weather_<point>.csv and waves_<point>.csv in the
ocean dir. Each bite day is ranked against the same place within 15 days of the same date in the 5 years either side, so
the season and long-term trends are matched. With no link, a quarter of bites fall in the top quarter of days.
Hot, calm days bring more people to the beach; big surf brings surfers. (Sunshine isn't tested: too many days tie at the
maximum, so it can't rank them.) One-sided binomial tests against a quarter
(hot, big waves: top quarter; calm: bottom quarter of wind)."""
import csv, datetime as dt, json, math, os, re, sys, unicodedata
import openpyxl

args = sys.argv[1:]; OCEAN, ISL, CA = args[:3]; HI = args[3] if len(args) == 5 else None; OUT = args[-1]

def load(kind, pt):
    p = os.path.join(OCEAN, f"{kind}_{pt}.csv")
    if not os.path.exists(p): return {}
    out = {}
    for r in csv.DictReader(open(p)):
        d = dt.date.fromisoformat(r.pop("date"))
        out[d] = {k: float(v) for k, v in r.items() if v not in ("", None)}
    return out

CA_PTS = [(32.625, "california_san_diego"), (34.375, "california_santa_barbara"), (36.625, "california_monterey"),
          (37.625, "california_san_francisco"), (40.875, "california_humboldt")]
bites = []  # (date, point, place, surfing)
ws = openpyxl.load_workbook(CA, read_only=True, data_only=True)["Attacks_1950_2021"]
rows = list(ws.iter_rows(values_only=True)); ix = {k: i for i, k in enumerate(rows[0])}
for r in rows[1:]:
    d, lat = r[ix["Date"]], r[ix["Latitude"]]
    if hasattr(d, "year") and lat:
        bites.append((d.date(), min(CA_PTS, key=lambda p: abs(p[0] - float(lat)))[1], "california", "surf" in str(r[ix["Mode"]]).lower() or "board" in str(r[ix["Mode"]]).lower()))
raw = open(ISL, "rb").read().decode("utf-8", "replace").splitlines()
for r in csv.DictReader(raw, delimiter=";" if raw[0].count(";") > raw[0].count(",") else ","):
    try: d = dt.date.fromisoformat(r["DATE"])
    except ValueError: continue
    nc = r["SITE"].startswith("New")
    bites.append((d, "new_caledonia_noumea" if nc else "reunion_west", "new_caledonia" if nc else "reunion", "surf" in r["ACTIVITY"].lower() or "board" in r["ACTIVITY"].lower()))
if HI:
    norm = lambda t: re.sub(r"[^a-z ,]", "", unicodedata.normalize("NFKD", t.lower()))
    ISLES = [("kauai", "hawaii_kauai"), ("maui", "hawaii_maui"), ("molokai", "hawaii_maui"), ("lanai", "hawaii_maui"),
             ("hawaii", "hawaii_big_island"), ("oahu", "hawaii_oahu_south")]
    NORTH = ("north shore", "haleiwa", "sunset", "waimea", "pipeline", "laie", "kahuku", "mokuleia", "kaena", "makaha", "waianae", "yokohama")
    for r in csv.DictReader(open(HI, encoding="utf-8")):
        m = re.match(r"\s*(\d{4})/(\d{1,2})/(\d{1,2})", r.get("Date and Time", ""))
        if not m: continue
        try: d = dt.date(*map(int, m.groups()))
        except ValueError: continue
        loc = norm(r.get("Location", "")); pt = next((p for name, p in ISLES if name in loc.split(",")[0] or loc.startswith(name)), None)
        if pt == "hawaii_oahu_south" and any(w in loc for w in NORTH): pt = "hawaii_oahu_north"
        if pt: bites.append((d, pt, "hawaii", "surf" in r.get("Activity", "").lower() or "board" in r.get("Activity", "").lower()))

DATA = {}
def series(kind, pt):
    if (kind, pt) not in DATA: DATA[(kind, pt)] = load(kind, pt)
    return DATA[(kind, pt)]

def rank(kind, pt, var, d):
    s = series(kind, pt)
    if d not in s or var not in s[d]: return None
    x = s[d][var]; others = []
    for y in range(d.year - 5, d.year + 6):
        try: c = d.replace(year=y)
        except ValueError: c = d.replace(year=y, day=28)
        for i in range(-15, 16):
            o = c + dt.timedelta(i)
            if o != d and o in s and var in s[o]: others.append(s[o][var])
    if len(others) < 150: return None
    return (sum(v < x for v in others) + 0.5 * sum(v == x for v in others)) / len(others)

def binom_ge(k, n, p=0.25):
    return round(sum(math.comb(n, x) * p ** x * (1 - p) ** (n - x) for x in range(k, n + 1)), 3)

def summary(sel, kind, var, top=True):
    rs = [r for b in sel if (r := rank(kind, b[1], var, b[0])) is not None]
    if not rs: return dict(n=0)
    k = sum((r >= 0.75) if top else (r < 0.25) for r in rs)
    return dict(n=len(rs), k=k, pct=round(100 * k / len(rs)), mean_rank=round(sum(rs) / len(rs), 2), p=binom_ge(k, len(rs)))

TESTS = {"hot": ("weather", "temperature_2m_max", True),
         "calm": ("weather", "wind_speed_10m_max", False), "big_waves": ("waves", "wave_height_max", True)}
out = {}
for name, (kind, var, top) in TESTS.items():
    out[name] = {pl: summary([b for b in bites if b[2] == pl], kind, var, top) for pl in ("california", "reunion", "new_caledonia", "hawaii")}
    out[name]["all"] = summary(bites, kind, var, top)
    if name == "big_waves":
        out[name]["surfers"] = summary([b for b in bites if b[3]], kind, var, top)
        out[name]["not_surfing"] = summary([b for b in bites if not b[3]], kind, var, top)
json.dump(out, open(OUT, "w"), indent=1)
print("beachday", json.dumps({k: v.get("all") for k, v in out.items()}))
