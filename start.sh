#!/bin/bash
set -e

set -a
source .env
set +a

if [ "${OLLAMA,,}" = "true" ]; then
    echo "Ollama enabled"
    sudo docker compose --profile ollama up -d --build
else
    echo "local ollama disabled"
    sudo docker compose --profile ollama stop ollama 2>/dev/null || true
    sudo docker compose up -d --build
fi
