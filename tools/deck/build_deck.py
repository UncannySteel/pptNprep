"""Build the ABOT talk deck for IEEE R10-HTC 2026 on the conference template.

Reads
    assets/template/HTC_2026_Presentation_Template.pptx   backgrounds, logo, mascot, masters
    talk/speech-v2.docx                                    the speech, copied into the speaker notes
    assets/figures/fig1_architecture_v2.png                paper Fig. 1
    assets/figures/fig4_pdr_vs_distance.png                paper Fig. 2
Writes
    ABOT-R10HTC-2026-talk.pptx

Every slide is drawn from native shapes so it stays editable in PowerPoint, and
every animation is written in the XML PowerPoint itself produces for that effect.
The speaker notes are the speech, cut per slide, with a [CLICK n] cue wherever
the slide animates. The script stops if a cue no longer matches the speech, or
if a slide's click count and its cues disagree, so re-run it after editing the
speech and fix whatever it names.

Numbers come from the camera-ready paper or a committed artifact (context.md
section 5). The exceptions are the WMO statistics on slide 3, which carry their
source on the slide. Wording follows ABOT-red-team-triage.md section 2.

Run from the pptNprep folder:

    python -E -P tools/deck/build_deck.py
"""
import html
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEMPLATE = ROOT / "assets" / "template" / "HTC_2026_Presentation_Template.pptx"
SPEECH = ROOT / "talk" / "speech-v2.docx"
FIG1 = ROOT / "assets" / "figures" / "fig1_architecture_v2.png"
FIG2 = ROOT / "assets" / "figures" / "fig4_pdr_vs_distance.png"
OUT = ROOT / "ABOT-R10HTC-2026-talk.pptx"

EMU = 914400

# Template palette (read from the template's own slides), plus series colours
# shared with ABOT-results-explained.html and the paper's figures.
NAVY, DEEP, CYAN, CYAN2 = "003E82", "08325F", "00A4C8", "00B7EA"
ORANGE, ORANGE_TXT, GOLD = "FF9100", "B85700", "F7B500"
GREY, MUTED, WHITE = "44546A", "66788A", "FFFFFF"
BORDER, PALE, PALE2, PALEB = "D3EAF6", "F2F8FC", "EAF7FF", "C7EAFE"
LINEC, GRIDC = "B9D3E6", "E3E8EB"
RED, GREEN = "D64545", "1E9E6A"
BLUE, PPO, CTX = "2A78D6", "EB6834", "9AA8B3"
SEV = [("intact", "1A9850"), ("moderate", "66BD63"), ("heavy", "E6B422"),
       ("severe", "F46D43"), ("extreme", "D73027")]
LAYER = {1: ("2A78D6", "DDEBFA"), 2: ("E8743B", "FCE5D8"),
         3: ("1FA37A", "D7F2E8"), 4: ("5B45B0", "E5E0F5")}
FONT = "Tahoma"

NS = ('xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
      'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
      'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"')
XML_HEAD = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
RT = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/"


def E(v):
    return int(round(v * EMU))


def esc(s):
    return html.escape(s, quote=False)


def q(s):
    return html.escape(s, quote=True)


# ---------------------------------------------------------------------------
# DrawingML fragments
# ---------------------------------------------------------------------------

def color_xml(c, alpha=None):
    a = f'<a:alpha val="{int(alpha * 1000)}"/>' if alpha is not None else ""
    return f'<a:srgbClr val="{c}">{a}</a:srgbClr>'


def fill_xml(c, alpha=None):
    return "<a:noFill/>" if c is None else f"<a:solidFill>{color_xml(c, alpha)}</a:solidFill>"


def ln_xml(c, w=1.0, alpha=None, dash=None, head=None, tail=None):
    if c is None:
        return "<a:ln><a:noFill/></a:ln>"
    d = f'<a:prstDash val="{dash}"/>' if dash else ""
    h = f'<a:headEnd type="{head}" w="med" len="med"/>' if head else ""
    t = f'<a:tailEnd type="{tail}" w="med" len="med"/>' if tail else ""
    return f'<a:ln w="{int(w * 12700)}">{fill_xml(c, alpha)}{d}{h}{t}</a:ln>'


def shadow_xml(kind):
    if not kind:
        return ""
    blur, dist, a = {"card": (76200, 19050, 13), "lift": (50800, 25400, 24)}[kind]
    return (f'<a:effectLst><a:outerShdw blurRad="{blur}" dist="{dist}" dir="5400000" algn="t" '
            f'rotWithShape="0"><a:srgbClr val="0A2E5C"><a:alpha val="{a * 1000}"/></a:srgbClr>'
            f'</a:outerShdw></a:effectLst>')


class Run:
    def __init__(self, t, **kw):
        self.t, self.kw = t, kw


class Para:
    def __init__(self, *runs, **kw):
        self.runs, self.kw = list(runs), kw


R, P = Run, Para


def rpr_xml(o):
    attrs = f'lang="en-US" sz="{int(round(o.get("size", 14) * 100))}"'
    if o.get("bold"):
        attrs += ' b="1"'
    if o.get("italic"):
        attrs += ' i="1"'
    if o.get("baseline"):
        attrs += f' baseline="{o["baseline"]}"'
    if o.get("spc"):
        attrs += f' spc="{o["spc"]}"'
    font = o.get("font", FONT)
    return (f'<a:rPr {attrs} dirty="0">{fill_xml(o.get("color", GREY), o.get("talpha"))}'
            f'<a:latin typeface="{font}"/><a:ea typeface="{font}"/><a:cs typeface="{font}"/></a:rPr>')


def para_xml(p, base):
    if isinstance(p, str):
        p = Para(Run(p))
    elif isinstance(p, Run):
        p = Para(p)
    elif isinstance(p, (list, tuple)):
        p = Para(*p)
    o = dict(base)
    o.update(p.kw)
    algn = {"l": "l", "c": "ctr", "r": "r"}[o.get("align", "l")]
    inner = ""
    if o.get("lnsp"):
        inner += f'<a:lnSpc><a:spcPct val="{int(o["lnsp"] * 100000)}"/></a:lnSpc>'
    if o.get("before"):
        inner += f'<a:spcBef><a:spcPts val="{int(o["before"] * 100)}"/></a:spcBef>'
    if o.get("after"):
        inner += f'<a:spcAft><a:spcPts val="{int(o["after"] * 100)}"/></a:spcAft>'
    if o.get("bullet"):
        ind = E(o.get("indent", 0.22))
        ppr = f'algn="{algn}" marL="{ind}" indent="-{ind}"'
        inner += (f'<a:buClr>{color_xml(o.get("bullet_color", ORANGE))}</a:buClr>'
                  f'<a:buSzPct val="100000"/><a:buFont typeface="Arial"/>'
                  f'<a:buChar char="{q(o["bullet"])}"/>')
    else:
        ppr = f'algn="{algn}" marL="0" indent="0"'
        inner += "<a:buNone/>"
    runs = ""
    for r in p.runs:
        if isinstance(r, str):
            r = Run(r)
        ro = dict(o)
        ro.update(r.kw)
        for i, part in enumerate(r.t.split("\n")):
            if i:
                runs += f"<a:br>{rpr_xml(ro)}</a:br>"
            if part:
                runs += f"<a:r>{rpr_xml(ro)}<a:t>{esc(part)}</a:t></a:r>"
    end = f'<a:endParaRPr lang="en-US" sz="{int(round(o.get("size", 14) * 100))}" dirty="0"/>'
    return f"<a:p><a:pPr {ppr}>{inner}</a:pPr>{runs}{end}</a:p>"


def txbody_xml(paras, base, anchor="t", ins=(0, 0, 0, 0), wrap=True):
    l, t, r, b = (E(v) for v in ins)
    body = (f'<a:bodyPr wrap="{"square" if wrap else "none"}" lIns="{l}" tIns="{t}" rIns="{r}" '
            f'bIns="{b}" rtlCol="0" anchor="{anchor}"><a:noAutofit/></a:bodyPr>')
    return f'<p:txBody>{body}<a:lstStyle/>{"".join(para_xml(p, base) for p in paras)}</p:txBody>'


# ---------------------------------------------------------------------------
# Animations: XML copied from what PowerPoint writes for each effect
# ---------------------------------------------------------------------------

class Fx:
    def __init__(self, kind, spid, dur=0.5, delay=0.0, **kw):
        self.kind, self.spid, self.dur, self.delay, self.kw = kind, spid, dur, delay, kw

    def span(self):
        reps = self.kw.get("repeat", 1) * (2 if self.kw.get("autorev") else 1)
        return self.delay + self.dur * reps


def fade(spid, dur=0.45, delay=0.0):
    return Fx("fade", spid, dur, delay)


def out(spid, dur=0.35, delay=0.0):
    return Fx("out", spid, dur, delay)


def wipe(spid, frm="left", dur=0.5, delay=0.0):
    return Fx("wipe", spid, dur, delay, frm=frm)


def zoom(spid, dur=0.4, delay=0.0):
    return Fx("zoom", spid, dur, delay)


def spin(spid, dur=1.2, delay=0.0, repeat=1):
    return Fx("spin", spid, dur, delay, repeat=repeat)


def pulse(spid, scale=1.18, dur=0.3, delay=0.0):
    return Fx("grow", spid, dur, delay, scale=scale, autorev=True)


WIPE = {"bottom": (4, "wipe(down)"), "left": (8, "wipe(left)")}


def effect_xml(fx, node, grp, nid):
    tgt = f'<p:tgtEl><p:spTgt spid="{fx.spid}"/></p:tgtEl>'
    d = int(fx.dur * 1000)
    head = nid()

    def vis(val, delay=0):
        return (f'<p:set><p:cBhvr><p:cTn id="{nid()}" dur="1" fill="hold"><p:stCondLst>'
                f'<p:cond delay="{delay}"/></p:stCondLst></p:cTn>{tgt}<p:attrNameLst>'
                f'<p:attrName>style.visibility</p:attrName></p:attrNameLst></p:cBhvr>'
                f'<p:to><p:strVal val="{val}"/></p:to></p:set>')

    extra = ""
    if fx.kind == "fade":
        pid, cls, sub = 10, "entr", 0
        body = vis("visible") + (f'<p:animEffect transition="in" filter="fade"><p:cBhvr>'
                                 f'<p:cTn id="{nid()}" dur="{d}"/>{tgt}</p:cBhvr></p:animEffect>')
    elif fx.kind == "out":
        pid, cls, sub = 10, "exit", 0
        body = (f'<p:animEffect transition="out" filter="fade"><p:cBhvr><p:cTn id="{nid()}" '
                f'dur="{d}"/>{tgt}</p:cBhvr></p:animEffect>') + vis("hidden", d - 1)
    elif fx.kind == "wipe":
        sub, filt = WIPE[fx.kw["frm"]]
        pid, cls = 22, "entr"
        body = vis("visible") + (f'<p:animEffect transition="in" filter="{filt}"><p:cBhvr>'
                                 f'<p:cTn id="{nid()}" dur="{d}"/>{tgt}</p:cBhvr></p:animEffect>')
    elif fx.kind == "zoom":
        pid, cls, sub = 23, "entr", 16
        body = vis("visible")
        for attr in ("ppt_w", "ppt_h"):
            body += (f'<p:anim calcmode="lin" valueType="num"><p:cBhvr><p:cTn id="{nid()}" '
                     f'dur="{d}" fill="hold"/>{tgt}<p:attrNameLst><p:attrName>{attr}</p:attrName>'
                     f'</p:attrNameLst></p:cBhvr><p:tavLst><p:tav tm="0"><p:val><p:fltVal val="0"/>'
                     f'</p:val></p:tav><p:tav tm="100000"><p:val><p:strVal val="#{attr}"/></p:val>'
                     f'</p:tav></p:tavLst></p:anim>')
    elif fx.kind == "spin":
        pid, cls, sub = 8, "emph", 0
        if fx.kw.get("repeat", 1) > 1:
            extra = f' repeatCount="{fx.kw["repeat"] * 1000}"'
        body = (f'<p:animRot by="21600000"><p:cBhvr><p:cTn id="{nid()}" dur="{d}" fill="hold"/>'
                f'{tgt}<p:attrNameLst><p:attrName>r</p:attrName></p:attrNameLst></p:cBhvr></p:animRot>')
    elif fx.kind == "grow":
        pid, cls, sub = 6, "emph", 0
        extra = ' autoRev="1"'
        sc = int(fx.kw["scale"] * 100000)
        body = (f'<p:animScale><p:cBhvr><p:cTn id="{nid()}" dur="{d}" fill="hold"/>{tgt}</p:cBhvr>'
                f'<p:by x="{sc}" y="{sc}"/></p:animScale>')
    else:
        raise ValueError(fx.kind)
    return (f'<p:par><p:cTn id="{head}" presetID="{pid}" presetClass="{cls}" presetSubtype="{sub}"'
            f'{extra} fill="hold" grpId="{grp}" nodeType="{node}"><p:stCondLst>'
            f'<p:cond delay="{int(fx.delay * 1000)}"/></p:stCondLst><p:childTnLst>{body}'
            f'</p:childTnLst></p:cTn></p:par>')


