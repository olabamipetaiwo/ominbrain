# Artifact: image interventions on brain-MRI questions (LUMIERE)

This artifact regenerates every number, table and macro the paper cites, from the saved model responses.
**No model is ever called and no GPU is needed** -- the model outputs are already here and are only re-analysed on CPU.

## 1. Quick start (about 5 minutes on a laptop)

Use a clean Python environment with just three packages. Python **3.12 or newer** is required
(the analysis uses 3.12 syntax; 3.9-3.11 will not run it). You need internet access only for the `pip` step.

    python3.12 -m venv .venv
    . .venv/bin/activate
    pip install numpy==2.3.5 scipy==1.18.1 pandas==3.0.5
    bash reproduce.sh

Those are the exact versions in `analysis_versions.json`; newer compatible releases also work. These three
packages are the only dependencies on the reproduction path -- nothing else needs to be installed.

## 2. What success looks like

`reproduce.sh` recomputes the statistics from the shipped responses and diffs them against the paper's values in
`expected/`. It prints one line per artefact; a clean run looks like this and exits 0:

    lumiere_v4_stats.json identical
    lumiere_v4_supplement.json identical
    lumiere_v4_baselines.json identical
    1059 v4 macros compared, 0 differ []
    tab_v4_confusion.tex identical
    tab_v4_ctrl.tex identical
    ... (every tab_v4_*.tex) ... identical

Every line ends in `identical` and the macro line ends in `0 differ`. If any line says `DIFFERS`, or the count is
not `0 differ`, the script exits non-zero and names what changed. The freshly built files are written to `generated/`
(`numbers.json` holds the cited numbers; `tab_v4_*.tex` are the paper's tables).

## 3. What is where
| Path | Content |
|---|---|
| `data/lumiere/v4/reviewed/` | The 46-patient question items: stems, options, answer key, key origin |
| `data/lumiere/v4/slices/` | The images shown to the models (rendered from LUMIERE) |
| `data/lumiere/v4/counterfactual_pairs.json` | Donor image assigned to each patient for the swap test |
| `prompts.jsonl` | Exact system and user text of every single-question prompt (image bytes shown as `[IMAGE]`) |
| `results/` | Saved model responses, one folder per run (`raw_results.json`) |
| `run_manifest.json`, `overrides.jsonl` | Which run supplied each response, and which later responses replaced earlier ones |
| `expected/` | The paper's statistics and tables, which `reproduce.sh` compares against |
| `analysis_versions.json` | Package versions, random seeds, equivalence margin, script hashes, source commit |
| `analysis_plan.md` | The internal prespecified analysis plan and its amendment log (incl. the cohort rebuild from 62 to 46); written before the model runs, not externally timestamped |
| `SHA256SUMS` | Checksum of every file (`sha256sum -c SHA256SUMS` to verify) |
| `src/`, `tools/`, `config/`, `tests/` | The analysis code (`reproduce.sh` runs `tools/`) |

`prompts.jsonl` can be rebuilt from the items with `python -m tools.export_release_prompts --out prompts.jsonl`.
A sanity-test of the item construction is available with `python -m tests.test_lumiere_v4`.

## 4. How a response is chosen (provenance)
A model may have several run folders. The loader (`tools.lumiere_v4_stats.load_records`) merges them **oldest-first,
sorted by the run timestamp** (the `YYYYMMDD_HHMMSS` at the end of each folder name) and keeps the last record for each
`(case_id, phase, condition)`, so **the newest run wins**; folders with a date before `min_stamp` ran on an earlier item
set and are ignored. `run_manifest.json` lists, per model, every folder in timestamp order, how many of its records were
used, and how many were superseded by a later run; `overrides.jsonl` has one line per superseded record and whether the
answer letter changed. Every reported cell therefore traces to the single `paper_numbers` run that `reproduce.sh` reproduces.

## 5. Post-hoc analyses (shipped as precomputed inputs)
The donor-dependence analyses are loaded by `paper_numbers` as precomputed inputs, like `results/compute_budget.json`.
`results/lumiere_v4_robustness_*.json` depends on model runs under alternative donor assignments and is NOT regenerated
from scratch by `reproduce.sh`. The other two are CPU re-analyses of the shipped responses and can be rerun directly
(seeds in `analysis_versions.json`):

    python -m tools.lumiere_v4_donor_validation   # synthetic-predictor validation of the donor-tracking test
    python -m tools.lumiere_v4_perm_validation    # Type-I calibration of the conditional donor-label permutation

`data/lumiere/v4/alt_pairs/` holds the released alternative donor-assignment identities (5 constraint-valid assignments
+ `manifest.json`, from `tools/lumiere_v4_altpairs.py`); `tools/lumiere_v4_robustness.py` re-runs the gain and permutation
on each. The conditional permutation (`tools/lumiere_v4_strat_perm.py`) assigns constrained donor-key labels sequentially
in random block order; it is constraint-valid but not exactly uniform over admissible allocations, so it is reported as a
reference distribution for the synthetic nulls evaluated, not as a randomization test for the image assignment.

## 6. License
Slices and measurements are derived from the LUMIERE dataset (Suter et al., 2022, Scientific Data;
doi:10.6084/m9.figshare.c.5904905.v1), released for non-commercial use with attribution. They are shared here only for
non-commercial research evaluation; any reuse must cite LUMIERE.

## 7. Not included
Model weights, API keys, and the full LUMIERE imaging archive.
