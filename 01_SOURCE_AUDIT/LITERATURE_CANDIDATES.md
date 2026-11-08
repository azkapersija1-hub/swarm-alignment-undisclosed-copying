# LITERATURE CANDIDATES (working file, NOT final references)

Status legend: HAIKU-VERIFIED = a Haiku subagent reports it opened the arXiv/publisher page and matched title, authors, year. SPOT-CHECKED = also re-opened by the main agent. Only SPOT-CHECKED items go into the submission reference list. Venue fields are copied only when the page showed them.

## A. Multi-agent LLM failures, propagation, topology, debate, sycophancy, agent infrastructure (agent report 1 of 5)

| # | Citation | URL | Status | Supports |
|---|---|---|---|---|
| A1 | Cemri, M., Pan, M. Z., Yang, S., et al. (2025). Why Do Multi-Agent LLM Systems Fail? arXiv preprint (no venue shown). | https://arxiv.org/abs/2503.13657 | HAIKU-VERIFIED | failure taxonomy (system design, inter-agent misalignment, task verification) |
| A2 | Hammond, L., et al. (2025). Multi-Agent Risks from Advanced AI. arXiv:2502.14143; Cooperative AI Foundation Technical Report #1. | https://arxiv.org/abs/2502.14143 | HAIKU-VERIFIED | miscoordination, conflict, collusion; information asymmetry |
| A3 | Lee, D., & Tiwari, M. (2024). Prompt Infection: LLM-to-LLM Prompt Injection within Multi-Agent Systems. arXiv:2410.07283. | https://arxiv.org/abs/2410.07283 | HAIKU-VERIFIED | propagation of malicious content across agents |
| A4 | Zhang, S., Yin, M., Zhang, J., et al. (2025). Which Agent Causes Task Failures and When? On Automated Failure Attribution of LLM Multi-Agent Systems. arXiv:2505.00212 (venue not shown; do not cite ICML). Do not quote the accuracy number (page 14.2% vs snippet 8.77%). | https://arxiv.org/abs/2505.00212 | HAIKU-VERIFIED | failure attribution is hard |
| A5 | Qian, C., Xie, Z., Wang, Y., et al. (2025). Scaling Large Language Model-based Multi-Agent Collaboration. arXiv:2406.07155; accepted ICLR 2025 per arXiv comments. | https://arxiv.org/abs/2406.07155 | HAIKU-VERIFIED | communication topology effects |
| A6 | Ashery, A. F., Aiello, L. M., & Baronchelli, A. (2025). Emergent social conventions and collective bias in LLM populations. Science Advances, 11(20), eadu9368. doi:10.1126/sciadv.adu9368 (arXiv:2410.08948) | https://arxiv.org/abs/2410.08948 | HAIKU-VERIFIED | collective bias without individual bias |
| A7 | Wu, H., Li, Z., & Li, L. (2025). Can LLM Agents Really Debate? A Controlled Study of Multi-Agent Debate in Logical Reasoning. arXiv:2511.07784. | https://arxiv.org/abs/2511.07784 | HAIKU-VERIFIED | majority pressure can suppress independent correction |
| A8 | Yao, B., Shang, C., Du, W., et al. (2025). Peacemaker or Troublemaker: How Sycophancy Shapes Multi-Agent Debate. arXiv:2509.23055. | https://arxiv.org/abs/2509.23055 | HAIKU-VERIFIED | inter-agent sycophancy |
| A9 | Wynn, A., Satija, H., & Hadfield, G. (2025). Talk Isn't Always Cheap: Understanding Failure Modes in Multi-Agent Debate. arXiv:2509.05396. | https://arxiv.org/abs/2509.05396 | HAIKU-VERIFIED | agents abandon correct answers to agree |
| A10 | Chan, A., Wei, K., Huang, S., et al. (2025). Infrastructure for AI Agents. arXiv:2501.10114; accepted to TMLR (year not shown on page). | https://arxiv.org/abs/2501.10114 | HAIKU-VERIFIED | agent identity and attribution infrastructure |

