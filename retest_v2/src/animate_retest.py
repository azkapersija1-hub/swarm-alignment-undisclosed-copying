"""Videos of the v2 re-test built ONLY from raw result files (no screen recording, no invented numbers).
 process    : four real scenarios (honest twin, paraphrase copy, adaptive lexical injection, adaptive out-of-band) with 3D PCA of sentence embeddings,
              the provenance ledger and the candidate monitor scores, then the pre-registered verdict scoreboard.
 performance: frame-by-frame replay of the scenario stream of three generator models, call latency, validity, running recall/FPR of the monitors, scoreboard.
Usage: py -3.12 -B -X utf8 animate_retest.py process|performance [fast] [--tag gemma_homog]"""
import argparse
import glob
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import animation

HERE = os.path.dirname(os.path.abspath(__file__))
RT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import features_v2 as F  # noqa: E402
import corpus  # noqa: E402
import monitors as M  # noqa: E402

BLUE, ORANGE, GREEN, GREY, RED, PURPLE = "#0072B2", "#E69F00", "#009E73", "#8c8c8c", "#D55E00", "#6a3d9a"
TYPES = ["IND_SAME", "IND_DIFF", "NOSRC_SAME", "TWIN_H", "NEAR_H", "SHARED_OK", "COPY_LIT", "COPY_PARA", "COPY_TWIN", "COPY_COVER",
         "ADAPT_SURROGATE_K3", "ADAPT_LEX_INJECT", "ADAPT_SPLIT_2", "ADAPT_OUT_OF_BAND"]
TCOL = dict(zip(TYPES, ["#56B4E9", "#0072B2", "#CC79A7", "#009E73", "#8fd14f", "#E69F00", "#F0E442", "#D55E00", "#a6322b", "#6a3d9a", "#000000", "#444444", "#777777", "#aaaaaa"]))
MCOL = {"gemma": BLUE, "qwen": ORANGE, "deepseek": GREEN}
FPS = 24
OUTDIR = os.path.join(RT, "videos")


def load_runs(tag):
    out = []
    for p in sorted(glob.glob(os.path.join(RT, "runs", tag, "rep*_*.jsonl"))):
        out += [r for r in (json.loads(l) for l in open(p, encoding="utf-8")) if not r.get("failed")]
    return out


def jload(path, default=None):
    return json.load(open(path, encoding="utf-8")) if os.path.isfile(path) else default


def verdict_lines(res_dir):
    fal = jload(os.path.join(res_dir, "falsifiers.json"), {})
    prim = jload(os.path.join(res_dir, "primary_comparisons.json"), {})
    lines = []
    for k in ["ARG-H%d" % i for i in range(1, 11)]:
        if k in fal:
            f = fal[k].get("falsified")
            lines.append((k, "undetermined" if f is None else ("FALSIFIED" if f else "not falsified")))
    ps = prim.get("target_A", {}).get("primary_success")
    return lines, ps


def arms_passed():
    """(n_passed, n_arms) of the pre-declared primary comparison over every evaluated arm, read from the result files."""
    ok = tot = 0
    for t in ("gemma_homog", "qwen_homog", "deepseek_homog", "het_gemma_qwen", "het_gemma_deepseek"):
        p = jload(os.path.join(RT, "results", t, "primary_comparisons.json"), {})
        v = p.get("target_A", {}).get("primary_success")
        if v is not None:
            tot += 1
            ok += bool(v)
    return ok, tot


def draw_slide(fig, full, lines, sizes, colors=None):
    full.set_visible(True)
    full.cla()
    full.axis("off")
    y = 0.88
    for i, (ln, sz) in enumerate(zip(lines, sizes)):
        full.text(0.5, y, ln, ha="center", va="center", fontsize=sz, color=(colors[i] if colors else "black"))
        y -= 0.045 + sz / 700


