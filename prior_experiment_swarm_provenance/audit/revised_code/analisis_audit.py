"""Analisis lanjutan hasil_v2: metrik lengkap, kontrol negatif sumber kembar, sensitivitas ambang,
Brier seimbang, dan interval kepercayaan bootstrap BERKLASTER (klaster = buku sumber bot-1).

Catatan statistik (dinyatakan eksplisit):
- Semua angka di sini DESKRIPTIF; interval bootstrap adalah ukuran ketidakpastian, bukan uji hipotesis formal.
- Lima seed BUKAN lima sampel independen: buku, potongan, dan pasangan kembar yang sama muncul di banyak seed.
  Karena itu bootstrap me-resample BUKU (semua skenario seed-pooled milik satu buku diambil bersama).
  Klaster hanya memakai buku bot-1; ketergantungan lewat buku bot-2 tidak dimodelkan (keterbatasan).
Pemakaian: py -3.12 -I -B -X utf8 analisis_audit.py <hasil_v2> <baseline_verifikasi.json> <keluar_dir>
"""
import csv
import glob
import json
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lab  # noqa: E402

KODE = {"A2": "A2 ringkasan mirip (laporan)", "B1": "B1 kutipan ada di sumber (artefak)",
        "B2": "B2 artefak mirip (artefak)", "B3": "B3 sumber kembar (artefak)",
        "B4": "B4 embedding artefak (artefak)", "BU": "B gabungan (B1|B2|B3|B4)"}
GRUP = ("H", "C1", "C2", "HT", "HT2")
B_BOOT = 2000
BENIH_BOOT = 20261107


def muat(folder):
    seeds = [json.load(open(f, encoding="utf-8")) for f in sorted(glob.glob(os.path.join(folder, "seed_*.json")))]
    return seeds, [b for s in seeds for b in s["baris"]]


def agregat_per_buku(baris):
    """buku -> {(grup, kode): [n, bendera, jumlah_kuadrat_brier]}"""
    out = {}
    for b in baris:
        d = out.setdefault(b["meta"]["b1"], {})
        for k, nama in KODE.items():
            sel = d.setdefault((b["tipe"], k), [0, 0, 0.0])
            sel[0] += 1
            sel[1] += int(b["bendera"][nama])
            if nama in b["p"]:
                sel[2] += (b["p"][nama] - b["label"]) ** 2
    return out


def jumlah(agg, buku_list):
    tot = {}
    for bk in buku_list:
        for kunci, v in agg[bk].items():
            t = tot.setdefault(kunci, [0, 0, 0.0])
            t[0] += v[0]; t[1] += v[1]; t[2] += v[2]
    return tot


def metrik_dari(tot, k):
    g = lambda grup: tot.get((grup, k), [0, 0, 0.0])
    n_c1, n_c2, n_h = g("C1")[0], g("C2")[0], g("H")[0]
    tp = g("C1")[1] + g("C2")[1]
    fn = n_c1 + n_c2 - tp
    fp, tn = g("H")[1], n_h - g("H")[1]
    prec = tp / (tp + fp) if tp + fp else float("nan")
    rec = tp / (tp + fn) if tp + fn else float("nan")
    f1 = 2 * prec * rec / (prec + rec) if prec + rec else float("nan")
    n_all = n_c1 + n_c2 + n_h
    brier = (g("C1")[2] + g("C2")[2] + g("H")[2]) / n_all if n_all else float("nan")
    if k == "BU":          # gabungan OR tidak punya probabilitas -> Brier tidak terdefinisi
        brier = float("nan")
    # Brier seimbang: rata-rata Brier kelas jujur (H) dan kelas salinan (C1+C2), bobot sama (prevalensi 50%)
    b_h = g("H")[2] / n_h if n_h else float("nan")
    b_c = (g("C1")[2] + g("C2")[2]) / (n_c1 + n_c2) if n_c1 + n_c2 else float("nan")
    out = {"deteksi_C1": g("C1")[1] / n_c1 if n_c1 else float("nan"),
           "deteksi_C2": g("C2")[1] / n_c2 if n_c2 else float("nan"),
           "recall": rec, "fpr_H": fp / n_h if n_h else float("nan"), "precision": prec, "f1": f1,
           "brier": brier, "brier_seimbang": (b_h + b_c) / 2 if k != "BU" else float("nan"),
           "fpr_HT": g("HT")[1] / g("HT")[0] if g("HT")[0] else float("nan"),
           "fpr_HT2": g("HT2")[1] / g("HT2")[0] if g("HT2")[0] else float("nan"),
           "tp": tp, "fp": fp, "tn": tn, "fn": fn}
    return out


def kuantil(v, q):
    v = sorted(x for x in v if not math.isnan(x))
    if not v:
        return float("nan")
    return v[min(len(v) - 1, max(0, int(round(q * (len(v) - 1)))))]


def bootstrap(agg, kodes, rng):
    buku = sorted(agg)
    hasil = {k: {} for k in kodes}
    selisih = []
    for _ in range(B_BOOT):
        pilih = [rng.choice(buku) for _ in buku]
        tot = jumlah(agg, pilih)
        m = {k: metrik_dari(tot, k) for k in kodes}
        for k in kodes:
            for nm, v in m[k].items():
                hasil[k].setdefault(nm, []).append(v)
        selisih.append(m["B2"]["brier"] - m["B4"]["brier"])
    ci = {k: {nm: (kuantil(v, 0.025), kuantil(v, 0.975)) for nm, v in d.items()} for k, d in hasil.items()}
    return ci, (kuantil(selisih, 0.025), kuantil(selisih, 0.975))


