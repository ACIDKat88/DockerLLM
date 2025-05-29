import os
import subprocess
import sys
import json

# Define the models to pull
MODELS = ["mistral:latest", "sskostyaev/mistral:7b-instruct-v0.2-q6_K-32k", "mistral:7b-instruct-v0.3-q3_K_M"]

# Create models directory for Ollama
OLLAMA_MODELS_DIR = "ollama_models"
os.makedirs(OLLAMA_MODELS_DIR, exist_ok=True)

def get_installed_models():
    """Get list of already installed Ollama models."""
    try:
        result = subprocess.run(
            ["ollama", "list", "--json"], 
            capture_output=True, 
            text=True, 
            check=True
        )
        models = json.loads(result.stdout)
        return [model.get("name") for model in models]
    except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
        print(f"Error checking installed models: {e}")
        return []
    except FileNotFoundError:
        print("Ollama is not installed or not in PATH")
        print("Please install Ollama from https://ollama.ai/download")
        sys.exit(1)

def pull_model(model_name):
    """Pull an Ollama model."""
    print(f"Pulling model: {model_name}...")
    try:
        subprocess.run(["ollama", "pull", model_name], check=True)
        print(f"Successfully pulled {model_name}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error pulling model {model_name}: {e}")
        return False

def configure_ollama_models_dir():
    """Configure Ollama to use our custom models directory."""
    # This is placeholder - Ollama doesn't currently support changing the storage location
    # but we can create symlinks or copy models as needed
    print(f"Ollama models will typically be stored in ~/.ollama/models")
    print(f"For Docker, we'll need to mount this directory from the host")

def main():
    print("Checking for Ollama installation...")
    
    # Check if Ollama is installed
    try:
        subprocess.run(["ollama", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Ollama is not installed or not in PATH")
        print("Please install Ollama from https://ollama.ai/download")
        sys.exit(1)
    
    # Get already installed models
    installed_models = get_installed_models()
    print(f"Already installed models: {installed_models}")
    
    # Pull models that aren't already installed
    for model in MODELS:
        if model in installed_models:
            print(f"Model {model} is already installed")
        else:
            pull_model(model)
    
    # Show all installed models after pulling
    print("\nFinal list of installed models:")
    try:
        subprocess.run(["ollama", "list"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error listing models: {e}")
    
    # Information for Docker configuration
    print("\nTo use these models in Docker, add this to your docker-compose.yml:")
    print("volumes:")
    print("  - $HOME/.ollama:/root/.ollama")
    
if __name__ == "__main__":
    main() 