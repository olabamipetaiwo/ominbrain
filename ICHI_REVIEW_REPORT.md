# IEEE ICHI Simulated Peer Review: *Measuring Image Dependence, Not Just Response Sensitivity: Controlled Ablation Tests on Brain-MRI Question Answering*

**Material reviewed:** `paper/latex/ichi_latex.tex` (695 lines) and the compiled `paper/latex/ichi_latex.pdf` (10 pp., build of Oct 15, 2026). I also reviewed the anonymous artifact `release/anon_artifact/`: the analysis plan, prompts, raw model outputs, stats and permutation outputs.
**Conducted:** Oct 15, 2026. This is a fresh, independent review. The earlier `REVIEW_REPORT.md` was not consulted. No manuscript or artifact file was modified.
**Conventions:** `L###` means a line in `ichi_latex.tex`, and `p.#` means a physical PDF page. Issue IDs (**M1–M7**, **m1–m6**) are defined once in §3–5 and referred to by ID after that.
**Independent recomputation:** My scripts are in the session scratchpad. They reuse the artifact's `load_records` loader. All analyses use the shipped responses only, and no model inference was run.

---

## 1. Executive Scientific Assessment

The paper is scientifically careful and unusually transparent. Its central methodological idea holds up: an image-minus-text accuracy gap should be read together with (a) the answer prior, (b) a no-image-corrected donor-key gain and (c) a test that separates donor-specific tracking from a generic image shift. The reference-model results establish that AIA and LIL are feasible. The open-model results are reported with appropriate caution. Every number I recomputed from the raw outputs matched the paper (§7).

The main rejection risk is not a hidden flaw in the data. It is how the **central worked example** (Llama-4-Scout on DSCR, Fig. 2) is interpreted:

- **M1 (Major).** The analysis plan's own E2 decision rule says tracking *is claimed* when the gain interval lies above 0. That rule is met by Scout/DSCR [+7.1, +50.0] and MedGemma/AIA [+2.2, +19.6]. The paper overturns this with two post hoc steps: a permutation test, and Holm correction over E2, a family the plan says is not adjusted. It never states that the prespecified rule was met. The abstract's claim that "no donor-specific tracking survives multiplicity correction" therefore rests entirely on post hoc analyses.
- **M2 (Major).** I ran a conditional label-association test on the **own-image** arm. It uses the same logic as the paper's donor permutation, with n=46, no donor reuse, and strata by image count. It finds that Scout's DSCR predictions associate with the key: κ=0.19, unadjusted p=0.015. A text-only negative control is null (p=0.88), and the result is not significant after Holm over 12 cells (p=0.175). The evidence is therefore *weak and mixed*, not "not separable from random". Fig. 2 also uses the below-majority comparison as a failing control, although §IV and Table VI say that comparison is not diagnostic.

Both issues can be fixed through reframing plus one reanalysis of existing outputs. Neither needs new model inference. Several smaller claim–evidence issues are also fixable in minutes: M3–M7 cover TCM evidence pooled into image claims, an unreported prespecified sensitivity analysis, uncited concurrent mismatched-image work, an over-broad "significant throughout" statement, and undisclosed tuning of the DSCR rule.

**Recommendation: submit only after addressing specific major concerns (M1, M2), which can be done in the available time.**

---

## 2. Reconstruction of the Paper's Contributions

| Element | Reconstruction |
|---|---|
| Problem | Accuracy changes under image ablation or swap do not show that a model reads the image correctly. They can reflect language priors, generic response shifts or default answers (L169, L185). |
| Healthcare relevance | Medical MLLM benchmarks are reported by accuracy. Evaluators need tests that separate image use from shortcuts before any trust claim is made. |
| Gap | Ablation studies report accuracy deltas or sensitivity. HEAL-MedVQA perturbs regions. Neither scores swapped answers against the donor's key with the prior subtracted, conditional on donor assignment (L443). |
| Questions | E1 image effect (prespecified, Holm-12); E2 donor gain (prespecified, interval rule); E3 use of stated facts (TCM); E4 upstream context; E5 PJRF (secondary). Post hoc additions: the reference model, precision controls, the conditional permutation, the explicit-rule TCM condition and the transition tables. |
| Contributions | (C1) A protocol separating accuracy benefit, output sensitivity and donor tracking, with a worked case. (C2) A LUMIERE item set with explicit key provenance, plus a rule–expert audit (38% agreement on determinate follow-ups). (C3) An evaluation of four open models and one reference model. |
| Principal findings | The reference model reads sequence and side (95.7/100% vs 21.7/36.8% text-only) and follows donor keys. Open models: one Holm-surviving E1 effect (Scout/DSCR); no tracking survives the post hoc permutation plus Holm; TCM below the oracle lookup. |
| Intended ICHI contribution | An evaluation methodology for medical MLLMs, i.e. how to tell observable image dependence apart from response sensitivity. |

