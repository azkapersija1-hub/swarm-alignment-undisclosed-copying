"""Three-in-one video: how sure three AI models say they are (Haiku, Gemma, Qwen) judging the SAME 97 report pairs, and how precise that sureness is (Brier, calibration).
Data: D1 rep0 test split (97 items); Gemma and Qwen stated probabilities come from the score file, Haiku from the blind exploratory run. Everything is read from files.
Usage: make_confidence_3models_video.py"""
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
from sklearn.metrics import roc_auc_score

HERE = os.path.dirname(os.path.abspath(__file__))
RT = os.path.dirname(HERE)
OUT = os.path.join(RT, "videos", "keyakinan_3_model_brier_replay.mp4")
CSV_OUT = os.path.join(RT, "results", "gemma_homog", "perbandingan_tiga_model_keyakinan.csv")
FPS = 15
SEED = 20261108
BLUE, ORANGE, GREY = "#0072B2", "#E69F00", "#777777"
COL = {"Haiku": "#6a3d9a", "Gemma": "#009E73", "Qwen": "#D55E00"}
fmt = lambda v, d=3: ("%.*f" % (d, v)).replace(".", ",")
MODELS = ["Haiku", "Gemma", "Qwen"]


def pcop(o):
    v = o.get("p_copying") if o else None
    return None if v is None or (isinstance(v, float) and math.isnan(v)) else float(v)


def load():
    key = {json.loads(l)["id"]: json.loads(l) for l in open(os.path.join(RT, "haiku_monitor", "key", "key.jsonl"), encoding="utf-8")}
    ver = {json.loads(l)["id"]: json.loads(l) for l in open(os.path.join(RT, "haiku_monitor", "blind", "verdicts.jsonl"), encoding="utf-8")}
    sc = {}
    for l in open(os.path.join(RT, "scores", "gemma_homog", "rep0_gemma_homog_scores.jsonl"), encoding="utf-8"):
        r = json.loads(l)
        if not r.get("failed"):
            sc[r["scenario_id"]] = r
    P = {m: [] for m in MODELS}
    Y = []
    for i, k in key.items():
        r = sc[k["scenario_id"]]
        q = pcop(r["llm"]["tp:qwen3.8-flash"]["report_only"])
        g = pcop(r["llm"]["gemma4:31b-cloud"]["report_only"])
        if q is None or g is None:
            continue
        P["Haiku"].append(float(ver[i]["p_copying"]))
        P["Gemma"].append(g)
        P["Qwen"].append(q)
        Y.append(int(k["copy_u"]))
    rng = np.random.default_rng(SEED)
    order = rng.permutation(len(Y))
    return {m: np.array(P[m])[order] for m in MODELS}, np.array(Y)[order]


def larger_set():
    G, Q, Y = [], [], []
    for tag in ("gemma_homog", "qwen_homog", "deepseek_homog"):
        for l in open(os.path.join(RT, "scores", tag, "rep0_%s_scores.jsonl" % tag), encoding="utf-8"):
            r = json.loads(l)
            if r.get("failed") or "gemma4:31b-cloud" not in r["llm"]:
                continue
            g, q = pcop(r["llm"]["gemma4:31b-cloud"]["report_only"]), pcop(r["llm"]["tp:qwen3.8-flash"]["report_only"])
            if g is None or q is None:
                continue
            G.append(g)
            Q.append(q)
            Y.append(int(r["copy_u"]))
    G, Q, Y = np.array(G), np.array(Q), np.array(Y)
    return dict(n=len(Y), brier_g=float(((G - Y) ** 2).mean()), brier_q=float(((Q - Y) ** 2).mean()))


def metrics(P, Y):
    out = {}
    for m in MODELS:
        p = P[m]
        hi = p >= 0.8
        out[m] = dict(n=len(p), brier=float(((p - Y) ** 2).mean()), auroc=float(roc_auc_score(Y, p)), sure=float(((p <= 0.1) | (p >= 0.9)).mean()), mid=float(((p > 0.3) & (p < 0.7)).mean()),
                      stated_hi=float(p[hi].mean()), actual_hi=float(Y[hi].mean()), n_hi=int(hi.sum()), prevalence=float(Y.mean()), brier_const=float(((Y.mean() - Y) ** 2).mean()))
    return out


