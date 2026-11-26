"""Answers to the questions people search about sharks (data: answers19.json; questions tracked monthly by tracker19.py).
Builds /questions/ (global questions, then regional ones by country, Australia first) and one page per answer at
/questions/<slug>, and the short question blocks on Home and Safety (block(), called by tab_pages.py).
Nothing here repeats a claim's result: an answer gives the short version and links to the claims for the evidence.
Staying current:
  - an answer's label follows its main claim's grade (grade_from). If the claim was regraded since the answer was written
    (written_grade), the answer is held back, with a warning, until its wording is reviewed;
  - answers with bite counts (asid_month) are held back the same way once the shark-incident database moves past that month;
  - outside figures carry a date (fresh.next) by which to check for a newer release; past it, the build warns."""
import datetime, html, json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = json.load(open(os.path.join(HERE, "answers19.json"), encoding="utf-8"))
MON = "January February March April May June July August September October November December".split()
esc = lambda x: html.escape(str(x), quote=True)
def text(h): return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", h))).strip()
def warn(msg): print(f"::warning::answers: {msg}")

def parse_claims(doc):
    """{cid: {label, grade, cls, title}} from the claim cards in the full page."""
    out = {}
    for m in re.finditer(r'<article class="claim" id="(c\d+)" data-status="\w+">(.*?)</article>', doc, re.S):
        h = re.search(r'<span class="cid">(C\d+)</span><span class="subt">.*?</span><span class="(cstat[^"]*)">(.*?)</span></div><h4>(.*?)</h4>', m.group(2), re.S)
        if h: out[m.group(1)] = dict(label=h.group(1), cls=h.group(2), grade=text(h.group(3)), title=text(h.group(4)))
    return out

def label_for(grade):
    if grade in ("Strong", "Supported"): return "Strong evidence", "fact"
    if grade in ("Early yes", "Leans yes", "Early no", "Leans no"): return "Some evidence", "lean"
    if grade in ("Unclear", "First look"): return "Early evidence", "open"
    if grade == "Ruled out": return "Ruled out", "open"
    return "Not answered yet", "none"

def _ym(v):
    if isinstance(v, dict): return f"{v['year']}-{int(v['month']):02d}"
    return str(v)[:7]

def resolve(claims, D, quiet=False):
    """The answers to show, with their labels and as-of lines; held answers are left out."""
    today = datetime.date.today().isoformat(); asid = _ym(D["asid_last"]) if D.get("asid_last") else None
    built = D.get("built", today)[:10]; b = datetime.date.fromisoformat(built)
    out = []
    for a0 in DATA["answers"]:
        a = dict(a0); f = a.get("fresh") or {}
        c = a.get("grade_from")
        if c:
            if c not in claims: (quiet or warn(f"{a['id']}: claim {c} not found, answer held")); continue
            g = claims[c]["grade"]
            if g != a.get("written_grade"):
                quiet or warn(f"'{a['q']}' held for review: {c} is now '{g}' (was '{a.get('written_grade')}' when the answer was written)"); continue
            a["status"], a["cls"] = label_for(g)
        if a.get("asid_month") and asid and asid != a["asid_month"]:
            quiet or warn(f"'{a['q']}' held for review: its bite counts run to {a['asid_month']}, the database now to {asid}"); continue
        parts = []
        if f.get("auto") == "asid" and a.get("asid_month"): y, m = a["asid_month"].split("-"); parts.append(f"bite records to {MON[int(m) - 1]} {y}")
        if f.get("auto") == "claims": parts.append(f"evidence as of {b.day} {MON[b.month - 1]} {b.year}")
        if f.get("text"): parts.append(f["text"])
        a["asof"] = "; ".join(parts)
        if f.get("next") and f["next"] < today and not quiet: warn(f"'{a['q']}': check for a newer release ({f.get('text', '')}; due {f['next']})")
        if re.search(r"\b(safe to swim|guarantee|proven to protect|prevents? (all|every) )", text(a["a"]), re.I): raise SystemExit(f"answers19: '{a['q']}' overstates the evidence")
        out.append(a)
    if not quiet:
        for src, due in DATA.get("sources_due", {}).items():
            if due < today: warn(f"source {src}: check for a newer release (due {due})")
    tier = lambda c: 0 if c in ("fact", "yes") else 2 if c in ("none", "no") else 1
    return sorted(out, key=lambda a: tier(a["cls"]))  # stable: answered, then partly, then not yet, in search order

def _chip(status, cls): return f'<span class="ast {cls}">{esc(status)}</span>'

def block(doc, D, ids, kicker, heading, sub, more):
    """Short cards for Home and Safety, linking to each answer's page. Returns "" if none of them is showing."""
    shown = {a["id"]: a for a in resolve(parse_claims(doc), D, quiet=True)}
    items = [shown[i] for i in ids if i in shown]
    if not items: return ""
    li = "".join(f'<li><a href="/questions/{a.get("long_page") or a["slug"]}"><span class="aq">{esc(a["q"])}</span><span class="aa">{a["a"]}</span>{_chip(a["status"], a["cls"])}</a></li>' for a in items)
    return (f'<div class="asked">{f"<div class=\"kicker\">{kicker}</div>" if kicker else ""}{heading}<p class="sub">{sub}</p>'
            f'<ol class="askl{" three" if len(items) == 3 else ""}">{li}</ol>{more}</div>')

