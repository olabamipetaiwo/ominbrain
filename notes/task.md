# Tasks

Only in-progress (`[~]`) and not-started (`[ ]`) items live here. 
When a task is confirmed finished, delete it from this file (history goes in `paper/update.md`).

## Standing rules
- PAPER RULE (user, 2026-09-28): the paper reports only the final design and results; no version history (rebuilt, earlier round, superseded). History lives in `paper/update.md` and the preregistration change log.
- Do not cite results from folders dated before 20260928; they used the old 62-patient items.
- GPU cap: standing cap is 3 concurrent GPUs;
- It's an evaluation paper, not benchmark

---
## NEW TASKS (delete each when done)

### Review-round-3 fixes (review.md, 2026-10-05; weak reject). ORDERED — do not skip ahead.
Dependency rule (HARD — no prose is written until all experiments/analysis are done):
Step A (code) → Step B (regenerate) and Steps C/D (compute) in parallel → ONLY THEN Steps E–G
(prose/tables/structure) → Step H (response letter). NO section of the manuscript is drafted or
edited until A, B, C, AND D have all completed and their numbers are frozen. Writing prose before
every experiment lands is the exact cause of the number/caption mismatches this review flagged.
All numbers come from the single frozen output (T-R14) via generated macros — nothing hand-typed.
Steps E/F/G that follow say "after analysis frozen" meaning after A+B+C+D, not merely after B.

#### OPEN DECISIONS (surfaced from review.md / solution.md)
- PARKED (user, 2026-10-06) **D1 — Independent statistician review of the permutation component (solution.md §3).**
  Ignore for now; the interpretation is resolved to a conditional label-association test (T-R13). Revisit only if raised.
- PARKED (user, 2026-10-06) **D2 — trimmed synthetic confounds.** Decision: KEEP the trim (position + image_count
  confounds, Wilson CIs, three tracker strengths are enough). class-specific tracking and correlated-errors-for-reused-
  donors stay OUT — neither is load-bearing: non-detection framing concedes un-excluded mechanisms, the cluster
  bootstrap + LOO already respect shared donors, any permutation-p inflation is conservative for the null, and the
  Gemini 5/5 reference control demonstrates real power. If a referee re-raises class-specific/correlated tracking, pick
  up the correlated-errors confound first (~1h, a validity not power check); leave class-specific as a stated limitation.
- Note: review concern 2's "define a minimum tracking effect + equivalence analysis" is intentionally NOT done — that
  path is only needed to CLAIM absence; we chose the non-detection framing (T-R18) instead.

#### STEP A — DONE 2026-10-05 (T-R11/12/13 code fixes verified; see paper/update.md). Prose spillover moved to T-R19.

#### STEP B — Regenerate from one frozen output (after Step A)
- [x] **T-R14 — DONE 2026-10-06.** supplement + stats + donor_validation + robustness all regenerated; final
  `paper_numbers` run wrote 1120 frozen macros to `paper/latex/generated/*`. Every v4 number traces to this one run.

#### STEP C — Real-model robustness (compute; after T-R11; within the standing GPU cap)
- [x] **T-R15 — DONE 2026-10-05.** `tools/lumiere_v4_altpairs.py` writes alternative valid assignment files
  (schema = counterfactual_pairs.json) via the real build_pairs. 5 generated under `data/lumiere/v4/alt_pairs/`,
  each differs from original on all phases; AIA 500+, LIL 500+, DSCR 500+ distinct valid assignments exist
  (answers reviewer Q1; the DSCR space is NOT degenerate — see update.md (9)).
- [x] **T-R16 — DONE 2026-10-06.** Both arms complete (Llama SLURM 44872728 COMPLETED 6h24; Gemini API clean).
  Results: Gemini reference 5/5 significant on AIA & LIL (gains +65..+87, stable); Llama DSCR 1/5 significant
  (gain +19..+33, p .039..706) -> donor tracking not reliably detected / unstable, so non-detection is robust to the
  assignment choice. Macros `\vfourRobust*` frozen via T-R14. Full numbers in update.md (11).

#### STEP D — Trim synthetic controls (after Step A; keep small, do NOT make it the centerpiece)
- [x] **T-R17 — code DONE 2026-10-05** (`tools/lumiere_v4_donor_validation.py` + `paper_numbers.py`): added the
  no-tracking confounds (position, image_count) for false-positive calibration; Wilson CI on each detection rate +
  explicit nominal_alpha=0.05; rho documented as the tracking-branch probability (effective donor-answer acc
  rho+(1-rho)/|opts|, e.g. 0.55 at rho=0.4). PROSE REMAINDER -> Step E/F: reframe as illustration not absence proof,
  drop the matched-+19.0 framing, answer reviewer Q3 (compatible tracking magnitudes).

#### STEP E — Claims & cross-section consistency (ONLY after analysis frozen: A+B+C+D complete)
- [x] **T-R18 — DONE 2026-10-06.** Narrowed to non-detection across abstract/Fig3/Results/App D/Conclusion; see update.md (12).**
  Headline: large image-vs-text accuracy gains can coexist with insufficient evidence of correct
  donor-specific tracking. Use "did not detect / did not establish donor-specific tracking." Remove
  every "absent," "low power excluded," "behaves like the generic predictor." Apply identically to
  abstract (`acl_latex.tex:156`), Figure 3, Results, Appendix D (`:613`), Conclusion.
