"""Compute every monitor input for each record of a run folder (local GPU embeddings, frozen formulas, candidate formulas, LLM monitors).
Usage: py -3.12 -B -X utf8 score_v2.py <tag> [--monitors gemma4:31b-cloud,tp:qwen3.8-flash] [--runs-dir runs] [--workers 6]
Output: scores/<tag>/repN_<tag>_scores.jsonl (failed scenarios are kept as {"failed": true} rows so rates can be reported)."""
import argparse
import concurrent.futures as cf
import glob
import hashlib
import json
import math
import os
import shutil
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
RT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import features_v2 as F  # noqa: E402
import corpus  # noqa: E402
import llm  # noqa: E402
import monitors as M  # noqa: E402

V1_ROOT = os.path.dirname(M.HERE)
ORIG_CACHE = M.EMB_PATH
NEW_CACHE = os.path.join(RT, "cache", "emb_cache_v2.pkl")
NAN = float("nan")


def copy_u(rec):
    return int(rec["scenario"]["truth"]["copying_occurred"] == 1 and rec["scenario"]["type"] != "SHARED_OK")


def llm_row(rec, catalog, model, seed):
    out = {}
    for name, with_src in (("report_only", False), ("with_sources", True)):
        o = None
        for attempt in range(8):                # transient server errors (HTTP 429) are retried with growing pauses
            try:
                o = M.llm_monitor(rec, catalog, model, with_sources=with_src, seed=seed)
                break
            except RuntimeError:
                time.sleep(15 * (attempt + 1))
        if o is None:                           # still failing: recorded as NaN with an error flag, never imputed
            o = {"p_copying": NAN, "p_nonindependent": NAN, "p_false_provenance": NAN, "llm_parse_fail": 1.0, "llm_error": 1.0}
        elif o.get("llm_parse_fail"):
            o = {"p_copying": NAN, "p_nonindependent": NAN, "p_false_provenance": NAN, "llm_parse_fail": 1.0}
        out[name] = o
    return out


def score_file(path, outp, catalog, emb, monitors, workers, expected=None):
    with open(path, encoding="utf-8") as fh:
        raw = [json.loads(line) for line in fh]
    if expected is not None and len(raw) != expected:       # a truncated run file must stop the pipeline, never be scored silently
        raise SystemExit("INTEGRITY: %s has %d records, expected %d" % (path, len(raw), expected))
    recs = [r for r in raw if not r.get("failed")]
    fails = [r for r in raw if r.get("failed")]
    texts = [t for r in recs for t in F.texts_needed_v2(r, catalog)]
    n_new = emb.fill(texts)
    truth = {r["scenario"]["scenario_id"]: (r["scenario"]["split"], r["scenario"]["type"], copy_u(r)) for r in recs}
    calib_obj = F.fit_calibration_objects(recs, truth, emb)
    rows = []
    for r in recs:
        sc = r["scenario"]
        seed = int(hashlib.sha256(("%s|%s" % (sc["scenario_id"], r["replicate"])).encode()).hexdigest()[:8], 16) % (2 ** 31)    # v1 hex()[:8] gave one seed per split
        feats = M.content_features(r, catalog, emb, seed)
        cand = F.candidate_features(r, catalog, emb, feats, calib_obj)
        legacy, h8 = F.ledger_block(r, catalog)
        rows.append({"scenario_id": sc["scenario_id"], "replicate": r["replicate"], "split": sc["split"], "type": sc["type"], "cluster": sc["cluster"],
                     "truth": sc["truth"], "copy_u": copy_u(r), "realized_overlap": r["realized_overlap"], "model": r.get("model"),
                     "model_b": r.get("model_b"), "feats": feats, "cand": cand, "ledger_legacy": legacy, "ledger_h8": h8,
                     "surrogate_trace": r.get("surrogate_trace")})

    def one(i):
        return {m: llm_row(recs[i], catalog, m, i) for m in monitors}
    with cf.ThreadPoolExecutor(max_workers=workers) as ex:
        for row, l in zip(rows, ex.map(one, range(len(recs)))):
            row["llm"] = l
    tmp = outp + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, allow_nan=True) + "\n")
        for f in fails:
            fh.write(json.dumps({"failed": True, "scenario_id": f["scenario"]["scenario_id"], "type": f["scenario"]["type"], "split": f["scenario"]["split"],
                                 "replicate": f["replicate"], "error": f.get("error")}) + "\n")
    os.replace(tmp, outp)
    return len(rows), len(fails), n_new


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tag")
    ap.add_argument("--monitors", default="gemma4:31b-cloud,tp:qwen3.8-flash")
    ap.add_argument("--runs-dir", default=os.path.join(RT, "runs"))
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--expected", type=int, default=244, help="records per replicate file (244 for v2 runs, 164 for the original study)")
    ap.add_argument("--cache", default=NEW_CACHE, help="embedding cache file; use a separate file per concurrent process")
    a = ap.parse_args()
    os.makedirs(os.path.dirname(NEW_CACHE), exist_ok=True)
    if not os.path.isfile(NEW_CACHE) and os.path.isfile(ORIG_CACHE):
        shutil.copy(ORIG_CACHE, NEW_CACHE)        # reuse embeddings of the original study texts; new texts are added
    if a.cache != NEW_CACHE and not os.path.isfile(a.cache):
        shutil.copy(NEW_CACHE, a.cache)
    catalog, _ = corpus.load_catalog()
    emb = M.EmbCache(a.cache)
    outdir = os.path.join(RT, "scores", a.tag)
    os.makedirs(outdir, exist_ok=True)
    monitors = [m for m in a.monitors.split(",") if m]
    t0 = time.time()
    for path in sorted(glob.glob(os.path.join(a.runs_dir, a.tag, "rep*_*.jsonl"))):
        outp = os.path.join(outdir, os.path.basename(path).replace(".jsonl", "_scores.jsonl"))
        if os.path.isfile(outp):
            print("skip", outp, flush=True)
            continue
        n, nf, nn = score_file(path, outp, catalog, emb, monitors, a.workers, a.expected)
        print("%s: %d scored, %d failed rows, %d new embeddings, t=%.0fs" % (os.path.basename(path), n, nf, nn, time.time() - t0), flush=True)


if __name__ == "__main__":
    main()