The intended contribution is methodological (C1). Its evidential weight therefore rests on (i) the AIA/LIL reference demonstration, which is strong, and (ii) the Scout/DSCR worked example, which is weaker than presented (M1, M2).

---

## 3. Reviewer 1: Methodology and Technical Soundness

**Paper summary.** Covered in §2. Each image phase is run with the own image, with text only, and with a matched donor swap, all under fixed context. Keys are mechanically derived: the sequence for AIA, segmentation masks for LIL and DSCR, and a rule for TCM. Inference uses paired exact tests, bootstrap intervals and a constrained permutation for donor-label association.

**Strengths**
- Fixed-context, one-question conditions isolate each phase from chain error propagation (L507).
- Stems for AIA, LIL and DSCR contain no patient-specific fact, and every option set contains all classes (Table I). I verified this in `prompts.jsonl`, so swap conditions never conflict with the text.
- Option order is shuffled per item (19–23 distinct orders per phase), and own, text and swap conditions share the same order within an item. This prevents a letter-position bias from masquerading as an image effect.
- Seeds, Holm family, margin and decision rules were fixed in a dated plan. Amendments (the cohort rebuild and the DSCR stem reword) are disclosed (L505).
- The authors are candid about key provenance, the DSCR new-lesion gap, selection enrichment for agreement (L487) and confounds in the precision control.

**Major weaknesses**

**M1. The prespecified E2 decision rule is overridden by post hoc analyses without saying so.**
- *Location:* Abstract L171 ("no donor-specific tracking survives multiplicity correction"); §V-d L566; Fig. 2 L579 ("three prespecified additions"); Conclusion L621.
- *Evidence:* `analysis_plan.md` (E2) says "Image tracking is claimed for a model and phase only if the interval for mean(G) lies above 0", and "No other family is adjusted." Table V shows Scout/DSCR +28.6 [+7.1, +50.0] and MedGemma/AIA +10.9 [+2.2, +19.6], so both meet the rule. The paper then applies a post hoc permutation and a post hoc Holm over 12 E2 cells, concluding "we read neither as donor-specific tracking." L566 says the cells have "an interval above zero" but never states that this satisfies the prespecified claim criterion.
- *Scientific consequence:* A reader comparing the paper with the shipped plan will see a prespecified positive result reversed by unplanned analyses, which looks like outcome switching. The post hoc reasoning is sound, since a generic image shift can produce a positive G (Table VII). The flaw is the non-disclosure and the abstract's framing, not the logic.
- *Severity:* Major. *Remedy:* State explicitly that both cells meet the prespecified E2 criterion, and that the post hoc permutation is why they are not interpreted as donor-specific. Reword the abstract and Fig. 2 accordingly (see §11). *Resolution type:* Reframing/Clarification.

**M2. The worked example's verdict is not robust to a more direct test of the same hypothesis.**
- *Location:* Fig. 2 (L575–599, p.7); §V-b L562; §V-e L602; Contribution 1 (L189); Table VII caption.
- *Evidence (independently computed from shipped outputs):*
  1. Because DSCR stems carry no patient information, the question the permutation asks ("do answers match the key of the image shown more than another item's key?") can be asked directly in the own-image arm. I permuted keys among items within image-count strata, holding predictions fixed (20,000 draws). For Scout/DSCR this gives κ=0.19 and p=0.015. The negative control (the same test on text-only answers) gives p=0.88, which rules out an option-order or stem artifact. After Holm over the 12 open-model cells, p=0.175. Scout/AIA gives p=0.018, and all other open-model cells give p≥0.06.
  2. In the swap arm, Scout's answer equals its own-image answer for that donor's images in only 27/42 cases. The two prompts differ only in patient ID and option order, so the swap arm adds substantial prompt-perturbation noise that lowers its power relative to the own-image test.
  3. The shipped `lumiere_v4_perm_validation.json` shows that the permutation null for Scout/DSCR has mean gain ≈23.0 pp (SD 6.2). Most of the observed +28.6 pp is therefore expected under random donor assignment. This *supports* the paper and should be reported. It also shows that Table VII's power figures, which come from synthetic guessers without class bias, overstate power for a PD-biased model: Scout predicts PD for 30/46 items.
  4. Fig. 2 card c1 ("With the image 54.3% < most-common key 58.7%: no gain over a constant answer") is presented as a failing control. However, §IV (L503) states that below-majority accuracy "neither establishes nor refutes image use", and the Table VI caption says the same. Fig. 2 thus contradicts the paper's own stated logic.
  5. Under the alternative donor assignments, p ranges from .057 to .548, and three of five are below .16. "Not detected under any assignment" is literally true but reads as stronger evidence of absence than it is.
