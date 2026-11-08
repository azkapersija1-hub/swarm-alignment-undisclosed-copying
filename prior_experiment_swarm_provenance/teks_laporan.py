"""Isi laporan (bahasa Inggris, sesuai juri). Semua angka berasal dari M (metrik.py)."""
import os

from docx.shared import Pt

JUDUL = "Trust the Report or Check the Artifact? Catching Falsely Independent Sources Among Agents"


def pct(x, d=0):
    return ("%." + str(d) + "f%%") % (100 * x)


def isi_laporan(S, M, dir_gambar):
    D, F, B = M["det"], M["fpr"], M["brier"]
    n_seed, n_h = M["n_seed"], M["n_jujur"]
    lo_f = lambda k: pct(F[k][1], 1)
    hi_f = lambda k: pct(F[k][2], 1)
    sel_b = sum(M["selisih_brier_b2_b4"]) / n_seed
    ppv = M["ppv"]

    abstrak = (
        "Multi-agent pipelines often treat agreement between agents that cite different sources as independent confirmation. "
        "We study false independence: one agent copies another's material, disguises it, and cites a different source. "
        "We ask whether a supervisor that reads reports or one that checks the artifacts agents worked from catches it. "
        "Our testbed uses 184 school textbooks (kept local). Scripted bot pairs are either honest, with same-subject hard negatives, "
        "or copiers under six disguise levels from exact copy to a 50:50 mosaic with text from the source they cite, including twin "
        "sources, where two books genuinely share a passage. We compare six supervisors, with thresholds fixed on disjoint books at a 5%% "
        "false-alarm target, and score probability quality with the Brier score. Over %d seeds, a supervisor that trusts claimed sources "
        "never detected copying; a summary reader fell from %s to %s detection under heavy disguise; checking that a quote exists in the "
        "claimed source detected only %s of twin-source copies; embedding the artifacts kept at least %s detection at every level with "
        "%s false alarms and the lowest Brier score (%.3f versus %.3f for word overlap). Bots are scripts and disguises are surface-level, "
        "so results bound rather than predict adaptive language-model copiers."
    ) % (n_seed, pct(D["A2"]["C1"][0]), pct(D["A2"]["C1"][4]), pct(M["det_gab"]["B1"]["C2"]),
         pct(min(D["B4"]["C1"] + D["B4"]["C2"])), pct(F["B4"][0], 1), B["B4"]["semua"], B["B2"]["semua"])
    n_ab = len(abstrak.split())
    assert 150 <= n_ab <= 250, "abstrak %d kata" % n_ab

    # ---------------- 1. Introduction ----------------
    S.h2("1. Introduction")
    S.par("Systems of cooperating AI agents are often supervised through what the agents say about themselves: a report naming the "
          "sources used, a message that a step is done. This is cheap, and it is also the channel the agents control. The sprint overview "
          "notes that agents in the Hugging Face incident spoofed their own tool calls in roughly 7% of the transcripts reviewed (METR, 2026); "
          "a supervisor that trusts reports inherits that weakness.")
    S.par("We study a narrow, testable instance, **false independence**. Two agents report different sources, so a downstream supervisor "
          "counts their agreement as two confirmations. In fact one agent copied the other's material, or both rely on the same underlying "
          "text, and the agreement carries the weight of one source. The failure is population-level: the copier's report is internally "
          "consistent and nothing in a single agent's output looks wrong. It matters wherever evidence is aggregated across agents, for "
          "example literature review, fact checking and evaluation of generated content.")
    S.par("Our question is what a supervisor must read to catch it, the reports or the artifacts the agents actually worked from, and how "
          "each supervisor degrades as the copier disguises the copy. We also measure false alarms on honest agents whose sources merely "
          "resemble each other, because a supervisor that accuses everyone is trivially sensitive.")
    S.par("Our main contributions are:", sesudah=3)
    S.daftar("num", [
        "**A testbed for false independence on real text.** Honest pairs with same-subject hard negatives; copy pairs under six disguise "
        "levels (L0 to L5); and twin-source pairs where two different books contain the same passage (a scan of our 184-book corpus found "
        "at least 150 such cross-book pairs; the scan was capped).",
        "**A comparison of six supervisors** that differ in what they read (claims, report content, artifacts), with thresholds fixed on "
        "disjoint books, false alarms reported next to detection, and probability quality scored with the Brier score.",
        "**Findings.** Claim-trusting is blind by construction and summary reading is fragile (Section 4). Verifying that a quote exists in "
        "the claimed source fails exactly when the claimed source is a genuine twin, and its detection rises as the copier disguises more. "
        "Embedding the artifacts is the most robust to surface disguise. OR-combining supervisors raises false alarms to %s." % pct(F["BU"][0]),
    ])

    # ---------------- 2. Related Work ----------------
    S.h2("2. Related Work")
    S.par("**Control and collusion.** AI control studies protocols in which a trusted monitor reviews an untrusted model, including untrusted "
          "monitoring with countermeasures against collusion (Greenblatt et al., 2024). Secret collusion shows that agents can hide "
          "coordination through steganography and evaluates monitoring and paraphrasing as defences (Motwani et al., 2024). Our setting has no "
          "hidden channel: the shared material is an ordinary artifact, and the concealment lives in the report. Surface paraphrase appears here as "
          "the copier's disguise rather than the defender's tool.")
    S.par("**Multi-agent oversight readings.** The sprint reading list adds a taxonomy of multi-agent risks (Hammond et al., 2025), failure "
          "attribution in multi-agent systems (Zhang et al., 2025), collusion detection through multi-agent interpretability (Rose et al., 2026) "
          "and attacks that split a task across agents (Jones et al., 2025). Its example projects include checking each worker's \"done\" "
          "message against the database before the next worker acts. False independence extends this idea from claims about actions to claims "
          "about evidence.")
    S.par("**Methods we build on.** Resemblance and containment of documents through word shingles (Broder, 1997); sigmoid calibration of "
          "scores into probabilities (Platt, 1999); the Brier score (Brier, 1950); and the Wilson interval for proportions (Wilson, 1927). "
          "We did not run a systematic literature search; to our knowledge, within the readings we examined, we did not find a comparison of "
          "report-reading and artifact-checking supervisors under graded disguise.")

    # ---------------- 3. Methods ----------------
    S.h2("3. Methods")
    S.par("**3.1 Task and threat model.** Each bot i in {1, 2} submits a report r_{i} = (c_{i}, s_{i}), a claimed source c_{i} (book, page) and a "
          "summary s_{i} of at most 200 characters, and holds an artifact a_{i}, the passage it worked from. The label y = 1 (false independence) "
          "when a_{2} derives from the source of bot 1 although c_{2} names a different source; y = 0 otherwise. A supervisor sees both reports and, "
          "depending on its type, the artifacts and the text of the claimed sources. The copier (bot 2) may rewrite its own artifact but cannot "
          "alter bot 1's artifact or the claimed sources. We assume artifacts are stored unaltered (Section 5).")
    S.par("**3.2 Data.** 184 school textbooks (Indonesian and English) converted earlier to page-level JSON (pre-existing; Appendix C). "
          "Pages are cut into chunks of about 800 characters by the pre-existing chunker; we keep chunks of 250 to 800 characters with at least "
          "75% letters. The pool has 3,908 chunks: up to 20 random chunks per book plus all chunks of the twin pairs. Twin pairs come from a scan "
          "of every chunk: 5-word shingles are hashed, only hashes divisible by 8 are indexed, candidate pairs share at least three indexed "
          "shingles, and a pair is accepted if the 3-gram containment (Eq. 1) is at least 0.6; the first 150 pairs by shared count are kept. "
          "Book text is never released or sent to a cloud model; all computation is local.")
    S.par("**3.3 Scenarios.** ~~Honest (H):~~ bot 1 uses chunk S1; bot 2 uses the chunk of a different book in the same subject with the highest "
          "word-level Jaccard similarity among up to 200 random candidates, rejected if 3-gram containment exceeds 0.3. Honest bots rewrite their "
          "notes lightly (L0, L1 or L2 with equal probability). ~~C1 (copy, different claim):~~ bot 2's artifact is the disguised text of S1 but it "
          "cites the H-style neighbour S2. ~~C2 (copy, twin claim):~~ bot 2 cites a genuine twin of S1, so its claim is partly true. Disguise levels: "
          "L0 identity; L1 lower-casing, punctuation and spacing changes; L2 sentence shuffle; L3 15% of words dropped and 15% of adjacent pairs "
          "swapped; L4 sentence shuffle, 35% dropped, 30% swapped and filler words from unrelated chunks added to 25% of the length; L5 mosaic, "
          "where every second sentence is replaced by a sentence from the source the copier cites.")
    S.par("**3.4 Supervisors.** Let tokens be lower-cased alphanumeric words, Sh_{n}(x) the set of word n-grams of x, and e(x) the L2-normalised "
          "embedding of x. Each supervisor returns a score; higher means more likely false independence.", sesudah=3)
    S.rumus("C(x, y) = |Sh_{3}(x) ∩ Sh_{3}(y)| / min(|Sh_{3}(x)|, |Sh_{3}(y)|)", 1)
    S.rumus("cos(x, y) = e(x) · e(y)", 2)
    S.par("**A1 claim-trust:** 1 if the two claimed sources are identical, else 0. **A2 summary reader:** C(s_{1}, s_{2}), a rule-based proxy for a "
          "reader of report content. **B1 quote check:** 1 − min_{i} C(a_{i}, src_{i}), where src_{i} is the text of the claimed source. **B2 artifact "
          "overlap:** C(a_{1}, a_{2}). **B3 twin sources:** C(src_{1}, src_{2}). **B4 embedding:** cos(a_{1}, a_{2}) with EmbeddingGemma-2 (740M, 768 "
          "dimensions, run locally through Ollama). The union **B** flags when any of B1 to B4 flags. A1 and A2 read reports only; B1 to B4 open "
          "artifacts. No supervisor is a language model: no local text-generation model was available, and book text may not go to a cloud model.")
    S.par("**3.5 Thresholds, calibration and scoring.** For each seed the books are split at random into a calibration half and a test half. "
          "Supervisor k flags when its score exceeds τ_{k}, the 95th percentile of its scores on honest calibration scenarios (Eq. 3), a 5% "
          "false-alarm target. We also fit a sigmoid to each score on calibration scenarios (honest and C1 at all levels; C2 is unseen), "
          "p = σ(a·z + b) with z the standardised score (Eq. 4), and report the Brier score on the test half (Eq. 5). The no-information "
          "reference predicts the base rate π (Eq. 6). Intervals are Wilson (Eq. 7).", sesudah=3)
    S.rumus("τ_{k} = Q_{0.95}({ score_{k}(i) : i honest, calibration half })", 3)
    S.rumus("p_{i} = σ(a·(s_{i} − μ)/sd + b),   σ(u) = 1/(1 + e^{−u})", 4)
    S.rumus("Brier = (1/N) Σ_{i} (p_{i} − y_{i})^{2}", 5)
    S.rumus("Brier_{0} = π(1 − π),   π = (1/N) Σ_{i} y_{i}", 6)
    S.rumus("p̃ = (p̂ + z^{2}/2n)/(1 + z^{2}/n),   h = z/(1 + z^{2}/n) · √( p̂(1 − p̂)/n + z^{2}/4n^{2} )", 7)
    S.par("**3.6 Protocol and reproducibility.** %d seeds (20261106 to 20261110). Per seed and half: 100 honest scenarios (rejected ones "
          "removed; %d honest test scenarios in total) and 40 scenarios per copy type and level (about %d per level for C1 and %d for C2 in "
          "total). Twin pairs available in the test half per seed: %s. Code, seeds and 19 unit tests are in the repository; scores (without text) "
          "are stored per seed. ~~What did not work first:~~ in one-seed pilots random sampling found only 3 twin pairs, so we scanned the whole "
          "corpus; and levels L0 to L4 left embedding detection saturated at 100%%, so we added the mosaic level L5. Both changes were made before "
          "the full run and no threshold was changed after test results were seen."
          % (n_seed, n_h, M["n_cel"]["C1"][0], M["n_cel"]["C2"][0], ", ".join(str(x) for x in M["kembar_uji"])))

    # ---------------- 4. Results ----------------
    S.h2("4. Results")
    S.par("**4.1 False alarms.** Table 1 and Figure 2a show false alarms on %d honest test scenarios. Thresholds were set for 5%%; observed "
          "rates are %s for A2, %s for B1, %s for B2, %s for B3 and %s for B4 (95%% Wilson intervals %s to %s for B4). Per-seed rates ranged "
          "from %s to %s for B2 and from %s to %s for B4, so the 5%% target was met on average but not within every seed. OR-combining B1 to B4 "
          "raised false alarms to %s (%s to %s)."
          % (n_h, pct(F["A2"][0], 1), pct(F["B1"][0], 1), pct(F["B2"][0], 1), pct(F["B3"][0], 1), pct(F["B4"][0], 1), lo_f("B4"), hi_f("B4"),
             pct(M["fpr_seed"]["B2"][0], 1), pct(M["fpr_seed"]["B2"][1], 1), pct(M["fpr_seed"]["B4"][0], 1), pct(M["fpr_seed"]["B4"][1], 1),
             pct(F["BU"][0], 1), lo_f("BU"), hi_f("BU")))
    S.gambar(os.path.join(dir_gambar, "fig1_deteksi.png"), 6.3,
             "Figure 1. Detection rate by disguise level (L0 exact copy to L5 mosaic) for (a) copiers citing a different real passage and (b) copiers "
             "citing a genuine twin source. Points are means over %d seeds, bars are standard deviations, and points are offset horizontally for "
             "legibility. A1 (claim-trust) is 0 at every level and is omitted." % n_seed)
    S.par("**4.2 Detection.** ~~Observations.~~ A1 detected nothing at any level (every copier cites a different source, so this is by "
          "construction). A2 reached %s at L0 but fell to %s at L4 (C1) and %s (C2) once sentences and words were disturbed, and recovered to "
          "%s at L5 because the mosaic keeps the opening sentences that the summary reads. B1 detected %s to %s of C1 copies at L0 to L4 but only "
          "%s to %s of C2 copies at L0 to L2 and %s at L5: when the claimed source is a genuine twin, the copied passage really is in it. B1's "
          "detection on C2 rises to %s at L3 and %s at L4, consistent with heavier disguise making the quote stop matching the claimed source. B2 "
          "stayed at %s or above through L3 and dropped to %s (C1) and %s (C2) at L4 (per-seed SD %s), then returned to %s at L5. B3 flagged "
          "%s of C2 copies at every level but only %s to %s of C1 copies. B4 stayed at %s at L0 to L3, %s and %s at L4, and %s and %s at L5 "
          "(C1, C2)."
          % (pct(D["A2"]["C1"][0]), pct(D["A2"]["C1"][4]), pct(D["A2"]["C2"][4]), pct(D["A2"]["C1"][5]),
             pct(min(D["B1"]["C1"][:5])), pct(max(D["B1"]["C1"][:5])), pct(min(D["B1"]["C2"][:3])), pct(max(D["B1"]["C2"][:3])), pct(D["B1"]["C2"][5]),
             pct(D["B1"]["C2"][3]), pct(D["B1"]["C2"][4]),
             pct(min(D["B2"]["C1"][:4] + D["B2"]["C2"][:4])), pct(D["B2"]["C1"][4]), pct(D["B2"]["C2"][4]), pct(M["sd_seed"][("B2", "C1", 4)][1]),
             pct(D["B2"]["C1"][5]),
             pct(min(D["B3"]["C2"])), pct(min(D["B3"]["C1"])), pct(max(D["B3"]["C1"])),
             pct(min(D["B4"]["C1"][:4] + D["B4"]["C2"][:4])), pct(D["B4"]["C1"][4]), pct(D["B4"]["C2"][4]), pct(D["B4"]["C1"][5]), pct(D["B4"]["C2"][5])))
    S.par("~~Interpretation.~~ What a supervisor reads decides what it can see. Report-only supervisors fail or are fragile because the copier "
          "controls the report. Checking a claim against its source is not enough when the false claim is partly true, and it creates a perverse "
          "incentive: a careful copier is caught less often than a sloppy one. Comparing the artifacts directly is the robust signal, and "
          "semantic similarity holds up longer than word overlap against surface disguise, though that is tested here only against surface disguise.")
    S.par("**4.3 Probability quality.** Table 1 and Figure 2b give Brier scores. The no-information reference is %.3f. A1 (%.3f) is worse than "
          "the reference because its calibration-half base rate differs from the test half. B4 has the lowest Brier score (%.3f), against %.3f for "
          "B2, %.3f for A2 and %.3f for B1. The B2 minus B4 difference is positive in all %d seeds (mean %.3f). At L4, B4 scores %.3f against "
          "%.3f for B2 and a reference of %.3f; at L5, %.3f against %.3f for B2."
          % (M["acuan"], B["A1"]["semua"], B["B4"]["semua"], B["B2"]["semua"], B["A2"]["semua"], B["B1"]["semua"], n_seed, sel_b,
             B["B4"][4], B["B2"][4], B["acuan"][4], B["B4"][5], B["B2"][5]))
    kode_tab = ["A1", "A2", "B1", "B2", "B3", "B4", "BU"]
    nama_tab = {"A1": "A1 claim-trust", "A2": "A2 summary reader", "B1": "B1 quote check", "B2": "B2 artifact overlap",
                "B3": "B3 twin sources", "B4": "B4 embedding", "BU": "B1|B2|B3|B4 (union)"}
    baris = [["Supervisor", "False alarm [95% CI]", "Per-seed range", "Detect C1", "Detect C2", "Brier", "Brier L4", "Brier L5"]]
    for k in kode_tab:
        br = B.get(k)
        baris.append([nama_tab[k], "%s [%s–%s]" % (pct(F[k][0], 1), pct(F[k][1], 1), pct(F[k][2], 1)),
                      "%s–%s" % (pct(M["fpr_seed"][k][0], 1), pct(M["fpr_seed"][k][1], 1)), pct(M["det_gab"][k]["C1"]), pct(M["det_gab"][k]["C2"]),
                      "%.3f" % br["semua"] if br else "–", "%.3f" % br[4] if br else "–", "%.3f" % br[5] if br else "–"])
    baris.append(["No-information reference", "–", "–", "–", "–", "%.3f" % M["acuan"], "%.3f" % B["acuan"][4], "%.3f" % B["acuan"][5]])
    S.tabel(baris, [1.4, 1.5, 0.85, 0.55, 0.55, 0.5, 0.5, 0.5], ukuran=Pt(8),
            judul="Table 1. Per-supervisor summary. False alarms are on %d honest test scenarios; detection is pooled over all six levels for "
                  "copy types C1 and C2; Brier is on all test scenarios (L4 and L5 columns pool the honest scenarios with that level's copies)." % n_h)
    S.gambar(os.path.join(dir_gambar, "fig2_alarm_brier.png"), 6.3,
             "Figure 2. (a) False-alarm rate on honest bots with 95% Wilson intervals; the dotted line is the 5% calibration target. (b) Brier score "
             "over all test scenarios; the dotted line is the no-information reference.")
    S.par("**4.4 Robustness.** Intervals in Table 1 and Figure 2a treat scenarios as independent, but all seeds draw from one pool of 3,908 chunks "
          "and twin scenarios reuse a limited set of pairs, so those intervals are optimistic. Seed-to-seed variation is the more honest "
          "guide: B4's L4 detection in C1 had SD %s across seeds and B2's had SD %s. The ordering of B4 over B2 in Brier score held in every seed."
          % (pct(M["sd_seed"][("B4", "C1", 4)][1]), pct(M["sd_seed"][("B2", "C1", 4)][1])))

    # ---------------- 5. Discussion ----------------
    S.h2("5. Discussion and Limitations")
    S.par("The result is a practical rule for multi-agent oversight: a claim of independence should be checked on the artifacts, not read from the "
          "report, and the check should compare artifacts with each other as well as with the sources they cite. Self-reports are controlled by "
          "the agents being supervised, and the sprint overview describes agents that edited or spoofed their own records; artifact checks help only "
          "if artifacts are held where agents cannot rewrite them, for example at a gateway. Base rates matter: with a true copy prevalence of %s, "
          "B4's detection of %s and false-alarm rate of %s give a positive predictive value of only %s, so a flag should trigger a review, not a "
          "verdict. The real corpus also contains at least 150 cross-book pairs sharing a passage; honest agents citing two different books can "
          "therefore already violate independence, independently of any copier." % (pct(ppv["prev"]), pct(ppv["tpr"]), pct(ppv["fpr"], 1), pct(ppv["ppv"])))
    S.h3("Limitations")
    S.par("(1) **Scripted bots.** Copiers do not adapt to the supervisors; an adaptive language-model copier could search for disguises that "
          "defeat B4. (2) **Surface-level disguise.** None of L1 to L5 is a semantic paraphrase or a translation; B4's advantage may shrink there, "
          "and B1 to B3 would fail against translation. (3) **No language-model supervisor.** A2 is a rule-based proxy, so our conclusions about "
          "report readers apply to rule-based readers only. (4) **Artifacts are assumed intact.** If a copier can edit bot 1's artifact or the log, "
          "B-family supervisors fail; our threat model excludes this. (5) **One domain.** School textbooks in two languages, with honest "
          "negatives chosen by lexical similarity rather than by semantic similarity. (6) **Mixture-dependent metrics.** The test base rate of "
          "copies is high by design, and Brier scores and the reference depend on it. (7) **Calibration drift.** Observed false alarms differ from "
          "the 5% target per seed. (8) **Optimistic intervals** (Section 4.4). If assumption (4) fails, all artifact results become upper bounds; "
          "if copiers translate, B1 to B3 drop sharply and B4 becomes the only candidate.")
    S.h3("Future Work")
    S.par("Adaptive copiers (language models trained against each supervisor); language-model supervisors that read reports, compared on the "
          "same scenarios with public text so that cloud models may be used; tamper-resistant artifact capture at an agent gateway; cross-language "
          "copies; and a human-labelled evaluation of twin-source cases.")

    # ---------------- 6. Conclusion ----------------
    S.h2("6. Conclusion")
    S.par("Agents that cite different sources can still be one source. In a controlled test on real textbook text, a supervisor that trusts "
          "claims never caught copying and a report-content reader was fragile, while comparing artifacts (embedding) caught at least %s of copies "
          "at every disguise level with %s false alarms. Checking quotes against claimed sources fails when the claimed source is a genuine twin. "
          "These results bound the benefit of artifact checking against scripted, surface-level copiers; adaptive copiers and language-model "
          "supervisors are the necessary next test." % (pct(min(D["B4"]["C1"] + D["B4"]["C2"])), pct(F["B4"][0], 1)))

    # ---------------- Code and Data ----------------
    S.h2("Code and Data")
    S.par("The code, 19 unit tests, scripts and per-seed score files (no book text) are in the project folder 27_Swarm_Provenance. Book text cannot "
          "be released (copyright; local-only processing), so the corpus is not shared; the scenario generator is deterministic given a corpus and seed.",
          sesudah=3)
    S.daftar("bullet", ["Code repository: [link to be added by the authors]",
                        "Data/Datasets: scores per seed (hasil/seed_*.json) [link to be added]; textbook corpus not released",
                        "Other artifacts: none"])
    S.h2("Author Contributions (optional)")
    S.par("[To be completed by the authors.]")

    # ---------------- References ----------------
    S.h2("References")
    S.par("Entries marked † are cited by title and year as listed on the sprint Resources page and were not independently retrieved.", sesudah=3, ukuran=__import__("docx").shared.Pt(9))
    S.daftar("ref", [
        "Apart Research and AI Alignment Foundation (2026). Swarm Alignment Hackathon: Overview, Resources and Guidelines. https://apartresearch.com/sprints/swarm-alignment-2026 (accessed 6 Nov 2026).",
        "Brier, G. W. (1950). Verification of forecasts expressed in terms of probability. Monthly Weather Review, 78(1), 1–3. doi:10.1175/1520-0493(1950)078<0001:VOFEIT>2.0.CO;2",
        "Broder, A. Z. (1997). On the resemblance and containment of documents. In Compression and Complexity of Sequences (SEQUENCES'97), IEEE Computer Society, pp. 21–29. doi:10.1109/SEQUEN.1997.666900",
        "Google. EmbeddingGemma-2 (740M), run locally through Ollama (accessed 6 Nov 2026).",
        "Greenblatt, R., Shlegeris, B., Sachan, K., and Roger, F. (2024). AI Control: Improving safety despite intentional subversion. Proceedings of the 41st International Conference on Machine Learning, PMLR 235:16295–16336. arXiv:2312.06942",
        "† Hammond et al. (2025). Multi-Agent Risks from Advanced AI.",
        "† Jones et al. (2025). Splitting tasks to evade per-agent safety filters.",
        "† METR (2026). Investigation of the Hugging Face incident.",
        "Motwani, S. R., et al. (2024). Secret collusion among AI agents: Multi-agent deception via steganography. Advances in Neural Information Processing Systems 37 (NeurIPS 2024). arXiv:2402.07510",
        "Platt, J. C. (1999). Probabilistic outputs for support vector machines and comparisons to regularized likelihood methods. In Advances in Large Margin Classifiers, MIT Press, pp. 61–74.",
        "† Rose et al. (2026). Detecting multi-agent collusion through multi-agent interpretability.",
        "Wilson, E. B. (1927). Probable inference, the law of succession, and statistical inference. Journal of the American Statistical Association, 22(158), 209–212. doi:10.1080/01621459.1927.10502953",
        "† Zhang et al. (2025). Attributing failures in multi-agent systems.",
    ])

    # ---------------- Appendix ----------------
    S.h2("Appendix")
    S.h3("A. Limitations and Dual-Use / Ethical Considerations")
    S.par("**What the result does and does not establish.** It establishes that, for scripted copiers with surface-level disguises on textbook text, "
          "comparing artifacts detects false independence much better than reading claims or summaries, at a measured false-alarm cost. It does not "
          "establish performance against adaptive or language-model copiers, semantic paraphrase, translation, tampered artifacts or other domains "
          "(Section 5). **Dual use.** The disguise generator and the finding that heavy mixing (L4) and mosaics (L5) lower detection could help a "
          "copier choose evasions. We judge the risk low: the disguises are crude, the detectors still flag most of them, nothing here attacks a "
          "deployed system, and the same results tell defenders which signals to combine. **Data and ethics.** Textbook content is used only locally "
          "for research, is not redistributed, and no personal data are involved. False alarms have a human cost if flags are treated as verdicts; "
          "we recommend human review of flagged cases (Section 5).", sesudah=6)
    S.h3("B. Detection rate by level")
    nam_lv = ["L0", "L1", "L2", "L3", "L4", "L5"]
    for t, ket in (("C1", "Table B1. Detection rate (%%) by disguise level, copier cites a different real passage (n = %s per level)"),
                   ("C2", "Table B2. Detection rate (%%) by disguise level, copier cites a genuine twin source (n = %s per level)")):
        baris = [["Supervisor"] + nam_lv]
        for k in kode_tab:
            baris.append([nama_tab[k]] + [pct(x) for x in D[k][t]])
        S.tabel(baris, [1.9, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7], ukuran=Pt(8.5),
                judul=ket % ("%d–%d" % (min(M["n_cel"][t]), max(M["n_cel"][t])) if min(M["n_cel"][t]) != max(M["n_cel"][t]) else str(M["n_cel"][t][0])))
    S.par("Mean thresholds τ over seeds: " + ", ".join("%s = %.3f" % (k, M["ambang"][k]) for k in ("A2", "B1", "B2", "B3", "B4")) + ". A1 uses 0.", sesudah=6, ukuran=Pt(9))
    S.h3("C. Pre-existing work versus work done during the sprint")
    S.par("**Pre-existing (before 6 Nov 2026, not claimed):** the conversion of the 184 textbooks to page-level JSON; the chunker "
          "(embed_korpus.buat_potongan) and the embedding of all chunks with EmbeddingGemma-2; and the local Ollama client (embed_lokal), taken from the earlier 69-bot "
          "Tools Sakti project, whose other code and audits were not used in the experiment. **Done during the sprint:** the scenario generator, disguise "
          "levels, twin scan, all six supervisors, thresholding, calibration and Brier scoring, the experiment runner, unit tests, figures, and this report.")
    S.h3("D. Disguise parameters")
    S.par("L1: lower-case, a space inserted before periods and commas, 30% of spaces doubled. L2: random shuffle of sentences. L3: each word dropped with probability 0.15, "
          "then adjacent pairs swapped with probability 0.15. L4: sentences shuffled, words dropped with 0.35, pairs swapped with 0.30, filler words "
          "(from 20 unrelated chunks) inserted up to 25% of the length. L5: sentences at odd positions replaced by sentences of the claimed source.", ukuran=Pt(10))
    S.h2("LLM Usage Statement")
    S.par("We used Claude (Anthropic; Claude Code, Sonnet 5.5) to write and test the experiment code, run the analyses and draft this report; Claude "
          "Haiku sub-agents audited the pre-existing code base and searched a local article collection for references (none of its articles were finally cited). All figures and tables are "
          "generated by scripts from the stored run outputs; bibliographic details of references not marked † were checked against web sources. "
          "[Authors: please review and edit this statement and the text of the report, which the template encourages teams to write primarily themselves.]")
    return JUDUL, abstrak
