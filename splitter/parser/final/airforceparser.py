import os
import re
import hashlib
from tqdm import tqdm
import pdfplumber

class AirForceParser:
    def __init__(self, pdf_folder):
        self.pdf_folder = pdf_folder
        # Use the imported hash function consistently (if needed, you could assign it here)
        self.chapter_number_line_regex = re.compile(r"^CHAPTER\s+(\d+)$", re.IGNORECASE)
        self.section_regex = re.compile(
            r"^(?P<number>(?:\(?[a-zA-Z0-9]{1,2}\)?|\d+\.\d+))[:.]?\s+(?P<title>(?:\S+\s+){0,12}\S+[:.])\s+(?P<content>.*)$",
            re.IGNORECASE
        )
        self.generic_heading_regex = re.compile(
            r"^(?P<number>(?:(?:\d+(?:\.\d+)*[a-zA-Z]?[:.])|(?:\([a-zA-Z0-9]+\)[:.]?)|(?:[a-zA-Z][:.]?)))\s+(?P<title>(?:(?:\S+\s+){0,13}\S+[:.]))$",
            re.IGNORECASE
        )
        self.numbering_prefix_regex = re.compile(
            r"^(?P<number>(?:\(?[a-zA-Z0-9]\)?|\d+(?:\.\d+)*(?:[a-zA-Z])?[:.]))\s+",
            re.IGNORECASE
        )
        self.dot_leader_pattern = re.compile(r'\.{5,}\s*(\d+)\s*$')

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
        lines = pdf_text.splitlines()
        hash_document = self.hash_content(pdf_text.strip())
        chapters = []
        current_chap = None
        current_sec = None
        heading_stack = []
        i = 0
        while i < len(lines):
            line = lines[i]
            stripped_line = line.strip()
            page_number = None
            try:
                m = self.dot_leader_pattern.search(stripped_line)
                if m:
                    page_number = int(m.group(1))
                    stripped_line = self.dot_leader_pattern.sub('', stripped_line).strip()
            except Exception as e:
                print(f"[Error] Removing trailing dots: {e}")
            try:
                chap_match = self.chapter_number_line_regex.match(stripped_line)
                if chap_match:
                    if i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        combined_title = f"CHAPTER {chap_match.group(1)} {next_line}"
                    else:
                        combined_title = f"CHAPTER {chap_match.group(1)}"
                    current_chap = {
                        "node_type": "chapter",
                        "title": combined_title,
                        "number": chap_match.group(1),
                        "content": "",
                        "sections": [],
                        "page_number": page_number
                    }
                    chapters.append(current_chap)
                    current_sec = None
                    heading_stack = []
                    i += 2
                    continue
            except Exception as e:
                print(f"[Error] Processing chapter line: {e}")
                i += 1
                continue
            try:
                sec_match = self.section_regex.match(stripped_line)
                if sec_match:
                    sec_number = sec_match.group("number").strip()
                    sec_title = sec_match.group("title").strip()
                    sec_content = sec_match.group("content").strip() if sec_match.group("content") else ""
                    current_sec = {
                        "node_type": "section",
                        "title": sec_title,
                        "number": sec_number,
                        "content": sec_content,
                        "sublevels": [],
                        "page_number": page_number
                    }
                    if current_chap:
                        current_chap.setdefault("sections", []).append(current_sec)
                    heading_stack = []
                    i += 1
                    continue
            except Exception as e:
                print(f"[Error] Processing section heading: {e}")
            try:
                gen_match = self.generic_heading_regex.match(stripped_line)
                if gen_match:
                    numbering = gen_match.group("number")
                    rest_text = gen_match.group("title").strip()
                    normalized = numbering.rstrip('.')
                    level = normalized.count('.') + 1
                    if level >= 3:
                        node = {
                            "node_type": "subsection",
                            "number": normalized,
                            "title": "",
                            "content": rest_text,
                            "page_number": page_number,
                            "sublevels": []
                        }
                        if not heading_stack:
                            parent = current_sec
                        else:
                            while heading_stack and heading_stack[-1][0] >= level:
                                heading_stack.pop()
                            parent = heading_stack[-1][1] if heading_stack else current_sec
                        if parent:
                            parent.setdefault("sublevels", []).append(node)
                        elif current_chap:
                            current_chap.setdefault("sections", []).append(node)
                        heading_stack.append((level, node))
                        i += 1
                        continue
            except Exception as e:
                print(f"[Error] Processing generic heading: {e}")
                i += 1
                continue
            try:
                num_prefix_match = self.numbering_prefix_regex.match(stripped_line)
                if num_prefix_match:
                    full_match = self.section_regex.match(stripped_line)
                    if not full_match:
                        full_match = self.generic_heading_regex.match(stripped_line)
                    if full_match:
                        sec_number = full_match.group("number").strip()
                        sec_title = full_match.group("title").strip()
                        sec_content = full_match.group("content").strip() if "content" in full_match.groupdict() and full_match.group("content") else ""
                        normalized = sec_number.rstrip('.')
                        level = normalized.count('.') + 1
                        if level >= 3:
                            new_node = {
                                "node_type": "subsection",
                                "number": sec_number,
                                "title": "",
                                "content": sec_title + ("\n" + sec_content if sec_content else ""),
                                "page_number": page_number,
                                "sublevels": []
                            }
                        else:
                            new_node = {
                                "node_type": "section",
                                "number": sec_number,
                                "title": sec_title,
                                "content": sec_content,
                                "page_number": page_number,
                                "sublevels": []
                            }
                        if current_sec:
                            current_sec.setdefault("sublevels", []).append(new_node)
                        elif current_chap:
                            current_chap.setdefault("sections", []).append(new_node)
                        heading_stack.append((level, new_node))
                    else:
                        sec_number = num_prefix_match.group("number").strip()
                        remainder = stripped_line[num_prefix_match.end():].strip()
                        normalized = sec_number.rstrip('.')
                        level = normalized.count('.') + 1
                        if level >= 3:
                            new_node = {
                                "node_type": "subsection",
                                "number": sec_number,
                                "title": "",
                                "content": remainder,
                                "page_number": page_number,
                                "sublevels": []
                            }
                        else:
                            new_node = {
                                "node_type": "section",
                                "number": sec_number,
                                "title": remainder,
                                "content": "",
                                "page_number": page_number,
                                "sublevels": []
                            }
                        if current_sec:
                            current_sec.setdefault("sublevels", []).append(new_node)
                        elif current_chap:
                            current_chap.setdefault("sections", []).append(new_node)
                        heading_stack.append((level, new_node))
                else:
                    if heading_stack:
                        heading_stack[-1][1]["content"] += "\n" + stripped_line
                    elif current_sec:
                        current_sec["content"] += "\n" + stripped_line
                    elif current_chap:
                        current_chap["content"] += "\n" + stripped_line
                i += 1
            except Exception as e:
                print(f"[Error] Handling content: {e}")
                i += 1
        
        doc = {
            "title": document_title,
            "hash_document": hash_document,
            "chapters": chapters
        }
        def add_hashes_to_node(node):
            if node["node_type"] == "chapter":
                hash_text = node.get("title", "") + node.get("number", "") + node.get("content", "")
                node["hash_chapter"] = self.hash_content(hash_text)
                for sec in node.get("sections", []):
                    add_hashes_to_node(sec)
            elif node["node_type"] == "section":
                hash_text = node.get("number", "") + node.get("title", "") + node.get("content", "")
                node["hash_section"] = self.hash_content(hash_text)
                for sub in node.get("sublevels", []):
                    add_hashes_to_node(sub)
            elif node["node_type"] == "subsection":
                hash_text = node.get("number", "") + node.get("title", "") + node.get("content", "")
                node["hash_subsection"] = self.hash_content(hash_text)
                for sub in node.get("sublevels", []):
                    add_hashes_to_node(sub)
        
        for chap in chapters:
            add_hashes_to_node(chap)
        
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
