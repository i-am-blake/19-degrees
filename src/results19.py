"""Writes the result sentences that come from the monthly-refreshed tests, from the data, at build time.
build19.py calls fill(html, D) after loading the results, so a new OBIS download or a new Hawaii incident updates the page
text instead of blocking the weekly publish. check19.py then checks the same sentences against the data as before.
Each paragraph is replaced whole (by its id); two Hawaii sentences inside older paragraphs are replaced in place."""
import re
import grades19 as G
import explain19 as X

def pf(p):
    return "p &lt; 0.001" if p < 0.001 else f"p = {p:.3f}" if p < 0.01 else f"p = {p:.2f}"

A = lambda url, text: f'<a href="{url}" target="_blank" rel="noopener">{text}</a>'
QLD = A("https://www.data.qld.gov.au/dataset/fisheries-queensland-s-shark-control-program-information-and-data", "Queensland Shark Control Program")
WDO = A("https://www.bom.gov.au/waterdata/", "Water Data Online")
HDL = A("https://dlnr.hawaii.gov/sharks/shark-incidents/incidents/", "Hawaii DLNR")
MON = "January February March April May June July August September October November December".split()

sig = lambda x, k="p": x[k] is not None and x[k] < 0.05

def mhwC19(D):
    M = D["mhw"]; c, h, ht, ib, it, a = M["california_white"], M["hawaii_all"], M["hawaii_tiger"], M["islands_bull"], M["islands_tiger"], M["all"]
    up = lambda x: x["pct"] > x["expected_pct"]
    def d(x):
        if sig(x): return "are more common during heatwaves" if up(x) else "are less common during heatwaves"
        return "lean that way" if up(x) else "lean the other way" if x["pct"] < x["expected_pct"] else "show no difference"
    link = A("https://www.ncei.noaa.gov/products/optimum-interpolation-sst", "marine heatwaves")
    lead = {"supports": f"bites are more common during {link}.", "leans": f"bites lean toward {link}, not settled.",
            "none": f"no clear link with {link} yet.", "other": f"bites are less common during {link}."}[G.V(up(a), a["p"])]
    dc, dh = d(c), d(h)
    haw = (f'and so {"are" if dc.startswith("are") else "do"} Hawaii\'s' if dh == dc else f"while Hawaii's {dh}")
    if not up(ib) and not up(it):
        isl = "didn't" if up(c) else "weren't more common during heatwaves either"
    elif up(ib) and up(it): isl = "lean toward heatwaves" + (" too" if up(c) else "")
    else: isl = "were mixed"
    return (f'Early result, by day, on the coasts that record the date of each bite: {lead} '
            f'California\'s white shark bites {dc}, {c["in_heatwave"]} of {c["n"]} ({c["pct"]}%) during a heatwave against {c["expected_pct"]}% expected for the same place and time of year (p = {c["p"]:.2f}), '
            f'{haw}, {h["in_heatwave"]} of {h["n"]} ({h["pct"]}% against {h["expected_pct"]}%; p = {h["p"]:.2f}), tiger sharks {ht["in_heatwave"]} of {ht["n"]}. '
            f'Bull and tiger shark bites at Réunion and New Caledonia {isl} ({ib["in_heatwave"]} of {ib["n"]} and {it["in_heatwave"]} of {it["n"]}). '
            f'All together, {a["in_heatwave"]} of {a["n"]} ({a["pct"]}% against {a["expected_pct"]}%; p = {a["p"]:.2f}).')

def bwC6(D):
    b, w = D["beachwatch"]["bull"], D["beachwatch"]["white"]
    end = "Small numbers, so this is a lead, not a finding." if sig(b) and b["pct"] > 25 else "Small numbers, and no clear link so far."
    return ('Early result, beach water quality: near beaches tested by ' + A("https://www.beachwatch.nsw.gov.au/", "Beachwatch")
            + ', which measures the gut bacteria that stormwater and sewage overflow wash in after rain, '
            f'{b["dirtiest_quarter"]} of {b["n"]} NSW bull shark bites since 1992 came in months when that water was in its dirtiest quarter for the time of year (p = {b["p"]}), against {w["dirtiest_quarter"]} of {w["n"]} white shark bites. '
            + end)

