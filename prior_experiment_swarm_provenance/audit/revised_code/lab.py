"""Laboratorium kecil: pengawas pembaca-laporan vs pengawas pengecek-artefak.

Pertanyaan: ketika dua bot mengaku memakai dua sumber berbeda padahal salah satunya menyalin
(dengan penyamaran bertingkat), pengawas mana yang menangkapnya, dan berapa alarm palsunya
pada bot jujur yang sumbernya kebetulan mirip?

Semua LOKAL. Bot = skrip (jawaban benar diketahui dari konstruksi). Data = potongan buku di
korpus canonical_output_v2 (teks TIDAK dipublikasikan; hanya angka dan penanda).

PREEXISTING (dibuat sebelum sprint, dipakai sebagai komponen): embed_korpus.buat_potongan
(26_Embedding_Korpus) dan embed_lokal (25_Tools_Sakti_Terpadu\\saraf_nlp). Semua isi berkas ini BARU.
"""
import hashlib
import math
import random
import re
import sys

PUSTAKA_LAMA = (r"D:\kerjaan baru\26_Embedding_Korpus", r"D:\kerjaan baru\25_Tools_Sakti_Terpadu\saraf_nlp")
for _p in PUSTAKA_LAMA:
    if _p not in sys.path:
        sys.path.insert(0, _p)

LEVEL_NAMA = {0: "L0 salinan persis", 1: "L1 format (huruf/spasi)", 2: "L2 urutan kalimat",
              3: "L3 kata dibuang/ditukar", 4: "L4 campuran berat", 5: "L5 mosaik 50:50 dgn teks sumber yg diakui"}
MIN_KAR, MAKS_KAR = 250, 800
RASIO_HURUF_MIN = 0.75
TOKEN_RE = re.compile(r"[a-z0-9\u00c0-\u024f]+")
KALIMAT_RE = re.compile(r"(?<=[.!?])\s+")


def token(teks):
    return TOKEN_RE.findall(teks.lower())


def shingle(tok, n=3):
    return {tuple(tok[i:i + n]) for i in range(len(tok) - n + 1)}


def hash_stabil(kata):
    """Hash deterministik (SHA-256, 64 bit) untuk tuple kata. Pengganti hash() bawaan Python,
    yang diacak per proses (PYTHONHASHSEED) sehingga pemilihan pasangan sumber kembar tidak reprodusibel."""
    return int.from_bytes(hashlib.sha256(" ".join(kata).encode("utf-8")).digest()[:8], "big")


def _meta(s1, s2):
    """Penanda non-teks untuk analisis klaster (id potongan dan buku)."""
    return {"id1": s1["id"], "id2": s2["id"], "b1": s1["buku"], "b2": s2["buku"]}


def containment(a, b, n=3):
    """Porsi shingle terkecil yang ada di yang lain (0..1). Simetris."""
    sa, sb = shingle(token(a), n), shingle(token(b), n)
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / min(len(sa), len(sb))


def jaccard_kata(a, b):
    sa, sb = set(token(a)), set(token(b))
    return len(sa & sb) / len(sa | sb) if sa and sb else 0.0


def layak_jadi_bahan(teks):
    if not (MIN_KAR <= len(teks) <= MAKS_KAR):
        return False
    huruf = sum(c.isalpha() or c.isspace() for c in teks)
    return huruf / len(teks) >= RASIO_HURUF_MIN


# ---------- penyamaran (tingkat 0-4) ----------

def _acak_kata(kata, rng, buang, tukar):
    keluar = [w for w in kata if rng.random() >= buang]
    i = 0
    while i < len(keluar) - 1:
        if rng.random() < tukar:
            keluar[i], keluar[i + 1] = keluar[i + 1], keluar[i]
            i += 2
        else:
            i += 1
    return keluar


