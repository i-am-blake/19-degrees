"""Claim C1: are bull sharks a growing share of what Queensland's shark-control gear catches at its southern beaches?
Usage: python3 -I range19.py <scp-numbers-caught.xlsx> <out catchshare.json>
Catches: Queensland Shark Control Program, numbers caught by beach, month and species, 1996 on (Queensland Government,
CC BY 4.0). Bull sharks ('BULL WHALER') as a share of all sharks caught, south (Rainbow Beach to the Gold Coast) and
north (Bundaberg to Cairns), in the program's first ten full years against its last ten full years. Share of catch stands
in for catch per unit of effort, which isn't published. Difference in shares with a 95% CI; two-sided p from a
two-proportion z-test."""
import json, math, sys
from statistics import NormalDist
import openpyxl

SCP, OUT = sys.argv[1:3]
SOUTH = {"Gold Coast", "Nth Stradbroke Is.", "Bribie Island", "Sunshine Coast South", "Sunshine Coast North", "Rainbow Beach"}

rows = [r for r in list(openpyxl.load_workbook(SCP, read_only=True, data_only=True)["Sheet1"].iter_rows(values_only=True))[1:] if r[0]]
months = {}
for r in rows: months.setdefault(int(r[0]), set()).add(int(r[1]))
full = sorted(y for y, m in months.items() if len(m) == 12)
first, last = (full[0], full[0] + 9), (full[-1] - 9, full[-1])

def share(south, y0, y1):
    b = t = 0
    for r in rows:
        if (r[3] in SOUTH) == south and y0 <= int(r[0]) <= y1 and r[7] == "SHARK":
            n = r[14] or 0; t += n
            if r[9] == "BULL WHALER": b += n
    return dict(bull=b, sharks=t, pct=round(100 * b / t, 1))

def compare(south):
    a, z = share(south, *first), share(south, *last)
    p1, p2 = a["bull"] / a["sharks"], z["bull"] / z["sharks"]
    d = p2 - p1
    se = math.sqrt(p1 * (1 - p1) / a["sharks"] + p2 * (1 - p2) / z["sharks"])
    pp = (a["bull"] + z["bull"]) / (a["sharks"] + z["sharks"])
    zz = d / math.sqrt(pp * (1 - pp) * (1 / a["sharks"] + 1 / z["sharks"]))
    return dict(first=a, last=z, diff_pts=round(100 * d, 1), ci=[round(100 * (d - 1.96 * se), 1), round(100 * (d + 1.96 * se), 1)],
                p=float(f"{2 * (1 - NormalDist().cdf(abs(zz))):.2g}"))

out = dict(first_years=list(first), last_years=list(last), south=compare(True), north=compare(False))
json.dump(out, open(OUT, "w"), indent=1)
print("catchshare", json.dumps(out))
