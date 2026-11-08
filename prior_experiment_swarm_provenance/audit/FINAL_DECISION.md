# FINAL DECISION

## Status: **MAJOR REVISION REQUIRED** (naskah). Percobaan: tidak perlu diulang dari nol.

### Dasar keputusan (dari hasil audit, bukan dari keinginan hasil positif)
1. **Angka lama benar secara aritmetika** (F1): 2.845 skenario, B4 97,6%, FPR 4,2%, Brier 0,0193/0,0632, 19/19 tes semuanya terverifikasi dari JSON.
2. **Pipeline lama tidak reprodusibel dari nol** (F2) karena `hash()` bawaan; sudah diperbaiki dan dibuktikan deterministik (2 run penuh identik; uji 3-proses identik).
3. **Klaim inti terlalu luas** (F3): kontrol negatif sumber kembar yang baru menunjukkan pengecek kemiripan/sumber (B2, B3, B4) menandai 81–100% pasangan jujur-kembar. Eksperimen mendeteksi **ketergantungan bukti**, bukan **penyalinan/kecurangan agen**. Ini hasil negatif yang harus dimuat, bukan disembunyikan.
4. **Cakupan generalisasi sempit** (F4): bot skrip, penyamaran permukaan, satu model embedding, tanpa pengawas LLM.
5. **Ketidakpastian sebelumnya terlalu sempit** (F6): sampel efektif jauh lebih kecil dari jumlah baris.

### Mengapa bukan "NOT REPRODUCIBLE"
Hasil v2 direproduksi bit demi bit dua kali di mesin pembuat, dan angka baseline dapat ditelusuri ke JSON. Keterbatasan: pihak lain tidak dapat mereproduksi penuh tanpa korpus.

### Mengapa bukan "READY WITH MINOR REVISION"
Judul, abstrak, kesimpulan, dan Gambar 2 versi lama menyiratkan hal yang kini terbantah oleh kontrol negatif baru; Methods/Results/Limitations/Appendix harus ditulis ulang; referensi † belum terverifikasi.

### Yang harus dilakukan sebelum diserahkan (urut prioritas)
1. Revisi naskah mengikuti `MANUSCRIPT_REVISION_NOTES.md` dengan hasil_v2 (angka hanya dari `analisis_audit.json`/CSV).
2. Ganti Gambar 2 agar menyertakan HT/HT2 dan CI bootstrap; hitung ulang kata abstrak (150–250) dan panjang isi (≤ 8 hlm).
3. Verifikasi manual referensi †; isi nama/afiliasi/tautan repositori/kontribusi penulis.
4. Sertakan `audit/` (tanpa `cache/`) sebagai bagian "Code and Data", tandai preexisting vs sprint.
5. Opsional bila waktu ada: penyamaran semantik dan pengawas LLM — hanya sebagai "future work" kecuali dijalankan dan dilaporkan jujur.

### Catatan integritas
Audit dilakukan oleh model yang sama dengan pembuat eksperimen; mintalah peninjau independen (manusia atau model lain) memeriksa `AUDIT_REPORT.md` dan `revised_code/`. Tidak ada seed, ambang, atau subset yang dipilih untuk memperbaiki angka; semua hasil negatif dilaporkan.
