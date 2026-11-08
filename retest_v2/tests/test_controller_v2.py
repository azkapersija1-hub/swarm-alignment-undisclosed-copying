"""Unit tests for controller_v2 using a fake LLM (no network, no credits)."""
import json
import os
import sys
import tempfile
import unittest

SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
sys.path.insert(0, SRC)
import controller_v2 as V  # noqa: E402
import controller as C  # noqa: E402
import corpus  # noqa: E402
import llm  # noqa: E402
from ledger import Ledger  # noqa: E402

CALLS = []


def fake_chat_any(model, system, user, **kw):
    CALLS.append((model, user[:60]))
    if "oversight monitor" in system:
        return {"text": json.dumps({"p_copying": 0.9, "p_nonindependent": 0.9, "p_false_provenance": 0.9}), "seconds": 0.0}
    obj = {"claims": ["Claim number %d about topic %d states a fact with value 42." % (i, len(CALLS) % 5) for i in range(5)],
           "method": ["The evidence was gathered from a document review."], "cited_sources": ["S000"],
           "independence_statement": "My evidence is independent."}
    return {"text": json.dumps(obj), "seconds": 0.0, "eval_count": 10}


class TestControllerV2(unittest.TestCase):
    def setUp(self):
        CALLS.clear()
        self._orig = llm.chat_any
        llm.chat_any = fake_chat_any
        self.catalog, self.fam = corpus.load_catalog()

    def tearDown(self):
        llm.chat_any = self._orig

    def test_plan_has_adaptive_arms_and_counts(self):
        scen = V.plan_v2(self.catalog, self.fam, 20261201, V.per_split_v2(10))
        for t in V.ADAPT:
            for split in ("calib", "test"):
                self.assertEqual(sum(1 for s in scen if s["type"] == t and s["split"] == split), 10)
        self.assertTrue(all(s["truth"]["provenance_claim_false"] == 1 for s in scen if s["type"] in V.ADAPT))
        self.assertEqual(len({s["scenario_id"] for s in scen}), len(scen))

    def test_plan_a_and_b_in_same_split_and_split2_has_second_source(self):
        scen = V.plan_v2(self.catalog, self.fam, 20261202, V.per_split_v2(10))
        dom = C.split_domains(self.catalog, 20261202)
        for s in scen:
            self.assertEqual(dom[self.catalog[s["a_src"]]["domain"]], s["split"])
            self.assertEqual(dom[self.catalog[s["b_src"]]["domain"]], s["split"])
            if s["type"] == "ADAPT_SPLIT_2":
                self.assertIn("a2_src", s)
                self.assertNotIn(s["a2_src"], (s["a_src"], s["b_src"]))

    def test_base_plan_identical_to_v1_plan(self):
        v1 = C.plan(self.catalog, self.fam, 20261203, C.per_split_for_dataset())
        v2 = [s for s in V.plan_v2(self.catalog, self.fam, 20261203, V.per_split_v2(10)) if s["type"] not in V.ADAPT]
        self.assertEqual([s["scenario_id"] for s in v1], [s["scenario_id"] for s in v2])
        self.assertEqual([s["a_src"] for s in v1], [s["a_src"] for s in v2])

    def _run_type(self, typ, model_a="m-a", model_b="m-b"):
        scen = [s for s in V.plan_v2(self.catalog, self.fam, 20261204, V.per_split_v2(2)) if s["type"] == typ][0]
        need_a = [scen["a_src"]] + ([scen["a2_src"]] if "a2_src" in scen else [])
        honest_a = {i: C.honest_report(model_a, self.catalog[i], 0) for i in need_a}
        honest_b = {scen["b_src"]: C.honest_report(model_b, self.catalog[scen["b_src"]], 0)}
        return V.run_scenario_v2(scen, self.catalog, honest_a, honest_b, model_a, model_b, 0)

    def test_every_type_produces_valid_chain_and_anchor(self):
        for typ in C.TYPES_ALL + list(V.ADAPT):
            rec = self._run_type(typ)
            ok, bad = Ledger.verify(rec["ledger"])
            self.assertTrue(ok, typ)
            self.assertEqual(rec["anchor"], rec["ledger"][-1]["hash"], typ)

    def test_out_of_band_has_no_message_events_but_opens_source(self):
        rec = self._run_type("ADAPT_OUT_OF_BAND")
        kinds = [e["kind"] for e in rec["ledger"]]
        self.assertNotIn("message", kinds)
        self.assertIn("open_source", [e["kind"] for e in rec["ledger"] if e["agent"] == rec["agent_b"]])

    def test_split2_logs_two_upstream_agents_and_first_submitter_is_a1(self):
        rec = self._run_type("ADAPT_SPLIT_2")
        submitted = [e["agent"] for e in rec["ledger"] if e["kind"] == "report_submitted"]
        self.assertEqual(submitted[0], rec["agent_a"])
        self.assertEqual(submitted[-1], rec["agent_b"])
        self.assertEqual(sum(1 for e in rec["ledger"] if e["kind"] == "message"), 2)
        self.assertIn("report_a2", rec)

    def test_surrogate_loop_is_bounded_and_records_trace(self):
        rec = self._run_type("ADAPT_SURROGATE_K3")
        self.assertGreaterEqual(len(rec["surrogate_trace"]), 1)
        self.assertLessEqual(len(rec["surrogate_trace"]), 1 + V.SURR_MAX_ROUNDS)

    def test_agent_ids_differ_when_models_differ(self):
        rec = self._run_type("COPY_PARA", "model-x", "model-y")
        self.assertNotEqual(rec["agent_a"], rec["agent_b"])
        self.assertEqual(rec["model_b"], "model-y")

    def test_failure_is_recorded_not_raised_or_imputed(self):
        def broken(model, system, user, **kw):
            raise RuntimeError("boom")
        llm.chat_any = broken
        scen = V.plan_v2(self.catalog, self.fam, 20261205, V.per_split_v2(1))[0]
        rec = V.safe_run(scen, self.catalog, {}, {}, "m", "m", 0)
        self.assertTrue(rec["failed"])
        self.assertIn("error", rec)

    def test_run_all_writes_file_and_counts(self):
        with tempfile.TemporaryDirectory() as d:
            ps = {k: 1 for k in V.per_split_v2(1)}
            out = V.run_all_v2("m-a", "m-a", 0, 20261206, os.path.join(d, "x", "rep0.jsonl"), workers=2, per_split=ps, log=lambda *a: None)
            lines = [json.loads(l) for l in open(os.path.join(d, "x", "rep0.jsonl"), encoding="utf-8")]
            self.assertEqual(len(lines), len(out))
            self.assertEqual(len(lines), 2 * len(ps))
            self.assertFalse(any(r.get("failed") for r in lines))


if __name__ == "__main__":
    unittest.main()
