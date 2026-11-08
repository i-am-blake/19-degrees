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

# Tiger sharks in the rain test (C6), when present
if rn.get("tiger"):
    tg = rn["tiger"]
    for m in find("C6 tiger", r"Tiger shark bites lean wetter too: (\d+) of (\d+) \((\d+)%\) came in the wettest quarter of months \(p = ([\d.]+)\), and (\d+) \((\d+)%\) in the wettest tenth \(p = ([\d.]+)\)"):
        check("C6 tiger", (int(m[1]), int(m[2]), int(m[3]), m[4], int(m[5]), int(m[6]), m[7]), (tg["q"], tg["n"], tg["q_pct"], f"{tg['q_p']:.2f}", tg["t"], tg["t_pct"], f"{tg['t_p']:.3f}"))

# Claims C26 (iod19.py) and C18 (coastpop19.py), when present
if "iod" in D:
    a = D["iod"]["all"]
    for m in find("C26", r"Compared with the same calendar month in the same decade, (\d+) bites against about ([\d.]+) expected \(p = ([\d.]+)\), and (\d+) in negative months against about (\d+(?:\.\d)?)"):
        check("C26 dipole", (int(m[1]), float(m[2]), m[3], int(m[4]), float(m[5])), (a["pos"], a["pos_exp"], f"{a['p']:.2f}", a["neg"], a["neg_exp"]))
if "coastpop" in D:
    C = D["coastpop"]; d0 = next(x for x in C["decades"] if x["decade"] == C["base"]); dN = C["decades"][-1]
    for m in find("C18", r"grew ([\d.]+) times from the 1990s to the (\d+)s, while unprovoked bites per million coastal residents a year rose from ([\d.]+) to ([\d.]+) \(([\d.]+) times\), and bull shark bites from ([\d.]+) to ([\d.]+) \(([\d.]+) times\)"):
        check("C18 coastal population", (float(m[1]), int(m[2]), float(m[3]), float(m[4]), float(m[5]), float(m[6]), float(m[7]), float(m[8])),
              (C["pop_growth"], dN["decade"], d0["rate"], dN["rate"], C["rate_growth"], d0["bull_rate"], dN["bull_rate"], C["bull_growth"]))

# Claim C25 (obis19.py), when present
if "obis" in D:
    A, U = D["obis"]["groups"]["africa"], D["obis"]["groups"]["us"]
    for m in find("C25", r"Off Mozambique and South Africa, ([\d,]+) days that tagged bull sharks were detected \((\d+)–(\d+)\) all fell in months at 19°C or warmer, the coolest ([\d.]+)°C, though (\d+)% of months in the same places were below 19°C\. Off the US Gulf and Atlantic coasts, ([\d.]+)% of ([\d,]+) bull shark record-days were at 19°C or warmer \((\d+) below, the coolest ([\d.]+)°C\), against (\d+)% of months below 19°C there\. Tiger sharks range cooler: ([\d.]+)% of ([\d,]+) US record-days at 19°C or warmer, the coolest ([\d.]+)°C"):
        b, ub, ut = A["bull"], U["bull"], U["tiger"]
        check("C25 outside Australia", (int(num(m[1])), int(m[2]), int(m[3]), float(m[4]), int(m[5]), float(m[6]), int(num(m[7])), int(m[8]), float(m[9]), int(m[10]), float(m[11]), int(num(m[12])), float(m[13])),
              (b["days"], b["y0"], b["y1"], b["min"], b["cell_months_below_pct"], ub["pct_warm"], ub["days"], ub["below"], ub["min"], ub["cell_months_below_pct"], ut["pct_warm"], ut["days"], ut["min"]))
    if A["bull"]["below"]: bad.append("C25: the page says no African bull shark detection was in a month below 19°C, but the data has one")

