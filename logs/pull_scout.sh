#!/bin/bash
module load ollama/0.20.2
export OLLAMA_MODELS=/blue/so589980.ucf/ta117847.ucf/.ollama/models
export OLLAMA_HOST=127.0.0.1:11556
ollama serve > /blue/so589980.ucf/ta117847.ucf/ominbrain/logs/pull_scout_serve.log 2>&1 &
SP=$!
for i in $(seq 1 60); do curl -s $OLLAMA_HOST >/dev/null && break; sleep 1; done
ollama pull llama4:scout || echo "FAILED llama4:scout"
ollama list
kill $SP
