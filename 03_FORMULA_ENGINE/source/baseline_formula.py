"""baseline_formula.py -- METHOD 1, the control condition (Part A of the
GCAW validation spec). Self-contained port of the SAME math already
validated on the real 15,000-PDF corpus (run_validation_n15000.stp_ar,
moi_formula.moi) -- ported here (not imported) because the real modules
require a live sqlite DB connection this synthetic experiment doesn't use.
Every formula step below is byte-for-byte the same arithmetic as the real,
validated implementation. DO NOT MODIFY per the spec's explicit instruction.
"""
import numpy as np

K_SHRINKAGE = 2.0
N_BOOTSTRAP = 25


def normalize_vec(v):
    n = np.linalg.norm(v)
    return v / n if n > 1e-12 else v


def geometric_median(vectors, max_iter=60, tol=1e-6):
    if len(vectors) == 0:
        return None
    if len(vectors) <= 2:
        return normalize_vec(np.mean(vectors, axis=0))
    median = np.mean(vectors, axis=0).astype(np.float64)
    for _ in range(max_iter):
        diffs = vectors - median
        dists = np.linalg.norm(diffs, axis=1)
        nonzero = dists > 1e-9
        if not np.any(nonzero):
            break
        weights = np.zeros_like(dists)
        weights[nonzero] = 1.0 / dists[nonzero]
        weight_sum = weights.sum()
        if weight_sum < 1e-12:
            break
        new_median = (vectors[nonzero] * weights[nonzero, None]).sum(axis=0) / weight_sum
        shift = np.linalg.norm(new_median - median)
        median = new_median
        if shift < tol:
            break
    return normalize_vec(median)


def stp_raw(U_A, U_B):
    mu_A = geometric_median(U_A)
    mu_B = geometric_median(U_B)
    if mu_A is None or mu_B is None:
        return None
    return float(np.clip(np.dot(mu_A, mu_B), 0.0, 1.0))


def stp_ar(U_A, U_B, rng, k=K_SHRINKAGE, n_boot=N_BOOTSTRAP):
    """Full STP-AR: raw score + bootstrap shrinkage. Identical mechanic to
    run_validation_n15000.stp_ar() / formula_irt_fusion.channel_score()."""
    raw = stp_raw(U_A, U_B)
    if raw is None:
        return None
    boot_scores = np.empty(n_boot)
    for i in range(n_boot):
        sample_a = U_A[rng.integers(0, len(U_A), size=len(U_A))]
        sample_b = U_B[rng.integers(0, len(U_B), size=len(U_B))]
        ca = geometric_median(sample_a)
        cb = geometric_median(sample_b)
        boot_scores[i] = np.clip(np.dot(ca, cb), 0.0, 1.0)
    sigma_boot = float(np.std(boot_scores, ddof=1)) if n_boot > 1 else 0.0
    final = raw * (1.0 / (1.0 + k * sigma_boot))
    return {"raw": raw, "sigma_boot": sigma_boot, "score": final, "n_chunks": len(U_A) + len(U_B)}


def moi(W_A, W_B):
    """MOI(A,B) = cos(normalize(mean(W_A)), normalize(mean(W_B))) -- exact
    definition from moi_formula.py. Returns None if either methodology
    channel is empty (explicit limitation, not silently imputed -- per
    the spec's own instruction in A5)."""
    if len(W_A) == 0 or len(W_B) == 0:
        return None
    mu_A = normalize_vec(np.mean(W_A, axis=0))
    mu_B = normalize_vec(np.mean(W_B, axis=0))
    return float(np.clip(np.dot(mu_A, mu_B), 0.0, 1.0))


def baseline_score(U_A, U_B, W_A, W_B, rng, k=K_SHRINKAGE, n_boot=N_BOOTSTRAP):
    """BaselineScore = 0.5*STP_AR + 0.5*MOI (Part A6 fallback fusion rule --
    documented assumption #1: no combined fusion rule exists in the real
    codebase for real PDFs, so the spec's explicit fallback is used).
    If MOI is unavailable (missing methodology channel for either doc),
    falls back to STP_AR alone, weight renormalized to 1.0 -- documented,
    not silently dropped."""
    ar = stp_ar(U_A, U_B, rng, k=k, n_boot=n_boot)
    if ar is None:
        return None
    m = moi(W_A, W_B)
    if m is None:
        return {"score": ar["score"], "stp_ar": ar["score"], "stp_raw": ar["raw"],
                "sigma_boot": ar["sigma_boot"], "moi": None, "moi_available": False}
    final = 0.5 * ar["score"] + 0.5 * m
    return {"score": final, "stp_ar": ar["score"], "stp_raw": ar["raw"],
            "sigma_boot": ar["sigma_boot"], "moi": m, "moi_available": True}
