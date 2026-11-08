"""Evaluation v2: per-replicate calibration -> single scoring of the test split, pooled cluster bootstrap, primary comparisons
(refit bootstrap + Argon F31 gate), per-hypothesis falsifier report, silent-fallback audit, cross-arm transfer.
Usage: evaluate_v2.py <tag> [--boot 1000] [--refit-boot 500] [--llm-monitors gemma4:31b-cloud,tp:qwen3.8-flash] [--transfer-from TAG]"""
import argparse
import csv
import glob
import json
import math
import os
import sys
import time

import numpy as np
from sklearn.metrics import roc_auc_score, roc_curve

HERE = os.path.dirname(os.path.abspath(__file__))
RT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import stats_v2 as S  # noqa: E402

CF = S.CF
NAN = float("nan")
BOOT_SEED = 20261108
GRANS = ["claim_level", "window_64tok", "report_centroid"]
MODES7 = ["full_anchored", "comm_hidden", "half_mcar", "none", "tail_truncated", "spoofed_open", "reordered"]
COPY_SET = ["COPY_LIT", "COPY_PARA", "COPY_TWIN", "COPY_COVER", "ADAPT_SURROGATE_K3", "ADAPT_LEX_INJECT", "ADAPT_SPLIT_2", "ADAPT_OUT_OF_BAND"]
HONEST_SOURCED = ["IND_SAME", "IND_DIFF", "TWIN_H", "NEAR_H"]


def dump_json(path, obj):
    """Atomic JSON write (temp file then replace) with the file handle closed."""
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=1, default=float)
    os.replace(tmp, path)


# ---------------- loading ----------------
def load_arm(tag, scores_dir=None):
    scores_dir = scores_dir or os.path.join(RT, "scores")
    reps, failed = {}, []
    for path in sorted(glob.glob(os.path.join(scores_dir, tag, "rep*_scores.jsonl"))):
        rows = []
        for line in open(path, encoding="utf-8"):
            r = json.loads(line)
            (failed if r.get("failed") else rows).append(r)
        if rows:
            reps[rows[0]["replicate"]] = rows
    return reps, failed


# ---------------- monitor specifications ----------------
def cand(r, key, g="claim_level", sub="score"):
    return r["cand"][g][key][sub] if key in ("h2", "h3", "h5", "h6", "h9") else r["cand"][key][sub]


def build_specs(llm_models):
    d = {"F0a same cited": ("score", lambda r: r["feats"]["same_cited"]),
         "F1 lexical 3-gram": ("score", lambda r: r["feats"]["lex"]),
         "F2 embedding cosine": ("score", lambda r: r["feats"]["cos"]),
         "F3 STP": ("score", lambda r: r["feats"]["stp"]),
         "F4 STP-AR": ("score", lambda r: r["feats"]["stpar"]),
         "F5 STP-AR+MOI": ("score", lambda r: r["feats"]["stpar_moi"]),
         "F6 RCC-v3.3 (AR)": ("score", lambda r: r["feats"]["rcc_ar"]),
         "F6b RCC-v3.3 (AR+MOI)": ("score", lambda r: r["feats"]["rcc_ar_moi"]),
         "F8a Argon F42 (cosine part)": ("score", lambda r: r["feats"]["argon_mmd"]),
         "F8b Argon F44 (jaccard part)": ("score", lambda r: r["feats"]["argon_claim_overlap"]),
         "S1 legacy unsup_own": ("score", lambda r: r["feats"]["unsup_own"]),
         "S2 source containment": ("score", lambda r: r["feats"]["src_cont"]),
         "F9 formula ensemble": ("logit", lambda r: [r["feats"][k] for k in S.ARTIFACT]),
         "F9b ensemble + source checks": ("logit", S.f9b_design),
         "F11x candidate ensemble": ("logit", S.f11x_design),
         "H1 E_sup": ("score", lambda r: r["cand"]["h1"]["score"]),
         "H1c clean unsupported (NaN abstain)": ("score", lambda r: r["cand"]["h1"]["unsup_own_clean"]),
         "H4 F_omit": ("score", lambda r: r["cand"]["h4"]["score"]),
         "H7 CSLS_cal": ("score", lambda r: r["cand"]["h7"]["score"]),
         "H10 Delta_overclaim": ("score", lambda r: r["cand"]["h10"]["score"]),
         "H10 -K_eff": ("score", lambda r: -r["cand"]["h10"]["k_effective_sources"]),
         "H8 content-only (no custody)": ("h8", ("full_anchored", True))}
    for g in GRANS:
        d["H2 S_orth [%s]" % g] = ("score", lambda r, g=g: cand(r, "h2", g))
        d["H3 S_disguise [%s]" % g] = ("score", lambda r, g=g: cand(r, "h3", g))
        d["H5 A_bipartite [%s]" % g] = ("score", lambda r, g=g: cand(r, "h5", g))
        d["H6 D_dpi [%s]" % g] = ("score", lambda r, g=g: cand(r, "h6", g))
        d["H9 F42_rep [%s]" % g] = ("score", lambda r, g=g: cand(r, "h9", g))
    for mode in MODES7:
        d["P ledger only [%s]" % mode] = ("logit", lambda r, m=mode: [r["ledger_legacy"][m][k] for k in S.LEDGER])
        d["F10 ensemble + ledger [%s]" % mode] = ("logit", lambda r, m=mode: S.f9b_design(r) + [r["ledger_legacy"][m][k] for k in S.LEDGER])
        d["H8 tri-state [%s]" % mode] = ("h8", (mode, False))
    for m in llm_models:
        d["F0b LLM report-only [%s]" % m] = ("llm", (m, "report_only"))
        d["D LLM with sources [%s]" % m] = ("llm", (m, "with_sources"))
    return d


