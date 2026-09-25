#!/bin/bash
#SBATCH --job-name=lumiv4_bf16_Gemma-3-27B
#SBATCH --account=so589980.ucf
#SBATCH --qos=so589980.ucf
#SBATCH --partition=hpg-rtx6000
#SBATCH --gres=gpu:rtx_pro_6000:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=96gb
#SBATCH --time=08:00:00
#SBATCH --output=/blue/so589980.ucf/ta117847.ucf/ominbrain/logs/%x_%j.out
#SBATCH --error=/blue/so589980.ucf/ta117847.ucf/ominbrain/logs/%x_%j.err
# Precision control: Gemma-3-27B in bf16 (google/gemma-3-27b-it, vLLM) on the v4 image conditions, to separate quantization
# from model quality in the open-model AIA/LIL results. Submit: sbatch [--export=ALL,N=2] shell/lumiere/lumiere_v4_bf16.sbatch
# N=2 runs the 2-patient smoke test (tag smoke); default runs all patients.
set -e
cd /blue/so589980.ucf/ta117847.ucf/ominbrain
source .venv/bin/activate
set -a; . ./.env; set +a
export HF_HOME=/blue/so589980.ucf/ta117847.ucf/.cache/huggingface HUGGINGFACE_HUB_CACHE=/blue/so589980.ucf/ta117847.ucf/.cache/huggingface/hub HF_HUB_OFFLINE=1
PORT=$((8200 + SLURM_JOB_ID % 700)); export VLLM_BASE_URL="http://localhost:${PORT}/v1"
nvidia-smi -L
mkdir -p .scratch
vllm serve google/gemma-3-27b-it --port "$PORT" --dtype bfloat16 --max-model-len 8192 --limit-mm-per-prompt '{"image": 4}' > ".scratch/vllm_bf16_${SLURM_JOB_ID}.log" 2>&1 &
VPID=$!
trap 'kill $VPID 2>/dev/null; wait $VPID 2>/dev/null' EXIT
for i in $(seq 1 180); do
  grep -qE "Application startup complete" ".scratch/vllm_bf16_${SLURM_JOB_ID}.log" 2>/dev/null && break
  kill -0 $VPID 2>/dev/null || { echo "vllm died"; tail -30 ".scratch/vllm_bf16_${SLURM_JOB_ID}.log"; exit 1; }
  sleep 10
done
if [ -n "${N:-}" ]; then ARGS="--n-cases $N --tag smoke"; else ARGS="--tag image"; fi
python run_lumiere_v4.py --model Gemma-3-27B-bf16 --conditions own,text,swap --phases AIA,LIL,DSCR $ARGS
