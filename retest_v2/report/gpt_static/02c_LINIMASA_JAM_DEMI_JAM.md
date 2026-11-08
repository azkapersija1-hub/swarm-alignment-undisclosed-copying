# Linimasa jam demi jam (6 sampai 8 November 2026, WIB = UTC+7)

**Sumber waktu:** cap waktu berkas asli di disk (waktu pembuatan dan waktu terakhir ditulis) dan catatan log; kolom "dasar" menyebut sumbernya. Berkas run dan skor ditulis sekali, saat satu replikasi selesai, sehingga waktu pembuatan sama dengan waktu selesai. **Waktu mulai yang bertanda "perkiraan" dihitung mundur dari durasi di log atau durasi replikasi pertama; itu bukan cap waktu langsung.** Waktu di berkas kunci pra-registrasi tersimpan dalam UTC; di bawah ini sudah dikonversi ke WIB. Tidak ada waktu yang diisi dari ingatan.

Ringkas untuk uji 3: kunci pra-registrasi tahap 1 pada **Minggu 8 November 00:51:43**; hasil konfirmatori pertama muncul **12:09:37 (metrik utama D1) dan 12:11:29 (perbandingan utama dan falsifier D1)**; hasil lengkap lima arm termasuk transfer dan diagnostik tersedia pada **12:53:27**. Rentang jam dinding **12 jam 1 menit 44 detik**, dengan jeda tidak aktif sekitar 02:05 sampai 10:00 (sesi sebelumnya berakhir).

## 1. Uji 1: Swarm Provenance (pilot, bot berskrip), Jumat 6 November
| waktu | kejadian | dasar |
|---|---|---|
| 18:23:06 | seed 20261106 selesai | mtime `hasil/seed_20261106.json` |
| 18:24:45 | seed 20261107 selesai | mtime |
| 18:26:18 | seed 20261108 selesai | mtime |
| 18:27:51 | seed 20261109 selesai | mtime |
| 18:29:21 | seed 20261110 selesai (lima seed selesai; sekitar 1,5 menit per seed) | mtime |
| 18:41:03 | laporan pilot (docx) selesai | mtime `laporan/Swarm_Provenance_Report.docx` |
| 23:01:13 sampai 23:02:15 | audit: `AUDIT_REPORT`, `CHANGELOG`, `TEST_REPORT`, `MANUSCRIPT_REVISION_NOTES`, `FINAL_DECISION` ditulis (ketidakdeterministikan `hash()` ditemukan dan diperbaiki; kontrol kembar jujur ditambahkan) | mtime folder `audit/` |

## 2. Uji 2: studi 820 skenario dengan agen Gemma (D0), Sabtu 7 November
| waktu | kejadian | dasar |
|---|---|---|
| sekitar 15:00 (perkiraan) | pembuatan skenario replikasi 0 dimulai (durasi per replikasi sekitar 3,5 sampai 4 menit) | dihitung mundur dari replikasi 0 selesai |
| 15:04:01 | replikasi 0 (164 skenario) selesai | mtime `llm_runs_tls/rep0_gemma4_31b-cloud.jsonl` |
| 15:07:53 | replikasi 1 selesai | mtime |
| 15:12:03 | replikasi 2 selesai | mtime |
| 15:15:48 | replikasi 3 selesai | mtime |
| 15:19:07 | replikasi 4 selesai (total 820 skenario) | mtime |
| 16:03:16 | Track 1: uji sandbox | mtime `t1_sandbox.json` |
| 16:07:10 | Track 1: reproduksibilitas | mtime |
| 16:08:56 sampai 16:08:59 | Track 1: sumber daya; Track 3: identitas, duplikat, atribusi rantai, perusakan | mtime |
| 16:11:07 | tabel hasil resmi uji 2 (`TABLES.md`) selesai | mtime |
| 16:15:31 | Track 2: jaringan | mtime `t2_summary.json` |
| 16:18:36 | laporan resmi (docx) selesai | mtime |
| 16:59:18 dan 16:59:25 | PDF resmi dan ZIP paket pertama selesai | mtime |
| 23:29:50 | status akhir semua rujukan halaman Resources Apart ditulis | mtime `ALL_APART_REFERENCES_STATUS.md` |

## 3. Persiapan uji 3, Minggu 8 November (tengah malam)
| waktu | kejadian | dasar |
|---|---|---|
| 00:07:45 | paket bahan untuk analisis celah berbantuan AI selesai (ZIP) | mtime `ARGON_PACKAGE_SWARM.zip` |
| 00:37:18 sampai 00:38:00 | keluaran analisis celah berbantuan AI tersimpan: `argon_gap_analysis`, `candidate_formulas.py`, `preregistered_test_plan`, `review_of_lenses`, `interdisciplinary_map`, `HYPOTHESES.json` | mtime berkas |
| 00:46:15 sampai 00:46:16 | berkas itu disalin ke folder `prereg/` uji 3 | ctime berkas di `prereg/` |
| 00:48:30 | deklarasi tahap 1 (`RETEST_DECLARATIONS.md`) selesai | mtime |
| 00:49:22 | tes pertama (`test_controller_v2.py`) dibuat | ctime |
| 00:49:40 dan 00:49:58 | `controller_v2.py` dan `gen_v2.py` dibuat | ctime |
| 00:51:43 | **kunci pra-registrasi tahap 1** (11 berkas, hash SHA-256): rumus, hipotesis, deklarasi, controller, generator | `locked_at_utc 2026-11-07T17:51:43` |

