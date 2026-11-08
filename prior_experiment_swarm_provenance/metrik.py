"""Semua angka laporan dihitung dari hasil/seed_*.json (skor saja). Satu sumber kebenaran untuk teks dan tabel."""
import glob
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lab  # noqa: E402

KODE = {
    "A1": "A1 percaya klaim (laporan)",
    "A2": "A2 ringkasan mirip (laporan)",
    "B1": "B1 kutipan ada di sumber (artefak)",
    "B2": "B2 artefak mirip (artefak)",
    "B3": "B3 sumber kembar (artefak)",
    "B4": "B4 embedding artefak (artefak)",
    "BU": "B gabungan (B1|B2|B3|B4)",
}
N_LEVEL = len(lab.LEVEL_NAMA)


def muat():
    return [json.load(open(f, encoding="utf-8")) for f in sorted(glob.glob(os.path.join(HERE, "hasil", "seed_*.json")))]


def _msd(v):
    m = sum(v) / len(v)
    return m, (math.sqrt(sum((x - m) ** 2 for x in v) / (len(v) - 1)) if len(v) > 1 else 0.0)


def hitung():
    seeds = muat()
    semua = [b for s in seeds for b in s["baris"]]
    jujur = [b for b in semua if b["tipe"] == "H"]
    M = {"n_seed": len(seeds), "n_jujur": len(jujur), "kembar_uji": [s["n_kembar_uji"] for s in seeds],
         "ambang": {k: sum(s["ambang"][n] for s in seeds) / len(seeds) for k, n in KODE.items() if n in seeds[0]["ambang"]}}
    M["n_cel"] = {t: [sum(1 for b in semua if b["tipe"] == t and b["level"] == lv) for lv in range(N_LEVEL)] for t in ("C1", "C2")}
    M["fpr"], M["fpr_seed"], M["det"], M["det_gab"], M["brier"] = {}, {}, {}, {}, {}
    y_semua = [b["label"] for b in semua]
    M["acuan"] = lab.brier_acuan(y_semua)
    for k, nama in KODE.items():
        n_a = sum(b["bendera"][nama] for b in jujur)
        lo, hi = lab.wilson(n_a, len(jujur))
        M["fpr"][k] = (n_a / len(jujur), lo, hi)
        per_seed = []
        for s in seeds:
            h = [b for b in s["baris"] if b["tipe"] == "H"]
            per_seed.append(sum(b["bendera"][nama] for b in h) / len(h))
        M["fpr_seed"][k] = (min(per_seed), max(per_seed))
        M["det"][k] = {}
        for t in ("C1", "C2"):
            M["det"][k][t] = []
            for lv in range(N_LEVEL):
                sub = [b for b in semua if b["tipe"] == t and b["level"] == lv]
                kk = sum(b["bendera"][nama] for b in sub)
                M["det"][k][t].append(kk / len(sub))
            sub = [b for b in semua if b["tipe"] == t]
            M["det_gab"].setdefault(k, {})[t] = sum(b["bendera"][nama] for b in sub) / len(sub)
        if k != "BU":
            M["brier"][k] = {"semua": lab.brier([b["p"][nama] for b in semua], y_semua)}
            for lv in (4, 5):
                sub = [b for b in semua if b["tipe"] == "H" or b["level"] == lv]
                M["brier"][k][lv] = lab.brier([b["p"][nama] for b in sub], [b["label"] for b in sub])
    for lv in (4, 5):
        sub = [b for b in semua if b["tipe"] == "H" or b["level"] == lv]
        M["brier"].setdefault("acuan", {})[lv] = lab.brier_acuan([b["label"] for b in sub])
    # selisih Brier B2-B4 per seed
    d = []
    for s in seeds:
        y = [b["label"] for b in s["baris"]]
        d.append(lab.brier([b["p"][KODE["B2"]] for b in s["baris"]], y) - lab.brier([b["p"][KODE["B4"]] for b in s["baris"]], y))
    M["selisih_brier_b2_b4"] = d
    # contoh nilai prediktif positif pada prevalensi rendah untuk B4
    tpr = (M["det_gab"]["B4"]["C1"] + M["det_gab"]["B4"]["C2"]) / 2
    fpr = M["fpr"]["B4"][0]
    prev = 0.01
    M["ppv"] = {"prev": prev, "tpr": tpr, "fpr": fpr, "ppv": tpr * prev / (tpr * prev + fpr * (1 - prev))}
    # sebaran antar-seed untuk TPR B4 dan B2 pada L4/L5
    M["sd_seed"] = {}
    for k in ("B2", "B4"):
        for t in ("C1", "C2"):
            for lv in (4, 5):
                v = []
                for s in seeds:
                    sub = [b for b in s["baris"] if b["tipe"] == t and b["level"] == lv]
                    v.append(sum(b["bendera"][KODE[k]] for b in sub) / len(sub))
                M["sd_seed"][(k, t, lv)] = _msd(v)
    return M


if __name__ == "__main__":
    import pprint

    pprint.pprint(hitung(), width=140)
