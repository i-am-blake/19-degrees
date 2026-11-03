"""Consistency check: do the numbers written into the page's text still match the data the page was built from?
Usage: python3 -I check19.py <19-degrees.html> [asid.csv]
The build fills the page's data block; the sentences around it are written by hand in page19.html. This script reads both
from the built page and stops (exit 1) if a sentence no longer matches the data, so a stale number can't go live.
It also checks sums and percentages written in the text ("18 of 31 (58%)") and counts (claims, early results, products).
With asid.csv it also checks the Western Australia bull shark counts in claim C7. Literature figures are not checked here."""
import csv, html, json, re, sys

page = open(sys.argv[1], encoding="utf-8").read()
D = json.loads(re.search(r'id="n19-data">(.*?)</script>', page, re.S).group(1))
body = re.sub(r"<script.*?</script>|<style.*?</style>|<svg.*?</svg>", " ", page, flags=re.S)
T = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", body)))
T = T.replace(" ", " ").replace(" ", " ")
# The change log and "how to cite" record what was true on a date; skip them.
for a, b in (("What has changed Results as they come in", "Who holds the data"), ("How to cite this page", "Free to use with credit")):
    i = T.find(a); j = T.find(b, i + 1)
    if i >= 0 and j > i: T = T[:i] + T[j:]

bad, ok = [], 0
def num(s): return float(s.replace(",", ""))
def check(label, got, want):
    global ok
    if got == want: ok += 1
    else: bad.append(f"{label}: page says {got}, data says {want}")
def find(label, pat, every=False):
    m = list(re.finditer(pat, T)) if every else [re.search(pat, T)]
    m = [x for x in m if x]
    if not m: bad.append(f"{label}: sentence not found (reworded? update check19.py)"); return []
    return m

WORDS = {w: i for i, w in enumerate("zero one two three four five six seven eight nine ten eleven twelve".split())}
sp, im, hb, rn = D["species"], D["imos"], D["heat"], D["rain"]

# Headline: bull shark bites and the 19°C line
for m in find("bull bites (hero)", r"(\d+) bull shark bites\. Not one below 19", True):
    check("bull bites (hero)", int(m[1]), sp["bull"]["n"])
for m in find("bull bites (notebook)", r"(\d+) of (\d+) bull shark bites below 19", True):
    check("bull bites below 19°C (notebook)", (int(m[1]), int(m[2])), (sp["bull"]["below"], sp["bull"]["n"]))
if sp["bull"]["below"]: bad.append("the page says no bull shark bite was below 19°C, but the data has one")

# Sydney's months at 19°C or more, now and 2050
syd = {b["name"]: b for b in D["ahead"]["east"]["beaches"]}
for m in find("Sydney months", r"Sydney's sea now stays above 19°C \(66°F\) (\w+) months a year"):
    check("Sydney months a year at 19°C", WORDS.get(m[1].lower(), m[1]), syd["Sydney"]["now"])

# Drownings vs shark deaths
r = D["ratio"]
for m in find("drowning totals", r"([\d,]+) coastal drownings (\d+) fatal shark bites"):
    check("drowning totals", (int(num(m[1])), int(m[2])), (r["drown"], r["shark"]))
for m in find("drown ratio", r"about (\d+) people drown", True):
    check("people drown per shark death", int(m[1]), round(r["drown"] / r["shark"]))

# Tagged sharks (IMOS)
for m in find("IMOS days", r"Of ([\d,]+) days that (\d+) tagged bull sharks were detected off NSW from (\d+) to (\d+), ([\d.]+)% fell in months when the sea was 19°C or warmer, and none in a month below ([\d.]+)°C"):
    check("IMOS headline", (int(num(m[1])), int(m[2]), int(m[3]), int(m[4]), float(m[5]), float(m[6])),
          (im["days"], im["sharks"], im["y0"], im["y1"], im["pct_warm"], im["min_sst"]))
for m in find("IMOS south", r"south of Sydney, (\d+)% of months in that time were below 19°C"):
    check("months below 19°C south of Sydney", int(m[1]), im["south_months_below"])
c2 = im["c2"]
for m in find("C2", r"from (\d+)–(\d+) a season in \d+–\d+ to (\d+)–(\d+) a season since \d+"):
    check("C2 sharks a season", tuple(map(int, m.groups())), (c2["early_min"], c2["early_max"], c2["recent_min"], c2["recent_max"]))
