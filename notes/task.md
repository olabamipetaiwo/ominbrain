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

All review-2026-09-29 tasks (T-R1..R8) are done (see update.md 2026-09-30). Pixtral is integrated as a second precision/stack control (AIA+LIL).

- [ ] **T-R9 — Rebuild the anonymous reproducibility artifact.** `release/anon_artifact/` was built before Pixtral, so its `numbers.tex`, `expected/` statistics and raw model records don't include the Pixtral run or the 1027-macro regeneration — it no longer matches the committed paper. Rebuild via `tools/build_anon_artifact.py` (include the `Pixtral-12B-bf16_image_20260929_181720` records), verify `reproduce.sh` regenerates statistics/macros/tables identically and the anonymity scrub is 0 hits, then re-upload to the anonymous repo (anonymous.4open.science) whose link is in the submission.

## PENDING, in order of importance


1. **Clinician review, T-3a–e** — OUT OF SCOPE by the professor's standing decision (2026-09-25); listed last because of its long external lead time, though it would matter most for the unvalidated keys. Sub-items:
    - [ ] **T-3a** — Recruit qualified clinician reader(s) to independently assess exactly the images/stems/options shown to models — blinded initially to model outputs and generated keys.
    - [ ] **T-3b** — Have them judge, per item: is it answerable from what's shown, which answer is supported, and why ambiguous if so. Target all 38 LIL + 46 DSCR items; if that is not feasible, a prespecified stratified sample with limitations reported.
    - [ ] **T-3c** — Include representative agreement and disagreement cases from the automated audit in the writeup.
    - [ ] **T-3d** — Report independent agreement pre-adjudication, uncertainty on it, and an error-source breakdown (segmentation vs. rendering vs. target choice vs. missing evidence).
    - [ ] **T-3e** — Fallback if clinician review cannot happen in time: narrow the benchmark-validity claim and reduce DSCR's prominence in the abstract/contributions (the concordance statistic is agreement with our rule, not proof the expert labels are wrong).

    <!-- cd release/anon_artifact -->
    <!-- artifact update -->

    <!-- Task
    When you're back (reconnect however you normally do, any node), restart Claude and just say something like "check the Pixtral run." I'll:
<!-- 1. Check 43944162 finished cleanly and eyeball the Pixtral results.
2. Regenerate numbers → integrate Pixtral into E1/E2/E3 + prereg log.
3. Do T-R5 (abstract) and T-R6 (E1 trim) against the fresh numbers, recompil -->


## Submission prep (2026-10-01)
- [x] Overview figure (Fig 1, TikZ) + experimental-results figure (Fig 2) added per professor feedback.
- [x] Main body trimmed to the 8-page ARR content limit (Option A: kept both figures, trimmed redundant prose). Conclusion ends p.8; Limitations p.9. See update.md 2026-10-01 (2).
- [ ] T-R9 — rebuild the anonymous reproducibility artifact (release/anon_artifact/) to include Pixtral + the 1027-macro regeneration, verify reproduce.sh + anonymity scrub, re-upload to anonymous.4open.science. (Note: the figures/trim changed numbers.tex usage but NOT the numbers; re-check the artifact's numbers.tex still matches.)


-- Final proofread pass on any section
- Verify the compiled PDF matches submission requirements (page limit, format, anonymization)
- Check figures/tables for consistency and caption quality
- Review references/BibTeX for completeness
- Draft the submission cover letter or abstract tweaks
