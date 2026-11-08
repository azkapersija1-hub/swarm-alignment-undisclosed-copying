"""Frame-by-frame performance replay of the whole test run: scenario stream, LLM call latency/tokens, agent behaviour, running monitor metrics, GPU.
All series come from raw files: llm_runs_*/rep*.jsonl, metrics/pooled_predictions.json, gpu_samples_*.jsonl.
Honest framing: monitor curves replay the FINAL predictions in execution order (they are not live retraining).
Usage: SWARM_DATASET=tls py -3.12 -I -B -X utf8 animate_performance.py [fast]"""
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
ROOT = os.path.dirname(HERE)
SUF = "" if os.environ.get("SWARM_DATASET", "synthetic") == "synthetic" else "_" + os.environ["SWARM_DATASET"]
FAST = len(sys.argv) > 1 and sys.argv[1] == "fast"
FRAMES = 150 if FAST else 1200
FPS = 24
BLUE, ORANGE, GREEN, GREY, RED, PURPLE = "#0072B2", "#E69F00", "#009E73", "#8c8c8c", "#D55E00", "#6a3d9a"
TYPES = ["IND_SAME", "IND_DIFF", "NOSRC_SAME", "TWIN_H", "NEAR_H", "SHARED_OK", "COPY_LIT", "COPY_PARA", "COPY_TWIN", "COPY_COVER"]
TCOL = dict(zip(TYPES, ["#56B4E9", "#0072B2", "#CC79A7", "#009E73", "#8fd14f", "#E69F00", "#F0E442", "#D55E00", "#a6322b", "#6a3d9a"]))
MONS = [("F0b LLM report-only", "LLM reads report only", ORANGE), ("F4 STP-AR", "STP-AR (formula)", BLUE),
        ("F9 formula ensemble (artifact only)", "formula ensemble", GREEN), ("F10 ensemble + ledger [full]", "ensemble + ledger", PURPLE)]


def load_runs():
    recs = []
    for p in sorted(glob.glob(os.path.join(ROOT, "06_RAW_RESULTS", "llm_runs" + SUF, "rep*.jsonl"))):
        recs += [json.loads(l) for l in open(p, encoding="utf-8")]
    return recs


