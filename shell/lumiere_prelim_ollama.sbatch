#!/bin/bash
#SBATCH --job-name=lumiere_prelim
#SBATCH --account=so589980.ucf
#SBATCH --qos=so589980.ucf
#SBATCH --partition=hpg-turin
#SBATCH --gres=gpu:l4:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32gb
#SBATCH --time=06:00:00
#SBATCH --output=/blue/so589980.ucf/ta117847.ucf/ominbrain/logs/%x_%j.out
#SBATCH --error=/blue/so589980.ucf/ta117847.ucf/ominbrain/logs/%x_%j.err
# Preliminary LUMIERE run on LLM-drafted (unreviewed) items, Ollama models.
set -e
source /blue/so589980.ucf/ta117847.ucf/scripts/setup_session.sh ominbrain
cd /blue/so589980.ucf/ta117847.ucf/ominbrain
nvidia-smi -L
ollama list
for M in Qwen2.5-VL-7B MedGemma-4B; do
  echo "=== smoke: $M ==="
  python run_lumiere.py --model "$M" --n-cases 2 --include-unreviewed
  echo "=== full: $M ==="
  python run_lumiere.py --model "$M" --n-cases 54 --include-unreviewed
done
