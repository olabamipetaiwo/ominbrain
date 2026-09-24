# Review 

## Status (2026-09-24, updated after the v4 rebuild)

- [x] PJRF/TCM task definitions: prediction time, information and 52-week horizon stated; Brier scoring; TCM key is a stated rule and the paper says a documented treatment does not exist in LUMIERE.
- [x] Page fit: Conclusion moved before Limitations; body ends on page 5 (limit 8).
- [x] References: DeepBraTumIA/HD-GLIO-AUTO (via LUMIERE and Kickingereder 2019), HD-BET, NCIt, Wilson, McNemar added and checked against publisher/Europe PMC records; medical-VQA shortcut work is Nguyen et al. 2025 (already cited) and Yan/Jin.
- [x] Concern 5 numbers: root cause (two spellings of one label) fixed; `tools/paper_numbers.py` generates macros and tables; `--check` guards stale strings.
- [x] Concern 1: answerability audit (49% agreement) and answerable-by-construction `v4` items. Clinician validation NOT done (outstanding by design).
- [x] Concern 2/3/4/6: matched donor swaps, fact-flip tests, rule baselines, pre-registered estimands and margin, KAB demoted to an appendix.
- [x] Optional: randomised wrong context (`ctx_wrong`); regex classifier not used in v4 (v3 rule kept as a deterministic tool).
- [ ] v4 model runs (queued) and the Results text written from `results/lumiere_v4_stats.json` under the decision rules in `paper/preregistration_v4.md`.
- [ ] Clinician review of v4 keys (TCM rule, assumed schedule, segmentation-based keys). Deliberately left.


Required revision: define the prediction time, available information, and outcome horizon. Use an appropriate
probabilistic survival task or clinician-validated risk categories. For TCM, similarly distinguish documented
treatment from a justified treatment recommendation.

- [ ] Page fit: on the scratch compile Results ends on p.8 and Conclusion lands on p.9 (it currently sits AFTER Limitations). Check how ARR counts pages, then trim or move the Conclusion before Limitations.
- [ ] References: only 14 entries (published-only rule). Add published citations for DeepBraTumIA, HD-GLIO-AUTO, NCIt, medical-VQA shortcut work, and the statistics used (Wilson, McNemar); verify each against the publisher or ACL Anthology record.

**Optional**
- [ ] Randomised or per-label wrong-context variant of gating-causality (code change + GPU).
- [ ] Replace the regex action-class classifier in the TCM analysis with a reproducible tool.

**Deferred, listed as limitations rather than fixed**
- Clinician review of the v3 items; answerability fix for LIL/DSCR; PJRF/TCM scoring redesign.


-------

### Review

My recommendation: reject in its current form and invite substantial revision. ARR overall assessment: 2/5 (“Resubmit next cycle”). 

