# Anonymous reproducibility artifact

Regenerates every statistic, macro and table of the intervention study from the shipped model responses. No model is called.

## Layout
- `src/ config/ tools/ tests/` code, same layout as the repository, so `python -m tools.<name>` runs from this directory.
- `data/lumiere/v4/` the item set: `reviewed/` items with answer keys, options and key origin; `facts/` per-patient facts;
  `measurements/` cached lesion measurements from the public segmentation masks; `slices/` the rendered slice images the models saw (derived from LUMIERE; see License); `selection_report.json` cohort and exclusion counts; `counterfactual_pairs.json` donor assignment for the swap condition.
- `results/` the raw model records (`raw_results.json` per job folder), one folder per job. Folder names end in `<date>_<time>`.
- `prompts.jsonl` the exact system and user text of every single-question prompt (image bytes replaced by `[IMAGE]`).
  Chain-run prompts paste the model's own earlier answers into later prompts, so they are built at run time
  (`src/prompts.py::build_main_prompt`); their responses are in the chain job folders (`raw_response` per question).
- `run_manifest.json`, `overrides.jsonl` which job folder supplied each record and which records replaced earlier ones.
  The loader keeps the last record per (case, phase, condition) over job folders sorted by timestamp; a rerun of the
  image-and-context conditions with a reworded DSCR stem relied on this. The manifest lists every replacement and whether the answer changed.
- `analysis_versions.json` package versions, seeds (bootstrap seed, 10,000 resamples), margin, first admitted job stamp, script hashes.
- `expected/` the statistics and generated tables shipped with the paper.

## Reproduce
    python -m venv .venv && . .venv/bin/activate && pip install numpy pandas scipy scikit-learn pillow matplotlib
    bash reproduce.sh

`reproduce.sh` reruns the statistics, supplement, baselines and table generation, then reports whether each output is identical to
`expected/`. To regenerate the prompt file: `python -m tools.export_release_prompts --out prompts.jsonl`.

## License and attribution
The slice images and measurements are derived from the LUMIERE dataset (Suter et al., 2022, Scientific Data; Figshare DOI
10.6084/m9.figshare.c.5904905.v1), which is released for non-commercial use with attribution. They are shared here for
non-commercial research evaluation only, under the same terms; any reuse must cite LUMIERE. The images are skull-stripped and
de-identified by the dataset's authors. Code in this artifact is provided for review and reproduction.

## Not included
Model weights, API keys and the full LUMIERE imaging archive. Segmentation masks are automated (not manually verified);
response ratings come from the public dataset. The answer keys are not clinician-validated.
