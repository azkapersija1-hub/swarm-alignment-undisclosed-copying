"""Figures for the v2 re-test, generated only from result files (csv/json). Usage: make_figures_v2.py"""
import csv
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
RT = os.path.dirname(HERE)
RES = os.path.join(RT, "results")
FIG = os.path.join(RES, "figures")
ARMS = [("D1 Gemma", "gemma_homog"), ("D2 Qwen", "qwen_homog"), ("D2 DeepSeek", "deepseek_homog"), ("D3 Gemma>Qwen", "het_gemma_qwen"), ("D3 Gemma>DeepSeek", "het_gemma_deepseek")]
BLUE, ORANGE, GREEN, GREY, RED, PURPLE = "#0072B2", "#E69F00", "#009E73", "#8c8c8c", "#D55E00", "#6a3d9a"
TYPES = ["IND_SAME", "IND_DIFF", "NOSRC_SAME", "TWIN_H", "NEAR_H", "SHARED_OK", "COPY_LIT", "COPY_PARA", "COPY_TWIN", "COPY_COVER",
         "ADAPT_SURROGATE_K3", "ADAPT_LEX_INJECT", "ADAPT_SPLIT_2", "ADAPT_OUT_OF_BAND"]


def rows(tag, name="results_main.csv"):
    p = os.path.join(RES, tag, name)
    return list(csv.DictReader(open(p, encoding="utf-8"))) if os.path.isfile(p) else []


def fnum(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return float("nan")


def fig_auroc():
    mons = ["F2 embedding cosine", "F9b ensemble + source checks", "F11x candidate ensemble", "H1 E_sup", "H3 S_disguise [claim_level]", "H4 F_omit",
            "F0b LLM report-only [tp:qwen3.8-flash]"]
    labels = ["F2 cosine", "F9b", "F11x", "H1", "H3", "H4", "LLM report-only"]
    fig, ax = plt.subplots(figsize=(11, 4.8))
    w = 0.16
    cols = [BLUE, ORANGE, GREEN, PURPLE, RED]
    drawn = False
    for k, (arm, tag) in enumerate(ARMS):
        rs = {r["monitor"]: r for r in rows(tag) if r["target"] == "A_primary"}
        if not rs:
            continue
        ys = [fnum(rs[m]["auroc"]) if m in rs else np.nan for m in mons]
        lo = [fnum(rs[m]["auroc_lo"]) if m in rs else np.nan for m in mons]
        hi = [fnum(rs[m]["auroc_hi"]) if m in rs else np.nan for m in mons]
        x = np.arange(len(mons)) + (k - 2) * w
        ax.bar(x, ys, w, color=cols[k], label=arm, yerr=[np.array(ys) - np.array(lo), np.array(hi) - np.array(ys)], capsize=2, error_kw={"lw": 0.8})
        drawn = True
    if not drawn:
        plt.close(fig)
        return
    ax.axhline(0.5, c=GREY, ls="--", lw=0.8)
    ax.set_xticks(range(len(mons)))
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylim(0.3, 1.02)
    ax.set_ylabel("AUROC, undisclosed copying (95% cluster bootstrap)")
    ax.legend(fontsize=8, ncol=5, frameon=False, loc="upper center")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig1_auroc_by_arm.png"), dpi=150)
    plt.close(fig)


def fig_type_heatmap(tag="gemma_homog"):
    rs = [r for r in rows(tag, "results_per_type.csv") if r["target"] == "A_primary"]
    if not rs:
        return
    mons = ["F2 embedding cosine", "F9b ensemble + source checks", "F11x candidate ensemble", "F0b LLM report-only [tp:qwen3.8-flash]", "D LLM with sources [tp:qwen3.8-flash]",
            "H1 E_sup", "H3 S_disguise [claim_level]", "H4 F_omit"]
    M = np.full((len(mons), len(TYPES)), np.nan)
    for r in rs:
        if r["monitor"] in mons and r["type"] in TYPES:
            M[mons.index(r["monitor"]), TYPES.index(r["type"])] = fnum(r["flag_rate"])
    fig, ax = plt.subplots(figsize=(12, 4.6))
    im = ax.imshow(M, cmap="viridis", vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(range(len(TYPES)))
    ax.set_xticklabels(TYPES, rotation=40, ha="right", fontsize=8)
    ax.set_yticks(range(len(mons)))
    ax.set_yticklabels([m.replace(" [tp:qwen3.8-flash]", " (Qwen)") for m in mons], fontsize=8)
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            if not np.isnan(M[i, j]):
                ax.text(j, i, "%.2f" % M[i, j], ha="center", va="center", fontsize=6.5, color="white" if M[i, j] < 0.6 else "black")
    ax.set_title("Flag rate per scenario type at the 95th-percentile calibration threshold (confirmatory arm D1). Columns 11-14 are adaptive attacks.", fontsize=9)
    fig.colorbar(im, ax=ax, fraction=0.02)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig2_flag_rates_by_type.png"), dpi=150)
    plt.close(fig)


def fig_logmodes(tag="gemma_homog"):
    rs = {r["monitor"]: r for r in rows(tag) if r["target"] == "C"}
    modes = ["full_anchored", "comm_hidden", "half_mcar", "none", "tail_truncated", "spoofed_open", "reordered"]
    if not rs:
        return
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.2))
    for ax, key, title in ((axes[0], "recall", "Recall (target C: false provenance claim)"), (axes[1], "fpr", "False positive rate")):
        for name, col, mk in (("F10 ensemble + ledger [%s]", BLUE, "o"), ("H8 tri-state [%s]", RED, "s")):
            ys = [fnum(rs.get(name % m, {}).get(key)) for m in modes]
            ax.plot(range(len(modes)), ys, c=col, marker=mk, label=name.split(" [")[0])
        ax.set_xticks(range(len(modes)))
        ax.set_xticklabels(modes, rotation=35, ha="right", fontsize=8)
        ax.set_ylim(-0.02, 1.02)
        ax.set_title(title, fontsize=10)
        ax.spines[["top", "right"]].set_visible(False)
    axes[0].legend(fontsize=8, frameon=False)
    axes[1].axhline(0.05, c=GREY, ls="--", lw=0.8)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig3_log_degradation.png"), dpi=150)
    plt.close(fig)