- *Scientific consequence:* The correct reading is that category reading is *suggested but not established after multiplicity correction*, not that it is "not separable from random." C1's message ("ablation alone credits image use; the additions do not") survives only in a weaker form: the additions show the gain is mostly non-specific, while some key-specific signal may remain.
- *Severity:* Major, because it bears on the paper's headline demonstration. *Remedy:* Report the own-image association test as a post hoc analysis, report the permutation null mean, revise c1 and the Fig. 2 verdict, and soften C1's wording. *Resolution type:* Reanalysis + Reframing, with no new inference.

**Moderate weaknesses**
- **M5. DSCR rule tuned against the expert ratings (not disclosed in the paper).** The plan states that "the DSCR rule was adjusted (nadir; abstention) before item building after its agreement with the expert ratings was inspected." The 38% agreement (L461, abstract) is therefore not independent of rule development. Tuning toward agreement would, if anything, inflate it, so the headline "low agreement" is conservative. Disclosing this is still required. *Remedy:* add one sentence to §III-A. *Resolution type:* Clarification.

**Minor weaknesses**
- **m1.** The permutation p-values for the same cell differ across shipped files: Scout/DSCR is .293 in the paper (supplement, 5,000 draws), .297 in `strat_perm` (50,000 draws), .287 in robustness and .240–.250 in `perm_validation`. MedGemma/AIA is .040 vs .0387, with Holm .482 vs .464. The differences are within Monte Carlo and sampler-variant error, but the README should say which file the paper uses.
- **m2.** Table III labels Gemma-3-27B/DSCR as "within ±10 pp". The model answers PD for all 46 items in both arms, so the bootstrap is degenerate. The add-half CI [−4.1, +4.1] supports the label, but a footnote ("constant answer in both arms") would prevent misreading.

**Questions for authors**
1. Under the plan's E2 rule, would the two cells have been reported as tracking had the permutation not been added? Why is this not stated?
2. Why was the conditional association test run only on the swap arm, when stems are patient-agnostic and the own-image arm has more items and no donor reuse?
3. What is the permutation's power against a tracker with Scout's class bias (PD-heavy marginals), rather than an unbiased guesser?

**Recommendation:** Borderline Accept, conditional on M1 and M2 being reframed. **Confidence:** 4/5. I read the full manuscript, plan and code paths and recomputed the key statistics. I did not rerun inference or review the image rendering.

---

## 4. Reviewer 2: Experimental Evaluation and Statistical Validity

**Paper summary.** Four 4-bit open models and one API reference model are evaluated on 46 patients (LIL 38; DSCR swap 42). E1 uses paired exact McNemar tests with Holm-12 and a ±10 pp margin. E2 uses a donor-key gain with bootstrap and add-half intervals. Diagnostics include a post hoc constrained permutation calibrated on synthetic predictors (Table VII).

**Strengths**
- The statistical reporting is careful. It includes exact p-values, sparse-data intervals where the bootstrap collapses (L510), separate denominators for donor-paired items (Table III/V captions) and explicit statements that non-significance is not evidence of no effect (L562, L171).
- Non-model references (Table II) make prior-driven accuracy visible: AIA 26.1%, DSCR majority 58.7% and the TCM lookup bounds.
- Table VII is a well-designed demonstration that gain and answer-change rate cannot separate a generic shift from a tracker.
- The numbers are internally consistent. Every value I checked matched (§7).

**Major weaknesses:** M1 and M2 (see §3). From the statistical side, M2's key point is that a single post hoc non-detection (p=.293) from the noisier of two available tests carries the Fig. 2 verdict. A more direct test of the same null gives p=.015 unadjusted.

**Moderate weaknesses**

