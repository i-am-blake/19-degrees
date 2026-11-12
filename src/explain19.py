"""Plain-language "Where this stands" summary for each claim card: what was tested, what came out, why it has its grade,
what would change it, and how the grade has moved. Written from the same data and rules as the grade (grades19.py),
so the words can't drift from the label. History lives in grades_history.json; build19.py adds an entry whenever a grade changes."""
import json, math, os
from statistics import NormalDist
import grades19 as G

def odds(p):
    """The p-value in words, for readers who don't use them."""
    if p < 0.001: return "less than 1 time in 1,000"
    if p >= 0.5: return "about half the time or more"
    n = 1 / p
    return f"about 1 time in {round(n):,}" if n >= 10 else f"about 1 time in {n:.0f}" if abs(n - round(n)) < 0.25 else f"about {round(100 * p)}% of the time"
def pv(p): return "p &lt; 0.001" if p < 0.001 else f"p = {p:.3f}" if p < 0.01 else f"p = {p:.2f}"
def chance(p): return f"If there were no real effect, a result at least this strong would turn up by chance {odds(p)} ({pv(p)})."

def t(tested, found, why, nxt): return dict(tested=tested, found=found, why=why, next=nxt)

def e_c1(D):
    c = D["catchshare"]; s, n = c["south"], c["north"]; f, l = c["first_years"], c["last_years"]; b = D["literature"]["banaghan2025"]
    flat = not ((b["south_drumline_r"] > 0 and b["south_drumline_sig"]) or (b["south_gillnet_r"] > 0 and b["south_gillnet_sig"]))
    return t("Whether bull shark catch rates in Queensland's shark-control gear are rising at its southern beaches.",
             f'A published study that allowed for fishing effort (catch per net or drumline per day, {b["years"]}) found '
             + ("no clear rise in the south overall: catches rose in the Sunshine Coast nets, fell on North Stradbroke Island's drumlines and were flat on the Gold Coast. " if flat else "a rise in the south. ")
             + f'This page\'s own measure, bull sharks\' share of all sharks caught, rose from {s["first"]["pct"]}% in {f[0]}–{f[1]} to {s["last"]["pct"]}% in {l[0]}–{l[1]} ({pv(s["p"])}).',
             ("Catch per unit of effort is the claim's own measure, and it shows no clear trend, so \"no clear link\". The rising share may come from other sharks falling, or from more frequent servicing of the gear in recent years, rather than more bull sharks."
              if flat else "Share of catch only stands in for catch per unit of effort, so the most it can reach is \"leans toward it\"."),
             "Effort-standardised catch rates for 2023 on, once gear has been serviced daily, and the southeast Queensland tagging data due next year.")
def e_c3(D):
    e = D["proj"]["eden"]
    return t(f'Where {e["models"]} global climate models put the line south of which the sea is 19°C or warmer for at least half the year, around 2050.',
             ("The middle model reaches Eden, about 50 km short of the Victorian border. The projected beaches stop at Eden, so they can't yet show whether the line crosses the border."
              if e["median"] >= 6 else f'The middle model stops short of Eden ({e["median"]} months a year there), so the line stays north of the border.'),
             "This is a projection, so it is graded by how many models agree rather than by a p-value. " +
             ("The line reaching Eden in most models leans toward the claim. To support it, at least 80% of models would need to take the line past the border."
              if e["median"] >= 6 else "The projected line staying north of Eden is what the card said would rule the claim out."),
             "Downscaled ocean projections for southeast Australia, which resolve the coast far better than global models.")
def e_c4(D):
    c = D["chlorophyll"]["all"]
    return t("Whether bites come more often in months when the sea is greener than usual, as a stand-in for baitfish runs.",
             f'{c["greenest_quarter"]} of {c["n"]} Australian bites ({c["pct"]}%) came in the greenest quarter of months for the place and season, where chance gives 25%. ' + chance(c["p"]),
             "The claim is about baitfish timing, and satellite chlorophyll only stands in for it, so the most it can reach is \"leans toward it\". " +
             ("The result points the predicted way but isn't strong enough to rule out chance." if c["p"] >= 0.05 else ""),
             "Monthly catches of mullet and other baitfish from NSW fisheries.")
