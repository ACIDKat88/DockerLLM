import os
import re
import uuid
import json
from tqdm import tqdm
from langchain.schema import Document
from langchain.vectorstores import Chroma
from embedd_class import customembedding
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd

# Initialize the embedding function and vector store.
embedding_function = customembedding("mixedbread-ai/mxbai-embed-large-v1")
persist_directory = "/home/cm36/Updated-LLM-Project/vectorstores/J1/chunk_size_170"
vectorstore = Chroma(
    embedding_function=embedding_function, 
    persist_directory=persist_directory,
    collection_name="langchain"  # Explicitly specifying collection
)

def initialize_langchain_retriever():
    """
    Initializes the LangChain retriever with semantic search only.
    """
    search_kwargs = {"k": 5}  # Retrieve top 10 results
    retriever = vectorstore.as_retriever(search_kwargs=search_kwargs)
    return retriever

# Read CSV containing the queries.
usaf_df = pd.read_csv('/home/cm36/Updated-LLM-Project/csv/test_questions.csv')
query_list = usaf_df["question"].tolist()

# Prepare lists to collect results.
query_text_list = []
result_index_list = []
content_list = []
cos_score_list = []
metadata_list = []

# Loop over each query.
for query in query_list:
    print(f"\nRunning test query: {query}")
    
    retriever = initialize_langchain_retriever()
    
    # Retrieve documents using the retriever.
    docs = retriever.invoke(query)
    print(f"Retrieved {len(docs)} documents for query: '{query}'")
    
    if not docs:
        print(f"No results found for query: {query}")
        continue
    
    # Debugging query embedding
    query_embedding = embedding_function.embed_query(query)
    print("Query Embedding:", query_embedding)
    
    # Compute cosine similarities manually.
    doc_embeddings = [embedding_function.embed_query(doc.page_content) for doc in docs]
    
    # Debugging: Ensure document embeddings exist
    if not doc_embeddings:
        print(f"No embeddings found for retrieved documents for query: {query}")
        continue
    
    similarities = cosine_similarity([query_embedding], doc_embeddings)[0]
    
    # Print retrieved document metadata for inspection
    for i, doc in enumerate(docs, 1):
        print(f"Document {i}: {doc.metadata}")
    
    for i, (doc, score) in enumerate(zip(docs, similarities), 1):
        query_text_list.append(query)
        result_index_list.append(i)
        content_list.append(doc.page_content[:500])
        cos_score_list.append(score)
        metadata_list.append(doc.metadata)

# Create a DataFrame with the results.
results_df = pd.DataFrame({
    "query": query_text_list,
    "result_rank": result_index_list,
    "content": content_list,
    "cos_score": cos_score_list,
    "metadata_list": metadata_list
})

# Save the results to CSV.
results_df.to_csv('/home/cm36/Updated-LLM-Project/csv/results_j1_langchain_pdf_170.csv', index=False)
print("Results saved to /home/cm36/Updated-LLM-Project/csv/results_j1_langchain_pdf_170.csv")
