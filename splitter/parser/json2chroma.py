#JSON Loader
import os
import uuid
import json
from tqdm import tqdm
from langchain.schema import Document
from langchain_community.vectorstores import Chroma
from embedd_class import customembedding
import chromadb

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
    Process a node from the JSON structure. If the node contains non-empty "content",
    embed that content into the collection with merged metadata. Then recursively process any sublevels.
    """
    # Merge parent metadata with the current node's metadata.
    node_metadata = {
        **parent_metadata,
        "node_type": node.get("node_type", ""),
        "number": node.get("number", ""),
        "title": node.get("title", ""),
        "hash": node.get("hash", "")
    }
    
    # Extract content from the node.
    node_content = node.get("content", "")
    if node_content.strip():
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
    
    # Recursively process any sublevels present in this node.
    if "sublevels" in node and node["sublevels"]:
        for sub in node["sublevels"]:
            process_node(sub, node_metadata, collection, pbar)

class HybridJSONEmbedder:
    def __init__(self, hash_mapping_file, chromadb_path):
        """
        Parameters:
          hash_mapping_file: Path to the JSON file storing the combined document structures.
          chromadb_path: Folder where the ChromaDB collection is (or will be) stored.
        """
        self.hash_mapping_file = hash_mapping_file
        self.chromadb_path = chromadb_path
        self.embedding_function = customembedding("mixedbread-ai/mxbai-embed-large-v1")
        self.hash_mapping = self.load_hash_mapping()

    def load_hash_mapping(self):
        """Load the hash mapping from the JSON file."""
        if not os.path.exists(self.hash_mapping_file):
            raise FileNotFoundError(f"Hash mapping file {self.hash_mapping_file} does not exist.")
        with open(self.hash_mapping_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def extract_and_embed(self):
        """
        Iterate over the entire JSON hierarchy. For each document (or node),
        process its content (if available) and embed it into the ChromaDB collection.
        This method processes every level (document, chapters, sections, sublevels) that contains text.
        """
        # Connect to (or create) a ChromaDB collection.
        client = chromadb.PersistentClient(path=self.chromadb_path)
        collection_name = "kg2"
        try:
            collection = client.get_collection(
                name=collection_name,
                embedding_function=self.embedding_function
            )
            print(f"Connected to collection '{collection_name}' at {self.chromadb_path}")
        except ValueError:
            print(f"Collection '{collection_name}' does not exist. Please create or verify it.")
            return

        # Use a progress bar that updates per node processed.
        pbar = tqdm(desc="Embedding nodes", unit="node")
        
        # Iterate over each category and document in the hash mapping.
        for category, docs in self.hash_mapping.items():
            print(f"Processing category: {category}")
            for document_name, doc_data in tqdm(docs.items(), desc=f"Embedding {category}", unit="doc"):
                if not doc_data:
                    continue

                # Unpack document structure; if nested under the document name, extract it.
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
                
                # Process the document node itself if it contains "content".
                if "content" in actual_doc and actual_doc["content"].strip():
                    process_node(actual_doc, base_metadata, collection, pbar)
                # Otherwise, process hierarchical levels (e.g., chapters) if available.
                if "chapters" in actual_doc:
                    for chapter in actual_doc["chapters"]:
                        process_node(chapter, base_metadata, collection, pbar)
        pbar.close()
        print("Done embedding all nodes from JSON content.")

    def process(self):
        """Load the JSON and run the extraction and embedding routines."""
        self.extract_and_embed()

if __name__ == "__main__":
    # Update these paths as needed.
    HASH_MAPPING_FILE = "/home/cm36/Updated-LLM-Project/J1_corpus/json/kg/combined_output_3.json"
    CHROMADB_PATH = "/home/cm36/Updated-LLM-Project/vectorstores/KG/chunk_size_mid"
    
    embedder = HybridJSONEmbedder(
        hash_mapping_file=HASH_MAPPING_FILE,
        chromadb_path=CHROMADB_PATH
    )
    embedder.process()