def build(T, D, CLAIMS, write, page, long_date, written_long=()):
    A = resolve(CLAIMS, D); by = {a["id"]: a for a in A}
    for a in A:
        if a.get("long") and f"questions/{a['long']}" in written_long: a["long_page"] = a["long"]
    N = DATA["needs"]
    def need(nid):
        n = N.get(nid)
        return f'<p class="need"><b>To answer this:</b> {esc(n["name"])}. {esc(n["who"])}. <span>{esc(n["access"])}.</span></p>' if n else ""
    def claims_ul(a):
        li = "".join(f'<li><a href="/claims/{c}"><b>{CLAIMS[c]["label"]}:</b> {esc(CLAIMS[c]["title"])}</a></li>'
                     for c in a["claims"] if c in CLAIMS)
        return f'<ul class="qclaims">{li}</ul>' if li else ""
    def card(a, n, where_extra=""):
        url = f'/questions/{a.get("long_page") or a["slug"]}'
        ul = "".join(f"<li>{x}</li>" for x in a["detail"])
        ev = "".join(f'<li><a href="/claims/{c}">{CLAIMS[c]["label"]}</a></li>' for c in a["claims"] if c in CLAIMS)
        see = f'<p class="qsrc"><a href="{a["see"][1]}">{esc(a["see"][0])}</a></p>' if a.get("see") else ""
        asof = f'<span class="qasof">{esc(a["asof"][:1].upper() + a["asof"][1:])}</span>' if a.get("asof") else ""
        evb = f'<p class="qev">The evidence, on Research:</p><ul class="qevl">{ev}</ul>' if ev else ""
        return (f'<details class="qa" id="a-{a["id"]}"><summary><span class="qn">{n:02d}</span><span class="qq">{esc(a["q"])}</span>{_chip(a["status"], a["cls"])}'
                f'<span class="qans">{a["a"]}</span>{asof}</summary>'
                f'<div class="qbody">{"<ul>" + ul + "</ul>" if ul else ""}{evb}{see}{need(a.get("need"))}{where_extra}'
                f'<p><a class="qmore" href="{url}">Full answer →</a></p></div></details>')
    def local_card(q, n, lang):
        lab = {"yes": ("Counted", "fact"), "part": ("Partly answered", "lean"), "no": ("Not answered yet", "none")}[q[2]]
        ptr = f' <a href="#a-{q[4]}" data-to="a-{q[4]}">See “{esc(by[q[4]]["q"])}” above</a>' if q[4] and q[4] in by and not by[q[4]].get("region") else ""
        orig = (f'<p class="qsrc">Searched as: <span lang="{esc(lang)}">“' + "”, “".join(esc(x) for x in q[1].split(" · ")) + "”</span></p>") if q[1] else ""
        src = f'<p class="qsrc">{esc(q[6])}</p>' if len(q) > 6 and q[6] else ""
        body = orig + src + (need(q[5]) if q[2] != "yes" else "")
        return (f'<details class="qa"><summary><span class="qn">{n:02d}</span><span class="qq">{esc(q[0])}</span>{_chip(*lab)}<span class="qans">{esc(q[3].rstrip("."))}.{ptr}</span></summary>'
                + (f'<div class="qbody">{body}</div>' if body else "") + "</details>")
    tier = lambda c: 0 if c in ("fact", "yes") else 2 if c in ("none", "no") else 1
    G = [a for a in A if not a.get("region")]
    glob = "".join(card(a, i + 1) for i, a in enumerate(G))
    regions = []
    for w, g in DATA["local"].items():
        items = [("s", a, tier(a["cls"])) for a in A if a.get("region") == w] + [("l", q, tier(q[2])) for q in g["qs"]]
        items.sort(key=lambda x: x[2])
        lst = "".join(card(x[1], i + 1) if x[0] == "s" else local_card(x[1], i + 1, g.get("lang", "en")) for i, x in enumerate(items))
        regions.append(f'<div class="qlist" data-where="{esc(w)}"{"" if w == "Australia" else " hidden"} lang="{esc(g.get("lang", "en"))}">'
                       + (f'<p class="note">{esc(g["note"])}</p>' if g.get("note") and w != "Australia" else "") + lst + "</div>")
    opts = "".join(f'<option value="{esc(w)}"{" selected" if w == "Australia" else ""}>{esc(w)}</option>' for w in DATA["local"])
    body = (CSS + '  <p class="lead">Answered with the evidence on this site. Each label shows how strong it is.</p>\n'
            '  <h2 id="global">Global</h2>\n  <p class="note">Asked in every country.</p>\n  <div class="qlist">' + glob + "</div>\n"
            '  <h2 id="regional">Regional</h2>\n  <p class="qpick"><label for="qwhere">Asked in</label> <select id="qwhere">' + opts + "</select></p>\n  "
            + "".join(regions) + "\n" + JS
            + '  <p class="note">General information only, not safety, medical or professional advice. Follow lifesavers, beach signs and local authorities. Spotted an error? <a href="/#contact">Tell us</a>.</p>\n')
    written = [write("questions/index", page("questions/", "What are people asking about sharks online?", "Questions", body,
                     desc="Answers to the questions people search about sharks, worldwide and by country: how many shark attacks a year, whether they're rare or increasing, shark season, rain, nets and more."))]
    for a in A:
        if a.get("long_page"): continue
        secs = ""
        if a["detail"]: secs += "  <h2>What we know</h2>\n  <ul>" + "".join(f"<li>{x}</li>" for x in a["detail"]) + "</ul>\n"
        if a["claims"]: secs += "  <h2>The evidence</h2>\n  <p>Each claim is tested on the Research page, with its data, method and limits.</p>\n  " + claims_ul(a) + "\n"
        if a.get("see"): secs += f'  <p><a href="{a["see"][1]}">{esc(a["see"][0])}</a></p>\n'
        if a.get("need"): secs += "  <h2>Still to find out</h2>\n  " + need(a["need"]) + "\n"
        if a.get("src"): secs += f"  <h2>Sources</h2>\n  <p>{esc(a['src'])}</p>\n"
        secs += '  <h2>More questions</h2>\n  <p><a href="/questions/">What people ask about sharks, answered</a></p>\n'
        body = (f'  <p class="answer">{a["a"]}</p>\n  <p class="meta">{esc(a["status"])}' + (f' · {esc(a["asof"])}' if a.get("asof") else "") + "</p>\n" + secs
                + '  <p class="note">General information only, not safety, medical or professional advice. Follow lifesavers, beach signs and local authorities. Spotted an error? <a href="/#contact">Tell us</a>.</p>\n')
        ld = {"@context": "https://schema.org", "@type": "Article", "headline": a["q"], "description": text(a["a"])[:300], "dateModified": D.get("built", "")[:10],
              "author": {"@type": "Organization", "@id": "https://19-degrees.org/#org", "name": "19 Degrees"}, "publisher": {"@id": "https://19-degrees.org/#org"},
              "mainEntityOfPage": f"https://19-degrees.org/questions/{a['slug']}"}
        written.append(write(f"questions/{a['slug']}", page(f"questions/{a['slug']}", a["q"], "Questions", body, desc=text(a["a"])[:300], jsonld=ld, crumbs=[("Questions", "/questions/")])))
    return written

