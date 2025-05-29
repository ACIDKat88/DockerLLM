import json

def check_missing_hashes():
    """Check for missing hash values in the JSON structure."""
    with open('/app/combined_output_3.json', 'r') as f:
        data = json.load(f)
    
    missing_doc_hashes = 0
    missing_chapter_hashes = 0
    missing_section_hashes = 0
    missing_subsection_hashes = 0
    
    total_docs = 0
    total_chapters = 0
    total_sections = 0
    total_subsections = 0
    
    # Iterate through categories
    for category, docs in data.items():
        # Iterate through documents
        for doc_name, doc_data in docs.items():
            total_docs += 1
            if "hash_document" not in doc_data:
                missing_doc_hashes += 1
                print(f"Document missing hash: {doc_name}")
            
            # Iterate through chapters
            for i, chapter in enumerate(doc_data.get('chapters', [])):
                total_chapters += 1
                if "hash_chapter" not in chapter:
                    missing_chapter_hashes += 1
                    print(f"Chapter missing hash in document {doc_name}: Chapter {i+1}")
                
                # Iterate through sections
                for j, section in enumerate(chapter.get('sections', [])):
                    total_sections += 1
                    if "hash_section" not in section:
                        missing_section_hashes += 1
                        section_info = f"Section {section.get('number', j+1)}: {section.get('title', 'Unknown')}"
                        print(f"Section missing hash in document {doc_name}, chapter {chapter.get('title', i+1)}: {section_info}")
                        # Print the section keys to see what's available
                        print(f"  Section keys: {list(section.keys())}")
                    
                    # Iterate through subsections
                    for k, subsection in enumerate(section.get('sublevels', [])):
                        total_subsections += 1
                        if "hash_subsection" not in subsection:
                            missing_subsection_hashes += 1
                            subsection_info = f"Subsection {subsection.get('number', k+1)}"
                            print(f"Subsection missing hash in section {section.get('title', 'Unknown')}: {subsection_info}")
    
    # Print summary
    print("\nSummary:")
    print(f"Documents: {missing_doc_hashes}/{total_docs} missing hash ({missing_doc_hashes/total_docs*100:.1f}%)")
    print(f"Chapters: {missing_chapter_hashes}/{total_chapters} missing hash ({missing_chapter_hashes/total_chapters*100:.1f}%)")
    print(f"Sections: {missing_section_hashes}/{total_sections} missing hash ({missing_section_hashes/total_sections*100:.1f}%)")
    print(f"Subsections: {missing_subsection_hashes}/{total_subsections} missing hash ({missing_subsection_hashes/total_subsections*100:.1f}%)")

if __name__ == "__main__":
    check_missing_hashes() 