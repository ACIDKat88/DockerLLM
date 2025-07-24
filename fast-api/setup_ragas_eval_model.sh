#!/bin/bash

# Script to download and set up Qwen3 0.6B model for RAGAS evaluation

echo "Setting up Qwen3 0.6B model for RAGAS evaluation..."

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "Ollama not found. Please install Ollama first:"
    echo "curl -fsSL https://ollama.com/install.sh | sh"
    exit 1
fi

# Pull the Qwen3 0.6B model (very small but capable for evaluation tasks)
echo "Downloading Qwen3 0.6B model (this should be quick, only 523MB)..."
ollama pull qwen3:0.6b

# Verify the model was downloaded
if [ $? -eq 0 ]; then
    echo "Qwen3 0.6B model successfully downloaded!"
    echo "Model size: ~523MB, ideal for lightweight evaluation tasks"
else
    echo "Error downloading the model. Please check your internet connection and try again."
    exit 1
fi

# Create the custom RAGAS evaluator model
echo -e "\nCreating specialized RAGAS evaluator model..."
if [ -f "ragas_evaluator.Modelfile" ]; then
    ollama create ragas-evaluator -f ragas_evaluator.Modelfile
    
    if [ $? -eq 0 ]; then
        echo "Custom RAGAS evaluator model created successfully!"
        # Update the model name in the ragas_evaluator.py file
        sed -i 's/EVAL_MODEL = "qwen3:0.6b"/EVAL_MODEL = "ragas-evaluator"/' ragas_evaluator.py
        echo "Updated ragas_evaluator.py to use the custom model"
    else
        echo "Error creating custom model. Using base Qwen3 0.6B model instead."
    fi
else
    echo "Modelfile not found. Using base Qwen3 0.6B model instead."
fi

# Install required Python packages for RAGAS with Ollama
echo -e "\nInstalling required Python packages..."
pip install ragas langchain-community langchain

echo ""
echo "Setup complete! You can now use the model for RAGAS evaluation."
echo "The model will be used automatically by the ragas_evaluator.py module."
echo ""
echo "To test the model, you can run:"
echo "ollama run ragas-evaluator \"Evaluate if this answer is relevant to the question...\""
echo ""
echo "Note: Make sure Ollama is running with 'ollama serve' before starting the API" 