# genericparser.py
import os
import hashlib
from langchain.text_splitter import RecursiveCharacterTextSplitter
import pdfplumber

class GenericParser:
    def __init__(self, pdf_folder, chunk_size=1000, chunk_overlap=200):
        self.pdf_folder = pdf_folder
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def hash_content(self, content: str) -> str:
        import hashlib
        return hashlib.md5(content.encode("utf-8")).hexdigest()

    def extract_text(self, pdf_path: str) -> str:
        text_content = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    text_content.append(text)
        return "\n".join(text_content)

    def parse_pdf(self, document_title: str, document_filename: str) -> dict:
        pdf_path = os.path.join(self.pdf_folder, document_filename)
        pdf_text = self.extract_text(pdf_path)
        if not pdf_text.strip():
            print(f"[Warning] No text extracted from {document_filename}.")
            return {}
        
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", " ", ""]
        )
        chunks = splitter.split_text(pdf_text)
        chapters = []
        for i, chunk in enumerate(chunks):
            chapter_hash = self.hash_content(chunk)
            chapter = {
                "node_type": "chapter",
                "number": str(i+1),
                "title": f"Chunk {i+1}",
                "content": chunk,
                "sections": [],
                "hash": chapter_hash
            }
            chapters.append(chapter)
        
        document_hash = self.hash_content(document_title + pdf_text.strip())
        return {
            document_filename: {
                "title": document_title,
                "hash_document": self.hash_content(pdf_text.strip()),
                "chapters": chapters,
                "hash": document_hash
            }
        }