**M3. A prespecified sensitivity analysis is computed but not reported.**
- *Location:* Missing from §V-b. In the plan: "Sensitivity, not primary: DSCR restricted to items whose category also equals the expert RANO rating". In code: `lumiere_v4_stats.py` L148–152, and `expected/lumiere_v4_stats.json`.
- *Evidence:* On the 26 agreeing items (PD share 80.8%), Scout's difference is +57.7 [+34.6, +76.9] (61.5% vs 3.8%, p=.0003). The reference model's is 0.0 (80.8% in both arms), Gemma-3-12B's is +19.2 [+3.8, +34.6], and MedGemma's is +3.8.
- *Consequence:* Omitting a prespecified analysis is a reporting gap. The result is also informative: on the subset whose key is corroborated by the expert, the reference model shows no image effect and Scout stays below the subset majority. This reinforces the "DSCR is exploratory" framing and is worth one sentence.
- *Severity:* Moderate. *Remedy:* Report it in one sentence. *Resolution type:* Reanalysis (already computed).

**M4. "The reference model stays significant throughout" overreaches.**
- *Location:* L566 (DSCR robustness paragraph).
- *Evidence:* `lumiere_v4_robustness_Gemini-3.6-Flash.json` contains alternative assignments for AIA and LIL only. No Gemini DSCR permutation p-value exists in the artifact or the paper.
- *Consequence:* In the context of the DSCR robustness sentence, readers will take it as covering DSCR. *Severity:* Moderate. *Remedy:* Add "on AIA and LIL". *Resolution type:* Clarification.

**Minor:** m1 and m2 (see §3). **m3.** The phrase "Empty API responses are counted and rerun (0 of 386 records)" (L519) is confusing. Say "none occurred." **m4.** The claims "Both survive resampling by donor and dropping any one donor" (L566) are reported from `donor_dependence` output and were not independently re-derived by me.

**Questions**
1. Report the permutation null mean gain for each E2 cell. Readers then see directly how much of each gain is generic.
2. Does Holm-12 across E2 cells belong to the plan, or is it a new post hoc family? (See M1.)

**Recommendation:** Borderline Reject as written, moving to Borderline Accept if M1–M4 are addressed. The data and computations are sound. The concern is how the central example is inferred. **Confidence:** 4/5, for the same reasons as Reviewer 1.

---

## 5. Reviewer 3: Novelty and Healthcare Informatics Significance

**Paper summary.** See §2.

**Strengths**
- The question is real and practical for medical-AI evaluation: accuracy deltas are routinely over-read as evidence of perception.
- The paper establishes that the OmniBrainBench groupings cannot support same-patient chains (2 verifiable links among 6,823 questions, L454). This is a useful negative finding about a CVPR 2026 benchmark.
- The paper documents clearly that expert RANO ratings cannot be naively treated as image-recoverable targets (L461). This is valuable for anyone building response-assessment VQA from LUMIERE.
- Scope discipline is good: there are no clinical-readiness claims, the ethics statement is appropriate, and limitations are extensive and specific.

**Moderate weaknesses**

**M6. TCM results are pooled into the image-dependence claim.**
- *Location:* Abstract L171 ("...limited and inconsistent evidence of correct image dependence...: ...and none exceeds the best category lookup on the management rule"); Conclusion L621.
- *Evidence:* TCM has no image (Table I). The lookup is a sample oracle applying a rule that the main condition does not give to the model (L604 concedes it is "descriptive").
- *Consequence:* This is a category error in the headline claim. It invites the objection that the paper evaluates image dependence with an image-free task. *Severity:* Moderate. *Remedy:* Move the TCM statement to a separate clause labelled as the image-free management step. *Resolution type:* Reframing.

**M7. Recent concurrent work with mismatched or shuffled images is not cited.**
- *Evidence:* A web search, which I verified only at snippet level and not by reading full papers, finds medical-VQA evaluations from 2026 that use blank, shuffled or other-case images: *Beyond Accuracy: Evaluating Visual Grounding in Multimodal Medical Reasoning* (arXiv 2603.03437), with Visual Reliance Score and Image Sensitivity, and *Ask4VG* (arXiv 2606.01044), with original, blank and mismatched-case images. As far as the snippets show, these measure answer similarity or sensitivity and do not score the swap against the donor's key with a prior correction. The paper's increment therefore appears to survive.
- *Consequence:* Reviewers in this area may know these papers. The current related-work section positions the paper only against HEAL-MedVQA and Goyal et al., which overstates the gap. *Severity:* Moderate. *Remedy:* Add one sentence with the citations and the differentiation, after checking the details of each paper. *Resolution type:* Clarification.

**Novelty assessment.** The novelty is methodological and modest. The specific combination is new as far as I could verify: donor-key scoring minus the no-image donor agreement, a conditional label permutation, and reference values per phase. The individual components are established. M2 additionally shows that the conditional association idea does not *require* the swap when stems are patient-agnostic. The authors should say why the swap remains useful, for example in settings with patient-specific text, or because it directly operationalizes counterfactual tracking. This is a framing point and does not undermine the contribution.

