from neo4j import GraphDatabase
from reranker import rerank_documents
from langchain.docstore.document import Document
import asyncio
from embedd_class import customembedding
import asyncio
import contextvars
import threading



# Load the embedding function if needed elsewhere in your system
embedding_function = customembedding("mixedbread-ai/mxbai-embed-large-v1")

class Hybrid:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.driver_lock = threading.Lock()

    def query_kg_for_documents(self, user_query, min_score=5):
        search_string = "*" + user_query + "*~"
        with self.driver_lock:
            with self.driver.session() as session:
                result = session.run(
                    """
                    CALL db.index.fulltext.queryNodes("documentCombinedIndex", $search_string) YIELD node, score
                    WHERE score > $min_score
                    RETURN node.hash AS hash, node.title AS title, node.content AS content, score
                    """,
                    search_string=search_string,
                    min_score=min_score
                )
                # Immediately convert the result to a list:
                records = list(result)
                documents = []
                for record in records:
                    # record is already a dictionary
                    doc = Document(
                        page_content=record["content"],
                        metadata={
                            "hash": record["hash"],
                            "title": record["title"],
                            "score": record["score"]
                        }
                    )
                    documents.append(doc)
                return documents


kg_lock = threading.Lock()

def safe_query_kg_for_documents(kg, user_query, min_score=5):
    with kg_lock:
        return kg.query_kg_for_documents(user_query, min_score)


def cypher_retriever(user_query, kg, vector_retriever, cross_encoder, k=30, re_rank_top=5):
    # Retrieve KG hashes, which might be empty.
    relevant_hashes = safe_query_kg_for_documents(kg, user_query)
    node_count = len(relevant_hashes)
    print(f"[DEBUG] Retrieved {node_count} hashes from KG: {relevant_hashes}")
    
    # Build filter condition only if hashes exist.
    filter_condition = {"hash": {"$in": relevant_hashes}} if relevant_hashes else None
    print(f"[DEBUG] Filter condition: {filter_condition}")
    
    # Query the vector store with or without the filter.
    if filter_condition is not None:
        docs = vector_retriever.get_relevant_documents(user_query, where=filter_condition)
    else:
        docs = vector_retriever.get_relevant_documents(user_query)
    print(f"[DEBUG] Retrieved {len(docs)} documents from vector store after filtering.")
    
    # Optionally limit the number of documents.
    if len(docs) > k:
        docs = docs[:k]
    
    # **Reranking happens regardless of filter condition.**
    scored_results = rerank_documents(user_query, docs)
    top_results = [doc for score, doc in scored_results[:re_rank_top]]
    context = "\n\n".join([doc.page_content for doc in top_results])
    
    return context, top_results, node_count



async def async_cypher_retriever(*args, **kwargs):
    ctx = contextvars.copy_context()
    return await asyncio.to_thread(ctx.run, cypher_retriever, *args, **kwargs)
