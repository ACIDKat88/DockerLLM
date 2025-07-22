# example_usage.py

# For local retrieval and evaluation, we use a dummy retriever.
from llm_evaluator.evaluators.rag_evaluator import RAGEvaluator, RAGASDatasetEvaluator
from llm_evaluator.pipelines.retriever_wrapper import RetrieverWrapper

# Import TeapotAI and define an adapter to provide a generate() method.
try:
    from teapotai import TeapotAI
except ImportError:
    raise ImportError("Please install teapotai (pip install teapotai) to run this example.")

class TeapotLLMAdapter:
    """
    Adapter for TeapotAI to provide a 'generate' method required by the evaluator.
    
    This temporary adaptation uses TeapotAI's query() method by setting both the query and context
    to the provided prompt.
    """
    def __init__(self, documents=None):
        # If documents are provided, initialize TeapotAI for RAG; otherwise, standard QnA.
        self.teapot_ai = TeapotAI(documents=documents) if documents else TeapotAI()
        
    def generate(self, prompt, max_length=100, **kwargs):
        """
        Generate text using TeapotAI. For simplicity, we treat the prompt as both query and context.
        
        :param prompt: Input prompt.
        :param max_length: Maximum length (ignored in this simple adapter).
        :return: Generated answer as a string.
        """
        # In a robust adapter, you might split query and context;
        # here we use the prompt for both.
        return self.teapot_ai.query(query=prompt, context=prompt)

# --- Dummy Retriever for RAG pipeline ---
class DummyRetriever:
    def retrieve(self, query):
        # In a real system, this would interface with a document store.
        return [
            "Albert Einstein proposed the theory of relativity, which transformed our understanding of time, space, and gravity.",
            "Marie Curie was a physicist and chemist who conducted pioneering research on radioactivity and won two Nobel Prizes.",
            "Isaac Newton formulated the laws of motion and universal gravitation, laying the foundation for classical mechanics.",
            "Charles Darwin introduced the theory of evolution by natural selection in his book 'On the Origin of Species'.",
            "Ada Lovelace is regarded as the first computer programmer for her work on Charles Babbage's early mechanical computer, the Analytical Engine."
        ]

def main():
    # Initialize the dummy retriever and wrap it with the pipeline interface.
    retriever = DummyRetriever()
    pipeline_interface = RetrieverWrapper(retriever)
    
    # --- Single Query Evaluation using RAGEvaluator ---
    evaluator = RAGEvaluator(pipeline_interface)
    
    query = "Who introduced the theory of relativity?"
    context = pipeline_interface.retrieve_context(query)
    # For demonstration, we manually define the generated_text.
    generated_text = ("Albert Einstein introduced the theory of relativity, transforming our understanding of the universe.")
    
    per_query_results = evaluator.evaluate(generated_text, context)
    print("Per-Query Evaluation Results:")
    print(per_query_results)
    
    # --- Dataset-Level Evaluation using RAGASDatasetEvaluator with TeapotLLMAdapter ---
    # Initialize TeapotLLMAdapter (which adapts TeapotAI to our expected interface).
    teapot_llm_adapter = TeapotLLMAdapter()
    dataset_evaluator = RAGASDatasetEvaluator(teapot_llm_adapter)
    
    # Prepare sample queries and reference responses following the RAGAS documentation.
    sample_queries = [
        "Who introduced the theory of relativity?",
        "Who was the first computer programmer?",
        "What did Isaac Newton contribute to science?",
        "Who won two Nobel Prizes for research on radioactivity?",
        "What is the theory of evolution by natural selection?"
    ]
    
    expected_responses = [
        "Albert Einstein proposed the theory of relativity, which transformed our understanding of time, space, and gravity.",
        "Ada Lovelace is regarded as the first computer programmer for her work on Charles Babbage's early mechanical computer, the Analytical Engine.",
        "Isaac Newton formulated the laws of motion and universal gravitation, laying the foundation for classical mechanics.",
        "Marie Curie was a physicist and chemist who conducted pioneering research on radioactivity and won two Nobel Prizes.",
        "Charles Darwin introduced the theory of evolution by natural selection in his book 'On the Origin of Species'."
    ]
    
    dataset = []
    for query, reference in zip(sample_queries, expected_responses):
        retrieved_docs = pipeline_interface.retrieve_context(query)["documents"]
        # For demonstration, we use the first retrieved document as the response.
        response = retrieved_docs[0] if retrieved_docs else ""
        dataset.append({
            "user_input": query,
            "retrieved_contexts": retrieved_docs,
            "response": response,
            "reference": reference
        })
    
    dataset_results = dataset_evaluator.evaluate_dataset(dataset)
    print("Dataset Evaluation Results:")
    print(dataset_results)

if __name__ == '__main__':
    main()


