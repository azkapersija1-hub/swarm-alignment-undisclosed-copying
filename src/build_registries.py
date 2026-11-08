"""Build BOT_REGISTRY.csv, FORMULA_REGISTRY.csv, MODEL_REGISTRY.json, SOURCE_INVENTORY.csv (01_SOURCE_AUDIT).
Bot inclusion decisions are made from capability/relevance criteria (NOT from performance on any test set)."""
import csv
import glob
import hashlib
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "01_SOURCE_AUDIT")
REG = r"D:\kerjaan baru\25_Tools_Sakti_Terpadu\bots\registri_69.json"
CLASS_MAP = {"worker_inproc": "tool module (in-process, rule-based)", "worker_subprocess": "tool module (subprocess, rule-based)",
             "review_brief": "brief only (no executable agent)", "worker_jaringan": "network worker (needs external API)",
             "logis": "logic/orchestration module", "model_handoff": "hand-off to an external model"}
# Bots whose function could serve as a supervisor/evaluator/tool in this study (criteria: provenance, duplicate, evidence audit, calibration, embedding).
RELEVANT = ("dokumen", "riset-gap", "riset-screening", "audit", "evid", "duplik", "embed", "kalibr", "rea-", "super:RESEARCH_ENGINEERING")


def bots():
    d = json.load(open(REG, encoding="utf-8"))
    rows = []
    for b in d["bot"]:
        kelas = b.get("kelas", "")
        executable = b.get("mode_v6") == "executable" and kelas in ("worker_inproc", "worker_subprocess", "logis")
        relevant = any(k in b["id"] for k in RELEVANT)
        if executable and relevant:
            decision, reason = "candidate tool/evaluator (not an LLM agent)", "executable, related to document/evidence audit; used only via formula engine in this study if at all"
        else:
            decision = "excluded"
            reason = ("brief only or not executable" if not executable else "not relevant to provenance oversight of the 4 tracks")
        rows.append({"bot_id": b["id"], "bot_name": b["id"], "source_file": REG, "original_purpose": (b.get("kontrak_input") or "")[:120],
                     "implementation_type": CLASS_MAP.get(kelas, kelas), "model_dependency": "yes" if (b.get("kelas_biaya") or {}).get("model_call") else "no",
                     "tool_dependency": b.get("rute_dispatcher", ""), "formula_dependency": b.get("modul_kanonik") or "",
                     "multi_agent_relevance": "role as tool/evaluator only; no runtime multi-agent behaviour",
                     "applicable_track": "T4 (tool/evaluator)" if decision.startswith("candidate") else "none",
                     "GPU_requirement": "none", "readiness_status": b.get("mode_v6", ""), "inclusion_decision": decision, "exclusion_reason": reason if decision == "excluded" else ""})
    return rows


FORMULAS = [
    ("F-STP", "STP = cos(gm(U_A), gm(U_B)), gm = geometric median (Weiszfeld)", "frozen baseline", "03_FORMULA_ENGINE/source/baseline_formula.py", "numpy", "chunk embeddings n x d", "float [0,1]", "max_iter=60 tol=1e-6", "validated R1-R7 per earlier project reports", "T4", "EXECUTED"),
    ("F-STPAR", "STP-AR = STP / (1 + k*sigma_boot), k=2, B=25", "frozen baseline", "03_FORMULA_ENGINE/source/baseline_formula.py", "F-STP", "chunk embeddings", "float", "k=2, n_boot=25", "validated R1-R7", "T4", "EXECUTED"),
    ("F-MOI", "MOI = cos(mean(W_A)/|.|, mean(W_B)/|.|) on methodology sentences; score = 0.5*STP-AR + 0.5*MOI", "frozen baseline", "03_FORMULA_ENGINE/source/baseline_formula.py", "numpy", "method-sentence embeddings", "float", "weights 0.5/0.5", "validated R1-R7", "T4", "EXECUTED"),
    ("F-RCC33", "RCC-v3.3 spectral-effective-rank gated centroid (SERG)", "frozen candidate", "03_FORMULA_ENGINE/source/rcc_v3_3_formula.py", "F-STP", "chunk embeddings", "float", "SER_ALPHA=10 CONF_THR=0.85 SHARP=20 LAMBDA_MAX=0.5 TAU_MIN=0.05", "stable, never shown better than baseline (earlier reports)", "T4", "EXECUTED (degenerate branch falls back to STP-AR and is flagged)"),
    ("F-ARGON-F42", "Argon embedding-MMD anomaly triage (cosine distance of candidates to reference)", "Argon engine rumus_engine_teruji.py via adaptor (hash-checked)", "D:/kerjaan baru/25_Tools_Sakti_Terpadu/kapabilitas_argon/adaptor_argon.py", "Argon", "reference/candidate embeddings", "ranked candidates", "dimensions=3", "label REVIEW_REQUIRED", "T4", "EXECUTED"),
    ("F-ARGON-F44", "Argon NLP claim-evidence audit (lexical Jaccard, negation/numeric conflict heuristics)", "Argon engine via adaptor", "adaptor_argon.py", "Argon", "claim + evidence chunks", "per-chunk audit", "token_limit=128", "label AUDIT_KLAIM_NLP_HEURISTIK", "T4", "EXECUTED"),
    ("F-ARGON-F35", "Argon calibration audit (ECE, log-loss)", "Argon engine via adaptor", "adaptor_argon.py", "Argon", "probabilities + labels", "ECE", "bins", "cross-checked vs core Brier to 1e-16 per project notes", "T4", "PLANNED (see FINAL_ACCEPTANCE_REPORT)"),
    ("F-STRICTGAP", "STRICT-GAP novelty-gap examiner", "AI_SCHOOL examiner / ART archive", "RND_Formula_Discovery/academic_bot_evolution_lab/.../strict_gap/ ", "n/a", "n/a", "n/a", "n/a", "designed for research-gap novelty, NOT provenance", "none", "NOT TESTED (not applicable to provenance violations; no definition/validation for this task)"),
    ("F-SERG-note", "SERG = Spectral Effective Rank Gating (component of RCC-v3.3)", "see F-RCC33", "rcc_v3_3_formula.py", "F-RCC33", "", "", "", "", "T4", "EXECUTED as part of F-RCC33"),
    ("F-GEOMED", "Geometric median / Weiszfeld", "frozen baseline", "baseline_formula.py", "numpy", "", "", "", "classical", "T4", "EXECUTED"),
    ("F-BOOTREL", "Bootstrap reliability (sigma_boot)", "frozen baseline", "baseline_formula.py", "numpy", "", "", "n_boot=25", "", "T4", "EXECUTED"),
    ("F-MOI-ROBUST", "MOI robust variants (trimmed mean / geometric median centroid)", "antigravity/moi_adversarial_validation", "moi_formula_robust.py", "numpy", "", "", "", "geomedian vs mean discrepancy noted in earlier project", "T4", "NOT TESTED (baseline MOI used; variants not mixed)"),
    ("F-RCC-v1-v3.2", "RCC v1, v2, v3, v3.1, v3.2", "superseded candidates", "gcaw_synthetic_validation/rcc_*_formula.py", "", "", "", "", "rejected or flawed per earlier reports", "none", "NOT TESTED (superseded)"),
    ("F-IRTFUSION", "IRT fusion formula", "real_pdf_validation", "formula_irt_fusion.py", "", "", "", "", "frozen; no post-hoc tuning allowed", "none", "NOT TESTED (not part of provenance oversight)"),
]


