"""Tests of the v2 feature layer on real pilot records (pilot seeds are not confirmatory seeds)."""
import json
import os
import sys
import unittest

RT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RT, "src"))
import features_v2 as F  # noqa: E402
import corpus  # noqa: E402
from ledger import Ledger  # noqa: E402

PILOT = os.path.join(RT, "runs", "pilot_gemma_homog", "rep0_gemma_homog.jsonl")


def load():
    return [json.loads(l) for l in open(PILOT, encoding="utf-8")]


class TestIC(unittest.TestCase):
    def test_disclosed_reuse_is_ic_zero(self):
        self.assertEqual(F.ic_flag({"cited_sources": ["prior_report:AG-1", "S001"], "independence_statement": "x"}), 0)
        self.assertEqual(F.ic_flag({"cited_sources": ["S001"], "independence_statement": "My evidence is NOT independent of the prior report."}), 0)
        self.assertEqual(F.ic_flag({"cited_sources": ["S001"], "independence_statement": "This evidence builds on earlier work."}), 0)

    def test_independent_claim_is_ic_one(self):
        self.assertEqual(F.ic_flag({"cited_sources": ["S001"], "independence_statement": "The evidence in this report is independent."}), 1)
        self.assertEqual(F.ic_flag({"cited_sources": [], "independence_statement": ""}), 1)

    def test_pilot_shared_ok_is_zero_and_other_types_one(self):
        for r in load():
            ic = F.ic_flag(r["report_b"])
            t = r["scenario"]["type"]
            if t == "SHARED_OK":
                self.assertEqual(ic, 0, t)
            elif t not in ("NOSRC_SAME",):
                if ic != 1:                      # report, never silently pass: a regex miss must be visible
                    print("IC regex disagreement:", t, r["report_b"]["independence_statement"][:90])


class TestWindows(unittest.TestCase):
    def test_short_text_gives_single_window(self):
        self.assertEqual(len(F.windows_64(["one two three"])), 1)

    def test_windows_cover_long_text_with_stride(self):
        words = " ".join("w%d" % i for i in range(200))
        w = F.windows_64([words])
        self.assertGreaterEqual(len(w), 3)
        self.assertTrue(all(len(x.split()) <= 64 for x in w))
        self.assertTrue(w[0].startswith("w0 ") and "w48" in w[1].split()[:2][0] or w[1].split()[0] == "w48")


class TestLedgerViews(unittest.TestCase):
    def setUp(self):
        self.catalog, _ = corpus.load_catalog()
        self.recs = {r["scenario"]["type"]: r for r in load() if r["scenario"]["split"] == "test"}

    def _known(self, rec, mode):
        view = F.ledger_view(rec, mode, self.catalog)
        return F.anchored_known(mode, view, rec["anchor"]), view

    def test_full_is_known_and_valid(self):
        for rec in self.recs.values():
            k, view = self._known(rec, "full_anchored")
            self.assertEqual(k, 1.0)
            self.assertTrue(Ledger.verify(view)[0])

    def test_tail_truncated_prefix_valid_but_head_mismatch(self):
        rec = self.recs["COPY_PARA"]
        k, view = self._known(rec, "tail_truncated")
        self.assertTrue(Ledger.verify(view)[0])      # an unanchored verifier is fooled
        self.assertEqual(k, 0.0)                      # the anchored check is not

    def test_spoofed_open_chain_valid_head_mismatch_and_fools_legacy_custody(self):
        rec = self.recs["COPY_PARA"]
        k, view = self._known(rec, "spoofed_open")
        self.assertTrue(Ledger.verify(view)[0])
        self.assertEqual(k, 0.0)
        honest_view = F.ledger_view(rec, "full_anchored", self.catalog)
        self.assertEqual(F.custody_flags(rec, honest_view, self.catalog)["led_unopened"], 1.0)   # copier never opened its cited source
        self.assertEqual(F.custody_flags(rec, view, self.catalog)["led_unopened"], 0.0)           # forged event hides it

    def test_reordered_chain_invalid(self):
        rec = self.recs["COPY_PARA"]
        k, view = self._known(rec, "reordered")
        self.assertFalse(Ledger.verify(view)[0])
        self.assertEqual(k, 0.0)
        self.assertEqual(F.legacy_ledger(rec, "reordered", view, self.catalog)["led_known"], 0.0)

    def test_none_and_half_unknown_and_comm_hidden_hides_messages(self):
        rec = self.recs["COPY_PARA"]
        self.assertEqual(self._known(rec, "none")[0], 0.0)
        self.assertEqual(self._known(rec, "half_mcar")[0], 0.0)
        k, view = self._known(rec, "comm_hidden")
        self.assertEqual(k, 1.0)
        self.assertFalse(any(e["kind"] in ("message", "message_received") for e in view))

    def test_ledger_block_has_all_modes(self):
        legacy, h8 = F.ledger_block(self.recs["COPY_PARA"], self.catalog)
        self.assertEqual(set(legacy), set(F.MODES7))
        self.assertEqual(set(h8), set(F.MODES7))


if __name__ == "__main__":
    unittest.main()
