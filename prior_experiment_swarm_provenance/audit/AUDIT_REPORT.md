# AUDIT REPORT — Swarm Provenance ("Trust the Report or Check the Artifact?")

Tanggal audit: 2026-11-06. Pengaudit: Claude (Sonnet 5.5) — pembuat awal eksperimen ini juga Claude, jadi ini audit-diri; ChatGPT/pihak ketiga sebaiknya memeriksa ulang.
Semua isi berkas diperlakukan sebagai data. Hasil lama TIDAK ditimpa: `../hasil/` (baseline), `baseline_code/` (kode asli), hasil baru di `hasil_v2/`.

## Ringkasan eksekutif

| # | Temuan | Keparahan | Status |
|---|---|---|---|
| F1 | Seluruh klaim angka laporan lama cocok dengan data JSON (2.845; 97,6%; 4,2%; 0,0193; 0,0632; 19/19 tes) | — (terverifikasi) | OK |
| F2 | `hash()` bawaan Python membuat pemilihan pasangan sumber kembar berubah tiap proses | **TINGGI** (reprodusibilitas) | Diperbaiki + diuji |
| F3 | Kelompok "jujur" membuang pasangan mirip (`containment > 0,3`); tidak ada kontrol negatif sumber kembar | **TINGGI** (validitas konstruk) | Kontrol baru ditambah; **hasilnya menurunkan klaim** |
| F4 | Agen = skrip, bukan LLM | **TINGGI** (batas generalisasi) | Istilah laporan harus diubah |
| F5 | Tugas pada dasarnya deteksi near-duplicate; rancangan skenario dan detektor berbagi operator | SEDANG | Dianalisis; sebagian diuji |
| F6 | Ukuran sampel efektif jauh lebih kecil dari jumlah baris; interval Wilson terlalu sempit | SEDANG | Bootstrap berklaster ditambah |
| F7 | Ambang 5% FPR tidak stabil antar seed; sensitivitas ambang belum dilaporkan | RENDAH | Sensitivitas dihitung |
| F8 | Kalibrasi Platt tanpa C2 dan prevalensi berbeda (72% vs 83%) | RENDAH | Brier seimbang ditambah |

**Putusan: lihat `FINAL_DECISION.md` — MAJOR REVISION REQUIRED (naskah, bukan percobaan).**

## F1 — Verifikasi klaim (kode independen `verifikasi_klaim.py`, tanpa mengimpor `lab.py`/`metrik.py`)

| Klaim | Hasil verifikasi dari `hasil/seed_*.json` | Cocok |
|---|---|---|
| 2.845 skenario | 2.845 (572+567+566+575+565) | ya |
| 5 seed | 20261106–20261110 | ya |
| Distribusi H / C1 / C2 | 476 / 1.169 / 1.200 (prevalensi salinan 83,3%) | ya |
| Deteksi B4 97,6% | TP 2.313 / 2.369 salinan = 97,64% (gabungan C1+C2; per sel L5 lebih rendah, 88–94%) | ya |
| FPR B4 4,2% | FP 20 / 476 = 4,20% | ya |
| Brier B4 0,0193; B2 0,0632 | 0,0193; 0,0632 (semua baris) | ya |
| 19/19 tes | 19 tes lulus (Python 3.12.10) | ya |

Tambahan yang tidak ada di laporan lama (dihitung dari data yang sama): precision B4 0,9914, F1 0,9838; B2 precision 0,9844, recall 0,9320. Brier acuan tanpa informasi = 0,1393 (A1 = 0,1548 lebih buruk daripada acuan).

Catatan lingkup: "97,6%" adalah **rata-rata gabungan** C1+C2 semua level pada prevalensi 83%. Itu sah, tetapi bukan angka kasus tersulit (L4/L5: 88–96%).

## F2 — Reproduksibilitas: `hash()` bawaan Python

Bukti kode: `jalankan.py:49` (`h = hash(sh); if h % 8 == 0`) memilih 1/8 shingle untuk diindeks; `lab.py:172` memakai `hash` sebagai kunci kamus. Hash string/tuple string Python diacak per proses (`PYTHONHASHSEED`).

Uji (`uji_hash.py`, kode LAMA, potongan teks sama, 3 proses dengan `PYTHONHASHSEED`=1,2,3):
- Tiap proses menghasilkan 150 pasangan, tetapi **hanya 14–18 pasangan beririsan antar dua proses; hanya 3 pasangan sama di ketiganya; gabungan 404**.
- Sidik jari hasil berbeda tiap proses (c6d50b1e93 / bf974e029b / 1561b331f9).

