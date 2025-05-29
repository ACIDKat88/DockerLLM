import os
import re
import hashlib
import json
from tqdm import tqdm
import PyPDF2

# Replace with your default paths
PDF_FILE_PATH = '/home/cm36/Updated-LLM-Project/J1_corpus/cleaned/stratcom'
JSON_OUTPUT_PATH = '/home/cm36/Updated-LLM-Project/J1_corpus/json/kg'

# (A) Detect chapter lines
# - Allows numeric or written-out numbers after "CHAPTER".
# - Can be up to 7 words long after "CHAPTER X".
# - May end with an acronym in parentheses, a single letter, or just a space.
chapter_number_line_regex = re.compile(
    r"^(?:CHAPTER|ENCLOSURE|ANNEX|SI)\s+"  # Match the prefix but do not capture it
    r"(?P<number>[A-Z]|\d+(?:[-\s]?[A-Z0-9]*)?)\s+"  # Capture only the number
    r"(?P<title>[A-Za-z0-9\- ]+)",  # Capture the title
    re.IGNORECASE
)


# (B) Section regex:
# - Numbering: exactly two or fewer alphanumerics (or a digit dot digit pattern), optionally in parentheses, with an optional trailing punctuation.
# - Title: 1 to 13 words that end with a period or colon.
# - Content: everything after that space.
section_regex = re.compile(
    r"^"                                          # Start of line
    r"(?P<number>"                                # Capture section numbering
      r"(?:\(?[a-zA-Z0-9]{1,2}\)?|\d+\.\d+)"      # E.g. "(a)", "(12)", "1.2", etc.
      r"[:.]?"                                    # Optional trailing punctuation
    r")"
    r"\s+"                                        # At least one space
    r"(?P<title>"                                 # Capture title (1-13 words)
      r"(?:\S+\s+){0,12}\S+"                       # 1 to 13 words
      r"[:.]"                                     # Must end with period or colon
    r")"
    r"\s+"                                        # At least one space after title punctuation
    r"(?P<content>.*)"                            # Capture content (may be empty)
    r"$",                                         # End of line
    re.IGNORECASE
)

# (C) Generic heading regex for subsections (level>=3)
generic_heading_regex = re.compile(
    r"^"                                               # Start of line
    r"(?P<number>"                                     # Capture numbering
      r"(?:"
         r"(?:\d+(?:\.\d+)*[a-zA-Z]?[:.])"             # e.g. "1.2.3", "1.2.a.", "1.2:" etc.
         r"|"                                          # OR
         r"(?:\([a-zA-Z0-9]+\)[:.]?)"                  # e.g. "(a)", "(b):", "(1)."
         r"|"                                          # OR
         r"(?:[a-zA-Z][:.]?)"                          # e.g. "a.", "b:"
      r")"
    r")"
    r"\s+"                                             # At least one space after numbering
    r"(?P<title>"                                      # Capture title (1-13 words)
      r"(?:(?:\S+\s+){0,13}\S+)"                       # 1 to 13 words
      r"[:.]"                                        # Must end with period or colon
    r")"
    r"$",                                              # End of line
    re.IGNORECASE
)

# Prefix regex: to check if a line starts with valid numbering.
# For letters, require exactly one character.
numbering_prefix_regex = re.compile(
    r"^(?P<number>(?:\(?[a-zA-Z0-9]\)?|\d+(?:\.\d+)*(?:[a-zA-Z])?[:.]))\s+",
    re.IGNORECASE
)

