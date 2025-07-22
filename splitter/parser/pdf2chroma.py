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
    def __init__(self, hash_mapping_file, chromadb_path, pdf_folder_map, parser_folder_map=None, use_parser=False):
        """
        Parameters:
          hash_mapping_file: Path to a JSON file storing the parsed document structures.
          chromadb_path: Folder where the ChromaDB collection is (or will be) stored.
          pdf_folder_map: Dictionary mapping each category (e.g. "airforce", "stratcom", "misc")
                          to its PDF folder path.
          parser_folder_map: (Optional) Dictionary mapping parser classes to their respective PDF folders.
                             Used only if use_parser=True.
          use_parser (bool): If True, generate the hash mapping on the fly.
        """
        self.hash_mapping_file = hash_mapping_file
        self.chromadb_path = chromadb_path
        self.embedding_function = customembedding("mixedbread-ai/mxbai-embed-large-v1")
        self.pdf_folder_map = pdf_folder_map

        # Default to using all three parsers with their respective folders if none is provided.
        if parser_folder_map is None:
            self.parser_folder_map = {
                AirForceParser: "/home/cm36/Updated-LLM-Project/spliter/parser/airforceparser.py",
                SIParser: "/home/cm36/Updated-LLM-Project/spliter/parser/stratcomparser.py",
                MiscParser: "/home/cm36/Updated-LLM-Project/spliter/parser/miscparser.py"
            }
        else:
            self.parser_folder_map = parser_folder_map

        self.hash_mapping = self.load_hash_mapping(use_parser=use_parser)

    def get_pdf_path(self, category, document_name):
        """
        Look up the designated folder for a given category and return the PDF path
        matching document_name (case-insensitive).
        """
        folder = self.pdf_folder_map.get(category)
        if not folder:
            return None
        for filename in os.listdir(folder):
            if filename.lower() == document_name.lower():
                return os.path.join(folder, filename)
        return None

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
        The metadata for each chunk includes the node hashes and the document hash.
        """
        # Build a lookup of PDFs across all folders using the pdf_folder_map.
        pdf_cache = {}
        for category, folder in self.pdf_folder_map.items():
            for pdf_file in os.listdir(folder):
                if pdf_file.lower().endswith(".pdf"):
                    pdf_cache[pdf_file.lower()] = os.path.join(folder, pdf_file)

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
            print(f"Collection '{collection_name}' does not exist. Create or verify it.")
            return

        # Iterate over each category and then over each document.
        for category, docs in self.hash_mapping.items():
            print(f"Processing category: {category}")
            for document_name, doc_data in tqdm(docs.items(), desc=f"Embedding {category}", unit="doc"):
                if not doc_data:
                    continue

                # If the document structure is nested under the document name, unpack it.
                if isinstance(doc_data, dict) and document_name in doc_data:
                    actual_doc = doc_data[document_name]
                else:
                    actual_doc = doc_data

                # Retrieve the document-level hash and title.
                document_hash = actual_doc.get("hash_document", "")
                document_title = actual_doc.get("title", "")

                # Find the PDF file (case-insensitive match) using pdf_folder_map.
                pdf_path = pdf_cache.get(document_name.lower())
                if not pdf_path:
                    print(f"Could not find a matching PDF for {document_name}. Skipping.")
                    continue

                pdf_lines = read_pdf_by_lines(pdf_path)

                # Determine the total number of chunks (sections and sublevels) for progress tracking.
                total_chunks = 0
                for chap in actual_doc.get("chapters", []):
                    total_chunks += len(chap.get("sections", []))
                    for sec in chap.get("sections", []):
                        total_chunks += len(sec.get("sublevels", []))
                # If no chunks are found, skip the progress bar.
                if total_chunks == 0:
                    print(f"No chunks found for {document_name}.")
                    continue

                with tqdm(total=total_chunks, desc=f"Processing {document_name}", unit="chunk") as pbar:
                    # Process each chapter.
                    for chapter in actual_doc.get("chapters", []):
                        chapter_metadata = {
                            "chapter_title": chapter.get("title", ""),
                            "chapter_number": chapter.get("number", ""),
                            "hash_chapter": chapter.get("hash_chapter", ""),
                            "hash_document": document_hash,
                            "document_title": document_title
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
                                self._recursive_embed_sublevels(pdf_lines, section["sublevels"], section_metadata, collection, pbar)
                            pbar.update(1)  # Update for processing each section
        print("Done embedding all sublevel nodes with actual PDF text.")

    def find_sublevel_text(self, pdf_lines, heading_number, next_heading_candidates):
        """
        Given the PDF lines, find the text starting at the line where the text begins
        with `heading_number` up to (but not including) the next heading candidate.
        """
        text_lines = []
        capturing = False
        for line in pdf_lines:
            stripped = line.strip()
            if not capturing:
                if stripped.startswith(heading_number):
                    capturing = True
                    text_lines.append(stripped)
            else:
                if any(stripped.startswith(candidate) for candidate in next_heading_candidates):
                    break
                text_lines.append(stripped)
        return "\n".join(text_lines)

    def _recursive_embed_sublevels(self, pdf_lines, sublevels, parent_metadata, collection, pbar):
        """
        Recursively traverse the 'sublevels' list and embed the PDF text for each node.
        Each node here corresponds to a generic heading (i.e. your sublevels).
        Since sublevels have no title, only their number and hash are used.
        """
        for i, node in enumerate(sublevels):
            node_metadata = {
                **parent_metadata,
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
            pbar.update(1)  # Update progress for each sublevel processed
            # Recursively process any nested sublevels.
            if "sublevels" in node and node["sublevels"]:
                self._recursive_embed_sublevels(pdf_lines, node["sublevels"], node_metadata, collection, pbar)
    
    def process(self):
        """
        Load the combined hash mapping and run the extraction and embedding routines.
        """
        self.extract_and_embed()

# =============================================================
# MAIN EXECUTION
# =============================================================
if __name__ == "__main__":
    # Update these paths as needed.
    HASH_MAPPING_FILE = "/home/cm36/Updated-LLM-Project/J1_corpus/json/kg/combined_output.json"
    CHROMADB_PATH = "/home/cm36/Updated-LLM-Project/vectorstores/KG/chunk_size_low"
    
    # Map each category to its PDF folder.
    pdf_folder_map = {
        "airforce": "/home/cm36/Updated-LLM-Project/J1_corpus/cleaned/air_force",
        "stratcom": "/home/cm36/Updated-LLM-Project/J1_corpus/cleaned/stratcom",
        "misc": "/home/cm36/Updated-LLM-Project/J1_corpus/cleaned/single"
    }
    
    # Instantiate the embedder using the precomputed hash mapping.
    embedder = HybridSubSubsectionEmbedder(
        hash_mapping_file=HASH_MAPPING_FILE,
        chromadb_path=CHROMADB_PATH,
        pdf_folder_map=pdf_folder_map
    )
    embedder.process()
