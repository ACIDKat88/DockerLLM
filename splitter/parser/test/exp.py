from tqdm import tqdm
from langchain.schema import Document
from langchain.vectorstores import Chroma
from embedd_class import customembedding
from sklearn.metrics.pairwise import cosine_similarity
from hybrid import Hybrid 
import pandas as pd

# Initialize Hybrid Retriever (Neo4j + Chroma)
graph_db = Hybrid(uri="neo4j://62.10.106.165:7687", user="neo4j", password="password")

# Initialize the embedding function and vector store.
embedding_function = customembedding("mixedbread-ai/mxbai-embed-large-v1")
persist_directory = "/home/cm36/Updated-LLM-Project/vectorstores/KG/chunk_size_mid"
vectorstore = Chroma(
    embedding_function=embedding_function, 
    persist_directory=persist_directory,
    collection_name="kg2"  # Explicitly specifying collection
)

def cypher_hybrid_retriever(query, k=30):
    """
    Retrieves documents using a two-step hybrid approach:
      1. Use a cypher query to retrieve relevant document hashes from Neo4j.
      2. Use the hashes as a filter for the vectorstore to get matching documents.
    
    Args:
        query (str): The user query.
        k (int): The number of documents to retrieve from the vectorstore.
    
    Returns:
        Tuple[List[Document], int]: The retrieved documents and the number of hashes retrieved.
    """
    # Step 1: Retrieve relevant document hashes from Neo4j via the cypher query.
    relevant_hashes = graph_db.query_kg_for_documents(query)
    num_hashes = len(relevant_hashes)
    print(f"[DEBUG] Retrieved {num_hashes} hashes from the knowledge graph: {relevant_hashes}")
    
    # Build a filter condition to match the document hashes in the vectorstore metadata.
    filter_condition = {"hash": {"$in": relevant_hashes}} if relevant_hashes else None
    print(f"[DEBUG] Filter condition: {filter_condition}")
    
    # Step 2: Retrieve documents from the vectorstore using the filter condition.
    search_kwargs = {"k": k}
    retriever = vectorstore.as_retriever(search_kwargs=search_kwargs)
    docs = retriever.get_relevant_documents(query, where=filter_condition)
    print(f"[DEBUG] Retrieved {len(docs)} documents from vectorstore after cypher filtering.")
    
    return docs, num_hashes

# Read CSV containing the queries.
usaf_df = pd.read_csv('/home/cm36/Updated-LLM-Project/csv/test_questions.csv')
query_list = usaf_df["question"].tolist()

# Prepare lists to collect results.
query_text_list = []
result_index_list = []
content_list = []
cos_score_list = []
metadata_list = []
kg_hash_count_list = []  # To record KG hash count per query

# Loop over each query.
for query in tqdm(query_list, desc="Running queries"):
    print(f"\nRunning test query: {query}")
    
    # Use the cypher-based hybrid retriever.
    docs, kg_hash_count = cypher_hybrid_retriever(query, k=30)
    print(f"Retrieved {len(docs)} documents for query: '{query}'")
    
    if not docs:
        print(f"No results found for query: {query}")
        continue
    
    # Compute the query embedding.
    query_embedding = embedding_function.embed_query(query)
    print("Query Embedding:", query_embedding)
    
    # Compute embeddings for each retrieved document.
    doc_embeddings = [embedding_function.embed_query(doc.page_content) for doc in docs]
    if not doc_embeddings:
        print(f"No embeddings found for retrieved documents for query: {query}")
        continue
    
    # Calculate cosine similarities between the query and each document.
    similarities = cosine_similarity([query_embedding], doc_embeddings)[0]
    
    # Pair each document with its cosine similarity score and sort by score (descending).
    doc_score_pairs = list(zip(docs, similarities))
    doc_score_pairs.sort(key=lambda x: x[1], reverse=True)
    
    # Select the top 5 documents based on cosine similarity.
    top_docs = doc_score_pairs[:5]
    
    # Record the results.
    for i, (doc, score) in enumerate(top_docs, 1):
        query_text_list.append(query)
        result_index_list.append(i)
        content_list.append(doc.page_content[:500])
        cos_score_list.append(score)
        metadata_list.append(doc.metadata)
        kg_hash_count_list.append(kg_hash_count)

# Save the results to a CSV.
results_df = pd.DataFrame({
    "query": query_text_list,
    "result_rank": result_index_list,
    "content": content_list,
    "cos_score": cos_score_list,
    "metadata_list": metadata_list,
    "kg_hash_count": kg_hash_count_list
})

results_df.to_csv('/home/cm36/Updated-LLM-Project/csv/results_j1_kg_preprocess.csv', index=False)
print("Results saved to /home/cm36/Updated-LLM-Project/csv/results_j1_kg_preprocess.csv")
