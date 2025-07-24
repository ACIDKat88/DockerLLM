import os
import json
import logging
import uuid
import numpy as np
import argparse
import time
from tqdm import tqdm
from embedd_class import customembedding
from db_utils import connect_db
from psycopg2.extras import execute_values

# Mapping of categories to PDF folder paths.
pdf_folder_map = {
    "airforce": "/home/cm36/Updated-LLM-Project/J1_corpus/cleaned/air_force",
    "stratcom": "/home/cm36/Updated-LLM-Project/J1_corpus/cleaned/stratcom",
    "single": "/home/cm36/Updated-LLM-Project/J1_corpus/cleaned/single"
}

def construct_pdf_path(category, document_title):
    """
    Constructs the PDF path based on the category and document title.
    """
    pdf_folder = pdf_folder_map.get(category.lower(), "")
    if pdf_folder and document_title:
        pdf_filename = f"{document_title}.pdf"
        return os.path.join(pdf_folder, pdf_filename)
    return ""

def filter_metadata(metadata):
    """
    Remove any keys with a None value from metadata.
    """
    return {k: v for k, v in metadata.items() if v is not None}

# Set up logging.
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Default JSON files if not specified via command line
DEFAULT_JSON_FILES = {
    "/app/combined_output_3.json": "document_embeddings_combined",
    "/app/combined_output_3_gs.json": "document_embeddings_gs",
    "/app/combined_output_3_airforce.json": "document_embeddings_airforce"
}

# For backward compatibility
DEFAULT_HASH_MAPPING_FILE = "/app/combined_output_3_airforce.json"
DEFAULT_TABLE_NAME = "document_embeddings"

# Set up the embedding model
embedding_model = customembedding("mixedbread-ai/mxbai-embed-large-v1")

# Default batch size - this will be configurable via command line
BATCH_SIZE = 100

# Function to handle embedding conversion
def prepare_embedding(embedding):
    """
    Ensure embedding is in the correct format for pgvector.
    Handles both numpy arrays and lists.
    """
    if isinstance(embedding, np.ndarray):
        return embedding.tolist()
    return embedding  # Return as is if already a list

# Batch embed texts for better throughput
def batch_embed_texts(texts):
    """
    Embed multiple texts at once for better throughput.
    
    Args:
        texts: List of text strings to embed
        
    Returns:
        List of embeddings
    """
    try:
        # If the embedding model supports batch embedding
        if hasattr(embedding_model, "embed_batch"):
            return embedding_model.embed_batch(texts)
        
        # Otherwise, embed each text individually but in a batch
        return [embedding_model(text) for text in texts]
    except Exception as e:
        logger.error(f"Error in batch embedding: {e}")
        # Fall back to individual embedding
        embeddings = []
        for text in texts:
            try:
                embedding = embedding_model(text)
                embeddings.append(embedding)
            except Exception as text_e:
                logger.error(f"Error embedding text: {text_e}")
                # Use a zero embedding as fallback
                embeddings.append(np.zeros(768))
        return embeddings

# Function to count total number of nodes for progress bar
def count_nodes(data):
    """
    Count the total number of document, chapter, section, and subsection nodes
    in the JSON structure.
    """
    count = 0
    
    def recursive_count(node):
        nonlocal count
        if isinstance(node, dict):
            # Count a node if it has any of the hash identifiers
            if any(key in node for key in ['hash_document', 'hash_chapter', 'hash_section', 'hash_subsection']):
                count += 1
            # Recurse into nested dictionaries or lists
            for key, value in node.items():
                if isinstance(value, (dict, list)):
                    recursive_count(value)
        elif isinstance(node, list):
            for item in node:
                recursive_count(item)
    
    recursive_count(data)
    return count

