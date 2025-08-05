#!/bin/bash

# GPT-OSS Agent Startup Script

# Activate virtual environment
# shellcheck source=/dev/null
source venv/bin/activate

# Check if Ollama is running
if ! pgrep -x "ollama" > /dev/null; then
    echo "Starting Ollama service..."
    nohup ollama serve > /dev/null 2>&1 &
    sleep 3
fi

# Start the GPT-OSS Agent
python gpt_oss_agent.py
