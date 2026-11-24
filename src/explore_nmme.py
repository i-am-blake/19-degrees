"""Look only: what one NMME archive month holds, so a hindcast skill test can be written. Changes nothing."""
import re, urllib.request
UA = {"User-Agent": "19-degrees-explore/1.0 (+https://19-degrees.org)"}
B = "https://ftp.cpc.ncep.noaa.gov/NMME/"
def get(u, n=None):
    r = urllib.request.Request(u, headers=dict(UA, **({"Range": f"bytes=0-{n}"} if n else {})))
    return urllib.request.urlopen(r, timeout=120).read()
def ls(p):
    try: t = get(B + p).decode("utf-8", "replace")
    except Exception as e: print(f"\n### {p}: {type(e).__name__} {e}"); return []
    rows = re.findall(r'href="([^"?/][^"?]*)"[^>]*>[^<]*</a>\s*([\d-]+ [\d:]+)?\s*([\d.KMG-]+)?', t)
    rows = [r for r in rows if not r[0].startswith("http")]
    print(f"\n### {p} ({len(rows)})\n"); [print(f"    - `{h}` {s}") for h, d, s in rows[:80]]
    return [h for h, _, _ in rows]
for p in ("archive/2015010800/", "archive/2026100800/", "realtime_anom/", "realtime_anom/ENSMEAN/", "verif/", "archive2025010800/"):
    k = ls(p)
    sub = [x for x in k if x.endswith("/")]
    if sub and p.startswith(("archive/", "realtime_anom/ENSMEAN")): ls(p + sub[-1])
print("\n### fish sample\n```\n" + get(B + "fish/CanCM4i.202001.tmpsfc.txt", 1500).decode("utf-8", "replace") + "\n```")
