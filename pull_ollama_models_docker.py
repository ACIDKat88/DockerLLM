#!/usr/bin/env python3
import requests
import sys
import os
import time
import json

# Define the models to pull
MODELS = ["mistral:latest", "mistral:7b-instruct-v0.3-q3_K_M"]

def get_ollama_base_url():
    """Get the Ollama base URL from environment or use default."""
    return os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")

def wait_for_ollama_service(base_url, max_retries=10, retry_interval=5):
    """Wait for the Ollama service to become available."""
    print(f"Waiting for Ollama service at {base_url}...")
    
    for attempt in range(1, max_retries + 1):
        try:
            print(f"Attempt {attempt}: Testing connection to {base_url}/api/tags")
            response = requests.get(f"{base_url}/api/tags", timeout=10)
            print(f"Response status code: {response.status_code}")
            
            if response.status_code == 200:
                print(f"Ollama service is available! Full response: {response.text[:200]}...")
                return True
            else:
                print(f"Got unexpected status code: {response.status_code}, response: {response.text[:200]}")
        except requests.RequestException as e:
            print(f"Attempt {attempt}/{max_retries}: Ollama service not available yet: {e}")
        
        if attempt < max_retries:
            print(f"Waiting {retry_interval} seconds before next attempt...")
            time.sleep(retry_interval)
    
    print(f"Ollama service did not become available after {max_retries} attempts")
    return False

def list_models(base_url):
    """List all models available on the Ollama server."""
    try:
        response = requests.get(f"{base_url}/api/tags")
        if response.status_code == 200:
            data = response.json()
            print(f"API response: {data}")
            return data.get("models", [])
        else:
            print(f"Error listing models: HTTP {response.status_code}")
            print(f"Response body: {response.text}")
            return []
    except requests.RequestException as e:
        print(f"Error listing models: {e}")
        return []

def pull_model(base_url, model_name):
    """Pull a model to the Ollama server."""
    print(f"Pulling model: {model_name}...")
    
    try:
        # Ollama pull API endpoint
        print(f"Sending POST request to {base_url}/api/pull with payload: {{\"name\": \"{model_name}\"}}")
        response = requests.post(
            f"{base_url}/api/pull",
            json={"name": model_name},
            timeout=30
        )
        
        print(f"Pull request response status: {response.status_code}")
        print(f"Response headers: {response.headers}")
        print(f"Response body (first 200 chars): {response.text[:200]}")
        
        if response.status_code == 200:
            print(f"Successfully started pulling {model_name}")
            
            # Check pull status until complete
            while True:
                status_response = requests.get(f"{base_url}/api/tags")
                if status_response.status_code == 200:
                    models = status_response.json().get("models", [])
                    for model in models:
                        if model.get("name") == model_name:
                            print(f"Model {model_name} is now available")
                            return True
                
                print("Waiting for model pull to complete...")
                time.sleep(10)
        else:
            print(f"Error pulling model {model_name}: HTTP {response.status_code}")
            print(f"Full response: {response.text}")
            return False
    except requests.RequestException as e:
        print(f"Error pulling model {model_name}: {e}")
        return False

def main():
    base_url = get_ollama_base_url()
    print(f"Using Ollama base URL: {base_url}")
    
    # Wait for Ollama service to be available
    if not wait_for_ollama_service(base_url):
        print("Exiting because Ollama service is not available")
        return 1
    
    # Get list of already installed models
    existing_models = list_models(base_url)
    existing_model_names = [model.get("name") for model in existing_models]
    print(f"Existing models: {existing_model_names}")
    
    # Pull models that aren't already installed
    for model_name in MODELS:
        if model_name in existing_model_names:
            print(f"Model {model_name} is already installed")
        else:
            pull_model(base_url, model_name)
    
    # Show final list of models
    print("\nFinal list of models:")
    final_models = list_models(base_url)
    for model in final_models:
        print(f"- {model.get('name')} (Size: {model.get('size', 0) / (1024*1024*1024):.2f} GB)")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 