# Review status

Status tracker for the round-2 reviewer's findings and the work that follows from them. Updated 2026-09-23 (evening).
Detail, numbers and history live in `paper/update.md` (entries "x12" to "x17"). The reviewer's full text is not kept
here any more; it is in git at commit `6e776ff` (`git show 6e776ff:paper/review.md`). Finding numbers below are the reviewer's.

---

## Direction

**Decided 2026-09-23 (Prof. Wang): reframe the paper around shortcut learning.** Working claim: on these chain-structured brain-MRI
MCQs, accuracy is largely explained by question text, option artifacts and upstream-label lookup, so it is weak evidence of image-grounded
or causal reasoning. Not claimed: that models never use the image, or that errors propagate across phases. Exploratory (unreviewed items).
The paper text has NOT been rewritten yet; it is waiting for the runs below.

Venue: NAACL 2027 via ARR. **ARR deadline 2026-10-12** (AoE), commitment 2026-12-23, conference 2027-06-01 to 06-05 (San Francisco).
Long paper: 8 pages (9 camera-ready). Shared ARR cycle with COLING 2027.

---

## Findings from the reviewer: where each stands

| # | Finding | Status |
|---|---|---|
| 1 | Images may not contain enough information (single slice; RANO needs more than two images) | **Open, limitation.** Disclosed in Sec. 6 and Limitations. No fix planned (needs the clinician review, deferred). |
| 2 | Continuity is not a causal chain | **Mostly addressed.** Reworded as "sequential evaluation" and "hard gating". Correct/wrong/absent intervention run: only TCM depends on context (MedGemma-4B, Gemma-3-12B compiled; 27B and Scout still running). TCM ablation queued. |
| 3 | Prognosis/TCM answer key confuses outcome with a unique prediction | **Open, limitation.** Text rewritten (48-week survival vs week-47 imaging). Redesign needs a clinician, deferred. |
| 4 | Substitution "below chance" is invalid | **Fixed in analysis, paper text stale.** Item-specific null (+11.9pp) is superseded by the donor-permutation test: 32/95 vs permutation mean 32.4, p = .64, no evidence of grounding (LIL permutation is degenerate by pairing design; DSCR informative). Repeated-run control: 260/260 identical answers in 2 of 4 models (27B compile pending, Scout running). |
| 5 | Evidence auditor cannot show claims were not visually verified | **Partly addressed.** Two-dimension audit done; "no checkable claim" reported separately (26-55%). Independent expert validation not done (limitation). |
| 6 | OmniBrainBench attribution | **Done.** Framed as an incompatibility with our sequential evaluation; "2 verifiable cross-phase links". |
| 7 | Framework not supported by the experiments | **Addressed by the reframe.** Adaptation and gating flagged exploratory; measures named "vocabulary and consistency". KAB becomes supporting, not the headline. |

Reporting corrections: all done and in the paper (MedGemma -1.9pp on the per-question basis, Gemma-27B 53.5/50.4 rounding, paired CIs, "prespecified
analysis plan" with the +-8pp margin disclosed as post hoc, per-phase forest plot, "zero violations = compliance with the auditor", regenerated vs frozen
upstream context, hard gating = masking). Also done: abstract cut to ~140 words, dataset-debugging history moved to Appendix B, body fits 8 pages.
Not done by choice: adding the proprietary models (GPT-5, Claude, Gemini); the reviewer said it would not fix the validity concerns.

---

## Runs (GPU cap raised 2 -> 4 for exactly these jobs, per the professor; back to 2 afterwards)

Status at last check: 4 running, 7 pending. Each pending job is chained behind another chain's last job, so never more than 4 GPUs.

| Experiment | MedGemma-4B | Gemma-3-12B | Gemma-3-27B | Llama-4-Scout |
|---|---|---|---|---|
| Repeated identical input (rep2) | done | done | done, not compiled | running (43091110) |
| Gating-causality (correct/wrong/absent) | done | done | running (43061679) | pending (43061683) |
| TCM ablation (`incl-DSCR`, `excl-DSCR`) | running (43118917) | running (43118918) | pending (43119393) | pending (43119394) |
| LLM options-only baseline | pending (43121093) | pending (43121094) | pending (43121095) | pending (43121096) |

Not GPU-tested: `run_lumiere_options_only.py` (prompt checked on a real patient, no model call). Check the first `lumiopt_*` log when it starts.
Everything else the paper reports (own-image, text-only, counterfactual images, all v3) is finished for all four models.

---

## Key numbers so far (v3, 52 patients, open-weight models)

- Text-only vs image-present: within about +-8pp overall; no per-phase cell entirely above 0.
- Substitution: 32/95 flips match the donor label; permutation mean 32.4 (p = .64). 67.8% of LIL flips land on the patient's own direction.
- Repeated runs: identical answers (noise floor 0), MedGemma-4B and Gemma-3-12B.
- Gating-causality (correct / wrong / absent, %): TCM MedGemma 33/15/25, Gemma-12B 62/27/19; LIL and PJRF flat; Gemma-12B DSCR 50/65/65 (correct context hurts, p = .008, uncorrected).
- TCM key follows the DSCR key's action class for 48/52 patients (keyword classifier, ad hoc); Gemma-12B follows the injected DSCR label, MedGemma-4B does not.
- Longest-option baseline: 67% on DSCR, above every model. AIA has one fixed answer string.

---

## TODO

**When all the jobs above finish**
- [ ] Check every job exited 0 (`sacct`), then `python -m tools.lumiere_gating_stats` (repeated-run, gating-causality, TCM ablation, options-only, all four models).
- [ ] Read the four-model results; decide what the shortcut story says (does `incl-DSCR`/`excl-DSCR` explain TCM; how high is options-only vs own-image).

**Then rewrite the paper around shortcut learning**
- [ ] Title, abstract, contributions, intro, Sec. 8. Lead evidence: text-only, substitution (permutation), gating-causality, TCM ablation, options-only.
- [ ] Replace the stale substitution sentence ("modest image sensitivity", +11.9pp over item-specific chance) with the permutation result.
- [ ] Rewrite the flip-rate paragraphs against the repeated-run baseline; drop "queued" language.
- [ ] Write up gating-causality and the TCM lookup finding, with the Gemma-12B DSCR reversal and its caveats (uncorrected p; anchoring is a hypothesis).
- [ ] Limitations: clinician review deferred (unreviewed LLM-drafted items and keys), single-slice answerability, PJRF/TCM key definition, unreviewed distractors, uncorrected multiplicity, four open models only, wrong-context condition is one fixed choice.
- [ ] Recompile LaTeX (`/apps/texlive/2023/bin/x86_64-linux` on PATH), confirm the body fits 8 pages and no undefined refs.

**Optional**
- [ ] Randomised or per-label wrong-context variant of gating-causality (code change + GPU).
- [ ] Replace the regex action-class classifier in the TCM analysis with a reproducible tool.

**Deferred, listed as limitations rather than fixed**
- Clinician review of the v3 items; answerability fix for LIL/DSCR; PJRF/TCM scoring redesign.
