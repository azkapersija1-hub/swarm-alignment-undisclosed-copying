# SPRINT CONTRIBUTIONS (2026-11-06 to 2026-11-08)

Each item points to evidence (file, log or hash). Nothing here depends on file dates.

| Contribution | Evidence |
|---|---|
| Audit of the scripted-bot experiment: claim verification, `hash()` non-determinism found and fixed, honest-twin negative control, cluster bootstrap | `27_Swarm_Provenance/audit/` (AUDIT_REPORT.md, CHANGELOG.md, TEST_REPORT.md) |
| Experiment controller, scenario plan, ground-truth rules (3 separate targets) | `src/controller.py`, `src/corpus.py`; plan determinism tested in `09_TESTS_AND_VERIFICATION/unit_tests/test_swarm.py` |
| Real LLM-agent runs (Gemma 4 31B, remote) on TLS materials: 5 replicates x 164 scenarios | `06_RAW_RESULTS/llm_runs_tls/*.jsonl`, `generation_tls.log` |
| Provenance ledger with SHA-256 hash chain; tamper tests | `src/ledger.py`, `05_EXPERIMENTS/track3_infrastructure_tls/` |
| Monitors: report-only, artifact, formula (STP/STP-AR/MOI/RCC/Argon), ledger, LLM-with-sources, hybrid; visibility modes | `src/monitors.py`, `06_RAW_RESULTS/formula_runs_tls/*.jsonl` |
| Independent metrics engine (confusion, MCC, AUROC/AUPRC, Brier, BSS, cluster bootstrap) | `src/evaluate.py`, `07_STATISTICAL_ANALYSIS/metrics_tls/` |
| Track 1 sandbox and reproducibility tests; Track 2 propagation; Track 3 identity/duplicate/attribution/tamper | `05_EXPERIMENTS/track*_tls/` |
| Literature search with verification status per item | `01_SOURCE_AUDIT/LITERATURE_CANDIDATES.md` |
| Registries (bots, formulas, models) | `01_SOURCE_AUDIT/` |
| Reports (English full, Indonesian full, official submission) | `10_REPORT_ENGLISH/`, `11_REPORT_INDONESIAN/`, `12_APART_SUBMISSION/` |