def main():
    recs = load_runs()
    N = len(recs)
    types = [r["scenario"]["type"] for r in recs]
    # LLM calls (unique reports), in execution order
    calls, seen = [], set()
    for r in recs:
        for key in ("report_a", "report_b"):
            rep = r[key]
            k = (r["replicate"], json.dumps(rep["claims"])[:80])
            if k in seen:
                continue
            seen.add(k)
            calls.append((len(calls), rep["seconds"], rep.get("eval_count") or 0, rep.get("attempts", 1), r["scenario"]["scenario_id"], r["scenario"]["type"]))
    calls = np.array([(c[0], c[1], c[2], c[3]) for c in calls], dtype=float)
    # per-scenario progress of each call (call index at scenario i)
    call_at = np.searchsorted(calls[:, 0], np.linspace(0, len(calls) - 1, N))
    copy_scn = [i for i, t in enumerate(types) if t.startswith("COPY")]
    comply = np.array([recs[i]["realized_overlap"] >= 0.5 for i in copy_scn], dtype=float)
    pp = os.path.join(ROOT, "07_STATISTICAL_ANALYSIS", "metrics" + SUF + os.environ.get("SWARM_METRICS_TAG", ""), "pooled_predictions.json")
    preds = json.load(open(pp)) if os.path.isfile(pp) else {}
    gp = sorted(glob.glob(os.path.join(ROOT, "06_RAW_RESULTS", "gpu_samples_scoring%s.jsonl" % SUF)))
    G = [json.loads(l) for l in open(gp[0], encoding="utf-8") if l.strip()] if gp else []
    gt = np.array([g["t"] for g in G]); gt = (gt - gt[0]) / 60 if len(G) else np.array([0.0])
    gu, gtemp = (np.array([float(g["utilization.gpu"]) for g in G]), np.array([float(g["temperature.gpu"]) for g in G])) if G else (np.zeros(1), np.zeros(1))

    fig = plt.figure(figsize=(12.8, 7.2), dpi=100)
    gs = fig.add_gridspec(2, 3, left=0.05, right=0.985, top=0.88, bottom=0.10, wspace=0.28, hspace=0.38)
    a1, a2, a3, a4, a5, a6 = [fig.add_subplot(gs[i // 3, i % 3]) for i in range(6)]
    head = fig.text(0.05, 0.945, "", fontsize=13, weight="bold")
    foot = fig.text(0.05, 0.03, "", fontsize=9)
    cols, rows = 41, int(np.ceil(N / 41))
    xy = np.array([(i % cols, i // cols) for i in range(N)])
    colors = [TCOL.get(t, GREY) for t in types]

    def running(mon, target, upto, key):
        d = preds.get("%s|%s" % (mon, target))
        if not d:
            return None
        y, fl = np.array(d["y"]), np.array(d["flag"], dtype=bool)
        k = max(1, int(np.ceil(upto * len(y))))
        yy, ff = y[:k], fl[:k]
        if key == "recall":
            return (ff & (yy == 1)).sum() / max(1, (yy == 1).sum()) if (yy == 1).sum() >= 8 else np.nan
        return (ff & (yy == 0)).sum() / max(1, (yy == 0).sum()) if (yy == 0).sum() >= 8 else np.nan

    hist = {}

    def frame(f):
        p = (f + 1) / FRAMES
        k = max(1, int(np.ceil(p * N)))
        c = max(1, int(np.ceil(p * len(calls))))
        for a in (a1, a2, a3, a4, a5, a6):
            a.cla()
        a1.scatter(xy[:k, 0], -xy[:k, 1], c=colors[:k], s=9, marker="s")
        a1.scatter(*xy[k - 1] * np.array([1, -1]), s=90, facecolors="none", edgecolors="black", lw=1.2)
        a1.set_xlim(-1, cols); a1.set_ylim(-rows, 1); a1.axis("off")
        a1.set_title("Scenarios executed: %d / %d" % (k, N), fontsize=9)
        for j, t in enumerate(TYPES[:5] + ["..."]):
            pass
        a1.text(0, -rows - 0.2, "types: " + ", ".join(TYPES[:4]) + ", ...", fontsize=6, va="top")
        a2.scatter(calls[:c, 0], calls[:c, 1], s=5, c=BLUE, alpha=0.5)
        if c > 10:
            a2.plot(calls[:c, 0], np.convolve(calls[:c, 1], np.ones(10) / 10, mode="same"), c=RED, lw=1.2)
        a2.set_xlim(0, len(calls)); a2.set_ylim(0, max(15, calls[:, 1].max() * 1.05))
        a2.set_title("LLM call latency, seconds (n=%d, mean %.1fs, ~%.0f tok/s)" % (c, calls[:c, 1].mean(), calls[:c, 2].sum() / max(1e-9, calls[:c, 1].sum())), fontsize=8)
        a2.set_xlabel("call index"); a2.spines[["top", "right"]].set_visible(False)
        first_ok = np.cumsum(calls[:, 3] == 1) / np.arange(1, len(calls) + 1)
        a3.plot(np.arange(c), first_ok[:c], c=GREEN, label="valid JSON on first attempt")
        ncs = int(np.sum(np.array(copy_scn) < k))
        if ncs > 3:
            a3.plot(np.array(copy_scn[:ncs]) / N * len(calls), np.cumsum(comply[:ncs]) / np.arange(1, ncs + 1), c=RED, label="copy verified by reused numbers (only where text has numbers)")
        a3.set_xlim(0, len(calls)); a3.set_ylim(0, 1.02); a3.legend(fontsize=7, frameon=False, loc="lower left")
        a3.set_title("Agent behaviour (running rates; copy check limited to numeric text)", fontsize=8); a3.spines[["top", "right"]].set_visible(False)
        for mon, lab, col in MONS:
            xs = np.linspace(0.05, p, max(2, int(60 * p)))
            for ax, key in ((a4, "recall"), (a5, "fpr")):
                ys = [running(mon, "copy", x, key) for x in xs]
                if preds and not all(v is None for v in ys):
                    ax.plot(xs * N, ys, c=col, label=lab)
        a4.set_ylim(0, 1.02); a4.set_xlim(0, N); a4.set_title("Running recall (target A: copying)", fontsize=9)
        a5.set_ylim(0, 1.02); a5.set_xlim(0, N); a5.axhline(0.05, c=GREY, ls="--", lw=0.8); a5.set_title("Running false positive rate", fontsize=9)
        if preds:
            a4.legend(fontsize=6.5, frameon=False, loc="lower right")
        else:
            a4.text(0.5, 0.5, "pooled predictions not available", ha="center", transform=a4.transAxes)
        for a in (a4, a5):
            a.spines[["top", "right"]].set_visible(False); a.set_xlabel("scenario index")
        gi = max(1, int(np.ceil(p * len(gt))))
        a6.plot(gt[:gi], gu[:gi], c=BLUE, label="utilisation %")
        a6.plot(gt[:gi], gtemp[:gi], c=RED, label="temp C")
        a6.set_xlim(0, gt[-1] if len(gt) > 1 else 1); a6.set_ylim(0, 100); a6.legend(fontsize=7, frameon=False, loc="upper right")
        a6.set_title("Local GPU during scoring (embeddings)", fontsize=9); a6.set_xlabel("minutes"); a6.spines[["top", "right"]].set_visible(False)
        head.set_text("Test run replay: Gemma 4 agents on TLS materials  |  scenario %d/%d  |  now: %s" % (k, N, types[k - 1]))
        foot.set_text("Series from raw logs. LLM agents run remotely (not on the local GPU). Monitor curves replay final predictions in execution order (test items only).")
        return []

    out = os.path.join(ROOT, "08_VISUAL_EVIDENCE", "video_documentation")
    os.makedirs(out, exist_ok=True)
    name = "performance_replay%s%s.mp4" % (SUF, "_fast" if FAST else "")
    matplotlib.rcParams["animation.ffmpeg_path"] = "ffmpeg"
    writer = animation.FFMpegWriter(fps=FPS, codec="libx264", extra_args=["-pix_fmt", "yuv420p", "-crf", "23"])
    animation.FuncAnimation(fig, frame, frames=FRAMES, blit=False).save(os.path.join(out, name), writer=writer)
    print("saved", name, FRAMES, "frames; scenarios", N, "calls", len(calls))


if __name__ == "__main__":
    main()
