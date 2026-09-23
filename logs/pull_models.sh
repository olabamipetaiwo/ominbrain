#!/bin/bash
module load ollama/0.20.2
export OLLAMA_MODELS=/blue/so589980.ucf/ta117847.ucf/.ollama/models
export OLLAMA_HOST=127.0.0.1:11555
ollama serve > /blue/so589980.ucf/ta117847.ucf/ominbrain/logs/pull_serve.log 2>&1 &
SP=$!
for i in $(seq 1 60); do curl -s $OLLAMA_HOST >/dev/null && break; sleep 1; done
for T in gemma3:12b gemma3:27b llama3.2-vision:11b; do echo "=== pull $T"; ollama pull $T || echo "FAILED $T"; done
ollama list
kill $SP
