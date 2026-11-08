# BACA DULU: paket bahan untuk membantu menulis laporan (Swarm Alignment Hackathon 2026, Track 4)

Paket ini berisi bahan jadi, bukan bahan untuk diuji ulang. Tiga uji sudah selesai. Tugas GPT: membantu menyusun kalimat laporan **dari bahan yang ada**, apa adanya.

Peneliti: Mochamad Azmi Rizkulloh (nama tertulis di bahan sebelumnya; peneliti memeriksa ulang ejaan dan afiliasinya). Batas pengumpulan: Minggu 8 November 2026 pukul 23.59 AoE (Senin 9 November pukul 18.59 WIB). Format: PDF pada templat resmi Apart, maksimal 8 halaman di luar referensi dan lampiran, abstrak 150 sampai 250 kata, lampiran "Limitations and Dual-Use / Ethical Considerations".

## Urutan membaca
1. `01_PROMPT_UNTUK_GPT.md`: instruksi tugas (tempel ke GPT).
2. `02_NARASI_LENGKAP_UJI_1_2_3.md`: **sumber utama**: tujuan, metode, rumus, hasil uji 1, 2, 3, keterbatasan, dual-use, kebaruan, tanya-jawab juri.
   - `02b_PENGEMBANGAN_DAN_RUMUS_UJI3.md`: **apa yang dikembangkan pada uji 3 dan semua rumus yang dipakai** (definisi, parameter, asal, berkas kode) untuk bagian Metode dan Lampiran.
   - `02c_LINIMASA_JAM_DEMI_JAM.md`: **linimasa tanggal dan jam** dari uji 1 sampai hasil uji 3 muncul (WIB), dengan dasar cap waktu berkas.
3. `03_ATURAN_LOMBA_DAN_CHECKLIST.md`: aturan panitia dan daftar periksa.
4. `04_BOLEH_DAN_DILARANG_DIKLAIM.md`: klaim yang aman dan tidak aman, serta gaya bahasa.
5. `05_KATALOG_SUMBER.csv` (+ `05b_STATUS_SEMUA_REFERENSI_APART.md`): daftar rujukan, status verifikasi, apa yang boleh dan tidak boleh dikutip.
6. `06_KLAIM_KE_BUKTI.csv`: setiap angka penting dipetakan ke berkas dan kolom buktinya.
7. `07_DATA_CSV/`: data hasil (CSV) untuk dikutip atau dibuat tabel.
8. `08_FIGUR/`: gambar penting (peta konsep, hasil, scatter) beserta SVG; `08_FIGUR/konsep_chatbot/` berisi diagram konsep buatan chatbot yang menjadi acuan gaya.
9. `09_LAPORAN_JADI/`: laporan lengkap EN dan ID dan draf versi lomba (sebagai contoh dan sumber kalimat).
10. `10_PRAREGISTRASI_DAN_ASAL_USUL/`: hipotesis resmi, deklarasi, deviasi, pekerjaan sebelum dan selama sprint, tabel dan ringkasan uji 1 dan 2.
11. `11_ANALISIS_CELAH_AI/`: analisis celah berbantuan AI yang melahirkan hipotesis H1 sampai H10.

## Tiga uji dalam satu baris
- **Uji 1:** pilot dengan bot berskrip tanpa LLM (184 buku, 5 seed): mempercayai laporan menangkap 0%; memeriksa sumber menangkap hampir semua.
- **Uji 2:** studi 820 skenario dengan agen Gemma (eksploratori, terkontaminasi): kosinus dan rumus tunggal mendekati peluang acak; pemeriksaan sumber (F9b) dan ensemble (F11x) jauh lebih baik.
- **Uji 3:** uji ulang pra-terdaftar, 5 arm, 3 model agen, seed baru (konfirmatori): kosinus 0,49 sampai 0,63; F11x 0,88 sampai 0,97; keunggulan F11x atas F9b kecil (0,01 sampai 0,05) dan lolos gerbang ketat di 3 dari 5 arm.

## Kesimpulan yang aman
Kemiripan teks saja tidak cukup untuk mendeteksi penyalinan terselubung antar-agen. Pemeriksaan terhadap sumber asli membantu, tetapi hasilnya kecil, tidak merata antar-model, dan masih bisa dihindari serangan adaptif. Log berjangkar menambah daya deteksi; log yang dipalsukan menghapusnya.

## Arti ukuran, sederhana
- **AUROC:** peluang kasus penyalin mendapat skor lebih tinggi daripada kasus jujur. 0,5 = tebakan; 1 = sempurna. Makin tinggi makin baik.
- **Recall:** dari semua yang menyalin, berapa persen tertangkap. Makin tinggi makin baik.
- **FPR:** dari semua yang jujur, berapa persen salah dituduh. Makin rendah makin baik.
- **Brier:** rata-rata kesalahan kuadrat probabilitas; 0 sempurna, 0,25 setara menebak. Makin rendah makin baik.
- **Kosinus (F2):** kemiripan makna dua teks lewat vektor embedding; baseline standar.
- **Monitor** = alat penilai (rumus atau LLM, bekerja offline sesudah kejadian); **agen** = model bahasa yang diamati. Jangan tertukar.
- **Eksploratori** = angka dari data yang sudah dilihat saat merancang; **konfirmatori** = uji ulang dengan data dan aturan yang dikunci lebih dulu.

## Sembilan hal yang harus tertulis jujur
1. Label target A dan C identik pada desain ini.
2. Penyalinan diperintahkan, bukan spontan; hanya 109 dokumen yang sama; satu model embedding.
3. Monitor LLM hanya Qwen karena kuota Gemma habis (deviasi 12); Track 1 dan 2 hanya Qwen dan DeepSeek.
4. Angka eksploratori (F11x 0,99) lebih tinggi daripada konfirmatori (0,93 di D1).
5. Keunggulan F11x atas F9b kecil; lolos gerbang di 3 dari 5 arm.
6. Hipotesis: H1, H6, H9 bertahan di semua arm; H2, H7, H8, H10 gugur di semua arm; H3, H4, H5 bervariasi.
7. AUROC 1,00 pada kontras H1 dan H3 mencerminkan desain sintetis yang mudah.
8. Audit retrospektif, bukan pengawasan waktu nyata.
9. F11x adalah komposisi tim atas fitur yang ada, bukan rumus Argon dan bukan rumus baru.

## Hal yang tidak dicakup paket ini
Templat resmi Apart (harus diunduh peneliti; PDF akhir dibuat pada templat itu), nama penulis lengkap dan afiliasi, dan data mentah besar (ada di ZIP lengkap). Bahan eksploratori Haiku hanya pembanding tambahan.
