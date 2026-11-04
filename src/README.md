# Rebuilding 19 Degrees from the raw data

Everything on the site is built from public data by the scripts in this folder. Run them in order from inside `src/`. All scripts take their inputs and outputs as arguments; `python3 -I` keeps them from loading stray modules.

Requirements: Python 3.10+ with the packages in `requirements.txt`. The share images and LinkedIn carousel also need Node.js with Playwright and the three page fonts (Bricolage Grotesque, Figtree, Martian Mono, all on Google Fonts under the SIL Open Font License).

## 1. Get the data

```sh
# Shark bites: download the newest "Australian Shark-Incident Database Public Version.xlsx"
# from https://zenodo.org/records/18752301 (CC BY 4.0), then:
python3 -I asid_to_csv.py "Australian Shark-Incident Database Public Version.xlsx" asid.csv

# Sea temperature: monthly HadISST 1900–present from NOAA ERDDAP
python3 -I fetch_sst.py sst            # one series per coastal region (regions.py)
python3 -I fetch_nino34.py sst         # El Niño / La Niña index (Niño 3.4 from HadISST)
python3 -I fetch_beaches.py beach_sst  # each beach's 1° patch (beaches.py) plus today's reading from Open-Meteo marine
```

`extra_incidents.json` holds bites reported in the news after the database's last month. They are marked unconfirmed and dropped once the database covers their month.

## 2. Build

```sh
python3 -I build.py asid.csv sst extra_incidents.json data.json        # incidents, regions, drowning comparison
python3 -I climate_analysis.py asid.csv sst climate.json               # warm vs cool months, the 19°C limit, the 19°C window by decade
python3 -I build19.py asid.csv sst beach_sst data.json page19.html 19-degrees.html
```

Then check that every number written into the page text still matches the data it was built from (the weekly rebuild stops here if one doesn't):

```sh
python3 -I check19.py 19-degrees.html asid.csv
```

`build19.py` prints the headline checks: bites below 19°C by species, months a year at 19°C or more by beach, the move into coastal waters, El Niño, Western Australia and north-coast white sharks.

## 3. Extras

```sh
python3 -I export19.py 19-degrees.html pub           # CSV and JSON downloads, data dictionary
python3 -I classroom19.py 19-degrees.html pub        # classroom sheets (run after export19.py)
python3 -I notebook19.py pub                         # starter Jupyter notebook
python3 -I share19.py 19-degrees.html pub/share      # share cards and link card
python3 -I carousel19.py 19-degrees.html pub         # LinkedIn carousel (PDF)
```

## 4. Assemble the site

`make_site.py` wraps the page with the link-preview tags (`launch/head.html`), swaps Google Fonts for the self-hosted copies, adds the security policy and copies everything into one folder. It stops if a placeholder, a personal email address or Google Fonts is left anywhere.

```sh
mkdir -p pub/launch && cp launch/head.html pub/launch/
cp ../favicon.ico ../favicon.svg ../apple-touch-icon.png ../icon-*.png ../site.webmanifest ../LICENSE pub/launch/
cp -r ../fonts pub/fonts
python3 -I make_site.py 19-degrees.html pub site
```

Then copy `site/` over the repo root. The live site's address is set in `make_site.py` (`SITE`) and in the settings block at the top of `page19.html` (`N19_CFG`).

## Shark tracking (IMOS)

`.github/workflows/fetch-imos.yml` checks IMOS Animal Tracking every month and saves bull, tiger and white shark and green turtle detections to the `imos-data` branch when IMOS publishes new data (about every six months). The weekly build reads that branch:

```sh
git fetch origin imos-data && mkdir -p imos && git archive origin/imos-data | tar -x -C imos
python3 -I imos19.py imos sst imos.json      # writes the tagging numbers; build19.py picks up imos.json beside it
```

## Daily readings

`update_today.py index.html index.html` refreshes only today's sea temperatures inside an already-built page.

## Fixed inputs to update by hand

- Drowning figures in `build.py` (`DROWN_YEARS` by state and year, `DROWN_NATIONAL`, window `W0`–`W1`) are the yearly counts in Surf Life Saving Australia's National Coastal Safety Report. When a new report is out, drop the oldest year, add the newest and move the window forward.
- Population by decade (`POP_MID` in `build.py`) uses approximate Australian Bureau of Statistics figures.

## Notes on method

- Sea temperature is the monthly HadISST average for the 1° patch of open sea nearest each bite or beach (about 110 km across). It describes the season, not the exact water a person was in.
- "Coastal waters" bites are the database's coastal sites, mostly surf beaches; inshore bites are rivers, estuaries and harbours or places named that way.
- Checked against NOAA ERSSTv5 as well: Sydney's months at 19°C or more rose by about three months in both data sets. Don't claim 2025 was Sydney's first full year above 19°C; that holds in HadISST but not in ERSSTv5.

## Rain and water clarity (claim C6)

`rain19.py` tests whether bull shark bites fall in wetter-than-usual months at the place they happened. The bite database gives the month, not the day, so each bite month's rainfall is ranked against the same calendar month in every other year (1982 to 2025) at the same 5 km cell, with white shark bites as the comparison. It also checks satellite water clarity (2003 to 2022).

```
python3 -I rain19.py fetch asid.csv chirps/ kd/            # downloads from NOAA ERDDAP, no account needed
python3 -I rain19.py test  asid.csv chirps/ kd/ rain.json  # build19.py reads rain.json beside itself
python3 -I rain19.py gauge asid.csv sites.csv gauge_monthly.csv rain.json   # rain-gauge check, files from the gauge-data branch
python3 -I rain19.py mouths asid.csv river_mouths_east.csv ne_10m_coastline.geojson rain.json   # river-mouth check, file from the ocean-data branch
```

The gauge files come from `.github/workflows/fetch-gauges.yml` (Actions tab, run by hand), which finds up to three long-running gauges within 25 km of each bite site in `rain_points.csv`.

## Warm current off Western Australia (claim C7)

`leeuwin19.py` ranks each Western Australian bull shark bite month by the strength of the Leeuwin Current, read from detrended Fremantle sea level (PSMSL station 111, or the Bureau of Meteorology table `bom_fremantle_62230.html`, which runs later; both on the `ocean-data` branch). The PSMSL copy ends in December 2022; the Bureau's runs to March 2026 (months with less than 90% of hourly readings are skipped). The page uses the Bureau's.

```
python3 -I leeuwin19.py asid.csv bom_fremantle_62230.html      # or fremantle_psmsl111.rlrdata
```

## Warm spells (claim C19)

`heat19.py` ranks each bite month's sea temperature against the same month in the 10 years either side, on the same stretch of coast (the page's HadISST regional series), and counts how many bites fall in the warmest tenth of months. It writes `heat.json`, which `build19.py` reads.

