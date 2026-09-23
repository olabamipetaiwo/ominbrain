#!/bin/bash
#SBATCH --job-name=ollama_probe
#SBATCH --account=so589980.ucf
#SBATCH --qos=so589980.ucf
#SBATCH --partition=hpg-rtx6000
#SBATCH --gres=gpu:rtx_pro_6000:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32gb
#SBATCH --time=00:15:00
#SBATCH --output=/blue/so589980.ucf/ta117847.ucf/ominbrain/logs/%x_%j.out
#SBATCH --error=/blue/so589980.ucf/ta117847.ucf/ominbrain/logs/%x_%j.err
module load ollama/${OV:-0.33.0}
export OLLAMA_MODELS=/blue/so589980.ucf/ta117847.ucf/.ollama/models
export OLLAMA_HOST=127.0.0.1:11600
ollama serve > logs/probe_serve_${OV:-0.33.0}.log 2>&1 &
for i in $(seq 1 60); do curl -s $OLLAMA_HOST >/dev/null && break; sleep 1; done
nvidia-smi --query-gpu=name,driver_version --format=csv
time curl -s -m 300 $OLLAMA_HOST/api/generate -d '{"model":"medgemma:4b","prompt":"Say OK.","stream":false}' | head -c 300; echo
curl -s $OLLAMA_HOST/api/ps | head -c 400; echo
nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv
grep -aE "inference compute|offloaded" logs/probe_serve_${OV:-0.33.0}.log | cut -c1-250
