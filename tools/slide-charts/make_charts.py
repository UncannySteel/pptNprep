"""Slide-ready versions of the two new results charts for the ABOT talk.

Draws Chart A (static vs dynamic link-quality score) and Chart B (average hops
per route-finder) as recommended in ABOT-results-explained.html, "New charts
worth making". Writes a 300 dpi PNG, a vector PDF and a vector SVG for each into
assets/figures/. The SVG keeps text as outlines so it looks the same when
inserted into PowerPoint.

Every number is copied from the camera-ready paper; the section is noted beside
each one. Nothing here reads the code directory.

Run from the pptNprep folder:

    python -E -P tools/slide-charts/make_charts.py
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, PathPatch
from matplotlib.path import Path as MPath

OUT = Path(__file__).resolve().parents[2] / "assets" / "figures"

# Colours follow ABOT-results-explained.html. The grey is one step lighter than
# the page's #7A8A95: that one sits ΔE 14.7 from the blue, under the dataviz
# validator's floor of 15; #8A98A2 gives 17.1. Every bar also carries a text
# label, so colour is never the only cue.
INK = "#13202A"
MUTED = "#566874"
GRID = "#E3E8EB"
BASELINE = "#8C9EA9"
GREY = "#8A98A2"
BLUE = "#2a78d6"
ORANGE = "#eb6834"

FONT = "Segoe UI"
TITLE, SUB, LEGEND, PANEL, ROW, VALUE, TICK, NOTE = 28, 19, 17, 19, 19, 19, 16, 14
LINE = 1.25  # line height as a multiple of font size

# Layout, in inches. 13.333 in is the width of a 16:9 PowerPoint slide, so at
# full width the font sizes above are the sizes the audience sees.
FIG_W = 13.333
MARGIN_X = 0.30
MARGIN_R = 0.45
MARGIN_TOP = 0.28
MARGIN_BOTTOM = 0.22
ROW_PITCH = 0.78
BAR_H = 0.44
RADIUS = 0.06       # rounded data end; the baseline end stays square
LABEL_GAP = 0.18    # row label to baseline
PANEL_GAP = 0.90
VALUE_PAD = 0.09    # bar end to value label
SWATCH = 0.22
TICK_BAND = 0.36

CHARTS = {
    "chart_a_link_scores": {
        "title": "Live link scores lead to better-quality routes",
        "subtitle": "Average link-quality score (0 to 1), Dijkstra, 10×10 grid, heavy damage",
        "legend": [("Static (counts hops)", GREY), ("Dynamic (uses live scores)", BLUE)],
        "rows": [("Static", GREY), ("Dynamic", BLUE)],
        "panels": [
            # Paper V-C: "lowers mean link PDR from 0.267 to 0.145"
            ("All 100 trips", [(0.145, "0.145"), (0.267, "0.267")]),
            # Paper V-C: 43 seeds with the identical initial route, "0.2067 against 0.3098"
            ("43 trips with the same first route", [(0.2067, "0.2067"), (0.3098, "0.3098")]),
        ],
        "xmax": 0.4,
        "ticks": [(0, "0"), (0.1, "0.1"), (0.2, "0.2"), (0.3, "0.3"), (0.4, "0.4")],
        "note": None,
    },
    "chart_b_avg_hops": {
        "title": "The AI sits between the fastest planners and Dijkstra dynamic",
        "subtitle": "Average hops, heavy damage, 100 trips each. Fewer is better.",
        "legend": [("Three fastest planners", GREY), ("PPO (the AI)", ORANGE),
                   ("Dijkstra dynamic", BLUE)],
        "rows": [("Three fastest", GREY), ("PPO", ORANGE), ("Dijkstra dynamic", BLUE)],
        "panels": [
            # Paper V-A: means 2.17 (three fastest), 2.48 (PPO), 3.23 (dijkstra_dynamic)
            ("10×10 grid (100 radios)", [(2.17, "2.17"), (2.48, "2.48"), (3.23, "3.23")]),
            # Paper V-A: means 3.23–3.25 (three fastest; bar drawn at the midpoint),
            # 3.56 (PPO), 4.40 (dijkstra_dynamic)
            ("15×15 grid (225 radios)", [(3.24, "3.23–3.25"), (3.56, "3.56"), (4.40, "4.40")]),
        ],
        "xmax": 5,
        "ticks": [(t, str(t)) for t in range(6)],
        # Paper V-A, Table II: astar_dynamic / astar_static / dijkstra_static
        "note": "Three fastest planners: A* static, A* dynamic and Dijkstra static.",
    },
}


def lh(pt):
    return pt * LINE / 72


def text_width(fig, s, size, weight="normal"):
    t = fig.text(0, 0, s, fontsize=size, fontweight=weight)
    w = t.get_window_extent(renderer=fig.canvas.get_renderer()).width / fig.dpi
    t.remove()
    return w


def bar_path(width, centre, half, rx, ry):
    """Bar from x = 0 with a square baseline end and a rounded data end."""
    k = 0.5523  # cubic Bezier approximation of a quarter ellipse
    rx = min(rx, width / 2)
    top, bot, w = centre - half, centre + half, width
    verts = [
        (0, top), (w - rx, top),
        (w - rx + k * rx, top), (w, top + ry - k * ry), (w, top + ry),
        (w, bot - ry),
        (w, bot - ry + k * ry), (w - rx + k * rx, bot), (w - rx, bot),
        (0, bot), (0, top),
    ]
    codes = [MPath.MOVETO, MPath.LINETO,
             MPath.CURVE4, MPath.CURVE4, MPath.CURVE4,
             MPath.LINETO,
             MPath.CURVE4, MPath.CURVE4, MPath.CURVE4,
             MPath.LINETO, MPath.CLOSEPOLY]
    return MPath(verts, codes)


def draw(spec):
    rows, panels = spec["rows"], spec["panels"]
    n = len(rows)

    # Vertical layout, inches from the top.
    y = MARGIN_TOP
    y_title = y; y += lh(TITLE) + 0.04
    y_sub = y; y += lh(SUB) + 0.18
    y_leg = y; y += lh(LEGEND) + 0.34
    y_panel = y; y += lh(PANEL) + 0.08
    y_axes = y; y += n * ROW_PITCH
    y += TICK_BAND
    if spec["note"]:
        y_note = y + 0.16
        y += 0.16 + lh(NOTE)
    fig_h = y + MARGIN_BOTTOM

    fig = plt.figure(figsize=(FIG_W, fig_h), dpi=100, facecolor="white")
    inch = fig.dpi_scale_trans

    def put(x, y_top, s, size, **kw):
        kw.setdefault("color", INK)
        kw.setdefault("va", "top")
        return fig.text(x, fig_h - y_top, s, fontsize=size, transform=inch, **kw)

    put(MARGIN_X, y_title, spec["title"], TITLE, fontweight="semibold")
    put(MARGIN_X, y_sub, spec["subtitle"], SUB, color=MUTED)

    x = MARGIN_X
    yc = fig_h - y_leg - lh(LEGEND) / 2
    for label, colour in spec["legend"]:
        fig.add_artist(FancyBboxPatch(
            (x, yc - SWATCH / 2), SWATCH, SWATCH, transform=inch,
            boxstyle="round,pad=0,rounding_size=0.035", fc=colour, ec="none"))
        fig.text(x + SWATCH + 0.10, yc, label, fontsize=LEGEND, color=INK,
                 va="center_baseline", transform=inch)
        x += SWATCH + 0.10 + text_width(fig, label, LEGEND) + 0.42
    legend_right = x - 0.42

    # Horizontal layout: row labels once, on the left; panels share the x scale.
    lab_w = max(text_width(fig, r, ROW) for r, _ in rows)
    x_ax = [MARGIN_X + lab_w + LABEL_GAP]
    ax_w = (FIG_W - MARGIN_R - x_ax[0] - PANEL_GAP) / 2
    x_ax.append(x_ax[0] + ax_w + PANEL_GAP)
    ax_h = n * ROW_PITCH

    for i, (label, _) in enumerate(rows):
        put(x_ax[0] - LABEL_GAP, y_axes + (i + 0.5) * ROW_PITCH, label, ROW,
            ha="right", va="center_baseline")

    rx = RADIUS * spec["xmax"] / ax_w
    ry = RADIUS / ROW_PITCH
    half = BAR_H / ROW_PITCH / 2
    value_labels, axes = [], []
    for p, ((panel_title, values), xa) in enumerate(zip(panels, x_ax)):
        ax = fig.add_axes([xa / FIG_W, (fig_h - y_axes - ax_h) / fig_h,
                           ax_w / FIG_W, ax_h / fig_h])
        axes.append(ax)
        ax.set_xlim(0, spec["xmax"])
        ax.set_ylim(n - 0.5, -0.5)
        ax.set_facecolor("none")
        for side in ax.spines.values():
            side.set_visible(False)
        ax.set_yticks([])
        ax.set_xticks([t for t, _ in spec["ticks"]], [s for _, s in spec["ticks"]])
        ax.tick_params(axis="x", length=0, pad=8, labelsize=TICK, labelcolor=MUTED)
        for t, _ in spec["ticks"][1:]:
            ax.axvline(t, color=GRID, lw=1.0, zorder=0)
        ax.axvline(0, color=BASELINE, lw=1.5, zorder=3)

        put(xa, y_panel, panel_title, PANEL, fontweight="semibold")

        for i, ((value, text), (_, colour)) in enumerate(zip(values, rows)):
            ax.add_patch(PathPatch(bar_path(value, i, half, rx, ry),
                                   fc=colour, ec="none", zorder=2))
            value_labels.append((p, ax.annotate(
                text, xy=(value, i), xytext=(VALUE_PAD * 72, 0),
                textcoords="offset points", ha="left", va="center_baseline",
                fontsize=VALUE, fontweight="semibold", color=INK,
                annotation_clip=False)))

    if spec["note"]:
        put(MARGIN_X, y_note, spec["note"], NOTE, color=MUTED)

    # Layout checks: nothing may run off the figure or into the next panel.
    r = fig.canvas.get_renderer()
    limit = FIG_W - 0.10
    problems = []
    for p, lbl in value_labels:
        right = lbl.get_window_extent(r).x1 / fig.dpi
        if (p == 0 and right > x_ax[1] - 0.15) or right > limit:
            problems.append(f"value label {lbl.get_text()!r} ends at {right:.2f} in")
    for t in fig.texts:
        right = t.get_window_extent(r).x1 / fig.dpi
        if right > limit:
            problems.append(f"text {t.get_text()!r} ends at {right:.2f} in")
    if legend_right > limit:
        problems.append(f"legend ends at {legend_right:.2f} in")
    if problems:
        raise SystemExit("Layout overflow:\n  " + "\n  ".join(problems))
    return fig


def main():
    plt.rcParams.update({
        "font.family": FONT,
        "pdf.fonttype": 42,       # embed TrueType, keep PDF text selectable
        "svg.fonttype": "path",   # outlines, so PowerPoint renders it exactly
        "svg.hashsalt": "abot-slide-charts",
    })
    OUT.mkdir(parents=True, exist_ok=True)
    for stem, spec in CHARTS.items():
        fig = draw(spec)
        fig.savefig(OUT / f"{stem}.png", dpi=300, facecolor="white")
        fig.savefig(OUT / f"{stem}.pdf", facecolor="white", metadata={"CreationDate": None})
        fig.savefig(OUT / f"{stem}.svg", facecolor="white", metadata={"Date": None})
        plt.close(fig)
        print(f"wrote {stem}.png/.pdf/.svg")


if __name__ == "__main__":
    main()
