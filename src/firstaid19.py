"""Claim C9 (first look): how many shark-bite deaths involved only a limb wound, the kind a tourniquet or firm pressure can reach?
Usage: python3 -I firstaid19.py <asid.csv>
Uses the Australian Shark-Incident Database's injury location for unprovoked fatal bites. "Limb only" means every listed
wound is on an arm, hand, leg, thigh, calf or foot. The pelvic region and shoulder count as junctional (hard to tourniquet)
and the torso and head as trunk. Bites with no location or no body recovered are counted separately."""
import csv, sys, collections
LIMB = {"leg", "thigh", "calf", "foot", "arm", "hand", "legs", "arms"}
def cls(loc):
    l = loc.lower().replace(" and ", ",").replace(";", ",")
    if not l.strip(): return "unknown"
    if "not recovered" in l: return "no body"
    parts = {p.strip() for p in l.split(",") if p.strip()}
    if parts <= LIMB: return "limb only"
    if any("torso" in p or "head" in p for p in parts): return "trunk or head"
    return "junctional"
rows = [x for x in csv.DictReader(open(sys.argv[1])) if x["Victim.injury"].strip() == "fatal" and x["Provoked/unprovoked"].strip() == "unprovoked" and x["Incident.year"].isdigit()]
for lab, y0 in (("since 1900", 1900), ("since 1960", 1960), ("since 2000", 2000)):
    c = collections.Counter(cls(x["Injury.location"]) for x in rows if int(x["Incident.year"]) >= y0)
    known = c["limb only"] + c["trunk or head"] + c["junctional"]
    print(f"{lab}: deaths {sum(c.values())}, known wound {known}, limb only {c['limb only']} ({100*c['limb only']/known:.0f}%), trunk or head {c['trunk or head']}, junctional {c['junctional']}, no body {c['no body']}, unknown {c['unknown']}")
