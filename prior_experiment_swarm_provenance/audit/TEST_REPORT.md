# TEST REPORT

## Lingkungan
- Windows 10 Home 10.0.19045; Python 3.12.10 (MSC v.1943 64 bit); semua kode hanya memakai pustaka standar Python (tidak ada pip dependency untuk eksperimen/tes).
- Embedding: Ollama 0.40.14 lokal, model `embeddinggemma-2:740m` (Q8_0, digest `f4981a15b99858ad1f2e0729416e526be7b4f428291b40082b9e4f7b27b5f62f`). Komponen lama yang diimpor: `embed_korpus.buat_potongan` (26_Embedding_Korpus), `embed_lokal` (25_Tools_Sakti_Terpadu\saraf_nlp).
- Seed eksperimen: 20261106–20261110 (sama dengan baseline). Parameter: `--seeds 5 --n-jujur 100 --n-salin 40 --per-buku 20`. Bootstrap: 2.000 resample, benih 20261107.

## Tes unit
| Perintah (di folder kode) | Hasil |
|---|---|
| `py -3.12 -I -B -X utf8 -m unittest discover -s tests` di `baseline_code/` | **19 tes OK** (0,46 dtk) — klaim "19/19" benar |
| sama di `revised_code/` | **27 tes OK** (19 lama + 8 baru, 1,65 dtk); log `hasil_v2/tes_revised.log` |

Kegagalan selama audit: 1 tes baru (`test_ht2_mengutip_sebagian`) gagal pada percobaan pertama karena fixture satu kalimat; fixture diperbaiki, kode tidak diubah.

## Tes determinisme (bukti F2)
| Uji | Hasil |
|---|---|
| Kode LAMA, 3 proses (`PYTHONHASHSEED`=1,2,3), potongan sama | 3 sidik jari berbeda; irisan pasangan 14–18 dari 150; 3 pasangan sama di ketiganya; gabungan 404 |
| Kode BARU, 3 proses (1,2,3) | sidik jari identik `2b7e204cd6`, 150 pasangan |
| Run penuh #1 vs #2 (`PYTHONHASHSEED` acak 777 pada run #2), 5 seed | 5 berkas JSON identik: 0 selisih skor, 0 bendera berbeda, `meta`/`tipe` sama |

Batas: run #2 memuat `cache/pool.json` v3 hasil run #1, jadi penemuan pasangan di dalam run penuh tidak diulang; determinismenya dibuktikan terpisah oleh uji 3-proses di atas (dengan potongan yang sama, dari `_semua_potongan` yang dikunci). Embedding Ollama menghasilkan vektor yang sama pada dua run di mesin ini; tidak dijamin lintas versi Ollama/GPU.

## Tiga tingkat verifikasi (TIDAK setara)
1. **Verifikasi hasil dari JSON** (tanpa korpus): `verifikasi_klaim.py hasil/` dan `analisis_audit.py` — dapat dijalankan siapa pun yang memiliki `seed_*.json`.
2. **Tes kode dengan fixture sintetis**: 27 tes unit — tidak butuh korpus atau Ollama.
3. **Reproduksi pipeline penuh dengan korpus 184 buku + Ollama**: dilakukan oleh pengaudit di mesin pembuat (2×); **tidak dapat dilakukan pihak lain** tanpa korpus (tidak dibagikan, hak cipta).

## Cara menjalankan (dari `revised_code/`)
```
py -3.12 -I -B -X utf8 -m unittest discover -s tests
py -3.12 -I -B -X utf8 jalankan.py --seeds 5 --n-jujur 100 --n-salin 40 --per-buku 20   # butuh korpus + Ollama
py -3.12 -I -B -X utf8 analisis_audit.py ../hasil_v2 ../hasil_v2/baseline_verifikasi.json ../hasil_v2
py -3.12 -I -B -X utf8 verifikasi_klaim.py ../../hasil          # verifikasi baseline dari JSON
```
Catatan: `jalankan.py` memuat `embed_korpus`/`embed_lokal` dari path lokal pembuat (lihat `lab.PUSTAKA_LAMA`); `cache/` berisi teks buku dan tidak boleh dipublikasikan.

## Tidak diuji
Ketahanan terhadap penyamaran semantik (parafrase/terjemahan), agen LLM nyata, pengawas LLM, model embedding lain, korpus lain, dan reproduksi lintas mesin/versi Ollama.
