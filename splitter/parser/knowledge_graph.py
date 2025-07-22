import json
from embedd_class import customembedding
from neo4j import GraphDatabase
from sklearn.metrics.pairwise import cosine_similarity

# Load embedding model
embedding_function = customembedding("mixedbread-ai/mxbai-embed-large-v1")

class KnowledgeGraph:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def add_node(self, label, properties):
        """Insert a node into Neo4j with hash as metadata, not as a separate node."""
        query = f"""
        MERGE (n:{label} {{title: $title}})
        SET n.hash = $hash, n += $properties
        """
        with self.driver.session() as session:
            session.run(query, title=properties["title"], hash=properties["hash"], properties=properties)

    def add_relationship(self, node1_title, node2_title, relation, score=None):
        """Insert relationships (CONTAINS or SIMILAR_TO)."""
        query = f"""
        MATCH (a {{title: $node1_title}}), (b {{title: $node2_title}})
        MERGE (a)-[r:{relation}]->(b)
        """
        if score is not None:
            query += " SET r.score = $score"
        
        with self.driver.session() as session:
            session.run(query, node1_title=node1_title, node2_title=node2_title, score=score)

    def compute_similarity(self, emb1, emb2):
        """Compute cosine similarity between two embeddings."""
        return cosine_similarity([emb1], [emb2])[0][0]

    def find_similar_nodes(self, node_list, threshold=0.8):
        """Find similar chapters, sections, and subsections across documents."""
        similar_pairs = []
        for (node1, emb1), (node2, emb2) in [(n1, n2) for n1 in node_list.items() for n2 in node_list.items() if n1 != n2]:
            similarity = self.compute_similarity(emb1, emb2)
            if similarity >= threshold:
                similar_pairs.append((node1, node2, similarity))
        return similar_pairs

    def process_json(self, json_path):
        """Process the JSON file and store the data in Neo4j."""
        with open(json_path, "r") as f:
            data = json.load(f)

        document_embeddings = {}
        chapter_embeddings = {}
        section_embeddings = {}
        subsection_embeddings = {}

        # Insert Documents, Chapters, Sections, Subsections
        for doc_type, doc_files in data.items():
            for doc_name, doc_data in doc_files.items():
                doc_hash = doc_data["hash_document"]
                doc_title = doc_data["title"]
                
                doc_text = " ".join(chap["content"] for chap in doc_data.get("chapters", []))
                doc_embedding = embedding_function.embed_query(doc_text)
                document_embeddings[doc_title] = doc_embedding

                self.add_node("Document", {"title": doc_title, "hash": doc_hash, "type": doc_type})

                for chapter in doc_data.get("chapters", []):
                    chap_hash = chapter["hash_chapter"]
                    chap_title = chapter["title"]
                    chap_text = chapter["content"]
                    chap_embedding = embedding_function.embed_query(chap_text)
                    chapter_embeddings[chap_title] = chap_embedding

                    self.add_node("Chapter", {"title": chap_title, "hash": chap_hash})
                    self.add_relationship(doc_title, chap_title, "CONTAINS")

                    for section in chapter.get("sections", []):
                        sec_hash = section["hash_section"]
                        sec_title = section["title"]
                        sec_text = section["content"]
                        sec_embedding = embedding_function.embed_query(sec_text)
                        section_embeddings[sec_title] = sec_embedding

                        self.add_node("Section", {"title": sec_title, "hash": sec_hash})
                        self.add_relationship(chap_title, sec_title, "CONTAINS")

                        for subsection in section.get("sublevels", []):
                            sub_hash = subsection["hash_subsection"]
                            sub_title = subsection["title"]
                            sub_text = subsection["content"]
                            sub_embedding = embedding_function.embed_query(sub_text)
                            subsection_embeddings[sub_title] = sub_embedding

                            self.add_node("Subsection", {"title": sub_title, "hash": sub_hash})
                            self.add_relationship(sec_title, sub_title, "CONTAINS")

        # Compute `SIMILAR_TO` Relationships
        similar_docs = self.find_similar_nodes(document_embeddings, threshold=0.8)
        similar_chapters = self.find_similar_nodes(chapter_embeddings, threshold=0.8)
        similar_sections = self.find_similar_nodes(section_embeddings, threshold=0.8)
        similar_subsections = self.find_similar_nodes(subsection_embeddings, threshold=0.8)

        for d1, d2, score in similar_docs:
            self.add_relationship(d1, d2, "SIMILAR_TO", score)

        for c1, c2, score in similar_chapters:
            self.add_relationship(c1, c2, "SIMILAR_TO", score)

        for s1, s2, score in similar_sections:
            self.add_relationship(s1, s2, "SIMILAR_TO", score)

        for sub1, sub2, score in similar_subsections:
            self.add_relationship(sub1, sub2, "SIMILAR_TO", score)

        print("Neo4j knowledge graph successfully updated.")
