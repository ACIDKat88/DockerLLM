#!/bin/bash

echo "===== J1 Chatbot Setup and Run Script ====="
echo "This script will set up the RAGAS environment and start the FastAPI server."

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "Ollama is not installed. Please install it from https://ollama.ai/download"
    echo "After installing, restart this script."
    exit 1
fi

# Check if Ollama is running
if ! ollama list &> /dev/null; then
    echo "Ollama is not running. Starting Ollama service..."
    # Different methods to start Ollama based on OS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        open -a Ollama
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        systemctl start ollama 2>/dev/null || sudo systemctl start ollama 2>/dev/null || echo "Failed to start Ollama service. Please start it manually."
    elif [[ "$OSTYPE" == "msys"* ]] || [[ "$OSTYPE" == "win32" ]]; then
        # Windows
        echo "Please start Ollama manually on Windows."
    fi
    
    # Wait for Ollama to start
    echo "Waiting for Ollama to start..."
    sleep 5
fi

# Check if the base model is available
echo "Checking for qwen3:0.6b..."
if ! ollama list | grep -q "qwen3:0.6b"; then
    echo "Pulling qwen3:0.6b model..."
    ollama pull qwen3:0.6b
else
    echo "Model qwen3:0.6b is already available."
fi

# Check if our custom model exists
if ! ollama list | grep -q "qwen3-ragas"; then
    echo "Creating custom qwen3-ragas model..."
    ollama create qwen3-ragas -f qwen3_ragas.modelfile
else
    echo "Custom qwen3-ragas model is already available."
fi

# Run the Python setup script
echo "Running RAGAS setup script..."
python setup_ragas.py

# Check if langchain-community is installed
if ! pip list | grep -q "langchain-community"; then
    echo "Installing langchain-community..."
    pip install langchain-community
else
    echo "langchain-community is already installed."
fi

# Start the FastAPI server
echo "Starting FastAPI server..."
python api_app.py 