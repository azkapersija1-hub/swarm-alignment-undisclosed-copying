"""Builds the compact material pack (<= 20 MB) for a writing assistant: detailed narrative, consolidated CSVs, source catalogue, claim-to-evidence map,
reduced figures, reports, pre-registration files. Everything numeric comes from result files. Usage: build_gpt_pack.py"""
import csv
import glob
import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
import zipfile

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
RT = os.path.dirname(HERE)
ROOT = os.path.dirname(RT)
RES = os.path.join(RT, "results")
PACK = os.path.join(os.path.dirname(ROOT), "BAHAN_GPT_SWARM")
ZIP = PACK + ".zip"
ARMS = [("D1 Gemma (konfirmatori utama)", "gemma_homog"), ("D2 Qwen", "qwen_homog"), ("D2 DeepSeek", "deepseek_homog"), ("D3 Gemma>Qwen", "het_gemma_qwen"), ("D3 Gemma>DeepSeek", "het_gemma_deepseek")]
F2, F9, F11 = "F2 embedding cosine", "F9b ensemble + source checks", "F11x candidate ensemble"
CLAIMS = []


def jl(tag, name):
    return json.load(open(os.path.join(RES, tag, name), encoding="utf-8"))


def mk(*p):
    d = os.path.join(PACK, *p)
    os.makedirs(d, exist_ok=True)
    return d


def write_csv(path, rows, fields=None):
    fields = fields or list(dict.fromkeys(k for r in rows for k in r))
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def claim(cid, text, value, file, locator, status, section):
    CLAIMS.append(dict(id_klaim=cid, klaim=text, nilai=value, berkas_bukti=file, lokasi_di_berkas=locator, status_bukti=status, bagian_laporan=section))


def stack_csv(name, out, extra_tag=True):
    rows = []
    for label, tag in ARMS + [("D0 analisis ulang (eksploratori, terkontaminasi)", "D0_exploratory_contaminated")]:
        p = os.path.join(RES, tag, name)
        if os.path.isfile(p):
            for r in csv.DictReader(open(p, encoding="utf-8")):
                rows.append({"arm": label, **{k: v for k, v in r.items() if k != "arm"}})
    write_csv(os.path.join(PACK, "07_DATA_CSV", out), rows)
    return rows


def flatten(prefix, v, out):
    if isinstance(v, dict):
        for k, x in v.items():
            flatten(prefix + [str(k)], x, out)
    elif isinstance(v, list) and len(v) <= 4 and all(isinstance(x, (int, float)) for x in v):
        out["_".join(prefix)] = "[" + ", ".join("%.4g" % x for x in v) + "]"
    elif not isinstance(v, list):
        out["_".join(prefix)] = v


def tracks_csv():
    t = os.path.join(RES, "tracks")
    for name, out in (("track1_redteam_qwen_deepseek.json", "track1_redteam_ringkasan.csv"), ("track2_summary_qwen_deepseek.json", "track2_v2_ringkasan.csv"), ("track2_v3_summary.json", "track2_v3_ringkasan.csv")):
        d = json.load(open(os.path.join(t, name), encoding="utf-8"))
        d = d.get("summary", d)
        rows = []
        for k, v in d.items():
            r = {"kondisi": k}
            flatten([], v, r)
            rows.append(r)
        write_csv(os.path.join(PACK, "07_DATA_CSV", out), rows)
    d3 = json.load(open(os.path.join(t, "track3.json"), encoding="utf-8"))
    rows = [dict(mode_perusakan=m, **v) for m, v in d3["tamper"]["detection_rate"].items()]
    write_csv(os.path.join(PACK, "07_DATA_CSV", "track3_deteksi_perusakan_log.csv"), rows)
    rows = []
    for k, v in d3.get("chain_attribution", {}).items():
        if isinstance(v, dict):
            for tname, val in v.items():
                rows.append(dict(ukuran=k, jenis_skenario=tname, nilai=val))
    if rows:
        write_csv(os.path.join(PACK, "07_DATA_CSV", "track3_kelengkapan_dan_atribusi.csv"), rows)
    b = json.load(open(os.path.join(t, "track1_board_qwen_deepseek.json"), encoding="utf-8")).get("summary", {})
    rows = []
    for k, v in b.items():
        r = {"model": k}
        flatten([], v, r)
        rows.append(r)
    if rows:
        write_csv(os.path.join(PACK, "07_DATA_CSV", "track1_papan_bersama_ringkasan.csv"), rows)


