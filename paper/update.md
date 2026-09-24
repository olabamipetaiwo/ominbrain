#Project Update

## 2026-09-24 — all queued control jobs finished (exit 0); four-model `lumiere_gating_stats` compiled; first read of the shortcut evidence

**Jobs.** `sacct` shows every `lumirep_*`, `lumigc_*`, `lumigcabl_*`, `lumiopt_*` job COMPLETED, exit 0; last was `lumiopt_Llama-4-Scout`
43121096 (ended 2026-09-24 03:18). Queue empty, so the GPU cap (4 for these experiments) is moot; standing cap is back to 2.
Ran `python -m tools.lumiere_gating_stats` on the login node (CPU only) -> `results/lumiere_gating_stats.{md,json}`; all four models
(MedGemma-4B, Gemma-3-12B, Gemma-3-27B, Llama-4-Scout) in every section. Numbers below are from that file; all p-values are exact
McNemar, UNCORRECTED, n = 52 patients per cell. Nothing here is committed yet. This is a first read, not yet in the paper.

**1. Repeated-run control (all 4 models):** 260/260 identical answers and identical correctness, 0 flips in every phase. Noise floor is 0
(deterministic decoding). Still does not bound sensitivity to small input perturbations.

**2. Gating-causality (correct / forced-wrong / absent upstream context):**
- **TCM: correct context beats forced-wrong for all four models**, +17.3pp (MedGemma, p=.004), +34.6 (Gemma-12B), +38.5 (Gemma-27B), +17.3
  (Scout, p=.004). Correct beats absent by +7.7 (MedGemma, p=.22, not significant), +42.3, +30.8, +26.9.
- **DSCR: correct context hurts** for three models: Gemma-12B 50.0 vs 65.4 (incorrect and absent; p=.008 / .021), Gemma-27B correct-absent
  -17.3pp (p=.012; correct-incorrect -9.6, p=.125), Scout correct-absent -13.5pp (p=.039; correct-incorrect -11.5, p=.070). MedGemma: no
  detectable effect. Anchoring on the injected label is still a hypothesis, untested.
- LIL and PJRF: flat for every model (no paired contrast with p < .2).

**3. TCM ablation (which upstream entry carries the effect):**
- DSCR entry alone reproduces the effect for Gemma-12B (+15.4pp correct-incorrect, p=.021), Gemma-27B (+26.9, p=.001) and Scout (+26.9, p<.001).
- Everything except DSCR (AIA+LIL+PJRF) does not: +1.9 / +5.8 / +3.8, all CIs include 0.
- **MedGemma-4B is the exception:** full context gives +17.3 but DSCR-only gives +1.9 (p=1.0) and no-DSCR -3.8. Its gap is unexplained (same as
  the x14 note). PJRF (which carries the true survival estimate) is not an alternative route for the three larger models.
- Reading: TCM accuracy in the larger models is largely a lookup of the upstream DSCR label. Consistent with the x14 keyword check (DSCR key
  predicts TCM key class for 48/52). By construction of the TCM prompt, so it is not evidence of multi-phase reasoning.

**4. Options-only baseline (no image, no stem, no chain; four options only):**
- Options-only accuracy (%): MedGemma AIA/LIL/DSCR/PJRF/TCM 40/29/0/14/15; Gemma-12B 38/33/40/23/12; Gemma-27B 62/36/44/25/12;
  Scout 44/36/19/21/19 (chance 25).
- **MedGemma-4B options-only is contaminated by parse failures**: DSCR 52/52, TCM 21, AIA 19, PJRF 18. Its DSCR 0% is a format failure, not a
  score; those cells must be flagged or excluded. Scout has 7 DSCR parse errors; the Gemma models have 0.
- **AIA is not a clean shortcut cell**: it has one fixed answer string (non-LLM "majority text" = 100%). Options-only AIA above chance (Gemma-27B
  62%) is therefore weak evidence; do not headline it.
- DSCR: non-LLM majority-text baseline is 63.5%, above every options-only score and above most own-image scores. LIL/PJRF/TCM majority = 1.9%.
- **Own-image minus options-only (paired):** LIL is at or below zero for the 12B (-9.6), 27B (-9.6), Scout (-11.5), all n.s.; MedGemma +11.5 n.s. -> no
  detectable image benefit on LIL. TCM is large: +26.9 (12B, p=.003), +48.1 (27B, p<.001), +17.3 (Scout, p=.035), +11.5 (MedGemma, n.s.). DSCR:
  +21.2 (27B, p=.043), +38.5 (Scout, p<.001), +15.4 (12B, n.s.).
  **Caveat (checked, see "Own-image run contents" below):** "own-image" is the v3 `nogate` run, which carries the model's OWN earlier answers as chain
  context, and options-only also drops the stem. The TCM Delta is therefore image + stem + own upstream answers versus none of them; it is NOT an image
  effect.

**Own-image run contents (code read + CPU check, 2026-09-24).** `results/lumiere_<model>_v3_nogate_*` = `run_lumiere.py` with gating OFF and adaptation
ON, image(s) present. In `src/evaluator.py::evaluate_case`, `chain_context` is appended after every question with the model's own answer, its answer
text and its visual-grounding note; `src/prompts.py::build_main_prompt` renders it as a "PRIOR REASONING CHAIN" block in every later phase. So each phase
sees the model's own answers to ALL earlier phases (not gold, not forced-wrong); gating-causality's "correct" condition injects gold instead, and
"absent" empties the list (image, stem and options kept). Consequence for §4 above: the "no-chain ctx" column (gating `absent`) is the right
image-and-stem-without-chain comparator for LIL-TCM; own-image minus no-chain ctx isolates the effect of the model's own chain.
Supporting check (own-image run, TCM accuracy split by whether the model's own DSCR answer was correct; n=52 per model, descriptive, no test, and
confounded because patients the model gets right on DSCR may be easier throughout):
MedGemma-4B 4/8 vs 10/44; Gemma-12B 17/29 vs 3/23; Gemma-27B 26/34 vs 5/18; Scout 18/30 vs 1/22 (TCM correct | DSCR correct vs | DSCR wrong).
Reading: for the three larger models TCM correctness follows the model's own DSCR correctness; consistent with the DSCR-lookup account from
gating-causality/ablation, and with why own-image TCM (59.6% for Gemma-27B) sits near the gold-context 63.5% and far above the absent 32.7%.
Not established: the direction (does a correct DSCR answer cause a correct TCM answer, or do both reflect item difficulty).

**Corrections to my own earlier same-day status message (not to any file):** I first read the raw `lumiopt_*` job summaries as "options-only well above
chance supports shortcut learning". After compile: AIA is a fixed-string cell, MedGemma DSCR is a parse failure, and DSCR options-only sits below the
63.5% label prior.

