"""Publication figures generated ONLY from raw/derived result files. English labels. Usage: SWARM_DATASET=tls python make_figures.py"""
import csv
import glob
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SUF = "" if os.environ.get("SWARM_DATASET", "synthetic") == "synthetic" else "_" + os.environ["SWARM_DATASET"]
MET = os.path.join(ROOT, "07_STATISTICAL_ANALYSIS", "metrics" + SUF + os.environ.get("SWARM_METRICS_TAG", ""))
FIG = os.path.join(ROOT, "08_VISUAL_EVIDENCE", "figures" + SUF)
os.makedirs(FIG, exist_ok=True)
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False, "figure.dpi": 100, "savefig.dpi": 220,
                     "font.family": "DejaVu Sans"})
BLUE, ORANGE, GREEN, GREY, RED = "#0072B2", "#E69F00", "#009E73", "#8c8c8c", "#D55E00"

SHORT = {"F0a report rule (same cited source)": "F0a report rule", "F0b LLM report-only": "F0b LLM, report only",
         "D  LLM with sources (Config D)": "D  LLM + sources", "F1 lexical 3-gram": "F1 lexical", "F2 embedding cosine": "F2 cosine",
         "F3 STP": "F3 STP", "F4 STP-AR": "F4 STP-AR", "F5 STP-AR+MOI": "F5 STP-AR+MOI", "F6 RCC-v3.3 (AR)": "F6 RCC-v3.3",
         "F6b RCC-v3.3 (AR+MOI)": "F6b RCC+MOI", "F8a Argon embedding triage": "F8a Argon F42", "F8b Argon claim overlap": "F8b Argon F44",
         "S1 claim unsupported by cited source": "S1 unsupported claim", "S2 source containment (twin/near)": "S2 source twin",
         "F9 formula ensemble (artifact only)": "F9 ensemble (artifact)", "F9b ensemble + source checks": "F9b + source checks",
         "F10 ensemble + ledger [full]": "F10 + ledger (full)", "F10 ensemble + ledger [comm_hidden]": "F10 ledger, no messages",
         "F10 ensemble + ledger [half]": "F10 ledger, 50% events", "F10 ensemble + ledger [none]": "F10 ledger missing",
         "P  ledger only [full]": "P ledger only (full)", "P  ledger only [comm_hidden]": "P ledger, no messages",
         "P  ledger only [half]": "P ledger, 50% events", "P  ledger only [none]": "P ledger missing"}
MAIN = ["F0a report rule (same cited source)", "F0b LLM report-only", "D  LLM with sources (Config D)", "F1 lexical 3-gram", "F2 embedding cosine", "F3 STP",
        "F4 STP-AR", "F5 STP-AR+MOI", "F6 RCC-v3.3 (AR)", "F8a Argon embedding triage", "F8b Argon claim overlap", "S1 claim unsupported by cited source",
        "S2 source containment (twin/near)", "F9 formula ensemble (artifact only)", "F9b ensemble + source checks", "F10 ensemble + ledger [full]"]
TARGET_NAME = {"copy": "Target A: copying occurred", "noninde": "Target B: evidence non-independent", "provfalse": "Target C: provenance claim false"}


def rows(name):
    p = os.path.join(MET, name)
    return list(csv.DictReader(open(p, encoding="utf-8"))) if os.path.isfile(p) else []


def f(x):
    try:
        return float(x)
    except Exception:
        return float("nan")


def get(main, mon, target, rule="all"):
    for r in main:
        if r["monitor"] == mon and r["target"] == target and r["threshold_rule"] == rule:
            return r
    return None


def save(name):
    plt.tight_layout()
    plt.savefig(os.path.join(FIG, name), bbox_inches="tight")
    plt.close()


