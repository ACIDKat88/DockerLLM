#!/bin/bash

# Build custom Qwen3 model for RAGAS evaluation
echo "Building custom Qwen3 RAGAS model..."

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "Ollama is not installed. Please install it first."
    echo "Visit https://ollama.ai/download for installation instructions."
    exit 1
fi

# Check if the modelfile exists
if [ ! -f "/home/cm36/Updated-LLM-Project/full/flask-api/qwen3_ragas.modelfile" ]; then
    echo "Error: qwen3_ragas.modelfile not found in the current directory."
    exit 1
fi

# Build the model
echo "Creating Qwen3 RAGAS model..."
ollama create qwen3-ragas -f qwen3_ragas.modelfile

# Verify the model is available
if ollama list | grep -q "qwen3-ragas"; then
    echo "✓ Custom Qwen3 RAGAS model created successfully!" 
    echo "  The model will now be used automatically for RAGAS evaluations."
else
    echo "× Failed to create custom model. Check Ollama logs for details."
    exit 1
fi

# Make the script executable
chmod +x build_ragas_model.sh

echo "Done." 