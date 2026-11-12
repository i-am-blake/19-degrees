"""Two checks on the Tampa Bay bull shark days that fell below 19°C in explore_daily.py.
Usage: python3 -I explore_tampa.py
1. Is the tracking dataset really bull sharks? Prints its OBIS description, its species list, and for the records labeled
   Carcharhinus leucas: how many tagged animals, their days and winter days, and where the receivers are.
2. Was the bay really that cold? Prints daily mean water temperature measured at NOAA tide gauges in Tampa Bay (CO-OPS,
   public domain), 2019 on, to set beside the satellite reading for the same days."""
import csv, io, json, time, urllib.request, urllib.parse, collections
DS = "c5e06e5d-7775-4df2-a24f-18babe51fc28"
def get(url, raw=False):
    for a in range(5):
        try:
            t = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "19-degrees.org research"}), timeout=120).read().decode()
            return t if raw else json.loads(t)
        except Exception as e:
            if a == 4: print("FAIL", url[:120], str(e)[:80], flush=True); return None
            time.sleep(6 * (a + 1))

m = get(f"https://api.obis.org/v3/dataset/{DS}")
if m and m.get("results"):
    r = m["results"][0]
    for k in ("title", "abstract", "citation", "intellectualrights", "published", "records", "url", "node_name"):
        print("META", k, "=", str(r.get(k))[:1500].replace("\n", " "))
    print("META contacts =", [(c.get("givenname"), c.get("surname"), c.get("organization")) for c in (r.get("contacts") or [])][:8])
c = get(f"https://api.obis.org/v3/checklist?datasetid={DS}&size=100")
if c:
    for x in c.get("results", []): print("SPECIES", x.get("scientificName"), x.get("records"), x.get("taxonRank"))

# every record labeled bull shark in that dataset
rows = []; after = None; first = True
while True:
    u = f"https://api.obis.org/v3/occurrence?datasetid={DS}&scientificname=Carcharhinus%20leucas&size=10000" + (f"&after={after}" if after else "")
    o = get(u)
    if not o or not o.get("results"): break
    if first:
        print("SAMPLE", json.dumps({k: v for k, v in o["results"][0].items() if k not in ("flags",)})[:2500]); print("TOTAL", o.get("total")); first = False
    for x in o["results"]:
        rows.append((x.get("organismID") or x.get("organismName") or x.get("recordedBy") or "?", (x.get("eventDate") or "")[:10], x.get("decimalLatitude"), x.get("decimalLongitude"),
                     x.get("occurrenceStatus"), x.get("lifeStage"), x.get("sex"), x.get("eventID") or "", x.get("locality") or x.get("locationID") or ""))
    after = o["results"][-1]["id"]
    if len(o["results"]) < 10000: break
print("ROWS", len(rows))
W = ("12", "01", "02")
ind = collections.defaultdict(set)
for r in rows: ind[r[0]].add(r[1])
print("ANIMALS", len(ind))
for k, d in sorted(ind.items(), key=lambda x: -len(x[1]))[:60]:
    d = sorted(d); print("ANIMAL", k, "days", len(d), "first", d[0], "last", d[-1], "winter_days", sum(x[5:7] in W for x in d), "winters", len({x[:4] if x[5:7] == "12" else str(int(x[:4]) - 1) for x in d if x[5:7] in W}))
print("STATUS", collections.Counter(r[4] for r in rows), "LIFE", collections.Counter(r[5] for r in rows).most_common(5))
for (la, lo, loc), n in collections.Counter((r[2], r[3], r[8]) for r in rows).most_common(40): print("SITE", la, lo, loc, n)
print("SITE_WINTER", collections.Counter((round(r[2], 2), round(r[3], 2)) for r in rows if r[1][5:7] in W).most_common(15))
print("DAYS_BY_MONTH", sorted(collections.Counter(d[5:7] for d in {(r[0], r[1]) for r in rows} for d in [d[1]]).items()))

# water temperature measured in the bay
for st, name in (("8726520", "St Petersburg"), ("8726384", "Port Manatee"), ("8726607", "Old Port Tampa"), ("8726667", "McKay Bay Entrance"), ("8726724", "Clearwater Beach")):
    day = collections.defaultdict(list)
    for y in range(2019, 2027):
        t = get(f"https://api.tidesandcurrents.noaa.gov/api/prod/datagetter?product=water_temperature&application=19degrees&begin_date={y}0101&end_date={y}1231&station={st}&time_zone=gmt&units=metric&interval=h&format=csv", raw=True)
        if not t or "Error" in t[:200]: print("GAUGE_NOTE", name, y, (t or "")[:100].replace("\n", " ")); continue
        for r in list(csv.reader(io.StringIO(t)))[1:]:
            try: day[r[0][:10]].append(float(r[1]))
            except (ValueError, IndexError): pass
    for d in sorted(day):
        v = day[d]
        if len(v) >= 12: print("GAUGE", st, d, round(sum(v) / len(v), 2), round(min(v), 2), sep=",")
    print("GAUGE_DONE", name, len(day), flush=True)