def fig_detection(main):
    fig, axes = plt.subplots(1, 3, figsize=(11, 5.2), sharey=True)
    y = np.arange(len(MAIN))
    for ax, (key, title) in zip(axes, (("recall", "Recall (flag rate on positives)"), ("fpr", "False positive rate (negatives)"), ("brier", "Brier score (lower = better)"))):
        for t, col, off in (("copy", BLUE, -0.25), ("noninde", ORANGE, 0.0), ("provfalse", GREEN, 0.25)):
            vals, lo, hi = [], [], []
            for m in MAIN:
                r = get(main, m, t)
                v = f(r[key]) if r else float("nan")
                vals.append(v)
                lo.append(v - f(r.get(key + "_lo", "nan")) if r else 0)
                hi.append(f(r.get(key + "_hi", "nan")) - v if r else 0)
            ax.barh(y + off, vals, height=0.23, color=col, label=TARGET_NAME[t] if key == "recall" else None, xerr=[np.nan_to_num(lo), np.nan_to_num(hi)],
                    error_kw={"elinewidth": 0.6, "capsize": 1.5})
        ax.set_title(title, fontsize=9)
        ax.set_xlim(0, 1.0)
        if key == "fpr":
            ax.axvline(0.05, color=GREY, ls="--", lw=0.8)
    axes[0].set_yticks(y)
    axes[0].set_yticklabels([SHORT.get(m, m) for m in MAIN])
    axes[0].invert_yaxis()
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=3, frameon=False, fontsize=8)
    fig.suptitle("Monitor performance at the 5%-FPR threshold (test splits pooled over replicates; bars = 95% cluster-bootstrap CI)", fontsize=9)
    fig.tight_layout(rect=[0, 0.05, 1, 0.95])
    plt.savefig(os.path.join(FIG, "fig2_detection_fpr_brier.png"), bbox_inches="tight")
    plt.close()


def fig_heat(per_type):
    types = ["IND_SAME", "IND_DIFF", "NOSRC_SAME", "TWIN_H", "NEAR_H", "SHARED_OK", "COPY_LIT", "COPY_PARA", "COPY_TWIN", "COPY_COVER"]
    mons = [m for m in MAIN if m != "F0a report rule (same cited source)"]
    M = np.full((len(mons), len(types)), np.nan)
    for r in per_type:
        if r["target"] == "copy" and r["monitor"] in mons and r["type"] in types:
            M[mons.index(r["monitor"]), types.index(r["type"])] = f(r["flag_rate"])
    fig, ax = plt.subplots(figsize=(9.5, 5.4))
    im = ax.imshow(M, cmap="viridis", vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(range(len(types)))
    ax.set_xticklabels(types, rotation=35, ha="right")
    ax.set_yticks(range(len(mons)))
    ax.set_yticklabels([SHORT.get(m, m) for m in mons])
    for i in range(len(mons)):
        for j in range(len(types)):
            if not np.isnan(M[i, j]):
                ax.text(j, i, "%.2f" % M[i, j], ha="center", va="center", fontsize=7, color="white" if M[i, j] < 0.6 else "black")
    ax.axvline(4.5, color="white", lw=2)
    ax.set_title("Flag rate by scenario type (threshold calibrated for target A). Left of line: no copying; right: copying/derived", fontsize=9)
    plt.colorbar(im, ax=ax, label="flag rate", fraction=0.03)
    save("fig3_flag_rate_by_type.png")


def fig_visibility(main):
    modes = ["full", "comm_hidden", "half", "none"]
    lab = ["full log", "no messages", "50% of events", "log missing"]
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.4))
    for ax, (key, title) in zip(axes, (("recall", "Recall"), ("fpr", "False positive rate"), ("brier", "Brier score"))):
        for t, col in (("copy", BLUE), ("noninde", ORANGE), ("provfalse", GREEN)):
            v = [f(get(main, "F10 ensemble + ledger [%s]" % m, t)[key]) if get(main, "F10 ensemble + ledger [%s]" % m, t) else np.nan for m in modes]
            ax.plot(range(4), v, "-o", color=col, label=TARGET_NAME[t].split(":")[0])
        ax.set_xticks(range(4))
        ax.set_xticklabels(lab, rotation=20, ha="right")
        ax.set_title(title, fontsize=9)
        ax.set_ylim(0, 1)
    axes[0].legend(frameon=False, fontsize=7, loc="lower left")
    fig.suptitle("Provenance-aware monitor (F10) under degraded log visibility", fontsize=9)
    save("fig6_visibility.png")


