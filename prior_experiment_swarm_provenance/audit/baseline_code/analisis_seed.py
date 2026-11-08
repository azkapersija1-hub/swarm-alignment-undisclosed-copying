"""Kekokohan antar-seed: rerata +- simpangan baku per seed (skor saja, tanpa teks buku)."""
import glob, json, math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import lab
seeds = [json.load(open(f, encoding="utf-8")) for f in sorted(glob.glob(os.path.join(HERE, "hasil", "seed_*.json")))]
def ms(v):
    m = sum(v) / len(v); sd = math.sqrt(sum((x - m) ** 2 for x in v) / (len(v) - 1)) if len(v) > 1 else 0.0
    return m, sd
nama = ["A1 percaya klaim (laporan)", "A2 ringkasan mirip (laporan)", "B1 kutipan ada di sumber (artefak)", "B2 artefak mirip (artefak)", "B3 sumber kembar (artefak)", "B4 embedding artefak (artefak)"]
print("FPR per seed (jujur):")
for n in nama:
    v = [sum(b["bendera"][n] for b in s["baris"] if b["tipe"] == "H") / sum(1 for b in s["baris"] if b["tipe"] == "H") for s in seeds]
    print("  %-38s %.3f +- %.3f  min %.3f max %.3f" % (n, *ms(v), min(v), max(v)))
for tipe in ("C1", "C2"):
    for lv in (4, 5):
        print("TPR %s L%d:" % (tipe, lv))
        for n in nama:
            v = []
            for s in seeds:
                sub = [b for b in s["baris"] if b["tipe"] == tipe and b["level"] == lv]
                v.append(sum(b["bendera"][n] for b in sub) / len(sub))
            print("  %-38s %.3f +- %.3f  min %.3f max %.3f" % (n, *ms(v), min(v), max(v)))
print("Brier semua level per seed:")
for n in nama:
    v = [lab.brier([b["p"][n] for b in s["baris"]], [b["label"] for b in s["baris"]]) for s in seeds]
    print("  %-38s %.3f +- %.3f" % (n, *ms(v)))
d = [lab.brier([b["p"][nama[3]] for b in s["baris"]], [b["label"] for b in s["baris"]]) - lab.brier([b["p"][nama[5]] for b in s["baris"]], [b["label"] for b in s["baris"]]) for s in seeds]
print("Selisih Brier B2-B4 per seed:", [round(x, 4) for x in d], "semua > 0:", all(x > 0 for x in d))
