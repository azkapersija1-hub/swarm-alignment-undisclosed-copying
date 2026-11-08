"""Process replay video built from REAL run data (not a screen recording and not invented numbers).
Scenes: four real scenarios (honest independent, honest twin, copy with paraphrase, copy with cover story) from replicate 0 test split.
Everything shown (sentence embeddings -> 3D PCA, geometric medians, cosine, ledger events, monitor scores, labels) comes from the result files.
Usage: SWARM_DATASET=tls py -3.12 -I -B -X utf8 animate_process.py [fast]"""
import csv
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
sys.path.insert(0, HERE)
import corpus  # noqa: E402
import monitors as M  # noqa: E402

ROOT = os.path.dirname(HERE)
SUF = corpus.SUFFIX
FAST = len(sys.argv) > 1 and sys.argv[1] == "fast"
FPS = 24
SCENE_FRAMES = 90 if FAST else 300
BLUE, ORANGE, GREEN, GREY, RED = "#0072B2", "#E69F00", "#009E73", "#8c8c8c", "#D55E00"
PICK = [("IND_DIFF", "Honest agents, independent sources"), ("TWIN_H", "Honest agents, twin sources (identical text, different publisher)"),
        ("COPY_PARA", "B receives A's report and paraphrases it, citing another source"), ("COPY_COVER", "B opens its cited source as a cover story, but still copies A")]


def load():
    rd = sorted(glob.glob(os.path.join(ROOT, "06_RAW_RESULTS", "llm_runs" + SUF, "rep0_*.jsonl")))[0]
    sd = sorted(glob.glob(os.path.join(ROOT, "06_RAW_RESULTS", "formula_runs" + SUF, "rep0_*_scores.jsonl")))[0]
    recs = {json.loads(l)["scenario"]["scenario_id"]: json.loads(l) for l in open(rd, encoding="utf-8")}
    scores = {json.loads(l)["scenario_id"]: json.loads(l) for l in open(sd, encoding="utf-8")}
    return recs, scores


def build_scene(rec, score, catalog, emb):
    ra, rb = rec["report_a"], rec["report_b"]
    UA, UB = emb.get(ra["claims"]), emb.get(rb["claims"])
    src = []
    for rep in (ra, rb):
        for sid in M.claimed_sources(rep, catalog):
            src += M.source_sentences(catalog[sid])
    S = emb.get(src) if src else np.zeros((0, UA.shape[1]))
    X = np.vstack([UA, UB, S])
    mu = X.mean(0)
    _, _, Vt = np.linalg.svd(X - mu, full_matrices=False)
    P = lambda Z: (Z - mu) @ Vt[:3].T
    gA, gB = M.BF.geometric_median(UA), M.BF.geometric_median(UB)
    return {"A": P(UA), "B": P(UB), "S": P(S) if len(S) else np.zeros((0, 3)), "gA": P(gA[None])[0], "gB": P(gB[None])[0],
            "cos": float(np.dot(gA, gB)), "ledger": rec["ledger"], "feats": score["feats"], "llm1": score["llm_report_only"], "llm2": score["llm_with_sources"],
            "truth": rec["scenario"]["truth"], "id": rec["scenario"]["scenario_id"], "type": rec["scenario"]["type"],
            "cited_b": rb["cited_sources"], "cited_a": ra["cited_sources"]}


def outro_numbers():
    p = os.path.join(ROOT, "07_STATISTICAL_ANALYSIS", "metrics" + SUF + os.environ.get("SWARM_METRICS_TAG", ""), "results_main.csv")
    if not os.path.isfile(p):
        return None
    rows = [r for r in csv.DictReader(open(p, encoding="utf-8")) if r["target"] == "copy" and r["threshold_rule"] == "all"]
    pick = {"F0b LLM report-only": "LLM reads report only", "F4 STP-AR": "STP-AR (formula)", "F6 RCC-v3.3 (AR)": "RCC-v3.3 (formula)",
            "F9 formula ensemble (artifact only)": "Formula ensemble", "F10 ensemble + ledger [full]": "Ensemble + ledger"}
    out = []
    for r in rows:
        if r["monitor"] in pick:
            out.append((pick[r["monitor"]], float(r["recall"]), float(r["fpr"]), float(r["brier"])))
    return out


