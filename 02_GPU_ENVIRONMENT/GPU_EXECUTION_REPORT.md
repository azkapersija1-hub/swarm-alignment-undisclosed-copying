# GPU EXECUTION REPORT

All figures come from `HARDWARE_AUDIT.json` and the sampler logs `06_RAW_RESULTS/gpu_samples_generation_tls.jsonl` and `gpu_samples_scoring_tls.jsonl` (nvidia-smi every 5 s).

| Item | Value |
|---|---|
| Device detected | NVIDIA GeForce RTX 3050 Laptop GPU, compute capability 8.6 (NOTE: the project brief assumed an RTX 2060; the measured device is the 3050) |
| VRAM | 4096 MiB total |
| Driver / CUDA | driver 610.74; PyTorch 2.6.0+cu124 reports `cuda_available = True` |
| Ollama | 0.40.14 |
| RAM | 15.8 GB total, about 2 GB available at start (memory pressure from other applications) |
| Python | 3.12.10 (pure standard library plus numpy, scikit-learn, matplotlib) |

## What actually ran where
| Workload | Backend | Evidence |
|---|---|---|
| Sentence embeddings (`embeddinggemma-2:740m`, Q8_0, 768-d) | **local GPU** via Ollama | VRAM rose to about 1.6 GB; utilisation peaks 80-89%; see samples |
| LLM agents, LLM monitors, source generation (`gemma4:31b-cloud`) | **remote (Ollama cloud)** - NOT the local GPU | model tag ends in `-cloud`; local VRAM unchanged during generation (mean utilisation 2.4%) |
| Formulas (STP, STP-AR, MOI, RCC-v3.3, Argon), ledger, metrics, bootstrap | **CPU** (numpy, small matrices; GPU transfer would cost more than it saves) | |
| Video rendering | CPU (matplotlib + ffmpeg libx264) | |

The pipeline is therefore NOT fully GPU-executed. Only the embedding step uses the local GPU. A 31B model cannot be loaded in 4 GB of VRAM; no local generative model is installed and none was downloaded without the researcher's permission.

## Measurements
| Metric | Generation phase | Scoring phase |
|---|---|---|
| Samples | 224 (18.9 min) | 416 (35.1 min) |
| GPU utilisation mean / max | 2.4% / 80% | 5.0% / 89% |
| VRAM max | 1610 MiB | 1610 MiB |
| Temperature max | 60 C | 60 C |
| Thermal events | none (limit configured at 82 C; never reached) | none |

Embedding throughput test (128 short texts, `t1_resources.json`): batch 4 = 72.5 s; batch 16 = 19.4 s; batch 64 = 6.0 s (the first setting includes warm-up; larger batches are clearly more efficient on this GPU).

## Fallback decisions
- No inference was silently moved to the CPU. Remote models were used for generative work and are labelled as remote throughout.
- CPU was not loaded by long inference: CPU work was light numerical code and rendering; video rendering was the heaviest CPU task.
- No thermal protection was disabled.