def hash_content(content: str) -> str:
    """Generate an MD5 hash from a string."""
    hasher = hashlib.md5()
    hasher.update(content.encode('utf-8'))
    return hasher.hexdigest()

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract all text from a PDF file using PyPDF2.
    Returns the concatenated string of all pages.
    """
    text_content = []
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            text_content.append(page.extract_text() or "")
    return "\n".join(text_content)

def parse_pdf_structure(pdf_text: str, document_title: str, document_filename: str) -> dict:
    """
    Build a nested structure:
      - Document → Chapter → Section → Subsections.
      - Chapters are detected via chapter_number_line_regex.
      - Sections are detected via section_regex.
      - Generic headings (for subsections) are detected via generic_heading_regex.
      - Additionally, if a content line starts with a valid numbering prefix (via numbering_prefix_regex),
        it is treated as a new child node. For any node of type "subsection", the captured title is moved
        to its content (and the title field is set to an empty string).
      - Otherwise, the line is appended as content to the last valid node.
    """
    lines = pdf_text.splitlines()
    hash_document = hash_content(pdf_text.strip())

    chapters = []
    current_chap = None
    current_sec = None

    # Regex to strip trailing dot leaders and page numbers (e.g., "........ 17")
    dot_leader_pattern = re.compile(r'\.{5,}\s*(\d+)\s*$')

    # Stack for generic headings (level>=3)
    heading_stack = []

    # Helper: get last segment of a numbering string (if needed)
    def get_last_segment(number_str):
        number_str = number_str.rstrip('.:')
        segments = number_str.split('.')
        return segments[-1] if segments else None

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped_line = line.strip()
        page_number = None
        try:
            m = dot_leader_pattern.search(stripped_line)
            if m:
                page_number = int(m.group(1))
                stripped_line = dot_leader_pattern.sub('', stripped_line)
            stripped_line = stripped_line.strip()
        except Exception as e:
            print(f"[Error] Removing trailing dots: {e}")

        # (A) Process chapter headings ("CHAPTER X")
        try:
            chap_match = chapter_number_line_regex.match(stripped_line)
            if chap_match:
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    combined_title = f"CHAPTER {chap_match.group(1)} {next_line}"
                else:
                    combined_title = f"CHAPTER {chap_match.group(1)}"
                current_chap = {
                    'node_type': 'chapter',
                    'title': combined_title,
                    'number': chap_match.group(1),
                    'content': '',
                    'sections': [],
                    'page_number': page_number
                }
                chapters.append(current_chap)
                current_sec = None
                heading_stack = []
                i += 2  # Skip chapter detail line
                continue
        except Exception as e:
            print(f"[Error] Processing chapter line: {e}")
            i += 1
            continue

        # (B) Process section headings using section_regex.
        try:
            sec_match = section_regex.match(stripped_line)
            if sec_match:
                sec_number = sec_match.group("number").strip()
                sec_title = sec_match.group("title").strip()
                sec_content = sec_match.group("content").strip() if sec_match.group("content") else ""
                current_sec = {
                    'node_type': 'section',
                    'title': sec_title,
                    'number': sec_number,
                    'content': sec_content,
                    'sublevels': [],
                    'page_number': page_number
                }
                if current_chap:
                    current_chap.setdefault('sections', []).append(current_sec)
                heading_stack = []
                i += 1
                continue
        except Exception as e:
            print(f"[Error] Processing section heading: {e}")

        # (C) Process generic headings (subsections) using generic_heading_regex.
        try:
            gen_match = generic_heading_regex.match(stripped_line)
            if gen_match:
                numbering = gen_match.group("number")
                rest_text = gen_match.group("title").strip()
                normalized = numbering.rstrip('.')
                level = normalized.count('.') + 1
                if level >= 3:
                    # For subsections, we now want no title; move the captured title text into content.
                    node = {
                        'node_type': 'subsection',
                        'number': normalized,
                        'title': "",  # Clear title for subsections
                        'content': rest_text,  # Move what was captured as title into content
                        'page_number': page_number,
                        'sublevels': []
                    }
                    if not heading_stack:
                        parent = current_sec
                    else:
                        while heading_stack and heading_stack[-1][0] >= level:
                            heading_stack.pop()
                        parent = heading_stack[-1][1] if heading_stack else current_sec
                    if parent:
                        parent.setdefault('sublevels', []).append(node)
                    elif current_chap:
                        current_chap.setdefault('sections', []).append(node)
                    heading_stack.append((level, node))
                    i += 1
                    continue
        except Exception as e:
            print(f"[Error] Processing generic heading: {e}")
            i += 1
            continue

        # (D) Content handling:
        # If the line starts with a valid numbering prefix, treat it as a new node.
        try:
            num_prefix_match = numbering_prefix_regex.match(stripped_line)
            if num_prefix_match:
                full_match = section_regex.match(stripped_line)
                if not full_match:
                    full_match = generic_heading_regex.match(stripped_line)
                if full_match:
                    sec_number = full_match.group("number").strip()
                    sec_title = full_match.group("title").strip()
                    sec_content = full_match.group("content").strip() if "content" in full_match.groupdict() and full_match.group("content") else ""
                    normalized = sec_number.rstrip('.')
                    level = normalized.count('.') + 1
                    # For level>=3, create a subsection with no title; move the captured title to content.
                    if level >= 3:
                        new_node = {
                            'node_type': 'subsection',
                            'number': sec_number,
                            'title': "",
                            'content': sec_title + ("\n" + sec_content if sec_content else ""),
                            'page_number': page_number,
                            'sublevels': []
                        }
                    else:
                        new_node = {
                            'node_type': 'section',
                            'number': sec_number,
                            'title': sec_title,
                            'content': sec_content,
                            'page_number': page_number,
                            'sublevels': []
                        }
                    if current_sec:
                        current_sec.setdefault("sublevels", []).append(new_node)
                    elif current_chap:
                        current_chap.setdefault("sections", []).append(new_node)
                    heading_stack.append((level, new_node))
                else:
                    # If no full match, use the prefix and the remainder.
                    sec_number = num_prefix_match.group("number").strip()
                    remainder = stripped_line[num_prefix_match.end():].strip()
                    # For subsections, we assume level>=3.
                    normalized = sec_number.rstrip('.')
                    level = normalized.count('.') + 1
                    if level >= 3:
                        new_node = {
                            'node_type': 'subsection',
                            'number': sec_number,
                            'title': "",
                            'content': remainder,
                            'page_number': page_number,
                            'sublevels': []
                        }
                    else:
                        new_node = {
                            'node_type': 'section',
                            'number': sec_number,
                            'title': remainder,
                            'content': "",
                            'page_number': page_number,
                            'sublevels': []
                        }
                    if current_sec:
                        current_sec.setdefault("sublevels", []).append(new_node)
                    elif current_chap:
                        current_chap.setdefault("sections", []).append(new_node)
                    heading_stack.append((level, new_node))
            else:
                # Otherwise, append the line as content to the most recent node.
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

    # Compute hashes recursively by accumulating child hashes.
    def compute_hashes_linear(node: dict) -> str:
        children_hash = ""
        if 'sections' in node:
            for sec in node['sections']:
                children_hash += compute_hashes_linear(sec)
        if 'sublevels' in node:
            for sub in node['sublevels']:
                children_hash += compute_hashes_linear(sub)
        if node.get("node_type") == "chapter":
            text_to_hash = (node.get("title", "") + "\n" + node.get("content", "") + "\n" + children_hash).strip()
            node["hash_chapter"] = hash_content(text_to_hash)
            return node["hash_chapter"]
        elif node.get("node_type") == "section":
            text_to_hash = (node.get("title", "") + "\n" + node.get("content", "") + "\n" + children_hash).strip()
            node["hash_section"] = hash_content(text_to_hash)
            return node["hash_section"]
        elif node.get("node_type") == "subsection":
            text_to_hash = (node.get("title", "") + "\n" + node.get("content", "") + "\n" + children_hash).strip()
            node["hash_subsection"] = hash_content(text_to_hash)
            return node["hash_subsection"]
        else:
            text_to_hash = (node.get("content", "") + "\n" + children_hash).strip()
            node["hash"] = hash_content(text_to_hash)
            return node["hash"]

    for chapter in chapters:
        compute_hashes_linear(chapter)

    return {
        document_filename: {
            "title": document_title,
            "hash_document": hash_document,
            "chapters": chapters
        }
    }

def generate_pdf_hashes(pdf_folder, output_folder):
    if not os.path.exists(pdf_folder):
        print(f"Error: The folder {pdf_folder} does not exist.")
        return

    os.makedirs(output_folder, exist_ok=True)
    output_file = os.path.join(output_folder, "hashes_strategic.json")
    hash_mapping = {}
    pdf_files = [f for f in os.listdir(pdf_folder) if f.lower().endswith(".pdf")]

    print(f"Generating structured hashes for {len(pdf_files)} PDF files in '{pdf_folder}'...")
    for filename in tqdm(pdf_files, desc="Hashing PDF Files", unit="file"):
        file_path = os.path.join(pdf_folder, filename)
        try:
            pdf_text = extract_text_from_pdf(file_path)
        except Exception as e:
            print(f"[Error] Extracting text from PDF '{filename}': {e}")
            continue

        document_title = filename
        try:
            structure = parse_pdf_structure(pdf_text, document_title, filename)
        except Exception as e:
            print(f"[Error] Parsing PDF structure for '{filename}': {e}")
            continue

        hash_mapping[filename] = structure

    try:
        with open(output_file, "w", encoding="utf-8") as json_file:
            json.dump(hash_mapping, json_file, indent=4)
    except Exception as e:
        print(f"[Error] Writing output file '{output_file}': {e}")

    print(f"Hashes for chapters, sections, and sublevels successfully generated and saved to {output_file}.")

if __name__ == "__main__":
    pdf_folder = PDF_FILE_PATH
    json_folder = JSON_OUTPUT_PATH
    generate_pdf_hashes(pdf_folder, json_folder)
