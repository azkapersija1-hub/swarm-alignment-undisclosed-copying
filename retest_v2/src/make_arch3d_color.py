"""Architecture schematic in the isometric-box style of the chatbot figure (fig_arch_bw 3d), rebuilt in matplotlib with soft base colours and a lighter shadow.
Same components and arrows as the reviewed prompt3 script (no component added). Usage: make_arch3d_color.py [en|id]"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Circle, FancyBboxPatch, Polygon, Rectangle

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(os.path.dirname(HERE), "results", "figures")
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "svg.fonttype": "none"})
INK = "#111111"
D, DY = 1.2, 0.95                       # extrusion offsets
# base colours: (front, top, side)
PAL = {"grey": ("#ECECEC", "#F7F7F7", "#BDBDBD"), "blue": ("#D3E5F4", "#E8F2FA", "#9EC3E1"), "green": ("#D5EFE5", "#E9F7F1", "#9AD2BC"),
       "purple": ("#E6DEF1", "#F2EDF8", "#C0B1D8"), "orange": ("#FBE9C8", "#FDF4E3", "#EBC98A"), "tan": ("#F3E9B8", "#FAF5DB", "#DCCB7E")}
L = {
    "en": {"src": "Source documents\n(109 docs, 17 domains)", "gt": "Ground truth: A copying,\nB non-independent evidence,\nC false provenance claim", "A": "Agent A (LLM)", "B": "Agent B (LLM)",
           "rep": "Reports A and B\n+ cited sources", "led": "Controller ledger\n(SHA-256 hash chain)", "f": "Formula monitors", "l": "LLM monitor", "g": "Log monitor",
           "m": "AUROC, recall,\nFPR, Brier", "copy": "copy / paraphrase\n(instructed)", "c1": "Inputs", "c2": "Agents", "c3": "Artifacts", "c4": "Monitors and scoring"},
    "id": {"src": "Dokumen sumber\n(109 dokumen, 17 domain)", "gt": "Kebenaran dasar: A salinan,\nB bukti tidak independen,\nC klaim asal-usul palsu", "A": "Agen A (LLM)", "B": "Agen B (LLM)",
           "rep": "Laporan A dan B\n+ sumber yang dikutip", "led": "Ledger controller\n(rantai hash SHA-256)", "f": "Monitor rumus", "l": "Monitor LLM", "g": "Monitor log",
           "m": "AUROC, recall,\nFPR, Brier", "copy": "salin / parafrase\n(diperintahkan)", "c1": "Masukan", "c2": "Agen", "c3": "Artefak", "c4": "Monitor dan penilaian"},
}


def panel(ax, x0, x1, y0, y1, label):
    sk = 2.2
    ax.add_patch(Polygon([(x0, y0), (x1, y0 + 1.2), (x1 + sk, y1 + 1.2), (x0 + sk, y1)], closed=True, fc="#FAFAFA", ec="#9A9A9A", lw=0.8, ls=(0, (4, 3)), zorder=0))
    ax.text((x0 + x1) / 2 + sk / 2, y1 + 1.9, label, ha="center", va="bottom", fontsize=9, fontweight="bold", color="#444444")


def bot(ax, cx, cy, s=2.2):
    h = s / 2
    ax.add_patch(FancyBboxPatch((cx - h, cy - h), s, s, boxstyle="round,pad=0,rounding_size=0.45", fc="white", ec=INK, lw=1.1, zorder=7))
    for dx in (-0.22 * s, 0.22 * s):
        ax.add_patch(Circle((cx + dx, cy + 0.04 * s), 0.09 * s, fc=INK, ec="none", zorder=8))
    ax.add_line(Line2D([cx, cx], [cy + h, cy + h + 0.36 * s], color=INK, lw=1.1, zorder=7))
    ax.add_patch(Circle((cx, cy + h + 0.44 * s), 0.09 * s, fc=INK, ec="none", zorder=8))


def box(ax, x, y, w, h, text, col, icon=False):
    f, t, s = PAL[col]
    ax.add_patch(Polygon([(x + 0.7, y - 0.7), (x + w + D + 0.7, y - 0.7), (x + w + D + 0.7, y + h + DY - 0.7), (x + 0.7, y + h - 0.7)], closed=True, fc="#000000", alpha=0.07, ec="none", zorder=1))
    ax.add_patch(Polygon([(x, y + h), (x + D, y + h + DY), (x + w + D, y + h + DY), (x + w, y + h)], closed=True, fc=t, ec=INK, lw=1.1, zorder=2))
    ax.add_patch(Polygon([(x + w, y), (x + w + D, y + DY), (x + w + D, y + h + DY), (x + w, y + h)], closed=True, fc=s, ec=INK, lw=1.1, zorder=2))
    ax.add_patch(Rectangle((x, y), w, h, fc=f, ec=INK, lw=1.2, zorder=3))
    if icon:
        bot(ax, x + 2.5, y + h / 2 - 0.2)
        tx = x + 4.2 + (w - 4.2) / 2
    else:
        tx = x + w / 2
    ax.text(tx, y + h / 2, text, ha="center", va="center", fontsize=9, color=INK, zorder=9, linespacing=1.25)
    return dict(x=x, y=y, w=w, h=h, r=x + w + D, cx=x + w / 2, cy=y + h / 2)


def arrow(ax, pts, dashed=False):
    ls = (0, (4, 3)) if dashed else "-"
    ax.add_line(Line2D([p[0] for p in pts], [p[1] for p in pts], color=INK, lw=1.2, ls=ls, zorder=6, solid_capstyle="butt"))
    (x1, y1), (x2, y2) = pts[-2], pts[-1]
    ax.annotate("", xy=(x2, y2), xytext=(x1 + (x2 - x1) * 0.0, y1 + (y2 - y1) * 0.0), arrowprops=dict(arrowstyle="-|>", color=INK, lw=1.2, linestyle=ls, shrinkA=0, shrinkB=0, mutation_scale=11), zorder=6)
    ax.add_patch(Circle(pts[0], 0.32, fc=INK, ec="none", zorder=8))


def draw(lang):
    t = L[lang]
    fig, ax = plt.subplots(figsize=(14.4, 6.8), dpi=200)
    ax.set_xlim(0, 109)
    ax.set_ylim(0, 52)
    ax.set_aspect("equal")
    ax.axis("off")
    panel(ax, 1.0, 29.5, 2.0, 38.0, t["c1"])
    panel(ax, 31.0, 49.0, 16.0, 46.0, t["c2"])
    panel(ax, 53.0, 74.0, 15.5, 44.0, t["c3"])
    panel(ax, 77.0, 100.5, 2.5, 47.0, t["c4"])
    src = box(ax, 3.0, 26.0, 20.0, 8.0, t["src"], "grey")
    gt = box(ax, 3.0, 5.0, 24.5, 9.0, t["gt"], "grey")
    a = box(ax, 32.0, 34.0, 15.5, 7.0, t["A"], "blue", True)
    b = box(ax, 32.0, 19.5, 15.5, 7.0, t["B"], "blue", True)
    rep = box(ax, 54.5, 32.0, 18.0, 8.0, t["rep"], "green")
    led = box(ax, 54.5, 18.5, 18.0, 8.0, t["led"], "purple")
    fm = box(ax, 78.5, 39.0, 19.0, 6.0, t["f"], "orange")
    lm = box(ax, 78.5, 29.5, 19.0, 6.5, t["l"], "orange", True)
    gm = box(ax, 78.5, 20.5, 19.0, 6.0, t["g"], "purple")
    me = box(ax, 78.5, 5.0, 19.0, 8.0, t["m"], "tan")
    arrow(ax, [(src["r"], src["cy"] + 1.5), (a["x"], a["cy"])])
    arrow(ax, [(src["r"], src["cy"] - 1.5), (b["x"], b["cy"])])
    arrow(ax, [(a["cx"], a["y"]), (b["cx"], b["y"] + b["h"])], dashed=True)
    ax.text(a["cx"] + 0.9, (a["y"] + b["y"] + b["h"]) / 2, t["copy"], ha="left", va="center", fontsize=8.5, color=INK, bbox=dict(boxstyle="square,pad=0.2", fc="white", ec="none"), zorder=9)
    arrow(ax, [(a["r"], a["cy"] + 1.0), (rep["x"], rep["cy"] + 1.5)])
    arrow(ax, [(b["r"], b["cy"] + 1.2), (rep["x"], rep["cy"] - 1.5)])
    arrow(ax, [(a["r"], a["cy"] - 1.2), (led["x"], led["cy"] + 1.5)])
    arrow(ax, [(b["r"], b["cy"] - 1.0), (led["x"], led["cy"] - 1.5)])
    arrow(ax, [(rep["r"], rep["cy"] + 1.5), (fm["x"], fm["cy"])])
    arrow(ax, [(rep["r"], rep["cy"] - 1.5), (lm["x"], lm["cy"])])
    arrow(ax, [(led["r"], led["cy"]), (gm["x"], gm["cy"])])
    arrow(ax, [(gm["cx"], gm["y"]), (me["cx"], me["y"] + me["h"] + DY)])
    arrow(ax, [(lm["r"], lm["cy"]), (103.0, lm["cy"]), (103.0, 16.4), (me["x"] + me["w"] - 5.5, 16.4), (me["x"] + me["w"] - 5.5, me["y"] + me["h"] + DY)])
    arrow(ax, [(fm["r"], fm["cy"]), (105.5, fm["cy"]), (105.5, 15.0), (me["x"] + me["w"] - 2.5, 15.0), (me["x"] + me["w"] - 2.5, me["y"] + me["h"] + DY)])
    arrow(ax, [(gt["r"], gt["cy"]), (me["x"], me["cy"])], dashed=True)
    fig.subplots_adjust(left=0.01, right=0.99, top=0.97, bottom=0.02)
    for ext in ("png", "svg"):
        fig.savefig(os.path.join(FIG, "fig0c_arch3d_color_%s.%s" % (lang, ext)), dpi=200, facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    os.makedirs(FIG, exist_ok=True)
    for lg in (sys.argv[1:] or ["en", "id"]):
        draw(lg)
    print("saved", sorted(f for f in os.listdir(FIG) if f.startswith("fig0c")))