def fig_reliability():
    p = os.path.join(MET, "pooled_predictions.json")
    if not os.path.isfile(p):
        return
    preds = json.load(open(p))
    fig, axes = plt.subplots(1, 3, figsize=(10.5, 3.6))
    for ax, mon in zip(axes, ("F0b LLM report-only", "F9 formula ensemble (artifact only)", "F10 ensemble + ledger [full]")):
        d = preds.get("%s|copy" % mon)
        ax.plot([0, 1], [0, 1], "--", color=GREY, lw=0.8)
        if d:
            pp, yy = np.array(d["p"]), np.array(d["y"])
            edges = np.linspace(0, 1, 9)
            idx = np.clip(np.digitize(pp, edges) - 1, 0, 7)
            xs, ys, ns = [], [], []
            for b in range(8):
                m = idx == b
                if m.sum() >= 3:
                    xs.append(pp[m].mean()); ys.append(yy[m].mean()); ns.append(m.sum())
            ax.scatter(xs, ys, s=[20 + 3 * n ** 0.7 for n in ns], color=BLUE, alpha=0.8)
            ax.plot(xs, ys, color=BLUE, lw=0.8)
        ax.set_title(SHORT.get(mon, mon), fontsize=9)
        ax.set_xlabel("predicted probability")
        ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    axes[0].set_ylabel("observed frequency (target A)")
    fig.suptitle("Reliability diagram (8 equal-width bins; marker size = bin count)", fontsize=9)
    save("fig7_reliability.png")


def fig_gpu():
    paths = sorted(glob.glob(os.path.join(ROOT, "06_RAW_RESULTS", "gpu_samples_scoring%s.jsonl" % SUF)))
    if not paths:
        return
    S = [json.loads(l) for l in open(paths[0], encoding="utf-8") if l.strip()]
    t = np.array([s["t"] for s in S]); t = (t - t[0]) / 60
    fig, axes = plt.subplots(1, 3, figsize=(10.5, 2.9))
    for ax, key, lab, col in zip(axes, ("utilization.gpu", "memory.used", "temperature.gpu"), ("GPU utilisation (%)", "VRAM used (MiB)", "Temperature (deg C)"), (BLUE, ORANGE, RED)):
        ax.plot(t, [float(s[key]) for s in S], color=col, lw=0.9)
        ax.set_xlabel("minutes"); ax.set_title(lab, fontsize=9)
    fig.suptitle("Local GPU (embeddings) during scoring; LLM agents run remotely and are not shown", fontsize=9)
    save("fig9_gpu.png")


def fig_distribution():
    runs = sorted(glob.glob(os.path.join(ROOT, "06_RAW_RESULTS", "llm_runs" + SUF, "rep*.jsonl")))
    if not runs:
        return
    cnt = {}
    for p in runs:
        for l in open(p, encoding="utf-8"):
            sc = json.loads(l)["scenario"]
            cnt.setdefault(sc["type"], {"calib": 0, "test": 0})[sc["split"]] += 1
    types = list(cnt)
    fig, ax = plt.subplots(figsize=(8, 3))
    ax.bar(range(len(types)), [cnt[t]["calib"] for t in types], color=GREY, label="calibration")
    ax.bar(range(len(types)), [cnt[t]["test"] for t in types], bottom=[cnt[t]["calib"] for t in types], color=BLUE, label="test")
    ax.set_xticks(range(len(types))); ax.set_xticklabels(types, rotation=30, ha="right")
    ax.set_ylabel("scenarios (all replicates)"); ax.legend(frameon=False)
    ax.set_title("Scenario distribution (calibration and test use disjoint topic domains)", fontsize=9)
    save("fig8_distribution.png")


