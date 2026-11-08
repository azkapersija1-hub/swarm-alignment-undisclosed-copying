"""Assembles a 3-4 minute demo video from real outputs: title card, architecture figure, process replay, performance replay, result figures, findings and limits slides.
All numbers on the findings slide are read from result files. Usage: make_demo_video.py"""
import csv
import json
import os
import subprocess
import sys

import matplotlib
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
RT = os.path.dirname(HERE)
RES = os.path.join(RT, "results")
FIG = os.path.join(RES, "figures")
VID = os.path.join(RT, "videos")
TMP = os.path.join(VID, "_demo_tmp")
FONT = os.path.join(os.path.dirname(matplotlib.__file__), "mpl-data", "fonts", "ttf", "DejaVuSans.ttf")
FONTB = os.path.join(os.path.dirname(matplotlib.__file__), "mpl-data", "fonts", "ttf", "DejaVuSans-Bold.ttf")
ARMS = ["gemma_homog", "qwen_homog", "deepseek_homog", "het_gemma_qwen", "het_gemma_deepseek"]
F2, F9, F11 = "F2 embedding cosine", "F9b ensemble + source checks", "F11x candidate ensemble"


def jl(tag, name):
    return json.load(open(os.path.join(RES, tag, name), encoding="utf-8"))


def findings():
    prim = [jl(t, "primary_comparisons.json")["target_A"] for t in ARMS]
    f2 = [p["auroc"][F2] for p in prim]
    f11 = [p["auroc"][F11] for p in prim]
    gain = [p["auroc"][F11] - p["auroc"][F9] for p in prim]
    ok = sum(bool(p["primary_success"]) for p in prim)
    fal = {t: jl(t, "falsifiers.json") for t in ARMS}
    held = [h for h in ["ARG-H%d" % i for i in range(1, 11)] if all(fal[t][h]["falsified"] is False for t in ARMS)]
    failed = [h for h in ["ARG-H%d" % i for i in range(1, 11)] if all(fal[t][h]["falsified"] is True for t in ARMS)]
    rows = {r["type"]: r for r in csv.DictReader(open(os.path.join(RES, "gemma_homog", "results_per_type.csv"), encoding="utf-8"))
            if r["target"] == "A_primary" and r["monitor"] == F11}
    main = {r["monitor"]: r for r in csv.DictReader(open(os.path.join(RES, "gemma_homog", "results_main.csv"), encoding="utf-8")) if r["target"] == "A_primary"}
    tr = []
    for t in ARMS[1:]:
        for r in csv.DictReader(open(os.path.join(RES, t, "transfer_from_gemma_homog.csv"), encoding="utf-8")):
            if r["target"] == "A_primary" and r["monitor"] == F11:
                tr.append(float(r["auroc"]))
    return dict(f2=(min(f2), max(f2)), f11=(min(f11), max(f11)), gain=(min(gain), max(gain)), ok=ok, n=len(ARMS), held=held, failed=failed,
                lex=float(rows["ADAPT_LEX_INJECT"]["flag_rate"]), split=float(rows["ADAPT_SPLIT_2"]["flag_rate"]),
                log_anch=float(main["F10 ensemble + ledger [full_anchored]"]["auroc"]), log_none=float(main["F10 ensemble + ledger [none]"]["auroc"]), tr=(min(tr), max(tr)))


def slide(path, title, lines, size=34, tsize=48):
    im = Image.new("RGB", (1280, 720), "white")
    d = ImageDraw.Draw(im)
    ft, fb = ImageFont.truetype(FONTB, tsize), ImageFont.truetype(FONT, size)
    d.text((70, 60), title, fill="#111111", font=ft)
    y = 190
    for ln in lines:
        d.text((70, y), ln, fill="#222222", font=fb)
        y += int(size * 1.75)
    im.save(path)


def seg_from_image(img, secs, out):
    vf = "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2:white,format=yuv420p"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-t", str(secs), "-i", img, "-vf", vf, "-r", "24", "-c:v", "libx264", "-crf", "23", out], check=True)


