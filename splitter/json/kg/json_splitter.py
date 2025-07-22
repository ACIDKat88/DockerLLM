import json
import sys
import os

input_file = "/home/cm36/Updated-LLM-Project/J1_corpus/json/kg/combined_output_3.json"

# Define hash lists for Air Force and GS categories
AIRFORCE_HASHES = {
    "68f64451e8f4b3fca106832ff6424f10",
    "a41f5621361882c453fb60722534b091",
    "505781eb2e4a5d90f1db8b2d36dcb6e7",
    "1d2175715d142564f5f8a30660e8d9bb",
    "9f165c527866e6f6a76d8c33ae534419",
    "1ef2222ae4a88763ee3bc7f1407568f8",
    "74e49f67b12bfc23a4b8b3c7a981076a",
    "76a084e6d1bef0ee4fc9685f94ac74f3",
    "2f16c794834af1e6797b04e13b6f16bb",
    "2170b7fd2d1e9dbf4fe1fcbe9de9e366"
}

GS_HASHES = {
    "bdc5452d803ed567aa1a87de06652ca1",
    "4b446523991ede9b87c15cc0beb8e0dc",
    "be1df423066a900a0f5bb43a794f56d3",
    "9c4ee6ce779f27eb2be505bf50c20895",
    "4647cc3cefaa3ec8cc6e24e7dc3ae35b",
    "68f64451e8f4b3fca106832ff6424f10",  # Note: overlaps with Air Force
    "a41f5621361882c453fb60722534b091",  # Note: overlaps with Air Force
    "505781eb2e4a5d90f1db8b2d36dcb6e7"   # Note: overlaps with Air Force
}

def find_hash_document(obj):
    """Recursively search for hash_document in a nested object."""
    if isinstance(obj, dict):
        # Direct check for hash_document in this dictionary
        if "hash_document" in obj:
            return obj["hash_document"]
        
        # Check each value in this dictionary
        for key, value in obj.items():
            result = find_hash_document(value)
            if result:
                return result
    elif isinstance(obj, list):
        # Check each item in the list
        for item in obj:
            result = find_hash_document(item)
            if result:
                return result
    return None

def process_document(item, hash_value=None):
    """Process a document with its hash value for classification."""
    # If no hash was provided, try to find it
    if not hash_value:
        hash_value = find_hash_document(item)
    
    results = {
        "item": item,
        "hash": hash_value,
        "is_airforce": hash_value in AIRFORCE_HASHES if hash_value else False,
        "is_gs": hash_value in GS_HASHES if hash_value else False
    }
    return results

def split_json(input_file):
    """
    Split a JSON file into separate files based on hash_document values.
    """
    # Create output directory if it doesn't exist
    output_dir = os.path.dirname(input_file)
    if not output_dir:
        output_dir = '.'

    # Read the input JSON file
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return
    except Exception as e:
        print(f"Error reading file: {e}")
        return

    # Initialize containers for split data
    airforce_data = {}
    gs_data = {}
    unknown_data = {}  # For documents that don't match either hash list

    # Track which hashes were found
    found_airforce_hashes = set()
    found_gs_hashes = set()

    # Check if data is a dictionary with categories at the top level
    if isinstance(data, dict):
        for category, category_content in data.items():
            # Handle content in dictionaries
            if isinstance(category_content, dict):
                # Check if the content contains documents
                for doc_key, doc_content in category_content.items():
                    doc_info = process_document(doc_content)
                    
                    # Check where this document belongs
                    if doc_info["is_airforce"]:
                        if category not in airforce_data:
                            airforce_data[category] = {}
                        airforce_data[category][doc_key] = doc_content
                        found_airforce_hashes.add(doc_info["hash"])
                        print(f"Added to Air Force: {doc_info['hash']}")
                    
                    if doc_info["is_gs"]:
                        if category not in gs_data:
                            gs_data[category] = {}
                        gs_data[category][doc_key] = doc_content
                        found_gs_hashes.add(doc_info["hash"])
                        print(f"Added to GS: {doc_info['hash']}")
                    
                    if not doc_info["is_airforce"] and not doc_info["is_gs"] and doc_info["hash"]:
                        if category not in unknown_data:
                            unknown_data[category] = {}
                        unknown_data[category][doc_key] = doc_content
                        print(f"Unknown hash: {doc_info['hash']}")
            
            # Handle content in lists
            elif isinstance(category_content, list):
                for doc_content in category_content:
                    doc_info = process_document(doc_content)
                    
                    # Check where this document belongs
                    if doc_info["is_airforce"]:
                        if category not in airforce_data:
                            airforce_data[category] = []
                        airforce_data[category].append(doc_content)
                        found_airforce_hashes.add(doc_info["hash"])
                        print(f"Added to Air Force: {doc_info['hash']}")
                    
                    if doc_info["is_gs"]:
                        if category not in gs_data:
                            gs_data[category] = []
                        gs_data[category].append(doc_content)
                        found_gs_hashes.add(doc_info["hash"])
                        print(f"Added to GS: {doc_info['hash']}")
                    
                    if not doc_info["is_airforce"] and not doc_info["is_gs"] and doc_info["hash"]:
                        if category not in unknown_data:
                            unknown_data[category] = []
                        unknown_data[category].append(doc_content)
                        print(f"Unknown hash: {doc_info['hash']}")
    
    # Write output files
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    
    airforce_file = os.path.join(output_dir, f"{base_name}_airforce.json")
    with open(airforce_file, 'w', encoding='utf-8') as f:
        json.dump(airforce_data, f, indent=2)
    print(f"Air Force data written to: {airforce_file}")
    
    gs_file = os.path.join(output_dir, f"{base_name}_stratcom.json")
    with open(gs_file, 'w', encoding='utf-8') as f:
        json.dump(gs_data, f, indent=2)
    print(f"GS data written to: {gs_file}")
    
    # Optionally write unknown data
    unknown_file = os.path.join(output_dir, f"{base_name}_unknown.json")
    with open(unknown_file, 'w', encoding='utf-8') as f:
        json.dump(unknown_data, f, indent=2)
    print(f"Unknown data written to: {unknown_file}")
    
    # Report missing hashes
    missing_airforce = AIRFORCE_HASHES - found_airforce_hashes
    missing_gs = GS_HASHES - found_gs_hashes
    
    if missing_airforce:
        print("Missing Air Force hashes:")
        for hash_val in missing_airforce:
            print(f"  - {hash_val}")
            
    if missing_gs:
        print("Missing GS hashes:")
        for hash_val in missing_gs:
            print(f"  - {hash_val}")
    
    # Print stats
    print(f"\nSummary:")
    print(f"  - Air Force documents found: {len(found_airforce_hashes)}/{len(AIRFORCE_HASHES)}")
    print(f"  - GS documents found: {len(found_gs_hashes)}/{len(GS_HASHES)}")

if __name__ == "__main__":
    # Check if the file exists
    if not os.path.exists(input_file):
        print(f"Error: File '{input_file}' not found.")
        sys.exit(1)
    
    split_json(input_file) 
