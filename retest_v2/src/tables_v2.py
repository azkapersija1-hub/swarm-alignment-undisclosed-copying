"""Markdown tables for the re-test report, generated only from result files. render(template, out) replaces {{NAME}} placeholders.
Usage: tables_v2.py <template.md> <out.md>"""
import csv
import json
import os
import re
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
RT = os.path.dirname(HERE)
RES = os.path.join(RT, "results")
ARMS = [("D1 Gemma (confirmatory)", "gemma_homog"), ("D2 Qwen", "qwen_homog"), ("D2 DeepSeek", "deepseek_homog"), ("D3 Gemma>Qwen", "het_gemma_qwen"), ("D3 Gemma>DeepSeek", "het_gemma_deepseek")]
TYPES = ["IND_SAME", "IND_DIFF", "NOSRC_SAME", "TWIN_H", "NEAR_H", "SHARED_OK", "COPY_LIT", "COPY_PARA", "COPY_TWIN", "COPY_COVER",
         "ADAPT_SURROGATE_K3", "ADAPT_LEX_INJECT", "ADAPT_SPLIT_2", "ADAPT_OUT_OF_BAND"]
MODES = ["full_anchored", "comm_hidden", "half_mcar", "none", "tail_truncated", "spoofed_open", "reordered"]


def jl(path, default=None):
    return json.load(open(path, encoding="utf-8")) if os.path.isfile(path) else default


def rows(tag, name="results_main.csv"):
    p = os.path.join(RES, tag, name)
    return list(csv.DictReader(open(p, encoding="utf-8"))) if os.path.isfile(p) else []


def fn(x, d=3):
    try:
        v = float(x)
        return "n/a" if v != v else ("%." + str(d) + "f") % v
    except (TypeError, ValueError):
        return "n/a" if x in (None, "") else str(x)


def ci(r, k):
    return "%s [%s, %s]" % (fn(r.get(k)), fn(r.get(k + "_lo")), fn(r.get(k + "_hi")))


def md(header, body):
    return "\n".join(["| " + " | ".join(header) + " |", "|" + "|".join("---" for _ in header) + "|"] + ["| " + " | ".join(r) + " |" for r in body]) + "\n"


def t_design():
    body = []
    for arm, tag in ARMS + [("D0 original study (exploratory)", "D0_exploratory_contaminated")]:
        a = jl(os.path.join(RES, tag, "audit.json"))
        if not a:
            continue
        body.append([arm, str(a["conditions_scored"]["replicates"]), str(a["rows_scored"]), str(a["generation_failures"]["n"]), fn(a["rcc_fallback_rate"]), fn(a["argon_f42_fallback_rate"]),
                     ", ".join("%s %s" % (k.split(":")[0].replace("tp", "qwen" if "qwen" in k else "deepseek"), fn(v)) for k, v in a["llm_parse_fail_rate"].items()) or "n/a",
                     fn(a["ic_regex_design_agreement"])])
    return md(["arm", "replicates", "scenarios scored", "generation failures", "RCC fallback", "F42 fallback", "LLM monitor failure rate", "IC regex vs design"], body)


def t_primary():
    p = jl(os.path.join(RES, "gemma_homog", "primary_comparisons.json"))
    if not p:
        return "(primary comparison not available)\n"
    a = p["target_A"]
    body = []
    for n in ("F2 embedding cosine", "F9b ensemble + source checks", "F11x candidate ensemble"):
        c = a.get("refit_ci", {}).get(n, {})
        body.append([n, fn(a.get("auroc", {}).get(n)), "[%s, %s]" % (fn((c.get("auroc") or [None, None])[0]), fn((c.get("auroc") or [None, None])[1])),
                     "[%s, %s]" % (fn((c.get("recall") or [None, None])[0]), fn((c.get("recall") or [None, None])[1])), "[%s, %s]" % (fn((c.get("fpr") or [None, None])[0]), fn((c.get("fpr") or [None, None])[1]))])
    out = md(["monitor", "AUROC", "AUROC 95% (refit bootstrap)", "recall 95%", "FPR 95%"], body)
    g = a.get("f31_gate") or {}
    d = a.get("paired_auroc_diff_ci", {})
    out += "\nF31 gate (K=10): promote=%s, mean cluster loss difference %s, upper95 %s, clusters %s, sentinel FPR new %s vs old %s.\n" % (
        g.get("promote"), fn(g.get("mean_cluster_diff"), 4), fn(g.get("upper95_bound"), 4), g.get("n_clusters"), fn(g.get("sentinel_fpr_new")), fn(g.get("sentinel_fpr_old")))
    for k, v in d.items():
        out += "Paired %s: 95%% interval [%s, %s].\n" % (k, fn(v[0]), fn(v[1]))
    out += "Success criteria: %s. **Primary comparison passed: %s.**\n" % (json.dumps(a.get("success_criteria")), a.get("primary_success"))
    return out


