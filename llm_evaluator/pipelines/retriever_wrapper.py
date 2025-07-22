# llm_evaluator/pipelines/retriever_wrapper.py

from .base import BaseRAGPipeline

class RetrieverWrapper(BaseRAGPipeline):
    """
    A wrapper to interface with a retriever inside a RAG pipeline.
    """

    def __init__(self, retriever):
        """
        Initialize the retriever wrapper.

        :param retriever: A retriever instance with a 'retrieve' method.
        """
        self.retriever = retriever

    def retrieve_context(self, query: str) -> dict:
        """
        Retrieve relevant documents for the given query.
        
        :param query: The query to search for context.
        :return: Dictionary with key "documents" mapping to a list of document texts.
        """
        documents = self.retriever.retrieve(query)
        return {"documents": documents}
