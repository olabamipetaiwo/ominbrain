# Artifact: image interventions on brain-MRI questions (LUMIERE)

Everything needed to check the paper's numbers. No model is run: the saved model responses are re-analysed.

## Quick start
    python -m venv .venv && . .venv/bin/activate
    pip install numpy pandas scipy scikit-learn pillow matplotlib
    bash reproduce.sh

Takes a few minutes on a CPU. Success looks like: every line ends in `identical`, and the v4-macro comparison ends in `0 differ`.
The regenerated tables are written to `generated/` (`tab_v4_*.tex`); the numbers cited in the paper are `generated/numbers.json`.

## What is where
| Path | Content |
|---|---|
| `data/lumiere/v4/reviewed/` | The 46-patient question items: stems, options, answer key, key origin |
| `data/lumiere/v4/slices/` | The images shown to the models (rendered from LUMIERE) |
| `data/lumiere/v4/counterfactual_pairs.json` | Donor image assigned to each patient for the swap test |
| `prompts.jsonl` | Exact system and user text of every single-question prompt (images shown as `[IMAGE]`) |
| `results/` | Saved model responses, one folder per run (`raw_results.json`) |
| `run_manifest.json`, `overrides.jsonl` | Which run supplied each response, and which later responses replaced earlier ones (the analysis keeps the last one) |
| `expected/` | The paper's statistics and tables, which `reproduce.sh` compares against |
| `analysis_versions.json` | Package versions, random seeds, script hashes |
| `SHA256SUMS` | Checksum of every file |
| `src/`, `tools/`, `config/`, `tests/` | Code |

Optional: `python -m tools.export_release_prompts --out prompts.jsonl` rebuilds `prompts.jsonl` from the items.

## Post-hoc analyses and provenance
`reproduce.sh` regenerates every cited number (`generated/numbers.json`) from the saved responses and the shipped
analysis inputs, and diffs it against `expected/`. The post-hoc donor-dependence analyses ship as precomputed inputs
(`results/lumiere_v4_donor_validation.json`, `results/lumiere_v4_robustness_*.json`, `results/lumiere_v4_perm_validation.json`),
loaded by `paper_numbers` exactly like `results/compute_budget.json`; `robustness` depends on model runs under alternative
assignments and is not regenerated from scratch, while `lumiere_v4_donor_validation` and `lumiere_v4_perm_validation` are
CPU re-analyses of the shipped responses and can be rerun directly (seeds in `analysis_versions.json`):

    python -m tools.lumiere_v4_donor_validation      # synthetic-predictor protocol validation
    python -m tools.lumiere_v4_perm_validation        # collision-repair sampling-distribution checks

- `data/lumiere/v4/alt_pairs/` holds the released alternative donor-assignment identities (5 distinct constraint-valid
  assignments + `manifest.json`), produced by `tools/lumiere_v4_altpairs.py`; `tools/lumiere_v4_robustness.py` re-runs the
  gain and permutation on each.
- `run_manifest.json` records which run folder supplied each response and the inclusion rule (folders older than the
  first admitted timestamp are ignored); `analysis_versions.json` records seeds, package versions and script hashes. Every
  reported cell traces to the single `paper_numbers` run that `reproduce.sh` reproduces.

## License
Slices and measurements are derived from the LUMIERE dataset (Suter et al., 2022, Scientific Data;
doi:10.6084/m9.figshare.c.5904905.v1), released for non-commercial use with attribution. They are shared here only for
non-commercial research evaluation; any reuse must cite LUMIERE.

## Not included
Model weights, API keys, and the full LUMIERE imaging archive.