def plumeC6(D):
    rv, hb = D["rivers"], D["harbour"]; b, w, t = rv["bull"], rv["white"], rv["tiger"]; hs, hw = hb["sharks"], hb["hours_west"]
    r_ok = sig(b) and b["pct"] > 25; h_ok = sig(hs) and hs["ratio"] > 1
    lead = "both back it up." if r_ok and h_ok else "one backs it up." if r_ok or h_ok else "neither backs it up."
    tl = "come with high flow" if sig(t) and t["pct"] > 25 else "lean toward high flow" if t["pct"] > 25 else "don't lean toward high flow either"
    hsx = ("more of them were around" if hs["ratio"] > 1 else "fewer of them were around") if sig(hs) else "no more of them were around"
    hwx = ("fewer hours" if hw["ratio"] < 1 else "more hours" if hw["ratio"] > 1 else "about the same hours")
    return (f'Early result, testing the plume idea two more ways: {lead} Rivers: of {b["n"]} NSW and Queensland bull shark bites since 1970 with a river gauge within 60 km, '
            f'{b["high_quarter"]} ({b["pct"]}%) came in a month when nearby rivers ran in their highest quarter for the time of year, against 25% by chance and {w["high_quarter"]} of {w["n"]} white shark bites ({w["pct"]}%). '
            f'Tiger sharks {tl}: {t["high_quarter"]} of {t["n"]} ({t["pct"]}%). '
            f'Sydney Harbour, {hb["animals"]} tagged bull sharks: {hsx} after the harbor tested dirtier than usual ({hs["ratio"]} times as many over the following fortnight, compared within the same month; {pf(hs["p"])}), '
            f'and west of the Harbour Bridge they were picked up for {hwx} ({hw["ratio"]} times; {pf(hw["p"])})'
            + (", though stormy water also shortens how far receivers can hear a tag. " if hw["ratio"] < 1 else ". ")
            + '(River flow: ' + WDO + '; tags: IMOS; water: Harbourwatch.)')

def qldC6(D):
    q = D["tigerqld"]; qb, qt, qo = q["bull"], q["tiger"], q["other_sharks"]
    lead = (("when rivers run high, bull sharks come to the beaches." if qb["ratio"] > 1 else "when rivers run high, fewer bull sharks are caught.")
            if sig(qb) else "no clear change in bull sharks when rivers run high.")
    areas = f', and higher at {qb["areas_higher"]} of {qb["areas_tested"]} areas' if "areas_higher" in qb else ""
    ch = lambda x: f'changed ({x["ratio"]} times, {pf(x["p"])}' if sig(x) else f"didn't change ({x['ratio']} times"
    if not sig(qt) and not sig(qo):
        rest = f'Tiger sharks didn\'t change ({qt["ratio"]} times; <a href="#c28">C28</a>), nor did other sharks ({qo["ratio"]} times).'
    else:
        rest = f'Tiger sharks {ch(qt)}; <a href="#c28">C28</a>); other sharks {ch(qo)}).'
    return ('Early result, from the sharks\' side: ' + lead + ' Queensland\'s shark-control gear from the Gold Coast to Bundaberg caught '
            f'{qb["per_month_high"]:.2f} bull sharks a month in months when nearby rivers ran in their highest quarter for the time of year, against {qb["per_month_other"]:.2f} in other months of the same calendar month, place and five years: '
            f'{qb["ratio"]} times as many ({pf(qb["p"])}){areas}. {rest} '
            f'With {qb["caught_high"] + qb["caught_other"]} bull sharks caught, this says far more than the bite tests above can. ({QLD}; {WDO}.)')