```
python3 -I heat19.py asid.csv sst/ heat.json
```

## Shark nets and drumlines, Queensland (claim C20)

`nets19.py` counts bull sharks caught by gear type and places each Queensland bull shark bite since 1962 relative to today's nets and drumlines. It describes only: gear locations are current, not historical, and busy beaches get gear first. The two input files are on the `ocean-data` branch.

```
python3 -I nets19.py asid.csv shark-gear-locations.xlsx scp-numbers-caught.xlsx
```

## First aid (claim C9)

`firstaid19.py` sorts unprovoked fatal bites by where the wound was, from the database's injury records: limb only (where a tourniquet or firm pressure can reach), trunk or head, junctional (hip or shoulder), no body recovered, or not recorded.

```
python3 -I firstaid19.py asid.csv
```

## 2050 projections (claim C3)

`cmip_sst.py` (run by `.github/workflows/fetch-cmip.yml`) reads each CMIP6 model's monthly sea surface temperature at every beach's sea patch and writes the change from 2016-2025 to 2040-2059 per month. `proj19.py` adds that change to each beach's observed 2016-2025 months and counts months at 19°C or more, giving the model median and the middle 80% of models.

```
python3 -I proj19.py beach_sst/ cmip_tos_delta_ssp245.csv proj.json
```


## Réunion and New Caledonia (claims C6 and C22)

`islands19.py` uses day-dated bites from the University of Reunion Island ([Zenodo, CC BY 4.0](https://doi.org/10.5281/zenodo.12549370); a copy is in `islands_nc_run.csv`). For C6 it compares bull shark bites with bites by other identified sharks: the share after 50 mm or more of rain over 3 days, and the share in turbid water. For C22 it looks up each bite month's HadISST sea temperature off each island. It writes `islands.json`, which `build19.py` reads. The data ends in 2021, so it doesn't run weekly; rerun it when a new version is published.

```
python3 -I islands19.py islands_nc_run.csv islands.json
```

## California white sharks (claim C23)

`california19.py` reads the California Department of Fish and Wildlife shark incident database ([CC BY](https://lab.data.ca.gov/dataset/shark-incident-database-california), fetched monthly to the `ocean-data` branch by `fetch-california.yml`). It counts white shark incidents by era, their median latitude and how many were south of Point Conception, and tests 2014 on against 1990–2013 with a permutation test on the median latitude. It writes `california.json`, which `build19.py` reads; the weekly rebuild reruns it.

```
python3 -I california19.py california_SharkIncidents_1950_2022_220302.xlsx california.json
```

## Water on the day, time of day and the moon (claims C21, C24)

`fieldnotes19.py` reads two fields the bite database records for some bites: the water temperature reported at the scene (a check of the 19°C line that doesn't rely on monthly averages) and the time of day (dawn, day, dusk and night shares by species, for claim C21). `lunar19.py` calculates the moon's phase for every dated bite in California, Réunion and New Caledonia and tests whether more than half fall within 3.7 days of a full or new moon (claim C24). Both write JSON files that `build19.py` reads; the weekly rebuild reruns them.

```
python3 -I fieldnotes19.py asid.csv fieldnotes.json
python3 -I lunar19.py islands_nc_run.csv california_SharkIncidents_1950_2022_220302.xlsx lunar.json
```
