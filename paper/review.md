# Senior-reviewer review — status tracker

Original full review text (unedited) is preserved in git history and in
`paper/update.md`'s 2026-09-23 "(later still x6)" entry. This file re-groups the same
findings by fix status instead of the reviewer's original section order, so it's easy
to see what's actually resolved. Recommendation on the original: **reject in current
form, encouraged to substantially revise.**

Reviewer's own numbering (1-8 + the internal-inconsistency table + presentation) is
kept in parentheses after each item for cross-reference.

---

## Done

- **Counterfactual-image substitution experiment** (finding 3/7, the 4th and strongest
  grounding check) — all 4 `lumicf_*` jobs completed cleanly. Compiled with the new
  `tools/compile_lumiere_counterfactual.py`: flip rate on LIL/DSCR (6-42%) exceeds the
  AIA no-image-dependency baseline (10-17%) for 3/4 models, but among flips, the
  truth-tracking rate (does the new answer match the substituted patient's actual
  facts) is 35.6% pooled (26/73, 95% CI [25.6, 47.1]) — entirely below the 50% chance
  rate. Written into §8 as its own paragraph, plus an honest update to the
  pre-registration reading: 2 of 3 pre-registered conditions met cleanly, the 3rd
  (flip-rate magnitude) only partly matches "low" as originally worded — flagged
  explicitly rather than asserted as satisfied. Abstract, §8 intro, and Limitations
  updated to match (no more "provisional"/"3 of 4 checks" language).

---

## In progress

- **Gating-causality experiments** (finding 2). Downstream accuracy (LIL, DSCR, PJRF,
  TCM) evaluated under 3 manufactured upstream-context conditions — correct, incorrect
  (fixed wrong option per upstream phase), absent — holding image/question/options
  fixed. Code written and validated (`src/gating_causality.py`,
  `run_lumiere_gating_causality.py`, `shell/lumiere/lumiere_gating_causality.sbatch`);
  context-construction logic dry-run-checked against real Patient-002 v3 data with no
  API calls, matched expected letters exactly. **Now queued on HiPerGator**, all 4
  models, chained sequentially behind the `lumicf_*` counterfactual jobs to respect the
  2-GPU cap: `lumigc_MedGemma-4B` (43061666) → `lumigc_Gemma-3-12B` (43061678) →
  `lumigc_Gemma-3-27B` (43061679) → `lumigc_Llama-4-Scout` (43061683), each
  `--dependency=afterany` on the previous.

---

## Blocked

Needs something outside what we can resolve from the cluster/codebase alone.

- **Independent clinical validation of answerability** (finding 5). Needs an external
  clinician to confirm each question is answerable from exactly the rendered
  images/text shown to the model, and to review distractor quality and label validity
  (options-only / longest-option / majority-class / no-chain-context baselines can be
  added without them, but the core answerability check can't). Same external-reviewer
  bottleneck as the LUMIERE expert-review pass — see
  `project_omnibrain_lumiere_build` memory, unresolved as of 2026-08-27.

- **Evidence-audit reliability validation** (finding 4). Needs expert-reviewed examples
  to validate the copied-vs-independently-supported classification and report
  annotation agreement — same external clinical reviewer dependency as above. (The
  audit's mechanism is now documented, Done above; its *reliability* is still
  unvalidated.)

- **Adversarial validation examples for the renamed metrics** (finding 1, the
  validation half). Needs constructed test cases (right vocab/wrong patient, negated
  findings, answer repetition, valid paraphrase) checked against independent expert
  judgment — depends on the same reviewer.

- **Whether to reframe the paper around continuity/leakage/image-dependence** (the
  reviewer's overall suggested revision strategy, de-emphasizing KAB metrics as
  "exploratory, unvalidated" until the above is resolved). User deferred this as a
  separate discussion, likely with Prof. Wang, rather than deciding it in this session.

---

## TODO

- [ ] Watch the queued gating-causality jobs (`lumigc_*`, 4 models) to completion;
      compile results (`summarize()` in `src/gating_causality.py`) and write up the
      correct/incorrect/absent accuracy comparison once all four finish.
- [ ] Line up an external clinical reviewer (same bottleneck as the LUMIERE
      expert-review pass) — needed for: independent answerability validation,
      evidence-audit reliability validation, and adversarial metric-validation
      examples.
- [ ] Decide with Prof. Wang whether to reframe the paper around
      continuity/leakage/image-dependence as the central contribution, demoting KAB
      metrics to exploratory/unvalidated in the meantime.
