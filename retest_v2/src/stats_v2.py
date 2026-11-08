"""Core fitting and metric engine for retest v2 (calibrate on a calibration split, score a test split once).
Monitor kinds: score (one scalar, NaN = abstain), logit (feature vector), llm (monitor-model probability), h8 (frozen tri-state rule)."""
import math
import os
import sys
import warnings

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score

warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__))
RT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(RT, "prereg"))
import candidate_formulas as CF  # noqa: E402

NAN = float("nan")
TARGETS = {"A_primary": lambda r: r["copy_u"],
           "A_secondary": lambda r: r["truth"]["copying_occurred"],
           "B": lambda r: r["truth"]["evidence_nonindependent"],
           "C": lambda r: r["truth"]["provenance_claim_false"]}
LLM_KEY = {"A_primary": "p_copying", "A_secondary": "p_copying", "B": "p_nonindependent", "C": "p_false_provenance"}
ARTIFACT = ["lex", "cos", "stp", "stpar", "stpar_moi", "rcc_ar_moi", "argon_mmd", "argon_claim_overlap"]
LEDGER = ["led_known", "led_msg", "led_unopened", "led_shared_body"]
Q_HI, Q_LO = 0.95, 0.80


def f9b_design(r):
    f = r["feats"]
    return [f[k] for k in ARTIFACT] + [f["unsup_own"], f["src_cont"], f["sup_in_a_src"]]


def f11x_design(r):
    """F9b features + [E_sup (NaN -> 0), has_src, S_disguise, F_omit]; NaN imputation and the has_src column are declared in STAGE2."""
    e = r["cand"]["h1"]["score"]
    h8 = r["cand"]["h8in"]
    return f9b_design(r) + [0.0 if e != e else e, float(h8["has_src"]), h8["s_disguise"], h8["f_omit"]]


def verdict_from_components(r_reuse, has_src, l_known, s_disg_clip, ic, s_prov, q_lo, q_hi):
    """Mirror of the decision branches in the frozen tri_state_claim_ledger_verdict (equality is unit-tested against the frozen function)."""
    if ic == 0:
        return 0
    if s_prov > q_hi:
        return 1
    if (has_src == 0 or l_known == 0) and (q_lo <= max(r_reuse, s_disg_clip) <= q_hi):
        return -1
    return 0


_H8_CACHE = {}


def h8_components(r, mode, content_only=False):
    """Call the FROZEN function once (q irrelevant) to obtain S_prov and r_reuse for a row under a log mode (memoised per row)."""
    key = (id(r), mode, content_only)       # object identity: unique per loaded row, so rows of different arms can never collide
    if key not in _H8_CACHE:
        _H8_CACHE[key] = _h8_components(r, mode, content_only)
    return _H8_CACHE[key]


def _h8_components(r, mode, content_only):
    h = r["cand"]["h8in"]
    led = r["ledger_h8"][mode]
    known, unop, shb = (0.0, 0.0, 0.0) if content_only else (led["l_known"], led["led_unopened"], led["led_shared_body"])
    out = CF.tri_state_claim_ledger_verdict(np.array(h["s_own_vec"]), np.array(h["s_a_vec"]), h["ic"], h["has_src"], known, unop, shb,
                                            h["s_disguise"], f_omit=h["f_omit"], q_lo=0.0, q_hi=1e9)
    s_disg_clip = float(np.clip(h["s_disguise"], 0.0, 1.0))
    return {"s_prov": out["score"], "r_reuse": out["r_reuse"], "has_src": h["has_src"], "l_known": known, "s_disg_clip": s_disg_clip, "ic": h["ic"]}


