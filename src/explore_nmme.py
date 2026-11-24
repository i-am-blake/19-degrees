"""Look only: map the NOAA CPC NMME seasonal forecast folders (what files exist, how far back, which variables),
so a hindcast skill test for the start and end of the 19 C season can be written. Prints a report; changes nothing."""
import re, urllib.request
UA = {"User-Agent": "19-degrees-explore/1.0 (+https://19-degrees.org)"}
B = "https://ftp.cpc.ncep.noaa.gov/NMME/"
def ls(u):
    try:
        t = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=90).read().decode("utf-8", "replace")
    except Exception as e:
        return None, f"{type(e).__name__}: {str(e)[:120]}"
    rows = re.findall(r'href="([^"?/][^"?]*)"[^>]*>[^<]*</a>\s*([\d-]+ [\d:]+)?\s*([\d.KMG-]+)?', t)
    return [(h, d or "", s or "") for h, d, s in rows if not h.startswith("http")], None
def show(path, n=40):
    r, err = ls(B + path)
    print(f"\n### /NMME/{path}\n")
    if err: print(f"- failed: {err}"); return []
    print(f"- {len(r)} entries")
    for h, d, s in (r[:n] + ([("…", "", "")] if len(r) > 2 * n else []) + (r[-n:] if len(r) > 2 * n else r[n:2 * n])):
        print(f"    - `{h}` {d} {s}")
    return [h for h, _, _ in r]
top = show("")
for sub in [h for h in top if h.endswith("/")]:
    kids = show(sub, 15)
    dirs = [k for k in kids if k.endswith("/")]
    if dirs:  # one level deeper: the newest and the oldest folder
        show(sub + dirs[-1], 30)
        if len(dirs) > 1: show(sub + dirs[0], 10)
