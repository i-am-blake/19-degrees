"""Monthly search tracker: what people type into Google, Bing and DuckDuckGo about sharks, in 11 countries and 5 languages,
plus Wikipedia reads of the main shark articles. Adds one month to src/search_tracker.json and changes nothing else.
Each month keeps, per country, every suggestion and the engines that gave it (g = Google, b = Bing, d = DuckDuckGo).
Stops without saving if too few suggestions come back, so a blocked or broken month is never recorded as real.
Usage: python3 -I src/tracker19.py [out.json]"""
import datetime, json, os, sys, time, urllib.parse, urllib.request

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "search_tracker.json")
UA = {"User-Agent": "Mozilla/5.0 (compatible; 19-degrees search tracker; +https://19-degrees.org)"}
def get(u, t=25):
    for k in range(2):
        try: return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=t).read().decode("utf-8", "replace")
        except Exception: time.sleep(3)
    return None

EN = ["why are there so many sharks", "are shark attacks", "why are shark attacks", "when is shark season", "how many shark attacks",
      "is it safe to swim", "bull sharks", "shark attack", "do shark nets", "where do sharks", "are sharks", "shark sightings",
      "great white sharks", "tiger sharks"]
PT = ["por que tem tantos tubarões", "por que os tubarões", "ataque de tubarão", "ataques de tubarão", "tubarão cabeça chata", "é seguro nadar",
      "quantos ataques de tubarão", "tubarão em", "tubarões em", "tubarão tigre", "tubarão branco", "época de tubarão"]
FR = ["pourquoi il y a autant de requins", "pourquoi les requins", "attaque de requin", "attaques de requin", "requin bouledogue", "requin tigre",
      "requin blanc", "est-ce dangereux de se baigner", "combien d'attaques de requin", "requin à", "requins à", "les requins"]
ES = ["por qué hay tantos tiburones", "por qué los tiburones", "ataque de tiburón", "ataques de tiburón", "tiburón toro", "tiburón tigre",
      "tiburón blanco", "es seguro nadar", "cuántos ataques de tiburón", "tiburones en", "temporada de tiburones", "hay tiburones en"]
AR = ["هجوم سمكة قرش", "هجوم القرش", "سمك القرش", "القرش في", "قرش الغردقة", "لماذا تهاجم أسماك القرش", "هل البحر الأحمر آمن", "سمكة القرش"]
COUNTRIES = {  # Google hl and gl, DuckDuckGo kl, Bing market, stems
    "Australia": ("en-AU", "au", "au-en", "en-AU", EN), "New Zealand": ("en-NZ", "nz", "nz-en", "en-NZ", EN),
    "United States": ("en-US", "us", "us-en", "en-US", EN), "Canada": ("en-CA", "ca", "ca-en", "en-CA", EN),
    "United Kingdom": ("en-GB", "gb", "uk-en", "en-GB", EN), "South Africa": ("en-ZA", "za", "za-en", "en-ZA", EN),
    "Brazil": ("pt-BR", "br", "br-pt", "pt-BR", PT), "France": ("fr-FR", "fr", "fr-fr", "fr-FR", FR), "Réunion": ("fr", "re", "fr-fr", "fr-FR", FR),
    "Mexico": ("es-MX", "mx", "mx-es", "es-MX", ES), "Egypt": ("ar-EG", "eg", "xa-ar", "ar-SA", AR)}
WIKI = ["Shark_attack", "Bull_shark", "Great_white_shark", "Tiger_shark", "Shark_attacks_in_Australia", "Shark_net"]

def suggestions(hl, gl, kl, mkt, q):
    out = {}
    for e, u, parse in (("g", f"https://suggestqueries.google.com/complete/search?client=firefox&hl={hl}&gl={gl}&q=" + urllib.parse.quote(q), lambda t: json.loads(t)[1]),
                        ("d", f"https://duckduckgo.com/ac/?kl={kl}&q=" + urllib.parse.quote(q), lambda t: [x["phrase"] for x in json.loads(t)]),
                        ("b", f"https://api.bing.com/osjson.aspx?mkt={mkt}&query=" + urllib.parse.quote(q), lambda t: json.loads(t)[1])):
        t = get(u)
        try: out[e] = [s.strip().lower() for s in parse(t)] if t else []
        except Exception: out[e] = []
        time.sleep(0.7)
    return out

today = datetime.date.today(); month = (today.replace(day=1) - datetime.timedelta(days=1)).strftime("%Y-%m")  # the month just ended
rec = {"recorded": today.isoformat(), "countries": {}, "wikipedia": {}}
for c, (hl, gl, kl, mkt, stems) in COUNTRIES.items():
    seen = {}
    for q in stems:
        for e, lst in suggestions(hl, gl, kl, mkt, q).items():
            for s in lst:
                if s != q.lower(): seen[s] = "".join(sorted(set(seen.get(s, "") + e)))
    rec["countries"][c] = dict(sorted(seen.items()))
    print(c, len(seen), "suggestions", flush=True)
y, m = month.split("-")
for a in WIKI:
    t = get(f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia.org/all-access/user/{a}/monthly/{y}{m}0100/{y}{m}2800")
    try: rec["wikipedia"][a] = json.loads(t)["items"][0]["views"]
    except Exception: rec["wikipedia"][a] = None

total = sum(len(v) for v in rec["countries"].values()); filled = sum(1 for v in rec["countries"].values() if len(v) >= 20)
if total < 1500 or filled < 9: sys.exit(f"Too few suggestions ({total}, {filled} countries with 20 or more): not saving this month")
data = json.load(open(OUT)) if os.path.exists(OUT) else {"about": __doc__.split("\n")[0], "months": {}}
prev = data["months"].get(max(data["months"]) if data["months"] else "", {}).get("countries", {})
data["months"][month] = rec
json.dump(data, open(OUT, "w"), ensure_ascii=False, separators=(",", ":"), sort_keys=True)
for c, now in rec["countries"].items():
    new = sorted(set(now) - set(prev.get(c, {})))
    if prev: print(f"{c}: {len(new)} new this month, e.g. {new[:5]}")
print("saved", month, total, "suggestions")
