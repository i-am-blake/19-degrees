"""A dated snapshot of where the evidence stands, saved by every weekly build so the history can be shown later.
Usage: python3 -I snapshot19.py <built 19-degrees.html> <history_dir>
Writes <history_dir>/<build date>.json (claim grades, headline numbers, data versions) and refreshes index.json."""
import html, json, os, re, sys
page = open(sys.argv[1], encoding="utf-8").read(); out = sys.argv[2]; os.makedirs(out, exist_ok=True)
D = json.loads(re.search(r'<script type="application/json" id="n19-data">(.*?)</script>', page, re.S).group(1).replace("<\\/", "</"))
claims = []
for cid, status, body in re.findall(r'<article class="claim" id="(c\d+)" data-status="(\w+)">(.*?)</article>', page, re.S):
    m = re.search(r'<span class="(cstat[^"]*)">([^<]*)</span>', body)
    t = re.search(r"<h4>(.*?)</h4>", body, re.S)
    claims.append(dict(id=cid.upper(), status=status, grade=html.unescape(m.group(2)).strip() if m else "",
                       grade_class=m.group(1).replace("cstat", "").strip() if m else "",
                       title=html.unescape(re.sub(r"<[^>]+>", "", t.group(1))).strip() if t else ""))
if not claims: sys.exit("snapshot: no claim cards found")
sp = {k: {f: v[f] for f in ("n", "below", "min", "median", "max")} | {"confirmed": v["conf"]["n"], "confirmed_below": v["conf"]["below"]} for k, v in D["species"].items()}
syd = next((b for b in D["beaches"] if b["key"] == "sydney"), {})
snap = dict(date=D["built"], bites_to=D.get("asid_last"), sea_temperature_to=D.get("sst_last"), species=sp,
            sydney_months=dict(base=syd.get("base"), recent=syd.get("recent")), half_year_line_lat=D["zones"].get("line"),
            claims=claims, counts={g: sum(1 for c in claims if c["grade"] == g) for g in sorted({c["grade"] for c in claims})})
json.dump(snap, open(os.path.join(out, D["built"] + ".json"), "w"), indent=1, ensure_ascii=False)
dates = sorted(f[:-5] for f in os.listdir(out) if re.fullmatch(r"\d{4}-\d{2}-\d{2}\.json", f))
json.dump(dict(snapshots=dates), open(os.path.join(out, "index.json"), "w"), indent=1)
print(f"snapshot {D['built']}: {len(claims)} claims, {len(dates)} snapshots in all")
