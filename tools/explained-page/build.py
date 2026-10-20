#!/usr/bin/env python3
"""Build the webpage version of ABOT-red-team-explained.md.

Every word on the page comes from the markdown, apart from the links to page 2 (the Q&A prep
plan, built by build_plan.py). To change the content, edit ABOT-red-team-explained.md and run
this again; don't edit the HTML by hand.

    python -E -P tools/explained-page/build.py [--fragment PATH]

Writes ABOT-red-team-explained.html next to the markdown: one standalone file
with its styles and script inline, so it opens offline (the web fonts need a
connection and fall back to system fonts without one). --fragment PATH also
writes the page without its <html>/<head>/<body> skeleton, which is the form
the claude.ai Artifact publisher expects.

The script stops with an error if the markdown no longer has the structure it
expects (52 entries, each with a badge line, "What it is", "Why it's an issue"
and "Impact on your talk"; badges that match the at-a-glance table).
"""
import argparse
import html
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SRC = ROOT / "ABOT-red-team-explained.md"
OUT = ROOT / "ABOT-red-team-explained.html"

PAGE_TITLE = "ABOT red team, explained"
DESCRIPTION = ("Plain-English guide to the 52 red-team points anyone can raise from the ABOT "
               "camera-ready paper, sorted by what each one means for the R10-HTC talk.")
PLAN_HREF = "ABOT-qa-prep-plan.html"  # page 2; the same name locally and inside the Artifact
ARROW_R = ('<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
           'stroke-linejoin="round" aria-hidden="true"><path d="M4 10h12M11 5l5 5-5 5"/></svg>')
FONTS = ("https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,500..800"
         "&family=IBM+Plex+Mono:wght@400;500"
         "&family=Public+Sans:ital,wght@0,400;0,600;0,700;1,400&display=swap")

CATS = ["answer", "wording", "aside"]
CAT_LABEL = {"answer": "Have an answer ready", "wording": "Watch your wording", "aside": "Safe to set aside"}
PRI = {"Critical": "critical", "Major": "major", "Minor": "minor"}
EMOJI = [("✏️", "wording"), ("✏", "wording"), ("🔴", "critical"), ("🟠", "major"),
         ("🟡", "minor"), ("🎯", "answer"), ("💤", "aside")]

# Short labels for the contents rail, in document order.
Q_SHORT = [
    "Is the task too easy?",
    "Do SOS messages reach a rescuer?",
    "How does a node know the whole network?",
    "Isn't the planner chasing its own score?",
    "How does it compare with existing mesh systems?",
    "Won't the channel jam?",
]
RULE_SHORT = [
    'No "6.7 million deaths"',
    "A protocol with four layers",
    "Range: about 2 km",
    'No "33-minute window"',
    "Fig. 2 and the damage levels",
    "The speed-up figure",
    "V-C numbers and sample sizes",
    "Success is at ceiling",
    "Don't oversell PPO",
    "The abstract's two claims",
    "Duty cycle as airtime",
]

WARN = '<span class="warn" aria-hidden="true">!</span>'
EXT_CHIP = f'<span class="ext">{WARN}Outside fact</span>'
BADGE = re.compile(r"^(🔴|🟠|🟡) \*\*(\w+)\*\* · Hard to defend: \*\*(\d+)\*\*/100 · Paper: (.+)$")


def fail(msg):
    sys.exit(f"build.py: {msg}")


def esc(s):
    return html.escape(s, quote=False)


def attr(s):
    return html.escape(s, quote=True)


def gh_slug(s):
    """GitHub's heading anchor, so links written for the markdown still work."""
    s = re.sub(r"[^\w\- ]", "", s.strip().lower())
    return s.replace(" ", "-")


def id_slug(s):
    return re.sub(r"-+", "-", gh_slug(s)).strip("-") or "x"


def dot(cls):
    return f'<span class="dot {cls}" aria-hidden="true"></span>'


def meter(score):
    return f'<span class="meter" aria-hidden="true"><i style="width:{score}%"></i></span>'


# ---------------------------------------------------------------- inline markdown

def autolink(s, skip_id=None):
    """Link every P-xx and "Question N" in running text (not inside links or code)."""
    out, in_a, in_code = [], 0, 0
    for part in re.split(r"(<[^>]+>)", s):
        if part.startswith("<"):
            tag = part[1:].split()[0].rstrip(">").lower() if len(part) > 2 else ""
            in_a += {"a": 1, "/a": -1}.get(tag, 0)
            in_code += {"code": 1, "/code": -1}.get(tag, 0)
            out.append(part)
            continue
        if not (in_a or in_code):
            part = re.sub(r"\bP-\d\d\b",
                          lambda m: m.group(0) if m.group(0) == skip_id
                          else f'<a class="pref" href="#{m.group(0)}">{m.group(0)}</a>', part)
            part = re.sub(r"\bQuestion ([1-6])\b", lambda m: f'<a href="#q{m.group(1)}">{m.group(0)}</a>', part)
        out.append(part)
    return "".join(out)


