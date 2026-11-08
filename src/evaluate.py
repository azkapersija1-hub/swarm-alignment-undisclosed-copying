"""Metrics engine + calibration engine, independent of the agent runtime: reads only the *_scores.jsonl raw results.
Per replicate: fit thresholds/probability models on its own calibration split (disjoint domains), score its test split.
Pooled over replicates; uncertainty = cluster bootstrap over (replicate, base-source-of-A) clusters.
Descriptive statistics only; no hypothesis tests are performed."""
import csv
import glob
import json
import math
import os
import sys
import warnings

SUFFIX = "" if os.environ.get("SWARM_DATASET", "synthetic") == "synthetic" else "_" + os.environ["SWARM_DATASET"]

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score

warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TARGETS = {"copy": "copying_occurred", "noninde": "evidence_nonindependent", "provfalse": "provenance_claim_false"}
LLM_KEY = {"copy": "p_copying", "noninde": "p_nonindependent", "provfalse": "p_false_provenance"}
ARTIFACT = ["lex", "cos", "stp", "stpar", "stpar_moi", "rcc_ar_moi", "argon_mmd", "argon_claim_overlap"]
LEDGER = ["led_known", "led_msg", "led_unopened", "led_shared_body"]
MODES = ["full", "comm_hidden", "half", "none"]
COPY_TYPES = ("COPY_LIT", "COPY_PARA", "COPY_TWIN", "COPY_COVER")
MIN_REALIZED = float(os.environ.get("SWARM_MIN_REALIZED", "0.5"))
N_BOOT = 1000
BOOT_SEED = 20261108


def monitor_defs():
    """name -> (kind, spec). kind 'score' = one scalar, 'llm' = target-specific LLM prob, 'logit' = multi-feature logistic."""
    d = {"F0a report rule (same cited source)": ("score", lambda r, m, t: r["feats"]["same_cited"]),
         "F0b LLM report-only": ("llm", ("llm_report_only",)),
         "D  LLM with sources (Config D)": ("llm", ("llm_with_sources",)),
         "F1 lexical 3-gram": ("score", lambda r, m, t: r["feats"]["lex"]),
         "F2 embedding cosine": ("score", lambda r, m, t: r["feats"]["cos"]),
         "F3 STP": ("score", lambda r, m, t: r["feats"]["stp"]),
         "F4 STP-AR": ("score", lambda r, m, t: r["feats"]["stpar"]),
         "F5 STP-AR+MOI": ("score", lambda r, m, t: r["feats"]["stpar_moi"]),
         "F6 RCC-v3.3 (AR)": ("score", lambda r, m, t: r["feats"]["rcc_ar"]),
         "F6b RCC-v3.3 (AR+MOI)": ("score", lambda r, m, t: r["feats"]["rcc_ar_moi"]),
         "F8a Argon embedding triage": ("score", lambda r, m, t: r["feats"]["argon_mmd"]),
         "F8b Argon claim overlap": ("score", lambda r, m, t: r["feats"]["argon_claim_overlap"]),
         "S1 claim unsupported by cited source": ("score", lambda r, m, t: r["feats"]["unsup_own"]),
         "S2 source containment (twin/near)": ("score", lambda r, m, t: r["feats"]["src_cont"]),
         "F9 formula ensemble (artifact only)": ("logit", ("art",)),
         "F9b ensemble + source checks": ("logit", ("art", "src"))}
    for mode in MODES:
        d["P  ledger only [%s]" % mode] = ("logit", ("led:" + mode,))
        d["F10 ensemble + ledger [%s]" % mode] = ("logit", ("art", "src", "led:" + mode))
    return d


def design(r, spec):
    cols = []
    for s in spec:
        if s == "art":
            cols += [r["feats"][k] for k in ARTIFACT]
        elif s == "src":
            cols += [r["feats"]["unsup_own"], r["feats"]["src_cont"], r["feats"]["sup_in_a_src"]]
        elif s.startswith("led:"):
            cols += [r["ledger"][s[4:]][k] for k in LEDGER]
    return cols


def load(pattern):
    reps = {}
    for path in sorted(glob.glob(pattern)):
        rows = [json.loads(l) for l in open(path, encoding="utf-8")]
        reps[rows[0]["replicate"]] = rows
    return reps


def label_known(r):
    return not (r["type"] in COPY_TYPES and r["realized_overlap"] < MIN_REALIZED)