def save_csv(M, big):
    with open(CSV_OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["model", "n_butir_sama", "brier", "auroc", "porsi_sangat_yakin", "porsi_ragu_0.3_0.7", "keyakinan_rata2_saat_>=0.8", "kenyataan_salinan_saat_>=0.8", "n_saat_>=0.8"])
        for m in MODELS:
            d = M[m]
            w.writerow([m, d["n"], round(d["brier"], 4), round(d["auroc"], 4), round(d["sure"], 4), round(d["mid"], 4), round(d["stated_hi"], 4), round(d["actual_hi"], 4), d["n_hi"]])
        w.writerow([])
        w.writerow(["brier_tebakan_50_50", 0.25])
        w.writerow(["brier_tebakan_konstan_prevalensi_97_butir", round(M["Qwen"]["brier_const"], 4)])
        w.writerow(["himpunan_lebih_besar_Gemma_vs_Qwen_baris", big["n"]])
        w.writerow(["brier_Gemma_himpunan_besar", round(big["brier_g"], 4)])
        w.writerow(["brier_Qwen_himpunan_besar", round(big["brier_q"], 4)])
        w.writerow(["catatan", "Haiku: satu subagen, satu replikasi, 97 butir, eksploratori; Gemma menilai laporan yang ditulis Gemma sendiri di D1"])


