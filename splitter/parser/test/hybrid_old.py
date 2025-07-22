from neo4j import GraphDatabase
from langchain.docstore.document import Document
from embedd_class import customembedding

# Load the embedding function if needed elsewhere in your system
embedding_function = customembedding("mixedbread-ai/mxbai-embed-large-v1")

class Hybrid:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def query_kg_for_documents(self, user_query, min_score=7):
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
                CALL db.index.fulltext.queryNodes("documentCombinedIndex", $search_string) YIELD node, score
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

def cypher_retriever(user_query, kg: Hybrid):
    """
    Retriever that uses only the cypher query results from Neo4j to filter documents.

    Args:
        user_query (str): The query input by the user.
        kg (Hybrid): Instance of the Hybrid class.

    Returns:
        List[Document]: List of documents retrieved from the knowledge graph.
    """
    documents = kg.query_kg_for_documents(user_query)
    print(f"[DEBUG] Retrieved {len(documents)} documents from the knowledge graph.")
    return documents