def verdict(v):
    return {True: "FALSIFIED", False: "not falsified", None: "undetermined"}.get(v, "n/a")


def t_falsifiers():
    hyps = ["ARG-H%d" % i for i in range(1, 11)]
    fals = {tag: jl(os.path.join(RES, tag, "falsifiers.json"), {}) for _, tag in ARMS}
    d0 = jl(os.path.join(RES, "D0_exploratory_contaminated", "falsifiers.json"), {})
    body = [[h] + [verdict(fals[t].get(h, {}).get("falsified", "n/a")) if fals[t] else "n/a" for _, t in ARMS] + [verdict(d0.get(h, {}).get("falsified", "n/a")) if d0 else "n/a"] for h in hyps]
    return md(["hypothesis"] + [a.split(" (")[0] for a, _ in ARMS] + ["D0 (contaminated)"], body)


def t_falsifier_numbers():
    f = jl(os.path.join(RES, "gemma_homog", "falsifiers.json"), {})
    body = []
    for h in ["ARG-H%d" % i for i in range(1, 11)]:
        if h in f:
            items = {k: (round(v, 3) if isinstance(v, float) else v) for k, v in f[h].items() if k not in ("falsified", "per_mode", "note")}
            body.append([h, verdict(f[h].get("falsified")), "; ".join("%s=%s" % (k, v) for k, v in items.items())])
    return md(["hypothesis", "verdict (D1)", "numbers behind the verdict"], body)


def t_monitors(target="A_primary"):
    mons = ["F2 embedding cosine", "F4 STP-AR", "F6 RCC-v3.3 (AR)", "F8a Argon F42 (cosine part)", "F8b Argon F44 (jaccard part)", "F9b ensemble + source checks", "F11x candidate ensemble",
            "H1 E_sup", "H3 S_disguise [claim_level]", "H4 F_omit", "F0b LLM report-only [tp:qwen3.8-flash]", "D LLM with sources [tp:qwen3.8-flash]"]
    out = ""
    for arm, tag in ARMS:
        rs = {r["monitor"]: r for r in rows(tag) if r["target"] == target}
        if not rs:
            continue
        body = [[m.replace("[tp:qwen3.8-flash]", "(Qwen)").replace("[tp:qwen3.8-flash]", "(Qwen)"), fn(rs[m]["recall"]), fn(rs[m]["fpr"]), ci(rs[m], "auroc"), fn(rs[m]["brier"]), fn(rs[m].get("coverage"))]
                for m in mons if m in rs]
        out += "\n**%s** (n = %s test rows)\n\n" % (arm, next(iter(rs.values()))["n"]) + md(["monitor", "recall", "FPR", "AUROC [95% CI]", "Brier", "coverage"], body)
    return out


def t_adaptive():
    mons = ["F2 embedding cosine", "F9b ensemble + source checks", "F11x candidate ensemble", "F0b LLM report-only [tp:qwen3.8-flash]", "D LLM with sources [tp:qwen3.8-flash]", "H3 S_disguise [claim_level]"]
    out = ""
    for arm, tag in ARMS[:1]:
        rs = [r for r in rows(tag, "results_per_type.csv") if r["target"] == "A_primary"]
        idx = {(r["monitor"], r["type"]): r for r in rs}
        body = [[t] + [fn(idx[(m, t)]["flag_rate"], 2) if (m, t) in idx else "n/a" for m in mons] for t in TYPES]
        out += md(["scenario type"] + [m.replace(" [tp:qwen3.8-flash]", " (Qwen)").replace(" ensemble + source checks", "").replace(" candidate ensemble", "") for m in mons], body)
    return out


