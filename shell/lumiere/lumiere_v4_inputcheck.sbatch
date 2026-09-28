#!/bin/bash
#SBATCH --job-name=lumiv4_inputcheck
#SBATCH --account=so589980.ucf
#SBATCH --qos=so589980.ucf
#SBATCH --partition=hpg-rtx6000
#SBATCH --gres=gpu:rtx_pro_6000:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=64gb
#SBATCH --time=02:00:00
#SBATCH --output=/blue/so589980.ucf/ta117847.ucf/ominbrain/logs/%x_%j.out
#SBATCH --error=/blue/so589980.ucf/ta117847.ucf/ominbrain/logs/%x_%j.err
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=Olacoderpad@gmail.com
# Input-handling check (paper/review.md concern 7) for the four Ollama models: serving record, image-token accounting on real v4
# items, and known-answer perception probes. tools/lumiere_v4_input_check.py; results/lumiere_v4_inputcheck_<model>_<ts>/.
# Submit: sbatch shell/lumiere/lumiere_v4_inputcheck.sbatch      (bf16 pipeline: lumiere_v4_inputcheck_bf16.sbatch)
set -e
export OLLAMA_PORT=$((11500 + SLURM_JOB_ID % 400))
export OLLAMA_BASE_URL="http://localhost:${OLLAMA_PORT}/v1"
export OLLAMA_VERSION=0.33.0   # same build as the v4 runs (0.20.2 has no CUDA build for the RTX PRO 6000)
source /blue/so589980.ucf/ta117847.ucf/scripts/setup_session.sh ominbrain
cd /blue/so589980.ucf/ta117847.ucf/ominbrain
nvidia-smi -L
ollama --version
ollama list
for M in ${MODELS:-MedGemma-4B Gemma-3-12B Gemma-3-27B Llama-4-Scout}; do
  echo "=== input check: $M ==="
  python -m tools.lumiere_v4_input_check --model "$M" || echo "!! input check failed for $M"
done
