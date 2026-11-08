# REPRODUCTION GUIDE
Level 1 (no tools needed): verify numbers from `07_STATISTICAL_ANALYSIS/metrics_tls_alllabels/results_main.csv` and `pooled_predictions.json`; re-run `src/evaluate.py` on `06_RAW_RESULTS/formula_runs_tls/*.jsonl`.
Level 2 (Python only): run the 17 unit tests (`09_TESTS_AND_VERIFICATION/unit_tests/test_swarm.py`) with synthetic fixtures.
Level 3 (Ollama + remote model): rerun `src/run_generation.py`, `src/compute_scores.py`, `src/evaluate.py`. LLM outputs will not be bit-identical (0% exact agreement at temperature 0.7 with a fixed seed, 30% at temperature 0 in our test); frozen formulas and metrics are exactly reproducible given the same records.
These levels are not equivalent. The 184-book corpus of the earlier pilot is not distributed.