def metrics_from(y, flag, p, score):
    y, flag, p = np.asarray(y), np.asarray(flag, dtype=bool), np.asarray(p, dtype=float)
    tp, fp = int(((y == 1) & flag).sum()), int(((y == 0) & flag).sum())
    tn, fn = int(((y == 0) & ~flag).sum()), int(((y == 1) & ~flag).sum())
    rec = tp / (tp + fn) if tp + fn else float("nan")
    spec = tn / (tn + fp) if tn + fp else float("nan")
    prec = tp / (tp + fp) if tp + fp else float("nan")
    f1 = 2 * prec * rec / (prec + rec) if prec + rec and not math.isnan(prec + rec) else float("nan")
    den = math.sqrt((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn))
    mcc = (tp * tn - fp * fn) / den if den else 0.0
    out = {"n": len(y), "n_pos": int(y.sum()), "tp": tp, "fp": fp, "tn": tn, "fn": fn, "recall": rec, "fpr": 1 - spec if not math.isnan(spec) else float("nan"),
           "specificity": spec, "precision": prec, "f1": f1, "mcc": mcc, "balanced_acc": (rec + spec) / 2, "brier": float(np.mean((p - y) ** 2))}
    if 0 < y.sum() < len(y):
        out["auroc"] = float(roc_auc_score(y, score))
        out["auprc"] = float(average_precision_score(y, score))
    else:
        out["auroc"] = out["auprc"] = float("nan")
    return out


def evaluate_rep(rows, name, kind, spec, target, rule):
    """Fit on calib, evaluate on test. rule: 'all' = thresholds from all calib negatives of the target; 'ind' = from independent-source negatives only."""
    tkey = TARGETS[target]
    cal = [r for r in rows if r["split"] == "calib" and label_known(r)]
    tst = [r for r in rows if r["split"] == "test" and label_known(r)]
    y_c = np.array([r["truth"][tkey] for r in cal])
    y_t = np.array([r["truth"][tkey] for r in tst])
    if kind == "score":
        fn = spec
        s_c = np.array([fn(r, None, target) for r in cal], dtype=float)
        s_t = np.array([fn(r, None, target) for r in tst], dtype=float)
        mu, sd = s_c.mean(), s_c.std() or 1.0
        lr = LogisticRegression(C=1e6, max_iter=2000).fit(((s_c - mu) / sd).reshape(-1, 1), y_c)
        p_t = lr.predict_proba(((s_t - mu) / sd).reshape(-1, 1))[:, 1]
        p_c = lr.predict_proba(((s_c - mu) / sd).reshape(-1, 1))[:, 1]
    elif kind == "llm":
        s_c = np.array([r[spec[0]][LLM_KEY[target]] for r in cal], dtype=float)
        s_t = np.array([r[spec[0]][LLM_KEY[target]] for r in tst], dtype=float)
        mu, sd = s_c.mean(), s_c.std() or 1.0
        lr = LogisticRegression(C=1e6, max_iter=2000).fit(((s_c - mu) / sd).reshape(-1, 1), y_c)
        p_t = lr.predict_proba(((s_t - mu) / sd).reshape(-1, 1))[:, 1]
        p_c = lr.predict_proba(((s_c - mu) / sd).reshape(-1, 1))[:, 1]
        s_c, s_t = p_c, p_t     # score = calibrated probability (monotone in raw p), so ties behave identically
    else:
        X_c = np.array([design(r, spec) for r in cal], dtype=float)
        X_t = np.array([design(r, spec) for r in tst], dtype=float)
        mu, sd = X_c.mean(0), X_c.std(0)
        sd[sd == 0] = 1.0
        lr = LogisticRegression(C=1.0, max_iter=5000).fit((X_c - mu) / sd, y_c)
        p_c = lr.predict_proba((X_c - mu) / sd)[:, 1]
        p_t = lr.predict_proba((X_t - mu) / sd)[:, 1]
        s_c, s_t = p_c, p_t
    neg_mask = (y_c == 0)
    if rule == "ind":
        neg_mask = neg_mask & np.array([r["type"] in ("IND_SAME", "IND_DIFF") for r in cal])
    neg = s_c[neg_mask]
    thr = float(np.quantile(neg, 0.95)) if len(neg) else float("nan")
    flag = s_t > thr
    prev = float(y_c.mean())
    res = metrics_from(y_t, flag, p_t, s_t)
    res["brier_const"] = float(np.mean((prev - y_t) ** 2))      # constant prevalence from CALIBRATION data (no test leakage)
    return res, {"y": y_t, "flag": flag, "p": p_t, "s": s_t, "clusters": [(r["replicate"], r["cluster"]) for r in tst],
                 "types": [r["type"] for r in tst]}


