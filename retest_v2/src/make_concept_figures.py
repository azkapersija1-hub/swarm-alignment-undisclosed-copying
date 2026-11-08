"""Concept figures drawn from the real design (no invented components). Usage: make_concept_figures.py [en|id]
Fig 0a: testbed architecture. Fig 0b: the five communication topologies of Track 2 (agent 1 holds the planted claim, agent 3 can verify it against its own source)."""
import math
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(os.path.dirname(HERE), "results", "figures")
BLUE, ORANGE, GREEN, GREY, RED, PURPLE, INK = "#0072B2", "#E69F00", "#009E73", "#8c8c8c", "#D55E00", "#6a3d9a", "#222222"

TXT = {
    "en": {
        "src": "Source documents\n109 course documents\n17 domains",
        "A": "Agent A\nwrites an evidence report",
        "B": "Agent B\nhonest, or instructed\nto copy A",
        "copy": "copy / paraphrase\n(instructed)",
        "art": "Artifacts seen by monitors",
        "rep": "Reports A and B\n+ cited sources",
        "led": "Controller ledger\nSHA-256 hash chain\n(+ anchored head)",
        "mon": "Monitors (offline, one pass)",
        "m1": "Formula monitors\ncosine, F9b, F11x, H1-H10",
        "m2": "LLM monitor\n(reads report; with sources)",
        "m3": "Log monitor\nFLAG / CLEAR / ABSTAIN",
        "gt": "Ground truth (3 targets)\nA: undisclosed copying\nB: non-independent evidence\nC: false provenance claim",
        "met": "Scored with\nAUROC, recall, FPR, Brier",
        "t_arch": "Test bed: agents write reports, a controller logs, monitors audit afterwards",
        "t_top": "Communication topologies of the propagation test (Track 2)",
        "plant": "planted claim", "ver": "can verify", "vrole": "verifier role", "none": "no links",
    },
    "id": {
        "src": "Dokumen sumber\n109 dokumen materi\n17 domain",
        "A": "Agen A\nmenulis laporan bukti",
        "B": "Agen B\njujur, atau diperintah\nmenyalin A",
        "copy": "salin / parafrase\n(diperintahkan)",
        "art": "Artefak yang dilihat monitor",
        "rep": "Laporan A dan B\n+ sumber yang dikutip",
        "led": "Ledger controller\nrantai hash SHA-256\n(+ kepala hash berjangkar)",
        "mon": "Monitor (offline, sekali jalan)",
        "m1": "Monitor rumus\nkosinus, F9b, F11x, H1-H10",
        "m2": "Monitor LLM\n(baca laporan; dengan sumber)",
        "m3": "Monitor log\nFLAG / CLEAR / ABSTAIN",
        "gt": "Kebenaran dasar (3 target)\nA: salinan tanpa pengungkapan\nB: bukti tidak independen\nC: klaim asal-usul palsu",
        "met": "Dinilai dengan\nAUROC, recall, FPR, Brier",
        "t_arch": "Bed uji: agen menulis laporan, controller mencatat, monitor mengaudit sesudahnya",
        "t_top": "Topologi komunikasi pada uji propagasi (Track 2)",
        "plant": "klaim tertanam", "ver": "bisa memverifikasi", "vrole": "peran verifikator", "none": "tanpa tautan",
    },
}


def box(ax, x, y, w, h, text, color, fs=9, tc=INK):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08", fc=color, ec=INK, lw=1.0, alpha=0.18))
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08", fc="none", ec=color, lw=1.6))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, color=tc, linespacing=1.25)


def arrow(ax, p, q, color=INK, style="-", rad=0.0, lw=1.4, text=None, tpos=None, fs=8):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=12, lw=lw, color=color, linestyle=style, connectionstyle="arc3,rad=%s" % rad))
    if text:
        ax.text(tpos[0], tpos[1], text, ha="center", va="center", fontsize=fs, color=color, linespacing=1.2,
                bbox=dict(fc="white", ec="none", pad=1.2, alpha=0.9))


