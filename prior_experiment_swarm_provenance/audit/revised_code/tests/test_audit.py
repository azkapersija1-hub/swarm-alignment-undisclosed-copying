"""Tes tambahan hasil audit: determinisme hash, kontrol negatif sumber kembar, metrik statistik.
Semua memakai fixture SINTETIS (tidak membutuhkan korpus 184 buku)."""
import json
import os
import random
import subprocess
import sys
import unittest

AKAR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, AKAR)
import lab  # noqa: E402

KATA = ("sumber bukti agen laporan artefak penelitian pengawas data metode model hasil uji kontrol skor "
        "klaim salinan bukti independen kalimat teks paragraf analisis angka tabel gambar proses sistem").split()


def teks_acak(rng, n=60):
    kata = [rng.choice(KATA) + str(rng.randrange(1000)) for _ in range(n)]
    return " ".join(w + ("." if i % 10 == 9 else "") for i, w in enumerate(kata))   # kalimat tiap 10 kata


def buat_pool(seed=7, n=24):
    rng = random.Random(seed)
    pool = []
    for i in range(n):
        t = teks_acak(rng)
        pool.append({"id": "p%02d" % i, "buku": "B%d_x" % (i % 8), "grup": "G%d" % (i % 2), "hal": i, "teks": t})
    # dua pasangan kembar: teks sama di buku berbeda
    pool.append({"id": "k1", "buku": "B90_x", "grup": "G0", "hal": 1, "teks": pool[0]["teks"]})
    pool.append({"id": "k2", "buku": "B91_x", "grup": "G1", "hal": 2, "teks": pool[3]["teks"]})
    return pool


class TesHashDeterministik(unittest.TestCase):
    def test_hash_stabil_sama_di_proses_lain(self):
        kode = "import sys;sys.path.insert(0,r'%s');import lab;print(lab.hash_stabil(('a','b','c')))" % AKAR
        hasil = set()
        for seed in ("1", "2", "99"):
            env = dict(os.environ, PYTHONHASHSEED=seed)
            hasil.add(subprocess.check_output([sys.executable, "-c", kode], env=env, text=True).strip())
        self.assertEqual(len(hasil), 1)

    def test_hash_bawaan_python_memang_berubah(self):
        # bukti latar belakang temuan audit: hash() bawaan berbeda antar proses
        hasil = set()
        for seed in ("1", "2", "99"):
            env = dict(os.environ, PYTHONHASHSEED=seed)
            hasil.add(subprocess.check_output([sys.executable, "-c", "print(hash(('a','b','c')))"], env=env, text=True).strip())
        self.assertGreater(len(hasil), 1)

    def test_cari_kembar_sama_di_proses_lain(self):
        pool_json = json.dumps(buat_pool())
        kode = ("import sys,json;sys.path.insert(0,r'%s');import lab;pool=json.loads(sys.stdin.read());"
                "k=lab.cari_kembar(pool);print(json.dumps(sorted((a,b['id']) for a,b in k.items())))" % AKAR)
        keluar = set()
        for seed in ("1", "5"):
            env = dict(os.environ, PYTHONHASHSEED=seed)
            keluar.add(subprocess.run([sys.executable, "-c", kode], input=pool_json, env=env, text=True,
                                      capture_output=True, check=True).stdout.strip())
        self.assertEqual(len(keluar), 1)
        pasang = json.loads(keluar.pop())
        self.assertGreaterEqual(len(pasang), 2)


class TesKontrolNegatifKembar(unittest.TestCase):
    def setUp(self):
        self.pool = buat_pool()
        self.kembar = lab.cari_kembar(self.pool)

    def test_kembar_ditemukan(self):
        self.assertTrue(self.kembar)
        for a, c in self.kembar.items():
            sumber = next(p for p in self.pool if p["id"] == a)
            self.assertNotEqual(sumber["buku"], c["buku"])
            self.assertGreaterEqual(lab.containment(sumber["teks"], c["teks"]), 0.6)

    def test_ht_label_nol_dan_tipe(self):
        sk = lab.skenario_jujur_kembar(self.pool, 30, random.Random(3), self.kembar)
        self.assertEqual(len(sk), 30)
        for s in sk:
            self.assertEqual((s["tipe"], s["label"], s["level"]), ("HT", 0, None))
            self.assertGreaterEqual(lab.containment(s["src1"], s["src2"]), 0.6)   # sumber memang kembar
            self.assertNotEqual(s["meta"]["b1"], s["meta"]["b2"])

    def test_ht_bot_menulis_dari_sumber_sendiri_bukan_menyalin_bot_lain(self):
        # Tiap artefak berasal dari sumbernya sendiri: tingkat 'kutip dari sumber sendiri' tinggi.
        for s in lab.skenario_jujur_kembar(self.pool, 20, random.Random(4), self.kembar):
            self.assertGreaterEqual(lab.containment(s["bot1"]["artefak"], s["src1"]), 0.5)
            self.assertGreaterEqual(lab.containment(s["bot2"]["artefak"], s["src2"]), 0.5)

    def test_ht2_mengutip_sebagian(self):
        sk = lab.skenario_jujur_kembar(self.pool, 20, random.Random(5), self.kembar, sebagian=True)
        self.assertTrue(all(s["tipe"] == "HT2" and s["label"] == 0 for s in sk))
        panjang = [len(s["bot1"]["artefak"]) / len(s["src1"]) for s in sk]
        self.assertLess(sum(panjang) / len(panjang), 1.0)

    def test_skenario_menyimpan_meta_tanpa_teks(self):
        sk = lab.skenario_jujur(self.pool, 5, random.Random(1)) + lab.skenario_salin(self.pool, 5, 3, random.Random(1))
        for s in sk:
            self.assertEqual(set(s["meta"]), {"id1", "id2", "b1", "b2"})


if __name__ == "__main__":
    unittest.main()
