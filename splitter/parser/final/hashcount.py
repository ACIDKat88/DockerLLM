import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions

# Specify the path where the Chroma vectorstore is stored
DB_PATH = "/home/cm36/Updated-LLM-Project/vectorstores/KG/chunk_size_mid"

# Initialize Chroma client
client = chromadb.PersistentClient(path=DB_PATH)

# Specify the collection name
collection_name = "kg2"

def count_hash_ids(metadata_list):
    """
    Count total occurrences of hash ids at each level in the metadata list.
    Returns a dictionary with counts for:
      - hash_document
      - hash_chapter
      - hash_section
      - hash_subsection
    """
    counts = {"hash_document": 0, "hash_chapter": 0, "hash_section": 0, "hash_subsection": 0}
    for meta in metadata_list:
        if meta.get("hash_document"):
            counts["hash_document"] += 1
        if meta.get("hash_chapter"):
            counts["hash_chapter"] += 1
        if meta.get("hash_section"):
            counts["hash_section"] += 1
        if meta.get("hash_subsection"):
            counts["hash_subsection"] += 1
    return counts

def count_unique_hash_ids(metadata_list):
    """
    Count unique hash ids at each level.
    Returns a dictionary with the number of unique values for:
      - hash_document
      - hash_chapter
      - hash_section
      - hash_subsection
    """
    unique = {"hash_document": set(), "hash_chapter": set(), "hash_section": set(), "hash_subsection": set()}
    for meta in metadata_list:
        if meta.get("hash_document"):
            unique["hash_document"].add(meta["hash_document"])
        if meta.get("hash_chapter"):
            unique["hash_chapter"].add(meta["hash_chapter"])
        if meta.get("hash_section"):
            unique["hash_section"].add(meta["hash_section"])
        if meta.get("hash_subsection"):
            unique["hash_subsection"].add(meta["hash_subsection"])
    # Convert sets to counts
    return {k: len(v) for k, v in unique.items()}

def retrieve_embeddings_and_chunks_from_chroma():
    try:
        # Access the collection
        collection = client.get_collection(name=collection_name)
        print(f"Collection '{collection_name}' accessed successfully in {DB_PATH}.")

        # Retrieve all entries by using a very high limit.
        results = collection.peek(limit=1000000)  # Retrieves the entire database
        
        if results and 'embeddings' in results and 'documents' in results and 'metadatas' in results:
            embeddings = results['embeddings']
            documents = results['documents']
            metadata = results['metadatas']

            total = len(embeddings)
            print(f"Retrieved {total} embeddings and document chunks.")

            # Print details for only the first 50 documents.
            for i, (embedding, document, meta) in enumerate(zip(embeddings, documents, metadata)):
                if i >= 50:
                    break
                print(f"\n--- Document {i+1} ---")
                print("Embedding:", embedding[:5], "...")  # Print a snippet of the embedding
                print("Document chunk:", document[:200], "...")  # First 200 characters of the chunk
                print("Metadata:", meta)

            return embeddings, documents, metadata
        else:
            print(f"No embeddings or documents found in the collection '{collection_name}'.")
            return None, None, None

    except Exception as e:
        print(f"Error accessing collection '{collection_name}': {e}")
        return None, None, None

# Run the function to retrieve embeddings and document chunks.
embeddings, documents, metadata = retrieve_embeddings_and_chunks_from_chroma()

if embeddings is not None and len(embeddings) > 0 and documents is not None and len(documents) > 0:
    print("\nSample of retrieved data:")
    print("Embedding:", embeddings[0][:5])
    print("Document chunk:", documents[0][:200])
    print("Metadata:", metadata[0])

    # Count the hash IDs over the entire database.
    hash_counts = count_hash_ids(metadata)
    unique_hash_counts = count_unique_hash_ids(metadata)

    print("\nHash ID counts (only showing types with > 1 occurrence):")
    for key, count in hash_counts.items():
        if count > 1:
            print(f"{key}: {count} (unique: {unique_hash_counts[key]})")

    # Explicitly print the number of unique sections and unique subsections.
    print("\nUnique sections (hash_section):", unique_hash_counts.get("hash_section", 0))
    print("Unique subsections (hash_subsection):", unique_hash_counts.get("hash_subsection", 0))
