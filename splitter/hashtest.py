#Style A & B
import os
import re
import hashlib
import json
from tqdm import tqdm
import pdfplumber  # For improved PDF text extraction

# ------------------------------------------------------------------------------
# CONFIGURATION
# ------------------------------------------------------------------------------
PDF_FILE_PATH = '/home/cm36/Updated-LLM-Project/J1_corpus/cleaned/single'
JSON_OUTPUT_PATH = '/home/cm36/Updated-LLM-Project/J1_corpus/json/kg'
OUTPUT_JSON_FILENAME = "hashes_test.json"
DEBUG = False  # Set True to print debug information

# ------------------------------------------------------------------------------
# STYLE A REGEX PATTERNS (Original style)
# ------------------------------------------------------------------------------
# Style A – Section: Begins with one or more numbers separated by dots then space.
section_regex = re.compile(r"^(?P<number>(?:\d+\.)+)\s+(?P<title>.+)$")
# Style A – Subsection: Begins with a letter and a dot then space.
subsection_regex = re.compile(r"^(?P<number>[A-Za-z])\.\s+(?P<title>.+)$")
# For Style A chapters, if a line is not caught by section/subsection and is entirely uppercase,
# we treat it as a chapter. (We may extract a number if present.)
number_in_line = re.compile(r"(\d+)")  # used to extract a number from the heading

# ------------------------------------------------------------------------------
# STYLE B REGEX PATTERNS (Alternate style)
# ------------------------------------------------------------------------------
# Style B – Chapter: Title ends with a 2–6 letter acronym within parentheses.
chapter_regex_b = re.compile(r"^(?P<title>.+\([A-Z]{2,6}\))$")
# Style B – Section: Entire line is uppercase and ends with a semicolon.
section_regex_b = re.compile(r"^(?P<title>[A-Z\s]+;)$")
# Style B – Subsection: Line begins with a bullet point (• or U+2022)
subsection_regex_b = re.compile(r"^[•\u2022]\s+(?P<content>.+)$")

# ------------------------------------------------------------------------------
# NEW HELPER PATTERNS
# ------------------------------------------------------------------------------
# A pattern to detect lines that end with a date (e.g. "07/29/2024" or "25 October 2023").
date_pattern = re.compile(r".*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{1,2}\s+[A-Za-z]+\s+\d{4})\s*$")
# A pattern to detect a labeled section (e.g. "PURPOSE:" or "ELIGIBILITY:" etc.)
labeled_section_regex = re.compile(r"^(?P<label>[A-Z][A-Z\s]+:)\s*(?P<sec_content>.+)$")
# A pattern to detect "REF:" metadata lines.
meta_pattern = re.compile(r"\bREF:|UNCLASSIFIED| SI 230-03|230|ENCLOSURE\s+[A-Z]\b", re.IGNORECASE)