# Water on the day, time of day and the moon, when present
if "fieldnotes" in D:
    w, t = D["fieldnotes"]["water"], D["fieldnotes"]["time"]
    for m in find("water on the day", r"all (\d+) bull shark bites were in water of ([\d.]+)°C or warmer\. For comparison, (\d+) of (\d+) tiger shark bites and (\d+) of (\d+) white shark bites were below 19°C, the coldest at ([\d.]+)°C"):
        check("water on the day", (int(m[1]), float(m[2]), int(m[3]), int(m[4]), int(m[5]), int(m[6]), float(m[7])),
              (w["bull"]["n"], w["bull"]["min"], w["tiger"]["below19"], w["tiger"]["n"], w["white"]["below19"], w["white"]["n"], w["white"]["min"]))
    if w["bull"]["below19"]: bad.append("water on the day: a bull shark bite below 19°C was recorded at the scene")
    for m in find("C21 time of day", r"(\d+)% of (\d+) bull shark bites with a recorded time happened at night \(8 pm to 5 am\), against (\d+)% of (\d+) white and tiger shark bites \(p = ([\d.]+)\)\. Across dawn, dusk and night together the shares are close \((\d+)% and (\d+)%, p = ([\d.]+)\)"):
        b, o = t["bull"], t["others"]
        check("C21 time of day", (int(m[1]), int(m[2]), int(m[3]), int(m[4]), m[5], int(m[6]), int(m[7]), m[8]),
              (b["night_pct"], b["n"], o["night_pct"], o["n"], f"{t['p_night']:.2f}", b["low_pct"], o["low_pct"], f"{t['p']:.2f}"))
if "lunar" in D:
    A, C, I = D["lunar"]["all"], D["lunar"]["california_white"], D["lunar"]["islands_bull"]
    for m in find("C24 moon", r"Of (\d+) bites with a known date in California, Réunion and New Caledonia, (\d+) \((\d+)%\) came within 3\.7 days of a full or new moon, about the half that chance gives \(p = ([\d.]+)\)\. California's white shark bites: (\d+) of (\d+) \((\d+)%\)\. The exception was bull sharks in the islands, with only (\d+) of (\d+) \((\d+)%; p = ([\d.]+)\)"):
        check("C24 moon", (int(m[1]), int(m[2]), int(m[3]), m[4], int(m[5]), int(m[6]), int(m[7]), int(m[8]), int(m[9]), int(m[10]), float(m[11])),
              (A["n"], A["near"], A["near_pct"], f"{A['p']:.2f}", C["near"], C["n"], C["near_pct"], I["near"], I["n"], I["near_pct"], I["p"]))

# C19 daily marine heatwaves (mhw19.py) and C6 Beachwatch (beach19.py), when present
if "mhw" in D:
    M = D["mhw"]; c, h, ht, ib, it, a = M["california_white"], M["hawaii_all"], M["hawaii_tiger"], M["islands_bull"], M["islands_tiger"], M["all"]
    for m in find("C19 heatwaves", r"California's white shark bites lean that way, (\d+) of (\d+) \((\d+)%\) during a heatwave against (\d+)% expected for the same place and time of year \(p = ([\d.]+)\), and so do Hawaii's, (\d+) of (\d+) \((\d+)% against (\d+)%; p = ([\d.]+)\), tiger sharks (\d+) of (\d+)\. Bull and tiger shark bites at Réunion and New Caledonia didn't \((\d+) of (\d+) and (\d+) of (\d+)\)\. All together, (\d+) of (\d+) \((\d+)% against (\d+)%; p = ([\d.]+)\)"):
        g = m.groups()
        check("C19 heatwaves", tuple(g), tuple(str(x) for x in (c["in_heatwave"], c["n"], c["pct"], c["expected_pct"], f"{c['p']:.2f}", h["in_heatwave"], h["n"], h["pct"], h["expected_pct"], f"{h['p']:.2f}",
              ht["in_heatwave"], ht["n"], ib["in_heatwave"], ib["n"], it["in_heatwave"], it["n"], a["in_heatwave"], a["n"], a["pct"], a["expected_pct"], f"{a['p']:.2f}")))
if "beachwatch" in D:
    b, w = D["beachwatch"]["bull"], D["beachwatch"]["white"]
    for m in find("C6 Beachwatch", r"(\d+) of (\d+) NSW bull shark bites since 1992 came in months when that water was in its dirtiest quarter for the time of year \(p = ([\d.]+)\), against (\d+) of (\d+) white shark bites"):
        check("C6 Beachwatch", (int(m[1]), int(m[2]), float(m[3]), int(m[4]), int(m[5])), (b["dirtiest_quarter"], b["n"], b["p"], w["dirtiest_quarter"], w["n"]))

