"""Penjalan eksperimen. Contoh:
    py -3.12 -I -X utf8 jalankan.py --seeds 5 --n-jujur 100 --n-salin 40 --per-buku 25
Keluaran: hasil\\seed_*.json (hanya skor, TANPA teks buku) dan hasil\\RINGKASAN.md.
"""
import argparse
import json
import os
import random
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lab  # noqa: E402
import embed_korpus as ek  # noqa: E402  (PREEXISTING: pemotong halaman -> potongan)
import embed_lokal as el  # noqa: E402  (PREEXISTING: klien Ollama lokal)

SUMBER = ek.SUMBER
CACHE = os.path.join(HERE, "cache", "pool.json")
KELUAR = os.path.join(HERE, "hasil")
MODEL = "embeddinggemma-2:740m"          # PREEXISTING; hanya lokal (periksa_model menolak -cloud)
TIPE_LABEL = {"H": "jujur (kontrol negatif)", "C1": "salin, klaim sumber lain", "C2": "salin, klaim sumber kembar"}


VERSI_POOL = 2
MAKS_PASANGAN_KEMBAR = 150


def _semua_potongan():
    semua = []
    for buku in sorted(os.listdir(SUMBER)):
        berkas = os.path.join(SUMBER, buku, "01_raw_document.json")
        if not os.path.isfile(berkas):
            continue
        with open(berkas, encoding="utf-8") as fh:
            for p in ek.buat_potongan(json.load(fh)["pages"]):
                if lab.layak_jadi_bahan(p["teks"]):
                    semua.append({"id": lab.id_potongan(buku, p["halaman_fisik"], p["block_ids"]), "buku": buku,
                                  "grup": buku.split("_")[0], "hal": p["halaman_fisik"], "teks": p["teks"]})
    return semua


def temukan_kembar_global(semua, maks_pasangan=MAKS_PASANGAN_KEMBAR):
    """Pasangan potongan dari buku berbeda dengan teks benar-benar sama, dipindai di SELURUH korpus.
    Hanya 1/8 shingle 5-kata yang diindeks (cukup untuk kandidat), lalu diverifikasi penuh."""
    indeks = {}
    for i, c in enumerate(semua):
        for sh in lab.shingle(lab.token(c["teks"]), 5):
            h = hash(sh)
            if h % 8 == 0:
                indeks.setdefault(h, []).append(i)
    hitung = {}
    for ids in indeks.values():
        if 2 <= len(ids) <= 20:
            for x in ids:
                for y in ids:
                    if x < y and semua[x]["buku"] != semua[y]["buku"]:
                        hitung[(x, y)] = hitung.get((x, y), 0) + 1
    pasangan = []
    for (x, y), n in sorted(hitung.items(), key=lambda kv: -kv[1]):
        if n >= 3 and lab.containment(semua[x]["teks"], semua[y]["teks"]) >= 0.6:
            pasangan.append((x, y))
        if len(pasangan) >= maks_pasangan:
            break
    return pasangan


def muat_pool(per_buku, benih=1):
    if os.path.isfile(CACHE):
        with open(CACHE, encoding="utf-8") as fh:
            tersimpan = json.load(fh)
        if (tersimpan.get("versi"), tersimpan["per_buku"], tersimpan["benih"]) == (VERSI_POOL, per_buku, benih):
            return tersimpan["pool"]
    semua = _semua_potongan()
    pasangan = temukan_kembar_global(semua)
    rng, per_buku_indeks = random.Random(benih), {}
    for i, c in enumerate(semua):
        per_buku_indeks.setdefault(c["buku"], []).append(i)
    pilih = {i for ids in per_buku_indeks.values() for i in rng.sample(ids, min(per_buku, len(ids)))}
    pilih |= {i for pasang in pasangan for i in pasang}
    pool = [semua[i] for i in sorted(pilih)]
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    with open(CACHE, "w", encoding="utf-8") as fh:
        json.dump({"versi": VERSI_POOL, "per_buku": per_buku, "benih": benih, "pasangan_kembar_global": len(pasangan),
                   "pool": pool}, fh, ensure_ascii=False)
    return pool