def primary_tables():
    rows, ci_rows, fal_rows = [], [], []
    for label, tag in ARMS:
        p = jl(tag, "primary_comparisons.json")["target_A"]
        d = p["paired_auroc_diff_ci"]
        k = list(d)
        au = p["auroc"]
        rows.append(dict(arm=label, auroc_F2=round(au[F2], 4), auroc_F9b=round(au[F9], 4), auroc_F11x=round(au[F11], 4),
                         selisih_F11x_F2_lo=round(d[k[0]][0], 4), selisih_F11x_F2_hi=round(d[k[0]][1], 4),
                         selisih_F11x_F9b_lo=round(d[k[1]][0], 4), selisih_F11x_F9b_hi=round(d[k[1]][1], 4),
                         F31_batas_atas95=round(p["f31_gate"]["upper95_bound"], 5), F31_lolos=p["f31_gate"]["promote"],
                         sukses_utama=p["primary_success"], kriteria=json.dumps(p["success_criteria"])))
        for m, v in p["refit_ci"].items():
            if m.startswith("_"):
                continue
            for metric, lh in v.items():
                ci_rows.append(dict(arm=label, monitor=m, ukuran=metric, lo95=round(lh[0], 4), hi95=round(lh[1], 4)))
        f = jl(tag, "falsifiers.json")
        for h, v in f.items():
            fal_rows.append(dict(arm=label, hipotesis=h, gugur=v.get("falsified"), angka=json.dumps({k2: v2 for k2, v2 in v.items() if k2 != "falsified"}, default=str)[:600]))
    write_csv(os.path.join(PACK, "07_DATA_CSV", "perbandingan_utama_5_arm.csv"), rows)
    write_csv(os.path.join(PACK, "07_DATA_CSV", "interval_refit_monitor_utama.csv"), ci_rows)
    write_csv(os.path.join(PACK, "07_DATA_CSV", "hipotesis_falsifier_5_arm.csv"), fal_rows)
    for r, (label, tag) in zip(rows, ARMS):
        st = "konfirmatori"
        for key, col in (("AUROC kosinus F2", "auroc_F2"), ("AUROC F9b", "auroc_F9b"), ("AUROC F11x", "auroc_F11x")):
            claim("PRIM-%s-%s" % (tag, col), "%s, %s (target A)" % (key, label), r[col], "07_DATA_CSV/perbandingan_utama_5_arm.csv", "baris arm=%s, kolom %s" % (label, col), st, "Hasil 4.1")
        claim("PRIM-%s-gain-F2" % tag, "Selisih AUROC F11x minus F2, interval 95%% (%s)" % label, "[%s, %s]" % (r["selisih_F11x_F2_lo"], r["selisih_F11x_F2_hi"]), "07_DATA_CSV/perbandingan_utama_5_arm.csv", "kolom selisih_F11x_F2_lo/hi", st, "Hasil 4.1")
        claim("PRIM-%s-gain-F9b" % tag, "Selisih AUROC F11x minus F9b, interval 95%% (%s)" % label, "[%s, %s]" % (r["selisih_F11x_F9b_lo"], r["selisih_F11x_F9b_hi"]), "07_DATA_CSV/perbandingan_utama_5_arm.csv", "kolom selisih_F11x_F9b_lo/hi", st, "Hasil 4.1")
        claim("PRIM-%s-F31" % tag, "Batas atas 95%% gerbang F31 (syarat < -0,005) (%s)" % (label), r["F31_batas_atas95"], "07_DATA_CSV/perbandingan_utama_5_arm.csv", "kolom F31_batas_atas95", st, "Hasil 4.1")
        claim("PRIM-%s-success" % tag, "Perbandingan utama lolos? (%s)" % label, r["sukses_utama"], "07_DATA_CSV/perbandingan_utama_5_arm.csv", "kolom sukses_utama", st, "Hasil 4.1")
    n_ok = sum(1 for r in rows if r["sukses_utama"])
    claim("PRIM-count", "Jumlah arm tempat perbandingan utama lolos", "%d dari %d" % (n_ok, len(rows)), "07_DATA_CSV/perbandingan_utama_5_arm.csv", "hitung kolom sukses_utama = True", "konfirmatori", "Abstrak, Hasil 4.1")
    byh = {}
    for fr in fal_rows:
        byh.setdefault(fr["hipotesis"], []).append(fr["gugur"])
    for h, v in byh.items():
        held = [x is False or x == "False" for x in v]
        txt = "bertahan di semua arm" if all(held) else ("gugur di semua arm" if not any(held) else "bervariasi (bertahan di %d dari %d arm)" % (sum(held), len(v)))
        claim("HIP-%s" % h, "Hipotesis %s %s" % (h, txt), "%d dari %d bertahan" % (sum(held), len(v)), "07_DATA_CSV/hipotesis_falsifier_5_arm.csv", "baris hipotesis=%s, kolom gugur" % h, "konfirmatori", "Hasil 4.2")