# ---------------- core evaluation ----------------
def per_rep_parts(reps, spec, target):
    parts = []
    for rep, rows in sorted(reps.items()):
        cal = [r for r in rows if r["split"] == "calib"]
        tst = [r for r in rows if r["split"] == "test"]
        if spec[0] == "llm" and not all(spec[1][0] in r.get("llm", {}) for r in rows):
            parts.append(None)          # LLM monitor not run for this arm: the only legitimate reason for a missing part
            continue
        parts.append(S.fit_apply(spec, cal, tst, target))     # any other KeyError is a real bug and must surface
    return parts


def sub_auc(P, pos, neg):
    t = np.array(P["types"])
    m = np.isin(t, pos + neg) & P["valid"]
    y = np.isin(t[m], pos).astype(int)
    return float(roc_auc_score(y, P["s"][m])) if 0 < y.sum() < len(y) else NAN


def tpr_at_fpr(P, pos, neg, fpr_max=0.05):
    t = np.array(P["types"])
    m = np.isin(t, pos + neg) & P["valid"]
    y = np.isin(t[m], pos).astype(int)
    if not (0 < y.sum() < len(y)):
        return NAN
    fpr, tpr, _ = roc_curve(y, P["s"][m])
    return float(tpr[fpr <= fpr_max].max())


def type_rates(P, name, target, arm):
    out = []
    t = np.array(P["types"])
    for typ in sorted(set(P["types"])):
        m = t == typ
        v = m & P["valid"]
        out.append({"arm": arm, "monitor": name, "target": target, "type": typ, "n": int(m.sum()), "n_scored": int(v.sum()),
                    "flag_rate": float((P["flag"][v] & ~P["abstain"][v]).mean()) if v.sum() else NAN,
                    "abstain_rate": float(P["abstain"][m].mean()) if m.sum() else NAN, "not_scored_rate": float(1 - v.sum() / m.sum()) if m.sum() else NAN,
                    "truth_pos_rate": float(P["y"][m].mean())})
    return out


def run_main(reps, specs, n_boot, arm):
    rng = np.random.default_rng(BOOT_SEED)
    table, per_type, pooled = [], [], {}
    for target in S.TARGETS:
        for name, spec in specs.items():
            P = S.pool(per_rep_parts(reps, spec, target))
            if P is None:
                continue
            pooled[(name, target)] = P
            m = S.summarize(P)
            ci = S.boot_ci(P, rng, n_boot=n_boot)
            const = float(np.mean((P["prev"] - P["y"][P["valid"]]) ** 2)) if P["valid"].any() else NAN
            row = dict(arm=arm, monitor=name, target=target, n_reps=len(reps), **m, brier_const=const,
                       bss=(1 - m["brier"] / const) if const and const == const and m["brier"] == m["brier"] else NAN)
            for w, (lo, hi) in ci.items():
                row["%s_lo" % w], row["%s_hi" % w] = lo, hi
            table.append(row)
            per_type += type_rates(P, name, target, arm)
        print("main target done", target, flush=True)
    return table, per_type, pooled