def pembuat_vektor(batch=64):
    model = el.periksa_model(MODEL)
    cache = {}

    def isi(teks_list):
        baru = [t for t in dict.fromkeys(teks_list) if t not in cache]
        for i in range(0, len(baru), batch):
            bagian = baru[i:i + batch]
            for t, v in zip(bagian, el._kirim_ollama(el.URL_DEFAULT, model, bagian, 300)):
                n = sum(x * x for x in v) ** 0.5 or 1.0
                cache[t] = [x / n for x in v]
    return cache, isi


def bangun_skenario(pool, n_jujur, n_salin, rng):
    sk = lab.skenario_jujur(pool, n_jujur, rng)
    kembar = lab.cari_kembar(pool)
    for lv in range(len(lab.LEVEL_NAMA)):
        sk += lab.skenario_salin(pool, n_salin, lv, rng)
        if len(kembar) >= 5:
            sk += lab.skenario_salin(pool, n_salin, lv, rng, kembar=kembar)
    return sk, len(kembar)


def beri_skor(skenario, cache, isi):
    isi([s["bot%d" % k]["artefak"] for s in skenario for k in (1, 2)])
    for s in skenario:
        s["skor"] = {nama: f(s) for nama, f in lab.PENGAWAS_TEKS.items()}
        s["skor"]["B4 embedding artefak (artefak)"] = lab.skor_embedding(s, cache.__getitem__)
    return skenario


