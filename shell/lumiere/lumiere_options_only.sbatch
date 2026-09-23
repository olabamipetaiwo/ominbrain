#!/bin/bash
#SBATCH --job-name=lumiopt
#SBATCH --account=so589980.ucf
#SBATCH --qos=so589980.ucf
#SBATCH --partition=hpg-rtx6000
#SBATCH --gres=gpu:rtx_pro_6000:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32gb
#SBATCH --time=03:00:00
#SBATCH --output=/blue/so589980.ucf/ta117847.ucf/ominbrain/logs/%x_%j.out
#SBATCH --error=/blue/so589980.ucf/ta117847.ucf/ominbrain/logs/%x_%j.err
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=Olacoderpad@gmail.com
# LLM options-only baseline (paper/review.md TODO): 5 phases x 52 patients, one call each, no image/stem/chain.
# Submit per model: sbatch --job-name=lumiopt_<Model> --export=ALL,MODELS=<Model> <this file>
set -e
export OLLAMA_PORT=$((11500 + SLURM_JOB_ID % 400))   # unique per job: several jobs can share a node
export OLLAMA_BASE_URL="http://localhost:${OLLAMA_PORT}/v1"
export OLLAMA_VERSION=0.33.0   # 0.20.2 has no CUDA build for the RTX PRO 6000 (falls back to CPU)
source /blue/so589980.ucf/ta117847.ucf/scripts/setup_session.sh ominbrain
cd /blue/so589980.ucf/ta117847.ucf/ominbrain
nvidia-smi -L
ollama list
for M in ${MODELS:-MedGemma-4B}; do
  echo "=== options-only: $M ==="
  python run_lumiere_options_only.py --model "$M" --include-unreviewed
done
