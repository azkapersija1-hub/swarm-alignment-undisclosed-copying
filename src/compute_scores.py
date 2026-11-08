"""Compute all monitor scores for every record of a replicate file (GPU embeddings via Ollama + frozen formulas + LLM monitors).
Usage: py -3.12 -I -B -X utf8 compute_scores.py <runs_glob_dir> [llm_monitor_model]"""
import concurrent.futures as cf
import glob
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import corpus  # noqa: E402
import monitors as M  # noqa: E402
from hardware_probe import GpuSampler  # noqa: E402

ROOT = os.path.dirname(HERE)
LLM_MODEL = sys.argv[2] if len(sys.argv) > 2 else "gemma4:31b-cloud"
MODES = ["full", "comm_hidden", "half", "none"]


def main():
    runs = sorted(glob.glob(os.path.join(sys.argv[1], "rep*_*.jsonl")))
    catalog, _ = corpus.load_catalog()
    out_dir = os.path.join(ROOT, "06_RAW_RESULTS", "formula_runs" + corpus.SUFFIX)
    os.makedirs(out_dir, exist_ok=True)
    sampler = GpuSampler(os.path.join(ROOT, "06_RAW_RESULTS", "gpu_samples_scoring%s.jsonl" % corpus.SUFFIX), period=5).start()
    emb = M.EmbCache()
    t0 = time.time()
    for path in runs:
        outp = os.path.join(out_dir, os.path.basename(path).replace(".jsonl", "_scores.jsonl"))
        if os.path.isfile(outp):
            print("skip", outp)
            continue
        recs = [json.loads(line) for line in open(path, encoding="utf-8")]
        texts = [t for r in recs for t in M.texts_needed(r, catalog)]
        n = emb.fill(texts)
        print(os.path.basename(path), len(recs), "records;", n, "new embeddings; t=%.0fs" % (time.time() - t0), flush=True)
        rows = []
        for r in recs:
            sc = r["scenario"]
            seed = int(sc["scenario_id"].replace("-", "").encode().hex()[:8], 16) % (2 ** 31)
            tc = time.perf_counter()
            feats = M.content_features(r, catalog, emb, seed)
            feats["t_content_s"] = time.perf_counter() - tc
            cited_b = r["report_b"]["cited_sources"]
            led = {m: M.ledger_features(r["ledger"], m, sc["scenario_id"], cited_b) for m in MODES}
            rows.append({"scenario_id": sc["scenario_id"], "replicate": r["replicate"], "split": sc["split"], "type": sc["type"],
                         "cluster": sc["cluster"], "truth": sc["truth"], "realized_overlap": r["realized_overlap"],
                         "feats": feats, "ledger": led})
        print("content+ledger done; t=%.0fs" % (time.time() - t0), flush=True)

        def llm_pair(i):
            r = recs[i]
            a = M.llm_monitor(r, catalog, LLM_MODEL, with_sources=False, seed=i)
            b = M.llm_monitor(r, catalog, LLM_MODEL, with_sources=True, seed=i)
            return a, b
        with cf.ThreadPoolExecutor(max_workers=4) as ex:
            for row, (a, b) in zip(rows, ex.map(llm_pair, range(len(recs)))):
                row["llm_report_only"], row["llm_with_sources"] = a, b
        with open(outp, "w", encoding="utf-8") as fh:
            for row in rows:
                fh.write(json.dumps(row) + "\n")
        print("wrote", outp, "t=%.0fs" % (time.time() - t0), flush=True)
    sampler.stop()
    print("GPU max temp", sampler.max_temp, "samples", sampler.n)


if __name__ == "__main__":
    main()
