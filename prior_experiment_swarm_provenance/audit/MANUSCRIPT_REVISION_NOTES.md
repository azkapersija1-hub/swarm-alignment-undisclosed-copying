# MANUSCRIPT REVISION NOTES

Aturan: JANGAN menaruh angka baru di naskah selain yang tertulis di `AUDIT_REPORT.md` / `hasil_v2/analisis_audit.json` / `RESULTS_COMPARISON.csv`. Laporan lama (`laporan/Swarm_Provenance_Report.*`) memakai hasil BASELINE (`hasil/`); pilih satu himpunan hasil dan pakai konsisten — rekomendasi: **hasil_v2** (deterministik, ada kontrol baru), sebutkan baseline sebagai "run awal".

## Judul/Abstract/Introduction
- Hapus kerangka "kecurangan/penyalinan oleh agen" sebagai hal yang dideteksi. Ganti: pengawas mendeteksi **ketergantungan bukti (artefak mirip / sumber kembar)**; apakah ketergantungan itu disengaja butuh bukti proses.
- Ganti "swarm"/"agents" menjadi "scripted bots / skenario simulasi terkontrol". Jangan menyiratkan pengujian pada LLM.
- Abstract harus menyebut kontrol negatif sumber kembar dan hasil negatifnya (pengecek artefak menandai 81–100% pasangan jujur-kembar).
- Judul boleh dipertahankan, tetapi subjudul/abstrak harus tegas bahwa jawabannya bersyarat: periksa artefak membantu mendeteksi ketergantungan, namun tak membedakan kembar sah dari salinan.

## Methods
- Tambah: definisi `HT`/`HT2` (kontrol negatif), label 0 = tidak ada penyalinan agen walau sumber kembar; ambang & Platt hanya dari H/C1 paruh kalibrasi.
- Tambah: pemilihan pasangan kembar kini deterministik (SHA-256); baseline memakai `hash()` bawaan (tidak deterministik) — nyatakan sebagai koreksi.
- Ganti interval: bootstrap berklaster-buku (2.000, benih 20261107) sebagai ukuran utama; Wilson hanya sebagai referensi dan beri catatan bahwa baris tidak independen. Nyatakan sampel efektif: C2 = 1.200 baris dari 137 potongan unik; HT = 500 dari 126.
- Nyatakan prevalensi uji 83% dan prevalensi kalibrasi ±72%; laporkan Brier biasa **dan** Brier seimbang.
- Nyatakan seluruh hasil deskriptif; hapus kata "signifikan" bila ada.

## Results
- Tabel utama: precision/recall/F1/FPR/Brier (RESULTS_COMPARISON.csv) + CI bootstrap.
- Tabel baru: FPR pada HT dan HT2 per pengawas (B1 4,4/6,4%; B2 98,2/89,8%; B3 100/100%; B4 91,8/80,8%; gabungan 100/100%).
- Sensitivitas ambang (AUDIT_REPORT F7) dan sebaran per-seed.
- Gambar 2 (alarm palsu + Brier) perlu diganti agar memuat HT/HT2; jangan menyebut "alarm palsu 4,2%" tanpa menyebut kontrol sumber kembar. Angka 4,2% dan 97,6% adalah hasil baseline; di hasil_v2: 6,1% dan 98,0%.
- Angka "deteksi ≥88%" lama berasal dari baseline per-sel; hitung ulang dari hasil_v2 sebelum dipakai.

## Discussion & Limitations
- Hasil negatif utama: B2/B3/B4 menandai hampir semua pasangan jujur-kembar; B1 tidak, tetapi gagal pada salinan klaim-kembar L0–L2 (29–37%). Tidak ada pengawas artefak tunggal yang memisahkan kembar sah dari salinan.
- Keterbatasan wajib: bot skrip; penyamaran permukaan; satu model embedding; satu korpus; A2 hanya aturan, tanpa LLM; kebocoran rancangan (B2 berbagi operator containment); sampel efektif kecil; ambang tidak stabil antar seed (B2 1–16%); ketergantungan klaster hanya via buku bot-1; tidak ada ground-truth manusia.
- Rekomendasi berbasis bukti proses (log penelusuran, asal artefak) sebagai pembeda — sebut sebagai hipotesis kerja, belum diuji.

## Appendix
- Limitations & Dual-Use: tambah risiko penyalahgunaan bila pengawas diberi label "deteksi kecurangan" (tuduhan palsu terhadap pengutip sah sumber kembar); tambahkan dampak alarm palsu pada prevalensi rendah: dengan B4, PPV pada prevalensi 1% ≈ 14% bila FPR = FPR H, tetapi ≈ 1% bila populasi jujur berisi sumber kembar (FPR HT).
- Appendix C (preexisting vs sprint): daftar `revised_code/` file baru; catat audit dilakukan oleh model yang sama dengan pembuat eksperimen.
- LLM Usage Statement: sebutkan audit-diri ini; penulis meninjau dan menyunting.

## References
- Referensi bertanda † (dikutip sebagai judul/tahun dari halaman Resources) belum diverifikasi ke sumbernya — verifikasi manual atau hapus. Jangan menambah DOI/penulis dari ingatan. Gaya satu jenis (APA 7 boleh); Zotero tidak wajib.

## Pemeriksaan templat (belum diulang di audit ini)
Judul, penulis/afiliasi (masih placeholder), abstract 150–250 kata (201 kata di versi lama — hitung ulang setelah revisi), Intro, Related Work, Methods, Results, Discussion/Limitations, Conclusion, Code and Data, References, Appendix, LLM Usage Statement; isi utama ≤ 8 halaman (versi lama 7).
