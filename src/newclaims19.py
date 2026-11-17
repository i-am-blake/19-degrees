"""Claims C44 (survival), C45 (Hawaii tiger shark season), C46 (what shark-control gear catches) and the El Nino check on C32.
Usage: python3 -I newclaims19.py <asid.csv> <hawaii_incidents.csv> <scp-numbers-caught.xlsx> <sst_dir> [newclaims.json]
C44  Australian Shark-Incident Database: share of injured victims of unprovoked bites who died, 1960-1989 against 2000 on
     (Fisher's exact test), by decade and for white, tiger and bull sharks.
C45  Hawaii DLNR incident list: share of tiger shark incidents in September-November, against a quarter of the year
     (binomial), and up to 2010 against after (Fisher's exact test).
C46  Queensland Shark Control Program catch: tiger, bull and white sharks (the three this site studies) against every
     other animal caught, all years and the last 10, with the share found alive and the split by gear.
C32  HadISST off Sydney and the Nino 3.4 index (both from fetch_sst.py / fetch_nino34.py): months a year at 19C or warmer,
     with the long-term trend taken out, against the year's mean El Nino index (Pearson)."""
import csv, collections, glob, json, os, re, sys, statistics as st
import openpyxl
from scipy import stats
asid, hcsv, scp, sdir = sys.argv[1:5]
out = sys.argv[5] if len(sys.argv) > 5 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "newclaims.json")
D = {}

# ---- C44: survival ----
def ym(r):
    try: return int(float(r["Incident.year"])), int(float(r["Incident.month"]))
    except (ValueError, KeyError): return None
rows = [r for r in csv.DictReader(open(asid, encoding="utf-8")) if r.get("Provoked/unprovoked", "").strip() == "unprovoked"]
hurt = [r for r in rows if ym(r) and r.get("Victim.injury", "").strip().lower() in ("injured", "fatal")]
fatal = lambda r: r["Victim.injury"].strip().lower() == "fatal"
def grp(lo, hi, sp=None):
    s = [r for r in hurt if lo <= ym(r)[0] < hi and (sp is None or sp in r.get("Shark.common.name", "").lower())]
    f = sum(map(fatal, s)); return dict(n=len(s), fatal=f, pct=round(100 * f / len(s)) if s else None)
dec = collections.defaultdict(lambda: [0, 0])
for r in hurt:
    d = ym(r)[0] // 10 * 10
    if d >= 1900: dec[d][0] += 1; dec[d][1] += fatal(r)
last = max(ym(r)[0] for r in hurt)
early, late = grp(1960, 1990), grp(2000, last + 1)
D["c44"] = dict(early=early, late=late, last_year=last,
                p=float(stats.fisher_exact([[early["fatal"], early["n"] - early["fatal"]], [late["fatal"], late["n"] - late["fatal"]]])[1]),
                decades=[dict(decade=d, injured=n, fatal=f, pct=round(100 * f / n)) for d, (n, f) in sorted(dec.items())],
                species={sp: dict(early=grp(1960, 1990, sp), late=grp(2000, last + 1, sp)) for sp in ("white", "tiger", "bull")})

# ---- C45: Hawaii tiger shark season ----
def hd(r):
    m = re.match(r"\s*(\d{4})/(\d{1,2})/", r.get("Date and Time", "")); return (int(m.group(1)), int(m.group(2))) if m else None
tig = [hd(r) for r in csv.DictReader(open(hcsv, encoding="utf-8")) if "tiger" in r.get("Shark", "").lower() and hd(r)]
son = lambda xs: sum(m in (9, 10, 11) for _, m in xs)
e = [x for x in tig if x[0] <= 2010]; l = [x for x in tig if x[0] > 2010]
D["c45"] = dict(n=len(tig), first=min(y for y, _ in tig), last=max(y for y, _ in tig),
                by_month=[sum(m == k for _, m in tig) for k in range(1, 13)], son=son(tig), son_pct=round(100 * son(tig) / len(tig)),
                p_season=float(stats.binomtest(son(tig), len(tig), 0.25).pvalue),
                early=dict(n=len(e), son=son(e), pct=round(100 * son(e) / len(e))), late=dict(n=len(l), son=son(l), pct=round(100 * son(l) / len(l))),
                p=float(stats.fisher_exact([[son(l), len(l) - son(l)], [son(e), len(e) - son(e)]], alternative="two-sided")[1]))

