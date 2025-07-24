#!/bin/bash

echo "===== Starting J1 Chatbot with RAGAS Support ====="

# Check if Ollama is installed (but don't fail if not)
if ! command -v ollama &> /dev/null; then
    echo "⚠️ Ollama is not installed. RAGAS metrics will use fallback methods."
    echo "   To install Ollama, visit: https://ollama.ai/download"
else
    # If installed, check if it's running and start if needed
    if ! ollama list &> /dev/null; then
        echo "Ollama is installed but not running. Attempting to start..."
        
        # Different methods to start Ollama based on OS
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            open -a Ollama
            echo "Started Ollama on macOS"
        elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
            # Linux
            if systemctl list-unit-files | grep -q ollama; then
                sudo systemctl start ollama
                echo "Started Ollama service via systemctl"
            else
                echo "Please start Ollama manually"
            fi
        else
            # Windows/other
            echo "Please start Ollama manually on your system"
        fi
        
        # Wait for Ollama to initialize
        echo "Waiting for Ollama to initialize..."
        sleep 5
    else
        echo "✅ Ollama is already running"
    fi
fi

# Start the FastAPI application
echo "Starting FastAPI application with RAGAS support..."
python api_app.py 