"""Builds the report markdown files from result files only: adds the five-arm summary tables, then renders {{PLACEHOLDERS}} through tables_v2.render.
Usage: build_reports.py <template.md> <out.md>"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(RT), "src"))
os.environ.setdefault("SWARM_DATASET", "tls")
import tables_v2 as T  # noqa: E402

ARMS = [("D1 Gemma (confirmatory)", "gemma_homog"), ("D2 Qwen", "qwen_homog"), ("D2 DeepSeek", "deepseek_homog"),
        ("D3 Gemma>Qwen", "het_gemma_qwen"), ("D3 Gemma>DeepSeek", "het_gemma_deepseek")]
F2, F9, F11 = "F2 embedding cosine", "F9b ensemble + source checks", "F11x candidate ensemble"


def load(tag, name):
    return json.load(open(os.path.join(RT, "results", tag, name), encoding="utf-8"))


def primary5():
    head = ["arm", "AUROC F2", "AUROC F9b", "AUROC F11x", "F11x - F2 [95%]", "F11x - F9b [95%]", "F31 upper95 (need < -0.005)", "primary comparison"]
    lines = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    for arm, tag in ARMS:
        p = load(tag, "primary_comparisons.json")["target_A"]
        d = p["paired_auroc_diff_ci"]
        k = list(d)
        au = p["auroc"]
        lines.append("| %s | %.2f | %.2f | %.2f | [%.2f, %.2f] | [%.3f, %.3f] | %+.4f | %s |" % (
            arm, au[F2], au[F9], au[F11], d[k[0]][0], d[k[0]][1], d[k[1]][0], d[k[1]][1], p["f31_gate"]["upper95_bound"], "passed" if p["primary_success"] else "NOT passed"))
    ok = sum(bool(load(t, "primary_comparisons.json")["target_A"]["primary_success"]) for _, t in ARMS)
    lines.append("")
    lines.append("The pre-declared primary comparison passed in **%d of %d arms**. The success rule uses the point AUROC gain over F2 (>= 0.25), the F31 gate on paired Brier loss, and the sentinel false-positive rate; the confidence interval of the gain over F2 can therefore extend below 0.25 even when the rule is met." % (ok, len(ARMS)))
    return "\n".join(lines)


def label_check():
    p = load("gemma_homog", "pooled_predictions.json")
    a = p[F9 + "|A_primary"]["y"]
    c = p[F9 + "|C"]["y"]
    return "identical" if a == c else "different"


def main():
    tpl = open(sys.argv[1], encoding="utf-8").read()
    tpl = tpl.replace("{{PRIMARY5}}", primary5()).replace("{{LABELS_A_C}}", label_check())
    tmp = sys.argv[2] + ".tmp.md"
    open(tmp, "w", encoding="utf-8").write(tpl)
    print("unresolved placeholders:", T.render(tmp, sys.argv[2]))
    os.remove(tmp)


if __name__ == "__main__":
    main()