def fig_architecture(lang):
    t = TXT[lang]
    fig, ax = plt.subplots(figsize=(13.2, 6.2))
    ax.set_xlim(0, 13.2)
    ax.set_ylim(0, 6.2)
    ax.axis("off")
    box(ax, 0.2, 2.35, 2.0, 1.5, t["src"], GREY)
    box(ax, 3.2, 3.9, 2.3, 1.3, t["A"], BLUE)
    box(ax, 3.2, 1.0, 2.3, 1.3, t["B"], ORANGE)
    arrow(ax, (2.25, 3.4), (3.15, 4.4))
    arrow(ax, (2.25, 2.8), (3.15, 1.8))
    arrow(ax, (4.35, 3.85), (4.35, 2.35), color=RED, style="--", text=t["copy"], tpos=(4.35, 3.1))
    box(ax, 6.6, 3.55, 2.2, 1.35, t["rep"], GREEN)
    box(ax, 6.6, 0.95, 2.2, 1.45, t["led"], PURPLE)
    ax.text(7.7, 5.2, t["art"], ha="center", fontsize=9, fontweight="bold", color=INK)
    arrow(ax, (5.55, 4.5), (6.55, 4.3))
    arrow(ax, (5.55, 1.7), (6.55, 3.8), rad=-0.15)
    arrow(ax, (5.55, 1.5), (6.55, 1.6), color=PURPLE)
    ax.text(10.35, 5.55, t["mon"], ha="center", fontsize=9, fontweight="bold", color=INK)
    box(ax, 9.4, 4.2, 1.95, 1.1, t["m1"], BLUE, fs=8)
    box(ax, 9.4, 2.85, 1.95, 1.1, t["m2"], ORANGE, fs=8)
    box(ax, 9.4, 1.5, 1.95, 1.1, t["m3"], PURPLE, fs=8)
    for y in (4.75, 3.4):
        arrow(ax, (8.85, 4.2), (9.35, y), lw=1.1)
    arrow(ax, (8.85, 1.9), (9.35, 2.05), color=PURPLE, lw=1.1)
    box(ax, 11.75, 3.2, 1.35, 1.95, t["met"].replace(", ", ",\n"), GREEN, fs=8)
    for y, ty in ((4.75, 4.85), (3.4, 4.2), (2.05, 3.55)):
        arrow(ax, (11.4, y), (11.7, ty), lw=1.0)
    box(ax, 9.4, 0.1, 3.7, 1.0, t["gt"], GREY, fs=7.5)
    arrow(ax, (12.4, 1.15), (12.4, 3.15), color=GREY, style="--", lw=1.2)
    ax.text(0.2, 6.0, t["t_arch"], fontsize=10.5, fontweight="bold", color=INK)
    fig.tight_layout()
    for ext in ("png", "svg"):
        fig.savefig(os.path.join(FIG, "fig0a_architecture_%s.%s" % (lang, ext)), dpi=170)
    plt.close(fig)


TOPOS = {
    "isolated": [],
    "chain": [(1, 2), (2, 3), (3, 4)],
    "star": [(1, 2), (1, 3), (1, 4)],
    "full": [(1, 2), (1, 3), (1, 4), (2, 3), (2, 4), (3, 4)],
    "chain_verifier": [(1, 2), (2, 3), (3, 4)],
}


def fig_topologies(lang):
    t = TXT[lang]
    fig, axes = plt.subplots(1, 5, figsize=(14, 3.4))
    pos = {1: (-1, 1), 2: (1, 1), 3: (1, -1), 4: (-1, -1)}
    for ax, (name, edges) in zip(axes, TOPOS.items()):
        ax.set_xlim(-1.9, 1.9)
        ax.set_ylim(-1.9, 1.9)
        ax.set_aspect("equal")
        ax.axis("off")
        ax.set_title(name, fontsize=10, color=INK)
        for a, b in edges:
            (x1, y1), (x2, y2) = pos[a], pos[b]
            d = math.hypot(x2 - x1, y2 - y1)
            ux, uy = (x2 - x1) / d, (y2 - y1) / d
            ax.add_patch(FancyArrowPatch((x1 + 0.3 * ux, y1 + 0.3 * uy), (x2 - 0.3 * ux, y2 - 0.3 * uy), arrowstyle="-|>", mutation_scale=11, lw=1.3, color=INK,
                                         connectionstyle="arc3,rad=0.12"))
        if not edges:
            ax.text(0, 0, t["none"], ha="center", va="center", fontsize=8, color=GREY)
        for i, (x, y) in pos.items():
            ring = GREEN if i == 3 else (PURPLE if (name == "chain_verifier" and i == 4) else INK)
            fill = ORANGE if i == 1 else "white"
            ax.add_patch(Circle((x, y), 0.3, fc=fill, ec=ring, lw=2.2 if ring != INK else 1.2))
            ax.text(x, y, str(i), ha="center", va="center", fontsize=10, color=INK)
    handles = [Circle((0, 0), 1, fc=ORANGE, ec=INK), Circle((0, 0), 1, fc="white", ec=GREEN, lw=2), Circle((0, 0), 1, fc="white", ec=PURPLE, lw=2)]
    fig.legend(handles, ["1: " + t["plant"], "3: " + t["ver"], "4: " + t["vrole"] + " (chain_verifier)"], loc="lower center", ncol=3, fontsize=8, frameon=False)
    fig.suptitle(t["t_top"], fontsize=10.5, fontweight="bold", color=INK)
    fig.tight_layout(rect=(0, 0.07, 1, 0.94))
    for ext in ("png", "svg"):
        fig.savefig(os.path.join(FIG, "fig0b_topologies_%s.%s" % (lang, ext)), dpi=170)
    plt.close(fig)


def main():
    os.makedirs(FIG, exist_ok=True)
    langs = sys.argv[1:] or ["en", "id"]
    for lang in langs:
        fig_architecture(lang)
        fig_topologies(lang)
    print("saved concept figures:", sorted(f for f in os.listdir(FIG) if f.startswith("fig0")))


if __name__ == "__main__":
    main()
