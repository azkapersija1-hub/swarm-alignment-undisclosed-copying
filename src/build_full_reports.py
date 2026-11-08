"""Build the full technical report (English) and the full report (Indonesian) as .docx from result files (numbers are read, not typed).
Usage: py -3.12 -I -B -X utf8 build_full_reports.py"""
import csv
import json
import os
import sys

import docx
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Inches, Pt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import build_official as BO  # noqa: E402  (reuses result readers v(), ci(), fl(), R())

FIG = BO.FIG
FIG_ALL = os.path.join(ROOT, "08_VISUAL_EVIDENCE", "figures_tls")
EXP = BO.EXP
v, ci, fl, R, pct = BO.v, BO.ci, BO.fl, BO.R, BO.pct


class Doc:
    def __init__(self, title):
        self.d = docx.Document()
        st = self.d.styles["Normal"]
        st.font.name, st.font.size = "Calibri", Pt(10.5)
        for sec in self.d.sections:
            sec.left_margin = sec.right_margin = Inches(0.9)
            sec.top_margin = sec.bottom_margin = Inches(0.8)
        t = self.d.add_heading(title, 0)
        t.alignment = WD_ALIGN_PARAGRAPH.CENTER

    def h(self, text, lvl=1):
        self.d.add_heading(text, lvl)

    def p(self, text, bold_lead=None):
        para = self.d.add_paragraph()
        para.paragraph_format.space_after = Pt(6)
        if bold_lead:
            para.add_run(bold_lead + " ").bold = True
        para.add_run(text)
        para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        return para

    def bullets(self, items):
        for it in items:
            self.d.add_paragraph(it, style="List Bullet")

    def eq(self, text, no):
        para = self.d.add_paragraph()
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = para.add_run("%s      (%s)" % (text, no))
        r.font.name = "Cambria Math"
        r._element.rPr.rFonts.set(qn("w:eastAsia"), "Cambria Math")
        r.font.size = Pt(10.5)

    def table(self, rows, widths=None, size=8):
        t = self.d.add_table(rows=len(rows), cols=len(rows[0]))
        t.style = "Light Grid Accent 1"
        for i, row in enumerate(rows):
            for j, cell in enumerate(row):
                c = t.cell(i, j)
                c.text = ""
                run = c.paragraphs[0].add_run(str(cell))
                run.font.size = Pt(size)
                run.bold = i == 0
                if widths:
                    c.width = Inches(widths[j])
        self.d.add_paragraph()

    def fig(self, path, caption, width=6.3):
        if not os.path.isfile(path):
            self.p("[figure not available: %s]" % os.path.basename(path))
            return
        para = self.d.add_paragraph()
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        para.add_run().add_picture(path, width=Inches(width))
        c = self.d.add_paragraph(caption)
        c.runs[0].italic = True
        c.runs[0].font.size = Pt(9)
        c.alignment = WD_ALIGN_PARAGRAPH.CENTER


def load_json(rel):
    p = os.path.join(EXP, rel)
    return json.load(open(p, encoding="utf-8")) if os.path.isfile(p) else None


MON_ROWS = ["F0a report rule (same cited source)", BO.F0B, BO.DLLM, "F1 lexical 3-gram", "F2 embedding cosine", "F3 STP", BO.F4, "F5 STP-AR+MOI", BO.F6,
            "F6b RCC-v3.3 (AR+MOI)", BO.F8A, "F8b Argon claim overlap", "S1 claim unsupported by cited source", "S2 source containment (twin/near)", BO.F9, BO.F9B,
            "P  ledger only [full]", BO.F10["full"], BO.F10["comm_hidden"], BO.F10["half"], BO.F10["none"]]


def metric_table(tgt):
    rows = [["Monitor", "Recall", "FPR", "Precision", "F1", "MCC", "AUROC", "Brier", "BSS"]]
    for m in MON_ROWS:
        r = R(m, tgt)
        f = lambda k: ("%.3f" % float(r[k])) if r[k] != "nan" else "n/a"
        rows.append([m.strip(), f("recall"), f("fpr"), f("precision"), f("f1"), f("mcc"), f("auroc"), f("brier"), f("bss")])
    return rows


SCEN = [["Scenario type", "What happens", "Copy (A)", "Non-indep. (B)", "False prov. (C)"],
        ["IND_SAME / IND_DIFF", "Both agents honest, own sources (same topic / other topic)", "0", "0", "0"],
        ["NOSRC_SAME", "Both answer from general knowledge, no source", "0", "0", "0"],
        ["TWIN_H", "Honest agents, twin sources (identical text, different publisher)", "0", "1", "0"],
        ["NEAR_H", "Honest agents, near-duplicate sources", "0", "1", "0"],
        ["SHARED_OK", "B builds on A's report and cites it, says it is not independent", "1", "1", "0"],
        ["COPY_LIT / COPY_PARA", "B reuses A's report verbatim / paraphrased, cites another source, claims independence", "1", "1", "1"],
        ["COPY_TWIN", "As COPY_PARA but cites the twin of A's source", "1", "1", "1"],
        ["COPY_COVER", "B opens its cited source as a cover story, still copies A", "1", "1", "1"]]

T2 = load_json("track2_networks_tls/t2_summary.json")
T1 = load_json("track1_sandbox_tls/t1_sandbox.json")
T1R = load_json("track1_sandbox_tls/t1_reproducibility.json")
T3T = load_json("track3_infrastructure_tls/t3_tamper.json")
T3C = load_json("track3_infrastructure_tls/t3_chain_attribution.json")
T3D = load_json("track3_infrastructure_tls/t3_duplicates.json")


