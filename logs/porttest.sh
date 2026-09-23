#!/bin/bash
module load ollama/0.33.0
export OLLAMA_MODELS=/blue/so589980.ucf/ta117847.ucf/.ollama/models OLLAMA_HOST=127.0.0.1:11677 APPTAINERENV_OLLAMA_HOST=127.0.0.1:11677
ollama serve > /blue/so589980.ucf/ta117847.ucf/ominbrain/logs/porttest.log 2>&1 &
SP=$!
sleep 12
grep -aE "Listening" /blue/so589980.ucf/ta117847.ucf/ominbrain/logs/porttest.log | cut -c1-140
echo "11677: $(curl -s -m 3 127.0.0.1:11677/api/version)"
echo "11434: $(curl -s -m 3 127.0.0.1:11434/api/version)"
kill $SP; pkill -u $USER -f "^/usr/bin/ollama serve"
