import os
import json
import hashlib
import chromadb
from chromadb.config import Settings
from embedd_class import customembedding

# Configuration (as in your chromadb creation script)
BASE_PATH = "/home/cm36/Updated-LLM-Project"
J1_DB_PATH = os.path.join(BASE_PATH, "vectorstores", "KG")
chunk_size = 'low'  # Use your desired chunk size
sub_dir_path = os.path.join(J1_DB_PATH, f'chunk_size_{chunk_size}')
collection_name = "kg2"

# Initialize the custom embedding function.
mistral_embedding_ef = customembedding("mixedbread-ai/mxbai-embed-large-v1")

# Initialize the persistent ChromaDB client.
try:
    client = chromadb.PersistentClient(path=sub_dir_path)
except Exception as e:
    print(f"ERROR: Failed to initialize Chroma client for {sub_dir_path}: {e}")
    exit()

# Get or create the collection (using your standard setup).
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


class ChromaDBManager:
    def __init__(self, collection):
        self.collection = collection

    def document_exists(self, doc_hash: str) -> bool:
        """
        Check if a document with the given hash already exists in the collection.
        This queries the collection directly.
        """
        try:
            result = self.collection.get(ids=[doc_hash])
            if result and "ids" in result and doc_hash in result["ids"]:
                return True
        except Exception as e:
            print(f"Error checking existence for {doc_hash}: {e}")
        return False

    def add_document(self, doc_hash: str, document: dict):
        """
        Add the document (serialized as JSON) to the collection if its hash does not already exist.
        """
        if not self.document_exists(doc_hash):
            self.collection.add(
                ids=[doc_hash],
                documents=[json.dumps(document)],
                metadatas=[{"hash": doc_hash, "title": document.get("title", "")}]
            )
            print(f"Document {doc_hash} added to the collection.")
        else:
            print(f"Document {doc_hash} already exists in the collection.")


# For standalone testing:
if __name__ == "__main__":
    # Example document for testing.
    sample_document = {
        "title": "Test Document",
        "content": "This is some sample content.",
    }
    sample_document["hash"] = hashlib.md5((sample_document["title"] + sample_document["content"]).encode("utf-8")).hexdigest()
    manager = ChromaDBManager(collection)
    manager.add_document(sample_document["hash"], sample_document)
