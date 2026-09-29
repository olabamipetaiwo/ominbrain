# Tasks 

Status key: `[ ]` not started, `[~]` decided/in progress, `[x]` done.

## RESUME HERE (updated 2026-09-29 afternoon)
STATE: T-19 reruns are DONE (all 14 jobs COMPLETED, counts validated, analysis regenerated, DSCR/PJRF/TCM/chain text re-audited, paper recompiled: 0 undefined refs, 16 pages, Conclusion/Limitations on page 8). Details and before/after numbers: top entry of `paper/update.md`.
Regeneration order (via srun, not the login node): `lumiere_v4_stats` -> `lumiere_v4_supplement` -> `lumiere_v4_baselines` -> `paper_numbers` -> `paper_numbers --check`, AND `python -m tools.paper_v4_example` (paper_numbers does NOT regenerate the worked example; it had kept the old DSCR stem until 2026-09-29).
Remaining for the user/next session: (a) read the edited results paragraphs once (abstract, E1, E3/E4, chain, what-this-shows) since several claims changed direction (rule-stated raises 3 of 4, not 4; gold beats wrong context for all four; Scout DSCR below the majority share); (b) page count is 16 vs 15 before, check the appendix is still concise (feedback_concise_appendix); (c) Gemma-3-27B's one invalid record (Patient-012 TCM explicit_rule) has no verified cause, none is stated; (d) the open items listed below (T-4, T-9, T-12, T-13, T-S1/S2/T-15). Tooling note: the shell safety check fails intermittently; retry once, or use Read/Edit.

## CURRENT STATUS (updated 2026-09-29)
- DONE: v4 item set rebuilt (46 patients; LIL 38) and ALL conditions rerun; stats, supplement, baselines and paper macros regenerated; manuscript prose, preregistration change log and `paper/update.md` brought in line with the rerun. Tests pass.
- DONE: **T-18** input-check rerun (results in, paper regenerated); was: jobs 43740495 (MedGemma-4B, Gemma-3-12B), 43740496 (Gemma-3-27B, Llama-4-Scout) and 43740453 (bf16 Gemma-3-27B); 3 GPUs, cap of 3 authorized by the user for this run (standing cap is 2). 43740452 was cancelled and split. When they finish: regenerate `paper_numbers`, the qualifier wording is already removed from the paper.
- Invalid-JSON cause established 2026-09-29 (details in `paper/update.md`): MedGemma-4B and Gemma-3-27B are truncation loops at the 800-token cap; Llama-4-Scout's are a misspelled key ("visual_ grounding"), not truncation. No raw-response rerun needed (raw text is saved for parse errors). Appendix sentence re-checked after the reruns: Gemma-3-27B now has 1 invalid (TCM explicit_rule), the sentence was split accordingly.
- DONE: **T-19** DSCR stem reworded and DSCR/PJRF/TCM/chain conditions rerun (14 jobs COMPLETED 2026-09-29), analysis regenerated, paper text re-audited and recompiled. AIA/LIL results unaffected.
- T-16 fully resolved: technical reports cited for model identification only, and the professor has been informed (confirmed by the user 2026-09-29). Nothing left to do.
- OPEN, not caused by the rerun: T-S1/T-S2/T-15 (artifact and PDF), P2 statistical repairs T-4a-d (T-4e partial), P3 writing items (T-9, T-12, T-13 partial; T-6, T-14, T-5, T-7; T-8 done), P5 clinician review (out of scope by standing decision).
- PAPER RULE (user, 2026-09-28): the paper reports only the final design and results; no version history (rebuilt, earlier round, superseded). History lives in `paper/update.md` and the preregistration change log. v3/KAB material and version names were cut on 2026-09-28 (reviewer point: stop organizing the scientific argument around internal version names).
- Do not cite results from folders dated before 20260928; they used the old 62-patient items.

---

## P0 — Correctness bugs (everything downstream depends on these being right)

### DSCR measurability implementation vs. stated prompt

Verified in code: `src/lumiere_measure.py:39,151-168` gates measurability on
`bidimensional_product >= 100 mm^2`; `src/lumiere_v4.py:311` tells the model "measurable
means at least 10 mm by 10 mm" (both perpendicular diameters). Not equivalent (e.g. 20x6mm
passes the code, fails the stated rule). `d1_mm`/`d2_mm` are already cached per lesion
(`src/lumiere_measure.py:101`), so no re-measurement pass is needed, only re-derivation.