def cosine_csv():
    by = {}
    for p in sorted(glob.glob(os.path.join(RT, "scores", "gemma_homog", "*_scores.jsonl"))):
        for l in open(p, encoding="utf-8"):
            r = json.loads(l)
            c = r.get("feats", {}).get("cos") if not r.get("failed") else None
            if c is not None and not (isinstance(c, float) and math.isnan(c)):
                by.setdefault(r["type"], []).append(c)
    rows = []
    allc = [x for v in by.values() for x in v]
    for t, v in sorted(by.items()):
        m = sum(v) / len(v)
        sd = (sum((x - m) ** 2 for x in v) / len(v)) ** 0.5
        rows.append(dict(jenis_skenario=t, n=len(v), rata_rata_kosinus=round(m, 4), simpangan_baku=round(sd, 4), min=round(min(v), 4), maks=round(max(v), 4)))
    rows.append(dict(jenis_skenario="SEMUA", n=len(allc), rata_rata_kosinus=round(sum(allc) / len(allc), 4)))
    write_csv(os.path.join(PACK, "07_DATA_CSV", "kosinus_rata_rata_per_jenis_D1.csv"), rows)
    for r in rows:
        if r["jenis_skenario"] in ("SEMUA", "TWIN_H", "NOSRC_SAME", "COPY_PARA", "COPY_TWIN", "IND_DIFF"):
            claim("COS-%s" % r["jenis_skenario"], "Rata-rata kosinus A vs B, jenis %s (D1)" % r["jenis_skenario"], r["rata_rata_kosinus"], "07_DATA_CSV/kosinus_rata_rata_per_jenis_D1.csv", "baris jenis_skenario=%s" % r["jenis_skenario"], "konfirmatori", "Hasil 4.1")


def results_claims(main, per_type, transfer):
    def val(rows, arm_prefix, monitor, target, col):
        for r in rows:
            if r["arm"].startswith(arm_prefix) and r["monitor"] == monitor and r.get("target") == target:
                return r.get(col)
        return None
    for key, col in (("recall", "recall"), ("FPR", "fpr")):
        vals = []
        for lab, _ in ARMS:
            for m in ("F0b LLM report-only [tp:qwen3.8-flash]", "D LLM with sources [tp:qwen3.8-flash]"):
                v = val(main, lab, m, "A_primary", col)
                if v not in (None, ""):
                    vals.append(float(v))
        if vals:
            claim("LLM-%s-range" % key, "Rentang %s monitor LLM Qwen pada target A di lima arm (ambang terkalibrasi)" % key, "%.3f sampai %.3f" % (min(vals), max(vals)), "07_DATA_CSV/hasil_utama_semua_arm.csv", "monitor F0b/D LLM [tp:qwen3.8-flash], target A_primary, kolom %s" % col, "konfirmatori", "Hasil 4.3")
    for mode in ("full_anchored", "none", "spoofed_open", "tail_truncated", "half_mcar", "comm_hidden", "reordered"):
        m = "F10 ensemble + ledger [%s]" % mode
        for tgt in ("A_primary", "C"):
            a, rc = val(main, "D1", m, tgt, "auroc"), val(main, "D1", m, tgt, "recall")
            if a:
                claim("LOG-%s-%s" % (mode, tgt), "AUROC dan recall F10 (F9b + log), kondisi log %s, target %s (D1)" % (mode, tgt), "AUROC %s; recall %s" % (a, rc), "07_DATA_CSV/hasil_utama_semua_arm.csv", "monitor=%s, target=%s" % (m, tgt), "konfirmatori", "Hasil 4.3 / 4.5")
        h8 = val(main, "D1", "H8 tri-state [%s]" % mode, "A_primary", "recall")
        if h8 is not None:
            claim("H8-%s" % mode, "Recall aturan tiga nilai H8, kondisi log %s (D1)" % mode, h8, "07_DATA_CSV/hasil_utama_semua_arm.csv", "monitor=H8 tri-state [%s], target A_primary, kolom recall" % mode, "konfirmatori", "Hasil 4.5")
    for t in ("ADAPT_LEX_INJECT", "ADAPT_SPLIT_2", "ADAPT_SURROGATE_K3", "ADAPT_OUT_OF_BAND", "COPY_LIT", "COPY_PARA", "COPY_TWIN", "COPY_COVER", "SHARED_OK", "NOSRC_SAME"):
        for m in (F11, F9, "H3 S_disguise [claim_level]"):
            for r in per_type:
                if r["arm"].startswith("D1") and r["monitor"] == m and r["type"] == t and r["target"] == "A_primary":
                    claim("TYPE-%s-%s" % (t, m.split()[0]), "Laju penandaan %s pada %s (D1, ambang terkalibrasi)" % (m, t), r["flag_rate"], "07_DATA_CSV/hasil_per_jenis_semua_arm.csv", "arm=D1, monitor=%s, type=%s, target=A_primary, kolom flag_rate" % (m, t), "konfirmatori", "Hasil 4.4")
    ts = [r for r in transfer if r["monitor"] == F11 and r["target"] == "A_primary"]
    if ts:
        au = [float(r["auroc"]) for r in ts]
        rc = [float(r["recall"]) for r in ts]
        claim("TRANS-F11x", "Rentang AUROC dan recall F11x pada transfer dari D1 ke empat arm lain", "AUROC %.3f sampai %.3f; recall %.3f sampai %.3f" % (min(au), max(au), min(rc), max(rc)), "07_DATA_CSV/transfer_dari_D1.csv", "monitor=F11x, target=A_primary", "konfirmatori", "Hasil 4.6")


