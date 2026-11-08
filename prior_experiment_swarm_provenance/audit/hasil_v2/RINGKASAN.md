# Ringkasan eksperimen (5 seed, ambang dikalibrasi pada paruh buku terpisah, FPR target 5%)

Sel = persen ditandai 'bukan independen' [interval Wilson 95%%] (n). Baris jujur = alarm palsu; makin RENDAH makin baik. Baris salin = deteksi; makin TINGGI makin baik.


## jujur (kontrol negatif)

| level | A1 percaya klaim (laporan) | A2 ringkasan mirip (laporan) | B1 kutipan ada di sumber (artefak) | B2 artefak mirip (artefak) | B3 sumber kembar (artefak) | B4 embedding artefak (artefak) | B gabungan (B1|B2|B3|B4) | B tanpa cek kutipan (B2|B3|B4) |
|---|---|---|---|---|---|---|---|---|
| - | 0% [0-1] (473) | 5% [3-7] (473) | 4% [2-6] (473) | 6% [4-8] (473) | 6% [4-8] (473) | 6% [4-9] (473) | 14% [11-18] (473) | 11% [8-14] (473) |

## salin, klaim sumber lain

| level | A1 percaya klaim (laporan) | A2 ringkasan mirip (laporan) | B1 kutipan ada di sumber (artefak) | B2 artefak mirip (artefak) | B3 sumber kembar (artefak) | B4 embedding artefak (artefak) | B gabungan (B1|B2|B3|B4) | B tanpa cek kutipan (B2|B3|B4) |
|---|---|---|---|---|---|---|---|---|
| L0 salinan persis | 0% [0-2] (192) | 90% [84-93] (192) | 98% [96-99] (192) | 100% [98-100] (192) | 10% [6-15] (192) | 100% [98-100] (192) | 100% [98-100] (192) | 100% [98-100] (192) |
| L1 format (huruf/spasi) | 0% [0-2] (196) | 90% [85-93] (196) | 97% [93-99] (196) | 99% [97-100] (196) | 8% [5-13] (196) | 100% [98-100] (196) | 100% [98-100] (196) | 100% [98-100] (196) |
| L2 urutan kalimat | 0% [0-2] (191) | 69% [62-75] (191) | 100% [98-100] (191) | 99% [97-100] (191) | 5% [3-9] (191) | 100% [98-100] (191) | 100% [98-100] (191) | 100% [98-100] (191) |
| L3 kata dibuang/ditukar | 0% [0-2] (195) | 82% [76-87] (195) | 100% [98-100] (195) | 100% [98-100] (195) | 8% [5-12] (195) | 100% [98-100] (195) | 100% [98-100] (195) | 100% [98-100] (195) |
| L4 campuran berat | 0% [0-2] (196) | 20% [15-26] (196) | 100% [98-100] (196) | 42% [36-49] (196) | 4% [2-8] (196) | 96% [92-98] (196) | 100% [98-100] (196) | 96% [93-98] (196) |
| L5 mosaik 50:50 dgn teks sumber yg diakui | 0% [0-2] (193) | 73% [66-79] (193) | 79% [73-84] (193) | 98% [95-99] (193) | 9% [6-14] (193) | 92% [88-95] (193) | 99% [97-100] (193) | 98% [96-99] (193) |

## salin, klaim sumber kembar

| level | A1 percaya klaim (laporan) | A2 ringkasan mirip (laporan) | B1 kutipan ada di sumber (artefak) | B2 artefak mirip (artefak) | B3 sumber kembar (artefak) | B4 embedding artefak (artefak) | B gabungan (B1|B2|B3|B4) | B tanpa cek kutipan (B2|B3|B4) |
|---|---|---|---|---|---|---|---|---|
| L0 salinan persis | 0% [0-2] (200) | 90% [86-94] (200) | 30% [24-37] (200) | 100% [97-100] (200) | 100% [98-100] (200) | 100% [98-100] (200) | 100% [98-100] (200) | 100% [98-100] (200) |
| L1 format (huruf/spasi) | 0% [0-2] (200) | 83% [77-88] (200) | 29% [23-36] (200) | 100% [97-100] (200) | 100% [98-100] (200) | 100% [98-100] (200) | 100% [98-100] (200) | 100% [98-100] (200) |
| L2 urutan kalimat | 0% [0-2] (200) | 68% [62-75] (200) | 37% [31-44] (200) | 98% [95-99] (200) | 100% [98-100] (200) | 100% [98-100] (200) | 100% [98-100] (200) | 100% [98-100] (200) |
| L3 kata dibuang/ditukar | 0% [0-2] (200) | 79% [73-84] (200) | 97% [94-99] (200) | 100% [97-100] (200) | 100% [98-100] (200) | 100% [98-100] (200) | 100% [98-100] (200) | 100% [98-100] (200) |
| L4 campuran berat | 0% [0-2] (200) | 22% [17-28] (200) | 100% [98-100] (200) | 42% [35-49] (200) | 100% [98-100] (200) | 90% [86-94] (200) | 100% [98-100] (200) | 100% [98-100] (200) |
| L5 mosaik 50:50 dgn teks sumber yg diakui | 0% [0-2] (200) | 78% [72-83] (200) | 26% [21-33] (200) | 98% [94-99] (200) | 100% [98-100] (200) | 98% [94-99] (200) | 100% [98-100] (200) | 100% [98-100] (200) |