for m in find("C2 stations", r"rising to (\d+) in (\d+) and falling to (\d+)–(\d+) since"):
    check("C2 listening stations", tuple(map(int, m.groups())), (c2["rec_peak"], c2["rec_peak_season"], c2["rec_last3_min"], c2["rec_last3_max"]))
c16 = im["c16"]
for m in find("C16", r"median of (\d+ \w+) in \d+–\d+ to (\d+ \w+) in (\d+)–(\d+), about ([\d.]+) days later each year \(95% CI ([\d.]+) to ([\d.]+); (\d+) shark-years from (\d+) sharks"):
    check("C16 leaving later", (m[1], m[2], int(m[3]), int(m[4]), float(m[5]), float(m[6]), float(m[7]), int(m[8]), int(m[9])),
          (c16["early"], c16["recent"], c16["recent_from"], c16["recent_to"], c16["slope"], c16["lo"], c16["hi"], c16["n"], c16["sharks"]))

# C6 rain and river mouths
b = rn["bull"]
for m in find("C6 rain", r"(\d+) of (\d+) bull shark bites \((\d+)%\) came in months among the wettest 25%.*?\(p = ([\d.]+)\)"):
    check("C6 wet months", (int(m[1]), int(m[2]), int(m[3]), float(m[4])), (b["q"], b["n"], b["q_pct"], b["q_p"]))
for m in find("C6 white", r"White shark bites, the comparison, sit close to chance in both \((\d+)% and (\d+)%\)"):
    check("C6 white shark comparison", (int(m[1]), int(m[2])), (rn["white"]["q_pct"], rn["gauge"]["white"]["q_pct"]))
mo = rn["mouths"]
for m in find("C6 mouths", r"(\d+) of (\d+) coastal bull shark bites \((\d+)%\) were within (\d+) km of a river mouth, against (\d+)% of the coastline"):
    check("C6 river mouths", tuple(map(int, m.groups())), (mo["bull"]["k"], mo["bull"]["n"], mo["bull"]["pct"], mo["km"], mo["coast_pct"]))
for m in find("C6 mouths others", r"But white \((\d+)%\) and tiger shark bites \((\d+)%\) were too"):
    check("C6 river mouths, white and tiger", (int(m[1]), int(m[2])), (mo["white"]["pct"], mo["tiger"]["pct"]))

# C19 warm spells
def p(x): return f"{x:.3f}".rstrip("0").rstrip(".") if x >= 0.01 else f"{x:.3f}"
for m in find("C19 white", r"White shark bites came in the warmest tenth of months (\d+)% of the time \((\d+) of (\d+)\)"):
    check("C19 white", tuple(map(int, m.groups())), (hb["white"]["t_pct"], hb["white"]["t"], hb["white"]["n"]))
for m in find("C19 tiger", r"tiger shark bites (\d+)% \((\d+) of (\d+), p = ([\d.]+)\)"):
    check("C19 tiger", (int(m[1]), int(m[2]), int(m[3]), m[4]), (hb["tiger"]["t_pct"], hb["tiger"]["t"], hb["tiger"]["n"], f"{hb['tiger']['t_p']:.3f}"))
for m in find("C19 bull", r"Bull shark bites didn't stand out \((\d+)%, (\d+) of (\d+), p = ([\d.]+)\)"):
    check("C19 bull", (int(m[1]), int(m[2]), int(m[3]), float(m[4])), (hb["bull"]["t_pct"], hb["bull"]["t"], hb["bull"]["n"], round(hb["bull"]["t_p"], 2)))

# Réunion and New Caledonia (islands19.py), when present
if "islands" in D:
    I = D["islands"]; c6 = I["c6"]; R, N = I["islands"]["Reunion"], I["islands"]["New Caledonia"]
    for m in find("islands C6", r"(\d+) of (\d+) bull shark bites \((\d+)%\) came after 50 mm or more of rain over 3 days, against (\d+) of (\d+) bites by other identified sharks \((\d+)%; p = ([\d.]+)\)\. The water was turbid at (\d+)% of bull shark bites and (\d+)% of the others \(p = ([\d.]+)\)"):
        b, o = c6["bull"], c6["other"]
        check("islands C6", (int(m[1]), int(m[2]), int(m[3]), int(m[4]), int(m[5]), int(m[6]), m[7], int(m[8]), int(m[9]), m[10]),
              (b["wet"], b["rain_n"], b["wet_pct"], o["wet"], o["rain_n"], o["wet_pct"], f"{c6['p_wet']:.2f}", b["turbid_pct"], o["turbid_pct"], f"{c6['p_turbid']:.2f}"))
    for m in find("islands C22", r"coldest month since 1980 averaged ([\d.]+)°C off Réunion and ([\d.]+)°C off New Caledonia, so all (\d+) bull shark bites there came in water above 19°C \(coolest bite month ([\d.]+)°C\)"):
        bs = [R["species"]["bull"], N["species"]["bull"]]
        check("islands C22", (float(m[1]), float(m[2]), int(m[3]), float(m[4])), (R["sea_min"], N["sea_min"], sum(x["n"] for x in bs), min(x["min"] for x in bs)))
    if R["months_below19"] or N["months_below19"]: bad.append("islands: the page says the sea there never falls to 19°C, but the data has months below")

