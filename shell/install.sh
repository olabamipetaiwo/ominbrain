#!/usr/bin/env bash
# Install all dependencies for the omnibrain evaluation
set -e
cd "$(dirname "$0")/.."

python3 -m pip install -r requirements.txt --break-system-packages
