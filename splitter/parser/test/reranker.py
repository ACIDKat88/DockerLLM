# reranker.py

from sentence_transformers import CrossEncoder

def rerank_documents(query, documents, model_name='cross-encoder/ms-marco-MiniLM-L-6-v2'):
    """
    Re-rank documents based on relevance to the query using a cross-encoder model.
    
    Args:
        query (str): The user query.
        documents (list): A list of document objects. Each document should have a 'page_content'
                          attribute or key containing the document text.
        model_name (str): The name of the cross-encoder model to use.
        
    Returns:
        List[Tuple[float, Document]]: A list of tuples (score, document) sorted by score in descending order.
    """
    # Initialize the cross-encoder
    cross_encoder = CrossEncoder(model_name)
    
    # Create query-document pairs for scoring
    pairs = []
    for doc in documents:
        # Support both dicts and objects with a page_content attribute
        if isinstance(doc, dict):
            doc_text = doc.get("page_content", "")
        else:
            doc_text = getattr(doc, "page_content", "")
        pairs.append([query, doc_text])
    
    # Predict relevance scores for each pair
    scores = cross_encoder.predict(pairs)
    
    # Pair each document with its score and sort by score (highest first)
    scored_docs = sorted(zip(scores, documents), key=lambda x: x[0], reverse=True)
    return scored_docs
