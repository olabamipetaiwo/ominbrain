# Recommendations for addressing review_round2.md

From a senior applied-research perspective, **repair the measurement argument before adding more models or experiments.** The paper has a defensible contribution, but currently asks the evidence to support too strong a conclusion.


## 1. Make the central claim narrower and consistent

Build the paper around:

> Image-ablation gains alone do not establish correct visual tracking. Our controls distinguish accuracy improvement, answer changes, and evidence of donor-specific correctness.

For the evaluated open models, say **“we did not establish donor-specific tracking.”** Remove claims that tracking is absent, that low power has been excluded, or that the models behave like the generic predictor.

This preserves the contribution without requiring proof of a negative. Apply the same interpretation to the abstract, Figure 3, Results, Appendix D, and Conclusion.

## 2. Repair the two concrete implementation problems first

For donor reassignment:

- Preserve the actual constraints: different key, matching image count, and at most two recipients per donor.
- Remove the silent fallback. An unsuccessful assignment must be reported as a failure.
- Save each assignment and report how many distinct assignments were actually evaluated.
- Include the noisy tracker in assignment-stability experiments.

For TCM, define eligibility using the **baseline answer alone**, before examining the flipped answer. Then regenerate the transition tables.

These are essential corrections. Editing the prose alone will not resolve them.

## 3. Decide exactly what the permutation test is testing

This is the most important methodological decision.

A test of association between answers and donor labels is not automatically a test based on the original randomized image assignment. Choose an interpretation, specify its assumptions, and make the sampler match it.

If the intended test is assignment-based, the reference distribution must respect the assignment mechanism and eligibility constraints. Randomly repairing invalid label permutations is not sufficient justification.

Ask a statistically experienced collaborator to review this component independently before investing in more inference runs. The headline interpretation depends on it.

## 4. Turn the synthetic experiment into a measurement-validation study

Keep the existing controls, but expand them purposefully:

| Question | Additional check |
|---|---|
| Does the test incorrectly detect tracking? | No-tracking predictors influenced by option position, image count, and class preferences |
| Can it detect weak tracking? | A range of tracking strengths, including substantially weaker alternatives |
| Does performance depend on the mechanism? | Class-specific tracking and correlated errors for reused donors |
| Is the result assignment-sensitive? | Multiple genuinely distinct valid assignments |
| How uncertain are detection rates? | Report uncertainty around simulation detection rates |

Separate **false-positive calibration**, **power**, and **assignment stability**. They answer different questions.

Explain that the current `rho = 0.4` predictor has **55% expected donor-answer accuracy**, because its random-guess branch can also be correct: `0.4 + 0.6 / 4 = 0.55`.

## 5. Add one focused real-model robustness experiment, if resources permit

After fixing the analysis, rerun donor swaps under several valid assignments for:

- Llama-4-Scout on DSCR, the central worked example.
- The reference model on AIA/LIL, the positive demonstration.

This would test robustness of the actual empirical finding. Synthetic reassignment alone cannot establish that real-model responses are stable across different donor images.

Prioritize this over expanding the model roster.

## 6. Simplify the paper's structure and inference rules

Treat AIA as a diagnostic positive control, not a universal prerequisite for interpreting other tasks. Preserve the original analysis plan, but distinguish its historical rule from the revised interpretation.

Make AIA/LIL/DSCR the main story. Keep TCM as a compact extension and move most chain, survival, and compatibility detail to the appendix. Use the recovered space for the estimator and validation, while bringing the conclusion within the applicable page limit.

## 7. Finish with a reproducibility audit

Generate every table from one frozen analysis output. Include sample sizes, relevant counts, exclusions, both precision controls, and the corrected transition results. Reconcile every caption and prompt description.

## Submission threshold

Correct implementation, a justified permutation test, calibrated synthetic validation, and consistently qualified claims would materially strengthen the paper. Clinician validation and broader generalization would remain separate limitations.
