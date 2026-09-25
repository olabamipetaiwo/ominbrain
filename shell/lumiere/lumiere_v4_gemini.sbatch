#!/bin/bash
#SBATCH --job-name=lumiv4_image_Gemini-3.6-Flash
#SBATCH --account=so589980.ucf
#SBATCH --qos=so589980.ucf
#SBATCH --cpus-per-task=2
#SBATCH --mem=8gb
#SBATCH --time=08:00:00
#SBATCH --output=/blue/so589980.ucf/ta117847.ucf/ominbrain/logs/%x_%j.out
#SBATCH --error=/blue/so589980.ucf/ta117847.ucf/ominbrain/logs/%x_%j.err
# Positive-control run: Gemini-3.6-Flash through Google's API (no GPU). Image conditions only, AIA LIL DSCR.
# Patients 1-2 already ran (results/lumiere_v4_Gemini-3.6-Flash_part1_*, same code and settings); this job runs the rest.
# GEMINI_API_KEY comes from the gitignored .env. Registered analysis: paper/preregistration_v4.md (change log 2026-09-25).
set -e
cd /blue/so589980.ucf/ta117847.ucf/ominbrain
set -a; . ./.env; set +a
source .venv/bin/activate
python run_lumiere_v4.py --model Gemini-3.6-Flash --conditions own,text,swap --phases AIA,LIL,DSCR --skip-cases 2 --tag image
