"""Retest v2 feature layer: inputs of the frozen candidate formulas, seven log-degradation modes, three granularities.
Pure functions of (record, catalog, embedding cache). Ground truth is never read here, except where a function receives
calibration-split labels explicitly (R_cal, mu_cal, nosrc baseline), which are fitted on calibration data only."""
import hashlib
import os
import re
import sys

import numpy as np

RT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RT, "prereg"))
import controller_v2  # noqa: F401,E402  (sets SWARM_DATASET=tls and the v1 import path)
import candidate_formulas as CF  # noqa: E402  (frozen, hash in PREREG_LOCK_STAGE1.json)
import corpus  # noqa: E402
import monitors as M  # noqa: E402
from ledger import Ledger  # noqa: E402

MODES7 = ["full_anchored", "comm_hidden", "half_mcar", "none", "tail_truncated", "spoofed_open", "reordered"]
GRANS = ["claim_level", "window_64tok", "report_centroid"]
TAU_COPY = 0.75
LR_CONST = 3.0
PRIOR0 = 0.5
IC_RE = re.compile(r"\bnot\b[^.]*\bindependent|\bnon-?independent|\bbuilds? on|\bprior (analyst|report)", re.I)
NEG_TYPES_COPY_U = ("IND_SAME", "IND_DIFF", "TWIN_H", "NEAR_H", "SHARED_OK", "NOSRC_SAME")


def ic_flag(rep_b):
    """Independence claim made by B: 0 if B discloses non-independence (regex or prior_report citation), else 1."""
    if any(str(c).startswith("prior_report") for c in rep_b.get("cited_sources", [])):
        return 0
    return 0 if IC_RE.search(rep_b.get("independence_statement", "") or "") else 1


def windows_64(texts, size=64, stride=48):
    words = " ".join(texts).split()
    if len(words) <= size:
        return [" ".join(words)]
    return [" ".join(words[i:i + size]) for i in range(0, len(words) - size + stride, stride) if words[i:i + size]]


def texts_needed_v2(rec, catalog):
    out = list(M.texts_needed(rec, catalog))
    for rep in (rec["report_a"], rec["report_b"]):
        out += windows_64(rep["claims"])
    return out


def unit(v):
    n = float(np.linalg.norm(v))
    return v / n if n > 1e-12 else v


def claim_mats(rec, emb, gran):
    ra, rb = rec["report_a"], rec["report_b"]
    if gran == "claim_level":
        return emb.get(ra["claims"]), emb.get(rb["claims"])
    if gran == "report_centroid":
        return unit(emb.get(ra["claims"]).mean(0))[None, :], unit(emb.get(rb["claims"]).mean(0))[None, :]
    if gran == "window_64tok":
        return emb.get(windows_64(ra["claims"])), emb.get(windows_64(rb["claims"]))
    raise ValueError(gran)


def source_mat(rep, catalog, emb):
    ids = M.claimed_sources(rep, catalog)
    if not ids:
        return np.zeros((0, emb.get(rep["claims"]).shape[1]))
    return np.vstack([emb.get(M.source_sentences(catalog[i])) for i in ids])


def body_hashes(rep, catalog):
    return {corpus.body_hash(catalog[i]) for i in M.claimed_sources(rep, catalog)}


def centroid(rec_report, emb):
    return unit(emb.get(rec_report["claims"]).mean(0))


# ---------------- ledger views ----------------
def _rehash(events):
    L = Ledger()
    for e in events:
        L.log(e["kind"], e["agent"], **e["data"])
    return L.events


