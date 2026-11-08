"""Build the OFFICIAL Apart Research submission (docx on the official template) from result files. All numbers are read from the CSV/JSON results.
Usage: py -3.12 -I -B -X utf8 build_official.py"""
import csv
import glob
import json
import os
import sys

import docx

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import docx_builder as DB  # noqa: E402

MET = os.path.join(ROOT, "07_STATISTICAL_ANALYSIS", "metrics_tls_alllabels")
MET_V = os.path.join(ROOT, "07_STATISTICAL_ANALYSIS", "metrics_tls")
FIG = os.path.join(ROOT, "08_VISUAL_EVIDENCE", "figures_tls")
EXP = os.path.join(ROOT, "05_EXPERIMENTS")
OUT = os.path.join(ROOT, "12_APART_SUBMISSION", "SWARM_ALIGNMENT_OFFICIAL_SUBMISSION.docx")
JUDUL = "Trust the Report or Check the Artifact? Provenance-Aware Oversight of Falsely Independent Reports in Multi-Agent LLM Systems"


def rows(folder, name):
    return list(csv.DictReader(open(os.path.join(folder, name), encoding="utf-8")))


MAIN, PT = rows(MET, "results_main.csv"), rows(MET, "results_per_type.csv")
MAIN_V = rows(MET_V, "results_main.csv")


def R(mon, tgt="copy", rule="all", src=None):
    return next(r for r in (src or MAIN) if r["monitor"] == mon and r["target"] == tgt and r["threshold_rule"] == rule)


def v(mon, key, tgt="copy", rule="all", src=None):
    return float(R(mon, tgt, rule, src)[key])


def fl(mon, typ):
    return float(next(r for r in PT if r["monitor"] == mon and r["target"] == "copy" and r["type"] == typ)["flag_rate"])


def j(path):
    p = os.path.join(EXP, path)
    return json.load(open(p, encoding="utf-8")) if os.path.isfile(p) else None


def ci(mon, key, tgt="copy"):
    r = R(mon, tgt)
    return "%.2f [%.2f, %.2f]" % (float(r[key]), float(r[key + "_lo"]), float(r[key + "_hi"]))


F0B, DLLM, F4, F6, F8A, F9, F9B = ("F0b LLM report-only", "D  LLM with sources (Config D)", "F4 STP-AR", "F6 RCC-v3.3 (AR)", "F8a Argon embedding triage",
                                   "F9 formula ensemble (artifact only)", "F9b ensemble + source checks")
F10 = {m: "F10 ensemble + ledger [%s]" % m for m in ("full", "comm_hidden", "half", "none")}
FORMULAS = ["F1 lexical 3-gram", "F2 embedding cosine", "F3 STP", F4, "F5 STP-AR+MOI", F6, "F6b RCC-v3.3 (AR+MOI)", F8A, "F8b Argon claim overlap"]
n_test = int(R(F4)["n"])
au_lo = min(v(m, "auroc") for m in FORMULAS)
au_hi = max(v(m, "auroc") for m in FORMULAS)
rec_hi = max(v(m, "recall") for m in FORMULAS)

ABSTRACT = (
    "Multi-agent LLM systems can produce reports that look independent while sharing or copying evidence. We ask what an overseer must inspect "
    "to notice: the reports, the artifacts, or a provenance record of how the reports were made. We built a controlled testbed in which real LLM "
    "agents (Gemma 4 31B) write evidence reports from the author's own course materials, while a controller creates scenarios with known ground "
    "truth for three separate targets: copying, non-independent evidence, and a false provenance claim. Honest twin sources, near-duplicates and "
    "a no-source control keep similarity from being mistaken for misconduct. Over %d replicates (%d pooled test scenarios, thresholds set at a "
    "5%% false-alarm target on disjoint topics), an LLM reading reports only recovered %.0f%% of copies, and only %.0f%% of paraphrased copies "
    "that falsely claimed independence. Research similarity formulas used alone (STP, STP-AR, MOI, RCC-v3.3, Argon) were close to chance "
    "(AUROC %.2f to %.2f). Checking claims against the cited source raised AUROC to %.2f, and adding a hash-chained provenance ledger gave "
    "recall %.2f and Brier %.3f with a complete log, degrading gracefully as events were removed. Results rest on one generator model, "
    "instructed agents and a controller-written ledger, so the ledger results are an upper bound."
) % (int(R(F4)["n_reps"]), n_test, 100 * v(F0B, "recall"), 100 * fl(F0B, "COPY_PARA"), au_lo, au_hi, v(F9B, "auroc"), v(F10["full"], "recall"), v(F10["full"], "brier"))
assert 150 <= len(ABSTRACT.split()) <= 250, len(ABSTRACT.split())


