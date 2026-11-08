# FINAL ACCEPTANCE REPORT

Status legend: PASS, PASS WITH LIMITATIONS, FAIL, NOT TESTED, BLOCKED. A PASS is given only where execution evidence exists.

## Technical execution
| Check | Status | Evidence / note |
|---|---|---|
| At least one LLM executed | PASS | Gemma 4 31B, 820 scenarios x 2 agents; `06_RAW_RESULTS/llm_runs_tls/`, `generation_tls.log` |
| Runtime evidence | PASS | per-call seconds, tokens, attempts stored in every record; GPU samples in `06_RAW_RESULTS/gpu_samples_*` |
| GPU used on appropriate operations | PASS WITH LIMITATIONS | only embeddings run on the local GPU (peak 1.6 GB VRAM, 89% utilisation); LLMs are remote; no local generative model |
| Agents exchanged information | PASS WITH LIMITATIONS | messages are controller-mediated (A's report passed to B in copy/shared scenarios); agents did not choose recipients |
| Formulas called as functions | PASS | frozen STP, STP-AR, MOI, RCC-v3.3 and Argon F42/F44 executed on every scenario |
| Results stored | PASS | raw JSONL, scores, metrics CSV/JSON, figures |

## Experimental validity
| Check | Status | Evidence / note |
|---|---|---|
| Baseline valid | PASS | F0a (trust cited sources), F0b (LLM reads reports), lexical and cosine baselines |
| Negative controls | PASS | honest twins, near-duplicates, same-topic independent, no-source control |
| Ground truth independent of monitors | PASS WITH LIMITATIONS | assigned by the controller's design; compliance verified by number reuse only for the subset with numbers (sensitivity analysis); ledger and labels share an author (controller) |
| Copying vs non-independence vs false provenance separated | PASS | three targets with separate labels and results |
| Thresholds calibrated without test leakage | PASS | calibration and test use disjoint topic domains; unit test `test_calib_and_test_domains_disjoint` |
| Formula ablation available | PASS | F1-F10 in `TABLES.md` (STRICT-GAP not applicable; ECE via F35 not run) |
| Negative results kept | PASS | single formulas near chance (AUROC 0.48-0.65) reported prominently |
| Heterogeneous / mixed-provider model comparison | BLOCKED | Qwen HTTP 401; other cloud tags HTTP 410/402; Haiku NOT TESTED as agent; no local LLM |

## Statistical integrity
| Check | Status | Evidence / note |
|---|---|---|
| Confusion matrix reproducible | PASS | recomputed by `evaluate.py` from raw scores; unit test of metric definitions |
| Brier from actual probabilities | PASS | logistic probabilities fitted on calibration; reference = calibration prevalence |
| Numerator/denominator for each percentage | PASS | counts tp/fp/tn/fn stored in `results_main.csv` |
| Uncertainty accounts for dependence | PASS WITH LIMITATIONS | cluster bootstrap by (replicate, source of A); replicates share one source library |
| Figures match raw results | PASS | figures generated only from CSV/JSON by `make_figures.py` |
| ECE / calibration via Argon F35 | NOT TESTED | planned, not run |
| Hypothesis tests | NOT TESTED | none claimed; all results are descriptive |

## Tracks
| Track | Status | Note |
|---|---|---|
| Track 4 (main) | PASS WITH LIMITATIONS | see above |
| Track 3 | PASS WITH LIMITATIONS | identity test is a harness sanity check; no cryptographic authentication; tail truncation undetected without an anchored head |
| Track 1 | PASS WITH LIMITATIONS | sandbox 18/18 blocked; LLM exact-output reproducibility low (30% at T=0) |
| Track 2 | PASS WITH LIMITATIONS | no propagation observed in any topology (ceiling effect); does not discriminate topologies; model heterogeneity BLOCKED |

## Submission compliance
| Check | Status | Note |
|---|---|---|
| Official Apart template used | PASS | `12_APART_SUBMISSION/*.docx` built on the supplied template |
| Main text <= 8 pages | PASS | 6 pages of body; 9 pages in total with references and appendices (Word render) |
| Abstract 150-250 words | PASS | 201 words |
| Author and affiliation | PASS WITH LIMITATIONS | name filled; affiliation placeholder |
| Required appendix (Limitations and Dual-Use / Ethical) | PASS | Appendix A |
| Preexisting work disclosed | PASS | Appendix C, `PREEXISTING_WORK.md` |
| References verified | PASS WITH LIMITATIONS | items marked VERIFIED/PARTIAL only; Brier 1950 and Platt 1999 flagged with a dagger; author must open them |
| Use of Claude and other LLMs declared | PASS WITH LIMITATIONS | LLM Usage Statement drafted; author must confirm |
| Final files open | PASS | docx opened and exported to PDF through Word |
| Repository link, author contributions | NOT TESTED | placeholders for the author |
| Videos | see `08_VISUAL_EVIDENCE/video_documentation/` | generated from real data; not screen recordings |