- [x] **T-1a** — DECIDED (2026-09-28): fix the code to match the prompt (implement the true
  two-diameter test: both d1 and d2 >= 10mm), not the other way around.
- [x] **T-1b** — DONE (2026-09-28): `measurable(d1, d2)` added in `src/lumiere_measure.py`
  (both diameters >= `MEASURABLE_MIN_DIAMETER_MM`, replacing `MEASURABLE_BP_MM2`);
  `imaging_rano_label` now takes `(d_ref, d_fu, d_nadir)` diameter pairs for measurability
  while still using the bp product for the 25%/50% ratio thresholds. Call site
  (`src/lumiere_v4.py:enumerate_candidates`, ~line 111-134) updated with a `diam(m)` lambda
  alongside the existing `bp(m)` one; `d_ref`/`d_fu`/`d_nadir` also stored on the candidate
  dict and surfaced in the DSCR item's `facts_used` for transparency. Regression tests added
  in `tests/test_lumiere_v4.py` (`test_rano_rule_measurability_is_not_just_the_product`
  reproduces the exact 20x6mm bug case). `python -m tests.test_lumiere_v4` passes.
- [x] **T-1c** — DONE (2026-09-28): scoped impact via `python -m src.lumiere_v4 --explore`
  (read-only, writes nothing) comparing old vs. corrected rule over all 360 cached
  measurement timepoints:
  - 35/360 timepoints flip measurable→not-measurable (all one-directional, as required
    mathematically — the two-diameter test is a strict subset of the product test).
  - Patients with rateable follow-ups: 69 → 65. Candidate follow-ups: 231 → 211.
  - Rule/expert concordance (the paper's headline audit stat): 130/231 = 56.3% → 121/211 =
    57.3% — **barely moves**, so that claim survives the fix.
  - Final selected cohort: 62 → 59 patients. TCM class split C/F/E: 27/19/16 → 23/16/20.
    LIL-eligible among selected: 51 → 48.
  - Conclusion: this is not just relabeling — cohort membership and TCM class balance
    genuinely shift, so **T-1e (rerun) is required**, not optional.
- [x] **T-1d** — DONE (2026-09-28): pre-fix `data/lumiere/v4` (drafts, reviewed, facts,
  slices, counterfactual_pairs.json, selection_report.json — 42MB) copied to
  `data/lumiere/_backup_v4_pre_dscr_tcm_fix_20260928/` before rebuilding, matching this
  project's existing `_backup_*` snapshot convention (see the other `_backup_*` dirs already
  under `data/lumiere/`). Original run fully recoverable.
- [x] **T-1d cont'd — rebuild executed** (2026-09-28): `python -m src.lumiere_v4 --no-render`
  regenerated drafts/facts/reviewed/selection_report.json (matched the `--explore` prediction
  exactly: 59 patients, LIL 48, TCM class split 23/16/20), then the full
  `python -m src.lumiere_v4` (with rendering) pulled slices for the corrected cohort from the
  remote LUMIERE archive — no GPU needed, network/CPU only, ran on the login node. No errors
  in the render log.
  - **Stale-file cleanup:** `build()` only writes the current cohort, it doesn't delete
    patients that fell out of it. 4 patients from the old 62-patient cohort
    (`Patient-030`, `Patient-064`, `Patient-066`, `Patient-090` — identified by file mtimes
    predating the rebuild) were left behind in `drafts/reviewed/facts/slices`, which would
    have leaked pre-fix patients into the loader (63 files vs. the correct 59). Removed after
    explicit user approval (the auto-mode safety classifier initially blocked the `rm` as
    "irreversible local destruction"; recoverable regardless via the T-1d backup). All four
    directories now correctly hold exactly 59 patients.
  - **Verified:** `python -m tests.test_lumiere_v4` passes and reports
    "Built 59 LUMIERE cases | phase coverage: AIA:59 | LIL:48 | DSCR:59 | PJRF:58 | TCM:59",
    matching the selection report exactly.
