from chromadb.utils import embedding_functions
from sentence_transformers import SentenceTransformer

class customembedding:
    def __init__(self, model_name):
        self.model = SentenceTransformer(model_name, device='cuda')  # Use GPU

    def __call__(self, input: str) -> list:
        """
        Embeds a single input string.
        """
        embedding = self.model.encode(input, device='cuda')  # Explicit GPU usage
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
        return self.model.encode(documents, device='cuda').tolist()

