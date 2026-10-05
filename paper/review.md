# Manuscript review for NAACL 2027

# Review of Imagedependence.pdf

**Simulated committee recommendation: weak reject in its current form, even excluding clinical review entirely.** The paper has a worthwhile evaluation idea and unusually transparent reporting, but its central interpretation, positioning against prior work, and several internal inconsistencies need revision.

This review covers all 15 pages, including the figures and appendices, and checks the two prior evaluation papers most directly implicated by the novelty claim. It concerns the manuscript; the experiments were not reproduced and the promised submission artifact was not inspected.

Source: [Imagedependence.pdf](Imagedependence.pdf).

## Paper summary

The paper distinguishes three observable behaviors in multimodal models: improved accuracy when an image is supplied, changed answers following an image intervention, and correct tracking of a replacement image's answer. It constructs brain-MRI questions from LUMIERE and evaluates four open-weight models, a reference model, and additional precision controls.

Its strongest result is the contrast between the reference model's clear image-dependent performance on sequence identification and localization, and the much weaker results of the evaluated open models. The methodological contribution is a collection of controls intended to prevent overinterpreting image-ablation results.

## Strengths

- **The research question matters.** Separating answer sensitivity from correct use of visual evidence is relevant to multimodal NLP evaluation.
- **The reference model provides a useful positive result.** Its high own-image and donor-image accuracy on AIA and LIL makes the evaluation substantially more informative than a collection of unexplained failures.
- **Several design choices are careful:** paired comparisons, documented key provenance, donor-compatible answer sets, multiplicity correction, and explicit separation of exploratory analyses.
- **The reporting is candid.** The paper acknowledges weak power, serving-stack confounds, parsing problems, and changes to the originally planned summaries.
- **The fact-flip transition analysis is useful.** Separating answers that moved to the new target from answers already at that target avoids a real measurement error.

## Major concerns

### 1. The central worked example does not establish the conclusion claimed

Figure 3 concludes:

> “response sensitivity to the image, not reading the RANO category from the slice.”

The evidence supports a narrower conclusion: **correct category tracking has not been established.**

Three distinctions matter:

- Accuracy below the majority-class baseline does not rule out image-dependent classification. A model can recognize some minority-class examples correctly while making enough other errors to underperform a constant predictor.
- A poor text-only baseline makes the ablation gain an inadequate measure of successful interpretation, but the observed accuracy improvement remains real.
- A donor permutation result of p = .244 does not demonstrate absent tracking or equivalence to random assignment.

The paper correctly warns elsewhere that nonsignificance is not evidence of no effect, but Figure 3 and the surrounding argument do not consistently follow that principle.

Suggested replacement for its verdict:

> “The image improves accuracy relative to the text-only condition, but these controls do not establish donor-specific category tracking.”

The claim on page 6 that DSCR is “therefore only partly answerable” because the reference model reaches 71.7% has the same problem. A model's errors do not establish that the remaining items are unanswerable. This objection is about inference, independent of clinical review.

### 2. The comparison with prior work is materially inaccurate

Lines 528–531 describe HEAL-MedVQA as scoring image reliance through an ablation drop, and balanced VQA as scoring whether answers change under replacement.

However:

- **HEAL-MedVQA's visual perturbation test replaces a specific anatomical region with one from a differently diagnosed image and measures a directional Yes-to-No transition.** It is not simply an image-versus-text accuracy drop. [Published HEAL-MedVQA paper](https://www.ijcai.org/proceedings/2025/0853.pdf)
- **Goyal et al. explicitly distinguish pairs with both answers correct, identical predictions, and different predictions.** Their analysis already separates correctness on complementary images from answer changes alone. [Goyal et al., Section 4](https://arxiv.org/html/1612.00837v3)

Consequently, the assertion that these protocols “would call this image use” is not established by the experiments reported.

This is particularly damaging because the paper's novelty depends on this contrast. Reframe the contribution as a carefully specified extension or synthesis, identify exactly what the prior-subtracted donor statistic adds, and compare it with correctness on complementary pairs. A design comparison is acceptable, but it must represent the earlier methods accurately.

### 3. The donor statistic needs stronger validation as a measurement tool

Subtracting text-only accuracy against the donor key is sensible, but it does not necessarily remove a generic effect of receiving any image.

For example, suppose a model switches to a favored category whenever an image is present, irrespective of its content. Its donor gain can be positive if that category is frequent among assigned donors. The permutation analysis recognizes this issue, but it becomes central to interpreting the main example despite being introduced post hoc.

The paper would benefit from:

- A precise statement of the null hypothesis tested by the donor-key permutation.
- An explanation of how permutations preserve image-count matching, class restrictions, and dependence from reused donors.
- Results over multiple valid donor assignments.
- Controlled predictors with known behavior: constant answers, image-presence-triggered answers, and deliberately noisy correct tracking.

These would show when the proposed protocol succeeds or fails.

Also clarify what swapping adds beyond reevaluating donor images under another item's prompt or option ordering. Since the stems have no patient-specific facts, the extra information supplied by this construction needs to be explicit.

### 4. The positive-control gate is not sufficiently justified across tasks

The rule that failure on sequence identification makes localization and category effects uninterpretable is too strong without further argument.

A model might recognize lesion location while being poor at distinguishing MRI sequences. Conversely, sequence recognition does not establish competence in lesion measurement or longitudinal comparison.

AIA is a useful diagnostic control, but it is not automatically a prerequisite for every other visual capability. Consider task-specific positive controls, or present AIA failure as a reason for caution rather than a universal gate.

The gate also illustrates the statistical instability: Llama-4-Scout passes because its bootstrap interval excludes zero, while its exact McNemar result is p = .070. That is not necessarily a computational error, but the methodological conclusion should not hinge on this discrepancy without justification.

### 5. The evidence is too narrow for the broader methodological conclusion

The main methodological demonstration rests heavily on one model-task combination, with 38–46 patients per phase and wide uncertainty intervals.

Small samples can support valuable evaluation studies. Here, however, the paper needs to distinguish:

- A protocol detecting correct tracking.
- A protocol detecting generic sensitivity.
- An inconclusive result caused by limited power.

The reference model helps with the first. The other two remain difficult to separate.

The most valuable additional work would be a focused validation of the protocol using known-behavior controls and repeated donor assignments, followed by a second setting if feasible. Adding more weak model results alone would contribute less.

### 6. The five-phase narrative dilutes the strongest contribution

The title promises a study of image dependence. AIA, LIL, and DSCR address that directly. The management-rule and survival analyses introduce different questions, while the ordinary chain produces little additional evidence.

Shorten the OmniBrainBench compatibility discussion, make the image interventions the main story, and move most chain and survival material to the appendix. TCM could remain as a clearly labeled extension concerning sensitivity to stated facts.

That would give more space to explaining and validating the actual measurement contribution.

## Specific inconsistencies that require correction

| Location | Issue |
|---|---|
| Table 3 | DSCR “answers differ” values of 19.0%, 11.9%, and 88.1% cannot arise from integer counts with the stated n = 46. They match 8/42, 5/42, and 37/42. This suggests an unstated subset or denominator mismatch. |
| Lines 543–546 | “Only a minority of informative items in every model” contradicts Gemma-3-27B's 25/46 label-flip transitions: **54.3%**. |
| Appendix D, lines 1008–1011 | Agreement is described as “the same,” but 21/33 is **63.6%**, whereas 22/48 is **45.8%**. An uncertain difference is not the same observed agreement. |
| Figure 3 and Appendix D | Figure 3 calls its controls prespecified, but the decisive permutation analysis is described as post hoc. Distinguish the planned intervention from the later inferential procedure. |
| TCM description versus Results | The task is repeatedly described as adherence to a stated rule, yet lines 561–562 describe supplying that rule as a post hoc condition. State exactly which prompts contained the rule. |
| Figure 2 caption and control reporting | The caption says precision controls are reported in tables, but the supplied tables do not provide complete bf16/Pixtral results comparable to Table 3. |
| Table 7 | DSCR displays n = 46, while donor evaluation uses 42 pairs. Give separate own-image and swap sample sizes. |
| Appendix D | The claim that every patient is both donor and recipient is difficult to reconcile with approximately 30–31 distinct donors and 38–46 recipients. Clarify the actual assignment graph. |

These are fixable, but together they would reduce a reviewer's confidence in the results until checked against the underlying records.

## Questions for author response

1. What happens to the main conclusion under a common, justified inferential procedure for the positive-control gate and donor tracking?
2. Does donor tracking remain similar across several valid assignments and option-order permutations?
3. Can the proposed protocol distinguish a generic image-presence response from weak but genuine correct tracking in controlled examples?
4. Which TCM results use an explicitly supplied rule, and how do the reported results change under that condition?
5. Can every table entry be regenerated with its exact numerator, denominator, and inclusion criteria?

## What would change the recommendation

Three substantive improvements would warrant reconsideration: correct the prior-work comparison; narrow the main conclusion to what the evidence establishes; and demonstrate that the donor protocol distinguishes known tracking behavior from generic sensitivity. Resolving the table inconsistencies is necessary alongside those changes.

There is a publishable research direction here. The current manuscript's most defensible finding is that **large image-ablation gains can coexist with inadequate evidence of correct donor-specific tracking**. Building the argument around that claim would make it considerably stronger.

## Suggested next actions

- Build a prioritized revision plan separating manuscript-only fixes from analyses and new experiments.
- Draft revised abstract, contribution statements, and Figure 3 text that accurately reflect the evidence and prior work.
- Audit the analysis code and results for reported tables, denominators, and contradictory statements identified in this review.
