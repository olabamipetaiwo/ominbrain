# IEEE ICHI adversarial peer-review report

**Manuscript:** *Measuring Image Dependence, Not Just Response Sensitivity: Controlled Ablation Tests on Brain-MRI Question Answering* (`paper/latex/ichi_latex.pdf`, 10 pages, PDF dated October 12, 2026).

**Review date:** October 15, 2026. Three separately tasked reviewer agents assessed the complete manuscript before their assessments were synthesized. These are simulated conference reviews, not official ICHI decisions. The paper was not modified.

**Location convention:** Page numbers refer to physical PDF pages. `L` references refer to `paper/latex/ichi_latex.tex`. Code paths below are relative to `release/anon_artifact/` unless otherwise stated. Findings distinguish **verified discrepancy**, **supported limitation**, and **unresolved risk**. A disclosed limitation can still limit a claim, but disclosure is not treated as misconduct.

## 1. Executive assessment

**Provisional recommendation: Borderline Reject; substantial but partly avoidable rejection risk.** The paper has a credible healthcare-informatics contribution: distinguishing image-related accuracy gains, response changes, and donor-key association. Its strongest evidence is the reference model’s sequence/localization performance and the reproducible demonstration that a large image–text accuracy gap does not identify its mechanism.

The numerical audit is reassuring. A fresh temporary copy reproduced three core analysis outputs, all 1,058 paper macros, and 11 generated tables. Independent count and exact-test calculations agree with the principal results. No model inference was rerun.

The main threat is construct validity. All 46 DSCR prompts mention new measurable lesions, whereas keys track one baseline-associated component and omit a general new-lesion criterion. This is a verified rule ambiguity, not proof that all—or any specified number of—scores are wrong. Calling these targets RANO categories and using DSCR as the central worked example magnifies its importance. The rule–expert disagreement audit cannot validate either target or establish answerability.

Other actionable concerns are undisclosed preference for expert-agreeing follow-ups during selection, headline language stronger than inconclusive tests support, and insufficient differentiation from HEAL-MedVQA’s existing counterfactual swaps. The permutation sampler is not uniform over admissible assignments; however, an independent uniform-sampling sensitivity check closely reproduced the two pivotal p-values. That concern warrants correction, not rejection of the observed result.

A few hours can substantially improve scientific defensibility through precise reframing, selection disclosure, and statistical clarification. They cannot establish clinician-verified DSCR answerability or explain weak open-model perception. Submit only after narrowing claims; do not present the current evidence as validated clinical response assessment or demonstrated absence of image use.

## 2. Manuscript understanding before evaluation

### Problem, questions, and hypotheses

The problem is that medical VQA accuracy and image perturbation effects can reflect language priors, generic response shifts, or other shortcuts. The principal question is whether controlled interventions identify **correct, task-relevant, observable image dependence**, rather than merely response sensitivity (§I; §IV).

The operational questions are: E1, whether adding the image improves correctness; E2, whether swapped-image responses move toward the donor key beyond no-image donor-key agreement; E3, whether changing stated diagnosis/timing changes management responses toward the rule-implied action; E4, how manufactured upstream context affects answers; E5, secondary probabilistic outcome prediction. AIA is an operational positive control; a ±10-point margin and a 12-test E1 Holm family were internally prespecified. The conditional donor-association analysis, reference/precision controls, explicit TCM rule, and several diagnostics are post hoc and disclosed as such.

### Contributions and findings

- **Methodological:** A combined interpretation of accuracy benefit, sensitivity, donor-key gain, and conditional donor-label association. Whole-image multi-class donor scoring and its conditional test are the plausible increment; ablation, language-prior controls, and counterfactual image pairing are established ideas.
- **Empirical/resource:** A 46-patient LUMIERE item set with phase-specific key provenance; an automated rule–expert agreement audit; model evaluations with saved responses and analysis code.
- **Strongest findings:** Reference-model AIA/LIL accuracy is 44/46 and 38/38 versus 10/46 and 14/38 without images. Scout DSCR improves from 4/46 to 25/46, the sole corrected E1 finding. Open-model corrected donor association is not detected. These are configuration- and sample-specific observations.
- **Scope:** AIA has acquisition-derived keys; LIL/DSCR have automated mask-derived keys; PJRF has uncertain outcome construction; TCM has a simplified policy target. They do not jointly establish clinical reasoning, causality, treatment quality, or deployment safety.

**ICHI audience:** Medical AI evaluation researchers, benchmark designers, and healthcare-informatics investigators studying evidence use. A methods contribution can be meaningful without deployment validation. The question is whether this particular protocol adds a reliable inferential distinction and whether its medical example validly instantiates that distinction.

## 3. Reviewer 1 — Methodology and technical soundness

### Paper Summary

The study separates image-related accuracy improvement from response sensitivity and donor-key association using paired own-image, text-only, and different-key donor conditions on selected glioblastoma follow-ups. It combines internally planned E1–E5 analyses with disclosed post hoc controls and a conditional permutation analysis. Reference-model results establish detectable sequence and localization dependence under this setup; most open-model comparisons are weak or inconclusive. Its central methodological demonstration is Scout’s large DSCR accuracy gain without statistically detected donor-specific association.

### Strengths

- Fixed-context interventions avoid conflating each phase’s effect with errors generated earlier in a chain (§IV).
- Donors have different keys, matched image counts, and available answer options; subtraction of text-only donor agreement is more informative than raw response changes.
- Paired analysis, explicit correction families, sparse-data sensitivity intervals, and donor-cluster checks show serious attention to statistical interpretation.
- The paper acknowledges that majority accuracy is not a necessary condition for image use and that reference-model success does not establish every item’s validity.

### Major Weaknesses

**R1.1 — DSCR instructions and target construction are not fully aligned.**

- **Location:** §III-B(c), p.3, Table I p.4; §V-B worked example/Fig.2 p.6; Limitations p.7, L491, L598–602, L628–630.
- **Evidence:** Every released DSCR item includes “or a new measurable enhancing lesion.” `src/lumiere_v4.py:334–336` builds this wording, while `src/lumiere_measure.py:217–224` scores measurability/change of the tracked component. The paper explicitly says a general new-lesion criterion is absent. The stem also restricts attention to the tracked lesion, creating ambiguity rather than an unqualified instruction to examine every lesion.
- **Why it matters:** An answer may follow one reasonable reading of the instructions yet disagree with the key. Therefore a DSCR error cannot be attributed cleanly to incorrect use of image evidence. The featured DSCR example is particularly exposed. Automated cache checks flag one of the nine selected CR cases, Patient-045/week-028, as having a plausible separate new lesion; visibility on the actual target slice and clinical status were not established. This is not evidence of 46 incorrect keys.
- **Severity:** **Major.**
- **Fix:** Immediate **reframing and explicit disclosure**; retain DSCR as exploratory agreement with a simplified tracked-component rule. If changing model-facing instructions or keys, **rerun affected conditions**. A targeted expert check would resolve whether the disputed criterion is observable and affects scoring.

