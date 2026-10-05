# Second review of the revised image-dependence manuscript

Reviewed 5 October 2026. Current source: `paper/latex/acl_latex.tex`, its generated tables and numbers, and the 16-page `paper/latex/acl_latex.pdf`. Previous review: `paper/review.md`.

**Simulated recommendation: weak reject; materially improved, but the principal methodological validation still needs correction.** This recommendation does not depend on completing clinician review. The new synthetic controls are a useful addition, but the supplied reassignment implementation cannot support the DSCR assignment-stability claim, and the manuscript still converts nondetection into an absence claim.

Scope: I read the revised manuscript and appendices, visually inspected all 16 PDF pages, inspected the donor-validation and supplementary analysis code, and rechecked the two central prior-work comparisons. I did not rerun model inference or reproduce the reported statistics: `data/lumiere/v4/` and the v4 raw-result/validation outputs are absent from this checkout. Findings below distinguish demonstrable code/text problems from questions requiring those records. Source-line references refer to the current files; PDF pages refer to the supplied compiled paper.

## What the revision has improved

- **The prior-work comparison is substantially repaired.** The worked example now describes HEAL-MedVQA's anatomical-region replacement and acknowledges complementary-pair correctness in balanced VQA. These agree with the relevant primary sources: [HEAL-MedVQA, Section 3.1](https://www.ijcai.org/proceedings/2025/0853.pdf) and [Goyal et al., Section 4](https://arxiv.org/html/1612.00837v3). The earlier assertion that those protocols would necessarily call this result image use is gone.
- **Figure 3's final verdict is more defensible.** It now acknowledges the accuracy improvement and says the controls do not establish category reading. The DSCR reference-model discussion also no longer equates the model's errors with proven item unanswerability.
- **Several reporting errors are addressed.** Table 3 explains the 42-item DSCR answer-change denominator; Table 7 uses the paired sample sizes; the 25/46 Gemma-3-27B transition is called a slim majority; the audit appendix no longer calls 21/33 and 22/48 the same agreement.
- **The TCM base-prompt description is clearer.** Section 3.2 explicitly says the management rule is absent from the base stems and supplied only in the post hoc explicit-rule condition, although Appendix C still contradicts this.
- **The new synthetic predictors address an appropriate question.** Table 6 usefully demonstrates that positive donor gain can occur for a generic image-presence response. Keeping that demonstration would strengthen a carefully qualified paper.
- **The reference-model result remains informative.** Strong AIA/LIL own-image and donor-image accuracy provides a positive demonstration of task feasibility, with appropriate caveats about item-level validity.

## Major concerns

### 1. The claimed DSCR stability across new donor assignments is not supported by the supplied implementation

**Location:** Appendix D, PDF p. 14; `acl_latex.tex:613`; `tools/lumiere_v4_donor_validation.py:111–127,144–153`.

The manuscript says detection is stable across redrawn valid assignments. However, `random_assignment` shuffles the recipient IDs into a **one-to-one** donor permutation, requires a different key for every recipient, tries 200 times, and silently returns the original assignment if it fails.

For the reported DSCR cohort, success is mathematically impossible:

- There are 27 progressive-disease items among 46 DSCR items.
- The paired subset excludes only four items, so its 42 recipients include **at least 23 progressive-disease items** and at most 19 other items.
- A one-to-one permutation would need a distinct non-progressive donor for each of those at least 23 recipients. At most 19 are available.

Consequently, for inputs matching the paper's counts, every DSCR call to this routine must return the original assignment. The subsequent stability loop also fixes the prediction seed to 13, and the evaluator resets its random seed. Repeating this calculation therefore supplies no DSCR assignment-stability evidence.

This routine also does not enforce the original same-image-count condition. Its one-use-per-donor construction differs from the actual design, which allows two uses. Furthermore, the stability loop evaluates only the perfect tracker and the generic shift, not the noisy tracker whose 92% detection rate immediately precedes the stability claim.

**Required revision:** use a generator that preserves the actual donor eligibility and capacity constraints, fails explicitly when infeasible, and records assignment identities, number of unique assignments, and constraint checks. Report assignment variation separately from prediction-seed variation. Until then, remove the DSCR stability claim. This defect does not by itself invalidate the fixed-assignment entries in Table 6; it invalidates the additional stability claim.

### 2. The synthetic power result does not establish absent tracking in the actual models

**Location:** Appendix D, PDF p. 14; `acl_latex.tex:613`; abstract, `acl_latex.tex:156`.

The new paragraph concludes that nondetection reflects an absence of donor-specific tracking rather than low power. That is stronger than the evidence allows.

