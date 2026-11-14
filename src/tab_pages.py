"""Each tab of the site also has its own address (/story, /safety, /research, /schools, /media).
GitHub Pages serves story.html at /story, so each is a copy of index.html with its own title and
canonical address; the page script opens the matching tab. Usage: python3 -I tab_pages.py <index.html> <out_dir>"""
import os, re, sys
SITE = "https://19-degrees.org/"
TABS = (("story", "Story"), ("safety", "Safety"), ("research", "Research"), ("schools", "Schools"), ("media", "News and media"))
def write(doc, out):
    for slug, name in TABS:
        d = doc.replace(f'<link rel="canonical" href="{SITE}">', f'<link rel="canonical" href="{SITE}{slug}">', 1)
        d = d.replace(f'<meta property="og:url" content="{SITE}">', f'<meta property="og:url" content="{SITE}{slug}">', 1)
        d, n = re.subn(r'<title>[^<]*</title>', f'<title>{name} · 19 Degrees</title>', d, count=1)
        if n != 1 or f'href="{SITE}{slug}"' not in d: sys.exit("could not set the address for " + slug)
        open(os.path.join(out, slug + ".html"), "w").write(d)
if __name__ == "__main__":
    write(open(sys.argv[1]).read(), sys.argv[2])
