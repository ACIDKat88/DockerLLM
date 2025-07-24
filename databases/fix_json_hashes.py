import json
import hashlib
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Global hash mappings to ensure consistency across files
doc_hash_map = {}  # Maps doc_title -> hash
chap_hash_map = {}  # Maps doc_hash+chap_title+chap_number -> hash
sec_hash_map = {}  # Maps chap_hash+sec_title+sec_number -> hash
subsec_hash_map = {}  # Maps sec_hash+sub_title+sub_number -> hash

def generate_hash(text):
    """Generate a MD5 hash for the given text."""
    return hashlib.md5(text.encode('utf-8')).hexdigest()

def fix_json_file(input_file, output_file=None, is_primary=False):
    """Fix the JSON file by adding missing hashes.
    
    Args:
        input_file: Path to the input JSON file
        output_file: Path to save the fixed JSON file (default: append "_fixed" to input filename)
        is_primary: If True, populate the global hash maps; if False, use existing hash maps
    """
    if output_file is None:
        # Default output is to add "_fixed" before the extension
        base, ext = os.path.splitext(input_file)
        output_file = f"{base}_fixed{ext}"
    
    logger.info(f"Processing {input_file} -> {output_file}")
    logger.info(f"Primary file: {is_primary}")
    
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    # Track counts of fixed items
    fixed_docs = 0
    fixed_chapters = 0
    fixed_sections = 0
    fixed_subsections = 0
    
    # Process all categories
    for category, docs in data.items():
        logger.info(f"Processing category: {category} with {len(docs)} documents")
        
        # Process all documents
        for doc_name, doc_data in docs.items():
            doc_title = doc_data.get("title", doc_name)
            
            # Fix document hash if missing
            if "hash_document" not in doc_data:
                # If we already have a hash for this document, use it
                if doc_title in doc_hash_map:
                    doc_hash = doc_hash_map[doc_title]
                    logger.info(f"Using existing hash for document: {doc_title}")
                # Otherwise, generate a new hash
                else:
                    doc_hash = generate_hash(f"{category}|{doc_title}")
                    if is_primary:
                        doc_hash_map[doc_title] = doc_hash
                
                doc_data["hash_document"] = doc_hash
                fixed_docs += 1
                logger.info(f"Added hash to document: {doc_title}")
            else:
                # If the document already has a hash, record it for consistency
                if is_primary:
                    doc_hash_map[doc_title] = doc_data["hash_document"]
            
            # Process all chapters
            for chapter in doc_data.get('chapters', []):
                chap_title = chapter.get("title", "")
                chap_number = chapter.get("number", "")
                doc_hash = doc_data["hash_document"]
                chap_key = f"{doc_hash}|{chap_title}|{chap_number}"
                
                # Fix chapter hash if missing
                if "hash_chapter" not in chapter:
                    # If we already have a hash for this chapter, use it
                    if chap_key in chap_hash_map:
                        chap_hash = chap_hash_map[chap_key]
                        logger.info(f"Using existing hash for chapter: {chap_title}")
                    # Otherwise, generate a new hash
                    else:
                        chap_hash = generate_hash(chap_key)
                        if is_primary:
                            chap_hash_map[chap_key] = chap_hash
                    
                    chapter["hash_chapter"] = chap_hash
                    fixed_chapters += 1
                    logger.info(f"Added hash to chapter: {chap_title}")
                else:
                    # If the chapter already has a hash, record it for consistency
                    if is_primary:
                        chap_hash_map[chap_key] = chapter["hash_chapter"]
                
                # Process all sections
                for section in chapter.get('sections', []):
                    sec_title = section.get("title", "")
                    sec_number = section.get("number", "")
                    chap_hash = chapter["hash_chapter"]
                    sec_key = f"{chap_hash}|{sec_title}|{sec_number}"
                    
                    # Check if section has hash_subsection instead of hash_section
                    if "hash_section" not in section and "hash_subsection" in section:
                        section["hash_section"] = section.pop("hash_subsection")
                        fixed_sections += 1
                        logger.info(f"Moved hash_subsection to hash_section in section: {sec_title}")
                        
                        # Record this hash for consistency
                        if is_primary:
                            sec_hash_map[sec_key] = section["hash_section"]
                        continue
                    
                    # Fix section hash if missing
                    if "hash_section" not in section:
                        # If we already have a hash for this section, use it
                        if sec_key in sec_hash_map:
                            sec_hash = sec_hash_map[sec_key]
                            logger.info(f"Using existing hash for section: {sec_title}")
                        # Otherwise, generate a new hash
                        else:
                            sec_content = section.get("content", "")[:100]  # Use first 100 chars of content
                            sec_hash = generate_hash(f"{sec_key}|{sec_content}")
                            if is_primary:
                                sec_hash_map[sec_key] = sec_hash
                        
                        section["hash_section"] = sec_hash
                        fixed_sections += 1
                        logger.info(f"Added hash to section: {sec_title}")
                    else:
                        # If the section already has a hash, record it for consistency
                        if is_primary:
                            sec_hash_map[sec_key] = section["hash_section"]
                    
                    # Process all subsections
                    for subsection in section.get('sublevels', []):
                        sub_title = subsection.get("title", "")
                        sub_number = subsection.get("number", "")
                        sec_hash = section["hash_section"]
                        sub_key = f"{sec_hash}|{sub_title}|{sub_number}"
                        
                        # Fix subsection hash if missing
                        if "hash_subsection" not in subsection:
                            # If we already have a hash for this subsection, use it
                            if sub_key in subsec_hash_map:
                                sub_hash = subsec_hash_map[sub_key]
                                logger.info(f"Using existing hash for subsection: {sub_number} - {sub_title}")
                            # Otherwise, generate a new hash
                            else:
                                sub_content = subsection.get("content", "")[:100]  # Use first 100 chars of content
                                sub_hash = generate_hash(f"{sub_key}|{sub_content}")
                                if is_primary:
                                    subsec_hash_map[sub_key] = sub_hash
                            
                            subsection["hash_subsection"] = sub_hash
                            fixed_subsections += 1
                            logger.info(f"Added hash to subsection: {sub_number} - {sub_title}")
                        else:
                            # If the subsection already has a hash, record it for consistency
                            if is_primary:
                                subsec_hash_map[sub_key] = subsection["hash_subsection"]
    
    # Save the fixed JSON file
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    logger.info(f"Fixed JSON saved to {output_file}")
    logger.info(f"Summary of fixes:")
    logger.info(f"  Documents: {fixed_docs}")
    logger.info(f"  Chapters: {fixed_chapters}")
    logger.info(f"  Sections: {fixed_sections}")
    logger.info(f"  Subsections: {fixed_subsections}")
    
    if is_primary:
        logger.info(f"Populated hash maps: {len(doc_hash_map)} docs, {len(chap_hash_map)} chapters, {len(sec_hash_map)} sections, {len(subsec_hash_map)} subsections")
    
    return output_file

def main():
    # JSON files to fix
    json_files = [
        "/app/combined_output_3.json",
        "/app/combined_output_3_gs.json",
        "/app/combined_output_3_airforce.json"
    ]
    
    fixed_files = []
    
    # First, process the primary file to populate hash maps
    primary_file = json_files[0]
    if os.path.exists(primary_file):
        fixed_file = fix_json_file(primary_file, is_primary=True)
        fixed_files.append(fixed_file)
        logger.info(f"Processed primary file: {primary_file}")
    else:
        logger.warning(f"Primary file not found: {primary_file}")
    
    # Then, process the secondary files using the populated hash maps
    for json_file in json_files[1:]:
        if os.path.exists(json_file):
            fixed_file = fix_json_file(json_file, is_primary=False)
            fixed_files.append(fixed_file)
        else:
            logger.warning(f"File not found: {json_file}")
    
    logger.info(f"All done! Fixed {len(fixed_files)} JSON files.")
    
    # Return the fixed files so they can be used in subsequent steps
    return fixed_files

if __name__ == "__main__":
    main() 