def metrics_from(y, flag, p, score):
    y, flag, p = np.asarray(y), np.asarray(flag, dtype=bool), np.asarray(p, dtype=float)
    tp, fp = int(((y == 1) & flag).sum()), int(((y == 0) & flag).sum())
    tn, fn = int(((y == 0) & ~flag).sum()), int(((y == 1) & ~flag).sum())
    rec = tp / (tp + fn) if tp + fn else NAN
    spec = tn / (tn + fp) if tn + fp else NAN
    out = {"n": len(y), "n_pos": int(y.sum()), "tp": tp, "fp": fp, "tn": tn, "fn": fn, "recall": rec, "fpr": (1 - spec) if spec == spec else NAN,
           "brier": float(np.nanmean((p - y) ** 2)) if np.isfinite(p).any() else NAN}
    if len(y) and 0 < y.sum() < len(y):
        out["auroc"] = float(roc_auc_score(y, score))
        out["auprc"] = float(average_precision_score(y, score))
    else:
        out["auroc"] = out["auprc"] = NAN
    return out


def _std_logit(Xc, yc, Xt, C):
    mu, sd = Xc.mean(0), Xc.std(0)
    sd[sd == 0] = 1.0
    lr = LogisticRegression(C=C, max_iter=5000).fit((Xc - mu) / sd, yc)
    return lr.predict_proba((Xc - mu) / sd)[:, 1], lr.predict_proba((Xt - mu) / sd)[:, 1]


def fit_apply(spec, cal, tst, target):
    """Fit on cal rows, score tst rows. spec = (kind, payload). Returns dict of arrays over ALL tst rows plus masks, or None if not fittable."""
    kind, payload = spec
    ty = TARGETS[target]
    y_c = np.array([ty(r) for r in cal])
    y_t = np.array([ty(r) for r in tst])
    n_t = len(tst)
    types = [r["type"] for r in tst]
    clusters = [(r["replicate"], r["cluster"]) for r in tst]
    valid_t = np.ones(n_t, dtype=bool)
    abstain_t = np.zeros(n_t, dtype=bool)
    p_t = np.full(n_t, NAN)
    if kind in ("score", "llm"):
        fn = payload if kind == "score" else (lambda r, _p=payload: r["llm"][_p[0]][_p[1]][LLM_KEY[target]])
        raw_c = np.array([fn(r) for r in cal], dtype=float)
        raw_t = np.array([fn(r) for r in tst], dtype=float)
        ok_c, valid_t = np.isfinite(raw_c), np.isfinite(raw_t)
        if ok_c.sum() < 10 or len(set(y_c[ok_c])) < 2:
            return None
        s_c = raw_c[ok_c]
        mu, sd = s_c.mean(), s_c.std() or 1.0
        lr = LogisticRegression(C=1e6, max_iter=2000).fit(((s_c - mu) / sd).reshape(-1, 1), y_c[ok_c])
        sc_t = np.where(valid_t, raw_t, 0.0)
        p_t = np.where(valid_t, lr.predict_proba(((sc_t - mu) / sd).reshape(-1, 1))[:, 1], NAN)
        if kind == "llm":
            s_c = lr.predict_proba(((s_c - mu) / sd).reshape(-1, 1))[:, 1]
            s_t = np.where(valid_t, p_t, NAN)
        else:
            s_t = np.where(valid_t, raw_t, NAN)
        neg = s_c[y_c[ok_c] == 0]
    elif kind == "logit":
        Xc = np.array([payload(r) for r in cal], dtype=float)
        Xt = np.array([payload(r) for r in tst], dtype=float)
        if len(set(y_c)) < 2 or not np.isfinite(Xc).all() or not np.isfinite(Xt).all():
            return None
        p_c, p_t = _std_logit(Xc, y_c, Xt, 1.0)
        s_t, neg = p_t, p_c[y_c == 0]
    elif kind == "h8":
        mode, content_only = payload
        comp_c = [h8_components(r, mode, content_only) for r in cal]
        comp_t = [h8_components(r, mode, content_only) for r in tst]
        sp_c = np.array([c["s_prov"] for c in comp_c])
        neg = sp_c[y_c == 0]
        if len(neg) < 5:
            return None
        q_hi, q_lo = float(np.quantile(neg, Q_HI)), float(np.quantile(neg, Q_LO))
        s_t = np.array([c["s_prov"] for c in comp_t])
        verd = np.array([verdict_from_components(c["r_reuse"], c["has_src"], c["l_known"], c["s_disg_clip"], c["ic"], c["s_prov"], q_lo, q_hi)
                         for c in comp_t])
        abstain_t = verd == -1
        flag = verd == 1
        return {"y": y_t, "s": s_t, "p": p_t, "flag": flag, "valid": valid_t, "abstain": abstain_t, "types": types, "clusters": clusters,
                "thr": q_hi, "q_lo": q_lo, "prev": float(y_c.mean())}
    else:
        raise ValueError(kind)
    thr = float(np.quantile(neg, Q_HI)) if len(neg) else NAN
    flag = np.where(valid_t, s_t > thr, False)
    return {"y": y_t, "s": s_t, "p": p_t, "flag": flag, "valid": valid_t, "abstain": abstain_t, "types": types, "clusters": clusters, "thr": thr,
            "prev": float(y_c.mean())}


