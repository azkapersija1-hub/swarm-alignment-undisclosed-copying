"""Verifikasi independen klaim laporan dari hasil/seed_*.json (TANPA mengimpor lab.py / metrik.py).
Pemakaian: py -3.12 -I -B -X utf8 verifikasi_klaim.py <folder_seed_json> [keluaran.json]
"""
import glob
import json
import os
import sys

NAMA = {"A1": "A1 percaya klaim (laporan)", "A2": "A2 ringkasan mirip (laporan)",
        "B1": "B1 kutipan ada di sumber (artefak)", "B2": "B2 artefak mirip (artefak)",
        "B3": "B3 sumber kembar (artefak)", "B4": "B4 embedding artefak (artefak)",
        "BU": "B gabungan (B1|B2|B3|B4)"}


def muat(folder):
    seeds = [json.load(open(f, encoding="utf-8")) for f in sorted(glob.glob(os.path.join(folder, "seed_*.json")))]
    return seeds, [b for s in seeds for b in s["baris"]]


def confusion(baris, kunci):
    tp = sum(1 for b in baris if b["label"] == 1 and b["bendera"][kunci])
    fn = sum(1 for b in baris if b["label"] == 1 and not b["bendera"][kunci])
    fp = sum(1 for b in baris if b["label"] == 0 and b["bendera"][kunci])
    tn = sum(1 for b in baris if b["label"] == 0 and not b["bendera"][kunci])
    prec = tp / (tp + fp) if tp + fp else float("nan")
    rec = tp / (tp + fn) if tp + fn else float("nan")
    f1 = 2 * prec * rec / (prec + rec) if prec + rec else float("nan")
    return {"tp": tp, "fp": fp, "tn": tn, "fn": fn, "precision": prec, "recall": rec, "fpr": fp / (fp + tn) if fp + tn else float("nan"), "f1": f1}


def brier(baris, kunci):
    return sum((b["p"][kunci] - b["label"]) ** 2 for b in baris) / len(baris)


def main():
    folder = sys.argv[1]
    seeds, semua = muat(folder)
    out = {"n_seed": len(seeds), "n_skenario": len(semua), "per_seed": [len(s["baris"]) for s in seeds],
           "per_tipe": {t: sum(1 for b in semua if b["tipe"] == t) for t in sorted({b["tipe"] for b in semua})},
           "confusion": {}, "brier": {}}
    base = sum(b["label"] for b in semua) / len(semua)
    out["prevalensi_salin"] = base
    out["brier_acuan_tanpa_informasi"] = base * (1 - base)
    for kode, kunci in NAMA.items():
        out["confusion"][kode] = confusion(semua, kunci)
        if kunci in semua[0]["p"]:
            out["brier"][kode] = brier(semua, kunci)
    if len(sys.argv) > 2:
        json.dump(out, open(sys.argv[2], "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