**Not done / next:** (a) DONE, see above (own-image carries the model's own earlier answers); (b) decide how MedGemma's parse-failed options-only cells are
reported (flag vs exclude; earlier MedGemma parse-failure decision applies); (c) tick the first two `paper/review.md` TODO items when the read is
agreed; (d) then the paper rewrite (title, abstract, contributions, Sec. 1/8) and the stale substitution sentence.

## 2026-09-23 (later still x17) — donor-permutation test done (substitution result weakens again); options-only compile section written; clinician review deferred; NAACL dates confirmed

**Donor-permutation test** (`tools/lumiere_reviewer_stats.py::donor_permutation_test`, 20,000 replicates, seed 20260924; results in
`results/lumiere_reviewer_stats.{md,json}`). Each patient's donor is redrawn uniformly from the opposite-LIL-direction side (the pairing rule), the
observed flipped answers are held fixed, truth-tracking is recounted; one donor per patient is shared by all models/phases, so shared-patient
dependence and donor reuse are respected. Result: observed 32/95 tracks the donor's label, permutation mean **32.4** (95% range 27-37), one-sided
p = **0.64**. LIL 18/59 vs 17.4 (p .56); DSCR 14/36 vs 15.0 (p .73). **Reading: which donor's image was shown does not matter beyond what the
label base rates predict.** This contradicts the "+11.9pp above item-specific chance" reading from x12: the item-specific null (flip drawn
uniformly among the item's other options) ignores that models' answers are skewed toward common labels (e.g. PD ~70% of DSCR keys), so it under-
states chance. Caveat: the pairing rule fixes every donor's LIL direction to the opposite of the patient's, so the LIL permutation is degenerate
(p ~ 0.5 by construction); only DSCR is informative about donor-specificity. **Substitution now gives no evidence of image grounding**; the paper's
"modest image sensitivity" sentence (Sec. 8) is not supported and must be rewritten in the reframe. Also still true: 67.8% of LIL flips land on the
patient's OWN direction, i.e. away from the substituted image.

**Options-only compile section** written (`tools/lumiere_gating_stats.py` section 4): per model x phase options-only accuracy [Wilson], the
no-chain-context baseline (gating 'absent' condition; own-image for AIA), own-image accuracy, paired own - options-only difference with patient
bootstrap CI and exact McNemar p; non-LLM reference rows (chance, majority text). Tested on SYNTHETIC results (fake dirs, deleted afterwards) - the
code path works; no real options-only result exists yet (`lumiopt_*` still queued). Real numbers appear when the jobs finish.

**Clinician review deferred (decision, user 2026-09-23):** will not be arranged for this submission; listed as a limitation of the paper (unreviewed,
LLM-drafted items and answer keys; answerability from single slices unvalidated). Consequence: the v3 results are final as-is, no re-run after review.

**NAACL 2027 (re-checked 2026-09-23):** ARR deadline **October 12, 2026** (AoE), commitment December 23, 2026, conference June 1-5, 2027, San Francisco;
long papers 8 pages (9 camera-ready), short 4 (5). Shared ARR cycle with COLING 2027. References/limitations/appendices treatment not stated on the page.
19 days from today to the ARR deadline.

## 2026-09-23 (later still x16) — DECISION: professor approved reframing the paper around shortcut learning

User relayed Prof. Wang's feedback: reframe around "shortcut learning". This closes the "Reframe around continuity/leakage/image-dependence"
item in `paper/review.md` (Blocked list). Working claim: on these chain-structured brain-MRI MCQs, accuracy is largely explained by
non-image, non-chain information (question text, option artifacts, upstream-label lookup), so it is weak evidence of image-grounded or
causal reasoning. Not claimed: that models never use the image, or that errors propagate across phases. Exploratory (unreviewed items).
Paper NOT yet rewritten (title, abstract, contributions, Sec. 1/8 still describe the causal-degradation framing).

## 2026-09-23 (later still x15) — LLM options-only baseline built and queued; compile tool guarded

`run_lumiere_options_only.py` + `shell/lumiere/lumiere_options_only.sbatch` (review.md TODO, reviewer item 9). Each of the 5 phase
questions per patient is asked with NO image, NO question stem (fixed placeholder), NO chain context; only the four options,
the phase header and the standard answer-format instructions (which still mention "visual features", same as the existing
text-only ablation). Reuses `_evaluate_question` unmodified (text_only=True, adaptation off). 4 models x 5 phases x 52 patients,
one call each; results -> `results/lumiere_optionsonly_<model>_<ts>/`. The no-chain-context baseline needs no new run: it is the
"absent" condition of gating-causality (LIL-TCM) plus the own-image v3 run for AIA. Prompt checked on a real patient (no patient id or
stem leaks). Jobs, each chained behind the tail of a different existing chain so no 5th concurrent GPU (cap-4 exception): 
`lumiopt_MedGemma-4B` 43121093 (afterany 43119393), `lumiopt_Gemma-3-12B` 43121094 (afterany 43119394),
`lumiopt_Gemma-3-27B` 43121095 (afterany 43091110), `lumiopt_Llama-4-Scout` 43121096 (afterany 43061683).
NOT yet compiled (needs a section in `tools/lumiere_gating_stats.py`); not smoke-tested on a GPU node before queuing.
Latent bug fixed: `tools/compile_lumiere_results.py`'s `RUN_RE` matched `lumiere_gatingcausality_*` / `lumiere_gcablate_*` folders as
if they were model runs and would have crashed on their raw_results shape (no overall_score); they are now excluded (`NOT_CHAIN_RUNS`).
Not re-run since.

## 2026-09-23 (later still x14) — analysis: first pass at the TCM-leakage question (CPU only, ad hoc, not yet a tool)

The TCM drafter prompt (`src/lumiere_prompts.py`) says the correct management "follows from this patient's actual disease
course" and the quiz-taker "must work out the disease state from their own earlier answers", so TCM is a function of the
upstream DSCR label by construction. Checked with a keyword classifier on the correct TCM option (escalate / continue /
stop; approximate, regex-based): the DSCR key predicts the TCM key's action class for **48/52** patients (PD -> escalate
31/35, SD/PR/CR -> continue 17/17). But the key's class is unique among the 4 options in only **22/52** items, so the label
alone does not fix the letter in the other 30.
Gemma-12B follows the injected label: on the 35 PD-keyed patients it picks an escalate-class option 25/35 with correct
context, 15/35 with the forced-wrong DSCR label ("Stable disease"), 13 absent. MedGemma-4B does NOT (8/35 and 8/35,
mostly picks "continue" whatever the context), yet its correct-vs-incorrect gap is 9 vs 0 discordant items - so its TCM
gap is not explained by the class shift and is unexplained. Reading: the TCM dependence is at least partly a label
lookup (intended by design, but then it is not evidence of multi-phase reasoning). Still to do: GPU ablation with only the
DSCR entry vs everything-except-DSCR in the injected context; a proper tool replacing the regex classifier.

**Built and queued the ablation (same day).** `src/gating_causality.py` / `run_lumiere_gating_causality.py` gained
`--conditions`, `--context-include`, `--context-exclude`, `--context-tag` (defaults reproduce the original experiment
exactly; ablation runs write to `results/lumiere_gcablate_<model>_<tag>_<ts>/`, a prefix the primary-run globs cannot
match; the CLI rejects an include-set that is not upstream of the queried phase, which would silently equal "absent").
New `shell/lumiere/lumiere_gating_ablation.sbatch`: per model, TCM only, correct/incorrect only, two variants -
`incl-DSCR` (context = the DSCR entry alone) and `excl-DSCR` (AIA + LIL + PJRF). Verified the built contexts on a real
patient before submitting. Jobs `lumigcabl_MedGemma-4B` 43118917 (afterany 43091110, the last `lumirep_*` job) ->
`lumigcabl_Gemma-3-12B` 43118918: still 2 concurrent GPUs at all times. `tools/lumiere_gating_stats.py` got section 3
(paired contrasts vs the primary run's full/absent conditions on the same patients); prints "not finished yet" until then.
Side finding while testing: the "correct" PJRF context entry contains the true survival estimate, so PJRF is a second
possible route into TCM besides DSCR; `excl-DSCR` tests it. Interpretation guide: incl-DSCR recovers the full effect ->
label lookup; excl-DSCR alone recovers it -> other phases (incl. PJRF); neither does -> the effect needs the combination.
**GPU cap raised 2 -> 4 for these listed experiments only (user relayed professor's OK, 2026-09-23); back to 2 afterwards.** Chains re-cut into 4 independent slots: gc 43061679 -> 43061683; rep 43091109 -> 43091110; ablation 43118917 -> 43119393 (27B); 43118918 -> 43119394 (Scout) (the first two ablation jobs no longer wait on the rep chain, dependency cleared with `scontrol update`).
Extended to all four models (user go-ahead): `lumigcabl_Gemma-3-27B` 43119393 (afterany 43118918) -> `lumigcabl_Llama-4-Scout` 43119394; chain is 43091110 -> 43118917 -> 43118918 -> 43119393 -> 43119394, so still <= 2 concurrent GPUs.

## 2026-09-23 (later still x13) — code: `tools/lumiere_gating_stats.py` compiles the repeated-run and gating-causality results

CPU-only, re-runnable as jobs finish (skips models whose runs are missing/unfinished); writes
`results/lumiere_gating_stats.{md,json}`. Seed 20260923, 10,000 patient-level bootstrap resamples.
Covers MedGemma-4B and Gemma-3-12B so far; 27B and Llama-4-Scout still queued (`lumirep_*` / `lumigc_*`).

- **Repeated-run control:** 260/260 identical answers for both models (acc 34.2 / 48.1 in both runs, parse errors
  13/13 and 0/0). Decoding is deterministic, so the run-to-run noise floor is 0 and counterfactual flips come from the
  input. Does not bound sensitivity to tiny input perturbations.
- **Gating-causality, paired (item-level `correct`, exact McNemar, UNCORRECTED):** only TCM shows a clear
  context dependence, correct - incorrect +17.3pp [+7.7,+28.8] (MedGemma, p=.004) and +34.6pp [+21.2,+48.1] (Gemma-12B).
  LIL/PJRF: no detectable effect in either model. **Gemma-12B DSCR is significantly NEGATIVE**: correct context
  50.0% vs 65.4% for incorrect and for absent (-15.4pp [-25.0,-5.8] / [-26.9,-5.8], p=.008 / .021) - correct upstream
  context hurts. My earlier unpaired read said MedGemma's TCM CIs overlap; the paired test is significant.
- **Open caveats (not yet in the paper):** TCM's dependence may be leakage (true upstream answers may hand over the
  treatment answer) rather than reasoning; DSCR anchoring is a hypothesis, untested; 20+ uncorrected cells.

## 2026-09-23 (later still x12) — paper: acted on the round-2 review (items 1-12 of the action list); two headline results changed

User asked to execute action items 1-12 from `paper/review.md`'s "New Review". Everything below is from existing
results (no new model calls) except item 11, which is queued. New tool: `tools/lumiere_reviewer_stats.py`
(-> `results/lumiere_reviewer_stats.{md,json}`, CPU only, ~8 s, seed 20260923, 10,000 patient-level bootstrap resamples).

**Bugs / inaccuracies found in our own numbers while doing this (all fixed in the paper)**
1. *MedGemma "3pp vs 1.9pp".* The Table 1 numbers came from each run's `overall_score`, which comes from
   `src/evaluator.py`'s `phase_score` and **drops parse-error items from the denominator**; with one question per
   phase, a salvaged-correct answer scores 0. MedGemma had 13/9 parse errors (image/text-only), 3/1 of them
   salvaged-correct. The bootstrap used the per-question `correct` flag. The paper's own Failed-response paragraph says
   salvaged answers count, so the per-question basis is now used everywhere: MedGemma 34.2 / 36.2 (-1.9pp), not
   33 / 36. Other three models are unaffected. `evaluator.py` NOT changed (would alter gating); documented in Setup.
2. *Gemma-3-27B "54 vs 50 shown as 3pp".* 53.46 was double-rounded (53.5 -> 54). Correct 53.5 / 50.4 (+3.1).
3. *Truth-label extractor bug* (`tools/compile_lumiere_counterfactual.py::_direction_word`): it tested
   `"increase" in text`, missing "increasing"/"decreasing"/"stable"/"reduction" (the drafter's most common
   phrasings) and misreading options that mention the opposite word for a sub-compartment. 22 of 95 flipped
   LIL/DSCR answers were silently excluded (73 checkable). Rewrote it (total-volume clause first) and validated it
   against every patient's correct LIL option (52/52; the one exception is Patient-028, whose +0.3% change is worded
   "stable" although pairs.json says "up" - the truth label is now read from the item text, not the sign). Re-ran
   the compile tool; `results/lumiere_counterfactual_summary.json` regenerated.
4. *"Identical answer with and without image for 87-91% of items"* was wrong: 87-91% is same **correctness**;
   identical answer is 77-89% (MedGemma 89, Gemma-12B 77, Gemma-27B 80, Llama 83). Fixed.
5. *"v3 image accuracy is 13-19pp below v2"* is 9-18pp. Fixed (also noted the cohorts are 54 vs 52 patients).
6. *"Pre-specified +-8pp margin"* was not: `update.md` (item 7 of the earlier review round) shows the margin was
   chosen after computing the intervals. The paper now says so, and calls the 2026-09-22 log entry a "prespecified
   analysis plan", not a preregistration (log not externally timestamped; the plan itself used CI overlap).

**Result changes**
- *Substitution, item-specific null (item 7).* Old: 26/73 = 35.6% vs "50% chance" -> "entirely below chance".
  Now: 32/95 = 33.7% carry the donor's label; expected under a uniform choice among each item's other options =
  20.7/95 = 21.8%; excess +11.9pp (patient-clustered 95% CI [+3.5, +20.3], donor-clustered [+2.9, +20.7]).
  By phase LIL 18/59 (12.0 expected), DSCR 14/36 (8.7 expected). But 67.8% of LIL flips land on the ORIGINAL patient's
  own direction (DSCR 47.2%), 30.5% of flips keep the same label, and the donor's fully correct LIL option was among
  the options for 0/52 patients (label present 37/52; DSCR option 48/52, label 52/52). Paper conclusion is now
  weaker: modest image sensitivity, not shown to be grounding; the third pre-plan condition ("low, non-tracking")
  is NOT met and the paper says so. This reverses the earlier "below chance" claim.
- *Text-only, paired (item 6).* Overall image - text-only: MedGemma -1.9 [-5.8,+1.9], Gemma-12B -2.7 [-7.3,+2.3]
  (was [-7.7,...] in the paper; different bootstrap draw), Gemma-27B +3.1 [-0.8,+7.3], Llama -3.1 [-7.3,+1.2].
  Per phase (20 cells): none lies entirely above 0; MedGemma DSCR/PJRF and Llama TCM end at 0 on the text-only side;
  largest image advantage Gemma-27B AIA +9.6 [-1.9,+21.2] (b=8, c=3). Discordant items summed: 55 right-only-image vs
  67 right-only-text (matches the paper). New per-phase forest plot replaces the duplicated bar chart
  (old `text_only_ablation.pdf` and `make_textonly_chart.py` left in place, no longer included).
- *Evidence audit, two dimensions (item 8; `tools/audit_reasoning_facts.py`, now also emits the 2-D table).* On v3,
  answers with no checkable claim: 26-55% (MedGemma 35, Gemma-12B 31, Gemma-27B 55, Llama 26). Of claims (251-668
  per model): in shown text & matches record 75-87%; in shown text but contradicts/unmatched 10-18%; NOT in text &
  matches 1-2%; NOT in text & contradicts/unmatched 2-6%. The worked example (Patient-002, Gemma-27B) confirmed: LIL
  has 3 in-text-supported claims and 2 in-text-contradicted (the repeated "right temporal lobe"), so the carried-forward
  error is visible under the new scheme. Note `results/lumiere_reasoning_facts.{md,csv}` now also include the
  `_cf_v3` runs (the tool picks up every latest run).
- *Option-only baselines (item 9).* v3, n=52/phase: longest option AIA 37 / LIL 25 / DSCR 67 / PJRF 19 / TCM 6;
  letter-prior 31-37; stem-overlap 0-33 (AIA 0, LIL 33, DSCR 8, PJRF 29, TCM 17); AIA text-majority 100% (fixed
  answer string). DSCR longest = majority (67%), above every model. LLM options-only / no-chain-context baselines
  still need GPU runs.

**Paper edits (`paper/latex/acl_latex.tex`, `custom.bib` +`wen2010updated`)** - items 1-4, 10, 11 in the action list:
abstract/intro/contributions/Fig. 1/related work reworded ("sequential", "threshold gating" - it is hard gating,
"vocabulary and consistency", OmniBrainBench = incompatibility, "2 verifiable cross-phase links", adaptation/gating
flagged exploratory); Sec. 3.3 rewritten (blocking = masking because a queried phase's inputs don't depend on gating;
DSCR key independent of LIL baseline); Sec. 4 retitled and softened; Sec. 5 adds the RANO-inputs and single-slice
answerability caveats and "zero violations = compliance with the auditor"; Sec. 7 rewrites the evidence audit, adds
"regenerated not frozen upstream context", the analysis-plan disclosure, and paragraphs for the repeated-run control
and the gating-causality experiment (design only, `sec:gating-causality`); Sec. 8 has the new Table 1, Fig. 3,
Table 2 (flip rates with CIs), rewritten text-only / evidence / substitution / option-only / reading-vs-plan
paragraphs; Limitations gets a lead paragraph on answerability, the PJRF/TCM key definition, unreviewed distractors and
uncorrected multiplicity; Appendix PJRF/LIL paragraphs rewritten (48-week survival vs week-47 imaging). Compiled with
`/apps/texlive/2023/bin/x86_64-linux` on PATH (`module load` did not put pdflatex on PATH in this shell): full
pdflatex-bibtex-pdflatex-pdflatex cycle, 18 pages, no errors, no undefined refs, no overfull boxes (fixed two tables);
Table 1 / Fig. 3 / Table 2 pages rasterized and inspected.

**Item 11 (repeated identical-input control) - submitted.** `run_lumiere.py` got `--run-tag` (folder becomes
`lumiere_<model>_rep2_v3_nogate_*`, so it cannot be picked up as the primary run). Jobs `lumirep_*`:
43091107 (MedGemma-4B, running) -> 43091108 (Gemma-3-12B) -> 43091109 (Gemma-3-27B) -> 43091110 (Llama-4-Scout), chained
`afterany`, same flags as the original own-image run (`--item-set v3 --no-gating`, adaptation left on to match).
With the `lumigc_*` chain this is 2 concurrent GPUs (the cap). Still to write: a small compile script for rep1-vs-rep2
flip rates.

**Follow-up (same day): abstract to ~140 words; dataset-debugging history moved to new Appendix B (`sec:dev-history`).** Sec. 5 now
has one "Item construction" paragraph describing only the final procedure (sampling rule, post-op LIL baseline, auditor-in-the-loop,
templated DSCR stem, v3 = 52 patients); the two sampling bugs, v2 leakage rates/cause, rebaselining, and the v2-vs-v3 difficulty
paragraph are in the appendix. Compiles clean, 18 pages: body (Intro-Results) ends p.13, Limitations p.14, refs p.15, appendices
16-18. NAACL 2027 main-conference limit (https://2027.naacl.org/calls/main_conference_papers/, fetched 2026-09-23): long paper
8 pages (9 camera-ready), short 4 (5); ARR deadline 2026-10-12, commitment 2026-12-23, notification 2027-02-10. The page did not say
how references/limitations/appendices count (standard ACL/ARR practice: excluded) - confirm against the ARR CFP. Body was ~8,500
words vs ~5,000-5,500 that fit in 8 pages.

**Length cut done (same day): 18 -> 14 pages total; body (Intro-Results) now ends on p.7, Limitations p.7-8, refs p.8, appendices 9-14.**
Rewrote Intro, Related Work, Framework, Compatibility, LUMIERE, Setup, Checks, Results, Limitations (~4,500 body words; script kept
in the session scratchpad, pre-restructure tex saved there too - `git diff paper/latex/acl_latex.tex` shows the full change). Nothing
substantive was dropped, it moved: metric definitions -> new Appendix C, OmniBrainBench compatibility details -> Appendix D, full evidence-
audit method + option-only baselines -> Appendix E, Fig. 2 (LUMIERE pipeline) -> Appendix B, dev history -> Appendix B. Related Work merged from
5 to 3 paragraphs; Framework cut to ~450 words; contributions 4 -> 3. Numbers unchanged (checked against results/lumiere_reviewer_stats.md).
Refs to `sec:grounding-test`, `sec:results`, `sec:gating-causality`, `fig:phase-effects`, `tab:flip` all resolve; no multiply-defined labels.
Figure numbering shifted (phase-effects is now Figure 2). Visually inspected pages 1-2, 5-8.

**Not done / needs a decision:** PJRF/TCM key redesign (needs clinician), LIL/DSCR answerability fix (restrict vs
supply more input - design choice), LLM option-only and no-chain-context baselines (GPU), donor-permutation null,
appendix move of the dataset-debugging history. (Abstract was then shortened in a follow-up: ~390 -> ~200 words, dropped the framework/dataset restatements and the trailing contribution sentence, kept the three caveats: margin set post hoc, modest-above-null substitution result, answerability/keys unvalidated.) `paper/review.md` tracker rewritten to match.

## 2026-09-23 (later still x11) — paper: compiled the counterfactual-image substitution results and wrote them into §8 — all 4 grounding checks now complete

All 4 `lumicf_*` jobs (submitted earlier this session) finished cleanly while the gating-causality jobs were
queued behind them (`.err` files only benign Singularity bind-mount INFO lines, no real errors). User asked to
compile and write up.

**New tool**: `tools/compile_lumiere_counterfactual.py`. For each model, joins the own-image `v3` run against
the matching `_cf_v3_` run per (patient, phase), and for flipped answers on LIL/DSCR specifically, checks
whether the new answer's content (volume-change direction for LIL, RANO label for DSCR) matches what the
*substituted* patient's own facts actually support (`data/lumiere/v3/counterfactual_pairs.json` has
`partner_direction`/`partner_rano` per patient already, from the original pairing build). Output saved to
`results/lumiere_counterfactual_summary.json`.

**Findings** (open-weight suite, all 4 models, `v3`):
- Flip rate: AIA (no image dependency by construction — its answer is a fixed cohort-wide string) sits at
  10-17% across models, the baseline attributable to reformatting/decoding noise alone. LIL (12-42%) and DSCR
  (6-27%) exceed that baseline for 3 of 4 models — some real sensitivity to the substituted image, not pure
  noise.
- Truth-tracking among flips (the decisive part): pooled across all 4 models and both phases, 26/73 flipped
  answers actually matched the substituted patient's true direction/label — **35.6%, 95% Wilson CI
  [25.6%, 47.1%]**, an interval sitting entirely *below* the 50% chance rate, not straddling it. Per-model:
  only Llama-4-Scout reaches chance (50%/50%, n=6 each — small sample); every other model is below 50% on
  both phases (MedGemma-4B 25%/0%, Gemma-3-12B 38%/36%, Gemma-3-27B 21%/46%).
- Read together: models are *not* ignoring the substituted image (flip rate is elevated vs. the AIA baseline),
  but the resulting answer change doesn't reliably reflect what's actually true in the new image — closer to
  noise-like sensitivity to input-changing than to genuine content extraction.

**Wrote this into the paper, not just as a clean win**: added a new "Counterfactual-image substitution"
results paragraph to §8. Updated the "Reading against the pre-registration" paragraph honestly rather than
declaring the pre-registered criterion satisfied outright — the flip-rate magnitude (6-42%) doesn't cleanly
match the original "low" wording (it exceeds the AIA baseline for most models), so stated that explicitly as
a partial match, while noting the *non-truth-tracking* result (the part that actually distinguishes grounding
from noise) is unambiguous. Updated: §8's intro sentence ("three of four checks" → "all four checks"),
abstract ("results from the first three checks" → "results from all four checks... with the counterfactual
check showing that answers which do change mostly fail to track that image's actual content"), and
Limitations (removed the "had not finished running" language, replaced with the flip-rate/pre-registration
partial-match caveat; clarified what's still outstanding is the proprietary model suite, not this check).

Recompiled full cycle — exit 0, no errors, no overfull/underfull warnings. Visually re-checked the new
Results/Limitations pages.

`paper/review.md`: counterfactual-image-substitution item moved from In Progress to Done with the pooled
numbers; corresponding TODO line removed.

## 2026-09-23 (later still x10) — code: built and queued the gating-causality experiment (reviewer finding #2)

User asked whether it was already set up — it wasn't (checked: `CausalChainEvaluator`/`evaluate_case` only ever
builds `chain_context` from a model's own real upstream answers within the same run; no mechanism existed to
force a specific correct/incorrect/absent upstream context). Built it, then user expanded scope mid-design from
an initial DSCR-only proposal to all 4 dependent phases (LIL, DSCR, PJRF, TCM) x all 4 open-weight models, for
completeness against the reviewer's own chain-wide illustrative math (independent 80%-accuracy phases
multiplying to ~33%, not phase-specific).

**New files:**
- `src/gating_causality.py` — core logic. For each patient and each of LIL/DSCR/PJRF/TCM, evaluates that
  phase's question 3x (same image/question/options every time) varying only the injected upstream
  `chain_context`: *correct* (every upstream phase's true answer), *incorrect* (every upstream phase forced to
  a deterministic, alphabetically-first wrong option — reproducible, not random), *absent* (empty). Reuses
  `_evaluate_question` from `src/evaluator.py` completely unmodified; manufactured context entries are built in
  the exact same shape (`phase`/`question_id`/`question`/`model_answer`/`model_answer_text`/`visual_grounding`)
  a real one would have, so they're indistinguishable in format to the model, only the content varies by
  condition. `adaptation_enabled=False` throughout, to isolate the context-manipulation effect from that
  orthogonal mechanism. `summarize()` reuses `src/analysis.py`'s `_wilson_ci` so CIs match the rest of the
  paper's convention.
- `run_lumiere_gating_causality.py` — thin CLI, same shape as `run_lumiere.py` (`--model`/`--all-models`,
  `--n-cases`, `--item-set`, KB paths), plus `--phases` to subset LIL/DSCR/PJRF/TCM and `--include-unreviewed`
  (required as of this writing — expert review of `v3` still hasn't completed, same as every other reported
  result in the paper; first dry-run without this flag returned 0 cases, a good reminder this is genuinely
  still an open item, not an oversight in the new script).
- `shell/lumiere/lumiere_gating_causality.sbatch` — same generic per-model shape as
  `lumiere_prelim_ollama.sbatch` (`MODELS`/`EXTRA_ARGS` at submission time, job-name override per model). 8h
  time budget (vs. 6h for a full chain run) since this does 4 phases x 3 conditions = 12 main+probe calls per
  patient, more than a normal 5-phase run despite skipping adaptation entirely.

**Validated before submitting, not just written:** dry-ran `build_chain_context()` against real, already-loaded
Patient-002 `v3` data (no API calls) — correct-condition letters matched Gemma-3-27B's actual known correct
answers exactly (AIA=C, LIL=D, DSCR=D, matching the worked-example appendix from the x9 entry), incorrect
condition picked the expected deterministic wrong letters. Also smoke-tested `summarize()` against a fabricated
result shape to confirm the CI/accuracy aggregation runs end-to-end before trusting it on real output later.

**Queued, not run yet**: submitted all 4 jobs, chained sequentially via `--dependency=afterany` on each other,
with the first depending on all 3 currently-active `lumicf_*` (counterfactual) job IDs — `lumigc_MedGemma-4B`
(43061666) → `lumigc_Gemma-3-12B` (43061678) → `lumigc_Gemma-3-27B` (43061679) → `lumigc_Llama-4-Scout`
(43061683). This keeps total concurrent GPU usage at 2 throughout (per the standing GPU-concurrency-cap
instruction), rather than adding a 3rd job competing for a slot. Confirmed via `squeue` after submission: both
`lumicf_*` jobs still running, `lumicf_Llama-4-Scout` and all 4 `lumigc_*` jobs correctly showing `PENDING
(Dependency)`.

`paper/review.md` updated: gating-causality entry moved from "not started" to "queued" under In Progress with
the job IDs; TODO line updated to "watch the queued jobs, then compile with `summarize()`."

## 2026-09-23 (later still x9) — paper: added the worked-patient-example appendix the reviewer asked for

Last open "fixable now" item from the x8 triage. Added Appendix A, "A Worked Patient Example," after the
bibliography (`\appendix` + `\section{}`, standard ACL structure).

**Picked Patient-002 for a mundane reason, not a good one**: it's the first case in evaluation order (first
entry in every model's `raw_results.json`), chosen before looking at its content, specifically so the
example couldn't be accused of cherry-picking. Walked its full leak-controlled (`v3`) 5-phase chain as
answered by Gemma-3-27B (best open-weight model): AIA → LIL → DSCR → PJRF → TCM, with each phase's question,
correct answer, model answer, and (for LIL/DSCR) the model's actual `visual_grounding`/`reasoning` text
quoted verbatim.

**Turned out to be a genuinely strong illustration of the paper's central finding, discovered while writing
it, not engineered in**: at AIA (a question only about imaging *modalities*, not location), the model's
`visual_grounding` volunteers an unprompted lesion location — "right temporal lobe" — that is wrong on both
counts against the structured facts (true baseline location is Superior Parietal Lobule / Left Cerebral
White Matter, true laterality is left). Ran `tools/audit_reasoning_facts.py`'s actual `check_item()`
function against this claim in isolation (not by hand) — it labels it `laterality_flip`, a real, tool-caught
contradiction. The same fabricated claim then reappears verbatim in the model's LIL and DSCR reasoning three
phases running, at which point the same audit function reclassifies every claim as `copied` — correctly,
since by then the claim is present in the model's own prior-turn output, which is exactly what the audit is
built to detect and exactly why it can't tell a re-verified observation from one just carried forward
(directly illustrates Limitations point 6, added in the x8 entry). All final answers on this chain are
correct except PJRF, where the model picked a more pessimistic survival bucket than the one matching the
recorded 48-week survival, included in the appendix for contrast rather than cutting it for looking
untidy. Stated in the writeup, verifiably: "its fact-check labels above are exactly what
`tools/audit_reasoning_facts.py` outputs when run on it, not a paraphrase."

Recompiled full cycle after adding — exit 0, no errors, no overfull/underfull-adjacent rendering issues;
rasterized and visually checked both new appendix pages (paper is now 15 pages, up from 13). `paper/review.md`
TODO's "write one full worked patient example" line removed (Done section in that file is currently kept
empty by the user's own edit — not refilled, per instructions not to revert deliberate changes outside our
context).