def pool(parts):
    parts = [p for p in parts if p is not None]
    if not parts:
        return None
    out = {k: np.concatenate([p[k] for p in parts]) for k in ("y", "s", "p", "flag", "valid", "abstain")}
    out["types"] = sum((p["types"] for p in parts), [])
    out["clusters"] = sum((p["clusters"] for p in parts), [])
    out["prev"] = float(np.mean([p["prev"] for p in parts]))
    out["thr"] = float(np.nanmean([p["thr"] for p in parts]))
    return out


def summarize(P, idx=None):
    """Metrics over finite-score rows; recall/FPR over finite-score, non-abstained rows."""
    if idx is None:
        idx = np.arange(len(P["y"]))
    v = P["valid"][idx]
    y, s, p, f, ab = P["y"][idx][v], P["s"][idx][v], P["p"][idx][v], P["flag"][idx][v], P["abstain"][idx][v]
    keep = ~ab
    m = metrics_from(y[keep], f[keep], p[keep], s[keep]) if keep.sum() else metrics_from([], [], [], [])
    if len(y) and 0 < y.sum() < len(y):                 # AUROC on all finite-score rows (abstention does not remove the score)
        m["auroc"] = float(roc_auc_score(y, s))
        m["auprc"] = float(average_precision_score(y, s))
    m["coverage"] = float(v.mean()) if len(v) else NAN
    m["abstain_rate"] = float(ab.mean()) if len(ab) else NAN
    return m


def aligned(*pools):
    """True only if every pool covers the same rows in the same order (types and clusters identical). Needed before any paired comparison."""
    return all(p is not None and p["types"] == pools[0]["types"] and p["clusters"] == pools[0]["clusters"] for p in pools)


def doc_key(c):
    """Bootstrap unit = the source document of agent A (clusters of different replicates that share a document are NOT independent)."""
    return c[1]


def boot_ci(P, rng, n_boot=1000, which=("recall", "fpr", "brier", "auroc")):
    cl = {}
    for i, c in enumerate(P["clusters"]):
        cl.setdefault(doc_key(c), []).append(i)
    keys = list(cl)
    vals = {w: [] for w in which}
    for _ in range(n_boot):
        pick = rng.integers(0, len(keys), len(keys))
        idx = np.concatenate([cl[keys[j]] for j in pick])
        m = summarize(P, idx)
        for w in which:
            vals[w].append(m[w])
    return {w: (float(np.nanquantile(v, 0.025)), float(np.nanquantile(v, 0.975))) if np.isfinite(v).any() else (NAN, NAN) for w, v in vals.items()}


def cluster_resample_rows(rows, rng):
    cl = {}
    for r in rows:
        cl.setdefault(r["cluster"], []).append(r)
    keys = list(cl)
    pick = rng.integers(0, len(keys), len(keys))
    return [r for j in pick for r in cl[keys[j]]]
