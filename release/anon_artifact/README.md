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

## License
Slices and measurements are derived from the LUMIERE dataset (Suter et al., 2022, Scientific Data;
doi:10.6084/m9.figshare.c.5904905.v1), released for non-commercial use with attribution. They are shared here only for
non-commercial research evaluation; any reuse must cite LUMIERE.

## Not included
Model weights, API keys, and the full LUMIERE imaging archive.
