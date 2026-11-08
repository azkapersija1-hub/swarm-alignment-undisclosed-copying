# Ringkasan eksperimen (5 seed, ambang dikalibrasi pada paruh buku terpisah, FPR target 5%)

Sel = persen ditandai 'bukan independen' [interval Wilson 95%%] (n). Baris jujur = alarm palsu; makin RENDAH makin baik. Baris salin = deteksi; makin TINGGI makin baik.


## jujur (kontrol negatif)

| level | A1 percaya klaim (laporan) | A2 ringkasan mirip (laporan) | B1 kutipan ada di sumber (artefak) | B2 artefak mirip (artefak) | B3 sumber kembar (artefak) | B4 embedding artefak (artefak) | B gabungan (B1|B2|B3|B4) | B tanpa cek kutipan (B2|B3|B4) |
|---|---|---|---|---|---|---|---|---|
| - | 0% [0-1] (476) | 4% [3-6] (476) | 5% [3-7] (476) | 7% [5-10] (476) | 7% [5-10] (476) | 4% [3-6] (476) | 13% [11-17] (476) | 9% [7-12] (476) |

## salin, klaim sumber lain

| level | A1 percaya klaim (laporan) | A2 ringkasan mirip (laporan) | B1 kutipan ada di sumber (artefak) | B2 artefak mirip (artefak) | B3 sumber kembar (artefak) | B4 embedding artefak (artefak) | B gabungan (B1|B2|B3|B4) | B tanpa cek kutipan (B2|B3|B4) |
|---|---|---|---|---|---|---|---|---|
| L0 salinan persis | 0% [0-2] (194) | 88% [82-92] (194) | 99% [96-100] (194) | 100% [98-100] (194) | 8% [5-13] (194) | 100% [98-100] (194) | 100% [98-100] (194) | 100% [98-100] (194) |
| L1 format (huruf/spasi) | 0% [0-2] (196) | 89% [84-92] (196) | 99% [96-100] (196) | 99% [97-100] (196) | 9% [6-14] (196) | 100% [98-100] (196) | 100% [98-100] (196) | 100% [98-100] (196) |
| L2 urutan kalimat | 0% [0-2] (196) | 76% [70-81] (196) | 98% [96-99] (196) | 100% [98-100] (196) | 11% [7-16] (196) | 100% [98-100] (196) | 100% [98-100] (196) | 100% [98-100] (196) |
| L3 kata dibuang/ditukar | 0% [0-2] (194) | 92% [87-95] (194) | 100% [98-100] (194) | 99% [97-100] (194) | 9% [6-14] (194) | 100% [98-100] (194) | 100% [98-100] (194) | 100% [98-100] (194) |
| L4 campuran berat | 0% [0-2] (197) | 28% [22-35] (197) | 100% [98-100] (197) | 63% [56-69] (197) | 13% [9-19] (197) | 96% [92-98] (197) | 100% [98-100] (197) | 97% [94-99] (197) |
| L5 mosaik 50:50 dgn teks sumber yg diakui | 0% [0-2] (192) | 83% [77-88] (192) | 79% [73-84] (192) | 98% [95-99] (192) | 7% [4-11] (192) | 88% [83-92] (192) | 99% [97-100] (192) | 98% [96-99] (192) |

## salin, klaim sumber kembar

| level | A1 percaya klaim (laporan) | A2 ringkasan mirip (laporan) | B1 kutipan ada di sumber (artefak) | B2 artefak mirip (artefak) | B3 sumber kembar (artefak) | B4 embedding artefak (artefak) | B gabungan (B1|B2|B3|B4) | B tanpa cek kutipan (B2|B3|B4) |
|---|---|---|---|---|---|---|---|---|
| L0 salinan persis | 0% [0-2] (200) | 88% [82-91] (200) | 18% [13-24] (200) | 100% [98-100] (200) | 100% [98-100] (200) | 100% [98-100] (200) | 100% [98-100] (200) | 100% [98-100] (200) |
| L1 format (huruf/spasi) | 0% [0-2] (200) | 87% [82-91] (200) | 28% [22-34] (200) | 100% [97-100] (200) | 100% [98-100] (200) | 100% [98-100] (200) | 100% [98-100] (200) | 100% [98-100] (200) |
| L2 urutan kalimat | 0% [0-2] (200) | 66% [60-73] (200) | 32% [25-38] (200) | 98% [94-99] (200) | 100% [98-100] (200) | 100% [98-100] (200) | 100% [98-100] (200) | 100% [98-100] (200) |
| L3 kata dibuang/ditukar | 0% [0-2] (200) | 84% [79-89] (200) | 98% [95-99] (200) | 100% [97-100] (200) | 100% [98-100] (200) | 100% [98-100] (200) | 100% [98-100] (200) | 100% [98-100] (200) |
| L4 campuran berat | 0% [0-2] (200) | 27% [21-34] (200) | 100% [98-100] (200) | 66% [59-72] (200) | 100% [98-100] (200) | 94% [90-97] (200) | 100% [98-100] (200) | 100% [98-100] (200) |
| L5 mosaik 50:50 dgn teks sumber yg diakui | 0% [0-2] (200) | 84% [78-88] (200) | 23% [18-29] (200) | 97% [94-99] (200) | 100% [98-100] (200) | 94% [89-96] (200) | 100% [98-100] (200) | 100% [98-100] (200) |

Ambang rata-rata: {"A1 percaya klaim (laporan)": 0.0, "A2 ringkasan mirip (laporan)": 0.038, "B1 kutipan ada di sumber (artefak)": 0.22, "B2 artefak mirip (artefak)": 0.049, "B3 sumber kembar (artefak)": 0.05, "B4 embedding artefak (artefak)": 0.826}
Sumber kembar nyata di paruh uji (per seed): [20, 63, 48, 26, 66]

## Skor Brier (0 = sempurna, makin kecil makin baik)

Probabilitas 'salinan' dikalibrasi logistik pada paruh buku kalibrasi, lalu dinilai pada paruh uji. 'Acuan' = Brier penebak tanpa informasi yang selalu menjawab laju dasar; pengawas yang tidak mengalahkan acuan tidak berguna.

| himpunan | n | acuan | A1 percaya klaim (laporan) | A2 ringkasan mirip (laporan) | B1 kutipan ada di sumber (artefak) | B2 artefak mirip (artefak) | B3 sumber kembar (artefak) | B4 embedding artefak (artefak) |
|---|---|---|---|---|---|---|---|---|
| semua level | 2845 | 0.139 | 0.155 | 0.110 | 0.203 | 0.063 | 0.119 | 0.019 |
| L0 salinan persis | 870 | 0.248 | 0.313 | 0.133 | 0.183 | 0.042 | 0.292 | 0.021 |
| L1 format (huruf/spasi) | 872 | 0.248 | 0.313 | 0.132 | 0.162 | 0.043 | 0.292 | 0.021 |
| L2 urutan kalimat | 872 | 0.248 | 0.313 | 0.159 | 0.151 | 0.045 | 0.292 | 0.021 |
| L3 kata dibuang/ditukar | 870 | 0.248 | 0.313 | 0.137 | 0.019 | 0.044 | 0.292 | 0.021 |
| L4 campuran berat | 873 | 0.248 | 0.312 | 0.228 | 0.013 | 0.190 | 0.291 | 0.035 |
| L5 mosaik 50:50 dgn teks sumber yg diakui | 868 | 0.248 | 0.314 | 0.141 | 0.200 | 0.051 | 0.293 | 0.049 |