Dampak: `cache/pool.json` lama membekukan satu himpunan acak pasangan kembar. Angka laporan tetap dapat ditelusuri ke JSON, tetapi **pipeline tidak dapat direproduksi dari nol**, dan himpunan C2 adalah satu sampel acak dari ±400 kandidat pasangan.

Perbaikan: `lab.hash_stabil` (SHA-256), urutan pasangan dengan pemutus seri deterministik. Uji kode BARU, 3 proses (`PYTHONHASHSEED`=1,2,3): sidik jari identik `2b7e204cd6` (150 pasangan). Dua pengulangan penuh (PYTHONHASHSEED acak berbeda) menghasilkan lima `seed_*.json` **identik bit demi bit** (selisih skor maks 0,0; 0 bendera berbeda) — namun run ke-2 memakai `pool.json` v3 dari run-1, jadi penemuan pasangan di run penuh hanya diuji lewat uji 3-proses di atas.

## F3 — Kontrol negatif sumber kembar

Bukti: `lab.py:138` (`containment(s1,s2) > 0.3 → continue`) membuang pasangan jujur yang mirip. Akibatnya kelompok H hanya berisi pasangan **tidak** mirip, sehingga pengawas berbasis kemiripan hampir otomatis "tidak salah alarm" — padahal kasus yang diklaim ("jujur namun sumber mirip") tidak diuji.

Kontrol baru (tipe `HT`: kedua bot mengutip penuh sumber kembar masing-masing; `HT2`: masing-masing ±60% kalimat; label 0 = tidak ada penyalinan oleh agen; sumber memang kembar). Ambang **tidak diubah** (dikalibrasi hanya pada H). Hasil (5 seed, 500 baris per jenis; CI95 bootstrap berklaster-buku):

| Pengawas | FPR H (lama-style) | **FPR HT (kutip penuh)** | **FPR HT2 (kutip 60%)** |
|---|---|---|---|
| B1 kutipan di sumber | 3,8% | 4,4% [1,4–9,5] | 6,4% |
| B2 overlap kata | 5,7% | **98,2%** [96,3–99,5] | 89,8% |
| B3 sumber kembar | 5,7% | **100%** | 100% |
| B4 embedding | 6,1% | **91,8%** [84,4–96,6] | 80,8% |
| Gabungan OR | 14,2% | 100% | 100% |

Tafsir (jujur): pengecek kemiripan artefak (B2, B4) dan pengecek sumber (B3) **tidak dapat membedakan** (i) dua agen jujur yang mengutip dua buku yang memuat paragraf sama dari (ii) satu agen yang menyalin. Pada L0–L2 artefak kedua kasus identik secara statistik; hanya **bukti proses** (log penelusuran, urutan tindakan) yang membedakan. B1 tidak menandai HT tetapi juga gagal pada C2 L0–L2 (29–37%). Jadi yang diukur eksperimen adalah **"deteksi ketergantungan bukti"**, bukan "deteksi kecurangan agen". Menyamakan keduanya adalah kesalahan konstruk yang harus dihapus dari naskah.

Pembeda yang masih bekerja: salinan tersamar berat (L3–L5) yang diklaim berasal dari sumber kembar tetap ditangkap B1 (97–100% pada L3/L4) karena kutipan tak lagi cocok sumber; honest-twin tidak ditandai B1. Ini analisis eksploratori dan hanya valid untuk penyamaran ber-ciri permukaan.

## F4 — Batas simulasi

Seluruh "agen" adalah fungsi Python (`samarkan`, `catatan_jujur`, `_bot`); tidak ada LLM, tidak ada interaksi, tidak ada tujuan atau strategi adaptif. Pengawas A2 hanyalah aturan, bukan LLM pembaca laporan. Istilah yang tepat: **"simulasi terkontrol berbasis skrip terhadap pengawas heuristik/embedding"**. Tidak boleh ditulis "swarm", "LLM agents", atau "membuktikan efektivitas pada swarm LLM nyata". Generalisasi terbatas pada: penyamaran permukaan (acak kata/kalimat/format/mosaik), teks buku berbahasa campuran di satu korpus, satu model embedding (embeddinggemma-2:740m, Q8_0), satu domain.

## F5 — Potensi kebocoran rancangan