The research question is worthwhile, and the controls are thoughtful, but the experiment does not yet distinguish model shortcut behavior from problems in the benchmark’s construction.

  The topic fits NAACL’s clinical NLP, multimodality, and evaluation areas. NAACL 2027 uses ARR, so I have followed its review categories. NAACL call, ARR review
  form.

   Criterion          Assessment
  ━━━━━━━━━━━━━━━━━  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Overall            2/5 — substantial revision
  ─────────────────  ────────────────────────────────────────────────────────────────────────────────────────
   Soundness          2/5 — central inference remains inadequately supported
  ─────────────────  ────────────────────────────────────────────────────────────────────────────────────────
   Excitement         3/5 — interesting research question and controls
  ─────────────────  ────────────────────────────────────────────────────────────────────────────────────────
   Reproducibility    3/5 — useful detail, but release and exact execution specifications need strengthening
  ─────────────────  ────────────────────────────────────────────────────────────────────────────────────────
   Confidence         4/5 on methodological assessment; experiments were not independently reproduced

  Paper summary. The paper constructs five-phase question chains from 52 LUMIERE patients and evaluates four open-weight models. It compares image-present and text-
  only performance, substitutes patient images, audits stated evidence, and manipulates upstream answers. It finds small aggregate accuracy differences after
  removing images, image-induced answer changes without detected donor-label tracking, and substantial treatment-answer sensitivity to diagnosis context.

  Strengths

  - The paper goes beyond accuracy. Text-only, options-only, repeated-input, image-substitution, and context interventions offer complementary information.
  - The reporting is unusually candid. The manuscript acknowledges its post hoc equivalence margin, unvalidated questions, failed original decision-rule condition,
    and limitations of its metrics. This transparency deserves credit.

  - The upstream-context experiment is promising. The 17–39 percentage-point treatment-accuracy changes identify an experimentally manipulable dependence worth
    studying.

  - The distinction between textual consistency and causal faithfulness is appropriate. The current manuscript generally avoids treating answer recoverability as
    proof of faithful reasoning.

  - Patient-clustered uncertainty is appropriate for questions sharing a patient.

  Major concerns

  ### 1. Answerability is the decisive unresolved issue.

  The benchmark asks questions that the supplied evidence may not answer:

  - LIL asks for whole-lesion volume change from one axial slice per timepoint.
  - DSCR uses expert RANO labels while withholding some information involved in their assignment.
  - AIA has the same correct answer across all patients.
  - PJRF scores forecasts against realized survival.
  - TCM combines recorded treatment and drafted recommendations without clinician validation.

  These problems affect the interpretation of the primary experiment. If the image lacks the required information, removing it may leave performance unchanged even
  for a model capable of using relevant visual evidence.

  The strongest supported conclusion is therefore:

  > On this constructed dataset, adding the supplied images yields little aggregate accuracy benefit.

  That is narrower than establishing shortcut learning as the principal explanation. Acknowledging this limitation is good practice, but does not resolve it.

  Required revision: have qualified clinicians independently assess answerability and answer-key validity from exactly the inputs shown to models. Report agreement
  and adjudication, and rerun the primary analyses on a validated subset. A clinician accuracy comparison under the same input restrictions would be especially
  informative.

  ### 2. The counterfactual substitution does not provide a clean test of visual truth tracking.

  The manuscript reports that:

  - The donor’s exact LIL answer is available in 0/52 option sets.
  - Even the donor’s LIL direction is available in only 37/52.
  - Textual clinical facts remain those of the original patient.
  - The LIL permutation is degenerate because donor direction is fixed by construction.

  Consequently, the intervention often presents conflicting evidence or makes the donor-correct answer unavailable. Failure to select that answer cannot cleanly
  establish failure to track the image.

  Furthermore, (p=.64) means this test did not detect donor-specific tracking. It does not establish the stronger statement that donor identity “does not matter.”

  Required revision: construct matched image pairs with a shared question and option set that permits both correct answers. Keep nonvisual facts compatible, fix
  upstream context when estimating a direct image effect, and report DSCR separately from the uninformative LIL permutation component.

  ### 3. The TCM result establishes context sensitivity more clearly than shortcut use.

  Treatment answers changing when diagnosis changes is not inherently undesirable. The benchmark deliberately makes treatment follow disease course, so this
  dependence is partly built into the task.

  The class-level lookup analysis also does not fully explain option selection: the predicted action class identifies a unique option in only 18/52 cases. Thus, the
  finding that diagnosis predicts the correct action class in 50/52 cases does not establish that a simple lookup reproduces model accuracy.

  “Reproduces the effect” also needs qualification: the DSCR-only contrast is substantially smaller than the full-context contrast for Gemma-3-12B.

  Required revision: include cases where identical diagnosis labels require different actions because other supplied facts differ. Test whether models respond to
  those facts. Compare against an explicit rule-based option-selection baseline.

  ### 4. The equivalence claim is exploratory and aggregate.

  Choosing the ±8-point margin after inspecting confidence intervals makes it a description of observed precision, not independent confirmation of practical
  equivalence. Eight points also needs substantive justification.

  Pooling across five heterogeneous phases can conceal opposing effects. Moreover, because each arm regenerates upstream answers, later-phase differences measure the
  total effect of removing images throughout the chain, rather than an isolated same-phase image contribution.

  Required revision: define the primary estimand and a meaningful margin before a new evaluation. Report phase-specific effects and include a fixed-context
  comparison. Keep the current results explicitly exploratory.

  ### 5. Several numerical and interpretive inconsistencies need correction.

  These are material because they affect the paper’s conclusions:

   Issue                                                                             Why it matters
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   DSCR majority accuracy appears as both 67% and 63.5%                              At 63.5%, Gemma-3-27B’s reported 65.4% exceeds the majority baseline
                                                                                     numerically; the claim that every model falls below it is incorrect. This alone
                                                                                     does not establish significant superiority.
  ────────────────────────────────────────────────────────────────────────────────  ─────────────────────────────────────────────────────────────────────────────────
   The 54-patient cohort has 37 progressive-disease cases, while the final 52-       Removing two patients cannot remove four progressive-disease labels without
   patient analysis describes 33                                                     another change that needs explanation.
  ────────────────────────────────────────────────────────────────────────────────  ─────────────────────────────────────────────────────────────────────────────────
   “Only TCM depends on upstream context”                                            The same paragraph reports DSCR accuracy changes under upstream-context
                                                                                     interventions. Distinguish beneficial dependence from sensitivity.
  ────────────────────────────────────────────────────────────────────────────────  ─────────────────────────────────────────────────────────────────────────────────
   Appendix baselines “sit at or below” 25% except DSCR                              Reported AIA and majority-letter baselines exceed 25%.
  ────────────────────────────────────────────────────────────────────────────────  ─────────────────────────────────────────────────────────────────────────────────
   “Correct DSCR context” in the DSCR experiment                                     Clarify whether this means correct context supplied to DSCR, consisting of
                                                                                     earlier phases, rather than injecting DSCR’s own label.

  All reported counts, percentages, and conclusions should be generated from one authoritative results table.

  ### 6. The contribution needs tighter focus.

  KAB receives substantial emphasis, but its proposed components are not strongly validated:

  - Recoverability is near ceiling.
  - Ontology coverage measures vocabulary membership.
  - Adaptation triggers too rarely for a meaningful conclusion.
  - Gating is an imposed scoring convention, with no gated results reported.

  Meanwhile, medical VQA shortcut evaluation already has relevant precedent, including visual and textual perturbation protocols in HEAL-MedVQA. The paper’s
  distinctive contribution should be the insight provided by longitudinal chains and upstream-context interventions. Nguyen et al., IJCAI 2025.

  I would reduce KAB’s prominence and center the paper on a validated empirical finding. The OmniBrainBench compatibility analysis is useful motivation, but should
  not carry substantial novelty weight when the original release did not promise the linkage being sought.

  ### Questions I would ask during author response

  1. What fraction of questions can clinicians answer from the exact model-visible inputs?
  2. Does the image-ablation finding persist on that answerable subset?
  3. What are the authoritative final DSCR counts and majority baseline?
  4. Can donor tracking be tested where both answers are available and the remaining context is compatible?
  5. Does diagnosis-only treatment prediction remain strong when other clinical facts distinguish actions?

  ### What would change my recommendation

  The highest-priority work is clinical validation and repair of the evaluation, followed by a valid counterfactual subset and reconciliation of the reported
  numbers. Adding proprietary models would broaden coverage, but would not resolve the central validity issue.

  A revised paper showing that models still obtain correct answers through textual cues on clinician-validated, visually answerable questions, while failing
  controlled image interventions, would support a substantially stronger contribution. I would not currently recommend Findings either: the unresolved concern is
  soundness, which remains central to that venue.