CSS = """  <style>
.qlist{display:grid;gap:10px;margin:12px 0 28px}.qa{border:1px solid var(--rule);background:rgba(11,44,70,.45)}
.qa>summary{list-style:none;cursor:pointer;padding:16px 18px;display:grid;gap:8px}.qa>summary::-webkit-details-marker{display:none}
.qn{font:500 12px var(--f-data);color:var(--muted)}.qq{font:700 19px/1.25 var(--f-display);color:var(--ink)}.qans{color:#C9DCE3}
.qasof{font:500 12px/1.5 var(--f-data);color:var(--muted)}.qbody{padding:0 18px 16px;display:grid;gap:8px;color:#C9DCE3;font-size:15px}
.qbody ul{margin:0;padding-left:20px}.qev,.qsrc{margin:0;color:var(--muted)}.qevl{list-style:none;padding:0;display:flex;flex-wrap:wrap;gap:6px 14px}
.need{margin:0;color:var(--muted)}.need b{color:var(--ink)}.qmore{color:var(--cold);font-weight:600}
.ast{justify-self:start;font:500 11px var(--f-data);letter-spacing:.08em;text-transform:uppercase;border:1px solid;border-radius:999px;padding:2px 9px}
.ast.fact{color:#7FD1AE}.ast.lean{color:var(--warm)}.ast.open{color:var(--cold)}.ast.none{color:var(--muted)}
.qpick select{font:inherit;color:var(--ink);background:#041A2C;border:1px solid var(--rule);padding:8px 10px;min-height:44px}
  </style>
"""
JS = """  <script>
(function(){var s=document.getElementById("qwhere");if(!s)return;
function show(w){document.querySelectorAll(".qlist[data-where]").forEach(function(d){d.hidden=d.getAttribute("data-where")!==w});try{localStorage.setItem("qwhere",w)}catch(e){}}
var v=null;try{v=localStorage.getItem("qwhere")}catch(e){}if(v&&document.querySelector('.qlist[data-where="'+v+'"]')){s.value=v;show(v)}
s.addEventListener("change",function(){show(s.value)});
function open(){var d=location.hash&&document.getElementById(location.hash.slice(1));if(d&&d.tagName==="DETAILS"){d.open=true}}
addEventListener("hashchange",open);open();
document.addEventListener("click",function(e){var l=e.target.closest&&e.target.closest("a[data-to]");if(l){var d=document.getElementById(l.getAttribute("data-to"));if(d)d.open=true}});})();
  </script>
"""