def fig_tracks():
    t2 = os.path.join(ROOT, "05_EXPERIMENTS", "track2_networks" + SUF, "t2_summary.json")
    t3 = os.path.join(ROOT, "05_EXPERIMENTS", "track3_infrastructure" + SUF, "t3_tamper.json")
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.2))
    if os.path.isfile(t2):
        S = json.load(open(t2)); names = list(S)
        x = np.arange(len(names))
        axes[0].bar(x - 0.2, [S[n]["propagation_rate_per_downstream_agent"] for n in names], 0.4, color=RED, label="repeats false claim")
        axes[0].bar(x + 0.2, [S[n]["correction_rate_per_downstream_agent"] for n in names], 0.4, color=GREEN, label="flags it as unsupported")
        axes[0].set_xticks(x); axes[0].set_xticklabels(names, rotation=20, ha="right"); axes[0].set_ylim(0, 1)
        axes[0].set_title("Track 2: planted false claim, per downstream agent", fontsize=9); axes[0].legend(frameon=False, fontsize=7)
    if os.path.isfile(t3):
        T = json.load(open(t3))["detection_rate"]; ks = list(T)
        axes[1].bar(range(len(ks)), [T[k] for k in ks], color=BLUE)
        axes[1].set_xticks(range(len(ks))); axes[1].set_xticklabels([k.replace("_", "\n") for k in ks], fontsize=7); axes[1].set_ylim(0, 1.05)
        axes[1].set_title("Track 3: hash-chain detection of ledger alteration", fontsize=9)
    fig.suptitle("Supporting tests for Tracks 2 and 3", fontsize=9)
    save("fig10_tracks.png")


def fig_architecture():
    fig, ax = plt.subplots(figsize=(10, 3.4))
    ax.axis("off")
    boxes = [(0.02, 0.55, "Source library\n(TLS materials,\ntwins, near-dups)", GREY), (0.22, 0.55, "Agent A / Agent B\n(LLM, sandboxed)", BLUE),
             (0.45, 0.55, "Provenance ledger\n(hash chain)", GREEN), (0.68, 0.55, "Oversight monitors\nreport | artifact |\nformulas | ledger | LLM", ORANGE),
             (0.68, 0.08, "Independent evaluation\n(ground truth from controller)", GREY), (0.22, 0.08, "Experiment controller\n(scenarios, truth labels)", GREY)]
    for x, y, t, c in boxes:
        ax.add_patch(plt.Rectangle((x, y), 0.19, 0.32, color=c, alpha=0.25, ec=c))
        ax.text(x + 0.095, y + 0.16, t, ha="center", va="center", fontsize=8)
    arrows = [((0.21, 0.71), (0.22, 0.71)), ((0.41, 0.71), (0.45, 0.71)), ((0.64, 0.71), (0.68, 0.71)), ((0.775, 0.55), (0.775, 0.40)), ((0.41, 0.24), (0.68, 0.24)), ((0.315, 0.40), (0.315, 0.55))]
    for a, b in arrows:
        ax.annotate("", xy=b, xytext=a, arrowprops=dict(arrowstyle="->", color="black", lw=0.8))
    ax.set_xlim(0, 0.92); ax.set_ylim(0, 1)
    ax.set_title("System architecture (monitors never read the ground-truth labels)", fontsize=9)
    save("fig1_architecture.png")


def main():
    main_rows, per_type = rows("results_main.csv"), rows("results_per_type.csv")
    fig_architecture()
    if main_rows:
        fig_detection(main_rows); fig_visibility(main_rows)
    if per_type:
        fig_heat(per_type)
    fig_reliability(); fig_gpu(); fig_distribution(); fig_tracks()
    print(sorted(os.listdir(FIG)))


if __name__ == "__main__":
    main()
