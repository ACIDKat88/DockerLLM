from chromadb.utils import embedding_functions
from sentence_transformers import SentenceTransformer
import torch
import os

class customembedding:
    def __init__(self, model_name):
        # Check if CUDA is available, otherwise fallback to CPU
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        print(f"Using device: {self.device} for embeddings")
        
        # Try to load from local path first
        model_dir = os.path.join("/app/models", os.path.basename(model_name))
        if os.path.exists(model_dir):
            print(f"Loading model from local path: {model_dir}")
            try:
                self.model = SentenceTransformer(model_dir, device=self.device)
                print("Successfully loaded model from local path")
                return
            except Exception as e:
                print(f"Error loading model from local path: {e}")
                print("Will try downloading from Hugging Face")
        
        # If local path doesn't exist or loading failed, try direct model loading with fallback settings
        try:
            print(f"Downloading model from Hugging Face: {model_name}")
            # Try with specific configuration to avoid model_type error
            self.model = SentenceTransformer(model_name, device=self.device)
        except ValueError as e:
            if "Unrecognized model" in str(e):
                print(f"Known issue with model {model_name}, trying fallback approach")
                try:
                    # Use a more compatible model as fallback
                    print("Using all-MiniLM-L6-v2 as fallback model")
                    self.model = SentenceTransformer("all-MiniLM-L6-v2", device=self.device)
                except Exception as fallback_error:
                    print(f"Fallback model loading failed: {fallback_error}")
                    raise
            else:
                raise

    def __call__(self, input: str) -> list:
        """
        Embeds a single input string.
        """
        embedding = self.model.encode(input, device=self.device)
        return embedding.tolist()
    
    def embed_query(self, query: str) -> list:
        """
        Embeds the given query string into a vector.
        """
        if not isinstance(query, str):
            raise ValueError("Query must be a string.")
        return self.__call__(query)
    
    def embed_documents(self, documents: list) -> list:
        """
        Embeds a list of documents into vectors.

        Args:
        - documents (list): A list of strings representing the documents.

        Returns:
        - list: A list of embedding vectors corresponding to the documents.
        """
        if not isinstance(documents, list):
            raise ValueError("Documents must be a list of strings.")
        if not all(isinstance(doc, str) for doc in documents):
            raise ValueError("All documents must be strings.")
        return self.model.encode(documents, device=self.device).tolist()

