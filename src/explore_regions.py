"""Look only: what people ask about sharks, country by country, in their own language. Autocomplete (Google, DuckDuckGo,
Bing) for 11 countries, and Google Trends interest by country for the "shark attack" and "bull shark" topics. Changes nothing."""
import json, time, urllib.parse, urllib.request
UA = {"User-Agent": "Mozilla/5.0 (compatible; 19-degrees research; +https://19-degrees.org)"}
def get(u, t=25):
    try: return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=t).read().decode("utf-8", "replace")
    except Exception as e: return "ERR " + repr(e)[:120]
EN = ["why are there so many sharks", "are shark attacks", "why are shark attacks", "when is shark season", "how many shark attacks", "is it safe to swim",
      "bull sharks", "shark attack", "do shark nets", "where do sharks", "are sharks", "shark sightings", "great white sharks", "tiger sharks"]
PT = ["por que tem tantos tubarões", "por que os tubarões", "ataque de tubarão", "ataques de tubarão", "tubarão cabeça chata", "é seguro nadar", "quantos ataques de tubarão",
      "tubarão em", "tubarões em", "tubarão tigre", "tubarão branco", "época de tubarão"]
FR = ["pourquoi il y a autant de requins", "pourquoi les requins", "attaque de requin", "attaques de requin", "requin bouledogue", "requin tigre", "requin blanc",
      "est-ce dangereux de se baigner", "combien d'attaques de requin", "requin à", "requins à", "les requins"]
ES = ["por qué hay tantos tiburones", "por qué los tiburones", "ataque de tiburón", "ataques de tiburón", "tiburón toro", "tiburón tigre", "tiburón blanco",
      "es seguro nadar", "cuántos ataques de tiburón", "tiburones en", "temporada de tiburones", "hay tiburones en"]
AR = ["هجوم سمكة قرش", "هجوم القرش", "سمك القرش", "القرش في", "قرش الغردقة", "لماذا تهاجم أسماك القرش", "هل البحر الأحمر آمن", "سمكة القرش"]
L = {  # country: (google hl, gl, duckduckgo kl, bing mkt, stems)
    "Australia": ("en-AU", "au", "au-en", "en-AU", EN), "New Zealand": ("en-NZ", "nz", "nz-en", "en-NZ", EN), "United States": ("en-US", "us", "us-en", "en-US", EN),
    "Canada": ("en-CA", "ca", "ca-en", "en-CA", EN), "United Kingdom": ("en-GB", "gb", "uk-en", "en-GB", EN), "South Africa": ("en-ZA", "za", "za-en", "en-ZA", EN),
    "Brazil": ("pt-BR", "br", "br-pt", "pt-BR", PT), "France": ("fr-FR", "fr", "fr-fr", "fr-FR", FR), "Réunion": ("fr", "re", "fr-fr", "fr-FR", FR),
    "Mexico": ("es-MX", "mx", "mx-es", "es-MX", ES), "Egypt": ("ar-EG", "eg", "xa-ar", "ar-SA", AR)}
out = {"made": time.strftime("%Y-%m-%d"), "auto": {}, "errors": {}}
for c, (hl, gl, kl, mkt, stems) in L.items():
    out["auto"][c] = {}
    for q in stems:
        row = {}
        for e, u, parse in (("google", f"https://suggestqueries.google.com/complete/search?client=firefox&hl={hl}&gl={gl}&q=" + urllib.parse.quote(q), lambda t: json.loads(t)[1]),
                            ("duckduckgo", f"https://duckduckgo.com/ac/?kl={kl}&q=" + urllib.parse.quote(q), lambda t: [x["phrase"] for x in json.loads(t)]),
                            ("bing", f"https://api.bing.com/osjson.aspx?mkt={mkt}&query=" + urllib.parse.quote(q), lambda t: json.loads(t)[1])):
            t = get(u)
            try: row[e] = parse(t) if not t.startswith("ERR") else []
            except Exception: row[e] = []
            time.sleep(0.7)
        out["auto"][c][q] = row
    n = sum(len(v) for r in out["auto"][c].values() for v in r.values()); print(c, n, "suggestions", flush=True)
time.sleep(60)
try:
    from pytrends.request import TrendReq
    tr = TrendReq(hl="en-US", tz=0, timeout=(10, 40)); out["world"] = {}
    for word in ("shark attack", "bull shark", "great white shark"):
        try:
            sug = tr.suggestions(word); topic = next((s for s in sug if s.get("type", "").lower() != "search term"), None)
            kw = topic["mid"] if topic else word; out["world"][word] = {"topic": topic}
            for k in range(4):
                try: tr.build_payload([kw], timeframe="today 5-y", geo=""); df = tr.interest_by_region(resolution="COUNTRY", inc_low_vol=True); break
                except Exception as e: print("retry", word, repr(e)[:80], flush=True); time.sleep(60 * (k + 1)); df = None
            if df is not None:
                s = df[kw].sort_values(ascending=False); out["world"][word]["countries"] = {k: int(v) for k, v in s.head(40).items() if v > 0}
                print("world", word, list(out["world"][word]["countries"].items())[:12], flush=True)
        except Exception as e: out["errors"]["world_" + word] = repr(e)[:150]
        time.sleep(45)
except Exception as e: out["errors"]["trends"] = repr(e)[:150]
json.dump(out, open("../regions.json", "w"), ensure_ascii=False)
