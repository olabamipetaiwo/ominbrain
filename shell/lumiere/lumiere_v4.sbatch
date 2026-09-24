#!/bin/bash
#SBATCH --job-name=lumiv4
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
# v4 (answerable-by-construction) item set. One job = one model x one MODE, so the 2-GPU cap can be met by chaining jobs
# with --dependency=afterany (never by giving a job fewer GPUs). Registered analysis: paper/preregistration_v4.md.
#   MODE=image    own,text,swap          AIA LIL DSCR (isolated: no upstream context)          run_lumiere_v4.py
#   MODE=context  ctx_gold,ctx_wrong,ctx_absent,flip_label,flip_window   LIL DSCR PJRF TCM       run_lumiere_v4.py
#   MODE=chain    ordinary 5-phase chain, image then text-only (own answers as context, no gating, no adaptation)
# Submit: sbatch --job-name=lumiv4_<MODE>_<Model> --export=ALL,MODELS=<Model>,MODE=<mode> shell/lumiere/lumiere_v4.sbatch
set -e
export OLLAMA_PORT=$((11500 + SLURM_JOB_ID % 400))   # unique per job: several jobs can share a node
export OLLAMA_BASE_URL="http://localhost:${OLLAMA_PORT}/v1"
export OLLAMA_VERSION=0.33.0   # 0.20.2 has no CUDA build for the RTX PRO 6000 (falls back to CPU)
source /blue/so589980.ucf/ta117847.ucf/scripts/setup_session.sh ominbrain
cd /blue/so589980.ucf/ta117847.ucf/ominbrain
nvidia-smi -L
ollama list
for M in ${MODELS:-MedGemma-4B}; do
  case "${MODE:-image}" in
    image)   echo "=== v4 image conditions: $M ==="
             python run_lumiere_v4.py --model "$M" --conditions own,text,swap --tag image ;;
    context) echo "=== v4 context conditions: $M ==="
             python run_lumiere_v4.py --model "$M" --conditions ctx_gold,ctx_wrong,ctx_absent,flip_label,flip_window --tag context ;;
    chain)   echo "=== v4 chain runs: $M ==="
             python run_lumiere.py --model "$M" --item-set v4 --include-unreviewed --no-gating --no-adaptation --n-cases 100
             python run_lumiere.py --model "$M" --item-set v4 --include-unreviewed --no-gating --no-adaptation --n-cases 100 --text-only ;;
    smoke)   echo "=== v4 smoke test: $M ==="
             python run_lumiere_v4.py --model "$M" --n-cases 2 --tag smoke ;;
    *) echo "unknown MODE=$MODE"; exit 1 ;;
  esac
done
