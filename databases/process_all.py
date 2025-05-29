import os
import sys
import logging
import json
import time
from fix_json_hashes import main as fix_json_files

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def load_into_postgres(json_files):
    """Load fixed JSON files into PostgreSQL using json2pgvector.py"""
    logger.info("Loading data into PostgreSQL vector database...")
    
    # Create config file for json2pgvector.py
    config = {}
    for json_file in json_files:
        if "airforce" in json_file:
            config[json_file] = "document_embeddings_airforce"
        elif "gs" in json_file:
            config[json_file] = "document_embeddings_gs"
        else:
            config[json_file] = "document_embeddings_combined"
    
    config_file = "/app/pgvector_config.json"
    with open(config_file, "w") as f:
        json.dump(config, f, indent=2)
    
    logger.info(f"Created config file at {config_file}: {config}")
    
    # Run json2pgvector.py with the config file
    import subprocess
    cmd = ["python", "/app/json2pgvector.py", "--config", config_file]
    logger.info(f"Running command: {' '.join(cmd)}")
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    if result.returncode == 0:
        logger.info("Successfully loaded data into PostgreSQL")
        return True
    else:
        logger.error(f"Failed to load data into PostgreSQL: {result.stderr.decode()}")
        return False

def load_into_neo4j(json_files):
    """Load fixed JSON files into Neo4j using knowledge_graph.py"""
    logger.info("Loading data into Neo4j...")
    
    # Import locally to avoid circular import
    from knowledge_graph import KnowledgeGraph
    
    # Get Neo4j connection details from environment variables
    neo4j_uri = os.environ.get("NEO4J_URI", "neo4j://neo4j:7687")
    neo4j_user = os.environ.get("NEO4J_USER", "neo4j")
    neo4j_password = os.environ.get("NEO4J_PASSWORD", "password")
    
    logger.info(f"Connecting to Neo4j at {neo4j_uri}...")
    
    try:
        # Create knowledge graph
        kg = KnowledgeGraph(neo4j_uri, neo4j_user, neo4j_password)
        
        # Process each JSON file
        success_count = 0
        for json_file in json_files:
            logger.info(f"Processing {json_file} for Neo4j...")
            if kg.process_json(json_file):
                success_count += 1
        
        # Close connection
        kg.close()
        logger.info(f"Neo4j data loading completed. Successfully processed {success_count}/{len(json_files)} files")
        return success_count == len(json_files)
        
    except Exception as e:
        logger.error(f"Error creating knowledge graph: {str(e)}")
        return False

def main():
    """Fix JSON files and load them into both databases"""
    logger.info("Starting complete data processing workflow...")
    
    # Step 1: Fix the JSON files
    logger.info("Step 1: Fixing JSON files by adding missing hashes...")
    fixed_json_files = fix_json_files()
    
    if not fixed_json_files:
        logger.error("No JSON files were fixed. Aborting.")
        sys.exit(1)
    
    # Step 2: Load into PostgreSQL
    logger.info("Step 2: Loading fixed JSON files into PostgreSQL...")
    postgres_success = load_into_postgres(fixed_json_files)
    
    # Step 3: Load into Neo4j
    logger.info("Step 3: Loading fixed JSON files into Neo4j...")
    neo4j_success = load_into_neo4j(fixed_json_files)
    
    # Summary
    logger.info("Data loading complete!")
    logger.info(f"PostgreSQL loading: {'Success' if postgres_success else 'Failed'}")
    logger.info(f"Neo4j loading: {'Success' if neo4j_success else 'Failed'}")
    
    if postgres_success and neo4j_success:
        logger.info("All operations completed successfully")
        return 0
    else:
        logger.warning("Some operations failed. Check logs for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 