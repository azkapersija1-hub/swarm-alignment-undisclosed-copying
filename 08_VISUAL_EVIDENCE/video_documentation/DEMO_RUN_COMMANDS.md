# DEMO RUN COMMANDS (run from the package root; needs Python 3.12, numpy, scikit-learn, matplotlib, ffmpeg)
```
set SWARM_DATASET=tls
set SWARM_METRICS_TAG=_alllabels
py -3.12 -I -B -X utf8 src/make_tables.py
py -3.12 -I -B -X utf8 src/make_figures.py
py -3.12 -I -B -X utf8 src/animate_performance.py fast
py -3.12 -I -B -X utf8 src/animate_process.py fast
py -3.12 -I -B -X utf8 -m unittest discover -s 09_TESTS_AND_VERIFICATION/unit_tests -p "test_swarm.py" -v
```
Drop the word `fast` for the full-length videos. Generating new LLM runs requires Ollama and access to the remote model (`src/run_generation.py`).
