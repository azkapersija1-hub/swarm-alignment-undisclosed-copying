"""rcc_v3_3_formula.py -- RCC-v3.3 (Spectral Effective Rank Gating, SERG).
Fourth attempt at fixing v2's fixed-threshold miscalibration, per the
cumulative lesson from v3/v3.1/v3.2's failures: work directly in the
1024-dim embedding space via the pairwise similarity matrix, not a 1D
projection (r_i = cos(chunk_i, g)) -- v3.2 showed bimodality can be
symmetric around g and vanish under that projection. No bootstrap
(v3.1's noise-vs-structure confound). No externally reused constant for
the heterogeneity scale (v3's TAU_MIN mismatch) -- SER is a property of
the document's own similarity matrix, self-contained per document.

Implemented exactly per the user-supplied spec (2026-08-13), hyperparameters
frozen as given, not tuned after seeing any result.
"""
import numpy as np
from baseline_formula import geometric_median, normalize_vec, moi

# === Spectral gating (NEW in v3.3) ===
SER_ALPHA = 10.0
CONFIDENCE_THRESHOLD = 0.85
GATE_SHARPNESS = 20.0
LAMBDA_MAX = 0.50
MAX_N_FOR_EIGEN = 200

# === Attention consensus (same as v1/v2) ===
TAU_MIN = 0.05
C_TAU = 1.0
EPS_SMOOTH = 0.10

# === Bootstrap AR (same as baseline) ===
N_BOOT = 25
K_SHRINK = 2.0

MIN_N_FOR_CONSENSUS = 3


def spectral_confidence(X, rng=None):
    """Confidence based on Spectral Effective Rank of the pairwise
    similarity matrix. Works directly in the high-dimensional embedding
    space. Returns confidence in [0,1] -- high (~1.0) for unimodal
    documents, low (~0.0) for multimodal documents."""
    n = len(X)
    if n < MIN_N_FOR_CONSENSUS:
        return 1.0

    if n > MAX_N_FOR_EIGEN:
        rng_local = rng if rng is not None else np.random.default_rng()
        idx = rng_local.choice(n, MAX_N_FOR_EIGEN, replace=False)
        X_work = X[idx]
        n_work = MAX_N_FOR_EIGEN
    else:
        X_work = X
        n_work = n

    S = X_work @ X_work.T
    eigenvalues = np.linalg.eigvalsh(S)
    eigenvalues = np.clip(eigenvalues, 0.0, None)
    eigenvalues = eigenvalues[::-1]

    total_var = np.sum(eigenvalues)
    if total_var < 1e-12:
        return 1.0

    p = eigenvalues / total_var
    entropy = -np.sum(p * np.log(p + 1e-12))
    ser = np.exp(entropy)

    n_ser = ser / n_work
    normalized_multimodality = (n_ser - 1.0 / n_work) / (1.0 - 1.0 / n_work)
    normalized_multimodality = np.clip(normalized_multimodality, 0.0, 1.0)

    confidence = np.exp(-SER_ALPHA * normalized_multimodality)
    return float(np.clip(confidence, 0.0, 1.0)), float(ser)


def rcc_v3_3_centroid(X, rng=None, return_diagnostics=False):
    X = np.asarray(X)
    n = len(X)
    if n == 0:
        raise ValueError("empty document")

    g = geometric_median(X)

    if n < MIN_N_FOR_CONSENSUS:
        if return_diagnostics:
            return g, {"n_chunks": n, "SER": None, "confidence": None, "gate": None,
                       "lambda": 0.0, "reason": f"n<{MIN_N_FOR_CONSENSUS}"}
        return g

    confidence, ser = spectral_confidence(X, rng=rng)

    gate_x = GATE_SHARPNESS * (confidence - CONFIDENCE_THRESHOLD)
    gate = float(1.0 / (1.0 + np.exp(-np.clip(gate_x, -500, 500))))
    lam = LAMBDA_MAX * gate

    r = X @ g
    med_r = float(np.median(r))
    mad_r = float(np.median(np.abs(r - med_r)))
    sigma_r = 1.4826 * mad_r
    tau = max(TAU_MIN, C_TAU * sigma_r)

    logits = (r - r.max()) / tau
    exp_logits = np.exp(logits)
    beta = exp_logits / exp_logits.sum()
    alpha = (1.0 - EPS_SMOOTH) * beta + EPS_SMOOTH / n

    a = normalize_vec((alpha[:, None] * X).sum(axis=0))

    c = normalize_vec((1.0 - lam) * g + lam * a)

    if not return_diagnostics:
        return c

    diag = {"n_chunks": n, "SER": ser, "confidence": confidence, "gate": gate,
            "lambda": float(lam), "median_r": med_r, "mad_r": mad_r}
    return c, diag


def rcc_v3_3_raw(U_A, U_B, rng=None, return_diagnostics=False):
    if return_diagnostics:
        c_A, diag_A = rcc_v3_3_centroid(U_A, rng=rng, return_diagnostics=True)
        c_B, diag_B = rcc_v3_3_centroid(U_B, rng=rng, return_diagnostics=True)
    else:
        c_A = rcc_v3_3_centroid(U_A, rng=rng)
        c_B = rcc_v3_3_centroid(U_B, rng=rng)
    score = float(np.clip(np.dot(c_A, c_B), 0.0, 1.0))
    if return_diagnostics:
        return score, {"A": diag_A, "B": diag_B}
    return score


def rcc_v3_3_stp_ar(U_A, U_B, rng, k=K_SHRINK, n_boot=N_BOOT, track_duplicate_rate=False):
    U_A, U_B = np.asarray(U_A), np.asarray(U_B)
    raw, diag = rcc_v3_3_raw(U_A, U_B, rng=rng, return_diagnostics=True)

    boot_scores = np.empty(n_boot)
    dup_rates = []
    for i in range(n_boot):
        idx_a = rng.integers(0, len(U_A), size=len(U_A))
        idx_b = rng.integers(0, len(U_B), size=len(U_B))
        if track_duplicate_rate:
            dup_rates.append(1.0 - len(set(idx_a.tolist())) / len(idx_a))
        boot_scores[i] = rcc_v3_3_raw(U_A[idx_a], U_B[idx_b], rng=rng)
    sigma_boot = float(np.std(boot_scores, ddof=1)) if n_boot > 1 else 0.0
    final = raw * (1.0 / (1.0 + k * sigma_boot))

    result = {"raw": raw, "sigma_boot": sigma_boot, "score": final,
              "n_chunks": len(U_A) + len(U_B), "diagnostics": diag}
    if track_duplicate_rate:
        result["mean_bootstrap_duplicate_rate"] = float(np.mean(dup_rates))
    return result


def rcc_v3_3_score_with_moi(U_A, U_B, W_A, W_B, rng, k=K_SHRINK, n_boot=N_BOOT):
    ar = rcc_v3_3_stp_ar(U_A, U_B, rng, k=k, n_boot=n_boot)
    m = moi(W_A, W_B)
    if m is None:
        return {"score": ar["score"], "rcc_v3_3_ar": ar["score"], "rcc_v3_3_raw": ar["raw"],
                "sigma_boot": ar["sigma_boot"], "moi": None, "moi_available": False}
    final = 0.5 * ar["score"] + 0.5 * m
    return {"score": final, "rcc_v3_3_ar": ar["score"], "rcc_v3_3_raw": ar["raw"],
            "sigma_boot": ar["sigma_boot"], "moi": m, "moi_available": True}