## 4. Uji 3: pembuatan data (generasi agen), 8 November
Tiap berkas ditulis saat replikasi selesai. Awal pembuatan sekitar 00:52 (perkiraan: selesai replikasi pertama DeepSeek 00:55:48 dikurangi sekitar 3,8 menit).
| arm | replikasi selesai (waktu, selang antar replikasi) |
|---|---|
| D2 DeepSeek | rep0 00:55:48; rep1 00:59:34 (3,8 menit); rep2 01:03:26 (3,9 menit) |
| D2 Qwen | rep0 00:56:30; rep1 01:01:11 (4,7 menit); rep2 01:05:58 (4,8 menit) |
| D1 Gemma (utama) | rep0 00:58:48; rep1 01:05:53 (7,1 menit); rep2 01:14:22 (8,5 menit); rep3 01:21:45 (7,4 menit); rep4 01:29:32 (7,8 menit) |
| D3 Gemma>DeepSeek | rep0 01:13:07; rep1 01:18:20 (5,2 menit) |
| D3 Gemma>Qwen | rep0 01:13:58; rep1 01:19:56 (6,0 menit) |
Seluruh pembuatan data selesai **01:29:32** (sekitar 37 menit dinding; keempat jalur berjalan paralel).

Pengembangan kode dan tes berlangsung bersamaan (waktu pembuatan berkas): `test_features_v2.py` 00:54:18; `test_stats_v2.py` 00:59:17; `agent_common.py` 01:02:52; `track1_v2.py` 01:03:42; `track3_v2.py` 01:05:14; `diagnostics_v2.py` 01:11:55; `stats_v2.py` 01:14:59; `evaluate_v2.py` 01:16:37; `features_v2.py` 01:16:38; `track2_v2.py` 01:17:05; `lock.py` 01:17:26; `test_review_fixes.py` 01:17:47; `DEVIATIONS.md` 01:17:27; `RETEST_DECLARATIONS_STAGE2.md` 01:08:00 (deklarasi tahap 2); **kunci tahap 2 pertama kali dibuat 01:18:09** (16 berkas); `score_v2.py` 01:29:00.

## 5. Uji 3: penilaian (monitor, fitur, embedding)
**Putaran pertama (dini hari):** penilaian dimulai sekitar 01:29:50 (perkiraan dari durasi 938 detik pada log). Selesai: DeepSeek rep0 01:41:05; Qwen rep0 01:41:14; Gemma rep0 01:45:28. Setelah itu **tidak ada berkas skor baru antara 01:45 dan 11:03**: proses penilaian terhenti saat sesi sebelumnya berakhir (tercatat "stopped" oleh sistem) dan proses Gemma keluar dengan kode 4; penyebab persisnya tidak dapat dipastikan dari berkas.

**Uji tambahan dini hari (tidak memakai hasil monitor konfirmatori):**
| waktu | kejadian | dasar |
|---|---|---|
| 01:39:04 | Track 3 pada ledger D1 (perusakan log) | mtime `track3.json` |
| 01:41:17 dan 01:41:45 | Track 1: red-team agen dan papan bersama (Qwen dan DeepSeek) | mtime |
| 01:49:34 | Track 2 (klaim tak relevan) | mtime |
| 01:49:58 sampai 01:51:41 | **analisis ulang D0 (eksploratori, terkontaminasi)** di pipeline uji 3; hasil utama 01:49:58, perbandingan utama dan falsifier 01:51:40 sampai 01:51:41 | mtime `results/D0_...` |
| 01:50:59 dan 02:03:29 | Track 2 v3 (eksploratori): kode dibuat dan hasil ditulis (sekitar 11 menit, 663 detik) | ctime dan mtime |

