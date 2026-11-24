"""Look only: first pass at two new ideas. Prints a report; changes nothing.
A. Frontier coasts: where bull sharks reach the cool edge of their range (east Australia, KwaZulu-Natal, the US East
   Coast, southern Brazil). Along each coast, HadISST monthly sea temperature at an offshore point every degree of latitude:
   months a year at or above 19 C in 1950-1979 and 2010-2025, and where the half-year line sits in each era.
B. Seasonal forecasts: can the runner reach the NMME seasonal sea temperature forecasts (NOAA CPC and Columbia's
   forecast.ccsr), and what do the files hold?"""
import csv, io, re, time, urllib.request
UA = {"User-Agent": "19-degrees-explore/1.0 (+https://19-degrees.org)"}
def get(u, t=150):
    return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=t).read()
H = "https://coastwatch.pfeg.noaa.gov/erddap/griddap/erdHadISST.csv?sst"
COASTS = {  # offshore 1-degree cells along each coast, from the warm end toward the cool end
 "East Australia": [(-24.5, 153.5), (-25.5, 153.5), (-26.5, 153.5), (-27.5, 154.0), (-28.5, 154.0), (-29.5, 153.8), (-30.5, 153.5), (-31.5, 153.2),
                    (-32.5, 152.8), (-33.5, 151.8), (-34.5, 151.3), (-35.5, 150.8), (-36.5, 150.5), (-37.5, 150.5)],
 "KwaZulu-Natal and Eastern Cape": [(-25.5, 33.5), (-26.5, 33.5), (-27.5, 33.0), (-28.5, 32.7), (-29.5, 31.8), (-30.5, 31.0), (-31.5, 30.0),
                    (-32.5, 29.0), (-33.5, 27.5), (-34.5, 25.0)],
 "US East Coast": [(27.5, -79.8), (28.5, -80.0), (29.5, -80.8), (30.5, -81.0), (31.5, -80.8), (32.5, -79.8), (33.5, -78.3), (34.5, -76.5),
                    (35.5, -75.3), (36.5, -75.5), (37.5, -75.3), (38.5, -74.8), (39.5, -74.0), (40.5, -73.5)],
 "Southern Brazil": [(-22.5, -41.5), (-23.5, -44.5), (-24.5, -46.5), (-25.5, -47.8), (-26.5, -48.2), (-27.5, -48.2), (-28.5, -48.5),
                    (-29.5, -49.5), (-30.5, -50.0), (-31.5, -50.8), (-32.5, -52.0), (-33.5, -53.0)],
}
def series(la, lo):
    for dla, dlo in ((0, 0), (0, 1), (0, -1), (0, 2), (0, -2)):
        for k in range(6):
            try:
                t = get(f"{H}%5B(1950-01-16):1:(last)%5D%5B({la + dla})%5D%5B({lo + dlo})%5D").decode(); break
            except Exception as e:
                if k == 5: raise
                time.sleep(20 * (k + 1))
        rows = [(r[0][:7], r[3]) for r in list(csv.reader(io.StringIO(t)))[2:]]
        good = [(d, float(v)) for d, v in rows if v not in ("NaN", "")]
        if len(good) > 0.95 * len(rows): return la + dla, lo + dlo, good
    return None
def warm(good, y0, y1):
    by = {}
    for d, v in good:
        y = int(d[:4])
        if y0 <= y <= y1: by.setdefault(y, []).append(v)
    full = [m for y, m in by.items() if len(m) == 12]
    return sum(sum(1 for v in m if v >= 19) for m in full) / len(full) if full else None
def frontier():
    print("\n## A. Frontier coasts: months a year at or above 19°C\n")
    for coast, pts in COASTS.items():
        print(f"\n### {coast}\n\n| Latitude | Cell | 1950–79 | 2010–25 | Change |\n|---|---|---|---|---|")
        line = {"a": None, "b": None}
        for la, lo in pts:
            try:
                s = series(la, lo)
            except Exception as e:
                print(f"| {la} | failed: {type(e).__name__} | | | |"); continue
            if not s: print(f"| {la} | no ocean cell | | | |"); continue
            cla, clo, good = s; a, b = warm(good, 1950, 1979), warm(good, 2010, 2025)
            print(f"| {abs(la)}°{'S' if la < 0 else 'N'} | {cla},{clo} | {a:.1f} | {b:.1f} | {b - a:+.1f} |")
            if a is not None and a >= 6: line["a"] = la
            if b is not None and b >= 6: line["b"] = la
            time.sleep(1)
        if line["a"] is not None and line["b"] is not None:
            print(f"\nHalf-year line (last cell with 6+ warm months): {abs(line['a'])}° in 1950–79, {abs(line['b'])}° in 2010–25, "
                  f"about {abs(line['b'] - line['a']) * 111:.0f} km {'poleward' if abs(line['b']) > abs(line['a']) else 'toward the equator'}")
def forecasts():
    print("\n## B. Seasonal forecast sources\n")
    for name, u in (("NOAA CPC NMME directory", "https://ftp.cpc.ncep.noaa.gov/NMME/"),
                    ("CPC NMME real-time SST, ensemble mean", "https://ftp.cpc.ncep.noaa.gov/NMME/realtime_anom/ENSMEAN/"),
                    ("Columbia forecast.ccsr", "https://forecast.ccsr.columbia.edu/"),
                    ("NOAA NCEI ERDDAP NMME", "https://www.ncei.noaa.gov/erddap/search/index.html?searchFor=nmme+sst&page=1&itemsPerPage=50")):
        try:
            t = get(u, 60).decode("utf-8", "replace")
            links = re.findall(r'href="([^"?]+)"', t)
            print(f"- **{name}**: reachable; {len(links)} links, e.g. " + ", ".join(links[5:20]))
        except Exception as e:
            print(f"- **{name}**: {type(e).__name__}: {str(e)[:150]}")
try: frontier()
except Exception as e: print("frontier failed", e)
forecasts()