def inline(t, skip_id=None):
    t = t.replace("\\*", "\x00")
    codes = []

    def keep_code(m):
        codes.append(m.group(1))
        return f"\x01{len(codes) - 1}\x02"

    t = re.sub(r"`([^`]+)`", keep_code, t)
    t = esc(t)

    def link(m):
        label, href = m.group(1), m.group(2)
        if href.startswith("#"):
            return f'<a href="{attr(href)}">{label}</a>'
        if re.search(r"\.(md|xlsx|py|docx|html)$", href):
            return label  # files in the prep folder aren't part of the page
        return f'<a href="{attr(href)}" rel="noopener" target="_blank">{label}</a>'

    t = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", link, t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<![\w*])\*(?=\S)(.+?)(?<=\S)\*(?![\w*])", r"<em>\1</em>", t)
    for e, cls in EMOJI:
        t = t.replace(e + " ", dot(cls)).replace(e, dot(cls))
    t = t.replace("⚠️ ", WARN).replace("⚠️", WARN).replace("⚠", WARN)
    t = re.sub(r"\x01(\d+)\x02", lambda m: f"<code>{esc(codes[int(m.group(1))])}</code>", t)
    t = t.replace("\x00", "*")
    if "*" in re.sub(r"<[^>]+>", "", t).replace("A*", ""):
        fail(f"unconverted asterisk in: {t[:120]}")
    return autolink(t, skip_id)


# ---------------------------------------------------------------- block markdown

class Node:
    def __init__(self, level, title):
        self.level, self.title, self.lines, self.children, self.blocks = level, title, [], [], []


def parse_table(rows):
    cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
    if not re.fullmatch(r"[\s:|-]+", rows[1]):
        fail(f"table without a separator row: {rows[0][:80]}")
    return cells[0], cells[2:]


def parse_blocks(lines):
    out, i, n = [], 0, len(lines)
    while i < n:
        line = lines[i]
        if not line.strip():
            i += 1
        elif line.startswith("|"):
            rows = []
            while i < n and lines[i].startswith("|"):
                rows.append(lines[i])
                i += 1
            out.append(("table", parse_table(rows)))
        elif line.startswith(">"):
            q = []
            while i < n and lines[i].startswith(">"):
                q.append(re.sub(r"^> ?", "", lines[i]))
                i += 1
            out.append(("quote", parse_blocks(q)))
        elif re.match(r"^- \[[ xX]\] ", line):
            items = []
            while i < n and re.match(r"^- \[[ xX]\] ", lines[i]):
                items.append(re.sub(r"^- \[[ xX]\] ", "", lines[i]))
                i += 1
            out.append(("check", items))
        elif line.startswith("- "):
            items = []
            while i < n:
                cur = lines[i]
                if cur.startswith("- "):
                    items.append([cur[2:], []])
                elif re.match(r"^ {2,}- ", cur):
                    items[-1][1].append(cur.strip()[2:])
                else:
                    break
                i += 1
            out.append(("ul", items))
        elif re.match(r"^\d+\. ", line):
            items = []
            while i < n and re.match(r"^\d+\. ", lines[i]):
                items.append(re.sub(r"^\d+\. ", "", lines[i]))
                i += 1
            out.append(("ol", items))
        else:
            para = [line]
            i += 1
            while i < n and lines[i].strip() and not re.match(r"^(\||>|- |\d+\. )", lines[i]):
                para.append(lines[i])
                i += 1
            out.append(("p", para))
    return out


def build_tree(text):
    root = Node(0, "")
    stack = [root]
    for line in text.split("\n"):
        m = re.match(r"^(#{1,6}) (.+?)\s*$", line)
        if m:
            node = Node(len(m.group(1)), m.group(2))
            while stack[-1].level >= node.level:
                stack.pop()
            stack[-1].children.append(node)
            stack.append(node)
        else:
            stack[-1].lines.append(line)

    def fill(node):
        node.blocks = parse_blocks(node.lines)
        for c in node.children:
            fill(c)

    fill(root)
    return root


def ptext(block):
    return " ".join(block[1])


def render_ul(items, skip_id=None):
    lis = []
    for text, subs in items:
        body = inline(text, skip_id)
        if subs:
            body += "<ul>" + "".join(f"<li>{inline(s, skip_id)}</li>" for s in subs) + "</ul>"
        lis.append(f"<li>{body}</li>")
    return "<ul>" + "".join(lis) + "</ul>"


def render_items(items, skip_id=None):
    out = []
    for kind, val in items:
        if kind == "p":
            out.append(f"<p>{inline(val, skip_id)}</p>")
        elif kind == "ol":
            out.append("<ol>" + "".join(f"<li>{inline(x, skip_id)}</li>" for x in val) + "</ol>")
        else:
            fail(f"unexpected item {kind}")
    return "".join(out)


def render_generic(blocks):
    out = []
    for b in blocks:
        if b[0] == "p":
            out.append(f"<p>{inline(ptext(b))}</p>")
        elif b[0] == "ul":
            out.append(render_ul(b[1]))
        elif b[0] == "ol":
            out.append("<ol>" + "".join(f"<li>{inline(x)}</li>" for x in b[1]) + "</ol>")
        else:
            fail(f"unexpected block {b[0]} in running text")
    return "".join(out)


# ---------------------------------------------------------------- entries