def e_c5(D):
    w, h = D["whitecool"], D["whales"]
    b = math.log(1 + w["trend_pct_per_year"] / 100); z = NormalDist().inv_cdf(1 - w["trend_p"] / 2); yrs = len(w["per_year"]) - 1
    most = math.exp((b + 1.96 * abs(b) / z) * yrs)
    return t("Two things: whether white shark bites in NSW fall in the humpback migration months more than other sharks' bites do, and whether white sharks follow the whales or keep their own winter calendar. The card said in advance that the second would rule the claim out.",
             f'The timing holds: white shark bites do peak in the migration months (details below), and {h["white_pct"]}% of white shark bites fell in the four peak whale months, against {h["other_pct"]}% for other sharks ({pv(h["p"])}). '
             f'But humpbacks grew roughly tenfold since the 1990s while Queensland\'s winter white shark catches didn\'t grow ({w["first_half"]} in the first fifteen years, {w["second_half"]} in the next).',
             f'The card\'s own "rules it out" condition is met: white sharks keep the season regardless of whale numbers. The 95% range allows at most {most:.2f} times more white sharks over {yrs} years, short of the 1.5 times a whale-driven rise would need, so the data had room to show a real effect and didn\'t.',
             "Tagged white sharks showing they stay longer, or move differently, where whales are thickest.")
def e_c6(D):
    b, r = D["rain"]["bull"], D["rivers"]["bull"]
    return t("Whether bull shark bites come after heavy rain, when rivers flush murky water to the beaches.",
             f'Main test: {b["q"]} of {b["n"]} bull shark bites since {D["rain"]["y0"]} ({b["q_pct"]}%) came in the wettest quarter of months for the place and season, where chance gives 25%. ' + chance(b["q_p"]) +
             f' Check: nearby river flow didn\'t agree ({r["high_quarter"]} of {r["n"]} bites in high-flow months, {r["pct"]}%).',
             "The main test passed, but a further check didn't agree, and the bite records give the month rather than the day, so it can't test \"3 days after rain\". Both hold it at \"leans toward it\".",
             "Bite dates to the day, so the test can look at the 3 days after rain the claim names.")
def e_c16(D):
    c = D["imos"]["c16"]; r = c["long_run"]
    return t("Whether tagged bull sharks are leaving Sydney later each autumn.",
             f'The last detection each year moved about {c["slope"]} days later a year. ' + chance(c["p"]) +
             f' Check: at the {r["stations"]} listening stations that were in the water in most years, the shift almost disappears ({r["slope"]} days a year, {pv(r["p"])}).',
             "The main test passed but the station check didn't: part of the shift may come from where receivers sat, not when sharks left. So \"leans toward it\", not \"supports it\".",
             "The full deployment history of every listening station, including those that heard nothing.")
def e_c18(D):
    d = {x["decade"]: x for x in D["coastpop"]["decades"]}; a, z = d[1990], d[max(d)]
    ea, ez = a["people"] * a["years"], z["people"] * z["years"]; p = G.binom2(z["bites"], a["bites"] + z["bites"], ez / (ea + ez))
    return t("Whether bites in southern NSW are rising faster than the number of people using the beach.",
             f'Bites per million coastal residents a year rose from {a["rate"]} in the 1990s to {z["rate"]} in the {max(d)}s, while the number of residents grew {z["people"] / a["people"]:.2f} times. ' + chance(p),
             "People living on the coast stand in for people on the beach, which nobody counts, and minor bites are probably recorded more now. A stand-in can reach \"leans toward it\" at most.",
             "Beach attendance counts from Surf Life Saving, season by season.")
