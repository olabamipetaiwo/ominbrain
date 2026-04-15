#!/usr/bin/env bash
# Download OmniBrainBench dataset from HuggingFace.
#
# Downloads:
#   closed-ended-qa_6823.json   ~5 MB    (metadata + phase labels)
#   closed-ended-qa_6823.zip    ~734 MB  (images)
#
# Files are cached in omnibrain/data/ — re-run with --force to re-download.
set -e
cd "$(dirname "$0")/.."

python3 - <<'EOF'
from data_loader import download_dataset
import sys
force = "--force" in sys.argv
download_dataset(force=force)
EOF
