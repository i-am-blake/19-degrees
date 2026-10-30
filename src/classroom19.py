"""Build the 19 Degrees classroom sheets from the built page's data: a hub page and three printable versions.
Usage: python3 -I classroom19.py <19-degrees.html> <out_dir>
Writes classroom.html (choose a version), classroom-primary.html (ages 8-11), classroom-middle.html (ages 12-15)
and classroom-senior.html (ages 16 and up). Each sheet has a data map of the east coast and an answer page that
prints on its own sheet. All numbers come from the page data, so the sheets stay current with the weekly update."""
import sys, re, json, os
page, out = sys.argv[1:3]
d = json.loads(re.search(r'id="n19-data">(.*?)</script>', open(page).read(), re.S).group(1))
os.makedirs(out, exist_ok=True)
logo = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo_shark19.svg")).read()
syd = next(b for b in d["beaches"] if b["key"] == "sydney"); bull = d["species"]["bull"]
O = d["bull_open"]["aus"]["eras"]; Z = d["zones"]; W = d["wa_spike"]; R = d["ratio"]
pct = lambda e: round(e[1] / e[0] * 100)
km = round((Z["line"][0] - Z["line"][-1]) * 111)
mi = round(km * 0.621)
inc = round((syd["recent"] / syd["base"] - 1) * 100)
ratio = round(R["drown"] / R["shark"])
sA = next(b for b in d["ahead"]["east"]["beaches"] if b["name"] == "Sydney")

# --- the picture: east-coast map with the half-year 19°C line in 1950-79, now, and the 2050 look-ahead
C = d["coast"]
X = lambda lon: (lon - C["lon0"]) / (C["lon1"] - C["lon0"]) * C["w"]
Y = lambda lat: (C["lat0"] - lat) / (C["lat0"] - C["lat1"]) * C["h"]
lonA, lonB, latA, latB = 143.5, 157.5, -24.5, -39.2
vx, vy, vw, vh = X(lonA), Y(latA), X(lonB) - X(lonA), Y(latB) - Y(latA)
sc = vw / 200
def line(lat, col, lab, dash=""):
    y = Y(lat)
    return (f'<line x1="{X(149.4):.1f}" x2="{vx+vw-sc*4:.1f}" y1="{y:.1f}" y2="{y:.1f}" stroke="{col}" stroke-width="{sc*1.8:.2f}" {dash}/>'
            f'<text x="{vx+vw-sc*5:.1f}" y="{y-sc*2.5:.1f}" text-anchor="end" font-size="{sc*6.2:.2f}" font-weight="700" fill="{col}" font-family="system-ui,sans-serif">{lab}</text>')
towns = "".join(f'<circle cx="{X(lo):.1f}" cy="{Y(la):.1f}" r="{sc*1.6:.2f}" fill="#10212B"/><text x="{X(lo)-sc*4:.1f}" y="{Y(la)+sc*2.4:.1f}" text-anchor="end" font-size="{sc*6:.2f}" fill="#10212B" font-family="system-ui,sans-serif">{n}</text>'
                for n, la, lo in (("Brisbane", -27.47, 153.03), ("Coffs Harbour", -30.3, 153.11), ("Sydney", -33.87, 151.21), ("Eden", -37.07, 149.91)))
