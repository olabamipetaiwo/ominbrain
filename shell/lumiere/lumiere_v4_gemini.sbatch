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
# GEMINI_API_KEY comes from the gitignored .env. Registered analysis: paper/preregistration_v4.md (change log 2026-09-25).
# 2026-09-28: full rerun against the corrected 59-patient DSCR/TCM cohort (paper/review.md concerns 1-2);
# the old --skip-cases 2 was specific to the prior 62-patient run's partial-failure recovery and no longer applies.
set -e
cd /blue/so589980.ucf/ta117847.ucf/ominbrain
set -a; . ./.env; set +a
source .venv/bin/activate
python run_lumiere_v4.py --model Gemini-3.6-Flash --conditions own,text,swap --phases ${PHASES:-AIA,LIL,DSCR} --tag ${TAG:-image}