**R1.2 — The operational gate and headline interpretation are not fully consistent.**

- **Location:** §IV E1, pp.4–5; §V-B(b), pp.5–6; Abstract p.1; Conclusion/Limitations p.7; L171, L510, L562, L621, L634.
- **Evidence:** The prespecified gate says E1 LIL/DSCR supports no conclusion for models failing AIA. Three models fail it. Scout’s AIA bootstrap interval excludes zero, but exact McNemar p=.0703. No open-model AIA/LIL interval establishes the stated equivalence margin. Nevertheless, the abstract and conclusion characterize four models as showing “limited image dependence.”
- **Why it matters:** Limited detection is not an established small effect. AIA sequence classification also is not a necessary biological or computational prerequisite for lesion localization. A gate can conservatively restrict this study’s interpretation, but cannot prove a general inability to use images. The paper partially makes these distinctions, then compresses them away in its main conclusions.
- **Severity:** **Major for interpretation**, not an arithmetic defect.
- **Fix:** **Reframing.** Separate observed low performance, failed detection, and equivalence. Explicitly label the gate operational and E2 independently descriptive/exploratory.

**R1.3 — The conditional permutation implementation does not exactly implement uniform exchangeability.**

- **Location:** §IV E2, pp.4–5, L511; §V-B(d)/Fig.2 p.6; Table VII p.10.
- **Evidence:** `tools/lumiere_v4_strat_perm.py:135–164` assigns remaining allowable keys sequentially in random block order and restarts on dead ends. This is not uniformly distributed over all admissible block-key allocations. Its Type-I procedure at lines 201–215 generates null truths using the same sampler, so calibration validates that generator, not the general stated exchangeability assumption.
- **Why it matters:** A claimed permutation p-value needs a specified null distribution and valid sampling from it. Constraints and shared donors make this more than a cosmetic implementation detail. However, independent uniform conditional sampling during this review gave Scout DSCR p≈.2975 versus .293 reported, and MedGemma AIA p≈.0399 versus .040 reported. The central inferences did not change in these checks.
- **Severity:** **Moderate after sensitivity analysis**; not a demonstrated reversal of results.
- **Fix:** **Reanalysis and clarification.** Use a verified uniform conditional sampler or define the sequential generator as the null explicitly; rerun the complete reported correction family and diagnostics before updating claims. No model inference is needed.

**R1.4 — Rule–expert agreement cannot function as an answerability test.**

- **Location:** §II(b), §III-A, p.2; Conclusion p.7; L443, L461, L621.
- **Evidence:** The audit compares a knowingly simplified rule with clinical expert ratings. Missing new-lesion handling, weaker CR semantics, target tracking, and automated measurement can cause disagreement without any inability to infer the expert rating from displayed images. §III-A correctly says this, but §II calls it a “key-recoverability audit.”
- **Why it matters:** The protocol’s target is what the image supports. Procedure disagreement establishes neither that support nor the superiority of replacement labels. This leaves DSCR target validity unresolved even when all statistics reproduce.
- **Severity:** **Major for DSCR validity; Moderate for the audit’s naming.**
- **Fix:** **Reframing** as procedure agreement; targeted adjudication only if retaining claims about clinical key recoverability.

### Minor Weaknesses

- Table III visually labels bootstrap intervals “CI above 0” even when exact tests are not significant; the text explains the discrepancy, but readers need a single clear hierarchy (§IV E1; Table III).
- The E2 formula is defined clearly, but the conditional test’s exchangeability unit, tail, draw count, and distribution should be specified together (§IV E2).
- The ±10-point equivalence margin is an operational judgment, not a clinically validated threshold; retain that distinction (§IV E1; internal plan).

### Questions for Authors

1. Does “new measurable lesion” in DSCR mean only re-emergence of the tracked component, or any visible separate lesion? Which interpretation generated the scoring key?
2. What evidence establishes DSCR item answerability beyond agreement with an unseen automated mask and a single reference model?
3. Is the donor null uniform conditional block-key exchangeability, the actual donor-assignment mechanism, or the sequential sampler’s distribution?
4. Which conclusions remain when failed AIA gates and inconclusive intervals are interpreted strictly according to the original plan?
5. Would exact/sparse-data interval reporting change any operational gate or claim of equivalence?

### Overall Recommendation

**Borderline Reject.** The core distinction is scientifically credible, but the central DSCR application has unresolved construct validity and the inferential language needs tightening. The sampler issue is repairable and does not, on the checks performed, invalidate the central empirical observation.

### Confidence

**4/5.** Complete manuscript and relevant implementation inspected; conditional-sampler and measurement-cache calculations executed. No new model inference or clinician adjudication was performed.

## 4. Reviewer 2 — Experimental evaluation and empirical evidence

### Paper Summary

The paper evaluates image dependence using paired own-image/text-only comparisons, donor-image swaps, answer-prior references, and positive controls on 46 selected LUMIERE patients. AIA/LIL provide the strongest image-grounded tasks, DSCR supplies the principal harder worked example, and TCM/PJRF are extensions. The contribution is an evaluation design and empirical caution about interpreting ablation gains, rather than a clinically validated diagnostic benchmark.

### Strengths

- Pairing, controlled upstream context, explicit priors, and multiplicity correction make the main comparisons interpretable.
- Reference-model AIA/LIL results provide meaningful feasibility evidence.
- The archive supports inspection of prompts, outcomes, selection, and result provenance. Independent recounting reproduced the principal accuracies, donor-gain numerators, and exact E1 tests.
- Precision controls address one plausible explanation for low open-model scores without claiming to isolate quantization causally.
- The authors disclose selection limitations, automated keys, post hoc changes, uncertain survival labels, and weak precision for null findings.

### Major Weaknesses

**R2.1 — The most important DSCR comparison has an unresolved instructions–key discrepancy.**

- **Location:** §III-B(c), p.3; Table I p.4; Fig.2/§V-B p.6; Limitations p.7, L491, L598–602, L630.
- **Evidence:** Released questions allow progression for a new measurable lesion; the key algorithm follows the baseline-associated component rather than implementing a general new-lesion search.
- **Why it matters:** Scoring and prompting may reward different behavior. Consequently, a weak donor-tracking result cannot distinguish poor perception from disagreement with the proxy scoring procedure. The number of genuinely affected displayed items is unknown; the existence of the wording does not prove observed answers were mis-scored.
- **Severity:** **Major.**
- **Fix:** **Reframe** DSCR as exploratory surrogate agreement immediately. An item audit should determine whether visible separate lesions change the prompted answer. **New inference is required only if prompts or keys are changed and those comparisons are retained as corrected experiments.**

**R2.2 — Most negative findings do not exclude scientifically meaningful effects.**

