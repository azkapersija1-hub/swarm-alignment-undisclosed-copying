# SWARM ALIGNMENT 2026 - FINAL EVIDENCE PACKAGE

Project: "Trust the Report or Check the Artifact? Formula-Augmented Oversight of Evidence Provenance in Multi-Agent Systems"
Event: Apart Research Swarm Alignment Hackathon, 6-8 Nov 2026 (main track: Track 4; supporting tests for Tracks 1-3).
Researcher: Mochamad Azmi Rizkulloh.

## What this is
A controlled study with REAL LLM agents (Gemma 4 31B, remote Ollama cloud) writing reports from the researcher's own TLS course materials
(definition and explanation texts). The controller builds scenarios with known ground truth (independent, honest twins, near-duplicates,
shared-with-attribution, copy variants, no-source control). Monitors compare reports, artifacts, frozen research formulas
(STP, STP-AR, MOI, RCC-v3.3, Argon F42/F44), a hash-chained provenance ledger, and an LLM monitor. Metrics are computed by an independent engine.

## Folder map
| Folder | Contents |
|---|---|
| `00_README_AND_MANIFEST` | this file, `NARRATION_BRIEF_FOR_GPT.md` (read first), `EXECUTION_MANIFEST.md`, `PREEXISTING_WORK.md`, `SPRINT_CONTRIBUTIONS.md` |
| `01_SOURCE_AUDIT` | `BOT_REGISTRY.csv`, `FORMULA_REGISTRY.csv`, `MODEL_REGISTRY.json`, `SOURCE_INVENTORY.csv`, `LITERATURE_CANDIDATES.md` (verification status per reference) |
| `02_GPU_ENVIRONMENT` | `HARDWARE_AUDIT.json`, `GPU_EXECUTION_REPORT.md` |
| `03_FORMULA_ENGINE` | frozen formula sources + SHA-256 (PREEXISTING) |
| `05_EXPERIMENTS` | Track 1 / 2 / 3 outputs (`*_tls` = TLS dataset; folders without suffix = preliminary fictional-corpus runs) |
| `06_RAW_RESULTS` | agent runs (`llm_runs_tls`), monitor scores (`formula_runs_tls`), logs, GPU samples |
| `07_STATISTICAL_ANALYSIS` | `metrics_tls/` (main results, per-replicate, per-type, pooled predictions) |
| `08_VISUAL_EVIDENCE` | `figures_tls/`, `video_documentation/` (process replay and performance replay videos) |
| `09_TESTS_AND_VERIFICATION` | unit tests, `FINAL_ACCEPTANCE_REPORT.md` |
| `10_REPORT_ENGLISH`, `11_REPORT_INDONESIAN`, `12_APART_SUBMISSION` | report drafts and submission checklist |
| `src/` | all sprint code (Python) | `data/` | frozen corpora with SHA-256 |
| `prior_experiment_swarm_provenance/` | the earlier scripted-bot experiment and its audit (pilot, E0) |

## Reproduce (needs Ollama + models; not included)
```
set SWARM_DATASET=tls
py -3.12 -I -B -X utf8 src/build_tls_sources.py 150
py -3.12 -I -B -X utf8 src/run_generation.py gemma4:31b-cloud 5 20261107
py -3.12 -I -B -X utf8 src/compute_scores.py 06_RAW_RESULTS/llm_runs_tls
py -3.12 -I -B -X utf8 src/evaluate.py
py -3.12 -I -B -X utf8 src/make_figures.py
```
Unit tests (no network): `py -3.12 -I -B -X utf8 -m unittest discover -s 09_TESTS_AND_VERIFICATION/unit_tests -p "test_swarm.py"`

## Honest limits (short)
One generator model (Gemma 4, remote); agents are instructed (red-team simulation), tool use is controller-mediated, ledger is written by the controller;
embeddings run on the local GPU (RTX 3050 Laptop, 4 GB) but LLM calls do not; Qwen, other cloud models and Claude Haiku (as agent) were BLOCKED or NOT TESTED;
STRICT-GAP not applicable; text sources are the researcher's own AI-assisted drafts and many facts are common knowledge (a no-source control measures this).