## 2026-09-23 (later still x8) — paper: fixed all 8 remaining "fixable now" reviewer items; `paper/review.md` status tracker updated

User asked which In Progress/TODO items from `paper/review.md` could be fixed immediately (no new
experiments, no external reviewer, no waiting on the running `lumicf_*` jobs); identified 8, user said do
all 8 in one pass. All 8 done, plus a 9th (the §7-vs-§8 preregistration timing inconsistency, which turned
out fixable now too — see below). `paper/review.md` rewritten with a `## Done` section for all of these.

1. **§5 Patient-025 cohort-eligibility contradiction.** Traced `src/lumiere_facts.py`'s
   `select_target_patients()`: the 55-patient eligibility count is two *independent* per-patient checks
   (≥3 RANO-rated timepoints anywhere, and ≥1 complete-imaging timepoint anywhere) — not "at least one
   timepoint with both," which is what the paper claimed. The *same-timepoint* requirement only appears
   later, in `build_patient_case_facts()`'s `imaged_response_facts` filter, which is why Patient-025
   (confirmed present in a live re-run of `select_target_patients()`, 55/55 selected) gets dropped at
   extraction instead of never being in the 55 to begin with. Rewrote the Cohort paragraph to describe the
   two-part criterion honestly instead of the single simultaneous-timepoint claim.

2. **Limitations "<5%" phase-share line.** Clarified it's about OmniBrainBench's 6,823-question composition
   (PJRF 64, TCM 51, confirmed well under 5% each), not the LUMIERE chain dataset — which has no such
   imbalance (every patient contributes exactly one PJRF/TCM item). Added a note about the LUMIERE
   dataset's own wide per-phase CIs at n=52 as the real reason results are reported unpooled there.

3. **§7 vs §8 preregistration-criterion timing.** The "Reading against the pre-registration" paragraph
   previously said "we read this as satisfying the paper's own pre-registered criterion" in the same
   breath as admitting the 4th (counterfactual) check wasn't done — a real contradiction, not just
   ambiguous phrasing. Reworded to explicitly state the criterion "cannot yet be reported as fully
   satisfied" until that check resolves. Fixed independent of whether the running jobs finish soon (unlike
   the original review.md triage assumed) — this was a wording fix, not something blocked on the jobs.

4. **6,823 vs. 9,527 QA-pair count discrepancy + `source_file` attribution** (finding 6). Listed the actual
   HF dataset repo's files (`huggingface_hub.list_repo_files` on `FrankPN/OmniBrainBench`):
   `open-ended-qa_2704.json` + `closed-ended-qa_6823.json` = 9,527, exactly matching the reviewer's
   public-abstract figure — added this to §4 rather than leaving the two numbers unreconciled. Also added
   a sentence clarifying `source_file` is a field OmniBrainBench itself ships, but using it to represent
   same-patient identity for a causal chain is KAB's own interpretive choice, not an OmniBrainBench claim.

5. **No results reported for core KAB metrics** (finding 7). Pulled real per-model, per-phase numbers
   (answer recoverability ~96-100%, ontology term coverage bimodal 15-48% vs 94-98%, answer-term overlap
   0-73%, adaptation triggered only on LIL) from the v3 nogate `total_results.json` files and added a new
   "KAB framework metrics" paragraph to §8. Explicitly stated gated chain completion is *not yet available*
   (no gated `v3` run has been executed) rather than fabricating a number for it.

6. **Metric renaming** (finding 1, naming half). Renamed the four measures the reviewer specifically named
   as mismatched to what they observe, throughout the paper (definitions, Related Work citations, Results,
   Limitations): KBAlign → **ontology term coverage**, ConceptPrecision → **answer-term overlap**, local
   faithfulness → **answer recoverability** (and correct-but-unfaithful → correct-but-unrecoverable),
   chain faithfulness → **upstream-term repetition**. Fixed the exact overclaim sentence the reviewer
   quoted ("faithfulness metrics establish whether a model reasoned correctly" — paper's own flagged
   lines). Also caught and fixed the adjacent knowledge-gap/activation-failure claim in the same
   paragraph, which needs a generic-retry/irrelevant-hint control we haven't run; now stated as an open
   caveat ("we report the targeted-hint adaptation rate alone") instead of an established distinction —
   this wasn't explicitly one of the 8 planned items but was directly adjacent to the fix and cheap to
   correct honestly while already in that paragraph.

7. **Image-ablation paired statistics** (finding 3, CI half). Computed patient-clustered bootstrap 95% CIs
   (10,000 resamples, real per-patient per-phase correctness from `raw_results.json`, not simulated) for
   the image-minus-text-only accuracy difference, all 4 models. Result: none of the 4 CIs sit inside a
   ±5pp margin, but all 4 sit inside ±8pp. Replaced the paper's "overlapping CIs ⇒ equivalence" framing
   (exactly what the reviewer objected to) with the actual interval plus this explicit, honestly-reported
   margin dependency, in both the Text-only ablation paragraph and the pre-registration paragraph. Also
   added a caveat that the "decoding noise" explanation for per-question answer flips hasn't been
   confirmed by repeat-run controls under unchanged inputs (finding 3's other sub-point).

8. **Reproducibility details** (presentation, mostly). Added: exact Ollama tags (`medgemma:4b`,
   `gemma3:12b`, `gemma3:27b`, `llama4:scout`, Q4_K_M) and decoding settings (temperature 0, 800-token
   budget) to Models; a new "Failed-response handling" paragraph (3-try exponential backoff, lenient
   non-strict JSON parse for literal-newline responses, answer-letter regex salvage since `"answer"` is
   schema-first, unparseable-after-salvage scored incorrect rather than excluded — sourced directly from
   `src/evaluator.py`); a new "Image rendering" paragraph (max-tumor-mask-area axial slice, atlas-
   registered CT1 sequence, rotated 90°, 1st-99th-percentile intensity clip — sourced from
   `_render_axial_slice_png()` in `src/lumiere_facts.py`); exact ontology versions (NCIt `26.07d` from its
   `owl:versionInfo`; RadLex has no embedded version tag in the release, cited by download date instead);
   and a claim-audit implementation note (deterministic numeric/hemisphere pattern matching against
   structured facts, not an LLM judge — sourced from `tools/audit_reasoning_facts.py`), with a matching
   paraphrase/synonymy-risk caveat added as a new Limitations point.

9. **PDF misplaced line numbers "particularly on page 4 and near column endings."** Root-caused via the
   full `pdflatex` log rather than guessing: both TikZ figures (`fig:overview`, `fig:lumiere-pipeline`,
   both `figure*`) were mildly overfull relative to `\textwidth` (Overfull \hbox warnings of 10.3pt and
   47.5pt). Wrapped both in `\resizebox{\textwidth}{!}{...}` — zero overfull/underfull warnings after.
   Since the paper has grown substantially since the reviewer's read (this session alone added ~1.5 pages
   of content, on top of earlier citation/em-dash fixes), rasterized and visually inspected **all 13
   pages** of the recompiled PDF end-to-end (via `convert`/ImageMagick, since `pdftoppm`/`pdftotext` aren't
   on this login node) rather than assuming page 4 still corresponds to the same content — found no visual
   overlap anywhere, consistent with the log now being fully clean.

Not done from this paragraph's original scope: one full worked patient example (reviewer explicitly asked
for this in place of some construction-history detail) — still open, moved to `review.md`'s In Progress.

Recompiled the full `pdflatex` → `bibtex` → `pdflatex` → `pdflatex` cycle after each batch of edits — final
state: exit 0, no errors, no undefined references, no overfull/underfull box warnings at all.

`paper/review.md` rewritten: all 11 items above (3 from the x7 entry + these 8/9) moved to a new `## Done`
section with what was actually checked; `## In progress` now holds only the counterfactual jobs (running),
the gating-causality experiment (not started, needs new runs), and the worked-patient-example writeup;
`## Blocked` unchanged (still needs the external clinical reviewer + the reframe-the-paper decision with
Prof. Wang); `## TODO` checklist updated with strikethroughs for the 8 completed items.

## 2026-09-23 (later still x7) — paper: fixed 3 of the reviewer's internal-inconsistency findings (verified against real data, not just reworded)

Continuing the triage from the entry below. For each item, checked the actual result JSONs / dataset / code before touching
paper prose, per the reviewer's own complaint that construction-loop self-validation isn't enough — didn't want to fix a
review finding by just rewording it into apparent consistency.

**1. AIA "image advantage" sentence had the labels swapped (§8, ~line 331).** Checked
`results/lumiere_Gemma-3-27B_v3_nogate_20260922_191649/total_results.json` against the matching `_textonly_v3_` run:
real AIA accuracy is 86.5% with image, 76.9% text-only (image is *higher*). The paper's parenthetical read "86% text-only
versus 77% image" — backwards. Fixed to "86% image versus 77% text-only", which now actually supports the sentence's own
claim instead of contradicting it. One-line fix, no data/code change.

**2. DSCR majority-class baseline was a real undercount (§8, ~line 337) — root cause was a bucketing bug in `src/analysis.py`.**
Reviewer's math (35/54 progressive-disease cases → ≥35/52=67.3% after 2 exclusions) didn't match the paper's reported
64-65%. Traced it to `_majority_baseline()`: it buckets by exact string match on `correct_answer_text`, and 2 of the 52
v3-cohort DSCR items are worded `"Progressive disease (PD)"` vs. 33 worded `"Progressive disease"` — same class, different
literal strings, so the naive bucketing undercounted (33/52≈64% instead of the true 35/52=67.3%). Confirmed this is
DSCR-specific (checked PJRF/TCM/LIL answer-text distributions — all near-unique free text, unaffected) before touching the
metric. **Fixed** `_majority_baseline()` to strip a trailing parenthetical abbreviation before bucketing (regex
`\s*\([^()]*\)\s*$`), scoped narrowly to that one function so it can't silently change anything else. Regenerated
`report.txt`/`total_results.json` for all 8 affected `v3_nogate`/`textonly_v3_nogate` result directories (4 models ×
image/text-only) from their untouched `raw_results.json` — no re-inference needed. Corrected baseline is **67.3% for all
four models** (previously reported as a misleading model-varying "64-65%", which was actually just the same bug applied to
each model's report independently — it's a property of the question set, not the model, so it should never have varied).
Updated the paper's "64-65%" to "67%". All four models still sit at/below the corrected (higher) baseline, so the
reviewer's original point — no model shows RANO skill above class imbalance — holds, and is now more clearly true.

**3. "2 questions" / "AIA-LIL pairs" (plural) / "2 cases" was a real undercount, not just inconsistent wording (abstract,
§1, §4).** Re-ran both of the paper's own described methods directly against `src/data/closed-ended-qa_6823.json`
(the cached OmniBrainBench dataset) rather than trusting the original one-off audit's output, since that script no longer
exists in the repo: (a) group by `source_file`, find `image_path` values shared across ≥2 distinct `clinical_phase`
values; (b) independently, strip modality/view/slice filename suffixes to recover per-patient case IDs, same check. Both
methods agree: **2 genuine same-patient cross-phase cases (both VQA\_RAD, both one AIA question + one LIL question) = 4
questions total**, zero spanning 3+ phases. The paper's "2 questions" undercounted by exactly 2x — it was counting cases/
pairs but labeling them as questions. Fixed all three occurrences (abstract, §1 intro, §4) to state patients/pairs and
questions separately and consistently: "2 patients... 4 questions total".

Recompiled the full `pdflatex` → `bibtex` → `pdflatex` → `pdflatex` cycle after all edits — exit 0, no errors, no
undefined references (`pdftotext` isn't available on this login node to grep the rendered PDF directly, but the .tex
source and compile log were checked directly).

**Not yet done** (deferred, larger scope): the Patient-025 eligibility-wording contradiction (§5 cohort paragraph — text
currently implies the 55-patient count already used the stricter simultaneous-timepoint criterion that only got fixed for
sampling afterward; needs tracing through `src/lumiere_loader.py`/`src/lumiere_facts.py` to state the actual sequencing
accurately), the preregistration-timing inconsistency (§7 vs §8), and the Limitations "<5%" dataset-mismatch line — none
of these were investigated this session. The 7 core methodological findings (metrics don't establish causal reasoning,
gating conflates mechanical propagation with causal, image-ablation "equivalence" claim, copied-vs-grounded audit
reliability, independent answerability validation, OmniBrainBench scope/attribution, no results for the core KAB metrics)
are unstarted — those require new analysis/experiments, not just number-checking, and are a separate, bigger conversation
(user indicated wanting to defer the "reframe the paper" question, likely with Prof. Wang, rather than decide it here).

## 2026-09-23 (later still x6) — paper: received senior-reviewer review (paper/review.md), reject-and-revise, triage started

User shared a full senior-reviewer review of the compiled 12-page manuscript (`paper/latex/acl_latex.pdf`), saved
at `paper/review.md`. **Recommendation: reject in current form, encouraged to substantially revise.** Reviewer
states high confidence on the internal inconsistencies and metric/claims gap; underlying implementation and
clinical labels flagged as needing separate verification (reviewer did not reproduce experiments).