- **Location:** Abstract; contribution 3; §V-B(b,d), Tables III/V; Conclusion and “Power and scope,” L171, L191, L562, L566, L621, L634.
- **Evidence:** Scout DSCR donor gain is +28.6 points, bootstrap CI [+7.1,+50.0], yet conditional association is nonsignificant. Most image-effect intervals are wide; no open-model AIA/LIL interval establishes ±10-point equivalence. Scout’s operational gate passes despite exact p=.0703.
- **Why it matters:** Corrected nondetection does not establish absence or a small upper bound. Gain and conditional association test different questions, so their apparent disagreement is not a numerical contradiction; it is precisely why the conclusion needs to identify the estimand.
- **Severity:** **Major for broad capability claims; Moderate for the narrow demonstration.**
- **Fix:** **Reframing**, with intervals preserved. A prospective powered experiment would be essential only if the authors insist on excluding a specified meaningful tracking effect; it is not required for reporting inconclusive evidence.

**R2.3 — The reported donor-test calibration establishes a narrower result than the prose suggests.**

- **Location:** §IV E2, pp.4–5; Table VII p.10; `tools/lumiere_v4_strat_perm.py`, `_assign_stratum` and `type_I`.
- **Evidence:** Sequential constrained draws are not automatically uniform conditional permutations, and null simulation uses that same generator. Fifty synthetic simulations per predictor do not establish general calibration across realistic failure mechanisms. The paper acknowledges that the analysis is not an assignment-randomization test.
- **Why it matters:** Calibration under the chosen synthetic null demonstrates self-consistency under that null, not validity under the actual donor experiment. A protocol paper must make this boundary explicit.
- **Severity:** **Major for an unrestricted calibration claim; Moderate for the observed numerical conclusion after the independent sensitivity check reported in §7.**
- **Fix:** **Clarification/reanalysis**, specifying the null and using a verified conditional sampler. No model inference needed. The independently obtained uniform p-values substantially reduce concern about a false headline result, but do not establish calibration for the original image-assignment mechanism.

**R2.4 — Cohort selection omits an important preference from the manuscript.**

- **Location:** §III-B(a), “Cohort,” p.3, L487; `src/lumiere_v4.py:214`.
- **Evidence:** The code ranks eligible candidates by `(not concordant, not lil_ok, rng.random())`: expert–rule agreement first, LIL eligibility second, seeded tie-breaking last. The paper reports strata, quotas, and seed but not this ranking. Selected agreement is 26/46 (56.5%), versus 75/197 (38.1%) across determinate audit follow-ups.
- **Why it matters:** The effective sampling procedure is incompletely described and enriches the benchmark for agreement/eligibility. The full audit’s disagreement rate cannot characterize selected item quality. These two rates also have different sampling units and should not be compared as an unbiased before/after effect.
- **Severity:** **Moderate.**
- **Fix:** **Clarification**, reporting the ranking and selected-cohort composition. No evidence of selection on model output was found; this is not an allegation of result cherry-picking.

### Minor Weaknesses

- **Run provenance:** `tools/lumiere_v4_stats.py:56` sorts complete folder names, not timestamps, contrary to `run_manifest.json`. Pixtral’s earlier `smoke` folder overrides 18 records from a later full run. Chronological merging changes one answer, Patient-003/AIA/own, C versus D; both are incorrect, so headline accuracies/gains remain unchanged. This is a verified provenance defect, not a demonstrated performance error.
- **Synthetic test precision:** Table VII should call percentages observed detection frequencies over 50 simulations, report uncertainty, and define rho as the probability of tracking rather than guessing. With four classes and uniform guessing otherwise, rho=.4 implies expected donor accuracy .55, not .4.
- **Serving reproducibility:** §IV should point to exact weight revisions/digests, tokenizer/preprocessor revisions, and serving versions. Mutable tags alone do not identify immutable experiments. Missing details are a reproducibility limitation, not proof of a broken pipeline.
- **Budgets:** The API model’s larger hidden-reasoning cap is acceptable for a feasibility control. It is not a matched computational-budget comparison of model quality; the paper generally respects this distinction.

### Questions for Authors

1. How many selected DSCR images contain a visible separate lesion that would change the prompted category but not the tracked-component key?
2. Which distribution over valid donor labels is intended, and why is its exchangeability assumption appropriate here?
3. What magnitude of donor tracking remains compatible with the data, rather than merely failing significance?
4. How frequently did concordance/LIL ranking determine the selected follow-up, and can this be disclosed with selected-cohort agreement?
5. Can the immutable model/serving identifiers and smoke-versus-full-run inclusion rules be pinned unambiguously?

### Overall Recommendation

**Borderline Reject.** Principal counts are supported, but the DSCR ambiguity and interpretation of nondetection weaken the empirical case. Selection and sampler reporting can be repaired without new model runs; clinical target validity remains unresolved.

### Confidence

**4/5.** Full manuscript read and selection, scoring, prompts, permutation, and provenance inspected; main binary counts and exact tests independently recalculated. No model inference or clinical adjudication was performed.

## 5. Reviewer 3 — Novelty, clinical significance, and scientific communication

### Paper Summary

The paper combines image ablation, donor-key scoring, no-image subtraction, and conditional association testing to distinguish accuracy gains from task-relevant image dependence. It instantiates these controls on MRI-derived questions and reports strong reference-model sequence/localization performance alongside weak or inconclusive open-model results. Its resource and empirical contributions are the LUMIERE question set, rule–expert agreement audit, and reproducible model observations. Its methodological novelty lies in the combined diagnostic interpretation, not the general idea of ablation or counterfactual visual questions.

### Strengths

- The question is relevant to healthcare-informatics evaluation, independently of clinical deployment readiness.
- The three-way distinction between accuracy, sensitivity, and donor association is useful and illustrated with synthetic controls.
- Key provenance, post hoc changes, and clinical limitations are unusually explicit.
- The reference model provides positive evidence that the protocol can detect task-relevant image dependence on AIA/LIL.

### Major Weaknesses

**R3.1 — Clinical task names exceed the validated operational constructs.**

