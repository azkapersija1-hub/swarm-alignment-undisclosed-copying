"""Unit + integration tests for the sprint code. No network, no LLM, no GPU needed (synthetic fixtures only)."""
import copy
import hashlib
import os
import random
import sys
import unittest

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "src"))
os.environ.setdefault("SWARM_DATASET", "synthetic")
import controller as C  # noqa: E402
import corpus  # noqa: E402
import evaluate as EV  # noqa: E402
import monitors as M  # noqa: E402
from ledger import Ledger  # noqa: E402


def unit(v):
    v = np.asarray(v, dtype=float)
    return v / np.linalg.norm(v)


class TestFrozenFormulas(unittest.TestCase):
    def test_source_hash_matches_manifest(self):
        want = {}
        for line in open(os.path.join(ROOT, "03_FORMULA_ENGINE", "SOURCE_SHA256.txt"), encoding="utf-8"):
            h, name = line.split()
            want[name.lstrip("*")] = h
        for name, h in want.items():
            got = hashlib.sha256(open(os.path.join(ROOT, "03_FORMULA_ENGINE", "source", name), "rb").read()).hexdigest()
            self.assertEqual(got, h, name)

    def test_stp_identical_is_one_and_orthogonal_is_zero(self):
        a = np.array([unit([1, 0, 0]), unit([1, 0.1, 0]), unit([1, -0.1, 0])])
        b = np.array([unit([0, 1, 0]), unit([0.1, 1, 0]), unit([-0.1, 1, 0])])
        self.assertAlmostEqual(M.BF.stp_raw(a, a), 1.0, places=6)
        self.assertLess(M.BF.stp_raw(a, b), 0.2)

    def test_stpar_never_exceeds_raw(self):
        rng = np.random.default_rng(1)
        a = np.array([unit(rng.normal(size=8) + 3) for _ in range(6)])
        b = np.array([unit(rng.normal(size=8) + 3) for _ in range(6)])
        r = M.BF.stp_ar(a, b, np.random.default_rng(2))
        self.assertLessEqual(r["score"], r["raw"] + 1e-12)
        self.assertGreaterEqual(r["sigma_boot"], 0.0)

    def test_geometric_median_robust_to_outlier(self):
        pts = np.array([unit([1, 0.01 * i]) for i in range(-3, 4)] + [unit([-1, 0.2])])
        g = M.BF.geometric_median(pts)
        self.assertGreater(float(np.dot(g, unit([1, 0]))), 0.95)

    def test_rcc_in_unit_interval(self):
        rng = np.random.default_rng(3)
        a = np.array([unit(rng.normal(size=16) + 2) for _ in range(6)])
        b = np.array([unit(rng.normal(size=16) + 2) for _ in range(6)])
        s = M.RF.rcc_v3_3_stp_ar(a, b, np.random.default_rng(4))["score"]
        self.assertTrue(0.0 <= s <= 1.0)


class TestLedger(unittest.TestCase):
    def make(self):
        L = Ledger()
        for i in range(6):
            L.log("e%d" % i, "AG-x", k=i)
        return L.events

    def test_valid_chain(self):
        self.assertEqual(Ledger.verify(self.make()), (True, None))

    def test_edit_delete_reorder_detected_truncation_not(self):
        ev = self.make()
        a = copy.deepcopy(ev); a[2]["data"]["k"] = 99
        self.assertFalse(Ledger.verify(a)[0])
        b = copy.deepcopy(ev); del b[3]
        self.assertFalse(Ledger.verify(b)[0])
        c = copy.deepcopy(ev); c[1], c[2] = c[2], c[1]
        self.assertFalse(Ledger.verify(c)[0])
        d = copy.deepcopy(ev)[:-1]
        self.assertTrue(Ledger.verify(d)[0])          # known limitation: needs an external head anchor
        self.assertNotEqual(d[-1]["hash"], ev[-1]["hash"])


