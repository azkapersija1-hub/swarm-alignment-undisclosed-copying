"""Exploratory diagnostics (descriptive, NOT confirmatory): why ARG-H8 behaves as it does, which added features carry F11x, and which attack arms evade which monitor.
Usage: diagnostics_v2.py <tag> [--out name]"""
import argparse
import csv
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
RT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import evaluate_v2 as E  # noqa: E402
import stats_v2 as S  # noqa: E402


def h8_component_table(reps):
    rows = [r for v in reps.values() for r in v]
    out = []
    for typ in sorted({r["type"] for r in rows}):
        rs = [r for r in rows if r["type"] == typ]
        for mode in ("full_anchored", "none"):
            cs = [S.h8_components(r, mode) for r in rs]
            out.append({"type": typ, "mode": mode, "n": len(rs), "mean_s_prov": float(np.mean([c["s_prov"] for c in cs])), "mean_r_reuse": float(np.mean([c["r_reuse"] for c in cs])),
                        "mean_s_disguise_clip": float(np.mean([c["s_disg_clip"] for c in cs])), "share_has_src": float(np.mean([c["has_src"] for c in cs])),
                        "share_ic1": float(np.mean([c["ic"] for c in cs])), "share_s_prov_ge_0.999": float(np.mean([c["s_prov"] >= 0.999 for c in cs]))})
    return out


def f11x_ablation(reps, target="A_primary"):
    base = S.f9b_design
    add = {"F9b (baseline)": lambda r: [],
           "F9b + E_sup,has_src": lambda r: [0.0 if r["cand"]["h1"]["score"] != r["cand"]["h1"]["score"] else r["cand"]["h1"]["score"], float(r["cand"]["h8in"]["has_src"])],
           "F9b + S_disguise": lambda r: [r["cand"]["h8in"]["s_disguise"]],
           "F9b + F_omit": lambda r: [r["cand"]["h8in"]["f_omit"]],
           "F11x (all three)": lambda r: S.f11x_design(r)[len(base(r)):]}
    out = []
    for name, extra in add.items():
        spec = ("logit", lambda r, e=extra: base(r) + e(r))
        P = S.pool(E.per_rep_parts(reps, spec, target))
        m = S.summarize(P)
        out.append({"model": name, "target": target, "auroc": m["auroc"], "recall_at_95pct_threshold": m["recall"], "fpr": m["fpr"], "brier": m["brier"]})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tag")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    reps, _ = E.load_arm(a.tag)
    outdir = os.path.join(RT, "results", a.out or a.tag)
    os.makedirs(outdir, exist_ok=True)
    for name, rows in (("diag_h8_components.csv", h8_component_table(reps)), ("diag_f11x_ablation.csv", f11x_ablation(reps) + f11x_ablation(reps, "B") + f11x_ablation(reps, "C"))):
        with open(os.path.join(outdir, name), "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
    print("diagnostics written to", outdir)


if __name__ == "__main__":
    main()
