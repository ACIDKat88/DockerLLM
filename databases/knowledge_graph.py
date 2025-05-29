import json
import os
import logging
from embedd_class import customembedding
from neo4j import GraphDatabase
from sklearn.metrics.pairwise import cosine_similarity
import hashlib

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Load embedding model
embedding_function = customembedding("mixedbread-ai/mxbai-embed-large-v1")

class KnowledgeGraph:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.batch_size = 100  # Default batch size

    def close(self):
        self.driver.close()

    def add_node(self, label, properties):
        """Insert a node into Neo4j with hash as metadata, not as a separate node."""
        try:
            query = f"""
            MERGE (n:{label} {{title: $title}})
            SET n.hash = $hash, n += $properties
            """
            with self.driver.session() as session:
                session.run(query, title=properties["title"], hash=properties["hash"], properties=properties)
                return True
        except Exception as e:
            logger.error(f"Error adding {label} node: {e}")
            return False

    def add_relationship(self, node1_title, node2_title, relation, score=None):
        """Insert relationships (CONTAINS or SIMILAR_TO)."""
        try:
            query = f"""
            MATCH (a {{title: $node1_title}}), (b {{title: $node2_title}})
            MERGE (a)-[r:{relation}]->(b)
            """
            if score is not None:
                query += " SET r.score = $score"
            
            with self.driver.session() as session:
                session.run(query, node1_title=node1_title, node2_title=node2_title, score=score)
                return True
        except Exception as e:
            logger.error(f"Error adding relationship: {e}")
            return False

    def compute_similarity(self, emb1, emb2):
        """Compute cosine similarity between two embeddings."""
        return cosine_similarity([emb1], [emb2])[0][0]

    def find_similar_nodes(self, node_list, threshold=0.8):
        """Find similar chapters, sections, and subsections across documents."""
        similar_pairs = []
        if len(node_list) < 2:
            logger.warning(f"Not enough nodes to compare (only {len(node_list)} nodes)")
            return similar_pairs
        
        try:
            for (node1, emb1), (node2, emb2) in [(n1, n2) for n1 in node_list.items() for n2 in node_list.items() if n1 != n2]:
                similarity = self.compute_similarity(emb1, emb2)
                if similarity >= threshold:
                    similar_pairs.append((node1, node2, similarity))
        except Exception as e:
            logger.error(f"Error computing similarity: {e}")
        
        return similar_pairs

    def process_json(self, json_path):
        """Process the JSON file and store the data in Neo4j."""
        try:
            with open(json_path, "r") as f:
                data = json.load(f)

            document_embeddings = {}
            chapter_embeddings = {}
            section_embeddings = {}
            subsection_embeddings = {}
            
            doc_counter = 0
            chapter_counter = 0
            section_counter = 0
            subsection_counter = 0

            # Insert Documents, Chapters, Sections, Subsections
            for doc_type, doc_files in data.items():
                logger.info(f"Processing document type: {doc_type} with {len(doc_files)} documents")
                
                for doc_name, doc_data in doc_files.items():
                    try:
                        doc_hash = doc_data.get("hash_document")
                        if not doc_hash:
                            logger.warning(f"Skipping document with missing hash: {doc_name}")
                            continue
                            
                        doc_title = doc_data.get("title", doc_name)
                        
                        # Get chapter content for document embedding
                        chapters = doc_data.get("chapters", [])
                        if not chapters:
                            logger.warning(f"Document has no chapters: {doc_title}")
                            doc_text = doc_title  # Use title as fallback
                        else:
                            # Combine content from chapters
                            chapter_contents = []
                            for chap in chapters:
                                if "content" in chap and chap["content"]:
                                    chapter_contents.append(chap["content"])
                            
                            if not chapter_contents:
                                logger.warning(f"No content found in chapters for document: {doc_title}")
                                doc_text = doc_title  # Use title as fallback
                            else:
                                doc_text = " ".join(chapter_contents)
                        
                        # Generate document embedding
                        doc_embedding = embedding_function.embed_query(doc_text)
                        document_embeddings[doc_title] = doc_embedding

                        # Add document node
                        if self.add_node("Document", {"title": doc_title, "hash": doc_hash, "type": doc_type}):
                            doc_counter += 1
                        
                        # Process chapters
                        for chapter in chapters:
                            try:
                                chap_hash = chapter.get("hash_chapter")
                                if not chap_hash:
                                    logger.warning(f"Skipping chapter with missing hash in document: {doc_title}")
                                    continue
                                    
                                chap_title = chapter.get("title", f"Chapter in {doc_title}")
                                chap_text = chapter.get("content", "")
                                
                                if not chap_text:
                                    logger.warning(f"Chapter has no content: {chap_title}")
                                    chap_text = chap_title  # Use title as fallback
                                
                                # Generate chapter embedding
                                chap_embedding = embedding_function.embed_query(chap_text)
                                chapter_embeddings[chap_title] = chap_embedding

                                # Add chapter node
                                if self.add_node("Chapter", {"title": chap_title, "hash": chap_hash}):
                                    chapter_counter += 1
                                
                                # Add document-chapter relationship
                                self.add_relationship(doc_title, chap_title, "CONTAINS")

                                # Process sections
                                sections = chapter.get("sections", [])
                                if not sections:
                                    logger.info(f"Chapter has no sections: {chap_title}")
                                    continue
                                    
                                for section in sections:
                                    try:
                                        # First check for proper hash_section, then check for hash_subsection
                                        sec_hash = section.get("hash_section")
                                        if not sec_hash:
                                            # If hash_section is missing, try using hash_subsection if available
                                            sec_hash = section.get("hash_subsection")
                                            if sec_hash:
                                                logger.warning(f"Section using hash_subsection instead of hash_section: {section.get('title', 'Unknown')}")
                                            else:
                                                # If no hash is available, generate one based on available identifiers
                                                sec_title = section.get("title", "")
                                                sec_number = section.get("number", "")
                                                sec_content = section.get("content", "")[:100]  # Use first 100 chars of content
                                                # Combine available identifiers to generate a hash
                                                hash_source = f"{chap_title}|{sec_title}|{sec_number}|{sec_content}"
                                                sec_hash = hashlib.md5(hash_source.encode()).hexdigest()
                                                logger.warning(f"Generated hash for section without hash: {sec_title}")
                                        
                                        if not sec_hash:
                                            logger.warning(f"Skipping section with missing hash in chapter: {chap_title}")
                                            continue
                                            
                                        sec_title = section.get("title", f"Section in {chap_title}")
                                        sec_text = section.get("content", "")
                                        
                                        if not sec_text:
                                            logger.warning(f"Section has no content: {sec_title}")
                                            sec_text = sec_title  # Use title as fallback
                                        
                                        # Generate section embedding
                                        sec_embedding = embedding_function.embed_query(sec_text)
                                        section_embeddings[sec_title] = sec_embedding

                                        # Add section node
                                        if self.add_node("Section", {"title": sec_title, "hash": sec_hash}):
                                            section_counter += 1
                                        
                                        # Add chapter-section relationship
                                        self.add_relationship(chap_title, sec_title, "CONTAINS")

                                        # Process subsections (sublevels) if they exist
                                        sublevels = section.get("sublevels", [])
                                        if not sublevels:
                                            logger.info(f"Section has no sublevels: {sec_title}")
                                            continue
                                            
                                        for subsection in sublevels:
                                            try:
                                                sub_hash = subsection.get("hash_subsection")
                                                if not sub_hash:
                                                    # If no hash is available, generate one based on available identifiers
                                                    sub_number = subsection.get("number", "")
                                                    sub_content = subsection.get("content", "")[:100]  # Use first 100 chars of content
                                                    
                                                    # Combine available identifiers to generate a hash
                                                    hash_source = f"{sec_hash}|{sub_number}|{sub_content}"
                                                    sub_hash = hashlib.md5(hash_source.encode()).hexdigest()
                                                    logger.warning(f"Generated hash for subsection without hash: {sub_number}")
                                                
                                                if not sub_hash:
                                                    logger.warning(f"Skipping subsection with missing hash in section: {sec_title}")
                                                    continue
                                                    
                                                # Get a better subsection title when the title field is empty
                                                sub_title = subsection.get("title", "")
                                                if not sub_title.strip():
                                                    # Try to use the number and content as title
                                                    sub_number = subsection.get("number", "")
                                                    sub_content = subsection.get("content", "")
                                                    if sub_content:
                                                        # Use the first line of content (up to 50 chars)
                                                        sub_content_title = sub_content.split('\n')[0][:50]
                                                        if sub_number:
                                                            sub_title = f"{sub_number}: {sub_content_title}"
                                                        else:
                                                            sub_title = sub_content_title
                                                    else:
                                                        # Fallback to a generic title
                                                        sub_title = f"Subsection in {sec_title}"
                                                
                                                sub_text = subsection.get("content", "")
                                                
                                                if not sub_text:
                                                    logger.warning(f"Subsection has no content: {sub_title}")
                                                    sub_text = sub_title  # Use title as fallback
                                                
                                                # Generate subsection embedding
                                                sub_embedding = embedding_function.embed_query(sub_text)
                                                subsection_embeddings[sub_title] = sub_embedding

                                                # Add subsection node
                                                if self.add_node("Subsection", {"title": sub_title, "hash": sub_hash}):
                                                    subsection_counter += 1
                                                
                                                # Add section-subsection relationship
                                                self.add_relationship(sec_title, sub_title, "CONTAINS")
                                            except Exception as e:
                                                logger.error(f"Error processing subsection in section {sec_title}: {e}")
                                    except Exception as e:
                                        logger.error(f"Error processing section in chapter {chap_title}: {e}")
                            except Exception as e:
                                logger.error(f"Error processing chapter in document {doc_title}: {e}")
                    except Exception as e:
                        logger.error(f"Error processing document {doc_name}: {e}")

            logger.info(f"Added {doc_counter} documents, {chapter_counter} chapters, {section_counter} sections, and {subsection_counter} subsections")

            # Compute `SIMILAR_TO` Relationships
            logger.info("Computing similarity relationships")
            
            if document_embeddings:
                logger.info(f"Finding similar documents among {len(document_embeddings)} documents...")
                similar_docs = self.find_similar_nodes(document_embeddings, threshold=0.8)
                logger.info(f"Found {len(similar_docs)} similar document pairs")

                for d1, d2, score in similar_docs:
                    self.add_relationship(d1, d2, "SIMILAR_TO", score)
            
            if chapter_embeddings:
                logger.info(f"Finding similar chapters among {len(chapter_embeddings)} chapters...")
                similar_chapters = self.find_similar_nodes(chapter_embeddings, threshold=0.8)
                logger.info(f"Found {len(similar_chapters)} similar chapter pairs")

                for c1, c2, score in similar_chapters:
                    self.add_relationship(c1, c2, "SIMILAR_TO", score)
            
            if section_embeddings:
                logger.info(f"Finding similar sections among {len(section_embeddings)} sections...")
                similar_sections = self.find_similar_nodes(section_embeddings, threshold=0.8)
                logger.info(f"Found {len(similar_sections)} similar section pairs")

                for s1, s2, score in similar_sections:
                    self.add_relationship(s1, s2, "SIMILAR_TO", score)
            
            if subsection_embeddings:
                logger.info(f"Finding similar subsections among {len(subsection_embeddings)} subsections...")
                similar_subsections = self.find_similar_nodes(subsection_embeddings, threshold=0.8)
                logger.info(f"Found {len(similar_subsections)} similar subsection pairs")

                for sub1, sub2, score in similar_subsections:
                    self.add_relationship(sub1, sub2, "SIMILAR_TO", score)

            logger.info("Neo4j knowledge graph successfully updated.")
            return True
        except Exception as e:
            logger.error(f"Error processing JSON file {json_path}: {e}")
            return False

