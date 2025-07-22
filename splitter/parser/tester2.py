import chromadb
from chromadb.config import Settings

# Specify the path where the Chroma vectorstore is stored
DB_PATH = "/home/cm36/Updated-LLM-Project/vectorstores/KG/chunk_size_mid"

# Initialize Chroma client using the persistent client
client = chromadb.PersistentClient(path=DB_PATH)

# Specify the collection name
collection_name = "kg2"

def retrieve_documents_by_hashes(target_hashes, limit=1):
    """
    Searches the specified collection for documents whose metadata contains any of the target hashes.

    Args:
        target_hashes (list[str]): List of hash values to search for.
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
            metadatas = results['metadatas']

            # Normalize target hashes into a set for fast lookup.
            target_hashes_set = set(h.strip().lower() for h in target_hashes)
            found_any = False

            # Define the hash keys to check in each document's metadata.
            hash_keys = ["hash", "hash_document", "hash_chapter", "hash_section", "hash_subsection"]

            for i, (embed, doc, meta) in enumerate(zip(embeddings, documents, metadatas)):
                # Collect all hash values from metadata and normalize them.
                meta_hashes = [meta.get(key, "").strip().lower() for key in hash_keys if meta.get(key)]
                matching = target_hashes_set.intersection(meta_hashes)
                if matching:
                    print(f"\n--- Document {i+1} matching hashes {matching} ---")
                    print("Embedding:", embed[:5], "...")
                    print("Document chunk:", doc[:200], "...")
                    print("Metadata:", meta)
                    found_any = True

            if not found_any:
                print("No document found with any of the target hashes.")
        else:
            print(f"No embeddings or documents found in the collection '{collection_name}'.")
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

# Search the collection for documents matching any of the target hashes.
retrieve_documents_by_hashes(target_hashes, limit=1)