shark = d["sharks"]["species"]["bull"]["shapes"][0]["d"]
MAP = f"""<svg class="map" viewBox="{vx:.1f} {vy:.1f} {vw:.1f} {vh:.1f}" role="img" aria-label="Map of the east coast of Australia showing the line where the sea is 19°C or warmer for half the year: near Jervis Bay in 1950 to 1979, near Eden now, and past the Victorian border by about 2050 at the recent pace.">
<defs><linearGradient id="sea" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#F6C27F"/><stop offset=".55" stop-color="#BFE0EF"/><stop offset="1" stop-color="#7FB8D6"/></linearGradient></defs>
<rect x="{vx:.1f}" y="{vy:.1f}" width="{vw:.1f}" height="{vh:.1f}" fill="url(#sea)"/>
<path d="{C['d']}" fill="#F3EBDD" stroke="#10212B" stroke-width="{sc*0.7:.2f}" stroke-linejoin="round"/>
{line(Z['line'][0], '#1C5A80', f'1950–79', 'stroke-dasharray="6 5"')}
{line(Z['line'][-1], '#C2561F', 'Now')}
{line(-37.9, '#7A2E12', '2050?', 'stroke-dasharray="2 4"')}
{towns}
<g transform="translate({X(152.6):.1f},{Y(-31.2):.1f}) scale({sc*0.42:.3f})"><path d="{shark}" fill="#10212B" opacity=".85"/></g>
<text x="{vx+sc*4:.1f}" y="{vy+sc*9:.1f}" font-size="{sc*6.4:.2f}" font-weight="700" fill="#10212B" font-family="system-ui,sans-serif">Where the sea stays 19°C+</text>
<text x="{vx+sc*4:.1f}" y="{vy+sc*16:.1f}" font-size="{sc*5.4:.2f}" fill="#10212B" font-family="system-ui,sans-serif">for at least half the year</text>
</svg>"""

CSS = """:root{--ink:#10212B;--muted:#4A6170;--warm:#C2561F;--cold:#1C5A80;--rule:#C9D6DD}
*{box-sizing:border-box}body{margin:0;background:#fff;color:var(--ink);font:16px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif;padding:24px 16px}
.wrap{max-width:780px;margin:0 auto}.top{display:flex;align-items:center;justify-content:space-between;gap:16px;border-bottom:3px solid var(--ink);padding-bottom:12px;margin-bottom:16px}
.logo{width:150px;color:var(--ink)}.logo svg{width:100%;height:auto;display:block}
.k{font:12px ui-monospace,Menlo,monospace;letter-spacing:.12em;text-transform:uppercase;color:var(--muted)}
h1{font-size:30px;line-height:1.1;margin:4px 0 0}h2{font-size:19px;margin:22px 0 8px}
.hero{display:grid;grid-template-columns:minmax(0,1fr) 300px;gap:22px;align-items:start}.map{width:100%;height:auto;display:block;border:1px solid var(--rule)}
.fact{border-left:4px solid var(--warm);padding:6px 0 6px 12px;margin:10px 0}.fact b{color:var(--warm)}
table{border-collapse:collapse;width:100%}th,td{padding:3px 6px;text-align:left;font-size:14px}th{width:70px;color:var(--muted);font-weight:500}td:last-child{width:50px;text-align:right}
.b{display:block;height:14px;background:var(--warm)}.half{position:relative}.half::after{content:"";position:absolute;left:50%;top:-3px;bottom:-3px;border-left:1.5px dashed var(--ink)}
ol li{margin-bottom:14px}.lines{border-bottom:1px solid var(--rule);height:30px}.box{border:1.5px dashed var(--rule);height:150px;margin-top:8px}
dl{display:grid;grid-template-columns:170px 1fr;gap:6px 14px}dt{font-weight:600}dd{margin:0}
.ans{break-before:page;page-break-before:always;margin-top:36px;border-top:2px dashed var(--rule);padding-top:12px;font-size:14.5px}
.src{font-size:12.5px;color:var(--muted);margin-top:18px}
.teach{border:1.5px solid var(--ink);padding:16px 18px;margin-bottom:22px;font-size:14px}.teach h3{font-size:15px;margin:14px 0 4px}.teach ul{margin:4px 0;padding-left:20px}.teach p{margin:4px 0}.tgrid{display:grid;grid-template-columns:1fr 1fr;gap:16px}.seq th{width:auto}.seq td:last-child{width:auto;text-align:left}.seq th,.seq td{border-bottom:1px solid var(--rule);vertical-align:top}.seq td:nth-child(2){white-space:nowrap}.cur th{width:190px;color:var(--ink);font-weight:600}.cur td:last-child{white-space:normal!important;text-align:left}
@media (max-width:620px){.tgrid{grid-template-columns:1fr}}
.btns{display:flex;flex-wrap:wrap;gap:8px;margin:6px 0 4px}.btn{font:inherit;padding:8px 14px;border:1.5px solid var(--ink);background:#fff;color:var(--ink);cursor:pointer;min-height:44px;text-decoration:none;display:inline-flex;align-items:center}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,220px),1fr));gap:14px;margin-top:14px}.card{border:1.5px solid var(--rule);padding:18px;display:grid;gap:6px}.card h3{margin:0;font-size:19px}
@media print{.btns{display:none}body{padding:0}.ans{margin-top:0;border-top:0}}
@media (max-width:620px){.hero{grid-template-columns:1fr}.hero .map{max-width:320px}dl{grid-template-columns:1fr}}"""