## JUJUR sumber kembar, kutip penuh (kontrol negatif baru)

| level | A1 percaya klaim (laporan) | A2 ringkasan mirip (laporan) | B1 kutipan ada di sumber (artefak) | B2 artefak mirip (artefak) | B3 sumber kembar (artefak) | B4 embedding artefak (artefak) | B gabungan (B1|B2|B3|B4) | B tanpa cek kutipan (B2|B3|B4) |
|---|---|---|---|---|---|---|---|---|
| - | 0% [0-1] (500) | 73% [69-77] (500) | 4% [3-7] (500) | 98% [97-99] (500) | 100% [99-100] (500) | 92% [89-94] (500) | 100% [99-100] (500) | 100% [99-100] (500) |

## JUJUR sumber kembar, kutip ~60% (kontrol negatif baru)

| level | A1 percaya klaim (laporan) | A2 ringkasan mirip (laporan) | B1 kutipan ada di sumber (artefak) | B2 artefak mirip (artefak) | B3 sumber kembar (artefak) | B4 embedding artefak (artefak) | B gabungan (B1|B2|B3|B4) | B tanpa cek kutipan (B2|B3|B4) |
|---|---|---|---|---|---|---|---|---|
| - | 0% [0-1] (500) | 66% [62-70] (500) | 6% [5-9] (500) | 90% [87-92] (500) | 100% [99-100] (500) | 81% [77-84] (500) | 100% [99-100] (500) | 100% [99-100] (500) |

Ambang rata-rata: {"A1 percaya klaim (laporan)": 0.0, "A2 ringkasan mirip (laporan)": 0.05, "B1 kutipan ada di sumber (artefak)": 0.217, "B2 artefak mirip (artefak)": 0.081, "B3 sumber kembar (artefak)": 0.081, "B4 embedding artefak (artefak)": 0.817}
Sumber kembar nyata di paruh uji (per seed): [16, 70, 43, 25, 53]

## Skor Brier (0 = sempurna, makin kecil makin baik)

Probabilitas 'salinan' dikalibrasi logistik pada paruh buku kalibrasi, lalu dinilai pada paruh uji. 'Acuan' = Brier penebak tanpa informasi yang selalu menjawab laju dasar; pengawas yang tidak mengalahkan acuan tidak berguna.

| himpunan | n | acuan | A1 percaya klaim (laporan) | A2 ringkasan mirip (laporan) | B1 kutipan ada di sumber (artefak) | B2 artefak mirip (artefak) | B3 sumber kembar (artefak) | B4 embedding artefak (artefak) |
|---|---|---|---|---|---|---|---|---|
| semua level | 2836 | 0.139 | 0.154 | 0.116 | 0.190 | 0.064 | 0.137 | 0.019 |
| L0 salinan persis | 865 | 0.248 | 0.313 | 0.130 | 0.160 | 0.043 | 0.301 | 0.020 |
| L1 format (huruf/spasi) | 869 | 0.248 | 0.312 | 0.135 | 0.165 | 0.044 | 0.300 | 0.020 |
| L2 urutan kalimat | 864 | 0.248 | 0.313 | 0.160 | 0.135 | 0.046 | 0.302 | 0.020 |
| L3 kata dibuang/ditukar | 868 | 0.248 | 0.312 | 0.144 | 0.021 | 0.044 | 0.301 | 0.020 |
| L4 campuran berat | 869 | 0.248 | 0.312 | 0.231 | 0.013 | 0.196 | 0.301 | 0.041 |
| L5 mosaik 50:50 dgn teks sumber yg diakui | 866 | 0.248 | 0.313 | 0.150 | 0.192 | 0.049 | 0.301 | 0.041 |