if "hawaii" in D:
    h = D["hawaii"]
    for m in find("C6 Hawaii", r"Hawaii \((\d+)–(\d+)\): the water was turbid or muddy at (\d+)% of tiger shark bites \((\d+) of (\d+)\) and (\d+)% of bites by other identified sharks \((\d+) of (\d+); p = ([\d.]+)\)"):
        check("C6 Hawaii", (int(m[1]), int(m[2]), int(m[3]), int(m[4]), int(m[5]), int(m[6]), int(m[7]), int(m[8]), m[9]),
              (h["first"], h["last"], h["tiger_murky_pct"], h["tiger_murky"], h["tiger_clarity_n"], h["other_murky_pct"], h["other_murky"], h["other_clarity_n"], f"{h['p_murky']:.2f}"))
if "lunar" in D and "hawaii_all" in D["lunar"]:
    a, t = D["lunar"]["hawaii_all"], D["lunar"]["hawaii_tiger"]
    for m in find("C24 Hawaii", r"Hawaii agrees: (\d+) of (\d+) bites \((\d+)%; p = ([\d.]+)\), and (\d+) of (\d+) tiger shark bites"):
        check("C24 Hawaii", (int(m[1]), int(m[2]), int(m[3]), m[4], int(m[5]), int(m[6])), (a["near"], a["n"], a["near_pct"], f"{a['p']:.2f}", t["near"], t["n"]))

# Day-dated tests: weekends and beach weather (C18), humpbacks (C5), chlorophyll (C4), tides (C24), when present
def _pf(p): return "p < 0.001" if p < 0.001 else f"p = {p:.3f}" if p < 0.01 else f"p = {p:.2f}"
P = r"(p < 0\.001|p = [\d.]+)"
if "exposure" in D:
    w = D["exposure"]["weekend"]; ca, nc, hi, al = w["california"], w["new_caledonia"], w["hawaii"], w["all"]
    for m in find("C18 weekends", r"In California, (\d+) of (\d+) bites \((\d+)%\) fell on a weekend, which is (\d+)% of days: ([\d.]+) times as many bites per weekend day as per weekday \(" + P + r"\)\. New Caledonia shows the same \((\d+) of (\d+), ([\d.]+) times; " + P + r"\); Hawaii, where locals surf every day, doesn't \((\d+) of (\d+), ([\d.]+) times\)\. All (\d+) day-dated bites: ([\d.]+) times \(" + P + r"\)"):
        check("C18 weekends", m.groups(), tuple(str(x) for x in (ca["busy"], ca["n"], ca["pct"], ca["expected_pct"], ca["ratio"], _pf(ca["p"]), nc["busy"], nc["n"], nc["ratio"], _pf(nc["p"]),
              hi["busy"], hi["n"], hi["ratio"], al["n"], al["ratio"], _pf(al["p"]))))
if "beachday" in D:
    h, c, su, ns = D["beachday"]["hot"]["all"], D["beachday"]["calm"]["all"], D["beachday"]["big_waves"]["surfers"], D["beachday"]["big_waves"]["not_surfing"]
    for m in find("C18 beach weather", r"(\d+) of (\d+) bites \((\d+)%\) came on a day in the hottest quarter for the place and season, and (\d+) \((\d+)%\) in the calmest, against 25% by chance \(" + P + " and " + P + r"\)\. Big surf: (\d+)% of surfers' bites came on the biggest-wave quarter of days and (\d+)% of everyone else's"):
        check("C18 beach weather", m.groups(), tuple(str(x) for x in (h["k"], h["n"], h["pct"], c["k"], c["pct"], _pf(h["p"]), _pf(c["p"]), su["pct"], ns["pct"])))
if "whales" in D:
    w = D["whales"]
    for m in find("C5 humpbacks", r"([\d,]+) humpback whale records on OBIS ?peak in .*? (\d+) of (\d+) NSW white shark bites since 1980 \((\d+)%\) came in those months, against (\d+) of (\d+) bull, tiger and whaler shark bites \((\d+)%; " + P + r"\)"):
        check("C5 humpbacks", m.groups(), tuple(str(x) for x in (f"{w['humpback_records']:,}", w["white_in"], w["white_n"], w["white_pct"], w["other_in"], w["other_n"], w["other_pct"], _pf(w["p"]))))
