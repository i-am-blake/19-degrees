"""Explore two public tag datasets and write small summaries (run on GitHub; the hosts aren't reachable elsewhere).
1. Lubitz (2024) bull shark tags, Dryad doi:10.5061/dryad.xd2547dn1 (Agulhas and East Australian currents).
2. U.S. Animal Telemetry Network satellite positions (IOOS ERDDAP atn_collection): which shark species are there."""
import io, json, os, sys, urllib.request, urllib.parse, urllib.error, gzip
import pandas as pd

OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
log = open(os.path.join(OUT, "log.txt"), "w")
def get(url, timeout=600):
    req = urllib.request.Request(url, headers={"User-Agent": "19-degrees.org open data"})
    try:
        return urllib.request.urlopen(req, timeout=timeout).read()
    except urllib.error.HTTPError as e:
        log.write(f"HTTP {e.code} for {url}: {e.read()[:400]!r}\n"); log.flush(); raise

# 1. Dryad
try:
    doi = urllib.parse.quote("doi:10.5061/dryad.xd2547dn1", safe="")
    base = "https://datadryad.org"
    ds = json.loads(get(f"{base}/api/v2/datasets/{doi}"))
    json.dump(ds, open(os.path.join(OUT, "dryad_dataset.json"), "w"), indent=1)
    ver = ds["_links"]["stash:version"]["href"]
    files = json.loads(get(base + ver + "/files"))
    json.dump(files, open(os.path.join(OUT, "dryad_files.json"), "w"), indent=1)
    summ = {}
    for f in files["_embedded"]["stash:files"]:
        name = f["path"]; fid = f["_links"]["self"]["href"].rstrip("/").split("/")[-1]
        dl = f"{base}/downloads/file_stream/{fid}"
        log.write(f"dryad file {name} {f.get('size')}\n"); log.flush()
        raw = get(dl, timeout=1800)
        if name.lower().endswith((".md", ".txt")):
            open(os.path.join(OUT, "dryad_" + name), "wb").write(raw); continue
        if not name.lower().endswith(".csv"): continue
        df = pd.read_csv(io.BytesIO(raw), low_memory=False)
        s = {"rows": len(df), "columns": list(df.columns), "head": df.head(5).astype(str).values.tolist()}
        num = {}
        for c in df.columns:
            v = pd.to_numeric(df[c], errors="coerce").dropna()
            if len(v): num[c] = {k: round(float(x), 3) for k, x in v.describe(percentiles=[.01, .05, .5, .95, .99]).items()}
        s["numeric"] = num
        summ[name] = s
        # keep a compact copy for local analysis: every column, every 50th row of very large files
        keep = df if len(df) <= 200000 else df.iloc[::50]
        keep.to_csv(os.path.join(OUT, "dryad_" + name + ".gz"), index=False, compression="gzip")
    json.dump(summ, open(os.path.join(OUT, "dryad_summary.json"), "w"), indent=1)
except Exception as e:
    log.write(f"dryad failed: {e!r}\n")

# 2. ATN
try:
    E = "https://erddap.ioos.us/erddap/tabledap/atn_collection"
    try: taxa = get(E + ".csv?taxon_name&distinct()").decode()
    except Exception: taxa = get(E + ".csv?taxon_name&time>=2007-01-01&time<=2007-12-31").decode() + get(E + ".das").decode()
    open(os.path.join(OUT, "atn_taxa.csv"), "w").write(taxa)
    for sp in ("Carcharhinus leucas", "Galeocerdo cuvier", "Carcharodon carcharias"):
        if sp not in taxa: log.write(f"atn: no {sp}\n"); continue
        q = E + ".csv?time,latitude,longitude,animal,location_class&taxon_name=" + urllib.parse.quote(f'"{sp}"')
        raw = get(q, timeout=1800)
        gzip.open(os.path.join(OUT, "atn_" + sp.split()[1] + ".csv.gz"), "wb").write(raw)
        log.write(f"atn {sp}: {raw.count(b'\n') - 2} rows\n")
except Exception as e:
    log.write(f"atn failed: {e!r}\n")
log.close()
print(open(os.path.join(OUT, "log.txt")).read())
