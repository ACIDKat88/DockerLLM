import os
import json
from embedd_class import customembedding
from neo4j import GraphDatabase
from sklearn.metrics.pairwise import cosine_similarity
from tqdm import tqdm

# Load embedding model
embedding_function = customembedding("mixedbread-ai/mxbai-embed-large-v1")

class KnowledgeGraph:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def add_node(self, label, properties):
        query = f"""
        MERGE (n:{label} {{title: $title}})
        SET n.hash = $hash, n += $properties
        """
        with self.driver.session() as session:
            session.run(query, title=properties["title"], hash=properties["hash"], properties=properties)

    def add_relationship(self, node1_title, node2_title, relation, content=None, score=None):
        query = f"""
        MATCH (a {{title: $node1_title}}), (b {{title: $node2_title}})
        MERGE (a)-[r:{relation}]->(b)
        """
        params = {"node1_title": node1_title, "node2_title": node2_title}
        if score is not None:
            query += " SET r.score = $score"
            params["score"] = score
        if content is not None:
            query += " SET r.content = $content"
            params["content"] = content
        with self.driver.session() as session:
            session.run(query, **params)

    def compute_similarity(self, emb1, emb2):
        return cosine_similarity([emb1], [emb2])[0][0]

    def find_similar_nodes(self, node_list, threshold=0.8):
        similar_pairs = []
        for (node1, emb1), (node2, emb2) in [(n1, n2) for n1 in node_list.items() for n2 in node_list.items() if n1 != n2]:
            similarity = self.compute_similarity(emb1, emb2)
            if similarity >= threshold:
                similar_pairs.append((node1, node2, similarity))
        return similar_pairs

    def process_json(self, json_path):
        with open(json_path, "r") as f:
            data = json.load(f)

        document_embeddings = {}
        chapter_embeddings = {}
        section_embeddings = {}
        subsection_embeddings = {}

        # Count total number of documents for progress display.
        total_docs = sum(len(doc_files) for doc_files in data.values())
        pbar = tqdm(total=total_docs, desc="Inserting Documents", unit="doc")

        # Insert Documents, Chapters, Sections, Subsections
        for doc_type, doc_files in data.items():
            for doc_name, doc_data in doc_files.items():
                doc_title = doc_data["title"]
                # Check if the document already exists:
                with self.driver.session() as session:
                    result = session.run("MATCH (n:Document {title: $title}) RETURN n LIMIT 1", title=doc_title)
                    if result.single() is not None:
                        print(f"Document '{doc_title}' already exists. Skipping insertion.")
                        pbar.update(1)
                        continue

                doc_hash = doc_data["hash_document"]
                # Combine all chapter contents for document-level text.
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

                    self.add_node("Chapter", {"title": chap_title, "hash": chap_hash, "content": chap_text})
                    self.add_relationship(doc_title, chap_title, "CONTAINS", content=chap_text)

                    for section in chapter.get("sections", []):
                        sec_hash = section.get("hash_section")
                        if sec_hash is None:
                            print(f"Warning: Missing 'hash_section' for section titled '{section.get('title', 'Unknown')}'. Skipping section.")
                            continue
                        sec_title = section["title"]
                        sec_text = section["content"]
                        sec_embedding = embedding_function.embed_query(sec_text)
                        section_embeddings[sec_title] = sec_embedding

                        self.add_node("Section", {"title": sec_title, "hash": sec_hash, "content": sec_text})
                        self.add_relationship(chap_title, sec_title, "CONTAINS", content=sec_text)

                        for subsection in section.get("sublevels", []):
                            sub_hash = subsection.get("hash_subsection")
                            if sub_hash is None:
                                print(f"Warning: Missing 'hash_subsection' for subsection titled '{subsection.get('title', 'Unknown')}'. Skipping subsection.")
                                continue
                            sub_title = subsection["title"]
                            sub_text = subsection["content"]
                            sub_embedding = embedding_function.embed_query(sub_text)
                            subsection_embeddings[sub_title] = sub_embedding

                            self.add_node("Subsection", {"title": sub_title, "hash": sub_hash, "content": sub_text})
                            self.add_relationship(sec_title, sub_title, "CONTAINS", content=sub_text)
                pbar.update(1)
        pbar.close()

        # Compute SIMILAR_TO relationships
        for d1, d2, score in self.find_similar_nodes(document_embeddings, threshold=0.8):
            self.add_relationship(d1, d2, "SIMILAR_TO", score=score)
        for c1, c2, score in self.find_similar_nodes(chapter_embeddings, threshold=0.8):
            self.add_relationship(c1, c2, "SIMILAR_TO", score=score)
        for s1, s2, score in self.find_similar_nodes(section_embeddings, threshold=0.8):
            self.add_relationship(s1, s2, "SIMILAR_TO", score=score)
        for sub1, sub2, score in self.find_similar_nodes(subsection_embeddings, threshold=0.8):
            self.add_relationship(sub1, sub2, "SIMILAR_TO", score=score)

        print("Neo4j knowledge graph successfully updated.")

# Example usage:
# kg = KnowledgeGraph(uri="bolt://localhost:7687", user="neo4j", password="password")
# kg.process_json("your_json_file.json")