**Core methodological findings (highest priority, in reviewer's order):**
1. KAB metrics (KBAlign, ConceptPrecision, local/chain faithfulness) measure surface overlap/recoverability, not
   correctness or causal dependency — the "establishes whether a model reasoned correctly" claim (paper lines
   366–367) is unsupported as written. Recommends renaming metrics to describe what they actually measure and
   validating against independent expert judgments + adversarial examples (right vocab/wrong patient, negated
   findings, answer repetition, valid paraphrase).
2. Gated chain scoring produces failure propagation *mechanically* (independent 80%-accuracy phases chained
   multiplicatively → ~33% with zero real causal dependency), not necessarily causally. Needs
   correct/incorrect/absent-upstream-context conditioning experiments to support the causal claim; "soft" gating
   framing needs justification since the current rule reads as hard blocking.
3. Image-ablation "statistical equivalence" claims (§8) aren't supported — CIs treated this way ignore that
   questions are paired/patient-clustered, and non-significance ≠ equivalence. Needs paired accuracy-difference
   CIs (patient-cluster-preserving) and a pre-specified equivalence margin if the claim is "no practical benefit."
4. Copied-vs-grounded evidence audit (§7) can't distinguish real visual grounding expressed in option wording from
   actual copying, or "unlabeled" from "fabricated" — reported 43–90% copied / 0–8% independently-supported rates
   don't directly estimate image-grounded-reasoning frequency as currently defined.
5. Benchmark answerability was validated against KAB's own auditor, not an external clinician — needs independent
   clinical review of answerability/distractors/label validity, plus options-only/longest-option/majority-class/
   no-chain-context baselines.
6. OmniBrainBench continuity critique (§4) needs tighter scope — same-patient continuity isn't only same-image;
   also flags a 6,823 (this paper) vs. 9,527 (public abstract) QA-pair count discrepancy needing explanation.
7. §8 reports no results for the actual KAB metrics (ontology alignment, concept precision, faithfulness,
   adaptation, gated completion) — empirical section is really just the image-grounding audit; title/abstract/
   method vs. results mismatch.

**Internal inconsistencies flagged (table, reviewer's §8), need reconciliation:** patient/question/pair counts
vary across Abstract/§4; §5 cohort description excludes a patient for conditions it says are satisfied; §5 vs §8
cohort math (35/52 = 67.3% floor) doesn't match the reported 64–65% majority baseline; §8 lines 818–820 attribute
an image advantage to AIA but the supplied AIA numbers favor text-only (86% vs 77%); §7 vs §8 claims the
preregistered criterion is satisfied before the counterfactual-substitution check it depends on is complete;
Limitations' "<5%" phase-share claim doesn't match the illustrated 52-patient × 5-phase dataset.

**Presentation/reproducibility:** reads partly as a dev log — wants a full worked patient example instead of
construction history; missing exact model IDs, prompts, decoding settings, image rendering, ontology versions,
failed-response handling, claim-audit implementation. PDF has misplaced line numbers overlapping text/equations
near page 4 and column endings.

**Reviewer's suggested revision strategy:** re-center the paper on patient continuity / answer leakage / image
dependence in longitudinal brain-MRI eval (called the most defensible current contribution); treat KAB metrics as
exploratory/unvalidated until supporting experiments exist; prioritize independent clinical validation, corrected
paired stats, and repeat-run controls over running more models.

**Decision (this session):** log-then-triage — record the review in full here first, then work through the
mechanical/reconcilable items (internal inconsistencies, stats framing, presentation) before revisiting the
bigger reframe-the-paper-around-continuity question, which the user wants to defer as a separate discussion
(likely with Prof. Wang) rather than decide unilaterally right now.

## 2026-09-23 (later still x5) — paper: fixed unresolved cross-refs/citations, removed excessive em-dashes and scare-quotes

**Unresolved "Section ??" / "(?)" citations:** user asked why. Not a source bug -- LaTeX `\ref{}`/`\citep{}` need a
full `pdflatex` -> `bibtex` -> `pdflatex` -> `pdflatex` cycle to resolve; whatever compiled the copy the user was
reading had only run a single pass. Ran the full cycle here (confirmed `bibtex` ships inside the `texlive/2023`
module, just needed the module loaded first) -- zero undefined references or citations now, References section
renders with real author-year entries. `acl_latex.bbl` is generated by this and now tracked in the repo (already
committed by the user separately, see below) so a plain `pdflatex` without `bibtex` still resolves citations for
anyone else opening this in Overleaf or locally.

**Em-dash reduction:** user flagged excessive ` -- ` usage paper-wide. Audited first (`awk` per-line occurrence
count) rather than guessing: 77 raw hits, but 14 of those are literal TikZ `--` path-drawing syntax inside the two
figures' code (not prose) -- left those untouched. Fixed all 63 real prose instances individually (not a blind
find-replace, each needed a different fix depending on the sentence): colons where a dash introduced a list or
elaboration, parentheses for true asides, commas for light appositives, semicolons where both sides were
independent clauses, and two cases split into separate sentences. Compiled + visually verified after (rasterized
pages, not just log output) -- reads as confident scientific prose now, not the hedge-heavy dash-per-clause style
from before.

**Scare-quote reduction:** user also flagged quotation marks, giving `"chain"` / `"gated out"` as the example.
Distinguished two different uses that both used the same punctuation: **scare quotes** (hedging distance around an
ordinary word, e.g. `"chain"`, `"gated out"`, `"volume change"`, `"progressive disease"`, `"right only with
image"`) vs. **verbatim quotation** (marking actual quoted source text, e.g. `"$\geq$25\% increase"` from a cited
clinical guideline, explicitly described in the same sentence as "quoted verbatim"). Removed/reworded the former
(rephrased two sentences to drop the hedge entirely; converted defined/mentioned terms to `\emph{}`, matching the
paper's own existing convention for terms like `\emph{self-leakage}`); left the latter alone since removing it
would be wrong (verbatim clinical-guideline text should be quoted). Flagging this judgment call explicitly in case
the user wants the verbatim one gone too.

**Note:** the user is committing changes independently in a separate session/terminal while I work (saw a new
commit `69257d0 dev::psper review` appear mid-session that I hadn't made). Continuing to leave commits to them
rather than committing myself, per standing instructions not to commit unless asked.

## 2026-09-23 (later still x4) — paper: whole-paper tone/currency pass — expert-review track removed, roster history dropped, contributions as a list

**User read the compiled paper and flagged it directly:** "it contains a lot of outdated stuff... every mention of
a reviewer should be excluded," followed by "no need to also mention [the roster-removal sentence], we just stick
to the current four we are using," and "I discovered that the tone used is as if we are giving a progress report
on a project, we are to write it as a scientific paper." Three linked instructions, treated as one pass since they
overlap (the expert-review narrative and the roster-history narrative were the two biggest sources of the
progress-report feel).

**Expert-review track removed paper-wide** (grepped every "review/reviewer/expert/unreviewed/validat*" hit first
to scope it, ~15 mentions across 8 sections): abstract, intro (hybrid-pipeline sentence + contributions), Figure 2's
lead-in sentence and caption, the LUMIERE section's Cohort/Contribution paragraphs, Results' pre-registration
paragraph, Limitations, and the Ethics Statement. Two full paragraphs describing the review mechanism and the
"preliminary vs. reviewed" framing (`Review mechanism`, `Preliminary evaluation on unreviewed items`) were deleted
outright rather than trimmed, since their entire content was about the review process. `Hybrid drafting and expert
review` was renamed `LLM drafting` and cut down to only the drafting-methodology content that's still true. Where a
sentence's justification depended on review (e.g., "draft the full cohort so a review pass can cover it in one
sitting"; Limitations' "provisional pending review" framing), rewrote the justification to something independently
true rather than just deleting the clause and leaving a non sequitur (full-cohort drafting is now justified by
maximizing item-set size; "provisional" is now justified by the v2->v3 leak-correction history and the
still-incomplete counterfactual check alone). **Kept** one intentionally: "a point of reviewer scrutiny" in
Limitations refers to this paper's own academic peer reviewers, not the clinical domain-expert -- different sense,
not outdated, left as-is (flagging this judgment call in case the user meant literally every occurrence of the
string).

**Roster-revision history dropped from Models paragraph** (`sec:setup`), per the user's explicit correction --
no more "the senior author restricted the roster... removed five models... we dropped Llava-Med-7B." States the
current four open-weight models directly. This also removed the last "senior author" mentions in the paper
(3 occurrences total, all tied to either this or the now-deleted review paragraphs). The Infrastructure paragraph
and one Limitations sentence both referenced "the roster revision above" as a callback -- rewritten to state the
current infrastructure fact plainly (open-weight suite is single-GPU, no tensor parallelism needed) without the
historical callback, since the history it was calling back to no longer appears in the paper.

**Contributions list converted from a run-on "First,...Second,...Third,...Fourth," paragraph to `itemize`**
(added `\usepackage{enumitem}` for compact spacing) -- separate ask, addressed in the same pass since it landed
mid-edit.

**Also updated while in these paragraphs anyway** (natural consequence of removing "companion release"
progress-report language, not a separate ask): abstract and intro now describe the image-grounding test suite and
its provisional findings, since those are now actually in the paper (added earlier this session) and the old
"full results in a companion release" line was already stale before this pass even started.

Compiled and visually verified the same way as every other paper change this session (rasterize + look, not just
exit-code): abstract, intro/contributions list, Figure 2's section, Models/Infrastructure, Results, Limitations,
and Ethics all re-rendered clean, no dangling cross-refs, no orphaned sentences referencing deleted content.
Page count 12 -> 11. Compile artifacts removed after.

## 2026-09-23 (later still x3) — paper: Figure 3, text-only-vs-image results chart (the non-counterfactual-dependent follow-up)

Built the results chart from the pair of follow-up options offered earlier (results chart vs. counterfactual
flip-rate chart) — this one, since it visualizes numbers already in hand (Table 1 / `sec:results`) rather than
the still-running counterfactual job (43058034-37).

`figures/text_only_ablation.pdf` (source: `figures/make_textonly_chart.py`, kept in the repo for reproducibility —
regenerate if the Table 1 numbers ever change), embedded as Figure 3 next to Table 1 in `sec:results`. Grouped bar
chart, image vs. text-only accuracy per model, **drawn on the full 0-100% axis deliberately** (not zoomed/truncated)
so the ~3pp gaps read as small, matching what the text and Table 1 already say — a truncated axis here would have
visually overstated a difference the paper's own claim says is not real. Followed the `dataviz` skill's procedure:
categorical colors are slots 1+2 (blue/orange) from its reference palette, documented in that skill's own
`palette.md` as already passing the adjacent-pair CVD gate for bar charts (worst-case ΔE 9.1 light) — could not
re-run `scripts/validate_palette.js` to confirm directly, no `node` on this cluster, so relied on the skill's own
pre-validated documentation for this exact slot pair instead of skipping the check silently. Added a diagonal hatch
on the text-only series as redundant (non-color) encoding for print/grayscale safety, direct value labels on all 8
bars (dataset is small enough that this doesn't clutter), legend for the 2 series.

**Bug caught before shipping:** first render had the 4 model x-axis labels overlapping/colliding (too long for a
single-column figure width) — caught by rasterizing the rendered PDF page, not from matplotlib's exit code (it
exits 0 either way). Fixed with two-line wrapped labels ("Llama-4-\nScout" etc.); re-rendered and confirmed clean.
Installed `matplotlib` into the project `.venv` (wasn't present; a lightweight pip install, not model weights, ran
on the login node — no GPU/SLURM needed for a static chart).

Compiled + visually verified (same rasterize-and-look method as Figures 1-2): Table 1 and Figure 3 land side by
side at the top of Section 8 as intended, no overlaps, all cross-refs resolve. Compile artifacts removed after.

**Note for next commit:** `paper/latex/acl_latex.aux/.log/.out` show as tracked-but-deleted (`D`) in `git status`
after cleanup — `git ls-files` confirms they're actually committed in this repo's history (commit `936a715`), which
contradicts this conversation's opening `git status` snapshot showing them as untracked (`??`); root cause not
investigated, flagging rather than silently fixing. Recommend `git rm --cached` on those three plus a `.gitignore`
entry for `*.aux/*.log/*.out/*.bbl/*.blg` so every future compile stops dirtying `git status` — left undone since
it's a git-tracking decision, not something asked for this session. New untracked content ready to be added
whenever changes are committed: `paper/latex/figures/` (chart script + generated PDF).

## 2026-09-23 (later still x2) — paper: Figure 2, LUMIERE construction pipeline (expert review excluded per user)

**User decision:** exclude the domain-expert review step from this figure "for now" — pipeline shows only the
automatic stages (fact extraction -> LLM drafting -> leakage audit/retry), ending at the leak-controlled (v3) item
set as a terminal box. Caption and the referencing sentence in `sec:lumiere`'s opening paragraph both say explicitly
that expert review is a separate, still-ongoing track not shown in the diagram — not silently omitted.

`fig:lumiere-pipeline`, placed at the top of Section 5 (`sec:lumiere`), same TikZ visual language as Figure 1
(rounded boxes, `arr` style, scriptsize sub-labels): LUMIERE Cohort -> Fact Extraction -> LLM Drafting -> Leakage
Audit -> Leak-Controlled Item Set (v3), with a retry loop from the audit back to drafting labeled "violation found:
retry (up to 8x), fed back into the drafting prompt."

**Bug caught before shipping:** first version drew the retry loop as a `to[bend right=35]` curve with a
`node[midway, below=0.9cm, ...]` label — rendered with the label text overlapping/illegible against the box row
above it (confirmed by rasterizing the actual compiled page, not just checking pdflatex's exit code — the compile
itself reported no error, only a generic "Overfull \hbox" warning that undersold how broken it looked). Root cause:
`below=0.9cm` as a bare positioning key doesn't reliably offset a path label the way `node[below=X of Y]` does.
Fixed by routing the loop with explicit coordinates above the row (`(audit.north) -- ++(0,0.55cm) -| (draft.north)`)
and placing the label at an explicit computed midpoint coordinate instead of relying on `midway`+relative
positioning together. Re-rendered and visually confirmed clean after the fix.

**Process note for future figure work this session:** pdflatex exiting 0 / "no errors" is not sufficient
verification for a TikZ diagram — always rasterize the actual page (`ghostscript` + `convert`, no `pdftoppm` on this
node) and look at it before calling a figure done. A remaining `Overfull \hbox` warning in the log (from the caption
paragraphs, ~10-47pt, both figures) did not visually manifest as an overflow in the rendered page and was left as-is
after checking.

## 2026-09-23 (later still) — paper: Results section (steps 1-3 numbers) + Figure 1 (KAB framework overview)

**Results section added** (`paper/latex/acl_latex.tex`, new `\section{Results}\label{sec:results}`, placed between
`sec:grounding-test` and Limitations). Reports the three grounding-test checks that are actually complete and
numbers-in-hand, all on `v3`: stem-leakage audit (v2 vs v3 violation rates), text-only ablation (headline table —
3/4 models score >= as well text-only, 87-91% of individual questions get an identical answer with vs without the
image, v3 vs v2 difficulty context), evidence fact-check (43-90% copied, 0-8% independently-supported), and the two
secondary v3 findings that sharpen the reading (DSCR at/below the 64-65% majority baseline — construct-validity
caveat, not grounding evidence; LIL at/near chance 23-40% — the one result that speaks to grounding directly).
Closing paragraph explicitly reads these against the pre-registration already stated in `sec:grounding-test` and
flags both remaining caveats (unreviewed items; counterfactual-image substitution — step 4 — still running, not
included). Limitations section's opening paragraph updated to match (now says three of four checks are reported
provisionally, not zero).

**Figure 1 added** (`fig:overview`, new `\usepackage{tikz}` + `decorations.pathreplacing`/`positioning`/`calc`
libraries): native TikZ diagram of the KAB framework — five-phase chain (AIA->LIL->DSCR->PJRF->TCM) with "gate"
labels on each arrow, a brace below spanning the full chain labeling soft gating, and two dashed callouts above
(Faithfulness -> AIA/LIL, Feedback-Adaptation -> DSCR/PJRF). Placed in the Introduction, referenced right after the
five-phase/three-metric sentence. First draft had a third top callout ("Soft Gating") pointing only at TCM, which
duplicated the brace below saying the same thing — cut it, kept the brace as the single soft-gating explanation.
Chose TikZ over an external image (PNG/draw.io) so the figure stays editable in the paper source with no binary
asset to keep in sync.

**Verified by compiling and visually inspecting rendered pages** (`module load texlive/2023`; no `pdftoppm`/`gs`
binary directly on PATH, used `module load ghostscript/9.22` + `convert` to rasterize pages for a visual check —
note for future paper-compile sessions on this cluster). Two-pass `pdflatex` run, 0 errors, all new cross-refs
(`sec:results`, `tab:textonly`, `fig:overview`) resolve; remaining `Citation ... undefined` warnings are pre-existing
(no `.bbl`/bibtex run here, unrelated to this change). Confirmed Figure 1 renders legibly (5 boxes, gate labels,
brace, both callouts, no overlap) and the Results section/table render correctly (checked via rasterized page
images, not just log output). Compile artifacts (`.aux`/`.log`/`.out`/`.bbl`/`.blg`) removed after — only `.tex`
and the regenerated `.pdf` are meant to be tracked.

**Context: professor said** (relayed by user) **"you can start revising the paper, adding some overview/teaser
figures etc."** — Figure 1 is the first figure of that revision pass. Not yet done: any additional figures (e.g., a
LUMIERE dataset-construction pipeline figure, a results plot once the counterfactual test finishes) — scope not yet
discussed with the user beyond this first one.

## 2026-09-23 (later still) — Methods sections of the ACL draft rewritten to match actual project state
`paper/latex/acl_latex.tex` had fallen well behind the last few days' work; per user request, rewrote the methods
sections (not abstract/introduction/related work, which are unchanged pending a separate pass):
- **Dataset construction (`sec:lumiere`):** added the precise cohort numbers (91 LUMIERE patients -> 55 eligible ->
  54 extracted/drafted, Patient-025 excluded) and the real post-fix RANO distribution (PD 37, SD 9, PR 4, CR 4).
  Added new paragraphs on the leak-controlled item-set rebuild (stem-leakage auditor, root cause in the drafting
  prompt, retry loop, DSCR templating), post-operative rebaselining (42/54 pre-op baselines found, 44/54 changed,
  Patient-049/068 excluded -> 52 patients, 20 up/32 down), the display-orientation note, and a new paragraph stating
  plainly that preliminary evaluation runs on unreviewed items with the senior author's approval, not gated on
  expert review completing.
- **New Section 8, "Testing Whether Correct Answers Are Image-Grounded" (`sec:grounding-test`):** describes all four
  non-grounding checks as pure methodology (setup, justification, decision rule) with zero outcome numbers, per the
  academic-writing skill's methodology/findings genre boundary — stem-leakage audit (cross-referenced to sec:lumiere),
  text-only ablation, evidence fact-check (copied/independently-supported/fabricated/laterality-flip categories,
  RANO-threshold exclusion), and counterfactual-image substitution (pairing method, all-5-phases scope, the PJRF/TCM
  confound caveat, and the pre-registered joint decision rule across all four checks).
- **Experimental Setup:** model roster corrected to the actual current 7 models (3 proprietary + MedGemma-4B/
  Gemma-3-12B/Gemma-3-27B/Llama-4-Scout, Q4 via Ollama), replacing the stale 12-model list; explains the no-
  China-models roster cut and the Llava-Med-7B JSON-output drop. Infrastructure paragraph corrected from the old
  "L4, multi-GPU tensor parallelism needed" claim to the actual single-GPU RTX PRO 6000 setup — the roster cut
  removed every model that would have needed multi-GPU serving.
- **Limitations:** corrected the sentence claiming all results are gated on expert-review completion (now inconsistent
  with the new preliminary-evaluation paragraph); flagged the counterfactual test as still running at time of writing;
  replaced the stale 30B-38B GPU-memory limitation with an accurate note that the roster revision resolved it; added
  a limitation stating the local-faithfulness probe's structural inability to establish grounding on its own (why
  Section 8 exists).
- Compiled clean with `module load texlive/2023`: 2 pdflatex passes, 10 pages, 0 errors, all new `\label`/`\ref` pairs
  resolved (remaining "undefined" warnings are pre-existing unrun-bibtex citation keys, not from these edits).
- **Not yet touched:** Abstract, Introduction, Related Work, Ethics Statement — Abstract in particular should be
  redone last, once Results exists, per the academic-writing skill's Abstract-last workflow.

## 2026-09-23 (later) — step 4 built and submitted: counterfactual-image test, throttled to <=2 concurrent GPUs
Per professor's request, all future job submissions cap total concurrent GPU usage at 2 (was previously up to 8
concurrent, e.g. the v3 batch). Implemented here via SLURM `--dependency=afterany:<jobid>`, not by asking for fewer
GPUs per job (each job still needs its own 1 GPU) — 2 jobs submitted to run immediately, the other 2 held with a
dependency on the first 2 so they only start once a slot frees. Same pattern to reuse going forward.

**Built, scoped 2026-09-23:**
- `tools/build_lumiere_counterfactual_pairs.py`: deterministic (seed=42) patient pairing for v3 — every patient is
  assigned a partner with the OPPOSITE LIL volume-change direction (v3's real 20-up/32-down split makes this always
  achievable, 52/52). Not jointly optimized for DSCR's RANO label, but measured: 27/52 (52%) pairs also happen to
  differ in RANO. Output: `data/lumiere/v3/counterfactual_pairs.json`.
- `src/lumiere_loader.py`: new `counterfactual_pairs` param on `build_lumiere_cases()`/`load_lumiere()`. When set,
  for every phase, only the resolved image file(s) are swapped to the PARTNER's own rendered slices — stem, options,
  chain context, and image labels stay exactly the original patient's. Deliberately did NOT swap the image labels
  (e.g. "baseline (week-084)") to the partner's own timepoint ids — the label stays what the original patient's text
  says, so the manipulation is a pure pixel swap: text says X, the model is actually shown Y. Records
  `_counterfactual_partner` on each question for traceability.
  Verified with a dry-run (login node, no GPU): image_dir/image_path resolve to a genuinely different real patient's
  files for all 5 phases, 0/52 self-paired, swapped files confirmed to exist on disk.
- `run_lumiere.py`: new `--counterfactual-images` flag; results land in a `_cf`-suffixed folder
  (`lumiere_<model>_cf_v3_nogate_*`) so they can't be confused with the plain v3 image run already in hand.
- `src/evaluator.py`: `counterfactual_partner` field added to both result-dict construction paths (parse-success and
  salvaged-parse-failure) — additive, `.get()` returns None for every non-counterfactual run (OmniBrainBench and
  plain LUMIERE runs unaffected).

**Scope decisions (user, 2026-09-23):** all 5 phases swapped (not just LIL/DSCR) for completeness — AIA/PJRF/TCM
expected null (AIA is protocol-invariant; PJRF/TCM are single-image and largely text-driven per earlier findings).
Non-gated only (gated adds nothing per the 2026-09-22 redundancy finding, and would cut N on exactly the phases
under test). Metric: flip rate (own-image v3 answer vs counterfactual-image answer) as headline, with flips checked
against whether they land on the swapped-in patient's actual correct answer (distinguishes real visual uptake from
decoding noise).
**Caveat flagged in advance:** since all 5 phases are swapped together, PJRF/TCM's chain context includes text from
an upstream DSCR call that was itself run against a swapped image — their result isn't a perfectly isolated test of
"does PJRF's own image matter." LIL and DSCR remain the clean, headline comparison.

