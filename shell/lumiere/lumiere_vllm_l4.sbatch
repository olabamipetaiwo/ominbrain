#!/bin/bash
#SBATCH --job-name=lumiere_vllm_l4
#SBATCH --account=so589980.ucf
#SBATCH --qos=so589980.ucf
#SBATCH --partition=hpg-turin
#SBATCH --gres=gpu:l4:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16gb
#SBATCH --time=03:00:00
#SBATCH --output=/blue/so589980.ucf/ta117847.ucf/ominbrain/logs/%x_%j.out
#SBATCH --error=/blue/so589980.ucf/ta117847.ucf/ominbrain/logs/%x_%j.err
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=Olacoderpad@gmail.com
# Preliminary LUMIERE run (LLM-drafted, unreviewed items) for one vLLM model.
# Usage: sbatch --export=ALL,MODEL=<ModelName> shell/lumiere/lumiere_vllm_l4.sbatch
set -e
: "${MODEL:?set MODEL via --export=ALL,MODEL=<ModelName>}"
module load python/3.12 2>/dev/null || true
cd /blue/so589980.ucf/ta117847.ucf/ominbrain
nvidia-smi -L
bash shell/lumiere/run_vllm_model_lumiere.sh "$MODEL" --n-cases 54 --include-unreviewed