def wkC18(D):
    w = D["exposure"]["weekend"]; ca, nc, hi, al = w["california"], w["new_caledonia"], w["hawaii"], w["all"]
    b = D["beachday"]; h, c, su, ns = b["hot"]["all"], b["calm"]["all"], b["big_waves"]["surfers"], b["big_waves"]["not_surfing"]
    more = lambda x: sig(x) and x["ratio"] > 1
    people = more(al)
    lead = "bites follow people." if people else "no clear weekend effect."
    ncx = "New Caledonia shows the same" if more(nc) else "New Caledonia doesn't"
    hix = "Hawaii shows it too" if more(hi) else "Hawaii, where locals surf every day, doesn't"
    wx = (("points the same way, faintly" if people else "leans toward busy beach days, faintly") if h["pct"] > 25 and c["pct"] > 25
          else "doesn't point the same way")
    return (f'Early result, by day: {lead} In California, {ca["busy"]} of {ca["n"]} bites ({ca["pct"]}%) fell on a weekend, which is {ca["expected_pct"]}% of days: '
            f'{ca["ratio"]} times as many bites per weekend day as per weekday ({pf(ca["p"])}). {ncx} ({nc["busy"]} of {nc["n"]}, {nc["ratio"]} times; {pf(nc["p"])}); '
            f'{hix} ({hi["busy"]} of {hi["n"]}, {hi["ratio"]} times). All {al["n"]} day-dated bites: {al["ratio"]} times ({pf(al["p"])}).'
            + (" Sharks don't keep a calendar, so this is people, not sharks." if people else "")
            + ' Beach weather on the day (' + A("https://open-meteo.com/", "Open-Meteo") + f' historical weather and waves) {wx}: '
            f'{h["k"]} of {h["n"]} bites ({h["pct"]}%) came on a day in the hottest quarter for the place and season, '
            f'and {c["k"]} ({c["pct"]}%) in the calmest, against 25% by chance ({pf(h["p"])} and {pf(c["p"])}). Big surf: {su["pct"]}% of surfers\' bites came on the biggest-wave quarter of days and {ns["pct"]}% of everyone else\'s'
            + (", as you'd expect if bites follow who is in the water." if su["pct"] > ns["pct"] else "."))

def whaleC5(D):
    w = D["whales"]; mm = w["migration_months"]
    months = ", ".join(MON[m - 1] for m in mm[:-1]) + " and " + MON[mm[-1] - 1]
    up = w["white_pct"] > w["other_pct"]
    lead = {"supports": "white shark bites follow the whale season.", "leans": "leans that way, not settled.",
            "none": "no clear link.", "other": "points the other way."}[G.V(up, w["p"])]
    return (f'Early result: {lead} Off NSW, {w["humpback_records"]:,} humpback whale records on ' + A("https://obis.org", "OBIS") + f' peak in {months}. '
            f'{w["white_in"]} of {w["white_n"]} NSW white shark bites since 1980 ({w["white_pct"]}%) came in those months, against {w["other_in"]} of {w["other_n"]} bull, tiger and whaler shark bites ({w["other_pct"]}%; {pf(w["p"])}). '
            'Comparing species keeps the season\'s beach crowds out of it. Whale records also depend on when people look.')

def whitecoolC5(D):
    w = D["whitecool"]
    grew = w["trend_p"] < 0.05 and w["trend_pct_per_year"] > 0; fell = w["trend_p"] < 0.05 and w["trend_pct_per_year"] < 0
    cool = w["cool_p"] < 0.05 and w["cool_ratio"] > 1; warm = w["cool_p"] < 0.05 and w["cool_ratio"] < 1
    lead = ("the whales' calendar, not their numbers." if not grew and not cool else "both the whales' numbers and cool water count." if grew and cool
            else "catches have grown with the whales." if grew else "cooler water brings more.")
    t = f'({w["trend_pct_per_year"]}% a year, {pf(w["trend_p"])}; {w["first_half"]} in the first fifteen years, {w["second_half"]} in the next)'
    s2 = f'and white shark catches grew too {t}' if grew else f'but white shark catches fell {t}' if fell else f"but white shark catches didn't {t}"
    k = f'({w["cooler"]["per_month"]:.3f} against {w["warmer"]["per_month"]:.3f} a month in warmer ones, compared within the same calendar month; {w["cool_ratio"]} times, {pf(w["cool_p"])})'
    s3 = (f"Cooler-than-usual months caught more {k}" if cool else f"Cooler-than-usual months caught fewer {k}" if warm
          else f"Nor did cooler-than-usual months catch more {k}" if not grew else f"Cooler-than-usual months didn't catch more {k}")
    end = " White sharks pass on a fixed winter calendar that overlaps the whales'; neither the whales' numbers nor the cold drives it." if not grew and not cool else ""
    return ('Early result, from the sharks\' side: ' + lead + ' Queensland\'s shark-control gear, Gold Coast to Bundaberg, '
            f'caught {w["total"]} white sharks from May to November between 1996 and 2025. '
            f'East Australian humpbacks grew roughly tenfold over those years, {s2}. {s3}.{end} ({QLD}; HadISST.)')

