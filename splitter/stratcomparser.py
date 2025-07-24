import os
import re
import hashlib
from tqdm import tqdm
import pdfplumber

class SIParser:
    def __init__(self, pdf_folder):
        self.pdf_folder = pdf_folder

        # Chapter regex – one to eight words of ALL CAPS only.
        self.chapter_regex = re.compile(r"^(?P<title>[A-Z]+(?:\s+[A-Z]+){0,7})$")

        # Section regex – a number followed by a period, a title capped at the first period, then any extra content.
        # Example: "2. INTRODUCTION. The purpose of this section is..."
        self.section_regex = re.compile(
            r"^(?P<number>\d+\.)\s+(?P<title>[^.]+)\.\s*(?P<content>.*)$"
        )

        # Subsection regex – a single letter followed by a period, a title capped at the first period, then extra content.
        # Example: "a. OVERVIEW. Some additional info..."
        self.subsection_regex = re.compile(
            r"^(?P<number>[A-Za-z])\.\s+(?P<title>[^.]+)\.\s*(?P<content>.*)$"
        )

        # Sublevel regex – starts with a number or letter in parentheses followed by content.
        # Example: "(1) Some detailed content here" or "(a) Additional details..."
        self.sublevel_regex = re.compile(
            r"^\((?P<number>\d+|[A-Za-z])\)\s*(?P<content>.+)$"
        )

        # Additional patterns (unchanged)
        self.labeled_section_regex = re.compile(
            r"^(?P<label>[A-Z][A-Z\s]+:)\s*(?P<sec_content>.+)$"
        )
        self.date_pattern = re.compile(
            r".*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{1,2}\s+[A-Za-z]+\s+\d{4})\s*$"
        )
        self.meta_pattern = re.compile(
            r"(?:\bREF:|\bUNCLASSIFIED\b|\bSI 230-03\b|\b230\b|\bENCLOSURE\s+[A-Z]\b|\bCJCSI 1100.01E\b|\b1100\b)",
            re.IGNORECASE
        )
        self.dot_leader_pattern = re.compile(r'\.{5,}\s*(\d+)\s*$')

    def hash_content(self, content: str) -> str:
        """Returns an MD5 hash of the given content string."""
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
        Build the document structure using the new rules.
        All nodes (document, chapter, section, and subsection) will be assigned a hash.
        """
        lines = pdf_text.splitlines()
        # Compute the document hash using the entire pdf text.
        hash_document = self.hash_content(pdf_text.strip())
        chapters = []
        current_chap = None
        current_sec = None
        current_sub = None
        
        for line in lines:
            stripped_line = line.strip()
            page_number = None

            # Remove dot leader numbers (e.g. ".......... 12")
            try:
                m = self.dot_leader_pattern.search(stripped_line)
                if m:
                    page_number = int(m.group(1))
                    stripped_line = self.dot_leader_pattern.sub('', stripped_line).strip()
                if not stripped_line:
                    continue
            except Exception as e:
                print(f"[Error] Removing trailing dots: {e}")
            
            # Ignore lines ending with a date or containing metadata.
            if self.date_pattern.match(stripped_line) or self.meta_pattern.search(stripped_line):
                continue

            # Check for a Chapter (all-caps, 1 to 8 words)
            chap_match = self.chapter_regex.match(stripped_line)
            if chap_match:
                current_chap = {
                    'node_type': 'chapter',
                    'title': chap_match.group("title"),
                    'content': '',
                    'sections': [],
                    'page_number': page_number
                }
                chapters.append(current_chap)
                current_sec = None
                current_sub = None
                continue

            # Check for a Section (e.g. "2. TITLE. extra content")
            sec_match = self.section_regex.match(stripped_line)
            if sec_match:
                sec_number = sec_match.group("number").strip()
                sec_title = sec_match.group("title").strip()
                sec_content = sec_match.group("content").strip()
                current_sec = {
                    'node_type': 'section',
                    'number': sec_number,
                    'title': sec_title,
                    'content': sec_content,
                    'sublevels': [],
                    'page_number': page_number
                }
                if current_chap is not None:
                    current_chap.setdefault('sections', []).append(current_sec)
                current_sub = None
                continue

            # Check for a Subsection (e.g. "a. TITLE. extra content")
            sub_match = self.subsection_regex.match(stripped_line)
            if sub_match:
                sub_number = sub_match.group("number").strip()
                sub_title = sub_match.group("title").strip()
                sub_content = sub_match.group("content").strip()
                current_sub = {
                    'node_type': 'subsection',
                    'number': sub_number,
                    'title': sub_title,
                    'content': sub_content,
                    'sublevels': [],
                    'page_number': page_number,
                }
                if current_sec is not None:
                    current_sec.setdefault('sublevels', []).append(current_sub)
                continue

            # Check for a Sublevel (e.g. "(1) content" or "(a) content")
            # Create these nodes with the same node name as subsections.
            sublevel_match = self.sublevel_regex.match(stripped_line)
            if sublevel_match:
                new_subsection = {
                    'node_type': 'subsection',  # Use "subsection" as the node type.
                    'number': sublevel_match.group('number'),
                    'title': '',  # Sublevels do not have titles.
                    'content': sublevel_match.group('content'),
                    'page_number': page_number,
                    'sublevels': []  # Allow for deeper nesting if needed.
                }
                if current_sub is not None:
                    current_sub.setdefault('sublevels', []).append(new_subsection)
                elif current_sec is not None:
                    current_sec.setdefault('sublevels', []).append(new_subsection)
                continue

            # Labeled Section (e.g. "PURPOSE:")
            labeled_match = self.labeled_section_regex.match(stripped_line)
            if labeled_match and current_chap is not None:
                label = labeled_match.group("label").strip()
                sec_content = labeled_match.group("sec_content").strip()
                new_section = {
                    'node_type': 'section',
                    'number': '',
                    'title': label,
                    'content': sec_content,
                    'sublevels': [],
                    'page_number': page_number
                }
                current_chap.setdefault("sections", []).append(new_section)
                current_sec = new_section
                current_sub = None
                continue

            # Labeled Section Continuation:
            if current_sec is not None and current_sec.get("title", "").strip().endswith(":"):
                if not (stripped_line and stripped_line[0].isupper() and stripped_line.endswith(":")):
                    current_sec["content"] += "\n" + stripped_line
                    continue
            
            # Append content to the current active node.
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
        # --- Recursive helper to add a "hash" key to every node ---
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
        for filename in tqdm(pdf_files, desc="Processing SI PDFs"):
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