def static_claims():
    claim("T3-lex-leak", "Track 1: jumlah kebocoran kotak pasir (Qwen dan DeepSeek)", "0", "07_DATA_CSV/track1_redteam_ringkasan.csv", "kolom leaks", "konfirmatori", "Hasil 4.7")
    claim("T3-board", "Track 1 papan bersama: proporsi agen yang menemukan folder tak disebut", "0,00 (10 agen x 4 putaran per model)", "07_DATA_CSV/track1_papan_bersama_ringkasan.csv", "kolom discovered", "konfirmatori", "Hasil 4.7")
    claim("T2-noprop", "Track 2 (klaim tak relevan): propagasi di semua sel", "0; batas atas 95% 0,096", "07_DATA_CSV/track2_v2_ringkasan.csv", "kolom propagation_rate dan propagation_ci95", "konfirmatori", "Hasil 4.7")
    claim("T2-v3", "Track 2 v3 (klaim relevan): laju pengulangan maksimum per sel", "0,22 (guarded|deepseek|chain, agen 3)", "07_DATA_CSV/track2_v3_ringkasan.csv", "kolom agent3_can_verify_repeat_false_rate", "eksploratori (tidak dikunci)", "Hasil 4.7")
    claim("T3-chain", "Track 3: rantai hash saja tidak mendeteksi pemotongan ekor, penulisan ulang admin, pemalsuan sebagai agen lain", "0%; dengan jangkar 100%", "07_DATA_CSV/track3_deteksi_perusakan_log.csv", "kolom R1_chain_only, R2_chain_plus_anchor", "konfirmatori", "Hasil 4.7")
    claim("HAIKU", "Pembanding Haiku vs Qwen pada 97 butir D1: AUROC dan FPR pada ambang 0,5", "Haiku 0,81; Qwen 0,70; FPR 0,66 keduanya", "07_DATA_CSV/haiku_vs_qwen_97_butir.csv", "hitung dari kolom p_copying_haiku, p_copying_qwen, salinan_tanpa_pengungkapan", "eksploratori", "Lampiran D")
    for cid, text, val_, f, loc, st, sec in (
        ("U1-A1", "Uji 1: pengawas yang percaya klaim menangkap salinan (semua level)", "0%", "10_PRAREGISTRASI_DAN_ASAL_USUL/RINGKASAN_UJI1.md", "tabel 'salin, klaim sumber lain', kolom A1", "pilot", "Metode 3, Lampiran"),
        ("U1-A2-L4", "Uji 1: pembaca ringkasan mirip (A2) pada penyamaran berat L4", "28%", "10_PRAREGISTRASI_DAN_ASAL_USUL/RINGKASAN_UJI1.md", "baris L4, kolom A2", "pilot", "Metode 3, Lampiran"),
        ("U1-B", "Uji 1: pemeriksa artefak gabungan menangkap salinan", "99 sampai 100%; alarm palsu jujur 13%", "10_PRAREGISTRASI_DAN_ASAL_USUL/RINGKASAN_UJI1.md", "kolom B gabungan; baris jujur", "pilot", "Metode 3, Lampiran"),
        ("U2-F9b", "Uji 2 asli: F9b recall/FPR/AUROC/Brier (target A, 410 skenario uji)", "0,971 / 0,075 / 0,990 / 0,048", "10_PRAREGISTRASI_DAN_ASAL_USUL/NARRATION_BRIEF_UJI2.md", "bagian 'Headline results'", "eksploratori", "Lampiran"),
        ("U2-F0b", "Uji 2 asli: LLM hanya-laporan pada salinan parafrase", "laju penandaan 0,06", "10_PRAREGISTRASI_DAN_ASAL_USUL/NARRATION_BRIEF_UJI2.md", "bagian 'Headline results'", "eksploratori", "Lampiran"),
        ("U2-single", "Uji 2 asli: rumus tunggal pada target A", "AUROC 0,48 sampai 0,65; recall <= 0,09", "10_PRAREGISTRASI_DAN_ASAL_USUL/NARRATION_BRIEF_UJI2.md", "bagian 'Headline results'", "eksploratori", "Lampiran"),
        ("BRIER-const", "Brier acuan prevalensi konstan untuk target salinan (uji 2)", "0,250 (bukan 0,217)", "10_PRAREGISTRASI_DAN_ASAL_USUL/NARRATION_BRIEF_UJI2.md", "bagian 'Headline results'", "eksploratori", "Lampiran")):
        claim(cid, text, val_, f, loc, st, sec)