def main():
    catalog, _ = corpus.load_catalog()
    emb = M.EmbCache()
    recs, scores = load()
    scenes = []
    for typ, caption in PICK:
        sid = next(s for s in sorted(recs) if recs[s]["scenario"]["type"] == typ and recs[s]["scenario"]["split"] == "test")
        d = build_scene(recs[sid], scores[sid], catalog, emb)
        d["caption"] = caption
        scenes.append(d)
    outro = outro_numbers()
    intro_n, outro_n = (24 if FAST else 96), (36 if FAST else 144)
    total = intro_n + SCENE_FRAMES * len(scenes) + outro_n

    fig = plt.figure(figsize=(12.8, 7.2), dpi=100)
    ax3 = fig.add_axes([0.02, 0.10, 0.56, 0.78], projection="3d")
    axL = fig.add_axes([0.60, 0.55, 0.38, 0.33]); axL.axis("off")
    axB = fig.add_axes([0.74, 0.12, 0.23, 0.36])
    title = fig.text(0.02, 0.95, "", fontsize=13, weight="bold")
    cap = fig.text(0.02, 0.03, "", fontsize=11)
    full = fig.add_axes([0, 0, 1, 1]); full.axis("off"); full.set_visible(False)

    def stage(t):  # t in [0,1]
        return 0 if t < 0.22 else 1 if t < 0.42 else 2 if t < 0.58 else 3 if t < 0.82 else 4

    def draw_scene(sc, t, frame_in_scene):
        ax3.cla(); axL.cla(); axL.axis("off"); axB.cla(); full.set_visible(False)
        ax3.set_visible(True); axL.set_visible(True); axB.set_visible(True)
        st = stage(t)
        title.set_text("%s   |   %s" % (sc["id"], sc["caption"]))
        nA = int(np.ceil(len(sc["A"]) * min(1.0, t / 0.20))) if st >= 0 else 0
        nB = int(np.ceil(len(sc["B"]) * min(1.0, max(0.0, (t - 0.22) / 0.18)))) if st >= 1 else 0
        if len(sc["S"]):
            ax3.scatter(*sc["S"].T, c=GREY, marker="x", s=14, alpha=0.5, label="cited source sentences")
        ax3.scatter(*sc["A"][:nA].T, c=BLUE, s=46, label="Agent A claims")
        if nB:
            ax3.scatter(*sc["B"][:nB].T, c=ORANGE, marker="^", s=52, label="Agent B claims")
        if st >= 2:
            ax3.scatter(*sc["gA"], c=BLUE, marker="D", s=170, edgecolors="black", label="geometric median A")
            ax3.scatter(*sc["gB"], c=ORANGE, marker="D", s=170, edgecolors="black", label="geometric median B")
            ax3.plot(*zip(sc["gA"], sc["gB"]), c="black", lw=1.5)
            mid = (sc["gA"] + sc["gB"]) / 2
            ax3.text(*mid, "  cos = %.3f" % sc["cos"], fontsize=10, weight="bold")
        ax3.view_init(elev=22, azim=20 + 0.9 * frame_in_scene)
        ax3.set_xlabel("PC1"); ax3.set_ylabel("PC2"); ax3.set_zlabel("PC3")
        ax3.tick_params(labelsize=6)
        ax3.legend(loc="upper left", fontsize=7, frameon=False)
        ax3.set_title("Sentence embeddings (768-d, local GPU) projected to 3D by PCA", fontsize=9)
        evs = sc["ledger"]
        k = len(evs) if st >= 3 else int(np.ceil(len(evs) * min(1.0, t / 0.58)))
        axL.text(0, 1.0, "Provenance ledger (hash chain)", fontsize=10, weight="bold", va="top")
        for i, e in enumerate(evs[:k]):
            d = e["data"]
            detail = d.get("source", "") or ("->" + d.get("to", "")) or ""
            if e["kind"] == "report_submitted":
                detail = "cites " + ",".join(d.get("cited", []))
            if e["kind"] == "message_received":
                detail = "from " + d.get("sender", "")
            axL.text(0, 0.88 - 0.115 * i, "#%d %-17s %s  %s  [%s]" % (e["n"], e["kind"], e["agent"][-6:], detail, e["hash"][:6]), fontsize=7, family="monospace", va="top")
        bars = [("F2 cosine", sc["feats"]["cos"]), ("F4 STP-AR", sc["feats"]["stpar"]), ("F6 RCC-v3.3", sc["feats"]["rcc_ar"]),
                ("F8b Argon F44", sc["feats"]["argon_claim_overlap"]), ("S1 unsupported", sc["feats"]["unsup_own"]),
                ("LLM report only", sc["llm1"]["p_copying"]), ("LLM + sources", sc["llm2"]["p_copying"])]
        grow = 0.0 if st < 3 else min(1.0, (t - 0.58) / 0.14)
        axB.barh(range(len(bars)), [v * grow for _, v in bars], color=[BLUE, BLUE, BLUE, BLUE, GREY, ORANGE, ORANGE])
        axB.set_yticks(range(len(bars))); axB.set_yticklabels([b for b, _ in bars], fontsize=7); axB.invert_yaxis(); axB.set_xlim(0, 1)
        axB.set_title("Monitor scores (higher = more suspicious)", fontsize=8)
        msgs = ["Agent A writes its report from its source.",
                "Agent B writes its report%s." % (" after receiving A's report (see ledger)" if sc["type"].startswith("COPY") else " from its own source"),
                "Sentences become points; each report gets a robust centre (geometric median).",
                "Monitors compare the reports. Formula scores look at content only; the ledger records the process.",
                "Ground truth (set by the controller, never seen by monitors): copying=%d  non-independent=%d  false provenance=%d" % tuple(sc["truth"].values())]
        cap.set_text(msgs[st])

    def draw_text_slide(lines, sizes):
        ax3.set_visible(False); axL.set_visible(False); axB.set_visible(False); full.set_visible(True); full.cla(); full.axis("off")
        title.set_text(""); cap.set_text("")
        y = 0.86
        for ln, sz in zip(lines, sizes):
            full.text(0.5, y, ln, ha="center", va="center", fontsize=sz); y -= 0.045 + sz / 700

    def frame(i):
        if i < intro_n:
            draw_text_slide(["Trust the Report or Check the Artifact?", "Oversight of evidence provenance in multi-agent LLM systems",
                             "Real runs: Gemma 4 agents on TLS course materials", "Swarm Alignment Hackathon 2026 - Track 4 (with Tracks 1-3 support)"], [24, 14, 12, 12])
        elif i < intro_n + SCENE_FRAMES * len(scenes):
            j = i - intro_n
            draw_scene(scenes[j // SCENE_FRAMES], (j % SCENE_FRAMES) / SCENE_FRAMES, j % SCENE_FRAMES)
        else:
            lines = ["Pooled test results, target A (copying), 5%-FPR threshold", ""]
            sizes = [16, 8]
            if outro:
                for n, r, f_, b in outro:
                    lines.append("%-26s recall %.2f   FPR %.2f   Brier %.3f" % (n, r, f_, b)); sizes.append(11)
            else:
                lines.append("(final metrics not available when this video was rendered)"); sizes.append(11)
            lines += ["", "Numbers come from raw result files. Limits: one model (Gemma 4), instructed agents, controller-written ledger."]; sizes += [8, 9]
            draw_text_slide(lines, sizes)
        return []

    out = os.path.join(ROOT, "08_VISUAL_EVIDENCE", "video_documentation")
    os.makedirs(out, exist_ok=True)
    name = "process_replay%s%s.mp4" % (SUF, "_fast" if FAST else "")
    matplotlib.rcParams["animation.ffmpeg_path"] = "ffmpeg"
    writer = animation.FFMpegWriter(fps=FPS, codec="libx264", extra_args=["-pix_fmt", "yuv420p", "-crf", "23"])
    ani = animation.FuncAnimation(fig, frame, frames=total, blit=False)
    ani.save(os.path.join(out, name), writer=writer)
    print("saved", name, total, "frames")


if __name__ == "__main__":
    main()
