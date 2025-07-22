import chromadb 
from chromadb.config import Settings

# Specify the path where the Chroma vectorstore is stored
DB_PATH = "/home/cm36/Updated-LLM-Project/vectorstores/KG/chunk_size_mid"

# Initialize Chroma client using the persistent client
client = chromadb.PersistentClient(path=DB_PATH)

# Specify the collection name
collection_name = "kg2"

def retrieve_embeddings_for_hash(user_hash, limit=20000):
    """
    Searches the specified collection for documents whose metadata contains the given hash.
    
    Args:
        user_hash (str): The hash value to search for.
        limit (int): Number of documents to inspect.
    
    Returns:
        list: A list of embeddings associated with the hash.
    """
    try:
        # Access the collection
        collection = client.get_collection(name=collection_name)
        print(f"Collection '{collection_name}' accessed successfully in {DB_PATH}.")
        
        # Peek into the collection to retrieve embeddings and metadatas
        results = collection.peek(limit=limit)
        if not results or 'embeddings' not in results or 'metadatas' not in results:
            print(f"No embeddings or metadatas found in the collection '{collection_name}'.")
            return []
        
        embeddings = results['embeddings']
        metadatas = results['metadatas']
        
        # Define metadata keys where the hash might appear.
        hash_keys = ["hash", "hash_document", "hash_chapter", "hash_section", "hash_subsection"]
        user_hash = user_hash.strip().lower()
        matching_embeddings = []
        
        # Iterate over the documents' metadata and embeddings.
        for embed, meta in zip(embeddings, metadatas):
            for key in hash_keys:
                if key in meta and meta.get(key):
                    if meta.get(key).strip().lower() == user_hash:
                        matching_embeddings.append(embed)
                        break  # stop after first match in this document
        
        return matching_embeddings
    
    except Exception as e:
        print(f"Error accessing collection '{collection_name}': {e}")
        return []

if __name__ == "__main__":
    # Prompt the user for the hash value.
    user_hash = input("Enter the hash to search for: ")
    matching_embeddings = retrieve_embeddings_for_hash(user_hash, limit=20000)
    count = len(matching_embeddings)
    
    if count == 0:
        print(f"No embeddings found for hash '{user_hash}'.")
    else:
        print(f"Found {count} embeddings for hash '{user_hash}'.")
        try:
            num_to_display = int(input("Enter the number of embeddings to display: "))
        except ValueError:
            print("Invalid number entered. Exiting.")
            exit(1)
        
        # Display a preview of the requested number of embeddings.
        print(f"Displaying {min(num_to_display, count)} embeddings:")
        for i, embed in enumerate(matching_embeddings[:num_to_display]):
            # Here we print the first few elements of each embedding as a preview.
            print(f"Embedding {i+1}: {embed[:5]} ...")
