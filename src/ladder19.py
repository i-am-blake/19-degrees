"""The evidence ladder: one page per group of safety products (/safety-check/<group>), each product placed on the
highest rung its independent tests have reached. A summary never claims a rung above that: a product shown only to
cut bait-taking is never described as cutting bites, and none is described as protecting people until a study of
real-world use shows it. Rungs are set by hand below from the published tests linked on the Safety page; the build
stops if a product on that page has no rung, so a new product can't go up without one."""
import re, sys

# Deterrents (electric, magnetic and chemical, visual, barriers): does it keep sharks away?
DETER = ("Changed shark behavior in a test", "Cut bait-taking in a field trial",
         "Cut bites on boards or decoys in a field trial", "Shown to protect people in real-world use")
# Bite-resistant fabric: does it reduce the injury?
FABRIC = ("Resisted cutting or puncture in material tests", "Less damage when bitten by live sharks in a trial",
          "Fewer or less severe injuries in real bites")
# Bleeding control: does it save lives?
BLEED = ("Worked in a controlled test", "Used in real rescues", "Shown to improve survival in a study of real use")
LADDER = {"deter": DETER, "fabric": FABRIC, "bleed": BLEED}
# What each rung lets a summary say, and what it may not say yet
SAY = {
 "deter": ("has changed shark behavior in a test, but hasn't been shown to cut bait-taking, cut bites, or protect people",
           "has cut bait-taking in a field trial, but hasn't been shown to cut bites or to protect people in real-world use",
           "has cut bites on boards or decoys in a field trial, but hasn't been shown to protect people in real-world use",
           "has been shown to protect people in real-world use"),
 "fabric": ("resisted cutting in material tests, but hasn't been tested with live sharks or in real bites",
            "was damaged less than standard neoprene when bitten by live sharks in a trial, but hasn't been shown to reduce injuries in real bites",
            "has been shown to reduce injuries in real bites"),
 "bleed": ("worked in a controlled test, but hasn't been studied in real rescues",
           "has been used in real rescues, but no study has yet measured whether it improves survival",
           "has been shown to improve survival in a study of real use"),
}
GROUPS = [  # (heading on the Safety page, address, ladder, page title, lead)
 ("Electric deterrents", "electric-deterrents", "deter", "Electric shark deterrents: what independent tests found",
  "Electric deterrents make a field around a board, a diver or a boat that sharks can sense with the pores on their snouts. They are the most tested shark deterrents, and the results vary by product and by shark."),
 ("Magnetic and chemical", "magnetic-and-chemical", "deter", "Magnetic and chemical shark deterrents: what independent tests found",
  "Bands with magnets and surf wax with a repellent smell are cheap and easy to use. Independent tests have mostly found no measurable effect."),
 ("Wetsuits and visual", "wetsuits-and-visual", "mixed", "Bite-resistant wetsuits and visual deterrents: what independent tests found",
  "Two different ideas: fabric that limits the damage if a shark bites, and patterns or lights meant to change how a shark sees a swimmer or surfer from below."),
 ("Bleeding control", "bleeding-control", "bleed", "Bleeding control after a shark bite: what the evidence says",
  "Most shark-bite deaths come from blood loss, often within minutes. Tourniquets and bleeding kits don't prevent bites; they are judged on whether they stop bleeding and save lives."),
 ("Barriers", "barriers", "deter", "Shark barriers: what independent tests found",
  "Barriers try to keep sharks out of a swimming area without catching or killing them. They have been tried in calm water; ocean surf is harder."),
]
# product -> (ladder, rung reached with an effect: 0 = no effect shown or not yet tested)
RUNG = {
 "Ocean Guardian Freedom+ Surf": ("deter", 3), "Ocean Guardian Freedom+ Surf Shortboard": ("deter", 2),
 "Ocean Guardian Freedom7 (Shark Shield)": ("deter", 3), "Ocean Guardian Scuba7": ("deter", 2), "Ocean Guardian BOAT01": ("deter", 2),
 "Rpela (first version)": ("deter", 0), "Rpela V2": ("deter", 3), "E-Shark Force": ("deter", 0), "NoShark": ("deter", 0),
 "Electronic Shark Defense System": ("deter", 0),
 "SharkBanz bracelet": ("deter", 0), "SharkBanz surf leash": ("deter", 0), "SharkBanz Zeppelin": ("deter", 1), "Chillax Wax": ("deter", 0),
 "SharkStop": ("fabric", 2), "ActionTX-S": ("fabric", 2), "Aqua Armour": ("fabric", 2), "Brewster": ("fabric", 2),
 "Kevlar-lined neoprene": ("fabric", 2), "SAMS patterned wetsuits": ("deter", 1), "Counter-illumination lights": ("deter", 3),
 "OMNA marine tourniquet and tourniquet leash": ("bleed", 1), "Community Shark Bite Kits": ("bleed", 2),
 "Exclusion Barrier": ("deter", 1), "Sharksafe Barrier": ("deter", 1), "Eco-friendly surf barriers (NSW north coast)": ("deter", 0),
}
# where a single trial reached a rung for only some species, say so
NOTE = {
 "Ocean Guardian Freedom7 (Shark Shield)": "The bite reduction was for tiger sharks only; there was no effect on white sharks.",
 "Rpela V2": "The bite reduction was for white sharks; for bull sharks only bait-taking was tested.",
 "Ocean Guardian Freedom+ Surf": "Bull sharks got used to it over three weeks of testing.",
 "Ocean Guardian Scuba7": "Tested with blacktip reef sharks, not the species that bite people most.",
 "Counter-illumination lights": "A research prototype, tested on seal-shaped decoys, not on surfers.",
 "SAMS patterned wetsuits": "The trial was promoted by the maker and not peer reviewed.",
}
DROP_RE = re.compile(r"\b(protect|safe from|prevent(s|ed)? (bites|attacks)|stops? (every|all) (bite|attack))", re.I)