def page(title, kicker, body):
    return f"""<!doctype html><html lang="en-US"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title><style>{CSS}</style></head><body><div class="wrap">
<div class="top"><div><div class="k">{kicker}</div><h1>{title}</h1></div><div class="logo" aria-hidden="true">{logo}</div></div>
{body}
<p class="src">Data: Australian Shark-Incident Database (Taronga Conservation Society Australia and Flinders University); HadISST sea temperature (UK Met Office); Pacoureau et al. 2021; Surf Life Saving Australia. From 19 Degrees, free and open source. © 2026 Blake Erickson.</p>
</div></body></html>"""

BTN = '<div class="btns"><button class="btn" onclick="window.print()">Print this sheet</button><a class="btn" href="classroom.html">All versions</a></div>'
rows = "".join(f'<tr><th>{r["decade"]}s</th><td class="half"><span class="b" style="width:{r["months"]/12*100:.0f}%"></span></td><td>{r["months"]:.1f}</td></tr>' for r in syd["rows"])
CHART = f'<h2>Months a year the sea off Sydney is 19°C or warmer</h2><table>{rows}</table><p class="k" style="margin-top:6px">Dashed line = 6 months, half the year</p>'
WORDS = '<h2>Words</h2><dl><dt>Sea surface temperature</dt><dd>How warm the top of the sea is.</dd><dt>Estuary</dt><dd>Where a river meets the sea; the water is part fresh, part salty.</dd><dt>Range</dt><dd>Where an animal can live.</dd><dt>Season</dt><dd>The part of the year an animal is in a place.</dd><dt>Marine heatwave</dt><dd>Days when the sea is much warmer than usual.</dd></dl>'
L = lambda n=2: '<div class="lines"></div>' * n

NGSS = "Next Generation Science Standards (US)"
WELL = ("This topic involves injuries and deaths. Some students may know someone affected by a shark bite or a drowning. "
        "Keep the focus on patterns and staying safe, avoid graphic images and news footage, let students step out if they need to, "
        "and follow your school's wellbeing procedures. Sharks hold cultural significance for many Indigenous peoples, including Aboriginal and Torres Strait Islander, Māori, Native Hawaiian and other Pacific peoples; "
        "if you explore this, use resources developed with or approved by local communities.")
def TEACH(t):
    li = "".join(f"<li>{x}</li>" for x in t["li"]); sc = "".join(f"<li>{x}</li>" for x in t["sc"])
    seq = "".join(f"<tr><th>{a}</th><td>{b}</td><td>{c}</td></tr>" for a, b, c in t["seq"])
    return f"""<section class="teach"><h2 style="margin-top:0">Teacher notes</h2>
<p class="k">{t['years']} · {t['time']} · {t['mode']}</p>
<div class="tgrid"><div><h3>Learning intentions</h3><ul>{li}</ul></div><div><h3>Success criteria</h3><ul>{sc}</ul></div></div>
<h3>Big ideas</h3><p>{t['big']}</p>
<h3>Curriculum links</h3><table class="seq cur"><tbody>
<tr><th>Australia (v9)</th><td>{t['ac']}</td></tr>
<tr><th>United States (NGSS)</th><td>{t['ngss']}</td></tr>
<tr><th>England (National Curriculum)</th><td>{t['eng']}</td></tr>
<tr><th>International Baccalaureate</th><td>{t['ib']}</td></tr>
<tr><th>Other curricula</th><td>{t['other']}</td></tr>
<tr><th>Global goals</th><td>UN Sustainable Development Goals 13 (Climate action) and 14 (Life below water); UNESCO Education for Sustainable Development.</td></tr>
</tbody></table><p class="k">Mapped by topic. Check your own syllabus for local codes.</p>
<h3>Lesson sequence</h3><table class="seq"><thead><tr><th>Phase</th><th>Time</th><th>What happens</th></tr></thead><tbody>{seq}</tbody></table>
<h3>Materials</h3><p>{t['mat']}</p>
<h3>Differentiation</h3><p><b>Support:</b> {t['sup']}<br><b>Extension:</b> {t['ext']}</p>
<h3>Assessment</h3><p>{t['assess']}</p>
<h3>Wellbeing</h3><p>{WELL}</p></section>"""