# ---------------- primary comparisons ----------------
def refit_bootstrap(reps, specs, target, names, B, seed):
    rng = np.random.default_rng(seed)
    acc = {n: {"auroc": [], "recall": [], "fpr": [], "brier": []} for n in names}
    skipped = 0
    for _ in range(B):
        parts = {n: [] for n in names}
        for rep, rows in reps.items():
            cal = S.cluster_resample_rows([r for r in rows if r["split"] == "calib"], rng)
            tst = S.cluster_resample_rows([r for r in rows if r["split"] == "test"], rng)
            for n in names:
                parts[n].append(S.fit_apply(specs[n], cal, tst, target))
        if any(p is None for n in names for p in parts[n]):      # keep draws paired: a resample is used for all monitors or for none
            skipped += 1
            continue
        for n in names:
            m = S.summarize(S.pool(parts[n]))
            for k in acc[n]:
                acc[n][k].append(m[k])
    acc["_skipped_resamples"] = skipped
    out = {"_skipped_resamples": acc.pop("_skipped_resamples")}
    for n in names:
        out[n] = {k: [float(np.nanquantile(v, 0.025)), float(np.nanquantile(v, 0.975))] if len(v) and np.isfinite(v).any() else [NAN, NAN] for k, v in acc[n].items()}
    diffs = {}
    for a, b in (("F11x candidate ensemble", "F2 embedding cosine"), ("F11x candidate ensemble", "F9b ensemble + source checks")):
        if a in acc and b in acc and len(acc[a]["auroc"]) == len(acc[b]["auroc"]):
            d = np.array(acc[a]["auroc"]) - np.array(acc[b]["auroc"])
            diffs["AUROC(%s) - AUROC(%s)" % (a, b)] = [float(np.nanquantile(d, 0.025)), float(np.nanquantile(d, 0.975))]
    return out, diffs


def f31_gate(pooled, target="A_primary", new="F11x candidate ensemble", old="F9b ensemble + source checks"):
    Pn, Po = pooled.get((new, target)), pooled.get((old, target))
    if Pn is None or Po is None or not S.aligned(Pn, Po):
        return {"promote": False, "error": "monitors cover different rows (a replicate was dropped for one of them); paired gate not computed"}
    ln, lo = (Pn["p"] - Pn["y"]) ** 2, (Po["p"] - Po["y"]) ** 2
    cl = np.array([str(S.doc_key(c)) for c in Pn["clusters"]])
    t = np.array(Pn["types"])
    sent = np.isin(t, ["NOSRC_SAME", "TWIN_H"])
    fpr_new = float(Pn["flag"][sent].mean()) if sent.any() else 0.0
    fpr_old = float(Po["flag"][sent].mean()) if sent.any() else 0.0
    g = CF.argon_f31_cluster_promotion_gate(ln, lo, cl, n_comparisons=10, min_gain=0.005, sentinel_fpr_new=fpr_new, sentinel_fpr_old=fpr_old, sentinel_tol=0.01)
    g["sentinel_fpr_new"], g["sentinel_fpr_old"] = fpr_new, fpr_old
    return g


