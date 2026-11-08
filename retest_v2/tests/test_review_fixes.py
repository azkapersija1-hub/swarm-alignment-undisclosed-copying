"""Tests for the defects found by the independent code review (see prereg/DEVIATIONS.md)."""
import os
import sys
import unittest

import numpy as np

RT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RT, "src"))
import stats_v2 as S  # noqa: E402
import evaluate_v2 as E  # noqa: E402
import features_v2 as F  # noqa: E402


def pool_of(types, clusters):
    n = len(types)
    return {"y": np.zeros(n), "s": np.zeros(n), "p": np.zeros(n), "flag": np.zeros(n, bool), "valid": np.ones(n, bool), "abstain": np.zeros(n, bool),
            "types": list(types), "clusters": list(clusters), "prev": 0.5, "thr": 0.5}


class TestAlignment(unittest.TestCase):
    def test_aligned_requires_identical_rows(self):
        a = pool_of(["x", "y"], [(0, "d1"), (0, "d2")])
        b = pool_of(["x", "y"], [(0, "d1"), (0, "d2")])
        c = pool_of(["x", "y"], [(1, "d1"), (1, "d2")])       # same length, different replicate
        self.assertTrue(S.aligned(a, b))
        self.assertFalse(S.aligned(a, c))
        self.assertFalse(S.aligned(a, None))

    def test_f31_gate_refuses_misaligned_pools(self):
        pooled = {("F11x candidate ensemble", "A_primary"): pool_of(["x", "y"], [(0, "d1"), (0, "d2")]),
                  ("F9b ensemble + source checks", "A_primary"): pool_of(["x", "y"], [(1, "d1"), (1, "d2")])}
        g = E.f31_gate(pooled)
        self.assertFalse(g["promote"])
        self.assertIn("error", g)

    def test_doc_key_ignores_replicate(self):
        self.assertEqual(S.doc_key((0, "S001")), S.doc_key((3, "S001")))


class TestNaNFalsifiers(unittest.TestCase):
    def test_nan_is_undetermined_not_pass(self):
        nan = float("nan")
        self.assertIsNone(E.lt(nan, 0.8))
        self.assertIsNone(E.anyof(E.lt(nan, 0.8), E.gt(0.1, 0.2)))
        self.assertTrue(E.anyof(E.lt(nan, 0.8), E.gt(0.3, 0.2)))
        self.assertFalse(E.anyof(E.lt(0.9, 0.8), E.gt(0.1, 0.2)))


class TestRCalExclusion(unittest.TestCase):
    def test_identical_centroid_is_excluded_even_from_another_scenario(self):
        v = np.array([1.0, 0.0, 0.0])
        w = np.array([0.0, 1.0, 0.0])
        obj = {"mu_cal": np.zeros(3), "cents": [("scn-a", v), ("scn-b", v.copy()), ("scn-c", w)]}
        rows = F.r_cal_for(obj, "scn-a", (v,))
        self.assertEqual(rows.shape[0], 1)             # the copy of v from scn-b must be gone
        self.assertTrue(np.allclose(rows[0], w))

    def test_without_own_vectors_only_same_scenario_is_removed(self):
        v = np.array([1.0, 0.0, 0.0])
        obj = {"mu_cal": np.zeros(3), "cents": [("scn-a", v), ("scn-b", v.copy())]}
        self.assertEqual(F.r_cal_for(obj, "scn-a").shape[0], 1)


class TestSeedDiffers(unittest.TestCase):
    def test_hash_seed_differs_across_rows_of_one_split(self):
        import hashlib
        seed = lambda sid, rep: int(hashlib.sha256(("%s|%s" % (sid, rep)).encode()).hexdigest()[:8], 16) % (2 ** 31)
        self.assertNotEqual(seed("calib-IND_SAME-00", 0), seed("calib-IND_SAME-01", 0))
        old = lambda sid: int(sid.replace("-", "").encode().hex()[:8], 16)
        self.assertEqual(old("calib-IND_SAME-00"), old("calib-COPY_PARA-05"))      # documents the v1 defect


if __name__ == "__main__":
    unittest.main()