Leads NOT opened (do not cite): arXiv 2606.07937 and 2608.14588 (error cascades, 2026); 2510.07517; 2604.02668; Huang et al. arXiv:2408.00989 (figures disputed).

## B. Provenance, attribution, tamper-evident logging (agent report 2 of 5)

| # | Citation | URL | Status | Supports |
|---|---|---|---|---|
| B1 | Bohnet, B., Tran, V. Q., Verga, P., et al. (2022). Attributed Question Answering: Evaluation and Modeling for Attributed Large Language Models. arXiv:2212.08037. | https://arxiv.org/abs/2212.08037 | HAIKU-VERIFIED | attribution evaluation of LLM outputs |
| B2 | Rashkin, H., Nikolaev, V., Lamm, M., et al. (2021). Measuring Attribution in Natural Language Generation Models. arXiv:2112.12870 (later journal version not verified). | https://arxiv.org/abs/2112.12870 | HAIKU-VERIFIED | Attributable to Identified Sources (AIS) |
| B3 | Gao, T., Yen, H., Yu, J., & Chen, D. (2023). Enabling Large Language Models to Generate Text with Citations. arXiv:2305.14627; EMNLP 2023 per arXiv comment. | https://arxiv.org/abs/2305.14627 | HAIKU-VERIFIED | citation faithfulness (ALCE) |
| B4 | Crosby, S. A., & Wallach, D. S. (2009). Efficient Data Structures for Tamper-Evident Logging. 18th USENIX Security Symposium. | https://www.usenix.org/conference/usenixsecurity09/technical-sessions/presentation/efficient-data-structures-tamper-evident | HAIKU-VERIFIED | tamper-evident logging |

Could NOT be opened (verify manually before citing; do NOT cite from memory): Broder 1997 (resemblance/containment, doi 10.1109/SEQUEN.1997.666900); Potthast et al. 2011 (cross-language plagiarism); Walters & Wilder 2023 (ChatGPT fabricated citations, Sci Rep 13:14045); Haber & Stornetta 1991; Dong, Berti-Equille & Srivastava 2009 (two PVLDB papers on source dependence/copying detection). Gaps: no verified item for text reuse and for copying detection among sources.

## C. AI control, multi-agent oversight, collusion (agent report 3 of 5; items 1,3,4,5 appear on the Apart Resources list per the agent)

| # | Citation | URL | Status | Supports |
|---|---|---|---|---|
| C1 | Greenblatt, R., Shlegeris, B., Sachan, K., & Roger, F. (2024). AI Control: Improving Safety Despite Intentional Subversion. ICML 2024, PMLR 235:16295-16336 (arXiv:2312.06942). | https://proceedings.mlr.press/v235/greenblatt24a.html | HAIKU-VERIFIED | trusted/untrusted monitoring protocols, control evaluation |
| C2 | Bhatt, A., Rushing, C., Kaufman, A., et al. (2025). Ctrl-Z: Controlling AI Agents via Resampling. arXiv:2504.10374 (no venue; do not quote the 58%->7% figure). | https://arxiv.org/abs/2504.10374 | HAIKU-VERIFIED | control protocols for agentic multi-step settings |
| C3 | Hammond, L., Chan, A., Clifton, J., et al. (2025). Multi-Agent Risks from Advanced AI. arXiv:2502.14143. (same as A2) | https://arxiv.org/abs/2502.14143 | HAIKU-VERIFIED | multi-agent risk taxonomy |
| C4 | Motwani, S. R., Baranchuk, M., Strohmeier, M., et al. (2024). Secret Collusion among AI Agents: Multi-Agent Deception via Steganography. NeurIPS 37. | https://proceedings.neurips.cc/paper_files/paper/2024/hash/861f7dad098aec1c3560fb7add468d41-Abstract-Conference.html | HAIKU-VERIFIED | hidden coordination; partial visibility of messages |
| C5 | Rose, A., Cullen, C., Abdelnabi, S., et al. (2026). Detecting Multi-Agent Collusion Through Multi-Agent Interpretability. arXiv:2604.01151 (no venue). | https://arxiv.org/abs/2604.01151 | HAIKU-VERIFIED | collusion detection with internal signals |
| C6 | Nguyen, K. L., Nghiem, H., & Tran, T. (2026). TraceGuard: Structured Multi-Dimensional Monitoring as a Collusion-Resistant Control Protocol. arXiv:2604.03968. | https://arxiv.org/abs/2604.03968 | HAIKU-VERIFIED | collusion-resistant monitoring |
| C7 | Xiao, F., & Phuong, M. (2026). Bootstrapped Monitoring: Leveraging Transparent Reasoning to Oversee Stronger AI Agents. arXiv:2606.11998. | https://arxiv.org/abs/2606.11998 | HAIKU-VERIFIED | monitoring stronger agents |
| C8 | Tailor, O. (2025). Audit the Whisper: Detecting Steganographic Collusion in Multi-Agent LLMs. arXiv:2510.04303. | https://arxiv.org/abs/2510.04303 | HAIKU-VERIFIED | auditing hidden coordination |