**Claim–evidence notes** are in §6. Claims about the reference model, the audit, OmniBrainBench and precision are well qualified. Overreach is concentrated in the abstract/conclusion donor-tracking sentence (M1), Fig. 2 (M2) and TCM pooling (M6).

**Questions**
1. Could the protocol be applied to an existing benchmark such as VQA-RAD or HEAL-MedVQA, so that the method's generality is shown beyond one 46-patient set?
2. What concrete evaluation guidance should a benchmark builder take away, for example a checklist?

**Recommendation:** Borderline Accept. The contribution suits the ICHI evaluation audience if the headline example is reframed honestly. **Confidence:** 3/5. My literature verification was limited to search snippets.

---

## 6. Claim–Evidence Matrix

| # | Claim | Location | Evidence | What it establishes | Alternative explanation | Assessment |
|---|---|---|---|---|---|---|
| 1 | The reference model reads sequence and lesion side, so the tasks are feasible | Abstract, L560, Table IV | 44/46 and 38/38 vs 10/46 and 14/38; donor keys 95.7/100%; perm p≈.0002 under all assignments | Image-specific, key-concordant behavior for AIA/LIL | Rendering artifacts unique to sequence (unlikely given swap tracking) | **Fully supported** |
| 2 | Open models show limited and inconsistent evidence of correct image dependence | Abstract, L621 | Table III/V; one E1 test survives Holm | Weak evidence on AIA/LIL; DSCR mixed | — | **Supported**, but the list of reasons includes TCM (M6) |
| 3 | "No donor-specific tracking survives multiplicity correction" | Abstract, L621 | Post hoc permutation + post hoc Holm (p=.482, .293) | Nothing survives the post hoc analysis | Prespecified E2 rule met in 2 cells (M1); own-image association p=.015 (M2) | **Partially supported.** Narrower form: "two cells meet the prespecified gain criterion; neither survives the post hoc conditional permutation after correction" |
| 4 | Scout/DSCR: the ablation alone credits image use and the additions do not establish it | C1 L189, Fig. 2, L602 | Δ=+45.7; acc < majority; text-only 8.7%; perm p=.293; null mean gain ≈23 pp | The gain is mostly non-specific (prior + generic shift) | Weak key-specific reading (κ=.19, p=.015 unadj.) | **Partially supported.** "Suggested but not established after correction" |
| 5 | A slice-based rule matches the expert rating for 38% of 197 determinate follow-ups | Abstract, L461 | 75/197; Wilson 32–45% (verified) | Low rule–expert agreement | Rule tuned toward agreement (M5); measurement error | **Fully supported** (disclose M5) |
| 6 | OmniBrainBench has only 2 verifiable cross-phase links | L190, L454 | Shipped link counts | Released groupings do not provide chains | Lower bound only (stated) | **Supported** (not re-derived by me) |
| 7 | Two bf16 reruns remain near chance, so 4-bit serving is an unlikely sole cause | Abstract, L564 | 26.1 vs 26.1; 30.4 vs 26.1 | Precision alone does not restore AIA | Stack, scale and training (stated) | **Supported as qualified** |
| 8 | None exceeds the best category lookup on TCM | Abstract, L604 | Oracle 84.8% vs ≤69.6% unstated, ≤82.6% stated | Incomplete rule adherence | The rule is unstated in the main condition | **Supported for TCM. Misplaced as image evidence (M6)** |
| 9 | Below-majority Scout accuracy reflects redistributed errors, not non-use | L562, Table VI | 6/19 non-majority items recovered | Not a constant predictor | — | **Supported.** Strengthened by my association test (M2) |
| 10 | Stating the rule raises TCM accuracy, but it is followed incompletely | L604 | +13.0, +10.9, +13.0, +0.0 | As stated | — | **Fully supported** |
| 11 | The reference model "stays significant throughout" | L566 | AIA/LIL only | AIA/LIL robustness | — | **Partially supported** (M4) |

---

## 7. Methodological and Reproducibility Audit

