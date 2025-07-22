import os
import uuid
import json
from tqdm import tqdm
from langchain.schema import Document
from langchain_community.vectorstores import Chroma
from embedd_class import customembedding
import chromadb
import PyPDF2

# Import parser classes
from airforceparser import AirForceParser
from miscparser import MiscParser
from stratcomparser import SIParser

# =============================================================
# UTILITY FUNCTIONS
# =============================================================
def read_pdf_by_lines(pdf_path):
    """Return a list of lines from the PDF, preserving some notion of order (page by page)."""
    lines = []
    with open(pdf_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            page_text = page.extract_text() or ""
            page_lines = page_text.splitlines()
            lines.extend(page_lines)
    return lines

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
# =============================================================
# EMBEDDING CLASS
# =============================================================
class HybridSubSubsectionEmbedder:
    def __init__(self, hash_mapping_file, chromadb_path, parser_folder_map=None, use_parser=False):
        """
        Parameters:
          hash_mapping_file: Path to a JSON file storing the parsed document structures.
          chromadb_path: Folder where the ChromaDB collection is (or will be) stored.
          parser_folder_map: Dictionary mapping parser classes to their respective PDF folders.
          use_parser (bool): If True, generate the hash mapping on the fly.
        """
        self.hash_mapping_file = hash_mapping_file
        self.chromadb_path = chromadb_path
        self.embedding_function = customembedding("mixedbread-ai/mxbai-embed-large-v1")

        # Default to using all three parsers with their respective folders
        if parser_folder_map is None:
            self.parser_folder_map = {
                AirForceParser: "/home/cm36/Updated-LLM-Project/J1_corpus/cleaned/air_force",
                SIParser: "/home/cm36/Updated-LLM-Project/J1_corpus/cleaned/stratcom",
                MiscParser: "/home/cm36/Updated-LLM-Project/J1_corpus/cleaned/single"
            }
        else:
            self.parser_folder_map = parser_folder_map

        self.hash_mapping = self.load_hash_mapping(use_parser=use_parser)

    def load_hash_mapping(self, use_parser=False):
        """
        Load the hash mapping from the JSON file. If use_parser is True (or if the file does
        not exist), run each designated parser to build the mapping and then write it out.
        The expected JSON structure is a dictionary whose top-level keys are category names.
        """
        if use_parser or not os.path.exists(self.hash_mapping_file):
            print("Generating hash mapping using the parser(s)...")
            combined_mapping = {}

            for parser_class, folder in self.parser_folder_map.items():
                print(f"Running parser {parser_class.__name__} on folder: {folder}")
                parser = parser_class(folder)
                mapping = parser.process_pdfs()  # Expected output: { "category": { ... } }
                combined_mapping.update(mapping)

            with open(self.hash_mapping_file, "w", encoding="utf-8") as f:
                json.dump(combined_mapping, f, indent=2, ensure_ascii=False)
            
            return combined_mapping
        else:
            with open(self.hash_mapping_file, "r", encoding="utf-8") as f:
                return json.load(f)

    def extract_and_embed(self):
        """
        For every document in the hash mapping, locate its chapters, sections, and sublevels;
        then (by scanning the appropriate PDF folder) extract the corresponding text and
        embed it into the ChromaDB collection.
        """
        # Collect all PDF folders from the parser-folder mapping.
        all_pdf_folders = set(self.parser_folder_map.values())

        # Create a mapping of PDFs across all folders
        pdf_cache = {}
        for folder in all_pdf_folders:
            for pdf_file in os.listdir(folder):
                if pdf_file.lower().endswith(".pdf"):
                    pdf_cache[pdf_file.lower()] = os.path.join(folder, pdf_file)

        # Connect to (or create) a ChromaDB collection.
        client = chromadb.PersistentClient(path=self.chromadb_path)
        collection_name = "kg1"
        try:
            collection = client.get_collection(
                name=collection_name,
                embedding_function=self.embedding_function
            )
            print(f"Connected to collection '{collection_name}' at {self.chromadb_path}")
        except ValueError:
            print(f"Collection '{collection_name}' does not exist. Create or verify it.")
            return

        # Iterate over each category and then over each document.
        for category, docs in self.hash_mapping.items():
            print(f"Processing category: {category}")
            for document_name, doc_data in tqdm(docs.items(), desc=f"Embedding {category}", unit="doc"):
                if not doc_data:
                    continue

                # Find the PDF file (case-insensitive match)
                pdf_path = pdf_cache.get(document_name.lower())
                if not pdf_path:
                    print(f"Could not find a matching PDF for {document_name}. Skipping.")
                    continue

                pdf_lines = read_pdf_by_lines(pdf_path)

                # Traverse the document’s chapters.
                for chapter in doc_data.get("chapters", []):
                    chapter_metadata = {
                        "chapter_title": chapter.get("title", ""),
                        "chapter_number": chapter.get("number", ""),
                        "hash_chapter": chapter.get("hash_chapter", "")
                    }
                    # Process each section within the chapter.
                    for section in chapter.get("sections", []):
                        section_metadata = {
                            **chapter_metadata,
                            "section_title": section.get("title", ""),
                            "section_number": section.get("number", ""),
                            "hash_section": section.get("hash_section", "")
                        }
                        if "sublevels" in section and section["sublevels"]:
                            self._recursive_embed_sublevels(pdf_lines, section["sublevels"], section_metadata, collection)
        print("Done embedding all sublevel nodes with actual PDF text.")

    def _recursive_embed_sublevels(self, pdf_lines, sublevels, parent_metadata, collection):
        """
        Recursively traverse the 'sublevels' list and embed the PDF text for each node.
        Each node here corresponds to a generic heading (i.e. your sublevels).
        """
        for i, node in enumerate(sublevels):
            node_metadata = {
                **parent_metadata,
                "sublevel_title": node.get("title", ""),
                "sublevel_number": node.get("number", ""),
                "hash_subsection": node.get("hash_subsection", "")
            }
            next_candidates = []
            if i + 1 < len(sublevels):
                next_candidates.append(sublevels[i+1].get("number", ""))
            pdf_node_text = self.find_sublevel_text(pdf_lines, node.get("number", ""), next_candidates)
            doc = Document(
                page_content=pdf_node_text,
                metadata=serialize_metadata(node_metadata)
            )
            doc_id = node.get("hash_subsection") or str(uuid.uuid4())
            collection.add(
                documents=[doc.page_content],
                metadatas=[doc.metadata],
                ids=[doc_id]
            )
            # Recursively process any nested sublevels.
            if "sublevels" in node and node["sublevels"]:
                self._recursive_embed_sublevels(pdf_lines, node["sublevels"], node_metadata, collection)

# =============================================================
# MAIN EXECUTION
# =============================================================
if __name__ == "__main__":
    HASH_MAPPING_FILE = "/home/cm36/Updated-LLM-Project/J1_corpus/json/kg/combined_output.json"
    CHROMADB_PATH = "/home/cm36/Updated-LLM-Project/vectorstores/KG/chunk_size_high"

    # Instantiate the embedder with multiple parser classes and PDF folders.
    embedder = HybridSubSubsectionEmbedder(
        hash_mapping_file=HASH_MAPPING_FILE,
        chromadb_path=CHROMADB_PATH,
        use_parser=True  # Set to True to regenerate the hash mapping.
    )
    embedder.extract_and_embed()