T_PRIMARY = dict(big="Living things depend on the conditions of their habitat. Climate change is shifting those conditions. Maps and simple data show change over time. Staying safe at the beach.", eng="Key Stage 2 science: Living things and their habitats; Year 6 Evolution and inheritance (how animals are adapted to their environment); geography fieldwork and map skills.", ib="PYP units of inquiry under Sharing the planet (how living things depend on their environment).", other="New Zealand: Science, Living World and Nature of Science. Canada (Ontario): Grade 4 Habitats and communities. Most primary curricula: habitats, adaptation and reading simple data.", years="Ages 8 to 11 (Australia Years 3–6, US Grades 3–5, UK Years 4–6)", time="45–60 minutes", mode="whole class, then pairs",
 li=["Living things survive in places where the conditions suit them, including water temperature.", "Maps and numbers can show how a place changes over time."],
 sc=["I can find a place on a map and say which side of a line it is on.", "I can work out the difference between two numbers from the sheet.", "I can explain one way to stay safe at the beach."],
 ac="AC9S5U01 (structural features and behaviours that let living things survive in their habitats); AC9S6U01 (how changing physical conditions affect the growth and survival of living things). Mathematics: reading maps and simple data, subtraction.",
 ngss="3-LS4-3 (in a particular habitat some organisms survive well, some less well, and some not at all).",
 seq=[("Engage","5 min","Ask: what makes a beach safe or unsafe? Share ideas."),("Explore","15 min","Read the facts and the map together; answer questions 1–2 in pairs."),("Explain","10 min","Discuss why some animals live only where the water is warm enough."),("Elaborate","15 min","Questions 3–4; compare shark and drowning numbers."),("Evaluate","10 min","Draw the safety poster (question 5); share two posters.")],
 mat="Printed sheet (2 pages; print the teacher notes separately), coloured pencils. Optional: the 19 Degrees page on a projector to show today's sea temperatures.",
 sup="Read the text aloud, pair readers with non-readers, and give a number line for question 3.",
 ext="Use the 19 Degrees page to pick another beach and compare its warm months now and a century ago.",
 assess="Use the answer guide on the next page. Questions 1–3 check map and number skills; question 5 shows understanding of beach safety.")

T_MIDDLE = dict(big="A change in one non-living factor, water temperature, changes where and when a species lives. Patterns in data can support or challenge an explanation. Apparent contradictions can both be true.", eng="Key Stage 3 science: Interactions and interdependencies; Working scientifically (analysis and evaluation). Key Stage 3 maths: percentages and interpreting data.", ib="MYP Sciences criteria B (inquiring and designing) and C (processing and evaluating); MYP Individuals and societies: environmental change.", other="New Zealand: Science, Living World and Nature of Science (investigating in science). Canada (Ontario): Grade 7 Interactions in the environment. Cambridge Lower Secondary Science: ecosystems and thinking and working scientifically.", years="Ages 12 to 15 (Australia Years 7–9, US Grades 6–9, UK Years 8–10)", time="50–60 minutes", mode="individual or pairs",
 li=["A change in an abiotic factor (water temperature) can change where and when a species is found.", "Data can be used to test whether an explanation holds."],
 sc=["I can read a chart and calculate a percentage change.", "I can explain how two facts that seem to clash can both be true.", "I can suggest a fair way to test an explanation."],
 ac="AC9S7U02 (models of ecosystems; how changes in abiotic and biotic factors affect populations); AC9S7I05, AC9S7I06, AC9S7I07 (analyzing data, evaluating claims and constructing evidence-based arguments; the Year 8 and 9 equivalents are AC9S8I05–07 and AC9S9I05–07). Mathematics: percentages and reading data displays.",
 ngss="MS-LS2-1 (effects of resource availability on organisms and populations); MS-LS2-4 (changes to physical or biological components of an ecosystem affect populations).",
 seq=[("Engage","5 min","Show the hero headline: 170 bites, not one below 19°C. Ask what could explain it."),("Explore","15 min","Read the chart and map; questions 1–2."),("Explain","10 min","Discuss range and season, and why fewer sharks worldwide doesn't mean fewer near one coast."),("Elaborate","15 min","Questions 3–4: competing explanations and how to test one."),("Evaluate","10 min","Question 5, then exit ticket: one thing the data shows and one thing it can't.")],
 mat="Printed sheet; calculators. Optional: the 19 Degrees page for the interactive beach chart.",
 sup="Work through question 1 as a class; give sentence starters for questions 3–4 (\"Both can be true because...\", \"To test this I would compare...\").",
 ext="Use the downloadable CSV to make your own chart for another beach and describe the trend.",
 assess="Use the answer guide. Question 1 checks calculation, questions 3–4 reasoning with evidence, question 5 communication.")

