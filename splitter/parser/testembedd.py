import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions

# Specify the path where the Chroma vectorstore is stored
DB_PATH = "/home/cm36/Updated-LLM-Project/vectorstores/KG/chunk_size_mid"

# Initialize Chroma client
client = chromadb.PersistentClient(path=DB_PATH)

# Specify the collection name
collection_name = "kg2"

# Function to retrieve embeddings and document chunks from Chroma
def retrieve_embeddings_and_chunks_from_chroma():
    try:
        # Access the collection
        collection = client.get_collection(name=collection_name)
        print(f"Collection '{collection_name}' accessed successfully in {DB_PATH}.")

        # Peek into the collection to retrieve stored embeddings, document chunks, and metadata
        results = collection.peek(limit=50)  # Modify limit as needed to retrieve more entries

        # Check the retrieved results and print document chunks with embeddings
        if results and 'embeddings' in results and 'documents' in results and 'metadatas' in results:
            embeddings = results['embeddings']
            documents = results['documents']  # Retrieved document chunks
            metadata = results['metadatas']  # Metadata associated with each document

            print(f"Retrieved {len(embeddings)} embeddings and document chunks.")
            for i, (embedding, document, meta) in enumerate(zip(embeddings, documents, metadata)):
                print(f"\n--- Document {i+1} ---")
                print("Embedding:", embedding[:5], "...")  # Print a snippet of the embedding
                print("Document chunk:", document[:200], "...")  # Print the first 200 characters of the chunk
                print("Metadata:", meta)  # Print metadata, which may include hierarchical info

            return embeddings, documents, metadata
        else:
            print(f"No embeddings or documents found in the collection '{collection_name}'")
            return None, None, None

    except Exception as e:
        print(f"Error accessing collection '{collection_name}': {e}")
        return None, None, None

# Run the function to retrieve embeddings and document chunks
embeddings, documents, metadata = retrieve_embeddings_and_chunks_from_chroma()

if embeddings is not None and len(embeddings) > 0 and documents is not None and len(documents) > 0:
    print("\nSample of retrieved data:")
    print("Embedding:", embeddings[0][:5])  # Show a sample embedding snippet
    print("Document chunk:", documents[0][:200])  # Show a sample document chunk snippet
    print("Metadata:", metadata[0])  # Show the first metadata entry