Gap: no verified paper on monitors with PARTIAL visibility of agent messages (treat that claim as unsupported by literature). Not used: Jarviniemi 2025 (not opened), arXiv:2510.05174 (not opened).

## D. Method components (agent report 4 of 5). VERIFIED = publisher/PMC/PMLR/arXiv page opened; PARTIAL = catalogue/mirror only; UNVERIFIED = nothing readable.

| # | Component | Citation | Status |
|---|---|---|---|
| D1 | Brier score | Brier, G. W. (1950). Verification of forecasts expressed in terms of probability. Monthly Weather Review, 78(1), 1-3. doi:10.1175/1520-0493(1950)078<0001:VOFEIT>2.0.CO;2 | UNVERIFIED (AMS 403) - check in browser |
| D2 | Platt scaling | Platt, J. C. (1999). Probabilistic outputs for support vector machines and comparisons to regularized likelihood methods. In Advances in Large Margin Classifiers, MIT Press (year 1999 vs 2000 conflict) | PARTIAL |
| D2b | Calibration of supervised learners | Niculescu-Mizil, A., & Caruana, R. (2005). Predicting good probabilities with supervised learning. ICML 2005, 625-632. doi:10.1145/1102351.1102430 | PARTIAL (mlanthology record) |
| D3 | ECE | Guo, C., Pleiss, G., Sun, Y., & Weinberger, K. Q. (2017). On calibration of modern neural networks. ICML 2017, PMLR 70:1321-1330 (arXiv:1706.04599) | VERIFIED |
| D4 | MCC | Chicco, D., & Jurman, G. (2020). The advantages of the Matthews correlation coefficient (MCC) over F1 score and accuracy in binary classification evaluation. BMC Genomics, 21, 6. doi:10.1186/s12864-019-6413-7 | VERIFIED (covers MCC, not AUPRC; AUPRC source still missing) |
| D5a | Cluster bootstrap | Field, C. A., & Welsh, A. H. (2007). Bootstrapping clustered data. JRSS B, 69(3), 369-390. doi:10.1111/j.1467-9868.2007.00593.x | VERIFIED |
| D5b | Bootstrap book | Efron, B., & Tibshirani, R. J. (1993). An Introduction to the Bootstrap. Chapman & Hall | VERIFIED (title/authors/series only) |
| D6a | Wilson interval | Wilson, E. B. (1927). Probable inference, the law of succession, and statistical inference. JASA, 22(158), 209-212. doi:10.1080/01621459.1927.10502953 | PARTIAL (catalogue) |
| D6b | Binomial intervals | Brown, L. D., Cai, T. T., & DasGupta, A. (2001). Interval estimation for a binomial proportion. Statistical Science, 16(2), 101-133 (page range conflict 101-117 vs 101-133) | UNVERIFIED |
| D7a | Weiszfeld | Weiszfeld, E. (1937). Sur le point pour lequel la somme des distances de n points donnes est minimum. Tohoku Math. J., 43, 355-386 | VERIFIED |
| D7b | L1-median | Vardi, Y., & Zhang, C.-H. (2000). The multivariate L1-median and associated data depth. PNAS, 97(4), 1423-1426. doi:10.1073/pnas.97.4.1423 | VERIFIED |
| D8 | EmbeddingGemma | Schechter Vera, H., Dua, S., Zhang, B., et al. (2025). EmbeddingGemma: Powerful and Lightweight Text Representations. arXiv:2509.20354 | VERIFIED (title/authors/ID). NOTE: our model tag is 'embeddinggemma-2:740m' (gemma-embedding2 family in Ollama), which may differ from this paper's model; state the exact Ollama tag and digest, do not claim it is the model of this paper. |