def primary_report(reps, specs, pooled, refit_b, seed):
    out = {"target_A": {}, "target_C": {}}
    namesA = ["F2 embedding cosine", "F9b ensemble + source checks", "F11x candidate ensemble"]
    namesC = ["H8 tri-state [comm_hidden]", "H8 tri-state [half_mcar]", "F10 ensemble + ledger [comm_hidden]", "F10 ensemble + ledger [half_mcar]"]
    if refit_b > 0:
        ciA, dA = refit_bootstrap(reps, specs, "A_primary", namesA, refit_b, seed)
        ciC, _ = refit_bootstrap(reps, specs, "C", namesC, refit_b, seed + 1)
        out["target_A"]["refit_ci"], out["target_A"]["paired_auroc_diff_ci"], out["target_C"]["refit_ci"] = ciA, dA, ciC
    gate = f31_gate(pooled)
    out["target_A"]["f31_gate"] = gate
    mA = {n: S.summarize(pooled[(n, "A_primary")]) for n in namesA if (n, "A_primary") in pooled}
    if len(mA) == 3:
        d_f2 = mA[namesA[2]]["auroc"] - mA[namesA[0]]["auroc"]
        out["target_A"]["auroc"] = {n: mA[n]["auroc"] for n in namesA}
        out["target_A"]["auroc_gain_vs_F2"] = d_f2
        out["target_A"]["success_criteria"] = {"f31_gate_passes": bool(gate and gate["promote"]), "auroc_gain_vs_F2_ge_0.25": bool(d_f2 >= 0.25),
                                               "sentinel_fpr_not_worse": bool(gate and gate["sentinel_fpr_new"] <= gate["sentinel_fpr_old"] + 0.01)}
        out["target_A"]["primary_success"] = all(out["target_A"]["success_criteria"].values())
    return out


# ---------------- falsifiers ----------------
def lt(x, t):
    return None if x != x else bool(x < t)


def gt(x, t):
    return None if x != x else bool(x > t)


def le(x, t):
    return None if x != x else bool(x <= t)


def anyof(*c):
    """Falsified if any declared condition holds; undetermined (None) if none holds but some value could not be computed (NaN)."""
    return True if any(v is True for v in c) else (None if any(v is None for v in c) else False)


def rate(P, typ_list):
    t = np.array(P["types"])
    m = np.isin(t, typ_list) & P["valid"] & ~P["abstain"]
    return float(P["flag"][m].mean()) if m.any() else NAN


def abstain(P, typ_list):
    t = np.array(P["types"])
    m = np.isin(t, typ_list)
    return float(P["abstain"][m].mean()) if m.any() else NAN


def median_diff_ci(P, pos, neg, B=1000):
    rng = np.random.default_rng(BOOT_SEED)
    t = np.array(P["types"])
    cl = {}
    for i, c in enumerate(P["clusters"]):
        cl.setdefault(S.doc_key(c), []).append(i)
    keys = list(cl)
    vals = []
    for _ in range(B):
        idx = np.concatenate([cl[keys[j]] for j in rng.integers(0, len(keys), len(keys))])
        tt, ss, vv = t[idx], P["s"][idx], P["valid"][idx]
        a, b = ss[np.isin(tt, pos) & vv], ss[np.isin(tt, neg) & vv]
        if len(a) and len(b):
            vals.append(np.median(a) - np.median(b))
    return [float(np.quantile(vals, 0.025)), float(np.quantile(vals, 0.975))] if vals else [NAN, NAN]


