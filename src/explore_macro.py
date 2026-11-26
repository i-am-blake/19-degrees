"""Look only: macro check of what people search about sharks. Google Trends interest over time (2004 to now, AU and US),
each question group chained to the same anchor so groups can be compared; Wikipedia monthly pageviews (real counts, 2015 to now);
and a re-pull of Google suggestions with an Australian language setting to test the AU/US split. Changes nothing on the site."""
import json, time, urllib.parse, urllib.request
UA = {"User-Agent": "19-degrees/1.0 (+https://19-degrees.org) research"}
def get(u, t=40):
    try: return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=t).read().decode("utf-8", "replace")
    except Exception as e: return "ERR " + repr(e)[:150]
out = {"made": time.strftime("%Y-%m-%d"), "errors": {}}
ANCHOR = "shark attack"
GROUPS = {  # one or two plain search phrases per question group
    "incident": ["shark attack today"], "rising": ["shark attacks increasing", "why so many sharks"], "season": ["shark season"],
    "counts": ["how many shark attacks", "shark attack statistics"], "nets": ["shark nets", "drumlines"], "safety": ["avoid sharks", "what attracts sharks"],
    "where": ["bull shark", "where do sharks live"], "rare": ["are sharks endangered", "shark attack odds"], "white": ["great white shark"], "tiger": ["tiger shark"]}
terms = [t for v in GROUPS.values() for t in v]
try:
    from pytrends.request import TrendReq
    tr = TrendReq(hl="en-US", tz=0, timeout=(10, 40)); out["trends"] = {}
    for geo in ("AU", "US"):
        for tf, lab in (("2004-01-01 2026-11-24", "all"), ("today 5-y", "5y")):
            res = {}
            for i in range(0, len(terms), 4):
                kw = [ANCHOR] + terms[i:i + 4]
                for k in range(3):
                    try: tr.build_payload(kw, timeframe=tf, geo=geo); df = tr.interest_over_time(); break
                    except Exception as e: print(geo, lab, kw, "retry", repr(e)[:80], flush=True); time.sleep(20 * (k + 1)); df = None
                if df is None or df.empty: continue
                a = df[ANCHOR].astype(float)
                for t in kw[1:]:  # each term as a share of the anchor, so batches line up
                    res[t] = {"mean_vs_anchor": round(float(df[t].mean() / max(a.mean(), 1e-9)), 3), "peak": str(df[t].idxmax())[:7],
                              "series": {str(ix)[:7]: int(v) for ix, v in df[t].items()}}
                res[ANCHOR] = {"series": {str(ix)[:7]: int(v) for ix, v in a.items()}, "peak": str(a.idxmax())[:7]}
                time.sleep(8)
            out["trends"][f"{geo}_{lab}"] = res; print("trends", geo, lab, len(res), "terms", flush=True)
except Exception as e: out["errors"]["trends"] = repr(e)[:200]; print("trends failed", repr(e)[:200], flush=True)
# Wikipedia pageviews: real monthly counts, English Wikipedia, people not bots
W = ["Shark_attack", "Shark_attacks_in_Australia", "Bull_shark", "Great_white_shark", "Tiger_shark", "Shark_net", "Shark_culling", "Drum_line",
     "List_of_fatal_shark_attacks_in_Australia", "List_of_fatal_shark_attacks_in_the_United_States", "International_Shark_Attack_File", "Shark"]
out["wiki"] = {}
for a in W:
    t = get(f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia.org/all-access/user/{a}/monthly/2015070100/2026110100")
    if t.startswith("ERR"): out["errors"]["wiki_" + a] = t; print("wiki", a, t[:80], flush=True); continue
    it = json.loads(t).get("items", []); out["wiki"][a] = {x["timestamp"][:6]: x["views"] for x in it}
    tot = sum(out["wiki"][a].values()); pk = max(out["wiki"][a], key=out["wiki"][a].get) if it else None
    print("wiki", a, "total", tot, "peak", pk, out["wiki"][a].get(pk), flush=True); time.sleep(0.5)
# Google suggestions again, with Australian vs US language settings, to test whether the AU/US split is real
out["split"] = {}
for q in ("why are there so many sharks", "when is shark season", "how many shark attacks", "is it safe to swim", "bull sharks"):
    for hl, gl in (("en-AU", "au"), ("en-US", "us")):
        t = get(f"https://suggestqueries.google.com/complete/search?client=firefox&hl={hl}&gl={gl}&q=" + urllib.parse.quote(q))
        out["split"][f"{q}|{gl}"] = json.loads(t)[1] if not t.startswith("ERR") else t; time.sleep(1)
same = sum(out["split"][f"{q}|au"] == out["split"][f"{q}|us"] for q in ("why are there so many sharks", "when is shark season", "how many shark attacks", "is it safe to swim", "bull sharks"))
print("google AU and US lists identical for", same, "of 5 stems", flush=True)
json.dump(out, open("../macro.json", "w"), indent=1)
