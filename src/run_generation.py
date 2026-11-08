"""Run the LLM-agent scenarios for N replicates (distinct plan seeds and generation seeds) and sample the GPU.
Usage: py -3.12 -I -B -X utf8 run_generation.py <model> <n_replicates> [first_seed]"""
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import controller as C  # noqa: E402
import corpus  # noqa: E402
from hardware_probe import GpuSampler  # noqa: E402

ROOT = os.path.dirname(HERE)
model, n_rep = sys.argv[1], int(sys.argv[2])
first = int(sys.argv[3]) if len(sys.argv) > 3 else 20261107
tag = model.replace(":", "_").replace("/", "_")
outdir = os.path.join(ROOT, "06_RAW_RESULTS", "llm_runs" + corpus.SUFFIX)
os.makedirs(outdir, exist_ok=True)
sampler = GpuSampler(os.path.join(ROOT, "06_RAW_RESULTS", "gpu_samples_generation%s.jsonl" % corpus.SUFFIX), period=5).start()
t0 = time.time()
for r in range(n_rep):
    seed = first + r
    path = os.path.join(outdir, "rep%d_%s.jsonl" % (r, tag))
    if os.path.isfile(path):
        print("skip existing", path, flush=True)
        continue
    C.run_all(model, r, seed, path, workers=4, per_split=C.per_split_for_dataset(), log=lambda *a: print("rep", r, *a, "t=%.0fs" % (time.time() - t0), flush=True))
sampler.stop()
print("done", round(time.time() - t0), "s; max GPU temp", sampler.max_temp, flush=True)
