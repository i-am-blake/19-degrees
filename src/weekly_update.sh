#!/usr/bin/env bash
# The weekly rebuild, run by .github/workflows/weekly-update.yml from the repo root. Builds in a temporary folder,
# checks the results, then copies the finished site over the repo root and the refreshed results into src/.
set -euo pipefail
R="$PWD"; W="${RUNNER_TEMP:-/tmp}/w"; rm -rf "$W"; mkdir -p "$W"; cp -r src/. "$W/"; cd "$W"
warn(){ echo "::warning::$*"; }
LOG="$W/run.log"; exec > >(tee -a "$LOG") 2>&1
trap 'echo "::error::Stopped at line $LINENO ($BASH_COMMAND): $(tail -n 12 "$LOG" | tr "\n" "|" | cut -c1-900)"' ERR

# 1. Newest Australian Shark-Incident Database from Zenodo
python3 - <<'PY'
import json, urllib.request
h = json.load(urllib.request.urlopen("https://zenodo.org/api/records/18752301/versions?sort=version&size=1", timeout=60))["hits"]["hits"][0]
f = next(x for x in h["files"] if x["key"].endswith(".xlsx"))
urllib.request.urlretrieve(f["links"]["self"], "asid.xlsx")
open("asid_version.txt", "w").write(str(h["id"]) + "\n"); print("database record", h["id"], h["metadata"].get("version", ""))
PY
python3 -I asid_to_csv.py asid.xlsx asid.csv
NEWDB=0; cmp -s asid_version.txt "$R/src/asid_version.txt" 2>/dev/null || NEWDB=1

# 2. Sea temperature (stop if NOAA is unreachable: these scripts exit with an error)
mkdir -p sst beach_sst; python3 -I fetch_sst.py sst; python3 -I fetch_nino34.py sst; python3 -I fetch_beaches.py beach_sst

# 3. Tagging, warm spells, rain (rain only when the database is new; the page keeps its last numbers otherwise)
if git -C "$R" fetch -q origin imos-data 2>/dev/null; then mkdir -p imos && git -C "$R" archive origin/imos-data | tar -x -C imos && python3 -I imos19.py imos sst imos.json || warn "IMOS step failed, page keeps last numbers"; else warn "no imos-data branch"; fi
python3 -I heat19.py asid.csv sst heat.json
# Warm current off WA (claim C7), from the Fremantle sea-level files the monthly fetch saves to ocean-data
( git -C "$R" fetch -q origin ocean-data && mkdir -p ocean && git -C "$R" archive origin/ocean-data | tar -x -C ocean \
  && { [ -s ocean/bom_fremantle_62230.html ] && python3 -I leeuwin19.py asid.csv ocean/bom_fremantle_62230.html leeuwin.json \
       || python3 -I leeuwin19.py asid.csv ocean/fremantle_psmsl111.rlrdata leeuwin.json; } ) || warn "C7 step failed, page keeps last numbers"