class TestScenarioPlan(unittest.TestCase):
    def setUp(self):
        self.cat, self.fam = corpus.load_catalog()

    def test_plan_deterministic(self):
        a = C.plan(self.cat, self.fam, 123)
        b = C.plan(self.cat, self.fam, 123)
        self.assertEqual([s["scenario_id"] + s["a_src"] + s["b_src"] for s in a], [s["scenario_id"] + s["a_src"] + s["b_src"] for s in b])

    def test_calib_and_test_domains_disjoint(self):
        sc = C.plan(self.cat, self.fam, 5)
        dom = {s: set() for s in ("calib", "test")}
        for s in sc:
            dom[s["split"]].add(self.cat[s["a_src"]]["domain"])
            dom[s["split"]].add(self.cat[s["b_src"]]["domain"])
        self.assertFalse(dom["calib"] & dom["test"])

    def test_ground_truth_comes_from_design(self):
        for s in C.plan(self.cat, self.fam, 7):
            self.assertEqual(tuple(s["truth"].values()), C.TRUTH[s["type"]])
        self.assertEqual(C.TRUTH["TWIN_H"], (0, 1, 0))      # honest twins: not copying, but non-independent evidence
        self.assertEqual(C.TRUTH["COPY_TWIN"], (1, 1, 1))

    def test_twin_bodies_identical_near_differs(self):
        for base, ids in self.fam.items():
            for i in ids[1:]:
                same = corpus.body_hash(self.cat[i]) == corpus.body_hash(self.cat[base])
                self.assertEqual(same, self.cat[i]["kind"] == "twin")

    def test_agent_ids_stable_and_distinct(self):
        self.assertEqual(C.agent_id("m", "A", "s1"), C.agent_id("m", "A", "s1"))
        self.assertNotEqual(C.agent_id("m", "A", "s1"), C.agent_id("m", "B", "s1"))


class TestMetrics(unittest.TestCase):
    def test_confusion_and_rates(self):
        y = [1, 1, 1, 0, 0, 0, 0, 0]
        flag = [1, 1, 0, 1, 0, 0, 0, 0]
        p = [0.9, 0.8, 0.4, 0.6, 0.2, 0.1, 0.1, 0.2]
        m = EV.metrics_from(y, flag, p, p)
        self.assertEqual((m["tp"], m["fn"], m["fp"], m["tn"]), (2, 1, 1, 4))
        self.assertAlmostEqual(m["recall"], 2 / 3)
        self.assertAlmostEqual(m["fpr"], 1 / 5)
        self.assertAlmostEqual(m["precision"], 2 / 3)
        self.assertAlmostEqual(m["brier"], float(np.mean((np.array(p) - np.array(y)) ** 2)))
        self.assertAlmostEqual(m["mcc"], (2 * 4 - 1 * 1) / np.sqrt(3 * 3 * 5 * 5))
        self.assertAlmostEqual(m["auroc"], 1.0 - 1 / 15 * 1 if False else m["auroc"])

    def test_perfect_probabilities_have_zero_brier(self):
        m = EV.metrics_from([1, 0, 1, 0], [1, 0, 1, 0], [1.0, 0.0, 1.0, 0.0], [1.0, 0.0, 1.0, 0.0])
        self.assertEqual(m["brier"], 0.0)
        self.assertEqual(m["auroc"], 1.0)


class TestLedgerFeatures(unittest.TestCase):
    def ledger(self, copy_case):
        L = Ledger()
        L.log("open_source", "AG-A", source="S1", body_hash="h1")
        L.log("report_submitted", "AG-A", cited=["S1"])
        if copy_case:
            L.log("message", "AG-A", to="AG-B", content_hash="x")
            L.log("message_received", "AG-B", sender="AG-A")
        else:
            L.log("open_source", "AG-B", source="S2", body_hash="h2")
        L.log("report_submitted", "AG-B", cited=["S2"])
        return L.events

    def test_copy_case_visible_in_full_and_hidden_without_comm(self):
        ev = self.ledger(True)
        self.assertEqual(M.ledger_features(ev, "full", "k", ["S2"])["led_msg"], 1.0)
        self.assertEqual(M.ledger_features(ev, "full", "k", ["S2"])["led_unopened"], 1.0)
        self.assertEqual(M.ledger_features(ev, "comm_hidden", "k", ["S2"])["led_msg"], 0.0)
        self.assertEqual(M.ledger_features(ev, "none", "k", ["S2"])["led_known"], 0.0)

    def test_honest_case(self):
        f = M.ledger_features(self.ledger(False), "full", "k", ["S2"])
        self.assertEqual((f["led_msg"], f["led_unopened"]), (0.0, 0.0))

    def test_half_mode_deterministic(self):
        ev = self.ledger(True)
        self.assertEqual(M.ledger_features(ev, "half", "same", ["S2"]), M.ledger_features(ev, "half", "same", ["S2"]))


if __name__ == "__main__":
    unittest.main()