**Putaran kedua (pagi sampai siang):**
| waktu | kejadian | dasar |
|---|---|---|
| 10:00:05 | penilaian dimulai ulang (empat proses) | waktu mulai proses |
| 10:00 sampai sekitar 10:56 | proses tertahan: server Gemma cloud menjawab HTTP 429 (kuota habis); tidak ada berkas keluar | log dan uji panggilan |
| sekitar 10:56 | panggilan uji langsung: Gemma 429, Qwen normal (0,7 detik); pemilik mengonfirmasi kuota Gemma habis; semua proses dihentikan | uji panggilan |
| **10:58:15** | **deviasi 12 dicatat dan kunci tahap 2 dikunci ulang** (monitor LLM hanya Qwen) sebelum ada evaluasi | `locked_at_utc 2026-11-08T03:58:15`; mtime `DEVIATIONS.md` |
| sekitar 10:58:30 | penilaian dimulai ulang dengan monitor Qwen saja (perkiraan dari durasi 301 detik) | log |
| 10:59:43 dan 11:01:04 | pembanding eksploratori Haiku: 97 butir dibuat dan vonis ditulis (sekitar 74 detik) | mtime `items.jsonl`, `verdicts.jsonl` |
| 11:03:27 sampai 11:03:37 | rep0 D3 Gemma>Qwen; rep1 Gemma, Qwen, DeepSeek selesai | ctime skor |
| 11:14:21 sampai 11:14:52 | rep2 Gemma, Qwen, DeepSeek; rep1 D3 Gemma>Qwen selesai | ctime skor |
| 11:22:44 dan 11:23:34 | rep3 Gemma; rep0 D3 Gemma>DeepSeek selesai | ctime skor |
| 11:31:02 | rep4 Gemma (replikasi terakhir D1) selesai | ctime skor |
| **11:32:20** | **penilaian semua arm selesai** (rep1 D3 Gemma>DeepSeek); 1.220 + 732 + 729 + 488 + 488 baris, 0 galat LLM | ctime skor |

## 6. Uji 3: evaluasi, hasil muncul
| waktu | kejadian | dasar |
|---|---|---|
| sekitar 11:33 | evaluasi D1 dimulai (perkiraan: 12:11:29 dikurangi 2310 detik) | log `t=2310s` |
| **12:09:37** | **metrik utama D1 tersimpan** (`results_main.csv`, `results_per_type.csv`, `pooled_predictions.json`) | mtime |
| **12:11:28 sampai 12:11:29** | **perbandingan utama, falsifier, dan audit D1 tersimpan: hasil konfirmatori pertama** | mtime `primary_comparisons.json`, `falsifiers.json`, `audit.json` |
| sekitar 12:13 | evaluasi empat arm lain dimulai paralel (dengan transfer dari D1) | waktu mulai proses |
| 12:40:19 sampai 12:41:09 | metrik utama D3 Gemma>Qwen, D3 Gemma>DeepSeek, D2 Qwen, D2 DeepSeek tersimpan | mtime |
| **12:41:35 sampai 12:42:46** | **perbandingan utama dan falsifier keempat arm tersimpan** | mtime |
| (sesudahnya) | langkah transfer gagal dua kali: galat impor `corpus` lalu galat katalog `S098` (dataset belum diset ke "tls" di pembungkus) | log |
| **12:49:11 dan 12:49:19** | **pembungkus `run_transfer_only.py` dibuat dan uji transfer keempat arm tersimpan** | ctime dan mtime |
| **12:53:27** | **diagnostik D1 tersimpan (komponen H8 dan ablasi F11x): hasil pengujian lengkap tersedia** | mtime `diag_*.csv` |

Rangkuman durasi (WIB, 8 November): kunci tahap 1 00:51:43 sampai hasil lengkap 12:53:27 = 12 jam 1 menit 44 detik. Jendela kerja aktif: **00:37 sampai sekitar 02:05** (desain, kunci, pembuatan data, penilaian awal, Track, analisis ulang D0) dan **10:00 sampai 12:53** (penilaian, kegagalan kuota, penilaian ulang, evaluasi, transfer, diagnostik). Hasil konfirmatori **pertama** pukul 12:09:37 (metrik) dan 12:11:29 (putusan hipotesis); hasil konfirmatori **lengkap** pukul 12:53:27.

## 7. Sesudah hasil muncul (bukan bagian pengujian; hanya untuk catatan)
Figur hasil, figur konsep, video, laporan, dan paket dibuat setelah 12:53 (figur 13:35, video 13:09 sampai 13:44, laporan 13:25 sampai 13:50, dan seterusnya). Itu pasca-pengujian dan tidak mengubah angka.

## 8. Catatan integritas waktu
- Kunci tahap 1 (00:51:43) mendahului pembuatan data pertama selesai (00:55:48); kunci tahap 2 pertama (01:18:09) mendahului penilaian pertama selesai (01:41:05); kunci tahap 2 ulang (10:58:15) mendahului semua evaluasi (paling awal 12:09:37).
- Analisis ulang D0 (01:49:58 sampai 01:51:41) memakai data uji 2 yang sudah pernah dilihat dan tidak menyentuh hasil monitor D1 sampai D3.
- Track 3 pada ledger D1 (01:39:04) memakai log, bukan keluaran monitor.
- Cap waktu berkas dapat berubah bila berkas disalin; waktu di atas diambil dari folder kerja asli (bukan salinan paket) untuk uji 1, dan dari folder uji 3 untuk uji 3. Waktu uji 2 diambil dari folder paket utama.