**What I verified (from shipped raw outputs and prompts):**
- E2 swap=donor, text=donor and gain for all 7 models × 3 phases match Table IV/V exactly. For example, Scout/DSCR is 50.0/21.4/+28.6 and MedGemma/AIA is 32.6/21.7/+10.9.
- E1 Scout/DSCR is 25/46 vs 4/46. The Table VI confusion matrix is internally consistent (diagonal 25; 6/19 off-majority; recalls 44/33/0%).
- Audit arithmetic: 75/197=38.1%; Wilson [31.6, 45.0]; 75/241=31.1%; 122 disagreements. The selection count 26/46=56.5% matches.
- TCM: lookup bounds 39/46=84.8% and 26/46=56.5%; 7+20=27 PD items; explicit-rule deltas (6/46, 5/46). PJRF base rate 28/45.
- The paper's p-values come from `lumiere_v4_supplement.json`. Holm .482 is consistent with p=.040×12 (m1).
- Stems: no patient-specific fact in AIA, LIL or DSCR. Options shuffled per item and shared across conditions within an item. Text-only prompts still describe images as "shown" (disclosed, L634).
- DSCR image count (2 vs 3) is revealed by the stem wording and correlates with the key (PD in 16/22 three-image vs 11/24 two-image items). PD is the majority in both strata, so a stratum lookup does not beat 58.7%. *I investigated this as a leakage concern and withdrew it.*

**What I did not verify:** image rendering and slice selection, segmentation-derived keys against images, the OmniBrainBench link counts, the donor leave-one-out and cluster intervals, and the Type-I calibration simulations (I only read their output).

**Issue classification**

| ID | Category |
|---|---|
| M1 | Unsupported scientific interpretation (deviation from plan without disclosure) |
| M2 | Unsupported scientific interpretation + missing analysis |
| M3 | Missing methodological report (prespecified analysis omitted) |
| M4 | Minor documentation issue with interpretive impact |
| M5 | Missing methodological explanation |
| M6 | Unsupported interpretation (category error) |
| M7 | Related-work gap |
| m1–m4 | Minor documentation |
| New-lesion criterion, selection enrichment, quantization/stack confound, single API reference, PJRF outcome | **Already adequately disclosed** (L491, L487, L519/L636, L630, L632). These remain limitations but are not unaddressed weaknesses |

**Reproducibility.** The artifact is strong: all prompts and responses, the plan with its change log, seeds and regeneration scripts. An independent researcher could reproduce every reported statistic from the shipped outputs. Re-running inference depends on API/model versions (disclosed).

---

## 8. Senior Area Chair Metareview

All three reviewers agree on the paper's strengths: careful key provenance, a clear distinction between accuracy benefit, sensitivity and donor tracking, a decisive reference-model feasibility demonstration on AIA/LIL, exemplary disclosure, and a fully reproducible artifact whose numbers check out.

The convergent concern, raised independently by R1 and R2 and touched on by R3, is the **worked example (Scout/DSCR)**, which is meant to show why ablation alone misleads. Two problems are substantiated, not speculative. (M1) The prespecified E2 rule would have claimed tracking, and the paper's opposite reading comes from post hoc analyses without the override being stated. (M2) A more direct version of the paper's own conditional-association test finds an uncorrected association, so "not separable from random" overstates a null from a lower-powered test. Neither problem invalidates the method. The permutation null mean (≈23 pp) actually confirms that most of the gain is generic. Both problems do change what the example licenses: *mostly non-specific gain, with weak key-specific signal that is not established after correction*. This is still a valid illustration of the paper's thesis, arguably a better one.

R3's single-reviewer concerns (M6 TCM pooling, M7 uncited concurrent work) are real but minor in consequence. The reviewers disagree on severity: R2 leans reject as written, because a reviewer who opens the shipped plan will find M1. R1 and R3 lean accept because the science is sound. I side with the view that the **principal contribution survives**, provided M1 and M2 are fixed. The paper offers a meaningful, if modest, methodological contribution to healthcare-informatics evaluation, and its evidence is adequate for appropriately narrowed conclusions.

**Overall:** Borderline as submitted. Borderline Accept if M1–M2 are reframed and M3–M7 corrected.

---

## 9. Adversarial Verification of Reviewer Criticisms

