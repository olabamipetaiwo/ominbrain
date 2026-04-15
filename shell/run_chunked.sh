#!/usr/bin/env bash
# Run evaluation in parallel chunks — useful for large local models.
# Splits cases across N processes running simultaneously.
#
# Usage:
#   bash shell/run_chunked.sh Qwen3-VL-30B 4     # 4 parallel chunks
#   bash shell/run_chunked.sh InternVL3-38B 2
#
# Each chunk writes results to results/<ModelName>_chunk<idx>_<timestamp>/
set -e
cd "$(dirname "$0")/.."

MODEL=${1:?"Usage: bash shell/run_chunked.sh <model-name> <num-chunks>"}
N=${2:-4}

echo "Running $MODEL in $N chunks in parallel…"

for i in $(seq 0 $((N-1))); do
    python3 run_omnibrain.py \
        --model "$MODEL" \
        --num-chunks "$N" \
        --chunk-idx "$i" \
        "${@:3}" &
    echo "  Launched chunk $i (PID $!)"
done

wait
echo "All $N chunks complete."
