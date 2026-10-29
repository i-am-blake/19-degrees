"""Export the 19 Degrees data as open files and build the printable classroom sheet.
Usage: python3 -I export19.py <19-degrees.html> <out_dir>
Writes <out_dir>/data/*.csv and 19-degrees-data.json, and <out_dir>/classroom.html."""
import sys, re, json, csv, os
page, out = sys.argv[1:3]
d = json.loads(re.search(r'id="n19-data">(.*?)</script>', open(page).read(), re.S).group(1))
dd = os.path.join(out, "data"); os.makedirs(dd, exist_ok=True)
keep = {k: v for k, v in d.items() if k not in ("coast", "sharks")}
json.dump(keep, open(os.path.join(dd, "19-degrees-data.json"), "w"), indent=1)

def w(name, header, rows):
    with open(os.path.join(dd, name), "w", newline="") as f:
        c = csv.writer(f); c.writerow(header); c.writerows(rows)

w("bite-temperatures.csv", ["species", "sea_temp_c"],
  [[sp, t] for sp, s in d["species"].items() for t in s["t"]])
w("bite-temperature-summary.csv", ["species", "set", "bites", "below_19c", "min_c", "median_c", "max_c"],
  [[sp, lab, x["n"], x["below"], x["min"], x["median"], x["max"]] for sp, s in d["species"].items() for lab, x in (("all", s), ("confirmed", s["conf"]))])
w("beach-seasons-by-decade.csv", ["beach", "coast", "decade", "years", "months_at_or_above_19c"] + [f"share_{m}" for m in ("jan","feb","mar","apr","may","jun","jul","aug","sep","oct","nov","dec")],
  [[b["name"], b["coast"], r["decade"], r["years"], r["months"]] + r["share"] for b in d["beaches"] for r in b["rows"]])
w("beach-outlook-2050.csv", ["beach", "coast", "trend_c_per_decade_1980_2025", "months_at_or_above_19c_now", "months_2050_at_recent_pace"],
  [[b["name"], b["coast"], b["trend"], b["months_now"], b["months_2050"]] for b in d["beaches"]])
w("bull-bites-open-coast.csv", ["area", "set", "era_start", "era_end", "bites", "open_coast_bites"],
  [[a, "confirmed" if k.endswith("_conf") else "all", e[0], e[1], v[0], v[1]]
   for k, a in (("aus", "Australia"), ("nsw_south", "NSW south of Port Macquarie"), ("aus_conf", "Australia"), ("nsw_south_conf", "NSW south of Port Macquarie"))
   for e, v in zip(d["bull_open"]["eras"], d["bull_open"][k]["eras"])])
w("bull-bites-by-decade.csv", ["area", "decade", "bites", "inshore_bites", "population_millions_mid_decade"],
  [[a, dec, v[0], v[1], d["pop_mid"].get(dec)] for a, t in d["bull_decades"].items() for dec, v in t.items()])
if d.get("enso"):
    E = d["enso"]
    w("bull-bites-enso.csv", ["coast", "phase", "months_since_1950", "bites", "bites_per_10_years_of_months"],
      [[c, p, E["months"][p], E[c]["counts"].get(p, 0), E[c]["per10y"][p]] for c in ("east", "west") for p in ("nina", "neutral", "nino")])
w("zones-by-era.csv", ["species", "era_start", "era_end", "bites", "north_lat_p90", "center_lat", "south_lat_p10", "line_19c_half_year_lat"],
  [[sp, z["era"][0], z["era"][1], z["n"], z["north"], z["mid"], z["south"], d["zones"]["line"][i]] for sp, zs in d["zones"]["species"].items() for i, z in enumerate(zs)])

