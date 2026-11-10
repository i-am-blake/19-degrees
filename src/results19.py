"""Writes the result sentences that come from the monthly-refreshed tests, from the data, at build time.
build19.py calls fill(html, D) after loading the results, so a new OBIS download or a new Hawaii incident updates the page
text instead of blocking the weekly publish. check19.py then checks the same sentences against the data as before.
Each paragraph is replaced whole (by its id); two Hawaii sentences inside older paragraphs are replaced in place."""
import re

def pf(p):
    return "p &lt; 0.001" if p < 0.001 else f"p = {p:.3f}" if p < 0.01 else f"p = {p:.2f}"

A = lambda url, text: f'<a href="{url}" target="_blank" rel="noopener">{text}</a>'
QLD = A("https://www.data.qld.gov.au/dataset/fisheries-queensland-s-shark-control-program-information-and-data", "Queensland Shark Control Program")
WDO = A("https://www.bom.gov.au/waterdata/", "Water Data Online")
HDL = A("https://dlnr.hawaii.gov/sharks/shark-incidents/incidents/", "Hawaii DLNR")
MON = "January February March April May June July August September October November December".split()

def mhwC19(D):
    M = D["mhw"]; c, h, ht, ib, it, a = M["california_white"], M["hawaii_all"], M["hawaii_tiger"], M["islands_bull"], M["islands_tiger"], M["all"]
    return ('Early result, by day, on the coasts that record the date of each bite: no clear link with '
            + A("https://www.ncei.noaa.gov/products/optimum-interpolation-sst", "marine heatwaves") + ' yet. '
            f'California\'s white shark bites lean that way, {c["in_heatwave"]} of {c["n"]} ({c["pct"]}%) during a heatwave against {c["expected_pct"]}% expected for the same place and time of year (p = {c["p"]:.2f}), '
            f'and so do Hawaii\'s, {h["in_heatwave"]} of {h["n"]} ({h["pct"]}% against {h["expected_pct"]}%; p = {h["p"]:.2f}), tiger sharks {ht["in_heatwave"]} of {ht["n"]}. '
            f'Bull and tiger shark bites at Réunion and New Caledonia didn\'t ({ib["in_heatwave"]} of {ib["n"]} and {it["in_heatwave"]} of {it["n"]}). '
            f'All together, {a["in_heatwave"]} of {a["n"]} ({a["pct"]}% against {a["expected_pct"]}%; p = {a["p"]:.2f}).')

def bwC6(D):
    b, w = D["beachwatch"]["bull"], D["beachwatch"]["white"]
    return ('Early result, beach water quality: near beaches tested by ' + A("https://www.beachwatch.nsw.gov.au/", "Beachwatch")
            + ', which measures the gut bacteria that stormwater and sewage overflow wash in after rain, '
            f'{b["dirtiest_quarter"]} of {b["n"]} NSW bull shark bites since 1992 came in months when that water was in its dirtiest quarter for the time of year (p = {b["p"]}), against {w["dirtiest_quarter"]} of {w["n"]} white shark bites. '
            'Small numbers, and the link fades for beaches more than 5 km from the bite.')

def plumeC6(D):
    rv, hb = D["rivers"], D["harbour"]; b, w, t = rv["bull"], rv["white"], rv["tiger"]; hs, hw = hb["sharks"], hb["hours_west"]
    return (f'Early result, testing the plume idea two more ways: neither backs it up. Rivers: of {b["n"]} NSW and Queensland bull shark bites since 1970 with a river gauge within 60 km, '
            f'{b["high_quarter"]} ({b["pct"]}%) came in a month when nearby rivers ran in their highest quarter for the time of year, against 25% by chance and {w["high_quarter"]} of {w["n"]} white shark bites ({w["pct"]}%); '
            f'using only the biggest river near each bite gives the same. Tiger sharks lean toward high flow: {t["high_quarter"]} of {t["n"]} ({t["pct"]}%). '
            f'Sydney Harbour, {hb["animals"]} tagged bull sharks: no more of them were around after the harbor tested dirtier than usual ({hs["ratio"]} times as many over the following fortnight, compared within the same month; {pf(hs["p"])}), '
            f'and west of the Harbour Bridge they were picked up for fewer hours ({hw["ratio"]} times; {pf(hw["p"])}), though stormy water also shortens how far receivers can hear a tag. '
            '(River flow: ' + WDO + '; tags: IMOS; water: Harbourwatch.)')

