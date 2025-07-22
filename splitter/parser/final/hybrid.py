from langchain_community.vectorstores import Chroma
from neo4j import GraphDatabase
from reranker import rerank_documents  # Import your existing reranker
from embedd_class import customembedding

# Load the embedding function
embedding_function = customembedding("mixedbread-ai/mxbai-embed-large-v1")

class Hybrid:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def query_kg_for_hashes(self, user_query, min_score=3):
        """
        Query the knowledge graph to retrieve relevant document hashes across all levels 
        (Document, Chapter, Section, Subsection) using a full-text index,
        but only return nodes with a score above min_score.
        
        Assumes that a full-text index named "combinedIndex" exists over these labels 
        on the properties [title, content].
        
        Args:
            user_query (str): The user's input query.
            min_score (float): Minimum score threshold (e.g. 0.5) to filter results.
            
        Returns:
            List[str]: A list of document hashes.
        """
        search_string = "*" + user_query + "*~"  # Example: "*feedback*~"
        with self.driver.session() as session:
            result = session.run(
                """
                CALL db.index.fulltext.queryNodes("combinedIndex", $search_string) YIELD node, score
                WHERE score > $min_score
		MATCH (node)-[:SIMILAR_TO]->(child)
                RETURN DISTINCT node.hash AS hash
                """,
                search_string=search_string,
                min_score=min_score
            )
            return [record["hash"] for record in result]


def hybrid_retriever(user_query, kg: Hybrid, vector_retriever, cross_encoder, k=30, re_rank_top=5):
    """
    Hybrid retriever that combines structured filtering from Neo4j with dense retrieval from ChromaDB.

    Args:
        user_query (str): The query input by the user.
        kg (KnowledgeGraph): Instance of the KnowledgeGraph class.
        vector_retriever: ChromaDB retriever for dense vector search.
        cross_encoder: Cross-encoder reranking model.
        k (int): Number of documents to retrieve from the vector store.
        re_rank_top (int): Number of top-ranked documents to return after reranking.

    Returns:
        str: A string containing the concatenated text of the most relevant documents.
        List[Document]: List of top retrieved and reranked documents.
    """
    # Step 1: Retrieve relevant document hashes from Neo4j
    relevant_hashes = kg.query_kg_for_hashes(user_query)
    
    # Step 2: Use hashes as a filter for vector retrieval in ChromaDB
    filter_condition = {"hash": {"$in": relevant_hashes}} if relevant_hashes else None
    langchain_chunks = vector_retriever.get_relevant_documents(user_query, where=filter_condition, k=k)

    # Step 3: Re-rank retrieved documents using cross-encoder
    scored_results = rerank_documents(user_query, langchain_chunks)
    top_results = [doc for score, doc in scored_results[:re_rank_top]]

    # Step 4: Build the final context from the top results
    context = "\n\n".join([doc.page_content for doc in top_results])
    return context, top_results

