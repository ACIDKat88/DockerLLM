#!/bin/bash

# Script to download Qwen3 0.6B model for Docker containers

# Model directories
FAST_API_MODEL_DIR="$(pwd)/fast-api/models/qwen3-0.6b"
DATABASES_MODEL_DIR="$(pwd)/databases/models/qwen3-0.6b"

# Create directories if they don't exist
mkdir -p "$FAST_API_MODEL_DIR"
mkdir -p "$DATABASES_MODEL_DIR"

echo "Downloading Qwen3 0.6B model files..."

# Use Ollama to pull the model temporarily
echo "Pulling model with Ollama..."
ollama pull qwen3:0.6b

# Copy model files from Ollama's directory to our model directories
echo "Copying model files to our directories..."
OLLAMA_MODEL_DIR="$HOME/.ollama/models"

# Check if the Ollama model directory exists and if the model is there
if [ -d "$OLLAMA_MODEL_DIR" ]; then
    # Find the Qwen3 model files
    QWEN_MODEL_FILES=$(find "$OLLAMA_MODEL_DIR" -name "*qwen3*0.6b*")
    
    if [ -n "$QWEN_MODEL_FILES" ]; then
        echo "Found Qwen3 0.6B model files in Ollama directory."
        
        # Copy to the fast-api models directory
        echo "Copying to $FAST_API_MODEL_DIR..."
        cp -r $QWEN_MODEL_FILES "$FAST_API_MODEL_DIR"
        
        # Copy to the databases models directory
        echo "Copying to $DATABASES_MODEL_DIR..."
        cp -r $QWEN_MODEL_FILES "$DATABASES_MODEL_DIR"
        
        echo "Model files copied successfully!"
    else
        echo "Error: Qwen3 0.6B model files not found in Ollama directory."
        exit 1
    fi
else
    echo "Error: Ollama model directory not found."
    exit 1
fi

# Create a modelfile for Docker
cat > "$FAST_API_MODEL_DIR/Modelfile" << EOL
FROM qwen3:0.6b

# Customize the Qwen3 0.6B model for RAG evaluation tasks
PARAMETER temperature 0.1
PARAMETER top_p 0.9
PARAMETER seed 42

# System prompt to specialize the model for evaluation tasks
SYSTEM """
You are a specialized AI assistant focused exclusively on evaluating the quality of retrieval-augmented generation (RAG) systems.
Your job is to critically analyze:

1. FAITHFULNESS: Whether answers contain only information present in the provided context
2. ANSWER RELEVANCY: How well answers address the original question
3. CONTEXT RELEVANCY: How relevant retrieved context passages are to the question
4. CONTEXT PRECISION: The proportion of relevant information in retrieved contexts
5. CONTEXT RECALL: How well retrieved contexts cover all aspects of the question

Be precise, fair, and thorough in your evaluation. Your goal is to help improve RAG systems by providing accurate assessments.
"""
EOL

# Copy modelfile to databases directory as well
cp "$FAST_API_MODEL_DIR/Modelfile" "$DATABASES_MODEL_DIR/"

# Create a simple README in both directories
README_CONTENT="# Qwen3 0.6B for RAGAS Evaluation
Model size: ~523MB
Used for evaluating RAG system performance with RAGAS metrics.

This model is used by the ragas_evaluator.py module to calculate:
- Faithfulness
- Answer Relevancy
- Context Relevancy
- Context Precision
- Context Recall"

echo "$README_CONTENT" > "$FAST_API_MODEL_DIR/README.md"
echo "$README_CONTENT" > "$DATABASES_MODEL_DIR/README.md"

echo "================================================"
echo "Qwen3 0.6B model setup for Docker complete!"
echo "Model files are available in:"
echo "1. $FAST_API_MODEL_DIR"
echo "2. $DATABASES_MODEL_DIR"
echo ""
echo "Don't forget to update your Docker configuration to mount these directories"
echo "================================================" 