| ID | Challenge | Outcome |
|---|---|---|
| M1 | Does the paper disclose the override elsewhere? L511 labels the permutation post hoc, and L566 reports both intervals as above zero. Neither says the prespecified *claim rule* was met. The abstract's "multiplicity correction" applies Holm to a family the plan explicitly left unadjusted. The plan text is verbatim. | **Retained, Major.** The logic is defensible, so the fix is disclosure, not reanalysis |
| M2 | Is my own-image test valid? Stems are patient-agnostic, keys are permuted within image-count strata, and predictions are held fixed. The text-only negative control is null (p=.88), so it is not a letter or stem artifact. Is it simply another post hoc test? Yes, and it does not survive Holm (p=.175). It therefore does **not** establish image reading. The criticism is that the paper's verdict is stated more negatively than the combined evidence allows, not that the verdict is wrong. Fig. 2 c1 contradicting L503 and Table VI is verified textually. | **Retained, Major**, explicitly scoped: an interpretation and framing issue, not a methodological error |
| M3 | Is the omission consequential? It is prespecified and the result is informative (reference Δ=0 on corroborated items). It does not change the conclusions. | **Downgraded to Moderate** (from Major) |
| M4 | Could "throughout" mean AIA/LIL? The sentence sits in Scout/DSCR robustness context, and no Gemini DSCR permutation exists. | **Retained, Moderate** |
| M5 | Does the tuning bias the audit? The direction would increase agreement, so the headline is conservative. Disclosure is still owed for a reported statistic. | **Retained, Moderate** |
| M6 | Does "on the management rule" make the separation clear? The sentence is grammatically listed as evidence of image dependence. | **Retained, Moderate** |
| M7 | Verified only through search snippets, so I cannot confirm that these works precede the submission or are peer reviewed. | **Retained, Moderate, with uncertainty stated.** Authors must check the details |
| Withdrawn | DSCR image-count leakage (stratum lookup ≤ majority); option-position artifact (null text-only control); new-lesion construct gap and selection enrichment (already disclosed adequately); E1 Holm validity (correct) | **Withdrawn / not raised** |

**Final verified list:** Major M1, M2. Moderate M3–M7. Minor m1–m4.

---

## 10. Verified P0, P1 and P2 Weaknesses

**P0 (submission-threatening):** None. No data leakage, incorrect computation, numerical inconsistency or invalid design was found.

**P1 (high-impact, fixable now):** M1, M2, M6, M3, M4, M5, M7 (ranked in §11).

**P2:** m1 (README note on which permutation file feeds the paper), m2 (Table III footnote for the constant-answer cell), m3 (wording "none occurred"), and an optional note in the Table VII caption that the synthetic guessers have no class bias.

---

## 11. Ranked Pre-Submission Correction Plan

All numbers in the replacement text below come from the shipped outputs. Regenerate them through `paper_numbers.py` before submission rather than hard-coding them.

**1. M1: Disclose the prespecified E2 rule.** No new experiment. Effort: Low.
- *Abstract (L171), replace* "no donor-specific tracking survives multiplicity correction, and none exceeds the best category lookup on the management rule." *with:*
  > "two model–phase cells meet the prespecified donor-gain criterion, but a post hoc conditional permutation separates neither from a random assignment of donor keys after multiplicity correction. On the image-free management step, no model reaches the best category lookup."
- *§V-d (L566), after* "...the phase in which its accuracy gain also survives correction." *insert:*
  > "Both cells therefore meet the prespecified E2 criterion (gain interval above zero). Because a generic response to any image can also produce a positive gain (Table VII), we added the post hoc permutation below, and we interpret the cells by it rather than by the prespecified rule; the Holm correction over E2 cells is likewise post hoc."
- *Fig. 2 (L579), replace* "but three prespecified additions leave category reading unestablished (the donor permutation is post hoc):" *with:*
  > "but the additions leave category reading unestablished (the first two are contextual; the donor permutation is post hoc):"

**2. M2: Reanalyse and reframe the worked example.** No new experiment (reanalysis of shipped outputs). Effort: Low–Medium, about 1 hour.
- Add the own-image conditional association test to `lumiere_v4_supplement.py`, using the same stratified permutation logic, Holm over 12 cells and the text-only negative control. Also report the permutation null mean gain.
- *§V-d, after the permutation sentence, insert:*
  > "Under that permutation a random assignment of donor keys yields a mean gain of about 23 points, so most of Scout's 28.6-point gain is expected without donor-specific reading. Applying the same conditional association logic to the own-image arm (keys permuted within image-count strata, answers fixed; post hoc) gives weak association for Scout on DSCR (κ = 0.19, unadjusted p = .015; text-only control p = .88) that does not survive Holm correction over the twelve open-model cells (p = .18). Category reading is therefore suggested but not established."
- *Fig. 2 card c1, replace* "no gain over a constant answer." *with:*
  > "below a constant answer (contextual, not diagnostic; Table VI)."
- *Fig. 2 verdict, replace with:*
  > "Verdict: accuracy improves over text-only, but most of the swap gain is non-specific; weak key association does not survive correction, so category reading is not established."
- *C1 (L189), replace* "its donor gain is not separable from a random donor assignment" *with:*
  > "most of its donor gain is expected under a random donor assignment and the residual key association does not survive correction"