def main():
    os.makedirs(OUT, exist_ok=True)
    b = bots()
    with open(os.path.join(OUT, "BOT_REGISTRY.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(b[0]))
        w.writeheader()
        w.writerows(b)
    cols = ["formula_id", "mathematical_definition", "version", "implementation_file", "dependencies", "input", "output", "parameters", "previous_validation", "relevant_tracks", "execution_status"]
    with open(os.path.join(OUT, "FORMULA_REGISTRY.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(cols)
        w.writerows(FORMULAS)
    models = {"audit_date": "2026-11-07", "models": [
        {"id": "gemma4:31b-cloud", "provider": "Ollama cloud (remote hardware; NOT the local GPU)", "status": "USED (agents, LLM monitors, corpus generation for preliminary set)"},
        {"id": "embeddinggemma-2:740m", "provider": "Ollama local (local GPU)", "status": "USED (embeddings)", "note": "digest f4981a15b99858ad1f2e0729416e526be7b4f428291b40082b9e4f7b27b5f62f; may differ from the model in arXiv:2509.20354"},
        {"id": "qwen3.5:397b-cloud", "provider": "Ollama cloud", "status": "BLOCKED: HTTP 410 Gone"},
        {"id": "deepseek-v4-flash:cloud", "provider": "Ollama cloud", "status": "BLOCKED: HTTP 410 Gone"},
        {"id": "minimax-m3:cloud / kimi-k2.7-code:cloud", "provider": "Ollama cloud", "status": "BLOCKED: HTTP 402 Payment Required"},
        {"id": "qwen-max / qwen3.8-flash / qwen-plus (DashScope API)", "provider": "Alibaba DashScope", "status": "BLOCKED: HTTP 401 (configured key rejected)"},
        {"id": "Claude Haiku (API)", "provider": "Anthropic", "status": "NOT TESTED: no API key in environment; Haiku was used only as literature-search helper agents, not as experimental agent"},
        {"id": "local generative model on GPU", "provider": "local", "status": "NOT TESTED: none installed; download requires researcher permission; GPU has 4 GB VRAM"}]}
    json.dump(models, open(os.path.join(OUT, "MODEL_REGISTRY.json"), "w", encoding="utf-8"), indent=1)
    inv = []
    for pat, kind in ((os.path.join(ROOT, "src", "*.py"), "sprint code"), (os.path.join(ROOT, "03_FORMULA_ENGINE", "source", "*.py"), "PREEXISTING frozen formula"),
                      (os.path.join(ROOT, "data", "*.json"), "frozen data")):
        for p in sorted(glob.glob(pat)):
            inv.append((os.path.relpath(p, ROOT), kind, os.path.getsize(p), hashlib.sha256(open(p, "rb").read()).hexdigest(), os.path.getmtime(p)))
    with open(os.path.join(OUT, "SOURCE_INVENTORY.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["path", "kind", "bytes", "sha256", "mtime_epoch"])
        w.writerows(inv)
    from collections import Counter
    print(len(b), "bots;", Counter(r["inclusion_decision"] for r in b), Counter(r["implementation_type"] for r in b))


if __name__ == "__main__":
    main()
