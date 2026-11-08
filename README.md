# Cosine Is Not Enough: detecting undisclosed copying between LLM agents (Swarm Alignment Hackathon 2026, Track 4)

Controlled test bed and **pre-registered re-test** of monitors that try to detect an LLM agent copying another agent's report while claiming independent evidence. Code, data, results, reports and videos for the Apart Research Swarm Alignment Hackathon (6 to 8 November 2026).

**Start here:** `retest_v2/README_RETEST_V2.md` (map of files, honest status, reproduction commands) and `retest_v2/report/SUBMISSION_EN.pdf` (competition draft) or `REPORT_EN.pdf` (full results report; Indonesian version `REPORT_ID.pdf`).

## What was found (confirmatory arms D1 to D3, about 3,650 scored scenarios, 5 arms, 3 agent models)
- Plain embedding cosine is close to chance for undisclosed copying (AUROC 0.49 to 0.63).
- An ensemble of source-aware and contrast features (F11x) reaches AUROC 0.88 to 0.97 and beats cosine in every arm, but its gain over a strong in-house baseline (F9b) is small (0.01 to 0.05) and passes the pre-declared strict gate in **3 of 5 arms**.
- Of ten pre-registered candidate hypotheses, 3 held in every arm, 4 failed in every arm, 3 varied.
- An anchored log adds about 0.06 AUROC; a spoofed log removes it. Lexical injection and split citation lower detection. Fits do not transfer well across agent models (AUROC 0.71 to 0.78).

## Limits you must read
Same 109 documents in every arm; copying is **instructed**, not spontaneous; the log is written by the controller; one embedding model; the LLM monitor is Qwen only (the Gemma cloud quota ended during scoring, `retest_v2/prereg/DEVIATIONS.md` item 12); targets A and C have identical labels in this design; results are **offline audits**, not real-time oversight. The earlier 820-scenario study (`results/D0_exploratory_contaminated`) is exploratory and contaminated and is not used for claims.

## Work before the sprint (preexisting, not claimed as sprint work)
| item | where |
|---|---|
| STP, STP-AR, MOI and RCC-v3.3 formulas | `03_FORMULA_ENGINE/source/` |
| Older formula library (Argon F42/F44 adaptor), 69-bot registry | referenced only, **not** included |
| Course documents used as source texts (written by the author with AI-assisted drafting) | `data/` |
| Local embedding runtime and model `embeddinggemma-2:740m` | not included |
| Scripted-bot pilot "Swarm Provenance" (created on the first sprint day, reported as a pilot only) | `prior_experiment_swarm_provenance/` |

Everything else (controller, scenarios, ledger, monitors, metrics engine, candidate-feature composition F11x, the 820-scenario study, the pre-registered re-test D1 to D3, tracks 1 to 3, tests, figures, videos, reports) was built during the sprint. See `00_README_AND_MANIFEST/PREEXISTING_WORK.md` and `SPRINT_CONTRIBUTIONS.md`.

## Layout
| folder | content |
|---|---|
| `retest_v2/` | the pre-registered re-test (D1 to D3): code (`src/`), 35 tests (`tests/`), pre-registration and deviations (`prereg/`), agent runs and scores (`runs/`, `scores/`), results, figures, reports, videos |
| `src/`, `data/` | test-bed controller, corpus loader, monitors, ledger, metrics, source texts |
| `prior_experiment_swarm_provenance/` | pilot with scripted bots (no LLM) and its audit |
| `00_` to `13_` | the first study (820 scenarios) package: manifest, source audit, formula engine, experiments, raw results, statistics, visual evidence, reports (superseded, see notices) |

## Reproduce (Windows, Python 3.12)
Install `requirements.txt`, ffmpeg (for videos), a local Ollama with `embeddinggemma-2:740m`. Agent and LLM-monitor calls need your own API access: the code reads a key only from the file named by the environment variable `TOKENPLAN_KEY_FILE`; **no key is included**. Set `SWARM_DATASET=tls`. Commands: `retest_v2/README_RETEST_V2.md`. Pre-registration hashes can be verified with `py -3.12 retest_v2/src/lock.py verify STAGE1` and `STAGE2`. Embedding caches are not included and are rebuilt during scoring.

## Dual-use note
The adaptive arms show which edits lower detection (lexical injection, citation splitting) and the log tests show where hash chains fail. The test bed is synthetic and local, no attack code for real systems is released, and the findings point to defences (source-aware features, external anchors, per-model recalibration). Details: Appendix A of `retest_v2/report/SUBMISSION_EN.pdf`.

## AI-tools statement
AI assistants were used for code, a candidate-hypothesis analysis, figure code and drafting. The authors verified outputs against data and are responsible for all content.

## License
Code: **MIT** (`LICENSE`). Reports, figures, videos, data and generated texts: **CC BY 4.0**. Details and exceptions: `NOTICE.md`.