def timing_xml(groups, sp_ids):
    if not groups:
        return ""
    counter = [2]

    def nid():
        counter[0] += 1
        return counter[0]

    builds, bld = {}, []
    out_groups = []
    for g in groups:
        gid = nid()
        cond = '<p:cond delay="indefinite"/>'
        if g["auto"]:
            cond += '<p:cond evt="onBegin" delay="0"><p:tn val="2"/></p:cond>'
        t, steps = 0.0, []
        for si, step in enumerate(g["steps"]):
            sid = nid()
            effs, end = [], 0.0
            for ei, fx in enumerate(step):
                if ei:
                    node = "withEffect"
                elif si == 0:
                    node = "withEffect" if g["auto"] else "clickEffect"
                else:
                    node = "afterEffect"
                grp = builds.get(fx.spid, 0)
                builds[fx.spid] = grp + 1
                if fx.spid in sp_ids:
                    bld.append((fx.spid, grp))
                effs.append(effect_xml(fx, node, grp, nid))
                end = max(end, fx.span())
            steps.append(f'<p:par><p:cTn id="{sid}" fill="hold"><p:stCondLst><p:cond '
                         f'delay="{int(round(t * 1000))}"/></p:stCondLst><p:childTnLst>'
                         f'{"".join(effs)}</p:childTnLst></p:cTn></p:par>')
            t += end
        out_groups.append(f'<p:par><p:cTn id="{gid}" fill="hold"><p:stCondLst>{cond}'
                          f'</p:stCondLst><p:childTnLst>{"".join(steps)}</p:childTnLst></p:cTn></p:par>')
    bld_xml = "".join(f'<p:bldP spid="{s}" grpId="{g}" animBg="1"/>' for s, g in bld)
    return ('<p:timing><p:tnLst><p:par><p:cTn id="1" dur="indefinite" restart="never" '
            'nodeType="tmRoot"><p:childTnLst><p:seq concurrent="1" nextAc="seek"><p:cTn id="2" '
            f'dur="indefinite" nodeType="mainSeq"><p:childTnLst>{"".join(out_groups)}'
            '</p:childTnLst></p:cTn><p:prevCondLst><p:cond evt="onPrev" delay="0"><p:tgtEl>'
            '<p:sldTgt/></p:tgtEl></p:cond></p:prevCondLst><p:nextCondLst><p:cond evt="onNext" '
            'delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:nextCondLst></p:seq>'
            '</p:childTnLst></p:cTn></p:par></p:tnLst>'
            + (f"<p:bldLst>{bld_xml}</p:bldLst>" if bld_xml else "") + "</p:timing>")


# ---------------------------------------------------------------------------
# Slides
# ---------------------------------------------------------------------------

class Slide:
    def __init__(self, deck, key, dark=False):
        self.deck, self.key, self.dark = deck, key, dark
        self.root, self.stack, self.nid = [], [], 1
        self.sp_ids, self.groups, self.images = set(), [], {}
        self.notes = ""

    def _id(self):
        self.nid += 1
        return self.nid

    def _emit(self, xml, bbox):
        if self.stack:
            self.stack[-1]["items"].append(xml)
            self.stack[-1]["bbox"].append(bbox)
        else:
            self.root.append(xml)

    @contextmanager
    def group(self, name):
        g = {"id": self._id(), "items": [], "bbox": []}
        self.stack.append(g)
        yield g["id"]
        self.stack.pop()
        x = min(b[0] for b in g["bbox"])
        y = min(b[1] for b in g["bbox"])
        w = max(b[0] + b[2] for b in g["bbox"]) - x
        h = max(b[1] + b[3] for b in g["bbox"]) - y
        xfrm = (f'<a:xfrm><a:off x="{E(x)}" y="{E(y)}"/><a:ext cx="{E(w)}" cy="{E(h)}"/>'
                f'<a:chOff x="{E(x)}" y="{E(y)}"/><a:chExt cx="{E(w)}" cy="{E(h)}"/></a:xfrm>')
        self._emit(f'<p:grpSp><p:nvGrpSpPr><p:cNvPr id="{g["id"]}" name="{q(name)}"/>'
                   f'<p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr>{xfrm}</p:grpSpPr>'
                   f'{"".join(g["items"])}</p:grpSp>', (x, y, w, h))

    def shape(self, x, y, w, h, geom="rect", fill=None, alpha=None, line=None, lw=1.0,
              line_alpha=None, dash=None, shadow=None, adj=None, name=None, paras=None, rot=0,
              anchor="t", ins=(0, 0, 0, 0), wrap=True, descr=None, **text):
        sid = self._id()
        av = "".join(f'<a:gd name="{k}" fmla="val {v}"/>' for k, v in (adj or {}).items())
        rot_a = f' rot="{int(rot * 60000)}"' if rot else ""
        sppr = (f'<p:spPr><a:xfrm{rot_a}><a:off x="{E(x)}" y="{E(y)}"/><a:ext cx="{E(w)}" '
                f'cy="{E(h)}"/></a:xfrm><a:prstGeom prst="{geom}"><a:avLst>{av}</a:avLst>'
                f'</a:prstGeom>{fill_xml(fill, alpha)}{ln_xml(line, lw, line_alpha, dash)}'
                f'{shadow_xml(shadow)}</p:spPr>')
        tx = txbody_xml(paras, text, anchor, ins, wrap) if paras is not None else ""
        is_box = ' txBox="1"' if paras is not None and fill is None and line is None else ""
        d = f' descr="{q(descr)}"' if descr else ""
        self._emit(f'<p:sp><p:nvSpPr><p:cNvPr id="{sid}" name="{q(name or f"Shape {sid}")}"{d}/>'
                   f'<p:cNvSpPr{is_box}/><p:nvPr/></p:nvSpPr>{sppr}{tx}</p:sp>', (x, y, w, h))
        self.sp_ids.add(sid)
        return sid

    def text(self, x, y, w, h, paras, **kw):
        if not isinstance(paras, list):
            paras = [paras]
        return self.shape(x, y, w, h, paras=paras, **kw)

    def card(self, x, y, w, h, fill=WHITE, line=BORDER, shadow="card", radius=0.09, **kw):
        adj = {"adj": int(radius / min(w, h) * 100000)}
        return self.shape(x, y, w, h, "roundRect", fill=fill, line=line, shadow=shadow, adj=adj, **kw)

    def line(self, x1, y1, x2, y2, color, lw=1.0, alpha=None, dash=None, head=None, tail=None,
             name=None):
        sid = self._id()
        x, y, w, h = min(x1, x2), min(y1, y2), abs(x2 - x1), abs(y2 - y1)
        fl = (' flipH="1"' if x2 < x1 else "") + (' flipV="1"' if y2 < y1 else "")
        self._emit(f'<p:cxnSp><p:nvCxnSpPr><p:cNvPr id="{sid}" name="{q(name or f"Line {sid}")}"/>'
                   f'<p:cNvCxnSpPr/><p:nvPr/></p:nvCxnSpPr><p:spPr><a:xfrm{fl}><a:off x="{E(x)}" '
                   f'y="{E(y)}"/><a:ext cx="{E(w)}" cy="{E(h)}"/></a:xfrm><a:prstGeom prst="line">'
                   f'<a:avLst/></a:prstGeom>{ln_xml(color, lw, alpha, dash, head, tail)}</p:spPr>'
                   f'</p:cxnSp>', (x, y, w, h))
        return sid

    def pic(self, media, x, y, w, h, name=None, descr=""):
        sid = self._id()
        rid = self.images.setdefault(media, f"rId{len(self.images) + 2}")
        self.deck.media.add(media)
        self._emit(f'<p:pic><p:nvPicPr><p:cNvPr id="{sid}" name="{q(name or media)}" '
                   f'descr="{q(descr)}"/><p:cNvPicPr><a:picLocks noChangeAspect="1"/></p:cNvPicPr>'
                   f'<p:nvPr/></p:nvPicPr><p:blipFill><a:blip r:embed="{rid}"/><a:stretch>'
                   f'<a:fillRect/></a:stretch></p:blipFill><p:spPr><a:xfrm><a:off x="{E(x)}" '
                   f'y="{E(y)}"/><a:ext cx="{E(w)}" cy="{E(h)}"/></a:xfrm><a:prstGeom prst="rect">'
                   f'<a:avLst/></a:prstGeom></p:spPr></p:pic>', (x, y, w, h))
        return sid

    # animation groups: each positional argument is one step (a list runs "with
    # previous"); later steps run "after previous"
    def _add(self, auto, steps):
        steps = [list(s) if isinstance(s, (list, tuple)) else [s] for s in steps]
        steps = [s for s in steps if s]
        if steps:
            self.groups.append({"auto": auto, "steps": steps})

    def auto(self, *steps):
        assert not self.groups, "an automatic group must come first"
        self._add(True, steps)

    def click(self, *steps):
        self._add(False, steps)

    def clicks(self):
        return sum(1 for g in self.groups if not g["auto"])

    def xml(self):
        return (f'{XML_HEAD}<p:sld {NS}><p:cSld name="{q(self.key)}"><p:spTree><p:nvGrpSpPr>'
                '<p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm>'
                '<a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" '
                f'cy="0"/></a:xfrm></p:grpSpPr>{"".join(self.root)}</p:spTree></p:cSld>'
                '<p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr><p:transition spd="med"><p:fade/>'
                f'</p:transition>{timing_xml(self.groups, self.sp_ids)}</p:sld>')


class Deck:
    def __init__(self):
        self.slides, self.media = [], set()

    def slide(self, key, dark=False):
        s = Slide(self, key, dark)
        self.slides.append(s)
        s.pic("bg_dark.png" if dark else "bg_light.png", 0, 0, 13.333, 7.5, name="Background")
        return s


# ---------------------------------------------------------------------------
# Reusable pieces
# ---------------------------------------------------------------------------

FOOT = "IEEE R10 HTC 2026  |  Bangkok, Thailand  |  26 – 28 October 2026"


def header(s, title, subtitle):
    s.text(0.72, 0.42, 11.9, 0.62, title, size=25, color=NAVY, bold=True, anchor="ctr", name="Title")
    s.text(0.76, 1.05, 11.8, 0.36, subtitle, size=12.5, color=CYAN, bold=True, anchor="ctr",
           name="Subtitle")
    s.shape(0.72, 1.5, 1.35, 0.06, fill=ORANGE, name="Template accent")


def footer(s):
    n = len(s.deck.slides)
    if s.dark:
        s.line(0.55, 6.78, 12.75, 6.78, WHITE, 1, alpha=35, name="Footer rule")
    else:
        s.line(0.55, 6.78, 12.75, 6.78, NAVY, 1, alpha=25, name="Footer rule")
    s.pic("logo.png", 0.7927, 6.88, 0.8647, 0.45, name="HTC 2026 logo", descr="IEEE R10 HTC 2026 logo")
    s.text(2.02, 6.94, 8.8, 0.32, FOOT, size=7.8, bold=True, anchor="ctr", name="Footer",
           color=WHITE if s.dark else DEEP, talpha=93 if s.dark else None)
    s.text(12.1, 6.87, 0.7, 0.38, f"{n:02d}", size=9.5, bold=True, align="r", anchor="ctr",
           color=CYAN2 if s.dark else NAVY, name="Slide number")


def badge(s, x, y, d, label, fill=NAVY, size=14, color=WHITE, name=None):
    return s.shape(x, y, d, d, "ellipse", fill=fill, line=WHITE, lw=1.5, paras=[label], size=size,
                   bold=True, color=color, align="c", anchor="ctr", name=name or f"Badge {label}")


def dot(s, cx, cy, d, color, name=None, line=None, lw=1.0):
    return s.shape(cx - d / 2, cy - d / 2, d, d, "ellipse", fill=color, line=line, lw=lw, name=name)


def chip(s, x, y, w, label, color, bold=False, h=0.36, size=11.5, name=None):
    with s.group(name or f"Chip {label}") as gid:
        s.shape(x, y, w, h, "roundRect", fill=WHITE, line=BORDER, adj={"adj": 50000})
        dot(s, x + 0.2, y + h / 2, 0.15, color)
        s.text(x + 0.35, y, w - 0.4, h, label, size=size, bold=bold, color=DEEP, anchor="ctr")
    return gid


def pill_pair(s, x, y, w, h, runs, name, size=14.5):
    """A name pill plus its highlighted twin, drawn exactly on top of it."""
    base_runs = [R(t, **{**kw, "color": MUTED if kw.get("ref") else GREY}) for t, kw in runs]
    hi_runs = [R(t, **{**kw, "color": "BFD9F2" if kw.get("ref") else WHITE, "bold": True})
               for t, kw in runs]
    for r in base_runs + hi_runs:
        r.kw.pop("ref", None)
    s.shape(x, y, w, h, "roundRect", fill=PALE, line=BORDER, adj={"adj": 50000},
            paras=[P(*base_runs)], size=size, align="c", anchor="ctr", name=f"{name} (base)")
    return s.shape(x, y, w, h, "roundRect", fill=NAVY, line=GOLD, lw=1.5, shadow="lift",
                   adj={"adj": 50000}, paras=[P(*hi_runs)], size=size, align="c", anchor="ctr",
                   name=f"{name} (highlight)")


def states(s, seq, first_auto=False, delay=0.0):
    """Click through highlight states: each state is the set of overlays shown."""
    prev = set()
    for i, st in enumerate(seq):
        st = set(st)
        fx = [out(x) for x in sorted(prev - st)] + [fade(x, delay=delay if i == 0 else 0)
                                                   for x in sorted(st - prev)]
        (s.auto if first_auto and i == 0 else s.click)(fx)
        prev = st


def icon_mesh(s, cx, cy, r, color):
    import math
    pts = [(cx + r * math.cos(math.radians(-90 + 72 * k)), cy + r * math.sin(math.radians(-90 + 72 * k)))
           for k in range(5)]
    for k, (px, py) in enumerate(pts):
        s.line(cx, cy, px, py, color, 1.25)
        nx, ny = pts[(k + 1) % 5]
        s.line(px, py, nx, ny, color, 1.25)
    for px, py in pts + [(cx, cy)]:
        dot(s, px, py, 0.13, ORANGE if (px, py) == (cx, cy) else color)


def icon_signal(s, cx, cy, color):
    for k, hgt in enumerate((0.16, 0.27, 0.38, 0.5)):
        s.shape(cx - 0.29 + k * 0.155, cy + 0.25 - hgt, 0.11, hgt, fill=ORANGE if k == 3 else color)


def icon_grid(s, cx, cy, color):
    for i in range(3):
        for j in range(3):
            s.shape(cx - 0.25 + i * 0.18, cy - 0.25 + j * 0.18, 0.14, 0.14, fill=ORANGE if (i, j) == (2, 0) else color)


# ---------------------------------------------------------------------------
# The deck
# ---------------------------------------------------------------------------

