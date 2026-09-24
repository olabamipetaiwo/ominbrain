# Review status

Status tracker for the round-2 reviewer's findings and the work that follows from them. Updated 2026-09-24.
Detail, numbers and history live in `paper/update.md` (entries "x12" to "x17"). The reviewer's full text is not kept
here any more; it is in git at commit `6e776ff` (`git show 6e776ff:paper/review.md`). Finding numbers below are the reviewer's.

---

## Direction

**Decided 2026-09-23 (Prof. Wang): reframe the paper around shortcut learning.** Working claim: on these chain-structured brain-MRI
MCQs, accuracy is largely explained by question text, option artifacts and upstream-label lookup, so it is weak evidence of image-grounded
or causal reasoning. Not claimed: that models never use the image, or that errors propagate across phases. Exploratory (unreviewed items).
All runs below finished 2026-09-24; results compiled. The LaTeX text was rewritten around this direction 2026-09-24 (recompile and page-fit check are the user's).

Venue: NAACL 2027 via ARR. **ARR deadline 2026-10-12** (AoE), commitment 2026-12-23, conference 2027-06-01 to 06-05 (San Francisco).
Long paper: 8 pages (9 camera-ready). Shared ARR cycle with COLING 2027.

---

## Findings from the reviewer: where each stands

| # | Finding | Status |
|---|---|---|
| 1 | Images may not contain enough information (single slice; RANO needs more than two images) | **Open, limitation.** Disclosed in Sec. 6 and Limitations. No fix planned (needs the clinician review, deferred). |
| 2 | Continuity is not a causal chain | **Addressed.** Reworded as "sequential evaluation" and "hard gating". Correct/wrong/absent intervention run (4 models): only TCM depends on context, and the DSCR entry alone carries it for the three larger models (ablation); correct DSCR context hurts DSCR for three models. MedGemma-4B is the exception (no DSCR-only effect). See `results/lumiere_gating_stats.md`, `results/lumiere_tcm_lookup.md`. |
| 3 | Prognosis/TCM answer key confuses outcome with a unique prediction | **Open, limitation.** Text rewritten (48-week survival vs week-47 imaging). Redesign needs a clinician, deferred. |
| 4 | Substitution "below chance" is invalid | **Fixed in analysis, paper text stale.** Item-specific null (+11.9pp) is superseded by the donor-permutation test: 32/95 vs permutation mean 32.4, p = .64, no evidence of grounding (LIL permutation is degenerate by pairing design; DSCR informative). Repeated-run control: 260/260 identical answers in all 4 models (noise floor 0). |
| 5 | Evidence auditor cannot show claims were not visually verified | **Partly addressed.** Two-dimension audit done; "no checkable claim" reported separately (26-55%). Independent expert validation not done (limitation). |
| 6 | OmniBrainBench attribution | **Done.** Framed as an incompatibility with our sequential evaluation; "2 verifiable cross-phase links". |
| 7 | Framework not supported by the experiments | **Addressed by the reframe.** Adaptation and gating flagged exploratory; measures named "vocabulary and consistency". KAB becomes supporting, not the headline. |

Reporting corrections: all done and in the paper (MedGemma -1.9pp on the per-question basis, Gemma-27B 53.5/50.4 rounding, paired CIs, "prespecified
analysis plan" with the +-8pp margin disclosed as post hoc, per-phase forest plot, "zero violations = compliance with the auditor", regenerated vs frozen
upstream context, hard gating = masking). Also done: abstract cut to ~140 words, dataset-debugging history moved to Appendix B, body fits 8 pages.
Not done by choice: adding the proprietary models (GPT-5, Claude, Gemini); the reviewer said it would not fix the validity concerns.

---

## Runs

All finished 2026-09-24 (`sacct`: COMPLETED, exit 0; last was `lumiopt_Llama-4-Scout` 43121096). Compiled by `python -m tools.lumiere_gating_stats`
(and `python -m tools.lumiere_tcm_lookup`). Nothing in the primary experiment set is pending.

| Experiment | MedGemma-4B | Gemma-3-12B | Gemma-3-27B | Llama-4-Scout |
|---|---|---|---|---|
| Repeated identical input (rep2) | done | done | done | done |
| Gating-causality (correct/wrong/absent) | done | done | done | done |
| TCM ablation (`incl-DSCR`, `excl-DSCR`) | done | done | done | done |
| LLM options-only baseline | done, **parse-failure contaminated** (DSCR 52/52) | done | done | done (DSCR 7/52 unparsed) |

**One diagnostic job:** `lumiodiag_MedGemma-4B` 43170217 (options-only rerun, same decoding, raw responses saved to
`results/lumiere_optionsonly_diag_MedGemma-4B_*`). Purpose: find why MedGemma's options-only DSCR fails 52/52. Until it reports, MedGemma's
options-only cells are flagged, not interpreted (see `paper/update.md`, 2026-09-24).

---

## Key numbers so far (v3, 52 patients, open-weight models)

- Text-only vs image-present: within about +-8pp overall; no per-phase cell entirely above 0.
- Substitution: 32/95 flips match the donor label; permutation mean 32.4 (p = .64). 67.8% of LIL flips land on the patient's own direction.
- Repeated runs: identical answers for all four models (noise floor 0).
- Gating-causality TCM (correct / wrong / absent, %): MedGemma 33/15/25, Gemma-12B 62/27/19, Gemma-27B 64/25/33, Scout 60/42/33. LIL and PJRF flat. DSCR: correct context hurts for Gemma-12B (50/65/65, p = .008), Gemma-27B and Scout (correct - absent -17pp p = .012, -13.5pp p = .039); all uncorrected.
- TCM ablation: DSCR entry alone reproduces the correct-vs-wrong gap for Gemma-12B (+15pp), Gemma-27B (+27pp), Scout (+27pp); without DSCR it does not (all CIs include 0). MedGemma-4B: no DSCR-only effect.
- TCM key follows the DSCR key's class for 50/52 patients (`tools/lumiere_tcm_lookup.py`; class unique among the options in only 18/52). TCM correct given own DSCR correct vs wrong: Gemma-12B 17/29 vs 3/23, Gemma-27B 26/34 vs 5/18, Scout 18/30 vs 1/22 (descriptive, confounded).
- Options-only (chance 25): MedGemma cells flagged (parse failures 52/52 DSCR, 18-21/52 AIA/PJRF/TCM); Gemma-12B 38/33/40/23/12, Gemma-27B 62/36/44/25/12, Scout 44/36/19/21/19 (AIA/LIL/DSCR/PJRF/TCM). AIA has one fixed answer string, so its above-chance rate is not a shortcut signal.
- Longest-option baseline: 67% on DSCR, above every model. AIA has one fixed answer string.

---

## TODO

**When all the jobs above finish**
- [x] Check every job exited 0 (`sacct`), then `python -m tools.lumiere_gating_stats` (repeated-run, gating-causality, TCM ablation, options-only, all four models). Done 2026-09-24.
- [x] Read the four-model results; decide what the shortcut story says. Done 2026-09-24: TCM is largely a lookup of the upstream DSCR label; options-only vs own-image is confounded by the model's own chain (own-image carries its earlier answers), so the like-for-like comparator is the no-chain 'absent' condition.

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
