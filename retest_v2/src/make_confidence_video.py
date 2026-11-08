"""Video: how sure the LLM monitor (Qwen) says it is, and how often that sureness is right (calibration and Brier). Built only from D1 score files (real stated probabilities and ground truth).
Usage: make_confidence_video.py"""
import csv
import glob
import json
import math
import os
import subprocess

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import animation

HERE = os.path.dirname(os.path.abspath(__file__))
RT = os.path.dirname(HERE)
OUT = os.path.join(RT, "videos", "keyakinan_ai_brier_replay.mp4")
BLUE, ORANGE, RED, GREEN, GREY = "#0072B2", "#E69F00", "#D55E00", "#009E73", "#777777"
FPS = 15
fmt = lambda v, d=3: ("%.*f" % (d, v)).replace(".", ",")
SEED = 20261108
TYPE_ID = {"TWIN_H": "kembar jujur", "SHARED_OK": "berbagi diungkapkan", "NEAR_H": "hampir-duplikat jujur", "NOSRC_SAME": "tanpa sumber, topik sama", "ADAPT_LEX_INJECT": "serangan injeksi kata"}


def load():
    rows = []
    for p in sorted(glob.glob(os.path.join(RT, "scores", "gemma_homog", "*_scores.jsonl"))):
        for line in open(p, encoding="utf-8"):
            r = json.loads(line)
            if r.get("failed"):
                continue
            v = r["llm"]["tp:qwen3.8-flash"]["report_only"].get("p_copying")
            if v is None or (isinstance(v, float) and math.isnan(v)):
                continue
            rows.append((float(v), int(r["copy_u"]), r["type"]))
    rng = np.random.default_rng(SEED)
    idx = rng.permutation(len(rows))
    return [rows[i] for i in idx]


def stats(rows):
    p = np.array([r[0] for r in rows])
    y = np.array([r[1] for r in rows])
    sure = (p <= 0.1) | (p >= 0.9)
    pred = (p >= 0.5).astype(int)
    wrong_sure = sure & (pred != y)
    types = {}
    for r, w in zip(rows, wrong_sure):
        if w:
            types[r[2]] = types.get(r[2], 0) + 1
    bins = [(0, 0.2), (0.2, 0.4), (0.4, 0.6), (0.6, 0.8), (0.8, 1.0001)]
    rel = []
    for a, b in bins:
        m = (p >= a) & (p < b)
        rel.append((a, b, int(m.sum()), float(p[m].mean()) if m.any() else float("nan"), float(y[m].mean()) if m.any() else float("nan")))
    return dict(p=p, y=y, sure=sure, mid=((p > 0.3) & (p < 0.7)), brier=float(((p - y) ** 2).mean()), brier_const=float(((y.mean() - y) ** 2).mean()), types=types, rel=rel, wrong_sure=int(wrong_sure.sum()), n_sure=int(sure.sum()))


def save_csv(s):
    path = os.path.join(RT, "results", "gemma_homog", "kalibrasi_keyakinan_qwen_D1.csv")
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["bin_keyakinan_dari", "bin_keyakinan_sampai", "n", "rata_rata_keyakinan_dinyatakan", "laju_salinan_sebenarnya"])
        for a, b, n, c, rate in s["rel"]:
            w.writerow([a, min(b, 1.0), n, "" if n == 0 else round(c, 4), "" if n == 0 else round(rate, 4)])
        w.writerow([])
        w.writerow(["ukuran", "nilai"])
        w.writerow(["n_penilaian", len(s["p"])])
        w.writerow(["brier", round(s["brier"], 4)])
        w.writerow(["brier_tebakan_50_50", 0.25])
        w.writerow(["brier_tebakan_konstan_prevalensi", round(s["brier_const"], 4)])
        w.writerow(["porsi_sangat_yakin_(<=0.1_atau_>=0.9)", round(float(s["sure"].mean()), 4)])
        w.writerow(["porsi_ragu_(0.3-0.7)", round(float(s["mid"].mean()), 4)])
        w.writerow(["sangat_yakin_tapi_salah", s["wrong_sure"]])
        w.writerow(["sangat_yakin_total", s["n_sure"]])


