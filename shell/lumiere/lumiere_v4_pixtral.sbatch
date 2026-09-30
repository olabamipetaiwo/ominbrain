#!/bin/bash
#SBATCH --job-name=lumiv4_pixtral
#SBATCH --account=so589980.ucf
#SBATCH --qos=so589980.ucf
#SBATCH --partition=hpg-rtx6000
#SBATCH --gres=gpu:rtx_pro_6000:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=48gb
#SBATCH --time=08:00:00
#SBATCH --output=/blue/so589980.ucf/ta117847.ucf/ominbrain/logs/%x_%j.out
#SBATCH --error=/blue/so589980.ucf/ta117847.ucf/ominbrain/logs/%x_%j.err
# Reference model: Pixtral-12B (mistral-community/pixtral-12b, HF format) in bf16 via vLLM on the v4 image conditions.
# NOTE (2026-09-29): the repo's bundled chat_template.json crashes on vLLM ("str + list": it can't render a
# list-normalized system message, and only knows type=="image" not "image_url"). We override it with our fixed
# pixtral_hf_chat_template.jinja (handles list/string system msgs + both image chunk types). Do NOT drop --chat-template.
# Reproducible image-reading feasibility point (review.md concerns 1+2). Submit: sbatch [--export=ALL,N=2] shell/lumiere/lumiere_v4_pixtral.sbatch
# N=2 runs the 2-patient smoke test (tag smoke); default runs all patients.
set -e
cd /blue/so589980.ucf/ta117847.ucf/ominbrain
source .venv/bin/activate
set -a; . ./.env; set +a
export HF_HOME=/blue/so589980.ucf/ta117847.ucf/.cache/huggingface HUGGINGFACE_HUB_CACHE=/blue/so589980.ucf/ta117847.ucf/.cache/huggingface/hub HF_HUB_OFFLINE=1
PORT=$((8200 + SLURM_JOB_ID % 700)); export VLLM_BASE_URL="http://localhost:${PORT}/v1"
nvidia-smi -L
mkdir -p .scratch
vllm serve mistral-community/pixtral-12b --port "$PORT" --dtype bfloat16 --max-model-len 16384 --limit-mm-per-prompt '{"image": 4}' --chat-template shell/lumiere/pixtral_hf_chat_template.jinja > ".scratch/vllm_pixtral_${SLURM_JOB_ID}.log" 2>&1 &
VPID=$!
trap 'kill $VPID 2>/dev/null; wait $VPID 2>/dev/null' EXIT
for i in $(seq 1 180); do
  grep -qE "Application startup complete" ".scratch/vllm_pixtral_${SLURM_JOB_ID}.log" 2>/dev/null && break
  kill -0 $VPID 2>/dev/null || { echo "vllm died"; tail -30 ".scratch/vllm_pixtral_${SLURM_JOB_ID}.log"; exit 1; }
  sleep 10
done
if [ -n "${N:-}" ]; then ARGS="--n-cases $N --tag smoke"; else ARGS="--tag ${TAG:-image}"; fi
python run_lumiere_v4.py --model Pixtral-12B-bf16 --conditions own,text,swap --phases ${PHASES:-AIA,LIL,DSCR} $ARGS
