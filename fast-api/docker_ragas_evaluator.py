import numpy as np
import os
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

# RAGAS imports for RAG evaluation metrics
try:
    from ragas.metrics import (
        faithfulness,
        answer_relevancy,
        context_relevancy,
        context_recall,
        context_precision
    )
    from ragas.metrics.critique import harmfulness
    from ragas.llms import LangchainLLM
    from langchain_community.llms import HuggingFacePipeline
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
    RAGAS_AVAILABLE = True
except ImportError:
    RAGAS_AVAILABLE = False
    print("RAGAS package not available. Install with: pip install ragas langchain-community transformers torch")

# Configuration for the evaluation LLM - use local model files
MODEL_PATH = "/app/models/qwen3-0.6b"  # Path in Docker container
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"  # Use GPU if available

class RagasResult(BaseModel):
    """Model for storing RAGAS evaluation results"""
    faithfulness: Optional[float] = None
    answer_relevancy: Optional[float] = None
    context_relevancy: Optional[float] = None
    context_precision: Optional[float] = None
    context_recall: Optional[float] = None
    harmfulness: Optional[float] = None

def init_eval_llm():
    """
    Initialize the evaluation LLM using local model files
    
    Returns:
        LangchainLLM: Wrapped LLM for RAGAS evaluation or None if not available
    """
    if not RAGAS_AVAILABLE:
        return None
    
    try:
        # Check if model path exists
        if not os.path.exists(MODEL_PATH):
            print(f"Error: Model path {MODEL_PATH} not found")
            return None
            
        print(f"Loading Qwen3 0.6B model from {MODEL_PATH} on {DEVICE}")
        
        # Load model and tokenizer from local path
        tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_PATH,
            device_map=DEVICE,
            torch_dtype=torch.float16 if DEVICE == "cuda" else torch.float32,
            low_cpu_mem_usage=True
        )
        
        # Create text generation pipeline
        pipe = pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer,
            max_new_tokens=512,
            temperature=0.1,
            top_p=0.9,
            do_sample=True
        )
        
        # Create LangChain pipeline
        llm = HuggingFacePipeline(pipeline=pipe)
        
        # Wrap with RAGAS LangchainLLM adapter
        return LangchainLLM(llm)
    except Exception as e:
        print(f"Error initializing evaluation LLM: {e}")
        import traceback
        traceback.print_exc()
        print(f"Falling back to simplified evaluation without LLM")
        return None

def evaluate_with_ragas(
    question: str,
    answer: str,
    contexts: List[str],
    use_harmfulness: bool = False
) -> Dict[str, float]:
    """
    Evaluate RAG responses using RAGAS metrics with a local model
    
    Args:
        question: User query/question
        answer: Generated answer from the LLM
        contexts: List of context passages used for generation
        use_harmfulness: Whether to include harmfulness evaluation (more expensive)
        
    Returns:
        Dictionary with RAGAS metrics
    """
    # If RAGAS is not available, return empty results
    if not RAGAS_AVAILABLE:
        return RagasResult().dict()
    
    # Initialize evaluation LLM
    eval_llm = init_eval_llm()
    
    # Prepare the data in the format expected by RAGAS
    data = {
        "question": [question],
        "answer": [answer],
        "contexts": [contexts]
    }
    
    # Initialize results dictionary
    results = {}
    
    try:
        # Initialize metrics with the evaluation LLM if available
        if eval_llm:
            print("Using local Qwen3 0.6B model for evaluation")
            # Calculate faithfulness with specified LLM
            faith_metric = faithfulness.Faithfulness(llm=eval_llm)
            faith_score = faith_metric.score(data)
            results["faithfulness"] = float(np.mean(faith_score))
            
            # Calculate answer relevancy with specified LLM
            ans_rel_metric = answer_relevancy.AnswerRelevancy(llm=eval_llm)
            ans_rel_score = ans_rel_metric.score(data)
            results["answer_relevancy"] = float(np.mean(ans_rel_score))
            
            # Calculate context relevancy with specified LLM
            ctx_rel_metric = context_relevancy.ContextRelevancy(llm=eval_llm)
            ctx_rel_score = ctx_rel_metric.score(data)
            results["context_relevancy"] = float(np.mean(ctx_rel_score))
            
            # Calculate context precision (doesn't always need LLM)
            ctx_prec_metric = context_precision.ContextPrecision()
            ctx_prec_score = ctx_prec_metric.score(data)
            results["context_precision"] = float(np.mean(ctx_prec_score))
            
            # Calculate context recall (doesn't always need LLM)
            ctx_recall_metric = context_recall.ContextRecall()
            ctx_recall_score = ctx_recall_metric.score(data)
            results["context_recall"] = float(np.mean(ctx_recall_score))
            
            # Optionally calculate harmfulness with specified LLM
            if use_harmfulness:
                harm_metric = harmfulness.Harmfulness(llm=eval_llm)
                harm_score = harm_metric.score(data)
                results["harmfulness"] = float(np.mean(harm_score))
        else:
            print("Warning: LLM initialization failed. Using simplified metrics.")
            # Fallback to non-LLM-based metrics only
            ctx_prec_metric = context_precision.ContextPrecision()
            ctx_prec_score = ctx_prec_metric.score(data)
            results["context_precision"] = float(np.mean(ctx_prec_score))
            
            ctx_recall_metric = context_recall.ContextRecall()
            ctx_recall_score = ctx_recall_metric.score(data)
            results["context_recall"] = float(np.mean(ctx_recall_score))
            
            # Set other metrics to None
            results["faithfulness"] = None
            results["answer_relevancy"] = None
            results["context_relevancy"] = None
            results["harmfulness"] = None
    
    except Exception as e:
        print(f"Error calculating RAGAS metrics: {e}")
        import traceback
        traceback.print_exc()
        # Return empty results on error
        return RagasResult().dict()
    
    return results

async def async_evaluate_with_ragas(
    question: str,
    answer: str,
    contexts: List[str],
    use_harmfulness: bool = False
) -> Dict[str, float]:
    """
    Asynchronous wrapper for evaluate_with_ragas
    """
    import asyncio
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None, 
        lambda: evaluate_with_ragas(question, answer, contexts, use_harmfulness)
    )

def extract_contexts_from_docs(retrieved_docs):
    """
    Extract context passages from retrieved documents
    
    Args:
        retrieved_docs: List of document objects from vector store
        
    Returns:
        List of context passages as strings
    """
    contexts = []
    
    for doc in retrieved_docs:
        if hasattr(doc, "page_content"):
            contexts.append(doc.page_content)
        elif isinstance(doc, dict) and "page_content" in doc:
            contexts.append(doc["page_content"])
        elif isinstance(doc, dict) and "content" in doc:
            contexts.append(doc["content"])
    
    return contexts 