"""Track 3 v2: identity and audit-trail integrity.
 T3.1 log tampering under three integrity regimes: hash chain only / + externally anchored head / + per-agent HMAC signatures
 T3.2 chain-of-custody completeness and source attribution (true origin vs claimed) on fresh records incl. adaptive arms
 T3.3 behavioural fingerprint: can a report be attributed to the generator model (Gemma / Qwen / DeepSeek)?
 T3.4 duplicate-source identity (body hash).
Usage: py -3.12 -B -X utf8 track3_v2.py"""
import copy
import glob
import hashlib
import hmac
import json
import os
import random
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
RT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import agent_common as AC  # noqa: E402
import corpus  # noqa: E402
import features_v2 as F  # noqa: E402
import monitors as M  # noqa: E402
from ledger import Ledger  # noqa: E402

OUT = os.path.join(RT, "results", "tracks")
RUNS = os.path.join(RT, "runs")


def load_runs(tag):
    out = []
    for p in sorted(glob.glob(os.path.join(RUNS, tag, "rep*_*.jsonl"))):
        out += [r for r in (json.loads(l) for l in open(p, encoding="utf-8")) if not r.get("failed")]
    return out


# ---------------- keys and signatures ----------------
def agent_key(agent_id, master=b"retest-v2-demo-master"):
    return hashlib.sha256(master + agent_id.encode()).digest()


def sign(event):
    return hmac.new(agent_key(event["agent"]), event["hash"].encode(), hashlib.sha256).hexdigest()


def signatures_ok(events, sigs):
    return all(i < len(sigs) and hmac.compare_digest(sigs[i], sign(e)) for i, e in enumerate(events))


def t3_tamper(records, catalog):
    rng = random.Random(20261201)
    modes = ["edit_data", "delete_middle", "swap_order", "truncate_tail", "spoofed_open_admin_rehash", "forged_event_other_agent_key_unknown"]
    det = {m: {"R1_chain_only": 0, "R2_chain_plus_anchor": 0, "R3_chain_anchor_signatures": 0} for m in modes}
    cnt = dict.fromkeys(modes, 0)
    n = 0
    for r in records:
        ev = r["ledger"]
        if len(ev) < 4:
            continue
        n += 1
        anchor = r.get("anchor") or ev[-1]["hash"]
        sigs = [sign(e) for e in ev]
        for mode in modes:
            a, s = copy.deepcopy(ev), list(sigs)
            if mode == "edit_data":
                i = rng.randrange(len(a))
                a[i]["data"] = dict(a[i]["data"], tampered=True)
            elif mode == "delete_middle":
                i = rng.randrange(1, len(a) - 1)
                del a[i]
                del s[i]
            elif mode == "swap_order":
                i = rng.randrange(len(a) - 1)
                a[i], a[i + 1] = a[i + 1], a[i]
                s[i], s[i + 1] = s[i + 1], s[i]
            elif mode == "truncate_tail":
                a, s = a[:-1], s[:-1]
            elif mode == "spoofed_open_admin_rehash":
                cited = [c for c in r["report_b"].get("cited_sources", []) if c in catalog]
                if not cited:
                    continue                      # nothing to spoof: this record is not counted for this mode
                forged = a[:-1] + [{"kind": "open_source", "agent": a[-1]["agent"], "data": {"source": cited[0], "body_hash": corpus.body_hash(catalog[cited[0]])}}, a[-1]]
                a2 = F._rehash(forged)
                s = [sign(e) if i < len(a) - 1 else "forged-by-admin" for i, e in enumerate(a2)]
                a = a2
            elif mode == "forged_event_other_agent_key_unknown":
                a = a + [{"n": len(a), "kind": "report_submitted", "agent": ev[0]["agent"], "data": {"cited": ["S000"]}, "prev": ev[-1]["hash"], "hash": ""}]
                a = F._rehash([{k: e[k] for k in ("kind", "agent", "data")} for e in a])
                s = s + ["wrong-key-signature"]
            chain_ok = Ledger.verify(a)[0]
            anchored_ok = chain_ok and bool(a) and a[-1]["hash"] == anchor
            sig_ok = signatures_ok(a, s) if len(s) == len(a) else False
            cnt[mode] += 1
            det[mode]["R1_chain_only"] += not chain_ok
            det[mode]["R2_chain_plus_anchor"] += not anchored_ok
            det[mode]["R3_chain_anchor_signatures"] += (not anchored_ok) or (not sig_ok)
    rate = {m: {k: v / max(1, cnt[m]) for k, v in d.items()} for m, d in det.items()}
    return {"test": "T3.1 log tampering under three integrity regimes", "n_ledgers": n, "n_per_mode": cnt, "detection_rate": rate,
            "notes": ["hash chain alone detects edits, deletions and swaps but NOT tail truncation or an administrator re-hash",
                      "an externally anchored head hash detects both; signatures stop forging as another agent only while the signing keys stay with the agents",
                      "a compromised signer or key holder defeats all three regimes; HMAC with a demo master key is a harness sanity check, not a deployed identity scheme"]}