**Pre-registered expectation:** low flip rate on LIL/DSCR, not tracking the swapped patient's truth -> confirms
non-grounding directly (closing the loop from steps 1-3). A high flip rate that DOES track the swapped-in truth would
instead narrow the claim to "images are ignored because text is redundant here," not "models can't use images."

**Submitted:** 4 jobs (one per model, `lumicf_<model>`), `--item-set v3 --counterfactual-images`, non-gated —
43058034 (MedGemma-4B), 43058035 (Gemma-3-12B) running now; 43058036 (Gemma-3-27B, deps on 43058034), 43058037
(Llama-4-Scout, deps on 43058035) queued behind them.

## 2026-09-23 — v3 (leak-free) text-only ablation complete: image-non-grounding finding CONFIRMED on leak-free items
All 8 v3 jobs (43010721-43010728) COMPLETED overnight, exit 0, no failures. Full non-gated overall accuracy, image vs
text-only:
| Model | Image | Text-only | Δ |
|---|---|---|---|
| Llama-4-Scout | 49% | 52% | +3 |
| Gemma-3-27B | 54% | 50% | -3 |
| Gemma-3-12B | 48% | 51% | +3 |
| MedGemma-4B | 33% | 36% | +3 |

Per-phase, 3/4 models have text-only >= image on every phase; Gemma-3-27B is the exception (image ahead, mainly AIA
86% vs 77%), but per-phase CIs (n=52) overlap in every case, including that one. No model shows a real image
advantage anywhere.

**Reading against the pre-registration (2026-09-22, "Plan agreed + executed" section above):** text-only accuracy is
within CI of with-image for all 4 models, on the leak-free v3 set — this satisfies "claim supported" and, combined
with step 3's evidence fact-check (72-100% of correct answers' stated evidence copied straight from the prompt, not
image-derived), the non-grounding finding is now confirmed independent of the v2 stem/option leaks. This was the
open question from the leak-free rebuild: whether removing the leaks would restore image dependence. It did not.

Side note: v3 items are substantially harder than v2 across the board (image-based overall down 13-19pp per model,
e.g. Scout 67%->49%, MedGemma 45%->33%), consistent with the leak removal working as intended. DSCR remains at/near
its own majority baseline in v3 too (56-65% vs MajBase 64%) — still no model shows RANO-assessment skill above chance
given the class imbalance.

Not yet decided: whether to also run the counterfactual-image test (step 4 of the plan) now that steps 1-3 already
converged on the same answer, or treat this as sufficient and move to writing the section.

## 2026-09-22 (latest) — expert review confirmed OPTIONAL, not a blocker; artifact send is a nice-to-have
Prof. Wang confirmed sending `tools/lumiere_review_artifact.html` (rebuilt 2026-09-21, self-contained, localStorage
autosave + download/load-review-file flow, no `window.claude` refs) to the radiologist/neuro-oncologist collaborator
is OPTIONAL for now — consistent with the earlier v3 decision (see "v3 item set" entry below: "prof: expert review
optional for now"). **Correction to my own framing above:** I called this "the last blocker" — wrong. It isn't a
blocker at all: round-3/v3 evals already ran to completion on the unreviewed LLM-drafted items without it, and
sync -> `lumiere_merge_reviewed.py` isn't gating anything currently in flight. User will send it when convenient;
not time-critical.

## 2026-09-22 (round 3) — LIL image-labeling fix, majority-baseline reporting, AIA finding, MedGemma re-run — RESULTS IN

### LIL: images now labeled with their actual timepoint
Investigated whether presentation (not just model skill) contributes to LIL's direction-flip errors. Found: the two images (baseline,
follow-up) were always sent in the correct order but labeled only generically (`<image_1>:`, `<image_2>:`) — never tied to which
timepoint is which; the question text mentions the weeks in prose but nothing links that to the image numbers. Fixed, additively:
- `src/lumiere_loader.py`: new `_image_labels_for()` returns `["baseline (week-XXX)", "follow-up (week-YYY)"]` for LIL only (None
  elsewhere) -> stored as `_image_labels` on the question dict.
- `src/evaluator.py`: threads it through as `case["image_labels"]`.
- `src/prompts.py`: `_build_user_content()` takes an optional `img_labels` param; when present and length-matched, renders
  `<image_1> — baseline (week-000):` instead of the bare `<image_1>:`. Falls back to the exact old behavior when absent/mismatched —
  verified OmniBrainBench's `data_loader.py` never sets this field, so `run_omnibrain.py` is provably unaffected (dry-run checked, no
  GPU needed). Also nudged the instruction text to say "compare them explicitly... using their labels."

### New: majority-baseline column in every report (src/analysis.py, tools/compile_lumiere_results.py)
Added `_majority_baseline()`: per phase, the accuracy of a trivial "always guess the most common correct answer" baseline, shown as a
new `MajBase` column in `report.txt` and folded into `tools/compile_lumiere_results.py`'s tables (flagged inline when >=40%). Two real
findings this immediately surfaced, neither is a drafting bug — both are properties of the LUMIERE cohort itself, not fixable by
re-drafting:
- **DSCR (MajBase ~65-69%):** most LUMIERE GBM patients are progressing, so "Progressive disease" is both the correct answer AND the
  longest option label most of the time (see round-2 entry above — reframes that "69% longest=correct" number as class imbalance, not
  a guessability bug). Checked against round-2 non-gated DSCR accuracy: MedGemma 37%, Gemma-27B 59%, Gemma-12B 65%, Llama-Scout 63% —
  **every model is at or below this trivial baseline.** Report DSCR accuracy next to MajBase in the paper; don't present it as raw
  skill.
- **AIA (MajBase 100%):** ALL 54 patients' correct AIA answer is the identical string ("T1-weighted, contrast-enhanced T1-weighted,
  T2-weighted, and FLAIR sequences") — LUMIERE used one consistent imaging protocol for every patient. A baseline that always outputs
  that fixed string scores 100% without looking at any image; models score 52-96%, i.e. below that ceiling — they sometimes talk
  themselves into a wrong-sounding distractor despite the answer never varying. This means AIA does not test "identify modalities from
  the image" so much as "avoid hallucinating a wrong modality" — a real limitation of this phase to state plainly in the paper. Not
  fixable by re-drafting (it's a genuine property of the LUMIERE cohort, not a bug we introduced).
- PJRF/TCM's MajBase is near 0 (free-text numeric estimates, ~unique per item) — the column is harmless noise there, as intended.

### MedGemma-4B re-run: killed and resubmitted across all 4 models for consistency
Per-user decision: rather than let the already-running MedGemma re-run (jobs 42932294/42932295, parse-fix only, predates the LIL/MajBase
work above) finish on its own, killed both (`scancel`) and resubmitted ALL 4 models x {gated, nogate} = 8 jobs so every model's numbers
reflect the parse-fix + LIL image-labeling fix + MajBase reporting consistently. Job IDs: 42941575-42941582 (`lumiv4_<model>_<mode>`).
All 8 COMPLETED 2026-09-22 (00:35-12:41, exit 0; only 2 MedGemma nogate parse failures, both salvaged). Compiled ->
`results/lumiere_summary.md/.csv` (now = round 3).

### Round-3 results (non-gated accuracy; items still LLM-drafted, NOT expert-reviewed)
| Model | AIA | LIL | DSCR (MajBase 65%) | PJRF | TCM | Overall | Chain completion |
|---|---|---|---|---|---|---|---|
| Llama-4-Scout | 96% | 50% | 59% | 54% | 74% | 67% | 15% |
| Gemma-3-27B | 80% | 59% | 61% | 39% | 72% | 62% | 4% |
| Gemma-3-12B | 89% | 48% | 63% | 35% | 65% | 60% | 2% |
| MedGemma-4B | 54% | 52% | 39% | 33% | 46% | 45% | 4% |
- **LIL image-labeling fix helped every model** (round 2 -> round 3, non-gated): Scout 33->50 (+17pp), Gemma-12B 39->48 (+9), Gemma-27B
  54->59 (+5), MedGemma 46->52 (+6). AIA/DSCR/PJRF/TCM essentially unchanged, as expected (the fix only touched LIL). So part of the
  earlier LIL deficit was presentation (unlabeled timepoints), not model skill. LIL is still the steepest drop after AIA (~50-59%).
- **DSCR: all 4 models still at/below the 65% majority baseline.** No model shows response-assessment skill above "always say PD".
- **Chain completion is very low (2-15%)** — almost no patient gets all 5 phases right; Scout is clearly best.
- **Gating effect is mixed, not a clean signal:** conditional on upstream correctness, Scout's PJRF/TCM rise (60% n=15 / 89% n=9 vs 54%/74%
  non-gated) but Gemma-12B's PJRF falls (8% n=12 vs 35%). Gated n's are tiny and CIs overlap heavily — do not claim a gating effect yet.
- Correct-but-unfaithful counts are 0-3 per model — too few to support the "right for wrong reasons" story on this set.
- MedGemma-4B (the only medical-tuned model) is last overall — medical tuning at 4B does not beat general 12-27B models here.

### Gated runs are redundant with non-gated runs (checked 2026-09-22)
- Every question answered in a gated run was answered identically in the matching non-gated run: 106/106, 136/136, 140/140,
  155/155 (MedGemma, G-12B, G-27B, Scout), in all phases. Decoding is deterministic, and a question that passes the gate sees the same
  chain context either way. So a gated run is just a subset of the non-gated run and adds no new model behavior. Every gated number
  (gate-block rate, conditional accuracy, gated overall) can be recomputed offline from non-gated `raw_results.json`.
- LUMIERE has one question per phase, so with GATING_THRESHOLD=0.5 the "soft" gate is really a hard pass/fail on the upstream
  question. The gated "Overall" is lower only because blocked phases are scored 0. That is a scoring rule, not a model effect.
- Non-gated runs also give the comparison arm the gated runs can't: accuracy when upstream was WRONG. P(phase correct | all upstream
  correct) vs P(... | some upstream wrong), non-gated:
  - MedGemma: LIL 52 vs 52, DSCR 40 vs 38, PJRF 33 vs 33, TCM 100 (n=2) vs 46
  - G-12B: LIL 44 vs 83 (n=6), DSCR 57 vs 67, PJRF 8 vs 43, TCM 100 (n=1) vs 64
  - G-27B: LIL 58 vs 64, DSCR 56 vs 66, PJRF 29 vs 42, TCM 50 (n=4) vs 74
  - Scout: LIL 48 vs 100 (n=2), DSCR 60 vs 59, PJRF 60 vs 51, TCM 89 vs 71
  **No consistent error propagation:** getting upstream phases right does not predict getting downstream right (the Gemmas are often
  better AFTER an upstream error). Scout shows the expected direction only on PJRF/TCM, with overlapping CIs. So at this item quality
  and n=54, the data do NOT support the causal-degradation claim. Possible causes: the phases may be answerable independently (the
  MCQ gives enough text context), the items are still unreviewed, or n is too small.
- Decision pending: future runs (especially the paid API models) can be non-gated only, with gating applied as an offline scoring pass.

### "Right answer for wrong reasons": the zero count is a weak metric, not a negative finding (checked 2026-09-22)
- `local_faithful` (src/evaluator.py) asks the SAME model to predict the answer from its own reasoning. The reasoning already restates
  the chosen option in 781/1078 answers (72%, round-3 non-gated, all 4 models), so the probe nearly always "recovers" it. It flagged
  4 of ~1,000 correct answers. This tests self-consistency, not whether the reasoning is right. A near-zero count is expected by
  construction.
- `kb_alignment_faithful` flags correct answers almost only in AIA (25-47 per model), where the answer is a fixed list of sequence names
  (vocabulary artifact). It flags 0-6 in LIL and 0-1 in DSCR/PJRF/TCM. It isn't usable as a wrong-reasons signal either.
