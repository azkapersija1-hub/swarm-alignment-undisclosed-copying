# revised_code

Kode hasil audit. Kode asli ada di `../baseline_code/`. Lihat `../CHANGELOG.md` untuk perubahan.

- `lab.py` — penyamaran, skenario (H, C1, C2, **HT/HT2 baru**), pengawas, ambang, Platt, Brier, Wilson, `hash_stabil`.
- `jalankan.py` — membangun pool dari korpus 184 buku, menjalankan 5 seed → `../hasil_v2/seed_*.json` (butuh korpus + Ollama `embeddinggemma-2:740m`).
- `analisis_audit.py` — metrik lengkap, bootstrap berklaster-buku, sensitivitas ambang → `analisis_audit.json`, `RESULTS_COMPARISON.csv`.
- `verifikasi_klaim.py` — verifikasi independen dari JSON, tanpa mengimpor `lab.py`.
- `uji_hash.py` — uji determinisme pemilihan pasangan kembar lintas proses.
- `tests/` — 27 tes (fixture sintetis; tidak butuh korpus).

Perintah: lihat `../TEST_REPORT.md`. `cache/` (jika ada) berisi teks buku — jangan dipublikasikan.
