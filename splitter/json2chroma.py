import os
import json
import logging
import uuid
import chromadb
from tqdm import tqdm
from embedd_class import customembedding

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

# Constants (update these paths if necessary)
HASH_MAPPING_FILE = "/home/cm36/Updated-LLM-Project/J1_corpus/json/kg/combined_output_3.json"
CHROMADB_PATH = "/home/cm36/Updated-LLM-Project/vectorstores/KG/chunk_size_mid"

# Set up the Chroma client and collection.
client = chromadb.PersistentClient(path=CHROMADB_PATH)
embedding_fn = customembedding("mixedbread-ai/mxbai-embed-large-v1")
collection = client.get_or_create_collection(name="kg2", embedding_function=embedding_fn)

# Batch configuration for Chroma inserts.
BATCH_SIZE = 100

# Global dictionary to track occurrences of composite IDs.
composite_id_occurrences = {}

def get_unique_id(base_id):
    """
    Returns a unique ID based on the given base_id.
    If the base_id has already been used, a suffix is appended.
    """
    if not base_id:
        return str(uuid.uuid4())
    if base_id in composite_id_occurrences:
        composite_id_occurrences[base_id] += 1
        return f"{base_id}-{composite_id_occurrences[base_id]}"
    else:
        composite_id_occurrences[base_id] = 0
        return base_id

# Sets to track composite hash IDs found in the JSON.
all_json_ids = set()
json_docs = set()
json_chapters = set()
json_sections = set()
json_subsections = set()

# Sets to track composite IDs that are successfully added to Chroma.
added_ids = set()
added_docs = set()
added_chapters = set()
added_sections = set()
added_subsections = set()

# Batch buffers for insertion.
batch_ids = []
batch_texts = []
batch_metadatas = []

# Create a single global progress bar.
pbar = tqdm(desc="Processing nodes", unit="node")

def flush_batch():
    """Flush the current batch of embeddings to the Chroma collection."""
    global batch_ids, batch_texts, batch_metadatas
    if not batch_ids:
        return
    try:
        collection.add(ids=batch_ids, documents=batch_texts, metadatas=batch_metadatas)
    except Exception as e:
        logger.error(f"Error adding batch: {e}")
        raise
    # Update tracking of added IDs.
    for idx, meta in zip(batch_ids, batch_metadatas):
        added_ids.add(idx)
        node_type = meta.get("type")
        if node_type == "document":
            added_docs.add(idx)
        elif node_type == "chapter":
            added_chapters.add(idx)
        elif node_type == "section":
            added_sections.add(idx)
        elif node_type == "subsection":
            added_subsections.add(idx)
    logger.info(f"Flushed {len(batch_ids)} embeddings to Chroma. Total added: {len(added_ids)}")
    batch_ids.clear()
    batch_texts.clear()
    batch_metadatas.clear()

def process_node(node, cur_doc=None, cur_chapter=None, cur_section=None, parent_meta=None):
    """
    Recursively traverse the JSON structure.
    When a node contains a hash, build a composite ID, ensure uniqueness,
    and enrich metadata (ensuring 'hash_document' is always present).
    Queue the node for embedding and update the global progress bar.
    """
    if parent_meta is None:
        parent_meta = {}

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
            unique_id = get_unique_id(base_id)
            all_json_ids.add(unique_id)
            json_docs.add(unique_id)
            local_meta["composite_id"] = unique_id
            content = node.get('content') or node.get('title') or "No content"
            batch_ids.append(unique_id)
            batch_texts.append(content)
            batch_metadatas.append(filter_metadata(local_meta.copy()))
            pbar.update(1)
            logger.debug(f"Queued document {unique_id} (content length {len(content)})")
        
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
            unique_id = get_unique_id(base_id)
            all_json_ids.add(unique_id)
            json_chapters.add(unique_id)
            local_meta["composite_id"] = unique_id
            content = node.get('content') or node.get('title') or "No content"
            batch_ids.append(unique_id)
            batch_texts.append(content)
            batch_metadatas.append(filter_metadata(local_meta.copy()))
            pbar.update(1)
            logger.debug(f"Queued chapter {unique_id} (content length {len(content)})")
        
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
            unique_id = get_unique_id(base_id)
            all_json_ids.add(unique_id)
            json_sections.add(unique_id)
            local_meta["composite_id"] = unique_id
            content = node.get('content') or node.get('title') or "No content"
            batch_ids.append(unique_id)
            batch_texts.append(content)
            batch_metadatas.append(filter_metadata(local_meta.copy()))
            pbar.update(1)
            logger.debug(f"Queued section {unique_id} (content length {len(content)})")
        
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
            unique_id = get_unique_id(base_id)
            all_json_ids.add(unique_id)
            json_subsections.add(unique_id)
            local_meta["composite_id"] = unique_id
            content = node.get('content') or node.get('title') or "No content"
            batch_ids.append(unique_id)
            batch_texts.append(content)
            batch_metadatas.append(filter_metadata(local_meta.copy()))
            pbar.update(1)
            logger.debug(f"Queued subsection {unique_id} (content length {len(content)})")

        if len(batch_ids) >= BATCH_SIZE:
            flush_batch()
        # Recurse into nested dictionaries or lists.
        for key, value in node.items():
            if isinstance(value, (dict, list)):
                process_node(value, cur_doc, cur_chapter, cur_section, local_meta)
    elif isinstance(node, list):
        for item in node:
            process_node(item, cur_doc, cur_chapter, cur_section, parent_meta)

if __name__ == "__main__":
    with open(HASH_MAPPING_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    logger.info(f"Loaded JSON from {HASH_MAPPING_FILE}.")
    
    # Determine JSON structure.
    if isinstance(data, dict):
        first_val = next(iter(data.values()))
        if isinstance(first_val, dict) and first_val.get("hash_document", "").strip():
            logger.info("Detected top-level document structure.")
            process_node(data)
        else:
            logger.info("Detected top-level category structure.")
            for category, docs in data.items():
                if isinstance(docs, dict):
                    for doc_name, doc_val in docs.items():
                        if isinstance(doc_val, dict):
                            doc_val["category"] = category
                            if "title" in doc_val:
                                doc_val["pdf_path"] = construct_pdf_path(category, doc_val["title"])
                            process_node(doc_val)
                elif isinstance(docs, list):
                    for doc_val in docs:
                        if isinstance(doc_val, dict):
                            doc_val["category"] = category
                            if "title" in doc_val:
                                doc_val["pdf_path"] = construct_pdf_path(category, doc_val["title"])
                            process_node(doc_val)
    flush_batch()
    pbar.close()

    logger.info("Finished embedding nodes into Chroma.")
    logger.info(f"Total unique composite IDs extracted from JSON: {len(all_json_ids)}")
    logger.info(f"Total unique composite IDs added to Chroma: {len(added_ids)}")
    
    # Generate a discrepancy report.
    missing_ids = all_json_ids - added_ids
    logger.info(f"Missing composite IDs (present in JSON but not in Chroma): {len(missing_ids)}")
    if missing_ids:
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
    else:
        logger.info("No discrepancies found. All JSON hashes are present in Chroma.")

    # Verification: Check that every expected hash_document has been inherited.
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
    for expected in expected_hash_docs:
        try:
            result = collection.get(where={"hash_document": expected})
            count = len(result.get("ids", []))
        except Exception as e:
            logger.error(f"Error querying for hash_document '{expected}': {e}")
            count = 0
        if count == 0:
            logger.warning(f"No documents found with hash_document '{expected}'.")
        else:
            logger.info(f"Found {count} documents with hash_document '{expected}'.")