The 92% rate is power against one specified synthetic alternative on one assignment, estimated from 50 simulations. It does not establish comparable power against heterogeneous, class-specific, correlated, or weaker tracking by the evaluated models. Even that particular alternative was not detected in 8% of simulations. A nonsignificant observation cannot select the generic predictor over all possible tracking mechanisms.

There are additional mismatches between the simulation and the interpretation:

- The matched +19.0-point gain is between two synthetic predictors. Llama-4-Scout's observed DSCR gain is +28.6 points. Matching a scalar gain would not in any event match the joint answer distribution or power.
- In the implementation, a tracker uses the true donor answer with probability rho and otherwise guesses uniformly. With four choices, rho = 0.4 therefore gives a 55% probability of the correct donor answer, not 40%. Describe rho as the tracking-branch probability.
- The constant and generic-shift examples are deterministic controls whose statistics are invariant to relevant label permutations. Their 0% detection is a useful sanity check, but not broad calibration of false-positive rates for realistic no-tracking behavior.
- Table 6 reports 0% detection for random answers, while the prose says controls are flagged at the nominal rate. Distinguish a nominal 5% threshold from the observed detection rate and report simulation uncertainty.

**Suggested replacement:** “Under the specified synthetic predictor family, the test detected the rho = 0.4 tracker in 46 of 50 simulations and did not flag the generic image-shift predictor. These checks illustrate discrimination for these mechanisms; nonsignificant model results do not rule out weaker or differently structured tracking.”

Use “did not detect donor-specific tracking” in the abstract instead of language implying equivalence to random assignment. If ruling out tracking is essential, define a meaningful minimum tracking effect and conduct an appropriately justified exclusion/equivalence analysis.

### 3. The permutation null and its implementation need a stronger justification

**Location:** Appendix D; `tools/lumiere_v4_supplement.py:221–288`.

The code permutes donor-key entries across recipients and repairs assignments that equal the recipient's own key. It does not check image-count compatibility, retain same-donor label blocks, or reproduce the original constrained donor-assignment mechanism. Labels associated with repeated uses of the same donor can be scattered independently. A fixed number of random repairs also does not establish uniform sampling over the permitted assignments.

These facts do not automatically make every reported p-value wrong: the authors could define a conditional label-association test distinct from a design-based assignment test. But that distinction must be explicit. The present language moves between those interpretations while using the result as evidence against donor-specific behavior.

The implementation attempts 5,000 permutations but skips those whose repair fails. It saves the accepted count as `n_perm`; the manuscript simply says 5,000 permutations. Report actual accepted counts and demonstrate that the sampler targets the stated null distribution. The plus-one p-value adjustment is already present and is not the problem here.

**Required revision:** specify what is held fixed, what is exchangeable under the null, how image-count strata and reused donors are handled, and what inference the test permits. Validate calibration under several no-tracking mechanisms, including responses that depend on image count and option ordering. Donor-cluster bootstrap results do not, by themselves, validate the separate permutation procedure.

The final sentence of Appendix D also says subtraction of the no-image prior isolates tracking from generic response. Table 6's generic shift is a direct counterexample to that statement: it has a positive gain without tracking. Attribute any discrimination to a separately justified permutation analysis, not to the gain alone.

### 4. The central interpretation and positive-control rule remain inconsistent across sections

**Location:** `acl_latex.tex:419,487,504–527,559`.

The revised Figure 3 verdict says tracking is unestablished, but its heading still says the controls overturn image use. The worked-example paragraph likewise says the controls separate correct slice use from collapse of the text-only arm. The experiment supports a narrower conclusion: the gain is real, while correct donor-specific tracking remains unestablished. Below-majority accuracy does not rule out correct visual classification of some items.

The phrase that the gain arises only because text-only accuracy is poor is also a causal overinterpretation. The two measured accuracies establish the difference; they do not identify the exclusive mechanism behind it.

The AIA gate has a similar inconsistency. Results describe sequence identification as a cautionary screen rather than a prerequisite for lesion/category reading, but Methods and Limitations still state that failing it means LIL/DSCR effects support no conclusion. Keeping the original prespecified decision rule in the record is appropriate. Distinguish that historical rule from the scientifically justified interpretation of task-specific estimates. Do not make evidence on one capability logically contingent on another without justification.

Figure 3 also retains the unqualified claim that +45.7 points is the largest ablation gain in the study. The reference model has +73.9 on AIA and +63.2 on LIL. Say “largest among the four open-weight models.” Its prespecified-controls heading should acknowledge that the decisive permutation analysis was added post hoc, as the caption now does.

### 5. The TCM transition denominator does not implement the definition in the caption

