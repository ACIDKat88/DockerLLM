import os
import uuid
import json
from tqdm import tqdm
from langchain.schema import Document
from langchain_community.vectorstores import Chroma
from embedd_class import customembedding
import chromadb

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
    Filters out keys with None values from the metadata dictionary.
    """
    return {k: v for k, v in metadata.items() if v is not None}

class HybridJSONEmbedder:
    def __init__(self, hash_mapping_file, chromadb_path):
        """
        Parameters:
          hash_mapping_file: Path to the JSON file storing the document structures.
          chromadb_path: Folder where the ChromaDB collection is (or will be) stored.
        """
        self.hash_mapping_file = hash_mapping_file
        self.chromadb_path = chromadb_path
        self.embedding_function = customembedding("mixedbread-ai/mxbai-embed-large-v1")
        self.records = self.load_records()

    def load_records(self):
        """
        Parses the JSON file and constructs Document objects with appropriate metadata.
        """
        with open(self.hash_mapping_file, 'r') as file:
            data = json.load(file)

        documents = []
        for category, docs in data.items():
            for doc_name, doc_val in docs.items():
                doc_meta = {
                    "category": category,
                    "document_title": doc_val.get("title", ""),
                    "hash_document": doc_val.get("hash_document", ""),
                    "pdf_path": construct_pdf_path(category, doc_val.get("title", ""))
                }
                for chapter in doc_val.get("chapters", []):
                    if chapter.get("node_type") == "chapter":
                        chap_meta = {
                            "chapter_title": chapter.get("title", ""),
                            "chapter_number": chapter.get("number", ""),
                            "hash_chapter": chapter.get("hash_chapter", "")
                        }
                        for section in chapter.get("sections", []):
                            if section.get("node_type") == "section":
                                sec_meta = {
                                    "section_title": section.get("title", ""),
                                    "section_number": section.get("number", ""),
                                    "section_page_number": section.get("page_number"),
                                    "hash_section": section.get("hash_section", "")
                                }
                                # Create a document for the section
                                section_content = section.get("content", "")
                                page_content = f"{chap_meta['chapter_title']} {chap_meta['chapter_number']}\n" \
                                               f"{sec_meta['section_title']} {sec_meta['section_number']}\n" \
                                               f"{section_content}"
                                metadata = filter_metadata({**doc_meta, **chap_meta, **sec_meta})
                                documents.append(Document(page_content=page_content, metadata=metadata))

                                # Create documents for each subsection
                                for sublevel in section.get("sublevels", []):
                                    if sublevel.get("node_type") == "subsection":
                                        sub_meta = {
                                            "subsection_title": sublevel.get("title", ""),
                                            "subsection_number": sublevel.get("number", ""),
                                            "subsection_page_number": sublevel.get("page_number"),
                                            "hash_subsection": sublevel.get("hash_subsection", "")
                                        }
                                        subsection_content = sublevel.get("content", "")
                                        page_content = f"{chap_meta['chapter_title']} {chap_meta['chapter_number']}\n" \
                                                       f"{sec_meta['section_title']} {sec_meta['section_number']}\n" \
                                                       f"{sub_meta['subsection_title']} {sub_meta['subsection_number']}\n" \
                                                       f"{subsection_content}"
                                        metadata = filter_metadata({**doc_meta, **chap_meta, **sec_meta, **sub_meta})
                                        documents.append(Document(page_content=page_content, metadata=metadata))
        return documents

    def extract_and_embed(self):
        """
        Iterates over each loaded Document object and embeds it into the ChromaDB collection.
        """
        client = chromadb.PersistentClient(path=self.chromadb_path)
        try:
            collection = client.get_collection(
                name="kg2",
                embedding_function=self.embedding_function
            )
        except ValueError:
            return

        pbar = tqdm(desc="Embedding nodes", unit="node")
        for record in self.records:
            # Determine a unique document ID
            doc_id = (
                record.metadata.get("hash_subsection") or
                record.metadata.get("hash_section") or
                record.metadata.get("hash_chapter") or
                record.metadata.get("hash_document") or
                str(uuid.uuid4())
            )
            collection.add(
                documents=[record.page_content],
                metadatas=[record.metadata],
                ids=[doc_id]
            )
            pbar.update(1)
        pbar.close()

    def process(self):
        self.extract_and_embed()

if __name__ == "__main__":
    HASH_MAPPING_FILE = "/home/cm36/Updated-LLM-Project/J1_corpus/json/kg/combined_output_3.json"
    CHROMADB_PATH = "/home/cm36/Updated-LLM-Project/vectorstores/KG/chunk_size_mid"
    embedder = HybridJSONEmbedder(
        hash_mapping_file=HASH_MAPPING_FILE,
        chromadb_path=CHROMADB_PATH
    )
    embedder.process()
