import numpy as np
from langchain.docstore.document import Document
from chromadb import PersistentClient
from chromadb.errors import InvalidCollectionException

class CustomChromaRetriever:
    def __init__(self, embedding_function, collection_name, persist_directory):
        """
        Args:
            embedding_function: An object with an embed_query method.
            collection_name (str): The name of your Chroma collection.
            persist_directory (str): Directory where the collection is stored.
        """
        self.embedding_function = embedding_function
        self.persist_directory = persist_directory
        # Initialize the persistent Chroma client using the provided directory.
        self.client = PersistentClient(path=persist_directory)
        try:
            # Get the collection by name.
            self.collection = self.client.get_collection(name=collection_name)
            print(f"[DEBUG] Collection '{collection_name}' accessed successfully at {persist_directory}.")
        except InvalidCollectionException as e:
            print(f"[ERROR] {e}")
            print("[WARNING] It appears that the collection does not exist in the given persist directory. "
                  "If you upgraded from a version below 0.5.6, consider running 'chromadb utils vacuum --help'. "
                  "Otherwise, verify that the persist directory and collection name are correct.")
            # Optionally, you can create the collection if desired:
            # self.collection = self.client.create_collection(name=collection_name)
            raise

    def get_relevant_documents(self, query: str, filter_hashes=None, k=30):
        """
        Retrieves documents using cosine similarity between the query embedding and document embeddings.
        
        Args:
            query (str): The user query.
            filter_hashes (List[str], optional): List of acceptable hash values.
            k (int): Number of top results to return.
        
        Returns:
            List[Document]: A list of Document objects for the top‑k matches.
        """
        # Normalize acceptable hashes if provided.
        if filter_hashes is not None:
            normalized_filter_hashes = [h.strip().lower() for h in filter_hashes]
        else:
            normalized_filter_hashes = None

        # Compute the query embedding.
        query_embedding = np.array(self.embedding_function.embed_query(query))
        
        # Use Chromadb's native query method.
        result = self.collection.query(query_embeddings=[query_embedding], n_results=k)
        
        docs = []
        # Define the hash keys you want to check.
        hash_keys = ["hash", "hash_document", "hash_chapter", "hash_section", "hash_subsection"]
        
        # Debug: print how many documents were returned before filtering.
        raw_docs = result["documents"][0]
        print(f"[DEBUG] Retrieved {len(raw_docs)} documents before filtering from vector store.")
        
        # Iterate over returned documents and metadata.
        for doc_text, metadata in zip(result["documents"][0], result["metadatas"][0]):
            # For debugging, print out the metadata hash values.
            doc_hashes = [metadata.get(key) for key in hash_keys if metadata.get(key)]
            normalized_doc_hashes = [h.strip().lower() for h in doc_hashes]
            print(f"[DEBUG] Document metadata hashes: {normalized_doc_hashes}")
            
            # If filtering is requested, only include if any normalized hash is in the acceptable list.
            if normalized_filter_hashes is not None:
                if not any(h in normalized_filter_hashes for h in normalized_doc_hashes):
                    continue
            docs.append(Document(page_content=doc_text, metadata=metadata))
        
        print(f"[DEBUG] Retrieved {len(docs)} documents from vector store after filtering.")
        return docs

 
