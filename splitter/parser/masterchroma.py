import os
import uuid
import json
from tqdm import tqdm
from langchain.schema import Document
from langchain_community.vectorstores import Chroma
from embedd_class import customembedding
import chromadb

# Import parser classes
from airforceparser import AirForceParser
from miscparser import MiscParser
from stratcomparser import SIParser

def serialize_metadata(metadata):
    """Flatten or serialize nested metadata to make it compatible with ChromaDB."""
    new_md = {}
    for key, value in list(metadata.items()):
        if value is None:
            continue
        if isinstance(value, (dict, list)):
            new_md[key] = json.dumps(value)
        else:
            new_md[key] = value
    return new_md

def process_node(node, parent_metadata, collection, pbar):
    """
    Recursively process a node from the parsed PDF structure.
    If the node contains non-empty "content", create a Document and add it to the collection.
    Then, recursively process any children under "chapters", "sections", or "sublevels".
    """
    node_metadata = {
        **parent_metadata,
        "node_type": node.get("node_type", ""),
        "number": node.get("number", ""),
        "title": node.get("title", ""),
        "hash": node.get("hash", "")
    }
    node_content = node.get("content", "").strip()
    if node_content:
        doc = Document(
            page_content=node_content,
            metadata=serialize_metadata(node_metadata)
        )
        doc_id = node.get("hash") or str(uuid.uuid4())
        collection.add(
            documents=[doc.page_content],
            metadatas=[doc.metadata],
            ids=[doc_id]
        )
        pbar.update(1)
    for child_key in ["chapters", "sections", "sublevels"]:
        if child_key in node and node[child_key]:
            for child in node[child_key]:
                process_node(child, node_metadata, collection, pbar)

class HybridSubSubsectionEmbedder:
    def __init__(self, chromadb_path, pdf_folder_map, use_parser=True):
        """
        Parameters:
          chromadb_path: Folder where the ChromaDB collection is (or will be) stored.
          pdf_folder_map: Dictionary mapping each category (e.g. "airforce", "stratcom", "misc")
                          to its PDF folder path.
          use_parser (bool): If True, parse the PDFs on the fly using the default parser mapping.
        """
        self.chromadb_path = chromadb_path
        self.embedding_function = customembedding("mixedbread-ai/mxbai-embed-large-v1")
        self.pdf_folder_map = pdf_folder_map

        if use_parser:
            print("Parsing PDFs using parser classes...")
            # Hard-code a default mapping from category to parser class.
            default_parser_map = {
                "airforce": AirForceParser,
                "stratcom": SIParser,
                "misc": MiscParser
            }
            combined_mapping = {}
            # For each category, instantiate the appropriate parser using the folder from pdf_folder_map.
            for category, folder in self.pdf_folder_map.items():
                parser_class = default_parser_map.get(category)
                if parser_class:
                    print(f"Running parser {parser_class.__name__} on folder: {folder}")
                    parser = parser_class(folder)
                    # process_pdfs() is expected to return a dict: { document_name: structure, ... }
                    mapping = parser.process_pdfs()
                    combined_mapping.setdefault(category, {}).update(mapping)
                else:
                    print(f"No parser available for category '{category}'.")
            self.hash_mapping = combined_mapping
        else:
            raise ValueError("This version requires use_parser=True to parse PDFs on the fly.")

    def extract_and_embed(self):
        """
        Iterate over each document in the parsed structure (self.hash_mapping) and recursively embed
        every node with non-empty "content" into the ChromaDB collection. In addition, it builds a cache
        of PDF file paths from the pdf_folder_map and adds the corresponding PDF path to the metadata.
        """
        client = chromadb.PersistentClient(path=self.chromadb_path)
        collection_name = "kg2"
        try:
            collection = client.get_collection(
                name=collection_name,
                embedding_function=self.embedding_function
            )
            print(f"Connected to collection '{collection_name}' at {self.chromadb_path}")
        except ValueError:
            print(f"Collection '{collection_name}' does not exist. Create or verify it.")
            return

        # Build a PDF cache from all folders in self.pdf_folder_map.
        pdf_cache = {}
        for category, folder in self.pdf_folder_map.items():
            for pdf_file in os.listdir(folder):
                if pdf_file.lower().endswith(".pdf"):
                    # Use the lowercased filename as key for matching.
                    pdf_cache[pdf_file.lower()] = os.path.join(folder, pdf_file)

        # Estimate total nodes for progress reporting.
        total_nodes = 0
        def count_nodes(node):
            count = 1 if node.get("content", "").strip() else 0
            for key in ["chapters", "sections", "sublevels"]:
                for child in node.get(key, []):
                    count += count_nodes(child)
            return count

        for category, docs in self.hash_mapping.items():
            for doc_name, doc_data in docs.items():
                if isinstance(doc_data, dict) and doc_name in doc_data:
                    actual_doc = doc_data[doc_name]
                else:
                    actual_doc = doc_data
                total_nodes += count_nodes(actual_doc)

        pbar = tqdm(total=total_nodes, desc="Embedding nodes", unit="node")

        # Process each document in the hash mapping.
        for category, docs in self.hash_mapping.items():
            print(f"Processing category: {category}")
            for document_name, doc_data in tqdm(docs.items(), desc=f"Processing {category}", unit="doc"):
                if not doc_data:
                    continue
                if isinstance(doc_data, dict) and document_name in doc_data:
                    actual_doc = doc_data[document_name]
                else:
                    actual_doc = doc_data

                document_hash = actual_doc.get("hash_document", "")
                document_title = actual_doc.get("title", "")
                base_metadata = {
                    "hash_document": document_hash,
                    "document_title": document_title
                }
                # Look up the PDF file using the document name (lowercased).
                pdf_path = pdf_cache.get(document_name.lower())
                if not pdf_path:
                    print(f"Could not find a matching PDF for {document_name}. Skipping.")
                    continue
                # Add the full PDF path to the metadata.
                base_metadata["pdf_path"] = pdf_path

                # Recursively process the entire parsed document structure.
                process_node(actual_doc, base_metadata, collection, pbar)
        pbar.close()
        print("Done embedding all nodes from parser output.")

    def process(self):
        """Run the extraction and embedding routines directly using parser output."""
        self.extract_and_embed()

# =============================================================
# MAIN EXECUTION
# =============================================================
if __name__ == "__main__":
    # Update these paths as needed.
    CHROMADB_PATH = "/home/cm36/Updated-LLM-Project/vectorstores/KG/chunk_size_low"
    
    # Map each category to its PDF folder.
    pdf_folder_map = {
        "airforce": "/home/cm36/Updated-LLM-Project/J1_corpus/cleaned/air_force",
        "stratcom": "/home/cm36/Updated-LLM-Project/J1_corpus/cleaned/stratcom",
        "misc": "/home/cm36/Updated-LLM-Project/J1_corpus/cleaned/single"
    }
    
    # Instantiate the embedder using the pdf folder map only (no separate parser folder map)
    embedder = HybridSubSubsectionEmbedder(
        chromadb_path=CHROMADB_PATH,
        pdf_folder_map=pdf_folder_map,
        use_parser=True
    )
    embedder.process()
