# llm_evaluator/pipelines/base.py

from abc import ABC, abstractmethod

class BaseRAGPipeline(ABC):
    """
    Abstract Base Class for RAG pipelines.
    """

    @abstractmethod
    def retrieve_context(self, query: str) -> dict:
        """
        Retrieve relevant context (such as documents) for a given query.
        
        :param query: The query or question.
        :return: Dictionary with context data.
        """
        pass