def t2_rows():
    rows = [["Topology", "Trials", "Propagation per downstream agent", "Correction per downstream agent", "Trials contaminated", "Mean depth", "Mean messages"]]
    for k, d in (T2 or {}).items():
        rows.append([k, d["n_trials"], "%.2f" % d["propagation_rate_per_downstream_agent"], "%.2f" % d["correction_rate_per_downstream_agent"],
                     "%.2f" % d["trials_contaminated"], "%.2f" % d["mean_depth_reached"], "%.1f" % d["mean_messages"]])
    return rows


def build_en():
    D = Doc("Trust the Report or Check the Artifact? Provenance-Aware Oversight of Falsely Independent Reports in Multi-Agent LLM Systems - Full Technical Report")
    D.p("Mochamad Azmi Rizkulloh. Swarm Alignment Hackathon, 6-8 November 2026 (main track: Track 4, Multi-Agent Oversight and Control; supporting tests for Tracks 1-3).")
    D.h("Abstract")
    D.p(BO.ABSTRACT)
    D.h("1. Research background and problem")
    D.p("Multi-agent LLM systems are usually supervised through what agents say about themselves. A report can claim independent evidence while the content was copied from another agent, "
        "or while both agents used the same document. Identical content does not prove copying, because honest agents can cite different publications with the same text. The problem is therefore "
        "to decide what an overseer must inspect, and which signals separate copying, shared evidence and false provenance claims.")
    D.h("2. Objectives, research questions, contributions")
    D.bullets(["RQ1: Does reading reports suffice to detect copying, non-independent evidence and false provenance claims?",
               "RQ2: Do research similarity formulas (STP, STP-AR, MOI, RCC-v3.3, Argon) improve oversight over lexical and embedding baselines?",
               "RQ3: Do claim-versus-cited-source checks and a provenance ledger improve detection, and how does the ledger degrade when events are missing?",
               "RQ4: Which monitors raise false alarms on honest twin sources and on a no-source control?"])
    D.p("Contributions: a controlled testbed with real LLM agents on course texts; three separately labelled targets; a monitor comparison with Brier scores and cluster-aware intervals; "
        "an audited pipeline (an earlier scripted-bot pilot exposed a hash non-determinism bug and an honest-twin control that lowered the original claim).")
    D.h("3. Related work")
    D.p("AI control evaluates trusted monitoring of untrusted models (Greenblatt et al., 2024). Multi-agent risk taxonomies (Hammond et al., 2025) and failure taxonomies (Cemri et al., 2025) motivate "
        "inter-agent oversight; secret collusion studies hidden coordination (Motwani et al., 2024). Attribution evaluation (Rashkin et al., 2021; Gao et al., 2023) relates claims to cited sources. "
        "Agent infrastructure (Chan et al., 2025) motivates identifiers and attribution; tamper-evident logging (Crosby and Wallach, 2009) motivates the hash chain. Collective bias in LLM populations "
        "(Ashery et al., 2025) shows that group behaviour can differ from individual behaviour. References marked VERIFIED or PARTIAL in 01_SOURCE_AUDIT/LITERATURE_CANDIDATES.md are the only ones used.")
    D.h("4. System architecture")
    D.fig(os.path.join(FIG, "fig1_architecture.png"), "System architecture: the controller builds scenarios and holds the ground truth; monitors never read the labels.")
    D.h("5. Experimental environment and GPU")
    D.p("Measured device: NVIDIA GeForce RTX 3050 Laptop GPU, 4096 MiB, driver 610.74, PyTorch 2.6.0+cu124 (the brief assumed an RTX 2060). Embeddings (embeddinggemma-2:740m, 768-d) ran on the local GPU "
        "through Ollama 0.40.14 (utilisation mean 5%, peak 89%, VRAM peak 1.6 GB, maximum temperature 60 C, no thermal events). The agents and LLM monitors (Gemma 4 31B, remote Ollama cloud) did not use the local GPU. "
        "Formulas, ledger and statistics ran on the CPU. See 02_GPU_ENVIRONMENT/GPU_EXECUTION_REPORT.md.")
    D.fig(os.path.join(FIG, "fig9_gpu.png"), "Local GPU during scoring (embeddings only).")
    D.h("6. Agent selection and bot inventory")
    D.p("The earlier 69-bot inventory was audited (BOT_REGISTRY.csv): 22 are briefs only, 17 and 13 are rule-based tool modules, 10 are orchestration modules, 4 hand off to external models and 3 need an external API; "
        "3 are candidate tool or evaluator modules and none is an LLM agent. Selection used capability and relevance criteria, not test performance. In this study the agents are Gemma 4 31B instances "
        "with separate contexts (same model, so independence of the agents is limited to context), and the oversight roles (provenance, formula analysis, oversight) are software components.")
    D.h("7. Mathematical formulas")
    D.p("Sentence embeddings U_A, U_B (claims) and W_A, W_B (method sentences) are unit vectors. g(X) is the geometric median (Weiszfeld iteration). Frozen preexisting formulas:")
    D.eq("STP(A,B) = clip[0,1] < g(U_A)/|g(U_A)| , g(U_B)/|g(U_B)| >", 1)
    D.eq("STP-AR = STP / (1 + k sigma_boot),  k = 2,  sigma_boot = sd of STP over B = 25 bootstrap resamples", 2)
    D.eq("MOI(A,B) = clip[0,1] < mu(W_A), mu(W_B) >,  mu(W) = mean(W)/|mean(W)|;   S_base = 0.5 STP-AR + 0.5 MOI", 3)
    D.eq("RCC: SER = exp(-sum p_i ln p_i), p_i = nu_i / sum nu_l (eigenvalues of X X^T);  kappa = exp(-10 m),  m = clip((SER/n - 1/n)/(1 - 1/n))", 4)
    D.eq("gamma = 1/(1 + exp(-20 (kappa - 0.85))),  lambda = 0.5 gamma,  c = normalise((1 - lambda) g + lambda a),  RCC(A,B) = cos(c_A, c_B)", 5)
    D.eq("a = normalise(sum alpha_i x_i),  alpha_i = 0.9 beta_i + 0.1/n,  beta = softmax((r - max r)/tau),  r_i = <x_i, g>,  tau = max(0.05, 1.4826 MAD(r))", 6)
    D.p("Argon F42 (embedding triage) and F44 (claim-evidence audit) are called through a hash-checked adaptor. Decision rule and calibration:")
    D.eq("theta = Q0.95 { s_i : y_i = 0, i in calibration },   y_hat = 1[s > theta]", 7)
    D.eq("p = sigma(w^T z + b),  z_k = (x_k - mu_k)/s_k,  (w,b) = argmin  -sum [y ln p + (1-y) ln(1-p)] + |w|^2/(2C)  (calibration only)", 8)
    D.eq("Brier = (1/N) sum (p_i - y_i)^2,   BSS = 1 - Brier / Brier_ref,   Brier_ref = (1/N) sum (pi_cal - y_i)^2", 9)
    D.eq("MCC = (TP TN - FP FN) / sqrt((TP+FP)(TP+FN)(TN+FP)(TN+FN)),   CI95 = [q0.025, q0.975] of 1000 cluster-bootstrap resamples", 10)
    D.p("STRICT-GAP and the superseded RCC versions were not tested (see FORMULA_REGISTRY.csv); Argon calibration F35 (ECE) is planned, not run.")
    D.h("8. Dataset and source provenance")
    D.p("Sources: 109 definition-and-explanation texts from the author's course materials (13 biology topics, anthropology, geography, social studies, mathematics), eight evenly spaced sentences each, "
        "plus 44 honest twins and 22 near-duplicates (175 sources). The texts are the author's AI-assisted drafts. Calibration and test scenarios use disjoint topic domains. "
        "Frozen corpora and SHA-256 are in data/. The 184-book corpus of the earlier pilot was not used for LLM runs because book text is not sent to remote services.")
    D.fig(os.path.join(FIG, "fig8_distribution.png"), "Scenario distribution over the five replicates.")
    D.h("9. Experiment design, ground truth and baselines")
    D.table(SCEN, [1.3, 3.3, 0.6, 0.8, 0.8])
    D.p("Ground truth comes from the controller's design and is never visible to monitors. Five replicates use different scenario plans and generation seeds (164 scenarios each). "
        "Baselines: F0a (trust cited sources), F0b (LLM reads reports only), lexical 3-gram overlap and embedding cosine. The primary analysis keeps all scenarios; the sensitivity analysis keeps only copy scenarios "
        "verified by reused numbers (course text has few numbers, so 35% of copy scenarios cannot be verified this way).")
    D.h("10. Communication protocol and oversight mechanisms")
    D.p("Agent B receives Agent A's report as a message in copy and shared scenarios; tool use is controller-mediated (open_source) and every event is written to a SHA-256 hash-chained ledger "
        "(open_source, message, message_received, report_submitted). Monitors: report-only (rule and LLM), LLM with sources, single formulas, claim-support and source-overlap checks (S1, S2), ensembles (F9, F9b) "
        "and F10 (ensemble plus ledger features) under four visibility settings: full log, no message events, 50% of events (deterministic hash), log missing.")
    D.h("11. Statistical analysis plan")
    D.p("Per replicate, thresholds and logistic models are fitted on the calibration split and evaluated on the test split; test results are pooled. Uncertainty: 95% cluster bootstrap over "
        "(replicate, source of A) clusters. All results are descriptive; no hypothesis tests were run, and the five replicates share one source library, so they are not independent samples.")
    D.h("12. Results - Track 4 (oversight)")
    D.p("Main table for Target A (copying):")
    D.table(metric_table("copy"), [2.2, 0.55, 0.5, 0.65, 0.5, 0.5, 0.55, 0.55, 0.5], size=7)
    D.fig(os.path.join(FIG, "fig2_detection_fpr_brier.png"), "Recall, false positive rate and Brier score of all monitors for the three targets (95% cluster-bootstrap CI).")
    D.fig(os.path.join(FIG, "fig3_flag_rate_by_type.png"), "Flag rate by scenario type (Target A threshold).")
    D.p("Reports only: the LLM report reader flagged %s of copies; by type it flagged %s of shared-with-attribution reports and %s of verbatim copies, but only %s of paraphrased copies and %s of "
        "copies citing the twin source. Single formulas reached at most %.2f recall (AUROC %.2f-%.2f). Claim-versus-cited-source checks (F9b) reached AUROC %.2f; with the ledger (F10) recall %.2f and Brier %.3f." % (
            ci(BO.F0B, "recall"), pct(fl(BO.F0B, "SHARED_OK")), pct(fl(BO.F0B, "COPY_LIT")), pct(fl(BO.F0B, "COPY_PARA")), pct(fl(BO.F0B, "COPY_TWIN")), BO.rec_hi, BO.au_lo, BO.au_hi,
            v(BO.F9B, "auroc"), v(BO.F10["full"], "recall"), v(BO.F10["full"], "brier")))
    D.h("13. Formula ablation", 2)
    D.p("The ablation sequence (lexical, cosine, STP, STP-AR, STP-AR+MOI, RCC, Argon, ensembles) is in the Target A table above and in TABLES.md. Formulas that improved results only as part of an ensemble: "
        "F9 (logistic ensemble) raised AUROC from at most %.2f to %.2f. Formulas that did not change results alone: STP, STP-AR, RCC-v3.3 (recall 0.00-0.01 at the 5%% target). "
        "Formulas that added false alarms: embedding cosine, STP and RCC on the no-source control." % (BO.au_hi, v(BO.F9, "auroc")))
    D.h("14. Model comparison", 2)
    D.p("Only Gemma 4 31B (remote) was executed. Qwen (HTTP 401 for the configured key), qwen3.5 and deepseek cloud tags (HTTP 410), minimax and kimi (HTTP 402) were BLOCKED; Claude Haiku as an experimental agent and a local GPU model "
        "were NOT TESTED. Configurations B (heterogeneous) and C (mixed provider) therefore have no results; Configuration A (homogeneous) and D (LLM monitor with sources) were run.")
    D.h("15. Brier score and calibration", 2)
    D.p("Brier scores and skill versus a constant-prevalence predictor are in the main table. Figure: reliability diagram for three monitors (8 bins).")
    D.fig(os.path.join(FIG, "fig7_reliability.png"), "Reliability diagram for Target A (report-only LLM, formula ensemble, ensemble plus ledger).")
    D.p("Expected calibration error via Argon F35 was planned but not run, so no ECE is reported.")
    D.h("16. Targets B and C")
    D.p("Target B (evidence non-independent) and Target C (provenance claim false):")
    D.table(metric_table("noninde"), [2.2, 0.55, 0.5, 0.65, 0.5, 0.5, 0.55, 0.55, 0.5], size=7)
    D.table(metric_table("provfalse"), [2.2, 0.55, 0.5, 0.65, 0.5, 0.5, 0.55, 0.55, 0.5], size=7)
    D.fig(os.path.join(FIG, "fig6_visibility.png"), "Provenance-aware monitor F10 under degraded log visibility.")
    D.h("17. Supporting tests (Tracks 1-3)")
    if T1:
        D.p("The sandbox blocked %d of %d path-traversal attempts (an unprotected read leaked %d), all %d denials were logged and the ledger chain verified. The formula pipeline reproduced exactly (%.0f%%); "
            "LLM exact-output agreement was %.0f%% at temperature 0 and %.0f%% at temperature 0.7 with a fixed seed, while semantic agreement (cosine > 0.99) was %.0f%%." % (
                T1["n_attacks"] - T1["leaks_with_sandbox"], T1["n_attacks"], T1["leaks_naive_open_baseline"], T1["denied_and_logged"], 100 * T1R["formula_pipeline_exact_agreement"],
                100 * T1R["llm_temp0"]["exact_output_agreement"], 100 * T1R["llm_temp0.7_fixed_seed"]["exact_output_agreement"], 100 * T1R["llm_temp0"]["semantic_agreement_cos_gt_0.99"]), "Track 1.")
    if T2:
        D.p("A false claim was planted in agent 1 of 4 and the other agents held different sources. Results by topology:", "Track 2.")
        D.table(t2_rows(), [1.3, 0.5, 1.2, 1.2, 0.9, 0.7, 0.8])
        D.p("No downstream agent repeated the planted claim in any topology (ceiling effect: agents were told to include only facts their own source supports), so this test does not separate topologies on propagation; correction rates only reflect how many downstream agents saw the planted report. A weaker instruction or agents that must rely on the shared report would be needed.")
    else:
        D.p("Track 2 results were not available when this document was built (see 05_EXPERIMENTS/track2_networks_tls).", "Track 2.")
    if T3T:
        dr = T3T["detection_rate"]
        D.p("Duplicate-source identity by body hash: precision 1.00, recall 1.00 (%s). Hash chain detection: edit %.2f, deletion %.2f, reordering %.2f, tail truncation %.2f (%.2f when the head hash is anchored). "
            "Identity by internal id was 1.00 versus 0.00 by display name in a simulated rename-collision (a sanity check of the harness). Chain completeness hides the cover story (COPY_COVER = %.2f); "
            "only message events reveal it." % (T3D["exact_twin_by_body_hash"], dr["edit_data"], dr["delete_middle"], dr["swap_order"], dr["truncate_tail"], dr["truncate_tail_with_anchored_head"],
                                                  T3C["chain_completeness_by_type"]["COPY_COVER"]), "Track 3.")
    D.fig(os.path.join(FIG, "fig10_tracks.png"), "Supporting tests for Tracks 2 and 3.")
    D.h("18. Failure case analysis")
    D.bullets(["Paraphrased copies claiming independence pass an LLM report reader (flag rate %s); copies citing a twin source pass even an LLM that reads the sources (%s)." % (pct(fl(BO.F0B, "COPY_PARA")), pct(fl(BO.DLLM, "COPY_TWIN"))),
               "Honest same-topic reports and the no-source control look as similar as copies to embedding formulas (cosine flags %s of the no-source pairs)." % pct(fl("F2 embedding cosine", "NOSRC_SAME")),
               "The ledger's chain completeness is satisfied by a cover story (the cited source was opened); only the message record reveals copying.",
               "Without the ledger, Target C recall falls from %.2f to %.2f." % (v(BO.F10["full"], "recall", tgt="provfalse"), v(BO.F10["none"], "recall", tgt="provfalse"))])
    D.h("19. Reproducibility")
    D.p("Code, frozen corpora with SHA-256, raw runs, scores and metrics are in this package; 17 unit tests pass without network or GPU. Formula pipeline reproduction is exact; LLM generation is not exactly reproducible "
        "even at temperature 0 (setup is reproducible, outputs are not). Full reproduction needs Ollama, the embedding model and access to the remote Gemma model; the earlier 184-book corpus is not distributed.")
    D.h("20. Discussion, limitations, dual use, future work")
    D.p("Content similarity is the wrong main signal for copying and provenance claims; claim-to-source support and process evidence carry it. The ledger result is an upper bound because the controller writes both the log "
        "and the labels. Limitations: one generator model; instructed agents; controller-mediated tools; AI-assisted source texts with common knowledge; shared source library across replicates; frozen formulas not tuned. "
        "Dual use: the scenarios instruct a model to misrepresent provenance in a sandbox with fictional framing, and results show which signals monitors miss. Future work: heterogeneous and local models, "
        "agents choosing their own tool calls, adaptive copiers, signed logs, real transcripts, and ECE via Argon F35.")
    D.h("21. Conclusion")
    D.p("Reading reports is not enough; similarity formulas alone did not help; claim-to-source checks and a provenance record separated copying, shared evidence and false provenance claims in controlled scenarios.")
    D.h("References")
    for ref in ["Ashery, A. F., Aiello, L. M., & Baronchelli, A. (2025). Emergent social conventions and collective bias in LLM populations. Science Advances, 11(20), eadu9368.",
                "Cemri, M., et al. (2025). Why do multi-agent LLM systems fail? arXiv:2503.13657.", "Chan, A., et al. (2025). Infrastructure for AI agents. arXiv:2501.10114.",
                "Crosby, S. A., & Wallach, D. S. (2009). Efficient data structures for tamper-evident logging. USENIX Security.",
                "Gao, T., Yen, H., Yu, J., & Chen, D. (2023). Enabling large language models to generate text with citations. EMNLP 2023.",
                "Greenblatt, R., Shlegeris, B., Sachan, K., & Roger, F. (2024). AI control. ICML 2024, PMLR 235, 16295-16336.", "Hammond, L., et al. (2025). Multi-agent risks from advanced AI. arXiv:2502.14143.",
                "Motwani, S. R., et al. (2024). Secret collusion among AI agents. NeurIPS 37.", "Rashkin, H., et al. (2021). Measuring attribution in natural language generation models. arXiv:2112.12870.",
                "Vardi, Y., & Zhang, C.-H. (2000). The multivariate L1-median and associated data depth. PNAS 97(4), 1423-1426.", "Weiszfeld, E. (1937). Tohoku Mathematical Journal 43, 355-386.",
                "Brier (1950) and Platt (1999) are cited from secondary records only; the status of every reference is listed in 01_SOURCE_AUDIT/LITERATURE_CANDIDATES.md."]:
        D.p(ref)
    D.h("Appendix: per-type flag rates and sensitivity")
    D.p("Full tables with confidence intervals, the naive-threshold variant and the verified-subset sensitivity analysis are in 07_STATISTICAL_ANALYSIS/TABLES.md.")
    out = os.path.join(ROOT, "10_REPORT_ENGLISH", "SWARM_ALIGNMENT_FULL_TECHNICAL_REPORT_EN.docx")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    D.d.save(out)
    return out