def chlC4(D):
    c = D["chlorophyll"]; a = c["all"]
    v = G.V(a["pct"] > 25, a["p"]); link = v == "supports"
    lead = {"supports": "bites follow greener water.", "leans": "bites lean toward greener water, not settled.",
            "none": "no clear link with greener water.", "other": "bites come in clearer water."}[v]
    return (f'Early result: {lead} NASA ' + A("https://oceancolor.gsfc.nasa.gov/", "MODIS") + ' chlorophyll (plankton, the base of the baitfish food chain), 2003 to 2022: '
            f'{a["greenest_quarter"]} of {a["n"]} Australian bites ({a["pct"]}%) came in a month in the greenest quarter for that place and time of year, against 25% by chance ({pf(a["p"])}); '
            f'white sharks {c["white"]["pct"]}%, bull sharks {c["bull"]["pct"]}%.' + (" Monthly satellite averages may be too coarse to see a bait run." if not link else ""))

def tideC24(D):
    t = D["tides"]["all"]
    lead = "bites aren't spread evenly." if sig(t) else "no effect either."
    return (f'Tides, the other thing the moon drives: {lead} Of {t["n"]} bites with a known time in California and Hawaii, {t["pct"][0]}% came around low water, {t["pct"][1]}% on the rising tide, '
            f'{t["pct"][2]}% around high water and {t["pct"][3]}% on the falling tide' + (", close to a quarter each" if not sig(t) else "")
            + f' ({pf(t["p"])}). (' + A("https://tidesandcurrents.noaa.gov/", "NOAA") + ' tide predictions.)')

def c28_ok(D):
    q, ta = D["tigerqld"]["tiger"], D["tigerrain"]["all"]["tiger"]
    return sig(ta) and ta["pct"] > 25, sig(q) and q["ratio"] > 1

def tigerC28(D):
    q, qb, ta = D["tigerqld"]["tiger"], D["tigerqld"]["bull"], D["tigerrain"]["all"]["tiger"]
    a, b = c28_ok(D)
    lead = {"supports": "supports it so far.", "leans": "leans toward it so far.", "none": "no clear link so far.", "other": "points the other way so far."}[G.g_c28(D)]
    tests = "Two stronger tests agree." if a and b else "Two stronger tests disagree." if a or b else "Two stronger tests don't."
    qx = ("the quarter chance gives" if not sig(ta) else "more than the quarter chance gives" if ta["pct"] > 25 else "fewer than the quarter chance gives")
    rate = ("at the same rate" if not sig(q) else "more often" if q["ratio"] > 1 else "less often")
    bull = ("while bull shark catches more than doubled" if sig(qb) and qb["ratio"] >= 2 else f'while bull shark catches rose {qb["ratio"]} times' if sig(qb) and qb["ratio"] > 1
            else f'and bull shark catches changed {qb["ratio"]} times')
    return ('Early result: ' + lead + ' A 2019 Australian study found tiger shark bite risk rose with rainfall, and this page\'s monthly rain test leaned the same way (<a href="#c6">C6</a>). '
            f'{tests} By the day, {ta["wettest_quarter"]} of {ta["n"]} tiger shark bites in Hawaii, Réunion and New Caledonia followed a 3-day spell in the wettest quarter for the place and season, {qx} ({pf(ta["p"])}). '
            f'And Queensland\'s shark-control gear, Gold Coast to Bundaberg since 1996, caught tiger sharks {rate} in high-river months as in others ({q["per_month_high"]:.2f} against {q["per_month_other"]:.2f} a month; {q["ratio"]} times, {pf(q["p"])}), '
            f'{bull} (<a href="#c6">C6</a>). (Rain: ' + A("https://open-meteo.com/", "Open-Meteo") + '; river flow: ' + WDO + '; catches: ' + QLD + '.)')