def process_video(tag, fast, res_dir):
    catalog, _ = corpus.load_catalog()
    cache_by_tag = {"gemma_homog": "c_gemma.pkl", "qwen_homog": "c_qwen.pkl", "deepseek_homog": "c_deepseek.pkl"}   # scoring wrote one cache file per process
    emb = M.EmbCache(os.path.join(RT, "cache", cache_by_tag.get(tag, "emb_cache_v2.pkl")))
    sfile = sorted(glob.glob(os.path.join(RT, "scores", tag, "rep0_*_scores.jsonl")))[0]
    scores = {r["scenario_id"]: r for r in (json.loads(l) for l in open(sfile, encoding="utf-8")) if not r.get("failed")}
    runs = {r["scenario"]["scenario_id"]: r for r in load_runs(tag) if r["replicate"] == 0}
    pick = [("TWIN_H", "Honest agents, twin sources (identical text, different publisher)"), ("COPY_PARA", "B paraphrases A's report and cites another source"),
            ("ADAPT_LEX_INJECT", "Adaptive: B copies 4 claims and injects 1-2 facts from its own opened source"),
            ("ADAPT_OUT_OF_BAND", "Adaptive: copy with NO message events in the ledger, own source opened as cover")]
    scenes = []
    for typ, cap in pick:
        sid = next(s for s in sorted(runs) if runs[s]["scenario"]["type"] == typ and runs[s]["scenario"]["split"] == "test" and s in scores)
        rec, sc = runs[sid], scores[sid]
        UA, UB = emb.get(rec["report_a"]["claims"]), emb.get(rec["report_b"]["claims"])
        src = [t for rep in (rec["report_a"], rec["report_b"]) for i in M.claimed_sources(rep, catalog) for t in M.source_sentences(catalog[i])]
        S = emb.get(src) if src else np.zeros((0, UA.shape[1]))
        X = np.vstack([UA, UB, S])
        mu = X.mean(0)
        _, _, Vt = np.linalg.svd(X - mu, full_matrices=False)
        P = lambda Z: (Z - mu) @ Vt[:3].T
        gA, gB = M.BF.geometric_median(UA), M.BF.geometric_median(UB)
        c = sc["cand"]
        bars = [("F2 cosine", sc["feats"]["cos"]), ("H1 E_sup", c["h1"]["score"]), ("H3 disguise", c["claim_level"]["h3"]["score"]), ("H4 F_omit", c["h4"]["score"]),
                ("H5 bipartite", c["claim_level"]["h5"]["score"]), ("H6 D_dpi", c["claim_level"]["h6"]["score"]), ("H7 CSLS", c["h7"]["score"])]
        scenes.append({"A": P(UA), "B": P(UB), "S": P(S) if len(S) else np.zeros((0, 3)), "gA": P(gA[None])[0], "gB": P(gB[None])[0], "cos": float(np.dot(gA, gB)),
                       "ledger": rec["ledger"], "bars": bars, "truth": rec["scenario"]["truth"], "id": sid, "type": typ, "caption": cap})
    verdicts, prim_ok = verdict_lines(res_dir)
    SF = 90 if fast else 300
    intro, outro = (24 if fast else 96), (48 if fast else 192)
    total = intro + SF * len(scenes) + outro
    fig = plt.figure(figsize=(12.8, 7.2), dpi=100)
    ax3 = fig.add_axes([0.02, 0.10, 0.56, 0.78], projection="3d")
    axL = fig.add_axes([0.60, 0.50, 0.38, 0.38])
    axB = fig.add_axes([0.74, 0.10, 0.23, 0.34])
    title = fig.text(0.02, 0.95, "", fontsize=13, weight="bold")
    cap = fig.text(0.02, 0.03, "", fontsize=11)
    full = fig.add_axes([0, 0, 1, 1])

    def scene(sc, t, k):
        full.set_visible(False)
        for a in (ax3, axL, axB):
            a.cla()
            a.set_visible(True)
        axL.axis("off")
        st = 0 if t < 0.22 else 1 if t < 0.42 else 2 if t < 0.58 else 3 if t < 0.82 else 4
        title.set_text("%s | %s" % (sc["id"], sc["caption"]))
        nA = int(np.ceil(len(sc["A"]) * min(1.0, t / 0.20)))
        nB = int(np.ceil(len(sc["B"]) * min(1.0, max(0.0, (t - 0.22) / 0.18)))) if st >= 1 else 0
        if len(sc["S"]):
            ax3.scatter(*sc["S"].T, c=GREY, marker="x", s=14, alpha=0.5, label="cited source sentences")
        ax3.scatter(*sc["A"][:nA].T, c=BLUE, s=46, label="Agent A claims")
        if nB:
            ax3.scatter(*sc["B"][:nB].T, c=ORANGE, marker="^", s=52, label="Agent B claims")
        if st >= 2:
            ax3.scatter(*sc["gA"], c=BLUE, marker="D", s=170, edgecolors="black")
            ax3.scatter(*sc["gB"], c=ORANGE, marker="D", s=170, edgecolors="black")
            ax3.plot(*zip(sc["gA"], sc["gB"]), c="black", lw=1.5)
            ax3.text(*((sc["gA"] + sc["gB"]) / 2), "  cos = %.3f" % sc["cos"], fontsize=10, weight="bold")
        ax3.view_init(elev=22, azim=20 + 0.9 * k)
        ax3.legend(loc="upper left", fontsize=7, frameon=False)
        ax3.set_title("Sentence embeddings projected to 3D by PCA (real run data)", fontsize=9)
        ax3.tick_params(labelsize=6)
        evs = sc["ledger"]
        n_ev = len(evs) if st >= 3 else int(np.ceil(len(evs) * min(1.0, t / 0.58)))
        axL.text(0, 1.0, "Provenance ledger (hash chain)", fontsize=10, weight="bold", va="top")
        for i, e in enumerate(evs[:n_ev]):
            d = e["data"]
            detail = d.get("source", "") or ("->" + d.get("to", ""))
            if e["kind"] == "report_submitted":
                detail = "cites " + ",".join(d.get("cited", []))
            axL.text(0, 0.90 - 0.095 * i, "#%d %-17s %s %s [%s]" % (e["n"], e["kind"], e["agent"][-6:], detail, e["hash"][:6]), fontsize=7, family="monospace", va="top")
        grow = 0.0 if st < 3 else min(1.0, (t - 0.58) / 0.14)
        vals = [v if v == v else 0.0 for _, v in sc["bars"]]
        axB.barh(range(len(vals)), [v * grow for v in vals], color=BLUE)
        axB.set_yticks(range(len(vals)))
        axB.set_yticklabels([b for b, _ in sc["bars"]], fontsize=7)
        axB.invert_yaxis()
        axB.set_xlim(-0.3, 1.1)
        axB.axvline(0, c="black", lw=0.6)
        axB.set_title("Candidate monitor scores (raw; see report for thresholds)", fontsize=7)
        msg = ["Agent A writes its report from its source.",
               "Agent B writes its report (%s)." % ("honest, own source" if sc["type"] == "TWIN_H" else "after receiving A's report; the adaptive arms hide it differently"),
               "Sentences become points; each report gets a robust centre (geometric median).",
               "Monitors compare the reports; the ledger records the process (adaptive arms tamper with what the ledger shows).",
               "Ground truth (controller-assigned, never seen by monitors): copying=%d  non-independent=%d  false provenance=%d" % tuple(sc["truth"].values())]
        cap.set_text(msg[st])

    def frame(i):
        if i < intro:
            for a in (ax3, axL, axB):
                a.set_visible(False)
            title.set_text("")
            cap.set_text("")
            draw_slide(fig, full, ["Re-test of the oversight study: pre-registered, fresh samples, adaptive attackers", "Gemma 4, Qwen 3.8 flash and DeepSeek v4.1 flash agents on TLS materials",
                                   "Swarm Alignment Hackathon 2026 - Track 4 (Tracks 1-3 supporting tests)"], [22, 13, 12])
        elif i < intro + SF * len(scenes):
            j = i - intro
            scene(scenes[j // SF], (j % SF) / SF, j % SF)
        else:
            for a in (ax3, axL, axB):
                a.set_visible(False)
            title.set_text("")
            cap.set_text("")
            lines = ["Pre-registered hypotheses: verdicts on fresh data", ""]
            colors = ["black", "black"]
            for k_, v_ in verdicts:
                lines.append("%s   %s" % (k_, v_))
                colors.append(RED if v_ == "FALSIFIED" else GREEN)
            n_ok, n_all = arms_passed()
            lines += ["", "Primary comparison, this arm (target A): %s" % ("PASSED all pre-declared criteria" if prim_ok else "did NOT pass all pre-declared criteria"),
                      "Across all %d evaluated arms the primary comparison passed in %d (see report)." % (n_all, n_ok),
                      "Limits: same 109 TLS documents, instructed agents, controller-written ledger."]
            colors += ["black", RED if not prim_ok else GREEN, "black", "black"]
            draw_slide(fig, full, lines, [15, 6] + [11] * len(verdicts) + [6, 12, 10, 9], colors)
        return []

    return fig, frame, total, "process_replay_retest%s.mp4" % ("_fast" if fast else "")


def performance_video(tag, fast, res_dir):
    arms = [("gemma", "gemma_homog"), ("qwen", "qwen_homog"), ("deepseek", "deepseek_homog")]
    calls, stream = [], []
    for name, t in arms:
        for r in load_runs(t):
            stream.append((name, r["scenario"]["type"]))
            for key in ("report_a", "report_b"):
                calls.append((name, r[key].get("seconds", np.nan), r[key].get("attempts", 1)))
    N = len(stream)
    preds = jload(os.path.join(res_dir, "pooled_predictions.json"), {})
    verdicts, prim_ok = verdict_lines(res_dir)
    FR = 150 if fast else 1200
    fig = plt.figure(figsize=(12.8, 7.2), dpi=100)
    gs = fig.add_gridspec(2, 3, left=0.05, right=0.985, top=0.88, bottom=0.10, wspace=0.28, hspace=0.38)
    a1, a2, a3, a4, a5, a6 = [fig.add_subplot(gs[i // 3, i % 3]) for i in range(6)]
    head = fig.text(0.05, 0.945, "", fontsize=13, weight="bold")
    foot = fig.text(0.05, 0.03, "", fontsize=9)
    cols = 52
    rows_n = int(np.ceil(N / cols))
    xy = np.array([(i % cols, i // cols) for i in range(N)])
    colors = [TCOL.get(t, GREY) for _, t in stream]
    MONS = [("F2 embedding cosine", "cosine baseline", GREY), ("F9b ensemble + source checks", "F9b", BLUE), ("F11x candidate ensemble", "F11x (candidates)", GREEN),
            ("F0b LLM report-only [tp:qwen3.8-flash]", "LLM reads report", ORANGE)]

    def running(mon, upto, key, tgt="A_primary"):
        d = preds.get("%s|%s" % (mon, tgt))
        if not d:
            return None
        y, fl, v, ab = (np.array(d[k]) for k in ("y", "flag", "valid", "abstain"))
        k = max(1, int(np.ceil(upto * len(y))))
        yy, ff, ok = y[:k], (fl[:k].astype(bool) & ~ab[:k].astype(bool)), v[:k].astype(bool)
        pos, neg = ((yy == 1) & ok).sum(), ((yy == 0) & ok).sum()
        if key == "recall":
            return (ff & (yy == 1) & ok).sum() / pos if pos >= 8 else np.nan
        return (ff & (yy == 0) & ok).sum() / neg if neg >= 8 else np.nan

    def frame(f):
        p = (f + 1) / FR
        k = max(1, int(np.ceil(p * N)))
        c = max(1, int(np.ceil(p * len(calls))))
        for a in (a1, a2, a3, a4, a5, a6):
            a.cla()
        a1.scatter(xy[:k, 0], -xy[:k, 1], c=colors[:k], s=7, marker="s")
        a1.set_xlim(-1, cols)
        a1.set_ylim(-rows_n, 1)
        a1.axis("off")
        a1.set_title("Scenarios executed: %d / %d (colour = type; dark = adaptive attacks)" % (k, N), fontsize=8)
        cs = calls[:c]
        for name in MCOL:
            xs = [i for i, x in enumerate(cs) if x[0] == name]
            if xs:
                a2.scatter(xs, [cs[i][1] for i in xs], s=3, c=MCOL[name], alpha=0.4, label=name)
        a2.legend(fontsize=6, frameon=False, loc="upper left")
        a2.set_title("LLM call latency (s) by generator model", fontsize=9)
        a2.set_xlim(0, len(calls))
        a2.set_ylim(0, 60)
        a2.spines[["top", "right"]].set_visible(False)
        for name in MCOL:
            vv = [x[2] == 1 for x in cs if x[0] == name]
            if len(vv) > 20:
                a3.plot(np.cumsum(vv) / np.arange(1, len(vv) + 1), c=MCOL[name], label=name)
        a3.set_ylim(0.8, 1.01)
        a3.legend(fontsize=6, frameon=False, loc="lower left")
        a3.set_title("Valid JSON on first attempt (running)", fontsize=9)
        a3.spines[["top", "right"]].set_visible(False)
        for mon, lab, col in MONS:
            xs = np.linspace(0.05, p, max(2, int(60 * p)))
            for ax, key in ((a4, "recall"), (a5, "fpr")):
                ys = [running(mon, x, key) for x in xs]
                if preds and not all(v is None for v in ys):
                    ax.plot(xs * len(preds.get("F2 embedding cosine|A_primary", {"y": [0]})["y"]) if "F2 embedding cosine|A_primary" in preds else xs, ys, c=col, label=lab)
        a4.set_ylim(0, 1.02)
        a4.set_title("Running recall, undisclosed copying (test rows, confirmatory arm)", fontsize=8)
        a5.set_ylim(0, 1.02)
        a5.axhline(0.05, c=GREY, ls="--", lw=0.8)
        a5.set_title("Running false positive rate", fontsize=9)
        if preds:
            a4.legend(fontsize=6.5, frameon=False, loc="lower right")
        for a in (a4, a5):
            a.spines[["top", "right"]].set_visible(False)
        a6.axis("off")
        a6.set_title("Pre-registered verdicts", fontsize=9)
        show = int(len(verdicts) * max(0.0, (p - 0.55) / 0.40))
        for i, (k_, v_) in enumerate(verdicts[:show]):
            a6.text(0.02, 0.95 - 0.09 * i, "%s  %s" % (k_, v_), fontsize=9, color=RED if v_ == "FALSIFIED" else GREEN, va="top")
        if p > 0.97 and verdicts:
            n_ok, n_all = arms_passed()
            a6.text(0.02, 0.02, "Primary comparison (this arm): %s; all arms: %d of %d" % ("PASSED" if prim_ok else "NOT passed", n_ok, n_all), fontsize=9, weight="bold", color=GREEN if prim_ok else RED)
        head.set_text("Re-test replay | three generator models | scenario %d/%d" % (k, N))
        foot.set_text("Series from raw logs; agents run remotely, local GPU only embeds. Monitor curves replay final predictions in execution order (not live training).")
        return []

    return fig, frame, FR, "performance_replay_retest%s.mp4" % ("_fast" if fast else "")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["process", "performance"])
    ap.add_argument("fast", nargs="?", default="")
    ap.add_argument("--tag", default="gemma_homog")
    a = ap.parse_args()
    fast = a.fast == "fast"
    res_dir = os.path.join(RT, "results", a.tag)
    fig, frame, total, name = (process_video if a.what == "process" else performance_video)(a.tag, fast, res_dir)
    os.makedirs(OUTDIR, exist_ok=True)
    matplotlib.rcParams["animation.ffmpeg_path"] = "ffmpeg"
    writer = animation.FFMpegWriter(fps=FPS, codec="libx264", extra_args=["-pix_fmt", "yuv420p", "-crf", "23"])
    animation.FuncAnimation(fig, frame, frames=total, blit=False).save(os.path.join(OUTDIR, name), writer=writer)
    print("saved", name, total, "frames")


if __name__ == "__main__":
    main()