def ledger_view(rec, mode, catalog):
    """Return the event list a monitor would see under the given degradation mode."""
    ev, key = rec["ledger"], rec["scenario"]["scenario_id"]
    if mode in ("full_anchored",):
        return list(ev)
    if mode == "comm_hidden":
        return [e for e in ev if e["kind"] not in ("message", "message_received")]
    if mode == "half_mcar":
        return [e for e in ev if int(hashlib.sha256(("%s|%d" % (key, e["n"])).encode()).hexdigest()[:4], 16) % 2 != 0]
    if mode == "none":
        return []
    if mode == "tail_truncated":
        return list(ev[:-2])
    if mode == "reordered":
        out = list(ev)
        if len(out) >= 2:
            out[-1], out[-2] = out[-2], out[-1]
        return out
    if mode == "spoofed_open":      # administrator forges B's open_source event and re-hashes the whole chain
        cited = [c for c in rec["report_b"].get("cited_sources", []) if c in catalog]
        if not cited:
            return list(ev)
        forged, done = [], False
        for e in ev:
            if not done and e["kind"] == "report_submitted" and e is ev[-1]:
                forged.append({"kind": "open_source", "agent": e["agent"], "data": {"source": cited[0], "body_hash": corpus.body_hash(catalog[cited[0]])}})
                done = True
            forged.append(e)
        return _rehash(forged)
    raise ValueError(mode)


def anchored_known(mode, view, anchor):
    """L_known used by ARG-H8: chain verifies AND head equals the externally stored anchor. comm_hidden is a visibility mask over
    a log the service attests (declared), half_mcar and none are gap/absent logs."""
    if mode in ("none", "half_mcar"):
        return 0.0
    if mode == "comm_hidden":
        return 1.0
    ok, _ = Ledger.verify(view)
    return float(bool(ok and view and view[-1]["hash"] == anchor))


def _roles(rec):
    sub = [e["agent"] for e in rec["ledger"] if e["kind"] == "report_submitted"]
    return (sub[0], sub[-1]) if sub else (None, None)


def custody_flags(rec, view, catalog):
    """Facts read from the visible events: B cited-without-open, shared opened body between A and B, message received by B."""
    a, b = _roles(rec)
    cited_b = rec["report_b"].get("cited_sources", [])
    b_opened = [e for e in view if e["kind"] == "open_source" and e["agent"] == b]
    opened_ids = {e["data"]["source"] for e in b_opened}
    unopened = [c for c in cited_b if not str(c).startswith("prior_report") and c not in opened_ids]
    ha = {e["data"]["body_hash"] for e in view if e["kind"] == "open_source" and e["agent"] == a}
    hb = {e["data"]["body_hash"] for e in b_opened}
    msg = any(e["kind"] == "message_received" and e["agent"] == b for e in view)
    return {"led_unopened": float(len(unopened) > 0), "led_shared_body": float(bool(ha & hb)), "led_msg": float(msg)}


def legacy_ledger(rec, mode, view, catalog):
    """Features of the v1 ledger monitors (P, F10) computed on the degraded view; unanchored verification for the new modes."""
    if mode == "none":
        return {"led_known": 0.0, "led_msg": 0.0, "led_unopened": 0.0, "led_shared_body": 0.0}
    if mode == "reordered":
        ok, _ = Ledger.verify(view)
        if not ok:
            return {"led_known": 0.0, "led_msg": 0.0, "led_unopened": 0.0, "led_shared_body": 0.0}
    out = {"led_known": 1.0}
    out.update(custody_flags(rec, view, catalog))
    return {k: out[k] for k in ("led_known", "led_msg", "led_unopened", "led_shared_body")}


# ---------------- pass 1: calibration-only fitted objects ----------------
def fit_calibration_objects(recs, rows_truth, emb):
    """recs: records of one replicate; rows_truth: dict scenario_id -> (split, type, copy_u). Uses calibration split only."""
    cal = [r for r in recs if rows_truth[r["scenario"]["scenario_id"]][0] == "calib"]
    allclaims = np.vstack([emb.get(rep["claims"]) for r in cal for rep in (r["report_a"], r["report_b"])])
    mu_cal = allclaims.mean(0)
    cents = []
    for r in cal:
        sid, copy_u = r["scenario"]["scenario_id"], rows_truth[r["scenario"]["scenario_id"]][2]
        cents.append((sid, centroid(r["report_a"], emb)))
        if copy_u == 0:
            cents.append((sid, centroid(r["report_b"], emb)))
    nos = [CF._regularized_spectral_mi(CF.l2_normalize_rows(emb.get(r["report_a"]["claims"])), CF.l2_normalize_rows(emb.get(r["report_b"]["claims"])))
           for r in cal if r["scenario"]["type"] == "NOSRC_SAME"]
    return {"mu_cal": mu_cal, "cents": cents, "nosrc_mi": float(np.median(nos)) if nos else 0.0}


