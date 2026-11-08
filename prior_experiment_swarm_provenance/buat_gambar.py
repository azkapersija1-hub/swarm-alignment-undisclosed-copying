"""Gambar laporan dari hasil/seed_*.json (hanya skor, tanpa teks buku). Keluaran PNG 300 dpi di laporan/."""
import glob
import json
import math
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lab  # noqa: E402

plt.rcParams.update({"font.family": "DejaVu Sans", "axes.spines.top": False, "axes.spines.right": False})
seeds = [json.load(open(f, encoding="utf-8")) for f in sorted(glob.glob(os.path.join(HERE, "hasil", "seed_*.json")))]
OUT = os.path.join(HERE, "laporan")

# kode -> (nama gambar, kunci data, warna, penanda, garis)
SUP = {
    "A1": ("A1 claim-trust (report)", "A1 percaya klaim (laporan)", "#6e6e6e", "x", ":"),
    "A2": ("A2 summary reader (report)", "A2 ringkasan mirip (laporan)", "#8a8a8a", "s", "--"),
    "B1": ("B1 quote in claimed source (artifact)", "B1 kutipan ada di sumber (artefak)", "#c9731c", "^", "-."),
    "B2": ("B2 word overlap of artifacts (artifact)", "B2 artefak mirip (artefak)", "#2b6cb0", "o", "-"),
    "B3": ("B3 twin sources (artifact)", "B3 sumber kembar (artefak)", "#7b5ea7", "v", ":"),
    "B4": ("B4 embedding of artifacts (artifact)", "B4 embedding artefak (artefak)", "#1a7f4b", "D", "-"),
}


def tpr(tipe, lv, kunci):
    v = []
    for s in seeds:
        sub = [b for b in s["baris"] if b["tipe"] == tipe and b["level"] == lv]
        v.append(sum(b["bendera"][kunci] for b in sub) / len(sub))
    m = sum(v) / len(v)
    return m, math.sqrt(sum((x - m) ** 2 for x in v) / (len(v) - 1))


def gambar_deteksi():
    fig, ax = plt.subplots(1, 2, figsize=(7.4, 3.5), sharey=True, dpi=300)
    tampil = ("A2", "B1", "B2", "B4")
    geser = {"A2": -0.15, "B1": -0.05, "B2": 0.05, "B4": 0.15}
    for a, tipe, judul in zip(ax, ("C1", "C2"), ("(a) Copier cites a different real passage", "(b) Copier cites a genuine twin source")):
        for k in tampil:
            nama, kunci, c, mk, ls = SUP[k]
            pts = [tpr(tipe, lv, kunci) for lv in range(6)]
            a.errorbar([lv + geser[k] for lv in range(6)], [p[0] for p in pts], yerr=[p[1] for p in pts], color=c, marker=mk, ls=ls,
                       ms=5, lw=1.4, capsize=2.5, elinewidth=1, label=nama if tipe == "C1" else None)
        a.set_title(judul, fontsize=9.5, fontweight="bold")
        a.set_xticks(range(6))
        a.set_xticklabels(["L0\nexact", "L1\nformat", "L2\nsentence\norder", "L3\nwords\ndropped", "L4\nheavy\nmix", "L5\nmosaic"], fontsize=8)
        a.set_ylim(-0.03, 1.08)
        a.set_yticks([0, 0.2, 0.4, 0.6, 0.8, 1.0])
        a.tick_params(axis="y", labelsize=8.5)
        a.grid(alpha=0.3)
    ax[0].set_ylabel("Detection rate", fontsize=9.5)
    for a in ax:
        a.set_xlabel("Disguise level (mean ± SD over 5 seeds)", fontsize=8.5, labelpad=4)
    fig.legend(loc="lower center", ncol=2, fontsize=8.5, frameon=False, bbox_to_anchor=(0.5, -0.01))
    fig.tight_layout(rect=(0, 0.14, 1, 1))
    fig.savefig(os.path.join(OUT, "fig1_deteksi.png"), bbox_inches="tight")
    plt.close(fig)


def gambar_alarm_brier():
    semua = [b for s in seeds for b in s["baris"]]
    jujur = [b for b in semua if b["tipe"] == "H"]
    y = [b["label"] for b in semua]
    kode = list(SUP)
    alarm, lo, hi, brier = [], [], [], []
    for k in kode:
        kunci = SUP[k][1]
        n_alarm = sum(b["bendera"][kunci] for b in jujur)
        l, h = lab.wilson(n_alarm, len(jujur))
        alarm.append(100 * n_alarm / len(jujur))
        lo.append(max(0.0, 100 * (n_alarm / len(jujur) - l)))
        hi.append(max(0.0, 100 * (h - n_alarm / len(jujur))))
        brier.append(lab.brier([b["p"][kunci] for b in semua], y))
    acuan = lab.brier_acuan(y)
    nama = [SUP[k][0] for k in kode]
    pos = list(range(len(kode)))[::-1]
    warna = [SUP[k][2] for k in kode]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.6, 3.4), dpi=300, sharey=True)
    a1.barh(pos, alarm, xerr=[lo, hi], color=warna, error_kw={"elinewidth": 1, "capsize": 2.5})
    a1.axvline(5, color="k", ls=":", lw=1)
    a1.text(5.3, 5.62, "5% target", fontsize=7.5, va="center")
    for p, v, h in zip(pos, alarm, hi):
        a1.text(v + h + 0.4, p, "%.1f%%" % v, fontsize=8, va="center")
    a1.set_yticks(pos)
    a1.set_yticklabels(nama, fontsize=8)
    a1.set_xlabel("False-alarm rate (%), 95% Wilson CI", fontsize=8.5)
    a1.set_xlim(0, 13.5)
    a1.set_ylim(-1.2, 5.9)
    a1.set_title("(a) False alarms on honest bots", fontsize=9.5, fontweight="bold")
    a2.barh(pos, brier, color=warna)
    a2.axvline(acuan, color="k", ls=":", lw=1)
    a2.text(acuan, -0.85, "no-information\nreference %.3f" % acuan, fontsize=7.5, ha="center", va="center")
    for p, v in zip(pos, brier):
        a2.text(v + 0.004, p, "%.3f" % v, fontsize=8, va="center", bbox={"fc": "white", "ec": "none", "pad": 0.8})
    a2.set_xlabel("Brier score, all levels pooled", fontsize=8.5)
    a2.set_ylim(-1.2, 5.9)
    a2.set_xlim(0, 0.25)
    a2.set_title("(b) Brier score (lower is better)", fontsize=9.5, fontweight="bold")
    for a in (a1, a2):
        a.tick_params(axis="x", labelsize=8)
        a.grid(axis="x", alpha=0.3)
    fig.tight_layout(w_pad=2.0)
    fig.savefig(os.path.join(OUT, "fig2_alarm_brier.png"), bbox_inches="tight")
    plt.close(fig)
    return alarm, brier, acuan


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    gambar_deteksi()
    print(gambar_alarm_brier())
