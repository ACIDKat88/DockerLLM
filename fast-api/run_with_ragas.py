#!/usr/bin/env python3
"""
This script ensures the RAGAS evaluation setup is ready and then runs the FastAPI server.
It checks for Ollama, pulls the necessary models, and runs the API server.
"""

import os
import subprocess
import sys
import time

def run_command(cmd):
    """Run a command and return the output."""
    try:
        process = subprocess.Popen(
            cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        # Stream output in real-time
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(output.strip())
                
        # Get any remaining output
        stdout, stderr = process.communicate()
        if stderr and process.returncode != 0:
            print(f"Error: {stderr}")
            
        return process.returncode
    except Exception as e:
        print(f"Error running command '{cmd}': {e}")
        return 1

def check_ollama():
    """Check if Ollama is installed and running."""
    print("Checking if Ollama is installed and running...")
    
    try:
        result = subprocess.run(
            "ollama --version", 
            shell=True, 
            capture_output=True, 
            text=True
        )
        if result.returncode != 0:
            print("Ollama is not installed or not in PATH.")
            print("Please install Ollama from: https://ollama.ai/download")
            return False
            
        print(f"Ollama is installed: {result.stdout.strip()}")
        
        # Check if Ollama server is running
        result = subprocess.run(
            "ollama list", 
            shell=True, 
            capture_output=True, 
            text=True
        )
        if result.returncode != 0:
            print("Ollama server is not running.")
            print("Please start the Ollama server first.")
            return False
            
        print("Ollama server is running.")
        return True
        
    except Exception as e:
        print(f"Error checking Ollama: {e}")
        return False

def setup_models():
    """Ensure required models are available."""
    print("\nChecking for required models...")
    
    # Check for qwen3:0.6b
    result = subprocess.run(
        "ollama list", 
        shell=True, 
        capture_output=True, 
        text=True
    )
    
    if "qwen3:0.6b" not in result.stdout:
        print("Pulling qwen3:0.6b model...")
        if run_command("ollama pull qwen3:0.6b") != 0:
            print("Failed to pull qwen3:0.6b model.")
            return False
    else:
        print("qwen3:0.6b model is already available.")
    
    # Create custom RAGAS model if it doesn't exist
    if "qwen3-ragas" not in result.stdout:
        print("Creating qwen3-ragas custom model...")
        modelfile_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "qwen3_ragas.modelfile")
        if not os.path.exists(modelfile_path):
            print(f"Error: Modelfile not found at {modelfile_path}")
            return False
            
        if run_command(f"ollama create qwen3-ragas -f {modelfile_path}") != 0:
            print("Failed to create qwen3-ragas custom model.")
            return False
    else:
        print("qwen3-ragas custom model is already available.")
    
    return True

def check_dependencies():
    """Check for required Python dependencies."""
    print("\nChecking for required Python dependencies...")
    
    # Check for langchain-community
    try:
        import langchain_community
        print("langchain-community is installed.")
    except ImportError:
        print("Installing langchain-community...")
        if run_command("pip install langchain-community") != 0:
            print("Failed to install langchain-community.")
            return False
    
    return True

def main():
    """Main entry point."""
    print("=== J1 Chatbot with RAGAS Evaluation Setup ===")
    
    # Check Ollama installation
    if not check_ollama():
        sys.exit(1)
    
    # Setup required models
    if not setup_models():
        sys.exit(1)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    print("\n=== Setup complete! Starting FastAPI server... ===\n")
    
    # Run the API server
    sys.exit(run_command("python api_app.py"))

if __name__ == "__main__":
    main() 