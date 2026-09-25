# Analysis plan for the v4 (answerable-by-construction) LUMIERE evaluation

Written 2026-09-24, **before any v4 model run**. No model output on the v4 items exists at the time of writing (checked:
`results/` holds no `lumiere_v4_*` or `*_v4_nogate_*` folder). The file is not externally timestamped; the SHA-256 recorded
in `paper/update.md` at the time of writing, and the git history once it is committed, are the only evidence of its date.
It answers `paper/review.md` concerns 1 to 4 and 6. Everything not listed as primary is descriptive.

## What is fixed here

**Item set.** `data/lumiere/v4/` built by `src/lumiere_v4.py` (seed 20260925): 62 patients, one first-line follow-up each.
Every key is a stated function of what the model sees (`paper/latex/acl_latex.tex`, Section "A Same-Patient Chain Dataset").
Selection used only the tabular records and the segmentation masks. Model output was never consulted.

| Phase | Question | Key | n |
|---|---|---|---|
| AIA | Which MRI sequence is shown? | the sequence rendered (balanced 16/16/15/15) | 62 |
| LIL | Hemisphere and anterior/posterior half of the main tumor region on the displayed slice | position of the largest tumor-core component on that slice | 51 |
| DSCR | RANO enhancement category from the displayed baseline, nadir and follow-up slices | category from bidimensional products of the enhancing lesion on those slices | 62 |
| PJRF | Probability of death within 52 weeks of this scan, from stated clinical facts | recorded outcome (34 of 61 died); scored by Brier score | 61 |
| TCM | Next management step | rule(category, weeks since chemoradiotherapy): non-PD continue; PD within 12 weeks of radiotherapy repeat MRI first; PD later change therapy | 62 |

**Rules behind the keys (fixed in `src/lumiere_measure.py` and `src/lumiere_v4.py`).** DSCR: bidimensional product of the largest enhancing
component on the slice with the largest enhancing area of each scan; measurable is at least 100 mm^2 (10 x 10 mm); progression is a product at least 1.25 times the
nadir (smallest earlier product, post-operative scan included) or a new measurable lesion; partial response is at most 0.5 times the post-operative product;
complete response is nothing measurable left; follow-ups with nothing measurable on the baseline and nadir scans are not built (the rule abstains). LIL: hemisphere and
anterior/posterior half of the largest tumor-core (enhancing plus necrotic) component on the slice with the largest such area, against the midline and the
front-to-back midpoint of the brain mask on that slice; lesions under 100 mm^2, within 10 mm of a midline, or with under 80% of their pixels on one side are not built.
TCM: weeks since chemoradiotherapy = weeks since the post-operative scan minus 10; progressive-disease items are early at 2 to 10 and late at 14 or more weeks; the
11 to 13 week band is not built. PJRF outcome: death by 52 weeks after the scan among patients alive at the scan. Slice rendering: 1st to 99.5th percentile of the
volume, 4x magnification, 20 mm scale bar. Nothing in these rules was tuned on model output; the DSCR rule was adjusted (nadir; abstention) before item building after
its agreement with the expert ratings was inspected, which is disclosed here because that agreement is a reported statistic.

**Models and decoding.** MedGemma-4B, Gemma-3-12B, Gemma-3-27B, Llama-4-Scout, served as in the v3 study, temperature 0,
800 tokens. A response that cannot be parsed and cannot be salvaged scores incorrect (PJRF: forecast 0.5).

**Conditions** (`src/v4_conditions.py`), all one question at a time so an effect is not mixed with the model's own earlier answers:
`own` (image, no upstream context), `text` (no image), `swap` (image of a donor with a different key, one donor per patient and phase, matched
number of images), `ctx_gold`, `ctx_wrong` (each upstream answer replaced by a seeded random incorrect option), `ctx_absent`,
`flip_label`, `flip_window` (TCM). The ordinary five-phase chain (own answers as context, no gating, no adaptation) is run with and without
images as a secondary analysis.

## Primary estimands and decision rules

Unit of analysis: the patient (one question per phase). Intervals are 95% percentile bootstrap intervals over patients (10,000 resamples,
seed 20260925); paired binary contrasts also get exact McNemar p-values.

**E1. Image effect per phase.** Delta = accuracy(`own`) - accuracy(`text`), paired, for AIA, LIL and DSCR, per model.
- Margin: **+/-10 percentage points**, fixed now. Rationale: with 51 to 62 patients one item is about 2 points, so 10 points is 5 to 6 patients; a
  smaller effect would not change a conclusion about whether a model reads the scan. This is a judgment, not a derived quantity.
- "Image helps" if the interval lies above 0. "Within margin" if the interval lies inside (-10, +10). Otherwise "inconclusive".
- Precision warning written in advance: the interval half-width is about 1.96 * sqrt(d / n) where d is the share of items whose correctness differs
  between arms. With n = 62, "within margin" is reachable only if d is at most about 14%. If d is larger the result is "inconclusive" and is reported as such.
- **Positive control.** AIA cannot be answered without the image (text-only accuracy is at chance by construction, the key being uniform over four
  sequences). A model whose AIA interval does not lie above 0 has not shown that this test detects image use, and no claim about that model's
  LIL or DSCR image dependence is made from E1.
- Multiplicity: Holm correction across the 12 E1 tests (4 models x 3 phases); both raw and Holm p-values are reported. No other family is adjusted.
- Sensitivity, not primary: DSCR restricted to items whose category also equals the expert RANO rating (`facts_used.concordant`).

**E2. Donor tracking (matched pairs, fixed context).** For each item, G = 1[swap answer = donor key] - 1[`text` answer = donor key], the second
term being what the no-image prior does. Image tracking is claimed for a model and phase only if the interval for mean(G) lies above 0.
Every AIA, LIL and DSCR option set contains all four possible answers and the stems contain no patient-specific fact, so the donor's answer is always
available and text never conflicts with the swapped image. Reported alongside: own-image accuracy, share of swapped answers that keep the patient's own key,
share of answers that change.

