import chromadb 
from chromadb.config import Settings

# Specify the path where the Chroma vectorstore is stored
DB_PATH = "/home/cm36/Updated-LLM-Project/vectorstores/KG/chunk_size_mid"

# Initialize Chroma client using the persistent client
client = chromadb.PersistentClient(path=DB_PATH)

# Specify the collection name
collection_name = "kg2"

def retrieve_documents_by_hash(user_hash, limit=20000):
    """
    Searches the specified collection for documents whose metadata contains the given hash.
    Returns a list of dictionaries, each containing the embedding, metadata, and document chunk.
    
    Args:
        user_hash (str): The hash value to search for.
        limit (int): Number of documents to inspect.
    
    Returns:
        list: A list of dicts with keys 'embedding', 'metadata', and 'document' for the matching documents.
    """
    try:
        # Access the collection
        collection = client.get_collection(name=collection_name)
        print(f"Collection '{collection_name}' accessed successfully in {DB_PATH}.")
        
        # Peek into the collection to retrieve embeddings, documents, and metadatas
        results = collection.peek(limit=limit)
        if not results or 'embeddings' not in results or 'metadatas' not in results or 'documents' not in results:
            print(f"No embeddings, metadatas, or documents found in the collection '{collection_name}'.")
            return []
        
        embeddings = results['embeddings']
        metadatas = results['metadatas']
        documents = results['documents']
        
        # Define metadata keys where the hash might appear.
        hash_keys = ["hash", "hash_document", "hash_chapter", "hash_section", "hash_subsection"]
        user_hash = user_hash.strip().lower()
        matching_results = []
        
        # Iterate over the documents' metadata, embeddings, and document chunks.
        for embed, meta, doc in zip(embeddings, metadatas, documents):
            for key in hash_keys:
                if key in meta and meta.get(key):
                    if meta.get(key).strip().lower() == user_hash:
                        matching_results.append({
                            "embedding": embed,
                            "metadata": meta,
                            "document": doc
                        })
                        break  # stop after first matching key for this document
        
        return matching_results
    
    except Exception as e:
        print(f"Error accessing collection '{collection_name}': {e}")
        return []

if __name__ == "__main__":
    while True:
        user_hash = input("Enter the hash to search for: ")
        matching_docs = retrieve_documents_by_hash(user_hash, limit=1000)
        count = len(matching_docs)
        
        if count == 0:
            print(f"No documents found for hash '{user_hash}'.")
        else:
            print(f"Found {count} documents for hash '{user_hash}'.")
            try:
                num_to_display = int(input("Enter the number of documents to display: "))
            except ValueError:
                print("Invalid number entered. Skipping display.")
                num_to_display = 0
            
            for i, result in enumerate(matching_docs[:num_to_display]):
                print(f"\n--- Document {i+1} ---")
                # Display a preview of the embedding (first 5 values)
                print("Embedding:", result["embedding"][:5], "...")
                # Display the full metadata
                print("Metadata:", result["metadata"])
                # Display a preview of the document chunk (first 200 characters)
                print("Document chunk:", result["document"][:200], "...")
        
        search_again = input("\nDo you want to search again? (y/n): ").strip().lower()
        if search_again != "y":
            print("Exiting search.")
            break
