import chromadb 
from chromadb.config import Settings

# Specify the path where the Chroma vectorstore is stored
DB_PATH = "/home/cm36/Updated-LLM-Project/vectorstores/KG/chunk_size_mid"

# Initialize Chroma client using the persistent client
client = chromadb.PersistentClient(path=DB_PATH)

# Specify the collection name
collection_name = "kg2"

def retrieve_embeddings_by_hashes(target_hashes, limit=20000):
    """
    Searches the specified collection for documents whose metadata contains any of the target hashes,
    and returns a dictionary mapping each target hash to a list of its embeddings.
    
    For each hash, if at least 5 embeddings are found, the function prints a preview (first 5) of those embeddings.
    If fewer than 5 are found, it prints a warning.

    Args:
        target_hashes (list[str]): List of hash values to search for.
        limit (int): Number of documents to inspect.
    
    Returns:
        dict: Mapping of each target hash (lowercase) to a list of embeddings.
    """
    try:
        # Access the collection
        collection = client.get_collection(name=collection_name)
        print(f"Collection '{collection_name}' accessed successfully in {DB_PATH}.")

        # Peek into the collection to retrieve embeddings and metadata
        results = collection.peek(limit=limit)

        if results and 'embeddings' in results and 'metadatas' in results:
            embeddings = results['embeddings']
            metadatas = results['metadatas']

            # Prepare a dictionary to accumulate embeddings for each target hash.
            # Normalize the target hashes for case-insensitive matching.
            hash_embeddings = {h.strip().lower(): [] for h in target_hashes}

            # Define the metadata keys to check.
            hash_keys = ["hash", "hash_document", "hash_chapter", "hash_section", "hash_subsection"]

            # Iterate over each document's metadata and embedding.
            for embed, meta in zip(embeddings, metadatas):
                for key in hash_keys:
                    if key in meta and meta.get(key):
                        hash_val = meta.get(key).strip().lower()
                        if hash_val in hash_embeddings:
                            hash_embeddings[hash_val].append(embed)

            # Check each hash for at least 5 embeddings.
            for hash_val, embeds in hash_embeddings.items():
                count = len(embeds)
                if count < 5:
                    print(f"Warning: Only found {count} embeddings for hash {hash_val}.")
                else:
                    print(f"Hash {hash_val} has {count} embeddings. Previewing the first 5 embeddings:")
                    for i, e in enumerate(embeds[:5]):
                        # Print a truncated version of each embedding for brevity.
                        print(f"  Embedding {i+1}: {e[:5]} ...")
            return hash_embeddings
        else:
            print(f"No embeddings or metadatas found in the collection '{collection_name}'.")
    except Exception as e:
        print(f"Error accessing collection '{collection_name}': {e}")

# List of 15 target hash values.
target_hashes = [
    "1ef2222ae4a88763ee3bc7f1407568f8",
    "74e49f67b12bfc23a4b8b3c7a981076a",
    "76a084e6d1bef0ee4fc9685f94ac74f3",
    "2f16c794834af1e6797b04e13b6f16bb",
    "2170b7fd2d1e9dbf4fe1fcbe9de9e366",
    "bdc5452d803ed567aa1a87de06652ca1",
    "1d2175715d142564f5f8a30660e8d9bb",
    "9f165c527866e6f6a76d8c33ae534419",
    "4b446523991ede9b87c15cc0beb8e0dc",
    "be1df423066a900a0f5bb43a794f56d3",
    "9c4ee6ce779f27eb2be505bf50c20895",
    "4647cc3cefaa3ec8cc6e24e7dc3ae35b",
    "68f64451e8f4b3fca106832ff6424f10",
    "a41f5621361882c453fb60722534b091",
    "505781eb2e4a5d90f1db8b2d36dcb6e7"
]

# Retrieve and print embeddings by hash.
embeddings_by_hash = retrieve_embeddings_by_hashes(target_hashes, limit=20000)