if "chlorophyll" in D:
    c = D["chlorophyll"]
    for m in find("C4 chlorophyll", r"(\d+) of (\d+) Australian bites \((\d+)%\) came in a month in the greenest quarter for that place and time of year, against 25% by chance \(" + P + r"\); white sharks (\d+)%, bull sharks (\d+)%"):
        check("C4 chlorophyll", m.groups(), tuple(str(x) for x in (c["all"]["greenest_quarter"], c["all"]["n"], c["all"]["pct"], _pf(c["all"]["p"]), c["white"]["pct"], c["bull"]["pct"])))
if "tides" in D:
    t = D["tides"]["all"]
    for m in find("C24 tides", r"Of (\d+) bites with a known time in California and Hawaii, (\d+)% came around low water, (\d+)% on the rising tide, (\d+)% around high water and (\d+)% on the falling tide, close to a quarter each \(" + P + r"\)"):
        check("C24 tides", m.groups(), tuple(str(x) for x in (t["n"], *t["pct"], _pf(t["p"]))))

if "rivers" in D and "harbour" in D:
    b, w, t, hb = D["rivers"]["bull"], D["rivers"]["white"], D["rivers"]["tiger"], D["harbour"]
    for m in find("C6 rivers and harbour", r"of (\d+) NSW and Queensland bull shark bites since 1970 with a river gauge within 60 km, (\d+) \((\d+)%\) came in a month when nearby rivers ran in their highest quarter for the time of year, against 25% by chance and (\d+) of (\d+) white shark bites \((\d+)%\); using only the biggest river near each bite gives the same\. Tiger sharks lean toward high flow: (\d+) of (\d+) \((\d+)%\)\. Sydney Harbour, (\d+) tagged bull sharks: no more of them were around after the harbor tested dirtier than usual \(([\d.]+) times as many over the following fortnight, compared within the same month; " + P + r"\), and west of the Harbour Bridge they were picked up for fewer hours \(([\d.]+) times; " + P + r"\)"):
        check("C6 rivers and harbour", m.groups(), tuple(str(x) for x in (b["n"], b["high_quarter"], b["pct"], w["high_quarter"], w["n"], w["pct"], t["high_quarter"], t["n"], t["pct"],
              hb["animals"], hb["sharks"]["ratio"], _pf(hb["sharks"]["p"]), hb["hours_west"]["ratio"], _pf(hb["hours_west"]["p"]))))

if "tigerqld" in D and "tigerrain" in D:
    q, ta = D["tigerqld"], D["tigerrain"]["all"]["tiger"]
    for m in find("C6 Queensland bull catches", r"caught ([\d.]+) bull sharks a month in months when nearby rivers ran in their highest quarter for the time of year, against ([\d.]+) in other months of the same calendar month, place and five years: ([\d.]+) times as many \(" + P + r"\), and higher at 6 of 7 areas\. Tiger sharks didn't change \(([\d.]+) times; C28 ?\), nor did other sharks \(([\d.]+) times\)\. With (\d+) bull sharks caught"):
        check("C6 Queensland bull catches", m.groups(), tuple(str(x) for x in (f"{q['bull']['per_month_high']:.2f}", f"{q['bull']['per_month_other']:.2f}", q["bull"]["ratio"], _pf(q["bull"]["p"]),
              q["tiger"]["ratio"], q["other_sharks"]["ratio"], q["bull"]["caught_high"] + q["bull"]["caught_other"])))
    for m in find("C28 tiger sharks", r"By the day, (\d+) of (\d+) tiger shark bites in Hawaii, Réunion and New Caledonia followed a 3-day spell in the wettest quarter for the place and season, the quarter chance gives \(" + P + r"\)\. And Queensland's shark-control gear, Gold Coast to Bundaberg since 1996, caught tiger sharks at the same rate in high-river months as in others \(([\d.]+) against ([\d.]+) a month; ([\d.]+) times, " + P + r"\)"):
        check("C28 tiger sharks", m.groups(), tuple(str(x) for x in (ta["wettest_quarter"], ta["n"], _pf(ta["p"]), f"{q['tiger']['per_month_high']:.2f}", f"{q['tiger']['per_month_other']:.2f}", q["tiger"]["ratio"], _pf(q["tiger"]["p"]))))

