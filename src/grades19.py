"""How claims are graded. One scale for every claim card; build19.py applies it and check19.py checks it.
Stages: Open -> Not testable yet -> First look -> Early result -> Supported -> Strong; or Ruled out.
  First look            data exists but is too thin to test (fewer than about 20 cases), or the card can only describe it.
  Early result          a test on the claim's own measure (exploratory: chosen after seeing the data). The verdict is fixed by
                        direction and p: supports it (predicted direction, p < 0.05), leans toward it (predicted direction,
                        p < 0.20), no clear link (p >= 0.20 or tests disagree), points the other way (opposite, p < 0.05).
  Main test and checks  the claim's main test sets the verdict; further tests can lower it (supports -> leans) but never raise it.
  Evidence tiers        each tested claim names the kind of data it rests on (EVID below): 1 measured at the shark,
                        2 tracked by tag (detections on fixed receivers), 3 catch or survey with effort recorded, 4 stand-in, 5 no denominator
                        (bites, incidents, sightings), 6 projection. Tiers 4 to 6 reach "leans toward it" at most, and
                        "leans the other way" at most when the claim is about sharks rather than the records themselves.
  Stand-ins             a test on a stand-in for the claim's measure (residents for beach visits, chlorophyll for baitfish)
                        reaches "leans toward it" at most.
  Supported / Strong    need a test set in advance plus a second dataset, region or method (Supported), or two or more
                        independent datasets or regions, a plausible mechanism and agreement with peer-reviewed work (Strong).
                        None qualify yet: every test so far was chosen after seeing the data.
  Ruled out             the claim's own "rules it out" condition is met, and the 95% range excludes an effect worth acting on,
                        set here as a 1.5-times rise. Without a 95% range, a null result is "no clear link", not "ruled out".
Records like these can't prove cause, so the top grade is Strong, never Proven."""
import math
from statistics import NormalDist

LABEL = {"supports": "Early result: supports it", "leans": "Early result: leans toward it",
         "none": "Early result: no clear link", "other": "Early result: points the other way",
         "leansother": "Early result: leans the other way"}
STAGE = {"open": "Open", "nt": "Not testable yet", "look": "First look", "supported": "Supported", "strong": "Strong", "ruled": "Ruled out"}
# Words shown on the site. The full labels above stay in grades_history.json, so renaming never looks like a new result.
SHORT = {LABEL["supports"]: "Early: yes", LABEL["leans"]: "Leans yes", LABEL["none"]: "Unclear", LABEL["other"]: "Early: no",
         LABEL["leansother"]: "Leans no", "Open": "Not yet tested", "Not testable yet": "Can't test yet"}
def show(label): return SHORT.get(label, label)
def css(st, label):  # badge color follows the direction of the result
    s = show(label)
    return {"Early: yes": "cstat early", "Leans yes": "cstat early", "Leans no": "cstat no", "Early: no": "cstat no", "Unclear": "cstat unc"}.get(s,
        {"ruled": "cstat ruled", "look": "cstat look", "nt": "cstat nt", "supported": "cstat sup", "strong": "cstat strong"}.get(st, "cstat"))

def V(ok, p):
    if p is None: return "none"
    if ok and p < 0.05: return "supports"
    if ok and p < 0.20: return "leans"
    if not ok and p < 0.05: return "other"
    return "none"
def down(v, check_ok):  # a failed check lowers "supports" to "leans"
    return "leans" if v == "supports" and not check_ok else v
cap = lambda v: "leans" if v == "supports" else v  # stand-in measure, or a count with no fair "per"

from scipy.stats import binomtest, fisher_exact
def binom2(k, n, q): return float(binomtest(k, n, q).pvalue)  # two-sided exact
def wilson(k, n, z=1.96):
    p = k / n; c = (p + z * z / (2 * n)) / (1 + z * z / n); h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return c - h, c + h
def fisher2(a, b, c, d): return float(fisher_exact([[a, b], [c, d]])[1])
sig = lambda x, k="p": x.get(k) is not None and x[k] < 0.05

# claims whose numbers sit in the card text rather than the data block; the rule still applies to them

def g_c1(D):  # share of catch stands in for catch per unit of effort; the published effort-standardised test comes first
    b = D["literature"]["banaghan2025"]
    if not ((b["south_drumline_r"] > 0 and b["south_drumline_sig"]) or (b["south_gillnet_r"] > 0 and b["south_gillnet_sig"])):
        return "none"  # catch per unit of effort in the south shows no clear rise (Banaghan et al. 2025)
    s = D["catchshare"]["south"]; return cap(V(s["diff_pts"] > 0, s["p"]))