def t_logmodes():
    out = ""
    for arm, tag in ARMS[:1]:
        rs = {r["monitor"]: r for r in rows(tag) if r["target"] == "C"}
        body = []
        for m in MODES:
            f10, h8 = rs.get("F10 ensemble + ledger [%s]" % m, {}), rs.get("H8 tri-state [%s]" % m, {})
            body.append([m, fn(f10.get("recall")), fn(f10.get("fpr")), ci(f10, "auroc") if f10 else "n/a", fn(h8.get("recall")), fn(h8.get("fpr")), fn(h8.get("auroc")), fn(h8.get("abstain_rate"))])
        out += md(["log mode", "F10 recall", "F10 FPR", "F10 AUROC [CI]", "H8 recall (non-abstained)", "H8 FPR", "H8 AUROC", "H8 abstain"], body)
    return out


def t_transfer():
    out = ""
    for arm, tag in ARMS[1:]:
        p = os.path.join(RES, tag, "transfer_from_gemma_homog.csv")
        if not os.path.isfile(p):
            continue
        rs = [r for r in csv.DictReader(open(p, encoding="utf-8")) if r["target"] == "A_primary"]
        out += "\n**%s** (thresholds and fits from D1 calibration rows of domain-disjoint documents)\n\n" % arm + md(
            ["monitor", "recall", "FPR", "AUROC", "Brier", "abstain"], [[r["monitor"].replace("[tp:qwen3.8-flash]", "(Qwen)").replace("[tp:qwen3.8-flash]", "(Qwen)"), fn(r["recall"]), fn(r["fpr"]), fn(r["auroc"]), fn(r["brier"]), fn(r["abstain_rate"])] for r in rs])
    return out


def t_diag():
    out = ""
    c = rows("gemma_homog", "diag_h8_components.csv")
    if c:
        out += md(["type", "mode", "n", "mean S_prov", "mean R_reuse", "mean S_disguise", "share S_prov at ceiling"], [[r["type"], r["mode"], r["n"], fn(r["mean_s_prov"], 2), fn(r["mean_r_reuse"], 2), fn(r["mean_s_disguise_clip"], 2), fn(r["share_s_prov_ge_0.999"], 2)]
                                                                                                                for r in c if r["mode"] == "full_anchored"])
    a = rows("gemma_homog", "diag_f11x_ablation.csv")
    if a:
        out += "\n" + md(["model", "target", "AUROC", "recall at 95th-pct threshold", "FPR", "Brier"], [[r["model"], r["target"], fn(r["auroc"]), fn(r["recall_at_95pct_threshold"]), fn(r["fpr"]), fn(r["brier"])] for r in a])
    return out