def parse_entry(node):
    m = re.match(r"^(P-\d\d) · (.+)$", node.title)
    if not m:
        fail(f"entry heading not understood: {node.title}")
    e = dict(id=m.group(1), title=m.group(2), badge=None, what=[], why=[], why_lead=None,
             impact=[], backup=[], ext=None)
    cur = None
    labels = (("**What it is.**", "what"), ("**Why it's an issue.**", "why"), ("**Impact on your talk.**", "impact"))
    for b in node.blocks:
        if b[0] == "p":
            t = ptext(b)
            mb = BADGE.match(t)
            if mb:
                e["badge"] = dict(pri=mb.group(2), score=int(mb.group(3)), paper=mb.group(4))
                continue
            for label, key in labels:
                if t.startswith(label):
                    cur, rest = key, t[len(label):].strip()
                    if rest and key == "why":
                        e["why_lead"] = rest
                    elif rest:
                        e[key].append(("p", rest))
                    break
            else:
                if t.startswith("⚠"):
                    e["ext"] = t
                elif cur is None:
                    fail(f"{e['id']}: text before 'What it is': {t[:60]}")
                else:
                    e[cur].append(("p", t))
        elif b[0] == "ol":
            e[cur].append(("ol", b[1]))
        elif b[0] == "quote":
            e["backup"].append(b[1])
        else:
            fail(f"{e['id']}: unexpected {b[0]} block")
    if not (e["badge"] and e["what"] and (e["why"] or e["why_lead"]) and e["impact"]):
        fail(f"{e['id']}: missing badge, What, Why or Impact")
    return e


def split_section(items):
    before, lst, after = [], None, []
    for kind, val in items:
        if kind == "ol":
            if lst is not None:
                fail("two numbered lists in one section")
            lst = val
        elif lst is None:
            before.append(val)
        else:
            after.append(val)
    return before, lst, after


FILLER_LEADS = {"Each problem matters for its own reason:"}
REPORT = []


def render_entry(e, cat, tag_href, tag_text):
    pid, b = e["id"], e["badge"]
    pri = PRI[b["pri"]]
    w_before, w_list, w_after = split_section(e["what"])
    y_before, y_list, y_after = split_section(e["why"])
    lead = e["why_lead"]
    paired = bool(w_list and y_list and len(w_list) == len(y_list) and not y_before)
    REPORT.append((pid, "paired" if paired else "plain", len(w_list or []), len(y_list or []), lead if paired else ""))

    head = (f'<header class="pt-h"><div class="pt-top"><a class="pt-id" href="#{pid}">{pid}</a>'
            f'<a class="tag" href="{tag_href}">{dot(cat)}{esc(tag_text)}</a></div>'
            f'<h4>{inline(e["title"], pid)}</h4>'
            f'<p class="badges"><span class="pri">{dot(pri)}{b["pri"]}</span>'
            f'<span class="hd"><span class="hd-l">Hard to defend</span>{meter(b["score"])}'
            f'<span><b>{b["score"]}</b>/100</span></span>'
            f'<span class="sec-tag">Paper: {esc(b["paper"])}</span>'
            f'{EXT_CHIP if e["ext"] else ""}</p></header>')

    x = ['<div class="pt-explain">']
    if paired:
        x.append('<div class="blk prose"><h5 class="lbl">What it is</h5>'
                 + "".join(f"<p>{inline(p, pid)}</p>" for p in w_before) + "</div>")
        if lead and lead not in FILLER_LEADS:
            x.append(f'<p>{inline(lead, pid)}</p>')
        x.append('<div class="pairs-h" aria-hidden="true"><span></span><span class="lbl">The problem</span>'
                 "<span class=\"lbl\">Why it's an issue</span></div>")
        x.append('<ol class="pairs" role="list">')
        for i, (prob, why) in enumerate(zip(w_list, y_list), 1):
            x.append(f'<li><span class="n" aria-hidden="true">{i}</span>'
                     f'<div class="prob"><span class="vh">Problem {i}: </span>{inline(prob, pid)}</div>'
                     f"<div class=\"why\"><span class=\"lbl\">Why it's an issue</span>{inline(why, pid)}</div></li>")
        x.append("</ol>")
        x.extend(f"<p>{inline(p, pid)}</p>" for p in w_after)
        x.extend(f'<p class="sum">{inline(p, pid)}</p>' for p in y_after)
    else:
        x.append('<div class="blk prose"><h5 class="lbl">What it is</h5>' + render_items(e["what"], pid) + "</div>")
        why_items = ([("p", lead)] if lead else []) + e["why"]
        x.append("<div class=\"blk prose\"><h5 class=\"lbl\">Why it's an issue</h5>" + render_items(why_items, pid) + "</div>")
    x.append("</div>")

    tail = [f'<div class="impact prose"><h5 class="lbl">Impact on your talk</h5>{render_items(e["impact"], pid)}</div>']
    for q in e["backup"]:
        ps = [ptext(blk) for blk in q if blk[0] == "p"]
        mq = re.match(r'^\*\*Only if asked:\*\* \*(.+)\*$', ps[0])
        if not mq:
            fail(f"{pid}: backup line not understood")
        tail.append('<div class="backup"><p class="lbl">Only if asked</p>'
                    f'<p class="bq">{inline(mq.group(1), pid)}</p>'
                    + "".join(f'<p class="ba">{inline(p, pid)}</p>' for p in ps[1:]) + "</div>")
    if e["ext"]:
        note = e["ext"].replace("⚠️", "").replace("⚠", "").strip()
        tail.append(f'<p class="ext-note">{WARN}<span>{inline(note, pid)}</span></p>')

    more = '<button type="button" class="pt-more linkbtn" aria-expanded="false">Show the full explanation</button>'
    return (f'<article class="pt" id="{pid}" data-cat="{cat}" data-pri="{pri}" data-search="Points" '
            f'data-key="{pid}" data-title="{attr(e["title"])}" data-href="#{pid}">'
            + head + "".join(x) + more + "".join(tail) + "</article>")


