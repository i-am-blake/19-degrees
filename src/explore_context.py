"""Look only: daily rain before a shark incident, from GHCN-Daily (NOAA NCEI, Bureau of Meteorology stations).
Usage: python3 explore_context.py STATION[,STATION] YYYY-MM-DD. Prints daily rain for the 14 days before and the 1991-2020
average 7-day total for the same dates. Changes nothing."""
import json, sys, datetime as dt, urllib.request, statistics as st
U = "https://www.ncei.noaa.gov/access/services/data/v1?dataset=daily-summaries&dataTypes=PRCP&format=json&units=metric"
def get(s, a, b):
    r = urllib.request.urlopen(urllib.request.Request(f"{U}&stations={s}&startDate={a}&endDate={b}", headers={"User-Agent": "19-degrees/1.0"}), timeout=120)
    return {x["DATE"][:10]: float(x["PRCP"]) for x in json.loads(r.read()) if x.get("PRCP") not in (None, "")}
day = dt.date.fromisoformat(sys.argv[2])
for s in sys.argv[1].split(","):
    try:
        d = get(s, (day - dt.timedelta(days=14)).isoformat(), day.isoformat())
        print(f"\n## {s}\nlatest day: {max(d) if d else None}\n" + " ".join(f"{k[5:]}:{v:g}" for k, v in sorted(d.items())))
        wk = [(day - dt.timedelta(days=k)).isoformat() for k in range(1, 8)]
        print("7 days before:", round(sum(d.get(k, 0) for k in wk), 1), "mm; days with data", sum(k in d for k in wk))
        tot = []
        for y in range(1991, 2021):
            a, b = (day.replace(year=y) - dt.timedelta(days=7)), (day.replace(year=y) - dt.timedelta(days=1))
            h = get(s, a.isoformat(), b.isoformat())
            if len(h) >= 6: tot.append(sum(h.values()))
        print(f"1991-2020 average for those dates: {st.mean(tot):.1f} mm over {len(tot)} years; wetter years: {sum(t > sum(d.get(k,0) for k in wk) for t in tot)}" if tot else "no normals")
    except Exception as e:
        print(s, type(e).__name__, str(e)[:200])
