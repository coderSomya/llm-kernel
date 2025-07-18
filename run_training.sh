#!/bin/bash

mkdir -p results

HOST_IP=$(ifconfig | grep -E "inet [0-9]" | grep -v 127.0.0.1 | head -1 | awk '{print $2}')

if [ -z "$HOST_IP" ]; then
    echo "Could not detect IP automatically."
    echo "Available interfaces:"
    ifconfig | grep -E "inet [0-9]" | grep -v 127.0.0.1
    exit 1
fi

echo "Using Ollama at: $HOST_IP:11434"

if ! curl -s "http://$HOST_IP:11434/api/tags" > /dev/null; then
    echo "Warning: Cannot reach Ollama at $HOST_IP:11434"
    echo "Make sure Ollama is running: ollama serve"
fi

docker build -t driver-eval .
docker run --rm \
    -e OLLAMA_HOST=$HOST_IP \
    -v $(pwd)/results:/app/results \
    driver-eval python3 training_loop.py "$@"

echo "Results saved:"
ls -la results/
