# CHANGELOG (kode asli → `revised_code/`)

Kode asli disimpan utuh di `baseline_code/`. Hasil lama di `../hasil/` tidak diubah. Definisi metrik (containment, Platt, Brier, Wilson, ambang persentil-95) TIDAK diubah.

| # | Berkas | Perubahan | Alasan metodologis |
|---|---|---|---|
| 1 | `lab.py` | Tambah `hash_stabil` (SHA-256 64-bit); `cari_kembar` memakainya menggantikan `hash()` | `hash()` diacak per proses → kunci kamus tak deterministik (risiko tabrakan berbeda tiap proses) |
| 2 | `jalankan.py` | `temukan_kembar_global`: `hash()` → `lab.hash_stabil`; urutan pasangan `sorted(..., key=(-jumlah, id_x, id_y))` | Pemilihan 1/8 shingle dan pemutus seri bergantung hash acak → himpunan pasangan kembar berbeda tiap proses (F2) |
| 3 | `jalankan.py` | `VERSI_POOL = 3`; `cache/pool.json` baru di folder `revised_code/` | Pool lama (v2) tidak ditimpa; cache v2 tak akan dimuat ulang |
| 4 | `lab.py` | `skenario_jujur_kembar` (+`_bagian_kalimat`): kontrol negatif sumber kembar `HT` (kutip penuh) dan `HT2` (±60%) | F3: kelompok jujur lama membuang pasangan mirip; ujikan alarm palsu pada kemiripan sah, dilaporkan terpisah |
| 5 | `lab.py` | Setiap skenario menyimpan `meta` = {id1, id2, b1, b2} (id potongan & buku, tanpa teks) | Memungkinkan bootstrap berklaster (F6) |
| 6 | `jalankan.py` | `satu_seed`: HT/HT2 dibangkitkan SETELAH H/C1/C2 pada aliran acak yang sama; ambang & Platt tetap hanya dari H/C1 paruh kalibrasi | Tidak menggeser draw H/C1/C2; HT tidak dipakai menyetel apa pun |
| 7 | `jalankan.py` | Hasil seed menyimpan `kalib_skor_jujur`/`kalib_skor_salin` (angka saja) | Analisis sensitivitas ambang tanpa menjalankan ulang |
| 8 | `jalankan.py` | `rekap_brier` hanya H/C1/C2; ringkasan menampilkan HT/HT2 sendiri; keluaran ke `../hasil_v2` | Brier tetap sebanding dengan baseline; hasil lama tak tertimpa |
| 9 | `analisis_audit.py` (baru) | Metrik lengkap, bootstrap berklaster-buku (2.000, benih 20261107), sensitivitas ambang, per-seed, Brier seimbang, PPV, `RESULTS_COMPARISON.csv` | F5–F7 |
| 10 | `verifikasi_klaim.py`, `uji_hash.py` (baru) | Verifikasi klaim independen dari JSON; uji determinisme lintas-proses | F1, F2 |
| 11 | `tests/test_audit.py` (baru, 8 tes) | Tes hash lintas-proses, `cari_kembar` lintas-proses, properti HT/HT2, `meta` | Setiap fungsi yang diperbaiki punya tes; fixture sintetis |
| 12 | `analisis_audit.py` | Brier `BU` = NaN | Aturan OR tidak punya probabilitas; nilai 0 sebelumnya menyesatkan (ditemukan dan diperbaiki saat audit) |

Perbaikan kesalahan saat audit: fixture teks sintetis pertama satu kalimat sehingga tes `ht2` gagal; fixture diperbaiki (bukan kode).