**Location:** Tables 4 and 10; `tools/lumiere_v4_supplement.py:177–198`.

Table 4 defines informative items as those whose baseline true-context answer was not already the new target. The code instead computes total items minus `already_at_new`, where that category is incremented only when **both the baseline and post-flip answers equal the new target**.

An item that starts at the new target and moves away is therefore included in the denominator, even though the caption excludes it. This is a definite implementation/definition mismatch. I cannot establish which reported cells change without the raw responses.

**Required revision:** compute baseline eligibility independently of the post-flip answer; separately report items that start at the target and move away. Recalculate the affected ratios and explicitly report whether the published values change.

## Remaining reporting and presentation issues

| Location | Finding and correction |
|---|---|
| Table 8, PDF p. 15 | DSCR has one displayed n = 46 although the donor metrics use 42. The old denominator concern remains in the reference-model table, even though Table 7 is improved. Add separate own/text and swap sample sizes. |
| Precision paragraph, PDF p. 7; source line 489 | It points to Table 8 for the bf16 rerun, but that table contains only Gemini. Full precision-control intervals and donor results are still missing from the paper. Changing Figure 2's caption to say results are in prose fixes the reference, not the incomplete reporting. |
| Table 9, PDF p. 16 | Pixtral and the API reference are absent despite claims about checks for each pipeline and tags in this table. Add their applicable information or narrow the claim and give the precise location of the evidence. |
| Appendix C, PDF p. 12; `generated/v4_example.tex:13` | The worked example says the TCM stem states the rule, conflicting with Section 3.2's base-stem description. Label the example's exact condition or correct its text. Figure 4 also does not show the DSCR donor images despite the opening claim that it shows the donor images used. |
| Table 3 caption, PDF p. 7 | “Accuracy uses all 46” is overbroad: LIL uses 38. State AIA 46, LIL 38, DSCR 46; retain the separate 42-item DSCR answer-change denominator. |
| Audit discussion, PDF p. 4 | Main text still says agreement did not differ with size closeness. Appendix D now correctly treats the observed 63.6% versus 45.8% difference as uncertain. Align the main text with that wording. |
| Output handling, PDF p. 14 | Valid-JSON DSCR accuracy of 23.1% does not “match” 19.6% overall. Say it remains low/below nominal chance; distinguish an observed difference from an inferential conclusion. |
| Methods and Appendix B | The local analysis-plan change log documents a 16,384-token reference-model cap versus 800 for the open models, but the current manuscript's cap description does not clearly retain that exception. Restore the per-model distinction and its reason. |
| Appendix D | The donor-count range renders as “31 to 30”; order the endpoints and preferably list each phase's count. |
| Limitations | Correct the visible “enhancems ent” typo. |

**Submission-length issue:** the conclusion continues onto page 9, before Limitations begins. For a standard ARR long-paper submission, main content is limited to eight pages, with extra space allowed after the conclusion for limitations and ethical considerations. The current PDF therefore exceeds that main-content allowance; the problem is not its 16-page total including references and appendices. Check the intended venue's applicable rules, and shorten the main text without changing the template. [Current ARR call for papers](https://aclrollingreview.org/cfp).

Visually, the figures and tables are intact and readable when enlarged. Tables 3 and 7 and Figure 3 are dense at normal page size; Appendix page 16 has large empty regions around its floats. These are secondary to the substantive corrections. The five-phase chain and compatibility narrative still occupy space that could better explain the central estimand and validation. Keep TCM clearly secondary and retain PJRF's appropriately limited interpretation.

## Questions for the next revision

1. How many genuinely distinct, constraint-valid donor assignments were tested, and can their identities and checks be released?
2. What exact null distribution does the permutation sampler target, and how does it preserve relevant image-count and donor-dependence structure?
3. What tracking magnitudes and heterogeneous behaviors remain compatible with the observed model results?
4. Do the corrected baseline-eligibility denominators change any TCM transition rates?
5. Can all reported cells, including both precision controls, be regenerated with numerators, denominators, inclusion criteria, and the final run manifest?

## What would change my recommendation

The most valuable next revision is focused: repair the assignment validation and establish the permutation's interpretation; narrow absence claims to nondetection; reconcile the TCM definition and reporting; and fit the main paper within the applicable limit. Broader model coverage is less urgent than these corrections.

The defensible contribution remains worthwhile: **large image-versus-text accuracy gains can coexist with insufficient evidence of correct donor-specific tracking, and reference models can demonstrate that some tasks are feasible.** The revised paper is closer to supporting that contribution, but the new validation should strengthen the evidence rather than be used to claim that all low-power explanations have been eliminated.
