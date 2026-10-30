"""Claim C20 (first look, Queensland): bull shark catches by gear, and where bull shark bites happened relative to today's gear.
Usage: python3 -I nets19.py <asid.csv> <shark-gear-locations.xlsx> <scp-numbers-caught.xlsx>
Both files: Queensland Shark Control Program open data, CC BY 4.0 (data.qld.gov.au). Gear locations are today's, not
historical, and busy beaches get gear first, so this describes; it cannot say whether the gear works."""
import collections, csv, math, re, sys, openpyxl
asid, gfile, cfile = sys.argv[1:4]
num = lambda v: float(re.sub(r"[^0-9.]", "", str(v))) if v not in (None, "") and re.sub(r"[^0-9.]", "", str(v)) else None
gear = []
for ws in openpyxl.load_workbook(gfile, read_only=True, data_only=True).worksheets[1:]:
    loc = None
    for r in ws.iter_rows(values_only=True):
        r = list(r) + [None] * 12
        if r[1] and str(r[1]).strip().lower().startswith(("net", "drum")) and num(r[3]) and num(r[5]):
            if r[0]: loc = str(r[0]).strip()
            gear.append((ws.title, loc, "net" if str(r[1]).lower().startswith("net") else "drum", -(num(r[3]) + (num(r[4]) or 0) / 60), num(r[5]) + (num(r[6]) or 0) / 60))
beach = collections.defaultdict(set)
for a, l, t, la, lo in gear: beach[(a, l)].add(t)
print(f"gear: {len(gear)} items ({sum(g[2]=='net' for g in gear)} nets) at {len(beach)} beaches, {sum('net' in v for v in beach.values())} with nets")
rows = list(openpyxl.load_workbook(cfile, read_only=True, data_only=True).worksheets[0].iter_rows(values_only=True)); H = rows[0]
C = [dict(zip(H, r)) for r in rows[1:]]
bull = [c for c in C if str(c["CommonName"]).upper() == "BULL WHALER"]
print(f"bull sharks caught {min(c['Year'] for c in C)}-{max(c['Year'] for c in C)}: {len(bull)}", dict(collections.Counter(c["Gear"] for c in bull)))
def km(a, b, c, d): return math.hypot((b - d) * 111.32 * math.cos(math.radians(a)), (a - c) * 110.57)
cnt = collections.Counter()
for x in csv.DictReader(open(asid)):
    if x["State"].strip() != "QLD" or x["Provoked/unprovoked"].strip() != "unprovoked" or "bull" not in x["Shark.common.name"].lower(): continue
    if not x["Latitude"].strip() or not x["Incident.year"].isdigit() or int(x["Incident.year"]) < 1962: continue
    la, lo = float(x["Latitude"]), float(x["Longitude"]); g = min(gear, key=lambda g: km(la, lo, g[3], g[4]))
    cnt["no gear within 1.5 km" if km(la, lo, g[3], g[4]) > 1.5 else "beach with nets" if "net" in beach[(g[0], g[1])] else "drumlines only"] += 1
print("Queensland bull shark bites since 1962, by today's gear:", dict(cnt), "total", sum(cnt.values()))