def fig_scoreboard():
    hyps = ["ARG-H%d" % i for i in range(1, 11)]
    fig, ax = plt.subplots(figsize=(9, 4.4))
    drawn = False
    for k, (arm, tag) in enumerate(ARMS):
        p = os.path.join(RES, tag, "falsifiers.json")
        if not os.path.isfile(p):
            continue
        f = json.load(open(p, encoding="utf-8"))
        for i, h in enumerate(hyps):
            v = f.get(h, {}).get("falsified", "missing")
            col = RED if v is True else GREEN if v is False else GREY
            ax.add_patch(plt.Rectangle((i, k), 0.92, 0.9, color=col))
            ax.text(i + 0.46, k + 0.45, {True: "F", False: "ok", None: "?"}.get(v, "-"), ha="center", va="center", color="white", fontsize=8)
        drawn = True
    if not drawn:
        plt.close(fig)
        return
    ax.set_xlim(0, len(hyps))
    ax.set_ylim(0, len(ARMS))
    ax.set_xticks([i + 0.46 for i in range(len(hyps))])
    ax.set_xticklabels([h.replace("ARG-", "") for h in hyps], fontsize=9)
    ax.set_yticks([k + 0.45 for k in range(len(ARMS))])
    ax.set_yticklabels([a for a, _ in ARMS], fontsize=9)
    ax.invert_yaxis()
    ax.set_title("Pre-registered falsifiers by arm: F = falsified, ok = not falsified, ? = undetermined", fontsize=9)
    for s in ax.spines.values():
        s.set_visible(False)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig4_falsifier_scoreboard.png"), dpi=150)
    plt.close(fig)