- Proposed ways to actually test the claim, none run yet:
  1. Fact-check the reasoning against LUMIERE ground truth (`data/lumiere/facts/*.json`: hemisphere/region, volumes, change
     direction, RANO) -> "correct answer, reasoning contradicts the facts". Uses existing raw_results, no GPU needed.
  2. Blind baseline via the existing `run_lumiere.py --text-only`: accuracy that survives without images is not image-grounded.
  3. Counterfactual images (another patient's scans / L-R flip): the answer should change and doesn't -> not grounded.
  If 1-3 also come up empty, drop the claim and reframe around the validity findings (no error propagation, below-majority DSCR).

### Plan agreed + executed (2026-09-22): where do correct answers come from — image, question text, or neither?
Steps: (1) stem-leakage audit, (2) text-only ablation, (3) evidence fact-check, (4) counterfactual images only if still
unclear. Choices: steps 1+2 in parallel; rule-based checks only (no LLM judge); tell Prof. Wang after step 1's numbers.
Pre-registered reading: text-only accuracy within CI of with-image AND evidence mostly copied/wrong -> claim supported
("correct because of text, not image"); clear text-only drop AND image claims check out -> drop the claim.

**Step 1 — stem leakage (`tools/audit_stem_leakage.py` -> `results/lumiere_stem_leakage.md/.csv`).** Rule-based lower bound:
| Phase | Self leak (stem states own answer) | Upstream leak (stem states earlier phase's answer) | Any |
|---|---|---|---|
| AIA | 0% | — | 0% |
| LIL | 13% (7) | — | 13% |
| DSCR | 0% (exact label) | 98% (47/54 give LIL's exact % volume change) | 98% |
| PJRF | 31% (17/54 state the actual survival, e.g. "She survived 93 weeks") | 72% (39 name the RANO label) | 85% |
| TCM | — | 98% (44 give LIL %, 33 name the RANO label) | 98% |
- The drafter wrote each later stem as a self-contained vignette restating earlier findings. This breaks the chain design: a model
  that got LIL/DSCR wrong is handed the right answer in the next stem. **This likely explains the null error-propagation result above.**
- The PJRF self-leaks are straightforward drafting bugs (the question gives the outcome, then asks which profile "explains" it).
- A word-overlap guesser (pick the option sharing the most words with the stem) is at or below chance (2-30%). The leak is semantic
  (e.g. "+67% volume" -> PD), not lexical, so simple overlap doesn't catch it.
- Fixing this means re-drafting stems (dataset change -> expert review + Prof. Wang's sign-off). Not done.

**Step 2 — text-only ablation:** jobs 43005289-43005292 (`lumitxt_<model>_nogate`, non-gated, `--text-only`). Added
`EXTRA_ARGS` passthrough to `shell/lumiere/lumiere_prelim_ollama.sbatch`. Results in `results/lumiere_<model>_textonly_nogate_*`.
All 4 COMPLETED 2026-09-22 (16:25-17:09). Text-only vs round-3 with-image (v2 items, non-gated):
| Model | AIA | LIL | DSCR | PJRF | TCM | Overall |
|---|---|---|---|---|---|---|
| Llama-4-Scout | 89 (96) | 46 (50) | 61 (59) | 54 (54) | 74 (74) | 65 (67) |
| Gemma-3-27B | 78 (80) | 52 (59) | 57 (61) | 43 (39) | 76 (72) | 61 (62) |
| Gemma-3-12B | 93 (89) | 41 (48) | 63 (63) | 39 (35) | 65 (65) | 60 (60) |
| MedGemma-4B | 57 (54) | 50 (52) | 24 (39) | 39 (33) | 54 (46) | 45 (45) |
(text-only, with-image in parentheses.) Removing the images costs 0-2pp overall. Every per-phase difference is inside the
n=54 CIs except MedGemma DSCR (-15pp). LIL drops a little for 3/4 models (4-7pp) but stays in CI. **On v2 items, accuracy
does not depend on the images.** This matches the pre-registered "claim supported" reading (together with step 3's 72-100%
copied-only evidence), and it is consistent with the stem leakage from step 1. v3 (leak-free) image vs text-only is the
test of whether this holds once the leaks are removed.

**Step 3 — evidence fact-check (`tools/audit_reasoning_facts.py` -> `results/lumiere_reasoning_facts.md/.csv`).** Each claim in
visual_grounding+reasoning (hemisphere; measurements with units) is sorted into: copied (appears in the stem, options, or prior-chain
text the model saw), supported (not shown, matches facts), fabricated (not shown, matches no fact), or laterality flip.
- **Correct answers' evidence is almost entirely copied from the prompt:** copied-only 72-100% of correct LIL/DSCR/PJRF/TCM answers
  across all 4 models. Supported-and-not-shown is 0-6%. The stated "visual grounding" almost never contains a correct fact the model
  could only have gotten from the image.
- **Fabricated measurements are rare on correct answers** (0-8%, mostly Gemma-12B/Scout LIL, e.g. Scout "baseline ~120-130 cm^3").
  They are more common on INCORRECT DSCR answers (15-29%). So "right answer + false stated facts" is rare; fabrication tracks errors.
- **Laterality: a display-convention confound, not model error.** Slices are rendered in radiological orientation: FSL MNI grid,
  patient-right at voxel 0, then np.rot90 in `src/lumiere_facts.py:_render_axial_slice_png` -> patient-right on screen-left. The
  prompt never states this. In AIA (no hemisphere in the prompt), models' hemisphere claims mostly disagree with the segmentation:
  Scout 8/9, Gemma-27B 9/11. That fits reading screen-left as "left". So the models ARE locating the lesion on the image, just
  under the other convention. Reported as its own label, not as wrong reasons. Fix candidates: state the convention in the prompt,
  or render in neurological orientation. Either would change the stimulus, so it needs a decision.
- Fixes to the checker made during validation: RANO criteria thresholds cited in reasoning ("≥25% increase") were being counted as
  fabricated measurements -> now skipped.
- Interim reading: in the sense of "correct answer but reasoning states false facts", the claim is weak (0-8%). In the sense of
  "correct answer whose stated evidence is not image-derived", it is strong (72-100% copied-only). That second sense is what step 2
  tests directly.

## 2026-09-22 — v3 item set: leak-free stems/options + post-op baselines (prof: expert review optional for now)
Decisions (user): rewrite items so no later stem/option restates an earlier answer; DSCR shown BOTH images; add an
orientation line to the prompt in the same pass; post-op baselines; run the same 4 open models (no API models).
v2 is kept intact and runnable (`run_lumiere.py --item-set v2|v3`, default v2), so "leaky vs leak-free" is itself a result.
- **Leak rules** (`src/lumiere_leakage.py`, shared by the drafter's retry loop and the audit): stems may state only patient id,
  timepoints and non-imaging clinical facts. DSCR/PJRF/TCM stems: no %, volumes/measurements, regions, change words, or RANO
  labels. PJRF stem: no survival duration. PJRF/TCM options: no imaging findings or RANO labels (options differ by prognosis /
  action). LIL stem: no % change, follow-up-only region, or direction. Under these rules v2 violates LIL 7, DSCR 54, PJRF 48,
  TCM 54 of 54. **TCM options leaked too** (50/54 correct options described the direction of change, 26 named the RANO label),
  so PJRF/TCM needed full redrafts, not stem edits.
- **Root cause in the drafter:** `build_draft_prompt` fed each phase the earlier phases' correct answers, and the DSCR
  instruction told it to let the quiz-taker "infer [the label] from lesion/volume-change facts" -> stems restated them.
  Leak-free mode (`--leak-free-set v3`) still shows the drafter the upstream truth, for consistency, but forbids restating
  it, and retries with the violations fed back (up to 8 attempts).
- **DSCR stem is a fixed template (no LLM)** built from real table fields only: extent of resection (CRET/PRET), re-resection
  between the scans, whether the baseline is pre-/post-op, and "within 3 months of radiotherapy" (LessThan3Months). Options
  and answer are unchanged (the 4 RANO labels). **Found: v2 DSCR stems invented clinical details** ("clinically stable without
  corticosteroid escalation"). LUMIERE has no steroid or neurological-status fields.
- **Post-op baselines (`src/lumiere_facts.py::rebaseline_to_postop`, `--postop-baseline-set v3` -> `data/lumiere/v3/facts/`).**
  v2 used the earliest imaged scan as the LIL baseline, which was pre-operative for 42/54 patients. So LIL's "volume
  change" mostly measured the resection, while RANO (DSCR) is judged against the post-op scan. v3 baseline = the latest
  imaged Post-Op scan before the follow-up (a re-resection before the follow-up resets it). Baseline changes for 44/54.
  Follow-up, DSCR/PJRF/TCM facts and answer keys are unchanged. **Patient-049 and Patient-068 are excluded from v3 (52
  patients):** their post-op scans lack CT1 + segmentation (049) or are absent from the imaging table (068). Keeping them
  on a pre-op baseline would mix two baseline definitions.
- Orientation: `config/lumiere.py::IMAGE_ORIENTATION_NOTE` ("radiological convention: patient's right on image left") is
  prepended to image content for v3 only (via loader `_image_note` -> evaluator -> `prompts._build_user_content`).
  OmniBrainBench and v2 are unaffected (verified that v2 loading is unchanged).
- Drafter: Claude-4.5-Sonnet via own LiteLLM proxy on login-node port 8011 (8001 was already bound). Caveat for the
  paper: Claude drafts the items and is on the roster -> footnote if it's ever evaluated on v3.
- FSL for the atlas lookup: `module load fsl/6.0.7` (a bare `module load fsl` doesn't set FSLDIR).

### v3 built + validated; DSCR answerability problem found and fixed (2026-09-22)
- Rebaseline: 52 facts in `data/lumiere/v3/facts/`, 44 baselines changed, all new slices rendered. Volume change is now
  20 up / 32 down (v2 was dominated by resection-driven drops).
- Drafting (Claude via port-8011 proxy; stopped after): 52/52 patients clean. About 45 retries where the drafter restated a
  finding and the fed-back violation fixed it. `tools/audit_stem_leakage.py --item-set v3` -> **0 v3-rule violations in
  every phase** (`results/lumiere_stem_leakage_v3.md`). Hand-read 008 and 034 end to end: answer keys match the facts
  (PJRF 93w -> "18-24 months", 74w -> "12-18 months"; TCM PD -> second-line, SD -> continue TMZ). Minor: PJRF/TCM stems
  mention baseline+follow-up imaging but only the follow-up image is attached (the model has its chain context);
  LIL options quote mm³ volumes the model can't measure from a 2D slice (it discriminates on direction/%/location).
- **DSCR answerability (important, affected v2 too):** only ~18/52 expert RANO ratings agree with the baseline->follow-up
  volume change the model sees (rough check: total volume incl. edema vs thresholds; RANO really uses 2D enhancing
  products). 23 of 35 PD ratings come with SHRINKING total volume. Reasons: the rating rests on evidence not in the rendered
  contrast-enhanced T1 slice (T2/FLAIR progression, 23 items; new or non-measurable lesions), and RANO judges PD against the
  nadir, not the post-op scan. v2 hid this because its stems stated the key finding ("T2/FLAIR progression").
  **Decision (user): give DSCR the rater's recorded findings as a radiology-report line** (`_report_findings()` in
  `src/lumiere_drafter.py`: abbreviations expanded, "(PD according to clinic)" stripped since it names the label,
  "Less than 3 months" dropped since the template states it; 41/52 have a rationale, 11 have none -> no line).
  Leak rule for the DSCR stem relaxed to allow the report's own findings; it still bans LIL's % change, regions and any
  RANO label (`--refresh-dscr v3` re-applied in place; still 0 violations). Consequence to state in the paper:
  DSCR is now partly text-answerable ("apply RANO to image + report", like a clinician). The text-only arm measures how much.
  Note: the legacy "upstream leak" column of the audit now flags 19 DSCR items only because it treats any change word as
  LIL's answer. These are report words, and none contain LIL's %. The v3-rule column is the relevant one.
- Also still open: the one rendered slice is contrast-enhanced T1 only, so T2/FLAIR findings are never visible in images
  (LIL included).
- Submitted 8 v3 jobs 43010721-43010728 (`lumiv3img_<model>`, `lumiv3txt_<model>`; non-gated; `EXTRA_ARGS="--item-set v3
  [--text-only]"`). Results -> `results/lumiere_<model>[_textonly]_v3_nogate_*`.

### RESULTS (2026-09-22): v2/v3 x with-image/text-only, non-gated, all 4 models (12 new jobs, all COMPLETED)
Full table: `results/lumiere_summary_all.md` (Wilson CIs, majority baseline). v3 = 52 patients, v2 = 54.
| Model | v2 image | v2 text-only | v3 image | v3 text-only |
|---|---|---|---|---|
| Llama-4-Scout | 67% | 65% | 49% | 52% |
| Gemma-3-27B | 62% | 61% | 53% | 50% |
| Gemma-3-12B | 60% | 60% | 48% | 51% |
| MedGemma-4B | 45% | 45% | 33% | 36% |
(overall = mean per-case score)

**1. Images add nothing measurable, in either item set.** The paired, same-question comparison gives 87-91% identical
correctness with vs without images for every model/set. "Right only with image" roughly equals "right only without":
v2 66 vs 58, v3 55 vs 67 (summed over models). Text-only is never meaningfully worse, including LIL, the phase that most
needs the image. This is the strongest result so far and the defensible form of the "right answer for wrong reasons" claim:
**correct answers are not image-grounded.** It holds after the leaks were removed, so it's not a leak artifact.
**2. The v2 leaks inflated scores by 9-18 points overall** (Scout 67->49, G-27B 62->53, G-12B 60->48, MedGemma 45->33).
TCM fell most (v2 65-74% -> v3 27-60%). LIL fell 48-59% -> 23-40% (leak removal + post-op baselines). AIA and DSCR changed
little. Caveat: v2->v3 also changed baselines, the DSCR report line, orientation note and 2 patients, so the drop isn't
attributable to leak removal alone.
**3. LIL is at chance on v3** for Gemma-12B (23%), Gemma-27B (27%) and Scout (25%) (4 options -> 25%). MedGemma 40%.
Text-only LIL is the same (23-38%). Models can't read lesion change off the two slices.
**4. DSCR is still at or below the majority baseline (64%)**: G-27B 65, Scout 58, G-12B 56, MedGemma 14% (far below chance).
Even with the report findings, no model applies RANO better than "always PD".
**5. Error propagation: still not supported on v3.** P(correct | upstream right) vs (| upstream wrong) is inconsistent in
sign across models and phases. For the immediate predecessor: Scout DSCR 77 vs 51 and MedGemma PJRF 62 vs 32 / TCM 42 vs 18
go the expected way, while Gemma-27B PJRF 18 vs 50, G-12B TCM 29 vs 43 and Scout TCM 25 vs 42 reverse. Most cells have
n<20. **With LIL at chance, whether upstream is "right" is mostly luck, so there's little real signal to propagate.** The
chain can't show causal degradation until the perception phases are above chance.
**6. Evidence fact-check (v3):** correct answers' stated evidence is still mostly copied from the prompt (43-90%, except
Gemma-27B, which now mostly cites no checkable claim). Image-supported claims 0-8%. Consistent with (1).

**Implications for the paper (for discussion with Prof. Wang):**
- Claim 2 (right for wrong reasons) -> **supported in a sharper form**: "models' correct answers do not depend on the image;
  a text-only ablation matches with-image accuracy on 87-91% of questions." This is the headline candidate.
- Claim 1 (causal degradation) -> **accuracy does fall from AIA to later phases, but error propagation is not
  demonstrated.** It can't be tested while LIL is at chance. Options: make perception answerable (more/better slices,
  FLAIR, fewer mm³ distractors), or reframe claim 1 as phase-wise difficulty rather than propagation.
- Benchmark-validity findings worth reporting: stem leakage inflates scores 9-18 pts; pre-op baselines; DSCR ratings not
  derivable from the shown image (~18/52); invented clinical details in LLM-drafted stems.

## 2026-09-22 (later) — three follow-ups executed: PJRF re-draft caveat, comparison tool, LIL/MedGemma investigations

### 1. PJRF/TCM "before -> after" caveat (important for how the numbers are described)
`draft_patient_chain`'s retry loop makes a FRESH LLM call each retry — it does not edit the existing item's wording. Checked: 0 of 54
PJRF items have identical `correct_answer_text` between round 1 and round 2 (e.g. "12-14 months" -> "13-15 months, representing survival
beyond one year despite..."); question TYPE is unchanged (52/54 "survival-estimate" in both rounds). **So the round1->round2 PJRF/TCM
delta is bias-removal + ordinary item-resampling variance (temperature 0.7 draft calls) confounded together, not a controlled edit of the
same item.** Correct framing for the paper: "the new, less-guessable item set produces lower accuracy," not "de-biasing this exact item
caused an N-point drop." Does not change the headline conclusion (old TCM/PJRF numbers were inflated by guessability) — only how precisely
we can attribute the exact point-drop.

### 2. `tools/compile_lumiere_results.py`: two-round comparison support (adapted, run)
Added `latest_runs(before=, after=)` and `--split-at TIMESTAMP` (+ `--before-label`/`--after-label`) so one command produces a before/after
table instead of only ever showing the latest run per model. Ran it: `results/lumiere_compare_round1_round2.md` (full table, all phases,
gated+non-gated, all 4 models). Default no-args behavior unchanged (latest run per model) — now written to `results/lumiere_summary.md/.csv`
and, since round 2 is now latest, reflects round 2 only; round 1 is preserved in its own `results/lumiere_*_20260921_1[6-7]*/` folders and in
the compare table.

### 3. LIL bottleneck: real finding, not just item difficulty — and a correction to the "perception failures" framing
- **Correction:** `config.FAILURE_TYPE` assigns "perception" to any wrong AIA/LIL answer and "decision"/"reasoning" to wrong PJRF/TCM/DSCR
  answers **by fixed phase label, not by diagnosing the actual failure**. So "perception failures dominate (31-55/run)" reported earlier is
  largely tautological — LIL has the most questions and is *labeled* perception regardless of why the model got it wrong. Correcting this
  framing before it goes in the paper.
- **Real, substantive finding (checked directly against round-2 non-gated raw responses):** LIL questions ask for volume-CHANGE direction
  (increase/decrease) between baseline and follow-up. Isolating wrong answers where both the correct and model answer text state a direction:
  Gemma-3-12B flips direction (says grew when it shrank, or vice versa) in 17/25 (68%) of its wrong LIL answers; Llama-4-Scout 15/28 (54%);
  Gemma-3-27B 9/20 (45%); MedGemma-4B 4/17 (24%). This IS a genuine, independently-verified perception/longitudinal-comparison failure — models
  struggle specifically at comparing two scans over time, not just at reading a single image. Worth a paper claim on its own (a real
  capability gap, distinct from the tautological phase-label framing above). Not yet checked: region-naming-only errors (right direction,
  wrong volume/region) as a separate bucket, or whether this correlates with the raw magnitude of the true volume change.

### 4. MedGemma-4B parse failures: root cause found (two distinct causes), fixed for future runs
- All 27 parse failures across every MedGemma run so far (round 1 + round 2, gated + non-gated) were checked directly against saved
  `raw_response` text. Two distinct causes, not one:
  - **24/27: genuine truncation.** Repetition loop inside `visual_grounding`/`reasoning` hits `MAX_TOKENS=800`; JSON never closes. Confirmed
    the answer field is always written and complete before this happens (schema puts "answer" first) — 27/27 parse failures had a clean,
    recoverable `"answer": "X"` even when truncated.
  - **3/27: NOT truncation — a strict-JSON quirk.** MedGemma occasionally emits a literal (unescaped) newline inside a string value; the JSON
    is otherwise complete and valid, but Python's `json.loads(strict=True)` rejects the bare control character.
- **Fix shipped in `src/evaluator.py`** (additive, default behavior unchanged for other models/OmniBrainBench — `run_omnibrain.py`'s
  `CausalChainEvaluator(...)` call is untouched):
  - `_loads_lenient()`: retries `json.loads(..., strict=False)` before giving up → recovers the 3/27 losslessly (full answer + reasoning +
    visual_grounding, faithfulness probe can run normally on a live re-run).
  - `_salvage_answer_letter()`: regex-extracts the answer letter from otherwise-unparseable (truncated) JSON → recovers the other 24/27's
    answer, scored correctly; `answer_salvaged: true` flag added to the result dict; `visual_grounding`/`reasoning`/faithfulness/KB-alignment
    stay "not computed" (None/0.0) for these, since that text was never generated.
  - Verified against all 27 historical parse failures: 3 now fully parse, 24 salvage the answer, 0 remain unrecoverable.
- **Decision: did NOT retroactively rescore existing result files.** Gating is sequential/dynamic (each phase's pass/block depends on the
  running score), so patching an early phase's answer after the fact doesn't cleanly propagate to whether a later phase would have gated
  in/out — editing raw_results.json post hoc would produce an inconsistent, unreproducible record. **Recommendation: re-run MedGemma-4B
  (gated + non-gated) fresh now that the fix is in**, rather than hand-editing old JSON; the old runs stay as "pre-fix" for the record. This
  is ~2 short GPU jobs (round 1: 29 min gated, 75-83 min non-gated) — not yet submitted, holding for go-ahead.
  **Superseded (see round-3 section above, dated the same day but written later):** rather than a MedGemma-only re-run, all 4
  models x {gated, non-gated} were killed/resubmitted together (jobs 42941575-42941582) so every model reflects the parse-fix +
  LIL fix + MajBase consistently. Done — this recommendation is resolved, not still open.

### Still open (not executed — need your input, not just compute)
- **Text-only baseline:** capability now exists (`run_lumiere.py --text-only`, threaded through `CausalChainEvaluator(text_only=...)`,
  strips images before the main call; `run_omnibrain.py` unaffected — flag defaults off). Not yet run — need to agree scope (which
  model(s), gated/non-gated, all 5 phases or just PJRF/TCM/LIL) before spending GPU time.
- **Send the rebuilt review artifact to the expert:** this needs the user to actually send `tools/lumiere_review_artifact.html` (or its
  location) to the radiologist/neuro-oncologist collaborator — not something to execute from here without reviewer contact info.

## 2026-09-22 — round-2 results in: item fix confirmed (TCM/PJRF drop as predicted), gated chain-completion collapsed

**All 8 re-eval jobs COMPLETED, no failures** (job IDs 42918287-42918294; results in new `results/lumiere_<model>[_nogate]_2026092[12]*/`, round-1 results
kept as the pre-fix baseline; wall-clock 29 min - 2h 07m, in line with round 1).

### Non-gated PJRF/TCM, old items vs fixed items (N=54, directly comparable)
| Model | TCM old -> new | PJRF old -> new |
|---|---|---|
| MedGemma-4B | 91% -> 56% | 48% -> 33% |
| Gemma-3-12B | 96% -> 68% | 68% -> 35% |
| Gemma-3-27B | 94% -> 72% | 63% -> 39% |
| Llama-4-Scout | 100% -> 78% | 68% -> 57% |

Every model now sits well above the item's own length-guessing floor (~25-30%, see section 2/3 above) but well below the old ceiling — reads as "the fix
removed the shortcut without erasing all signal," i.e. TCM/PJRF now measure something closer to the intended task. Other phases (AIA/LIL/DSCR) essentially
unchanged from round 1 (not re-drafted), as expected.

### Side effect: gated chain completion collapsed
| Model | Chains completed (gated), old -> new |
|---|---|
| MedGemma-4B | 3/54 -> 1/54 |
| Gemma-3-12B | 5/54 -> 1/54 |
| Gemma-3-27B | 8/54 -> 1/54 |
| Llama-4-Scout | 9/54 -> 7/54 |

With PJRF/TCM genuinely harder, the gate now blocks nearly everyone before TCM for 3 of 4 models — gated PJRF/TCM N is now 1-4 for most models (worse than
round 1's already-low 3-13). **Recommendation: lean on non-gated numbers for PJRF/TCM in the paper** (as already decided for round 1); report the gated
chain-completion rate itself as a finding — models rarely sustain quality across all 5 phases — rather than trying to report gated PJRF/TCM accuracy at
these Ns.

### Next
1. Rebuild the full old-vs-new comparison (all phases, gated+non-gated) — `tools/compile_lumiere_results.py` not yet adapted for a two-round comparison.
2. Investigate PJRF's larger-than-length-bias-alone drop (e.g. MedGemma 48%->33% despite length bias only 59%->37%) — check whether the wording/content
   changed substantively, not just length.
3. Still open from before: text-only baseline, LIL bottleneck, MedGemma parse-failure handling, send the rebuilt review artifact to the expert.
4. Still uncommitted: notes/, new tools, modified src/ and shell/ files, new results/.

---

## 2026-09-21 (latest) — preliminary LUMIERE runs done (8/8); items found guessable; PJRF/TCM re-drafted, swapped in, artifact rebuilt

**Status: source of truth for this work is this file.** (`notes/notes.md` is the user's personal scratch; not maintained by Claude.)

### 1. Preliminary runs (all COMPLETED, no job errors)
- 54 LUMIERE patients, 5 phases, LLM-drafted **unreviewed** items (`--include-unreviewed`), 4 open models (MedGemma-4B, Gemma-3-12B,
  Gemma-3-27B, Llama-4-Scout; Ollama 0.33.0, Q4, RTX PRO 6000 96GB, temp 0, MAX_TOKENS 800), each **gated** (proposed protocol) and **non-gated**
  (ablation, every phase asked). Results: `results/lumiere_<model>[_nogate]_<timestamp>/`; logs `logs/lumi_*`. Runtimes: gated 29-77 min, non-gated 75-143 min.
- Overall accuracy gated / non-gated (do NOT compare across columns — different question mix): MedGemma 31.6/54.7, Gemma-12B 52.7/70.9,
  Gemma-27B 52.6/69.1, Llama-4-Scout 58.2/72.1. Chain completion 3/5/8/9 of 54 (same gated and non-gated).
- Per-phase non-gated accuracy: AIA 52/87/80/94, LIL 46/39/54/35, DSCR 37/65/56/63, PJRF 48/68/63/68, TCM 91/96/94/100 (MedGemma/12B/27B/Scout).
- Observations: LIL is the weakest phase for every model (31-54%) and drives the gate; perception failures dominate the failure taxonomy (31-55/run);
  correct-but-unfaithful is rare (0-3), so the "right answer for wrong reasons" safety framing has thin support on this data; 27B does not
  clearly beat 12B (overlapping CIs); the gate's selection effect differs by model (higher later-phase accuracy when gated for MedGemma/Scout, lower for
  12B, equal for 27B). MedGemma-4B has 11 non-gated / 3 gated parse failures (repetition loop hits MAX_TOKENS); decision on handling deferred.
- Gated PJRF/TCM rest on 3-13 patients: report separately with Wilson CIs, never pooled.
- Not run: the 3 proprietary API models.

### 2. Finding: the drafted items are guessable from form (invalidates the TCM number)
- TCM accuracy of 91-100% is largely an artifact. Answer-letter position is NOT the cause (post-shuffle key balanced; models' answer letters track the key).
- **Option length is:** correct option is the longest in AIA 37%, LIL 63%, DSCR 69%, PJRF 59%, TCM 89% (chance 25%); TCM correct averages 139 chars vs 103
  for distractors. "Always pick longest" ~ the models' TCM scores.
- **Wording cue (TCM):** correct options are hedged ("repeat imaging in 4-8 weeks to distinguish pseudoprogression...") while distractors are absolute
  ("immediately discontinue...", "definitively"). A hedge-minus-absolute keyword guesser picks the correct TCM option in 74% of original items (0% other phases).
- Tool: `tools/check_option_bias.py` (per-phase longest-option rate, mean lengths, keyword-guesser rate). Word lists are ad hoc -> rough lower bound.
- Paper implication: the runs above are the **pre-fix baseline** and must be reported as such (not silently discarded); DSCR/PJRF/LIL are probably inflated
  too; text-only (no-image) baseline still to run for a stronger guessability estimate.

### 3. Fix in progress (option-length bias)
- `src/lumiere_prompts.py`: system prompt gained an answer-length rule (options within ~15% length, same detail/hedging/register, no curt absolute
  distractors, vary the correct letter).
- `src/lumiere_drafter.py`: `_length_biased()` + retry loop (reject if correct option >5% longer than the longest distractor; up to 5 retries); new flags
  `--phases`, `--out-dir`, `--base-url`, `--fix-biased`. First pass used 15%-over-mean-distractor / 3 retries and only reached 44% (PJRF) / 57% (TCM)
  longest-correct; tightened, re-drafted 16 patients in place (12 retries).
- Re-drafted PJRF+TCM for all 54 patients into `data/lumiere/drafts_v2/` (Claude-4.5-Sonnet via own LiteLLM proxy on login-node port 8011; port 8001 was
  occupied by an unknown service, so it was not used). AIA/LIL/DSCR carried over unchanged (incl. ct1 fixes). Patient-041's TCM initially failed to
  parse and was filled by the fix-up pass. Live `data/lumiere/drafts/` NOT yet replaced (data dir is gitignored).
- Result (longest = correct): PJRF 59% -> 37%, TCM 89% -> 43%; mean TCM length 260 vs 258. **TCM wording cue NOT fixed** (keyword guesser 76% on new drafts;
  PJRF 0%).

### 4. TCM wording-cue fix and swap into live drafts (2026-09-21, later)
- `src/lumiere_prompts.py`: TCM instruction gained a STYLE RULE (every option a cautious, defensible recommendation with the same structure: action +
  monitoring/reassessment + rationale; no abrupt/absolute distractors; correct answer must not be the only one mentioning monitoring/repeat imaging).
- `src/lumiere_drafter.py`: `_cue_biased()` (hedge-minus-absolute keyword guesser) added to the retry check for TCM (`_biased()` = length OR cue); `HEDGE`/`ABSOLUTE`
  word lists now live here and `tools/check_option_bias.py` imports them. Re-drafted TCM in `drafts_v2/` (41 patients + a fix-up pass; 28+ retries; 1 initial
  parse failure retried successfully).
- Final `drafts_v2` numbers: TCM longest-correct 89% (original) -> 30%; mean length 297 vs 298; keyword guesser 74% -> 0%. PJRF 59% -> 37%. AIA 37%, LIL 63%,
  DSCR 69% unchanged (not re-drafted; DSCR options are short labels, needs a different check). All 270 items valid, 5 phases for all 54 patients.
- **Swapped into live `data/lumiere/drafts/`** (only PJRF/TCM changed) and **rebuilt `tools/lumiere_review_artifact.html`** (270 items, 108 images, 2.71 MB, no
  `window.claude`, new TCM text confirmed present). Backups: `data/lumiere/_backup_drafts_pre_v2_20260921/`, `_backup_review_artifact_pre_v2_20260921.html`,
  `_backup_drafts_v2_pre_tcm_wording_20260921/`. `data/lumiere/reviewed/` left untouched (all 269 items pending, different schema, regenerated by the sync step when the
  expert returns their file). LiteLLM proxy on port 8011 stopped. Logs: `logs/redraft_v2*.log`.
- Caveats: guessability checks are heuristics (ad hoc word lists; not a model baseline); the drafter (Claude) shares a family with one proprietary eval model; the
  earlier 8 runs used the OLD PJRF/TCM items and are the pre-fix baseline; the review artifact previously sent (if any) is now stale — send the rebuilt one.

### 4b. Re-evaluation on the fixed items (submitted 2026-09-21)
- **Pipeline gotcha found before submitting:** `src/lumiere_loader.py::merge_reviewed` reads question/options/answer from `data/lumiere/reviewed/`
  (drafts/ is used only to backfill `timepoint`/`facts_used`). Swapping `drafts/` alone would have silently re-run the OLD PJRF/TCM items. Refreshed the 108 PJRF/TCM
  rows in `reviewed/` from the new drafts (all were `pending`, no expert edits; backup `data/lumiere/_backup_reviewed_pre_v2_20260921/`). Verified drafts vs reviewed
  question/options/answer identical for all 270 items, and that the loader's TCM questions (54/54) equal the new drafts. **After the expert returns their file, the sync
  step will overwrite `reviewed/` — this coupling matters for future re-drafts.**
- TCM now has 54 patients (was 53; Patient-041's TCM item was filled in), so PJRF/TCM N differs by one from round 1.
- Submitted 8 jobs (same script/settings as round 1: `shell/lumiere/lumiere_prelim_ollama.sbatch`, hpg-rtx6000, 1 RTX PRO 6000, Ollama 0.33.0, temp 0,
  `--n-cases 54 --include-unreviewed`), one per model x {gated, nogate}, names `lumiv2_<model>_<mode>`: job IDs 42918287-42918294. Results land in new timestamped
  `results/lumiere_<model>[_nogate]_<timestamp>/` (round 1 results kept as the pre-fix baseline). Expected wall-clock ~0.5-2.5 h per job (round 1: gated 29-77 min,
  non-gated 75-143 min). Old-vs-new comparison table to follow.

### 5. Next
1. (DONE, see section 4) TCM prompt + re-draft + swap + artifact rebuild.
2. Send the REBUILT artifact to the expert (do not send older copies).
3. (SUBMITTED, see 4b) Re-run gated + non-gated evals on new items; then report old vs new side by side per phase (expect TCM to drop from 91-100%).
4. Text-only baseline; investigate LIL bottleneck; run `tools/compile_lumiere_results.py` (not yet run/checked); decide MedGemma parse-failure handling.
5. (DONE) LiteLLM proxy on 8011 stopped.
6. Still uncommitted: notes/, new tools, modified src/ and shell/ files.


---

## 2026-09-21 — professor's constraint: no China-developed models; Llava-Med dropped; roster now 7 (3 API + 4 open)

**Decision (professor):** remove all China-developed models from the project. Llama- and
Gemma-family models are explicitly fine ("llama, gemma, these kind of models").

- **Removed:** Qwen2.5-VL-7B, Qwen3-VL-30B, InternVL3-38B, HuatuoGPT-V-34B, Lingshu-32B
  (DeepSeek was already banned on HiPerGator, 2026-08).
- **Kept:** GPT-5, Claude-4.5-Sonnet, Gemini-2.5-Pro (API); MedGemma-4B (Google),
  Llava-Med-7B (Microsoft; Mistral-7B base, community "-hf" re-upload).
- **Added (Ollama, default Q4 quant, 1 L4 each):** Gemma-3-12B (`gemma3:12b`),
  Gemma-3-27B (`gemma3:27b`), Llama-3.2-Vision-11B (`llama3.2-vision:11b`), category
  `general` in `config/models.py`.
- **Side effect:** the old unsolved 30B+ VRAM/tensor-parallel problem is gone — nothing in
  the roster needs more than one L4. `lumiere_vllm_b200.sbatch` is unused.
- **Files updated:** `config/models.py`, `task.md`, `CLAUDE.md`, `shell/run_opensource.sh`,
  `shell/run_medical.sh`, and example comments in the vLLM/chunked runner scripts.

**Status: config edited and imports cleanly; NOTHING run yet.** New Ollama tags not pulled;
no smoke test on any new model; changes uncommitted.

**Also removed (user decision, same day): Llava-Med-7B** — cannot produce the required JSON
(documented 2026-09-07). Its cached weights (both HF copies) were deleted. No vLLM models remain, so the
vLLM sbatch scripts are unused.

**Also (professor, same day): "we can try with the open-weight models" + "you can reserve use of
RTX 6000".** Open-weight models are now the primary roster (`MODELS` in `config/models.py`:
MedGemma-4B, Gemma-3-12B, Gemma-3-27B, Llama-3.2-Vision-11B). GPT-5/Claude/Gemini moved to
`API_MODELS` — still runnable by name, but excluded from `--all-models` so no API spend
happens by accident. Ollama jobs now target `hpg-rtx6000` (`gpu:rtx_pro_6000:1`, 96GB,
QOS `so589980.ucf`; `-b` QOS is rejected there). No SLURM reservation exists for our account,
so "reserve" = submit to that partition; `sbatch --test-only` accepted (est. start ~2026-09-24).

**Llama swap (2026-09-21, after smoke test):** Llama-3.2-Vision-11B DROPPED — Ollama 0.33.0
(required for the RTX PRO 6000; 0.20.2 has no sm_120 CUDA build and silently runs on CPU)
cannot load the `mllama` architecture. Replaced by **Llama-4-Scout** (`llama4:scout`, 67GB Q4,
109B MoE / 17B active, same Llama family). Pixtral is not in Ollama's library. Smoke test
(5 cases, ollama 0.33.0, RTX 6000) passed for MedGemma-4B, Gemma-3-12B, Gemma-3-27B; Scout
untested. Roster is now MedGemma-4B, Gemma-3-12B, Gemma-3-27B, Llama-4-Scout.

**Real runs launched (2026-09-21 ~15:35):** smoke tests passed for all 4 models (Ollama 0.33.0,
RTX PRO 6000). `results/` archived to `.scratch/results_archive_20260921` (includes
`_invalid_flawed_key_20260921`). 8 jobs: 4 models x {gated, non-gated}, all 54 patients,
`--include-unreviewed` (label results "LLM-drafted, unreviewed"). Job IDs 42873575-42873582
(name `lumi_<model>_<gated|nogate>`, logs `logs/lumi_*`). Per-job Ollama port (11500 + jobid%400)
added because 0.33.0's container ignores OLLAMA_HOST and jobs share nodes.
**MedGemma-4B parse failures:** repetition loop at temperature 0 -> truncation at MAX_TOKENS=800 ->
unclosed JSON (answer letter present but unparsed). DECISION: leave as-is until results are in,
then revisit (repetition penalty / salvage answer / report as finding).

**Open items**
- Pull the three new tags (Ollama module + `ollama serve`, `OLLAMA_MODELS` on /blue), then
  smoke-test each before the LUMIERE prelim runs (`task.md` has the sbatch commands).
- Gemma-3-27B at Q4 is ~17GB of the L4's 22.5GB — may OOM on long image contexts; fallback
  is a B200 or dropping it.
- Methods must state: Ollama models are Q4-quantized (unlike FP16 vLLM runs), and that the
  Llava-Med-7B checkpoint is a third-party "-hf" re-upload of Microsoft's weights.
- Optionally confirm with the professor that Llava-Med's Mistral base is acceptable (Mistral
  is French, so it should be fine).
- Cached Chinese-model weights still on /blue (HF cache: HuatuoGPT-Vision-34B(-hf),
  Lingshu-32B, InternVL3-38B, Qwen3-VL-30B; Ollama: qwen2.5vl) — delete pending user OK.
- Results tables will have a different model set than the earlier proposal; any prior draft
  text/figures naming the removed models need updating.

## 2026-09-07 — Llava-Med-7B guided-JSON re-test: still degenerates, stronger finding now

Ran the guided-JSON re-test flagged 2026-08-25 as required before reporting
Llava-Med-7B's near-zero score as a finding. Added `--guided-json` to
`run_omnibrain.py`/`src/evaluator.py` (passes `extra_body={"guided_json":
schema}` to vLLM's OpenAI-compatible endpoint, forcing token-level structured
output; new `ANSWER_RESPONSE_SCHEMA`/`FAITHFULNESS_RESPONSE_SCHEMA` in
`src/prompts.py`). Ran on `hpg-turin` (SLURM job 41296339, ~3 min) against
the same AIA-phase question set as the original 2026-08-21 run.

**Result: 0/25 AIA questions answered — same as unconstrained decoding.**
All 25 requests returned `200 OK` from the vLLM server (confirmed in
`.scratch/vllm_serve_Llava-Med-7B.log` — no server-side errors, no rejected
requests), but every response body was an empty string. This is a cleaner
result than the original test: it's not a malformed-JSON parsing failure,
it's the model producing zero content even when the server is enforcing
valid JSON at the decoding level. Ruled out MAX_TOKENS (800, plenty) and
temperature (0.0, greedy) as the cause.

**This lands on the stronger of the two anticipated outcomes** (see
2026-08-25 entry): "not fixable via output-format constraints — no coherent
answer to extract even when forced into valid syntax." The near-zero score
can now be reported as a genuine capability/robustness finding, not an
artifact of prompt/parsing mismatch. Results saved to
`results/Llava-Med-7B-guided-json_20260907_042950/`.

**Not yet done:** re-frame the write-up as a deployment-readiness/robustness
point (per the 2026-08-25 note) rather than a reasoning-quality point when
this goes into the paper draft.

## Target venue: NAACL 2027 (https://2027.naacl.org/)
Confirmed 2026-08-27. CFP details (deadline, page limits, formatting/anonymity
rules) not yet looked up — check the site directly once planning the writing
timeline.

## 2026-08-27 — fixed review-mechanism login wall; reviewer needs no Claude account now

Found a real blocker in the review mechanism built 2026-08-26: it persisted
decisions via the claude.ai `artifact` runtime capability
(`claude.use("artifact") -> publish()`), which requires the *viewer* to be
signed into a Claude account to write. The actual reviewer (radiologist/
neuro-oncologist collaborator) doesn't have one — they hit a login wall
trying to save. Evidence in the artifact's saved state: one item
(Patient-091_DSCR) was left `"review_status": "edited"` with an empty
`reviewer` field — a save that started but couldn't complete.

**Fix:** `tools/build_lumiere_review_artifact.py` now generates a fully
standalone `.html` file with no server/account dependency at all — every
approve/edit/reject autosaves to the reviewer's own browser via
`localStorage`, and a "Download review file" button produces an updated,
self-contained `.html` they email back (or a "Load review file…" picker to
resume from a previously downloaded one on another machine). Rebuilt and
verified: valid standalone document, no leftover `window.claude` references,
`tools/sync_lumiere_artifact_review.py` round-trips against it unchanged
(that script never actually needed the Artifact tool — it only ever
regex-parsed the `lumiere-data` script tag out of whatever HTML file it's
pointed at).

**Next step:** send `tools/lumiere_review_artifact.html` directly to the
reviewer (email attachment or a shared-drive direct-download link — NOT the
old claude.ai Artifact link, which is now superseded/stale) and have them
open it locally. Once they send back a completed download, sync with:
`python -m tools.sync_lumiere_artifact_review --html-file <path>` ->
`tools/lumiere_merge_reviewed.py` -> `run_lumiere.py` smoke test. No agent/
Claude Code session needs to be involved in the sync step anymore.

## ✅ DECIDED (2026-08-26) — professor approved LUMIERE + hybrid LLM/expert build

**Decision made.** Professor has approved option 3: build a real same-patient chain
dataset on LUMIERE (91 real GBM patients) using the hybrid LLM-draft +
domain-expert-review pipeline described below. This resolves the
chain-validity/construct-validity issue that was blocking the paper's core causal-
degradation claim (see investigation detail below for the original problem).

**Immediate next steps now unblocked:**
- Confirm radiologist/neuro-oncologist collaborator availability for the review step
  (still open — materially affects timeline).
- Pull LUMIERE's actual data dictionary/access process to confirm exact available
  fields before designing the phase-to-field extraction pipeline.
- Design the per-phase MCQ generation pipeline (fact extraction -> LLM draft -> expert
  review) and the review interface/format for the domain expert.

Full investigation, feasibility breakdown, and other options considered are preserved
below for context.

**Phase-by-phase feasibility (LLM-draftable vs. needs expert review), candidate = LUMIERE:**
- AIA / LIL — near-programmatic: LUMIERE ships per-timepoint tumor segmentation
  masks, so location/volume/volume-change facts are computable directly (atlas
  registration + voxel counts), not really "annotation."
- DSCR — LUMIERE already includes expert-assigned RANO response labels
  (progression/stable/partial/complete response) per follow-up scan — existing
  expert ground truth, not new annotation.
- PJRF (prognosis) — survival data is structured, but plausible-but-wrong distractors
  need someone who knows GBM prognostic literature; LLM-only distractors risk being
  trivially or misleadingly wrong.
- TCM (treatment) — Stupp protocol is templatable, but real judgment questions
  (progression vs. pseudoprogression, a well-known confound even for radiologists)
  need expert review of the answer key, not just LLM drafting.

**Rough effort estimate:** ~20–30 chains (patients) × 5 phases ≈ 100–150 items;
~10–15 min expert review per item (checking answer key + distractor plausibility,
esp. PJRF/TCM) ≈ **20–35 hours of expert time** for a first pass. Full 91-patient
LUMIERE cohort would scale to roughly 90–150 hours.

**Open sub-question, not yet resolved:** whether Prof. Wang's group already has a
radiologist/neuro-oncologist collaborator lined up for the review step, or whether
that access still needs to be arranged — materially affects timeline, not yet answered.

---

## Investigation detail (raised 2026-08-21/22, discussion ongoing above)

**Problem: OmniBrainBench does not actually support the causal-chain premise the KAB
framework is built on.** The framework evaluates a model through 5 sequential phases
(AIA → LIL → DSCR → PJRF → TCM) for *the same patient*, gating later phases on earlier
ones. Investigated the real dataset structure directly and found:

- Checked whether any image is shared across questions tagged with different clinical
  phases — the only way "same patient, multiple phases" could be genuinely true.
- Out of 6,823 total questions across 15 source sub-corpora (PubMedVision, MedXpert,
  RSNA, BraTS2021, ISLES2022, RadImageNet, VQA_RAD, NOVA, NEJMIC, Br35h, baby_brain,
  BraTS2023-MEN/MET, fastMRI, TCP, NOVA), only **2 questions** genuinely share a
  same-patient image across two different phases (both from VQA_RAD, AIA+LIL only).
- Re-verified with a second, more rigorous method: extracted real per-patient case IDs
  by stripping known modality/view/slice suffixes from filenames per corpus (e.g.
  `BraTS2021_00006_flair/t1/t1ce/t2` → case `BraTS2021_00006`; `ID_xxx_original/lung/
  bone` → case `ID_xxx`; `sub-strokecase0001_ses-0001_adc/dwi/FLAIR` → same case).
  Result: still only **2 genuine multi-phase same-patient cases in the entire
  dataset**, 2 phases each. Zero span 3+ phases. Zero span all 5.
- Root cause: each of the 15 source sub-corpora was built for one specific clinical
  task (BraTS → tumor characterization, RSNA → hemorrhage classification, ISLES →
  stroke, etc.), so a given real patient in that corpus is essentially only ever asked
  *one* phase-type of question, never a full multi-phase battery.
- What the current pipeline calls a "case" (`source_file` grouping, only 10 usable
  under `min-phases=2`) is really **one whole origin sub-corpus** standing in for one
  patient — the "chain" evaluated is stitched from *different real patients'*
  questions within that corpus, not one patient's actual journey. When a model gets
  "gated out" of DSCR after failing AIA, that's an artifact of this aggregation, not a
  demonstration of causal degradation for one patient.

**Searched for a replacement/supplementary dataset with genuine same-patient,
multi-phase continuity — none exists ready-to-use:**

| Dataset | Real same-patient continuity? | Covers prognosis/treatment? | Ready-made QA layer? |
|---|---|---|---|
| OmniBrainBench (current) | No (2 cases in 6,823 questions) | Nominally yes, not linked to real chains | Yes |
| [NeuroQA](https://neuroqa.stanford.edu) (56,953 QA / 12,977 subjects, incl. BraTS-GLI/MEN) | Partial (a "Longitudinal" category = 2 timepoints, not a full chain) | **Explicitly excluded by design** — paper states it's "not intended to support claims about...treatment planning" | Yes |
| [UCSF-PDGM-VQA](https://arxiv.org/abs/2605.17140) (2,387 QA / 473 studies) | No — single timepoint only | No | Yes |
| [LUMIERE](https://www.nature.com/articles/s41597-022-01881-7) (91 real GBM patients) | **Yes** — real longitudinal MRI, RANO response assessment, survival, Stupp-protocol treatment | **Yes** | **No** — raw imaging + clinical data only, no questions |
| [MU-Glioma-Post](https://www.cancerimagingarchive.net/collection/mu-glioma-post/) (203 patients, 617 post-treatment timepoints) | **Yes** | **Yes** (treatment + genomic data) | **No** — segmentation/clinical data, no questions |

**The honest conclusion:** no published benchmark currently provides genuine
same-patient continuity across a full imaging → diagnosis → prognosis → treatment
arc. The datasets with real clinical continuity (LUMIERE, MU-Glioma-Post) have no
question layer; the datasets with questions (OmniBrainBench, NeuroQA) don't have the
continuity, and NeuroQA's authors explicitly disclaim prognosis/treatment support.

**Options on the table, not yet decided:**
1. Build a modest MCQ layer on top of LUMIERE ourselves (~91 real patients available;
   even 20-30 annotated chains would be a genuine, defensible causal-chain dataset —
   something that doesn't currently exist elsewhere). More work, but produces a real
   contribution instead of working around a construct-validity gap.
2. Drop the full 5-phase same-patient chain claim; pivot to per-phase KAB evaluation
   at much larger scale (NeuroQA for AIA/LIL/DSCR-equivalent phases, existing sources
   for whatever prognosis/treatment questions exist standalone) — keeps the KB-
   alignment and feedback-adaptation contributions, loses the causal-chain narrative.
3. Keep researching other TCIA collections (TCGA-GBM/LGG, etc.) for something closer
   to ready-to-use before committing to option 1's build effort.

**User's call (2026-08-21): flag this to the professor before proceeding further —
this affects the paper's core framing, not just an implementation detail.**

---

## What Was Presented

In the meeting, I walked the professor through two things I had worked out since the last discussion:

### 1. Knowledge Base Selection (RadLex + NCIt)

I explained why I chose **RadLex** and the **NCI Thesaurus (NCIt)** as the two knowledge bases for the Knowledge Alignment Benchmarking framework — and specifically why I did not go with UMLS.

**RadLex** (RSNA, ~46k radiology-specific terms, OWL + CSV):
- The only KB built exclusively for radiology
- 71% of OmniBrainBench questions sit in AIA and LIL phases — imaging observation and lesion localization — which is exactly what RadLex covers
- When the model describes something like "FLAIR hyperintensity in the left temporal lobe," RadLex is the authoritative source to validate that claim

**NCI Thesaurus / NCIt** (NIH NCI, ~170k concepts, public domain):
- OmniBrainBench is predominantly a brain tumor dataset (glioma, glioblastoma, meningioma dominate)
- NCIt has the deepest coverage of brain tumor biology, WHO grading (Grade I–IV), staging, and treatment protocols of any freely available KB
- Preferred over UMLS because NCIt is more specific to the tumor cases that actually appear in the dataset, and it is public domain with a direct download — no account or API key required, which removes a reproducibility barrier for reviewers

The two KBs divide cleanly along the perception/reasoning boundary already in the framework:
- AIA + LIL → RadLex
- DSCR + PJRF + TCM → NCIt

### 2. Knowledge Alignment Benchmarking (KAB) and Feedback-based Adaptation Loop

I explained how I understand the KAB framework:

**KAB** replaces the current vocabulary-matching grounding metric with real KB concept alignment. Instead of checking whether a hardcoded word like "lesion" appears in the output, we:
1. Extract clinical concepts from the model's `reasoning` and `visual_grounding` fields
2. Cross-reference those concepts against the appropriate KB for that phase
3. Compute a **KB Alignment Score** (proportion of stated concepts that are valid KB entries) and a **Concept Precision Score** (are the KB concepts consistent with the correct answer?)

**Feedback-based Adaptation Loop** — what happens when a phase produces unfaithful output:
1. Retrieve the KB concept(s) the model missed or misused
2. Inject them as a structured clinical knowledge correction into the prompt
3. Re-run the phase
4. Measure whether the model self-corrects — **Adaptation Rate**

---




# Status Log

This section is a running log of project status, kept current so the project can be
picked back up cold after any gap. Newest entry on top.

## 2026-08-26 (latest) — full 55-patient batch drafted; expert-review artifact live

Since the previous entry: expanded from the initial 30-patient target to the
**full 55-patient eligible cohort** (54 successfully extracted/drafted — one,
Patient-025, has no timepoint with both a real RANO rating and complete
imaging) so the expert reviews everything in one pass. Added idempotency
guards to `lumiere_facts.extract_all()`/`lumiere_drafter.draft_all()` so
re-running against the expanded list doesn't redo the original 29 patients'
work or re-spend API credit — confirmed working (a mid-run LiteLLM proxy
outage caused one bad batch of empty drafts for the 25 new patients; the
guard correctly detected empty `[]` files as "not actually done" and retried
only those on the next run, not the whole set).

**Result: 269 MCQ items across 54 patients, all schema-valid.**

**Review mechanism changed from the Streamlit app to a published Artifact**,
since the actual reviewer (a radiologist/neuro-oncologist collaborator) is
not technical — SSH port-forwarding into a HiPerGator login node was a
non-starter. Built `tools/build_lumiere_review_artifact.py`, which bundles
all 269 items + 108 slice images (base64-embedded, ~2.5MB total) into one
self-contained page using the `artifact` runtime capability (reviewer
actions call `publish()`, persisting decisions server-side, readable back
later — no cluster/terminal access needed at all for the reviewer).

**Review link (durable — works independently of any Claude Code session
being open; check by re-reading this URL from any future session):**
https://claude.ai/code/artifact/af930975-d647-4f59-89f1-df1840384877

Self-tested in a real browser (not just static validation) — confirmed
`publish()` actually persists across reloads (4 test approvals landed and
were readable back). Iterated once on UX feedback: added a prominent
"N / 269 reviewed" progress counter + bar (was previously buried in small
text) and a "Saving…" disabled-button state during publish (previously no
loading feedback at all).

**Update (same day, later):** built and tested `tools/sync_lumiere_artifact_review.py`
end-to-end (Artifact `read` -> sync -> `merge_reviewed()` -> `build_lumiere_cases()`,
simulated a fully-approved patient to confirm a complete 5-phase case builds
correctly). Also caught and fixed a schema gap: the artifact's item data was
missing `task_label` (required by `build_lumiere_cases()`) — fixed in
`tools/build_lumiere_review_artifact.py`, artifact republished with the fix
(same link, resets to all-269-pending — no real review data existed yet, so
nothing lost).

**Current state: fully built and ready for the actual expert reviewer.**
Nothing left to do until they complete their pass — then:
`python -m tools.sync_lumiere_artifact_review --html-file <path from Artifact
read>` -> `tools/lumiere_merge_reviewed.py` -> `run_lumiere.py` smoke test.

## 2026-08-26 (later) — LUMIERE pipeline built through fact extraction; blocked on API key for drafting

Built the full LUMIERE ingestion pipeline (config/lumiere.py,
src/lumiere_downloader.py, src/lumiere_facts.py, src/lumiere_prompts.py,
src/lumiere_drafter.py, src/lumiere_loader.py, tools/lumiere_review_app.py,
tools/lumiere_merge_reviewed.py, run_lumiere.py — see CLAUDE.md's new LUMIERE
section for the technical detail). Verified real access via the Figshare API
(collection DOI 10.6084/m9.figshare.c.5904905.v1) and confirmed the actual
per-patient folder layout from the readme PDF and a live zip listing.

**Progress so far:**
- Selected 30 target patients by real multi-timepoint RANO coverage (>=3
  response-rated follow-ups); 29 had complete-enough data to extract.
- Extracted per-patient facts (AIA/LIL/DSCR/PJRF/TCM) with full provenance —
  no registration step needed (DeepBraTumIA's atlas-space masks are already
  MNI-aligned; precomputed volume JSONs ship with the dataset).
- **Caught and fixed a real bug during build**: picking each patient's LAST
  RANO-rated timepoint made every DSCR answer "progressive disease" (GBM
  patients almost always end on PD before their final scan) — would have
  made the DSCR phase trivially guessable. Fixed by sampling a random
  eligible timepoint per patient; real distribution now PD 20 / SD 6 / CR 2 / PR 1.
- Spot-checked chain coherence across all 29: volume-change direction vs.
  RANO label, and survival-week vs. followup-week ordering, both consistent
  except one flagged case (Patient-073, survival predates its sampled
  followup timepoint) — left flagged for expert attention, not silently fixed.
- Rendering slice PNGs (bridges LUMIERE's 3D NIfTI to the evaluator's 2D image
  loader) — in progress as of this entry.

**Blocked:** `OPENAI_API_KEY` (or another proprietary model's credentials) is
not set in this environment — needed for the LLM-drafting step
(src/lumiere_drafter.py) before expert review can start.

**Not yet done:** LLM drafting, expert review (radiologist/neuro-oncologist
collaborator availability still unconfirmed — see below), final merge, and
the run_lumiere.py smoke test against the existing evaluator.

## 2026-08-26 — professor approved LUMIERE + hybrid LLM/expert build

Professor's decision is in: proceed with option 3 — build a real same-patient causal
chain dataset on LUMIERE (91 real GBM patients) using the hybrid LLM-draft +
domain-expert-review pipeline (see feasibility breakdown at top of file). This
resolves the chain-validity issue flagged 2026-08-21/22 and unblocks the paper's core
causal-degradation claim. Next: confirm radiologist/neuro-oncologist collaborator
availability, pull LUMIERE's actual data dictionary, and design the per-phase MCQ
generation pipeline + expert review interface.

## 2026-08-25 — chain-validity issue: discussing hybrid LLM+expert build with professor (not yet decided)

Professor is asking, in-meeting, about the feasibility of the chain-validity open
issue's option 3: build a real same-patient chain dataset ourselves (candidate:
LUMIERE, 91 real GBM patients, genuine longitudinal imaging + RANO response +
survival + Stupp-protocol treatment), using a hybrid LLM + domain-expert pipeline.
User confirmed the approach shape is hybrid (LLM drafts, expert reviews/corrects) —
**this is the professor's live question, not a finalized decision.** See top of file
for the full feasibility breakdown prepared to answer it (phase-by-phase LLM vs.
expert-review split, ~20-35 expert hours estimated for a first pass of ~20-30 chains,
~90-150 hours for the full cohort).

**Not yet done / next steps:**
- ~~Get the professor's actual decision on whether to proceed with LUMIERE + this
  approach, or a different direction.~~ **DONE (2026-08-26): approved, see top of file.**
- Confirm whether a radiologist/neuro-oncologist collaborator is already available
  for the expert-review step, or needs to be arranged — blocks timeline planning.
- Pull LUMIERE's actual data dictionary/access process to confirm exact available
  fields (segmentation format, RANO label schema, survival/treatment fields) before
  designing the phase-to-field extraction pipeline.
- Design the per-phase MCQ generation pipeline (fact extraction -> LLM draft -> expert
  review) and a review interface/format for the domain expert, once approved.
- Decide on adding Qwen2.5-VL-3B (Ollama `qwen2.5vl:3b`) to `config/models.py` /
  `shell/run_opensource.sh` — gives MedGemma-4B a matched-scale general-model pair.
  Not yet added, pending go-ahead.
- **Before reporting Llava-Med-7B's near-zero score as a finding**: re-test it with
  vLLM's guided/structured-output decoding (`guided_json`) enabled. Currently the
  "cannot produce valid JSON under instruction" claim is only tested at greedy
  decoding with the standard prompt — a reviewer will ask whether constrained
  decoding fixes it. Two outcomes both usable: still degenerates under guided
  decoding -> stronger claim ("not fixable, no coherent answer to extract even when
  forced into valid syntax"); works under guided decoding -> different, still-useful
  finding ("needs structured-output tooling most deployment pipelines don't
  provide") — but then the near-zero number must be updated, not kept as-is. Also
  reframe the write-up as a deployment-readiness/robustness point, not a
  reasoning-quality point, when this goes into the paper.




## POSSIBLE CONTRIBUTION


1. A new benchmark that doesn't currently exist. No published dataset has both genuine same-patient continuity and a full imaging→diagnosis→prognosis→treatment question layer — we confirmed this by process of elimination across every candidate (OmniBrainBench, NeuroQA, LUMIERE, MU-Glioma-Post, UCSF-ALPTDG, UCSD-PTGBM). Building the LUMIERE-based chain set makes us the first to have one. That's a standalone contributable artifact, independent of anything else in the paper.

2. The causal-degradation finding becomes real, not artifactual. This is the important one. The paper's most novel claim — that model reasoning degrades across clinical phases for the same patient — was previously undermined by the fact that OmniBrainBench's "chains" were stitched from different real patients (2 of 6,823 questions were genuine). Once the chain is built on LUMIERE, that finding is no longer vulnerable to the obvious reviewer objection; it's now measuring what we always claimed it measures.

3. The KAB framework itself — KB-grounded faithfulness + feedback-adaptation. RadLex/NCIt concept-alignment scoring and the feedback-adaptation loop (does the model self-correct when given a structured knowledge correction) were already planned contributions, unaffected by the dataset problem — but they become more meaningful measured on a real causal chain: "did correcting the model at phase 2 actually help phase 4" is only a meaningful question if phase 4 genuinely follows from phase 2 for the same patient.

4. A reusable construction method. The hybrid LLM-draft + targeted-expert-review pipeline (~20–35 expert hours to turn a raw longitudinal clinical dataset into 20–30 validated causal-reasoning chains) is itself worth stating as a methods contribution — it's a cheap, repeatable way to build this kind of benchmark elsewhere, not just a one-off dataset.

<!-- - Professor's decision on LUMIERE + hybrid build — APPROVED 2026-08-26
- Whether a radiologist/neuro-oncologist collaborator is available
- Pull LUMIERE's actual data dictionary before designing the extraction pipeline
- Qwen2.5-VL-3B addition to config/models.py — awaiting go-ahead
- Guided-JSON re-test on Llava-Med-7B before that finding goes in the paper -->