def sources_catalog():
    rows = []
    src = os.path.join(ROOT, "01_SOURCE_AUDIT", "RELATED_WORK_COMPARISON.csv")
    where = {"R1": "Related Work 2; Kebaruan N", "R2": "Related Work 2; catatan monitor tak tepercaya", "R3": "Related Work 2", "R4": "Related Work 2", "R5": "Related Work 2; Track 2", "R6": "Related Work 2 (periferal)", "R7": "Related Work 2 (kerangka konsep)", "R8": "Related Work 2; motivasi Track 3", "R9": "Related Work 2 (metode berbeda)"}
    for r in csv.DictReader(open(src, encoding="utf-8")):
        rid = r["ref_id"]
        full = r["reference"]
        no_cmp = "JANGAN membandingkan angka AUROC dengan sumber ini. " if r["comparable_numbers"].strip().upper() == "NO" else ""
        rows.append(dict(ref_id=rid, referensi_lengkap=full, url=r["verified_from"], track_apart=r["track"], status_verifikasi=r["verification_status"],
                         pertanyaan_penelitian_sumber=r["research_question"], desain_sumber=r["design_and_baseline"],
                         hasil_yang_dilaporkan_sumber=r["metrics_and_results_reported"],
                         boleh_dikutip_untuk="Hanya isi yang tertulis di kolom pertanyaan, desain, dan hasil (tingkat abstrak atau halaman yang dibaca).",
                         jangan_diklaim=(no_cmp + (r["limitations_stated_or_visible"] or "")).strip(), dipakai_di_bagian=where.get(rid, "Related Work"),
                         perbedaan_dengan_penelitian_ini=r["how_ours_differs_or_builds_on"], catatan=r["comparison_note"]))
    extra = [
        ("X1", "Tennenholtz (2004). Program Equilibrium.", "", "3", "BLOCKED (ScienceDirect 403)", "JANGAN DIKUTIP: tidak pernah dibaca."),
        ("X2", "OpenAI disclosure tentang insiden OpenAI / Hugging Face", "", "tools", "BLOCKED (HTTP 403)", "JANGAN DIKUTIP: tidak pernah dibaca; gunakan laporan METR dan Redwood yang terbaca."),
        ("X3", "Broder (1997) dan Dong dkk. (kemiripan dokumen)", "", "-", "NOT VERIFIED", "JANGAN DIKUTIP sebelum diverifikasi."),
        ("X4", "Brier (1950) dan Platt (1999) (penanda dagger di draf lama)", "", "-", "NOT VERIFIED", "JANGAN DIKUTIP sebelum diverifikasi; skor Brier dan kalibrasi dijelaskan tanpa sitasi bila belum diverifikasi."),
        ("X5", "Model embedding embeddinggemma-2:740m (tag Ollama)", "", "-", "TAG LOKAL; mungkin berbeda dari arXiv:2509.20354", "Sebut hanya tag model yang dipakai; jangan menautkan ke arXiv tanpa verifikasi."),
        ("X6", "Teks tautan panitia yang tidak sama dengan judul asli (Gandhi, Agrawal, Tilli, Jorgensen, Riedl, Jones)", "", "-", "LIHAT 05b_STATUS_SEMUA_REFERENSI_APART.md", "Kutip judul asli, bukan teks tautan panitia."),
    ]
    for rid, full, url, tr, status, note in extra:
        rows.append(dict(ref_id=rid, referensi_lengkap=full, url=url, track_apart=tr, status_verifikasi=status, jangan_diklaim=note, dipakai_di_bagian="-"))
    write_csv(os.path.join(PACK, "05_KATALOG_SUMBER.csv"), rows)


