"""Runs ONLY the domain-disjoint transfer step of evaluate_v2.main (same code path as lines 450-455 of evaluate_v2.py), after the full evaluation
finished all other outputs but crashed at `import corpus` because the main project's src folder was not on sys.path.
evaluate_v2.py is under the stage-2 lock and is NOT modified; this wrapper only fixes the import path.
Usage: run_transfer_only.py <test_arm_tag> <fit_arm_tag> [--llm-monitors tp:qwen3.8-flash]"""
import argparse
import os
import sys

os.environ.setdefault("SWARM_DATASET", "tls")      # the retest corpus; corpus.py reads this at import time (default would be the synthetic corpus)
HERE = os.path.dirname(os.path.abspath(__file__))
RT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(RT), "src"))
import evaluate_v2 as E  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tag")
    ap.add_argument("fit")
    ap.add_argument("--llm-monitors", default="tp:qwen3.8-flash")
    a = ap.parse_args()
    llm_models = [m for m in a.llm_monitors.split(",") if m]
    reps, _ = E.load_arm(a.tag)
    fit_reps, _ = E.load_arm(a.fit)
    specs = E.build_specs(llm_models)
    names = ["F2 embedding cosine", "F9b ensemble + source checks", "F11x candidate ensemble", "H8 tri-state [comm_hidden]", "H8 tri-state [half_mcar]",
             "F10 ensemble + ledger [comm_hidden]", "F10 ensemble + ledger [half_mcar]", "H1 E_sup", "H3 S_disguise [claim_level]"] + \
            ["F0b LLM report-only [%s]" % m for m in llm_models] + ["D LLM with sources [%s]" % m for m in llm_models]
    out = E.transfer(fit_reps, reps, specs, names, a.tag)
    E.write_csv(os.path.join(RT, "results", a.tag, "transfer_from_%s.csv" % a.fit), out)
    print("transfer done %s <- %s: %d rows" % (a.tag, a.fit, len(out)), flush=True)


if __name__ == "__main__":
    main()
