import os
import re
import hashlib
from tqdm import tqdm
import pdfplumber

class MiscParser:
    def __init__(self, pdf_folder):
        self.pdf_folder = pdf_folder
        # --- STYLE A patterns (unchanged) ---
        self.section_regex = re.compile(r"^(?P<number>(?:\d+\.)+)\s+(?P<title>.+)$")
        self.subsection_regex = re.compile(r"^(?P<number>[A-Za-z])\.\s+(?P<title>.+)$")
        self.number_in_line = re.compile(r"(\d+)")
        # --- STYLE B patterns ---
        # Chapters: title ending with an acronym in parentheses (2-6 letters)
        self.chapter_regex_b = re.compile(r"^(?P<title>.+\s\([A-Z]{2,6}\))$")
        # Sections: line that starts with 1-4 uppercase words followed by a colon, then optional content.
        self.section_regex_b = re.compile(r"^(?P<title>[A-Z]+(?:\s+[A-Z]+){0,3}):\s*(?P<content>.*)$")
        # Subsections: indicated by a bullet point.
        self.subsection_regex_b = re.compile(r"^[•\u2022]\s+(?P<content>.+)$")
        # --- Additional helper patterns ---
        self.date_pattern = re.compile(
            r".*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{1,2}\s+[A-Za-z]+\s+\d{4})\s*$"
        )
        self.labeled_section_regex = re.compile(
            r"^(?P<label>[A-Z][A-Z\s]+:)\s*(?P<sec_content>.+)$"
        )
        self.meta_pattern = re.compile(
            r"\bREF:|UNCLASSIFIED| SI 230-03|230|ENCLOSURE\s+[A-Z]\b",
            re.IGNORECASE
        )
    
    def hash_content(self, content: str) -> str:
        hasher = hashlib.md5()
        hasher.update(content.encode('utf-8'))
        return hasher.hexdigest()
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        text_content = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    text_content.append(text)
        return "\n".join(text_content)
    
    def parse_pdf_structure(self, pdf_text: str, document_title: str, document_filename: str) -> dict:
        """
        Build the document structure using STYLE A and STYLE B rules.
        Every node (document, chapter, section, and subsection) is assigned a hash.
        """
        lines = pdf_text.splitlines()
        hash_document = self.hash_content(pdf_text.strip())
        chapters = []
        current_chap = None
        current_sec = None
        current_sub = None
        
        for line in lines:
            stripped_line = line.strip()
            # Ignore lines with dates or metadata
            if self.date_pattern.match(stripped_line) or self.meta_pattern.search(stripped_line):
                continue
            
            # --- STYLE A Processing (unchanged) ---
            # Style A – Section
            sec_match = self.section_regex.match(stripped_line)
            if sec_match:
                sec_number = sec_match.group("number").strip()
                sec_title = sec_match.group("title").strip()
                current_sec = {
                    'node_type': 'section',
                    'number': sec_number,
                    'title': sec_title,
                    'content': '',
                    'sublevels': [],
                    'page_number': None
                }
                if current_chap is not None:
                    current_chap.setdefault('sections', []).append(current_sec)
                current_sub = None
                continue
            
            # Style A – Subsection
            sub_match = self.subsection_regex.match(stripped_line)
            if sub_match:
                sub_number = sub_match.group("number").strip()
                sub_title = sub_match.group("title").strip()
                current_sub = {
                    'node_type': 'subsection',
                    'number': sub_number,
                    'title': '',  # Title cleared
                    'content': sub_title,
                    'page_number': None,
                    'sublevels': []
                }
                if current_sec is not None:
                    current_sec.setdefault('sublevels', []).append(current_sub)
                continue
            
            # Style A – Chapter (entirely uppercase)
            if stripped_line and stripped_line == stripped_line.upper() and re.search('[A-Z]', stripped_line):
                num_match = self.number_in_line.search(stripped_line)
                chap_number = num_match.group(1) if num_match else ""
                current_chap = {
                    'node_type': 'chapter',
                    'number': chap_number,
                    'title': stripped_line,
                    'content': '',
                    'sections': [],
                    'page_number': None
                }
                chapters.append(current_chap)
                current_sec = None
                current_sub = None
                continue
            
            # --- STYLE B Processing ---
            # Style B – Subsection: starts with a bullet point.
            sub_b_match = self.subsection_regex_b.match(stripped_line)
            if sub_b_match:
                sub_content = sub_b_match.group("content").strip()
                current_sub = {
                    'node_type': 'subsection',
                    'number': '',
                    'title': '',
                    'content': sub_content,
                    'page_number': None,
                    'sublevels': []
                }
                if current_sec is not None:
                    current_sec.setdefault('sublevels', []).append(current_sub)
                else:
                    if current_chap is not None:
                        # If no current section exists, create an empty section.
                        current_sec = {
                            'node_type': 'section',
                            'number': '',
                            'title': '',
                            'content': '',
                            'sublevels': [current_sub],
                            'page_number': None
                        }
                        current_chap.setdefault('sections', []).append(current_sec)
                continue
            
            # Style B – Section: line that starts with 1-4 uppercase words followed by a colon,
            # and then optional content.
            sec_b_match = self.section_regex_b.match(stripped_line)
            if sec_b_match:
                sec_title = sec_b_match.group("title").strip()  # e.g., "PURPOSE"
                sec_content = sec_b_match.group("content").strip()  # content on the same line (if any)
                num_match = self.number_in_line.search(sec_title)
                sec_number = num_match.group(1) if num_match else ""
                current_sec = {
                    'node_type': 'section',
                    'number': sec_number,
                    'title': sec_title,
                    'content': sec_content,
                    'sublevels': [],
                    'page_number': None
                }
                if current_chap is not None:
                    current_chap.setdefault('sections', []).append(current_sec)
                current_sub = None
                continue
            
            # Style B – Chapter: title ends with an acronym in parentheses (e.g., "Some Title (SASA)")
            chap_b_match = self.chapter_regex_b.match(stripped_line)
            if chap_b_match:
                chapter_title = chap_b_match.group("title").strip()
                # Optionally, ensure the chapter title isn't too long.
                if len(chapter_title) <= 60:
                    num_match = self.number_in_line.search(chapter_title)
                    chap_number = num_match.group(1) if num_match else ""
                    current_chap = {
                        'node_type': 'chapter',
                        'number': chap_number,
                        'title': chapter_title,
                        'content': '',
                        'sections': [],
                        'page_number': None
                    }
                    chapters.append(current_chap)
                    current_sec = None
                    current_sub = None
                    continue
            
            # Otherwise, append non-heading lines as content.
            if current_sub is not None:
                current_sub["content"] += "\n" + stripped_line
            elif current_sec is not None:
                current_sec["content"] += "\n" + stripped_line
            elif current_chap is not None:
                current_chap["content"] += "\n" + stripped_line
            
            
            # Build the document structure.
        doc = {
            "title": document_title,
            "hash_document": hash_document,
            "chapters": chapters
        }
        # --- Add a hash to every node recursively ---
        # --- Recursive helper to add specific hash keys to every node ---
        def add_hashes_to_node(node):
            if node["node_type"] == "chapter":
                # For chapters, we assign "hash_chapter"
                hash_text = node.get("title", "") + node.get("number", "") + node.get("content", "")
                node["hash_chapter"] = self.hash_content(hash_text)
                for sec in node.get("sections", []):
                    add_hashes_to_node(sec)
            elif node["node_type"] == "section":
                # For sections, we assign "hash_section"
                hash_text = node.get("number", "") + node.get("title", "") + node.get("content", "")
                node["hash_section"] = self.hash_content(hash_text)
                for sub in node.get("sublevels", []):
                    add_hashes_to_node(sub)
            elif node["node_type"] == "subsection":
                # For subsections, we assign "hash_subsection"
                hash_text = node.get("number", "") + node.get("title", "") + node.get("content", "")
                node["hash_subsection"] = self.hash_content(hash_text)
                for sub in node.get("sublevels", []):
                    add_hashes_to_node(sub)
        
        # Add hashes to all chapters and their children.
        for chap in chapters:
            add_hashes_to_node(chap)
        
        # Also add a top-level "hash_document" if desired (already computed) and a document hash.
        doc["hash"] = self.hash_content(document_title + pdf_text.strip())
        
        return {
            document_filename: {
                "title": document_title,
                "hash_document": hash_document,
                "chapters": chapters,
                "hash": doc["hash"]
            }
        }
    
    def process_pdfs(self):
        results = {}
        pdf_files = [f for f in os.listdir(self.pdf_folder) if f.lower().endswith(".pdf")]
        for filename in tqdm(pdf_files, desc="Processing Misc PDFs"):
            file_path = os.path.join(self.pdf_folder, filename)
            try:
                pdf_text = self.extract_text_from_pdf(file_path)
                if not pdf_text.strip():
                    print(f"[Warning] No text extracted from {filename}. Skipping.")
                    continue
                structure = self.parse_pdf_structure(pdf_text, filename, filename)
                results.update(structure)
            except Exception as e:
                print(f"[Error] Processing {filename}: {e}")
        return results