if "whitecool" in D:
    w = D["whitecool"]
    for m in find("C5 Queensland white catches", r"caught (\d+) white sharks from May to November between 1996 and 2025\. East Australian humpbacks grew roughly tenfold over those years, but white shark catches didn't \(([-\d.]+)% a year, " + P + r"; (\d+) in the first fifteen years, (\d+) in the next\)\. Nor did cooler-than-usual months catch more \(([\d.]+) against ([\d.]+) a month in warmer ones, compared within the same calendar month; ([\d.]+) times, " + P + r"\)"):
        check("C5 Queensland white catches", m.groups(), tuple(str(x) for x in (w["total"], w["trend_pct_per_year"], _pf(w["trend_p"]), w["first_half"], w["second_half"],
              f"{w['cooler']['per_month']:.3f}", f"{w['warmer']['per_month']:.3f}", w["cool_ratio"], _pf(w["cool_p"]))))

if "upwelling" in D:
    u = D["upwelling"]
    for m in find("C29 upwelling", r"Of (\d+) California white shark incidents since 1988, (\d+) \((\d+)%\) followed a week in the strongest-upwelling quarter for the latitude and season, below the quarter chance gives; (\d+) \((\d+)%\) followed the weakest \(" + P + r"\)"):
        check("C29 upwelling", m.groups(), tuple(str(x) for x in (u["n"], u["strongest_quarter"], u["strongest_pct"], u["weakest_quarter"], u["weakest_pct"], _pf(u["p_weak"]))))

# Claim C23 (california19.py), when present
if "california" in D:
    ca = D["california"]; e0, e3, t = ca["eras"][0], ca["eras"][-1], ca["test"]
    for m in find("C23", r"Of (\d+) white shark incidents in California from (\d+) to (\d+), (\d+) were south of Point Conception, against (\d+) of (\d+) in (\d+)–(\d+)\. The median latitude moved from ([\d.]+)°N in (\d+)–(\d+) to ([\d.]+)°N since 2014, about (\d+) km south \(p = ([\d.]+)\)"):
        check("C23 California", (int(m[1]), int(m[2]), int(m[3]), int(m[4]), int(m[5]), int(m[6]), int(m[7]), int(m[8]), float(m[9]), int(m[10]), int(m[11]), float(m[12]), int(m[13]), float(m[14])),
              (e3["n"], e3["era"][0], e3["era"][1], e3["south"], e0["south"], e0["n"], e0["era"][0], e0["era"][1], t["pre_lat"], t["pre"][0], t["pre"][1], t["post_lat"], abs(t["shift_km"]), t["p"]))
    if t["shift_km"] >= 0: bad.append("C23: the page says incidents moved south, but the data now shows a northward shift")

# Claim C7 (leeuwin19.py), when present
if "leeuwin" in D:
    lw = D["leeuwin"]
    for m in find("C7 current", r"Western Australia has (\d+) recorded unprovoked bull shark bites since 1900, (\d+) of them since 2020\..*?to (\w+) (\d{4})\)\. (\d+) of the (\d+) recent bites can be checked.*?(\d+) of the (\d+) came in stronger-than-usual months, which could still be chance \(p = ([\d.]+)\)"):
        mon = ["January","February","March","April","May","June","July","August","September","October","November","December"]
        check("C7 warm current", (int(m[1]), int(m[2]), f"{m[4]}-{mon.index(m[3]) + 1:02d}", int(m[5]), int(m[6]), int(m[7]), int(m[8]), float(m[9])),
              (lw["n"], lw["since2020"], lw["last"], lw["checked"], lw["since2020"], lw["strong"], lw["checked"], lw["p"]))

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
                       ("claims", r"Pick one of (\d+) claims", cards),
                       ("early results", r"Early results (\d+)", early)):
    for m in find(lab, pat, True): check(f"number of {lab} ('{m[0]}')", int(m[1]), want)
# Every claim card names the decision it informs
for c in re.finditer(r'<article class="claim" id="(c\d+)"([\s\S]*?)</article>', page):
    check(f"{c[1].upper()} has a 'Decision it informs' line", "<dt>Decision it informs</dt>" in c[2], True)
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
