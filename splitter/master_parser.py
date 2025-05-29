# master_parser.py
import os
import json
from airforceparser import AirForceParser
from miscparser import MiscParser
from stratcomparser import SIParser
#from genericparser import GenericParser
from knowledge_graph import KnowledgeGraph 

def main():
    # Define PDF folders (adjust these paths as needed)
    airforce_pdf_folder = '/home/cm36/Updated-LLM-Project/J1_corpus/cleaned/air_force'
    misc_pdf_folder = '/home/cm36/Updated-LLM-Project/J1_corpus/cleaned/single'
    stratcom_pdf_folder = '/home/cm36/Updated-LLM-Project/J1_corpus/cleaned/stratcom'
    #generic_pdf_folder  = '/home/cm36/Updated-LLM-Project/J1_corpus/cleaned/generic'
    
    # Define output folder and ensure it exists
    json_output_folder = '/home/cm36/Updated-LLM-Project/J1_corpus/json/kg'
    os.makedirs(json_output_folder, exist_ok=True)
    
    # Instantiate each parser
    airforceparser = AirForceParser(airforce_pdf_folder)
    miscparser = MiscParser(misc_pdf_folder)
    stratcomparser = SIParser(stratcom_pdf_folder)
    #genericparser = GenericParser(generic_pdf_folder)
    
    # Process PDFs with each parser
    results = {}
    results['airforce'] = airforceparser.process_pdfs()
    results['misc'] = miscparser.process_pdfs()
    results['stratcom'] = stratcomparser.process_pdfs()
    #results['generic'] = genericparser.process_pdfs() 
    
    # Combine the results into one JSON file
    output_file = os.path.join(json_output_folder, "combined_output_2.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"Combined JSON output saved to: {output_file}")

    # Call Knowledge Graph to process JSON into Neo4j
    graph_db = KnowledgeGraph(uri="bolt://62.10.106.165:7687", user="neo4j", password="password")
    graph_db.process_json(output_file)
    graph_db.close()
    
    print("Knowledge Graph processing completed successfully.")

if __name__ == "__main__":
    main()