def g_c3(D):  # projection: model agreement instead of p. "Supports" needs 80% of models past the border (about 37.5°S);
    e = D["proj"]["eden"]  # the projected beaches stop at Eden (37.1°S), so for now the best it can reach is "leans"
    return "leans" if e["median"] >= 6 else "ruled"
def g_c4(D): c = D["chlorophyll"]["all"]; return cap(V(c["pct"] > 25, c["p"]))
def g_c5(D):
    w = D["whitecool"]; b = math.log(1 + w["trend_pct_per_year"] / 100)
    z = NormalDist().inv_cdf(1 - w["trend_p"] / 2); se = abs(b) / z if z > 0 else float("inf")
    if not sig(w, "trend_p") and math.exp((b + 1.96 * se) * (len(w["per_year"]) - 1)) < 1.5: return "ruled"
    h = D["whales"]; return V(h["white_pct"] > h["other_pct"], h["p"])
def g_c6(D):
    b = D["rain"]["bull"]; r = D["rivers"]["bull"]
    return down(V(b["q_pct"] > 25, b["q_p"]), r["pct"] > 25 and sig(r))
def g_c16(D):
    c = D["imos"]["c16"]; r = c.get("long_run")
    return down(V(c["slope"] > 0, c["p"]), r is None or (r["slope"] > 0 and sig(r)))
def g_c18(D):
    d = {x["decade"]: x for x in D["coastpop"]["decades"]}; a, z = d[1990], d[max(d)]
    ea, ez = a["people"] * a["years"], z["people"] * z["years"]
    p = binom2(z["bites"], a["bites"] + z["bites"], ez / (ea + ez))
    return cap(V(z["bites"] / ez > a["bites"] / ea, p))
def g_c19(D):
    h = D["heat"]; k = sum(h[s]["t"] for s in h); n = sum(h[s]["n"] for s in h)
    a = D["mhw"]["all"]
    return down(V(k / n > 0.10, binom2(k, n, 0.10)), a["pct"] > a["expected_pct"] and sig(a))
def g_c21(D):
    t = D["fieldnotes"]["time"]; b = t["bull"]; o = [t["white"], t["tiger"]]
    on, ok = sum(x["n"] for x in o), sum(x["night"] for x in o)
    return cap(V(b["night"] / b["n"] > ok / on, fisher2(b["night"], b["n"] - b["night"], ok, on - ok)))
def g_c23(D): t = D["california"]["test"]; return V(t["shift_km"] > 0, t["p"])
def g_c24(D):
    a = D["lunar"]["all"]
    k, n = a["near"], a["n"]; p = binom2(k, n, 0.5)
    if p >= 0.05 and wilson(k, n)[1] < 0.6: return "ruled"  # 60% near the moons = 1.5 times the odds chance gives
    return V(k / n > 0.5, p)
def g_c25(D):
    ps = []
    for g in ("africa", "us"):
        x = D["obis"]["groups"][g]["bull"]; q = x["cell_months_below_pct"] / 100
        ps.append(binom2(x["below"], x["days"], q))
    v = V(True, max(ps))
    if "daily" in D:  # the stricter daily test, with its rule set in advance: under 5% of US shark-days below 19°C
        v = down(v, D["daily"]["us"]["bull"]["below19_pct"] < D["daily"]["rule"]["supports_below_pct"])
    return v
def g_c43(D):
    m = D["size"]["main"]; sm, lg = m["by_shark"]["small"], m["by_shark"]["large"]
    v = V(sm["winter_sharks"] / sm["sharks"] > lg["winter_sharks"] / lg["sharks"], m["p"])
    return down(v, D["size"]["checks"]["without_clarence"]["by_day"]["small"]["days"] >= 100)  # small sharks tracked in a second river
def g_c26(D): i = D["iod"]["all"]; return V(i["ratio"] > 1, i["p"])
def g_c28(D):
    t = D["tigerrain"]["all"]["tiger"]; q = D["tigerqld"]["tiger"]
    return down(V(t["pct"] > 25, t["p"]), q["ratio"] > 1 and sig(q))
def g_c29(D):
    u = D["upwelling"]; return V(u["strongest_pct"] > 25, binom2(u["strongest_quarter"], u["n"], 0.25))

