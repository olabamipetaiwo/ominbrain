# Tasks

Only in-progress (`[~]`) and not-started (`[ ]`) items live here. When a task is confirmed finished, delete it from this file (history goes in `paper/update.md`).

## RESUME HERE 

PAGE LENGTH (user, 2026-09-29): not a task. Finish all tasks first; trimming to the page limit happens once at the end.

Remaining follow-up: read the edited results paragraphs once (abstract, E1, E3/E4, chain, what-this-shows), since several claims changed direction (rule-stated raises 3 of 4, not 4; gold beats wrong context for all four; Scout DSCR below the majority share).

Tooling note: the shell safety check fails intermittently; retry once, or use Read/Edit.

## Standing rules
- PAPER RULE (user, 2026-09-28): the paper reports only the final design and results; no version history (rebuilt, earlier round, superseded). History lives in `paper/update.md` and the preregistration change log.
- Do not cite results from folders dated before 20260928; they used the old 62-patient items.
- GPU cap: standing cap is 2 concurrent GPUs; 3 was authorized only for the T-18/T-19 runs.

---

## PENDING, in order of importance

1. [~] **T-15** — Reproducibility artifact. STATUS 2026-09-29: built at `release/anon_artifact/` by `python -m tools.build_anon_artifact` (0 scrub hits). Remaining: confirm the SLURM check (job 43916997: prompt export + `reproduce.sh`, expected all outputs identical) and inspect `prompts.jsonl`; then decide how it is delivered (anonymous repository or supplementary zip, no local paths in the paper). The paper still needs one sentence pointing to the artifact once the delivery route is chosen.

2. **Clinician review, T-3a–e** — OUT OF SCOPE by the professor's standing decision (2026-09-25); listed last because of its long external lead time, though it would matter most for the unvalidated keys. Sub-items:
    - [ ] **T-3a** — Recruit qualified clinician reader(s) to independently assess exactly the images/stems/options shown to models — blinded initially to model outputs and generated keys.
    - [ ] **T-3b** — Have them judge, per item: is it answerable from what's shown, which answer is supported, and why ambiguous if so. Target all 38 LIL + 46 DSCR items; if that is not feasible, a prespecified stratified sample with limitations reported.
    - [ ] **T-3c** — Include representative agreement and disagreement cases from the automated audit in the writeup.
    - [ ] **T-3d** — Report independent agreement pre-adjudication, uncertainty on it, and an error-source breakdown (segmentation vs. rendering vs. target choice vs. missing evidence).
    - [ ] **T-3e** — Fallback if clinician review cannot happen in time: narrow the benchmark-validity claim and reduce DSCR's prominence in the abstract/contributions (the concordance statistic is agreement with our rule, not proof the expert labels are wrong).


    <!-- My recommendation: ship the slices with an attribution and non-commercial notice, and change the paper sentence to say so. Do you want that, or should I keep the images out as the paper currently says? -->