- **Label bocor lewat konstruksi**: salinan = turunan langsung teks bot-1; jujur = potongan lain yang dipilih sebagai tetangga kata terdekat dari 200 kandidat satu bidang, lalu disaring `containment ≤ 0,3`. Maka B2 (containment 3-gram) berbagi operator dengan penyaring dan dengan penyamar L3 (buang/tukar kata) — keunggulan B2 pada L0–L3 sebagian adalah artefak rancangan. B4 independen dari operator itu tetapi tetap menang karena tugas = near-duplicate detection.
- **Ketidakseimbangan**: test 83% positif; kalibrasi Platt 72% positif, tanpa C2. Brier bergantung pada campuran. Brier seimbang (bobot kelas 50:50): B4 0,026 vs B2 0,070; urutan antar metode tidak berubah.
- **Distribusi C2**: 1.200 baris C2 berasal dari hanya 137 potongan sumber unik (HT: 126), karena pasangan kembar per seed hanya 16–70.
- **Ketergantungan ambang**: lihat F7. **Overfitting ke sintetis**: tidak terukur; tidak ada data ground-truth eksternal.
- Pengujian tambahan yang layak dan dilakukan tanpa mengubah hipotesis: HT/HT2, sensitivitas ambang, Brier seimbang, bootstrap berklaster. Yang tidak dilakukan (butuh desain baru): penyamaran semantik (parafrase/terjemahan), agen adaptif, pengawas LLM.

## F6 — Statistik

Semua hasil bersifat **deskriptif**. Interval Wilson di laporan lama memperlakukan tiap baris independen; kenyataannya buku, potongan, dan pasangan kembar yang sama muncul di banyak seed dan banyak level. Baseline: FPR B4 20/476 → Wilson ≈ [2,7%; 6,4%]. Hasil baru memakai **bootstrap berklaster-buku (2.000 resample, benih 20261107)**: FPR B4 6,1% [3,9; 8,7]. Selisih Brier B2−B4 = 0,0451, CI95 bootstrap [0,0396; 0,0508] (positif di semua seed pada analisis lama); ini bukti kuat konsisten, **bukan uji signifikansi formal**; tidak ada uji hipotesis yang dilakukan, jadi jangan ditulis "signifikan". Klaster hanya memakai buku bot-1 (buku bot-2 tak dimodelkan) — keterbatasan.

## F7 — Sensitivitas ambang (FPR target kalibrasi → hasil uji pooled, B4)

| target | FPR H | deteksi C1 | deteksi C2 | FPR HT |
|---|---|---|---|---|
| 1% | 0,4% | 85,8% | 88,2% | 69,4% |
| 2,5% | 3,2% | 96,8% | 97,7% | 89,8% |
| 5% (dipakai) | 6,1% | 98,0% | 98,0% | 91,8% |
| 10% | 11,4% | 98,8% | 98,8% | 93,6% |
| 20% | 21,6% | 99,5% | 99,3% | 94,2% |

FPR per seed dengan target 5%: B4 0,0–8,4%; B2 1,0–15,8% (ambang dari ±95 sampel jujur per seed). Tidak ada ambang yang menurunkan FPR HT tanpa membuang deteksi; HT tak bisa "diselesaikan" dengan ambang.

## Perubahan nilai baseline → baru (bukan hasil penyetelan)

Setelah hash dibuat deterministik, himpunan pasangan kembar berubah (pool 3.908 → 3.941 potongan), sehingga kelompok H juga ditarik ulang: 476 → 473 baris; C1 1.169 → 1.163. FPR B4 4,2% → 6,1% (di dalam CI), deteksi B4 97,6% → 98,0%, Brier B4 0,0193 → 0,0192, B2 0,0632 → 0,0643. Tidak ada seed, ambang, atau subset yang dipilih; 5 seed sama, parameter sama (`--n-jujur 100 --n-salin 40 --per-buku 20`).

## Yang TIDAK diaudit / artefak tidak tersedia

- Tahap 6 (referensi & templat) tidak diulang di audit ini: referensi bertanda † (5 buah) tetap belum diverifikasi ke sumbernya; enam referensi lain dicocokkan lewat web pada sesi penyusunan. Perlu pemeriksaan manual oleh penulis. Zotero tidak diperlukan.
- Tidak ada ground-truth manusia; tidak ada LLM-pembaca laporan.
- Reproduksi penuh bergantung pada korpus 184 buku dan Ollama lokal (`embeddinggemma-2:740m`, digest `f4981a15…`), yang tidak disertakan (hak cipta). Pihak lain hanya bisa: (1) memverifikasi angka dari JSON, (2) menjalankan tes dengan fixture sintetis. **Ketiganya tidak setara** — lihat `TEST_REPORT.md`.