def pct(x, d=0):
    return ("%." + str(d) + "f%%") % (100 * x)


def body(S):
    S.h2("1. Introduction")
    S.par("Systems of cooperating AI agents are commonly supervised through what the agents say about themselves: a report that names its sources, "
          "a message that a step is done. That is the channel the agents control. A report can state that its evidence is independent while the "
          "underlying material was copied from another agent, or both agents relied on the same document. A reader who trusts the report "
          "counts one source twice.")
    S.par("Identical content does not prove copying: two honest agents may cite two different publications that contain the same text. We therefore "
          "separate three targets with their own ground truth: **(A) copying occurred**, **(B) the evidence is non-independent**, and **(C) the "
          "provenance claim is false**. We ask which information an overseer needs for each target, and whether research similarity formulas "
          "help.")
    S.par("Contributions:", sesudah=3)
    S.daftar("num", [
        "**A controlled testbed with real LLM agents on real course text.** Ten scenario types (independent, no-source, honest twin, near-duplicate, "
        "shared-with-attribution and four copy variants), ground truth fixed by the controller, and disjoint calibration and test topics.",
        "**A comparison of monitors by what they read:** reports only, an LLM given the sources, frozen formulas (STP, STP-AR, MOI, RCC-v3.3, "
        "Argon F42 and F44), claim-versus-cited-source checks, and a hash-chained provenance ledger, with Brier scores and cluster-aware intervals.",
        "**Findings:** report reading misses paraphrased copies that claim independence; the formulas alone did not help; source-support checks "
        "and process evidence carry the signal; the ledger degrades gracefully when events are missing.",
    ])
    S.h2("2. Related Work")
    S.par("**AI control and multi-agent risk.** AI control evaluates protocols in which a trusted monitor reviews an untrusted model (Greenblatt et al., 2024). "
          "Multi-agent risk taxonomies name miscoordination, conflict and collusion (Hammond et al., 2025), and failure taxonomies show that inter-agent "
          "misalignment and weak verification are common causes of failure (Cemri et al., 2025). Secret collusion studies hidden coordination "
          "between agents (Motwani et al., 2024). Our setting has no hidden channel: the shared material is an ordinary artifact and the concealment "
          "lives in the report.")
    S.par("**Attribution and agent infrastructure.** Attribution evaluation asks whether generated text is supported by an identified source "
          "(Rashkin et al., 2021) and benchmarks citation quality (Gao et al., 2023). Infrastructure for agents proposes identifiers and attribution "
          "of actions to agents (Chan et al., 2025). We use controller-issued agent identifiers and a hash-chained log in the spirit of "
          "tamper-evident logging (Crosby and Wallach, 2009); the chain gives integrity, not authentication.")
    S.par("**Collective behaviour.** Groups of LLM agents can develop collective bias that no single agent has (Ashery et al., 2025). We do not "
          "study emergent dynamics; we study whether an overseer can tell dependence from independence.")
    S.h2("3. Methods")
    S.h3("3.1 Testbed and scenarios")
    S.par("Sources are %d definition and explanation texts from the author's course materials (biology, anthropology, geography, social studies, "
          "mathematics); eight evenly spaced sentences per text form a source document. From them we derive honest twins (identical body, "
          "different publisher) and near-duplicates (two sentences dropped, two swapped). In each scenario Agent A writes a report from its source. "
          "Agent B then either writes from its own source (independent, twin, near-duplicate), writes from general knowledge only (no-source "
          "control), builds openly on A's report and cites it (shared), or, in a red-team role play with fictional framing, reuses A's report "
          "while citing another source: verbatim (COPY_LIT), paraphrased (COPY_PARA), citing the twin of A's source (COPY_TWIN), or after opening "
          "the cited source as a cover story (COPY_COVER). Agents are Gemma 4 31B (remote); each replicate uses a different scenario plan and "
          "generation seed (5 replicates, 164 scenarios each). Calibration and test scenarios come from disjoint topic domains." % 109, sesudah=4)
    S.par("Ground truth comes from the controller's design, never from the agents or monitors. Honest twins are (A=0, B=1, C=0); copies are "
          "(1, 1, 1); shared-with-attribution is (1, 1, 0). A numeric reuse check verified copying for the subset of copy scenarios that contain "
          "numbers; because course text has few numbers, the primary analysis keeps all scenarios and a sensitivity analysis keeps only verified ones.")
    S.h3("3.2 Monitors and formulas")
    S.par("Each sentence is embedded with embeddinggemma-2:740m on the local GPU. For reports A and B with sentence vectors U_A and U_B, let g(X) be the "
          "geometric median (Weiszfeld iteration) and cos the cosine. The frozen, preexisting formulas are:")
    S.rumus("STP(A,B) = cos( g(U_A), g(U_B) )", 1)
    S.rumus("STP-AR = STP / ( 1 + k σ_boot ),  k = 2,  σ_boot = sd of STP over 25 bootstrap resamples", 2)
    S.rumus("MOI(A,B) = cos( mean(W_A), mean(W_B) ),   S_base = ½ STP-AR + ½ MOI", 3)
    S.rumus("RCC(A,B) = cos( c_A, c_B ),   c = normalise( (1−λ) g + λ a ),   λ = 0.5 / (1 + exp(−20(κ − 0.85)))", 4)
    S.par("W are method-sentence embeddings, a is an attention-weighted centroid, and κ is a confidence from the spectral effective rank of the "
          "similarity matrix (Appendix E). Argon F42 gives an embedding-distance score and F44 a claim-overlap score. Monitors are: F0a "
          "(trust the cited sources), F0b (Gemma reads both reports), D (Gemma also reads the cited sources), single formulas, S1 and S2 "
          "(claims unsupported by the cited source; overlap of the cited sources), F9 (logistic ensemble of artifact scores), F9b (F9 plus S1, S2 "
          "and claim support in A's source) and F10 (F9b plus ledger features: message received, cited source not opened, shared source body hash). "
          "The ledger is a SHA-256 hash chain written by the controller; visibility is varied (full, no messages, 50% of events, missing).")
    S.h3("3.3 Calibration and statistics")
    S.par("Thresholds are the 95th percentile of calibration scores of all negatives of the target (honest twins included); logistic models and "
          "their probabilities are fitted on the calibration split only, with Brier score BS = (1/N) Σ (p_i − y_i)^{2} and a constant-prevalence "
          "reference (prevalence from calibration data). Intervals are 95% cluster bootstrap (clusters = replicate × source of A; 1000 resamples); "
          "all statistics are descriptive.")
    S.h2("4. Results")
    S.par("**Report reading.** Trusting the cited sources never flags anything (recall 0.00). An LLM reading both reports detects %s of copies at "
          "FPR %s. Its detections are concentrated where the report itself says it is not independent (shared-with-attribution %s) or the copy is verbatim "
          "(%s); paraphrased copies claiming independence are almost invisible (%s), as are copies citing a twin source (%s). Giving the LLM the cited "
          "sources raises recall to %s but it still misses twin-source copies (%s)." % (
              ci(F0B, "recall"), pct(v(F0B, "fpr"), 1), pct(fl(F0B, "SHARED_OK")), pct(fl(F0B, "COPY_LIT")), pct(fl(F0B, "COPY_PARA")), pct(fl(F0B, "COPY_TWIN")),
              ci(DLLM, "recall"), pct(fl(DLLM, "COPY_TWIN"))))
    S.par("**Formulas alone.** Used as single scores, none of the similarity formulas separates copying from honest same-topic work: recall is at most %.2f at the 5%% "
          "target and AUROC ranges from %.2f to %.2f (Table 1). They also raise false alarms on the no-source control, where agents share general knowledge "
          "(embedding cosine flags %s of those pairs). RCC-v3.3 was stable but not better than STP-AR, consistent with earlier validation." % (
              rec_hi, au_lo, au_hi, pct(fl("F2 embedding cosine", "NOSRC_SAME"))))
    S.tabel([["Monitor (Target A)", "Recall [95% CI]", "FPR", "AUROC", "Brier", "BSS"]] + [
        [lab, ci(m, "recall"), "%.2f" % v(m, "fpr"), "%.2f" % v(m, "auroc"), "%.3f" % v(m, "brier"), "%.2f" % v(m, "bss")] for lab, m in (
            ("F0b LLM, reports only", F0B), ("D  LLM + sources", DLLM), ("F4 STP-AR", F4), ("F6 RCC-v3.3", F6), ("F8a Argon F42", F8A),
            ("F9 formula ensemble", F9), ("F9b + source checks", F9B), ("F10 + ledger (full)", F10["full"]), ("F10 ledger missing", F10["none"]))],
        [2.0, 1.45, 0.55, 0.6, 0.6, 0.5], ukuran=DB.Pt(8),
        judul="Table 1. Target A (copying), %d pooled test scenarios, 5 replicates, threshold at 5%% false alarms on calibration negatives. BSS = Brier skill versus constant prevalence." % n_test)
    S.par("**Source support and process evidence.** Combining artifact scores with claim-versus-cited-source checks (F9b) reaches AUROC %.2f with recall %.2f at FPR %.2f; "
          "adding the ledger (F10, full log) reaches recall %.2f, AUROC %.2f and Brier %.3f. The ledger result is an upper bound: the controller writes both the log "
          "and the labels. Figure 1 shows flag rates by scenario type and Figure 2 shows how F10 degrades: with message events hidden recall stays %.2f, with half of the "
          "events %.2f, and with no log it equals F9b (%.2f). For Target C (false provenance claim) the ledger matters most: recall %.2f with the full log versus %.2f without." % (
              v(F9B, "auroc"), v(F9B, "recall"), v(F9B, "fpr"), v(F10["full"], "recall"), v(F10["full"], "auroc"), v(F10["full"], "brier"),
              v(F10["comm_hidden"], "recall"), v(F10["half"], "recall"), v(F10["none"], "recall"),
              v(F10["full"], "recall", tgt="provfalse"), v(F10["none"], "recall", tgt="provfalse")))
    S.gambar(os.path.join(FIG, "fig3_flag_rate_by_type.png"), 6.0,
             "Figure 1. Flag rate by scenario type for Target A. Left of the white line: no copying. Honest twin sources (TWIN_H) and the no-source control (NOSRC_SAME) are "
             "where content-similarity monitors raise false alarms.")
    S.gambar(os.path.join(FIG, "fig6_visibility.png"), 6.0,
             "Figure 2. Provenance-aware monitor (F10) as the log degrades. Target C (false provenance claim) loses the most when events are removed.")
    S.par("**Sensitivity.** Keeping only copy scenarios verified by reused numbers (n = %d) gives the same ranking: F0b recall %.2f, D %.2f, best single formula AUROC %.2f, F9b AUROC %.2f." % (
        int(R(F4, src=MAIN_V)["n"]), v(F0B, "recall", src=MAIN_V), v(DLLM, "recall", src=MAIN_V), max(v(m, "auroc", src=MAIN_V) for m in FORMULAS), v(F9B, "auroc", src=MAIN_V)))
    S.h2("5. Discussion and Limitations")
    S.par("The central result is negative for content similarity and positive for process evidence. Honest agents that read the same material, or twin sources, write "
          "reports that are as similar as copies, so a similarity score cannot carry the decision; what separates the cases is whether the claims are supported by the cited "
          "source and what the agents actually did. For overseers this suggests logging which sources an agent opened and which messages it received, and checking claims "
          "against cited sources, before investing in more elaborate similarity measures.")
    S.h3("Limitations")
    S.par("(1) One generator model (Gemma 4 31B, remote); Qwen and other cloud models returned HTTP errors, Claude Haiku was not run as an agent and no local LLM fits the 4 GB GPU, so "
          "heterogeneous-model configurations were not tested. (2) Agents are instructed; they do not choose to deceive, tool use is controller-mediated and the ledger is "
          "written by the controller, so ledger results show the value of trustworthy logs, not detection of a tampering agent. (3) Source texts are the author's AI-assisted drafts and "
          "contain common knowledge. (4) Five replicates reuse one source library; the bootstrap is clustered but residual dependence remains. (5) Formulas were frozen "
          "and not tuned; their failure here does not show failure on their original task. (6) The embedding model tag is embeddinggemma-2:740m and may differ from the cited paper.")
    S.h3("Future Work")
    S.par("Test heterogeneous and local models, agents that choose their own tool calls, adaptive copiers, and signed logs; evaluate monitors on real multi-agent transcripts.")
    S.h2("6. Conclusion")
    S.par("Reading reports is not enough: paraphrased copies with a false independence claim passed an LLM report reader almost entirely. Similarity formulas alone were near chance. "
          "Claim-to-source checks and a provenance record separated the cases, and the record kept most of its value when half of the events were missing. These results come "
          "from controlled scenarios with instructed agents and should be tested on other models and on real transcripts.")
    S.h2("Code and Data")
    S.daftar("bullet", ["Code, frozen corpora, raw agent runs, metrics and figures: SWARM_ALIGNMENT_2026_FINAL (repository link to be added by the author).",
                        "Preexisting formulas (STP, STP-AR, MOI, RCC-v3.3), the Argon engine and the course materials are listed in Appendix C; book texts from an earlier pilot are not distributed."])
    S.h2("Author Contributions (optional)")
    S.par("[To be completed by the author.]")
    S.h2("References")
    S.daftar("ref", [
        "Ashery, A. F., Aiello, L. M., & Baronchelli, A. (2025). Emergent social conventions and collective bias in LLM populations. ~~Science Advances, 11~~(20), eadu9368.",
        "Brier, G. W. (1950). Verification of forecasts expressed in terms of probability. ~~Monthly Weather Review, 78~~(1), 1-3. †",
        "Cemri, M., Pan, M. Z., Yang, S., et al. (2025). Why do multi-agent LLM systems fail? arXiv:2503.13657.",
        "Chan, A., Wei, K., Huang, S., et al. (2025). Infrastructure for AI agents. arXiv:2501.10114.",
        "Chicco, D., & Jurman, G. (2020). The advantages of the Matthews correlation coefficient (MCC) over F1 score and accuracy in binary classification evaluation. ~~BMC Genomics, 21~~, 6.",
        "Crosby, S. A., & Wallach, D. S. (2009). Efficient data structures for tamper-evident logging. ~~18th USENIX Security Symposium~~.",
        "Field, C. A., & Welsh, A. H. (2007). Bootstrapping clustered data. ~~Journal of the Royal Statistical Society B, 69~~(3), 369-390.",
        "Gao, T., Yen, H., Yu, J., & Chen, D. (2023). Enabling large language models to generate text with citations. ~~EMNLP 2023~~ (arXiv:2305.14627).",
        "Greenblatt, R., Shlegeris, B., Sachan, K., & Roger, F. (2024). AI control: Improving safety despite intentional subversion. ~~ICML 2024~~, PMLR 235, 16295-16336.",
        "Hammond, L., Chan, A., Clifton, J., et al. (2025). Multi-agent risks from advanced AI. arXiv:2502.14143.",
        "Motwani, S. R., Baranchuk, M., Strohmeier, M., et al. (2024). Secret collusion among AI agents: Multi-agent deception via steganography. ~~NeurIPS 37~~.",
        "Platt, J. C. (1999). Probabilistic outputs for support vector machines and comparisons to regularized likelihood methods. In ~~Advances in Large Margin Classifiers~~, MIT Press. †",
        "Rashkin, H., Nikolaev, V., Lamm, M., et al. (2021). Measuring attribution in natural language generation models. arXiv:2112.12870.",
        "Vardi, Y., & Zhang, C.-H. (2000). The multivariate L1-median and associated data depth. ~~PNAS, 97~~(4), 1423-1426.",
        "Weiszfeld, E. (1937). Sur le point pour lequel la somme des distances de n points donnes est minimum. ~~Tohoku Mathematical Journal, 43~~, 355-386."])
    S.par("† Bibliographic details taken from secondary records; the publisher page could not be opened during verification.", ukuran=DB.Pt(9))
    S.h2("Appendix")
    S.h3("A. Limitations and Dual-Use / Ethical Considerations")
    S.par("**Dual use.** The copy scenarios instruct a model to misrepresent provenance in a sandbox with fictional framing; the findings show which signals a monitor misses "
          "(paraphrase plus a false independence claim) and could help an evader. We use fictional framing, publish no deceptive prompt tuned for deployment, and the "
          "defensive conclusions (log what agents open and receive, check claims against sources) do not depend on the attack details. **False accusations.** Content similarity "
          "alone flags honest agents with twin sources; any deployed monitor must treat a flag as a reason to inspect process records, not as proof. **Data.** All sources are the author's "
          "own course texts; no student data is involved. **Integrity versus authentication.** The hash chain detects edits, deletions and reordering but not truncation of the tail "
          "unless its head hash is anchored externally, and it does not authenticate agents.")
    S.h3("B. Results for Targets B and C (primary analysis, 5%-FPR threshold)")
    tb = [["Monitor", "B recall", "B FPR", "B AUROC", "C recall", "C FPR", "C AUROC"]]
    for lab, m in (("F0b LLM, reports only", F0B), ("D  LLM + sources", DLLM), ("F4 STP-AR", F4), ("F6 RCC-v3.3", F6), ("F9 ensemble", F9), ("F9b + source checks", F9B),
                   ("F10 ledger full", F10["full"]), ("F10 ledger missing", F10["none"])):
        tb.append([lab] + ["%.2f" % v(m, k, tgt=t) for t in ("noninde", "provfalse") for k in ("recall", "fpr", "auroc")])
    S.tabel(tb, [1.9, 0.75, 0.7, 0.75, 0.75, 0.7, 0.75], ukuran=DB.Pt(8), judul="Table 2. Targets B (evidence non-independent) and C (provenance claim false).")
    S.h3("C. Preexisting work versus work done during the sprint")
    S.par("Preexisting: STP, STP-AR and MOI baseline formulas and RCC-v3.3 (frozen files, SHA-256 recorded), the Argon formula engine and adaptor, the 69-bot Tools Sakti inventory "
          "(3 candidate tool modules, no LLM agents), the course materials, the Ollama runtime and the embedding model. During the sprint: an audit of a scripted-bot pilot (a hash() "
          "non-determinism bug was fixed and an honest-twin control lowered the original claim), the scenario controller, the ledger, the monitors, the LLM runs, the metrics engine, "
          "the Track 1-3 tests, figures and this report. Evidence for each item is listed in SPRINT_CONTRIBUTIONS.md.")
    t1, t2, t3 = j("track1_sandbox_tls/t1_sandbox.json"), j("track2_networks_tls/t2_summary.json"), j("track3_infrastructure_tls/t3_tamper.json")
    S.h3("D. Supporting tests for Tracks 1-3")
    txt = []
    if t1:
        txt.append("Track 1: the sandbox blocked %d of %d path-traversal attempts (an unprotected read leaked %d), all %d denials were logged and the ledger chain verified." % (
            t1["n_attacks"] - t1["leaks_with_sandbox"], t1["n_attacks"], t1["leaks_naive_open_baseline"], t1["denied_and_logged"]))
        rp = j("track1_sandbox_tls/t1_reproducibility.json")
        txt.append("The formula pipeline reproduced exactly (%.0f%%); LLM exact-output agreement was %.0f%% at temperature 0 and %.0f%% at temperature 0.7 with a fixed seed, "
                   "although semantic agreement (cosine > 0.99) was %.0f%%." % (100 * rp["formula_pipeline_exact_agreement"], 100 * rp["llm_temp0"]["exact_output_agreement"],
                                                                                100 * rp["llm_temp0.7_fixed_seed"]["exact_output_agreement"], 100 * rp["llm_temp0"]["semantic_agreement_cos_gt_0.99"]))
    if t2:
        parts = ["%s: propagation %.2f, correction %.2f" % (k, d["propagation_rate_per_downstream_agent"], d["correction_rate_per_downstream_agent"]) for k, d in t2.items()]
        txt.append("Track 2 (a false claim planted in agent 1 of 4, per downstream agent): " + "; ".join(parts) + ".")
        if all(d["propagation_rate_per_downstream_agent"] == 0 for d in t2.values()):
            txt.append("No downstream agent repeated the planted claim in any topology (ceiling effect: agents were told to include only facts their own source supports), so Track 2 does not separate topologies on propagation; the correction rates only reflect how many downstream agents saw the planted report.")
    if t3:
        dr = t3["detection_rate"]
        txt.append("Track 3: duplicate-source identity by body hash had precision and recall 1.00; the hash chain detected edits (%.2f), deletions (%.2f) and reordering (%.2f) but tail truncation "
                   "only when the head hash was anchored (%.2f without, %.2f with)." % (dr["edit_data"], dr["delete_middle"], dr["swap_order"], dr["truncate_tail"], dr["truncate_tail_with_anchored_head"]))
    S.par(" ".join(txt))
    S.h3("E. RCC-v3.3 definition (frozen parameters)")
    S.rumus("p_i = ν_i / Σ ν_l,   SER = exp( −Σ p_i ln p_i )", 5)
    S.rumus("m̃ = clip( (SER/n − 1/n) / (1 − 1/n) ),   κ = exp(−10 m̃)", 6)
    S.rumus("r_i = ⟨x_i, ĝ⟩,  τ = max(0.05, 1.4826 MAD(r)),  β_i = softmax(r_i/τ)", 7)
    S.rumus("α_i = 0.9 β_i + 0.1/n,   a = normalise(Σ α_i x_i)", 8)
    S.par("ν are the eigenvalues of X X^{T}. Parameters (10, 20, 0.85, 0.5, 0.05) are those of the preexisting implementation and were not tuned.")
    S.h2("LLM Usage Statement")
    S.par("Claude (Anthropic, Sonnet 5.5) wrote and ran the experiment code and drafted this report; Claude Haiku helper agents searched for literature (all items were checked against "
          "their landing pages where accessible, and † marks those that could not be). Gemma 4 31B served as the experimental agent, the LLM monitor and, in preliminary work, as "
          "a drafter of course materials. The author directed the work and is responsible for the content; [the author should confirm and edit this statement].")


def main():
    template = DB.TEMPLAT
    doc = docx.Document(template)
    S = DB.Penyusun(doc)
    body(S)
    DB.isi_judul_penulis(doc, JUDUL, ABSTRACT)
    for n in doc.tables[0]._tbl.iter(DB.qn("w:t")):
        if n.text == "[Name]":
            n.text = "Mochamad Azmi Rizkulloh"
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    doc.save(OUT)
    DB.perbaiki_catatan_kaki(OUT)
    print("saved", OUT, "| abstract words:", len(ABSTRACT.split()))


if __name__ == "__main__":
    main()