def seg_from_video(src, out):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-vf", "scale=1280:720,format=yuv420p", "-r", "24", "-c:v", "libx264", "-crf", "23", out], check=True)


def main():
    os.makedirs(TMP, exist_ok=True)
    f = findings()
    pct = lambda x: "%.0f%%" % (100 * x)
    slides = {
        "s_title": ("Cosine Is Not Enough", ["Detecting undisclosed copying between LLM agents", "A pre-registered test bed (Track 4: Multi-Agent Oversight and Control)", "", "Authors: to be filled in", "All numbers in this video are read from result files."], 6),
        "s_find": ("What we found", [
            "Embedding cosine alone: AUROC %.2f to %.2f (near chance)." % f["f2"],
            "Source-aware ensemble F11x: AUROC %.2f to %.2f in %d arms." % (f["f11"][0], f["f11"][1], f["n"]),
            "Gain over our strong baseline F9b: only %.2f to %.2f AUROC." % f["gain"],
            "Pre-declared primary comparison passed in %d of %d arms." % (f["ok"], f["n"]),
            "Held in every arm: %s." % ", ".join(h.replace("ARG-", "") for h in f["held"]),
            "Failed in every arm: %s." % ", ".join(h.replace("ARG-", "") for h in f["failed"]),
            "Adaptive attacks: F11x flags %s (lexical injection), %s (split citation)." % (pct(f["lex"]), pct(f["split"])),
            "Anchored log: AUROC %.2f vs %.2f without log; fit from one model transfers at %.2f to %.2f." % (f["log_anch"], f["log_none"], f["tr"][0], f["tr"][1])], 22),
        "s_lim": ("Limits we report", [
            "Same 109 documents in every arm; copying is instructed, not spontaneous.",
            "The log is written by the controller; one embedding model.",
            "The LLM monitor is Qwen only (Gemma quota ended during scoring).",
            "Offline audit of finished episodes, not real-time oversight.",
            "Targets A and C have identical labels in this design.",
            "Perfect AUROC on single contrasts reflects an easy synthetic design."], 28),
        "s_end": ("Thank you", ["Code, prompts, hashes and deviations are in the package.", "Formulas, hypotheses and falsifiers were locked before scoring."], 5),
    }
    paths = {}
    for k, (t, ls, secs) in slides.items():
        img = os.path.join(TMP, k + ".png")
        slide(img, t, ls, size=22 if k == "s_find" else 30, tsize=46)
        paths[k] = (img, secs)
    order = [("s_title", None), ("fig0c_arch3d_color_en.png", 14), ("process", None), ("performance", None), ("fig1_auroc_by_arm.png", 15), ("fig2_flag_rates_by_type.png", 14),
             ("fig4_falsifier_scoreboard.png", 14), ("fig3_log_degradation.png", 12), ("s_find", None), ("s_lim", None), ("s_end", None)]
    segs = []
    for i, (name, secs) in enumerate(order):
        out = os.path.join(TMP, "seg%02d.mp4" % i)
        if name in paths:
            seg_from_image(paths[name][0], paths[name][1], out)
        elif name == "process":
            seg_from_video(os.path.join(VID, "process_replay_retest.mp4"), out)
        elif name == "performance":
            seg_from_video(os.path.join(VID, "performance_replay_retest.mp4"), out)
        else:
            seg_from_image(os.path.join(FIG, name), secs, out)
        segs.append(out)
    lst = os.path.join(TMP, "list.txt")
    with open(lst, "w", encoding="utf-8") as fh:
        for s in segs:
            fh.write("file '%s'\n" % s.replace("\\", "/"))
    final = os.path.join(VID, "demo_video_3min.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", final], check=True)
    dur = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", final], capture_output=True, text=True).stdout.strip()
    print("saved", final, "duration %.1f s" % float(dur))


if __name__ == "__main__":
    sys.exit(main())