T_SENIOR = dict(big="Testing a claim with real data. Rates versus counts, statistical significance and its limits, correlation versus cause, and what would prove a claim wrong.", eng="GCSE Biology: ecology (abiotic factors, adaptation, distribution of organisms). GCSE Geography: climate change. A-level Biology and Geography independent investigations; GCSE and A-level maths statistics.", ib="DP Biology (ecology) and Environmental Systems and Societies (climate change, biodiversity); the Extended Essay and internal assessment (independent investigation).", other="Cambridge IGCSE and A Level Biology and Environmental Management. New Zealand NCEA: Science and Biology investigations, Statistics. Canada (Ontario): Grade 12 Biology, Population dynamics; Grade 11 Environmental science.", years="Ages 16 and up (Australia Years 10–12, US Grades 10–12, UK Years 11–13)", time="one 60–90 minute lesson, or two lessons with the data", mode="individual or small groups",
 li=["Claims about climate and wildlife can be tested with real data.", "Rates, p-values and alternative explanations all matter when judging evidence.", "A good test says in advance what result would prove the claim wrong."],
 sc=["I can calculate and compare rates over different time periods.", "I can explain what a p-value does and does not tell us.", "I can evaluate alternative explanations and design a falsifiable test."],
 ac="AC9S10U04 (models of energy flow between Earth's spheres to explain patterns of global climate change); AC9S10I05, AC9S10I06, AC9S10I07 (analyzing data, assessing validity and reproducibility, constructing evidence-based arguments). Senior secondary: suits depth studies or research investigations in Biology, Earth and Environmental Science, and General or Standard Mathematics (statistics).",
 ngss="HS-ESS3-5 (analyze geoscience data to make an evidence-based forecast of the rate of climate change and its impacts); HS-LS2-6 (evaluate claims about how changing conditions affect ecosystems).",
 seq=[("Engage","10 min","Present the claim. Ask students to predict what evidence would convince them, and what would not."),("Explore","20 min","Tasks 1–2: rates and the p-value."),("Explain","10 min","Class discussion: what does a p-value not tell us? Correlation versus cause."),("Elaborate","25 min","Tasks 3–4: alternative explanations and designing a test from the Researchers tab (C1–C22)."),("Evaluate","10 min","Task 5, then peer review of the test designs against the rubric.")],
 mat="Printed sheet; calculators. For two lessons: computers with the downloadable CSVs or the starter notebook (Python) from the Researchers tab.",
 sup="Model task 1 together; provide a worked example of interpreting a p-value.",
 ext="Run the starter notebook, change the threshold from 19°C to 18.5°C and 19.5°C, and report how sensitive the rule is. Strong designs can be sent to 19 Degrees as a contribution.",
 assess="Rubric for task 4 (design a test). Excellent: falsifiable claim, appropriate data and holder named, a clear result that would disprove it, and a confounder addressed. Sound: testable claim and data named, disproof stated loosely. Developing: claim restated without a clear test.")