- [x] **T-1e / T-2d — round 1 CANCELLED (2026-09-28), superseded by T-1f.** 14 jobs were
  submitted (3 lanes + standalone Gemini, job IDs 43615663-700) and job 43615663 confirmed
  running cleanly against the corrected 59-patient cohort. Before letting the rest run, T-1f's
  audit (below) found a second, larger correctness issue in the same DSCR construction, so all
  14 jobs were cancelled (`scancel`) rather than waste GPU-hours evaluating data about to be
  superseded again. See T-1f/T-1e-round-2 below for the actual rerun.
- [x] **T-1f** — DONE (2026-09-28). Audited whether "largest enhancing component per
  timepoint" tracks the same physical lesion across ref/nadir/follow-up, using the (then-)
  current 59-patient cohort: fetched ref/nadir/fu segmentation masks for all patients and
  measured centroid displacement of the naive largest-component pick.
  - **Finding: a real, majority-case problem.** Median reference→follow-up centroid
    displacement 21.1mm (p90 46.9mm, max 79.2mm), median 10-slice z-jump; 36/56 patients (64%)
    showed a jump >30mm or >10 slices. Plausible cause: the reference scan is the first
    post-operative scan, where enhancement near the resection cavity is small/patchy/noisy, so
    "largest component" often isn't the same lesion later scans show as dominant.
  - **Fix implemented** (`src/lumiere_measure.py`): `MEASURE_VERSION` bumped to 2 (with
    version-check auto-invalidation added to `load_or_measure`, so stale v1 caches recompute
    without needing `--force`). New `_enh_components()` finds every 3D-connected enhancing
    component (not just the largest), each measured on its own best 2D cross-section. New
    `nearest_component(anchor, components)` implements the correspondence rule: track the
    component nearest the reference scan's own largest component, not whichever is largest at
    each timepoint independently (falls back to largest when there's no reference anchor).
    `enumerate_candidates()` (`src/lumiere_v4.py`) now computes one `anchor` per patient and
    uses corresponded (not independently-largest) bp/diameters for the follow-up, nadir search,
    AND the rendered slice (`render_patient` now reads `ch["z_ref"/"z_fu"/"z_nadir"]` — the
    exact slice actually measured — instead of recomputing its own independent pick, which
    would have reintroduced the same class of image/measurement mismatch). Unit tests added:
    `test_lesion_correspondence_tracks_nearest_not_largest` (synthetic two-lesion case).
  - **Impact of this fix alone: much larger than the diameter fix.** Re-measured all 360
    timepoints (v2 schema) and reran `--explore`: concordance **57.3% (121/211) → 38.1%
    (75/197)**; final cohort **59 → 46 patients**; the "expert=PD, rule=CR" confusion jumped
    13→46. This is because the reference RANO implementation has no "new lesion = automatic
    progression" criterion, and once the correspondence bug stopped masking it, cases where the
    tracked lesion resolves while a genuinely different lesion grows elsewhere now correctly
    show as (rule) complete response vs. (expert) progressive disease.
  - **Decision (2026-09-28, discussed at length):** do NOT implement RANO new-lesion detection
    now. Root-cause breakdown of the 46 "expert=PD, rule=CR" cases
    (`tools/lumiere_v4_supplement.py::audit_new_lesion_pattern`, verified to reproduce the
    scratch-analysis numbers exactly): 22 plausible-new-lesion, 16 no-other-measurable-component
    -at-all, 8 pre-existing-secondary-lesion. A new-lesion rule would at best recover ~22/197
    (concordance to ~49%, not back to 56-57%), while adding its own arbitrary thresholds (how
    far is "elsewhere", how much smaller counts as "new") — the same class of self-chosen
    parameter that caused concern 1 in the first place — and would require a third full
    rebuild+rerun cycle this close to Oct 12. Instead: disclose precisely, with the 22/16/8
    breakdown as new macros (`vfourNewLesionN/Plausible/None/Preexisting`, wired through
    `tools/paper_numbers.py`) cited in a new Limitations sentence. Accept 46-patient/38.1% as
    the corrected, honest result — arguably a *stronger* result for the paper's actual thesis
    (expert ratings are not validated targets for the displayed/tracked lesion) than a higher
    number would have been.
  - **Rebuild executed (2026-09-28), round 2:** backed up the intermediate (diameter-fix-only,
    59-patient) build to `data/lumiere/_backup_v4_pre_lesion_correspondence_fix_20260928/`
    before overwriting (same discipline as T-1d). `python -m src.lumiere_v4 --measure`
    re-measured all 361 timepoints under the v2 schema (no errors), `--explore` and then the
    real `--no-render`/full-render build matched exactly: 46 patients, LIL 38, TCM class split
    19 continue / 7 confirm / 20 escalate. `python -m tests.test_lumiere_v4` passes.
    Donor-pair note: `pairs_built.DSCR = 42/46` (4 patients have no compatible donor left after
    the cohort/class shift) — expected behavior of the existing assignment algorithm under
    tighter class balance, not a bug.
- [x] **T-1e round 2 — rerun on the 46-patient corrected cohort.** DONE 2026-09-28: all jobs completed; stats/supplement/baselines/paper_numbers regenerated (see paper/update.md, evening entry). Immediate next step:
  resubmit the same 3-lane + standalone job structure as the cancelled round 1 (identical
  commands/sbatch scripts, GPU cap 3 for this rerun still approved), now against the
  correspondence-fixed build. Then rerun `tools/lumiere_v4_stats.py` and
  `tools/paper_numbers.py` to regenerate `paper/latex/generated/*` before touching any paper
  text that cites those numbers.
- [x] **T-1g** — DONE (2026-09-28). The model-facing DSCR stem already precisely defines
  complete response as "no remaining *measurable* enhancing disease" (an unambiguous
  operational rule for the model), but the manuscript's own Limitations text disclosed the
  omitted RANO conditions (T2/FLAIR, steroids, clinical status) without ever stating the actual
  consequence: our complete response label permits real residual sub-threshold enhancement,
  unlike clinical RANO's sustained-disappearance criterion. Added one sentence to Limitations
  making this explicit (plus the new-lesion disclosure from T-1f, same paragraph).

### TCM "explicit rule" claim not actually shown to the model

Verified in code: `tcm_rule` is stored only in item metadata (`src/lumiere_v4.py:359-361`);
`build_main_prompt` (`src/prompts.py:104-144`) never reads it, only `question`/`options`/chain
context. `SYSTEM_PROMPT` (`src/prompts.py:14-18`) tells the model to rely on "what you can
directly observe in the image" even for text-only TCM/PJRF questions.

- [x] **T-2a** — DECIDED (2026-09-28): add a new explicit-rule TCM condition (inject the rule
  into the prompt) rather than only narrowing the claim.
- [x] **T-2b** — DONE (2026-09-28): new `"explicit_rule"` condition added to `CONDITIONS`/
  `PHASES_BY_CONDITION` in `src/v4_conditions.py` (TCM only). It reuses `ctx_gold`'s upstream
  context and additionally passes a new `TCM_RULE_STATEMENT` constant (`src/lumiere_v4.py`)
  through a new `extra_instructions` parameter threaded through `ask()` →
  `build_main_prompt()` (`src/prompts.py`) into the actual prompt text. The existing
  `ctx_gold`/`ctx_wrong`/`ctx_absent`/`flip_*` conditions are unchanged (implicit-rule
  comparison preserved). The existing `stated_rule_class`/`follows_stated_label` bookkeeping
  in `run_case` applies to this condition automatically since it also injects a gold DSCR
  context.
- [x] **T-2c** — DONE (2026-09-28): reworded `SYSTEM_PROMPT` in `src/prompts.py` to not
  assert an image is always shown ("may include a brain imaging scan... base your answer on
  the image when one is shown, and on the clinical facts and any instructions stated in the
  question when it is not"). This is a shared prompt, so it also fixes the same mismatch for
  every other text-only condition (AIA/LIL/DSCR text-only, PJRF), not just TCM.
- [x] **T-2d** — DONE 2026-09-28 (results in; analysed in supplement D2). Rerun TCM under the new explicit condition for the 4 open-weight models
  (corrected from an earlier note here that said "all 5" — checked
  `shell/lumiere/lumiere_v4_{bf16,gemini}.sbatch`: the reference model and the bf16 precision
  control were only ever run on `own,text,swap`/`AIA,LIL,DSCR`, never the context/TCM
  conditions, so `explicit_rule` has no reference/precision-control counterpart to add).
  `shell/lumiere/lumiere_v4.sbatch`'s MODE=context branch updated to include
  `explicit_rule` in its condition list (2026-09-28). Keep the original implicit-rule results
  alongside (new runs get fresh timestamped filenames under `results/`, so nothing is
  overwritten). Combine with T-1e into one
  rebuild + rerun pass (user request, 2026-09-28).

**Verification done for T-2b/T-2c (2026-09-28):** new unit tests
`test_explicit_rule_condition_states_the_rule_in_the_prompt` (confirms the rule text is
present under `explicit_rule` and absent under every other condition) and
`test_system_prompt_does_not_assume_an_image` in `tests/test_lumiere_v4.py`, both passing.
Also end-to-end smoke-tested `run_case(..., ("explicit_rule",))` against a real built v4 case
with the offline `MockClient` — runs cleanly through the full `ask()`/prompt/parse pipeline.

## P1 — Reproducibility / artifact hygiene (need this to know what's currently real)

- [~] **T-S1** — Confirm the v4 raw run records + aggregate stats that back the generated
  STATUS 2026-09-28: raw v4 run records exist and are locatable (`results/lumiere_v4_<model>_{image,context}_20260928_*`, chain runs `results/lumiere_<model>[_textonly]_v4_nogate_noadapt_20260928_*`, controls `lumiere_v4_{Gemini-3.6-Flash,Gemma-3-27B-bf16}_image_*`); analysis reads only 20260928 folders (`MIN_STAMP` in `tools/lumiere_v4_stats.py`). Still to do: put them, the measurement caches and the run manifest into the T-15 artifact.
  numbers actually exist and are locatable (reviewer's checkout was missing `results/`
  v4 raw runs and the v4 measurement caches). If they exist here, make sure they end up
  in the reproducibility artifact (T-15).
- [~] **T-S2 / T-17** — Rebuild the compiled PDF from the current `acl_latex.tex` and
  STATUS 2026-09-28: scratch compile of the current `acl_latex.tex` is clean (0 undefined refs, 16 pages, Conclusion and Limitations on page 8). Not done: visual inspection of every page, and archiving/removing stale `body_main.tex`. The compile was on a scratch copy; no PDF was kept.
  visually inspect every page (current compile log is dated Sept 23, predates the Sept 25
  runs; cannot certify the 8-page ACL/NAACL content limit or layout without a fresh build).
  Remove or clearly archive the unused, stale `body_main.tex` so it can't be accidentally
  submitted or confused with the active manuscript.
- [x] **T-19** — DSCR stem vs slices mismatch. DECIDED 2026-09-28 (user): reword the stem and rerun. DONE: stem reworded in `src/lumiere_v4.py` to "the largest cross-section of the same enhancing lesion (the enhancing lesion nearest the largest enhancing region on the post-operative baseline scan, followed across scans)"; items rebuilt (pre-fix copy in `data/lumiere/_backup_v4_pre_dscr_stem_fix_20260928/`); verified that exactly the 46 DSCR `question` fields changed and nothing else (same patients, keys, options, donor pairs); tests pass. SCOPE of rerun (the chain context pastes every earlier question into later prompts, so the DSCR stem is inside PJRF/TCM prompts too): DSCR own/text/swap (4 open + bf16 + Gemini); DSCR/PJRF/TCM under ctx_gold, ctx_wrong, flip_label, flip_window, explicit_rule (4 open); full ordinary chain, image and text-only arms (4 open). NOT rerun (prompts do not contain the DSCR stem): AIA and LIL image conditions, LIL contexts, ctx_absent. SUBMITTED, 3 GPUs (authorized by the user), lanes with `afterany` dependencies: L1 Gemma-3-27B 43748788/789/790 -> bf16 DSCR 43748791 -> Gemma-3-12B image 43748792; L2 Llama-4-Scout 43748793/794/796 -> Gemma-3-12B context 43748797; L3 MedGemma-4B 43748798/801/802 -> Gemma-3-12B chain 43748803; Gemini DSCR 43748804 (API) COMPLETED 2026-09-28 22:xx (46 own / 46 text / 42 swap records, 0 parse errors; own 33/46, text 27/46). Lane heads 43748788/793/798 (image_dscr) COMPLETED (1h03/1h16/0h48); context_dscr jobs 43748789/794/801 COMPLETED (2h33/2h17/1h55); chain 43748802 (MedGemma-4B) COMPLETED (1h58); chain jobs 43748790 (27B) and 43748796 (Scout) running; Gemma-3-12B chain 43748803 started (it ran ahead of its image/context jobs 43748792/797, which are still pending, plus bf16 43748791). New result folders are tagged `imagedscr` / `contextdscr` and, being later, override the same (case, phase, condition) keys in the analysis loader. TO DO when all finish: (1) check record counts per model/phase (no missing keys, none silently taken from the old stem); (2) rerun `lumiere_v4_stats` -> `lumiere_v4_supplement` -> `lumiere_v4_baselines` -> `paper_numbers` (via srun); (3) re-audit every results sentence in `acl_latex.tex` against the new numbers (DSCR E1/E2, Scout's Holm result, E3/E4/E5, chain, explicit-rule) because they will change again; (4) regenerate the worked example (it quotes the stem); (5) add the stem rewording to the preregistration change log (done, see below) and update.md. Do not cite any DSCR/PJRF/TCM/chain number until these finish; the 09-28 evening numbers in `paper/update.md` for those phases are superseded.
- [x] **T-18** — DONE 2026-09-28 (jobs 43740453/495/496 completed in 2-3 min each; results `results/lumiere_v4_inputcheck_*_20260928_*`): all five pipelines 8/8 probes; token increments per added image consistent (Ollama Gemma/MedGemma ~280-308, Llama-4-Scout ~1456-1477, bf16 271-288), including DSCR images 2 and 3; squash montage checked by eye, lesion and scale bar legible at 896 and 448. Macros and `tab_v4_inputcheck` regenerated; paper text needed no change. (Was: BLOCKS SUBMISSION — the paper now describes the input check with no qualifier (no version history in the paper, per the user), so its table and claims must come from the rerun; until the jobs finish they are from the old build.  SUBMITTED 2026-09-28 (jobs 43740495, 43740496, 43740453; tool reads the rebuilt v4 items and current `build_main_prompt`). Rerun the input check (`shell/lumiere/lumiere_v4_inputcheck*.sbatch`) on the rebuilt items and the reworded system prompt. The 09-25 results (`results/lumiere_v4_inputcheck_*`) ran on the old items; the paper discloses that in Limitations and the appendix. After the rerun: regenerate `paper_numbers`, (the qualifier wording is already removed from `acl_latex.tex`). 3 GPUs authorized for this run only; the standing cap is 2.

- [ ] **T-15** — Build the anonymous reproducibility artifact: item manifests, exact
  serialized prompts, donor assignments, model response provenance, analysis versions, a
  deterministic table-generation command, and a run/override manifest (the model loader lets
  later records silently replace earlier ones — document that explicitly). Local paths in the
  paper are not usable supplementary material for reviewers.

## P2 — Statistical repairs

- [ ] **T-4a** — Report the exact two-sided McNemar p-value alongside the percentile-bootstrap
  CI for MedGemma AIA (5 image-only correct, 0 text-only correct → CI excludes 0, but exact
  p=0.0625 pre-multiplicity). Don't present gate-passage as statistically established image
  competence when the unadjusted exact test doesn't even clear significance.
- [ ] **T-4b** — Add a paired-binomial (or similarly sparse-appropriate) interval as a
  sensitivity analysis wherever the bootstrap degenerates to [0,0] on all-concordant pairs
  (e.g. Gemma-3-27B E2 DSCR gain) — `tools/lumiere_v4_stats.py:75-80` resamples observed
  paired differences only, which can't represent unobserved discordant outcomes.
- [ ] **T-4c** — Use patient-clustered uncertainty (not a plain Wilson interval) for the
  longitudinal audit, since it has repeated visits per patient unlike the one-visit-per-patient
  model experiment — `tools/lumiere_v4_supplement.py:35-49`. Report patient count alongside
  visit count.
- [ ] **T-4d** — State the donor-dependence estimand explicitly (conditional on the fixed
  donor assignment, vs. generalizing over patients/assignments) — `src/lumiere_v4.py:400-424`
  lets each patient donate to two recipients, and E2 only resamples recipient differences.
  Run a donor-reuse/assignment sensitivity analysis; don't assume pair-level resampling
  covers both estimands.
- [~] **T-4e** — Reword E2 "clearly tracks" language (abstract + body) to something like
  STATUS 2026-09-28: wording changed to "interval above zero" (abstract, results, conclusion) after the rerun. Still to do: exact tests alongside the intervals and an explicitly exploratory multiplicity-sensitivity analysis for E2.
  "positive unadjusted intervals"; show exact tests and an explicitly exploratory
  multiplicity-sensitivity analysis; keep the original preregistered family intact.

## P3 — Writing / description fixes (mostly independent of reruns)

- [x] **T-11** — Correct the LIL-exclusion description: code allows limited midline crossing
  DONE 2026-09-28: text now says lesions with under 80% of pixels on the centroid's side of the midline are not asked about.
  (passes if ≥80% of component pixels are on one side), but the manuscript states crossing
  lesions are excluded outright. Make the text match the actual rule.
- [x] **T-10** — Fix the Limitations sentence claiming the bf16 result "argues against
  DONE 2026-09-28: Limitations now matches Results (bf16 rerun does not isolate quantization from the serving stack; no other model rerun).
  quantization as the main cause" — align with Results' correct framing (precision and
  serving stack changed together; a null result can't isolate quantization).
- [~] **T-13** — Add an accessible dataset summary: donor reuse/matching details, class
  STATUS 2026-09-28: AIA now described as balanced with its realized most-common share (macro) and chance as an expectation. Still to do: the dataset summary (donor reuse/matching, class counts, exclusions).
  counts, item exclusions. State AIA's ~16/16/15/15 balance and chance-expectation framing
  correctly (not "exactly fixed 25%", since that's an expectation under independence, not a
  guaranteed realized value).
- [~] **T-12** — Handle E3 moved/informative rates more carefully across models: informative
  STATUS 2026-09-28: full transition table (`tab_v4_e3trans`) and moved/informative counts per model are in the paper; the informative denominator differing by model is stated. Still to do: show the prespecified original metric next to the revised one.
  denominators differ by model since conditioning depends on that model's original answer.
  Show full transitions plus the prespecified original metric alongside the revised one.
- [~] **T-9** — Keep "no open-model E1 test survives Holm correction" but don't frame it as
  STATUS 2026-09-28: PREMISE CHANGED by the rerun. One open-model E1 test now survives Holm (Llama-4-Scout DSCR, adjusted p=0.028), so the text says that. Still to do: do not frame the non-surviving tests as evidence of absence; note which intervals admit practically meaningful gains.
  evidence of absence; note several intervals admit practically meaningful gains.
- [ ] **T-6** — Reframe the RANO-disagreement audit as motivating validation, not the headline
  discovery; lead with the determinate-denominator number as primary, report coverage separately.
- [ ] **T-14** — Keep PJRF noncentral given unresolved survival-time origin/censoring;
  consider dropping it from the main table/narrative entirely, not just the appendix.
- [x] **T-8** — DONE 2026-09-28 (user approved): v3 appendix, KAB appendix, evidence-audit/option-only/TCM-lookup appendix, the Limitations paragraph on the first item set and the v3 AI-drafting note are cut from `acl_latex.tex`; the audit section now stands alone (expert RANO ratings vs the enhancement rule); "v3"/"v4" names removed from the text, captions and headings (only internal labels remain). Paper is 15 pages. Original note follows.
   — Move most v3 history, KAB discussion, and OmniBrainBench-compatibility detail
  out of the main narrative; stop organizing the scientific argument around internal version
  names (v3/v4).
- [ ] **T-5** — Reframe the lead/contributions around the precise methodological question
  (when does an image intervention measure correct visual tracking vs. mere response
  sensitivity) rather than the five-phase chain architecture; identify and demonstrate, with
  a worked failure case, which design choices here improve interpretability relative to prior
  protocols (e.g. HEAL-MedVQA). Treat the multi-phase patient chain as an extension, not the
  headline, unless T-2's corrected TCM results establish a substantive additional finding.
  Do this last among writing fixes — it depends on how T-1/T-2/T-4 land.
- [ ] **T-7** — Compress the abstract further (currently carries 5 acronyms + construction
  history + audit caveats + controls + outcomes before the takeaway). Do this last, once
  T-1/T-2/T-4/T-5 changes are locked in, so the abstract reflects final content instead of
  needing a second pass.

## P4 — Needs a decision before acting

- [x] **T-16** — DECIDED 2026-09-28 by the user: cite the MedGemma and Gemma 3 technical reports for model identification ONLY (no claim rests on them); Llama-4-Scout has no report, so it stays identified by name/tag/digest. Done in `acl_latex.tex` (Section 4 model list, appendix "Models and terms") and `custom.bib`. The professor has been informed of this exception to the published-only rule (confirmed by the user 2026-09-29). Nothing left. Original note follows.
   — **Conflicts with an existing constraint:** reviewer suggests reconsidering
  the blanket exclusion of non-peer-reviewed references (model cards/reports support
  attribution/identification even though they're not peer-reviewed). This conflicts with the
  professor's standing "published papers only" rule (peer-reviewed only, drop
  arXiv/workshop-only). Flag to professor before changing anything.
  STATUS 2026-09-28: web search for peer-reviewed versions of the model reports found none. MedGemma Technical Report (arXiv 2507.05201, plus a MedGemma 1.5 report, arXiv 2604.05081) and Gemma 3 Technical Report (arXiv 2503.19786) appear only as arXiv preprints; Llama 4 has only Meta's model card and release blog, no paper. SECOND CHECK 2026-09-28 (bibliographic databases): Semantic Scholar lists MedGemma (arXiv 2507.05201) with empty venue and no journal, and Gemma 3 (arXiv 2503.19786) as venue arXiv.org with DBLP id journals/corr/abs-2503-19786, i.e. CoRR only; targeted searches for a Nature/MICCAI/ICLR/NeurIPS/ICML/ACL/TMLR version of either found none; no Llama 4 paper exists (model card and blog only). Not reachable: DBLP (blocked), OpenReview search (HTTP 400), Semantic Scholar for Llama 4 and MedGemma 1.5 (rate-limited). Conclusion: no peer-reviewed versions found. Under the published-only rule none of the three can be cited; only the professor can grant an exception for model-identification citations.

## P5 — Independent clinician validation (long external lead time, listed last)

- [ ] **T-3a** — Recruit qualified clinician reader(s) to independently assess exactly the
  images/stems/options shown to models — blinded initially to model outputs and generated keys.
- [ ] **T-3b** — Have them judge, per item: is it answerable from what's shown, which answer
  is supported, and why ambiguous if so. Target all 38 LIL + 46 DSCR items; if that's not
  feasible, a prespecified stratified sample with limitations reported.
- [ ] **T-3c** — Include representative agreement and disagreement cases from the automated
  audit in the writeup.
- [ ] **T-3d** — Report independent agreement pre-adjudication, uncertainty on it, and an
  error-source breakdown (segmentation vs. rendering vs. target choice vs. missing evidence).
- [ ] **T-3e** — Fallback if clinician review can't happen in time: narrow the
  benchmark-validity claim and reduce DSCR's prominence in the abstract/contributions
  (currently the 56%/49% concordance stat is given outsized weight relative to what it
  actually establishes — it's agreement with our rule, not proof the expert labels are wrong).

---

## Reference: reviewer's proposed schedule (informational, not the priority order above)

| Window (2026) | Focus | Deliverable |
|---|---|---|
| Sept 28–30 | Resolve validity blockers | Retrieve raw artifacts (T-S1); reconcile DSCR definitions (T-1); quantify affected items (T-1c); freeze a versioned correction plan; start recruiting clinician readers (T-3a) |
| Oct 1–5 | Produce decisive evidence | Complete independent item review (T-3); run explicit-rule TCM (T-2); rerun affected DSCR/downstream conditions (T-1e); complete sparse-data/dependence sensitivity analyses (T-4) |
| Oct 6–8 | Rewrite around supported contribution | Tighter intro, shorter abstract (T-7), validated primary tasks, clear separation of original vs. corrected analyses (T-1d), compact comparison with closest prior work (T-5) |
| Oct 9–11 | Verify submission | Regenerate all numbers, build + visually inspect PDF (T-S2/T-17), anonymous artifact (T-15), references (T-16), checklist, registration requirements |
| Oct 12 | Submit | ARR submission, 23:59 AoE; confirm author reviewer-registration requirement |
