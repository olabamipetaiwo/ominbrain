#!/usr/bin/env bash
# Download LUMIERE tabular data (readme + RANO/demographics/completeness CSVs,
# ~250KB total) and verify collection access/license terms.
#
# Does NOT download the 32.5GB imaging archive by default — fact extraction
# (src/lumiere_facts.py) pulls only the specific members it needs via HTTP
# range requests, without downloading the full zip. Pass --full-imaging to
# download+extract the complete archive instead (only if you actually need
# every patient's full imaging, not just the ~30-patient target batch).
#
# Run on the login node — this is I/O-bound network work, not compute
# (see CLAUDE.md's golden rule: compute goes through SLURM, downloads don't).
set -e
cd "$(dirname "$0")/.."
source .venv/bin/activate

python -m src.lumiere_downloader --verify-access --tabular

if [[ "$1" == "--full-imaging" ]]; then
  python -m src.lumiere_downloader --download-imaging-full
fi