# ---------------------------------------------------------------- sections

def section_by_title(h1, title):
    for c in h1.children:
        if c.title == title or c.title.startswith(title):
            return c
    fail(f"section '{title}' not found")


def parse_glance(node):
    tables = [b for b in node.blocks if b[0] == "table"]
    header, rows = tables[0][1]
    out = {}
    for pid, line, pri, score, talk in rows:
        out[pid] = dict(line=line, pri=pri.split()[-1], score=int(score), talk=talk)
    if len(out) != 52:
        fail(f"at-a-glance table has {len(out)} rows, expected 52")
    return out


def render_start(node):
    out, blocks, i = [], node.blocks, 0
    while i < len(blocks):
        b = blocks[i]
        if b[0] == "table":
            header, rows = b[1]
            tiles = []
            for label, pts, todo in rows:
                cat = "answer" if "🎯" in label else "wording" if "✏" in label else "aside"
                name = CAT_LABEL[cat]
                if name not in label:
                    fail(f"talk category label changed: {label}")
                tiles.append(f'<div class="tile"><p class="tile-k">{dot(cat)}{esc(name)}</p>'
                             f'<p class="tile-n"><b>{esc(pts)}</b> {esc(header[1].lower())}</p>'
                             f'<p class="tile-t">{inline(todo)}</p></div>')
            out.append('<div class="tiles">' + "".join(tiles) + "</div>")
        elif b[0] == "p" and ptext(b).startswith("**Reading the badge line.**"):
            t = ptext(b)
            mb = re.search(r"Example: (.+)$", t)
            ex = BADGE.match(mb.group(1))
            if not ex:
                fail("badge example not understood")
            pri = ex.group(2)
            out.append("<p><strong>Reading the badge line.</strong> Example:</p>")
            out.append(f'<p class="badges sample"><span class="pri">{dot(PRI[pri])}{pri}</span>'
                       f'<span class="hd"><span class="hd-l">Hard to defend</span>{meter(int(ex.group(3)))}'
                       f'<span><b>{ex.group(3)}</b>/100</span></span>'
                       f'<span class="sec-tag">Paper: {esc(ex.group(4))}</span></p>')
        elif b[0] == "p" and ptext(b).startswith("**Two cautions.**"):
            inner = f"<p>{inline(ptext(b))}</p>"
            if i + 1 < len(blocks) and blocks[i + 1][0] == "ul":
                inner += render_ul(blocks[i + 1][1])
                i += 1
            out.append(f'<div class="callout">{inner}</div>')
        elif b[0] == "ul":
            items = []
            for text, subs in b[1]:
                if text.startswith("⚠️ marks"):
                    text = text.replace("⚠️ ", "\x03", 1)
                items.append([text, subs])
            out.append(render_ul(items).replace("\x03", EXT_CHIP + " "))
        else:
            out.append(render_generic([b]))
        i += 1
    return out


