#!/bin/bash
#SBATCH --job-name=lumigcabl
#SBATCH --account=so589980.ucf
#SBATCH --qos=so589980.ucf
#SBATCH --partition=hpg-rtx6000
#SBATCH --gres=gpu:rtx_pro_6000:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32gb
#SBATCH --time=06:00:00
#SBATCH --output=/blue/so589980.ucf/ta117847.ucf/ominbrain/logs/%x_%j.out
#SBATCH --error=/blue/so589980.ucf/ta117847.ucf/ominbrain/logs/%x_%j.err
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=Olacoderpad@gmail.com
# TCM-leakage check (paper/update.md 2026-09-23 x14): does the TCM context effect come from the DSCR label
# alone, or from the other upstream phases? Per model, two variants of the gating-causality experiment on
# TCM only, correct/incorrect conditions only ('absent' is identical to the primary lumigc run):
#   incl-DSCR : context = the DSCR entry only
#   excl-DSCR : context = AIA + LIL + PJRF (everything except DSCR)
# Results -> results/lumiere_gcablate_<model>_<tag>_<ts>/ (separate prefix from the primary runs).
# Submit per model, e.g. `sbatch --job-name=lumigcabl_Gemma-3-12B --export=MODELS=Gemma-3-12B <this file>`.
set -e
export OLLAMA_PORT=$((11500 + SLURM_JOB_ID % 400))   # unique per job: several jobs can share a node
export OLLAMA_BASE_URL="http://localhost:${OLLAMA_PORT}/v1"
export OLLAMA_VERSION=0.33.0   # 0.20.2 has no CUDA build for the RTX PRO 6000 (falls back to CPU)
source /blue/so589980.ucf/ta117847.ucf/scripts/setup_session.sh ominbrain
cd /blue/so589980.ucf/ta117847.ucf/ominbrain
nvidia-smi -L
ollama list
for M in ${MODELS:-MedGemma-4B}; do
  echo "=== gating ablation incl-DSCR: $M ==="
  python run_lumiere_gating_causality.py --model "$M" --include-unreviewed --phases TCM \
      --conditions correct,incorrect --context-include DSCR --context-tag incl-DSCR
  echo "=== gating ablation excl-DSCR: $M ==="
  python run_lumiere_gating_causality.py --model "$M" --include-unreviewed --phases TCM \
      --conditions correct,incorrect --context-exclude DSCR --context-tag excl-DSCR
done