def figures():
    out = mk("08_FIGUR")
    figs = ["fig0c_arch3d_color_en.png", "fig0c_arch3d_color_id.png", "fig0c_arch3d_color_en.svg", "fig0c_arch3d_color_id.svg", "fig0a_architecture_en.png", "fig0a_architecture_id.png",
            "fig0b_topologies_en.png", "fig0b_topologies_id.png", "fig1_auroc_by_arm.png", "fig2_flag_rates_by_type.png", "fig3_log_degradation.png", "fig4_falsifier_scoreboard.png",
            "fig5_tracks.png", "fig6_scatter3d_view1.png", "fig6_scatter3d_view2.png", "fig6_scatter2d_cosine_vs_esup.png", "fig6_scatter3d.html"]
    notes = []
    for f in figs:
        s = os.path.join(RES, "figures", f)
        d = os.path.join(out, f)
        if f.endswith(".png"):
            im = Image.open(s).convert("RGB")
            if im.width > 1500:
                im = im.resize((1500, int(im.height * 1500 / im.width)), Image.LANCZOS)
            im.save(d, optimize=True)
        else:
            shutil.copy(s, d)
    cap = {"fig0c_arch3d_color_en": "Arsitektur bed uji (Metode)", "fig0a_architecture_en": "Arsitektur bed uji, versi datar", "fig0b_topologies_en": "Lima topologi komunikasi uji propagasi (Metode atau Lampiran)",
           "fig1_auroc_by_arm": "AUROC per arm dengan interval bootstrap klaster (Hasil)", "fig2_flag_rates_by_type": "Laju penandaan per jenis skenario (Lampiran)", "fig3_log_degradation": "Degradasi log: recall dan FPR (Lampiran)",
           "fig4_falsifier_scoreboard": "Papan skor falsifier (Hasil atau Lampiran)", "fig5_tracks": "Track 1, 2, 3 (Lampiran)", "fig6_scatter3d_view1": "Data nyata D1 pada tiga sumbu (Hasil)",
           "fig6_scatter2d_cosine_vs_esup": "Pendamping 2D kosinus vs E_sup (Hasil)", "fig6_scatter3d": "Versi interaktif (HTML)"}
    kc = mk("08_FIGUR", "konsep_chatbot")
    for f in ("Code_Generated_Image.png", "fig_arch_bw 3d.svg"):
        src_f = os.path.join(RT, "chatbot_figures", "argon", f)
        if os.path.isfile(src_f):
            shutil.copy(src_f, os.path.join(kc, f.replace(" ", "_")))
    with open(os.path.join(out, "DAFTAR_FIGUR.md"), "w", encoding="utf-8") as fh:
        fh.write("# Daftar figur\n\nSemua PNG diperkecil ke lebar 1500 piksel. Versi `_id` berbahasa Indonesia, `_en` berbahasa Inggris. SVG dapat disunting teksnya.\n\n| berkas | fungsi |\n|---|---|\n")
        for k, v in cap.items():
            fh.write("| %s | %s |\n" % (k, v))
        fh.write("\nCatatan caption: sebut data (D1, n), status (konfirmatori), dan arti sumbu. Sel kosong pada H1 untuk NOSRC_SAME di `fig2` berarti abstain (tidak ada sumber).\n")


def copy_static():
    s = os.path.join(RT, "report", "gpt_static")
    for f in os.listdir(s):
        shutil.copy(os.path.join(s, f), os.path.join(PACK, f))
    shutil.copy(os.path.join(ROOT, "01_SOURCE_AUDIT", "ALL_APART_REFERENCES_STATUS.md"), os.path.join(PACK, "05b_STATUS_SEMUA_REFERENSI_APART.md"))
    d = mk("09_LAPORAN_JADI")
    for f in ("REPORT_EN.md", "REPORT_ID.md", "SUBMISSION_EN.md"):
        t = open(os.path.join(RT, "report", f), encoding="utf-8").read().replace("../results/figures/", "../08_FIGUR/")
        open(os.path.join(d, f), "w", encoding="utf-8").write(t)
    d = mk("10_PRAREGISTRASI_DAN_ASAL_USUL")
    pre = os.path.join(RT, "prereg")
    for f in ("DEVIATIONS.md", "RETEST_DECLARATIONS.md", "RETEST_DECLARATIONS_STAGE2.md", "HYPOTHESES.json", "preregistered_test_plan.md"):
        shutil.copy(os.path.join(pre, f), os.path.join(d, f))
    for f in ("PREEXISTING_WORK.md", "SPRINT_CONTRIBUTIONS.md"):
        shutil.copy(os.path.join(ROOT, "00_README_AND_MANIFEST", f), os.path.join(d, f))
    shutil.copy(os.path.join(ROOT, "00_README_AND_MANIFEST", "NARRATION_BRIEF_FOR_GPT.md"), os.path.join(d, "NARRATION_BRIEF_UJI2.md"))
    shutil.copy(os.path.join(ROOT, "07_STATISTICAL_ANALYSIS", "TABLES.md"), os.path.join(d, "TABLES_UJI2.md"))
    shutil.copy(os.path.join(ROOT, "prior_experiment_swarm_provenance", "hasil", "RINGKASAN.md"), os.path.join(d, "RINGKASAN_UJI1.md"))
    d = mk("11_ANALISIS_CELAH_AI")
    for f in ("argon_gap_analysis.md", "interdisciplinary_map.md", "review_of_lenses.md", "candidate_formulas.py"):
        shutil.copy(os.path.join(pre, f), os.path.join(d, f))
    with open(os.path.join(d, "BACA.md"), "w", encoding="utf-8") as fh:
        fh.write("# Analisis celah berbantuan AI\n\nBerkas ini adalah keluaran asisten AI (dalam proyek disebut Argon) yang melahirkan hipotesis H1 sampai H10 dan kode rumus kandidat. Di laporan sebut sebagai 'analisis celah berbantuan AI'. Peneliti yang menetapkan komposisi F11x, syarat gugur yang dikunci, dan protokol. Jangan menyebut Argon sebagai nama rumus.\n")