def render_glance(node, glance, where):
    intro = [ptext(b) for b in node.blocks if b[0] == "p"]
    counts = {"cat": {}, "pri": {}, "ext": 0}
    rows = []
    for pid, g in glance.items():
        w = where[pid]
        counts["cat"][w["cat"]] = counts["cat"].get(w["cat"], 0) + 1
        counts["pri"][g["pri"]] = counts["pri"].get(g["pri"], 0) + 1
        counts["ext"] += w["ext"]
        talk_label = re.sub(r"^\S+\s+", "", g["talk"])
        talk = f'<a class="tag" href="{w["href"]}">{dot(w["cat"])}{esc(talk_label)}</a>'
        rows.append(
            f'<tr id="row-{pid}" data-cat="{w["cat"]}" data-pri="{PRI[g["pri"]]}" data-score="{g["score"]}" data-ext="{w["ext"]}">'
            f'<td class="c-id"><a href="#{pid}">{pid}</a></td>'
            f'<td class="c-line"><a href="#{pid}">{inline(g["line"])}</a></td>'
            f'<td class="c-pri">{dot(PRI[g["pri"]])}{g["pri"]}</td>'
            f'<td class="c-hd"><span class="vh">Hard to defend: </span>{meter(g["score"])}{g["score"]}</td>'
            f'<td class="c-talk">{talk}</td></tr>')

    def chip(f, v, label, n, mark):
        return (f'<button type="button" class="chip" data-f="{f}" data-v="{v}" aria-pressed="false">'
                f'{mark}{esc(label)} <span class="c">{n}</span></button>')

    tools = ['<div class="idx-tools" id="idxTools">',
             '<div class="ctl"><p class="lbl" id="f-talk">For your talk</p><div class="chips" role="group" aria-labelledby="f-talk">',
             chip("cat", "answer", "Answer ready", counts["cat"].get("answer", 0), dot("answer")),
             chip("cat", "wording", "Watch your wording", counts["cat"].get("wording", 0), dot("wording")),
             chip("cat", "aside", "Set aside", counts["cat"].get("aside", 0), dot("aside")),
             "</div></div>",
             '<div class="ctl"><p class="lbl" id="f-pri">Priority</p><div class="chips" role="group" aria-labelledby="f-pri">',
             chip("pri", "critical", "Critical", counts["pri"].get("Critical", 0), dot("critical")),
             chip("pri", "major", "Major", counts["pri"].get("Major", 0), dot("major")),
             chip("pri", "minor", "Minor", counts["pri"].get("Minor", 0), dot("minor")),
             "</div></div>",
             '<div class="ctl"><p class="lbl" id="f-flag">Flag</p><div class="chips" role="group" aria-labelledby="f-flag">',
             chip("ext", "1", "Outside fact", counts["ext"], WARN),
             "</div></div>",
             '<div class="ctl"><p class="lbl" id="f-sort">Sort by</p><div class="seg" role="group" aria-labelledby="f-sort">'
             '<button type="button" data-sort="id" aria-pressed="true">ID</button>'
             '<button type="button" data-sort="score" aria-pressed="false">Hard to defend</button></div></div>',
             "</div>"]
    legend = inline(intro[0])
    html_ = [f'<div class="prose"><p>{legend} Each row opens the full entry. Filter the list by what to do in '
             'your talk, by priority or by the outside-fact flag, or sort it by how hard each point is to defend.</p></div>',
             "".join(tools),
             '<p class="idx-status"><span id="idxCount" aria-live="polite">Showing all 52 points</span>'
             '<button type="button" class="linkbtn" id="idxClear" hidden>Clear filters</button></p>',
             '<div class="tbl-wrap"><table class="idx" id="idx"><thead><tr>'
             '<th scope="col">ID</th><th scope="col">The problem in one line</th><th scope="col">Priority</th>'
             '<th scope="col">Hard to defend</th><th scope="col">For your talk</th></tr></thead><tbody>'
             + "".join(rows) + "</tbody></table></div>",
             '<p class="idx-empty" id="idxEmpty" hidden>No points match all of these filters. Clear one to see more.</p>']
    return html_, counts


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--fragment", type=Path, help="also write the Artifact form of the page here")
    args = ap.parse_args()

    md = SRC.read_text(encoding="utf-8")
    tree = build_tree(md)
    if len(tree.children) != 1 or tree.children[0].level != 1:
        fail("expected one top-level '# ' title")
    h1 = tree.children[0]
    name, _, subtitle = h1.title.partition(": ")

    meta = {}
    for b in h1.blocks:
        if b[0] != "p":
            continue
        for line in b[1]:
            m = re.match(r"^\*\*(\w[\w ]*):\*\* (.+)$", line)
            if m:
                meta[m.group(1)] = m.group(2)
    for k in ("For", "Date", "Built from"):
        if k not in meta:
            fail(f"header line '{k}:' missing")

    glance_node = section_by_title(h1, "All 52 at a glance")
    glance = parse_glance(glance_node)
    parts = [section_by_title(h1, f"Part {n}:") for n in (1, 2, 3)]

    # First pass: where each entry lives, for the index and the cross-links.
    where = {}
    for n, part in enumerate(parts):
        cat = CATS[n]
        for si, sub in enumerate(part.children):
            if n == 0:
                mq = re.match(r"^Q(\d)\. ", sub.title)
                sub_id, sub_label = f"q{mq.group(1)}", f"Answer ready · Q{mq.group(1)}"
            else:
                sub_id, sub_label = id_slug(sub.title), ("Watch your wording" if n == 1 else "Set aside")
            sub.anchor = sub_id
            for entry in sub.children:
                pid = entry.title.split(" · ")[0]
                ext = int(any(b[0] == "p" and ptext(b).startswith("⚠") for b in entry.blocks))
                where[pid] = dict(cat=cat, href=f"#{sub_id}", label=sub_label, ext=ext)
    if sorted(where) != sorted(glance):
        fail("the entries and the at-a-glance table list different IDs")

    # ---- hero
    counts_by_cat = {c: sum(1 for w in where.values() if w["cat"] == c) for c in CATS}
    groups_by_cat = {"answer": f"{len(parts[0].children)} questions to prepare",
                     "wording": f"{len(parts[1].children)} wording rules",
                     "aside": "Read once, so nothing surprises you"}
    part_ids = [gh_slug(p.title) for p in parts]
    hero = [f'<header class="hero" id="top"><p class="eyebrow">IEEE R10-HTC 2026 · Talk prep · Page 1 of 2</p>',
            f"<h1>{esc(name)}</h1>",
            f'<p class="subtitle">{esc(subtitle[:1].upper() + subtitle[1:])}</p>',
            '<dl class="meta">']
    for k in ("For", "Date", "Built from"):
        hero.append(f'<div><dt class="lbl">{esc(k)}</dt><dd>{inline(meta[k])}</dd></div>')
    hero.append("</dl>")
    hero.append('<nav class="split" aria-label="The 52 points by what they mean for your talk">'
                '<div class="split-bar" aria-hidden="true">'
                + "".join(f'<i class="{c}" style="flex-grow:{counts_by_cat[c]}"></i>' for c in CATS)
                + '</div><ol class="split-legend">'
                + "".join(f'<li><a href="#{part_ids[i]}">{dot(c)}<span class="sl-n">{counts_by_cat[c]}</span>'
                          f'<span class="sl-t">{CAT_LABEL[c]}<small>{groups_by_cat[c]}</small></span></a></li>'
                          for i, c in enumerate(CATS))
                + "</ol></nav>"
                + f'<a class="plan-banner" href="{PLAN_HREF}"><span><span class="eyebrow">Page 2</span>'
                '<span class="pb-t">Q&amp;A prep plan</span><span class="pb-s">The points you chose to prepare, '
                'reviewed and regrouped into 9 sets, each with an opening line to learn.</span></span>'
                f'<span class="go">Open page 2{ARROW_R}</span></a></header>')

    # ---- start here
    start = section_by_title(h1, "Start here")
    sections = [f'<section class="sec" id="start-here" data-search="Sections" data-key="Section" '
                f'data-title="Start here" data-href="#start-here"><h2>Start here</h2>'
                f'<div class="prose">{"".join(render_start(start))}</div></section>']

    # ---- at a glance
    glance_html, counts = render_glance(glance_node, glance, where)
    sections.append('<section class="sec" id="all-52-at-a-glance"><h2>All 52 at a glance</h2>'
                    + "".join(glance_html) + "</section>")

    # ---- the three parts
    toc_parts, entry_count, seen = [], 0, set()
    view_seg = ('<div class="seg" role="group" aria-label="How much of each entry to show">'
                '<button type="button" data-view-btn="full" aria-pressed="true">Full explanations</button>'
                '<button type="button" data-view-btn="actions" aria-pressed="false">Talk actions only</button></div>')
    for n, part in enumerate(parts):
        cat = CATS[n]
        pnum, ptitle = part.title.split(": ", 1)
        pid_anchor = gh_slug(part.title)
        n_entries = sum(len(s.children) for s in part.children)
        if n == 0:
            grouping = f" · {len(part.children)} questions"
        elif n == 1:
            grouping = f" · {len(part.children)} rules"
        else:
            grouping = f" · {len(part.children)} groups"
        out = [f'<section class="sec part" id="{pid_anchor}"><div class="part-head">'
               f'<p class="eyebrow">{dot(cat)}{esc(pnum)} of 3 · {n_entries} points{grouping}</p>'
               f"<h2>{esc(ptitle)}</h2><div class=\"prose\">{render_generic(part.blocks)}</div>{view_seg}</div>"]
        subs_toc = []
        for si, sub in enumerate(part.children):
            if n == 0:
                mq = re.match(r'^Q(\d)\. (.+)$', sub.title)
                qn, qtext = mq.group(1), mq.group(2)
                answer, notes, behind = None, [], None
                for b in sub.blocks:
                    if b[0] == "quote":
                        t = " ".join(ptext(x) for x in b[1] if x[0] == "p")
                        ma = re.match(r"^\*\*Your answer:\*\* (.+)$", t)
                        if not ma:
                            fail(f"Q{qn}: answer not understood")
                        answer = ma.group(1)
                    elif b[0] == "p" and ptext(b).startswith("*Points behind"):
                        behind = ptext(b)
                    elif b[0] == "p":
                        notes.append(ptext(b))
                    else:
                        fail(f"Q{qn}: unexpected {b[0]}")
                head = (f'<div class="q-head" data-search="Questions" data-key="Q{qn}" data-title="{attr(Q_SHORT[si])}" '
                        f'data-href="#q{qn}"><p class="eyebrow">Question {qn}</p><h3>{inline(qtext)}</h3>'
                        f'<div class="ans"><p class="lbl">Your answer</p><p>{inline(answer)}</p></div>'
                        + "".join(f'<p class="note">{inline(x)}</p>' for x in notes)
                        + f'<p class="behind">{inline(behind)}</p></div>')
                cls, sid, toc_label = "q", f"q{qn}", f'<span class="k">Q{qn}</span>{esc(Q_SHORT[si])}'
            elif n == 1:
                swap, behind = None, None
                for b in sub.blocks:
                    if b[0] == "table":
                        header, rows = b[1]
                        if header != ["Avoid", "Say instead"] or len(rows) != 1:
                            fail(f"rule table not understood: {sub.title}")
                        swap = rows[0]
                    elif b[0] == "p" and ptext(b).startswith("*Points behind"):
                        behind = ptext(b)
                    else:
                        fail(f"rule '{sub.title}': unexpected {b[0]}")
                head = (f'<div class="rule-head" data-search="Rules" data-key="Rule" data-title="{attr(sub.title)}" '
                        f'data-href="#{sub.anchor}"><h3>{inline(sub.title)}</h3><div class="swap">'
                        f'<div class="avoid"><p class="lbl">Avoid</p><p>{inline(swap[0])}</p></div>'
                        f'<div class="say"><p class="lbl">Say instead</p><p>{inline(swap[1])}</p></div></div>'
                        f'<p class="behind">{inline(behind)}</p></div>')
                cls, sid, toc_label = "rule", sub.anchor, esc(RULE_SHORT[si])
            else:
                why = [ptext(b) for b in sub.blocks if b[0] == "p"]
                if len(why) != 1 or len(sub.blocks) != 1:
                    fail(f"group '{sub.title}' not understood")
                head = (f'<div class="grp-head" data-search="Groups" data-key="Group" data-title="{attr(sub.title)}" '
                        f'data-href="#{sub.anchor}"><h3>{inline(sub.title)}</h3><p class="note">{inline(why[0])}</p></div>')
                cls, sid, toc_label = "grp", sub.anchor, esc(sub.title)
            pts = []
            for entry in sub.children:
                e = parse_entry(entry)
                g = glance[e["id"]]
                if (g["pri"], g["score"]) != (e["badge"]["pri"], e["badge"]["score"]):
                    fail(f"{e['id']}: badge doesn't match the at-a-glance table")
                if e["title"] != g["line"]:
                    fail(f"{e['id']}: title doesn't match the at-a-glance table")
                if e["id"] in seen:
                    fail(f"{e['id']} appears twice")
                seen.add(e["id"])
                w = where[e["id"]]
                pts.append(render_entry(e, cat, w["href"], w["label"]))
                entry_count += 1
            out.append(f'<section class="{cls}" id="{sid}">{head}<div class="pts">{"".join(pts)}</div></section>')
            subs_toc.append(f'<li><a href="#{sid}">{toc_label}</a></li>')
        out.append("</section>")
        sections.append("".join(out))
        toc_parts.append(f'<li><a href="#{pid_anchor}">{dot(cat)}<span>{esc(ptitle)}</span>'
                         f'<span class="count">{n_entries}</span></a><ol class="sub">{"".join(subs_toc)}</ol></li>')
    if entry_count != 52:
        fail(f"rendered {entry_count} entries, expected 52")

    # ---- checklist
    ck_node = section_by_title(h1, "Your slide checklist")
    ck_html, ck_n, group = [], 0, None
    intro_done = False
    for b in ck_node.blocks:
        if b[0] == "p":
            t = ptext(b)
            mg = re.match(r"^\*\*(.+)\*\*$", t)
            if mg:
                if group:
                    ck_html.append("</ul></div>")
                group = mg.group(1)
                ck_html.append(f'<div class="ck-g"><h3>{esc(group)}</h3><ul class="ck" role="list">')
            elif not intro_done:
                ck_html.append(f'<div class="prose"><p>{inline(t)}</p></div>'
                               '<div class="ck-progress"><p id="ckCount" aria-live="polite">0 of  done</p>'
                               '<div class="pbar" aria-hidden="true"><i id="ckBar"></i></div>'
                               '<button type="button" class="linkbtn" id="ckReset" hidden>Clear ticks</button></div>'
                               '<p class="note">Your ticks are saved in this browser only.</p>')
                intro_done = True
            else:
                fail(f"checklist: unexpected text {t[:60]}")
        elif b[0] == "check":
            for item in b[1]:
                ck_n += 1
                ck_html.append(f'<li id="check-{ck_n}" data-search="Checklist" data-key="Check" '
                               f'data-title="{attr(group)}" data-href="#check-{ck_n}">'
                               f'<input type="checkbox" id="ck-{ck_n}"><label for="ck-{ck_n}">{inline(item)}</label></li>')
        else:
            fail(f"checklist: unexpected {b[0]}")
    ck_html.append("</ul></div>")
    ck_html = [h.replace("", str(ck_n)) for h in ck_html]
    sections.append(f'<section class="sec" id="your-slide-checklist"><h2>Your slide checklist</h2>{"".join(ck_html)}</section>')

    # ---- what still stands
    st = section_by_title(h1, "What still stands")
    st_html = []
    for b in st.blocks:
        if b[0] == "table":
            header, rows = b[1]
            st_html.append('<div class="safest">' + "".join(
                f'<div class="safe-row"><p class="safe-k">{inline(r[0])}</p><p>{inline(r[1])}</p></div>' for r in rows)
                + "</div>")
        else:
            st_html.append(render_generic([b]))
    sections.append(f'<section class="sec" id="what-still-stands" data-search="Sections" data-key="Section" '
                    f'data-title="What still stands" data-href="#what-still-stands"><h2>What still stands</h2>'
                    f'<div class="prose">{"".join(st_html)}</div></section>')

    # ---- glossary
    gl = section_by_title(h1, "Glossary")
    gl_html, g_ids = [], set()
    for b in gl.blocks:
        if b[0] == "table":
            header, rows = b[1]
            items = []
            for term, meaning in rows:
                plain = re.sub(r"\*\*|\\", "", term)
                gid = "g-" + id_slug(plain.replace("*", " star"))
                if gid in g_ids:
                    fail(f"duplicate glossary id {gid}")
                g_ids.add(gid)
                items.append(f'<div id="{gid}" data-search="Glossary" data-key="Term" data-title="{attr(plain)}" '
                             f'data-href="#{gid}"><dt>{esc(plain)}</dt><dd>{inline(meaning)}</dd></div>')
            gl_html.append('<dl class="gloss">' + "".join(items) + "</dl>")
        else:
            gl_html.append(f'<div class="prose">{render_generic([b])}</div>')
    sections.append(f'<section class="sec" id="glossary"><h2>Glossary</h2>{"".join(gl_html)}</section>')

    # ---- contents rail
    toc = ['<nav class="toc" id="toc" aria-label="Contents">',
           '<div class="toc-head"><p class="lbl">Contents</p><button type="button" class="toc-close" id="tocClose">Close</button></div>',
           '<div class="toc-view"><p class="lbl" id="tv-l">Entries show</p>'
           '<div class="seg" role="group" aria-labelledby="tv-l">'
           '<button type="button" data-view-btn="full" aria-pressed="true">Everything</button>'
           '<button type="button" data-view-btn="actions" aria-pressed="false">Talk actions only</button></div></div>',
           '<ol class="toc-list">',
           '<li><a href="#start-here">Start here</a></li>',
           '<li><a href="#all-52-at-a-glance">All 52 at a glance</a></li>',
           "".join(toc_parts),
           '<li><a href="#your-slide-checklist">Slide checklist</a></li>',
           '<li><a href="#what-still-stands">What still stands</a></li>',
           '<li><a href="#glossary">Glossary</a></li>',
           f'<li class="toc-page"><a href="{PLAN_HREF}">Q&amp;A prep plan<small>Page 2</small></a></li>',
           "</ol></nav>"]

    bar = ('<header class="bar">'
           '<button type="button" class="menu-btn" id="menuBtn" aria-expanded="false" aria-controls="toc">'
           '<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true">'
           '<path d="M3 5h14M3 10h14M3 15h9"/></svg><span>Contents</span></button>'
           '<a class="brand" href="#top">ABOT red team</a>'
           '<div class="search" role="search">'
           '<svg class="search-ic" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true">'
           '<circle cx="8.5" cy="8.5" r="5.5"/><path d="M13 13l4 4"/></svg>'
           '<label class="vh" for="q">Search the guide</label>'
           '<input id="q" type="search" placeholder="Search the guide" autocomplete="off" '
           'spellcheck="false" enterkeyhint="search" aria-controls="results" aria-expanded="false">'
           '<kbd class="kbd" aria-hidden="true">/</kbd>'
           '<div class="results" id="results" role="region" aria-label="Search results" aria-live="polite" hidden></div>'
           f'</div><a class="pagelink" href="{PLAN_HREF}"><span class="pl-long">Q&amp;A prep plan</span>'
           f'<span class="pl-short">Page 2</span>{ARROW_R}</a></header>')

    totop = ('<a class="totop" id="totop" href="#top" hidden><svg viewBox="0 0 20 20" fill="none" stroke="currentColor" '
             'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M10 16V4M5 9l5-5 5 5"/></svg>Top</a>')

    css = (HERE / "page.css").read_text(encoding="utf-8")
    js = (HERE / "page.js").read_text(encoding="utf-8")
    early = ("<script>try{if(localStorage.getItem('abotrt.view')==='actions')"
             "document.documentElement.setAttribute('data-view','actions')}catch(e){}</script>")
    head_bits = (f"<title>{esc(PAGE_TITLE)}</title>\n"
                 '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
                 '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
                 f'<link rel="stylesheet" href="{attr(FONTS)}">\n'
                 f"<style>\n{css}</style>\n{early}\n")
    body = ('<a class="skip" href="#main">Skip to the guide</a>\n' + bar + '\n<div class="scrim" id="scrim" hidden></div>\n'
            '<div class="shell">' + "".join(toc) + '<main id="main" tabindex="-1">' + "".join(hero)
            + "\n".join(sections) + "</main></div>\n" + totop + f"\n<script>\n{js}</script>\n")

    standalone = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
                  '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
                  f'<meta name="description" content="{attr(DESCRIPTION)}">\n'
                  + head_bits + "</head>\n<body>\n" + body + "</body>\n</html>\n")
    OUT.write_text(standalone, encoding="utf-8", newline="\n")
    print(f"wrote {OUT.relative_to(ROOT)} ({len(standalone.encode('utf-8')) / 1024:.0f} KB)")
    if args.fragment:
        frag = head_bits + body
        args.fragment.write_text(frag, encoding="utf-8", newline="\n")
        print(f"wrote {args.fragment} ({len(frag.encode('utf-8')) / 1024:.0f} KB)")

    print(f"entries 52, questions {len(parts[0].children)}, rules {len(parts[1].children)}, "
          f"groups {len(parts[2].children)}, checklist {ck_n}, glossary {len(g_ids)}")
    print("talk categories:", counts["cat"], " priorities:", counts["pri"], " outside-fact:", counts["ext"])
    plain = [r for r in REPORT if r[1] == "plain"]
    print(f"paired layout: {52 - len(plain)} entries; plain layout: {len(plain)} -> "
          + ", ".join(f"{r[0]}({r[2]}/{r[3]})" for r in plain))
    leads = sorted({r[4] for r in REPORT if r[1] == "paired" and r[4]})
    print("leads in paired entries:", leads)


if __name__ == "__main__":
    main()
