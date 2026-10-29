"""Build data.json for Sharks in Perspective.

Usage: python3 -I build.py <asid.csv> <sst_dir> <extra_incidents.json> <out data.json>

Inputs
  asid.csv               Australian Shark-Incident Database (Zenodo), converted to CSV
  sst_dir                NOAA OISST v2.1 point series per region (from fetch_sst.py)
  extra_incidents.json   incidents newer than the database, from public lists/news (unconfirmed)
"""
import csv, json, os, sys, statistics as st, collections, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from regions import REGIONS, region_of

ASID, SST_DIR, EXTRA, OUT = sys.argv[1:5]
STATES = ["NSW", "QLD", "WA", "VIC", "SA", "TAS", "NT"]
STATE_NAMES = {"NSW": "New South Wales", "QLD": "Queensland", "WA": "Western Australia", "VIC": "Victoria",
               "SA": "South Australia", "TAS": "Tasmania", "NT": "Northern Territory"}

# Coastal drowning, 10-year average per year to 2024/25, derived from SLSA National Coastal Safety Report 2025:
# 2024/25 count / (1 + stated % difference from the 10-year average).
DROWN_2425 = {"NSW": (52, 0.13), "QLD": (31, 0.15), "WA": (27, 0.37), "VIC": (20, 0.05),
              "SA": (18, 1.25), "TAS": (5, -0.17), "NT": (1, -0.50)}

# Approximate Australian population (millions) at mid-decade, ABS historical estimates.
POP_MID = {1900: 4.0, 1910: 4.9, 1920: 5.9, 1930: 6.7, 1940: 7.4, 1950: 9.2, 1960: 11.4, 1970: 13.9,
           1980: 15.8, 1990: 18.0, 2000: 20.4, 2010: 23.8, 2020: 26.6}

SPECIES = ["white", "tiger", "bull", "whaler", "wobbegong"]
def species_key(sp):
    sp = (sp or "").strip().lower()
    if sp == "white shark": return "white"
    if sp == "tiger shark": return "tiger"
    if sp == "bull shark": return "bull"
    if sp in ("whaler shark", "bronze whaler shark", "dusky shark"): return "whaler"
    if sp == "wobbegong": return "wobbegong"
    if sp in ("", "unknown", "unidentified"): return "unknown"
    return "other"

def activity_group(a):
    a = (a or "").strip().lower()
    if any(k in a for k in ["board", "surf", "paddle", "wind"]): return "Surfing or on a board"
    if any(k in a for k in ["swim", "wading", "standing", "float"]): return "Swimming or wading"
    if any(k in a for k in ["dive", "diving", "scuba", "snorkel", "spear"]): return "Diving, snorkelling or spearfishing"
    if any(k in a for k in ["fish", "boat", "kayak", "jet", "hull"]): return "Fishing or boating"
    return "Not recorded"

def load():
    rows = []
    for x in csv.DictReader(open(ASID, encoding="utf-8")):
        try:
            y = int(float(x["Incident.year"]))
        except ValueError:
            continue
        m = x["Incident.month"].strip()
        m = int(float(m)) if m else None
        inj = x["Victim.injury"].strip().lower().replace("injury", "injured")
        try:
            lat, lon = float(x["Latitude"]), float(x["Longitude"])
        except ValueError:
            lat = lon = None
        st_ = x["State"].strip().upper()
        sp = (x["Shark.common.name"] or "").strip().lower()
        wt = x.get("Water.temperature.°C", "").strip()
        rows.append(dict(year=y, month=m, injury=inj, fatal=inj == "fatal", state=st_,
                         unprovoked=x["Provoked/unprovoked"].strip().lower() == "unprovoked",
                         place=x["Location"].strip(), lat=lat, lon=lon, species=sp,
                         activity=activity_group(x["Victim.activity"]),
                         region=region_of(st_, lat, lon) if lat is not None else None,
                         water_temp=float(wt) if wt.replace(".", "", 1).isdigit() else None,
                         source="ASID"))
    return rows

def in_window(r, start, end):  # (year, month) inclusive; unknown month counts as mid-year
    ym = (r["year"], r["month"] or 6)
    return start <= ym <= end

def title(place):
    return ", ".join(p.strip().title().replace("'S", "'s") for p in place.split(",")[::-1] if p.strip())