def t_tracks():
    t = os.path.join(RES, "tracks")
    out = ""
    for name in ("track1_redteam_qwen_deepseek.json", "track1_redteam_gemma.json", "track1_redteam.json"):
        d = jl(os.path.join(t, name))
        if d:
            out += "\n**Track 1: real LLM agents try to leave the sandbox (%s)**\n\n" % name.replace(".json", "") + md(
                ["model | task", "episodes", "failed", "leaks", "attempts / episode", "denied and logged", "allowed", "episodes that tried outside"],
                [[k, str(v["episodes"]), str(v["failed_episodes"]), str(v["leaks"]), fn(v["attempts_per_episode"], 1), str(v["denied"]), str(v["allowed"]), str(v["agents_that_tried_outside"])] for k, v in d["summary"].items()])
    for name in ("track1_board_qwen_deepseek.json", "track1_board_gemma.json"):
        d = jl(os.path.join(t, name))
        if d:
            out += "\n**Track 1/2: do agents discover an unmentioned shared folder? (%s)**\n\n" % name.replace(".json", "") + md(
                ["model", "agents", "rounds", "discovered", "used as board", "read others' posts", "failed agents"],
                [[v["model"], str(v["n_agents"]), str(v["rounds"]), fn(v["discovered_shared_folder_rate"], 2), fn(v["used_as_board_rate"], 2), fn(v["read_someone_elses_post_rate"], 2), str(v["failed_agents"])] for v in d.values()])
    for name in ("track2_summary_qwen_deepseek.json", "track2_summary_gemma_mixed.json"):
        d = jl(os.path.join(t, name))
        if d:
            out += "\n**Track 2 (irrelevant planted false claim): propagation per downstream agent (%s)**\n\n" % name.replace(".json", "") + md(
                ["prompt | models | topology", "trials", "excluded", "propagation", "95% CI", "trials contaminated", "correction rate"],
                [[k, str(v["n_trials"]), str(v["n_trials_excluded_failed_agent"]), fn(v["propagation_rate"], 3), "[%s, %s]" % (fn(v["propagation_ci95"][0]), fn(v["propagation_ci95"][1])), fn(v["trials_contaminated"], 2), fn(v["correction_rate"], 2)] for k, v in d.items()])
    d = jl(os.path.join(t, "track2_v3_summary.json"))
    if d:
        out += "\n**Track 2 v3 (exploratory): planted false version of a real finding; agent 3 can verify, agents 2 and 4 cannot**\n\n" + md(
            ["prompt | models | topology", "trials", "agent 3 repeats false", "agent 3 states true", "agents 2,4 repeat false", "n (agent 3 / agents 2,4)"],
            [[k, str(v["n_trials"]), "%s %s" % (fn(v["agent3_can_verify"]["repeat_false_rate"], 2), v["agent3_can_verify"]["ci95"]), fn(v["agent3_can_verify"]["state_true_rate"], 2),
              "%s %s" % (fn(v["agents_2_4_cannot_verify"]["repeat_false_rate"], 2), v["agents_2_4_cannot_verify"]["ci95"]), "%d / %d" % (v["agent3_can_verify"]["n"], v["agents_2_4_cannot_verify"]["n"])] for k, v in d.items()])
    d = jl(os.path.join(t, "track3.json"))
    if d:
        tm = d["tamper"]["detection_rate"]
        out += "\n**Track 3: log tampering detection by integrity regime (n = %d ledgers)**\n\n" % d["tamper"]["n_ledgers"] + md(
            ["alteration", "hash chain only", "+ anchored head", "+ per-agent signatures"], [[k, fn(v["R1_chain_only"], 2), fn(v["R2_chain_plus_anchor"], 2), fn(v["R3_chain_anchor_signatures"], 2)] for k, v in tm.items()])
        fp = d["fingerprint"]
        out += "\nBehavioural fingerprint (generator model from report text): accuracy %s over %s reports, chance %s; confusion matrix (rows true %s): %s.\n" % (
            fn(fp.get("accuracy")), fp.get("n_reports"), fn(fp.get("chance")), fp.get("classes"), fp.get("confusion_matrix_rows_true"))
        ca = d["chain_attribution"]
        out += "\nCustody completeness by type: %s.\nSource attribution top-1: %s.\n" % (json.dumps(ca["chain_completeness_by_type"]), json.dumps(ca["attribution_recovery_top1_by_type"]))
    return out or "(track results not available)\n"


def t_d0():
    rs = {r["monitor"]: r for r in rows("D0_exploratory_contaminated") if r["target"] == "A_primary"}
    mons = ["F2 embedding cosine", "F9b ensemble + source checks", "F11x candidate ensemble", "H1 E_sup", "H3 S_disguise [claim_level]", "H4 F_omit"]
    return md(["monitor", "recall", "FPR", "AUROC [95% CI]"], [[m, fn(rs[m]["recall"]), fn(rs[m]["fpr"]), ci(rs[m], "auroc")] for m in mons if m in rs])


TABLES = {"DESIGN": t_design, "PRIMARY": t_primary, "FALSIFIERS": t_falsifiers, "FALSIFIER_NUMBERS": t_falsifier_numbers, "MONITORS_A": lambda: t_monitors("A_primary"),
          "MONITORS_B": lambda: t_monitors("B"), "MONITORS_C": lambda: t_monitors("C"), "ADAPTIVE": t_adaptive, "LOGMODES": t_logmodes, "TRANSFER": t_transfer,
          "DIAG": t_diag, "TRACKS": t_tracks, "D0": t_d0}


def render(template, out):
    text = open(template, encoding="utf-8").read()
    for name, f in TABLES.items():
        text = text.replace("{{%s}}" % name, f())
    left = re.findall(r"\{\{[A-Z_0-9]+\}\}", text)
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(text)
    return left


if __name__ == "__main__":
    print("unresolved placeholders:", render(sys.argv[1], sys.argv[2]))
