# Task: preliminary LUMIERE experiments

Run the 4 open-weight models on the LUMIERE chains using the LLM-drafted
(unreviewed) items. All 269 items are still `pending` expert review, so every run
passes `--include-unreviewed`. Label these results "LLM-drafted, unreviewed" in the paper.

**Professor's constraint (2026-09-21):** no China-developed models. Removed: Qwen2.5-VL,
Qwen3-VL, InternVL3, HuatuoGPT-V, Lingshu (and DeepSeek). Llama/Gemma-family models approved.

- Data: 54 patients, 5 phases (AIA -> LIL -> DSCR -> PJRF -> TCM)
- Open-weight models only (professor: "we can try with the open-weight models"). API models
  (Gemini-2.5-Pro, GPT-5, Claude-4.5-Sonnet) are in `API_MODELS`: optional, not run by `--all-models`
- GPU: RTX PRO 6000 (96GB) on `hpg-rtx6000`, QOS `so589980.ucf` (the `-b` QOS is rejected there)
- Run from the project root: `/blue/so589980.ucf/ta117847.ucf/ominbrain`
- Logs: `logs/<jobname>_<jobid>.out|.err`. Results: `results/lumiere_<model>_<timestamp>/`

## Models and commands

| # | Model | Backend | Hardware | Script |
|---|---|---|---|---|
| 1 | MedGemma-4B | Ollama | 1 RTX PRO 6000 (`hpg-rtx6000`) | `lumiere_prelim_ollama.sbatch` |
| 2 | Gemma-3-12B | Ollama | 1 RTX PRO 6000 (`hpg-rtx6000`) | `lumiere_prelim_ollama.sbatch` |
| 3 | Gemma-3-27B | Ollama (Q4, ~17GB) | 1 RTX PRO 6000 (`hpg-rtx6000`) | `lumiere_prelim_ollama.sbatch` |
| 4 | Llama-4-Scout | Ollama | 1 RTX PRO 6000 (`hpg-rtx6000`) | `lumiere_prelim_ollama.sbatch` |

All scripts are in `shell/lumiere/`. MedGemma weights are cached on `/blue`;
the Gemma-3 and Llama-4-Scout tags must be pulled first (login node is fine, with
`OLLAMA_MODELS=/blue/so589980.ucf/ta117847.ucf/.ollama/models` and `ollama serve` running):
`ollama pull gemma3:12b gemma3:27b llama4:scout` (one tag per pull command).

### Step 1: Ollama models (1-4), one job each
```bash
sbatch --export=ALL,MODELS=MedGemma-4B          shell/lumiere/lumiere_prelim_ollama.sbatch
sbatch --export=ALL,MODELS=Gemma-3-12B          shell/lumiere/lumiere_prelim_ollama.sbatch
sbatch --export=ALL,MODELS=Gemma-3-27B          shell/lumiere/lumiere_prelim_ollama.sbatch
sbatch --export=ALL,MODELS=Llama-4-Scout shell/lumiere/lumiere_prelim_ollama.sbatch
```
Check each log before continuing.

## Monitor
```bash
squeue -u $USER
tail -f logs/<jobname>_<jobid>.out
```

## Notes
- Scripts are syntax-checked but untested. Time limit (6h Ollama) are guesses.
- `lumiere_vllm_*.sbatch` are no longer used (no vLLM models remain).
- Ollama default quantization (Q4) applies to the Gemma/Llama models — state this in the methods.
- Llava-Med-7B was removed (2026-09-21) because it cannot produce the required JSON.
- After the runs: report PJRF and TCM separately with Wilson CIs, do not pool them.

## After all runs: compile the comparison table (login node is fine, read-only)
```bash
source .venv/bin/activate
python -m tools.compile_lumiere_results
```
Reads the latest `results/lumiere_<model>_*/raw_results.json` per model and writes
`results/lumiere_summary.md` and `results/lumiere_summary.csv` (per-phase accuracy,
Wilson CI, n; PJRF and TCM kept separate).


Plan


The results are in, so the main open question is what they can support. The answer keys are still unreviewed LLM drafts, and the length bias means the later-phase numbers are partly guessable. My suggested order:

1. Fix the option-length bias in the items. This blocks everything else. 

Change the drafter prompt so distractors match the correct option's length and hedging style. 

Re-draft only TCM, PJRF and DSCR, since draft_all() skips patients that already have drafts unless forced. 
Then run python -m tools.check_option_bias and aim for about 25–35% on each phase.


--
Still to do after the run:
What's next, once the run finishes:
1. Run check_option_bias on drafts_v2/ for all 54 patients and check the wording cues. The pilot's TCM distractors were still somewhat more absolute than the correct answers.
2. Swap drafts_v2 into drafts/, keeping a backup, and rebuild the review artifact for the expert.
3. Re-run the evals on the new PJRF/TCM items. The old PJRF/TCM results no longer apply to the new questions./
----


2. Run a text-only baseline (no image) on the same items with one or two models. If accuracy stays high without the image, the phase is testing text priors, not imaging. This is also what the paper's claim needs, since the perception failures dominate. It would take about an hour of GPU time per model.

3. Investigate LIL. It is the weak phase (31–54%) and it drives the gate, so it determines how many chains complete. Check whether the failures are genuinely perception errors, or whether the LIL facts don't match what is visible in the image slices.

4. Send the expert the review artifact. This is the real gate on the paper, and it should go out after step 1 so the items are final. Ask the reviewer to flag length and wording cues as well.

5. Housekeeping. Run tools/compile_lumiere_results.py for the cross-model table, decide how to handle MedGemma's parse failures, and log this session in paper/update.md. Nothing is committed yet, so the notes, the new script and the modified files are all uncommitted.