- **Location:** Fig.1(b) p.3; Table I p.4; §III-B(c); Fig.2 p.6; Limitations pp.7, L433, L478, L491, L628–630.
- **Evidence:** “RANO category” denotes a simplified single-component rule whose CR class includes residual sub-measurable enhancement, omits general new-lesion progression, and lacks full clinical criteria. Automated masks and displayed-key recoverability are unvalidated. Full RANO has additional response requirements, as the original criteria document confirms. [Wen et al., 2010](https://imaging.cancer.gov/clinical_trials/docs/RANO%20Criteria%20-%20JCO-2010-Wen-1963-72.pdf)
- **Why it matters:** The central example cannot cleanly establish clinically meaningful response assessment or its failure. Failure to reproduce the authors’ operational proxy is a different outcome. This does not make the methods question irrelevant to ICHI.
- **Severity:** **Major.**
- **Fix:** **Reframing** to “simplified enhancement-rule category” throughout; targeted adjudication only if stronger answerability/clinical claims are retained.

**R3.2 — The closest prior protocol is insufficiently differentiated.**

- **Location:** §I paragraph 2/contribution 1 and §II(b), pp.1–2, L185, L189, L443.
- **Evidence:** HEAL-MedVQA already replaces a pathological region with a corresponding region from a different-class image and evaluates the expected answer transition (§3.1/Fig.2). Complementary-image VQA already uses different images requiring different answers to the same question. [HEAL-MedVQA](https://www.ijcai.org/proceedings/2025/0853.pdf), [Goyal et al.](https://arxiv.org/abs/1612.00837)
- **Why it matters:** Describing prior work mainly as reporting accuracy change understates its targeted counterfactual design. A protocol contribution needs to identify precisely what inferential capability is added: whole-image multi-class donor scoring, no-image subtraction, and conditional donor association are plausible distinctions. The current evidence does not establish empirical superiority to HEAL-MedVQA.
- **Severity:** **Major for contribution positioning**, not proof that the paper lacks novelty.
- **Fix:** **Clarification/reframing.** Compare intervention unit, answer target, baseline subtraction, and inferential assumptions. No additional benchmark experiment is necessary unless claiming superior performance over that protocol. Novelty assessment remains provisional rather than exhaustive.

**R3.3 — The motivating agreement audit is inconsistently described as recoverability validation.**

- **Location:** §II(b), §III-A, p.2; Conclusion p.7, L443, L461, L621.
- **Evidence:** The body correctly says disagreement neither adjudicates labels nor measures unanswerability, but “key-recoverability audit” and the conclusion’s opening invite that interpretation.
- **Why it matters:** A knowingly different automated procedure can disagree with an accurate, recoverable expert label. The 38% statistic supports a disagreement claim, not a reason to regard replacement keys as validated or expert labels as defective.
- **Severity:** **Moderate to Major**, because this is a claimed contribution and motivates the targets.
- **Fix:** **Reframing** as a rule–expert agreement audit; explain mechanically traceable targets as a design choice, not a consequence of demonstrated expert-label failure.

**R3.4 — The headline characterization is stronger than the uncertainty permits.**

- **Location:** Abstract, contribution 3, §V-B(b), Conclusion, and Limitations, L171, L191, L562, L621, L634.
- **Evidence:** “Limited image dependence” is paired with failed gates and intervals explicitly described as inconclusive. The manuscript itself acknowledges that below-majority accuracy does not establish non-use.
- **Why it matters:** A paper advocating careful evaluation should distinguish low accuracy, lack of detection, and evidence of small effects consistently, especially in the abstract.
- **Severity:** **Major for the broad claim.**
- **Fix:** **Textual reframing** to limited evidence under the evaluated settings, with explicit acknowledgment that meaningful effects are not excluded.

### Minor Weaknesses

- §III-B’s “stated management rule” can imply that the main TCM prompt contains the rule, although §III-B(e) correctly says only the post hoc condition does. Main-condition agreement and explicit-rule adherence should be named separately.
- Inherited labels such as “diagnostic synthesis and causal reasoning” and “therapeutic cycle management” should not imply validated tests of those full constructs (§I; Fig.1).
- Fig.2 should explicitly state that below-majority accuracy does not rule out image use, matching Table VI’s caption.
- The conclusion’s source-benchmark chain discussion distracts from the controlled evaluation; the paper rightly says this is incompatibility with its design, not a violated promise by the original benchmark (§III).

### Questions for Authors

1. Which DSCR disagreements arise from measurement ambiguity versus different operational meanings of CR or new-lesion progression?
2. What does the conditional association analysis establish beyond expected counterfactual answer transitions in HEAL-MedVQA, under comparable assumptions?
3. How are clinically sensible answers handled when full RANO and the stipulated proxy disagree?
4. Does “limited dependence” mean small bounded effects, low accuracy, or insufficient evidence—and which tests support that meaning?
5. How do TCM results distinguish failure to infer an unstated policy from failure to follow a supplied one?

### Overall Recommendation

**Borderline Reject.** A meaningful evaluation-methods contribution remains plausible, but the clinical proxy, novelty positioning, and headline interpretation weaken the submitted case. Clinical deployment validation is not an acceptance requirement; faithful operationalization of the claimed task is.

### Confidence

**4/5.** Complete manuscript and relevant primary literature inspected. This reviewer did not execute the numerical reproduction or clinically adjudicate images; the literature search was targeted, not exhaustive. Additional verified medical-VQA context supports the problem motivation: [Yan et al., ProbMed](https://aclanthology.org/2025.findings-acl.981/).

## 6. Claim–evidence audit

“Fully supported” means supported within the stated finite sample and evaluated configurations, not universal validity.

| Major claim | Manuscript location | Supporting evidence | What it actually demonstrates | Status | Plausible alternative or boundary |
|---|---|---|---|---|---|
| Accuracy change alone does not identify correct image reading | Abstract; §I; §IV; Fig.2 | E1 versus E2; Table VII | Raw gain can coincide with generic image-presence shifts; observed gain does not identify mechanism | Fully supported as a caution | Does not prove a particular real model uses a generic shift |
| Reference model reads sequence and lesion location | Abstract; §V-B(a), p.5 | Table IV: 44/46, 38/38 own; 44/46, 38/38 donor | Strong task-relevant dependence on these inputs/keys | Fully supported operationally | Not item-level clinical validation or evidence about internal mechanisms |
| Four open models show limited image dependence | Abstract; contribution 3; Conclusion | Tables III/V; gate and Holm tests | Low accuracy and limited detected effects in these runs; many effects inconclusive | Partially supported | Low power, input/serving limitations, model capability, and proxy-key ambiguity remain |
| Only one E1 test survives correction | Abstract; §V-B(b); Table III | Twelve exact McNemar tests plus Holm | Scout DSCR adjusted p=.0005908; other eleven fail | Fully supported | Does not make the other effects zero |
| Scout DSCR accuracy improves by 45.7 points | Fig.2; Table III | 25/46 versus 4/46 | Large paired correctness gain against the same proxy keys | Fully supported numerically | Poor no-image performance and generic shifts can contribute; key ambiguity limits clinical meaning |
| Below-majority Scout accuracy leaves category reading unestablished | §V-B(b); Fig.2; Table VI | 25/46 versus 27/46 majority; class-wise confusion | No aggregate gain over the sample majority constant; six nonmajority items correct | Partially supported as one contextual observation | It neither proves nor disproves image reading; model is not a constant predictor |
| No corrected donor-specific tracking is detected | Abstract; §V-B(d); Conclusion | Conditional p-values and twelve-cell Holm family | No rejection under the implemented conditional reference distribution | Supported with qualification | Nondetection is not equivalence; uniform sensitivity checked only two cells |
| Conditional test separates sensitivity from tracking | §II(b), §IV E2; Table VII | Generic shift and noisy tracker share median +19 pp; detection 0/50 versus 39/50 | Discrimination among specified synthetic generators | Partially supported | Other shortcuts/nulls, finite simulation uncertainty, and exchangeability assumptions remain |
| Permutation holds nominal 5% false positives | §IV E2, p.5 | Synthetic null calibration in artifact | Calibration under the chosen generator, not original donor assignment | Partially supported | Nonuniform sequential draws and same-generator calibration narrow validity |
| Enhancement rule agrees with expert rating in 38% | Abstract; §III-A; Conclusion | 75/197; 44/241 abstentions; patient resampling | Agreement of two non-equivalent procedures on determinate follow-ups | Fully supported numerically | Does not locate errors or estimate displayed-image answerability |
| Audit is a “key-recoverability audit” | §II(b), L443 | Rule–expert comparison | No direct observer recoverability test | Unsupported as named | Either rule/measurement error or omitted clinical criteria could cause disagreement |
| DSCR is a RANO category recovered from supplied slices | Fig.1; Table I; §III-B(c) | Automated component measurements and simplified rule | A mechanically defined proxy, without item validation and with new-lesion ambiguity | Partially supported | Image ambiguity or instruction–target mismatch, not necessarily perception failure |
| Selection is stratified with quotas and fixed seed | §III-B(a), p.3 | `select_cohort`, selection report | Also prefers expert agreement and LIL eligibility | Partially supported description | Unreported enrichment affects target sample, not evidence of model-output selection |
| No model exceeds category-only TCM lookup | Abstract; §V-B(f); Conclusion | Lookup 39/46=84.8%; explicit-rule best 38/46=82.6% | Descriptive point estimates do not exceed the oracle sample lookup | Fully supported descriptively | Does not establish statistical inferiority or absence of timing use |
| Models incompletely follow supplied rule | §V-B(f), pp.6–7 | Explicit-rule accuracy below 100%; rule states deterministic target | Errors remain in the explicit-rule condition | Supported for the stipulated rule | Main unstated-rule condition measures a different construct; not clinical treatment quality |
| 4-bit serving is unlikely the sole explanation | Abstract; §V-B(c); Limitations | Gemma27 bf16 and Pixtral bf16 remain near chance on AIA | Weak AIA also occurs in two bf16/vLLM configurations | Partially supported | No causal isolation of quantization, stack, preprocessing, family, or scale |
| Every image reaches the model | §V-B(b), p.6, L562 | Prompt-token increments and probes | Supplied images register in input handling | Partially supported | Usable contrast/encoder-equivalent representations not verified |
| PJRF establishes meaningful mortality prediction | Not claimed; §III-B(d)/Limitations | Secondary Brier evaluation; unknown censoring/origin | Provisional scoring of uncertain labels | Unsupported if inferred, appropriately disclaimed | Outcome construction and sample base rate prevent clinical interpretation |
| Reproducibility artifact regenerates paper statistics | Ethics p.8; artifact README | Reproduction script, raw responses, expected outputs | Core analyses/macros/tables match; some diagnostics/alternative runs loaded as summaries | Supported with scope qualification | Reproducing saved outputs is not rerunning inference or independent clinical validation |

### Cross-section inconsistencies requiring correction

1. **Rule scope:** model-facing new-lesion clause versus the omitted general criterion acknowledged in Limitations (§III-B/Table I versus L630 and actual prompts).
2. **Audit construct:** “key-recoverability audit” (§II) versus explicit denial that recoverability is measured (§III-A).
3. **Inference strength:** “limited image dependence” (Abstract/Conclusion) versus failed gates and inconclusive intervals (§IV/Limitations).
4. **TCM construct:** generic “stated rule” description versus rule absent in primary prompts and present only in the explicit-rule condition (§III-B and §V-B).
5. **Input validity:** “every image reaches the model” (§V-B) versus partial pipeline verification (Limitations).
6. **Selection:** manuscript’s strata/seed description omits code’s concordance/eligibility ranking. This is an implementation-description omission, not a contradiction between reported percentages.

## 7. Reproducibility and numerical audit

### What was actually inspected and executed

The full 10-page PDF was text-extracted and every page rendered and visually inspected, including both figures, all seven tables, equations, captions, appendix, and references. The LaTeX source, generated tables/macros, internal plan and amendments, local artifact README/manifest, selection report, released items, saved responses, and relevant selection, measurement, prompt, parsing, scoring, and statistical code were inspected. No manuscript portion was inaccessible.

The original manuscript and supporting files were not changed. The artifact was copied to `/private/tmp/ichi-review-oct15-artifact`; its `reproduce.sh` was executed there using an existing Python environment with Python 3.12.13, NumPy 2.3.5, SciPy 1.18.1, and pandas 3.0.5. It exited successfully. The log is `/private/tmp/ichi-review-oct15-reproduce.log`.

| Executed check | Result | What it does not establish |
|---|---|---|
| Core statistics, supplement, and baseline regeneration | All three JSON outputs identical to shipped expected outputs | Correctness of every scientific assumption |
| Paper macro regeneration | 1,058 v4 macros, zero differences | Independent regeneration of every precomputed input |
| Generated table comparison | All 11 artifact tables identical | All 11 appear in the PDF; only a subset is included there |
| Comparison with current paper source outputs | All 1,058 v4 macros and 11 source tables match regenerated outputs | Recompilation of the PDF was not performed |
| Independent raw-response recount and exact tests | Main accuracy, donor numerators, and E1 exact tests agree | Clinical label validity |
| Independent uniform conditional donor sampling | Two pivotal p-values essentially unchanged | Complete corrected 12-test family not rerun with this sampler |
| Chronological versus lexical result loading | One Pixtral answer changes; headline accuracies/gains do not | No comprehensive immutable model-version audit |

**Not performed:** GPU/API model inference; training; re-extraction of all MRI measurements from original volumes; clinician assessment of all keys; exhaustive source-literature verification; reconstruction of every alternative-donor run. Alternative-assignment robustness summaries and some synthetic/calibration diagnostics are inputs to the reproduction script, not all independently regenerated by that script. The new-lesion cache audit and two conditional-sampler checks were executed separately. The remotely hosted anonymous repository was not compared byte-for-byte with the local artifact.

### Independent E1 recount

Counts are own-image versus text-only correctness. Discordants are own-only/text-only correct; p is two-sided exact McNemar. These match Table III to reported precision.

| Model | Phase | Own | Text | Discordants | Exact p |
|---|---|---:|---:|---:|---:|
| MedGemma-4B | AIA | 16/46 | 12/46 | 6/2 | .2890625 |
| MedGemma-4B | LIL | 9/38 | 7/38 | 3/1 | .625 |
| MedGemma-4B | DSCR | 9/46 | 5/46 | 4/0 | .125 |
| Gemma-3-12B | AIA | 12/46 | 12/46 | 4/4 | 1 |
| Gemma-3-12B | LIL | 12/38 | 9/38 | 7/4 | .5488281 |
| Gemma-3-12B | DSCR | 27/46 | 22/46 | 5/0 | .0625 |
| Gemma-3-27B | AIA | 15/46 | 12/46 | 4/1 | .375 |
| Gemma-3-27B | LIL | 9/38 | 7/38 | 3/1 | .625 |
| Gemma-3-27B | DSCR | 27/46 | 27/46 | 0/0 | 1 |
| Llama-4-Scout | AIA | 17/46 | 11/46 | 7/1 | .0703125 |
| Llama-4-Scout | LIL | 15/38 | 13/38 | 6/4 | .7539063 |
| Llama-4-Scout | DSCR | 25/46 | 4/46 | 24/3 | .0000492334 |

Holm gives Scout DSCR **.0005908012**; it is the only surviving E1 test. The next adjusted values are .6875 and .703125. Reference-model counts are AIA 44/46 versus 10/46, LIL 38/38 versus 14/38, and DSCR 33/46 versus 27/46. Reference DSCR exact p=.109375; its bootstrap interval touching zero should not be read as strong evidence of improvement.

### Independent E2 recount

Entries are swapped-answer donor matches / text-only donor matches, with the common denominator in the column heading. Subtracting the numerators reproduces Table V gains.

| Model | AIA, n=46 | LIL, n=38 | DSCR, n=42 |
|---|---:|---:|---:|
| MedGemma-4B | 15 / 10 | 8 / 11 | 12 / 10 |
| Gemma-3-12B | 8 / 8 | 9 / 7 | 15 / 13 |
| Gemma-3-27B | 16 / 14 | 10 / 8 | 15 / 14 |
| Llama-4-Scout | 14 / 13 | 12 / 9 | 21 / 9 |
| Reference | 44 / 13 | 38 / 5 | 21 / 14 |

Scout’s DSCR gain is 12/42=28.5714 points. DSCR own accuracy in Table III uses 46 items; Table V uses the 42 donor-paired items. Their 54.3% versus 54.8% values are **not an error**. Table III’s answer-change denominator is also the three-arm intersection and is explicitly disclosed.

### Additional arithmetic, sample, and procedure checks

- Phase counts: AIA 46, LIL 38, DSCR 46, PJRF 45, TCM 46. Donor pairs: 46, 38, and 42.
- Audit: 75/197=38.0711%; 197/241=81.7427% coverage; 75/241=31.1203% if abstentions count as failures. The manuscript correctly separates these estimands. The 59-patient resampling interval addresses repeated follow-ups better than treating all 197 as independent.
- Selected cohort: 26/46=56.5217% expert–rule agreement; DSCR class counts 27 PD, 9 CR, 6 SD, 4 PR. These are enriched, non-population proportions.
- DSCR majority: 27/46=58.6957%. Scout confusion diagonal is 19+4+2=25; nonmajority correctness is 6/19. Table VI is internally consistent.
- TCM classes: 19 continue, 7 confirm, 20 escalate. Best category-only lookup is (19+20)/46=84.7826%; confirm-first lookup is (19+7)/46=56.5217%. These are sample oracle references, not held-out trained baselines.
- PJRF outcomes: 28/45=62.2222%. Its unknown time-origin/censoring problem is acknowledged and prevents substantive clinical forecasting claims. The logistic baseline uses leave-one-out fitting with scaling fit inside each training fold; no obvious scaling leakage was found in the inspected implementation.
- There is no study-specific model training or checkpoint-selection experiment to audit. The evaluation uses pretrained systems; the key selection risks are sample construction, mutable model identifiers, run overrides, and post hoc analysis—not a missing train/test split for fine-tuning.
- Selection uses no observed model answer in the inspected code. It does use expert-label agreement and LIL eligibility as priorities, which must be disclosed.
- Primary E1/E2 invalid JSON responses had recoverable answer letters. Parsing failure alone does not explain the four main models’ low accuracy. The regex salvage path extracts the explicitly named answer field, rather than arbitrarily picking an option mentioned in reasoning.
- TCM’s “not at all” timing response for Gemma27 (§V-B(f)) refers to the informative PD subset: 0/20 eligible transitions, with seven already at the new target. Across all items there are four movements to the target. This needs denominator clarification, not an accusation that the PD result is false.

### Conditional-permutation check: verified defect, bounded consequence

The sampler is generally nonuniform. Exact enumeration of a four-distinct-key example with forbidden recipient labels `(0,0,1,2)` produces eight valid allocations. Four have probability 21/170 and four 43/340 under the sequential/restart procedure, rather than 1/8 each.

A separate dynamic-programming calculation counted valid completions in a fixed block order, then sampled each next label proportional to its number of completions. This yields uniform sampling over admissible multiset allocations under the paper’s stated conditional constraints. With 20,000 draws and seed 83245:

| Cell | Reported p | Independent uniform p | Approximate Monte Carlo SE |
|---|---:|---:|---:|
| Scout DSCR | .293 | .297485 | .003232 |
| MedGemma AIA | .040 | .039898 | .001383 |

Scout’s two DSCR strata had 17 blocks/74,170 admissible allocations and 12 blocks/30 allocations. These checks show no material reversal in the two pivotal raw tests. They do not validate every other cell, every synthetic diagnostic, or a design-based interpretation. Do not advertise “the permutation result is wrong”; correct the implementation/description and preserve the distinction between conditional association and causal assignment inference.

### Verified discrepancies versus unresolved risks

**Verified:** new-lesion wording and restricted key rule; omitted within-stratum selection ranking; nonuniform sampler; lexical rather than timestamp override rule; inconsistent terminology for audit/negative findings.

**Unresolved:** number of genuinely mis-scored displayed DSCR items; actual MRI contrast preservation through each encoder; original model weight identities if unpinned; extent of pretraining exposure; clinical correctness of all labels. None is established merely by low scores. No evidence of fabricated results, model-output-based cherry-picking, or a numerical failure of the principal tables was found.

## 8. Senior Program Committee metareview

### Consensus and adjudication

All three reviewers identify the DSCR construct/answerability problem and the distinction between limited evidence and demonstrated limited dependence. Reviewers 1 and 2 independently identify the conditional-sampler issue; Reviewer 2 identifies selection/provenance omissions; Reviewer 3 establishes that closest prior work already contains medically targeted donor replacement.

The strongest criticisms are supported by inspectable evidence: actual prompt text versus key code, actual selection ranking, wide reported intervals, and the source protocol. They are not demands for arbitrarily larger benchmarks. The sampler criticism is valid but its severity falls after the independent uniform check. It should not be counted as a separate fatal numerical error. Similarly, the loader discrepancy does not change the audited headline performance.

No reviewer has established that a particular model’s low accuracy is caused by preprocessing failure, that all DSCR labels are wrong, or that the authors selected favorable model outputs. Such assertions would be speculative. Requiring a second reference model, a new hospital cohort, or prospective clinical deployment as automatic acceptance conditions would exceed the paper’s defensible methods scope. A second reference could reduce dependence on one API system, but it would not itself validate clinical keys.

### What remains credible

The methodological caution remains sound: a large ablation gain need not establish donor-specific reading. Reference-model AIA/LIL results are persuasive within the experimental setup. The raw Scout DSCR improvement and lack of corrected conditional association are reproducible observations, even though their clinical interpretation is constrained. The artifact is a substantial strength.

### Sufficiency for acceptance

As submitted, the evidence is **borderline insufficient** for a strong claim that this protocol establishes correct clinical image dependence across the proposed chain. The flagship DSCR example uses an unvalidated proxy with an instruction ambiguity, while most negative results do not exclude meaningful dependence. The incremental methodological contribution needs a sharper comparison with prior counterfactual VQA.

These problems are fatal to stronger claims of validated RANO reasoning, demonstrated absence of image use, superiority over prior evaluation protocols, or clinical management quality. The paper mostly avoids those claims already; the remaining ambiguity is why the recommendation is **Borderline Reject**, not Strong Reject. The narrower contribution—an auditable evaluation framework plus bounded MRI observations—remains credible.

### Time feasibility and provisional decision

Within hours, the authors can fix headline inference, disclose selection, separate surrogate tasks from clinical constructs, clarify prior work, and correct/document the conditional sampler. They cannot honestly manufacture clinical validation by adding limitations or changing the description of prompts already used. Correcting historical prompts requires affected reruns; otherwise the DSCR evidence must remain explicitly exploratory.

**Provisional SPC recommendation: Borderline Reject as submitted.** This is based on target validity and the evidentiary scope of the contribution, not an average of three scores. Careful immediate corrections could move the paper toward a defensible borderline submission; they do not guarantee acceptance or eliminate the unresolved target-validity concern.

## 9. Ranked P0/P1/P2 rescue plan

Ranking reflects expected rejection-risk reduction relative to effort. Time estimates are planning estimates, not guarantees. P0 means address before submission by correction **or explicit narrowing**; it does not mean all existing experiments must be discarded.

### Rank 1 — P0: Align headline claims with inconclusive evidence (15–25 minutes)

**Location:** Abstract paragraph 2 L171; contribution 3 L191; §V-B(b) L562; Conclusion L621; Fig.2 caption L598.

**Problem/rejection rationale:** “Limited image dependence” can be interpreted as an established small capability/effect, whereas failed gates and wide intervals establish limited evidence. The methodological paper risks making the inference error it criticizes.

**Smallest defensible correction:** Consistently report detection and uncertainty. Keep low observed accuracy and absence of corrected association as separate facts. Do not delete non-significant results.

**New experiments:** No.

**Replacement:**

> Under the evaluated prompts and serving configurations, the four open-weight models provided limited and inconsistent evidence of correct image dependence. Only one E1 contrast survived correction, and no conditional donor-association test survived correction. Most image-effect estimates remained inconclusive, so these results do not establish absence of image use or exclude meaningful effects.

**Fig.2 addition:**

> Below-majority accuracy does not rule out item-level image reading; the donor-association result is a separate, conditional diagnostic.

### Rank 2 — P0: Disclose DSCR instructions–key ambiguity and narrow the central example (25–45 minutes for honest reframing)

**Location:** §III-B(c) L491; Table I DSCR row L478; Fig.1/2; §V-B worked example L602; Limitations L630. Underlying prompts: `src/lumiere_v4.py:334–336`; key: `src/lumiere_measure.py:217–224`.

**Problem/rejection rationale:** Prompted new-lesion behavior and tracked-component scoring may differ. The central example cannot establish failure to interpret a valid clinical target without resolving this ambiguity.

**Smallest defensible correction:** Use “simplified tracked-lesion enhancement category”; disclose historical wording; make DSCR exploratory; retain AIA/LIL as the strongest demonstrations. Do not silently edit saved prompts or imply new results.

**New experiments:** No for narrowing/disclosure. Yes, affected model conditions must be rerun if their prompts/keys are corrected. Targeted image/clinician adjudication could determine which items are affected before deciding rerun scope.

**Replacement:**

> DSCR is an exploratory agreement task against an automated single-component enhancement rule, not validated clinical RANO response assessment. The prompts used in these runs mention a new measurable enhancing lesion, whereas scoring follows the baseline-associated component and does not implement a general new-lesion search. We have not established how many displayed items are affected. DSCR therefore illustrates uncertainty in interpreting an ablation gain, rather than validated failure to read clinical response from the slices.

**If correcting model-facing wording later:** specify that only the tracked component is scored, including its transition from nonmeasurable to measurable enhancement, and omit the ambiguous general new-lesion clause. Version and rerun the resulting task rather than relabeling old outputs.

### Rank 3 — P1: Report actual follow-up selection (10–15 minutes)

**Location:** §III-B(a), p.3, L487; `src/lumiere_v4.py:214`; selection report.

**Problem/rejection rationale:** A fixed seed does not describe the preferential selection policy; omission undermines reproducibility and could make the audit agreement appear representative of the benchmark.

**Smallest defensible correction:** Disclose ranking and selected agreement; distinguish the follow-up audit population from one-item-per-patient evaluation.

**New experiments:** No.

**Replacement:**

> Within each selection stratum, eligible follow-ups were ranked to prefer agreement between the automated category and expert rating, then LIL eligibility, with seeded random tie-breaking. The selected 46-patient set contains 26 expert–rule agreements (56.5%); the 38.1% audit agreement refers to all 197 determinate follow-ups. This enrichment limits population-level interpretation and was not based on model responses.

### Rank 4 — P1: Correct the audit construct and clinical naming (10–20 minutes)

**Location:** §II(b) L443; §III-A heading/body L458–461; Conclusion L621; Table I/Fig.1 DSCR labels.

**Problem/rejection rationale:** Rule disagreement does not demonstrate recoverability or validate replacing expert labels. Calling a deliberately weaker proxy “RANO” without immediate qualification creates an avoidable construct-validity objection.

**Smallest defensible correction:** Rename “key-recoverability audit” as “rule–expert agreement audit”; put operational CR and new-lesion limitations in Methods, not only Limitations.

**New experiments:** No for the narrower statement.

**Replacement:**

> This rule–expert agreement audit compares different labeling procedures. It neither validates the automated keys nor determines whether expert ratings are recoverable from the displayed slices. We use mechanically traceable proxy keys as an experimental design choice, not because the audit establishes that expert ratings are wrong. The DSCR complete-response proxy includes enhancement below the measurability threshold and is not full clinical RANO complete response.

### Rank 5 — P1: State the increment over closest prior work (15–25 minutes)

**Location:** §I paragraph 2/contribution 1 L185/L189; §II(b) L443.

**Problem/rejection rationale:** The contribution can appear to reinvent counterfactual medical VQA if HEAL-MedVQA is characterized only as accuracy perturbation.

**Smallest defensible correction:** Contrast intervention unit and inference explicitly; claim no empirical superiority.

**New experiments:** No, unless retaining a superiority claim not currently established.

**Replacement:**

> HEAL-MedVQA already evaluates expected answer changes after replacing a pathological region with a corresponding region from a different-class image. Our increment is whole-image, multi-class donor-key scoring with subtraction of no-image donor agreement and a conditional donor-label association analysis, instantiated on brain MRI. We compare these designs conceptually rather than empirically.

### Rank 6 — P1: Correct/qualify the conditional reference distribution (45–90 minutes, bounded CPU reanalysis)

**Location:** §IV E2 L511; §V-B(d) L566; Fig.2/Table VII; `tools/lumiere_v4_strat_perm.py:135–215`.

**Problem/rejection rationale:** Uniform exchangeability and sequential constrained sampling are different distributions. Calibration under the latter cannot validate the former or the actual image assignment. The two-cell check lowers numerical risk but does not complete the correction family.

**Smallest defensible correction:** Replace the sampler with verified uniform conditional sampling; regenerate all 12 tests, adjusted p-values, and relevant diagnostics. If that cannot be completed, explicitly identify the heuristic reference distribution and narrow all inferential claims. Preserve the original result provenance.

**New experiments:** No model inference; CPU reanalysis required for corrected p-values. Do not substitute this report’s two p-values into the paper without regenerating the family.

**Interim replacement if retaining existing results:**

> This post hoc diagnostic compares the observed gain with a sequentially generated, constraint-valid donor-label reference distribution. Its calibration applies to the synthetic nulls evaluated here; it is not a uniform conditional permutation test or a randomization test for the original image-assignment mechanism.

**After verified correction, replace with an accurate implementation-specific description** stating uniform constrained donor-block sampling, image-count strata, forbidden own keys, one-sided tail, draws, seeds, and the correction family. Report the actual regenerated numbers.

### Rank 7 — P1: Distinguish TCM agreement, adherence, and transition denominators (15–20 minutes)

**Location:** §III-B opening/TCM L466/L495; §IV E3 L512; §V-B(f) L604.

**Problem/rejection rationale:** Failure to match an unstated simplified policy is not a demonstrated failure to follow that policy. “Not at all” can also be misunderstood without the PD/informative denominator.

**Smallest defensible correction:** Name the two conditions accurately; add relevant counts. Treat the 84.8% lookup as a sample reference, not evidence of statistical inferiority or absence of fact use.

**New experiments:** No.

**Replacement:**

> The main TCM condition measures agreement with a simplified policy not supplied in its prompt; only the post hoc explicit-rule condition tests adherence to the supplied policy. The best explicit-rule point estimate is 38/46 (82.6%), compared with 39/46 (84.8%) for the category-only sample lookup; this is a descriptive comparison. For Gemma-3-27B, the timing flip moved 0/20 informative progressive-disease responses to the new target; seven other progressive-disease responses already matched that target before the flip.

### Rank 8 — P1: Fix result provenance and delimit input-handling evidence (20–40 minutes)

**Location:** Ethics/reproducibility paragraph L642; §IV model paragraph L507; §V-B(b) L562; Limitations L638; `tools/lumiere_v4_stats.py:56`; `run_manifest.json`.

**Problem/rejection rationale:** The claimed chronological override rule is false for differently named run types; token-count checks cannot certify encoder-equivalent images. These details matter when serving artifacts are a plausible alternative explanation.

**Smallest defensible correction:** Use an explicit versioned inclusion manifest or parsed full timestamps, verify overrides, regenerate outputs; pin model/preprocessor/server identifiers where records exist. Do not invent missing versions. Replace the overstrong input statement.

**New experiments:** No for provenance repair and disclosure; no broad rerun is warranted solely by this audit because the checked score did not change.

**Replacement:**

> Each supplied image increased the recorded prompt token count, and the pipelines passed the reported known-answer probes. These checks establish input registration but do not establish equivalence of encoder representations or preservation of diagnostically useful MRI contrast.

**Manifest wording pending an actual loader change:**

> The current analysis resolves duplicate records in lexicographic folder order, which is not necessarily chronological. The released inclusion manifest identifies the response used for each item and condition.

### P2 — Optional improvements after P0/P1

1. **Table VII caption, L691:** label percentages observed detection frequencies over 50 simulations; define rho and include intervals. For example, 0/50 is not proof of zero false positives (Wilson upper bound approximately 7.1%).
2. **Table III caption/legend, L554:** explain directly that bootstrap interval labels are descriptive and corrected exact tests determine confirmatory significance. Keep all existing intervals visible.
3. **Fig.1/§I:** identify inherited phase names as organizational labels, not proof of testing full causal reasoning or treatment planning.
4. **Conclusion:** lead with the controlled evaluation rather than the unrelated source-benchmark linkage incompatibility.
5. **Reference entries/model manifest:** verify precise publication/model identifiers and the anonymous artifact URL before submission. No venue-page-limit judgment is made here because the applicable ICHI call/track requirements were not verified.

## 10. Five highest-impact changes achievable before submission

1. **Replace every broad negative headline with “limited evidence under these configurations,”** retaining uncertainty and failed-gate implications.
2. **Disclose the historical DSCR prompt–key ambiguity and make DSCR exploratory,** consistently naming the simplified tracked-lesion proxy.
3. **Add the missing concordance/LIL selection priority and selected agreement count** to the cohort paragraph.
4. **Rename the agreement audit and sharpen the HEAL-MedVQA comparison,** making the actual methodological increment explicit.
5. **Complete the uniform conditional reanalysis if feasible; otherwise honestly qualify the existing diagnostic.** Preserve the finite-sample observation without claiming calibration beyond the evaluated null.

These are prioritized over adding another model or dataset. Additional inference would not by itself resolve the principal target-definition and inferential-scope problems.

## 11. Final submission-readiness assessment

**Current scientific readiness: borderline and vulnerable; not ready for a strong clinical or capability claim.** Numerical reproducibility is strong. The conceptual distinction and reference AIA/LIL controls survive scrutiny. The central DSCR target and interpretation of negative evidence do not yet support the strongest possible reading of the title, abstract, and worked example.

**Minimum defensible submission:** implement the P0 reframing/disclosure, disclose actual selection, correct audit/novelty positioning, and either correct or explicitly qualify the conditional sampler. Leave unvalidated clinical targets labeled as such. Do not imply that newly edited instructions generated the archived results.

**Remaining acceptance risk after immediate fixes:** reviewers may still judge the methodological increment too incremental, the clinically interesting task insufficiently validated, or the small single-center evaluation too inconclusive. Those are genuine judgment risks, not verified numerical invalidity. A defensible narrower submission is achievable in hours; clinician-validated DSCR and a general absence-of-image-use conclusion are not established by the current evidence.