def build():
    d = Deck()

    # 1 -- title ------------------------------------------------------------
    s = d.slide("Title", dark=True)
    s.shape(0.58, 0.5, 12.2, 6.38, "roundRect", fill="000000", alpha=22, line=WHITE, line_alpha=18,
            adj={"adj": 4000}, name="Glass panel")
    s.pic("mascot.png", 6.25, 1.013, 6.55, 4.324, name="HTC 2026 artwork",
          descr="IEEE R10 HTC 2026 Bangkok conference artwork")
    s.text(0.78, 0.92, 5.6, 0.9, "ABOT", size=48, bold=True, color=WHITE, anchor="ctr", name="Title")
    s.text(0.82, 1.86, 5.35, 1.0, "A Decentralized LoRa Mesh Communication Framework for "
           "Post-Disaster Environments", size=16, bold=True, color=CYAN2, lnsp=1.05, name="Paper title")
    s.text(0.82, 3.05, 5.4, 0.4, "Aniraj Singh  ·  Azzah Mallick", size=15, bold=True, color=WHITE,
           name="Authors")
    s.text(0.82, 3.45, 5.4, 0.35, "Department of CSE, Amity University, Uttar Pradesh, India",
           size=11.5, color=WHITE, talpha=85, name="Affiliation")
    s.text(0.82, 4.02, 4.2, 0.32, "IEEE R10 HTC 2026", size=12, bold=True, color=GOLD, name="Conference")
    s.shape(0.82, 4.45, 5.65, 0.45, "roundRect", fill=NAVY, line=GOLD, lw=1.2, shadow="lift",
            adj={"adj": 18000}, paras=["26 – 28 October 2026  |  Bangkok, Thailand"], size=10.5,
            bold=True, color=WHITE, align="c", anchor="ctr", name="Date pill")
    s.shape(0.87, 6.09, 0.2, 0.2, "diamond", fill=GOLD, name="Diamond")
    s.text(1.2, 6.03, 6.0, 0.32, "Empowering Humanity Through Emerging Technology & Innovation",
           size=9, color=WHITE, talpha=85, anchor="ctr", name="Conference theme")
    s.notes = ("[Introduce yourself and your co-author, Azzah Mallick, Amity University.]\n\n"
               "Title: ABOT, a decentralized LoRa mesh communication framework for post-disaster "
               "environments.")

    # 2 -- outline ----------------------------------------------------------
    s = d.slide("Outline")
    header(s, "Outline", "From the problem to what we found")
    rows = [("Why it matters", "Motivation and existing work"),
            ("The problem", "Research gaps, our question, and ABOT's objectives"),
            ("How we built it", "Methodology and the four-layer design"),
            ("What we found", "Six results from simulation"),
            ("What's next", "Limitations and future work")]
    ids = []
    for i, (h, sub) in enumerate(rows):
        y = 1.85 + i * 0.86
        with s.group(f"Outline row {i + 1}") as gid:
            s.card(1.06, y, 11.15, 0.7, radius=0.06)
            s.shape(1.28, y + 0.12, 0.72, 0.46, "roundRect", fill=NAVY if i % 2 == 0 else ORANGE,
                    adj={"adj": 16000}, paras=[f"{i + 1:02d}"], size=13, bold=True, color=WHITE,
                    align="c", anchor="ctr")
            s.text(2.25, y + 0.08, 4.0, 0.32, h, size=15, bold=True, color=NAVY, anchor="ctr")
            s.text(2.25, y + 0.38, 9.5, 0.26, sub, size=11.5, color=GREY, anchor="ctr")
        ids.append(gid)
    s.auto([fade(g, delay=0.12 * i) for i, g in enumerate(ids)])
    s.notes = ("[Optional, one line] I'll cover why this matters, the problem we set out to answer, "
               "how we built ABOT, what we found, and what comes next.")
    footer(s)

    # 3 -- motivation: the numbers ------------------------------------------
    s = d.slide("Motivation")
    header(s, "Disasters are rising, and so are the losses", "Introduction and motivation")
    chips = [chip(s, 0.83, 1.85, 3.0, "Bangkok · severe flooding", BLUE, h=0.4, size=12),
             chip(s, 4.0, 1.85, 3.5, "Kashmir · forest fires in winter", PPO, h=0.4, size=12)]
    stats = [("5×", NAVY, "more reported weather- and climate-related disasters", "1970 → 2019"),
             ("≈3×", CYAN, "fewer deaths, thanks to better forecasts and early warnings", "1970s → 2010s"),
             ("7×", ORANGE, "higher reported economic losses", "1970s → 2010s")]
    cards = []
    for i, (big, col, lab, sub) in enumerate(stats):
        x = 0.83 + i * 4.0
        with s.group(f"Stat {big}") as gid:
            s.card(x, 2.5, 3.67, 2.95)
            s.text(x + 0.35, 2.68, 3.0, 1.05, big, size=54, bold=True, color=col, anchor="ctr")
            s.text(x + 0.35, 3.8, 3.0, 0.95, lab, size=14.5, bold=True, color=DEEP)
            s.text(x + 0.35, 4.85, 3.0, 0.35, sub, size=11.5, color=MUTED)
        cards.append(gid)
    take = s.card(0.83, 5.62, 11.67, 0.6, fill=PALE2, line=PALEB, shadow=None, radius=0.08,
                  paras=["The hazard is only part of the problem: what matters just as much is how "
                         "well our systems withstand it."], size=14, bold=True, color=NAVY,
                  anchor="ctr", ins=(0.25, 0, 0.2, 0), name="Takeaway")
    s.text(0.83, 6.3, 11.67, 0.3, "Source: WMO, Atlas of Mortality and Economic Losses from Weather, "
           "Climate and Water Extremes (1970–2019), 2021", size=9, color=MUTED, anchor="ctr",
           name="Source")
    s.auto([fade(chips[0]), fade(chips[1], delay=0.15)])
    for g in cards:
        s.click(fade(g))
    s.click(fade(take))
    footer(s)

    # 4 -- what if it strikes anyway ----------------------------------------
    s = d.slide("When disaster strikes", dark=True)
    s.text(0.85, 1.2, 6.5, 1.65, "What happens when the disaster strikes anyway?", size=34, bold=True,
           color=WHITE, lnsp=0.95, anchor="ctr", name="Question")
    # tower, kept clear of the template's skyline (bottom right) and constellation (top right)
    ax, top, base, hw = 8.15, 1.55, 4.5, 0.74
    s.shape(ax - hw, top, 2 * hw, base - top, "triangle", line=WHITE, lw=2.25, name="Tower")
    for (ya, yb) in ((2.6, 3.5),):
        wa, wb = hw * (ya - top) / (base - top), hw * (yb - top) / (base - top)
        s.line(ax - wa, ya, ax + wa, ya, WHITE, 1.5)
        s.line(ax - wb, yb, ax + wb, yb, WHITE, 1.5)
        s.line(ax - wa, ya, ax + wb, yb, WHITE, 1.25)
        s.line(ax + wa, ya, ax - wb, yb, WHITE, 1.25)
    dot(s, ax, top - 0.1, 0.18, WHITE)
    for r in (0.45, 0.75):
        s.shape(ax - r, top - 0.1 - r, 2 * r, 2 * r, "arc", line=CYAN2, lw=2, line_alpha=80,
                adj={"adj1": 18900000, "adj2": 2700000}, name="Signal right")
        s.shape(ax - r, top - 0.1 - r, 2 * r, 2 * r, "arc", line=CYAN2, lw=2, line_alpha=80,
                adj={"adj1": 8100000, "adj2": 13500000}, name="Signal left")
    xmark = s.shape(ax - 0.62, 2.2, 1.24, 1.24, "mathMultiply", fill=RED, line=WHITE, lw=2,
                    name="Tower down")
    rows = ["Towers damaged: cellular and internet go down",
            "Survivors can't call for help",
            "Rescue teams struggle to coordinate"]
    rids = []
    for i, t in enumerate(rows):
        y = 3.2 + i * 0.66
        with s.group(f"Consequence {i + 1}") as gid:
            dot(s, 1.0, y + 0.25, 0.18, CYAN2)
            s.text(1.3, y, 5.9, 0.5, t, size=18, color=WHITE, anchor="ctr")
        rids.append(gid)
    stmt = s.shape(0.85, 5.45, 8.0, 0.62, "roundRect", fill=NAVY, line=GOLD, lw=1.25, shadow="lift",
                   adj={"adj": 18000}, paras=["Keeping communication possible after infrastructure fails"],
                   size=16, bold=True, color=WHITE, anchor="ctr", ins=(0.3, 0, 0.2, 0), name="Problem")
    s.auto(zoom(xmark, delay=0.6))
    s.click([fade(g, delay=0.25 * i) for i, g in enumerate(rids)])
    s.click(fade(stmt))
    footer(s)

    # 5 -- existing work: names only, highlighted as they are spoken ----------
    s = d.slide("Existing work")
    header(s, "Existing work", "Post-disaster communication: what is already out there")
    lora = pill_pair(s, 5.17, 1.82, 3.0, 0.56, [("LoRa", {}), (" (Long Range radio)", {"size": 13})], "LoRa", size=16)
    s.line(6.67, 2.38, 6.67, 2.66, LINEC, 1.5)
    s.line(2.68, 2.66, 10.68, 2.66, LINEC, 1.5)
    cols = [("LPWAN disaster systems", [[("Titan", {}), (" [4]", {"ref": True, "size": 11})]]),
            ("Consumer-grade LoRa platforms", [[("Meshtastic", {}), (" [12]", {"ref": True, "size": 11})],
                                               [("Disaster Radio", {})],
                                               [("Project OWL · DuckLink", {}), (" [13]", {"ref": True, "size": 11})]]),
            ("Routing research", [[("AI-optimised routing", {}), (" [7]", {"ref": True, "size": 11})],
                                  [("Power-aware routing", {}), (" [8]", {"ref": True, "size": 11})]])]
    heads, pills = [], []
    for i, (h, names) in enumerate(cols):
        x = 0.83 + i * 4.0
        s.line(x + 1.85, 2.66, x + 1.85, 2.96, LINEC, 1.5)
        s.card(x, 2.96, 3.7, 3.35, name=f"Column {i + 1}")
        s.text(x + 0.25, 3.12, 3.2, 0.62, h, size=14.5, bold=True, color=NAVY, anchor="ctr",
               name=f"{h} (base)")
        heads.append(s.shape(x + 0.25, 3.12, 3.2, 0.62, fill=WHITE, paras=[h], size=14.5, bold=True,
                             color=ORANGE_TXT, anchor="ctr", name=f"{h} (highlight)"))
        row = []
        for j, runs in enumerate(names):
            row.append(pill_pair(s, x + 0.25, 3.92 + j * 0.68, 3.2, 0.52, runs, runs[0][0]))
        pills.append(row)
    titan, (mesh, drad, owl), (ai, power) = pills[0][0], pills[1], pills[2]
    states(s, [{lora}, {heads[0], titan}, {heads[1], mesh, drad, owl}, {heads[1], owl},
               {heads[2], ai}, {heads[2], power}], first_auto=True, delay=0.5)
    footer(s)

    # 6 -- why ABOT: the gaps ------------------------------------------------
    s = d.slide("Gaps")
    header(s, "So why ABOT? Three recurring gaps", "Existing work laid the foundation; the gaps show up when conditions change")
    gaps = [("Routing decisions", "Link-quality routing exists, but uses static information or re-routes only after a failure"),
            ("Simulation", "LoRa simulators target protocol analysis, not fast, RL-ready training"),
            ("Evaluation", "Adaptive routing is rarely benchmarked across worsening damage levels")]
    gids = []
    for i, (h, body) in enumerate(gaps):
        x = 0.83 + i * 4.0
        with s.group(f"Gap {i + 1}") as gid:
            s.card(x, 1.85, 3.7, 2.5)
            badge(s, x + 0.25, 2.07, 0.58, str(i + 1), fill=ORANGE if i == 1 else NAVY, size=16)
            s.text(x + 1.0, 2.07, 2.5, 0.58, h, size=18, bold=True, color=NAVY, anchor="ctr")
            s.text(x + 0.25, 2.88, 3.2, 1.35, body, size=14, color=GREY, lnsp=1.05)
        gids.append(gid)
    with s.group("Related protocols") as strip:
        s.card(0.83, 4.6, 7.25, 1.8)
        s.text(1.08, 4.75, 6.8, 0.4, "Decentralised mesh protocols that route by link quality", size=14,
               bold=True, color=NAVY, anchor="ctr")
        for name, x, w in (("B.A.T.M.A.N.", 1.08, 1.95), ("Babel", 3.18, 1.35), ("OLSR", 4.68, 1.35)):
            s.shape(x, 5.27, w, 0.52, "roundRect", fill=NAVY, line=GOLD, lw=1.5, shadow="lift",
                    adj={"adj": 50000}, paras=[name], size=14.5, bold=True, color=WHITE, align="c",
                    anchor="ctr", name=name)
        s.text(1.08, 5.92, 6.8, 0.36, "Compared on hardware: packet loss, delay, CPU and memory under "
               "load (Diniz et al., ICUAS 2025)", size=10.5, color=MUTED, anchor="ctr")
    with s.group("ABOT adds") as adds:
        s.shape(8.2, 5.25, 0.5, 0.5, "rightArrow", fill=ORANGE, name="Arrow")
        s.card(8.83, 4.6, 3.67, 1.8, fill=NAVY, line=NAVY)
        s.text(9.08, 4.72, 3.2, 0.36, "ABOT adds", size=13, bold=True, color=GOLD, anchor="ctr")
        s.text(9.08, 5.1, 3.25, 1.2, ["LoRa radio limits", "Five damage levels", "An RL training interface"],
               size=14.5, bold=True, color=WHITE, bullet="•", bullet_color=CYAN2, indent=0.22, after=2)
    for g in gids:
        s.click(fade(g))
    s.click(fade(strip))
    s.click(fade(adds))
    footer(s)

    # 7 -- problem statement --------------------------------------------------
    s = d.slide("Problem statement")
    header(s, "Problem statement", "What we set out to answer")
    probs = [("Central gateway dependency", "single point of failure"),
             ("Static routing decisions", "limited adaptation to changing link quality"),
             ("Reactive route recalculation", "routes change only after a failure"),
             ("Limited simulation scalability", "hard to evaluate learning-based routing at scale"),
             ("Limited damage-level evaluation", "adaptive routing not tested across rising damage")]
    pids = []
    for i, (h, sub) in enumerate(probs):
        y = 1.85 + i * 0.9
        with s.group(f"Challenge {i + 1}") as gid:
            s.card(0.83, y, 5.6, 0.78, radius=0.07)
            badge(s, 1.0, y + 0.14, 0.5, str(i + 1), size=13)
            s.text(1.7, y + 0.07, 4.6, 0.36, h, size=14.5, bold=True, color=DEEP, anchor="ctr")
            s.text(1.7, y + 0.41, 4.6, 0.3, sub, size=12, color=GREY, anchor="ctr")
        pids.append(gid)
    with s.group("Research question") as rq:
        s.card(6.75, 1.85, 5.75, 4.38, fill=NAVY, line=NAVY)
        s.text(7.1, 2.12, 5.1, 0.36, "RESEARCH QUESTION", size=12, bold=True, color=GOLD, spc=150,
               anchor="ctr")
        s.text(7.1, 2.65, 5.1, 2.6, "How can routing in a gateway-free LoRa mesh use continuously "
               "updated link-state information, and how do classical and RL-based routing compare "
               "as network damage increases?", size=19, bold=True, color=WHITE, lnsp=1.08)
        s.text(7.1, 5.55, 5.1, 0.42, "A comparison, studied entirely in simulation", size=12.5,
               bold=True, color=CYAN2, anchor="ctr")
    s.auto([fade(g, delay=0.12 * i) for i, g in enumerate(pids)])
    s.click(fade(rq))
    footer(s)

    # 8 -- objectives ---------------------------------------------------------
    s = d.slide("Objectives")
    header(s, "ABOT: three objectives", "A decentralized LoRa mesh framework for post-disaster environments")
    objs = [("Decentralized mesh", "Every node is both a terminal and a relay; no central gateway", icon_mesh),
            ("Live link-state routing", "Routes use continuously updated link quality", icon_signal),
            ("Fast simulation backend", "A vectorized simulator to compare routing across five "
             "damage-severity presets", icon_grid)]
    oids = []
    for i, (h, body, icon) in enumerate(objs):
        x = 0.83 + i * 4.0
        with s.group(f"Objective {i + 1}") as gid:
            s.card(x, 1.95, 3.7, 3.45)
            s.shape(x + 0.3, 2.22, 1.05, 1.05, "ellipse", fill=PALE2, line=PALEB, lw=1.25)
            cx, cy = x + 0.825, 2.745
            if icon is icon_mesh:
                icon_mesh(s, cx, cy, 0.3, NAVY)
            else:
                icon(s, cx, cy, NAVY)
            s.text(x + 0.3, 3.5, 3.15, 0.5, h, size=17, bold=True, color=NAVY, anchor="ctr")
            s.text(x + 0.3, 4.05, 3.15, 1.2, body, size=14, color=GREY, lnsp=1.05)
        oids.append(gid)
    tag = s.card(0.83, 5.72, 11.67, 0.58, fill=PALE2, line=PALEB, shadow=None, radius=0.08,
                 paras=["Investigated entirely in simulation  ·  The RL part is exploratory"], size=14,
                 bold=True, color=NAVY, align="c", anchor="ctr", name="Scope")
    s.auto([fade(g, delay=0.2 * i) for i, g in enumerate(oids)], fade(tag))
    footer(s)

    # 9 -- how it works --------------------------------------------------------
    s = d.slide("How ABOT works")
    header(s, "How ABOT works", "Every node is both a terminal and a relay")
    s.card(0.83, 1.85, 7.3, 4.6, name="Diagram card")
    N = {"S": (1.55, 5.55), "A": (2.55, 4.75), "B": (1.75, 3.55), "C": (3.55, 5.7), "D": (3.75, 3.95),
         "E": (2.95, 2.7), "F": (4.95, 5.05), "G": (5.05, 3.05), "H": (6.15, 4.25), "I": (4.3, 2.35),
         "J": (6.75, 5.55), "R": (7.35, 2.75)}
    edges = ["SA", "SC", "AB", "AD", "AC", "BE", "BD", "CF", "DE", "DG", "DF", "EI", "IG", "FH", "FJ",
             "GH", "GR", "HR", "HJ"]
    for a, b in edges:
        s.line(*N[a], *N[b], "C5D9E8", 2, name=f"Link {a}{b}")
    rings = []
    for k in "ADEFGH":
        cx, cy = N[k]
        rings.append(s.shape(cx - 0.45, cy - 0.45, 0.9, 0.9, "ellipse", line=CYAN2, lw=1.75,
                             name=f"Beacon {k}"))

    def seg(a, b, color, name, dash=None):
        return s.line(*N[a], *N[b], color, 4.5, dash=dash, name=name)

    path = [seg("S", "A", PPO, "SOS hop 1"), seg("A", "D", PPO, "SOS hop 2"),
            seg("D", "G", PPO, "SOS hop 3"), seg("G", "R", PPO, "SOS hop 4")]
    alt = [seg("A", "C", CYAN, "Re-route 1"), seg("C", "F", CYAN, "Re-route 2"),
           seg("F", "H", CYAN, "Re-route 3"), seg("H", "R", CYAN, "Re-route 4")]
    for k, (cx, cy) in N.items():
        if k == "S":
            dot(s, cx, cy, 0.38, PPO, name="Survivor", line=WHITE, lw=2)
        elif k == "R":
            rescue = s.shape(cx - 0.24, cy - 0.24, 0.48, 0.48, "ellipse", fill=GREEN, line=WHITE, lw=2,
                             paras=["+"], size=18, bold=True, color=WHITE, align="c", anchor="ctr",
                             name="Rescue node")
        else:
            dot(s, cx, cy, 0.32, WHITE, name=f"Node {k}", line=NAVY, lw=2)
    s.text(0.95, 5.85, 1.6, 0.3, "Survivor", size=11, bold=True, color=ORANGE_TXT, align="c")
    s.text(6.75, 2.1, 1.25, 0.3, "Rescue node", size=11, bold=True, color=GREEN, align="c")
    sos = s.shape(0.98, 4.95, 0.62, 0.3, "roundRect", fill=PPO, adj={"adj": 30000}, paras=["SOS"],
                  size=10.5, bold=True, color=WHITE, align="c", anchor="ctr", name="SOS tag")
    dcx, dcy = N["D"]
    with s.group("Node D fails") as fail:
        dot(s, dcx, dcy, 0.42, RED, line=WHITE, lw=2)
        s.shape(dcx - 0.15, dcy - 0.15, 0.3, 0.3, "mathMultiply", fill=WHITE)
    steps = [("Beacons", "Nodes announce themselves to find neighbours and measure link quality"),
             ("SOS + GPS", "Hops node to node until it reaches an active rescue node"),
             ("Live link state", "PDR · RSSI · reachability: routes are re-assessed as nodes fail or links degrade")]
    sids = []
    for i, (h, body) in enumerate(steps):
        y = 1.95 + i * 1.5
        with s.group(f"Step {i + 1}") as gid:
            badge(s, 8.45, y, 0.5, str(i + 1), fill=[CYAN, PPO, NAVY][i], size=13)
            s.text(9.1, y - 0.02, 3.4, 0.5, h, size=16, bold=True, color=NAVY, anchor="ctr")
            s.text(9.1, y + 0.5, 3.4, 0.9, body, size=13, color=GREY, lnsp=1.05)
        sids.append(gid)
    # beacons pulse twice, the SOS walks hop by hop, then node D fails and the route moves
    s.click([fade(sids[0])] + [zoom(r, 0.35) for r in rings], [out(r, 0.6) for r in rings],
            [zoom(r, 0.35) for r in rings], [out(r, 0.6) for r in rings])
    s.click([fade(sids[1]), zoom(sos)], *[[wipe(p, dur=0.35)] for p in path], [pulse(rescue)])
    s.click([fade(sids[2]), zoom(fail)], [out(path[1]), out(path[2]), out(path[3])],
            *[[wipe(p, dur=0.35)] for p in alt], [pulse(rescue)])
    footer(s)

    # 10 -- methodology: the testbed ---------------------------------------------
    s = d.slide("Testbed")
    header(s, "Methodology: a simulated disaster testbed", "A virtual LoRa mesh with no central tower")
    s.card(0.83, 1.85, 5.3, 4.6, name="Grid card")
    gx, gy, sp = 1.86, 2.5, 0.36
    rc_x, rc_y, rr = gx + 4 * sp, gy + 5 * sp, 3.75 * sp
    s.shape(rc_x - rr, rc_y - rr, 2 * rr, 2 * rr, "ellipse", fill=CYAN, alpha=8, line=CYAN, lw=1.5,
            dash="dash", name="Radio range")
    for i in range(10):
        for j in range(10):
            if j == 0 and i in (0, 9):
                continue
            dot(s, gx + i * sp, gy + j * sp, 0.1, "7FA3C4", name=f"N{j}{i}")
    dot(s, rc_x, rc_y, 0.16, PPO, name="Example node")
    for i in (0, 9):
        dot(s, gx + i * sp, gy, 0.28, GREEN, name="Safe zone", line=WHITE, lw=1.5)
        s.text(gx + i * sp - 0.7, gy - 0.48, 1.4, 0.28, "Safe zone", size=10.5, bold=True, color=GREEN,
               align="c", anchor="ctr")
    s.text(1.0, 5.83, 4.95, 0.3, "10 × 10 grid · 100 nodes · 400 m apart", size=12.5, bold=True,
           color=DEEP, align="c", anchor="ctr")
    s.text(1.0, 6.1, 4.95, 0.27, "Dashed circle: the 1.5 km radio range of one node", size=10.5,
           color=MUTED, align="c", anchor="ctr")
    facts1 = ["Scale-up runs: 15 × 15 and up to 30 × 30 (900 nodes)",
              "Two safe zones at the corners: the goal for every message"]
    for i, t in enumerate(facts1):
        s.text(6.55, 1.95 + i * 0.62, 5.95, 0.55, t, size=15, color=DEEP, bullet="•", indent=0.3,
               anchor="ctr", name=f"Fact {i + 1}")
    with s.group("Damage presets") as f3:
        s.text(6.55, 3.25, 5.95, 0.4, [P(R("Five damage-severity presets "), R("(default: heavy)", color=MUTED, size=13))],
               size=15, color=DEEP, bullet="•", indent=0.3, anchor="ctr")
        x = 6.85
        for name, col in SEV:
            w = 0.36 + 0.105 * len(name)
            chip(s, x, 3.75, w, name, col, bold=(name == "heavy"), size=11)
            x += w + 0.1
    f4 = s.text(6.55, 4.4, 5.95, 0.6, "Radio collisions: a sufficiently stronger signal wins (6 dB capture)",
                size=15, color=DEEP, bullet="•", indent=0.3, anchor="ctr", name="Fact collisions")
    f5 = s.text(6.55, 5.15, 5.95, 0.6, "Node failures: sudden, or gradual as batteries drain",
                size=15, color=DEEP, bullet="•", indent=0.3, anchor="ctr", name="Fact failures")
    s.click(fade(f3))
    s.click(fade(f4))
    s.click(fade(f5))
    footer(s)

    # 11 -- methodology: pipeline ----------------------------------------------
    s = d.slide("Pipeline")
    header(s, "Methodology: from protocol to benchmark", "How every experiment is put together")
    pipe = [("Protocol", ["Beacon every 30 s", "Link score: PDR over the last 50 packets",
                          "Gossip3: forward 75%, stay quiet after 3 copies"]),
            ("Routing task", ["Random start → a safe zone", "1 hop = 10 s of simulated time",
                              "Seeded, reproducible trials"]),
            ("Simulators", ["SimPy reference: one event at a time",
                                "Time-stepped: all radios together, built for AI training"]),
            ("PPO router", ["Picks the next neighbour", "3 training runs × 200,000 steps",
                            "Default settings"]),
            ("Benchmark", ["Classical planners: Dijkstra and A*", "Static and dynamic versions",
                           "Same setup, five damage levels"])]
    pgs = []
    for i, (h, items) in enumerate(pipe):
        x = 0.83 + i * 2.335
        with s.group(f"Pipeline step {i + 1}") as gid:
            s.shape(x, 1.9, 2.4, 0.72, "homePlate" if i == 0 else "chevron",
                    fill=ORANGE if i % 2 else NAVY, adj={"adj": 32000}, shadow="lift",
                    paras=[P(R(f"{i + 1}  ", color=GOLD if i % 2 == 0 else NAVY), R(h))], size=13,
                    bold=True, color=WHITE, align="c", anchor="ctr", ins=(0.3 if i else 0.08, 0, 0.1, 0))
            s.card(x + 0.04, 2.9, 2.18, 2.6, radius=0.07)
            s.text(x + 0.2, 3.1, 1.88, 2.3, items, size=13, color=GREY, bullet="•", indent=0.17,
                   after=9, lnsp=1.0)
        pgs.append(gid)
    same = s.card(0.83, 5.75, 11.67, 0.55, fill=PALE2, line=PALEB, shadow=None, radius=0.08,
                  paras=["Every routing approach runs in the same framework, across the same damage levels"],
                  size=14, bold=True, color=NAVY, align="c", anchor="ctr", name="Same framework")
    s.auto(fade(pgs[0]))
    for g in pgs[1:-1]:
        s.click(fade(g))
    s.click([fade(pgs[-1])], [fade(same)])
    footer(s)

    # 12 -- architecture: paper Fig. 1 ------------------------------------------------
    s = d.slide("Architecture")
    header(s, "System design: four layers", "Paper Fig. 1  ·  The architecture of every ABOT node, inside a simulation harness")
    s.card(0.83, 1.85, 8.3, 4.6, name="Figure card")
    iw = 8.0
    ih = iw * 1634 / 3120
    ix, iy = 0.98, 1.85 + (4.6 - ih) / 2
    s.pic("fig1.png", ix, iy, iw, ih, name="Paper Fig. 1",
          descr="ABOT's four layers, from bottom to top: physical LoRa radio, MAC and forwarding, "
                "link-state monitoring, routing and evacuation, inside a dashed simulation-harness box")

    def region(fx0, fy0, fx1, fy1, name):
        """An orange frame over part of the figure, given as fractions of its width and height."""
        return s.shape(ix + fx0 * iw, iy + fy0 * ih, (fx1 - fx0) * iw, (fy1 - fy0) * ih, "roundRect",
                       line=ORANGE, lw=2.75, adj={"adj": 8000}, name=name)

    down = region(0.022, 0.245, 0.172, 0.805, "Frame: decisions down")
    up = region(0.752, 0.255, 0.968, 0.805, "Frame: measurements up")
    harness = region(0.012, 0.028, 0.988, 0.978, "Frame: harness")
    tips = [("↓  Decisions go down", "Layer 4 picks the next hop; Layer 2 sends it as a LoRa transmission"),
            ("↑  Measurements go up", "Received frames → de-duplicated beacons → PDR, RSSI and reachability "
                                        "for routing"),
            ("Dashed box: the harness", "Used only to train and evaluate; not part of a deployed node")]
    tids = [s.card(9.42, 1.85 + i * 1.57, 3.08, 1.42, name=f"Tip {i + 1}",
                   paras=[P(R(h), size=14, bold=True, color=NAVY, after=4), P(R(b), size=12, color=GREY)],
                   ins=(0.2, 0.08, 0.15, 0.08), anchor="ctr", lnsp=1.02) for i, (h, b) in enumerate(tips)]
    s.click([fade(down), fade(tids[0])])
    s.click([out(down), fade(up), fade(tids[1])])
    s.click([out(up), fade(harness), fade(tids[2])])
    footer(s)

    # 13 -- four layers, one at a time ---------------------------------------------------
    s = d.slide("Four layers")
    header(s, "System design: layer by layer", "Each layer handles one part of communication")
    lays = [(4, "Routing & evacuation"), (3, "Link-state monitoring"), (2, "MAC & forwarding"),
            (1, "Physical (LoRa)")]
    hi = {}
    for i, (n, name) in enumerate(lays):
        y = 1.85 + i * 0.98
        col, tint = LAYER[n]
        s.shape(0.83, y, 5.2, 0.83, "roundRect", fill=tint, line=col, lw=1.5, adj={"adj": 10000},
                name=f"Layer {n} (base)")
        s.shape(1.0, y + 0.165, 0.55, 0.5, "roundRect", fill=col, adj={"adj": 18000}, paras=[f"L{n}"],
                size=13, bold=True, color=WHITE, align="c", anchor="ctr")
        s.text(1.75, y, 4.1, 0.83, name, size=16, bold=True, color=DEEP, anchor="ctr")
        with s.group(f"Layer {n} (highlight)") as gid:
            s.shape(0.83, y, 5.62, 0.83, "homePlate", fill=col, line=col, lw=1.5, shadow="lift",
                    adj={"adj": 42000})
            s.shape(1.0, y + 0.165, 0.55, 0.5, "roundRect", fill=WHITE, adj={"adj": 18000},
                    paras=[f"L{n}"], size=13, bold=True, color=col, align="c", anchor="ctr")
            s.text(1.75, y, 4.1, 0.83, name, size=16, bold=True, color=WHITE, anchor="ctr")
        hi[n] = gid
    s.shape(0.83, 5.8, 5.2, 0.6, "roundRect", fill="F7F9FB", line=MUTED, lw=1.25, dash="dash",
            adj={"adj": 14000}, paras=["Battery & failure model"], size=14, bold=True, color=GREY,
            anchor="ctr", ins=(0.3, 0, 0.1, 0), name="Battery (base)")
    with s.group("Battery (highlight)") as gid:
        s.shape(0.83, 5.8, 5.62, 0.6, "homePlate", fill="5A6B7B", shadow="lift", adj={"adj": 42000},
                paras=["Battery & failure model"], size=14, bold=True, color=WHITE, anchor="ctr",
                ins=(0.3, 0, 0.1, 0))
    hi["bat"] = gid
    s.card(6.7, 1.85, 5.8, 4.55, name="Detail panel")
    detail = {
        1: ("Layer 1 · Physical (LoRa)", LAYER[1][0], [
            "865 MHz band · +20 dBm",
            "Spreading factor 12 · 125 kHz: ≈2.5 s of airtime per frame",
            "Payload of at most 51 bytes",
            "Log-distance path loss plus shadowing (rubble, walls)",
            "Five severity presets, intact → extreme"]),
        2: ("Layer 2 · MAC & forwarding", LAYER[2][0], [
            "Slotted ALOHA: a stronger signal survives a collision if it is 6 dB ahead",
            "Gossip3: forward with 75% probability; stay quiet after 3 duplicates",
            "Geo-greedy: hand the message to a neighbour closer to its destination",
            "34-byte header · TTL 16 hops · cache of the last 256 message IDs"]),
        3: ("Layer 3 · Link-state monitoring", LAYER[3][0], [
            "A beacon from every node every 30 s",
            "PDR over the last 50 packets",
            "RSSI: received signal strength",
            "Reachability: neighbours heard recently",
            "Each node builds its own view; no central monitor"]),
        4: ("Layer 4 · Routing & evacuation", LAYER[4][0], [
            "Dynamic Dijkstra: shortest path on live link state; re-plans when the route ahead degrades",
            "PPO agent (exploratory): learns to pick the next neighbour",
            "Compares classical and learning-based routing"]),
        "bat": ("Battery & failure model", "5A6B7B", [
            "Linear battery drain over 300 s",
            "Below 20% charge, outgoing links weaken in proportion",
            "One failure per node per hour",
            "Sudden · graceful · mixed (default) · burst"]),
    }
    dids = {}
    for k, (h, col, items) in detail.items():
        dids[k] = s.text(7.05, 2.12, 5.15, 4.1,
                         [P(R(h), size=18, bold=True, color=col, after=10)] +
                         [P(t, bullet="•", bullet_color=col) for t in items],
                         size=14.5, color=GREY, after=8, lnsp=1.02, indent=0.24, name=f"Detail: {h}")
    # Layer 1 shows from the start (the slide before gave the overview); each click
    # swaps the panel and the highlighted layer
    seq = [1, 2, 3, 4, "bat"]
    for prev, k in zip(seq, seq[1:]):
        s.click([out(dids[prev]), out(hi[prev]), fade(dids[k]), fade(hi[k])])
    footer(s)

    # 14 -- six results ---------------------------------------------------------------
    s = d.slide("Six results")
    header(s, "Six results", "What the simulations showed")
    res = [("Live link state helps", "≈1.8× higher link-quality score"),
           ("PPO ≈ classical planners", "Same range, not better than the fastest"),
           ("Damage sweep", "Damage weakens long links, not trips"),
           ("A faster simulator", "Up to 7.3× faster than our reference"),
           ("Gossip", "No measurable difference yet"),
           ("Radio model", "Internally consistent with the standard model")]
    tids = []
    for i, (h, sub) in enumerate(res):
        x, y = 0.83 + (i % 3) * 4.0, 1.9 + (i // 3) * 2.3
        with s.group(f"Result {i + 1}") as gid:
            s.card(x, y, 3.7, 2.0)
            badge(s, x + 0.25, y + 0.3, 0.6, str(i + 1), fill=ORANGE if i % 2 else NAVY, size=16)
            s.text(x + 1.0, y + 0.22, 2.55, 0.78, h, size=16, bold=True, color=NAVY, anchor="ctr", lnsp=1.0)
            s.text(x + 0.25, y + 1.15, 3.2, 0.7, sub, size=13.5, color=GREY, lnsp=1.05)
        tids.append(gid)
    s.auto([fade(g, delay=0.12 * i) for i, g in enumerate(tids)])
    footer(s)

    # 15 -- result 1 --------------------------------------------------------------------
    s = d.slide("Result 1")
    header(s, "Live link state: ≈1.8× higher link-quality score",
           "Result 1 of 6  ·  Dijkstra with and without live link scores  ·  the same 100 trips, 10×10 grid")
    s.card(0.83, 1.85, 6.4, 4.6, name="Chart card")
    s.text(1.1, 2.02, 5.9, 0.35, "Average link-quality score along the route", size=13.5, bold=True,
           color=DEEP, anchor="ctr")
    x0, k = 2.75, 12.0
    for v in (0.1, 0.2, 0.3):
        s.line(x0 + v * k, 2.65, x0 + v * k, 4.85, GRIDC, 0.75)
    for v, lab in ((0, "0"), (0.1, "0.1"), (0.2, "0.2"), (0.3, "0.3")):
        s.text(x0 + v * k - 0.3, 4.9, 0.6, 0.28, lab, size=10.5, color=MUTED, align="c", anchor="ctr")
    s.line(x0, 2.65, x0, 4.85, NAVY, 1, alpha=60)
    bars = []
    for i, (lab, sub, v, col, vcol) in enumerate([("Static", "hop count", 0.145, CTX, "5F6F7D"),
                                                  ("Dynamic", "live link score", 0.267, BLUE, BLUE)]):
        y = 2.8 + i * 1.05
        s.text(0.95, y, 1.7, 0.78, [P(R(lab), bold=True, size=14), P(R(sub), size=11, color=MUTED)],
               color=DEEP, align="r", anchor="ctr", lnsp=1.0)
        b = s.shape(x0, y, v * k, 0.78, fill=col, name=f"Bar {lab}")
        t = s.text(x0 + v * k + 0.12, y, 1.0, 0.78, f"{v:.3f}", size=20, bold=True, color=vcol,
                   anchor="ctr", name=f"Value {lab}")
        bars.append((b, t))
    ratio = s.shape(x0, 5.42, 2.2, 0.55, "roundRect", fill=ORANGE, adj={"adj": 50000}, shadow="lift",
                    paras=["≈1.8× higher"], size=18, bold=True, color=WHITE, align="c", anchor="ctr",
                    name="Ratio")
    rnote = s.text(x0 + 2.35, 5.35, 2.05, 0.7, "1.5–1.9× across all five damage levels", size=11.5,
                   color=GREY, anchor="ctr", lnsp=1.0, name="Ratio range")
    c1 = s.card(7.55, 1.85, 4.95, 1.38, name="Matched length",
                paras=[P(R("1.9–2.6×"), size=28, bold=True, color=BLUE),
                       P(R("comparing only trips of the same length: longer routes score lower, so "
                           "the gap widens"), size=12.5, color=GREY)], ins=(0.25, 0.12, 0.2, 0.1),
                anchor="ctr", lnsp=1.0)
    c2 = s.card(7.55, 3.38, 4.95, 1.38, name="A star pair",
                paras=[P(R("1.03×"), size=28, bold=True, color="7C8B99"),
                       P(R("A* pair: re-planned in only 3 of 100 trips, so it tells us nothing either way"),
                         size=12.5, color=GREY)], ins=(0.25, 0.12, 0.2, 0.1), anchor="ctr", lnsp=1.0)
    s.card(7.55, 4.92, 4.95, 1.53, fill=PALE2, line=PALEB, shadow=None, name="Definition",
           paras=[P(R("What is the link-quality score?"), size=13, bold=True, color=NAVY, after=3),
                  P(R("A 0–1 number each radio keeps for how well its links have worked recently, "
                      "averaged over the radios on the route. A relative score for comparing "
                      "route-finders, not the share of messages delivered."), size=11.5, color=GREY)],
           ins=(0.22, 0.1, 0.18, 0.1), anchor="ctr", lnsp=1.0)
    s.click([wipe(bars[0][0], dur=0.6)], [fade(bars[0][1], 0.3), wipe(bars[1][0], dur=0.8)],
            [fade(bars[1][1], 0.3), zoom(ratio), fade(rnote, delay=0.2)])
    s.click(fade(c1))
    s.click(fade(c2))
    footer(s)

    # 16 -- result 2 ----------------------------------------------------------------------
    s = d.slide("Result 2")
    header(s, "PPO lands in the same range as classical planners",
           "Result 2 of 6  ·  Average hops to a safe zone  ·  100 trips per agent per grid")
    s.card(0.83, 1.85, 6.95, 4.6, name="Chart card")
    legend = [("3 fastest classical planners", CTX, 2.3), ("PPO (AI)", PPO, 0.85), ("Dynamic Dijkstra", BLUE, 1.5)]
    lx = 1.1
    for lab, col, w in legend:
        s.shape(lx, 2.12, 0.2, 0.2, fill=col)
        s.text(lx + 0.28, 2.02, w, 0.4, lab, size=11, color=DEEP, anchor="ctr")
        lx += w + 0.55
    base_y, kk = 5.5, 0.53
    for v in range(1, 6):
        s.line(1.55, base_y - v * kk, 7.45, base_y - v * kk, GRIDC, 0.75)
        s.text(1.05, base_y - v * kk - 0.14, 0.4, 0.28, str(v), size=10.5, color=MUTED, align="r", anchor="ctr")
    s.line(1.55, base_y, 7.45, base_y, NAVY, 1, alpha=60)
    data = [("10 × 10 grid", 1.95, [(2.17, "2.17"), (2.48, "2.48"), (3.23, "3.23")]),
            ("15 × 15 grid", 4.85, [(3.24, "3.23–3.25"), (3.56, "3.56"), (4.40, "4.40")])]
    bar_fx, val_fx = [], []
    for glab, gx0, vals in data:
        for j, (v, lab) in enumerate(vals):
            x = gx0 + j * 0.74
            b = s.shape(x, base_y - v * kk, 0.62, v * kk, fill=[CTX, PPO, BLUE][j], name=f"{glab} bar {j + 1}")
            t = s.text(x - 0.3, base_y - v * kk - 0.36, 1.22, 0.32, lab, size=12.5 if len(lab) < 6 else 10.5,
                       bold=True, color=DEEP, align="c", anchor="ctr", name=f"{glab} value {j + 1}")
            bar_fx.append(wipe(b, "bottom", dur=0.5, delay=0.12 * len(bar_fx)))
            val_fx.append(fade(t, 0.3, delay=0.12 * len(val_fx)))
        s.text(gx0 - 0.1, base_y + 0.08, 2.3, 0.32, glab, size=12.5, bold=True, color=DEEP, align="c", anchor="ctr")
    s.text(1.1, 6.0, 6.5, 0.32, "Success ≈100% for every agent, so we compare route length", size=11,
           color=MUTED, anchor="ctr")
    s.card(8.1, 1.85, 4.4, 0.95, fill=PALE2, line=PALEB, shadow=None, name="PPO definition",
           paras=["PPO: trial-and-error learning, with points for good moves and penalties for bad ones"],
           size=12.5, color=GREY, ins=(0.2, 0.05, 0.15, 0.05), anchor="ctr", lnsp=1.0)
    v1 = s.card(8.1, 2.98, 4.4, 1.12, name="Verdict 1",
                paras=[P(R("vs dynamic Dijkstra"), size=12, bold=True, color=MUTED),
                       P(R("PPO takes fewer hops on both grids"), size=15, bold=True, color=DEEP),
                       P(R("p = 2.5×10"), R("−5", baseline="30000"), R(" and 1.9×10"), R("−3", baseline="30000"),
                         size=11.5, color=MUTED)], ins=(0.22, 0.08, 0.15, 0.08), anchor="ctr", lnsp=1.0)
    v2 = s.card(8.1, 4.25, 4.4, 1.12, name="Verdict 2",
                paras=[P(R("vs the 3 fastest planners"), size=12, bold=True, color=MUTED),
                       P(R("10×10: slightly more hops (p = 0.047)"), size=13.5, bold=True, color=DEEP),
                       P(R("15×15: no significant difference (p = 0.255)"), size=13, color=GREY)],
                ins=(0.22, 0.08, 0.15, 0.08), anchor="ctr", lnsp=1.0)
    v3 = s.card(8.1, 5.52, 4.4, 0.93, fill=NAVY, line=NAVY, name="Takeaway",
                paras=["Learns a sensible route, but doesn't beat simple shortest-route methods → exploratory"],
                size=13, bold=True, color=WHITE, ins=(0.22, 0.05, 0.15, 0.05), anchor="ctr", lnsp=1.0)
    s.click(bar_fx, val_fx + [fade(v1)])
    s.click(fade(v2))
    s.click(fade(v3))
    footer(s)

    # 17 -- result 3: damage sweep ---------------------------------------------------------
    s = d.slide("Result 3")
    header(s, "Damage weakens long links, but trips still succeed",
           "Result 3 of 6  ·  Five damage levels (relative stress settings)  ·  250 trips per route-finder per level")
    s.card(0.83, 1.85, 7.0, 4.6, name="Chart card")
    s.text(1.1, 2.0, 6.5, 0.35, "Distance at which a single link works half the time", size=13.5,
           bold=True, color=DEEP, anchor="ctr")
    X0, KM, X1 = 2.45, 1.95, 7.33
    ytop, ybot = 2.5, 5.45
    s.shape(X0 + 0.4 * KM, ytop, 1.1 * KM, ybot - ytop, fill=CYAN, alpha=10, name="Mesh band")
    s.text(X0 + 0.4 * KM, ytop + 0.02, 1.1 * KM, 0.28, "our mesh: 400 m – 1.5 km", size=10, bold=True,
           color=CYAN, align="c", anchor="ctr")
    s.line(X0 + 1.5 * KM, ytop, X0 + 1.5 * KM, ybot, NAVY, 1.25, dash="dash", name="Radio range")
    s.line(X0, ybot, X1, ybot, NAVY, 1, alpha=60)
    for v in (0, 0.5, 1, 1.5, 2, 2.5):
        s.text(X0 + v * KM - 0.35, ybot + 0.04, 0.7, 0.26, f"{v:g}" + (" km" if v == 2.5 else ""),
               size=10.5, bold=(v == 1.5), color=NAVY if v == 1.5 else MUTED, align="c", anchor="ctr")
    vals = {"intact": None, "moderate": None, "heavy": (2.0, "≈2 km"), "severe": (1.03, "≈1 km"),
            "extreme": (0.637, "≈640 m")}
    lolli = []
    for i, (name, col) in enumerate(SEV):
        y = 2.95 + i * 0.55
        chip(s, 1.0, y - 0.18, 1.32, name, col, bold=(name == "heavy"), size=11)
        v = vals[name]
        with s.group(f"Lollipop {name}") as gid:
            if v is None:
                s.line(X0, y, X1 - 0.05, y, col, 3, tail="triangle")
                s.text(X1 - 1.75, y - 0.32, 1.7, 0.26, "far beyond range", size=10, color=MUTED,
                       align="r", anchor="ctr")
            else:
                s.line(X0, y, X0 + v[0] * KM, y, col, 3)
                dot(s, X0 + v[0] * KM, y, 0.2, col, line=WHITE, lw=1.5)
                s.text(X0 + v[0] * KM + 0.15, y - 0.16, 0.95, 0.32, v[1], size=12, bold=True, color=DEEP,
                       anchor="ctr")
        lolli.append(gid)
    ring = s.shape(0.93, 2.95 + 3 * 0.55 - 0.25, 6.75, 0.5, "roundRect", line=SEV[3][1], lw=2.25,
                   adj={"adj": 50000}, name="Severe highlight")
    c1 = s.card(8.15, 1.85, 4.35, 2.05, name="Severe callout",
                paras=[P(R("Severe is the first level where links within range fail often"), size=15,
                         bold=True, color=DEEP, after=6),
                       P(R("Heavy: halfway point ≈2 km, outside our range"), size=12.5, color=GREY),
                       P(R("Severe: ≈1 km, inside it"), size=12.5, color=GREY)],
                ins=(0.25, 0.1, 0.2, 0.1), anchor="ctr", lnsp=1.02)
    c2 = s.card(8.15, 4.05, 4.35, 2.4, name="Success callout",
                paras=[P(R("99.6%"), size=44, bold=True, color=PPO),
                       P(R("of trips: PPO reaches a safe zone at every damage level"), size=14,
                         bold=True, color=DEEP, after=4),
                       P(R("1 trip in 250 fails · classical planners: 100%"), size=12, color=GREY)],
                ins=(0.25, 0.1, 0.2, 0.1), anchor="ctr", lnsp=1.0)
    s.click(*[[wipe(g, dur=0.45)] for g in lolli])
    s.click([fade(ring), fade(c1)])
    s.click(fade(c2))
    footer(s)

    # 18 -- result 3 continued: the livelock ---------------------------------------------------
    s = d.slide("Livelock")
    header(s, "The AI's one weak spot: a livelock",
           "Result 3 of 6 (continued)  ·  Reward per trip: a normal trip scores just over 100")
    s.card(0.83, 1.85, 4.85, 3.9, name="Reward card")
    s.text(1.15, 2.05, 4.3, 0.32, "4 of 5 seed groups", size=13, bold=True, color=MUTED, anchor="ctr")
    s.text(1.15, 2.4, 4.3, 0.75, "101.4 – 102.2", size=34, bold=True, color=NAVY, anchor="ctr")
    s.text(1.15, 3.12, 4.3, 0.3, "average reward, at every damage level", size=12, color=GREY, anchor="ctr")
    with s.group("Fourth group") as g4:
        s.line(1.15, 3.7, 5.35, 3.7, BORDER, 1)
        s.text(1.15, 3.85, 4.3, 0.32, "The 4th seed group", size=13, bold=True, color=MUTED, anchor="ctr")
        s.text(1.15, 4.2, 4.3, 0.75, "≈17  ·  ≈23", size=34, bold=True, color=RED, anchor="ctr")
        s.text(1.15, 4.92, 4.3, 0.55, "intact to heavy  ·  severe and extreme", size=12, color=GREY,
               anchor="ctr")
    with s.group("Loop") as loop:
        s.card(6.0, 1.85, 6.5, 3.9)
        s.text(6.25, 2.0, 6.0, 0.32, "The stuck loop", size=13, bold=True, color=MUTED, anchor="ctr")
        boxes = [(6.3, 2.75, "Picks neighbour\nslot 0 again"), (10.15, 2.75, "It has died:\nrejected, −20"),
                 (8.22, 4.3, "Next view looks\nalmost the same")]
        for bx, by, t in boxes:
            s.shape(bx, by, 2.05, 0.85, "roundRect", fill=PALE, line=BORDER, adj={"adj": 14000},
                    paras=[t], size=12.5, bold=True, color=DEEP, align="c", anchor="ctr", lnsp=1.0)
    # outside the group: PowerPoint animates whole groups, so the spinning arrow stands alone
    arrow = s.shape(8.55, 2.45, 1.4, 1.4, "circularArrow", fill=PPO, name="Loop arrow",
                    adj={"adj1": 12500, "adj2": 1142319, "adj3": 16200000, "adj4": 0, "adj5": 12500})
    with s.group("Cause") as cause:
        s.text(6.25, 5.2, 6.0, 0.4, [P(R("Cause: ", color=ORANGE_TXT), R("a fixed list of 8 neighbours, "
               "where dead ones stay listed"))], size=12.5, bold=True, color=DEEP, anchor="ctr")
    note = s.card(0.83, 5.92, 4.85, 0.62, fill=PALE2, line=PALEB, shadow=None, name="Every level",
                  paras=["Same group at every level, even intact: a design issue, not damage"],
                  size=12, bold=True, color=NAVY, anchor="ctr", ins=(0.2, 0, 0.15, 0), lnsp=1.0)
    ban = s.card(6.0, 5.92, 6.5, 0.62, fill=NAVY, line=NAVY, name="Sweep takeaway",
                 paras=["Damage weakens long links but doesn't stop trips: the sweep compares route-finders under rising stress"],
                 size=11.5, bold=True, color=WHITE, anchor="ctr", ins=(0.2, 0, 0.15, 0), lnsp=1.0)
    s.click(fade(g4))
    s.click([fade(loop), fade(arrow)], [spin(arrow, dur=1.4, repeat=2)])
    s.click([fade(cause), fade(note, delay=0.2)])
    s.click(fade(ban))
    footer(s)

    # 19 -- result 4: speed ----------------------------------------------------------------------
    s = d.slide("Result 4")
    header(s, "A faster simulator for RL training",
           "Result 4 of 6  ·  Time-stepped backend vs our own SimPy reference, collisions on")
    s.card(0.83, 1.85, 7.0, 4.6, name="Lanes card")
    s.text(1.1, 2.0, 6.5, 0.36, "Reference (SimPy): one transmission event at a time", size=13.5,
           bold=True, color=DEEP, anchor="ctr")
    s.text(1.1, 4.0, 6.5, 0.36, "Time-stepped: every radio moves forward together", size=13.5,
           bold=True, color=DEEP, anchor="ctr")
    lane_a, lane_b = [], []
    for r in range(3):
        for c in range(8):
            lane_a.append((c, r, s.shape(1.25 + c * 0.44, 2.55 + r * 0.44, 0.32, 0.32, "roundRect",
                                         fill=CTX, adj={"adj": 16000}, name=f"Event {r}{c}")))
    for c in range(8):
        with s.group(f"Step column {c + 1}") as gid:
            for r in range(3):
                s.shape(1.25 + c * 0.44, 4.55 + r * 0.44, 0.32, 0.32, "roundRect", fill=BLUE,
                        adj={"adj": 16000})
        lane_b.append(gid)
    s.text(4.95, 2.55, 2.7, 1.2, "Each event handled separately: accurate, but slow for AI training",
           size=12, color=GREY, anchor="ctr", lnsp=1.02)
    s.text(4.95, 4.55, 2.7, 1.2, "One shared time step for all radios, same models for links, failures "
           "and collisions", size=12, color=GREY, anchor="ctr", lnsp=1.02)
    order = sorted(lane_a, key=lambda t: (t[0], t[1]))
    fx = [fade(sid, 0.08, delay=0.1 * i) for i, (_, _, sid) in enumerate(order)]
    fx += [fade(g, 0.08, delay=0.041 * i) for i, g in enumerate(lane_b)]
    s.click(fx)
    big = s.card(8.15, 1.85, 4.35, 2.55, name="Speed-up",
                 paras=[P(R("up to"), size=14, color=GREY), P(R("7.3×"), size=64, bold=True, color=PPO),
                        P(R("faster than our reference simulator"), size=14, bold=True, color=DEEP)],
                 ins=(0.25, 0.05, 0.2, 0.05), anchor="ctr", lnsp=0.95)
    sub = s.card(8.15, 4.55, 4.35, 1.9, name="Speed-up detail",
                 paras=[P(R("≈4.7× at the 10×10 grid used for the main results"), bullet="•"),
                        P(R("Training needs 200,000 practice steps per run"), bullet="•")],
                 size=13.5, color=GREY, after=8, ins=(0.25, 0.1, 0.2, 0.1), anchor="ctr", lnsp=1.02)
    s.click([zoom(big)], [fade(sub)])
    footer(s)

    # 20 -- result 5: gossip ----------------------------------------------------------------------
    s = d.slide("Result 5")
    header(s, "Gossip: no measurable difference",
           "Result 5 of 6  ·  AI with gossip on vs off  ·  3 training runs × 300 trips per setting")
    s.card(0.83, 1.85, 4.3, 4.6, name="Gossip card")
    G = {"c": (1.75, 3.3), "a": (2.85, 2.55), "b": (3.0, 3.35), "d": (2.85, 4.1),
         "e": (3.95, 2.3), "f": (4.1, 2.95), "g": (4.1, 3.75), "h": (3.95, 4.4)}
    for a, b in ("ca", "cb", "cd", "ae", "af", "bf", "bg", "dg", "dh"):
        (x1, y1), (x2, y2) = G[a], G[b]
        dx, dy = x2 - x1, y2 - y1
        L = (dx * dx + dy * dy) ** 0.5
        s.line(x1 + dx / L * 0.18, y1 + dy / L * 0.18, x2 - dx / L * 0.2, y2 - dy / L * 0.2, CYAN, 1.75,
               tail="triangle")
    for k, (cx, cy) in G.items():
        dot(s, cx, cy, 0.3 if k == "c" else 0.24, PPO if k == "c" else WHITE, line=NAVY if k != "c" else WHITE, lw=2)
    s.text(1.1, 4.85, 3.8, 1.45, [P(R("Gossip: radios pass information to neighbours, who pass it on, "
                                      "like a rumour."), bold=True, color=DEEP, size=13, after=6),
                                  P(R("Here: the AI's value estimate for each position."), size=12,
                                    color=GREY)], lnsp=1.02)
    cols_x = [(5.45, 2.65, "Metric"), (8.1, 1.45, "Gossip on"), (9.55, 1.45, "Gossip off"),
              (11.0, 1.5, "p-value")]
    s.shape(5.45, 1.85, 7.05, 0.55, "roundRect", fill=NAVY, adj={"adj": 18000}, name="Table header")
    for x, w, lab in cols_x:
        s.text(x + 0.2, 1.85, w - 0.25, 0.55, lab, size=13, bold=True, color=WHITE, anchor="ctr",
               align="l" if lab == "Metric" else "c")
    rows = [("Reached a safe zone", "100%", "100%", "–"), ("Average hops", "2.487", "2.497", "0.842"),
            ("Average reward", "101.42", "101.27", "0.826")]
    rws = []
    for i, row in enumerate(rows):
        y = 2.5 + i * 0.7
        with s.group(f"Row {i + 1}") as gid:
            s.shape(5.45, y, 7.05, 0.62, "roundRect", fill=PALE if i % 2 else WHITE, line=BORDER,
                    adj={"adj": 14000})
            for j, ((x, w, _), val) in enumerate(zip(cols_x, row)):
                s.text(x + 0.2, y, w - 0.25, 0.62, val, anchor="ctr", align="l" if j == 0 else "c",
                       size=[14, 18, 18, 15][j], bold=j < 3, color=[DEEP, NAVY, NAVY, GREY][j])
        rws.append(gid)
    pn = s.text(5.45, 4.62, 7.05, 0.35, "Both p-values are far above 0.05: no measurable difference",
                size=12, color=MUTED, anchor="ctr", name="p note")
    why = s.card(5.45, 5.12, 7.05, 1.33, fill=NAVY, line=NAVY, name="Why",
                 paras=[P(R("Why: the merge step, where a radio combines received values with its own, "
                            "isn't connected yet, and both settings already solve the task."), size=13,
                          color=WHITE, after=4),
                        P(R("→ The system works without gossip; this doesn't show gossip helps."), size=13,
                          bold=True, color=GOLD)], ins=(0.25, 0.08, 0.2, 0.08), anchor="ctr", lnsp=1.02)
    s.click([fade(g, delay=0.25 * i) for i, g in enumerate(rws)] + [fade(pn, delay=0.75)])
    s.click(fade(why))
    footer(s)

    # 21 -- result 6: radio model --------------------------------------------------------------------
    s = d.slide("Result 6")
    header(s, "The radio model is internally consistent",
           "Result 6 of 6  ·  Link delivery (PDR) vs distance from the channel model (paper Fig. 2)")
    s.card(0.83, 1.8, 7.45, 4.72, name="Figure card")
    iw, ih = 7.15, 7.15 * 1307 / 2068
    ix, iy = 0.98, 1.9
    s.pic("fig2.png", ix, iy, iw, ih, name="Paper Fig. 2",
          descr="Packet delivery ratio versus distance on a log scale for the five damage presets")
    px = iw / 2068

    def fx_(dist_m):
        import math
        return ix + (901.6 + (math.log10(dist_m) - 3) * 551.1) * px

    yh = iy + 629.7 * px
    with s.group("Half-way markers") as marks:
        for dist, lab, dy in ((637, "≈640 m", -0.42), (1030, "≈1 km", 0.2), (2000, "≈2 km", -0.42)):
            x = fx_(dist)
            dot(s, x, yh, 0.22, None, line=DEEP, lw=2.5)
            s.shape(x - 0.42, yh + dy, 0.84, 0.26, "roundRect", fill=DEEP, adj={"adj": 50000},
                    paras=[lab], size=10, bold=True, color=WHITE, align="c", anchor="ctr")
    s.card(8.55, 1.8, 3.95, 0.98, fill=PALE2, line=PALEB, shadow=None, name="How to read",
           paras=["Log scale: each labelled gridline is 10× further. Shaded band: our mesh, 400 m to 1.5 km."],
           size=11.5, color=GREY, ins=(0.2, 0.05, 0.15, 0.05), anchor="ctr", lnsp=1.02)
    with s.group("Half-way distances") as r1:
        s.card(8.55, 2.93, 3.95, 1.45)
        s.text(8.78, 3.0, 3.6, 0.32, "A link works half the time at", size=12, bold=True, color=MUTED, anchor="ctr")
        for i, (name, col, val) in enumerate((("heavy", SEV[2][1], "≈2 km"), ("severe", SEV[3][1], "≈1 km"),
                                              ("extreme", SEV[4][1], "≈640 m"))):
            dot(s, 8.9, 3.5 + i * 0.29, 0.15, col)
            s.text(9.1, 3.36 + i * 0.29, 3.2, 0.28, [P(R(f"{name}  "), R(val, bold=True))], size=13,
                   color=DEEP, anchor="ctr")
    r2 = s.card(8.55, 4.5, 3.95, 0.82, name="At 1.5 km",
                paras=[P(R("At 1.5 km: 66% · 29% · 11%"), size=14, bold=True, color=DEEP),
                       P(R("heavy · severe · extreme"), size=11, color=MUTED)],
                ins=(0.22, 0.05, 0.15, 0.05), anchor="ctr", lnsp=1.0)
    r3 = s.card(8.55, 5.43, 3.95, 0.48, name="At 400 m",
                paras=[P(R("At 400 m: above 73% at every level"), size=13, bold=True, color=DEEP)],
                ins=(0.22, 0, 0.15, 0), anchor="ctr")
    r4 = s.card(8.55, 6.0, 3.95, 0.52, fill=NAVY, line=NAVY, name="Consistency",
                paras=["Internal consistency, not agreement with real radios"], size=11.5, bold=True,
                color=WHITE, ins=(0.2, 0, 0.12, 0), anchor="ctr", lnsp=1.0)
    s.click([fade(marks), fade(r1)])
    s.click(fade(r2))
    s.click(fade(r3))
    s.click(fade(r4))
    footer(s)

    # 22 -- limitations -------------------------------------------------------------------------------
    s = d.slide("Limitations")
    header(s, "Limitations", "What the results do, and don't, show")
    lims = [("Simulation only", "No hardware validation yet: read every result as a simulation finding"),
            ("Radio airtime", "30 s beacons at SF12 ≈ 4.4% channel occupancy per node; a compliant "
                              "schedule could shift beacon-dependent results"),
            ("RL is exploratory", "The 8-neighbour action space causes the livelock; value estimates "
                                  "were inconsistent across the 3 training runs"),
            ("Score ≠ delivery", "The link-quality score is not end-to-end SOS delivery; measuring "
                                 "that is the next step"),
            ("Adoption", "Needs enough devices and relays; participation can't be assumed")]
    lids = []
    for i, (h, body) in enumerate(lims):
        y = 1.85 + i * 0.91
        with s.group(f"Limitation {i + 1}") as gid:
            s.card(0.83, y, 11.67, 0.79, radius=0.07)
            badge(s, 1.02, y + 0.145, 0.5, str(i + 1), fill=ORANGE, size=13)
            s.text(1.75, y, 3.1, 0.79, h, size=15.5, bold=True, color=DEEP, anchor="ctr")
            s.text(4.9, y, 7.4, 0.79, body, size=13.5, color=GREY, anchor="ctr", lnsp=1.0)
        lids.append(gid)
    for g in lids:
        s.click(fade(g))
    footer(s)

    # 23 -- future work ------------------------------------------------------------------------------
    s = d.slide("Future work")
    header(s, "Future work", "From a simulation framework toward real-world validation")
    fut = [("Measure", "End-to-end SOS delivery, plus adaptive beaconing to cut airtime"),
           ("Validate", "On physical LoRa hardware: timing, interference, real radio behaviour"),
           ("Integrate", "With existing LoRa platforms and search-and-rescue systems"),
           ("Improve RL", "Fix the action space, stabilise training, test larger networks and harsher failures"),
           ("Adopt", "Responders → pre-positioned relays → the public, with disaster-management authorities")]
    centers = [0.83 + 1.1 + i * 2.3675 for i in range(5)]
    fids, segs = [], []
    for i in range(4):
        segs.append(s.line(centers[i] + 0.4, 2.35, centers[i + 1] - 0.4, 2.35, NAVY, 2, alpha=70,
                           name=f"Road {i + 1}"))
    for i, (h, body) in enumerate(fut):
        cx = centers[i]
        with s.group(f"Future {i + 1}") as gid:
            badge(s, cx - 0.375, 1.975, 0.75, str(i + 1), fill=ORANGE if i % 2 else NAVY, size=16)
            s.card(cx - 1.08, 3.0, 2.16, 2.45, radius=0.07)
            s.text(cx - 0.9, 3.15, 1.8, 0.3, f"STEP {i + 1}", size=10, bold=True, color=ORANGE_TXT, spc=100,
                   anchor="ctr")
            s.text(cx - 0.9, 3.45, 1.8, 0.45, h, size=16.5, bold=True, color=NAVY, anchor="ctr")
            s.text(cx - 0.9, 4.0, 1.85, 1.55, body, size=12.5, color=GREY, lnsp=1.03)
        fids.append(gid)
    goal = s.card(0.83, 5.88, 11.67, 0.6, fill=NAVY, line=NAVY, radius=0.3, name="Goal",
                  paras=["Goal: from simulation to a system validated under real disaster-response conditions"],
                  size=14, bold=True,
                  color=WHITE, align="c", anchor="ctr")
    s.click(fade(fids[0]))
    for i in range(1, 5):
        s.click([wipe(segs[i - 1], dur=0.35)], [fade(fids[i])])
    s.click(fade(goal))
    footer(s)

    # 24 -- thank you ---------------------------------------------------------------------------------
    s = d.slide("Thank you", dark=True)
    s.pic("mascot.png", 6.65, 1.194, 5.85, 3.862, name="HTC 2026 artwork",
          descr="IEEE R10 HTC 2026 Bangkok conference artwork")
    s.text(0.85, 1.4, 5.2, 0.8, "Thank You", size=36, bold=True, color=WHITE, anchor="ctr")
    s.text(0.87, 2.25, 3.8, 0.72, "Q&A", size=31, bold=True, color=CYAN2, anchor="ctr")
    s.text(0.92, 3.35, 5.6, 1.4, [P(R("Aniraj Singh  ·  Azzah Mallick"), size=15, bold=True, after=4),
                                  P(R("Department of CSE, Amity University, Uttar Pradesh, India"), size=12,
                                    after=10),
                                  P(R("IEEE R10 HTC 2026  ·  Bangkok, Thailand"), size=12, bold=True,
                                    color=GOLD)], color=WHITE, lnsp=1.05)
    s.shape(0.88, 5.0, 4.9, 0.55, "roundRect", fill=NAVY, line=GOLD, lw=1.2, adj={"adj": 18000},
            paras=["Empowering Humanity Through Emerging Technology & Innovation"], size=9.5, bold=True,
            color=WHITE, align="c", anchor="ctr", name="Theme pill")
    s.notes = "[Thank the audience and invite questions.]"
    footer(s)
    return d


# ---------------------------------------------------------------------------
# Speaker notes from the speech
# ---------------------------------------------------------------------------

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
HEADINGS = {"SPEECH v2", "Introduction and Motivation", "Existing work", "Problem statement", "Solution",
            "Methodology", "Design", "Analysis and Results", "Limitations", "Future Work", "WHAT HAPPENED"}
SLIDE_LABELS = ("Central Gateway Dependency", "Static Routing Decisions", "Limited Simulation Scalability",
                "Limited Damage-Level Evaluation")

# slide key -> (where its part of the speech starts, cues for each click in order)
CUES = {
    "Motivation": ("I'd like to begin with something",
                   ["According to the World Meteorological Organization", "Yet, over the same period",
                    "What goes unmentioned", "In other words, the hazard"]),
    "When disaster strikes": ("That brings us to a question",
                              ["When communication towers are damaged", "Preparing for disasters is one part"]),
    "Existing work": ("One technology that has received attention",
                      ["For example, Titan", "There are also Consumer-Grade", "In particular, Project OWL",
                       "Alongside these communication systems", "Further study on this also added"]),
    "Gaps": ("So, if these technologies already exist",
             ["The first was concerning routing decisions", "The second was simulation",
              "And the third was evaluation", "B.A.T.M.A.N, Babel and OLSR", "ABOT extends its scope"]),
    "Problem statement": ("This brings us to the central problem", ["how can routing in a gateway-free"]),
    "Objectives": ("This is where ABOT comes in.", []),
    "How ABOT works": ("To investigate these questions, we propose ABOT",
                       ["When a node joins the network", "Now, imagine a survivor",
                        "ABOT is designed to account for changing conditions"]),
    "Testbed": ("We have built a virtual disaster environment",
                ["The network was tested under five damage-severity presets",
                 "The simulation accounts for radio collisions", "Radio failure scenarios include"]),
    "Pipeline": ("Next, we implemented the communication protocol.",
                 ["We then defined the routing task", "To support reinforcement-learning experiments",
                  "For the learning-based router", "Finally, we benchmarked"]),
    "Architecture": ("The system design for ABOT was based on four layers", []),
    "Four layers": ("Layer 1: Physical Communication",
                    ["Layer 2: MAC and Forwarding", "Layer 3: Link-State Monitoring",
                     "Layer 4: Routing and Evacuation", "Battery and Failure Model"]),
    "Six results": ("The tested simulation gave results around six areas", []),
    "Result 1": ("For our routing approach the considered result",
                 ["Without live link scores", "If we compare only trips", "We also tested the A-star pair"]),
    "Result 2": ("second finding was that the ai route finder",
                 ["The results show that AI takes fewer hops", "The p values come",
                  "It learned a sensible way to route"]),
    "Result 3": ("Third result was based on the damage preset",
                 ["At heavy, a link works half the time", "So severe is the first level",
                  "The AI doesn't get worse"]),
    "Livelock": ("Each trip also earns a points score",
                 ["The fourth averages only", "The AI's one weak spot is a livelock",
                  "It happens at every damage level", "So in our setup, damage weakens"]),
    "Result 4": ("Fourth, Our first simulator", ["So we built a faster one", "The newer simuklator runs"]),
    "Result 5": ("Fifth, was gossip.", ["Both settings reached a safe zone", "So gossip made no difference"]),
    "Result 6": ("Lastly, the radio model that we used.",
                 ["Each curve is one damage level", "At 1.5 kilometres, links succeed",
                  "At 400 metres, the nearest", "The radio model behaves the way"]),
    "Limitations": ("There are certain drawbacks to abot.",
                    ["First, ABOT has been evaluated entirely in simulation",
                     "There are also practical radio constraints", "Second, there are limitations in the routing",
                     "Another important distinction is that PDR", "Finally, real-world adoption"]),
    "Future work": ("Moving forward, we have identified",
                    ["First, we want to measure end-to-end", "Second, the framework needs to be validated",
                     "We also aim to explore integration", "On the routing side, future work",
                     "Finally, there is the question of adoption", "Ultimately, our goal"]),
}
END_MARK = "ONE IMPORTANT RESEARCH-INTEGRITY POINT"

# Presenter notes written for slides the speech doesn't walk through, added after
# that slide's part of the speech. Their [CLICK n] cues count towards the slide's clicks.
EXTRA_NOTES = {
    "Architecture": (
        "[Added for this slide: walking through paper Fig. 1]\n\n"
        "This is the architecture figure from our paper. Read it from the bottom up. Layer 1 is the "
        "LoRa radio itself. Layer 2 decides when a node transmits and how messages are passed on. "
        "Layer 3 turns what each node hears into link-quality measurements. Layer 4 uses those "
        "measurements to choose the route.\n\n"
        "[CLICK 1] Decisions flow down the left side: the routing layer selects the next hop, and "
        "that becomes a radio transmission.\n\n"
        "[CLICK 2] Measurements flow up the right side: received frames become de-duplicated beacon "
        "arrivals, and those become link metrics (packet delivery ratio, signal strength and "
        "reachability) that the routing layer reads. Between Layers 3 and 4, the learning agent "
        "receives its view as a list of 24 numbers.\n\n"
        "[CLICK 3] The dashed box around everything is the simulation harness. We use it only to "
        "train and evaluate the routing methods; it isn't part of the software a real node would "
        "run.\n\n"
        "Next, I'll go through the layers one at a time.\n\n"
        "[If asked]\n"
        "- \"The figure says PPO may replace the solver. Does it?\" The figure shows the option. In "
        "our results PPO is exploratory: it lands in the same range as the classical planners but "
        "doesn't beat the fastest ones.\n"
        "- \"How does each node know the whole network to run Dijkstra?\" In the simulation the "
        "planners get a full view of the network, as a best case. Sharing link state across the "
        "mesh, and the airtime that costs, is future work."),
}


def speech_text(path):
    root = ET.fromstring(zipfile.ZipFile(path).read("word/document.xml"))
    paras = []
    for p in root.iter(W + "p"):
        t = "".join(el.text or "" for el in p.iter(W + "t")).strip()
        if not t or t in HEADINGS or t.startswith(SLIDE_LABELS):
            continue
        if paras and not re.search(r"[.?!:)\"”]$", paras[-1]) and t[0].islower():
            paras[-1] += " " + t   # a paragraph the draft broke mid-sentence
        else:
            paras.append(t)
    return "\n\n".join(paras)


def find(hay, needle, pos=0):
    """str.find that treats curly and straight apostrophes alike (same length, so positions hold)."""
    flat = str.maketrans("’‘", "''")
    return hay.translate(flat).find(needle.translate(flat), pos)


def attach_notes(deck, text):
    keys = [s.key for s in deck.slides if s.key in CUES]
    starts = []
    for k in keys:
        i = find(text, CUES[k][0])
        if i < 0:
            sys.exit(f"speech: can't find the start of slide '{k}': {CUES[k][0]!r}")
        starts.append(i)
    if starts != sorted(starts):
        sys.exit("speech: slide starts are out of order")
    end = text.find(END_MARK)
    end = end if end >= 0 else len(text)
    for idx, k in enumerate(keys):
        chunk = text[starts[idx]: starts[idx + 1] if idx + 1 < len(keys) else end].strip()
        pos = 0
        for n, cue in enumerate(CUES[k][1], 1):
            j = find(chunk, cue, pos)
            if j < 0:
                sys.exit(f"speech: slide '{k}' click {n}: can't find {cue!r}")
            mark = f"[CLICK {n}] "
            chunk = chunk[:j] + mark + chunk[j:]
            pos = j + len(mark) + len(cue)
        slide = next(s for s in deck.slides if s.key == k)
        if k in EXTRA_NOTES:
            chunk += "\n\n" + EXTRA_NOTES[k]
        cues = len(CUES[k][1]) + EXTRA_NOTES.get(k, "").count("[CLICK ")
        if slide.clicks() != cues:
            sys.exit(f"slide '{k}': {slide.clicks()} clicks but {cues} cues")
        slide.notes = chunk
    for s in deck.slides:
        if s.key not in CUES and s.clicks():
            sys.exit(f"slide '{s.key}' has clicks but no cues")


def notes_xml(text):
    paras = "".join(
        f'<a:p><a:r><a:rPr lang="en-US" dirty="0"/><a:t>{esc(line)}</a:t></a:r></a:p>' if line
        else '<a:p><a:endParaRPr lang="en-US" dirty="0"/></a:p>' for line in text.split("\n"))
    return (f'{XML_HEAD}<p:notes {NS}><p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/>'
            '<p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" '
            'cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr><p:sp><p:nvSpPr>'
            '<p:cNvPr id="2" name="Slide Image Placeholder 1"/><p:cNvSpPr><a:spLocks noGrp="1" noRot="1" '
            'noChangeAspect="1"/></p:cNvSpPr><p:nvPr><p:ph type="sldImg"/></p:nvPr></p:nvSpPr><p:spPr/>'
            '</p:sp><p:sp><p:nvSpPr><p:cNvPr id="3" name="Notes Placeholder 2"/><p:cNvSpPr><a:spLocks '
            'noGrp="1"/></p:cNvSpPr><p:nvPr><p:ph type="body" idx="1"/></p:nvPr></p:nvSpPr><p:spPr/>'
            f'<p:txBody><a:bodyPr/><a:lstStyle/>{paras}</p:txBody></p:sp></p:spTree></p:cSld>'
            '<p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:notes>')


# ---------------------------------------------------------------------------
# Package
# ---------------------------------------------------------------------------

KEEP = ["_rels/.rels", "ppt/slideMasters/slideMaster1.xml", "ppt/slideMasters/_rels/slideMaster1.xml.rels",
        "ppt/slideLayouts/slideLayout1.xml", "ppt/slideLayouts/_rels/slideLayout1.xml.rels",
        "ppt/slideLayouts/slideLayout2.xml", "ppt/slideLayouts/_rels/slideLayout2.xml.rels",
        "ppt/theme/theme1.xml", "ppt/notesMasters/notesMaster1.xml",
        "ppt/notesMasters/_rels/notesMaster1.xml.rels", "ppt/presProps.xml", "ppt/viewProps.xml",
        "ppt/tableStyles.xml"]
MEDIA = {"bg_light.png": "ppt/media/image-2-1.png", "bg_dark.png": "ppt/media/image-1-1.png",
         "mascot.png": "ppt/media/image-1-2.png", "logo.png": "ppt/media/image-2-2.png"}


def rels_xml(rels):
    body = "".join(f'<Relationship Id="{i}" Type="{RT}{t}" Target="{tg}"/>' for i, t, tg in rels)
    return f'{XML_HEAD}<Relationships xmlns="{REL_NS}">{body}</Relationships>'


def write(deck, out_path):
    tz = zipfile.ZipFile(TEMPLATE)
    n = len(deck.slides)
    ct = "application/vnd.openxmlformats-officedocument.presentationml."
    overrides = [("/ppt/presentation.xml", ct + "presentation.main+xml"),
                 ("/ppt/slideMasters/slideMaster1.xml", ct + "slideMaster+xml"),
                 ("/ppt/slideLayouts/slideLayout1.xml", ct + "slideLayout+xml"),
                 ("/ppt/slideLayouts/slideLayout2.xml", ct + "slideLayout+xml"),
                 ("/ppt/notesMasters/notesMaster1.xml", ct + "notesMaster+xml"),
                 ("/ppt/theme/theme1.xml", "application/vnd.openxmlformats-officedocument.theme+xml"),
                 ("/ppt/presProps.xml", ct + "presProps+xml"), ("/ppt/viewProps.xml", ct + "viewProps+xml"),
                 ("/ppt/tableStyles.xml", ct + "tableStyles+xml"),
                 ("/docProps/core.xml", "application/vnd.openxmlformats-package.core-properties+xml"),
                 ("/docProps/app.xml", "application/vnd.openxmlformats-officedocument.extended-properties+xml")]
    for i in range(1, n + 1):
        overrides += [(f"/ppt/slides/slide{i}.xml", ct + "slide+xml"),
                      (f"/ppt/notesSlides/notesSlide{i}.xml", ct + "notesSlide+xml")]
    types = (f'{XML_HEAD}<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
             '<Default Extension="xml" ContentType="application/xml"/><Default Extension="rels" '
             'ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default '
             'Extension="png" ContentType="image/png"/>'
             + "".join(f'<Override PartName="{p}" ContentType="{c}"/>' for p, c in overrides) + "</Types>")

    pres = tz.read("ppt/presentation.xml").decode("utf8")
    ids = "".join(f'<p:sldId id="{256 + i}" r:id="rId{100 + i}"/>' for i in range(n))
    pres = re.sub(r"<p:sldIdLst>.*?</p:sldIdLst>", f"<p:sldIdLst>{ids}</p:sldIdLst>", pres, flags=re.S)
    pres_rels = [("rId1", "slideMaster", "slideMasters/slideMaster1.xml"),
                 ("rId11", "notesMaster", "notesMasters/notesMaster1.xml"),
                 ("rId12", "presProps", "presProps.xml"), ("rId13", "viewProps", "viewProps.xml"),
                 ("rId14", "theme", "theme/theme1.xml"), ("rId15", "tableStyles", "tableStyles.xml")]
    pres_rels += [(f"rId{100 + i}", "slide", f"slides/slide{i + 1}.xml") for i in range(n)]

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    core = (f'{XML_HEAD}<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/'
            'core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/'
            'terms/" xmlns:dcmitype="http://purl.org/dc/dcmitype/" xmlns:xsi="http://www.w3.org/2001/'
            'XMLSchema-instance"><dc:title>ABOT: IEEE R10 HTC 2026 talk</dc:title><dc:creator>Aniraj Singh, '
            'Azzah Mallick</dc:creator><cp:lastModifiedBy>Aniraj Singh</cp:lastModifiedBy><cp:revision>1'
            f'</cp:revision><dcterms:created xsi:type="dcterms:W3CDTF">{now}</dcterms:created>'
            f'<dcterms:modified xsi:type="dcterms:W3CDTF">{now}</dcterms:modified></cp:coreProperties>')
    app = (f'{XML_HEAD}<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-'
           'properties" xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">'
           '<Application>Microsoft Office PowerPoint</Application><PresentationFormat>Widescreen'
           f'</PresentationFormat><Slides>{n}</Slides><Notes>{n}</Notes><HiddenSlides>0</HiddenSlides>'
           '<AppVersion>16.0000</AppVersion></Properties>')

    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", types)
        for name in KEEP:
            z.writestr(name, tz.read(name))
        z.writestr("ppt/presentation.xml", pres)
        z.writestr("ppt/_rels/presentation.xml.rels", rels_xml(pres_rels))
        z.writestr("docProps/core.xml", core)
        z.writestr("docProps/app.xml", app)
        for media in sorted(deck.media):
            figs = {"fig1.png": FIG1, "fig2.png": FIG2}
            data = figs[media].read_bytes() if media in figs else tz.read(MEDIA[media])
            z.writestr(f"ppt/media/{media}", data)
        for i, s in enumerate(deck.slides, 1):
            rels = [("rId1", "slideLayout", "../slideLayouts/slideLayout2.xml")]
            rels += [(rid, "image", f"../media/{m}") for m, rid in s.images.items()]
            rels += [(f"rId{len(s.images) + 2}", "notesSlide", f"../notesSlides/notesSlide{i}.xml")]
            z.writestr(f"ppt/slides/slide{i}.xml", s.xml())
            z.writestr(f"ppt/slides/_rels/slide{i}.xml.rels", rels_xml(rels))
            z.writestr(f"ppt/notesSlides/notesSlide{i}.xml", notes_xml(s.notes))
            z.writestr(f"ppt/notesSlides/_rels/notesSlide{i}.xml.rels",
                       rels_xml([("rId1", "notesMaster", "../notesMasters/notesMaster1.xml"),
                                 ("rId2", "slide", f"../slides/slide{i}.xml")]))


def main():
    out_path = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    deck = build()
    attach_notes(deck, speech_text(SPEECH))
    write(deck, out_path)
    clicks = sum(s.clicks() for s in deck.slides)
    print(f"wrote {out_path.relative_to(ROOT) if out_path.is_relative_to(ROOT) else out_path}: "
          f"{len(deck.slides)} slides, {clicks} clicks")


if __name__ == "__main__":
    main()