def products(T):
    t = T[T.index('<table class="ptab">'):]; t = t[:t.index("</table>")]
    out, grp = [], None
    for r in re.findall(r"<tr[^>]*>.*?</tr>", t, re.S):
        if 'class="pg"' in r: grp = re.sub(r"<[^>]+>", "", r).strip(); continue
        c = re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", r, re.S)
        if len(c) < 5 or grp is None: continue
        name, use = (re.match(r"(.*?)<span>(.*?)</span>", c[0], re.S).groups() if "<span>" in c[0] else (c[0], ""))
        st = re.search(r'<span class="(cstat[^"]*)"[^>]*>(.*?)</span>', c[3])
        out.append(dict(group=grp, name=name.strip(), use=use.strip(), species=c[1].strip(), found=c[2].strip(), cls=st.group(1), grade=st.group(2), src=c[4]))
    return out

def ladder_html(kind, rung):
    steps = LADDER[kind]
    lis = "".join(f'<li class="{"on" if i < rung else ""}"><span class="sr">{"Reached" if i < rung else "Not shown"}: </span>{s}</li>' for i, s in enumerate(steps))
    return f'<ol class="ladder{" three" if len(steps) == 3 else ""}" aria-label="Evidence ladder">{lis}</ol>'

def summary(p, kind, rung, ruled):
    if rung == 0:
        return ("Independent tests found no measurable effect." if ruled else "Not yet tested in a completed trial.") + " It hasn't reached the first rung."
    return f"It {SAY[kind][rung - 1]}."

