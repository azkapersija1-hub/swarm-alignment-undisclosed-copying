# VIDEO SCRIPT (EN) - about 4 minutes; narrate over `process_replay_tls.mp4` and `performance_replay_tls.mp4`
The videos are generated from real result files (not screen recordings, not simulated numbers).

1. (0:00) Problem. "Multi-agent systems are usually supervised through what agents say about themselves. A report can claim independent evidence while the content was copied. Identical content does not prove copying, so we test three targets separately."
2. (0:25) Testbed. "Real LLM agents, Gemma 4, write reports from my own course materials. A controller creates scenarios with known ground truth: independent, no-source control, honest twin sources, near-duplicates, shared with attribution, and four copy variants."
3. (0:55) Process replay (3D). "Each dot is a sentence embedding. Blue is agent A, orange is agent B, diamonds are the robust centres. In an honest twin scenario the centres are close, as close as in a copy."
4. (1:30) Monitors. "Formula scores read content only. The ledger records the process: which source an agent opened and which message it received."
5. (2:00) Performance replay. "Frame by frame: scenarios executed, latency of each LLM call, how often agents followed instructions, and how the monitors' recall and false positive rate evolve."
6. (2:45) Results. "LLM reading reports only: 38% of copies, and 6% of paraphrased copies claiming independence. Similarity formulas alone are close to chance. Claim-to-source checks and the ledger separate the cases; recall 1.00 with a full log, degrading gracefully."  [Read the numbers from TABLES.md before recording.]
7. (3:30) GPU and limits. "Only embeddings ran on the local RTX 3050; the language models ran remotely. One generator model, instructed agents, and a controller-written ledger, so ledger results are an upper bound."
8. (3:50) Close. "Do not trust the report alone: check claims against sources and keep a provenance record."