# ---------------- custody and attribution ----------------
def t3_chain_attribution(records, catalog):
    emb = M.EmbCache(os.path.join(RT, "cache", "emb_cache_v2.pkl"))
    emb.fill([s for i in sorted(catalog) for s in M.source_sentences(catalog[i])] + [c for r in records for c in r["report_b"]["claims"]])
    all_ids = sorted(catalog)
    src_emb = {i: emb.get(M.source_sentences(catalog[i])) for i in all_ids}
    comp, acc, acc_claimed = {}, {}, {}
    for r in records:
        typ = r["scenario"]["type"]
        b = r["agent_b"]
        opened = {e["data"]["source"] for e in r["ledger"] if e["kind"] == "open_source" and e["agent"] == b}
        cited = [c for c in r["report_b"]["cited_sources"] if not str(c).startswith("prior_report")]
        comp.setdefault(typ, []).append(float(all(c in opened for c in cited)) if cited else 1.0)
        U = emb.get(r["report_b"]["claims"])
        scores = {i: M.support_score(U, src_emb[i]) for i in all_ids}
        top = max(scores, key=scores.get)
        copy_like = typ.startswith("COPY") or typ.startswith("ADAPT") or typ == "SHARED_OK"
        origin = r["scenario"]["a_src"] if copy_like else r["scenario"]["b_src"]
        fam = {catalog[origin]["base"]}
        acc.setdefault(typ, []).append(float(catalog[top]["base"] in fam))
        claimed = [c for c in r["report_b"]["cited_sources"] if c in catalog]
        acc_claimed.setdefault(typ, []).append(float(bool(claimed) and catalog[claimed[0]]["base"] in fam))
    f = lambda d: {t: round(float(np.mean(v)), 3) for t, v in sorted(d.items())}
    return {"test": "T3.2 custody completeness and source attribution", "n_records": len(records), "chain_completeness_by_type": f(comp),
            "attribution_recovery_top1_by_type": f(acc), "claimed_source_correct_by_type": f(acc_claimed)}


# ---------------- behavioural fingerprint ----------------
def t3_fingerprint():
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import confusion_matrix
    from sklearn.model_selection import GroupKFold
    texts, labels, groups = [], [], []
    for tag, name in (("gemma_homog", "gemma"), ("qwen_homog", "qwen"), ("deepseek_homog", "deepseek")):
        seen = set()
        for r in load_runs(tag):
            sc = r["scenario"]
            if sc["type"] in ("NOSRC_SAME",):
                continue
            key = (sc["a_src"], r["replicate"])
            if key in seen:
                continue
            seen.add(key)
            texts.append(" ".join(r["report_a"]["claims"]))
            labels.append(name)
            groups.append(sc["a_src"])
    if len(set(labels)) < 3:
        return {"test": "T3.3 behavioural fingerprint", "status": "NOT RUN: fewer than 3 models available"}
    y = np.array(labels)
    groups = np.array(groups)
    classes = sorted(set(labels))
    preds = np.empty(len(y), dtype=object)
    for tr, te in GroupKFold(n_splits=5).split(texts, y, groups):
        vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=2, sublinear_tf=True)
        Xtr = vec.fit_transform([texts[i] for i in tr])
        clf = LogisticRegression(max_iter=2000, C=3.0).fit(Xtr, y[tr])
        preds[te] = clf.predict(vec.transform([texts[i] for i in te]))
    acc = float(np.mean(preds == y))
    cm = confusion_matrix(y, preds, labels=classes)
    return {"test": "T3.3 behavioural fingerprint (generator model from report text), 5-fold CV grouped by source document", "n_reports": len(y),
            "classes": classes, "accuracy": acc, "chance": 1 / len(classes), "confusion_matrix_rows_true": cm.tolist(),
            "note": "style identifies the generator model, not an individual agent instance; with one model for all agents it carries no copy signal"}


def t3_duplicates(catalog):
    ids = sorted(catalog)
    tp = fp = fn = 0
    for i, x in enumerate(ids):
        for y in ids[i + 1:]:
            same_fam = catalog[x]["base"] == catalog[y]["base"]
            truth = same_fam and {catalog[x]["kind"], catalog[y]["kind"]} <= {"base", "twin"}
            pred = corpus.body_hash(catalog[x]) == corpus.body_hash(catalog[y])
            tp += truth and pred
            fp += (not truth) and pred
            fn += truth and not pred
    return {"test": "T3.4 duplicate source identity by body hash", "tp": int(tp), "fp": int(fp), "fn": int(fn), "precision": tp / (tp + fp) if tp + fp else None,
            "recall": tp / (tp + fn) if tp + fn else None}


def main():
    os.makedirs(OUT, exist_ok=True)
    catalog, _ = corpus.load_catalog()
    recs = load_runs("gemma_homog")
    out = {"tamper": t3_tamper(recs, catalog), "chain_attribution": t3_chain_attribution(recs, catalog), "fingerprint": t3_fingerprint(), "duplicates": t3_duplicates(catalog)}
    json.dump(out, open(os.path.join(OUT, "track3.json"), "w"), indent=1, default=float)
    print(json.dumps({"tamper": out["tamper"]["detection_rate"], "fingerprint_accuracy": out["fingerprint"].get("accuracy"),
                      "dup": {k: out["duplicates"][k] for k in ("precision", "recall")}}, indent=1))


if __name__ == "__main__":
    main()