## E. Local folders (D:\PELATIHAN AI ART etc.) - agent report 5 of 5. Metadata read from the first page/RIS record by a Haiku agent; NOT yet re-opened by the main agent. RIS-derived rows were not checked against PDFs.

| # | Citation (as printed) | Local file | Use |
|---|---|---|---|
| E1 | Radanliev P, Santos O, Maple C (2026). Threats and vulnerabilities in artificial intelligence and agentic AI models. Frontiers in Artificial Intelligence 9:1731566. doi:10.3389/frai.2026.1731566 | bahan AI ACADEMY ... Machine Learning and AI Engineering | agentic AI risk, governance (background) |
| E2 | Liu B, Li X, Zhang J, et al. (2025). Advances and Challenges in Foundation Agents: From Brain-Inspired Intelligence to Evolutionary, Collaborative, and Safe Systems. arXiv:2504.01990v2 | arsip\Zotero\storage\97WRCRU6 | collaborative multi-agent systems and safety (background) |
| E3 | Parakala A, Padgett P (2025). When AI Acts: Opportunities and Risks of Agentic Systems. IJAIDSML 6(4):29-40. doi:10.63282/3050-9262.IJAIDSML-V6I4P105 | same folder as E1 | weak background; low-impact venue, prefer A/C sections |
| E4 | Minsker S, Strawn N (2024). The Geometric Median and Applications to Robust Mean Estimation. SIAM J. Math. Data Sci. doi:10.1137/23m1592420 | RND_Formula_Discovery\PAKET_ARTIKEL_VALIDASI\09_REFERENSI_TERVERIFIKASI.ris | geometric median (RIS record only) |
| E5 | Vardi Y, Zhang C-H (2000). The multivariate L1-median and associated data depth. PNAS 97(4). doi:10.1073/pnas.97.4.1423 | same RIS | geometric median (also VERIFIED online, see D7b) |
| E6 | Reimers N, Gurevych I (2019). Sentence-BERT. EMNLP-IJCNLP 2019. doi:10.18653/v1/d19-1410 | same RIS | embedding similarity (RIS record only) |
| E7 | Cohan A, et al. (2020). SPECTER. ACL 2020. doi:10.18653/v1/2020.acl-main.207 | same RIS | document-level embeddings (RIS record only) |
| E8 | Brown P, et al. (2019). Large expert-curated database for benchmarking document similarity detection in biomedical literature search. Database. doi:10.1093/database/baz085 | same RIS | document-similarity benchmark (RIS record only) |

Do NOT cite: the DrillBit plagiarism report (it is the researcher's own thesis report, personal data). No local article was found on AI control/monitoring, collusion, Brier/Platt, or provenance of text; those come from sections A-D.