--------


 My remaining major concerns, excluding clinical review

  1. The current title announces a finding that the new study has not established.

  The abstract, results, generated tables, and conclusion all acknowledge that v4 runs are pending. The paper also correctly withdraws shortcut conclusions from v3.

  Consequently, “Right Answer, No Image: Shortcut Learning…” currently states the outcome before the decisive experiment has reported it.

  The alternative already commented in your source is better:

  > Do Medical MLLMs Read the Scan? Shortcut Controls on Brain-MRI Question Answering

  Complete the experiments before choosing a conclusion-bearing title. A rigorous finding of image use, mixed behavior, or inconclusive effects could all support a
  useful paper.

  2. The 49% agreement statistic is still interpreted too strongly.

  Your audit finds that an automated enhancement rule agrees with expert categories on 130/268 follow-ups. That establishes disagreement between two procedures.

  It does not establish that only 49% of labels can be recovered from the images, or that every remaining label necessarily depends on information outside them.
  Disagreement could also arise from segmentation error, lesion selection, measurement differences, or the simplified rule. Your reported measurement correlation of
  0.57 and median measurement ratio of 1.4 make these alternatives particularly relevant.

  The sentence attributing the remaining ratings to outside evidence is therefore unsupported.

  Use:

  > “Our slice-based enhancement rule agreed with expert RANO ratings on 130 of 268 follow-ups (48.5%). This disagreement prevents us from assuming that the
  > displayed inputs support the expert labels.”

  Also report rule coverage separately from agreement: 37 follow-ups are undetermined. Agreement among determinate cases is approximately 56.3%, alongside the 48.5%
  overall figure.

  This is an inference issue, independent of requesting clinical review.

  3. “Every key is a stated function of the model-visible inputs” is not accurate across all five phases.

  There are different task types here:

  - AIA–DSCR evaluate image-derived labels.
  - TCM evaluates a constructed decision rule.
  - PJRF evaluates a probabilistic forecast against a subsequently observed outcome.

  PJRF’s observed outcome is not a deterministic function of its supplied predictors. Using Brier score makes the evaluation more appropriate; it does not make
  individual mortality outcomes answerable by construction.

  A more precise claim would be:

  > “We define image-derived targets for AIA–DSCR, a rule-based target for TCM, and an explicitly timed probabilistic forecasting task for PJRF.”

  There is also an implementation mismatch: the TCM question does not explicitly give the decision rule. The rule is stored in metadata, while the question asks for
  the appropriate management step. If the intended experiment tests application of a supplied rule, put that rule in the prompt. Otherwise, performance combines rule
  knowledge with use of the supplied facts.

  4. The statistical decision rules need reconciliation with the implementation.

  The analysis computes Holm-adjusted p-values, but the displayed E1 verdict is assigned from the unadjusted bootstrap interval. Thus, a cell can say “image helps”
  while failing the stated multiplicity correction.

  Additionally, “image helps” and “within margin” are not mutually exclusive. An interval of [+2, +8] percentage points satisfies both. Report these as separate
  properties:

  - Evidence of a positive image effect.
  - Whether the effect is contained within the predefined practical margin.

  The ±10-point margin is now prospective, which is an improvement. However, its rationale should concern practical performance, not whether a model “reads the
  scan.” A small net accuracy effect can coexist with substantial image use.

  E2 also makes positive tracking claims across multiple model–phase comparisons without correction. That can be exploratory, but the designation should be
  consistent between the analysis plan and conclusions.

  5. I found a concrete mismatch between the DSCR prompt and label-generation code.

  The prompt defines measurability as at least 10 mm by 10 mm. The implementation tests whether the diameter product is at least 100 mm².

  Those conditions are not equivalent: 20 mm × 5 mm passes the implemented product threshold but fails the stated dimensional requirement.

  This is a target-definition bug, regardless of clinical interpretation. Align the prompt and implementation, identify affected items, and document any resulting
  change to the fixed item set and analysis plan.

  6. The fact-flip results must measure a paired response, not just post-intervention correctness.

  The main reported statistic counts whether the answer matches the rule after a flip. A model could already have selected that answer before the intervention and
  remain unchanged.

  The code includes a useful conditional measure for initially correct responses, but the primary presentation should show:

  - Original answer matches the original rule.
  - Changed answer matches the changed rule.
  - Answer actually changes when the rule requires it.

  For timing flips, emphasize the progressive-disease subset where the correct action changes. Unchanged non-progressive cases are useful negative controls, not
  evidence of timing sensitivity.

  Smaller corrections

  - AIA is approximately balanced—16/16/15/15—not exactly uniform. Text-only performance is not mathematically forced to equal 25% in this finite sample.
  - A logistic baseline failing to beat the base rate does not establish that the supplied facts contain no predictive information. Say “this baseline did not
    improve on the base rate.”

  - Replacing unparseable PJRF responses with 0.5 can reward failed outputs with reasonable Brier scores. Report failure rates and sensitivity to that handling.
  - “Cannot support same-patient chains at all” is stronger than finding only two verifiable links. State that the release does not provide sufficient verified
    linkage for your five-phase evaluation.

  My updated assessment

   Aspect                               Assessment
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Research question                    Strong
  ───────────────────────────────────  ────────────────────────────────
   Revised control design               Substantially improved
  ───────────────────────────────────  ────────────────────────────────
   Claim precision                      Still needs revision
  ───────────────────────────────────  ────────────────────────────────
   Implementation–method agreement      At least one material mismatch
  ───────────────────────────────────  ────────────────────────────────
   Empirical completeness               Pending
  ───────────────────────────────────  ────────────────────────────────
   Current submission recommendation    Revise; not ready yet

  The revision now has a credible experimental foundation. The next decisive steps are completing v4, fixing the prompt–key mismatch, and making the claims follow
  the results. None of those recommendations depends on obtaining clinical review.