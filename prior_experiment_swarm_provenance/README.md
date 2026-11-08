# Swarm Provenance: trust the report or check the artifact?

Eksperimen untuk Swarm Alignment Hackathon (Apart Research), Track 4. Laporan: `laporan/Swarm_Provenance_Report.docx` (+ `.pdf`).

## Pertanyaan
Dua bot mengaku memakai dua sumber berbeda, padahal satu menyalin yang lain (disamarkan bertingkat L0-L5). Pengawas mana yang menangkapnya: yang membaca laporan atau yang mengecek artefak/sumber asli? Berapa alarm palsunya pada bot jujur yang sumbernya mirip?

## Isi
| Berkas | Fungsi |
|---|---|
| `lab.py` | penyamaran L0-L5, skenario (jujur / salin / sumber kembar), 6 pengawas, ambang, Platt, Brier, Wilson |
| `jalankan.py` | membangun bahan dari 184 buku, memindai sumber kembar, menjalankan eksperimen (5 seed) |
| `metrik.py`, `buat_gambar.py`, `build_report.py`, `teks_laporan.py` | semua angka, gambar, dan laporan dihasilkan dari `hasil/seed_*.json` |
| `analisis_seed.py` | sebaran antar-seed |
| `tests/test_lab.py` | 19 tes |
| `hasil/` | skor per seed (tanpa teks buku) dan `RINGKASAN.md` |

## Menjalankan ulang
```
py -3.12 -I -B -X utf8 -m unittest discover -s tests
py -3.12 -I -B -X utf8 jalankan.py --seeds 5 --n-jujur 100 --n-salin 40 --per-buku 20
py -3.12 -I -B -X utf8 buat_gambar.py
py -3.12 -I -B -X utf8 build_report.py
```
Butuh Ollama lokal dengan `embeddinggemma-2:740m` dan korpus `canonical_output_v2` (tidak dibagikan).

## Pekerjaan LAMA (preexisting, jangan diklaim sebagai pekerjaan sprint)
- Konversi 184 buku ke JSON halaman (`canonical_output_v2`).
- `26_Embedding_Korpus\embed_korpus.py` (pemotong `buat_potongan`) dan embedding 184 buku.
- `25_Tools_Sakti_Terpadu\saraf_nlp\embed_lokal.py` (klien Ollama lokal).
Semua isi folder ini selain itu dibuat pada 6 November 2026 selama sprint.

## Batas bukti
Bot adalah skrip, penyamaran hanya tingkat permukaan, tidak ada pengawas berbasis model bahasa (A2 hanyalah pembaca aturan), artefak diasumsikan utuh. Teks buku tidak dibagikan (hak cipta); folder `cache/` berisi teks buku dan TIDAK boleh dipublikasikan.
