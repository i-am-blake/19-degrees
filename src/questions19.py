"""Question pages (/questions/<slug>): a direct answer first, then what it covers, the evidence, its limits, the
claims that test it and the sources. Every number comes from the page data or from text already checked on the
home page (claim results, the Safety summaries), so a page can't drift from the site. The wording of each answer
was last reviewed on REVIEWED; numbers update weekly."""
import html, json, re, sys

REVIEWED = "2026-11-17"  # change when the answers' wording is reviewed again

def build(T, D, CLAIMS, out, write, page, relink, esc, text, BUILT, long_date, ym):
    def field(cid, name):
        m = re.search(rf"<dt>{name}</dt><dd>(.*?)</dd>", CLAIMS[cid]["body"], re.S)
        if not m: sys.exit(f"questions19.py: {cid} has no '{name}'")
        return relink(m.group(1))
    def srow(name):
        m = re.search(r'<div class="srow"><div class="sname"><b>' + re.escape(name) + r'</b><span class="ev[^"]*">(.*?)</span></div>(.*?)</div>\s*(?=<div class="srow"|</div>)', T, re.S)
        if not m: sys.exit("questions19.py: no Safety summary for " + name)
        return text(m.group(1)), relink(m.group(2))
    def claim_li(cid):
        c = CLAIMS[cid]
        tested = re.search(r"<dt>What was tested</dt><dd>(.*?)</dd>", c["body"], re.S)
        sup = re.search(r"<dt>Supports it if</dt><dd>(.*?)</dd>", c["body"], re.S)
        detail = ("Tested: " + relink(tested.group(1))) if tested else (("Supported if " + relink(sup.group(1))) if sup else "")
        return (f'<li><a href="/claims/{cid}"><b>{c["label"]}: {esc(c["title"])}</b></a> <span class="{c["cls"]}">{esc(c["grade"])}</span>'
                f'<br><span class="note">{detail}</span></li>')
    def claims(*ids): return '<ul class="qclaims">' + "".join(claim_li(c) for c in ids) + "</ul>"
    def grade(cid): return f'"{CLAIMS[cid]["grade"]}"'
    def src(*links): return "<ul>" + "".join(f'<li><a href="{u}">{l}</a></li>' for l, u in links) + "</ul>"
    pct = lambda a, b: round(100 * a / b)

    sp = D["species"]; B, Ti, W = sp["bull"], sp["tiger"], sp["white"]
    SYD = next(b for b in D["beaches"] if b["key"] == "sydney")
    Z = D["zones"]; E = Z["eras"]
    era = lambda e: f"{e[0]}–now" if e[1] >= 2020 else f"{e[0]}–{str(e[1])[2:]}"
    line_km = round((Z["line"][0] - Z["line"][-1]) * 111)
    zs = Z["species"]
    move = {k: round((zs[k][0]["mid"] - zs[k][-1]["mid"]) * 111) for k in zs}  # + = south
    bt = sorted(B["t"]); n22 = sum(1 for x in bt if x >= 22)
    asid_to = ym(D["asid_last"])
    WS = D["wa_spike"]; BD = D["bull_decades"]; POP = D["pop_mid"]
    O = D["bull_open"]["aus"]["eras"]; OE = D["bull_open"]["eras"]
    ASID = ("Australian Shark-Incident Database", "https://zenodo.org/records/18752301")
    HAD = ("HadISST monthly sea surface temperature, Met Office Hadley Centre", "https://www.metoffice.gov.uk/hadobs/hadisst/")
    IMOS = ("IMOS Animal Tracking", "https://researchdata.edu.au/imos-animal-tracking-2007-ongoing/3961802")
    LUB = ("Lubitz et al. 2025, Science of the Total Environment", "https://doi.org/10.1016/j.scitotenv.2025.179966")
    SCOPE_AU = (f"Australia, bites from 1900 to {asid_to} with a known month and place, matched to the monthly sea temperature of the nearest "
                "1° patch of open sea (about 110 km across). Bull, tiger and white sharks.")
    zone_rows = "".join(f"<tr><td>{era(e)}</td>" + "".join(f'<td>{zs[k][i]["n"]}</td><td>{abs(zs[k][i]["mid"]):.1f}°S</td>' for k in ("bull", "tiger", "white"))
                        + f'<td>{abs(Z["line"][i]):.1f}°S</td></tr>' for i, e in enumerate(E))
    zone_tbl = ('<div class="tbl"><table><thead><tr><th>Era</th><th>Bull bites</th><th>Bull center</th><th>Tiger bites</th><th>Tiger center</th>'
                '<th>White bites</th><th>White center</th><th>Half-year 19°C line</th></tr></thead><tbody>' + zone_rows + "</tbody></table></div>"
                '<p class="note">East coast of Queensland and NSW. "Center" is the middle latitude of that era\'s bites; the line is where the sea is 19°C or more for at least half the year. '
                'One degree of latitude is about 111 km. From <a href="/data/zones-by-era.csv">zones-by-era.csv</a>.</p>')
    sp_tbl = ('<div class="tbl"><table><thead><tr><th>Species</th><th>Bites since 1900</th><th>In months below 19°C</th><th>Coolest month</th><th>Median month</th></tr></thead><tbody>'
              + "".join(f'<tr><td>{n}</td><td>{s["n"]}</td><td>{s["below"]} ({pct(s["below"], s["n"])}%)</td><td>{s["min"]:.1f}°C</td><td>{s["median"]:.1f}°C</td></tr>'
                        for n, s in (("Bull shark", B), ("Tiger shark", Ti), ("White shark", W))) + "</tbody></table></div>"
              '<p class="note">Sea temperature is the monthly average for the open-sea patch nearest each bite. From <a href="/data/bite-temperature-summary.csv">bite-temperature-summary.csv</a>.</p>')
    dec = lambda area: "".join(f'<tr><td>{d}s</td><td>{v[0]}</td><td>{v[1]}</td><td>{POP.get(d, "")}</td></tr>' for d, v in sorted(BD[area].items()))
    P = []  # (slug, question, short title, answer html, desc, sections [(h2, html)], related slugs)

    # 1. What is the 19°C line?
    P.append(("what-is-the-19c-line", "What is the 19°C line?",
     f'The 19°C line is the point along the coast where the sea stops averaging 19°C (66°F) or more for at least half the year. 19 Degrees follows it because not one of Australia\'s {B["n"]} recorded bull shark bites since 1900 happened in a month when the sea was cooler than 19°C. On the east coast, the line has moved about {line_km} km south since {era(E[0])}, from near Jervis Bay to near Eden.',
     f'The half-year 19°C line, and why it matters: none of Australia\'s {B["n"]} recorded bull shark bites since 1900 came in a month when the sea was below 19°C, and the line has moved about {line_km} km south.',
     [("What this covers", f"<p>{SCOPE_AU}</p>"),
      ("Why 19°C", f'<p>Matched to the sea temperature of the month they happened, Australia\'s shark bites split by species:</p>{sp_tbl}'
                   f'<p>For bull sharks the cut-off is sharp: the coolest month with a bull shark bite was {B["min"]:.1f}°C. Tiger sharks are almost the same. White sharks are different: {pct(W["below"], W["n"])}% of their bites came in months below 19°C, so the line tells you nothing about them.</p>'),
      ("How the line is moving", f'<p>The sea off Sydney now averages 19°C or more about {SYD["recent"]:.1f} months a year ({SYD["recent_span"][0]} to {SYD["recent_span"][1]}), against {SYD["base"]:.1f} in {SYD["base_span"][0]} to {SYD["base_span"][1]}. Further south, the line where half the year is that warm has moved along the coast:</p>{zone_tbl}'
                   f'<p>Bull shark bites have moved with it: the middle of the east-coast bull shark bite zone is about {move["bull"]} km further south than in {era(E[0])}. Whether the line keeps moving is claim C3: {field("c3", "What came out")}</p>'),
      ("What tagged sharks show", f'<p>Bites only show where sharks met people. Tags show where the sharks are. {field("c25", "What came out")}</p>'
                   f'<p>Large tagged bull sharks leave Sydney as the water cools to about 19–20.5°C, and are leaving later as the sea warms (<a href="{LUB[1]}">Lubitz et al. 2025</a>).</p>'),
      ("Limits", "<ul><li>The temperature is a monthly average over about 110 km of open sea. It describes the season, not the water at a beach on the day. Harbors and rivers can be warmer.</li>"
                 "<li>The bite database gives the month, not the day, so these are months, not days.</li>"
                 "<li>Bites follow people as well as sharks: fewer people swim when the sea is cold.</li>"
                 '<li>It is a pattern in past records, not a safety threshold. See <a href="/questions/is-19c-a-safety-threshold">Is 19°C a safety threshold?</a></li></ul>'),
      ("Claims that test it", claims("c25", "c22", "c16", "c3", "c32")),
      ("Sources", src(ASID, HAD, IMOS, LUB))],
     ["is-19c-a-safety-threshold", "what-temperature-do-bull-sharks-prefer", "are-sharks-moving-south"]))

    # 2. Is 19°C a safety threshold?
    P.append(("is-19c-a-safety-threshold", "Is 19°C a safety threshold?",
     f'No. 19°C describes when and where bull sharks have bitten in the past, measured as a monthly average over the open sea. It is not a temperature below which the water is safe. White sharks also bite in cooler water ({W["below"]} of {W["n"]} white shark bites came in months below 19°C), some young bull sharks stay through winter in rivers that drop below 19°C (as cold as 9.6°C in one Florida river), and the water at a beach on the day can differ from the monthly average. Whatever the temperature, follow lifesavers, beach signs and local authorities.',
     f'No. 19°C is a pattern in past bull shark bites, not a safe temperature: {W["below"]} of {W["n"]} white shark bites came in cooler months, and young bull sharks winter in some colder rivers.',
     [("What this covers", f"<p>{SCOPE_AU} Plus temperature tags on bull sharks in Australia, South Africa and the United States.</p>"),
      ("Why it isn't a safe temperature", f"{sp_tbl}<ul>"
                   f'<li><b>Other sharks.</b> White sharks bite in cooler water: their median bite month was {W["median"]:.1f}°C, and the coolest {W["min"]:.1f}°C.</li>'
                   f'<li><b>Small bull sharks in rivers.</b> {field("c43", "What came out")}</li>'
                   f'<li><b>Rivers on other continents.</b> {field("c25", "What came out")}</li>'
                   "<li><b>The measure.</b> The temperature is a monthly average for about 110 km of open sea, not a reading at the beach. The bite database records the month, not the day.</li></ul>"),
      ("What it is useful for", "<p>The line is a guide to the season and the coast where bull sharks are likely to be around, and to how that is changing as the sea warms. "
                   f'It can help decide when alerts, patrols and monitoring should run, which is what claim C16 informs: {field("c16", "Decision it informs").rstrip(".")}.</p>'),
      ("Limits", f"<ul><li>The records are Australian, and most bites are from the east coast. Whether bull shark bites elsewhere also stop below about 19°C is claim C22 (graded {grade('c22')}).</li>"
                 "<li>None of this is safety advice. 19 Degrees summarizes data and published research; it is not a guide to whether or where to swim.</li></ul>"),
      ("Claims that test it", claims("c43", "c25", "c22", "c16")),
      ("Sources", src(ASID, HAD, IMOS, LUB))],
     ["what-is-the-19c-line", "what-temperature-do-bull-sharks-prefer", "do-shark-deterrents-work"]))

    # 3. What temperature do bull sharks prefer?
    P.append(("what-temperature-do-bull-sharks-prefer", "What temperature do bull sharks prefer?",
     f'Large bull sharks off eastern Australia are found almost only in water of 19°C (66°F) or warmer. All {B["n"]} recorded bull shark bites since 1900 came in months when the nearby sea averaged {B["min"]:.1f}°C or more, with a median of {B["median"]:.1f}°C, and large tagged bull sharks leave Sydney as the water cools to about 19–20.5°C. Young bull sharks are the exception: in some rivers they stay through winter in colder water.',
     f'Adult bull sharks off Australia stay almost entirely in water of 19°C or warmer: all {B["n"]} recorded bites came in months at {B["min"]:.1f}°C or more. Small sharks in some rivers tolerate colder water.',
     [("What this covers", f"<p>{SCOPE_AU} Plus temperature tags on bull sharks off NSW, in South Africa and Mozambique, and in the United States.</p>"),
      ("Bites", f'<p>Of {B["n"]} bull shark bites with a known month and place, the coolest month was {B["min"]:.1f}°C, the median {B["median"]:.1f}°C and the warmest {B["max"]:.1f}°C. {n22} ({pct(n22, B["n"])}%) came in months at 22°C or more. '
                f'The full list is in <a href="/data/bite-temperatures.csv">bite-temperatures.csv</a>.</p>'),
      ("Tags", f'<p>Tags record where the sharks are, not only where they met people. {field("c25", "What came out")}</p>'
               f'<p>Large tagged bull sharks leave Sydney as the water cools to about 19–20.5°C, and leave later as the sea warms (<a href="{LUB[1]}">Lubitz et al. 2025</a>). Size matters: {field("c43", "What came out")}</p>'),
      ("Limits", "<ul><li>Bite months and the open-sea patch describe the season, not the water around a shark on the day. Harbors and rivers can be warmer or cooler than the open sea.</li>"
                 "<li>Tags are on a limited number of sharks in a few places, and receivers only hear sharks that pass them.</li>"
                 f"<li>Whether bull shark bites elsewhere stop at the same temperature is claim C22 (graded {grade('c22')}).</li></ul>"),
      ("Claims that test it", claims("c25", "c43", "c16", "c22")),
      ("Sources", src(ASID, HAD, IMOS, LUB))],
     ["what-is-the-19c-line", "is-19c-a-safety-threshold", "are-sharks-moving-south"]))

    # 4. Are sharks moving south?
    P.append(("are-sharks-moving-south", "Are sharks moving south?",
     f'Bull shark bites are. On Australia\'s east coast, the middle of the bull shark bite zone is about {move["bull"]} km further south than in {era(E[0])}, as the warm water moved south, and the bull shark season off NSW is getting longer (graded {grade("c16")}). Whether the sharks themselves are moving is less settled: tags point the same way but changes in where receivers sit cloud the trend. Not every shark is heading south: white shark bites on the east coast have moved north.',
     f'Bull shark bites in eastern Australia have moved about {move["bull"]} km south since {era(E[0])}, and the bull shark season is getting longer. White shark bites have moved north. What the evidence shows, and its limits.',
     [("What this covers", f"<p>{SCOPE_AU} Plus tag detections of bull sharks off NSW, and shark-control catches in Queensland.</p>"),
      ("Where bites happen, era by era", zone_tbl + f'<p>Bull shark bites have also moved out of rivers and harbors onto the open coast: {O[0][1]} of {O[0][0]} bull shark bites were in coastal waters in {OE[0][0]}–{str(OE[0][1])[2:]}, against {O[-1][1]} of {O[-1][0]} since {OE[-1][0]}.</p>'),
      ("The season", f'<p>{field("c16", "What came out")} {field("c16", "Why this grade")}</p>'),
      ("Catches", f'<p>Shark-control gear is another check, because it fishes in the same places every year. {field("c1", "What came out")} {field("c1", "Why this grade")}</p>'),
      ("Other coasts", f'<p>In California, white shark incidents moved the other way: {field("c23", "What came out")}</p>'),
      ("Limits", "<ul><li>Bites follow people as well as sharks. More people now live and swim on the coasts where bites are rising (claim C18).</li>"
                 "<li>The eras hold a few dozen bites each, so a handful of bites can shift a center.</li>"
                 "<li>Whether there are more young bull sharks in the south, rather than the same sharks ranging further, is claim C38, not yet tested.</li></ul>"),
      ("Claims that test it", claims("c16", "c1", "c38", "c42", "c23", "c3")),
      ("Sources", src(ASID, HAD, IMOS, LUB, ("Banaghan et al. 2025, Marine and Freshwater Research", "https://doi.org/10.1071/MF24256"), ("Queensland Shark Control Program data", "https://www.data.qld.gov.au/dataset/fisheries-queensland-s-shark-control-program-information-and-data")))],
     ["what-is-the-19c-line", "are-shark-bites-increasing", "what-temperature-do-bull-sharks-prefer"]))

    # 5. Are shark bites increasing?
    P.append(("are-shark-bites-increasing", "Are shark bites increasing?",
     f'More bites are recorded in Australia than in past decades, but more people are in the water and minor bites are recorded more often now, so counts alone overstate the rise. In southern NSW, bites are rising faster than the coastal population (graded {grade("c18")}). Western Australia has had more bull shark bites since 2020 ({WS["post"]}) than in the 120 years before ({WS["pre"]}). A smaller share of injured people die than in the 1960s to 1980s, but not for white or bull shark bites (graded {grade("c44")}).',
     f'More shark bites are recorded than in past decades, but more people use the water. In southern NSW bites are outpacing the coastal population, and Western Australia\'s bull shark bites jumped after 2020.',
     [("What this covers", f"<p>Australia, unprovoked bites from 1900 to {asid_to} in the Australian Shark-Incident Database, with population from the Australian Bureau of Statistics.</p>"),
      ("Southern NSW", f'<p>{field("c18", "What came out")} {field("c18", "Why this grade")}</p>'
                       f'<div class="tbl"><table><thead><tr><th>Decade</th><th>Bull shark bites, NSW south of Port Macquarie</th><th>In rivers, harbors or estuaries</th><th>Australia\'s population (millions)</th></tr></thead><tbody>{dec("nsw_south")}</tbody></table></div>'),
      ("Western Australia", f'<p>Since 2020, Western Australia has had {WS["post"]} bull shark bites, against {WS["pre"]} from 1900 to 2019: {WS["north"]} in the tropical north and {WS["south"]} around Perth. A jump that size is very unlikely to be chance.</p>'
                            f'<div class="tbl"><table><thead><tr><th>Decade</th><th>Bull shark bites, Western Australia</th><th>In rivers, harbors or estuaries</th><th>Australia\'s population (millions)</th></tr></thead><tbody>{dec("wa")}</tbody></table></div>'),
      ("Survival", f'<p>{field("c44", "What came out")} {field("c44", "Why this grade")}</p>'),
      ("Perspective", f'<p>For every shark death on Australia\'s coast, about {round(D["ratio"]["drown"] / D["ratio"]["shark"])} people drown ({D["ratio"]["drown"]:,} coastal drownings and {D["ratio"]["shark"]} fatal shark bites, {ym(D["ratio"]["window"]["start"])} to {ym(D["ratio"]["window"]["end"])}).</p>'),
      ("Limits", "<ul><li>Nobody counts how many people are in the water, so coastal population stands in for beach use.</li>"
                 "<li>Minor bites are more likely to be reported now than a century ago, which inflates recent counts.</li>"
                 "<li>Shark numbers worldwide have fallen; rising bites in some places are about where and when people and sharks meet, not more sharks.</li></ul>"),
      ("Claims that test it", claims("c18", "c44", "c19", "c6")),
      ("Sources", src(ASID, ("Australian Bureau of Statistics, population", "https://www.abs.gov.au/statistics/people/population"), ("National Coastal Safety Report 2025, Surf Life Saving Australia", "https://www.surflifesaving.com.au/")))],
     ["are-sharks-moving-south", "do-shark-nets-work", "do-shark-deterrents-work"]))

    # 6. Do shark nets work?
    nets_ev, nets = srow("Shark nets"); dl_ev, drum = srow("Smart drumlines"); dr_ev, drones = srow("Drones")
    P.append(("do-shark-nets-work", "Do shark nets work?",
     f'It hasn\'t been shown either way. Nets don\'t make a beach shark-free, and no study has separated their effect on bites from that of the lifesaver patrols at the same beaches, and bites at any one beach are too rare for a single season to tell. What is measured is the catch: in NSW, most animals caught are not the sharks behind most serious bites. Whether nets reduce bull shark bites is an open claim here (C20, graded {grade("c20")}).',
     "What the evidence says about shark nets: what they catch, what is known and unknown about their effect on bites, and the alternatives in use. Neutral, with sources.",
     [("What this covers", "<p>The NSW Shark Meshing Program and Queensland's shark-control program, from their own reports and published research. 19 Degrees takes no side on nets or drumlines; this page reports what has been measured.</p>"),
      ("What nets catch", f'<p><b>NSW ({esc(nets_ev.lower())}).</b> {nets}</p><p><b>Queensland.</b> {field("c46", "What came out")} {field("c46", "Why this grade")}</p>'),
      ("Do they reduce bites?", f'<p>{field("c20", "Already known")}</p>'),
      ("What else is used", f'<p><b>Smart drumlines ({esc(dl_ev.lower())}).</b> {drum}</p><p><b>Drones ({esc(dr_ev.lower())}).</b> {drones}</p>'),
      ("Limits", "<ul><li>Bites at any one beach are rare, so a difference between netted and un-netted beaches takes many years of data, or many beaches, to detect.</li>"
                 "<li>Most netted beaches are also patrolled, so the two effects are hard to separate.</li>"
                 "<li>Catch counts don't say how many sharks swim past without being caught.</li></ul>"),
      ("Claims that test it", claims("c20", "c46", "c21", "c1", "c40")),
      ("Sources", src(("NSW Shark Meshing Program 2025–26 annual report", "https://www.sharksmart.nsw.gov.au/__data/assets/pdf_file/0006/1676715/Attachment-A-SMP-2025-26-Annual-Performance-Report.pdf"),
                      ("SharkSmart NSW: shark nets", "https://www.sharksmart.nsw.gov.au/shark-nets"), ("Gibbs et al. 2019, People and Nature", "https://doi.org/10.1002/pan3.10063"), ("Queensland Shark Control Program data", "https://www.data.qld.gov.au/dataset/fisheries-queensland-s-shark-control-program-information-and-data")))],
     ["do-shark-deterrents-work", "are-shark-bites-increasing", "is-19c-a-safety-threshold"]))

    # 7. Do shark deterrents work?
    prod = re.findall(r'<span class="(cstat[^"]*)" data-was="[^"]*">([^<]+)</span>', T[T.index('<table class="ptab">'):T.index("</table>", T.index('<table class="ptab">'))])
    by = {}
    for _, g in prod: by[g] = by.get(g, 0) + 1
    order = ["Supported", "Leans yes", "Unclear", "First look", "Ruled out", "Not yet tested"]
    if set(by) - set(order): sys.exit("questions19.py: new product grade " + ", ".join(set(by) - set(order)))
    gl = ", ".join(f"{by[g]} {g.lower()}" for g in order if g in by)
    import ladder19
    groups = "".join(f'<li><a href="/safety-check/{slug}">{h}</a>: {lead.split(". ")[0].rstrip(".")}.</li>' for h, slug, _, _, lead in ladder19.GROUPS)
    P.append(("do-shark-deterrents-work", "Do shark deterrents work?",
     'Some help, partly, in trials. The best electric deterrents cut bites on boards and decoys by about half to two thirds for some species in independent field trials, but none stopped every bite, results vary by shark, and bull sharks got used to one over three weeks. Magnetic bands and repellent wax showed no measurable effect. No deterrent has yet been shown to protect people in real-world use.',
     f"{len(prod)} shark deterrents, bite-resistant wetsuits, barriers and bleeding-control products checked against published independent tests, and placed on an evidence ladder from lab test to real-world protection.",
     [("What this covers", f"<p>Every shark deterrent, protective wetsuit, bleeding-control product and barrier with a published test that 19 Degrees could find: {len(prod)} products. Products sold without any published test are left out.</p>"),
      ("The evidence", f'<p>Electric devices for boards and divers did best in independent field trials, cutting bites on boards or decoys by about half to two thirds for some species, but results vary by shark and none stopped every bite. Magnetic bands and repellent wax showed no measurable effect. A patterned-wetsuit trial promoted by its maker found sharks took longer to engage, but it wasn\'t peer reviewed. Bite-resistant fabrics tore less than standard neoprene when bitten by white and tiger sharks.</p><p>Grades across all {len(prod)} products: {gl}. Every product and its tests: <a href="/safety#h-products">the table on the Safety page</a>.</p>'),
      ("The evidence ladder", f'<p>Each product is placed on the highest rung its tests have reached: a change in behavior in a test, fewer baits taken in a field trial, fewer bites on boards or decoys in a field trial, and, at the top, protecting people in real-world use. No product has reached the top rung. By group:</p><ul>{groups}</ul>'),
      ("Limits", "<ul><li>Trials use baits, boards and decoys, not people, with a few species in a few places.</li>"
                 "<li>Most tests use white sharks. Bull sharks, which bite in murky water close to shore, are where new trials would help most.</li>"
                 "<li>This is a guide to the evidence, not an endorsement or criticism of any maker.</li></ul>"),
      ("Claims that test it", claims("c14", "c15", "c11")),
      ("Sources", f'<p>Each product\'s tests are linked on its <a href="/safety-check/">evidence ladder page</a> and in the <a href="/safety#h-products">table on the Safety page</a>.</p>')],
     ["do-shark-nets-work", "is-19c-a-safety-threshold", "are-shark-bites-increasing"]))

    # guards: an answer may not claim more than the ladder allows, and each answer must lead with a direct reply
    for slug, q, ans, *_ in P:
        if re.search(r"\b(safe to swim|guarantee|proven to protect|prevents? (all|every) )", text(ans), re.I): sys.exit(f"questions19.py: {slug} overstates the evidence")
        if len(text(ans)) > 700: sys.exit(f"questions19.py: {slug} answer is too long for a direct answer")
    title_of = {s: q for s, q, *_ in P}
    written = []
    for slug, q, ans, desc, secs, rel in P:
        body = (f'  <p class="answer">{ans}</p>\n  <p class="meta">Answer reviewed {long_date(REVIEWED)} · numbers updated {long_date(BUILT)} with the weekly data</p>\n'
                + "".join(f"  <h2>{h}</h2>\n  {b}\n" for h, b in secs)
                + "  <h2>Related questions</h2>\n  <ul>" + "".join(f'<li><a href="/questions/{r}">{esc(title_of[r])}</a></li>' for r in rel) + "</ul>\n"
                + '  <p class="note">General information only, not safety, medical or professional advice. Follow lifesavers, beach signs and local authorities. Spotted an error? <a href="/#contact">Tell us</a>.</p>\n')
        ld = {"@context": "https://schema.org", "@type": "Article", "headline": q, "description": desc, "datePublished": REVIEWED, "dateModified": BUILT,
              "author": {"@type": "Organization", "@id": "https://19-degrees.org/#org", "name": "19 Degrees"}, "publisher": {"@id": "https://19-degrees.org/#org"},
              "mainEntityOfPage": f"https://19-degrees.org/questions/{slug}"}
        written.append(write(f"questions/{slug}", page(f"questions/{slug}", q, "Questions", body, desc=desc[:300], jsonld=ld, crumbs=[("Questions", "/questions/")])))
    # /questions/ itself is written by answers19.py, which links to these pages
    return written