def qldC6(D):
    q = D["tigerqld"]; qb, qt, qo = q["bull"], q["tiger"], q["other_sharks"]
    return ('Early result, from the sharks\' side: when rivers run high, bull sharks come to the beaches. Queensland\'s shark-control gear from the Gold Coast to Bundaberg caught '
            f'{qb["per_month_high"]:.2f} bull sharks a month in months when nearby rivers ran in their highest quarter for the time of year, against {qb["per_month_other"]:.2f} in other months of the same calendar month, place and five years: '
            f'{qb["ratio"]} times as many ({pf(qb["p"])}), and higher at 6 of 7 areas. Tiger sharks didn\'t change ({qt["ratio"]} times; <a href="#c28">C28</a>), nor did other sharks ({qo["ratio"]} times). '
            f'With {qb["caught_high"] + qb["caught_other"]} bull sharks caught, this says far more than the bite tests above can. ({QLD}; {WDO}.)')

def wkC18(D):
    w = D["exposure"]["weekend"]; ca, nc, hi, al = w["california"], w["new_caledonia"], w["hawaii"], w["all"]
    b = D["beachday"]; h, c, su, ns = b["hot"]["all"], b["calm"]["all"], b["big_waves"]["surfers"], b["big_waves"]["not_surfing"]
    return (f'Early result, by day: bites follow people. In California, {ca["busy"]} of {ca["n"]} bites ({ca["pct"]}%) fell on a weekend, which is {ca["expected_pct"]}% of days: '
            f'{ca["ratio"]} times as many bites per weekend day as per weekday ({pf(ca["p"])}). New Caledonia shows the same ({nc["busy"]} of {nc["n"]}, {nc["ratio"]} times; {pf(nc["p"])}); '
            f'Hawaii, where locals surf every day, doesn\'t ({hi["busy"]} of {hi["n"]}, {hi["ratio"]} times). All {al["n"]} day-dated bites: {al["ratio"]} times ({pf(al["p"])}). Sharks don\'t keep a calendar, so this is people, not sharks.'
            ' Beach weather on the day (' + A("https://open-meteo.com/", "Open-Meteo") + ' historical weather and waves) points the same way, faintly: '
            f'{h["k"]} of {h["n"]} bites ({h["pct"]}%) came on a day in the hottest quarter for the place and season, '
            f'and {c["k"]} ({c["pct"]}%) in the calmest, against 25% by chance ({pf(h["p"])} and {pf(c["p"])}). Big surf: {su["pct"]}% of surfers\' bites came on the biggest-wave quarter of days and {ns["pct"]}% of everyone else\'s, as you\'d expect if bites follow who is in the water.')

def whaleC5(D):
    w = D["whales"]; mm = w["migration_months"]
    months = ", ".join(MON[m - 1] for m in mm[:-1]) + " and " + MON[mm[-1] - 1]
    return (f'Early result: leans that way, not settled. Off NSW, {w["humpback_records"]:,} humpback whale records on ' + A("https://obis.org", "OBIS") + f' peak in {months}. '
            f'{w["white_in"]} of {w["white_n"]} NSW white shark bites since 1980 ({w["white_pct"]}%) came in those months, against {w["other_in"]} of {w["other_n"]} bull, tiger and whaler shark bites ({w["other_pct"]}%; {pf(w["p"])}). '
            'Comparing species keeps the season\'s beach crowds out of it. Whale records also depend on when people look.')

def whitecoolC5(D):
    w = D["whitecool"]
    return ('Early result, from the sharks\' side: the whales\' calendar, not their numbers. Queensland\'s shark-control gear, Gold Coast to Bundaberg, '
            f'caught {w["total"]} white sharks from May to November between 1996 and 2025. '
            f'East Australian humpbacks grew roughly tenfold over those years, but white shark catches didn\'t ({w["trend_pct_per_year"]}% a year, {pf(w["trend_p"])}; {w["first_half"]} in the first fifteen years, {w["second_half"]} in the next). '
            f'Nor did cooler-than-usual months catch more ({w["cooler"]["per_month"]:.3f} against {w["warmer"]["per_month"]:.3f} a month in warmer ones, compared within the same calendar month; {w["cool_ratio"]} times, {pf(w["cool_p"])}). '
            f'White sharks pass on a fixed winter calendar that overlaps the whales\'; neither the whales\' numbers nor the cold drives it. ({QLD}; HadISST.)')

def chlC4(D):
    c = D["chlorophyll"]
    return ('First look: no clear link with greener water. NASA ' + A("https://oceancolor.gsfc.nasa.gov/", "MODIS") + ' chlorophyll (plankton, the base of the baitfish food chain), 2003 to 2022: '
            f'{c["all"]["greenest_quarter"]} of {c["all"]["n"]} Australian bites ({c["all"]["pct"]}%) came in a month in the greenest quarter for that place and time of year, against 25% by chance ({pf(c["all"]["p"])}); '
            f'white sharks {c["white"]["pct"]}%, bull sharks {c["bull"]["pct"]}%. Monthly satellite averages may be too coarse to see a bait run.')