# Western Australia's bull shark jump (chart data) and population
w = D["wa_spike"]
if not w["post"] > w["pre"]: bad.append(f"WA: page says more bull shark bites since 2020 than in the 120 years before, data has {w['post']} vs {w['pre']}")
pm = D["pop_mid"]
if not pm[max(pm, key=int)] / pm["1900"] > 6: bad.append("population: page says more than sixfold since 1900")

# Counts
cards = page.count('class="claim"')
early = page.count('data-status="early"')
for lab, pat, want in (("claims", r"See the (\d+) claims", cards), ("claims", r"Testable claims (\d+)", cards),
                       ("claims", r"Pick one of (\d+) claims", cards), ("claims", r"one of (\d+) testable claims", cards),
                       ("early results", r"Early results (\d+)", early)):
    for m in find(lab, pat, True): check(f"number of {lab} ('{m[0]}')", int(m[1]), want)
i = page.find("Products and the evidence"); seg = page[i:page.find("</section>", i)]
prods = seg.count('<td class="psrc">')
for pat in (r"Products checked (\d+)", r"See all (\d+) products", r"(\d+) products we checked"):
    for m in find("products", pat, True): check(f"number of products ('{m[0]}')", int(m[1]), prods)

# Sums written in the text
for m in find("Queensland catch", r"caught ([\d,]+) bull sharks since \d+, ([\d,]+) on drumlines,? (?:and )?([\d,]+) in nets(?: and ([\d,]+) by other gear)?"):
    check("Queensland bull shark catch (total = parts)", int(num(m[1])), sum(int(num(x)) for x in m.groups()[1:] if x))
for m in find("Queensland bites", r"Of the (\d+) bull shark bites in Queensland since.*?, (\d+) was within.*?, (\d+) at beaches with drumlines only, and (\d+) away"):
    check("Queensland bull shark bites (total = parts)", int(m[1]), int(m[2]) + int(m[3]) + int(m[4]))
for m in find("NSW nets", r"Only (\d+) were target sharks \((\d+) white, (\d+) tiger, (\d+) bull\)"):
    check("NSW net target sharks (total = parts)", int(m[1]), int(m[2]) + int(m[3]) + int(m[4]))
# "x of y (z%)" anywhere: z should be x/y rounded
for m in re.finditer(r"\b(\d[\d,]*) of (?:the )?(\d[\d,]*)\b[^()%.;]{0,90}?\((\d+(?:\.\d)?)%", T):
    x, y, z = num(m[1]), num(m[2]), float(m[3])
    if y and abs(100 * x / y - z) > 0.51: bad.append(f"percentage: '{m[0]}' — {m[1]} of {m[2]} is {100 * x / y:.1f}%")
    else: ok += 1

# C7 needs the bite database
if len(sys.argv) > 2:
    wa = [int(x["Incident.year"]) for x in csv.DictReader(open(sys.argv[2], encoding="utf-8"))
          if x["State"].strip() == "WA" and "bull" in x["Shark.common.name"].lower()
          and x["Provoked/unprovoked"].strip() == "unprovoked" and x["Incident.year"].isdigit()]
    for m in find("C7", r"Western Australia has (\d+) recorded (?:unprovoked )?bull shark bites since 1900, (\d+) of them since 2020"):
        check("C7 WA unprovoked bull shark bites", (int(m[1]), int(m[2])), (len(wa), sum(1 for y in wa if y >= 2020)))

print(f"check19: {ok} checks passed, {len(bad)} problems")
for x in bad: print("  -", x)
sys.exit(1 if bad else 0)