FIXED = {"c2": "look", "c4": "look", "c7": "look", "c8": "nt", "c9": "look", "c20": "look", "c21": "look", "c22": "look", "c30": "look",
         **{c: "open" for c in ("c10", "c11", "c12", "c13", "c14", "c15", "c17", "c27", "c31", "c32", "c33", "c34", "c35", "c36", "c37", "c38", "c39", "c40", "c41", "c42")}}
TESTS = {"c1": g_c1, "c3": g_c3, "c5": g_c5, "c6": g_c6, "c16": g_c16, "c18": g_c18, "c19": g_c19,
         "c23": g_c23, "c24": g_c24, "c25": g_c25, "c26": g_c26, "c28": g_c28, "c29": g_c29, "c43": g_c43}

# Evidence tiers: what kind of data a result rests on, strongest first. The strongest tier a claim has sets how high its
# grade can go: tiers 1 and 2 up to Strong, tier 3 up to Supported, tiers 4 to 6 no higher than "leans toward it".
TIER = {1: "measured at the shark", 2: "tracked by tag", 3: "catch or survey with effort recorded",
        4: "stand-in", 5: "no denominator", 6: "projection"}
CEILING = {1: "Strong", 2: "Strong", 3: "Supported", 4: 'Early result: leans toward it', 5: 'Early result: leans toward it', 6: 'Early result: leans toward it'}
BITES = "Bite records, which follow where and when people are in the water"
EVID = {
 "c1": ((3, 4), lambda D: "Published catch per unit of effort (Banaghan et al. 2025). This site's own figure is share of catch, a stand-in."),
 "c3": ((6,), lambda D: "Climate model projections. The grade follows the share of models that agree."),
 "c5": ((3, 5), lambda D: "White sharks caught in Queensland shark-control gear, where the gear in the water is known, and bite records."),
 "c6": ((3, 5), lambda D: BITES + ", against rainfall (main test). Queensland shark-control catches against river flow (check)."),
 "c16": ((2,), lambda D: f'{D["imos"]["c16"]["sharks"]} tagged sharks, 2010 to {D["imos"]["c16"]["recent_to"]}. Receivers changed over the period, and the trend fades at long-running stations.'),
 "c18": ((5,), lambda D: "Bite records per coastal resident, a stand-in for beach visits."),
 "c19": ((5,), lambda D: BITES + ", against hot days and marine heatwaves."),
 "c23": ((5,), lambda D: "Incident records by period, with no count of beach visits."),
 "c24": ((5,), lambda D: BITES + ", against the moon's cycle."),
 "c25": ((1, 4), lambda D: f'Temperature tags on {D["tagtemp"]["sharks"]} bull sharks in Australia and {D["tags_sa"]["sharks"]} in South Africa. Satellite temperature at {D["daily"]["us"]["bull"]["shark_days"] + D["daily"]["africa"]["bull"]["shark_days"]:,} record-days on two more coasts, a stand-in for the water at the shark.'),
 "c26": ((5,), lambda D: "Bite records per year, against the Indian Ocean Dipole."),
 "c28": ((3, 5), lambda D: BITES + ", against rainfall (main test). Queensland shark-control catches against river flow (check)."),
 "c29": ((5,), lambda D: "Incident records against upwelling strength."),
 "c43": ((2,), lambda D: f'{D["size"]["sharks_with_length"]} tagged sharks with a length at tagging. Small sharks were tracked through winter in one river only.'),
}
# Claims that are about the bite or incident records themselves (where incidents are, when bites fall), not about what
# sharks do. For these, records with no count of people are the right measure, so a clear opposite result stands.
ABOUT_RECORDS = {"c19", "c23", "c24"}
def evidence(cid, D):
    """The 'Evidence' line on a tested card: tier, what it rests on, and how high this kind of evidence can go."""
    tiers, rests = EVID[cid]; names = " and ".join(f"tier {t} ({TIER[t]})" for t in tiers)
    return f"{names[0].upper()}{names[1:]}. {rests(D)} Highest grade this evidence can reach: {show(CEILING[min(tiers)])}."

def grade(cid, D):
    """(data-status, label) for a claim card."""
    if cid in FIXED: s = FIXED[cid]; return s, STAGE[s]
    v = TESTS[cid](D)
    if v == "supports" and min(EVID[cid][0]) >= 4: v = "leans"   # the evidence tier caps the grade
    if v == "other" and min(EVID[cid][0]) >= 4 and cid not in ABOUT_RECORDS: v = "leansother"   # and caps it the other way too
    return ("ruled", STAGE["ruled"]) if v == "ruled" else ("early", LABEL[v])