primary = page("Shark detectives: the warm-water line", "19 Degrees · classroom sheet · ages 8 to 11", f"""{BTN}
<div class="hero"><div>
<p>Bull sharks like warm water. Scientists have records of {bull['n']} bull shark bites in Australia since 1900. <b>Not one</b> happened when the sea was colder than 19°C (66°F).</p>
<div class="fact">The line where the sea stays 19°C or warmer for half the year has moved about <b>{km} km</b> ({mi} miles) south since your grandparents were kids.</div>
<p>Look at the map. The orange line is now. The blue line is 1950 to 1979.</p></div>{MAP}</div>
<h2>Your mission</h2><ol>
<li>Find <b>Sydney</b> on the map. Is Sydney north or south of the orange line?{L(1)}</li>
<li>Draw an arrow on the map to show which way the warm-water line has moved.</li>
<li>Off Sydney, the sea used to be warm enough for bull sharks about <b>{round(syd['base'])} months</b> a year. Now it is about <b>{round(syd['recent'])} months</b>. How many more months is that?{L(1)}</li>
<li>For every person killed by a shark in Australia, about <b>{ratio}</b> people drown. Which is the bigger danger at the beach?{L(1)}</li>
<li>Draw yourself staying safe at the beach. (Hint: red and yellow flags!)<div class="box"></div></li></ol>
{WORDS}
<div class="ans">{TEACH(T_PRIMARY)}<b>Answer guide.</b> 1: Sydney is north of the orange line, so the water there gets warm enough for bull sharks. 2: the arrow points south (down the map). 3: about {round(syd['recent'])-round(syd['base'])} more months. 4: drowning, by far. 5: swimming between the red and yellow flags, where lifesavers are watching.</div>""")

middle = page("Sharks, warm water and a moving line", "19 Degrees · classroom sheet · ages 12 to 15", f"""{BTN}
<div class="hero"><div>
<p>Since 1900, Australia has recorded {bull['n']} bull shark bites, and <b>not one</b> happened in a month when the sea was cooler than 19°C (66°F). As the ocean warms, water that warm reaches further south and lasts longer each year.</p>
<div class="fact">Before 1960, <b>{pct(O[0])}%</b> of bull shark bites were in coastal waters; since 2015, <b>{pct(O[-1])}%</b>. Western Australia has had more bull shark bites since 2020 (<b>{W['post']}</b>) than in the 120 years preceding (<b>{W['pre']}</b>).</div></div>{MAP}</div>
{CHART}
<h2>Questions</h2><ol>
<li>Read the chart. About how many months a year was the sea off Sydney 19°C or warmer in the 1900s, and in the 2020s? By what percentage has the warm season grown?{L()}</li>
<li>Using the map, about how far south has the half-year 19°C line moved since 1950–79? Name one town that now sits inside the warm zone.{L()}</li>
<li>Oceanic sharks and rays worldwide are down about 71% since 1970, yet bites near some Australian beaches are rising. Give two reasons both can be true.{L(3)}</li>
<li>Bull shark bites used to happen mostly in rivers and harbors. Now most are in coastal waters, mostly off surf beaches. Suggest one reason, and one way to test it.{L(3)}</li>
<li>About {ratio} people drown on Australia's coast for every shark death. Write one safety message for your school newsletter.{L(2)}</li></ol>
{WORDS}
<div class="ans">{TEACH(T_MIDDLE)}<b>Answer guide.</b> 1: about {syd['rows'][0]['months']:.0f} months in the 1900s and about {syd['rows'][-1]['months']:.0f} in the 2020s; the warm season is about {inc}% longer ({syd['base']:.1f} to {syd['recent']:.1f} months, comparing 1900–1930 with the last ten years). 2: about {km} km; Eden (or Batemans Bay, Narooma). 3: sharks are in different places and seasons as warm water spreads; more people swim; rain and murky water bring sharks close to beaches; fewer sharks overall does not mean fewer near one coast. 4: possible reasons: warmer water near beaches for longer, runoff after heavy rain, better species identification; test by comparing bite places with river mouths and rainfall, or using only bites where the species was confirmed. 5: any message about swimming between the flags, avoiding murky water after rain, or checking the SharkSmart app.</div>""")