def e_c19(D):
    h = D["heat"]; k = sum(h[s]["t"] for s in h); n = sum(h[s]["n"] for s in h); a = D["mhw"]["all"]
    return t("Whether bites come more often in unusually warm months and marine heatwaves.",
             f'Main test: {k} of {n} bites ({round(100 * k / n)}%) came in the warmest tenth of months for the place, where chance gives 10% (white and tiger sharks, not bull sharks). ' + chance(G.binom2(k, n, 0.1)) +
             f' Check: by the day, {a["pct"]}% of bites came during a marine heatwave against {a["expected_pct"]}% expected ({pv(a["p"])}).',
             "The monthly test passed, but the sharper day-by-day check didn't clearly agree, so \"leans toward it\".",
             "Beach attendance by day, to separate more people in the water from more sharks.")
def e_c21(D):
    tm = D["fieldnotes"]["time"]; b = tm["bull"]; on = tm["white"]["n"] + tm["tiger"]["n"]; ok = tm["white"]["night"] + tm["tiger"]["night"]
    p = G.fisher2(b["night"], b["n"] - b["night"], ok, on - ok)
    return t("Whether drumlines set at dawn, dusk or night would catch more bull sharks.",
             f'No catch times are public, so this compares bites: {round(100 * b["night"] / b["n"])}% of bull shark bites with a time came at night, against {round(100 * ok / on)}% of white and tiger shark bites. ' + chance(p),
             "Bites by species stand in for catches by hour, so the most it can reach is \"leans toward it\".",
             "The time each animal was caught on Queensland's or NSW's drumlines.")
def e_c23(D):
    x = D["california"]["test"]
    return t("Whether California's white shark incidents have moved north as the coast warmed.",
             f'The middle latitude of incidents moved about {abs(x["shift_km"])} km south, from {x["pre_lat"]}°N in {x["pre"][0]}–{x["pre"][1]} to {x["post_lat"]}°N since 2014. ' + chance(x["p"]),
             "A clear result in the opposite direction to the claim: \"points the other way\". Why isn't settled: more young white sharks off Southern California, more people in the water there, or both.",
             "Tagging data on where young white sharks spend each year.")
def e_c24(D):
    a = D["lunar"]["all"]; lo, hi = G.wilson(a["near"], a["n"])
    return t("Whether bites cluster around the full or new moon.",
             f'{a["near"]} of {a["n"]} bites ({a["near_pct"]}%) came within 3.7 days of a full or new moon, where chance gives half. Tides showed no pattern either.',
             f'The card\'s own "rules it out" condition (bites spread evenly across the month) is met, and the 95% range, {100 * lo:.0f}% to {100 * hi:.0f}%, stops short of the 60% a 1.5-times effect would give. With this many bites, a moon effect worth acting on would have shown up.',
             "A much larger set of dated bites showing a clear cluster.")
