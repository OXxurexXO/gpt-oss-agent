#!/bin/bash

# GPT-OSS Agent Uninstall Script

echo "This will remove the GPT-OSS Agent and its components."
read -p "Are you sure? (y/N): " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Removing virtual environment..."
    rm -rf venv

    echo "Removing knowledge base..."
    rm -rf knowledge_base

    echo "Removing logs..."
    rm -rf logs

    echo "Removing temp files..."
    rm -rf temp

    echo "Removing startup script..."
    rm -f start_agent.sh

    echo "Stopping Ollama (if running)..."
    pkill ollama

    echo "GPT-OSS Agent uninstalled."
    echo "Note: Ollama and models are still installed. Remove manually if desired:"
    echo "  ollama rm gpt-oss:20b"
    echo "  ollama rm gpt-oss:120b"
    echo "  brew uninstall ollama"
else
    echo "Uninstall cancelled."
fi