# Water on the day and time of day (bite database), and the moon (claim C24, needs dated bites from ocean-data)
python3 -I fieldnotes19.py asid.csv fieldnotes.json || warn "fieldnotes step failed, page keeps last numbers"
{ f=$(ls ocean/california_*.xlsx 2>/dev/null | head -n 1); [ -n "$f" ] && python3 -I lunar19.py islands_nc_run.csv "$f" lunar.json; } || warn "C24 step failed, page keeps last numbers"
# Tagged and recorded bull and tiger sharks outside Australia (claim C25), from OBIS records on ocean-data;
# reruns only when those files change (obis19.py keeps the last result otherwise)
cp "$R/src/obis.json" obis.json 2>/dev/null || true
python3 -I obis19.py ocean obis.json || warn "C25 step failed, page keeps last numbers"
# Indian Ocean Dipole and WA bites (claim C26); coastal population and southern NSW bites (claim C18)
[ -f ocean/iod_dmi_hadisst.txt ] && { python3 -I iod19.py asid.csv ocean/iod_dmi_hadisst.txt iod.json || warn "C26 step failed, page keeps last numbers"; }
[ -f ocean/population_coastal_ghsl.csv ] && { python3 -I coastpop19.py asid.csv ocean/population_coastal_ghsl.csv coastpop.json || warn "C18 step failed, page keeps last numbers"; }
# California white sharks (claim C23), from the incident file the monthly fetch saves to ocean-data
{ f=$(ls ocean/california_*.xlsx 2>/dev/null | head -n 1); [ -n "$f" ] && python3 -I california19.py "$f" california.json; } || warn "C23 step failed, page keeps last numbers"
if [ "$NEWDB" = 1 ] || [ "${RERUN_RAIN:-}" = 1 ]; then
  ( python3 -I rain19.py fetch asid.csv chirps kd && python3 -I rain19.py test asid.csv chirps kd rain.json \
    && git -C "$R" fetch -q origin gauge-data ocean-data && mkdir -p gauge ocean \
    && git -C "$R" archive origin/gauge-data | tar -x -C gauge && git -C "$R" archive origin/ocean-data | tar -x -C ocean \
    && gunzip -f gauge/gauge_monthly.csv.gz && python3 -I rain19.py gauge asid.csv gauge/sites.csv gauge/gauge_monthly.csv rain.json \
    && curl -sSfL -o coast.geojson https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_10m_coastline.geojson \
    && python3 -I rain19.py mouths asid.csv ocean/river_mouths_east.csv coast.geojson rain.json ) || warn "rain step failed, page keeps last numbers"
fi

# 4. Build the page
python3 -I build.py asid.csv sst extra_incidents.json data.json
python3 -I climate_analysis.py asid.csv sst climate.json
python3 -I build19.py asid.csv sst beach_sst data.json page19.html 19-degrees.html | tee build.log

# 5. Checks: never publish a page whose headline finding changed without a person looking
python3 - <<'PY'
import json, re, sys
d = json.loads(re.search(r'id="n19-data">(.*?)</script>', open("19-degrees.html").read(), re.S).group(1))
b = d["species"]["bull"]
print("bull shark bites:", b["n"], "below 19 C:", b["below"], "beaches:", len(d["beaches"]))
if b["below"] != 0: sys.exit("::error::A bull shark bite below 19 C appeared. Not publishing until a person checks it.")
if b["n"] < 150 or len(d["beaches"]) < 10: sys.exit("::error::The build looks incomplete. Not publishing.")
PY
# Every number written into the page text must still match the data (stops here if not)
python3 -I check19.py 19-degrees.html asid.csv

# 6. Downloads, classroom sheets, notebook, share images, site
mkdir -p pub/launch pub/fonts
for f in favicon.ico favicon.svg apple-touch-icon.png icon-32.png icon-192.png icon-512.png site.webmanifest LICENSE; do cp "$R/$f" pub/launch/; done
cp launch/head.html pub/launch/head.html; cp -r "$R/fonts/." pub/fonts/
python3 -I export19.py 19-degrees.html pub; python3 -I classroom19.py 19-degrees.html pub; python3 -I notebook19.py pub
python3 -I share19.py 19-degrees.html pub/share || { warn "share images skipped, keeping last week's"; rm -rf pub/share; cp -r "$R/share" pub/share; }
python3 -I make_site.py 19-degrees.html pub site

# 7. Copy back
cp -r site/. "$R/"
cp heat.json asid_version.txt "$R/src/"; [ -f rain.json ] && cp rain.json "$R/src/"; [ -f imos.json ] && cp imos.json "$R/src/"; [ -f leeuwin.json ] && cp leeuwin.json "$R/src/"; [ -f california.json ] && cp california.json "$R/src/"; for j in fieldnotes lunar obis iod coastpop; do [ -f $j.json ] && cp $j.json "$R/src/"; done
echo "built OK (new database version: $NEWDB)"