def main():
    rows = load()
    extra = json.load(open(EXTRA)) if os.path.exists(EXTRA) else []
    last = max((r["year"], r["month"] or 1) for r in rows)
    for e in extra:  # only keep extras newer than the database
        if (e["year"], e["month"]) > last:
            rows.append(dict(e, unprovoked=e.get("unprovoked", True), lat=e.get("lat"), lon=e.get("lon"),
                             region=region_of(e["state"], e["lat"], e["lon"]) if e.get("lat") else None,
                             water_temp=None, injury="fatal" if e["fatal"] else "injured", source="unconfirmed"))
    W0, W1 = (2015, 7), (2025, 6)

    # ---- state comparison, July 2015 – June 2025
    states = []
    for s in STATES:
        n, pct = DROWN_2425[s]
        dpy = n / (1 + pct)
        win = [r for r in rows if r["state"] == s and in_window(r, W0, W1)]
        states.append(dict(k=s, name=STATE_NAMES[s], dpy=round(dpy, 2), d10=round(dpy * 10),
                           fatal=sum(r["fatal"] for r in win), nonfatal=sum(not r["fatal"] for r in win),
                           unsure=s == "SA"))
    fatal_list = sorted([r for r in rows if r["fatal"] and in_window(r, W0, W1)], key=lambda r: (r["year"], r["month"] or 0))
    deaths = [dict(y=r["year"], m=r["month"], state=r["state"], place=title(r["place"]), activity=r["activity"],
                   species=r["species"] or "not identified") for r in fatal_list]

    # ---- regional ranking, 2006–2025 unprovoked
    reg = {name: dict(name=name, coast=coast, state=s, unprov=0, fatal=0, first=0, second=0, sp=collections.Counter())
           for name, coast, s, _, _ in REGIONS}
    for r in rows:
        if r["region"] and r["unprovoked"] and 2006 <= r["year"] <= 2025:
            g = reg[r["region"]]
            g["unprov"] += 1; g["fatal"] += r["fatal"]
            g["first" if r["year"] <= 2015 else "second"] += 1
            if r["species"] and r["species"] not in ("unknown", "unidentified"):
                g["sp"][r["species"]] += 1
    ranking = []
    for g in reg.values():
        sp = g.pop("sp").most_common(1)
        g["species"] = sp[0][0] if sp else "not identified"
        ranking.append(g)

    # ---- decades and months
    decades = []
    for d in range(1900, 2030, 10):
        sel = [r for r in rows if d <= r["year"] < d + 10 and r["source"] == "ASID"]
        yrs = 10 if d + 10 <= last[0] else (last[0] - d) + (last[1] / 12)
        decades.append(dict(d=d, all=len(sel), fatal=sum(r["fatal"] for r in sel), years=round(yrs, 1),
                            per_m_yr=round(len(sel) / yrs / POP_MID[d], 2), partial=yrs < 10))
    months = [0] * 12
    for r in rows:
        if 2000 <= r["year"] <= 2025 and r["month"]:
            months[r["month"] - 1] += 1

    activity = collections.Counter(r["activity"] for r in fatal_list)

    # ---- climate: SST per region
    climate = []
    sst_last = ""
    for name, coast, s, lat, lon in REGIONS:
        fn = os.path.join(SST_DIR, name.replace(" ", "_").replace("&", "and") + ".csv")
        if not os.path.exists(fn):
            continue
        # HadISST monthly: date (YYYY-MM), sst
        by_year = collections.defaultdict(list)
        for row in list(csv.reader(open(fn)))[1:]:
            by_year[int(row[0][:4])].append(float(row[1]))
            sst_last = max(sst_last, row[0])
        years = sorted(y for y in by_year if len(by_year[y]) == 12)  # full years only
        annual = {y: st.mean(by_year[y]) for y in years}
        warm = {y: sum(v >= 19 for v in by_year[y]) for y in years}  # months averaging 19°C or warmer
        base = [y for y in years if 1961 <= y <= 1990]; recent = [y for y in years if y >= years[-1] - 9]
        trend_years = [y for y in years if y >= 1975]
        mx = st.mean(trend_years); my = st.mean(annual[y] for y in trend_years)
        slope = sum((y - mx) * (annual[y] - my) for y in trend_years) / sum((y - mx) ** 2 for y in trend_years) * 10
        # anomaly vs 1961–1990, smoothed as 5-year means for the chart
        b = st.mean(annual[y] for y in base)
        anom5 = []
        for y0 in range(1900, years[-1] + 1, 5):
            v = [annual[y] - b for y in years if y0 <= y < y0 + 5]
            if len(v) >= 3: anom5.append([y0, round(st.mean(v), 2)])
        climate.append(dict(name=name, state=s, anom5=anom5, base=round(b, 1),
                            slope=round(slope, 2),
                            change=round(st.mean(annual[y] for y in recent) - b, 2),
                            warm_base=round(st.mean(warm[y] for y in base), 1),
                            warm_recent=round(st.mean(warm[y] for y in recent), 1),
                            recent_span=f"{recent[0]}–{recent[-1]}"))

    # ---- climate: incident patterns over time
    def east_lat(species):
        out = []
        for a, b in [(1960, 1984), (1985, 2004), (2005, 2025)]:
            v = [r["lat"] for r in rows if r["species"] == species and r["state"] in ("NSW", "QLD")
                 and r["lat"] and a <= r["year"] <= b]
            out.append(dict(span=f"{a}–{b}", n=len(v), median=round(st.median(v), 1) if v else None,
                            south=round(min(v), 1) if v else None))
        return out
    nsw_cool = []
    for a, b in [(1960, 1989), (1990, 2009), (2010, 2019), (2020, 2026)]:
        v = [r for r in rows if r["state"] == "NSW" and r["month"] and a <= r["year"] <= b]
        nsw_cool.append(dict(span=f"{a}–{b if b < 2026 else 'mid-2026'}", n=len(v),
                             cool=round(100 * sum(r["month"] in (4, 5, 6, 7, 8, 9, 10) for r in v) / len(v))))
    nsw_bull = []
    for a, b in [(1960, 1989), (1990, 2009), (2010, 2026)]:
        v = [r for r in rows if r["state"] == "NSW" and r["species"] == "bull shark" and a <= r["year"] <= b]
        nsw_bull.append(dict(span=f"{a}–{b if b < 2026 else 'mid-2026'}", n=len(v),
                             sydney_south=sum(1 for r in v if r["lat"] and r["lat"] <= -33.3)))
    wt = collections.defaultdict(list)
    for r in rows:
        if r["water_temp"] and r["species"] in ("white shark", "bull shark", "tiger shark"):
            wt[r["species"]].append(r["water_temp"])
    water_temp = {k: dict(n=len(v), median=round(st.median(v), 1), lo=min(v), hi=max(v)) for k, v in wt.items()}

    # ---- incidents for the range map: [year, lat, lon, species, fatal, unconfirmed, place]
    incidents = [[r["year"], round(r["lat"], 2), round(r["lon"], 2), species_key(r["species"]), int(r["fatal"]),
                  int(r["source"] != "ASID"), title(r["place"])]
                 for r in rows if r["lat"] is not None]
    spsum = {}
    for k in SPECIES:
        sel = [r for r in rows if species_key(r["species"]) == k]
        wts = [r["water_temp"] for r in sel if r["water_temp"]]
        spsum[k] = dict(all=len(sel), fatal=sum(r["fatal"] for r in sel),
                        since2000=sum(1 for r in sel if r["year"] >= 2000),
                        temp_n=len(wts), temp_median=round(st.median(wts), 1) if wts else None)

    data = dict(
        incidents=incidents, species=spsum,
        built=datetime.date.today().isoformat(),
        asid_last=dict(year=last[0], month=last[1]),
        window=dict(start="2015-07", end="2025-06"),
        states=states, deaths=deaths,
        totals=dict(d10=sum(s["d10"] for s in states), fatal=sum(s["fatal"] for s in states),
                    nonfatal=sum(s["nonfatal"] for s in states)),
        activity=dict(activity), ranking=ranking, decades=decades, months=months,
        climate=climate, sst_last=sst_last, east_lat=dict(bull=east_lat("bull shark"), tiger=east_lat("tiger shark")),
        nsw_cool=nsw_cool, nsw_bull=nsw_bull, water_temp=water_temp,
        recent=[dict(y=r["year"], m=r["month"], state=r["state"], place=title(r["place"]), fatal=r["fatal"],
                     activity=r["activity"], species=r["species"] or "not identified", source=r["source"], ref=r.get("ref"))
                for r in sorted(rows, key=lambda r: (r["year"], r["month"] or 0)) if (r["year"], r["month"] or 0) > (2025, 6)],
    )
    json.dump(data, open(OUT, "w"), separators=(",", ":"))
    print(json.dumps({k: data[k] for k in ("asid_last", "totals", "activity", "nsw_cool", "nsw_bull", "water_temp", "east_lat")}, indent=1))
    print("states", [(s["k"], s["d10"], s["fatal"], s["nonfatal"]) for s in states])
    print("climate", [(c["name"], c["slope"], c["change"], c["warm_base"], c["warm_recent"], c["recent_span"]) for c in climate])

main()