def narrative():
    tpl = os.path.join(RT, "report", "GPT_NARASI.tpl.md")
    out = os.path.join(PACK, "02_NARASI_LENGKAP_UJI_1_2_3.md")
    subprocess.run([sys.executable, os.path.join(HERE, "build_reports.py"), tpl, out], check=True, env=dict(os.environ, PYTHONUTF8="1"))
    t = open(out, encoding="utf-8").read()
    for a, b in (("10_PRAREGISTRASI/NARATION_BRIEF_UJI2.md", "10_PRAREGISTRASI_DAN_ASAL_USUL/NARRATION_BRIEF_UJI2.md"), ("10_PRAREGISTRASI/TABLES_UJI2.md", "10_PRAREGISTRASI_DAN_ASAL_USUL/TABLES_UJI2.md"),
                 ("10_PRAREGISTRASI/", "10_PRAREGISTRASI_DAN_ASAL_USUL/"), ("interval Wilson di `RINGKASAN.md`", "interval Wilson di `10_PRAREGISTRASI_DAN_ASAL_USUL/RINGKASAN_UJI1.md`")):
        t = t.replace(a, b)
    open(out, "w", encoding="utf-8").write(t)


def haiku_csv():
    base = os.path.join(RT, "haiku_monitor")
    key = {json.loads(l)["id"]: json.loads(l) for l in open(os.path.join(base, "key", "key.jsonl"), encoding="utf-8")}
    ver = {json.loads(l)["id"]: json.loads(l) for l in open(os.path.join(base, "blind", "verdicts.jsonl"), encoding="utf-8")}
    sc = {}
    for l in open(os.path.join(RT, "scores", "gemma_homog", "rep0_gemma_homog_scores.jsonl"), encoding="utf-8"):
        r = json.loads(l)
        if not r.get("failed"):
            sc[r["scenario_id"]] = r
    rows = []
    for i, k in key.items():
        r = sc.get(k["scenario_id"])
        q = r["llm"]["tp:qwen3.8-flash"]["report_only"].get("p_copying") if r else None
        rows.append(dict(id=i, scenario_id=k["scenario_id"], jenis=k["type"], salinan_tanpa_pengungkapan=k["copy_u"], p_copying_haiku=ver[i]["p_copying"], p_copying_qwen=q))
    write_csv(os.path.join(PACK, "07_DATA_CSV", "haiku_vs_qwen_97_butir.csv"), rows)


