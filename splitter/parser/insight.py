import chromadb
from chromadb.config import Settings

# Specify the path where the Chroma vectorstore is stored
DB_PATH = "/home/cm36/Updated-LLM-Project/vectorstores/KG/chunk_size_mid"

# Initialize Chroma client using the persistent client
client = chromadb.PersistentClient(path=DB_PATH)

# Specify the collection name
collection_name = "kg2"

def count_unique_hash_types(limit=20000):
    """
    Retrieves metadata from the specified collection and counts the number of unique (deduplicated)
    hash values for each hash key. The keys considered are:
      - "hash"
      - "hash_document"
      - "hash_chapter"
      - "hash_section"
      - "hash_subsection"
    
    Args:
        limit (int): Number of documents to inspect from the collection.

    Returns:
        dict: Mapping of each hash key to the count of unique hash values.
    """
    try:
        collection = client.get_collection(name=collection_name)
        print(f"Collection '{collection_name}' accessed successfully in {DB_PATH}.")

        results = collection.peek(limit=limit)
        if results and 'metadatas' in results:
            metadatas = results['metadatas']

            # Define the hash keys to check.
            hash_keys = ["hash", "hash_document", "hash_chapter", "hash_section", "hash_subsection"]

            # Initialize a set for each hash type to collect unique hash values.
            unique_hashes = {key: set() for key in hash_keys}

            # Iterate over each document's metadata.
            for meta in metadatas:
                for key in hash_keys:
                    if key in meta and meta.get(key):
                        # Normalize the hash value by stripping whitespace and converting to lowercase.
                        normalized_hash = meta.get(key).strip().lower()
                        unique_hashes[key].add(normalized_hash)

            # Prepare counts for each hash type.
            counts = {key: len(unique_hashes[key]) for key in hash_keys}

            # Print the count for each hash type.
            for key, count in counts.items():
                print(f"{key}: {count} unique hash values.")
            return counts
        else:
            print(f"No metadatas found in the collection '{collection_name}'.")
    except Exception as e:
        print(f"Error accessing collection '{collection_name}': {e}")

if __name__ == "__main__":
    unique_counts = count_unique_hash_types(limit=20000)
