#!/bin/bash
#SBATCH --job-name=lumiere_vllm_b200
#SBATCH --account=so589980.ucf
#SBATCH --qos=so589980.ucf
#SBATCH --partition=hpg-b200
#SBATCH --gres=gpu:b200:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64gb
#SBATCH --time=04:00:00
#SBATCH --output=/blue/so589980.ucf/ta117847.ucf/ominbrain/logs/%x_%j.out
#SBATCH --error=/blue/so589980.ucf/ta117847.ucf/ominbrain/logs/%x_%j.err
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=Olacoderpad@gmail.com
# Preliminary LUMIERE run (LLM-drafted, unreviewed items) for one vLLM model.
# Usage: sbatch --export=ALL,MODEL=<ModelName> shell/lumiere/lumiere_vllm_b200.sbatch
set -e
: "${MODEL:?set MODEL via --export=ALL,MODEL=<ModelName>}"
module load python/3.12 2>/dev/null || true
cd /blue/so589980.ucf/ta117847.ucf/ominbrain
nvidia-smi -L
bash shell/lumiere/run_vllm_model_lumiere.sh "$MODEL" --n-cases 54 --include-unreviewed