def tideC24(D):
    t = D["tides"]["all"]
    return (f'Tides, the other thing the moon drives: no effect either. Of {t["n"]} bites with a known time in California and Hawaii, {t["pct"][0]}% came around low water, {t["pct"][1]}% on the rising tide, '
            f'{t["pct"][2]}% around high water and {t["pct"][3]}% on the falling tide, close to a quarter each ({pf(t["p"])}). (' + A("https://tidesandcurrents.noaa.gov/", "NOAA") + ' tide predictions.)')

def tigerC28(D):
    q, ta = D["tigerqld"]["tiger"], D["tigerrain"]["all"]["tiger"]
    return ('Early result: not supported so far. A 2019 Australian study found tiger shark bite risk rose with rainfall, and this page\'s monthly rain test leaned the same way (<a href="#c6">C6</a>). '
            f'Two stronger tests don\'t. By the day, {ta["wettest_quarter"]} of {ta["n"]} tiger shark bites in Hawaii, Réunion and New Caledonia followed a 3-day spell in the wettest quarter for the place and season, the quarter chance gives ({pf(ta["p"])}). '
            f'And Queensland\'s shark-control gear, Gold Coast to Bundaberg since 1996, caught tiger sharks at the same rate in high-river months as in others ({q["per_month_high"]:.2f} against {q["per_month_other"]:.2f} a month; {q["ratio"]} times, {pf(q["p"])}), '
            'while bull shark catches more than doubled (<a href="#c6">C6</a>). (Rain: ' + A("https://open-meteo.com/", "Open-Meteo") + '; river flow: ' + WDO + '; catches: ' + QLD + '.)')

def upC29(D):
    u = D["upwelling"]
    return (f'Early result: not supported so far. Of {u["n"]} California white shark incidents since 1988, {u["strongest_quarter"]} ({u["strongest_pct"]}%) followed a week in the strongest-upwelling quarter for the latitude and season, '
            f'below the quarter chance gives; {u["weakest_quarter"]} ({u["weakest_pct"]}%) followed the weakest ({pf(u["p_weak"])}). Ryan et al.\'s cooler-water finding came from Australia and compared places, not days, so this doesn\'t rule it out there. '
            '(' + A("https://upwell.pfeg.noaa.gov/erddap/info/erdCUTIdaily/index.html", "NOAA upwelling index") + '; California Department of Fish and Wildlife.)')

PARAS = {"mhwC19": (mhwC19, ("mhw",)), "bwC6": (bwC6, ("beachwatch",)), "plumeC6": (plumeC6, ("rivers", "harbour")),
         "qldC6": (qldC6, ("tigerqld",)), "wkC18": (wkC18, ("exposure", "beachday")), "whaleC5": (whaleC5, ("whales",)),
         "whitecoolC5": (whitecoolC5, ("whitecool",)), "chlC4": (chlC4, ("chlorophyll",)), "tideC24": (tideC24, ("tides",)),
         "tigerC28": (tigerC28, ("tigerqld", "tigerrain")), "upC29": (upC29, ("upwelling",))}

def hawaiiC6(D):
    h = D["hawaii"]
    return (f'Hawaii ({h["first"]}–{h["last"]}): the water was turbid or muddy at {h["tiger_murky_pct"]}% of tiger shark bites ({h["tiger_murky"]} of {h["tiger_clarity_n"]}) '
            f'and {h["other_murky_pct"]}% of bites by other identified sharks ({h["other_murky"]} of {h["other_clarity_n"]}; p = {h["p_murky"]:.2f}), so murky water isn\'t special to tiger sharks there.')

def hawaiiC24(D):
    a, t = D["lunar"]["hawaii_all"], D["lunar"]["hawaii_tiger"]
    return f'Hawaii agrees: {a["near"]} of {a["n"]} bites ({a["near_pct"]}%; p = {a["p"]:.2f}), and {t["near"]} of {t["n"]} tiger shark bites'

SENTENCES = [(re.compile(r"Hawaii \(\d{4}–\d{4}\): the water was turbid or muddy at .*?so murky water isn't special to tiger sharks there\."), hawaiiC6, ("hawaii",)),
             (re.compile(r"Hawaii agrees: \d+ of \d+ bites \(\d+%; p = [\d.]+\), and \d+ of \d+ tiger shark bites"), hawaiiC24, ("lunar",))]

def fill(html, D):
    for pid, (fn, need) in PARAS.items():
        if all(k in D for k in need):
            html = re.sub(rf'(<p class="agres" id="{pid}">).*?(</p>)', lambda m: m.group(1) + fn(D) + m.group(2), html, count=1, flags=re.S)
    for pat, fn, need in SENTENCES:
        if all(k in D for k in need) and (need != ("lunar",) or "hawaii_all" in D["lunar"]):
            html = pat.sub(lambda m: fn(D), html, count=1)
    return html
