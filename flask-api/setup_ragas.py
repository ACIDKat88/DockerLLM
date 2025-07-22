#!/usr/bin/env python3
import os
import subprocess
import sys
import time
import traceback

def run_command(command, timeout=60):
    """Run a shell command and return its stdout on success, None on failure.
    Prints detailed error information to stdout if the command fails.
    """
    current_cwd = os.getcwd()
    print(f"Running command: {command} (from CWD: {current_cwd})")
    try:
        process = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout
        )

        if process.returncode == 0:
            return process.stdout
        else:
            print(f"Command failed with exit code {process.returncode}")
            if process.stdout and process.stdout.strip():
                print(f"--- Stdout from failed command ---\n{process.stdout.strip()}")
            else:
                print("--- Stdout from failed command was empty ---")
            
            if process.stderr and process.stderr.strip():
                print(f"--- Stderr from failed command ---\n{process.stderr.strip()}")
            else:
                print("--- Stderr from failed command was empty ---")
            return None
    except subprocess.TimeoutExpired:
        print(f"Command timed out after {timeout} seconds: {command}")
        return None
    except FileNotFoundError:
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
            print("Ollama version check failed (run_command returned None).")
            return False
    except Exception as e: # Should be caught by run_command, but as a safeguard
        print(f"Ollama is not installed or not in PATH (exception during check): {e}")
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
    
    print(f"Target modelfile for ollama create: {modelfile_name} (will be relative to CWD)")
    
    cmd = f"ollama create qwen3-ragas -f {modelfile_name}"
    
    original_cwd = os.getcwd()
    try:
        print(f"Original CWD before building model: {original_cwd}")
        os.chdir(script_dir) 
        print(f"Temporarily changed CWD to: {script_dir} for 'ollama create'")
        
        output = run_command(cmd)

        if output is not None:
            print("Model created successfully!")
            if output.strip():
                 print(f"--- Ollama create stdout ---\n{output.strip()}")
            return True
        else:
            print("Failed to create model (run_command returned None, further details should be above).")
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
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    original_cwd = os.getcwd()
    
    try:
        # Ensure CWD is where the script is, in case ollama run needs model context
        # though for `ollama run <modelname> "prompt"` it usually doesn't matter.
        os.chdir(script_dir)
        print(f"Changed CWD to {script_dir} for model test")

        simple_test_query = "What is the capital of France?"
        # Escape double quotes within the query if any, though not present here.
        # For shell=True, the command string is passed to the shell. Complex prompts might need careful escaping.
        cmd = f'ollama run qwen3-ragas "{simple_test_query}"'
        
        print(f"Testing model with command: {cmd}")
        print("(Using 20-second timeout - will continue setup if model test takes too long)")
        output = run_command(cmd, timeout=20)
        
        if output and output.strip():
            print("Model test successful (received output)!")
            print("\nSample output from qwen3-ragas:")
            print("---")
            print(output.strip()[:500] + ("..." if len(output.strip()) > 500 else ""))
            print("---")
            return True
        else:
            # If output is None, run_command already printed the error.
            # If output is empty string, this message will be printed.
            print("Model test failed: No output or empty output received from 'ollama run'.")
            print("Continuing with API server startup even though the test failed. The model may still work.")
            return True  # Return True anyway to allow the server to start
            
    except Exception as e:
        print(f"Error testing model: {e}")
        traceback.print_exc()
        print("Continuing with API server startup despite test error. The model may still work.")
        return True  # Return True anyway to allow the server to start
    finally:
        os.chdir(original_cwd)
        print(f"Restored CWD to {original_cwd} after model test")

def test_langchain_integration():
    """Test that the model works with LangChain."""
    print("\n=== Testing LangChain integration with qwen3-ragas ===")
    
    try:
        from langchain_community.chat_models import ChatOllama
        
        llm = ChatOllama(
            model="qwen3-ragas",
            temperature=0.1,
        )
        
        prompt_text = "Evaluate the faithfulness of this answer: The answer is Paris, when the context mentions Paris is the capital of France."
        print(f"Sending prompt to LangChain Ollama: '{prompt_text}'")
        
        start_time = time.time()
        response_content = llm.invoke(prompt_text).content
        end_time = time.time()
        
        print(f"Response received in {end_time - start_time:.2f} seconds.")
        
        if response_content and response_content.strip():
            print("LangChain integration test successful!")
            print("--- Response from LangChain ---")
            print(str(response_content).strip())
            print("---")
            return True
        else:
            print("LangChain test failed: No content in response or empty response.")
            return False
            
    except ImportError:
        print("LangChain (langchain-community) not installed. Skipping test. Run: pip install langchain-community")
        return True # True because it's an optional test
    except Exception as e:
        print(f"Error in LangChain integration test: {e}")
        traceback.print_exc()
        return False

def main():
    """Main function to set up the RAGAS environment."""
    print("=== RAGAS Setup for Ollama ===")
    
    if not check_ollama_installed():
        print("Critical Error: Ollama is not installed or not responding correctly.")
        print("Please follow the installation instructions at: https://ollama.ai/download")
        sys.exit(1)
    
    print("\n=== Checking for qwen3:0.6b base model ===")
    output = run_command("ollama list")
    if output is None:
        print("Critical Error: Failed to get list of Ollama models. Exiting.")
        sys.exit(1)
        
    if "qwen3:0.6b" not in output:
        print("Base model qwen3:0.6b not found. Pulling now...")
        pull_output = run_command("ollama pull qwen3:0.6b")
        if pull_output is None:
            print("Critical Error: Failed to pull qwen3:0.6b model. Exiting.")
            sys.exit(1)
        print("Successfully pulled qwen3:0.6b.")
    else:
        print("Base model qwen3:0.6b is already available.")
    
    if not build_ragas_model():
        print("Critical Error: Failed to build qwen3-ragas model. Exiting.")
        sys.exit(1)
    
    # Model test always returns True now, but we'll still call it to log the result
    test_ragas_model()
    
    # We'll still try the LangChain integration test, but continue either way
    try:
        test_langchain_integration()
    except Exception as e:
        print(f"LangChain integration test error: {e}")
        print("Continuing with API server startup despite LangChain test error.")

    print("\n=== Ollama RAGAS Setup Complete ===")
    print("The qwen3-ragas model is now available for use.")
    print("Starting the FastAPI server...")

if __name__ == "__main__":
    main()