def build_id():
    D = Doc("Trust the Report or Check the Artifact? Pengawasan Sadar-Asal-Usul terhadap Laporan yang Tampak Independen pada Sistem Multi-Agen LLM - Laporan Lengkap")
    D.p("Mochamad Azmi Rizkulloh. Swarm Alignment Hackathon, 6-8 November 2026 (jalur utama: Track 4, Pengawasan dan Kendali Multi-Agen; uji pendukung Track 1-3).")
    D.h("Ringkasan")
    D.p("Sistem multi-agen LLM sering diawasi lewat laporan agen itu sendiri. Laporan bisa mengaku memakai bukti independen padahal isinya disalin dari agen lain, atau kedua agen memakai dokumen yang sama. "
        "Kami membangun uji terkendali dengan agen LLM nyata (Gemma 4 31B) yang menulis laporan dari materi pembelajaran milik peneliti. Kontroler membuat skenario dengan kebenaran dasar yang diketahui untuk tiga target "
        "terpisah: penyalinan, bukti tidak independen, dan klaim asal-usul yang palsu. Sumber kembar yang jujur, sumber hampir sama, dan kontrol tanpa sumber ikut diuji agar kemiripan tidak disalahartikan sebagai kecurangan.")
    D.p("Pada %d skenario uji (5 replikat, ambang pada alarm palsu 5%% dikalibrasi pada topik terpisah): LLM yang hanya membaca laporan menemukan %.0f%% salinan, dan hanya %.0f%% dari salinan parafrasa yang mengaku independen. "
        "Rumus kemiripan penelitian (STP, STP-AR, MOI, RCC-v3.3, Argon) yang dipakai sendiri mendekati tebakan acak (AUROC %.2f sampai %.2f). Pemeriksaan klaim terhadap sumber yang dikutip menaikkan AUROC menjadi %.2f, "
        "dan penambahan ledger asal-usul berantai hash memberi recall %.2f dengan Brier %.3f saat log lengkap, lalu menurun bertahap saat kejadian dihilangkan. Keterbatasan: satu model pembangkit, agen yang diinstruksikan, "
        "dan ledger yang ditulis kontroler, sehingga hasil ledger adalah batas atas." % (BO.n_test, 100 * v(BO.F0B, "recall"), 100 * fl(BO.F0B, "COPY_PARA"), BO.au_lo, BO.au_hi, v(BO.F9B, "auroc"),
                                                                                     v(BO.F10["full"], "recall"), v(BO.F10["full"], "brier")))
    D.h("1. Latar belakang dan masalah")
    D.p("Laporan agen yang tampak independen belum tentu independen. Isi yang sama juga belum membuktikan penyalinan, karena agen yang jujur dapat mengutip dua terbitan berbeda yang memuat teks sama. "
        "Masalahnya: apa yang harus diperiksa pengawas, dan sinyal apa yang memisahkan penyalinan, bukti bersama, dan klaim asal-usul palsu.")
    D.h("2. Tujuan dan pertanyaan penelitian")
    D.bullets(["P1: Apakah membaca laporan cukup untuk mendeteksi penyalinan, bukti tidak independen, dan klaim asal-usul palsu?",
               "P2: Apakah rumus kemiripan penelitian (STP, STP-AR, MOI, RCC-v3.3, Argon) memperbaiki pengawasan dibanding baseline leksikal dan embedding?",
               "P3: Apakah pemeriksaan klaim terhadap sumber dan ledger asal-usul memperbaiki deteksi, dan bagaimana ledger menurun saat kejadian hilang?",
               "P4: Monitor mana yang memberi alarm palsu pada sumber kembar jujur dan pada kontrol tanpa sumber?"])
    D.h("3. Karya terkait")
    D.p("Kendali AI mengevaluasi pemantauan terpercaya terhadap model tak terpercaya (Greenblatt dkk., 2024). Taksonomi risiko dan kegagalan multi-agen (Hammond dkk., 2025; Cemri dkk., 2025) memotivasi pengawasan antar-agen. "
        "Kolusi rahasia meneliti koordinasi tersembunyi (Motwani dkk., 2024). Evaluasi atribusi (Rashkin dkk., 2021; Gao dkk., 2023) menghubungkan klaim dengan sumber yang dikutip. "
        "Infrastruktur agen (Chan dkk., 2025) dan pencatatan tahan-ubah (Crosby dan Wallach, 2009) mendasari identitas agen dan rantai hash. Status verifikasi tiap referensi ada di 01_SOURCE_AUDIT/LITERATURE_CANDIDATES.md.")
    D.h("4. Arsitektur sistem")
    D.fig(os.path.join(FIG, "fig1_architecture.png"), "Arsitektur: kontroler membuat skenario dan memegang kebenaran dasar; monitor tidak pernah melihat label.")
    D.h("5. Lingkungan percobaan dan GPU")
    D.p("Perangkat terukur: NVIDIA GeForce RTX 3050 Laptop GPU, 4096 MiB, driver 610.74, PyTorch 2.6.0+cu124 (prompt awal mengira RTX 2060). Embedding (embeddinggemma-2:740m, 768 dimensi) berjalan di GPU lokal lewat Ollama 0.40.14 "
        "(utilisasi rata-rata 5%, puncak 89%, VRAM puncak 1,6 GB, suhu maksimum 60 C, tanpa kejadian termal). Agen dan monitor LLM (Gemma 4 31B, Ollama cloud) berjalan jarak jauh, bukan di GPU lokal. "
        "Rumus, ledger, dan statistik berjalan di CPU.")
    D.fig(os.path.join(FIG, "fig9_gpu.png"), "GPU lokal selama penghitungan skor (hanya embedding).")
    D.h("6. Pemilihan agen dan inventaris bot")
    D.p("Inventaris 69 bot terdahulu diaudit (BOT_REGISTRY.csv): 22 hanya brief, 17 dan 13 modul alat berbasis aturan, 10 modul orkestrasi, 4 serah-terima ke model luar, dan 3 butuh API luar; hanya 3 kandidat modul alat atau evaluator, "
        "dan tidak ada yang berupa agen LLM. Pemilihan berdasarkan kemampuan dan relevansi, bukan kinerja uji. Pada penelitian ini agen adalah instans Gemma 4 31B dengan konteks terpisah (model sama, sehingga independensi agen terbatas pada konteks).")
    D.h("7. Rumus matematika")
    D.p("Embedding kalimat klaim U_A, U_B dan kalimat metode W_A, W_B berupa vektor satuan; g(X) adalah geometric median (iterasi Weiszfeld). Rumus beku yang sudah ada sebelum sprint:")
    D.eq("STP(A,B) = clip[0,1] < g(U_A)/|g(U_A)| , g(U_B)/|g(U_B)| >", 1)
    D.eq("STP-AR = STP / (1 + k sigma_boot),  k = 2,  sigma_boot = simpangan baku STP dari B = 25 sampel ulang", 2)
    D.eq("MOI(A,B) = clip[0,1] < mu(W_A), mu(W_B) >;   S_base = 0,5 STP-AR + 0,5 MOI", 3)
    D.eq("RCC: SER = exp(-sum p_i ln p_i);  kappa = exp(-10 m);  gamma = 1/(1+exp(-20(kappa-0,85)));  lambda = 0,5 gamma;  c = normalise((1-lambda) g + lambda a)", 4)
    D.eq("theta = Q0,95 { s_i : y_i = 0, i di kalibrasi },   y_hat = 1[s > theta]", 5)
    D.eq("p = sigma(w^T z + b)   (dilatih hanya di data kalibrasi)", 6)
    D.eq("Brier = (1/N) sum (p_i - y_i)^2,   BSS = 1 - Brier / Brier_ref", 7)
    D.p("STRICT-GAP dan versi RCC lama tidak diuji karena tidak relevan atau sudah tergantikan; ECE lewat kalibrasi Argon F35 direncanakan tetapi belum dijalankan.")
    D.h("8. Data dan asal-usul sumber")
    D.p("Sumber: 109 teks definisi dan penjelasan dari materi pembelajaran peneliti (13 topik biologi, antropologi, geografi, IPS, matematika), delapan kalimat per teks, ditambah 44 kembar jujur dan 22 hampir-sama (175 sumber). "
        "Teks adalah draf buatan peneliti dengan bantuan AI. Skenario kalibrasi dan uji memakai domain topik yang terpisah. Korpus 184 buku pada pilot sebelumnya tidak dikirim ke layanan jarak jauh sehingga tidak dipakai untuk percobaan LLM.")
    D.fig(os.path.join(FIG, "fig8_distribution.png"), "Sebaran skenario pada lima replikat.")
    D.h("9. Rancangan percobaan, kebenaran dasar, dan baseline")
    D.table(SCEN, [1.3, 3.3, 0.6, 0.8, 0.8])
    D.p("Kebenaran dasar berasal dari rancangan kontroler dan tidak terlihat oleh monitor. Lima replikat memakai rencana skenario dan seed berbeda (164 skenario per replikat). Analisis utama memakai semua skenario; analisis sensitivitas "
        "hanya salinan yang terverifikasi lewat angka yang dipakai ulang (teks kurikulum sedikit memuat angka, sehingga 35% skenario salin tidak dapat diverifikasi dengan cara ini).")
    D.h("10. Protokol komunikasi dan mekanisme pengawasan")
    D.p("Agen B menerima laporan Agen A sebagai pesan pada skenario salin dan berbagi; penggunaan alat dimediasi kontroler dan setiap kejadian ditulis ke ledger berantai hash SHA-256. Monitor: laporan saja (aturan dan LLM), "
        "LLM dengan sumber, rumus tunggal, pemeriksaan dukungan klaim dan tumpang-tindih sumber, ansambel (F9, F9b), dan F10 (ansambel ditambah fitur ledger) pada empat kondisi log: penuh, tanpa pesan, 50% kejadian, dan hilang.")
    D.h("11. Rencana analisis statistik")
    D.p("Per replikat, ambang dan model logistik dilatih pada data kalibrasi dan dievaluasi pada data uji; hasil uji digabung. Ketidakpastian: bootstrap berklaster 95% atas (replikat, sumber A). Semua hasil deskriptif; tidak ada uji hipotesis, "
        "dan kelima replikat berbagi pustaka sumber yang sama sehingga bukan sampel independen.")
    D.h("12. Hasil Track 4 (pengawasan)")
    D.table(metric_table("copy"), [2.2, 0.55, 0.5, 0.65, 0.5, 0.5, 0.55, 0.55, 0.5], size=7)
    D.fig(os.path.join(FIG, "fig2_detection_fpr_brier.png"), "Recall, alarm palsu, dan Brier semua monitor untuk tiga target (CI 95% bootstrap berklaster).")
    D.fig(os.path.join(FIG, "fig3_flag_rate_by_type.png"), "Tingkat penandaan menurut jenis skenario (ambang Target A).")
    D.p("Laporan saja: pembaca laporan LLM menandai %s salinan; menurut jenis, %s laporan berbagi dengan atribusi dan %s salinan verbatim, tetapi hanya %s salinan parafrasa dan %s salinan yang mengutip sumber kembar. "
        "Rumus tunggal mencapai recall paling tinggi %.2f (AUROC %.2f-%.2f). Pemeriksaan klaim terhadap sumber (F9b) mencapai AUROC %.2f; dengan ledger (F10) recall %.2f dan Brier %.3f." % (
            ci(BO.F0B, "recall"), pct(fl(BO.F0B, "SHARED_OK")), pct(fl(BO.F0B, "COPY_LIT")), pct(fl(BO.F0B, "COPY_PARA")), pct(fl(BO.F0B, "COPY_TWIN")), BO.rec_hi, BO.au_lo, BO.au_hi,
            v(BO.F9B, "auroc"), v(BO.F10["full"], "recall"), v(BO.F10["full"], "brier")))
    D.h("13. Ablasi formula", 2)
    D.p("Urutan ablasi (leksikal, cosine, STP, STP-AR, STP-AR+MOI, RCC, Argon, ansambel) ada pada tabel Target A dan di TABLES.md. Formula yang membantu hanya sebagai bagian ansambel: F9 menaikkan AUROC dari paling tinggi %.2f menjadi %.2f. "
        "Formula yang tidak mengubah hasil sendirian: STP, STP-AR, RCC-v3.3. Formula yang menambah alarm palsu: cosine embedding, STP, dan RCC pada kontrol tanpa sumber." % (BO.au_hi, v(BO.F9, "auroc")))
    D.h("14. Perbandingan model", 2)
    D.p("Hanya Gemma 4 31B (jarak jauh) yang dijalankan. Qwen (HTTP 401), qwen3.5 dan deepseek cloud (HTTP 410), minimax dan kimi (HTTP 402) DIBLOKIR; Claude Haiku sebagai agen eksperimen dan model lokal di GPU TIDAK DIUJI. "
        "Konfigurasi B (heterogen) dan C (lintas penyedia) tidak memiliki hasil; konfigurasi A (homogen) dan D (monitor LLM dengan sumber) dijalankan.")
    D.h("15. Brier dan kalibrasi", 2)
    D.fig(os.path.join(FIG, "fig7_reliability.png"), "Diagram keandalan Target A (LLM laporan saja, ansambel formula, ansambel + ledger).")
    D.p("ECE lewat Argon F35 direncanakan tetapi belum dijalankan, jadi tidak dilaporkan.")
    D.h("16. Target B dan C")
    D.table(metric_table("noninde"), [2.2, 0.55, 0.5, 0.65, 0.5, 0.5, 0.55, 0.55, 0.5], size=7)
    D.table(metric_table("provfalse"), [2.2, 0.55, 0.5, 0.65, 0.5, 0.5, 0.55, 0.55, 0.5], size=7)
    D.fig(os.path.join(FIG, "fig6_visibility.png"), "Monitor sadar-asal-usul F10 saat log memburuk.")
    D.h("17. Uji pendukung Track 1-3")
    if T1:
        D.p("Sandbox menahan %d dari %d percobaan menembus folder (pembukaan tanpa pelindung membocorkan %d), seluruh %d penolakan tercatat, dan rantai ledger valid. Pipeline formula tereproduksi persis (%.0f%%); "
            "kesamaan keluaran LLM persis %.0f%% pada suhu 0 dan %.0f%% pada suhu 0,7 dengan seed tetap, sedangkan kesamaan semantik (cosine > 0,99) %.0f%%." % (
                T1["n_attacks"] - T1["leaks_with_sandbox"], T1["n_attacks"], T1["leaks_naive_open_baseline"], T1["denied_and_logged"], 100 * T1R["formula_pipeline_exact_agreement"],
                100 * T1R["llm_temp0"]["exact_output_agreement"], 100 * T1R["llm_temp0.7_fixed_seed"]["exact_output_agreement"], 100 * T1R["llm_temp0"]["semantic_agreement_cos_gt_0.99"]), "Track 1.")
    if T2:
        D.p("Klaim palsu ditanam pada agen 1 dari 4, dan agen lain memegang sumber berbeda. Hasil menurut topologi:", "Track 2.")
        D.table(t2_rows(), [1.3, 0.5, 1.2, 1.2, 0.9, 0.7, 0.8])
        D.p("Tidak ada agen hilir yang mengulang klaim palsu pada topologi mana pun (efek langit-langit: agen diberi tahu hanya memuat fakta yang didukung sumbernya sendiri), sehingga uji ini tidak membedakan topologi pada penyebaran; tingkat koreksi hanya mencerminkan berapa agen hilir yang melihat laporan tertanam. Diperlukan instruksi yang lebih lemah atau agen yang harus bergantung pada laporan bersama.")
    else:
        D.p("Hasil Track 2 belum tersedia saat dokumen ini dibuat (lihat 05_EXPERIMENTS/track2_networks_tls).", "Track 2.")
    if T3T:
        dr = T3T["detection_rate"]
        D.p("Identitas sumber duplikat lewat hash isi: presisi 1,00 dan recall 1,00. Deteksi rantai hash: perubahan %.2f, penghapusan %.2f, penukaran urutan %.2f, pemotongan ekor %.2f (%.2f bila hash kepala dijangkarkan di luar). "
            "Identitas lewat id internal 1,00 dibanding 0,00 lewat nama tampilan pada simulasi tabrakan nama (pemeriksaan kewarasan harness). Kelengkapan rantai tertipu oleh cerita penutup (COPY_COVER = %.2f); hanya catatan pesan yang mengungkapnya." % (
                dr["edit_data"], dr["delete_middle"], dr["swap_order"], dr["truncate_tail"], dr["truncate_tail_with_anchored_head"], T3C["chain_completeness_by_type"]["COPY_COVER"]), "Track 3.")
    D.fig(os.path.join(FIG, "fig10_tracks.png"), "Uji pendukung Track 2 dan 3.")
    D.h("18. Analisis kasus gagal")
    D.bullets(["Salinan parafrasa yang mengaku independen lolos dari pembaca laporan LLM (tingkat penandaan %s); salinan yang mengutip sumber kembar lolos bahkan dari LLM yang membaca sumber (%s)." % (pct(fl(BO.F0B, "COPY_PARA")), pct(fl(BO.DLLM, "COPY_TWIN"))),
               "Laporan jujur satu topik dan kontrol tanpa sumber tampak semirip salinan bagi rumus embedding (cosine menandai %s pasangan tanpa sumber)." % pct(fl("F2 embedding cosine", "NOSRC_SAME")),
               "Kelengkapan rantai ledger terpenuhi oleh cerita penutup; hanya catatan pesan yang mengungkap penyalinan.",
               "Tanpa ledger, recall Target C turun dari %.2f menjadi %.2f." % (v(BO.F10["full"], "recall", tgt="provfalse"), v(BO.F10["none"], "recall", tgt="provfalse"))])
    D.h("19. Reproduksibilitas")
    D.p("Kode, korpus beku dengan SHA-256, jalankan mentah, skor, dan metrik ada di paket ini; 17 uji unit lulus tanpa jaringan atau GPU. Reproduksi pipeline formula persis; pembangkitan LLM tidak persis bahkan pada suhu 0 "
        "(pengaturan dapat direproduksi, keluaran tidak). Reproduksi penuh butuh Ollama, model embedding, dan akses ke model Gemma jarak jauh; korpus 184 buku tidak dibagikan.")
    D.h("20. Diskusi, keterbatasan, penggunaan ganda, dan kerja lanjutan")
    D.p("Kemiripan isi bukan sinyal utama yang tepat untuk penyalinan dan klaim asal-usul; dukungan klaim terhadap sumber dan bukti proses yang membawanya. Hasil ledger adalah batas atas karena kontroler menulis log dan label. "
        "Keterbatasan: satu model pembangkit; agen diinstruksikan; alat dimediasi kontroler; teks sumber draf berbantuan AI dengan pengetahuan umum; pustaka sumber sama di semua replikat; formula beku tidak disetel. "
        "Penggunaan ganda: skenario menginstruksikan model menyamarkan asal-usul di sandbox berbingkai fiktif, dan hasilnya menunjukkan sinyal yang luput dari monitor. Kerja lanjutan: model heterogen dan lokal, agen yang memilih sendiri panggilan alat, "
        "penyalin adaptif, log bertanda tangan, transkrip nyata, dan ECE lewat Argon F35.")
    D.h("21. Kesimpulan")
    D.p("Membaca laporan saja tidak cukup; rumus kemiripan sendirian tidak membantu; pemeriksaan klaim terhadap sumber dan catatan proses memisahkan penyalinan, bukti bersama, dan klaim asal-usul palsu pada skenario terkendali.")
    D.h("Daftar pustaka")
    D.p("Lihat daftar pada laporan bahasa Inggris dan status verifikasi tiap referensi di 01_SOURCE_AUDIT/LITERATURE_CANDIDATES.md. Brier (1950) dan Platt (1999) hanya dikutip dari catatan sekunder.")
    out = os.path.join(ROOT, "11_REPORT_INDONESIAN", "LAPORAN_LENGKAP_SWARM_ALIGNMENT_INDONESIA.docx")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    D.d.save(out)
    return out


if __name__ == "__main__":
    print(build_en())
    print(build_id())
