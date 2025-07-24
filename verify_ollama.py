#!/usr/bin/env python3
import requests
import sys
import os
import time

def check_ollama_service(base_url="http://localhost:11434"):
    """Check if the Ollama service is running and responsive."""
    try:
        response = requests.get(f"{base_url}/api/tags")
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error connecting to Ollama service at {base_url}: {e}")
        return None

def main():
    print("Verifying Ollama Docker setup...")
    
    # Get base URL from environment or use default
    base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
    print(f"Using Ollama base URL: {base_url}")
    
    # Try to connect to Ollama service
    retries = 5
    for attempt in range(1, retries + 1):
        print(f"Attempt {attempt}/{retries} to connect to Ollama...")
        result = check_ollama_service(base_url)
        if result:
            print("Successfully connected to Ollama service!")
            print("Available models:")
            for model in result.get('models', []):
                print(f"- {model.get('name')} (Size: {model.get('size') / (1024*1024*1024):.2f} GB)")
            return 0
        
        if attempt < retries:
            print(f"Waiting 5 seconds before retry...")
            time.sleep(5)
    
    print("Failed to connect to Ollama service after multiple attempts.")
    return 1

if __name__ == "__main__":
    sys.exit(main()) 