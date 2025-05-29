from sentence_transformers import SentenceTransformer
import os
import torch
import shutil

# Print current directory for debugging
print(f"Current working directory: {os.getcwd()}")

# Define the model name and path
model_name = "mixedbread-ai/mxbai-embed-large-v1"
model_dir = "models/mxbai-embed-large-v1"

# Create models directory if it doesn't exist
os.makedirs("models", exist_ok=True)

# Check if model already exists
if os.path.exists(model_dir):
    print(f"Model already exists at {model_dir}. Checking if it's valid...")
    try:
        # Try to load the model to verify it's valid
        test_model = SentenceTransformer(model_dir)
        print("Existing model is valid. Skipping download.")
        exit(0)
    except Exception as e:
        print(f"Existing model is invalid: {str(e)}")
        print("Removing existing model directory and downloading again...")
        shutil.rmtree(model_dir)
        os.makedirs("models", exist_ok=True)

# Check if CUDA is available
device = 'cuda' if torch.cuda.is_available() else 'cpu'
print(f"Using device: {device} for model download")

# Download the model
print(f"Downloading model {model_name}...")
model = SentenceTransformer(model_name, device=device)

# Save the model locally
print(f"Saving model to {model_dir}...")
model.save(model_dir)

# Verify the model was saved correctly
if os.path.exists(model_dir):
    print(f"Model successfully saved to {model_dir}")
    
    # List files in the model directory to confirm
    files = os.listdir(model_dir)
    print(f"Files in model directory: {files}")
else:
    print(f"Error: Model directory {model_dir} not found after save operation") 