def e_c25(D):
    a, u = D["obis"]["groups"]["africa"]["bull"], D["obis"]["groups"]["us"]["bull"]
    if "daily" in D and "tagtemp" in D:
        d = D["daily"]; da, du, sp, m = d["africa"]["bull"], d["us"]["bull"], d["us_bull_split"], d["manatee_river"]
        T = D["tagtemp"]; sy, cl, cs = T["sydney"], T["clarence"], T["clarence_size"]
        return t("Whether bull sharks outside Australia stay in water of 19°C or warmer, matched to the sea temperature on the day of each record, and checked against tags in Australia that measure the water at the shark.",
                 f'<b>For the claim.</b> Off Mozambique and South Africa, {da["below19"]} of {da["shark_days"]:,} bull shark days fell on a day below 19°C. '
                 f'In the US records outside one Florida river, {sp["elsewhere"]["below19"]} of {sp["elsewhere"]["days"]:,} did ({100 * sp["elsewhere"]["below19"] / sp["elsewhere"]["days"]:.1f}%). '
                 f'In Sydney Harbour, {sy["sharks"]} large tagged bull sharks logged {sy["shark_days"]:,} days with {sy["below19"]} below 19°C, and none in winter.'
                 f'<br><b>Against it.</b> Off the US as a whole, {du["below19"]} of {du["shark_days"]:,} bull shark days ({du["below19_pct"]:.1f}%) were below 19°C. Of those, {sp["river_dataset"]["below19"]} come from Florida\'s Manatee River, where {m["animals"]} tagged bull sharks stayed through winter in water as cold as {m["gauge"]["min"]}°C at the nearest gauge. '
                 f'In the Clarence River in NSW, {cl["sharks_in_winter"]} tagged bull sharks stayed into winter, in water with a median of {cl["winter_median"]}°C. '
                 f'There, {cs["small"]["with_winter_day"]} of {cs["small"]["sharks"]} sharks under 150 cm were detected in winter, and none of {cs["large"]["sharks"]} sharks of 200 cm or more.',
                 f'The daily test was written down before the data came back: fewer than {d["rule"]["supports_below_pct"]}% of shark-days below 19°C would support the claim, and the US result misses that, so the grade drops from "supports it" to "leans toward it". The exceptions aren\'t scattered. They are river populations on two continents, and in Australia they are the smaller sharks. The claim holds on open coasts and in harbors, and fails in at least two rivers.',
                 'Sizes for the Manatee River sharks, and winter tracking from more rivers. If the cold-water sharks are consistently young, the claim should be restated as two: adults follow the 19°C line, young sharks in river nurseries do not.')
    return t("Whether bull sharks outside Australia also stay in water of 19°C or warmer.",
             f'Off Mozambique and South Africa, {a["below"]} of {a["days"]:,} tagged bull shark days came in a month below 19°C, though {a["cell_months_below_pct"]}% of months there were that cool. Off the US, {u["below"]} of {u["days"]:,} record-days ({100 - u["pct_warm"]:.1f}%), against {u["cell_months_below_pct"]}% of months. ' + chance(max(G.binom2(a["below"], a["days"], a["cell_months_below_pct"] / 100), G.binom2(u["below"], u["days"], u["cell_months_below_pct"] / 100))),
             "Tested on the claim's own measure, in the predicted direction, on two separate coasts: \"supports it\". It stays \"early\" because the test was chosen after seeing the data.",
             "A test set in advance on a third coast (Brazil or the Gulf of Mexico) would move it to Supported.")
def e_c43(D):
    z = D["size"]; m = z["main"]; sm, md, lg = (m["by_shark"][k] for k in ("small", "mid", "large")); dy = m["by_day"]; wc = z["checks"]["without_clarence"]["by_day"]["small"]["days"]
    return t("Whether a bull shark's size decides if it is detected in NSW in winter, with each shark aged forward from its length at tagging using a published growth curve for Australian bull sharks.",
             f'<b>For the claim.</b> {sm["winter_sharks"]} of {sm["sharks"]} sharks tagged under 150 cm were detected in NSW in winter, against {lg["winter_sharks"]} of {lg["sharks"]} tagged at 200 cm or more ({pv(m["p"])}). '
             f'Winter makes up {dy["small"]["winter_pct"]}% of small sharks\' days, {dy["mid"]["winter_pct"]}% for mid-sized sharks and {dy["large"]["winter_pct"]}% for large ones. A second growth curve, and a version with no growth curve, give the same answer.'
             f'<br><b>Against it.</b> Away from the Clarence River there {"is" if wc == 1 else "are"} {wc} shark-day{"" if wc == 1 else "s"} for a shark still under 150 cm, so what small sharks do in winter is known from one river. Large sharks are not absent in winter: {lg["winter_sharks"]} of {lg["sharks"]} were detected at least once.',
             'The result is strong and the checks agree, but it rests on one river, and the test was chosen after seeing that river\'s data. That holds it at "leans toward it".',
             "Winter tracking of small bull sharks in a second river, with sizes recorded. Lengths for the Manatee River sharks in Florida (claim C25) would test it on another continent.")
def e_c26(D):
    i = D["iod"]["all"]
    return t("Whether Western Australia's bites come more often when the Indian Ocean Dipole is positive.",
             f'{i["pos"]} bites came in positive-dipole months against about {i["pos_exp"]} expected for the same calendar months and decade. ' + chance(i["p"]),
             "A first look found twice the expected number, but positive-dipole years and bites have both become more common since the 1990s. Comparing like with like removes the link: \"no clear link\".",
             "More WA bites over the coming decade.")