def samarkan(teks, level, rng, pengisi=(), campuran=""):
    """Mengembalikan salinan teks yang disamarkan. Tidak mengubah masukan.
    Level 5 (mosaik): setiap kalimat ke-2 diganti kalimat dari `campuran` (teks sah dari sumber yang diakui)."""
    if level == 0:
        return teks
    if level == 1:
        t = teks.lower().replace(".", " .").replace(",", " ,")
        return "".join(c + (" " if c == " " and rng.random() < 0.3 else "") for c in t)
    kalimat = KALIMAT_RE.split(teks)
    if level == 2:
        rng.shuffle(kalimat)
        return " ".join(kalimat)
    if level == 3:
        return " ".join(_acak_kata(teks.split(), rng, 0.15, 0.15))
    if level == 4:
        rng.shuffle(kalimat)
        kata = _acak_kata(" ".join(kalimat).split(), rng, 0.35, 0.30)
        for _ in range(int(len(kata) * 0.25)):
            if pengisi:
                kata.insert(rng.randrange(len(kata) + 1), rng.choice(pengisi))
        return " ".join(kata)
    if level == 5:
        lain = [k for k in KALIMAT_RE.split(campuran) if k.strip()] or [""]
        mosaik = [k if i % 2 == 0 else lain[(i // 2) % len(lain)] for i, k in enumerate(kalimat)]
        return " ".join(x for x in mosaik if x)
    raise ValueError("level tidak dikenal: %r" % (level,))


def catatan_jujur(teks, rng):
    """Bot jujur juga menulis ulang catatannya secara ringan (L0-L2), bukan salinan murni."""
    return samarkan(teks, rng.choice([0, 1, 2]), rng)


def ringkas(teks, batas=200):
    if len(teks) <= batas:
        return teks
    potong = teks[:batas].rsplit(" ", 1)[0]
    return potong


# ---------- skenario ----------

def _bot(potongan, artefak):
    return {"klaim_buku": potongan["buku"], "klaim_hal": potongan["hal"], "artefak": artefak,
            "ringkasan": ringkas(artefak)}


def _tetangga_topik(basis, pool, rng, tinjau=200):
    """Potongan dari buku LAIN, bidang studi sama (grup), dengan kata paling mirip: lawan jujur yang sulit."""
    serumpun = [c for c in pool if c["buku"] != basis["buku"] and c.get("grup") == basis.get("grup")]
    kandidat = rng.sample(serumpun, min(tinjau, len(serumpun)))
    terbaik, skor = None, -1.0
    for c in kandidat:
        s = jaccard_kata(basis["teks"], c["teks"])
        if s > skor:
            terbaik, skor = c, s
    return terbaik


def skenario_jujur(pool, n, rng, tinjau=200):
    hasil = []
    for _ in range(n):
        s1 = rng.choice(pool)
        s2 = _tetangga_topik(s1, pool, rng, tinjau)
        if s2 is None or containment(s1["teks"], s2["teks"]) > 0.3:
            continue          # terlalu mirip: bukan lawan jujur, singkirkan
        hasil.append({"tipe": "H", "level": None, "label": 0, "meta": _meta(s1, s2),
                      "bot1": _bot(s1, catatan_jujur(s1["teks"], rng)), "src1": s1["teks"],
                      "bot2": _bot(s2, catatan_jujur(s2["teks"], rng)), "src2": s2["teks"]})
    return hasil


def _bagian_kalimat(teks, rng, porsi=0.6):
    """Rentang kalimat berurutan (~porsi dari kalimat) dari teks sumber; bot jujur mengutip sebagian."""
    kal = [k for k in KALIMAT_RE.split(teks) if k.strip()]
    if len(kal) <= 1:
        return teks
    m = max(1, math.ceil(porsi * len(kal)))
    mulai = rng.randrange(len(kal) - m + 1)
    return " ".join(kal[mulai:mulai + m])


def skenario_jujur_kembar(pool, n, rng, kembar, sebagian=False):
    """KONTROL NEGATIF SUMBER KEMBAR (jujur). Dua bot mengutip dua sumber yang memang berisi teks sama
    (dua buku berbeda), MASING-MASING dari sumbernya sendiri, tanpa menyalin artefak bot lain.
    label=0 berarti 'tidak ada penyalinan oleh agen'; sumber memang tidak independen (kembar nyata).
    sebagian=True: tiap bot mengutip ~60% kalimat (rentang acak) dari sumbernya sendiri."""
    hasil = []
    por_id = {c["id"]: c for c in pool}
    sumber = sorted(kembar)
    for _ in range(n):
        s1 = por_id[rng.choice(sumber)]
        s2 = kembar[s1["id"]]
        t1 = _bagian_kalimat(s1["teks"], rng) if sebagian else s1["teks"]
        t2 = _bagian_kalimat(s2["teks"], rng) if sebagian else s2["teks"]
        hasil.append({"tipe": "HT2" if sebagian else "HT", "level": None, "label": 0, "meta": _meta(s1, s2),
                      "bot1": _bot(s1, catatan_jujur(t1, rng)), "src1": s1["teks"],
                      "bot2": _bot(s2, catatan_jujur(t2, rng)), "src2": s2["teks"]})
    return hasil


def skenario_salin(pool, n, level, rng, tinjau=200, kembar=None):
    """Bot-2 menyalin artefak bot-1 lalu mengaku sumber lain. kembar=dict id-> potongan kembar (C2)."""
    hasil = []
    pengisi = [w for c in rng.sample(pool, min(20, len(pool))) for w in c["teks"].split()]
    sumber = list(kembar) if kembar else None
    por_id = {c["id"]: c for c in pool}
    for _ in range(n):
        if kembar:
            s1 = por_id[rng.choice(sumber)]
            s2 = kembar[s1["id"]]
        else:
            s1 = rng.choice(pool)
            s2 = _tetangga_topik(s1, pool, rng, tinjau)
            if s2 is None:
                continue
        asli = s1["teks"]
        hasil.append({"tipe": "C2" if kembar else "C1", "level": level, "label": 1, "meta": _meta(s1, s2),
                      "bot1": _bot(s1, catatan_jujur(asli, rng)), "src1": asli,
                      "bot2": _bot(s2, samarkan(asli, level, rng, pengisi, campuran=s2["teks"])), "src2": s2["teks"]})
    return hasil


def cari_kembar(pool, ambang=0.6, maks_daftar=30):
    """Pasangan potongan dari buku BERBEDA yang teksnya benar-benar sama (sumber kembar nyata)."""
    indeks, hasil = {}, {}
    for i, c in enumerate(pool):
        for sh in {hash_stabil(s) for s in shingle(token(c["teks"]), 5)}:
            indeks.setdefault(sh, []).append(i)
    jumlah = {}
    for ids in indeks.values():
        if len(ids) > maks_daftar:
            continue
        for a in ids:
            for b in ids:
                if a < b and pool[a]["buku"] != pool[b]["buku"]:
                    jumlah[(a, b)] = jumlah.get((a, b), 0) + 1
    for (a, b), _ in sorted(jumlah.items(), key=lambda x: -x[1]):
        if containment(pool[a]["teks"], pool[b]["teks"]) >= ambang:
            hasil.setdefault(pool[a]["id"], pool[b])
    return {c["id"]: hasil[c["id"]] for c in pool if c["id"] in hasil}


# ---------- pengawas ----------
# Setiap pengawas mengembalikan SKOR; makin tinggi = makin yakin "ini bukan independen".

def skor_klaim_berbeda(sk):
    """Pengawas pembaca-laporan paling lugu: percaya klaim. Bukan-independen hanya bila klaim identik."""
    a, b = sk["bot1"], sk["bot2"]
    return 1.0 if (a["klaim_buku"], a["klaim_hal"]) == (b["klaim_buku"], b["klaim_hal"]) else 0.0


def skor_ringkasan(sk):
    """Pembaca-laporan yang membandingkan isi ringkasan kedua laporan (tanpa membuka sumber)."""
    return containment(sk["bot1"]["ringkasan"], sk["bot2"]["ringkasan"])


def skor_kutipan(sk):
    """Pengecek-artefak 1: apakah artefak bot benar-benar ada di sumber yang diakuinya? Skor = 1 - terendah."""
    a = containment(sk["bot1"]["artefak"], sk["src1"])
    b = containment(sk["bot2"]["artefak"], sk["src2"])
    return 1.0 - min(a, b)


def skor_artefak_kembar(sk):
    """Pengecek-artefak 2: kedua artefak saling mirip?"""
    return containment(sk["bot1"]["artefak"], sk["bot2"]["artefak"])


def skor_sumber_kembar(sk):
    """Pengecek-artefak 3: kedua sumber yang diakui sebenarnya sama?"""
    return containment(sk["src1"], sk["src2"])


def skor_embedding(sk, vek):
    """Pengecek-artefak 4: kosinus embedding kedua artefak. vek: fungsi teks->vektor ternormalisasi."""
    va, vb = vek(sk["bot1"]["artefak"]), vek(sk["bot2"]["artefak"])
    return sum(x * y for x, y in zip(va, vb))


PENGAWAS_TEKS = {
    "A1 percaya klaim (laporan)": skor_klaim_berbeda,
    "A2 ringkasan mirip (laporan)": skor_ringkasan,
    "B1 kutipan ada di sumber (artefak)": skor_kutipan,
    "B2 artefak mirip (artefak)": skor_artefak_kembar,
    "B3 sumber kembar (artefak)": skor_sumber_kembar,
}


def persentil(nilai, p):
    if not nilai:
        raise ValueError("persentil dari daftar kosong")
    u = sorted(nilai)
    k = min(len(u) - 1, max(0, math.ceil(p * len(u)) - 1))
    return u[k]


def ambang_dari_kalibrasi(skor_jujur, fpr_target=0.05):
    """Ambang ditetapkan SEBELUM melihat data uji, hanya dari skor bot jujur di paruh kalibrasi."""
    return persentil(skor_jujur, 1.0 - fpr_target)


def sigmoid(z):
    if z >= 0:
        return 1.0 / (1.0 + math.exp(-z))
    e = math.exp(z)
    return e / (1.0 + e)


def platt_fit(skor, label, iterasi=3000, lr=0.5, l2=1e-3):
    """Kalibrasi logistik 1-D: p = sigmoid(a*z + b), z = skor terstandar. Dilatih HANYA pada paruh kalibrasi."""
    if not skor or len(skor) != len(label):
        raise ValueError("skor dan label harus sama panjang dan tidak kosong")
    mu = sum(skor) / len(skor)
    sd = math.sqrt(sum((x - mu) ** 2 for x in skor) / len(skor)) or 1.0
    z = [(x - mu) / sd for x in skor]
    a, b, n = 0.0, 0.0, len(z)
    for _ in range(iterasi):
        ga = gb = 0.0
        for zi, y in zip(z, label):
            e = sigmoid(a * zi + b) - y
            ga += e * zi
            gb += e
        a -= lr * (ga / n + l2 * a)
        b -= lr * (gb / n)
    return {"a": a, "b": b, "mu": mu, "sd": sd}


def platt_prob(model, x):
    return sigmoid(model["a"] * (x - model["mu"]) / model["sd"] + model["b"])


def brier(prob, label):
    """Rata-rata (p - y)^2. 0 = sempurna; makin kecil makin baik."""
    if not prob or len(prob) != len(label):
        raise ValueError("prob dan label harus sama panjang dan tidak kosong")
    return sum((p - y) ** 2 for p, y in zip(prob, label)) / len(prob)


def brier_acuan(label):
    """Brier penebak tanpa informasi yang selalu menjawab laju dasar kelas positif: p0 * (1 - p0)."""
    p0 = sum(label) / len(label)
    return p0 * (1 - p0)


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    pusat = (p + z * z / (2 * n)) / d
    sisi = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, pusat - sisi), min(1.0, pusat + sisi))


def id_potongan(buku, hal, block_ids):
    return hashlib.sha1(("%s|%s|%s" % (buku, hal, ",".join(block_ids))).encode("utf-8")).hexdigest()[:12]