def falsifiers(pooled, reps, table):
    g = lambda n, t="A_primary": pooled.get((n, t))
    au = lambda n, t="A_primary": S.summarize(g(n, t, ))["auroc"] if g(n, t) is not None else NAN
    out = {}
    positives = ["COPY_LIT", "COPY_PARA"]
    H1 = g("H1 E_sup")
    if H1 is not None:
        tst_med = float(np.median([r["cand"]["h1"]["score"] for rows in reps.values() for r in rows if r["split"] == "test" and r["type"] == "IND_SAME"
                                    and r["cand"]["h1"]["score"] == r["cand"]["h1"]["score"]]))
        cal_t = [r for rows in reps.values() for r in rows if r["split"] == "calib" and r["cand"]["h1"]["score"] == r["cand"]["h1"]["score"]]
        yy = np.array([1 if r["type"] in positives else 0 for r in cal_t if r["type"] in positives + HONEST_SOURCED])
        ss = np.array([r["cand"]["h1"]["score"] for r in cal_t if r["type"] in positives + HONEST_SOURCED])
        cal_auc = float(roc_auc_score(yy, ss)) if 0 < yy.sum() < len(yy) else NAN
        test_auc = sub_auc(H1, positives, HONEST_SOURCED)
        out["ARG-H1"] = {"auroc_test_{LIT,PARA}_vs_honest_sourced": test_auc, "auroc_calibration": cal_auc, "median_E_sup_IND_SAME_test": tst_med,
                         "falsified": anyof(lt(cal_auc, 0.80), gt(tst_med, 0.0), lt(test_auc, 0.80))}
    f2 = au("F2 embedding cosine")
    H2c = g("H2 S_orth [claim_level]")
    if H2c is not None:
        fpr = rate(H2c, ["NOSRC_SAME"])
        out["ARG-H2"] = {"auroc": au("H2 S_orth [claim_level]"), "auroc_F2": f2, "gain_vs_F2": au("H2 S_orth [claim_level]") - f2, "fpr_NOSRC_SAME": fpr,
                         "falsified": anyof(lt(au("H2 S_orth [claim_level]") - f2, 0.10), gt(fpr, 0.20))}
    H3 = g("H3 S_disguise [claim_level]")
    if H3 is not None:
        a_tw = sub_auc(H3, ["COPY_TWIN"], ["TWIN_H"])
        mx = max(au("F1 lexical 3-gram"), f2)
        out["ARG-H3"] = {"auroc_COPY_TWIN_vs_TWIN_H": a_tw, "auroc": au("H3 S_disguise [claim_level]"), "max_auroc_F1_F2": mx,
                         "falsified": anyof(lt(a_tw, 0.75), lt(au("H3 S_disguise [claim_level]") - mx, 0.15))}
    H4 = g("H4 F_omit")
    if H4 is not None:
        a_tw = sub_auc(H4, ["COPY_TWIN"], ["TWIN_H"])
        out["ARG-H4"] = {"auroc_COPY_TWIN_vs_TWIN_H": a_tw, "tpr_at_fpr_5pct": tpr_at_fpr(H4, ["COPY_TWIN"], ["TWIN_H"]), "falsified": le(a_tw, 0.65)}
    H5 = g("H5 A_bipartite [claim_level]")
    if H5 is not None:
        out["ARG-H5"] = {"auroc": au("H5 A_bipartite [claim_level]"), "auroc_F8a": au("F8a Argon F42 (cosine part)"),
                         "falsified": lt(au("H5 A_bipartite [claim_level]") - au("F8a Argon F42 (cosine part)"), 0.08)}
    H6 = g("H6 D_dpi [claim_level]")
    if H6 is not None:
        ci = median_diff_ci(H6, ["COPY_LIT", "COPY_PARA", "COPY_COVER"], ["IND_SAME", "IND_DIFF", "TWIN_H"])
        out["ARG-H6"] = {"auroc": au("H6 D_dpi [claim_level]"), "median_diff_ci95": ci, "falsified": le(ci[0], 0.0)}
    H7 = g("H7 CSLS_cal")
    if H7 is not None:
        f_h7, f_f2 = rate(H7, ["NOSRC_SAME"]), rate(g("F2 embedding cosine"), ["NOSRC_SAME"])
        out["ARG-H7"] = {"fpr_NOSRC_SAME_H7": f_h7, "fpr_NOSRC_SAME_F2": f_f2, "auroc_H7": au("H7 CSLS_cal"), "auroc_F2": f2,
                         "falsified": anyof(lt(f_f2 - f_h7, 0.10), lt(au("H7 CSLS_cal") - f2, 0.05))}
    h8 = {}
    for mode in MODES7:
        P = g("H8 tri-state [%s]" % mode, "C")
        if P is not None:
            m = S.summarize(P)
            h8[mode] = {"recall": m["recall"], "fpr": m["fpr"], "auroc": m["auroc"], "abstain_rate": m["abstain_rate"],
                        "abstain_IND_SAME_IND_DIFF": abstain(P, ["IND_SAME", "IND_DIFF"])}
    if h8:
        g8 = lambda mode, key: h8.get(mode, {}).get(key, NAN)          # a missing mode is undetermined, never a pass
        fa = anyof(gt(g8("tail_truncated", "fpr"), 0.075), gt(g8("comm_hidden", "fpr"), 0.075),
                   gt(g8("comm_hidden", "abstain_IND_SAME_IND_DIFF"), 0.15), lt(g8("comm_hidden", "recall"), 0.80))
        out["ARG-H8"] = {"per_mode": h8, "falsified": fa}
    H9 = g("H9 F42_rep [claim_level]")
    if H9 is not None:
        gains = {t: au("H9 F42_rep [claim_level]", t) - max(au("F3 STP", t), au("F6 RCC-v3.3 (AR)", t)) for t in ("A_primary", "B")}
        out["ARG-H9"] = {"auroc_A": au("H9 F42_rep [claim_level]"), "auroc_B": au("H9 F42_rep [claim_level]", "B"), "gain_vs_best_of_F3_F6": gains,
                         "falsified": (None if any(v != v for v in gains.values()) else bool(all(v <= 0 for v in gains.values())))}
    H10 = g("H10 Delta_overclaim", "B")
    if H10 is not None:
        PK = g("H10 -K_eff", "B")
        t = np.array(H10["types"])
        if S.aligned(H10, PK):
            keff = np.array([-x for x in PK["s"]])
            m = np.isin(t, ["TWIN_H", "IND_DIFF"])
            acc = float(np.mean((keff[m] < 1.5) == (t[m] == "TWIN_H"))) if m.any() else NAN
        else:
            acc = NAN
        out["ARG-H10"] = {"auroc_B": au("H10 Delta_overclaim", "B"), "k_eff_accuracy_TWIN_H_vs_IND_DIFF": acc,
                          "falsified": anyof(lt(au("H10 Delta_overclaim", "B"), 0.90), lt(acc, 0.95)), "note": "LR_r fixed at 3.0; only the dependency graph is tested"}
    return out


