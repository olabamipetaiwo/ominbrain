**My assessment: borderline Findings; not yet a strong NAACL main-conference submission.** The paper has a worthwhile evaluation contribution and substantial experimental care, but its central statistical argument and positioning need tightening.

I reviewed the latest manuscript, including its appendices and artifact documentation. As requested, I exclude clinical validity, treatment appropriateness, and the absence of clinician review from my recommendation. I did not rerun the experiments. paper/latex/acl\_latex.pdf

The paper fits NAACL’s **Resources, Benchmarks, and Evaluation** and **Multimodality and Language Grounding** areas. NAACL explicitly welcomes evaluation contributions; introducing a new model is unnecessary. The published deadline is October 12, 2026, through ARR. [NAACL 2027 call](<https://2027.naacl.org/calls/main_conference_papers/>)

Using the [ARR review scale](<https://github.com/acl-org/aclrollingreview/blob/main/reviewform.md>), my provisional scores would be:

| Criterion | Score | Rationale |
|---|---:|---|
| Soundness | 3/5 | Narrow empirical findings are supported; broader methodological interpretation needs work. |
| Excitement | 3/5 | Useful distinction between response changes and correct image-dependent behavior. |
| Overall | 2\.5/5 | Borderline Findings. |
| Confidence | 3/5 | Detailed manuscript review, without independent execution or an exhaustive novelty search. |

**What the paper contributes**

The paper distinguishes three outcomes often conflated in multimodal evaluation: an accuracy improvement when images are supplied, changes in answers when images change, and movement toward the answer supported by a replacement image. It evaluates these outcomes on a 46-patient question set, with positive controls and additional checks.

Its strongest example is Llama-4-Scout on DSCR: accuracy improves from **8\.7% to 54.3%**, yet the majority answer achieves **58\.7%**, and the original donor-label permutation does not detect donor-specific association. This is a useful demonstration that a large ablation effect needs additional interpretation.

**Strengths**

- **A clear, relevant evaluation question.** Distinguishing image sensitivity from correct image-conditioned behavior matters beyond medical QA.
- **Convincing positive-control results on AIA and LIL.** The reference model achieves 95.7% and 100% with images and tracks donor replacements. These results substantially strengthen the study.
- **Considerable attention to alternative explanations.** Precision reruns, a different model family and serving stack, image-input probes, parsing checks, and alternative donor assignments make this much stronger than a simple ablation study.
- **Transparent reporting.** The manuscript identifies post hoc analyses, protocol amendments, uncertainty, and limits on interpretation. The artifact documentation provides a useful route from saved responses to reported results.

**Major concerns**

**1\. The paper needs a sharper definition of “image dependence.”**

An image can influence predictions without improving accuracy. A model can also extract useful visual information while remaining below a majority baseline because it performs poorly on other items.

Consequently, **54\.3% below 58.7% does not establish that the model fails to read the image**. It establishes that aggregate accuracy does not outperform that constant predictor. The manuscript often acknowledges this distinction, but Figure 3’s red crosses and phrases such as “neither bears out image use” invite a stronger interpretation.

Similarly, the image-minus-text contrast remains a valid description of those two conditions. A weak text-only baseline makes it insufficient evidence of correct visual grounding; calling the contrast “confounded” needs a more precise estimand.

**Revision:** Define the target as _correct, task-relevant image dependence under specified interventions_. State explicitly that majority-baseline performance is contextual evidence, not a necessary test for image use. Add class-wise results or confusion matrices to show what the aggregate comparison conceals.

**2\. The donor permutation is central to the contribution, but its assumptions remain insufficiently justified.**

Appendix D acknowledges that the permutation:

- does not preserve the equal-image-count strata;
- does not keep reused donors together;
- repairs forbidden assignments and discards unsuccessful repairs.

These details matter because the donor assignment is constrained, and those constraints can affect whether labels are exchangeable across recipients.

The simulation checks are valuable. In particular, the 2,000-null-dataset checks and comparison with a repair-free sampler deserve credit. However, agreement between two samplers does not establish that either samples the intended null distribution. Calibration under the simulated mechanisms supports those mechanisms, rather than general validity.

**Revision:** State the conditional null and exchangeability assumptions in the main method. Either justify the current test under those assumptions or add an analysis preserving the relevant assignment structure. Keep the distinction between a conditional label-association test and an assignment-based randomization test explicit.

This is my most consequential technical concern because the permutation supplies much of the claimed advantage over raw donor gain.

**3\. The methodological novelty is plausible, but not yet demonstrated clearly enough for the main conference.**

The related work appropriately recognizes complementary-image evaluation and visual/textual shortcut testing. HEAL-MedVQA already contributes protocols targeting visual and textual shortcuts, so novelty cannot rest on using perturbations to question apparent visual understanding. [HEAL-MedVQA proceedings paper](<https://www.ijcai.org/proceedings/2025/853>)

The strongest candidate contribution is the combination of donor-key scoring, baseline subtraction, and a test separating donor association from generic image-induced shifts. That contribution is currently dispersed across the introduction, results, and appendix.

**Revision:** Compare several diagnostics on the same known-behavior predictors: raw ablation, answer-change rate, donor gain, and the proposed association test. Show precisely which misleading conclusions each permits. Much of the necessary evidence already exists in Table 5; promote and organize it around the novelty claim.

A second dataset would strengthen generality, but I would not make it mandatory if the claims remain appropriately scoped.

**4\. The negative findings require more consistent uncertainty language.**

The paper correctly notes that most intervals are too wide to establish equivalence within ±10 percentage points. Nevertheless, phrases such as “indistinguishable from text-only” and “null donor tracking” can imply a stronger absence claim.

The alternative donor assignments also yield one significant Scout DSCR result out of five. That supports assignment sensitivity; it does not settle whether weaker tracking exists.

**Revision:** Consistently say “no statistically detectable improvement” or “tracking was not consistently detected.” Report effect estimates across assignments alongside significance counts. Preserve the distinction between weak observed performance and evidence that an effect is negligible.

**5\. The five-phase framing dilutes the strongest paper.**

The main contribution concerns AIA, LIL, and DSCR image interventions. PJRF supports no substantive conclusion, while the chain experiment is secondary. Yet substantial introductory and methodological space establishes the five-phase structure.

TCM also mixes two questions: whether the model knows an unstated rule and whether it follows supplied facts. The explicit-rule condition is better suited to isolating the latter, but remains post hoc and peripheral.

**Revision:** Center the paper on the three image tasks and donor-test validation. Compress the chain motivation and secondary outcomes. If TCM stays prominent, foreground the explicit-rule experiment and report its numerical results directly.

**Presentation and reproducibility**

The main text ends on page 8, consistent with the stated long-paper length. The inspected layout is generally clean, although Table 3 and Figure 3 are dense. [NAACL submission details](<https://2027.naacl.org/calls/main_conference_papers/>)

More important than cosmetic changes:

- Move the donor-test assumptions and a compact validation table into the main paper. Essential methodological justification should be self-contained. [ARR author guidelines](<https://aclrollingreview.org/authors>)
- Simplify the AIA gate discussion. Its bootstrap/exact-test disagreement is disclosed, and no substantive conclusion depends on it; it currently receives disproportionate attention.
- Clarify the reproduction claim. The artifact README says some validation and robustness summaries enter the default reproduction workflow as precomputed inputs, with separate commands for additional analyses. Distinguish regenerating tables from recomputing every supporting analysis.

**What would change my recommendation**

For a stronger Findings recommendation, I would prioritize three changes: justify the donor test’s assumptions, tighten the interpretation of majority baselines and nonsignificant results, and bring the methodological validation into the main text.

For a main-conference recommendation, I would additionally want a compelling demonstration that this protocol reliably distinguishes behaviors that simpler established diagnostics cannot distinguish.

**The paper’s strongest publishable claim is that large ablation gains can leave correct image-conditioned behavior unestablished.** Organizing the submission around that claim would make its contribution clearer and more defensible.


---

**Final decision: Borderline Findings (2.5/5); not recommended for NAACL main conference in its current form.**

Excluding clinical review, the paper offers useful insights and careful controls. However, the donor-permutation assumptions need stronger justification, the methodological novelty needs clearer demonstration, and some conclusions exceed what the statistical evidence establishes.

I recommend revision before submission.