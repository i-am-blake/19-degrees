"""Claim C7 (first look): did Western Australia's bull shark bites come in months when the Leeuwin Current ran strong?
Usage: python3 -I leeuwin19.py <asid.csv> <fremantle_psmsl111.rlrdata> [uhslc_fremantle_daily.csv] [out leeuwin.json]
The current's strength is read from Fremantle monthly sea level (PSMSL station 111), the standard index: the record is
detrended (quadratic fit, to remove sea-level rise), the seasonal cycle removed, and each bite month ranked against the same
calendar month in 1950 to the end of the record. PSMSL lags by a few years, so later months come from the University of
Hawaii Sea Level Center's fast-delivery daily means (station 175), shifted onto PSMSL's datum by the average difference
over the months both cover. Prints the result; the page states it as a first look."""
import csv, sys, numpy as np
asid, fre = sys.argv[1:3]; rest = sys.argv[3:]
UH = rest.pop(0) if rest and rest[0].endswith(".csv") else None
OUT = rest[0] if rest else None; sl = {}
for l in open(fre):  # PSMSL monthly file (mm)
    t, v, *_ = [x.strip() for x in l.split(";")]
    if int(v) == -99999: continue
    y = int(float(t)); sl[(y, int(round((float(t) - y) * 12 + 0.5)))] = int(v)
if UH:
    # ERDDAP csv: a header row, a units row, then time,sea_level (mm). Keep months with at least 24 good days.
    days = {}
    with open(UH) as f:
        r = csv.reader(f); head = next(r); next(r, None)
        it, iv = head.index("time"), head.index("sea_level")
        for row in r:
            try: v = float(row[iv])
            except (ValueError, IndexError): continue
            if not v == v or v < -9000: continue  # skip NaN and fill values
            days.setdefault((int(row[it][:4]), int(row[it][5:7])), []).append(v)
    uh = {k: float(np.mean(v)) for k, v in days.items() if len(v) >= 24}
    both = [k for k in uh if k in sl and k[0] >= 1990]
    if len(both) >= 24:
        off = float(np.mean([sl[k] - uh[k] for k in both]))
        add = {k: uh[k] + off for k in uh if k not in sl and k > max(sl)}
        print(f"UHSLC: {len(both)} shared months, offset {off:.0f} mm, {len(add)} later months added"); sl.update(add)
    else:
        print("UHSLC: too few shared months to line up the datum; using PSMSL only")
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
if OUT:
    import json, math
    p = sum(math.comb(len(inrec), k) for k in range(strong, len(inrec) + 1)) / 2 ** len(inrec) if inrec else None
    json.dump(dict(n=len(bites), since2020=len(rec), checked=len(inrec), strong=strong, p=round(p, 2) if p is not None else None,
                   last=f"{last[0]}-{last[1]:02d}"), open(OUT, "w"))
