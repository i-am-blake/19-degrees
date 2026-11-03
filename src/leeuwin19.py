"""Claim C7 (first look): did Western Australia's bull shark bites come in months when the Leeuwin Current ran strong?
Usage: python3 -I leeuwin19.py <asid.csv> <fremantle_psmsl111.rlrdata | bom_fremantle_62230.html>
The current's strength is read from Fremantle monthly sea level (PSMSL station 111), the standard index: the record is
detrended (quadratic fit, to remove sea-level rise), the seasonal cycle removed, and each bite month ranked against the same
calendar month in 1950 to the end of the record. Prints the result; the page states it as a first look."""
import csv, sys, numpy as np
asid, fre = sys.argv[1:3]; sl = {}
if fre.endswith((".html", ".shtml")):
    # Bureau of Meteorology monthly table (port 62230, metres): Mth, Year, Gaps, Good, Min, Max, Mean, St Devn.
    # Keep months with at least 90% of hourly readings good; this record runs later than PSMSL's.
    import html, re
    for row in re.findall(r"<tr[^>]*>(.*?)</tr>", open(fre, errors="replace").read(), re.S):
        c = [html.unescape(re.sub(r"<[^>]+>", "", x)).strip() for x in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row, re.S)]
        if len(c) == 8 and c[0].isdigit() and c[1].isdigit() and re.match(r"-?\d", c[6]) and re.match(r"\d", c[3]):
            good, gaps = int(c[3]), int(c[2]) if c[2].isdigit() else 0
            if good >= 0.9 * (good + gaps): sl[(int(c[1]), int(c[0]))] = float(c[6]) * 1000
else:
    for l in open(fre):  # PSMSL monthly file (mm)
        t, v, *_ = [x.strip() for x in l.split(";")]
        if int(v) == -99999: continue
        y = int(float(t)); sl[(y, int(round((float(t) - y) * 12 + 0.5)))] = int(v)
ks = sorted(sl); t = np.array([y + (m - .5) / 12 for y, m in ks]); v = np.array([sl[k] for k in ks], float)
r = dict(zip(ks, v - np.polyval(np.polyfit(t, v, 2), t)))
clim = {m: np.mean([r[k] for k in r if k[1] == m]) for m in range(1, 13)}; an = {k: r[k] - clim[k[1]] for k in r}
last = ks[-1]; print("record", ks[0], "to", last)
bites = [(int(x["Incident.year"]), int(x["Incident.month"])) for x in csv.DictReader(open(asid))
         if x["State"].strip() == "WA" and "bull" in x["Shark.common.name"].lower() and x["Provoked/unprovoked"].strip() == "unprovoked"
         and x["Incident.month"].strip() and x["Incident.year"].isdigit()]
rec = [b for b in bites if b[0] >= 2020]; inrec = [b for b in rec if b in an]
strong = sum(1 for (y, m) in inrec if sum(an[(yy, m)] < an[(y, m)] for yy in range(1950, last[0] + 1) if yy != y and (yy, m) in an) / sum(1 for yy in range(1950, last[0] + 1) if yy != y and (yy, m) in an) >= 0.5)
print(f"WA bull shark bites since 1900: {len(bites)}; since 2020: {len(rec)}; inside the sea-level record: {len(inrec)}; in stronger-than-usual months: {strong}")