if __name__ == "__main__":
    print("Starting knowledge graph creation...")
    
    # Get Neo4j connection details from environment variables
    neo4j_uri = os.environ.get("NEO4J_URI", "neo4j://neo4j:7687")
    neo4j_user = os.environ.get("NEO4J_USER", "neo4j")
    neo4j_password = os.environ.get("NEO4J_PASSWORD", "password")
    
    logger.info(f"Connecting to Neo4j at {neo4j_uri}...")
    
    # JSON files to process
    json_files = [
        "/app/combined_output_3.json",
        "/app/combined_output_3_gs.json",
        "/app/combined_output_3_airforce.json"
    ]
    
    try:
        # Create knowledge graph
        kg = KnowledgeGraph(neo4j_uri, neo4j_user, neo4j_password)
        
        # Process each JSON file
        success_count = 0
        for json_file in json_files:
            if os.path.exists(json_file):
                logger.info(f"Processing {json_file}...")
                if kg.process_json(json_file):
                    success_count += 1
            else:
                logger.warning(f"Warning: {json_file} not found")
        
        # Close connection
        kg.close()
        logger.info(f"Knowledge graph creation completed. Successfully processed {success_count}/{len(json_files)} files")
        
    except Exception as e:
        logger.error(f"Error creating knowledge graph: {str(e)}")
