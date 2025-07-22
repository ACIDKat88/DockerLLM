import os
import chromadb
from chromadb.config import Settings
from embedd_class import customembedding

# Initialize the custom embedding function using the Ollama model
mistral_embedding_ef = customembedding("mixedbread-ai/mxbai-embed-large-v1")

# Specify the unified database path
BASE_PATH = "/home/cm36/Updated-LLM-Project"
J1_DB_PATH = os.path.join(BASE_PATH, "vectorstores", "KG")

# Define the single chunk size
chunk_size = 'mid'  # Change this to your desired chunk size

# Ensure the main directory for the J1 database path exists
print(f"Processing main database path: J1 (Path: {J1_DB_PATH})")
if not os.path.exists(J1_DB_PATH):
    print(f"Main database path does not exist. Creating it: {J1_DB_PATH}")
    os.makedirs(J1_DB_PATH, exist_ok=True)

# Define the path for the single chunk size
sub_dir_path = os.path.join(J1_DB_PATH, f'chunk_size_{chunk_size}')
if not os.path.exists(sub_dir_path):
    print(f"Creating database directory for chunk size {chunk_size}: {sub_dir_path}")
    os.makedirs(sub_dir_path, exist_ok=True)

print(f"Processing database for chunk size {chunk_size}: {sub_dir_path}")

# Initialize the Chroma client with the single database path
try:
    client = chromadb.PersistentClient(path=sub_dir_path)
except Exception as e:
    print(f"ERROR: Failed to initialize Chroma client for {sub_dir_path}: {e}")
    exit()

# Define the collection name
collection_name = "kg2"

# Check if the collection exists, and create it if it doesn't
try:
    try:
        collection = client.get_collection(name=collection_name, embedding_function=mistral_embedding_ef)
        print(f"Collection '{collection_name}' accessed successfully in {sub_dir_path}.")
    except Exception as e:
        print(f"Collection '{collection_name}' does not exist in {sub_dir_path}. Creating a new collection.")
        collection = client.create_collection(
            name=collection_name,
            embedding_function=mistral_embedding_ef,
            metadata={"hnsw:space": "cosine"}
        )
        print(f"Collection '{collection_name}' created successfully in {sub_dir_path}.")
except Exception as e:
    print(f"ERROR: Failed to create or access collection in {sub_dir_path}: {e}")
    exit()

# Check if the collection has been created and is accessible
try:
    documents = collection.peek()
    if documents and len(documents) > 0:
        print(f"Collection '{collection_name}' in {sub_dir_path} contains {len(documents)} documents.")
    else:
        print(f"Collection '{collection_name}' in {sub_dir_path} has been created but contains no documents.")
except Exception as error_collectview:
    print(f"Error peeking into collection in {sub_dir_path}: {error_collectview}")
    exit()

# Final confirmation message
print(f"Confirmed collection '{collection_name}' in path: {sub_dir_path}")