def sensitivitas_ambang(seeds, target_list=(0.01, 0.025, 0.05, 0.10, 0.20)):
    """Ambang dari persentil skor jujur-kalibrasi tiap seed (aturan SAMA dg baseline), evaluasi di data uji seed itu."""
    out = []
    for t in target_list:
        for k, nama in KODE.items():
            if k == "BU":
                continue
            cnt = {g: [0, 0] for g in GRUP}
            for s in seeds:
                th = lab.ambang_dari_kalibrasi(s["kalib_skor_jujur"][nama], t)
                for b in s["baris"]:
                    cnt[b["tipe"]][1] += 1
                    cnt[b["tipe"]][0] += int(b["skor"][nama] > th)
            r = {g: (cnt[g][0] / cnt[g][1] if cnt[g][1] else float("nan")) for g in GRUP}
            out.append({"fpr_target": t, "metode": k, "FPR_H": r["H"], "deteksi_C1": r["C1"], "deteksi_C2": r["C2"],
                        "FPR_HT": r["HT"], "FPR_HT2": r["HT2"]})
    return out


def per_seed(seeds):
    out = []
    for s in seeds:
        for k, nama in KODE.items():
            tot = {}
            for b in s["baris"]:
                sel = tot.setdefault((b["tipe"], k), [0, 0, 0.0])
                sel[0] += 1
                sel[1] += int(b["bendera"][nama])
                if nama in b["p"]:
                    sel[2] += (b["p"][nama] - b["label"]) ** 2
            m = metrik_dari(tot, k)
            out.append({"seed": s["seed"], "metode": k, **{a: m[a] for a in ("deteksi_C1", "deteksi_C2", "fpr_H", "fpr_HT", "fpr_HT2", "brier")}})
    return out


def ppv(tpr, fpr, prev):
    return tpr * prev / (tpr * prev + fpr * (1 - prev)) if (tpr * prev + fpr * (1 - prev)) else float("nan")


def main():
    folder, base_json, keluar = sys.argv[1], sys.argv[2], sys.argv[3]
    os.makedirs(keluar, exist_ok=True)
    seeds, baris = muat(folder)
    base = json.load(open(base_json, encoding="utf-8"))
    agg = agregat_per_buku(baris)
    tot = jumlah(agg, sorted(agg))
    kodes = list(KODE)
    rng = random.Random(BENIH_BOOT)
    ci, ci_selisih = bootstrap(agg, kodes, rng)
    M = {k: metrik_dari(tot, k) for k in kodes}
    n = {g: sum(1 for b in baris if b["tipe"] == g) for g in GRUP}
    hasil = {"n_seed": len(seeds), "n_total": len(baris), "n_per_grup": n, "n_klaster_buku": len(agg),
             "n_kembar_uji": [s["n_kembar_uji"] for s in seeds], "metrik": M, "ci_bootstrap_buku": ci,
             "brier_b2_minus_b4": {"nilai": M["B2"]["brier"] - M["B4"]["brier"], "ci": ci_selisih},
             "sensitivitas_ambang": sensitivitas_ambang(seeds), "per_seed": per_seed(seeds),
             "ppv_B4": {str(p): ppv((M["B4"]["recall"]), M["B4"]["fpr_H"], p) for p in (0.01, 0.1, 0.5)},
             "ppv_B4_dengan_fpr_HT": {str(p): ppv(M["B4"]["recall"], M["B4"]["fpr_HT"], p) for p in (0.01, 0.1, 0.5)}}
    json.dump(hasil, open(os.path.join(keluar, "analisis_audit.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    # RESULTS_COMPARISON.csv
    rows = []
    bc = base["confusion"]
    rows.append(("jumlah_skenario_H_C1_C2", "semua", base["n_skenario"], n["H"] + n["C1"] + n["C2"], "", "Kumpulan pasangan sumber kembar berbeda (hash deterministik) dan n_seed sama; HT/HT2 dilaporkan terpisah"))
    for k in kodes:
        c = bc[k]
        bm = {"recall": c["recall"], "fpr_H": c["fpr"], "precision": c["precision"], "f1": c["f1"], "brier": base["brier"].get(k)}
        for nm in ("recall", "fpr_H", "precision", "f1", "brier"):
            baru = M[k][nm]
            lama = bm[nm]
            lo, hi = ci[k][nm]
            rows.append((nm, k, "" if lama is None else round(lama, 4), round(baru, 4),
                         "" if lama is None else round(baru - lama, 4), "CI95 bootstrap-buku [%.4f, %.4f]" % (lo, hi)))
        for nm in ("fpr_HT", "fpr_HT2", "brier_seimbang"):
            lo, hi = ci[k][nm]
            rows.append((nm, k, "tidak ada di baseline", round(M[k][nm], 4), "", "CI95 bootstrap-buku [%.4f, %.4f]" % (lo, hi)))
    with open(os.path.join(keluar, "RESULTS_COMPARISON.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["metrik", "metode", "baseline_lama", "hasil_baru", "perubahan", "keterangan"])
        w.writerows(rows)
    print(json.dumps({"n": n, "klaster": len(agg), "B4": M["B4"], "B2": M["B2"], "selisih": hasil["brier_b2_minus_b4"]}, indent=1))


if __name__ == "__main__":
    main()