def upC29(D):
    u = D["upwelling"]; v = G.g_c29(D); p2 = G.binom2(u["strongest_quarter"], u["n"], 0.25)
    pos = "fewer than the quarter chance gives" if u["strongest_pct"] < 25 else "more than the quarter chance gives" if u["strongest_pct"] > 25 else "the quarter chance gives"
    lead = {"supports": "supports it so far.", "leans": "leans toward it so far.", "none": "no clear link so far.", "other": "points the other way."}[v]
    end = ("This agrees with Ryan et al.'s cooler-water finding from Australia. " if v == "supports" else
           "Ryan et al.'s cooler-water finding came from Australia and compared places, not days, so this doesn't rule it out there. ")
    return (f'Early result: {lead} Of {u["n"]} California white shark incidents since 1988, {u["strongest_quarter"]} ({u["strongest_pct"]}%) followed a week in the strongest-upwelling quarter for the latitude and season, '
            f'{pos} ({pf(p2)}); {u["weakest_quarter"]} ({u["weakest_pct"]}%) followed the weakest. ' + end
            + '(' + A("https://upwell.pfeg.noaa.gov/erddap/info/erdCUTIdaily/index.html", "NOAA upwelling index") + '; California Department of Fish and Wildlife.)')

def stationsC16(D):
    c = D["imos"]["c16"]; l, r = c["listening"], c["long_run"]
    m = lambda v: str(v).replace("-", "−")
    ci = lambda x: f'{m(x["slope"])} days a year; 95% CI {m(x["lo"])} to {m(x["hi"])}'
    s1 = (f'counting only stations that were in the water from March to August of that year, departures still moved later ({ci(l)})' if sig(l) and l["slope"] > 0
          else f'counting only stations that were in the water from March to August of that year, there\'s no clear trend ({ci(l)})')
    if sig(r) and r["slope"] > 0:
        s2 = f'At the {r["stations"]} stations that listened in at least 8 of the {r["years"]} years, it holds too ({ci(r)}; {r["n"]} shark-years).'
        end = ""
    else:
        s2 = f'At the {r["stations"]} stations that listened in at least 8 of the {r["years"]} years, there\'s no clear trend ({ci(r)}; {r["n"]} shark-years).'
        end = " So part of the shift may come from where receivers sat, not when sharks left. A full deployment history would settle it."
    return f'Holding the listening stations fixed: {s1}. {s2}{end}'

def juvC30(D):
    j = D["imos"]["c30"]
    return ('First look: the public data can\'t test this yet. ' + A("https://researchdata.edu.au/imos-animal-tracking-2007-ongoing/3961802", "IMOS Animal Tracking")
            + f' has {j["all_white"]} tagged white sharks in all. {j["sharks"]} young ones (under 3 m) were picked up off the Central Coast and Newcastle, '
            f'on {j["days"]} days across {j["years"]} years between {j["y0"]} and {j["y1"]}: too few to compare warm and cool years. '
            'The nursery tagging at Port Stephens and Stockton Beach isn\'t in the public data, and that is what would make this testable.')

def ruledC24(D):
    a = D["lunar"]["all"]; lo, hi = G.wilson(a["near"], a["n"])
    if G.g_c24(D) != "ruled": return ""
    return (f'Why ruled out: {a["near"]} of {a["n"]} bites ({a["near_pct"]}%) came within 3.7 days of a full or new moon, where chance gives half. '
            f'The 95% range, {100 * lo:.0f}% to {100 * hi:.0f}%, stops short of the 60% that a 1.5-times effect would give, so a moon effect worth acting on would have shown up.')

def ruledC5(D):
    if G.g_c5(D) != "ruled": return ""
    import math
    from statistics import NormalDist
    w = D["whitecool"]; b = math.log(1 + w["trend_pct_per_year"] / 100); z = NormalDist().inv_cdf(1 - w["trend_p"] / 2)
    yrs = len(w["per_year"]) - 1; most = math.exp((b + 1.96 * abs(b) / z) * yrs)
    return ('Why ruled out: the card\'s own test is whether the peak matches white sharks\' own winter move north, regardless of whales. '
            f'East Australian humpbacks grew roughly tenfold since the 1990s, but Queensland\'s winter white shark catches did not: at most {most:.2f} times over {yrs} years on the 95% range, '
            'short of the 1.5 times a whale-driven rise would need. The bite peak still falls in the migration months; the whales don\'t explain it.')

