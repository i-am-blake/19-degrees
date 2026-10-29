"""Refresh only today's sea temperature readings inside an already-built 19 Degrees page.
Usage: python3 -I update_today.py <page19.html> <out.html>
Reads each beach's coordinates from the page's own data block and asks Open-Meteo marine for the
current sea surface temperature; everything else in the page is left as it was."""
import sys, re, json, urllib.request
src, out = sys.argv[1:3]
html = open(src).read()
pat = re.compile(r'(<script type="application/json" id="n19-data">)(.*?)(</script>)', re.S)
d = json.loads(pat.search(html).group(2))
for b in d["beaches"]:
    lat, lon = b["beach"]
    u = (f"https://marine-api.open-meteo.com/v1/marine?latitude={lat}&longitude={lon}"
         "&current=sea_surface_temperature&daily=sea_surface_temperature_max&past_days=6&forecast_days=1&timezone=Australia%2FSydney")
    j = json.load(urllib.request.urlopen(u, timeout=60))
    b["today"] = dict(time=j["current"]["time"], sst=j["current"]["sea_surface_temperature"],
                      week=list(zip(j["daily"]["time"], j["daily"]["sea_surface_temperature_max"])))
    print(b["name"], b["today"]["time"], b["today"]["sst"])
blob = json.dumps(d, separators=(",", ":")).replace("</", "<\\/")
open(out, "w").write(pat.sub(lambda m: m.group(1) + blob + m.group(3), html, count=1))
print("wrote", out)
