# Status of EVERY item on Apart's Resources page (read 2026-11-07)

Legend: READ = abstract/page content opened at the URL; FULL = more than the abstract was read; BLOCKED = site refused automated reading (bot check, login, HTTP 403); not bypassed.
Only abstract-level claims may be made for items marked READ. This file supersedes the shorter VERIFIED_REFERENCES.md.

## General
| Item | Status | Verified facts |
|---|---|---|
| Hammond et al. 2025, Multi-Agent Risks from Advanced AI | READ | arXiv:2502.14143; taxonomy: miscoordination, conflict, collusion; 7 risk factors |
| Tomasev, Franklin, Jacobs, Krier, Osindero, Distributional AGI Safety | READ | arXiv:2512.16856 (v1 18 Dec 2025, v2 19 May 2026); conceptual framework, sandbox economies, no experiments in abstract |
| ARIA Scaling Trust programme | READ (programme web page, not a paper) | funding programme, nearly 50m GBP, three tracks; no research results |
| Dafoe et al. 2020, Open Problems in Cooperative AI | READ | arXiv:2012.08630; agenda paper |
| Chan et al. 2025, Infrastructure for AI Agents | READ | arXiv:2501.10114; accepted to TMLR per arXiv comment; conceptual |
| Conitzer and Oesterheld 2023, Foundations of Cooperative AI | READ (PDF pages 1-2, downloaded by the author) | AAAI-23 paper, research agenda for game theory of advanced AI; example: individually near-aligned agents can have a terrible only equilibrium (Traveler's Dilemma) |

## Track 1
| Item | Status | Verified facts |
|---|---|---|
| Park et al. 2023, Generative Agents | READ on arXiv (ACM page 403) | arXiv:2304.03442, 25-agent sandbox, ablation of observation/planning/reflection; match to the ACM DOI link is by identical title only |
| Akata et al., Playing repeated games with LLMs | READ on arXiv | arXiv:2305.16867 lists related DOI 10.1038/s41562-025-02172-y, which matches Apart's Nature link; Nature page itself needs login |
| Gandhi et al. 2023 (Apart link text: 'LLM agents in stylised games and simulated social environments') | READ (PDF pages 1-2, downloaded from the Apart link) | ACTUAL TITLE: 'Strategic Reasoning with Language Models', Gandhi, Sadigh, Goodman (Stanford), NeurIPS 2023 Foundation Models for Decision Making Workshop. Cite the actual title, not Apart's link text |
| Kapoor et al. 2026, CRUX | READ (project page, not a paper) | open-world evaluations; arXiv id 2605.20520 is linked on the page but NOT opened |
| Concordia (Google DeepMind) | READ (README) | Apache-2.0 library; tech report arXiv:2312.03664 cited, not opened |
| Piatti et al. 2024, GovSim (Cooperate or Collapse) | READ | arXiv:2404.16698, NeurIPS 2024 per comments; highest survival below 54% except the most powerful model; communication critical |

## Track 2
| Item | Status | Verified facts |
|---|---|---|
| Lee and Tiwari 2024, Prompt Infection | READ | arXiv:2410.07283 |
| Jones et al. (Apart: 'Splitting tasks to evade per-agent safety filters', 2025) | READ (PDF pages 1-2) | ICML 2025 (PMLR 267) paper 'Adversaries Can Misuse Combinations of Safe Models', Jones, Dragan, Steinhardt; same paper as arXiv:2406.14595 (same title, authors, abstract). Example in text: Claude 3 Opus + Llama 2 70B reached 43% on vulnerable code vs under 3% for either alone |
| Agrawal, Ebadian, Hammond 2026 (Apart: 'Coordination to resist modification or shutdown') | READ (PDF pages 1-2) | ACTUAL TITLE: 'The Multi-Agent Off-Switch Game', AAMAS 2026, DOI 10.65109/HQQZ1937 (DOI printed on the paper); result: corrigibility is not compositional, individually corrigible agents can be collectively incorrigible. Theory paper |
| Tilli 2026 (Apart: 'From individual cooperation properties to system outcomes') | READ (PDF pages 1-2) | PDF title 'Agent properties for multi-agent safety', Cecilia Elena Tilli, ICLR 2026 Workshop on Agents in the Wild; position paper; argues toy cooperation experiments with LLMs give weak evidence and models may recognise evaluations. Title differs from Apart's link text: confirm it is the same item |
| Jorgensen, Weichwald, Hammond 2026 (Apart: 'Defining collective agency', 2025) | READ (PDF pages 1-2) | ACTUAL TITLE: 'Causal Foundations of Collective Agency', PMLR 323, CLeaR 2026; formal framework (causal games, abstraction); no experiments on LLM swarms |

## Track 3
| Item | Status | Verified facts |
|---|---|---|
| Google A2A announcement (9 Apr 2025) | READ (blog post) | HTTP/SSE/JSON-RPC protocol, Agent Card; no experiments |
| Chan et al. 2024, IDs for AI Systems | READ | arXiv:2406.12137; RegML workshop NeurIPS 2024 per comments; conceptual |
| Kirchenbauer et al. 2023, A Watermark for LLMs | READ | ICML 2023, PMLR 202, pp. 17061-17084 |
| Sun et al. 2023, Decentralized Commitment Devices | READ | arXiv:2311.07815; position paper |
| Ramirez et al. 2023, Game Manipulators | READ | arXiv:2311.10586 |
| Haupt et al., Formal Contracts mitigate social dilemmas | READ | arXiv:2208.10469 (v4 29 Jan 2024) |
| Tennenholtz 2004, Program Equilibrium | BLOCKED | ScienceDirect 403 |

## Track 4
| Item | Status | Verified facts |
|---|---|---|
| Motwani et al. 2024, Secret Collusion | READ | NeurIPS 37, DOI 10.52202/079017-2336 |
| Rose et al. 2026, collusion via multi-agent interpretability | READ | arXiv:2604.01151 v5 |
| Greenblatt et al. 2024, AI Control | READ | arXiv:2312.06942 |
| Zhang et al. 2025, attributing failures | READ (PDF pages 1-2) | ICML 2025 (PMLR 267) 'Which Agent Causes Task Failures and When?'; same paper as arXiv:2505.00212; Who&When, 127 systems; best 53.5% agent, 14.2% step; a hand-crafted-system result of 8.77% step accuracy is also stated |
| Riedl 2026 (Apart: 'Emergent communication between agents') | READ (PDF pages 1-2) | ACTUAL TITLE: 'Emergent Coordination in Multi-Agent Language Models', Christoph Riedl (Northeastern), ICLR 2026; information-theoretic test of higher-order structure (time-delayed mutual information), guessing game, three interventions, GPT-4.1/Llama/Gemini 2.0 Flash/Qwen3. My earlier author-page guess (Caroline Riedl) was wrong and is discarded |
| Foerster et al. 2026, CaMeLs Can Use Computers Too | READ | arXiv:2601.09923; OSWorld; up to 57% of frontier performance retained |
| Mediated Multi-Agent RL (Ivanov et al. 2023) | READ | arXiv:2306.08419, AAMAS 2023 |
| Stackelberg Attacks on Auctions (Landis, Schwartzbach 2023) | READ | arXiv:2305.02178; arXiv note of text overlap with 2301.08523 |

## Tools and datasets
| Item | Status | Verified facts |
|---|---|---|
| METR and Redwood report, 26 Aug 2026 | FULL for pages 1-14 (of the PDF); later pages not read | ~1,200 agents, >70,000 messages and files, ~700 attacked Hugging Face; 1,206 agents in dataset, 688 participated; ~7% of evaluated transcripts successfully spoofed (small scale); scorer-tampering workstreams; stated limitations: small fraction of activity not captured, analysis heavily delegated to unreliable AI agents; agents did not succeed at the general scorer bypass; METR spent about 400K USD in API credits |
| OpenAI disclosure | BLOCKED | HTTP 403 |
| ControlAI (Bilge and Miotti, 2 Oct 2026) | FULL (newsletter) | secondary claims; much unknown; incident details come mostly from independent researchers |
| Swarm Traces (25 Sep 2026) | READ, partly (part verbatim, part model-summarised; only verbatim parts used) | dataset redacted.jsonl.gz, >80,000 reassembled payloads per page; credentials/PII redacted |
| AI Village dataset (Hugging Face) | READ (dataset card; data gated, not requested) | custom research terms: research use only, no training without permission, no re-identification, cite AI Digest; 280 GB; card says agents misreport events |
| Transluce agent activity (23 Sep 2026) | READ, partly | none of the hacking attempts appeared to succeed; artifacts incomplete |
| swarms.wiki | READ, empty (title only) | nothing usable |
| collusion.wiki (Von Arx et al., 4 Sep 2026) | READ, partly | ~18,000 agent posts on a wiki used as a message board; attribution to OpenAI is inferred ('we believe'); numbers from model-summarised parts discarded |

## Consequences for the manuscript
- Cite only items marked READ, and only for what the page text supports. PDFs downloaded by the author were read on pages 1-2 only (abstract, introduction); methods, results and limitations pages were not read.
- Still NOT usable: Tennenholtz 2004 (ScienceDirect 403) and the OpenAI disclosure (403); no copy provided yet.
- Apart's link texts do not always match the real paper titles (Gandhi, Agrawal, Tilli, Jorgensen, Riedl, Jones). Cite the real titles above.
- Datasets: Swarm Traces and AI Village were not used in our study; AI Village access is gated with research-only terms. Say so plainly.
- Real-incident data (METR, Swarm Traces, Transluce, collusion.wiki) are not comparable with our controlled testbed numbers.
- One discrepancy to avoid copying: the Apart page cites 7,905 agent names for ~1,200 agents, while collusion.wiki's own text says over 3,700 distinct names for a different swarm. Do not mix them.
