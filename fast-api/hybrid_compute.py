from neo4j import GraphDatabase
from reranker import rerank_documents
from langchain.docstore.document import Document
import asyncio
from embedd_class import customembedding
import asyncio
import contextvars
import threading
from retriever import CustomChromaRetriever
import time  # Add timing imports



# Load the embedding function if needed elsewhere in your system
embedding_function = customembedding("mixedbread-ai/mxbai-embed-large-v1")

class Hybrid:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.uri = uri
        self.user = user
        self.password = password

    def close(self):
        self.driver.close()

    def validate_neo4j_connection(self):
        """Test if Neo4j connection is still alive and responsive."""
        try:
            with self.driver.session() as session:
                result = session.run("RETURN 1 as test")
                record = result.single()
                return record and record["test"] == 1
        except Exception as e:
            print(f"[DEBUG] Neo4j connection validation failed: {e}")
            return False

    def refresh_neo4j_connection(self):
        """Refresh Neo4j driver if connection is stale."""
        try:
            self.driver.close()
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            print("[DEBUG] 🔄 Neo4j connection refreshed")
        except Exception as e:
            print(f"[ERROR] Failed to refresh Neo4j connection: {e}")

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
        # CRITICAL: Validate connection before use (prevents hangs)
        if not self.validate_neo4j_connection():
            print("[DEBUG] 🔄 Neo4j connection stale, refreshing...")
            self.refresh_neo4j_connection()
            
            # Test again after refresh
            if not self.validate_neo4j_connection():
                print("[ERROR] ❌ Neo4j connection still failed after refresh")
                return []  # Return empty rather than hang
        
        print("[DEBUG] ✅ Neo4j connection validated successfully")
        
        search_string = "*" + user_query + "*~"  # e.g., "*feedback*~"
        kg_start_time = time.time()
        
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
        
        kg_duration = time.time() - kg_start_time
        print(f"[TIMING] Neo4j KG query took {kg_duration:.2f} seconds, retrieved {len(documents)} documents")
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
    total_start_time = time.time()
    
    # Log retriever details if it's a PGVectorRetriever
    if hasattr(vector_retriever, 'table_name'):
        print(f"[DEBUG] cypher_retriever: Using PGVector retriever with table '{vector_retriever.table_name}'")

    # Step 1: Retrieve relevant document hashes and content from the knowledge graph.
    print("[TIMING] Starting Neo4j KG query...")
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
    print("[TIMING] Starting PostgreSQL vector retrieval...")
    vector_start_time = time.time()
    docs = vector_retriever.get_relevant_documents(user_query)
    vector_duration = time.time() - vector_start_time
    print(f"[TIMING] PostgreSQL vector retrieval took {vector_duration:.2f} seconds, retrieved {len(docs)} documents")

    # If there are KG hashes, manually filter the retrieved vectorstore docs.
    if filter_condition is not None:
        filter_start_time = time.time()
        filtered_docs = [doc for doc in docs if doc.metadata.get("hash") in relevant_hashes]
        filter_duration = time.time() - filter_start_time
        print(f"[TIMING] Document filtering took {filter_duration:.2f} seconds")
        
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
    print("[TIMING] Starting cross-encoder reranking...")
    rerank_start_time = time.time()
    
    # SAFETY CHECK: Only rerank if we have documents
    if docs and len(docs) > 0:
        print(f"[DEBUG] 🔄 Proceeding with reranking of {len(docs)} documents")
        scored_results = rerank_documents(user_query, docs)
        top_results = [doc for score, doc in scored_results[:re_rank_top]]
        print(f"[DEBUG] ✅ Reranking selected {len(top_results)} top documents")
    else:
        print("[DEBUG] ⚠️ No documents available for reranking, using empty results")
        scored_results = []
        top_results = []
    
    rerank_duration = time.time() - rerank_start_time
    print(f"[TIMING] Cross-encoder reranking took {rerank_duration:.2f} seconds")
    
    # Step 5: Combine context from both Neo4j nodes directly and PGVector retrieval
    print("[TIMING] Building final context...")
    context_start_time = time.time()
    
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
    
    context_duration = time.time() - context_start_time
    total_duration = time.time() - total_start_time
    
    print(f"[TIMING] Context building took {context_duration:.2f} seconds")
    print(f"[TIMING] Total cypher_retriever took {total_duration:.2f} seconds")
    print(f"[DEBUG] Final context includes {len(top_neo4j_docs)} Neo4j nodes and {len(top_results)} PGVector documents")
    
    return context, all_top_results, node_count


async def async_cypher_retriever(*args, **kwargs):
    ctx = contextvars.copy_context()
    return await asyncio.to_thread(ctx.run, cypher_retriever, *args, **kwargs)