def shareC1(D):
    c = D["catchshare"]; s, n = c["south"], c["north"]; f, l = c["first_years"], c["last_years"]
    sg = lambda x: f"{x:.1f}".replace("-", "−")
    fall = n["diff_pts"] < 0
    return (f'Early result (exploratory, not specified in advance): in southern Queensland\'s shark-control gear (Rainbow Beach to the Gold Coast), '
            f'bull sharks {"rose" if s["diff_pts"] > 0 else "fell"} from {s["first"]["pct"]}% of all sharks caught in {f[0]}–{f[1]} ({s["first"]["bull"]:,} of {s["first"]["sharks"]:,}) '
            f'to {s["last"]["pct"]}% in {l[0]}–{l[1]} ({s["last"]["bull"]:,} of {s["last"]["sharks"]:,}): a {"rise" if s["diff_pts"] > 0 else "fall"} of {abs(s["diff_pts"])} percentage points '
            f'(95% CI {sg(s["ci"][0])} to {sg(s["ci"][1])}; {pf(s["p"])}). In the north their share {"fell" if fall else "rose"} from {n["first"]["pct"]}% to {n["last"]["pct"]}% '
            f'({sg(n["diff_pts"])} points, 95% CI {sg(n["ci"][0])} to {sg(n["ci"][1])}). This is share of catch, not catch per unit of effort, which isn\'t published. '
            f'NSW data would extend it south. ' + A("https://www.data.qld.gov.au/dataset/fisheries-queensland-s-shark-control-program-information-and-data", "Queensland Shark Control Program data"))

def projC3(D):
    P = D["proj"]; e, sy, wo, al = P["eden"], P["sydney"], P["wollongong"], P["albany"]
    rng = f'{e["lo"]} to {e["hi"]}' if e["lo"] != e["hi"] else f'all {e["lo"]}'
    reach = (f'So the half-year line reaches Eden, about 50 km short of the Victorian border; whether it crosses the border needs finer, downscaled projections.'
             if e["median"] >= 6 else "So the half-year line stays north of Eden.")
    return (f'Early result (global climate models, not yet downscaled): we took {e["models"]} CMIP6 models under a middle emissions path (SSP2-4.5), measured each one\'s warming from 2016–2025 to 2040–2059 '
            f'at each beach\'s sea patch, and added it to the temperatures observed there in 2016–2025. Off Eden (37.1°S), the median model gives {e["median"]} months a year at 19°C or more by about 2050, '
            f'up from {e["now"]} now (the middle 80% of models: {rng}). {reach} Further north, Sydney reaches about {sy["median"]} months and Wollongong about {wo["median"]}. '
            f'On the west coast Albany stays near {al["median"]}. These broadly match the simple trend used in "Looking ahead". Models: '
            + A("https://wcrp-cmip.org/cmip-phase-6-cmip6/", "CMIP6") + ', via the Pangeo public archive.')

def tagsC25(D):
    t = D["tags_sa"]
    return (f'Measured on the sharks themselves: {t["sharks"]} bull sharks tagged in South Africa\'s Breede River, near the southern edge of their range, '
            f'carried temperature tags for {t["days_range"][0]} to {t["days_range"][1]} days each in {t["years"]}. They spent {t["pct_time_19_or_warmer"]}% of their time in water at 19°C or warmer. '
            f'On {t["days_mean_below19"]} of {t["shark_days"]} shark-days the day\'s average fell below 19°C, '
            + (f'{t["cold_week"]}; ' if t.get("cold_week") else "")
            + f'the coldest reading was {t["coldest"]}°C. The tags don\'t record where each shark was. ('
            + A("https://doi.org/10.1038/s41558-024-01966-8", "Lubitz et al. 2024") + "; data on " + A("https://doi.org/10.5061/dryad.xd2547dn1", "Dryad") + ", CC0.)")

