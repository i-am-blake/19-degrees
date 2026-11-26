"""Look only: more public search data. 1) Google Trends by state/city and related queries per Australian state;
2) a baseline for a monthly question tracker (autocomplete for question x place on Google, Bing, DuckDuckGo, YouTube);
3) Wikipedia daily reads; 4) YouTube suggestions (inside 2); 5) GDELT news volume. Changes nothing on the site."""
import json, time, urllib.parse, urllib.request
UA = {"User-Agent": "19-degrees/1.0 (+https://19-degrees.org) research"}
def get(u, t=60):
    for k in range(3):
        try: return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=t).read().decode("utf-8", "replace")
        except Exception as e:
            err = "ERR " + repr(e)[:150]
            if "404" in err: return err
            time.sleep(5 * (k + 1))
    return err
out = {"made": time.strftime("%Y-%m-%d"), "errors": {}}
# 1) Trends by region, and what each Australian state searches
try:
    from pytrends.request import TrendReq
    tr = TrendReq(hl="en-AU", tz=-600, timeout=(10, 40)); out["region"] = {}; out["related"] = {}
    def build(kw, geo, tf="today 5-y"):
        for k in range(4):
            try: tr.build_payload(kw, timeframe=tf, geo=geo); return True
            except Exception as e: print("retry", geo, repr(e)[:80], flush=True); time.sleep(30 * (k + 1))
        return False
    for geo, res in (("AU", "REGION"), ("AU", "CITY"), ("US", "REGION")):
        if build(["shark attack", "bull shark", "great white shark", "shark season"], geo):
            try:
                df = tr.interest_by_region(resolution=res, inc_low_vol=True, inc_geo_code=False)
                out["region"][f"{geo}_{res}"] = {c: {k: int(v) for k, v in df[c].sort_values(ascending=False).head(15).items()} for c in df.columns}
                print("region", geo, res, "ok", flush=True)
            except Exception as e: out["errors"][f"region_{geo}_{res}"] = repr(e)[:150]
        time.sleep(12)
    for geo in ("AU-NSW", "AU-WA", "AU-QLD", "AU-SA", "AU-VIC"):
        if build(["shark"], geo, "today 12-m"):
            try:
                rq = tr.related_queries()["shark"]
                out["related"][geo] = {s: (rq[s].head(20).to_dict("records") if rq.get(s) is not None else []) for s in ("top", "rising")}
                print("related", geo, "ok", flush=True)
            except Exception as e: out["errors"][f"related_{geo}"] = repr(e)[:150]
        time.sleep(12)
except Exception as e: out["errors"]["trends"] = repr(e)[:200]; print("trends failed", repr(e)[:200], flush=True)
# 2) Question tracker baseline (also YouTube)
PLACES_AU = ["sydney", "sydney harbour", "perth", "wa", "gold coast", "byron bay", "newcastle", "brisbane river", "adelaide", "australia"]
PLACES_US = ["cape cod", "florida", "hawaii", "california", "south africa", "maine"]
STEMS = ["why are there so many sharks in {}", "when is shark season in {}", "is it safe to swim in {}", "shark attack {}", "bull sharks {}", "how many shark attacks in {}"]
ENG = {
    "google": lambda q, r: (f"https://suggestqueries.google.com/complete/search?client=firefox&hl=en-{r.upper()}&gl={r}&q=" + urllib.parse.quote(q), lambda t: json.loads(t)[1]),
    "youtube": lambda q, r: (f"https://suggestqueries.google.com/complete/search?client=firefox&ds=yt&hl=en-{r.upper()}&gl={r}&q=" + urllib.parse.quote(q), lambda t: json.loads(t)[1]),
    "bing": lambda q, r: (f"https://api.bing.com/osjson.aspx?mkt=en-{r.upper()}&query=" + urllib.parse.quote(q), lambda t: json.loads(t)[1]),
    "duckduckgo": lambda q, r: (f"https://duckduckgo.com/ac/?kl={r}-en&q=" + urllib.parse.quote(q), lambda t: [x["phrase"] for x in json.loads(t)]),
}
out["tracker"] = {}
for places, r in ((PLACES_AU, "au"), (PLACES_US, "us")):
    for p in places:
        for st in STEMS:
            q = st.format(p); row = {}
            for e, f in ENG.items():
                u, parse = f(q, r); t = get(u, 20)
                try: row[e] = parse(t) if not t.startswith("ERR") else t
                except Exception as ex: row[e] = "ERR " + repr(ex)[:80]
                time.sleep(0.6)
            out["tracker"][q] = row
    print("tracker", r, "done", flush=True)
# 3) Wikipedia daily reads (people, not bots)
out["wiki_daily"] = {}
for a in ("Shark_attack", "Bull_shark", "Great_white_shark", "List_of_fatal_shark_attacks_in_Australia", "Shark_attacks_in_Australia", "Shark_net"):
    t = get(f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia.org/all-access/user/{a}/daily/20190101/20261124")
    if t.startswith("ERR"): out["errors"]["wiki_" + a] = t; continue
    out["wiki_daily"][a] = {x["timestamp"][:8]: x["views"] for x in json.loads(t).get("items", [])}
    print("wiki daily", a, len(out["wiki_daily"][a]), flush=True); time.sleep(0.5)
# 5) GDELT news volume: articles mentioning shark attacks or bites, from Australian and US news sources, by day
out["gdelt"] = {}
for c in ("AS", "US"):
    q = urllib.parse.quote(f'("shark attack" OR "shark bite") sourcecountry:{c}')
    for lab, span in (("since2017", "&startdatetime=20170101000000&enddatetime=20261124000000"), ("24m", "&timespan=24m")):
        t = get(f"https://api.gdeltproject.org/api/v2/doc/doc?query={q}&mode=timelinevolraw&format=json{span}", 120)
        try:
            j = json.loads(t); s = j["timeline"][0]["data"]
            out["gdelt"][f"{c}_{lab}"] = {x["date"][:8]: x["value"] for x in s}; print("gdelt", c, lab, len(s), flush=True); break
        except Exception: out["errors"][f"gdelt_{c}_{lab}"] = t[:200]; print("gdelt", c, lab, "failed", t[:120], flush=True)
        time.sleep(6)
json.dump(out, open("../search.json", "w"))
