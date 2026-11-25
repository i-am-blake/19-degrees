"""Look only: what people publicly ask about sharks. Autocomplete suggestions from Google, Bing and DuckDuckGo
(Australia and the US), Google Trends related queries if reachable, and shark questions in the public WildChat
dataset of real chatbot conversations. Low volume, one request at a time. Changes nothing on the site."""
import json, time, urllib.parse, urllib.request
UA = {"User-Agent": "Mozilla/5.0 (compatible; 19-degrees research; +https://19-degrees.org)"}
def get(u, t=30):
    try: return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=t).read().decode("utf-8", "replace")
    except Exception as e: return "ERR " + repr(e)[:120]
STEMS = ["why are sharks", "why are there so many sharks", "why are shark attacks", "are sharks", "are shark attacks", "are bull sharks", "are great white sharks",
         "is it safe to swim", "is it safe to surf", "is it safe to swim after rain", "when is shark season", "when do sharks", "where do bull sharks", "where are sharks",
         "do sharks", "do shark nets", "do drumlines", "does climate change", "will sharks", "should i", "how to avoid sharks", "how many shark attacks", "what time of day do sharks",
         "what attracts sharks", "can sharks", "bull sharks", "great white sharks", "tiger sharks", "shark attack", "shark bite", "sharks in"]
ALPHA = ["sharks", "shark attack", "bull shark", "shark"]
QS = STEMS + [f"{a} {c}" for a in ALPHA for c in "abcdefghijklmnopqrstuvwxyz"]
ENG = {
    "google": lambda q, r: (f"https://suggestqueries.google.com/complete/search?client=firefox&hl=en&gl={r}&q=" + urllib.parse.quote(q), lambda t: json.loads(t)[1]),
    "bing": lambda q, r: (f"https://api.bing.com/osjson.aspx?mkt=en-{r.upper()}&query=" + urllib.parse.quote(q), lambda t: json.loads(t)[1]),
    "duckduckgo": lambda q, r: (f"https://duckduckgo.com/ac/?kl={r}-en&q=" + urllib.parse.quote(q), lambda t: [x["phrase"] for x in json.loads(t)]),
}
out = {"made": time.strftime("%Y-%m-%d"), "suggest": {}, "errors": {}}
for e, f in ENG.items():
    for r in ("au", "us"):
        k = f"{e}_{r}"; out["suggest"][k] = {}; errs = 0
        for q in QS:
            u, parse = f(q, r); t = get(u)
            if t.startswith("ERR"):
                errs += 1
                if errs >= 5: out["errors"][k] = t; break
                continue
            try: out["suggest"][k][q] = parse(t)
            except Exception as ex: out["errors"][k] = repr(ex)[:120]
            time.sleep(0.8)
        print(k, len(out["suggest"][k]), "stems answered,", sum(len(v) for v in out["suggest"][k].values()), "suggestions", out["errors"].get(k, ""), flush=True)
# Google Trends related queries (unofficial; often refused from cloud servers)
try:
    from pytrends.request import TrendReq
    tr = TrendReq(hl="en-AU", tz=600, timeout=(10, 30)); out["trends"] = {}
    for geo in ("AU", "US"):
        tr.build_payload(["shark", "shark attack", "bull shark"], timeframe="today 12-m", geo=geo)
        rq = tr.related_queries(); out["trends"][geo] = {kw: {s: (v[s].to_dict("records") if v.get(s) is not None else []) for s in ("top", "rising")} for kw, v in rq.items()}
        print("trends", geo, "ok", flush=True); time.sleep(5)
except Exception as e: print("trends failed:", repr(e)[:200], flush=True); out["errors"]["trends"] = repr(e)[:200]
# WildChat: real chatbot conversations, publicly released by AI2 (search the first user turn for shark questions)
out["wildchat"] = []
for ds in ("allenai/WildChat-1M", "allenai/WildChat-4.8M", "allenai/WildChat"):
    got = 0
    for off in range(0, 500, 100):
        t = get(f"https://datasets-server.huggingface.co/search?dataset={urllib.parse.quote(ds)}&config=default&split=train&query=shark&offset={off}&length=100", 60)
        if t.startswith("ERR"): out["errors"][ds] = t; break
        try: rows = json.loads(t).get("rows", [])
        except Exception: out["errors"][ds] = t[:150]; break
        for r in rows:
            row = r.get("row", {}); conv = row.get("conversation") or []
            first = next((m.get("content", "") for m in conv if m.get("role") == "user"), "")
            if "shark" in first.lower() and len(first) < 400 and row.get("language", "English") == "English":
                out["wildchat"].append({"q": first.strip(), "when": str(row.get("timestamp", ""))[:10], "country": row.get("country")})
        got += len(rows)
        if len(rows) < 100: break
        time.sleep(1)
    print("wildchat", ds, got, "rows,", len(out["wildchat"]), "short English shark questions so far", out["errors"].get(ds, ""), flush=True)
    if out["wildchat"]: break
json.dump(out, open("../questions.json", "w"), indent=1)