PARAS = {"mhwC19": (mhwC19, ("mhw",)), "bwC6": (bwC6, ("beachwatch",)), "plumeC6": (plumeC6, ("rivers", "harbour")),
         "qldC6": (qldC6, ("tigerqld",)), "wkC18": (wkC18, ("exposure", "beachday")), "whaleC5": (whaleC5, ("whales",)),
         "whitecoolC5": (whitecoolC5, ("whitecool",)), "chlC4": (chlC4, ("chlorophyll",)), "tideC24": (tideC24, ("tides",)),
         "tigerC28": (tigerC28, ("tigerqld", "tigerrain")), "upC29": (upC29, ("upwelling",)),
         "stationsC16": (stationsC16, ("imos",)), "juvC30": (juvC30, ("imos",)),
         "shareC1": (shareC1, ("catchshare",)), "projC3": (projC3, ("proj",)),
         "tagsC25": (tagsC25, ("tags_sa",))}

def hawaiiC6(D):
    h = D["hawaii"]
    return (f'Hawaii ({h["first"]}–{h["last"]}): the water was turbid or muddy at {h["tiger_murky_pct"]}% of tiger shark bites ({h["tiger_murky"]} of {h["tiger_clarity_n"]}) '
            f'and {h["other_murky_pct"]}% of bites by other identified sharks ({h["other_murky"]} of {h["other_clarity_n"]}; p = {h["p_murky"]:.2f}), '
            + ("so murky water isn't special to tiger sharks there." if h["p_murky"] >= 0.05 else
               "so murky water does stand out for tiger sharks there." if h["tiger_murky_pct"] > h["other_murky_pct"] else "so tiger shark bites come in clearer water there."))

def hawaiiC24(D):
    a, t = D["lunar"]["hawaii_all"], D["lunar"]["hawaii_tiger"]
    return f'Hawaii {"agrees" if a["p"] >= 0.05 else "differs"}: {a["near"]} of {a["n"]} bites ({a["near_pct"]}%; p = {a["p"]:.2f}), and {t["near"]} of {t["n"]} tiger shark bites'

SENTENCES = [(re.compile(r"Hawaii \(\d{4}–\d{4}\): the water was turbid or muddy at .*?(?:so murky water isn't special to tiger sharks there|so murky water does stand out for tiger sharks there|so tiger shark bites come in clearer water there)\."), hawaiiC6, ("hawaii",)),
             (re.compile(r"Hawaii (?:agrees|differs): \d+ of \d+ bites \(\d+%; p = [\d.]+\), and \d+ of \d+ tiger shark bites"), hawaiiC24, ("lunar",))]

CLS = {"early": "cstat early", "ruled": "cstat ruled", "look": "cstat look", "nt": "cstat nt", "open": "cstat",
       "supported": "cstat early", "strong": "cstat early"}

def apply_grades(html, D):
    def one(m):
        cid = m[1]
        try: st, lab = G.grade(cid, D)
        except (KeyError, TypeError): return m[0]  # data for this claim not built yet: keep the page as it is
        return f'<article class="claim" id="{cid}" data-status="{st}">' + m[2] + f'<span class="{CLS[st]}">{lab}</span>'
    return re.sub(r'<article class="claim" id="(c\d+)" data-status="\w+">(.{0,240}?)<span class="cstat[^"]*">[^<]*</span>', one, html, flags=re.S)

def ready(fn, D):  # a result file from before a test was added lacks its fields until the next run
    try: fn(D); return True
    except (KeyError, TypeError): return False

def fill(html, D, history=None):
    html = apply_grades(html, D)
    H = X.load_history() if history is None else history
    def wts(m):
        try: body = X.block(m[1], D, H)
        except (KeyError, TypeError): return m[0]
        return f'<section class="wts" id="wts-{m[1]}"' + (f'><h5>Where this stands</h5><dl>{body}</dl></section>' if body else ' hidden></section>')
    html = re.sub(r'<section class="wts" id="wts-(c\d+)"[^>]*>.*?</section>', wts, html, flags=re.S)
    for pid, (fn, need) in PARAS.items():
        if all(k in D for k in need) and ready(fn, D):
            html = re.sub(rf'(<p class="agres" id="{pid}">).*?(</p>)', lambda m: m.group(1) + fn(D) + m.group(2), html, count=1, flags=re.S)
    for pat, fn, need in SENTENCES:
        if all(k in D for k in need) and (need != ("lunar",) or "hawaii_all" in D["lunar"]):
            html = pat.sub(lambda m: fn(D), html, count=1)
    return html
