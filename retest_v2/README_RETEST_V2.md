# retest_v2: pre-registered re-test (D1-D3) of formula monitors for undisclosed copying between LLM agents

Start here. Written 2026-11-08. Everything below is reproducible from the files in this folder except the LLM calls (agents and the Qwen monitor), whose raw outputs are stored in `runs/` and `scores/`.

## What is where
| folder | content |
|---|---|
| `prereg/` | candidate formulas, hypotheses and falsifiers, declarations (stage 1 and 2), `DEVIATIONS.md` (items 1-12), SHA-256 locks |
| `src/` | controller, generator, features, scoring, statistics, evaluation, tracks, figures, videos, report builders |
| `tests/` | 35 unit tests |
| `runs/`, `scores/` | agent outputs and per-record monitor inputs of the five arms |
| `results/<arm>/` | results_main.csv, results_per_type.csv, primary_comparisons.json, falsifiers.json, audit.json, transfer CSVs |
| `results/figures/`, `results/tracks/` | figures (fig0 to fig6) and track results |
| `report/` | `REPORT_EN/ID` (full results report, .md and .docx), `SUBMISSION_EN` (competition draft, .md and .docx) |
| `videos/` | process replay, performance replay, 3-minute demo |
| `haiku_monitor/` | exploratory blind Haiku monitor (97 items), not pre-registered |
| `chatbot_figures/` | real-data CSV and prompts used for chatbot-made figures |

Arms: D1 `gemma_homog` (5 replicates, confirmatory main arm), D2 `qwen_homog`, `deepseek_homog` (3 each), D3 `het_gemma_qwen`, `het_gemma_deepseek` (2 each). The older 820-scenario study is exploratory and contaminated (`results/D0_exploratory_contaminated`).

## Honest status
- Primary comparison passed in 3 of 5 arms (D1, D2-DeepSeek, D3 Gemma>Qwen). F11x beats cosine in every arm; its gain over F9b is small.
- Hypotheses H1, H6, H9 held in all arms; H2, H7, H8, H10 failed in all arms; H3, H5, H4 varied.
- Targets A and C have identical labels in this design.
- LLM monitor is Qwen only: the Gemma cloud quota ended on 2026-11-08 (DEVIATIONS item 12). Track 1/2 were run with Qwen and DeepSeek only.
- Not claimed: spontaneous deception, other corpora or embedding models, real-time oversight.
- Pre-existing work is listed in `../00_README_AND_MANIFEST/PREEXISTING_WORK.md`; sprint work in `SPRINT_CONTRIBUTIONS.md`.

## Reproduce (Windows, Python 3.12)
Needs a local Ollama with `embeddinggemma-2:740m`, and for agents/monitors an OpenAI-compatible endpoint key supplied through the environment variable `TOKENPLAN_KEY_FILE` (a path to a file holding the key; the key is NOT in this package) and, for Gemma, an Ollama cloud account. Set `SWARM_DATASET=tls`.
```
py -3.12 -B -X utf8 -m unittest discover -s tests -p "test_*.py"          (run inside tests/)
py -3.12 -B -X utf8 gen_v2.py --tag <arm> --model-a <m> --model-b <m> --reps N --seed0 S
py -3.12 -B -X utf8 score_v2.py <arm> --monitors tp:qwen3.8-flash --expected 244 --cache ..\cache\c_<arm>.pkl
py -3.12 -B -X utf8 evaluate_v2.py <arm> --boot 1000 --refit-boot 500 --llm-monitors tp:qwen3.8-flash [--transfer-from gemma_homog]
py -3.12 -B -X utf8 run_transfer_only.py <arm> gemma_homog                   (only if the transfer step of evaluate_v2 fails on the import path)
py -3.12 -B -X utf8 diagnostics_v2.py gemma_homog
py -3.12 -B -X utf8 make_figures_v2.py ; make_concept_figures.py ; make_arch3d_color.py ; make_scatter3d.py
py -3.12 -B -X utf8 animate_retest.py process|performance --tag gemma_homog ; make_demo_video.py
py -3.12 -B -X utf8 build_reports.py ..\report\REPORT_EN.tpl.md ..\report\REPORT_EN.md ; md_to_docx.py in.md out.docx
py -3.12 -B -X utf8 lock.py verify STAGE1 ; lock.py verify STAGE2
```
`cache/` (embedding caches, about 900 MB) is not included in the zip; it is rebuilt by scoring.
