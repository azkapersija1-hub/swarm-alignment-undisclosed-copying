# Klaim yang boleh dan tidak boleh, dan gaya bahasa

## Boleh ditulis (bersandar pada uji 3 konfirmatori, kecuali dinyatakan lain)
- "Kosinus embedding mendekati peluang acak untuk mendeteksi penyalinan terselubung pada bed uji ini (AUROC 0,49 sampai 0,63 di lima arm)."
- "Ensemble F11x memiliki AUROC 0,88 sampai 0,97 dan mengungguli kosinus di setiap arm dengan selisih titik 0,25 sampai 0,45."
- "Keunggulan F11x atas baseline internal F9b kecil (selisih titik 0,01 sampai 0,05; interval hingga 0,09) dan melewati gerbang pra-terdaftar hanya di tiga dari lima arm."
- "Dari sepuluh hipotesis kandidat, tiga bertahan di semua arm (H1, H6, H9), empat gugur di semua arm (H2, H7, H8, H10), dan tiga bervariasi (H3, H4, H5)."
- "Log berjangkar menaikkan AUROC F9b dari 0,909 menjadi 0,969 pada arm utama; rekaman terbuka yang dipalsukan menghapus manfaat itu."
- "Injeksi leksikal dan kutipan terpecah menurunkan laju penandaan F11x menjadi sekitar 12% dan 44%."
- "Model yang dikalibrasi pada agen Gemma mentransfer buruk ke agen lain (AUROC F11x 0,71 sampai 0,78)."
- "Pada ambang yang dikalibrasi (FPR 5%) monitor LLM Qwen hampir tidak menandai penyalinan (recall 0,01 sampai 0,15)."
- "Hasil eksploratori awal lebih tinggi daripada konfirmatori; pola relatif bertahan." (uji 2 versus uji 3)
- Hash chain tanpa jangkar tidak mendeteksi pemotongan ekor dan penulisan ulang admin; jangkar eksternal mendeteksinya; pemegang kunci yang disusupi mengalahkan ketiga rezim (kunci demo).
- Pembatasan: audit retrospektif, penyalinan diperintahkan, satu korpus, satu model embedding.

## Tidak boleh ditulis
- "Terbukti aman", "kebal", "deteksi spontan berhasil", "berlaku untuk sistem nyata".
- "F11x lebih baik daripada F9b" tanpa menyebut kecilnya selisih dan 3 dari 5 arm.
- "Formula baru", "rumus Argon", "temuan Argon"; F11x adalah komposisi tim atas fitur yang ada.
- "Pertama di dunia" atau klaim kebaruan matematis atas kosinus, regresi logistik, CSLS, atau rantai hash.
- Membandingkan angka AUROC dengan Rose dkk., Zhang dkk., dan lainnya (data, sinyal, tugas berbeda).
- Menghitung target C sebagai hasil terpisah dari A.
- Memakai angka uji 2 sebagai klaim utama; memakai bahan Haiku sebagai bukti.
- Menyebut H1 atau H3 "sempurna" tanpa catatan desain sintetis.
- Mengutip isi metode atau hasil sumber panitia yang hanya dibaca abstraknya.

## Cara menyebut hal-hal sensitif
- **Argon:** "analisis celah berbantuan AI" (asal hipotesis); pustaka rumus lama disebut "pustaka rumus tim (sebelum sprint)".
- **F9b:** "ensemble regresi logistik atas rumus kemiripan milik tim (STP, STP-AR, MOI, RCC-v3.3), dua fitur pustaka lama, kemiripan leksikal dan kosinus standar, serta tiga pemeriksaan sumber yang disusun selama sprint."
- **Studi awal (uji 2):** "studi eksploratori awal yang rumusnya dirancang sambil melihat data."
- **Kuota:** "kuota layanan Gemma cloud habis di tengah penilaian; sebelum ada hasil konfirmatori yang dihitung, monitor LLM pembanding dijadikan Qwen saja; data agen sudah lengkap."

## Gaya bahasa (naskah Indonesia)
Gaya akademik. Hindari kata "ia". Pakai "selaras dengan" dan "di sisi lain", bukan "senada" atau "kontras". Latar Belakang berbentuk piramida terbalik. Naskah lomba berbahasa Inggris akademik: kalimat pendek, angka dengan interval, kata kerja yang jujur ("menunjukkan", "konsisten dengan"), bukan "membuktikan".

## Tentang istilah
Monitor = alat penilai; agen = model bahasa yang diamati; arm = satu kondisi data; replikasi = satu putaran penuh skenario dengan seed berbeda; eksploratori = dari data yang sudah dilihat saat merancang; konfirmatori = uji ulang dengan data dan aturan yang dikunci lebih dulu.
