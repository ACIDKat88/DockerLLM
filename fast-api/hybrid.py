from neo4j import GraphDatabase
from reranker import rerank_documents
from langchain.docstore.document import Document
import asyncio
from embedd_class import customembedding
import asyncio
import contextvars
import threading
from retriever import CustomChromaRetriever



# Load the embedding function if needed elsewhere in your system
embedding_function = customembedding("mixedbread-ai/mxbai-embed-large-v1")

class Hybrid:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def query_kg_for_documents(self, user_query, min_score=5):
        """
        Query the knowledge graph using a full-text cypher query to retrieve
        relevant documents. Assumes that a full-text index named "combinedIndex"
        exists on the node properties [title, content].

        Args:
            user_query (str): The user's input query.
            min_score (float): Minimum score threshold to filter results.

        Returns:
            List[Document]: A list of Document objects with metadata.
        """
        search_string = "*" + user_query + "*~"  # e.g., "*feedback*~"
        with self.driver.session() as session:
            result = session.run(
                """
                CALL db.index.fulltext.queryNodes("combinedIndex", $search_string) YIELD node, score
                WHERE score > $min_score
                RETURN node.hash AS hash, node.title AS title, node.content AS content, score
                """,
                search_string=search_string,
                min_score=min_score
            )
            documents = []
            for record in result:
                data = record.data()
                doc = Document(
                    page_content=data["content"],
                    metadata={
                        "hash": data["hash"],
                        "title": data["title"],
                        "score": data["score"]
                    }
                )
                documents.append(doc)
            return documents

def cypher_retriever(user_query, kg, vector_retriever, cross_encoder, k=30, re_rank_top=5):
    """
    Retrieves documents by:
      1. Querying Neo4j for relevant document hashes (using a cypher query).
      2. Building a filter condition to match these hashes in the vectorstore.
      3. Retrieving the matching documents from the vectorstore.
      4. Reranking the documents using a cross-encoder.
      5. Additionally, including content directly from top 5 Neo4j nodes.
      
    Args:
        user_query (str): The user query.
        kg (Hybrid): An instance of your Hybrid class.
        vector_retriever: A Chroma retriever instance.
        cross_encoder: A cross-encoder model for reranking.
        k (int): Number of documents to retrieve from the vectorstore.
        re_rank_top (int): Number of top documents to return after reranking.
        
    Returns:
        Tuple[str, List[Document], int]: A tuple containing the concatenated context, 
                                         the list of top reranked documents, and the count of hashes.
    """
    # Log retriever details if it's a PGVectorRetriever
    if hasattr(vector_retriever, 'table_name'):
        print(f"[DEBUG] cypher_retriever: Using PGVector retriever with table '{vector_retriever.table_name}'")

    # Step 1: Retrieve relevant document hashes and content from the knowledge graph.
    kg_documents = kg.query_kg_for_documents(user_query)
    node_count = len(kg_documents)
    print(f"[DEBUG] Retrieved {node_count} nodes from KG")
    
    # Get the hashes for filtering PGVector
    relevant_hashes = [doc.metadata["hash"] for doc in kg_documents]
    print(f"[DEBUG] Using {len(relevant_hashes)} hashes for filtering: {relevant_hashes}")
    
    # Extract the top 5 Neo4j documents directly for inclusion in the context
    top_neo4j_docs = kg_documents[:5] if len(kg_documents) > 0 else []
    print(f"[DEBUG] Using content from {len(top_neo4j_docs)} Neo4j nodes directly in context")
    
    # Step 2: Build the filter condition for the vectorstore.
    filter_condition = {"hash": {"$in": relevant_hashes}} if relevant_hashes else None
    print(f"[DEBUG] Filter condition: {filter_condition}")
    
    # Step 3: Retrieve documents from the vectorstore using the filter.
    docs = vector_retriever.get_relevant_documents(user_query)
    print(f"[DEBUG] Retrieved {len(docs)} documents from vector store after filtering.")

    # If there are KG hashes, manually filter the retrieved vectorstore docs.
    if filter_condition is not None:
        filtered_docs = [doc for doc in docs if doc.metadata.get("hash") in relevant_hashes]
        if filtered_docs:
            docs = filtered_docs
            print(f"[DEBUG] Using filtered docs based on KG hashes; count: {len(filtered_docs)}")
        else:
            docs = docs
            print(f"[DEBUG] Filtered docs empty, falling back to all unfiltered vectorstore docs.")
    else:
        docs = docs

    print(f"[DEBUG] Retrieved {len(docs)} documents from vector store after filtering/fallback.")
    
    # Optionally, you can limit the number of documents (k) here.
    if len(docs) > k:
        docs = docs[:k]
    
    # Step 4: Rerank the retrieved documents using the cross-encoder.
    scored_results = rerank_documents(user_query, docs)
    top_results = [doc for score, doc in scored_results[:re_rank_top]]
    
    # Step 5: Combine context from both Neo4j nodes directly and PGVector retrieval
    # Add content from Neo4j nodes
    neo4j_context = "\n\n".join([f"[Neo4j Node] {doc.page_content}" for doc in top_neo4j_docs])
    
    # Add content from PGVector retrieval
    pgvector_context = "\n\n".join([doc.page_content for doc in top_results])
    
    # Combine both contexts
    if neo4j_context and pgvector_context:
        context = f"{neo4j_context}\n\n{pgvector_context}"
    else:
        context = neo4j_context or pgvector_context
    
    # Return top results including both Neo4j and PGVector documents for sources display
    all_top_results = list(top_neo4j_docs)
    # Add PGVector results that aren't duplicates of Neo4j nodes
    pgv_hashes = [doc.metadata.get("hash") for doc in all_top_results]
    for doc in top_results:
        if doc.metadata.get("hash") not in pgv_hashes:
            all_top_results.append(doc)
    
    print(f"[DEBUG] Final context includes {len(top_neo4j_docs)} Neo4j nodes and {len(top_results)} PGVector documents")
    
    return context, all_top_results, node_count


async def async_cypher_retriever(*args, **kwargs):
    ctx = contextvars.copy_context()
    return await asyncio.to_thread(ctx.run, cypher_retriever, *args, **kwargs)