# ---------------- audit ----------------
def audit(reps, failed, llm_models):
    rows = [r for v in reps.values() for r in v]
    out = {"generation_failures": {"n": len(failed), "by_type": {}}, "rows_scored": len(rows)}
    for f in failed:
        out["generation_failures"]["by_type"][f["type"]] = out["generation_failures"]["by_type"].get(f["type"], 0) + 1
    out["rcc_fallback_rate"] = float(np.mean([bool(r["feats"].get("rcc_fallback")) for r in rows])) if rows else NAN
    out["argon_f42_fallback_rate"] = float(np.mean([bool(r["feats"].get("argon_fail")) for r in rows])) if rows else NAN
    out["llm_parse_fail_rate"] = {}
    for m in llm_models:
        vals = [bool(r["llm"].get(m, {}).get(k, {}).get("llm_parse_fail")) for r in rows for k in ("report_only", "with_sources") if m in r.get("llm", {})]
        out["llm_parse_fail_rate"][m] = float(np.mean(vals)) if vals else NAN
    h1 = {}
    for r in rows:
        h1.setdefault(r["type"], []).append(r["cand"]["h1"]["status"] != "OK")
    out["h1_abstain_rate_by_type"] = {k: float(np.mean(v)) for k, v in h1.items()}
    ic = {}
    for r in rows:
        ic.setdefault(r["type"], []).append(r["cand"]["h8in"]["ic"])
    out["ic_regex_share_ic1_by_type"] = {k: float(np.mean(v)) for k, v in ic.items()}      # by design only SHARED_OK discloses non-independence
    out["ic_regex_design_agreement"] = float(np.mean([(r["cand"]["h8in"]["ic"] == 0) == (r["type"] == "SHARED_OK") for r in rows])) if rows else NAN
    tr = [r["surrogate_trace"] for r in rows if r.get("surrogate_trace")]
    if tr:
        out["surrogate_attack"] = {"n": len(tr), "mean_first_score": float(np.mean([t[0] for t in tr])), "mean_final_best_score": float(np.mean([min(t) for t in tr])),
                                   "mean_rounds": float(np.mean([len(t) - 1 for t in tr]))}
    out["conditions_scored"] = {"scenario_types": len({r["type"] for r in rows}), "granularities": 3, "log_modes": 7, "replicates": len(reps),
                                "cells_type_x_gran_x_mode_x_rep": len({r["type"] for r in rows}) * 3 * 7 * len(reps),
                                "pair_condition_evaluations": len(rows) * 3 * 7}
    return out


def write_csv(path, rows):
    if not rows:
        return
    keys = list(dict.fromkeys(k for r in rows for k in r))
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)


def _domain(r, catalog):
    return catalog[r["cluster"]]["domain"]