def r_cal_for(obj, sid, own_vectors=()):
    """Calibration centroids excluding those of the scenario itself AND any centroid identical to one of the row's own reports.
    Honest reports are reused across scenarios (same source and replicate), so excluding by scenario id alone would leave byte-identical copies in the reference set."""
    rows = []
    for s, c in obj["cents"]:
        if s == sid or any(float(np.dot(c, v)) > 0.999999 for v in own_vectors):
            continue
        rows.append(c)
    return np.vstack(rows) if rows else np.zeros((0, obj["mu_cal"].shape[0]))


# ---------------- pass 2: per-record candidate features ----------------
def candidate_features(rec, catalog, emb, feats, calib_obj):
    ra, rb = rec["report_a"], rec["report_b"]
    sid = rec["scenario"]["scenario_id"]
    UA, UB = emb.get(ra["claims"]), emb.get(rb["claims"])
    SA, SB = source_mat(ra, catalog, emb), source_mat(rb, catalog, emb)
    out = {}
    h1 = CF.cross_source_support_excess(UB, SA, SB)
    out["h1"] = h1
    out["h4"] = CF.source_omission_footprint_match(UA, UB, SB)
    r_cal = r_cal_for(calib_obj, sid, (unit(UA.mean(0)), unit(UB.mean(0))))
    out["h7"] = CF.csls_peer_hubness_contrast(UA.mean(0), UB.mean(0), r_cal, k=5) if len(r_cal) else {"score": float("nan")}
    disg = CF.semantic_lexical_disguise_contrast(UA, UB, feats["lex"])
    out["s_disguise_claim"] = disg["score"]
    w12 = max(float(bool(body_hashes(ra, catalog) & body_hashes(rb, catalog))), float(feats["src_cont"]), float(disg["score"] > TAU_COPY))
    out["h10"] = CF.argon_f25_f11_independence_gated_bayes(PRIOR0, np.array([LR_CONST, LR_CONST]), np.array([[1.0, w12], [w12, 1.0]]))
    out["w12"] = w12
    s_own = (UB @ SB.T).max(axis=1) if len(SB) else np.zeros(len(UB))
    s_a = (CF.l2_normalize_rows(UB) @ CF.l2_normalize_rows(UA).T).max(axis=1)
    out["h8in"] = {"s_own_vec": [float(x) for x in s_own], "s_a_vec": [float(x) for x in s_a], "ic": int(ic_flag(rb)),
                   "has_src": int(len(SB) > 0), "s_disguise": float(disg["score"]), "f_omit": float(out["h4"]["score"])}
    union = np.vstack([x for x in (SA, SB) if len(x)]) if (len(SA) or len(SB)) else None
    for g in GRANS:
        GA, GB = claim_mats(rec, emb, g)
        d = {}
        d["h2"] = CF.orthogonal_source_residual_cosine(GA, GB, union, calib_obj["mu_cal"])
        d["h3"] = CF.semantic_lexical_disguise_contrast(GA, GB, feats["lex"])
        d["h5"] = CF.bipartite_assignment_uniqueness_margin(GA, GB, SA if len(SA) else None, SB if len(SB) else None)
        d["h6"] = CF.gaussian_dpi_excess_mutual_information(GA, GB, SA if len(SA) else None, SB if len(SB) else None, nosrc_baseline_mi=calib_obj["nosrc_mi"])
        d["h9"] = CF.argon_f42_repaired_mmd_conformal_triage(GA, GB) if g != "report_centroid" else {"score": float("nan")}
        out[g] = d
    return out


def ledger_block(rec, catalog):
    legacy, h8 = {}, {}
    anchor = rec.get("anchor") or rec["ledger"][-1]["hash"]
    for mode in MODES7:
        view = ledger_view(rec, mode, catalog)
        legacy[mode] = legacy_ledger(rec, mode, view, catalog)
        cf = custody_flags(rec, view, catalog)
        h8[mode] = {"l_known": anchored_known(mode, view, anchor), "led_unopened": cf["led_unopened"], "led_shared_body": cf["led_shared_body"]}
    return legacy, h8
