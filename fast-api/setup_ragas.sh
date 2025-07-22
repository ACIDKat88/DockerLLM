#!/bin/bash

echo "Setting up RAGAS evaluation environment..."

# Check if pip is available
if ! command -v pip &> /dev/null; then
    echo "Error: pip not found. Please install pip first."
    exit 1
fi

# Install or upgrade RAGAS
echo "Installing/upgrading RAGAS..."
pip install --upgrade ragas

# Install other required packages
echo "Installing dependencies..."
pip install transformers torch langchain langchain_community sentence_transformers

# Check if RAGAS was installed successfully
if python -c "import ragas; print(f'RAGAS version: {ragas.__version__}')" 2>/dev/null; then
    echo "RAGAS installation successful!"
else
    echo "Failed to import RAGAS. Installing compatibility version..."
    # Install older version that's known to work
    pip install "ragas==0.0.11"
    
    # Check again
    if python -c "import ragas; print(f'RAGAS version: {ragas.__version__}')" 2>/dev/null; then
        echo "RAGAS v0.0.11 installed successfully as fallback."
    else
        echo "WARNING: Failed to install RAGAS. The application will use dummy metrics."
    fi
fi

# Create a requirements.txt with fixed versions if it doesn't exist
if [ ! -f "ragas_requirements.txt" ]; then
    echo "Creating ragas_requirements.txt with fixed versions..."
    pip freeze | grep -E "ragas|transformers|torch|langchain|sentence-transformers" > ragas_requirements.txt
    echo "Created ragas_requirements.txt with the following packages:"
    cat ragas_requirements.txt
fi

echo "RAGAS setup completed." 