def transfer(fit_reps, test_reps, specs, names, arm):
    """Fit on the fit arm's calibration rows, score the test arm's test rows. Domain splits are re-drawn per replicate, so per test replicate the fit rows
    are restricted to domains that are calibration domains of that test replicate: no document of a fit row can be a test document."""
    import corpus
    catalog, _ = corpus.load_catalog()
    fit_cal = [r for rows in fit_reps.values() for r in rows if r["split"] == "calib"]
    out = []
    for target in ("A_primary", "B", "C"):
        for n in names:
            parts = []
            for rep, rows in sorted(test_reps.items()):
                cal_domains = {_domain(r, catalog) for r in rows if r["split"] == "calib"}
                cal = [r for r in fit_cal if _domain(r, catalog) in cal_domains]
                tst = [r for r in rows if r["split"] == "test"]
                if len(cal) >= 10:
                    parts.append(S.fit_apply(specs[n], cal, tst, target))
            P = S.pool(parts)
            if P is None:
                continue
            m = S.summarize(P)
            out.append(dict(arm=arm, monitor=n, target=target, n_test_replicates=len(parts), **{k: m[k] for k in ("n", "recall", "fpr", "auroc", "brier", "abstain_rate")}))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tag")
    ap.add_argument("--boot", type=int, default=1000)
    ap.add_argument("--refit-boot", type=int, default=500)
    ap.add_argument("--llm-monitors", default="gemma4:31b-cloud,tp:qwen3.8-flash")
    ap.add_argument("--transfer-from", default=None)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    llm_models = [m for m in a.llm_monitors.split(",") if m]
    reps, failed = load_arm(a.tag)
    outdir = os.path.join(RT, "results", a.out or a.tag)
    os.makedirs(outdir, exist_ok=True)
    specs = build_specs(llm_models)
    t0 = time.time()
    table, per_type, pooled = run_main(reps, specs, a.boot, a.tag)
    write_csv(os.path.join(outdir, "results_main.csv"), table)
    write_csv(os.path.join(outdir, "results_per_type.csv"), per_type)
    keep = ["F2 embedding cosine", "F9b ensemble + source checks", "F11x candidate ensemble", "H1 E_sup", "H3 S_disguise [claim_level]", "H4 F_omit",
            "F10 ensemble + ledger [full_anchored]", "F10 ensemble + ledger [none]", "H8 tri-state [full_anchored]", "H8 tri-state [comm_hidden]"] + \
           ["F0b LLM report-only [%s]" % m for m in llm_models]
    preds = {"%s|%s" % (n, t): {"y": P["y"].tolist(), "flag": P["flag"].tolist(), "abstain": P["abstain"].tolist(), "valid": P["valid"].tolist(),
                                "s": [None if x != x else float(x) for x in P["s"]], "types": P["types"]}
             for (n, t), P in pooled.items() if n in keep and t in ("A_primary", "C")}
    dump_json(os.path.join(outdir, "pooled_predictions.json"), preds)
    prim = primary_report(reps, specs, pooled, a.refit_boot, BOOT_SEED + 11)
    dump_json(os.path.join(outdir, "primary_comparisons.json"), prim)
    dump_json(os.path.join(outdir, "falsifiers.json"), falsifiers(pooled, reps, table))
    dump_json(os.path.join(outdir, "audit.json"), audit(reps, failed, llm_models))
    if a.transfer_from:
        fit_reps, _ = load_arm(a.transfer_from)
        names = ["F2 embedding cosine", "F9b ensemble + source checks", "F11x candidate ensemble", "H8 tri-state [comm_hidden]", "H8 tri-state [half_mcar]",
                 "F10 ensemble + ledger [comm_hidden]", "F10 ensemble + ledger [half_mcar]", "H1 E_sup", "H3 S_disguise [claim_level]"] + \
                ["F0b LLM report-only [%s]" % m for m in llm_models] + ["D LLM with sources [%s]" % m for m in llm_models]
        write_csv(os.path.join(outdir, "transfer_from_%s.csv" % a.transfer_from), transfer(fit_reps, reps, specs, names, a.tag))
    print("done %s: %d result rows, t=%.0fs" % (a.tag, len(table), time.time() - t0), flush=True)


if __name__ == "__main__":
    main()