def e_c28(D):
    t_ = D["tigerrain"]["all"]["tiger"]; q = D["tigerqld"]["tiger"]
    return t("Whether heavy rain brings tiger sharks close to shore.",
             f'By the day, {t_["wettest_quarter"]} of {t_["n"]} tiger shark bites followed a 3-day spell in the wettest quarter, where chance gives 25%. ' + chance(t_["p"]) +
             f' Queensland\'s gear caught tiger sharks at the same rate in high-river months ({q["ratio"]} times).',
             "Both tests come out where chance puts them: \"no clear link\". It isn't \"ruled out\" because the catch test has no 95% range yet to show a real effect would have been seen.",
             "A 95% range on the catch comparison, or rain data from more coasts.")
def e_c29(D):
    u = D["upwelling"]; p = G.binom2(u["strongest_quarter"], u["n"], 0.25)
    return t("Whether cold upwelling brings white sharks close to shore in California.",
             f'{u["strongest_quarter"]} of {u["n"]} white shark incidents ({u["strongest_pct"]}%) followed a week of the strongest upwelling for the place and season, where chance gives 25%. ' + chance(p),
             "Fewer incidents than chance, the opposite of the claim: \"points the other way\". It doesn't rule out the Australian finding, which compared places rather than days.",
             "The same test on Australian coasts with upwelling records.")

LOOK = {"c2": ("The number of tagged bull sharks heard south of Sydney rose, but so did the number of listening stations, and the public data shows only stations that heard something.", "The full listening-station history from NSW."),
        "c7": ("Only 5 recent WA bites can be checked against the current's strength, too few for a test.", "More bites, or tag detections from WA's receivers."),
        "c9": ("The records show where the wounds were, not how long it took to stop the bleeding, so this can only describe the deaths.", "Coroner findings and ambulance timelines, through a university partner."),
        "c20": ("Without past net and drumline locations, any comparison would be against today's gear. This describes the counts only.", "Queensland's gear locations by year since 1962."),
        "c22": ("Réunion and New Caledonia never cool below 19°C, so they can't test where the line is.", "Bite records from coasts that do cool, such as the US southeast or South Africa."),
        "c30": ("Public tagging data has 15 young white sharks off the Central Coast and Newcastle, too few to compare warm and cool years.", "The nursery tagging data from Port Stephens and Stockton Beach.")}
EXPLAIN = {k[2:]: v for k, v in globals().items() if k.startswith("e_c")}

HIST = os.path.join(os.path.dirname(os.path.abspath(__file__)), "grades_history.json")
def load_history():
    try: return json.load(open(HIST))
    except (OSError, ValueError): return {}
def update_history(H, D, today):
    """Add an entry when a claim's grade changes. Returns True if anything changed."""
    changed = False
    for cid in list(G.FIXED) + list(G.TESTS):
        try: st, lab = G.grade(cid, D)
        except (KeyError, TypeError): continue
        h = H.setdefault(cid, [])
        if not h or h[-1]["label"] != lab:
            h.append(dict(date=today, label=lab, why="New data changed the result." if h else "First graded.")); changed = True
    return changed

def fmt_date(d):
    y, m, dd = d.split("-"); return f'{int(dd)} {"Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()[int(m) - 1]} {y}'
def block(cid, D, H):
    st, lab = G.grade(cid, D)
    if st in ("open", "nt"): return ""
    if st == "look":
        why, nxt = LOOK[cid]
        rows = [("Grade", lab), ("Why a first look", why + " A first look describes the data; it doesn't test the claim."), ("What would change it", nxt)]
    else:
        e = EXPLAIN[cid](D)
        rows = [("Grade", lab), ("What was tested", e["tested"]), ("What came out", e["found"]), ("Why this grade", e["why"]), ("What would change it", e["next"])]
    hist = H.get(cid, [])
    if len(hist) > 1:
        rows.append(("How it has changed", '<ul class="hist">' + "".join(f'<li><b>{fmt_date(x["date"])}: {x["label"]}.</b> {x["why"]}</li>' for x in hist) + "</ul>"))
    return "".join(f"<dt>{a}</dt><dd>{b}</dd>" for a, b in rows)