def setup_database(table_name):
    """Initialize the database with the proper schema for vector storage."""
    conn = connect_db()
    if not conn:
        logger.error("Failed to connect to the database")
        return False
    
    cursor = conn.cursor()
    try:
        # Create pgvector extension if it doesn't exist
        cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")
        
        # Create the table for storing documents and embeddings
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                id TEXT PRIMARY KEY,
                content TEXT,
                embedding vector(1024),
                type TEXT,
                hash_document TEXT,
                document_title TEXT,
                category TEXT,
                pdf_path TEXT,
                hash_chapter TEXT,
                chapter_title TEXT,
                chapter_number TEXT,
                hash_section TEXT,
                section_title TEXT,
                section_number TEXT,
                section_page_number TEXT,
                hash_subsection TEXT,
                subsection_title TEXT,
                subsection_number TEXT,
                subsection_page_number TEXT,
                composite_id TEXT
            )
        """)
        
        # Create an index for faster vector similarity searches
        cursor.execute(f"""
            CREATE INDEX IF NOT EXISTS {table_name}_embedding_idx 
            ON {table_name} 
            USING ivfflat (embedding vector_l2_ops)
        """)
        
        # Create hash indices for faster lookups
        cursor.execute(f"""
            CREATE INDEX IF NOT EXISTS {table_name}_hash_document_idx
            ON {table_name}(hash_document)
            WHERE hash_document IS NOT NULL
        """)
        
        cursor.execute(f"""
            CREATE INDEX IF NOT EXISTS {table_name}_hash_chapter_idx
            ON {table_name}(hash_chapter)
            WHERE hash_chapter IS NOT NULL
        """)
        
        cursor.execute(f"""
            CREATE INDEX IF NOT EXISTS {table_name}_hash_section_idx
            ON {table_name}(hash_section)
            WHERE hash_section IS NOT NULL
        """)
        
        cursor.execute(f"""
            CREATE INDEX IF NOT EXISTS {table_name}_hash_subsection_idx
            ON {table_name}(hash_subsection)
            WHERE hash_subsection IS NOT NULL
        """)
        
        cursor.execute(f"""
            CREATE INDEX IF NOT EXISTS {table_name}_type_idx
            ON {table_name}(type)
        """)
        
        conn.commit()
        logger.info(f"Database setup completed successfully for table {table_name}")
        return True
    except Exception as e:
        conn.rollback()
        logger.error(f"Error setting up database: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def flush_batch(batch_data, table_name, added_ids, added_docs, added_chapters, added_sections, added_subsections):
    """Flush the current batch of embeddings to PostgreSQL."""
    if not batch_data:
        return added_ids, added_docs, added_chapters, added_sections, added_subsections
    
    conn = connect_db()
    if not conn:
        logger.error("Failed to connect to the database for batch insertion")
        return added_ids, added_docs, added_chapters, added_sections, added_subsections
    
    cursor = conn.cursor()
    try:
        start_time = time.time()
        
        # Insert data using execute_values for efficiency
        # Use ON CONFLICT to update records if they already exist and content is different
        execute_values(cursor, f"""
            INSERT INTO {table_name} (
                id, content, embedding, type, hash_document, document_title, 
                category, pdf_path, hash_chapter, chapter_title, chapter_number,
                hash_section, section_title, section_number, section_page_number,
                hash_subsection, subsection_title, subsection_number, 
                subsection_page_number, composite_id
            ) VALUES %s
            ON CONFLICT (id) DO UPDATE SET
                content = EXCLUDED.content,
                embedding = EXCLUDED.embedding,
                document_title = COALESCE(EXCLUDED.document_title, {table_name}.document_title),
                category = COALESCE(EXCLUDED.category, {table_name}.category),
                pdf_path = COALESCE(EXCLUDED.pdf_path, {table_name}.pdf_path),
                chapter_title = COALESCE(EXCLUDED.chapter_title, {table_name}.chapter_title),
                chapter_number = COALESCE(EXCLUDED.chapter_number, {table_name}.chapter_number),
                section_title = COALESCE(EXCLUDED.section_title, {table_name}.section_title),
                section_number = COALESCE(EXCLUDED.section_number, {table_name}.section_number),
                section_page_number = COALESCE(EXCLUDED.section_page_number, {table_name}.section_page_number),
                subsection_title = COALESCE(EXCLUDED.subsection_title, {table_name}.subsection_title),
                subsection_number = COALESCE(EXCLUDED.subsection_number, {table_name}.subsection_number),
                subsection_page_number = COALESCE(EXCLUDED.subsection_page_number, {table_name}.subsection_page_number)
            WHERE {table_name}.content != EXCLUDED.content
        """, batch_data)
        
        conn.commit()
        
        end_time = time.time()
        batch_time = end_time - start_time
        
        # Update tracking of added IDs
        for item in batch_data:
            idx = item[0]  # id is the first column
            added_ids.add(idx)
            node_type = item[3]  # type is the fourth column
            if node_type == "document":
                added_docs.add(idx)
            elif node_type == "chapter":
                added_chapters.add(idx)
            elif node_type == "section":
                added_sections.add(idx)
            elif node_type == "subsection":
                added_subsections.add(idx)
        
        logger.info(f"Flushed {len(batch_data)} embeddings to PostgreSQL table {table_name} in {batch_time:.2f} seconds. Total added/updated: {len(added_ids)}")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error adding batch to PostgreSQL: {e}")
    finally:
        cursor.close()
        conn.close()
    
    return added_ids, added_docs, added_chapters, added_sections, added_subsections

def collect_batch_data(nodes, category_prefix, local_meta, all_json_ids, json_docs, json_chapters, json_sections, json_subsections, composite_id_occurrences):
    """
    Collect batch data for the given nodes.
    
    Args:
        nodes: List of nodes to process
        category_prefix: Prefix to add to the content based on category
        local_meta: Metadata for the nodes
        all_json_ids, json_docs, etc.: Sets to track IDs
        composite_id_occurrences: Dict to track ID occurrences
    
    Returns:
        List of tuples with data for batch insertion
    """
    batch_items = []
    contents = []
    
    for node in nodes:
        node_type = node.get("type")
        unique_id = node.get("unique_id")
        
        # Add to tracking sets
        all_json_ids.add(unique_id)
        if node_type == "document":
            json_docs.add(unique_id)
        elif node_type == "chapter":
            json_chapters.add(unique_id)
        elif node_type == "section":
            json_sections.add(unique_id)
        elif node_type == "subsection":
            json_subsections.add(unique_id)
        
        # Create enhanced content with titles and category-specific prefix
        doc_title = local_meta.get("document_title", '')
        content_parts = [f"{category_prefix}Document: {doc_title}"]
        
        if node_type != "document":
            chapter_title = local_meta.get("chapter_title", '')
            content_parts.append(f"Chapter: {chapter_title}")
            
            if node_type != "chapter":
                section_title = local_meta.get("section_title", '')
                content_parts.append(f"Section: {section_title}")
                
                if node_type == "subsection":
                    subsection_title = local_meta.get("subsection_title", '')
                    content_parts.append(f"Subsection: {subsection_title}")
        
        # Get the original content
        raw_content = node.get('content') or node.get('title') or "No content"
        content_parts.append("\n\n" + raw_content)
        
        # Join all content parts
        content = "\n".join(content_parts)
        contents.append(content)
        
        # Add metadata based on node type
        item = [
            unique_id,  # Will be replaced with actual content later
            content,
            None,  # Will be replaced with embedding
            node_type,
            local_meta.get("hash_document"),
            local_meta.get("document_title"),
            local_meta.get("category"),
            local_meta.get("pdf_path"),
            None,  # hash_chapter
            None,  # chapter_title
            None,  # chapter_number
            None,  # hash_section
            None,  # section_title
            None,  # section_number
            None,  # section_page_number
            None,  # hash_subsection
            None,  # subsection_title
            None,  # subsection_number
            None,  # subsection_page_number
            unique_id  # composite_id
        ]
        
        # Add chapter metadata if applicable
        if node_type != "document":
            item[8] = local_meta.get("hash_chapter")
            item[9] = local_meta.get("chapter_title")
            item[10] = local_meta.get("chapter_number")
            
            # Add section metadata if applicable
            if node_type != "chapter":
                item[11] = local_meta.get("hash_section")
                item[12] = local_meta.get("section_title")
                item[13] = local_meta.get("section_number")
                item[14] = local_meta.get("section_page_number")
                
                # Add subsection metadata if applicable
                if node_type == "subsection":
                    item[15] = local_meta.get("hash_subsection")
                    item[16] = local_meta.get("subsection_title")
                    item[17] = local_meta.get("subsection_number")
                    item[18] = local_meta.get("subsection_page_number")
        
        batch_items.append(item)
    
    # Generate embeddings for all contents at once
    embeddings = batch_embed_texts(contents)
    
    # Update batch items with embeddings
    batch_data = []
    for i, item in enumerate(batch_items):
        item[2] = prepare_embedding(embeddings[i])
        batch_data.append(tuple(item))
    
    return batch_data

def process_node(node, pbar, batch_data, table_name, all_json_ids, json_docs, json_chapters, json_sections, json_subsections,
                added_ids, added_docs, added_chapters, added_sections, added_subsections,
                composite_id_occurrences, cur_doc=None, cur_chapter=None, cur_section=None, parent_meta=None, batch_size=BATCH_SIZE):
    """
    Recursively traverse the JSON structure.
    When a node contains a hash, build a composite ID, ensure uniqueness,
    and enrich metadata (ensuring 'hash_document' is always present).
    Queue the node for embedding and update the global progress bar.
    """
    if parent_meta is None:
        parent_meta = {}

    # Determine category-specific prefixes based on table name
    category_prefix = ""
    if "airforce" in table_name:
        category_prefix = "air force: "
    elif "gs" in table_name:
        category_prefix = "civilian general schedule gs: "

    # Collect nodes for batch processing
    nodes_to_process = []

    if isinstance(node, dict):
        # Start with the parent's metadata.
        local_meta = parent_meta.copy()
        # Ensure hash_document is inherited if already set.
        if cur_doc is not None and "hash_document" not in local_meta:
            local_meta["hash_document"] = cur_doc

        unique_id = None

        # Document level
        if 'hash_document' in node:
            cur_doc = node['hash_document']
            local_meta.update({
                "type": "document",
                "hash_document": node.get("hash_document"),
                "document_title": node.get("title")
            })
            if "category" in node and "title" in node:
                local_meta["category"] = node["category"]
                local_meta["pdf_path"] = construct_pdf_path(node["category"], node["title"])
            base_id = cur_doc
            
            # Get unique ID for this document
            if base_id in composite_id_occurrences:
                composite_id_occurrences[base_id] += 1
                unique_id = f"{base_id}-{composite_id_occurrences[base_id]}"
            else:
                composite_id_occurrences[base_id] = 0
                unique_id = base_id
            
            # Prepare node for batch processing
            node_data = node.copy()
            node_data["type"] = "document"
            node_data["unique_id"] = unique_id
            nodes_to_process.append(node_data)
            pbar.update(1)
        
        # Chapter level
        if 'hash_chapter' in node:
            cur_chapter = node['hash_chapter']
            # Inherit hash_document from parent.
            if cur_doc is not None:
                local_meta["hash_document"] = cur_doc
            local_meta.update({
                "type": "chapter",
                "hash_chapter": node.get("hash_chapter"),
                "chapter_title": node.get("title"),
                "chapter_number": node.get("number")
            })
            base_id = "-".join(filter(None, [cur_doc, cur_chapter]))
            
            # Get unique ID for this chapter
            if base_id in composite_id_occurrences:
                composite_id_occurrences[base_id] += 1
                unique_id = f"{base_id}-{composite_id_occurrences[base_id]}"
            else:
                composite_id_occurrences[base_id] = 0
                unique_id = base_id
            
            # Prepare node for batch processing
            node_data = node.copy()
            node_data["type"] = "chapter"
            node_data["unique_id"] = unique_id
            nodes_to_process.append(node_data)
            pbar.update(1)
        
        # Section level
        if 'hash_section' in node:
            cur_section = node['hash_section']
            if cur_doc is not None:
                local_meta["hash_document"] = cur_doc
            local_meta.update({
                "type": "section",
                "hash_section": node.get("hash_section"),
                "section_title": node.get("title"),
                "section_number": node.get("number"),
                "section_page_number": node.get("page_number")
            })
            base_id = "-".join(filter(None, [cur_doc, cur_chapter, cur_section]))
            
            # Get unique ID for this section
            if base_id in composite_id_occurrences:
                composite_id_occurrences[base_id] += 1
                unique_id = f"{base_id}-{composite_id_occurrences[base_id]}"
            else:
                composite_id_occurrences[base_id] = 0
                unique_id = base_id
            
            # Prepare node for batch processing
            node_data = node.copy()
            node_data["type"] = "section"
            node_data["unique_id"] = unique_id
            nodes_to_process.append(node_data)
            pbar.update(1)
        
        # Subsection level
        if 'hash_subsection' in node:
            if cur_doc is not None:
                local_meta["hash_document"] = cur_doc
            sub_hash = node['hash_subsection']
            local_meta.update({
                "type": "subsection",
                "hash_subsection": node.get("hash_subsection"),
                "subsection_title": node.get("title"),
                "subsection_number": node.get("number"),
                "subsection_page_number": node.get("page_number")
            })
            base_id = "-".join(filter(None, [cur_doc, cur_chapter, cur_section, sub_hash]))
            
            # Get unique ID for this subsection
            if base_id in composite_id_occurrences:
                composite_id_occurrences[base_id] += 1
                unique_id = f"{base_id}-{composite_id_occurrences[base_id]}"
            else:
                composite_id_occurrences[base_id] = 0
                unique_id = base_id
            
            # Prepare node for batch processing
            node_data = node.copy()
            node_data["type"] = "subsection"
            node_data["unique_id"] = unique_id
            nodes_to_process.append(node_data)
            pbar.update(1)

        # Process collected nodes in batch
        if nodes_to_process:
            new_batch_data = collect_batch_data(
                nodes_to_process, 
                category_prefix, 
                local_meta, 
                all_json_ids, 
                json_docs, 
                json_chapters, 
                json_sections, 
                json_subsections, 
                composite_id_occurrences
            )
            batch_data.extend(new_batch_data)
            
        if len(batch_data) >= batch_size:
            added_ids, added_docs, added_chapters, added_sections, added_subsections = flush_batch(
                batch_data, table_name, added_ids, added_docs, added_chapters, added_sections, added_subsections
            )
            batch_data.clear()
            
        # Recurse into nested dictionaries or lists.
        for key, value in node.items():
            if isinstance(value, (dict, list)):
                process_node(value, pbar, batch_data, table_name, all_json_ids, json_docs, json_chapters, json_sections, json_subsections,
                            added_ids, added_docs, added_chapters, added_sections, added_subsections,
                            composite_id_occurrences, cur_doc, cur_chapter, cur_section, local_meta, batch_size)
    elif isinstance(node, list):
        for item in node:
            process_node(item, pbar, batch_data, table_name, all_json_ids, json_docs, json_chapters, json_sections, json_subsections,
                        added_ids, added_docs, added_chapters, added_sections, added_subsections, 
                        composite_id_occurrences, cur_doc, cur_chapter, cur_section, parent_meta, batch_size)
            
    return batch_data

def process_json_file(json_file_path, table_name, batch_size=BATCH_SIZE):
    """Process a single JSON file and store embeddings in the specified table."""
    # Sets to track composite hash IDs found in the JSON.
    all_json_ids = set()
    json_docs = set()
    json_chapters = set()
    json_sections = set()
    json_subsections = set()

    # Sets to track composite IDs that are successfully added to PostgreSQL.
    added_ids = set()
    added_docs = set()
    added_chapters = set()
    added_sections = set()
    added_subsections = set()

    # Dictionary to track occurrences of composite IDs.
    composite_id_occurrences = {}

    # Batch buffers for insertion.
    batch_data = []
    
    logger.info(f"Processing JSON file: {json_file_path}")
    logger.info(f"Target table: {table_name}")
    logger.info(f"Using batch size: {batch_size}")
    
    # Setup the database first
    if not setup_database(table_name):
        logger.error("Database setup failed. Exiting.")
        return
        
    start_time = time.time()
    
    with open(json_file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    logger.info(f"Loaded JSON from {json_file_path} in {time.time() - start_time:.2f} seconds.")
    
    # Count total nodes for progress bar
    logger.info("Counting total nodes...")
    total_nodes = count_nodes(data)
    logger.info(f"Found {total_nodes} total nodes to process")
    
    # Create progress bar with total
    pbar = tqdm(total=total_nodes, desc=f"Processing {os.path.basename(json_file_path)}", unit="node")
    
    # Determine JSON structure.
    if isinstance(data, dict):
        first_val = next(iter(data.values()))
        if isinstance(first_val, dict) and first_val.get("hash_document", "").strip():
            logger.info("Detected top-level document structure.")
            batch_data = process_node(data, pbar, batch_data, table_name, all_json_ids, json_docs, json_chapters, json_sections, json_subsections,
                                   added_ids, added_docs, added_chapters, added_sections, added_subsections, composite_id_occurrences, batch_size=batch_size)
        else:
            logger.info("Detected top-level category structure.")
            for category, docs in data.items():
                if isinstance(docs, dict):
                    for doc_name, doc_val in docs.items():
                        if isinstance(doc_val, dict):
                            doc_val["category"] = category
                            if "title" in doc_val:
                                doc_val["pdf_path"] = construct_pdf_path(category, doc_val["title"])
                            batch_data = process_node(doc_val, pbar, batch_data, table_name, all_json_ids, json_docs, json_chapters, json_sections, json_subsections,
                                                   added_ids, added_docs, added_chapters, added_sections, added_subsections, composite_id_occurrences, batch_size=batch_size)
                elif isinstance(docs, list):
                    for doc_val in docs:
                        if isinstance(doc_val, dict):
                            doc_val["category"] = category
                            if "title" in doc_val:
                                doc_val["pdf_path"] = construct_pdf_path(category, doc_val["title"])
                            batch_data = process_node(doc_val, pbar, batch_data, table_name, all_json_ids, json_docs, json_chapters, json_sections, json_subsections,
                                                   added_ids, added_docs, added_chapters, added_sections, added_subsections, composite_id_occurrences, batch_size=batch_size)
    # Flush any remaining embeddings
    if batch_data:
        added_ids, added_docs, added_chapters, added_sections, added_subsections = flush_batch(
            batch_data, table_name, added_ids, added_docs, added_chapters, added_sections, added_subsections
        )
        batch_data.clear()
        
    pbar.close()

    end_time = time.time()
    logger.info(f"Finished embedding nodes from {json_file_path} into PostgreSQL table {table_name} in {end_time - start_time:.2f} seconds.")
    logger.info(f"Total unique composite IDs extracted from JSON: {len(all_json_ids)}")
    logger.info(f"Total unique composite IDs added to PostgreSQL: {len(added_ids)}")
    logger.info(f"Documents: {len(added_docs)}, Chapters: {len(added_chapters)}, Sections: {len(added_sections)}, Subsections: {len(added_subsections)}")
    
    # Generate a discrepancy report.
    missing_ids = all_json_ids - added_ids
    logger.info(f"Missing composite IDs (present in JSON but not in PostgreSQL): {len(missing_ids)}")
    if missing_ids and len(missing_ids) < 20:  # Only show details if there are a few missing IDs
        missing_doc_ids = sorted(i for i in missing_ids if i in json_docs)
        missing_chap_ids = sorted(i for i in missing_ids if i in json_chapters)
        missing_sec_ids = sorted(i for i in missing_ids if i in json_sections)
        missing_subsec_ids = sorted(i for i in missing_ids if i in json_subsections)
        if missing_doc_ids:
            logger.info(f"Missing document hashes ({len(missing_doc_ids)}):")
            for i in missing_doc_ids:
                logger.info(f" - {i}")
        if missing_chap_ids:
            logger.info(f"Missing chapter hashes ({len(missing_chap_ids)}):")
            for i in missing_chap_ids:
                logger.info(f" - {i}")
        if missing_sec_ids:
            logger.info(f"Missing section hashes ({len(missing_sec_ids)}):")
            for i in missing_sec_ids:
                logger.info(f" - {i}")
        if missing_subsec_ids:
            logger.info(f"Missing subsection hashes ({len(missing_subsec_ids)}):")
            for i in missing_subsec_ids:
                logger.info(f" - {i}")
    elif missing_ids:
        logger.info(f"Too many missing IDs to display ({len(missing_ids)}). Check the logs for details.")
    else:
        logger.info(f"No discrepancies found. All JSON hashes are present in PostgreSQL table {table_name}.")
    
    return all_json_ids, added_ids

def verify_hash_documents(table_name, expected_hash_docs):
    """Verify that expected hash documents are present in the table."""
    conn = connect_db()
    if not conn:
        logger.error("Failed to connect to the database")
        return
        
    cursor = conn.cursor()
    try:
        # Create a temporary table for bulk checking
        cursor.execute(f"""
            CREATE TEMP TABLE temp_hash_docs (
                hash_document TEXT PRIMARY KEY
            ) ON COMMIT DROP
        """)
        
        # Insert all expected hashes
        execute_values(cursor, 
            "INSERT INTO temp_hash_docs (hash_document) VALUES %s ON CONFLICT DO NOTHING",
            [(h,) for h in expected_hash_docs]
        )
        
        # Check all hashes at once with a JOIN
        cursor.execute(f"""
            SELECT t.hash_document, 
                   CASE WHEN d.hash_document IS NULL THEN 'Missing' ELSE 'Present' END as status,
                   COUNT(d.id) as count
            FROM temp_hash_docs t
            LEFT JOIN {table_name} d ON t.hash_document = d.hash_document
            GROUP BY t.hash_document, status
            ORDER BY status DESC, t.hash_document
        """)
        
        results = cursor.fetchall()
        
        # Print summary
        missing = [r[0] for r in results if r[1] == 'Missing']
        present = sum(r[2] for r in results if r[1] == 'Present')
        
        if missing:
            logger.warning(f"Missing {len(missing)} hash documents in table {table_name}:")
            for hash_doc in missing:
                logger.warning(f" - {hash_doc}")
        else:
            logger.info(f"All {len(expected_hash_docs)} expected hash documents are present in table {table_name}")
            
        logger.info(f"Found {present} total documents with expected hash values")
    except Exception as e:
        logger.error(f"Error verifying hash documents: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Process JSON files and store embeddings in PostgreSQL with pgvector")
    parser.add_argument("--json_files", nargs="+", help="Path(s) to JSON file(s)")
    parser.add_argument("--table_names", nargs="+", help="PostgreSQL table name(s) to use")
    parser.add_argument("--config", help="Path to JSON config file with mapping of JSON files to table names")
    parser.add_argument("--batch_size", type=int, default=BATCH_SIZE, help=f"Batch size for database operations (default: {BATCH_SIZE})")
    
    args = parser.parse_args()
    
    # Set global batch size from command line
    BATCH_SIZE = args.batch_size
    logger.info(f"Using batch size: {BATCH_SIZE}")
    
    # Configuration for mapping JSON files to table names
    json_table_mapping = {}
    
    # Load from config file if provided
    if args.config:
        try:
            with open(args.config, 'r') as f:
                json_table_mapping = json.load(f)
            logger.info(f"Loaded configuration from {args.config}")
        except Exception as e:
            logger.error(f"Error loading config file: {e}")
            exit(1)
    # Otherwise use command line arguments
    elif args.json_files and args.table_names:
        if len(args.json_files) != len(args.table_names):
            logger.error("Number of JSON files must match number of table names")
            exit(1)
        json_table_mapping = dict(zip(args.json_files, args.table_names))
    # Default to a single file/table if nothing specified
    else:
        json_table_mapping = DEFAULT_JSON_FILES
        logger.info(f"No inputs specified, using defaults for all three JSON files:")
        for json_file, table_name in DEFAULT_JSON_FILES.items():
            logger.info(f"  - {json_file} -> {table_name}")
    
    # Process each JSON file in sequence
    overall_start_time = time.time()
    for json_file, table_name in json_table_mapping.items():
        file_start_time = time.time()
        process_json_file(json_file, table_name, BATCH_SIZE)
        file_end_time = time.time()
        logger.info(f"Processed {json_file} -> {table_name} in {file_end_time - file_start_time:.2f} seconds")
    
    overall_end_time = time.time()
    logger.info(f"All JSON files processed successfully in {overall_end_time - overall_start_time:.2f} seconds")
    
    # Verification: Check that every expected hash_document has been inherited
    # These are important document hashes that should be present in all processed data
    expected_hash_docs = [
        "1ef2222ae4a88763ee3bc7f1407568f8",
        "74e49f67b12bfc23a4b8b3c7a981076a",
        "76a084e6d1bef0ee4fc9685f94ac74f3",
        "2f16c794834af1e6797b04e13b6f16bb",
        "2170b7fd2d1e9dbf4fe1fcbe9de9e366",
        "bdc5452d803ed567aa1a87de06652ca1",
        "1d2175715d142564f5f8a30660e8d9bb",
        "9f165c527866e6f6a76d8c33ae534419",
        "4b446523991ede9b87c15cc0beb8e0dc",
        "be1df423066a900a0f5bb43a794f56d3",
        "9c4ee6ce779f27eb2be505bf50c20895",
        "4647cc3cefaa3ec8cc6e24e7dc3ae35b",
        "68f64451e8f4b3fca106832ff6424f10",
        "a41f5621361882c453fb60722534b091",
        "505781eb2e4a5d90f1db8b2d36dcb6e7",
    ]
    
    # Verify expected hashes in each table
    logger.info("Verifying expected hash documents in all tables...")
    for table_name in json_table_mapping.values():
        logger.info(f"Verifying hash documents in table {table_name}")
        verify_hash_documents(table_name, expected_hash_docs)

