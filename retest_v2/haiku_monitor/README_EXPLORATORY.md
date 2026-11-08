# Haiku blind monitor (EXPLORATORY, not pre-registered, not in the STAGE2 lock)
Why: the Gemma cloud quota ran out (see DEVIATIONS item 12), so a Claude Haiku subagent was used once as an extra, non-Qwen LLM comparator.
Design: 97 items sampled from the D1 (Gemma agents) rep0 TEST split, 7 per scenario type (6 for NEAR_H), seed 20261108. Report-only prompt identical to monitors.LLM_PROMPT (F0b analogue, no sources). Blind: the agent got only `blind/items.jsonl` (id + prompt); labels live in `key/key.jsonl` and were joined after the verdicts were written. The agent was told not to open other files; this is an instruction, not an enforced sandbox.
Verified after the run: 97 unique ids in order, all probabilities in [0,1].
Result on the same 97 items (56 positives for undisclosed copying): AUROC Haiku 0.811, Qwen 0.695; at threshold 0.5 both flag 66% of honest cases. One replicate, n=97, no confidence interval: do NOT use as evidence for a ranking of LLM monitors.
