import os
import random
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import lab  # noqa: E402

KATA = ("atom unsur reaksi energi massa gaya medan listrik larutan asam basa molekul ikatan "
        "kimia fisika proses sel enzim jaringan organ sistem hukum teori rumus hasil data").split()


def teks_acak(rng, n=90):
    kal = []
    for _ in range(n // 10):
        kal.append(" ".join(rng.choice(KATA) + str(rng.randrange(50)) for _ in range(10)) + ".")
    return " ".join(kal)


def potongan(rng, buku, hal):
    return {"id": "%s-%d" % (buku, hal), "buku": buku, "hal": hal, "teks": teks_acak(rng)}


class TestDasar(unittest.TestCase):
    def test_containment_identik_dan_terpisah(self):
        rng = random.Random(1)
        a, b = teks_acak(rng), teks_acak(rng)
        self.assertAlmostEqual(lab.containment(a, a), 1.0)
        self.assertLess(lab.containment(a, b), 0.05)
        self.assertEqual(lab.containment("a b", "a b"), 0.0)       # terlalu pendek untuk shingle

    def test_samarkan_tidak_mengubah_masukan_dan_level_menurunkan_kemiripan(self):
        rng = random.Random(2)
        asli = teks_acak(rng, 120)
        salinan = str(asli)
        pengisi = ["xx", "yy", "zz"]
        skor = [lab.containment(asli, lab.samarkan(asli, lv, random.Random(3), pengisi)) for lv in range(5)]
        self.assertEqual(asli, salinan)
        self.assertEqual(skor[0], 1.0)
        self.assertGreater(skor[1], 0.99)                         # L1 hanya format
        self.assertGreater(skor[2], 0.7)                          # L2 acak kalimat: shingle di dalam kalimat tetap
        self.assertLess(skor[4], skor[3])                         # L4 lebih berat dari L3
        self.assertLess(skor[4], 0.3)

    def test_mosaik_separuh_dari_sumber_diakui(self):
        rng = random.Random(4)
        asli, lain = teks_acak(rng, 120), teks_acak(random.Random(99), 120)
        m = lab.samarkan(asli, 5, random.Random(5), campuran=lain)
        self.assertGreater(lab.containment(m, asli), 0.35)
        self.assertLess(lab.containment(m, asli), 0.75)
        self.assertGreater(lab.containment(m, lain), 0.2)

    def test_level_tak_dikenal_ditolak(self):
        with self.assertRaises(ValueError):
            lab.samarkan("abc", 99, random.Random(0))


class TestSkenario(unittest.TestCase):
    def setUp(self):
        rng = random.Random(5)
        self.pool = [potongan(rng, "B%d" % (i % 6), i) for i in range(60)]

    def test_jujur_tak_mirip_dan_berlabel_nol(self):
        sk = lab.skenario_jujur(self.pool, 15, random.Random(7))
        self.assertGreater(len(sk), 5)
        for s in sk:
            self.assertEqual(s["label"], 0)
            self.assertNotEqual(s["bot1"]["klaim_buku"], s["bot2"]["klaim_buku"])
            self.assertLess(lab.containment(s["src1"], s["src2"]), 0.31)

    def test_salin_label_satu_klaim_beda_tapi_artefak_turunan_sumber_pertama(self):
        sk = lab.skenario_salin(self.pool, 10, 0, random.Random(8))
        for s in sk:
            self.assertEqual(s["label"], 1)
            self.assertNotEqual((s["bot1"]["klaim_buku"], s["bot1"]["klaim_hal"]), (s["bot2"]["klaim_buku"], s["bot2"]["klaim_hal"]))
            self.assertEqual(s["bot2"]["artefak"], s["src1"])     # L0: salinan persis sumber bot-1

    def test_cari_kembar_menemukan_teks_sama_beda_buku(self):
        rng = random.Random(9)
        pool = [potongan(rng, "B%d" % (i % 4), i) for i in range(20)]
        pool.append({"id": "kembar", "buku": "ZZ", "hal": 1, "teks": pool[3]["teks"]})
        kembar = lab.cari_kembar(pool)
        self.assertIn(pool[3]["id"], kembar)
        self.assertEqual(kembar[pool[3]["id"]]["buku"], "ZZ")


class TestPengawas(unittest.TestCase):
    def setUp(self):
        rng = random.Random(11)
        self.pool = [potongan(rng, "B%d" % (i % 6), i) for i in range(60)]

    def test_pengawas_laporan_lugu_buta_terhadap_salinan_klaim_beda(self):
        for s in lab.skenario_salin(self.pool, 10, 0, random.Random(12)):
            self.assertEqual(lab.skor_klaim_berbeda(s), 0.0)      # tertipu penuh

    def test_pengecek_kutipan_menangkap_klaim_palsu_pada_semua_level(self):
        for lv in range(5):                                       # L5 sengaja dikecualikan: setengah teksnya sah
            for s in lab.skenario_salin(self.pool, 5, lv, random.Random(13 + lv)):
                self.assertGreater(lab.skor_kutipan(s), 0.8)

    def test_pengecek_artefak_menurun_pada_penyamaran_berat(self):
        s0 = lab.skenario_salin(self.pool, 8, 0, random.Random(20))
        s4 = lab.skenario_salin(self.pool, 8, 4, random.Random(20))
        rata = lambda xs: sum(xs) / len(xs)
        self.assertGreater(rata([lab.skor_artefak_kembar(s) for s in s0]), rata([lab.skor_artefak_kembar(s) for s in s4]))

    def test_jujur_skor_artefak_rendah(self):
        for s in lab.skenario_jujur(self.pool, 10, random.Random(21)):
            self.assertLess(lab.skor_artefak_kembar(s), 0.3)


class TestBrier(unittest.TestCase):
    def test_brier_sempurna_dan_terburuk(self):
        self.assertEqual(lab.brier([1.0, 0.0], [1, 0]), 0.0)
        self.assertEqual(lab.brier([0.0, 1.0], [1, 0]), 1.0)

    def test_acuan_laju_dasar(self):
        self.assertAlmostEqual(lab.brier_acuan([1, 0, 0, 0]), 0.1875)
        self.assertEqual(lab.brier_acuan([1, 1]), 0.0)

    def test_platt_memisahkan_dan_mengalahkan_acuan(self):
        skor = [0.1, 0.2, 0.15, 0.9, 0.8, 0.95]
        y = [0, 0, 0, 1, 1, 1]
        m = lab.platt_fit(skor, y)
        p = [lab.platt_prob(m, x) for x in skor]
        self.assertLess(lab.brier(p, y), lab.brier_acuan(y))
        self.assertGreater(p[4], p[1])

    def test_platt_skor_konstan_jatuh_ke_laju_dasar(self):
        m = lab.platt_fit([0.0] * 8, [1, 0, 0, 0, 1, 0, 0, 0])
        self.assertAlmostEqual(lab.platt_prob(m, 0.0), 0.25, places=2)

    def test_masukan_tak_valid_ditolak(self):
        with self.assertRaises(ValueError):
            lab.brier([], [])
        with self.assertRaises(ValueError):
            lab.platt_fit([0.1], [0, 1])


class TestAmbangDanStatistik(unittest.TestCase):
    def test_ambang_menjaga_fpr(self):
        jujur = [i / 100 for i in range(100)]
        t = lab.ambang_dari_kalibrasi(jujur, 0.05)
        self.assertLessEqual(sum(x > t for x in jujur) / 100, 0.05)

    def test_persentil_kosong_ditolak(self):
        with self.assertRaises(ValueError):
            lab.persentil([], 0.5)

    def test_wilson_batas_wajar(self):
        lo, hi = lab.wilson(0, 10)
        self.assertEqual(lo, 0.0)
        self.assertGreater(hi, 0.0)
        self.assertEqual(lab.wilson(0, 0), (0.0, 0.0))


if __name__ == "__main__":
    unittest.main()