syd = next(b for b in d["beaches"] if b["key"] == "sydney"); bull = d["species"]["bull"]
O = d["bull_open"]["aus"]["eras"]; A = d["ahead"]["east"]; sA = next(b for b in A["beaches"] if b["name"] == "Sydney")
rows = "".join(f'<tr><th>{r["decade"]}s</th><td><span class="b" style="width:{r["months"]/12*100:.0f}%"></span></td><td>{r["months"]:.1f}</td></tr>' for r in syd["rows"])
open(os.path.join(out, "classroom.html"), "w").write(f"""<!doctype html><html lang="en-US"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>19 Degrees classroom sheet</title><style>
:root{{--ink:#10212B;--muted:#4A6170;--warm:#D9822B;--rule:#C9D6DD}}
body{{margin:0;background:#fff;color:var(--ink);font:16px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif;padding:24px 16px}}
.wrap{{max-width:760px;margin:0 auto}}h1{{font-size:30px;line-height:1.1;margin:0 0 6px}}h2{{font-size:19px;margin:22px 0 8px}}
.k{{font:12px ui-monospace,Menlo,monospace;letter-spacing:.12em;text-transform:uppercase;color:var(--muted)}}
table{{border-collapse:collapse;width:100%}}th,td{{padding:3px 6px;text-align:left;font-size:14px}}th{{width:70px;color:var(--muted);font-weight:500}}td:last-child{{width:50px;text-align:right}}
.b{{display:block;height:14px;background:var(--warm)}}ol li{{margin-bottom:12px}}.lines{{border-bottom:1px solid var(--rule);height:28px}}
dl{{display:grid;grid-template-columns:170px 1fr;gap:6px 14px}}dt{{font-weight:600}}dd{{margin:0}}
.ans{{border-top:2px dashed var(--rule);margin-top:26px;padding-top:10px;font-size:14px;color:var(--muted)}}
.print{{font:inherit;padding:8px 14px;border:1px solid var(--ink);background:#fff;cursor:pointer;min-height:44px}}
@media print{{.print{{display:none}}body{{padding:0}}}}@media (max-width:520px){{dl{{grid-template-columns:1fr}}}}
</style></head><body><div class="wrap">
<div class="k">19 Degrees · classroom sheet · ages 10 and up</div>
<h1>Sharks, warm water and a moving line</h1>
<p><button class="print" onclick="window.print()">Print this sheet</button></p>
<p>Bull sharks like warm water. Since 1900, Australia has recorded {bull['n']} bull shark bites, and <b>not one</b> happened in a month when the sea was cooler than 19°C (66°F). As the ocean warms, water that warm reaches further south and lasts longer each year.</p>
<h2>Chart: months a year the sea off Sydney is 19°C or warmer</h2>
<table>{rows}</table>
<h2>Fact: where bull sharks bite</h2>
<p>Before 1960, {O[0][1]} of {O[0][0]} bull shark bites were in coastal waters; most were in estuaries, harbors and rivers. Since 2015, {O[-1][1]} of {O[-1][0]} have been in coastal waters.</p>
<h2>Questions</h2>
<ol>
<li>Look at the chart. About how many months a year was the sea off Sydney 19°C or warmer in the 1900s? In the 2020s?<div class="lines"></div><div class="lines"></div></li>
<li>If bull sharks only visit when the water is 19°C or warmer, what happens to the number of months they can be near Sydney? Why might that matter to swimmers?<div class="lines"></div><div class="lines"></div></li>
<li>There are about 71% fewer oceanic sharks and rays than in 1970, but more bites near some beaches. Give two reasons that could both be true at once.<div class="lines"></div><div class="lines"></div></li>
<li>Bonus: About 49 people drown on Australia's coast for every person killed by a shark. What is one thing you can do to stay safe at the beach?<div class="lines"></div></li>
</ol>
<h2>Words</h2>
<dl><dt>Sea surface temperature</dt><dd>How warm the top of the sea is.</dd><dt>Estuary</dt><dd>Where a river meets the sea; the water is part fresh, part salty.</dd><dt>Range</dt><dd>Where an animal can live.</dd><dt>Season</dt><dd>The part of the year an animal is in a place.</dd><dt>Marine heatwave</dt><dd>Days when the sea is much warmer than usual.</dd></dl>
<div class="ans"><b>Answer guide.</b> 1: about {syd['rows'][0]['months']:.0f} months in the 1900s and about {syd['rows'][-1]['months']:.0f} in the 2020s. 2: more months, so bull sharks can stay longer each year, and swimmers share the water with them for more of the year. 3: sharks are in different places and seasons as warm water spreads; more people swim; heavy rain and murky water bring sharks close to beaches. 4: swim between the red and yellow flags, where lifesavers watch.
<br><br>Data: Australian Shark-Incident Database (Taronga Conservation Society and Flinders University); HadISST sea temperature (UK Met Office); Pacoureau et al. 2021; Surf Life Saving Australia. Full sources and methods are on the 19 Degrees page.</div>
</div></body></html>""")
# data dictionary: one row per column in every CSV
DICT = [
 ("bite-temperatures.csv","species","Shark species: bull, tiger or white"),
 ("bite-temperatures.csv","sea_temp_c","HadISST monthly sea surface temperature (°C) in the bite month for the 1° square nearest the bite; an open-sea monthly average, not the water at the beach that day"),
 ("bite-temperature-summary.csv","species","Shark species"),
 ("bite-temperature-summary.csv","set","all = every bite with a known month and place; confirmed = species identified by physical evidence (bite analysis, tooth, DNA, photo or video)"),
 ("bite-temperature-summary.csv","bites","Number of bites in the set"),
 ("bite-temperature-summary.csv","below_19c","Bites in months when sea_temp_c was below 19.0"),
 ("bite-temperature-summary.csv","min_c / median_c / max_c","Coolest, median and warmest sea temperature at those bites (°C)"),
 ("beach-seasons-by-decade.csv","beach / coast","Reference beach and coast (east or west)"),
 ("beach-seasons-by-decade.csv","decade","First year of the decade"),
 ("beach-seasons-by-decade.csv","years","Years of data in that decade"),
 ("beach-seasons-by-decade.csv","months_at_or_above_19c","Average number of months a year the sea averaged 19°C or more"),
 ("beach-seasons-by-decade.csv","share_jan ... share_dec","Share of years in the decade that month averaged 19°C or more (0 to 1)"),
 ("beach-outlook-2050.csv","trend_c_per_decade_1980_2025","Linear warming trend of the beach's sea temperature, 1980 to 2025 (°C a decade)"),
 ("beach-outlook-2050.csv","months_at_or_above_19c_now","Average months a year at 19°C or more, last 10 years"),
 ("beach-outlook-2050.csv","months_2050_at_recent_pace","Same, if the 1980–2025 trend continues to about 2050; an extrapolation, not a climate model"),
 ("bull-bites-by-decade.csv","area","nsw_south = NSW coast south of Port Macquarie; wa = Western Australia"),
 ("bull-bites-by-decade.csv","bites / inshore_bites","Bull shark bites, and those in a river, estuary, harbour or lake"),
 ("bull-bites-by-decade.csv","population_millions_mid_decade","Australia's population in millions, middle of the decade (ABS)"),
 ("bull-bites-open-coast.csv","area / set","Region, and all or confirmed-evidence bites (see bite-temperature-summary.csv)"),
 ("bull-bites-open-coast.csv","era_start / era_end","Years covered (inclusive)"),
 ("bull-bites-open-coast.csv","bites / open_coast_bites","Bull shark bites, and those in coastal waters (mostly surf beaches) rather than estuaries, harbors, rivers or lakes"),
 ("bull-bites-enso.csv","coast / phase","East or west coast; El Niño, La Niña or neutral month (Niño 3.4 index from HadISST, 3-month mean, ±0.5°C)"),
 ("bull-bites-enso.csv","months_since_1950 / bites / bites_per_10_years_of_months","Months in that phase since 1950, bull shark bites in them, and bites per 120 such months"),
 ("zones-by-era.csv","north_lat_p90 / center_lat / south_lat_p10","Latitude (negative = south) of the northern edge, middle and southern edge of where bites happened in that era"),
 ("zones-by-era.csv","line_19c_half_year_lat","Latitude where the sea is 19°C or more for at least half the year, averaged over the era"),
]
with open(os.path.join(dd, "data-dictionary.csv"), "w", newline="") as f:
    c = csv.writer(f); c.writerow(["file", "column", "meaning"]); c.writerows(DICT)
print("exported", sorted(os.listdir(dd)), "and classroom.html")
