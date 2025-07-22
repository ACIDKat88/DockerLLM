# llm_evaluator/evaluators/rag_evaluator.py

from .base import BaseEvaluator
from llm_evaluator.metrics.ragas_metrics import RagasMetrics

class RAGEvaluator(BaseEvaluator):
    """
    Evaluator for Retrieval-Augmented Generation (RAG) pipelines using custom RagasMetrics.
    
    This evaluator computes per-instance metrics based on generated text and retrieved contexts.
    """
    
    def __init__(self, pipeline, metrics=None):
        """
        Initialize the RAG Evaluator.

        :param pipeline: The RAG pipeline instance (must include a retriever/context interface).
        :param metrics: Optional list of metric instances. If None, defaults to [RagasMetrics()].
        """
        self.pipeline = pipeline
        self.metrics = metrics if metrics is not None else [RagasMetrics()]

    def evaluate(self, generated_text: str, context: dict) -> dict:
        """
        Evaluate the generated text against the provided context.
        
        :param generated_text: Generated answer from the primary LLM.
        :param context: Dictionary containing additional context data (e.g., a list of documents).
        :return: Dictionary with metric names as keys and evaluation scores as values.
        """
        evaluation_results = {}
        for metric in self.metrics:
            # Each metric should have a compute() method that returns a tuple (metric_name, score)
            metric_name, score = metric.compute(generated_text, context)
            evaluation_results[metric_name] = score

        return evaluation_results


###############################################################################
# Dataset-Level Evaluator Using the RAGAS Framework (Local LLM)
###############################################################################

class RAGASDatasetEvaluator:
    """
    Evaluator for a collection of RAG system outputs using the RAGAS evaluation framework.
    
    This class uses the RAGAS library to evaluate a dataset of queries, retrieved contexts,
    LLM responses, and reference answers with standard metrics.
    """

    def __init__(self, llm, metrics=None):
        """
        Initialize the dataset evaluator.

        :param llm: The LLM instance used for evaluation. If the LLM is locally hosted,
                    it should have a `generate(prompt, **kwargs)` method.
        :param metrics: Optional list of metric objects. By default, it uses:
                        [LLMContextRecall(), Faithfulness(), FactualCorrectness()].
        """
        from ragas.metrics import LLMContextRecall, Faithfulness, FactualCorrectness

        self.llm = llm
        self.metrics = metrics if metrics is not None else [LLMContextRecall(), Faithfulness(), FactualCorrectness()]

        # If the provided llm is locally hosted (has 'generate' method), use it directly.
        # Otherwise, wrap it using the LangchainLLMWrapper.
        if hasattr(llm, "generate"):
            self.llm_wrapper = llm
        else:
            from ragas.llms import LangchainLLMWrapper
            self.llm_wrapper = LangchainLLMWrapper(llm)

    def evaluate_dataset(self, dataset: list) -> dict:
        """
        Evaluate the RAG system on a dataset.

        :param dataset: List of dictionaries; each dictionary must have the keys:
                        "user_input", "retrieved_contexts", "response", and "reference".
        :return: A dictionary of evaluation metrics computed by the RAGAS library.
        """
        from ragas import EvaluationDataset, evaluate

        evaluation_dataset = EvaluationDataset.from_list(dataset)
        result = evaluate(dataset=evaluation_dataset, metrics=self.metrics, llm=self.llm_wrapper)
        return result
