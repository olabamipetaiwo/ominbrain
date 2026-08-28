#!/usr/bin/env bash
# Start a vLLM server for one model, run an eval through it, then tear the server
# down. Must be run inside a GPU srun/sbatch job — this does real GPU inference,
# unlike weight downloads which are fine on the login node.
#
# Uses run_omnibrain.py's own --n-cases default (100) unless overridden below — in
# practice this just pulls in every multi-phase case the dataset's case-builder
# finds (~10 under the default min-phases=2 filter), it doesn't mean 100 distinct
# cases actually exist.
#
# Usage:
#   bash shell/run_vllm_model.sh <ModelName> [extra run_omnibrain.py args]
#
# Example:
#   srun --qos=so589980.ucf --partition=hpg-b200 --gres=gpu:b200:1 \
#        --cpus-per-task=8 --mem=128gb --time=01:00:00 \
#        bash shell/run_vllm_model.sh InternVL3-38B --n-cases 5   # override for a quick check
#
# Looks up the model's HF repo id and port from config/models.py directly (no
# duplicated model list to drift out of sync — see run_opensource.sh/run_medical.sh
# history for what happens when the list is hand-maintained separately).
set -uo pipefail
cd "$(dirname "$0")/.."

MODEL_NAME=${1:?"Usage: bash shell/run_vllm_model.sh <ModelName> [extra args]"}
shift

source .venv/bin/activate
export HF_HOME=${HF_HOME:-/blue/so589980.ucf/$USER/.cache/huggingface}
export HUGGINGFACE_HUB_CACHE="$HF_HOME/hub"

LOOKUP=$(python3 -c "
from config.models import MODEL_MAP
import sys
m = MODEL_MAP.get('$MODEL_NAME')
if m is None:
    sys.exit('Unknown model: $MODEL_NAME')
if m.get('backend') != 'vllm':
    sys.exit('Model $MODEL_NAME is not vllm-backed (backend=' + str(m.get('backend')) + ')')
port = m['base_url'].rsplit(':', 1)[1].split('/')[0]
print(m['model'] + ' ' + port + ' ' + m.get('chat_template', ''))
")
if [ $? -ne 0 ] || [ -z "$LOOKUP" ]; then
    echo "$LOOKUP"
    exit 1
fi
read -r REPO PORT CHAT_TEMPLATE <<< "$LOOKUP"

mkdir -p .scratch
SAFE_NAME=$(echo "$MODEL_NAME" | tr '/' '_')
SERVE_LOG=".scratch/vllm_serve_${SAFE_NAME}.log"

CHAT_TEMPLATE_ARGS=()
if [ -n "$CHAT_TEMPLATE" ]; then
    CHAT_TEMPLATE_ARGS=(--chat-template "$CHAT_TEMPLATE")
    echo "===== $MODEL_NAME -> $REPO on port $PORT (chat template: $CHAT_TEMPLATE) ====="
else
    echo "===== $MODEL_NAME -> $REPO on port $PORT ====="
fi

vllm serve "$REPO" --port "$PORT" --trust-remote-code --enforce-eager "${CHAT_TEMPLATE_ARGS[@]}" > "$SERVE_LOG" 2>&1 &
VLLM_PID=$!

cleanup() {
    echo "===== tearing down vllm server (pid $VLLM_PID) ====="
    kill "$VLLM_PID" 2>/dev/null
    wait "$VLLM_PID" 2>/dev/null
}
trap cleanup EXIT

echo "===== waiting for server readiness (up to 25 min) ====="
READY=0
for i in $(seq 1 150); do
    if grep -qE "Application startup complete|Uvicorn running" "$SERVE_LOG" 2>/dev/null; then
        READY=1
        break
    fi
    if ! kill -0 "$VLLM_PID" 2>/dev/null; then
        echo "!!!! vllm process died before becoming ready !!!!"
        break
    fi
    sleep 10
done

if [ "$READY" != "1" ]; then
    echo "===== RESULT: FAILED — server did not become ready ====="
    tail -80 "$SERVE_LOG"
    exit 1
fi

echo "===== SERVER READY — running eval ====="
python3 run_omnibrain.py --model "$MODEL_NAME" "$@"
STATUS=$?

if [ $STATUS -eq 0 ]; then
    echo "===== RESULT: SUCCESS — $MODEL_NAME served and evaluated ====="
else
    echo "===== RESULT: FAILED — eval run exited with status $STATUS ====="
fi

exit $STATUS