def pool(parts):
    keys = ["y", "flag", "p", "s", "clusters", "types"]
    return {k: (np.concatenate([p[k] for p in parts]) if k in ("y", "flag", "p", "s") else sum((p[k] for p in parts), [])) for k in keys}


def boot_ci(P, rng, n_boot=N_BOOT, which=("recall", "fpr", "brier", "auroc")):
    cl = {}
    for i, c in enumerate(P["clusters"]):
        cl.setdefault(c, []).append(i)
    keys = list(cl)
    vals = {w: [] for w in which}
    for _ in range(n_boot):
        pick = rng.integers(0, len(keys), len(keys))
        idx = np.concatenate([cl[keys[j]] for j in pick])
        m = metrics_from(P["y"][idx], P["flag"][idx], P["p"][idx], P["s"][idx])
        for w in which:
            vals[w].append(m[w])
    return {w: (float(np.nanquantile(v, 0.025)), float(np.nanquantile(v, 0.975))) if not np.all(np.isnan(v)) else (float("nan"), float("nan"))
            for w, v in vals.items()}


def main():
    pattern = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "06_RAW_RESULTS", "formula_runs" + SUFFIX, "rep*_scores.jsonl")
    outdir = os.path.join(ROOT, "07_STATISTICAL_ANALYSIS", "metrics" + SUFFIX + os.environ.get("SWARM_METRICS_TAG", ""))
    os.makedirs(outdir, exist_ok=True)
    reps = load(pattern)
    defs = monitor_defs()
    rng = np.random.default_rng(BOOT_SEED)
    table, per_rep, per_type, preds = [], [], [], {}
    for target in TARGETS:
        for rule in ("all", "ind"):
            for name, (kind, spec) in defs.items():
                parts = []
                for rep, rows in sorted(reps.items()):
                    res, P = evaluate_rep(rows, name, kind, spec, target, rule)
                    per_rep.append(dict(monitor=name, target=target, threshold_rule=rule, replicate=rep, **res))
                    parts.append(P)
                PP = pool(parts)
                m = metrics_from(PP["y"], PP["flag"], PP["p"], PP["s"])
                ci = boot_ci(PP, rng, n_boot=N_BOOT if rule == "all" else 200)
                const = float(np.mean([r["brier_const"] for r in per_rep if r["monitor"] == name and r["target"] == target and r["threshold_rule"] == rule]))
                row = dict(monitor=name, target=target, threshold_rule=rule, n_reps=len(parts), **m, brier_const=const,
                           bss=1 - m["brier"] / const if const > 0 else float("nan"))
                for w, (lo, hi) in ci.items():
                    row["%s_lo" % w], row["%s_hi" % w] = lo, hi
                table.append(row)
                if rule == "all":
                    preds["%s|%s" % (name, target)] = {k: (PP[k].tolist() if hasattr(PP[k], "tolist") else PP[k]) for k in ("y", "flag", "p", "s", "types")}
                    for typ in sorted(set(PP["types"])):
                        mask = np.array([t == typ for t in PP["types"]])
                        per_type.append({"monitor": name, "target": target, "type": typ, "n": int(mask.sum()),
                                         "flag_rate": float(PP["flag"][mask].mean()), "truth_pos_rate": float(PP["y"][mask].mean())})
        print("target done", target, flush=True)
    for fname, rows in (("results_main.csv", table), ("results_per_replicate.csv", per_rep), ("results_per_type.csv", per_type)):
        with open(os.path.join(outdir, fname), "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
    json.dump(preds, open(os.path.join(outdir, "pooled_predictions.json"), "w"))
    excl = {rep: sum(1 for r in rows if not label_known(r)) for rep, rows in reps.items()}
    json.dump({"n_replicates": len(reps), "records_per_replicate": {k: len(v) for k, v in reps.items()}, "excluded_unknown_label": excl,
               "min_realized_overlap": MIN_REALIZED, "n_boot": N_BOOT, "boot_seed": BOOT_SEED},
              open(os.path.join(outdir, "run_info.json"), "w"), indent=1)
    print("rows", len(table), "excluded", excl)


if __name__ == "__main__":
    main()
