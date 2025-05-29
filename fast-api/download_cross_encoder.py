from sentence_transformers.cross_encoder import CrossEncoder
import os
import shutil
import tempfile
from huggingface_hub import snapshot_download

# Print current directory for debugging
print(f"Current working directory: {os.getcwd()}")

# Define the model name and path
model_name = "cross-encoder/ms-marco-MiniLM-L-6-v2"
alternative_model = "cross-encoder/ms-marco-TinyBERT-L-6"
model_dir = "models/cross-encoder"

# Create models directory if it doesn't exist
os.makedirs("models", exist_ok=True)
os.makedirs(model_dir, exist_ok=True)

# Check if model already exists
if os.path.exists(os.path.join(model_dir, "config.json")):
    print(f"Model already exists at {model_dir}. Checking if it's valid...")
    try:
        # Try to load the model to verify it's valid
        test_model = CrossEncoder(model_dir)
        print("Existing model is valid. Skipping download.")
        exit(0)
    except Exception as e:
        print(f"Existing model is invalid: {str(e)}")
        print("Removing existing model directory and downloading again...")
        # Just clean the directory but don't remove it
        for item in os.listdir(model_dir):
            item_path = os.path.join(model_dir, item)
            if os.path.isfile(item_path):
                os.unlink(item_path)
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)

# Try to download the primary model
try:
    print(f"Downloading model {model_name}...")
    
    # Use huggingface_hub to download files directly
    with tempfile.TemporaryDirectory() as tmpdir:
        print(f"Downloading model files to temporary directory: {tmpdir}")
        snapshot_download(repo_id=model_name, local_dir=tmpdir)
        
        # Copy files from temp dir to model_dir
        print(f"Copying files from {tmpdir} to {model_dir}")
        for item in os.listdir(tmpdir):
            s = os.path.join(tmpdir, item)
            d = os.path.join(model_dir, item)
            if os.path.isfile(s):
                shutil.copy2(s, d)
            else:
                shutil.copytree(s, d)
                
    # Verify the model by loading it
    print(f"Verifying model at {model_dir}")
    test_model = CrossEncoder(model_dir)
    print(f"Model {model_name} successfully downloaded and verified")
    
except Exception as e:
    print(f"Error downloading primary model: {str(e)}")
    print(f"Trying alternative model {alternative_model}...")
    
    try:
        # Try the alternative model
        with tempfile.TemporaryDirectory() as tmpdir:
            print(f"Downloading alternative model files to temporary directory: {tmpdir}")
            snapshot_download(repo_id=alternative_model, local_dir=tmpdir)
            
            # Copy files from temp dir to model_dir
            print(f"Copying files from {tmpdir} to {model_dir}")
            for item in os.listdir(tmpdir):
                s = os.path.join(tmpdir, item)
                d = os.path.join(model_dir, item)
                if os.path.isfile(s):
                    shutil.copy2(s, d)
                else:
                    shutil.copytree(s, d)
                    
        # Verify the model by loading it
        print(f"Verifying alternative model at {model_dir}")
        test_model = CrossEncoder(model_dir)
        print(f"Alternative model {alternative_model} successfully downloaded and verified")
        
    except Exception as e2:
        print(f"Error downloading alternative model: {str(e2)}")
        print("Failed to download any model.")
        exit(1) 