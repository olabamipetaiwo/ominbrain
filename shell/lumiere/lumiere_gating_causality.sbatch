#!/bin/bash
#SBATCH --job-name=lumigc
#SBATCH --account=so589980.ucf
#SBATCH --qos=so589980.ucf
#SBATCH --partition=hpg-rtx6000
#SBATCH --gres=gpu:rtx_pro_6000:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32gb
#SBATCH --time=08:00:00
#SBATCH --output=/blue/so589980.ucf/ta117847.ucf/ominbrain/logs/%x_%j.out
#SBATCH --error=/blue/so589980.ucf/ta117847.ucf/ominbrain/logs/%x_%j.err
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=Olacoderpad@gmail.com
# Gating-causality experiment (reviewer finding #2, paper/review.md; see
# src/gating_causality.py's module docstring for the full rationale). Same generic
# per-model shape as lumiere_prelim_ollama.sbatch -- MODELS/EXTRA_ARGS set at submission
# time, job-name overridden per model to match the lumicf_* naming convention (e.g.
# `sbatch --job-name=lumigc_Gemma-3-27B --export=MODELS=Gemma-3-27B ...`).
# Longer time budget than the full-chain run (8h vs 6h): 4 downstream phases x 3
# conditions = 12 main+probe calls/patient here, vs 5 for a normal chain run, even
# though this skips adaptation entirely (adaptation_enabled=False, always).
set -e
export OLLAMA_PORT=$((11500 + SLURM_JOB_ID % 400))   # unique per job: several jobs can share a node
export OLLAMA_BASE_URL="http://localhost:${OLLAMA_PORT}/v1"
export OLLAMA_VERSION=0.33.0   # 0.20.2 has no CUDA build for the RTX PRO 6000 (falls back to CPU)
source /blue/so589980.ucf/ta117847.ucf/scripts/setup_session.sh ominbrain
cd /blue/so589980.ucf/ta117847.ucf/ominbrain
nvidia-smi -L
ollama list
for M in ${MODELS:-MedGemma-4B}; do
  echo "=== gating-causality: $M ==="
  python run_lumiere_gating_causality.py --model "$M" --include-unreviewed ${EXTRA_ARGS:-}
done
