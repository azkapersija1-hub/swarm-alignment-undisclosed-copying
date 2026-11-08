"""Tests of the statistics core: equality with the frozen tri-state function, NaN abstention, calibration/test separation."""
import os
import sys
import unittest

import numpy as np

RT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RT, "src"))
sys.path.insert(0, os.path.join(RT, "prereg"))
import stats_v2 as S  # noqa: E402
import candidate_formulas as CF  # noqa: E402


class TestVerdictEquality(unittest.TestCase):
    def test_local_verdict_equals_frozen_function_on_random_inputs(self):
        rng = np.random.default_rng(7)
        for _ in range(3000):
            m = int(rng.integers(3, 8))
            s_own, s_a = rng.uniform(0, 1, m), rng.uniform(0, 1, m)
            ic, has_src, known = int(rng.integers(0, 2)), int(rng.integers(0, 2)), int(rng.integers(0, 2))
            unop, shb = int(rng.integers(0, 2)), int(rng.integers(0, 2))
            disg, fom = float(rng.uniform(-0.2, 1.2)), float(rng.uniform(-1, 1))
            q_lo = float(rng.uniform(0.05, 0.4))
            q_hi = float(rng.uniform(q_lo, 0.9))
            frozen = CF.tri_state_claim_ledger_verdict(s_own, s_a, ic, has_src, known, unop, shb, disg, f_omit=fom, q_lo=q_lo, q_hi=q_hi)
            base = CF.tri_state_claim_ledger_verdict(s_own, s_a, ic, has_src, known, unop, shb, disg, f_omit=fom, q_lo=0.0, q_hi=1e9)
            local = S.verdict_from_components(base["r_reuse"], has_src, known, float(np.clip(disg, 0, 1)), ic, base["score"], q_lo, q_hi)
            self.assertEqual(frozen["verdict"], local)


def rows(n, seed, shift):
    rng = np.random.default_rng(seed)
    out = []
    for i in range(n):
        y = i % 2
        x = rng.normal(shift * y, 1.0)
        out.append({"type": "T%d" % y, "replicate": 0, "cluster": "c%d" % (i // 2), "copy_u": y, "truth": {"copying_occurred": y, "evidence_nonindependent": y,
                    "provenance_claim_false": y}, "x": x, "xs": [x, rng.normal()], "llm": {"m": {"report_only": {"p_copying": 0.5 + 0.1 * (x > 0)}}}})
    return out


class TestFitApply(unittest.TestCase):
    def test_score_kind_threshold_from_calibration_negatives_only(self):
        cal, tst = rows(200, 1, 2.0), rows(200, 2, 2.0)
        res = S.fit_apply(("score", lambda r: r["x"]), cal, tst, "A_primary")
        neg = np.array([r["x"] for r in cal if r["copy_u"] == 0])
        self.assertAlmostEqual(res["thr"], float(np.quantile(neg, 0.95)))
        m = S.summarize(S.pool([res]))
        self.assertGreater(m["auroc"], 0.8)
        self.assertLess(m["fpr"], 0.30)      # 95th percentile of ~100 calibration negatives is noisy; exact equality is asserted above

    def test_nan_scores_are_abstained_not_imputed(self):
        cal, tst = rows(200, 3, 2.0), rows(100, 4, 2.0)
        for r in tst[:20]:
            r["x"] = float("nan")
        res = S.fit_apply(("score", lambda r: r["x"]), cal, tst, "A_primary")
        self.assertEqual(int((~res["valid"]).sum()), 20)
        m = S.summarize(S.pool([res]))
        self.assertAlmostEqual(m["coverage"], 0.8)
        self.assertEqual(m["n"], 80)

    def test_unfittable_returns_none(self):
        cal = rows(6, 5, 2.0)
        self.assertIsNone(S.fit_apply(("score", lambda r: r["x"]), cal, cal, "A_primary"))

    def test_logit_kind_runs_and_gives_probabilities(self):
        cal, tst = rows(200, 6, 2.0), rows(100, 7, 2.0)
        res = S.fit_apply(("logit", lambda r: r["xs"]), cal, tst, "B")
        self.assertTrue(np.all((res["p"] >= 0) & (res["p"] <= 1)))

    def test_llm_kind_uses_target_key(self):
        cal, tst = rows(200, 8, 2.0), rows(100, 9, 2.0)
        res = S.fit_apply(("llm", ("m", "report_only")), cal, tst, "A_primary")
        self.assertIsNotNone(res)

    def test_bootstrap_ci_brackets_point_estimate_for_auroc(self):
        cal, tst = rows(300, 10, 2.0), rows(300, 11, 2.0)
        P = S.pool([S.fit_apply(("score", lambda r: r["x"]), cal, tst, "A_primary")])
        m = S.summarize(P)
        lo, hi = S.boot_ci(P, np.random.default_rng(0), n_boot=200, which=("auroc",))["auroc"]
        self.assertLessEqual(lo, m["auroc"] + 1e-9)
        self.assertGreaterEqual(hi, m["auroc"] - 1e-9)


if __name__ == "__main__":
    unittest.main()