- [x] **T-R19 — DONE 2026-10-06** (Fig3 heading/largest-among-open-models, causal overclaim, post-hoc labels, App D sentence deletion, label-association scope; robustness paragraph added). See update.md (12).
    - Figure 3 heading still says controls "overturn image use" while the verdict says tracking is
      unestablished — make the heading match the narrower verdict.
    - Remove the causal overclaim that the gain arises ONLY because text-only accuracy is poor (the two
      accuracies give the difference, not its mechanism).
    - AIA gate: treat sequence-ID as a DIAGNOSTIC positive control, not a prerequisite that makes LIL/DSCR
      uninterpretable. Keep the historical prespecified rule in the record but distinguish it from the
      revised scientific interpretation (Methods + Limitations).
    - "+45.7 largest ablation gain in the study" → "largest among the four open-weight models" (reference
      model has +73.9 AIA, +63.2 LIL).
    - Mark the permutation analysis AND the synthetic controls as post hoc wherever presented.
    - Delete the Appendix D sentence claiming that subtracting the no-image prior "isolates tracking from generic
      response" (moved here from T-R13; the generic image-shift control is a direct counterexample). State the
      permutation test's narrow label-association scope instead (the `donor_dependence` docstring now spells it out).
    - Permutation count: write the ACTUAL accepted count, now exposed as macro \vfourDonorPermN..., not "5,000".
    - DSCR donor-reassignment stability (T-R11 outcome): the valid-assignment space is NOT degenerate (500+ distinct
      constraint-valid assignments; the scan-count x PD imbalance only forces a varying 4-of-46 to drop). The stability
      check is legitimate and shows true trackers stay detected while the generic shift is never flagged across
      reassignments. Report this as stability of the TEST's discrimination, still under the non-detection framing.
    - Narrower conclusion (review major 4): state that below-majority accuracy does NOT rule out correct visual
      classification of SOME items; the gain is real while correct donor-specific tracking is unestablished.
    - Caveat (review concern 3): the donor-cluster bootstrap does not by itself validate the permutation procedure;
      attribute any discrimination to the separately justified (label-association) permutation analysis, not to the gain.
    - Separate the two variance sources (review major 1: "report assignment variation separately from prediction-seed
      variation"). Frame explicitly: prediction-seed variation = the per-predictor detection CIs on the FIXED original
      assignment (donor-validation table); assignment variation = the across-500-assignments stability block. Do not
      present a single combined number as if it were one source.

#### STEP F — Reporting-issues checklist (after analysis frozen; review "Remaining issues" table)
- [x] **T-R20 — DONE 2026-10-06** (every row cleared; precision intervals+donor added to appendix; caught+fixed the stale hand-typed "25 of 46"->macro "25 of 43"). See update.md (12). Rows:
    - Table 8: shows DSCR n=46 while donor metrics use 42 — add separate own/text and swap sample sizes.
    - Precision paragraph (src ~line 489): points to Table 8 for the bf16 rerun, but that table is
      Gemini-only — add full precision-control intervals + donor results (both precision controls), or
      give the precise location of the evidence.
    - Table 9: Pixtral and the API reference absent despite per-pipeline claims — add their info or narrow
      the claim.
    - Appendix C / `generated/v4_example.tex:13`: worked example says the TCM stem states the rule,
      contradicting §3.2 — label the exact condition or correct it. Figure 4 does not show the DSCR donor
      images despite the caption — fix caption or add images.
    - Table 3 caption: "accuracy uses all 46" is overbroad — state AIA 46, LIL 38, DSCR 46; keep the
      separate 42-item DSCR answer-change denominator.
    - Audit discussion (PDF p.4): main text says agreement did not differ with size closeness; align with
      Appendix D's "uncertain" wording (63.6% vs 45.8%).
    - Output handling: valid-JSON DSCR 23.1% does not "match" 19.6% — say it remains below nominal chance;
      distinguish observed difference from inference.
    - Restore the per-model token-cap distinction (16,384 reference vs 800 open models) + reason in
      Methods/Appendix B.
    - Appendix D donor-count range renders "31 to 30" — order endpoints, preferably list per-phase counts.
    - Limitations: fix the "enhancems ent" typo.
    - (secondary, review visual note) Tables 3/7 and Figure 3 are dense at normal size; Appendix p.16 has large empty
      regions around its floats — tidy if cheap, do not let it displace the substantive corrections.
    - (reviewer Q5) Ship a final RUN MANIFEST: which result folders + inclusion criteria produced each reported cell
      (fold into T-R9 artifact / reproduce.sh; every number already traces to the one frozen paper_numbers run).

#### STEP G — Structure & length (review submission-length issue)
- [x] **T-R21 — DONE 2026-10-06.** Main content through the Conclusion now fits on page 8 (moved E3 table to appendix + trims; verified by probe label). See update.md (12).
  Move chain/survival/compatibility detail to the appendix; keep AIA/LIL/DSCR as the main story, TCM
  compact, PJRF's interpretation limited; use recovered space for the estimand + validation. Do not
  change the template. Verify against the current ARR CFP.

#### STEP H — Review(last)
- [x] **T-R22 — DONE 2026-10-06. Consistency gate passed.** Every digit in prose/tables/captions resolves to a frozen
  macro or a legitimate constant/cited value; no undefined/empty macros, no undefined refs/citations, no em-dashes;
  clean compile 17 pp; main content within 8 pages. Caught+fixed two stale hand-typed numbers (25 of 46->43; 500->
  "re-drawn"). PDFs refreshed. (Response-to-reviewers letter skipped per user.) See update.md (12).


## PENDING, in order of importance

    - [ ] **OUTSTANDING (need new inference / external expert, not reanalysis):** a second reference model, and independent clinician review of the keys. Paper's Conclusion already flags these.


1. **Clinician review, T-3a–e** — OUT OF SCOPE by the professor's standing decision (2026-09-25); listed last because of its long external lead time, though it would matter most for the unvalidated keys. Sub-items:
    - [ ] **T-3a** — Recruit qualified clinician reader(s) to independently assess exactly the images/stems/options shown to models — blinded initially to model outputs and generated keys.
    - [ ] **T-3b** — Have them judge, per item: is it answerable from what's shown, which answer is supported, and why ambiguous if so. Target all 38 LIL + 46 DSCR items; if that is not feasible, a prespecified stratified sample with limitations reported.
    - [ ] **T-3c** — Include representative agreement and disagreement cases from the automated audit in the writeup.
    - [ ] **T-3d** — Report independent agreement pre-adjudication, uncertainty on it, and an error-source breakdown (segmentation vs. rendering vs. target choice vs. missing evidence).
    - [ ] **T-3e** — Fallback if clinician review cannot happen in time: narrow the benchmark-validity claim and reduce DSCR's prominence in the abstract/contributions (the concordance statistic is agreement with our rule, not proof the expert labels are wrong).

 


## Submission prep (2026-10-01)
- [ ] T-R9 — rebuild the anonymous reproducibility artifact (release/anon_artifact/) to include Pixtral + the regenerated macros, verify reproduce.sh + anonymity scrub, re-upload to anonymous.4open.science. (Note: the figures/trim changed numbers.tex usage but NOT the numbers; re-check the artifact's numbers.tex still matches.)
    - ALSO ship the round-3 reproducibility materials (answers reviewer Q1 "release assignment identities + checks" and Q5
      "regenerate all cells"): `tools/lumiere_v4_altpairs.py` + `data/lumiere/v4/alt_pairs/` (the alternative assignment
      files + manifest, i.e. the released assignment identities), `tools/lumiere_v4_robustness.py` +
      `results/lumiere_v4_robustness_*.json`, the updated `tools/lumiere_v4_donor_validation.py` +
      `results/lumiere_v4_donor_validation.json`, and the `LUMIERE_V4_PAIRS` usage; add their runs to reproduce.sh.
    - A short RUN MANIFEST mapping each reported cell to its source result folder(s) + inclusion criteria (the Q5 ask;
      every number already traces to the one frozen paper_numbers run).


Final proofread pass on any section
- Verify the compiled PDF matches submission requirements (page limit, format, anonymization)
- Check figures/tables for consistency and caption quality
- Review references/BibTeX for completeness
- Draft the submission cover letter or abstract tweaks 

<!-- cd release/anon_artifact && git push origin main  -->

  
<!-- Two decisions (now flagged as D1/D2 in task.md):

1. D1 — Independent statistician review of the permutation test. Both files recommend a stats-experienced collaborator vet the permutation null before we trust it (solution.md §3: "ask a statistically experienced collaborator… before investing in more inference runs"). I resolved the interpretation to a conditional label-association test (T-R13), but I can't perform the external review myself — it's a professor/collaborator ask. Do you want to pursue it, or rely on the documented interpretation?
2. D2 — I deliberately trimmed two of solution.md §4's confound families. I implemented position + image_count confounds, Wilson CIs, and three tracker strengths. I did not implement class-specific tracking and correlated-errors-for-reused-donors predictors — on purpose, per my earlier §4 pushback (narrowing the claim to non-detection removes the need to exhaustively characterize the test, and more synthetic machinery is more bug surface). Confirm that trim is OK, or I'll add those two back.

Three minor gaps — added to the tasks:
- Two interpretation nuances the reviewer stressed → T-R19: (a) below-majority accuracy doesn't rule out correct visual classification of some items; (b) the donor-cluster bootstrap doesn't by itself validate the permutation procedure.
- Visual density note (Tables 3/7, Fig 3; Appendix p.16 whitespace) → T-R20 (marked secondary, as the reviewer did).
- A final run manifest for Q5 (which result folders produced each cell) → folded into T-R20/T-R9.

One intentional non-action: review concern 2's "define a minimum tracking effect + equivalence analysis" — I'm deliberately not doing that, because it's only needed to claim absence, and we chose the non-detection framing (T-R18). Noted in task.md so it's a recorded decision, not an oversight. -->