# ---- C46: what the gear catches ----
ws = openpyxl.load_workbook(scp, read_only=True, data_only=True).worksheets[0]
it = ws.iter_rows(values_only=True); H = list(next(it)); ix = {h: i for i, h in enumerate(H)}
catch = [r for r in it if r[ix["Year"]]]
TG = {"TIGER SHARK": "tiger", "BULL WHALER": "bull", "WHITE SHARK": "white"}
num = lambda r: float(r[ix["NumberCaught"]] or 0)
alive = lambda r: str(r[ix["Alive/Deceased"]]).lower().startswith("alive")
y1 = max(int(r[ix["Year"]]) for r in catch); y0 = min(int(r[ix["Year"]]) for r in catch)
def split(lo):
    S = [r for r in catch if int(r[ix["Year"]]) >= lo]
    t = collections.Counter(); g = collections.defaultdict(lambda: [0, 0]); gear = collections.defaultdict(lambda: [0, 0])
    for r in S:
        nm = str(r[ix["CommonName"]]).strip().upper(); k = num(r)
        if nm in TG: t[TG[nm]] += k
        else:
            grp_ = {"SHARK": "other sharks", "TURTLE": "turtles", "MAMMAL": "dolphins and whales"}.get(str(r[ix["SpeciesGroup"]]), "rays, fish and others")
            g[grp_][0] += k; g[grp_][1] += k if alive(r) else 0
        gear[str(r[ix["Gear"]]).lower()][0 if nm in TG else 1] += k
    tt, oo = sum(t.values()), sum(a for a, _ in g.values())
    return dict(target=int(tt), other=int(oo), pct_other=round(100 * oo / (tt + oo)), target_by={k: int(v) for k, v in t.items()},
                other_by={k: dict(n=int(a), alive=int(b), alive_pct=round(100 * b / a) if a else None) for k, (a, b) in g.items()},
                gear={k: dict(target=int(a), other=int(b)) for k, (a, b) in gear.items() if k in ("drum", "net")},
                p=float(stats.binomtest(int(oo), int(tt + oo), 0.5).pvalue))
D["c46"] = dict(first=y0, last=y1, all=split(y0), recent=split(y1 - 9), recent_from=y1 - 9)

# ---- C32: El Nino check ----
oni = {r["date"][:7]: float(r["oni"]) for r in csv.DictReader(open(os.path.join(sdir, "nino34.csv"))) if r.get("oni") not in ("", None)}
f = next(p for p in glob.glob(os.path.join(sdir, "*.csv")) if "Sydney" in os.path.basename(p))
syd = {}
for row in list(csv.reader(open(f)))[1:]:
    try: syd[row[0][:7]] = float(row[1])
    except (ValueError, IndexError): pass
ys = [y for y in range(1950, 2100) if all(f"{y}-{m:02d}" in syd for m in range(1, 13)) and all(f"{y}-{m:02d}" in oni for m in range(1, 13))]
warm = {y: sum(syd[f"{y}-{m:02d}"] >= 19 for m in range(1, 13)) for y in ys}
enso = {y: st.mean(oni[f"{y}-{m:02d}"] for m in range(1, 13)) for y in ys}
slope, icpt = st.linear_regression(ys, [warm[y] for y in ys])
res = {y: warm[y] - (icpt + slope * y) for y in ys}
r, p = stats.pearsonr([enso[y] for y in ys], [res[y] for y in ys])
nino = [res[y] for y in ys if enso[y] >= 0.5]; nina = [res[y] for y in ys if enso[y] <= -0.5]
D["c32"] = dict(first=ys[0], last=ys[-1], years=len(ys), per_decade=round(10 * slope, 2), r=round(float(r), 2), p=float(p),
                nino=dict(n=len(nino), months=round(st.mean(nino), 1)), nina=dict(n=len(nina), months=round(st.mean(nina), 1)))

json.dump(D, open(out, "w"), indent=1)
print("newclaims", json.dumps({k: {a: b for a, b in v.items() if not isinstance(b, (list, dict))} for k, v in D.items()}))
