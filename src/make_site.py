"""Assemble the GitHub Pages site: python3 -I make_site.py <built 19-degrees.html> <pub_dir> <out_dir>
Wraps the built page in a full HTML document with launch/head.html (link previews, icons) and copies
the classroom sheets, data/, share/ and launch files. Fails if the address placeholder or a personal email is left in."""
import os, re, shutil, sys
page, pub, out = sys.argv[1:4]
SITE = "https://19-degrees.org/"
body = open(page).read()
body = re.sub(r'<title>.*?</title>\n?', '', body, count=1)
# fonts: served from this site instead of Google, so no visitor data goes to Google
body, nf = re.subn(r'<link rel="preconnect" href="https://fonts\.googleapis\.com">\n<link rel="preconnect" href="https://fonts\.gstatic\.com" crossorigin>\n<link rel="stylesheet" href="https://fonts\.googleapis\.com/css2[^"]*">',
                   '<link rel="stylesheet" href="fonts/fonts.css">', body)
if nf != 1: sys.exit("Google Fonts tags not found")
# security: the page may only load its own files and talk to GoatCounter (visit counts) and Web3Forms (contact form)
GC = re.search(r'GOATCOUNTER:\s*"([^"]*)"', body).group(1)
gc = f" https://{GC}.goatcounter.com" if GC else ""
CSP = ("default-src 'self'; script-src 'self' 'unsafe-inline'" + (" https://gc.zgo.at" if GC else "") +
       "; style-src 'self' 'unsafe-inline'; font-src 'self'; img-src 'self' data: blob:" + gc +
       "; connect-src 'self' https://api.web3forms.com" + gc + "; object-src 'none'; base-uri 'self'; form-action 'self'; frame-src 'none'")
SEC = f'<meta http-equiv="Content-Security-Policy" content="{CSP}">\n<meta name="referrer" content="strict-origin-when-cross-origin">\n'
SEC_STATIC = ('<meta http-equiv="Content-Security-Policy" content="default-src \'self\'; script-src \'self\' \'unsafe-inline\'; style-src \'self\' \'unsafe-inline\'; img-src \'self\' data:; '
              'object-src \'none\'; base-uri \'self\'; form-action \'none\'; frame-src \'none\'">\n')
head = open(os.path.join(pub, "launch", "head.html")).read().replace("https://YOUR-SITE/", SITE)
head = re.sub(r'<!-- 19 Degrees: paste inside.*?-->\n', '', head, count=1)
doc = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
       '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n' + SEC + head + '\n' + body + '\n</html>\n')
if os.path.exists(out): shutil.rmtree(out)
os.makedirs(out)
open(os.path.join(out, "index.html"), "w").write(doc)
open(os.path.join(out, "CNAME"), "w").write(SITE.split("//")[1].strip("/") + "\n")  # GitHub Pages custom domain
for f in os.listdir(pub):
    if re.match(r"classroom.*\.html$", f):
        t = open(os.path.join(pub, f)).read()
        t, n = re.subn(r'(<meta charset="utf-8">)', r'\1' + SEC_STATIC.replace('\\', '\\\\'), t, count=1)
        if n != 1: sys.exit("no charset meta in " + f)
        open(os.path.join(out, f), "w").write(t)
shutil.copytree(os.path.join(pub, "data"), os.path.join(out, "data"))
shutil.copytree(os.path.join(pub, "fonts"), os.path.join(out, "fonts"))
shutil.copytree(os.path.join(pub, "share"), os.path.join(out, "share"), ignore=shutil.ignore_patterns("classroom-preview.png"))
for f in ["favicon.ico", "favicon.svg", "apple-touch-icon.png", "icon-32.png", "icon-192.png", "icon-512.png", "site.webmanifest", "LICENSE"]:
    shutil.copy(os.path.join(pub, "launch", f), out)
bad = []
for root, _, files in os.walk(out):
    for f in files:
        t = open(os.path.join(root, f), "rb").read()
        if f.endswith((".html", ".css")) and (b"fonts.googleapis" in t or b"fonts.gstatic" in t): bad.append(f + " (Google Fonts)")
        if b"YOUR-SITE" in t or b"YOUR-DOMAIN" in t or re.search(rb"[\w.+-]+@gmail\.com", t): bad.append(f)
if bad: sys.exit("placeholder or personal email left in: " + ", ".join(bad))
print("site written to", out)