def main():
    P, Y = load()
    M = metrics(P, Y)
    big = larger_set()
    save_csv(M, big)
    N = len(Y)
    T = {"title": 7, "hist": 24, "high": 16, "brier": 18, "score": 16, "end": 20}
    starts, acc = {}, 0
    for k, v in T.items():
        starts[k] = acc
        acc += v
    total = acc * FPS
    run = {m: np.cumsum((P[m] - Y) ** 2) / np.arange(1, N + 1) for m in MODELS}
    edges = np.linspace(0, 1, 11)
    ctr = (edges[:-1] + edges[1:]) / 2
    fig = plt.figure(figsize=(12.8, 7.2), dpi=100)

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
            fig.text(0.5, 0.66, "Tiga AI, soal yang sama:", ha="center", fontsize=32, weight="bold")
            fig.text(0.5, 0.56, "seberapa yakin mereka, dan seberapa tepat yakinnya?", ha="center", fontsize=28, weight="bold")
            fig.text(0.5, 0.42, "Haiku (Claude), Gemma, dan Qwen menilai %d pasang laporan yang sama." % N, ha="center", fontsize=19)
            fig.text(0.5, 0.34, "Tiap model menyebut peluang 0 sampai 1 bahwa laporan kedua menyalin yang pertama.", ha="center", fontsize=16)
            fig.text(0.5, 0.27, "Kunci jawaban diketahui, jadi ketepatan keyakinannya bisa diukur (skor Brier).", ha="center", fontsize=16)
            fig.text(0.5, 0.10, "Data asli uji D1, split uji, satu replikasi. Urutan kasus diacak tetap.", ha="center", fontsize=12, color=GREY)
        elif k == "hist":
            n_show = max(1, int(q * N))
            fig.text(0.04, 0.93, "Seberapa tegas jawaban masing-masing AI", fontsize=24, weight="bold")
            ymax = 0
            axes = []
            for i, m in enumerate(MODELS):
                ax = fig.add_axes([0.05 + i * 0.32, 0.28, 0.27, 0.51])
                axes.append(ax)
                pp, yy = P[m][:n_show], Y[:n_show]
                c0, _ = np.histogram(pp[yy == 0], bins=edges)
                c1, _ = np.histogram(pp[yy == 1], bins=edges)
                ax.bar(ctr, c0, width=0.085, color=BLUE, label="bukan salinan")
                ax.bar(ctr, c1, width=0.085, bottom=c0, color=ORANGE, label="salinan")
                ax.set_xlim(0, 1)
                ax.set_ylim(0, 60)
                ax.set_title(m, fontsize=21, weight="bold", color=COL[m])
                ax.set_xlabel("keyakinan 'ini salinan'", fontsize=12)
                ax.tick_params(labelsize=11)
                ax.spines[["top", "right"]].set_visible(False)
                sure = float(((pp <= 0.1) | (pp >= 0.9)).mean()) * 100
                mid = float(((pp > 0.3) & (pp < 0.7)).mean()) * 100
                fig.text(0.05 + i * 0.32, 0.135, "sangat yakin: %.0f%%" % sure, fontsize=16)
                fig.text(0.05 + i * 0.32, 0.085, "ragu-ragu: %s%%" % ("%.0f" % mid), fontsize=16, color=GREY)
                if i == 0:
                    ax.set_ylabel("jumlah jawaban", fontsize=12)
                    ax.legend(fontsize=11, frameon=False, loc="upper center")
            fig.text(0.04, 0.02, "Kasus dinilai: %d dari %d" % (n_show, N), fontsize=13, color=GREY)
        elif k == "high":
            ax = fig.add_axes([0.08, 0.16, 0.58, 0.62])
            w = 0.36
            x = np.arange(3)
            prog = min(1.0, q * 1.6)
            ax.bar(x - w / 2, [M[m]["stated_hi"] * prog for m in MODELS], w, color="#bdbdbd", label="keyakinan yang dinyatakan AI")
            ax.bar(x + w / 2, [M[m]["actual_hi"] * prog for m in MODELS], w, color=[COL[m] for m in MODELS], label="yang benar-benar salinan")
            ax.set_xticks(x)
            ax.set_xticklabels(MODELS, fontsize=18)
            ax.set_ylim(0, 1.32)
            ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
            ax.set_yticklabels(["0", "25%", "50%", "75%", "100%"], fontsize=13)
            ax.legend(fontsize=13, frameon=False, loc="upper left")
            ax.spines[["top", "right"]].set_visible(False)
            if q > 0.65:
                for xi, m in zip(x, MODELS):
                    ax.text(xi - w / 2, M[m]["stated_hi"] + 0.015, "%.0f%%" % (100 * M[m]["stated_hi"]), ha="center", fontsize=14)
                    ax.text(xi + w / 2, M[m]["actual_hi"] + 0.015, "%.0f%%" % (100 * M[m]["actual_hi"]), ha="center", fontsize=14, weight="bold")
            fig.text(0.08, 0.92, "Saat AI menyatakan 'hampir pasti salinan' (>= 80%)", fontsize=22, weight="bold")
            fig.text(0.70, 0.62, "Berapa yang benar-benar\nsalinan?", fontsize=17)
            for j, m in enumerate(MODELS):
                fig.text(0.70, 0.50 - 0.11 * j, "%s: %d jawaban" % (m, M[m]["n_hi"]), fontsize=15, color=COL[m])
        elif k == "brier":
            n_show = max(2, int(q * N))
            ax = fig.add_axes([0.08, 0.16, 0.60, 0.64])
            for m in MODELS:
                ax.plot(np.arange(1, n_show + 1), run[m][:n_show], color=COL[m], lw=3, label=m)
            ax.axhline(0.25, color=GREY, ls="--", label="0,25 = menebak 50/50")
            ax.set_xlim(1, N)
            ax.set_ylim(0.05, 0.45)
            ax.set_xlabel("jumlah kasus dinilai", fontsize=15)
            ax.set_ylabel("Brier berjalan (makin kecil makin tepat)", fontsize=14)
            ax.tick_params(labelsize=12)
            ax.legend(fontsize=13, frameon=False, loc="upper right")
            ax.spines[["top", "right"]].set_visible(False)
            fig.text(0.08, 0.92, "Skor Brier: seberapa tepat keyakinan tiap AI", fontsize=23, weight="bold")
            for j, m in enumerate(MODELS):
                fig.text(0.73, 0.66 - 0.17 * j, m, fontsize=17, color=COL[m], weight="bold")
                fig.text(0.73, 0.59 - 0.17 * j, fmt(run[m][n_show - 1]), fontsize=30, weight="bold", color=COL[m])
        elif k == "score":
            fig.text(0.04, 0.93, "Papan skor: tiga ukuran, tiga AI (kasus yang sama)", fontsize=22, weight="bold")
            spec = [("Brier (makin kecil makin tepat)", "brier", False, (0, 0.30)), ("AUROC (0,5 = tebakan; 1 = sempurna)", "auroc", False, (0.5, 1.0)),
                    ("Menjawab 'sangat yakin' (%)", "sure", True, (0, 105)), ("Menjawab ragu-ragu 0,3 sampai 0,7 (%)", "mid", True, (0, 30))]
            prog = min(1.0, q * 1.8)
            for i, (title, key, pct, lim) in enumerate(spec):
                ax = fig.add_axes([0.07 + (i % 2) * 0.47, 0.50 - (i // 2) * 0.43, 0.38, 0.30])
                vals = [M[m][key] * (100 if pct else 1) for m in MODELS]
                base = lim[0]
                ax.bar(MODELS, [base + (v - base) * prog for v in vals], color=[COL[m] for m in MODELS])
                ax.set_ylim(*lim)
                ax.set_title(title, fontsize=14)
                ax.tick_params(labelsize=13)
                ax.spines[["top", "right"]].set_visible(False)
                if q > 0.7:
                    for xi, v in enumerate(vals):
                        ax.text(xi, v + (lim[1] - lim[0]) * 0.02, (("%.0f" % v) if pct else fmt(v)), ha="center", fontsize=14, weight="bold")
        else:
            lines = ["Yang terukur pada uji ini (97 pasang laporan yang sama):",
                     "- Ketiga AI menyatakan angka keyakinan, bukan sekadar benar atau salah.",
                     "- Angka itu membawa informasi (AUROC di atas 0,5 pada ketiganya).",
                     "- Ketepatan keyakinan berbeda: Brier Haiku %s, Gemma %s, Qwen %s." % (fmt(M["Haiku"]["brier"]), fmt(M["Gemma"]["brier"]), fmt(M["Qwen"]["brier"])),
                     "- Haiku lebih sering menyatakan ragu (%.0f%% jawaban), Gemma dan Qwen hampir tidak pernah." % (100 * M["Haiku"]["mid"]),
                     "",
                     "Batas:",
                     "- n kecil: satu replikasi; Haiku satu subagen; belum tentu berlaku umum.",
                     "- Gemma menilai laporan yang ditulis Gemma sendiri pada uji ini.",
                     "- Pada himpunan lebih besar (%d baris; hanya Gemma dan Qwen) Brier setara," % big["n"],
                     "  Gemma %s dan Qwen %s." % (fmt(big["brier_g"]), fmt(big["brier_q"])),
                     "- Ini perilaku keyakinan yang terukur dari luar, bukan ukuran kesadaran."]
            fig.text(0.05, 0.93, "Kesimpulan", fontsize=30, weight="bold")
            y0 = 0.83
            for ln in lines:
                head = ln.endswith(":") and not ln.startswith("  ")
                fig.text(0.05, y0, ln, fontsize=17 if not head else 19, weight="bold" if head else "normal")
                y0 -= 0.062
        return []

    writer = animation.FFMpegWriter(fps=FPS, codec="libx264", extra_args=["-pix_fmt", "yuv420p", "-crf", "24"])
    animation.FuncAnimation(fig, frame, frames=total, blit=False).save(OUT, writer=writer)
    dur = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", OUT], capture_output=True, text=True).stdout.strip()
    print("saved", OUT, "duration %.1f s" % float(dur), "size MB %.1f" % (os.path.getsize(OUT) / 1e6))


if __name__ == "__main__":
    main()
