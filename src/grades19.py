"""How claims are graded. One scale for every claim card; build19.py applies it and check19.py checks it.
Stages: Open -> Not testable yet -> First look -> Early result -> Supported -> Strong; or Ruled out.
  First look            data exists but is too thin to test (fewer than about 20 cases), or the card can only describe it.
  Early result          a test on the claim's own measure (exploratory: chosen after seeing the data). The verdict is fixed by
                        direction and p: supports it (predicted direction, p < 0.05), leans toward it (predicted direction,
                        p < 0.20), no clear link (p >= 0.20 or tests disagree), points the other way (opposite, p < 0.05).
  Main test and checks  the claim's main test sets the verdict; further tests can lower it (supports -> leans) but never raise it.
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
         "none": "Early result: no clear link", "other": "Early result: points the other way"}
STAGE = {"open": "Open", "nt": "Not testable yet", "look": "First look", "supported": "Supported", "strong": "Strong", "ruled": "Ruled out"}

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
    return V(True, max(ps))
def g_c26(D): i = D["iod"]["all"]; return V(i["ratio"] > 1, i["p"])
def g_c28(D):
    t = D["tigerrain"]["all"]["tiger"]; q = D["tigerqld"]["tiger"]
    return down(V(t["pct"] > 25, t["p"]), q["ratio"] > 1 and sig(q))
def g_c29(D):
    u = D["upwelling"]; return V(u["strongest_pct"] > 25, binom2(u["strongest_quarter"], u["n"], 0.25))

FIXED = {"c2": "look", "c7": "look", "c8": "nt", "c9": "look", "c20": "look", "c22": "look", "c30": "look",
         **{c: "open" for c in ("c10", "c11", "c12", "c13", "c14", "c15", "c17", "c27", "c31", "c32", "c33", "c34", "c35", "c36", "c37", "c38", "c39", "c40", "c41", "c42")}}
TESTS = {"c1": g_c1, "c3": g_c3, "c4": g_c4, "c5": g_c5, "c6": g_c6, "c16": g_c16, "c18": g_c18, "c19": g_c19, "c21": g_c21,
         "c23": g_c23, "c24": g_c24, "c25": g_c25, "c26": g_c26, "c28": g_c28, "c29": g_c29}

def grade(cid, D):
    """(data-status, label) for a claim card."""
    if cid in FIXED: s = FIXED[cid]; return s, STAGE[s]
    v = TESTS[cid](D)
    return ("ruled", STAGE["ruled"]) if v == "ruled" else ("early", LABEL[v])
