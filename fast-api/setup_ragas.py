#!/usr/bin/env python3
import os
import subprocess
import sys
import time
import traceback

def run_command(command):
    """Run a shell command and return its stdout on success, None on failure.
    Prints detailed error information to stdout if the command fails.
    """
    current_cwd = os.getcwd()
    print(f"Running command: {command} (from CWD: {current_cwd})")
    try:
        process = subprocess.run(
            command,
            shell=True,        # shell=True is used for convenience
            capture_output=True, # Captures stdout and stderr
            text=True,         # Decodes stdout/stderr as text
            check=False        # Do not raise CalledProcessError, check returncode manually
        )

        if process.returncode == 0:
            # Command was successful
            return process.stdout
        else:
            # Command failed
            print(f"Command failed with exit code {process.returncode}")
            if process.stdout and process.stdout.strip():
                print(f"--- Stdout from failed command ---\\n{process.stdout.strip()}")
            else:
                print("--- Stdout from failed command was empty ---")
            
            if process.stderr and process.stderr.strip():
                print(f"--- Stderr from failed command ---\\n{process.stderr.strip()}")
            else:
                print("--- Stderr from failed command was empty ---")
            return None # Indicate failure

    except FileNotFoundError:
        # It's good practice to specify the command that was not found if possible
        cmd_to_report = command.split()[0] if isinstance(command, str) else command[0]
        print(f"Error: The command '{cmd_to_report}' was not found. Is it in your PATH?")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while trying to run command: {command}")
        print(f"Exception type: {type(e).__name__}")
        print(f"Exception details: {e}")
        traceback.print_exc()
        return None

def check_ollama_installed():
    """Check if Ollama is installed and running."""
    try:
        output = run_command("ollama --version")
        if output:
            print(f"Ollama is installed: {output.strip()}")
            return True
        else:
            print("Ollama version check failed")
            return False
    except Exception as e:
        print(f"Ollama is not installed or not in PATH: {e}")
        return False

def build_ragas_model():
    """Build the qwen3-ragas Ollama model from the modelfile."""
    print("\n=== Building qwen3-ragas model ===")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    modelfile_name = "qwen3_ragas.modelfile"
    modelfile_abs_path = os.path.join(script_dir, modelfile_name)
    
    if not os.path.exists(modelfile_abs_path):
        print(f"Error: Modelfile not found at {modelfile_abs_path}")
        return False
    
    print(f"Target modelfile: {modelfile_abs_path}")
    
    # Command uses relative path, CWD will be changed to script_dir
    cmd = f"ollama create qwen3-ragas -f {modelfile_name}"
    
    original_cwd = os.getcwd()
    try:
        print(f"Original CWD: {original_cwd}")
        os.chdir(script_dir) 
        print(f"Temporarily changed CWD to: {script_dir} for ollama create")
        
        output = run_command(cmd) # run_command now more verbose

        if output is not None: # run_command returns stdout on success, None on failure
            print("Model created successfully!")
            if output.strip():
                 print(f"--- Ollama create stdout ---\\n{output.strip()}")
            return True
        else:
            print("Failed to create model (further details should be above).")
            return False
            
    except Exception as e:
        print(f"An error occurred during model building process: {e}")
        traceback.print_exc()
        return False
    finally:
        os.chdir(original_cwd) 
        print(f"Restored CWD to: {original_cwd}")

def test_ragas_model():
    """Test that the qwen3-ragas model works with a simple evaluation prompt."""
    print("\n=== Testing qwen3-ragas model ===")
    
    # Test prompt for RAGAS evaluation
    test_prompt = """
<RAGAS Evaluation Task>
Question: What is the capital of France?
Generated Answer: The capital of France is Paris, a city known for its iconic Eiffel Tower.
Retrieved Context: Paris is the capital and most populous city of France. It has been a major European city since the 17th century.

Evaluation:
Please evaluate the faithfulness of this answer to the provided context.
</RAGAS Evaluation Task>
"""
    
    # Create a temporary file for the prompt
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp:
        tmp.write(test_prompt)
        tmp_path = tmp.name
    
    try:
        # Run Ollama with the test prompt
        cmd = f'ollama run qwen3-ragas -f {tmp_path}'
        output = run_command(cmd)
        
        if not output:
            print("Model test failed: No output")
            return False
        
        # Check for expected output patterns
        if "faithfulness" in output.lower() and "score" in output.lower():
            print("Model test successful!")
            print("\nSample output:")
            print("---")
            print(output[:500] + ("..." if len(output) > 500 else ""))
            print("---")
            return True
        else:
            print("Model test output doesn't contain expected evaluation patterns")
            print("\nOutput received:")
            print("---")
            print(output[:500] + ("..." if len(output) > 500 else ""))
            print("---")
            return False
    except Exception as e:
        print(f"Error testing model: {e}")
        traceback.print_exc()
        return False
    finally:
        # Clean up the temporary file
        os.unlink(tmp_path)

def test_langchain_integration():
    """Test that the model works with LangChain."""
    print("\n=== Testing LangChain integration with qwen3-ragas ===")
    
    try:
        from langchain_community.chat_models import ChatOllama
        
        # Initialize Ollama with our custom model
        llm = ChatOllama(
            model="qwen3-ragas",
            temperature=0.1,
            verbose=True
        )
        
        # Test with a simple prompt
        prompt = "Evaluate the faithfulness of this answer: The answer is Paris, when the context mentions Paris is the capital of France."
        print(f"Sending prompt: {prompt}")
        
        # Run the test
        start_time = time.time()
        response = llm.invoke(prompt)
        end_time = time.time()
        
        print(f"Response received in {end_time - start_time:.2f} seconds:")
        print(f"Response type: {type(response)}")
        print("---")
        print(response)
        print("---")
        
        if response and len(str(response)) > 10:
            print("LangChain integration test successful!")
            return True
        else:
            print("LangChain test failed: Insufficient response")
            return False
            
    except ImportError:
        print("LangChain not installed. Run: pip install langchain-community")
        return False
    except Exception as e:
        print(f"Error in LangChain integration test: {e}")
        traceback.print_exc()
        return False

def main():
    """Main function to set up the RAGAS environment."""
    print("=== RAGAS Setup for Ollama ===")
    
    # Check if Ollama is installed
    if not check_ollama_installed():
        print("Error: Ollama is not installed or not running.")
        print("Please follow the installation instructions at: https://ollama.ai/download")
        sys.exit(1)
    
    # Check if qwen3:0.6b is pulled
    print("\n=== Checking for qwen3:0.6b base model ===")
    output = run_command("ollama list")
    if "qwen3:0.6b" not in output:
        print("Base model qwen3:0.6b not found. Pulling now...")
        run_command("ollama pull qwen3:0.6b")
    else:
        print("Base model qwen3:0.6b is already available.")
    
    # Build the RAGAS model
    if not build_ragas_model():
        print("Failed to build RAGAS model.")
        sys.exit(1)
    
    # Test the model
    if not test_ragas_model():
        print("Model built but test failed.")
        sys.exit(1)
    
    # Test LangChain integration
    test_langchain_integration()
    
    print("\n=== Setup Complete ===")
    print("You can now use the qwen3-ragas model for RAGAS evaluations!")
    print("The model is ready to be used in your FastAPI application.")

if __name__ == "__main__":
    main() 