def build(T, out, write, page, relink, esc, text, BUILT, long_date):
    P = products(T)
    missing = [p["name"] for p in P if p["name"] not in RUNG]
    if missing: sys.exit("ladder19.py: give these products a rung: " + ", ".join(missing))
    known = {g[0] for g in GROUPS}
    if {p["group"] for p in P} - known: sys.exit("ladder19.py: new product group(s): " + ", ".join(sorted({p["group"] for p in P} - known)))
    # a "what tests found" line may not claim more than its rung allows
    for p in P:
        kind, rung = RUNG[p["name"]]
        if kind == "deter" and rung < 4 and DROP_RE.search(text(p["found"])):
            sys.exit(f"ladder19.py: '{p['name']}' says more than its rung ({rung}) allows: {text(p['found'])}")
    written = []
    allmax = {}
    for heading, slug, kind0, title, lead in GROUPS:
        ps = [p for p in P if p["group"] == heading]
        blocks = []
        for p in ps:
            kind, rung = RUNG[p["name"]]
            ruled = "ruled" in p["cls"]
            allmax[kind] = max(allmax.get(kind, 0), rung)
            blocks.append(f'''  <section class="prod" id="{re.sub(r"[^a-z0-9]+", "-", p["name"].lower()).strip("-")}">
    <h3>{p["name"]}</h3><p class="use">{p["use"]} · tested with: {p["species"]} · grade <span class="{p["cls"]}">{p["grade"]}</span></p>
    {ladder_html(kind, rung)}
    <p><b>{summary(p, kind, rung, ruled)}</b> {NOTE.get(p["name"], "")}</p>
    <p>What tests found: {relink(p["found"])}</p>
    <p class="note">Source: {p["src"]}</p>
  </section>''')
        kinds = {RUNG[p["name"]][0] for p in ps}
        tops = []
        for k in sorted(kinds):
            top = max(RUNG[p["name"]][1] for p in ps if RUNG[p["name"]][0] == k)
            if top < len(LADDER[k]):
                tops.append({"deter": "No product in this group has been shown to protect people in real-world use.",
                             "fabric": "No fabric has yet been shown to reduce injuries in real bites.",
                             "bleed": "No study has yet measured whether these improve survival in real use."}[k])
        legend = "".join(f'<li><b>{["Deterrents", "Bite-resistant fabric", "Bleeding control"][["deter", "fabric", "bleed"].index(k)]}:</b> ' + " → ".join(LADDER[k]) + "</li>" for k in sorted(kinds, key=["deter", "fabric", "bleed"].index))
        body = f'''  <p class="lead">{lead}</p>
  <p class="answer">{" ".join(tops) if tops else "At least one product here has reached the top rung."}</p>
  <h2>The evidence ladder</h2>
  <p>Each product is placed on the highest rung its published, independent tests have reached. Each rung is a harder test than the one before, and a summary here never claims a rung that hasn't been shown.</p>
  <ul>{legend}</ul>
  <p>The grade (Supported, Leans yes and so on) follows the <a href="/safety#h-products">Safety page's key</a> and also weighs how many tests agree and how good they were.</p>
  <h2>{len(ps)} product{"s" if len(ps) != 1 else ""}</h2>
{chr(10).join(blocks)}
  <h2>Limits</h2>
  <ul><li>Only products with a published test are listed. Products sold without any test we could find are left out.</li>
  <li>Trials use baits, boards and decoys, not people, and test a few species in a few places. Results may not carry over to other sharks, water or behavior.</li>
  <li>This is a guide to the evidence, not a safety rating or an endorsement or criticism of any maker. Follow lifesavers, beach signs and local authorities.</li></ul>
  <p class="meta">Updated {long_date(BUILT)} · <a href="/safety#h-products">All products on the Safety page</a> · <a href="/questions/do-shark-deterrents-work">Do shark deterrents work?</a></p>
'''
        desc = f"{heading}: {len(ps)} shark-safety products checked against published independent tests and placed on an evidence ladder from lab test to real-world protection. " + (tops[0] if tops else "")
        written.append(write(f"safety-check/{slug}", page(f"safety-check/{slug}", title, "Safety · evidence ladder", body, h1=title.split(":")[0],
                       desc=desc[:300], crumbs=[("Safety", "/safety")])))
    cards = "".join(f'<a href="/safety-check/{slug}"><span class="meta">{sum(1 for p in P if p["group"] == h)} products</span><b>{h}</b>{lead.split(". ")[0].rstrip(".")}.</a>' for h, slug, _, _, lead in GROUPS)
    body = f'''  <p class="lead">Every shark-safety product we could find with a published, independent test, placed on an evidence ladder: from a change in behavior in a test, to fewer bites in a field trial, to protecting people in real-world use.</p>
  <p class="answer">{"No deterrent has yet been shown to protect people in real-world use. " if allmax.get("deter", 0) < 4 else ""}The best electric deterrents have cut bites on boards and decoys in field trials, for some species.</p>
  <div class="cards">{cards}</div>
  <p class="meta">Updated {long_date(BUILT)} · <a href="/safety">Back to Safety</a></p>
'''
    written.append(write("safety-check/index", page("safety-check/", "Shark safety products: the evidence ladder", "Safety · evidence ladder", body,
                   desc="Shark deterrents, bite-resistant wetsuits, barriers and bleeding control, each placed on an evidence ladder from lab test to real-world protection.",
                   crumbs=[("Safety", "/safety")])))
    return written