**3. M6: Separate TCM from the image claim.** Covered by the abstract text in item 1. *Conclusion (L621), replace* "and none exceeds the best category lookup." *with:*
> "and, on the image-free management step, none reaches the best category lookup."

No new experiment. Effort: Low.

**4. M3: Report the prespecified sensitivity analysis.** *§V-b, after the sentence on Scout's DSCR accuracy, add:*
> "In the prespecified sensitivity analysis restricted to the 26 items whose rule category equals the expert rating (80.8% progressive disease), Llama-4-Scout's difference is +57.7 points [+34.6, +76.9], still below that subset's majority share, and the reference model's is 0.0 (80.8% in both arms)."

No new experiment. Effort: Low.

**5. M4: Scope "significant throughout".** *L566, replace* "while the reference model stays significant throughout." *with:*
> "while the reference model's AIA and LIL permutations stay significant under every assignment (its DSCR swap was not rerun)."

No new experiment. Effort: Low.

**6. M5: Disclose tuning of the DSCR rule.** *§III-A (L461), after* "The rule has no new-lesion criterion beyond that." *add:*
> "Its nadir handling and abstention were fixed after inspecting agreement with the expert ratings and before item building, so this agreement is not independent of rule development."

No new experiment. Effort: Low.

**7. M7: Cite concurrent mismatched-image evaluations.** *Related Work (L443), after the HEAL-MedVQA sentence, add* (after verifying the bibliographic details):
> "Concurrent evaluations probe medical VQA with blank, shuffled or other-case images and report answer similarity or sensitivity [Beyond Accuracy, arXiv 2603.03437; Ask4VG, arXiv 2606.01044]; we instead score the swapped answer against the donor's key with the no-image agreement subtracted."

No new experiment. Effort: Low.

---

## 12. Five Highest-Impact Immediate Revisions

1. **M1:** State that the prespecified E2 criterion was met in two cells, and reword the abstract, §V-d and Fig. 2.
2. **M2:** Add the own-image association test and the permutation null mean, and rewrite the Fig. 2 verdict and C1 as "suggested, not established."
3. **M6:** Remove TCM from the image-dependence claim in the abstract and conclusion.
4. **M3:** Report the prespecified expert-agreeing DSCR sensitivity analysis.
5. **M4 + M5 + M7:** Scope the "significant throughout" sentence, disclose the DSCR rule tuning, and cite the concurrent mismatched-image work. Each is a one-sentence edit.

---

## 13. Final Submission-Readiness Recommendation

1. **Is the paper defensible as is?** Mostly. The data and computations are sound, but the central worked example is framed more negatively than the combined evidence supports, and it departs from the plan without saying so.
2. **Strongest contributions:** the reference-model AIA/LIL demonstration; the separation of gain, sensitivity and donor tracking with Table VII's diagnostic; the rule–expert audit; the OmniBrainBench chain finding; and a fully reproducible artifact.
3. **Most serious verified weaknesses:** M1 and M2.
4. **Which weaknesses threaten acceptance?** M1, because it is discoverable by any reviewer who opens the plan. M2, because the headline example is the paper's main methodological demonstration.
5. **Can the central claims survive without new experiments?** Yes, in narrowed form. The fixes are reframing plus a reanalysis of existing outputs.
6. **Are the results sufficiently supported?** Yes for AIA/LIL and for the reference model. For DSCR, only as exploratory and mixed.
7. **What to correct before submission:** §11, items 1–7.
8. **What to disclose as limitations rather than present as resolved:** the post hoc status of the permutation and of the E2 Holm family; the noise in swap answers from prompt perturbation (27/42 swap–donor-own consistency for Scout); rule tuning; the lack of clinician-validated keys; and the unexplained open-model AIA failure.
9. **Five revisions:** see §12.
10. **What remains unresolved after the revisions:** clinician verification of answerability and keys; why open models fail sequence identification (perception vs serving); the small sample (n=38–46) and limited power; a single API reference model; and the post hoc status of every donor-specificity conclusion.

**Recommendation: submit only after addressing specific major concerns (M1, M2).** Both are fixable within hours, without new model runs.

---
*Literature sources consulted (snippet-level only):* [HEAL-MedVQA, arXiv 2505.00744](https://arxiv.org/abs/2505.00744v2); [IJCAI 2025 proceedings](https://www.ijcai.org/proceedings/2025/853); [Beyond Accuracy, arXiv 2603.03437](https://arxiv.org/html/2603.03437v1); [Ask4VG, arXiv 2606.01044](https://arxiv.org/pdf/2606.01044).
