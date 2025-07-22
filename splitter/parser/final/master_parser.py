import os
import json
import sys
from airforceparser import AirForceParser
from miscparser import MiscParser
from stratcomparser import SIParser
#from genericparser import GenericParser
from knowledge_graph import KnowledgeGraph 
from tqdm import tqdm
import nltk
from nltk.corpus import stopwords

# Download stopwords if not already downloaded
nltk.download('stopwords', quiet=True)
stop_words = set(stopwords.words('english'))

def remove_stopwords(text):
    """
    Removes stopwords from a given text string.
    """
    tokens = text.split()
    filtered_tokens = [token for token in tokens if token.lower() not in stop_words]
    return ' '.join(filtered_tokens)

def remove_stopwords_from_results(data):
    """
    Recursively traverse the data structure (dict, list, or str) and remove stopwords from all strings.
    """
    if isinstance(data, dict):
        return {key: remove_stopwords_from_results(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [remove_stopwords_from_results(item) for item in data]
    elif isinstance(data, str):
        return remove_stopwords(data)
    else:
        return data

def main():
    # Define PDF folders (adjust these paths as needed)
    airforce_pdf_folder = '/home/cm36/Updated-LLM-Project/J1_corpus/cleaned/air_force'
    misc_pdf_folder = '/home/cm36/Updated-LLM-Project/J1_corpus/cleaned/single'
    stratcom_pdf_folder = '/home/cm36/Updated-LLM-Project/J1_corpus/cleaned/stratcom'
    #generic_pdf_folder  = '/home/cm36/Updated-LLM-Project/J1_corpus/cleaned/generic'
    
    # Define output folder and ensure it exists
    json_output_folder = '/home/cm36/Updated-LLM-Project/J1_corpus/json/kg'
    os.makedirs(json_output_folder, exist_ok=True)
    
    output_file = os.path.join(json_output_folder, "combined_output_3.json")
    
    # Check if the JSON already exists; if not, process the PDFs.
    if not os.path.exists(output_file):
        # Instantiate each parser
        airforceparser = AirForceParser(airforce_pdf_folder)
        miscparser = MiscParser(misc_pdf_folder)
        stratcomparser = SIParser(stratcom_pdf_folder)
        #genericparser = GenericParser(generic_pdf_folder)
    
        # Wrap the parser processing loop in a tqdm progress bar.
        parsers = {
            "airforce": airforceparser,
            "misc": miscparser,
            "stratcom": stratcomparser
            # "generic": genericparser
        }
        results = {}
        for category, parser in tqdm(parsers.items(), desc="Processing parser categories"):
            results[category] = parser.process_pdfs()
        
        # Remove stop words from the results
        results = remove_stopwords_from_results(results)
    
        # Write the combined results to the JSON file.
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
    
        print(f"Combined JSON output saved to: {output_file}")
    else:
        print(f"JSON file already exists at {output_file}. Skipping PDF processing.")

    # Connect to Neo4j and process the JSON.
    # For a single instance, use the bolt URI.
    graph_db = KnowledgeGraph(uri="neo4j://62.10.106.165:7687", user="neo4j", password="password")
    graph_db.process_json(output_file)
    graph_db.close()
    
    print("Knowledge Graph processing completed successfully.")
    sys.exit(0)  # Force termination

if __name__ == "__main__":
    main()
