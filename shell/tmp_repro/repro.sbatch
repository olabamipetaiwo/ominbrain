#!/bin/bash
#SBATCH --account=so589980.ucf
#SBATCH --qos=so589980.ucf
#SBATCH --partition=hpg-turin
#SBATCH --cpus-per-task=2
#SBATCH --mem=6gb
#SBATCH --time=00:45:00
#SBATCH --output=/blue/so589980.ucf/ta117847.ucf/ominbrain/shell/tmp_repro/repro_%j.log
cd /blue/so589980.ucf/ta117847.ucf/ominbrain/release/anon_artifact
source /blue/so589980.ucf/ta117847.ucf/ominbrain/.venv/bin/activate
python -m tools.export_release_prompts --out prompts.jsonl 2>&1 | tail -8
bash reproduce.sh 2>&1 | tail -16
