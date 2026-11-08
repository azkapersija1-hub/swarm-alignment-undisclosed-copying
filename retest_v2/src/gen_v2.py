"""Generate retest-v2 scenario runs.
Usage: py -3.12 -B -X utf8 gen_v2.py --tag gemma_homog --model-a gemma4:31b-cloud --model-b gemma4:31b-cloud --reps 5 --seed0 20261201 [--pilot]
Token Plan models use the 'tp:' prefix and read the key from TOKENPLAN_KEY_FILE (never printed)."""
import argparse
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import controller_v2 as V  # noqa: E402

RUNS = os.path.join(os.path.dirname(HERE), "runs")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True)
    ap.add_argument("--model-a", required=True)
    ap.add_argument("--model-b", default=None)
    ap.add_argument("--reps", type=int, default=1)
    ap.add_argument("--seed0", type=int, required=True)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--adapt-n", type=int, default=10)
    ap.add_argument("--pilot", action="store_true", help="1 scenario per type per split, 1 replicate, separate folder")
    a = ap.parse_args()
    model_b = a.model_b or a.model_a
    outdir = os.path.join(RUNS, ("pilot_" if a.pilot else "") + a.tag)
    os.makedirs(outdir, exist_ok=True)
    per_split = {k: 1 for k in V.per_split_v2(1)} if a.pilot else V.per_split_v2(a.adapt_n)
    reps = 1 if a.pilot else a.reps
    t0 = time.time()
    for r in range(reps):
        path = os.path.join(outdir, "rep%d_%s.jsonl" % (r, a.tag))
        if os.path.isfile(path):
            print("skip existing", path, flush=True)
            continue
        V.run_all_v2(a.model_a, model_b, r, a.seed0 + r, path, workers=a.workers, per_split=per_split,
                     log=lambda *x: print("rep", r, *x, "t=%.0fs" % (time.time() - t0), flush=True))
    print("done %.0fs" % (time.time() - t0), flush=True)


if __name__ == "__main__":
    main()
