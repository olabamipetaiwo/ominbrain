# Tasks

Only in-progress (`[~]`) and not-started (`[ ]`) items live here. When a task is confirmed finished, delete it from this file (history goes in `paper/update.md`).

## RESUME HERE 

STATE: analysis, paper text and the reproducibility artifact are current with the DSCR-stem reruns; numbers and history are in the top entries of `paper/update.md`.

## Standing rules
- PAPER RULE (user, 2026-09-28): the paper reports only the final design and results; no version history (rebuilt, earlier round, superseded). History lives in `paper/update.md` and the preregistration change log.
- Do not cite results from folders dated before 20260928; they used the old 62-patient items.
- GPU cap: standing cap is 2 concurrent GPUs; 3 was authorized only for the T-18/T-19 runs.

---
## IN PROGRESS
 - [ ] Compile Paper
 - [ ] Read Through Paper


## PENDING, in order of importance

1. **Clinician review, T-3a–e** — OUT OF SCOPE by the professor's standing decision (2026-09-25); listed last because of its long external lead time, though it would matter most for the unvalidated keys. Sub-items:
    - [ ] **T-3a** — Recruit qualified clinician reader(s) to independently assess exactly the images/stems/options shown to models — blinded initially to model outputs and generated keys.
    - [ ] **T-3b** — Have them judge, per item: is it answerable from what's shown, which answer is supported, and why ambiguous if so. Target all 38 LIL + 46 DSCR items; if that is not feasible, a prespecified stratified sample with limitations reported.
    - [ ] **T-3c** — Include representative agreement and disagreement cases from the automated audit in the writeup.
    - [ ] **T-3d** — Report independent agreement pre-adjudication, uncertainty on it, and an error-source breakdown (segmentation vs. rendering vs. target choice vs. missing evidence).
    - [ ] **T-3e** — Fallback if clinician review cannot happen in time: narrow the benchmark-validity claim and reduce DSCR's prominence in the abstract/contributions (the concordance statistic is agreement with our rule, not proof the expert labels are wrong).

    <!-- cd release/anon_artifact -->