def satu_seed(pool, seed, a, cache, isi):
    rng = random.Random(seed)
    buku = sorted({p["buku"] for p in pool})
    rng.shuffle(buku)
    kalib_buku = set(buku[:len(buku) // 2])
    kalib = [p for p in pool if p["buku"] in kalib_buku]
    uji = [p for p in pool if p["buku"] not in kalib_buku]
    sk_kalib = lab.skenario_jujur(kalib, a.n_jujur, rng)
    for lv in range(len(lab.LEVEL_NAMA)):
        sk_kalib += lab.skenario_salin(kalib, a.n_salin, lv, rng)
    beri_skor(sk_kalib, cache, isi)
    nama_skor = list(sk_kalib[0]["skor"])
    jujur_kalib = [s for s in sk_kalib if s["label"] == 0]
    ambang = {n: lab.ambang_dari_kalibrasi([s["skor"][n] for s in jujur_kalib]) for n in nama_skor}
    platt = {n: lab.platt_fit([s["skor"][n] for s in sk_kalib], [s["label"] for s in sk_kalib]) for n in nama_skor}
    sk_uji, n_kembar = bangun_skenario(uji, a.n_jujur, a.n_salin, rng)
    beri_skor(sk_uji, cache, isi)
    baris = []
    for s in sk_uji:
        bendera = {n: s["skor"][n] > ambang[n] for n in ambang}
        bendera["B gabungan (B1|B2|B3|B4)"] = any(v for n, v in bendera.items() if n.startswith("B"))
        bendera["B tanpa cek kutipan (B2|B3|B4)"] = any(v for n, v in bendera.items() if n[:2] in ("B2", "B3", "B4"))
        prob = {n: lab.platt_prob(platt[n], s["skor"][n]) for n in nama_skor}
        baris.append({"tipe": s["tipe"], "level": s["level"], "label": s["label"], "bendera": bendera,
                      "skor": s["skor"], "p": prob})
    return {"seed": seed, "ambang": ambang, "n_kembar_uji": n_kembar, "n_buku_kalib": len(kalib_buku), "baris": baris}


def rekap(hasil_seed):
    kunci = list(hasil_seed[0]["baris"][0]["bendera"])
    grup = {}
    for h in hasil_seed:
        for b in h["baris"]:
            g = (b["tipe"], b["level"])
            grup.setdefault(g, {n: [0, 0] for n in kunci})
            for n in kunci:
                grup[g][n][0] += int(b["bendera"][n])
                grup[g][n][1] += 1
    return kunci, grup


def rekap_brier(hasil_seed):
    nama = list(hasil_seed[0]["baris"][0]["p"])
    semua = [b for h in hasil_seed for b in h["baris"]]
    himpunan = {"semua level": semua}
    for lv in range(len(lab.LEVEL_NAMA)):
        himpunan[lab.LEVEL_NAMA[lv]] = [b for b in semua if b["tipe"] == "H" or b["level"] == lv]
    hasil = {}
    for judul, sub in himpunan.items():
        y = [b["label"] for b in sub]
        hasil[judul] = ({n: lab.brier([b["p"][n] for b in sub], y) for n in nama}, lab.brier_acuan(y), len(sub))
    return nama, hasil


def tulis_brier(hasil_seed):
    nama, hasil = rekap_brier(hasil_seed)
    out = ["\n## Skor Brier (0 = sempurna, makin kecil makin baik)\n",
           "Probabilitas 'salinan' dikalibrasi logistik pada paruh buku kalibrasi, lalu dinilai pada paruh uji. "
           "'Acuan' = Brier penebak tanpa informasi yang selalu menjawab laju dasar; pengawas yang tidak mengalahkan acuan tidak berguna.\n",
           "| himpunan | n | acuan | " + " | ".join(nama) + " |", "|---|---|---|" + "---|" * len(nama)]
    for judul, (nilai, acuan, n) in hasil.items():
        out.append("| %s | %d | %.3f | %s |" % (judul, n, acuan, " | ".join("%.3f" % nilai[k] for k in nama)))
    return out


def tulis_ringkasan(hasil_seed, a):
    kunci, grup = rekap(hasil_seed)
    out = ["# Ringkasan eksperimen (%d seed, ambang dikalibrasi pada paruh buku terpisah, FPR target 5%%)\n" % len(hasil_seed),
           "Sel = persen ditandai 'bukan independen' [interval Wilson 95%%] (n). Baris jujur = alarm palsu; makin RENDAH makin baik. "
           "Baris salin = deteksi; makin TINGGI makin baik.\n"]
    for tipe in ("H", "C1", "C2"):
        baris = sorted((g for g in grup if g[0] == tipe), key=lambda g: (g[1] is None, g[1]))
        if not baris:
            continue
        out.append("\n## %s\n" % TIPE_LABEL[tipe])
        out.append("| level | " + " | ".join(kunci) + " |")
        out.append("|---|" + "---|" * len(kunci))
        for g in baris:
            sel = []
            for n in kunci:
                k, m = grup[g][n]
                lo, hi = lab.wilson(k, m)
                sel.append("%.0f%% [%.0f-%.0f] (%d)" % (100 * k / m, 100 * lo, 100 * hi, m))
            out.append("| %s | %s |" % ("-" if g[1] is None else lab.LEVEL_NAMA[g[1]], " | ".join(sel)))
    out.append("\nAmbang rata-rata: " + json.dumps(
        {n: round(sum(h["ambang"][n] for h in hasil_seed) / len(hasil_seed), 3) for n in hasil_seed[0]["ambang"]}, ensure_ascii=False))
    out.append("Sumber kembar nyata di paruh uji (per seed): " + str([h["n_kembar_uji"] for h in hasil_seed]))
    out += tulis_brier(hasil_seed)
    with open(os.path.join(KELUAR, "RINGKASAN.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(out) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--n-jujur", type=int, default=100)
    ap.add_argument("--n-salin", type=int, default=40)
    ap.add_argument("--per-buku", type=int, default=25)
    a = ap.parse_args()
    mulai = time.time()
    pool = muat_pool(a.per_buku)
    print("pool:", len(pool), "potongan dari", len({p["buku"] for p in pool}), "buku (%.0f dtk)" % (time.time() - mulai), flush=True)
    cache, isi = pembuat_vektor()
    os.makedirs(KELUAR, exist_ok=True)
    hasil = []
    for seed in range(20261106, 20261106 + a.seeds):
        h = satu_seed(pool, seed, a, cache, isi)
        hasil.append(h)
        with open(os.path.join(KELUAR, "seed_%d.json" % seed), "w", encoding="utf-8") as fh:
            json.dump(h, fh, ensure_ascii=False)
        print("seed", seed, "selesai; kembar uji:", h["n_kembar_uji"], "(%.0f dtk)" % (time.time() - mulai), flush=True)
    tulis_ringkasan(hasil, a)
    print("RINGKASAN ditulis. Total %.0f dtk" % (time.time() - mulai))


if __name__ == "__main__":
    main()
