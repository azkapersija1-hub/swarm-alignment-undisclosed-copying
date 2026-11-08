# Prompts untuk membuat figur lewat chatbot (ChatGPT / Antigravity)

Data nyata: `d1_test_features.csv` (610 baris = split uji arm D1, agen Gemma; 370 salinan tanpa pengungkapan, 240 bukan; kolom E_sup kosong pada 40 baris = status ABSTAIN karena tidak ada sumber).
Kolom: scenario_id, replicate, type, copying_undisclosed (0/1), cosine, lexical_3gram, E_sup, S_disguise, F_omit.
ATURAN UNTUK SEMUA PROMPT: jangan mengarang angka, hanya baca CSV. Kirim kode Python-nya ke saya untuk diperiksa sebelum dipakai.

---------------------------------------------------------------
## PROMPT 1: figur 3D data nyata (Plotly) — rekomendasi utama
---------------------------------------------------------------
I attach a CSV (d1_test_features.csv). Write ONE self-contained Python script (pandas + plotly + kaleido) that:
1. Reads the CSV with pandas. Drop rows where E_sup is empty (ABSTAIN) and print how many were dropped. Do not impute or invent any value.
2. Makes an interactive 3D scatter (plotly.graph_objects.Scatter3d). Axes: x = cosine, y = E_sup, z = S_disguise. One trace per class: copying_undisclosed = 1 ("undisclosed copying") and 0 ("not copying"). Marker size 3, opacity 0.7. Hover text shows scenario type and the three values.
3. Style: white background, black axis text, light grey grid, sans-serif font, class colours black (copying) and mid-grey #9a9a9a (not copying) with a different marker symbol for each class (circle vs diamond) so it works in black and white print. No gradients, no 3D shadows, no decorative icons. Axis titles: "Embedding cosine (A vs B)", "E_sup: support excess (A source minus B source)", "S_disguise: semantic-lexical contrast". Title: "Undisclosed copying separates only when source-aware features are used (D1, test split, n = ...)" with n computed from data.
4. Saves: fig3d.html (interactive, plotly.offline include_plotlyjs="cdn"), and three static PNGs (dpi-equivalent width 1800 px) from three fixed camera angles using fig.write_image: fig3d_view1.png, fig3d_view2.png, fig3d_view3.png.
5. Also makes a 2D companion: scatter of cosine (x) vs E_sup (y) in the same style, saved fig2d_cosine_vs_esup.png.
Constraints: no random jitter, no sampling unless n > 2000 (then print that it sampled with a fixed seed). Print the class counts at the end. Add short comments. Do not use any other data source.

---------------------------------------------------------------
## PROMPT 2: figur animasi Three.js (opsional, hanya untuk presentasi/video)
---------------------------------------------------------------
Write a single self-contained index.html using three.js (import from cdn.jsdelivr.net, pinned version) that loads d1_test_features.csv via an embedded JSON copy (I will paste the CSV below, do not invent data) and renders the same 3D scatter as an orbitable scene: x = cosine, y = E_sup, z = S_disguise, white background, black points for undisclosed copying and grey points for not copying, thin grey axis lines with tick labels, OrbitControls with slow auto-rotate that stops on drag, a small legend in plain HTML. No post-processing, no glow, no icons. Drop rows with empty E_sup and show the dropped count in the legend.

---------------------------------------------------------------
## PROMPT 3: skema arsitektur hitam-putih dengan ikon bot/LLM (SVG)
---------------------------------------------------------------
Write a Python script (matplotlib only, no external images) that draws a black-and-white scientific schematic of this exact pipeline and saves fig_arch_bw.svg and fig_arch_bw.png.
Boxes (use these labels with exact spelling and no others): "Source documents (109 docs, 17 domains)"; "Agent A (LLM)"; "Agent B (LLM)"; "Reports A and B + cited sources"; "Controller ledger (SHA-256 hash chain)"; "Formula monitors"; "LLM monitor"; "Log monitor"; "Ground truth: A copying, B non-independent evidence, C false provenance claim"; "AUROC, recall, FPR, Brier".
Arrows: Source -> Agent A; Source -> Agent B; dashed arrow Agent A -> Agent B labelled "copy / paraphrase (instructed)"; Agent A and Agent B -> Reports; Agent A and Agent B -> Controller ledger; Reports -> Formula monitors; Reports -> LLM monitor; Controller ledger -> Log monitor; the three monitors -> "AUROC, recall, FPR, Brier"; Ground truth -> "AUROC, recall, FPR, Brier" (dashed).
Style: white background, black lines (1.2 pt), no fill colours except very light grey (#f2f2f2) boxes, one small simple vector bot icon (a rounded square head with two dots and an antenna, drawn with matplotlib patches) on each "Agent" and "LLM monitor" box only. Layout left to right in four columns, no overlapping text, font DejaVu Sans 9 pt. Do not add any other component.

---------------------------------------------------------------
## Daftar periksa yang saya pakai untuk menilai kode dari chatbot
---------------------------------------------------------------
1. Membaca CSV asli, tanpa angka yang ditulis tangan atau dibuat acak.
2. Baris E_sup kosong dibuang dan jumlahnya dicetak (seharusnya 40 dari 610).
3. Jumlah kelas tercetak: 370 salinan, 240 bukan (setelah dibuang: kurang dari 610).
4. Label dan judul sesuai data (n dihitung dari data, bukan diketik).
5. Tidak ada jitter, sampling, atau normalisasi tersembunyi.
6. Berbeda bentuk penanda, bukan hanya warna.
7. File keluaran benar dibuat dan bisa dibuka.