def main():
    rows = load()
    s = stats(rows)
    save_csv(s)
    N = len(rows)
    T = {"title": 6, "hist": 18, "rel": 16, "brier": 16, "wrong": 14, "end": 14}
    starts, acc = {}, 0
    for k, v in T.items():
        starts[k] = acc
        acc += v
    total = acc * FPS
    fig = plt.figure(figsize=(12.8, 7.2), dpi=100)
    p, y = s["p"], s["y"]
    run_brier = np.cumsum((p - y) ** 2) / np.arange(1, N + 1)
    edges = np.linspace(0, 1, 11)

    def scene(f):
        t = f / FPS
        for k in T:
            if starts[k] <= t < starts[k] + T[k]:
                return k, (t - starts[k]) / T[k]
        return "end", 1.0

    def frame(f):
        fig.clf()
        k, q = scene(f)
        if k == "title":
            fig.text(0.5, 0.64, "Seberapa yakin AI, dan seberapa benar yakinnya?", ha="center", fontsize=30, weight="bold")
            fig.text(0.5, 0.50, "Sebuah monitor AI (Qwen) menilai %d pasang laporan." % N, ha="center", fontsize=20)
            fig.text(0.5, 0.42, "Tiap kali ia menyebut peluang 0 sampai 1 bahwa laporan kedua menyalin yang pertama.", ha="center", fontsize=17)
            fig.text(0.5, 0.34, "Kunci jawabannya kita tahu, jadi keyakinannya bisa diukur.", ha="center", fontsize=17)
            fig.text(0.5, 0.12, "Data asli uji konfirmatori D1 (agen Gemma, 5 replikasi). Urutan kasus diacak tetap.", ha="center", fontsize=12, color=GREY)
        elif k == "hist":
            n_show = max(1, int(q * N))
            ax = fig.add_axes([0.08, 0.14, 0.62, 0.68])
            pp, yy = p[:n_show], y[:n_show]
            c0, _ = np.histogram(pp[yy == 0], bins=edges)
            c1, _ = np.histogram(pp[yy == 1], bins=edges)
            ctr = (edges[:-1] + edges[1:]) / 2
            ax.bar(ctr, c0, width=0.085, color=BLUE, label="sebenarnya BUKAN salinan")
            ax.bar(ctr, c1, width=0.085, bottom=c0, color=ORANGE, label="sebenarnya salinan")
            ax.set_xlabel("Keyakinan yang dinyatakan AI: peluang 'ini salinan'", fontsize=15)
            ax.set_ylabel("jumlah jawaban", fontsize=15)
            ax.set_xlim(0, 1)
            ax.set_ylim(0, max(60, 1.1 * (c0 + c1).max()) if n_show > 5 else 60)
            ax.legend(fontsize=13, frameon=False, loc="upper center")
            ax.tick_params(labelsize=13)
            ax.spines[["top", "right"]].set_visible(False)
            fig.text(0.08, 0.92, "Jawaban AI menumpuk di ujung: hampir selalu 'sangat yakin'", fontsize=22, weight="bold")
            sure_now = float(((pp <= 0.1) | (pp >= 0.9)).mean()) * 100
            mid_now = float(((pp > 0.3) & (pp < 0.7)).mean()) * 100
            fig.text(0.74, 0.62, "Kasus dinilai: %d" % n_show, fontsize=17)
            fig.text(0.74, 0.54, "Sangat yakin\n(<=0,1 atau >=0,9):", fontsize=15)
            fig.text(0.74, 0.44, "%.0f%%" % sure_now, fontsize=34, weight="bold", color=RED)
            fig.text(0.74, 0.33, "Ragu-ragu (0,3 sampai 0,7):", fontsize=14)
            fig.text(0.74, 0.25, ("%.1f%%" % mid_now).replace(".", ","), fontsize=26, weight="bold", color=GREEN)
        elif k == "rel":
            ax = fig.add_axes([0.08, 0.14, 0.50, 0.68])
            ax.plot([0, 1], [0, 1], "--", color=GREY, lw=1.5)
            ax.text(0.52, 0.42, "yakin = benar\n(garis sempurna)", color=GREY, fontsize=13, rotation=40)
            shown = int(len([r for r in s["rel"] if r[2] > 0]) * min(1.0, q * 1.5) + 0.999)
            xs = [r[3] for r in s["rel"] if r[2] > 0][:shown]
            ys = [r[4] for r in s["rel"] if r[2] > 0][:shown]
            ns = [r[2] for r in s["rel"] if r[2] > 0][:shown]
            ax.scatter(xs, ys, s=[60 + 1.2 * n for n in ns], color=RED, zorder=5, alpha=0.85)
            for xv, yv, nv in zip(xs, ys, ns):
                if nv < 10:
                    continue
                ax.annotate("AI menyatakan %.0f%%\nkenyataan %.0f%% (n=%d)" % (100 * xv, 100 * yv, nv), (xv, yv), textcoords="offset points", xytext=(-190 if xv > 0.5 else 22, -60 if xv > 0.5 else 18), fontsize=13)
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.set_xlabel("keyakinan yang dinyatakan AI", fontsize=15)
            ax.set_ylabel("yang benar-benar salinan", fontsize=15)
            ax.tick_params(labelsize=13)
            ax.spines[["top", "right"]].set_visible(False)
            fig.text(0.08, 0.92, "Keyakinan AI dibandingkan dengan kenyataan", fontsize=24, weight="bold")
            if q > 0.55:
                hi = [r for r in s["rel"] if r[2] > 0][-1]
                fig.text(0.63, 0.62, "Saat AI menyatakan\nhampir pasti salinan\n(rata-rata %.0f%% yakin)," % (100 * hi[3]), fontsize=17)
                fig.text(0.63, 0.40, "yang benar-benar\nsalinan hanya", fontsize=17)
                fig.text(0.63, 0.24, "%.0f%%" % (100 * hi[4]), fontsize=44, weight="bold", color=RED)
        elif k == "brier":
            n_show = max(2, int(q * N))
            ax = fig.add_axes([0.08, 0.14, 0.62, 0.68])
            ax.plot(np.arange(1, n_show + 1), run_brier[:n_show], color=RED, lw=3, label="skor Brier AI (berjalan)")
            ax.axhline(0.25, color=GREY, ls="--", label="0,25 = menebak 50/50")

            ax.axhline(s["brier_const"], color=BLUE, ls=":", lw=2, label="%s = tebakan konstan" % fmt(s["brier_const"]))

            ax.set_xlim(1, N)
            ax.set_ylim(0.15, 0.36)
            ax.set_xlabel("jumlah kasus dinilai", fontsize=15)
            ax.set_ylabel("Brier (makin kecil makin baik)", fontsize=15)
            ax.tick_params(labelsize=13)
            ax.legend(fontsize=13, frameon=False, loc="upper right")
            ax.spines[["top", "right"]].set_visible(False)
            fig.text(0.08, 0.92, "Skor Brier: mengukur seberapa tepat keyakinan AI", fontsize=22, weight="bold")
            fig.text(0.74, 0.55, "Brier AI", fontsize=17)
            fig.text(0.74, 0.43, fmt(run_brier[n_show - 1]), fontsize=40, weight="bold", color=RED)
            fig.text(0.74, 0.30, "0 = sempurna\n0,25 = menebak", fontsize=14, color=GREY)
        elif k == "wrong":
            ax = fig.add_axes([0.30, 0.14, 0.62, 0.66])
            items = sorted(s["types"].items(), key=lambda kv: kv[1])
            names = [TYPE_ID.get(a, a) for a, _ in items]
            vals = [b for _, b in items]
            ax.barh(names, [v * min(1.0, q * 1.4) for v in vals], color=RED)
            for i, v in enumerate(vals):
                if q > 0.7:
                    ax.text(v + 2, i, str(v), va="center", fontsize=15, weight="bold")
            ax.set_xlim(0, max(vals) * 1.2)
            ax.set_xlabel("jawaban 'sangat yakin' yang tidak cocok dengan kenyataan", fontsize=15)
            ax.tick_params(labelsize=14)
            ax.spines[["top", "right"]].set_visible(False)
            fig.text(0.05, 0.92, "Keyakinan tinggi yang tidak cocok dengan kenyataan: laporan jujur yang mirip dinilai salinan", fontsize=21, weight="bold")
            fig.text(0.05, 0.84, "Dari %d jawaban 'sangat yakin', %d tidak cocok dengan kenyataan." % (s["n_sure"], s["wrong_sure"]), fontsize=17)
        else:
            lines = ["Yang terukur pada uji ini:",
                     "- AI tidak hanya menjawab: ia menyatakan seberapa yakin (angka 0 sampai 1).",
                     "- Angka itu membawa informasi: kasus salinan diberi angka lebih tinggi",
                     "  daripada kasus jujur (AUROC 0,69; 0,5 = tebakan).",
                     "- Ketepatan keyakinan itu diukur dengan skor Brier: %s (0 = sempurna, 0,25 = menebak)." % fmt(s["brier"]),
                     "- Saat AI menyatakan sekitar 94% yakin, kenyataannya 70%.",
                     "",
                     "Batas:",
                     "- satu model (Qwen), satu prompt, satu korpus 109 dokumen; model lain berbeda",
                     "  (pembanding kecil Haiku, 97 butir: Brier 0,19);",
                     "- ini perilaku keyakinan yang terukur dari luar; uji ini tidak mengukur",
                     "  kesadaran atau isi batin."]
            fig.text(0.07, 0.92, "Kesimpulan", fontsize=30, weight="bold")
            y0 = 0.80
            for ln in lines:
                fig.text(0.07, y0, ln, fontsize=17 if not ln.endswith(":") else 19, weight="bold" if ln.endswith(":") else "normal")
                y0 -= 0.066
        return []

    writer = animation.FFMpegWriter(fps=FPS, codec="libx264", extra_args=["-pix_fmt", "yuv420p", "-crf", "24"])
    animation.FuncAnimation(fig, frame, frames=total, blit=False).save(OUT, writer=writer)
    dur = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", OUT], capture_output=True, text=True).stdout.strip()
    print("saved", OUT, "duration %.1f s" % float(dur), "size MB %.1f" % (os.path.getsize(OUT) / 1e6))


if __name__ == "__main__":
    main()
