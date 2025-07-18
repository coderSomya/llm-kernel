#!/bin/bash

mkdir -p results

# Better IP detection using your method
HOST_IP=$(ifconfig | grep -E "inet [0-9]" | grep -v 127.0.0.1 | head -1 | awk '{print $2}')

# Check if we got an IP
if [ -z "$HOST_IP" ]; then
    echo "Could not detect IP automatically."
    echo "Available interfaces:"
    ifconfig | grep -E "inet [0-9]" | grep -v 127.0.0.1
    exit 1
fi

echo "Using Ollama at: $HOST_IP:11434"

# Test if Ollama is reachable
if ! curl -s "http://$HOST_IP:11434/api/tags" > /dev/null; then
    echo "Warning: Cannot reach Ollama at $HOST_IP:11434"
    echo "Make sure Ollama is running: ollama serve"
fi

docker build -t driver-eval .
docker run --rm \
    -e OLLAMA_HOST=$HOST_IP \
    -v $(pwd)/results:/app/results \
    driver-eval python3 enhanced_evaluation.py "$@"

echo "Results saved:"
ls -la results/