# ------------------------------------------------------------------------------
# HELPER FUNCTIONS
# ------------------------------------------------------------------------------
def hash_content(content: str) -> str:
    """Generate an MD5 hash from a string."""
    hasher = hashlib.md5()
    hasher.update(content.encode('utf-8'))
    return hasher.hexdigest()

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract text from all pages of a PDF file using pdfplumber.
    Returns the concatenated text.
    """
    text_content = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                text_content.append(text)
    return "\n".join(text_content)

# ------------------------------------------------------------------------------
# PARSING FUNCTION
# ------------------------------------------------------------------------------
def parse_pdf_structure(pdf_text: str, document_title: str, document_filename: str) -> dict:
    """
    Build a nested document structure from the PDF text.

    The parser supports two document styles:

      STYLE A (Original):
        - Section: Lines beginning with one or more numbers (separated by dots) then space.
        - Subsection: Lines beginning with a letter and a dot.
        - Chapter: Any line (not caught above) that is entirely uppercase (and contains at least one letter).
          (If a chapter line has a number, the first occurrence is extracted.)

      STYLE B (Alternate):
        - Chapter: A line whose title ends with a 2–6 letter acronym in parentheses.
          (Now, the title is only treated as a chapter header if it is not excessively long.)
        - Section: A line that is entirely uppercase and ends with a semicolon.
        - Subsection: A line that begins with a bullet point.

    ADDITIONAL RULES:
      - Any line that ends with a date or contains "REF:" is ignored as metadata.
      - Labeled Section Rule: If a non‐heading line matches the labeled section pattern
        (e.g. "PURPOSE: ..."), a new section node is created under the current chapter.
      - Labeled Section Continuation Rule:
        If a line does not start with an uppercase word and end with a colon and there is an active
        labeled section, then that line is appended to that section’s content.
    
    The final JSON structure nests the document under two keys (both the filename).
    """
    lines = pdf_text.splitlines()
    # Compute a document-level hash based on the full text.
    hash_document = hash_content(pdf_text.strip())
    
    if DEBUG:
        print("\n=== DEBUG: Extracted First 1000 Characters ===")
        print(pdf_text[:1000])
    
    chapters = []
    current_chap = None
    current_sec = None
    current_sub = None

    # Optional: Remove trailing dot leaders and page numbers (e.g. "........ 17")
    dot_leader_pattern = re.compile(r'\.{5,}\s*(\d+)\s*$')

    for line in lines:
        stripped_line = line.strip()
        page_number = None
        try:
            m = dot_leader_pattern.search(stripped_line)
            if m:
                page_number = int(m.group(1))
                stripped_line = dot_leader_pattern.sub('', stripped_line).strip()
        except Exception as e:
            print(f"[Error] Removing trailing dots: {e}")
        
        # --- Ignore lines that end with a date or contain "REF:" ---
        if date_pattern.match(stripped_line) or meta_pattern.search(stripped_line):
            continue

        # --- STYLE A PATTERNS ---
        # (A1) Try Style A Section: starts with numbers and dot(s)
        sec_match = section_regex.match(stripped_line)
        if sec_match:
            sec_number = sec_match.group("number").strip()
            sec_title = sec_match.group("title").strip()
            current_sec = {
                'node_type': 'section',
                'number': sec_number,
                'title': sec_title,
                'content': '',
                'sublevels': [],
                'page_number': page_number
            }
            if current_chap is not None:
                current_chap.setdefault('sections', []).append(current_sec)
            current_sub = None
            continue

        # (A2) Try Style A Subsection: begins with a letter and a dot.
        sub_match = subsection_regex.match(stripped_line)
        if sub_match:
            sub_number = sub_match.group("number").strip()
            sub_title = sub_match.group("title").strip()  # In Style A, title goes into content.
            current_sub = {
                'node_type': 'subsection',
                'number': sub_number,
                'title': '',            # Title cleared per original requirement.
                'content': sub_title,
                'page_number': page_number,
                'sublevels': []
            }
            if current_sec is not None:
                current_sec.setdefault('sublevels', []).append(current_sub)
            continue

        # (A3) Try Style A Chapter:
        # Only treat as chapter if the line is all uppercase and contains at least one alphabetic character.
        if stripped_line and stripped_line == stripped_line.upper() and re.search('[A-Z]', stripped_line):
            num_match = number_in_line.search(stripped_line)
            chap_number = num_match.group(1) if num_match else ""
            current_chap = {
                'node_type': 'chapter',
                'number': chap_number,
                'title': stripped_line,
                'content': '',
                'sections': [],
                'page_number': page_number
            }
            chapters.append(current_chap)
            current_sec = None
            current_sub = None
            continue

        # --- STYLE B PATTERNS (if none of the above matched) ---
        # (B1) Try Style B Chapter: line ends with a 2–6 letter acronym in parentheses.
        chap_b_match = chapter_regex_b.match(stripped_line)
        if chap_b_match:
            chapter_title = chap_b_match.group("title").strip()
            # Only treat as a chapter if the title length is below a threshold (e.g., 60 characters)
            # to avoid picking up long content lines.
            if len(chapter_title) <= 60:
                num_match = number_in_line.search(chapter_title)
                chap_number = num_match.group(1) if num_match else ""
                current_chap = {
                    'node_type': 'chapter',
                    'number': chap_number,
                    'title': chapter_title,
                    'content': '',
                    'sections': [],
                    'page_number': page_number
                }
                chapters.append(current_chap)
                current_sec = None
                current_sub = None
                continue

        # (B2) Try Style B Section: line is all uppercase and ends with a semicolon.
        sec_b_match = section_regex_b.match(stripped_line)
        if sec_b_match:
            sec_title = sec_b_match.group("title").strip()
            num_match = number_in_line.search(sec_title)
            sec_number = num_match.group(1) if num_match else ""
            current_sec = {
                'node_type': 'section',
                'number': sec_number,
                'title': sec_title,
                'content': '',
                'sublevels': [],
                'page_number': page_number
            }
            if current_chap is not None:
                current_chap.setdefault('sections', []).append(current_sec)
            current_sub = None
            continue

        # (B3) Try Style B Subsection: line starts with a bullet point.
        sub_b_match = subsection_regex_b.match(stripped_line)
        if sub_b_match:
            sub_content = sub_b_match.group("content").strip()
            current_sub = {
                'node_type': 'subsection',
                'number': '',         # No number in Style B subsections.
                'title': '',          # Title cleared per original requirement.
                'content': sub_content,
                'page_number': page_number,
                'sublevels': []
            }
            if current_sec is not None:
                current_sec.setdefault('sublevels', []).append(current_sub)
            else:
                if current_chap is not None:
                    current_sec = {
                        'node_type': 'section',
                        'number': '',
                        'title': '',
                        'content': '',
                        'sublevels': [current_sub],
                        'page_number': page_number
                    }
                    current_chap.setdefault('sections', []).append(current_sec)
            continue

        # --- NEW RULE: Labeled Section (e.g. "PURPOSE: ...") ---
        labeled_match = labeled_section_regex.match(stripped_line)
        if labeled_match and current_chap is not None:
            label = labeled_match.group("label").strip()  # e.g. "PURPOSE:"
            sec_content = labeled_match.group("sec_content").strip()
            new_section = {
                'node_type': 'section',
                'number': '',   # No number for labeled sections.
                'title': label,
                'content': sec_content,
                'sublevels': [],
                'page_number': page_number
            }
            current_chap.setdefault("sections", []).append(new_section)
            current_sec = new_section  # Make it the active section.
            current_sub = None
            continue

        # --- NEW RULE: Labeled Section Continuation ---
        # If the current section is a labeled section (its title ends with ":") and
        # the current line does NOT itself start with an uppercase word and end with a colon,
        # then append this line to the current section's content.
        if current_sec is not None and current_sec.get("title", "").strip().endswith(":"):
            if not (stripped_line and stripped_line[0].isupper() and stripped_line.endswith(":")):
                current_sec["content"] += "\n" + stripped_line
                continue

        # --- Append non-heading lines as content ---
        if current_sub is not None:
            current_sub["content"] += "\n" + stripped_line
        elif current_sec is not None:
            current_sec["content"] += "\n" + stripped_line
        elif current_chap is not None:
            current_chap["content"] += "\n" + stripped_line
        # Otherwise, if no heading is active, skip the line.
    
    # Build the document dictionary.
    doc = {
        "title": document_title,
        "hash_document": hash_content(pdf_text.strip()),
        "chapters": chapters
    }
    # Wrap the document dict one extra level keyed by the filename.
    return {document_filename: {document_filename: doc}}

# ------------------------------------------------------------------------------
# HASHING FUNCTIONS
# ------------------------------------------------------------------------------
def compute_node_hash(node: dict) -> str:
    """
    Recursively compute and assign a hash for the given node by combining:
      - node_type, number, title, content, page_number
      - and the hashes of any children (sections or sublevels).
    The computed hash is stored under an appropriate key:
      - For chapter nodes: "hash_chapter"
      - For section nodes: "hash_section"
      - For subsection nodes: "hash_subsection"
      - Otherwise, use "hash"
    """
    combined = (
        str(node.get("node_type", "")) +
        str(node.get("number", "")) +
        str(node.get("title", "")) +
        str(node.get("content", "")) +
        str(node.get("page_number", ""))
    )
    if "sections" in node:
        for sec in node["sections"]:
            combined += compute_node_hash(sec)
    if "sublevels" in node:
        for sub in node["sublevels"]:
            combined += compute_node_hash(sub)
    computed = hash_content(combined)
    if node.get("node_type") == "chapter":
        node["hash_chapter"] = computed
    elif node.get("node_type") == "section":
        node["hash_section"] = computed
    elif node.get("node_type") == "subsection":
        node["hash_subsection"] = computed
    else:
        node["hash"] = computed
    return computed

def update_document_hash(doc: dict):
    """
    For a document dict, compute a document-level hash that includes:
      - The document title, the full-document hash (hash_document)
      - and the combined hash of all chapters.
    The computed hash is stored in doc["hash"].
    """
    combined = doc.get("title", "") + doc.get("hash_document", "")
    for chapter in doc.get("chapters", []):
        combined += compute_node_hash(chapter)
    doc["hash"] = hash_content(combined)

# ------------------------------------------------------------------------------
# PROCESSING ALL PDFS AND WRITING COMBINED JSON
# ------------------------------------------------------------------------------
def generate_pdf_hashes(pdf_folder: str, json_folder: str, output_filename: str):
    """
    Process all PDF files in the given folder:
      - Extract text and build the document structure.
      - Compute content hashes at every level.
    The results from all PDFs are combined into one JSON file.
    """
    os.makedirs(json_folder, exist_ok=True)
    all_data = {}

    pdf_files = [f for f in os.listdir(pdf_folder) if f.lower().endswith('.pdf')]
    for pdf_file in tqdm(pdf_files, desc="Processing PDFs"):
        pdf_path = os.path.join(pdf_folder, pdf_file)
        try:
            pdf_text = extract_text_from_pdf(pdf_path)
            if not pdf_text.strip():
                print(f"[Warning] No text extracted from {pdf_file}. Skipping.")
                continue
            document_title = os.path.splitext(pdf_file)[0]
            parsed_data = parse_pdf_structure(pdf_text, document_title, pdf_file)
            # Merge into the combined dictionary.
            all_data.update(parsed_data)
        except Exception as e:
            print(f"[Error] Processing file {pdf_file}: {e}")

    # Update document-level hashes.
    for file_key, inner_dict in all_data.items():
        for doc_key, doc in inner_dict.items():
            update_document_hash(doc)

    # Write the combined JSON output.
    output_json_path = os.path.join(json_folder, output_filename)
    try:
        with open(output_json_path, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, indent=2, ensure_ascii=False)
        print(f"\nCombined JSON output saved to: {output_json_path}")
    except Exception as e:
        print(f"[Error] Writing JSON output: {e}")

# ------------------------------------------------------------------------------
# MAIN
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    generate_pdf_hashes(PDF_FILE_PATH, JSON_OUTPUT_PATH, OUTPUT_JSON_FILENAME)