def main():
    if os.path.isdir(PACK):
        shutil.rmtree(PACK)
    mk("07_DATA_CSV")
    copy_static()
    main_rows = stack_csv("results_main.csv", "hasil_utama_semua_arm.csv")
    pt_rows = stack_csv("results_per_type.csv", "hasil_per_jenis_semua_arm.csv")
    tr_rows = []
    for label, tag in ARMS[1:]:
        p = os.path.join(RES, tag, "transfer_from_gemma_homog.csv")
        tr_rows += [{"arm": label, **{k: v for k, v in r.items() if k != "arm"}} for r in csv.DictReader(open(p, encoding="utf-8"))]
    write_csv(os.path.join(PACK, "07_DATA_CSV", "transfer_dari_D1.csv"), tr_rows)
    audit = []
    for label, tag in ARMS + [("D0", "D0_exploratory_contaminated")]:
        a = jl(tag, "audit.json")
        r = {"arm": label}
        flatten([], {k: v for k, v in a.items() if k != "conditions_scored"}, r)
        audit.append(r)
    write_csv(os.path.join(PACK, "07_DATA_CSV", "audit_semua_arm.csv"), audit)
    shutil.copy(os.path.join(RT, "chatbot_figures", "d1_test_features.csv"), os.path.join(PACK, "07_DATA_CSV", "d1_test_features_untuk_scatter.csv"))
    shutil.copy(os.path.join(ROOT, "01_SOURCE_AUDIT", "RELATED_WORK_COMPARISON.csv"), os.path.join(PACK, "07_DATA_CSV", "perbandingan_karya_terkait_asli.csv"))
    kal = os.path.join(RES, "gemma_homog", "kalibrasi_keyakinan_qwen_D1.csv")
    if os.path.isfile(kal):
        shutil.copy(kal, os.path.join(PACK, "07_DATA_CSV", "kalibrasi_keyakinan_qwen_D1.csv"))
        for line in csv.reader(open(kal, encoding="utf-8")):
            if len(line) == 2 and line[0] in ("brier", "porsi_sangat_yakin_(<=0.1_atau_>=0.9)", "porsi_ragu_(0.3-0.7)", "sangat_yakin_tapi_salah", "sangat_yakin_total"):
                claim("KEYAKINAN-%s" % line[0], "Keyakinan monitor LLM Qwen (D1, hanya-laporan, 1.220 penilaian): %s" % line[0], line[1], "07_DATA_CSV/kalibrasi_keyakinan_qwen_D1.csv", "baris ukuran=%s" % line[0], "konfirmatori (monitor, bukan agen penulis)", "Hasil 4.3 / tambahan")
    k3 = os.path.join(RES, "gemma_homog", "perbandingan_tiga_model_keyakinan.csv")
    if os.path.isfile(k3):
        shutil.copy(k3, os.path.join(PACK, "07_DATA_CSV", "perbandingan_tiga_model_keyakinan.csv"))
        for r3 in csv.DictReader(open(k3, encoding="utf-8")):
            m3 = r3.get("model")
            if m3 in ("Haiku", "Gemma", "Qwen"):
                claim("KEYAKINAN3-%s-brier" % m3, "Brier %s pada 97 butir yang sama (monitor LLM, hanya-laporan, D1 rep0 uji)" % m3, r3["brier"], "07_DATA_CSV/perbandingan_tiga_model_keyakinan.csv", "baris model=%s, kolom brier" % m3, "eksploratori (n=97, satu replikasi)", "Lampiran D / video")
                claim("KEYAKINAN3-%s-ragu" % m3, "Porsi jawaban ragu-ragu (0,3 sampai 0,7) %s pada 97 butir" % m3, r3["porsi_ragu_0.3_0.7"], "07_DATA_CSV/perbandingan_tiga_model_keyakinan.csv", "baris model=%s, kolom porsi_ragu_0.3_0.7" % m3, "eksploratori (n=97, satu replikasi)", "Lampiran D / video")
                claim("KEYAKINAN3-%s-high" % m3, "Keyakinan rata-rata dan kenyataan salinan saat >= 0,8, %s" % m3, "%s lawan %s (n=%s)" % (r3["keyakinan_rata2_saat_>=0.8"], r3["kenyataan_salinan_saat_>=0.8"], r3["n_saat_>=0.8"]), "07_DATA_CSV/perbandingan_tiga_model_keyakinan.csv", "baris model=%s" % m3, "eksploratori (n=97, satu replikasi)", "Lampiran D / video")
    primary_tables()
    tracks_csv()
    cosine_csv()
    haiku_csv()
    results_claims(main_rows, pt_rows, tr_rows)
    static_claims()
    write_csv(os.path.join(PACK, "06_KLAIM_KE_BUKTI.csv"), CLAIMS)
    sources_catalog()
    figures()
    narrative()
    # manifest with hashes
    lines = []
    for dp, dn, fn in os.walk(PACK):
        for f in sorted(fn):
            p = os.path.join(dp, f)
            lines.append("%s  %s  %d" % (hashlib.sha256(open(p, "rb").read()).hexdigest(), os.path.relpath(p, PACK).replace(chr(92), "/"), os.path.getsize(p)))
    open(os.path.join(PACK, "DAFTAR_BERKAS_DAN_HASH.txt"), "w", encoding="utf-8").write("\n".join(sorted(lines)) + "\n")
    if os.path.exists(ZIP):
        os.remove(ZIP)
    with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for dp, dn, fn in os.walk(PACK):
            for f in fn:
                p = os.path.join(dp, f)
                z.write(p, os.path.join("BAHAN_GPT_SWARM", os.path.relpath(p, PACK)))
    print("pack files", len(lines), "zip MB %.2f" % (os.path.getsize(ZIP) / 1e6), "claims", len(CLAIMS))


if __name__ == "__main__":
    main()