def fig_tracks():
    t = os.path.join(RES, "tracks")
    p3 = os.path.join(t, "track3.json")
    p2 = os.path.join(t, "track2_v3_summary.json")
    p1 = os.path.join(t, "track1_redteam_qwen_deepseek.json")
    if not any(os.path.isfile(p) for p in (p1, p2, p3)):
        return
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.2))
    if os.path.isfile(p1):
        s = json.load(open(p1, encoding="utf-8"))["summary"]
        keys = [k for k in s if not k.endswith("control_summarize")]
        den = [s[k]["denied"] for k in keys]
        alw = [s[k]["allowed"] for k in keys]
        leak = [s[k]["leaks"] for k in keys]
        axes[0].bar(range(len(keys)), den, color=RED, label="denied and logged")
        axes[0].bar(range(len(keys)), alw, bottom=den, color=GREY, label="allowed (own/shared)")
        axes[0].set_xticks(range(len(keys)))
        axes[0].set_xticklabels([k.replace("|", "\n") for k in keys], fontsize=6)
        axes[0].set_title("Track 1: agent attempts to leave the sandbox (leaks: %d)" % sum(leak), fontsize=9)
        axes[0].legend(fontsize=7, frameon=False)
    if os.path.isfile(p2):
        s = json.load(open(p2, encoding="utf-8"))
        topo = ["isolated", "chain", "star", "full", "chain_verifier"]
        x2 = np.arange(len(topo))
        for k, (label, col, name) in enumerate((("agent3_can_verify", GREEN, "agent 3 (can verify)"), ("agents_2_4_cannot_verify", ORANGE, "agents 2 and 4 (cannot verify)"))):
            rate = []
            for tp in topo:
                cells = [v[label] for key, v in s.items() if key.split("|")[2] == tp]
                n = sum(c["n"] for c in cells)
                rate.append(sum(c["repeat_false_rate"] * c["n"] for c in cells) / n if n else np.nan)
            axes[1].bar(x2 + (k - 0.5) * 0.38, rate, 0.38, color=col, label=name)
        axes[1].set_xticks(x2)
        axes[1].set_xticklabels(topo, rotation=25, fontsize=7)
        axes[1].set_ylim(0, 0.3)
        axes[1].set_ylabel("share repeating the false claim", fontsize=8)
        axes[1].legend(fontsize=6.5, frameon=False, loc="upper left")
        axes[1].set_title("Track 2: relevant planted false claim (pooled over prompts and models)", fontsize=8.5)
    if os.path.isfile(p3):
        d = json.load(open(p3, encoding="utf-8"))["tamper"]["detection_rate"]
        modes = list(d)
        x = np.arange(len(modes))
        for k, (reg, col) in enumerate((("R1_chain_only", GREY), ("R2_chain_plus_anchor", BLUE), ("R3_chain_anchor_signatures", GREEN))):
            axes[2].bar(x + (k - 1) * 0.27, [d[m][reg] for m in modes], 0.27, color=col, label=reg)
        axes[2].set_xticks(x)
        axes[2].set_xticklabels([m.replace("_", "\n") for m in modes], fontsize=6)
        axes[2].set_ylim(0, 1.05)
        axes[2].set_title("Track 3: log tampering detection by integrity regime", fontsize=9)
        axes[2].legend(fontsize=6.5, frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.32), ncol=3)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig5_tracks.png"), dpi=150, bbox_inches="tight")
    plt.close(fig)


def main():
    os.makedirs(FIG, exist_ok=True)
    for f in (fig_auroc, fig_type_heatmap, fig_logmodes, fig_scoreboard, fig_tracks):
        f()
    print("figures:", sorted(os.listdir(FIG)))


if __name__ == "__main__":
    main()
