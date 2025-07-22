import chromadb
from chromadb.config import Settings

# Specify the path where the Chroma vectorstore is stored
DB_PATH = "/home/cm36/Updated-LLM-Project/vectorstores/KG/chunk_size_mid"

# Initialize Chroma client using the persistent client
client = chromadb.PersistentClient(path=DB_PATH)

# Specify the collection name
collection_name = "kg2"

def retrieve_document_by_hash(target_hash, limit=50):
    """
    Searches the specified collection for documents whose metadata contains the target hash.
    
    Args:
        target_hash (str): The hash value to search for.
        limit (int): Number of documents to peek into (default 50).
    """
    try:
        # Access the collection
        collection = client.get_collection(name=collection_name)
        print(f"Collection '{collection_name}' accessed successfully in {DB_PATH}.")
        
        # Peek into the collection to retrieve stored embeddings, document chunks, and metadata
        results = collection.peek(limit=limit)
        
        if results and 'embeddings' in results and 'documents' in results and 'metadatas' in results:
            embeddings = results['embeddings']
            documents = results['documents']
            metadata = results['metadatas']
            
            # Normalize the target hash.
            target_hash_norm = target_hash.strip().lower()
            found = False
            
            # Define the hash keys you want to check.
            hash_keys = ["hash", "hash_document", "hash_chapter", "hash_section", "hash_subsection"]
            
            for i, (embed, doc, meta) in enumerate(zip(embeddings, documents, metadata)):
                # Gather all hash values from metadata and normalize them.
                meta_hashes = [meta.get(key, "").strip().lower() for key in hash_keys if meta.get(key)]
                if target_hash_norm in meta_hashes:
                    print(f"\n--- Document {i+1} matching hash {target_hash} ---")
                    print("Embedding:", embed[:5], "...")
                    print("Document chunk:", doc[:200], "...")
                    print("Metadata:", meta)
                    found = True
            if not found:
                print(f"No document found with hash {target_hash}")
        else:
            print(f"No embeddings or documents found in the collection '{collection_name}'")
    except Exception as e:
        print(f"Error accessing collection '{collection_name}': {e}")

# Example usage: search for a specific hash.
target_hash = "1ef2222ae4a88763ee3bc7f1407568f8"
retrieve_document_by_hash(target_hash)