senior = page("Testing a climate claim with real data", "19 Degrees · classroom sheet · ages 16 and up", f"""{BTN}
<div class="hero"><div>
<p><b>The claim:</b> warming seas are giving bull sharks more time and more coastline, and bites have followed. Your job is to test it like a scientist, using the data from 19 Degrees (Researchers tab, then Download the data and images).</p>
<div class="fact">Bull shark bites below 19°C: <b>{bull['below']} of {bull['n']}</b>. Coastal share: <b>{pct(O[0])}%</b> (1900–59) to <b>{pct(O[-1])}%</b> (since 2015). WA: <b>{W['post']}</b> since 2020 against <b>{W['pre']}</b> in 1900–2019.</div></div>{MAP}</div>
{CHART}
<h2>Tasks</h2><ol>
<li><b>Rate, not count.</b> WA had {W['pre']} bull shark bites in 120 years and {W['post']} in {W['years_post']} years. Work out both yearly rates and how many times larger the recent rate is. Why compare rates rather than totals?{L()}</li>
<li><b>Chance or change?</b> The page reports p = {W['p_fisher']:.3f} for the WA bull shark share of all shark bites. In one sentence, explain what that p-value means, and one thing it does not tell you.{L(3)}</li>
<li><b>Other explanations.</b> List three things besides warming that could explain bites moving into coastal waters (see "Could something else explain it?" in the page's Researchers tab). For each, describe evidence that would rule it in or out.{L(4)}</li>
<li><b>Design a test.</b> Pick one of the twenty-two testable claims (C1–C22) in the page's Researchers tab. State the claim, the data you would need, who holds it, what result would support it and what would prove it wrong.{L(4)}</li>
<li><b>Communicate.</b> Write a 40-word social post that is accurate, not scary, and includes one number and one safety action.{L(2)}</li></ol>
<div class="ans">{TEACH(T_SENIOR)}<b>Answer guide.</b> 1: {W['pre']}/120 ≈ {W['pre']/120:.2f} a year against {W['post']}/{W['years_post']} ≈ {W['post']/W['years_post']:.2f} a year, about {W['post']/W['years_post']/(W['pre']/120):.0f} times higher; rates allow for periods of different length. 2: if nothing had really changed, a difference this big would turn up by chance only about {max(1,round(W['p_fisher']*1000))} times in 1,000; it does not say why the change happened or how big it matters. 3: identification (early river bites were labeled bull sharks partly by place), beach nets since the 1930s, rain and runoff plumes, more people surfing and spearfishing; test with confirmed-species bites, net locations, rainfall and river-mouth distance. 4: any claim with a measurable, falsifiable outcome. 5: for example, "Bull sharks never bite in water below 19°C, and that water now lasts 3 months longer off Sydney. Stay out of murky water after heavy rain and swim between the flags."</div>""")

hub = page("Classroom sheets", "19 Degrees · for teachers", f"""<p>Three printable versions of the same lesson, each with a data map of the east coast. The last page of each sheet holds the teacher notes (learning intentions, success criteria, big ideas, curriculum links for Australia, the US, England, the IB and others, lesson sequence, differentiation, assessment and a wellbeing note) and the answer guide, and prints separately. All numbers update with the data. Free to use and adapt under CC BY 4.0.</p>
<div class="hero"><div class="cards">
<a class="card" href="classroom-primary.html"><span class="k">Ages 8 to 11 · 45–60 min</span><h3>Shark detectives</h3><span>Read a map, count months, draw a safety poster.</span><span class="k">Habitats · adaptation · map and data skills</span></a>
<a class="card" href="classroom-middle.html"><span class="k">Ages 12 to 15 · 50–60 min</span><h3>A moving line</h3><span>Read a chart, work out a percentage, explain a pattern.</span><span class="k">Ecosystems · percentages · evaluating explanations</span></a>
<a class="card" href="classroom-senior.html"><span class="k">Ages 16 and up · 1–2 lessons</span><h3>Testing a climate claim</h3><span>Rates, p-values, other explanations and designing a test with real data.</span><span class="k">Climate change · statistics · designing a test</span></a>
</div>{MAP}</div>""")
for name, html in (("classroom.html", hub), ("classroom-primary.html", primary), ("classroom-middle.html", middle), ("classroom-senior.html", senior)):
    open(os.path.join(out, name), "w").write(html)
print("wrote classroom sheets to", out)
