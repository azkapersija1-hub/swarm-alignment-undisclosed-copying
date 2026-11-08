# NARRATION BRIEF FOR GPT (read this first)

You are helping the researcher (Mochamad Azmi Rizkulloh) NARRATE a finished experiment for the Apart Research Swarm Alignment Hackathon 2026
(official page: https://apartresearch.com/sprints/swarm-alignment-2026). Do not invent results, numbers, references or DOIs.
Every number below is copied from files in this package; the authoritative tables are `07_STATISTICAL_ANALYSIS/TABLES.md`.
Official submission limits: report PDF, official template, <= 8 pages excluding references and appendices, abstract 150-250 words,
a "Limitations and Dual-Use / Ethical Considerations" appendix, preexisting work disclosed, AI use disclosed. Everything is judged on one rubric:
Impact and Innovation, Execution Quality, Presentation and Clarity.

## One-paragraph story (safe to reuse)
Multi-agent LLM systems produce reports that look independent but may share or copy evidence. We built a controlled testbed: real LLM agents
(Gemma 4 31B) write evidence reports from the researcher's own course materials, while a controller creates scenarios with known ground truth
(independent, no-source control, honest twin sources, near-duplicates, shared-with-attribution, and four copy variants). We compare oversight
monitors that (a) read only the reports, (b) compare artifacts with research formulas (STP, STP-AR, MOI, RCC-v3.3, Argon F42/F44),
(c) check claims against the cited source, and (d) add a hash-chained provenance ledger. Ground truth is split into three separate targets
(A copying, B non-independent evidence, C false provenance claim) because identical content does not prove copying.

## Headline results (primary analysis: all 410 pooled test scenarios, 5 replicates, threshold = 95th percentile of calibration negatives; 95% cluster-bootstrap CIs are in TABLES.md)
Target A (copying), recall / FPR / AUROC / Brier (constant-prevalence reference Brier = 0.250 for the copy target, from results_main.csv brier_const; an earlier draft said 0.217, which was wrong):
- F0a rule that trusts cited sources: recall 0.000 (never flags).
- F0b LLM reading reports only: 0.381 / 0.010 / 0.919 / 0.113. By type it flags 0.88 of shared-with-attribution (the report itself says it is not independent) and 0.68 of verbatim copies, but only 0.06 of paraphrased copies and 0.10 of copies that cite the twin source (copy with a false independence claim).
- D LLM given the sources: 0.795 / 0.010 / 0.949 / 0.088 (misses copy-twin: 0.03 flag rate).
- Single formulas (STP, STP-AR, MOI, RCC-v3.3, Argon F42/F44, lexical, cosine): recall <= 0.09 at 5% FPR and AUROC 0.48 to 0.65 for Target A, i.e. near chance on this data. This is a NEGATIVE result for the formulas used alone. They also raise false alarms on the no-source control (embedding cosine flags 0.38 of NOSRC_SAME pairs: shared general knowledge looks like copying).
- F9 ensemble of artifact scores (logistic): 0.871 / 0.135 / 0.916 / 0.124.
- F9b ensemble plus claim-vs-cited-source checks: 0.971 / 0.075 / 0.990 / 0.048.
- P ledger only (full log): 1.000 / 0.000 / 1.000 / 0.002. CAUTION: the ledger and the ground truth are both written by the controller; this is an upper bound under a trustworthy log, not independent detection.
- F10 ensemble + ledger: full log 1.000 / 0.060 / 1.000 / 0.001; no message events 0.995 / 0.035 / 1.000 / 0.016; 50% of events 0.976 / 0.080 / 0.994 / 0.040; log missing 0.971 / 0.075 / 0.990 / 0.048 (equals F9b).
Target B (evidence non-independent): LLM with sources 0.997 recall at FPR 0.025; F9b 1.000 at FPR 0.025. Source-overlap features are part of the definition of this target (twins and near-duplicates), so treat this as expected.
Target C (provenance claim false): F10 full log 0.994 recall, FPR 0.062, AUROC 0.999, Brier 0.020; without ledger (F9b) 0.765 recall, AUROC 0.951, Brier 0.089.
Sensitivity (`metrics_tls/`): excluding copy scenarios whose copying could not be verified by reused numbers (the verified subset keeps n = 290 of 410 test scenarios, so 120 were excluded; an earlier draft said 35% of copy scenarios, which does not match these counts and must be recomputed before any figure is quoted) gives the same ranking.

## What is genuinely interesting (candidate contributions, state them as such)
1. Report-only monitoring fails on exactly the dangerous case: paraphrased copying with a false independence claim (LLM report reader flags 6% of them), while the same LLM catches reports that honestly say they are not independent.
2. Content similarity alone is the wrong tool for copying: honest same-topic and honest twin sources look as similar as copies; research formulas (STP family, RCC) did not help alone. Claim-versus-cited-source support and process evidence carry the signal.
3. Process evidence (ledger) improves provenance detection, and the monitor degrades gracefully when the log is incomplete (Figure 6).
4. Separating three targets and including honest-twin, near-duplicate and no-source controls exposes false alarms that a single "copy or not" label would hide.
5. Transparent audit trail: an earlier scripted-bot experiment was audited, a `hash()` non-determinism bug was found and fixed, and a negative control lowered the original claim (see `prior_experiment_swarm_provenance/audit/`).
Do NOT claim: "first in the world"; that results generalise to other LLMs, adaptive adversaries or real swarms; that formulas improved detection (they did not alone); that the ledger result is independent of how ground truth was made.

## Honest limitations that must appear
One generator model (Gemma 4 31B, remote Ollama cloud); Qwen (HTTP 401), other cloud models (HTTP 410/402), Claude Haiku as an experimental agent and a local GPU LLM were BLOCKED or NOT TESTED, so Configurations B and C (heterogeneous models) were not run.
Agents are instructed (red-team role play with fictional framing), tool use is controller-mediated, and the ledger is written by the controller. Source texts are the researcher's own AI-assisted drafts and are common knowledge, which is why the no-source control exists. Only 5 replicates share the same source library; bootstrap is clustered but residual dependence remains. The embedding model tag is `embeddinggemma-2:740m` (it may differ from arXiv:2509.20354). STRICT-GAP was not applicable and not tested. ECE via Argon F35 was planned but not run. The 69-bot inventory shows 3 candidate tool modules, 0 LLM agents.
Local GPU: RTX 3050 Laptop 4 GB; only embeddings ran on it (mean utilisation 5%, VRAM peak 1.6 GB, max 60 C).

## Suggested structure for the 8-page report
Title, abstract (150-250 words), Introduction (problem, three targets, contributions), Related work (use only references marked VERIFIED or PARTIAL in
`01_SOURCE_AUDIT/LITERATURE_CANDIDATES.md`; verify the rest manually), Methods (testbed, scenarios, ground truth, monitors, formulas, ledger, calibration, statistics),
Results (Figures 2, 3, 6; Tables from TABLES.md), Discussion and limitations, Conclusion, References, Appendix (formulas, Tracks 1-3 supporting tests,
preexisting vs sprint work, limitations and dual-use, LLM usage statement).
Dual-use: the copy scenarios instruct a model to misrepresent provenance in a sandbox with fictional framing; the findings could also help evaders learn which signals monitors miss.

## Supporting tests (Tracks 1-3), numbers from `05_EXPERIMENTS/`
Track 1: sandbox blocked 18/18 path-traversal attempts (0 leaks; an unprotected open leaks 11/18), 13/13 denials logged, ledger chain valid; formula pipeline exact reproduction 100%; LLM exact-output agreement 30% at temperature 0 and 0% at temperature 0.7 with a fixed seed, semantic agreement (cosine > 0.99) 100% in both; embedding batch 64 is 12x faster than batch 4.
Track 3: duplicate-source identity by body hash precision 1.0, recall 1.0 (44 twin pairs); hash chain detects edit, deletion and reordering 100%, tail truncation 0% unless the head hash is anchored externally (100% then); identity by internal id 100% vs by display name 0% in the simulated rename-collision test (a harness sanity check, not a finding); ledger chain completeness hides the cover story (COPY_COVER completeness = 1.0), only message events reveal it.
Track 2: see `05_EXPERIMENTS/track2_networks_tls/t2_summary.json` and `FINAL_ACCEPTANCE_REPORT.md` (results appended when finished).
