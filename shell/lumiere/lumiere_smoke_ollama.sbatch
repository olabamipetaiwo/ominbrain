#!/bin/bash
#SBATCH --job-name=lumiere_smoke
#SBATCH --account=so589980.ucf
#SBATCH --qos=so589980.ucf
#SBATCH --partition=hpg-rtx6000
#SBATCH --gres=gpu:rtx_pro_6000:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32gb
#SBATCH --time=01:30:00
#SBATCH --output=/blue/so589980.ucf/ta117847.ucf/ominbrain/logs/%x_%j.out
#SBATCH --error=/blue/so589980.ucf/ta117847.ucf/ominbrain/logs/%x_%j.err
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=Olacoderpad@gmail.com
# LUMIERE smoke test (5 cases per model, LLM-drafted/unreviewed items) for the Ollama models.
# Purpose: confirm each model loads and returns parseable JSON before the full 54-patient run.
set -e
export OLLAMA_PORT=$((11500 + SLURM_JOB_ID % 400))   # unique per job: several jobs can share a node
export OLLAMA_BASE_URL="http://localhost:${OLLAMA_PORT}/v1"
export OLLAMA_VERSION=0.33.0   # 0.20.2 has no CUDA build for the RTX PRO 6000 (falls back to CPU)
source /blue/so589980.ucf/ta117847.ucf/scripts/setup_session.sh ominbrain
cd /blue/so589980.ucf/ta117847.ucf/ominbrain
nvidia-smi -L
ollama list
for M in ${MODELS:-MedGemma-4B Gemma-3-12B Gemma-3-27B Llama-4-Scout}; do
  echo "=== smoke: $M ==="
  python run_lumiere.py --model "$M" --n-cases 5 --include-unreviewed || echo "SMOKE FAILED: $M"
done
