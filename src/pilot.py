"""Pilot: 1 scenario per type per split with real LLM agents; prints realized-copy compliance."""
import collections
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import controller as C  # noqa: E402
import corpus  # noqa: E402

cat, fam = corpus.load_catalog()
print(len(cat), "sources;", sum(1 for s in cat.values() if s["kind"] == "twin"), "twins;", sum(1 for s in cat.values() if s["kind"] == "near"), "near")
sc = C.plan(cat, fam, 20261107)
print(len(sc), "planned", dict(collections.Counter(s["type"] for s in sc)))
t = time.time()
out = C.run_all("gemma4:31b-cloud", 0, 20261107, os.path.join(os.path.dirname(HERE), "data", "pilot.jsonl"), workers=4,
                per_split={k: 1 for k in C.PER_SPLIT})
print("pilot seconds", round(time.time() - t))
for r in out:
    print(r["scenario"]["scenario_id"], "overlap=%.2f" % r["realized_overlap"], r["report_b"]["cited_sources"], "|", r["report_b"]["independence_statement"][:80])