**E3. TCM: use of facts other than the category.** With the gold upstream context, the rule needs both the category and the stated timing.
- Reference: answering with a category lookup alone (one action class for every progressive-disease item) reaches 69.4% (escalate) or 74.2% (confirm-first)
  (`results/lumiere_v4_baselines.md`); the full rule reaches 100%.
- `flip_window`: the stated weeks since chemoradiotherapy move to the other side of the 12-week window (to 20 or to 4); the informative items are the
  35 progressive-disease items, where the rule's answer changes. Report the share of answers that move to the rule's new answer, for all items and for PD items.
  `flip_label`: the stated category is replaced by one that the rule maps to another action class. Report the share that follow. No formal test; near 0% means the
  fact is ignored, near 100% that it is used. The share restricted to items answered correctly under `ctx_gold` is also reported.
- `ctx_wrong`: share of answers that match the rule applied to the (wrong) stated category.

**E4. Upstream-context effects.** Paired accuracy differences gold / wrong / absent for LIL, DSCR and TCM; descriptive, unadjusted.

**E5. PJRF.** Brier score of the forecast (bin midpoints 0.10, 0.30, 0.50, 0.80) against the recorded 52-week outcome; skill = 1 - Brier / Brier of the
leave-one-out constant base rate (0.255); AUC. A patient-bootstrap interval for the per-patient difference in squared error against the base rate.
Reference: a leave-one-out logistic model on the stated facts (age, MGMT, resection extent, weeks since surgery) has Brier 0.264 and AUC 0.547, i.e. the facts do not
support a forecast better than the base rate at this sample size; the paper says so and reads PJRF only as a check that models are not worse than a constant.

## Secondary and exploratory

E6, the chain total effect (`own`-chain image versus text-only per phase), is secondary: each arm regenerates its upstream answers, so a later-phase
difference is the total effect through the chain. All v3 results remain and are labeled exploratory (their equivalence margin was chosen after seeing
the intervals; this one is not). The KAB vocabulary and consistency metrics are computed in the chain runs but carry no claim.

## Not done here (declared)

- Clinician review of answerability and of every key, in particular the TCM rule, the 12-week window and the assumed chemoradiotherapy schedule
  (ends 10 weeks after surgery; LUMIERE has no radiotherapy dates), the automated segmentation behind LIL and DSCR keys, and the 52-week survival
  outcome (censoring is not documented in LUMIERE). This is the one item deliberately left.
- No proprietary models.

## Change log

Any deviation after the first v4 run is entered here with its date and reason, and in `paper/update.md`.

- 2026-09-25. **Positive-control model added (before any control run beyond a 2-patient smoke test).** Reason: two of the four open models (Gemma-3-12B, Gemma-3-27B)
  did not pass the AIA positive control in E1, so the test has not been shown to detect image use for them. Model: Gemini-3.6-Flash (`gemini-3.6-flash`, Google API, run date 2026-09-25), chosen because
  `gemini-2.5-pro` returns 404 for the account (no longer available to new users) and `gemini-3.1-pro-preview` had no free-tier quota; a Flash model was tried first as the cheaper control, with
  `gemini-3.1-pro-preview` as the fallback if Flash does not pass the AIA control. Conditions: `own`, `text`, `swap` on AIA, LIL and DSCR (E1 and E2 only), same prompts, temperature 0, same decision rules. Two
  differences from the open-model runs, both forced by the API: the output cap is 16,384 tokens instead of 800 (the model's hidden thinking tokens count against the cap), and the route is Google's OpenAI-compatible endpoint.
  The control is reported separately and is NOT added to the four-model Holm family (the 12 E1 tests are unchanged). Patients 1 and 2 come from the smoke run (`results/lumiere_v4_Gemini-3.6-Flash_part1_*`, identical
  code and settings); the smoke output for those two patients was seen before the full run (own-image 4 of 6 correct, text-only and swap 1 of 12). Empty API responses (errors, rate limits) are counted in
  `empty_responses.json`; any such item is rerun before results are read, and is not scored as a model failure. This supersedes "No proprietary models" under "Not done here" for this one control model.
- 2026-09-25. **Precision control added (before any run).** The four open models ran at 4-bit (Q4_K_M) through Ollama, so a gap to the API control model in E1/E2 could reflect quantization instead of model quality.
  One model, Gemma-3-27B, is rerun in bf16 (`google/gemma-3-27b-it`, Google's release, vLLM, one RTX PRO 6000) on `own`, `text`, `swap` for AIA, LIL and DSCR, same prompts, temperature 0 and 800-token cap; run name `Gemma-3-27B-bf16`.
  Chosen because it failed the AIA positive control and is the largest of the four whose bf16 weights fit one GPU (Llama-4-Scout in bf16 does not). It is reported apart from the four-model Holm family and is NOT a fifth model in E1 to E6.
  The serving stack differs (vLLM against Ollama), so a difference conflates precision with the stack; a 4-bit run through vLLM is not planned. Reading rule, fixed now: if its AIA interval lies above 0 and clearly above the 4-bit model's, the gap is at least partly quantization;
  if it stays near chance, quantization does not explain the gap; anything between is reported as inconclusive.

## Exclusions and missing data

No item is dropped after a run. A patient without an item for a phase (LIL: 11 patients; PJRF: 1) is absent from that phase only. Unparseable model output scores incorrect
(PJRF: forecast 0.5). Results are reported for every model that finishes; a model that does not finish is reported as such, not replaced.


<!-- paper/acl_before_trim.tex -->