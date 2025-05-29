import os
import sys
import logging
import hashlib
import json
from knowledge_graph import KnowledgeGraph

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def process_file(input_file, table_name, neo4j_load=True, postgres_load=True):
    """Process a single JSON file, fixing hashes if needed, then load into databases.
    
    Args:
        input_file: Path to JSON file to process
        table_name: PostgreSQL table name to load data into
        neo4j_load: Whether to load into Neo4j
        postgres_load: Whether to load into PostgreSQL
    """
    logger.info(f"Processing file: {input_file} for table: {table_name}")
    
    # Step 1: Check if the file exists
    if not os.path.exists(input_file):
        logger.error(f"File not found: {input_file}")
        return False
    
    # Step 2: Load into Neo4j if requested
    if neo4j_load:
        logger.info(f"Loading {input_file} into Neo4j...")
        try:
            # Get Neo4j connection details from environment variables
            neo4j_uri = os.environ.get("NEO4J_URI", "neo4j://neo4j:7687")
            neo4j_user = os.environ.get("NEO4J_USER", "neo4j")
            neo4j_password = os.environ.get("NEO4J_PASSWORD", "password")
            
            # Create knowledge graph
            kg = KnowledgeGraph(neo4j_uri, neo4j_user, neo4j_password)
            
            # Process the file
            success = kg.process_json(input_file)
            
            # Close connection
            kg.close()
            
            if success:
                logger.info(f"Successfully loaded {input_file} into Neo4j")
            else:
                logger.error(f"Failed to load {input_file} into Neo4j")
                
        except Exception as e:
            logger.error(f"Error loading into Neo4j: {str(e)}")
            return False
    
    # Step 3: Load into PostgreSQL if requested
    if postgres_load:
        logger.info(f"Loading {input_file} into PostgreSQL table {table_name}...")
        try:
            import subprocess
            cmd = ["python", "/app/json2pgvector.py", 
                   "--json_files", input_file, 
                   "--table_names", table_name]
            logger.info(f"Running command: {' '.join(cmd)}")
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            if result.returncode == 0:
                logger.info(f"Successfully loaded {input_file} into PostgreSQL table {table_name}")
            else:
                logger.error(f"Failed to load into PostgreSQL: {result.stderr.decode()}")
                return False
                
        except Exception as e:
            logger.error(f"Error loading into PostgreSQL: {str(e)}")
            return False
    
    logger.info(f"Successfully processed {input_file}")
    return True

def main():
    if len(sys.argv) < 3:
        print("Usage: process_one_file.py <json_file_path> <table_name> [--no-neo4j] [--no-postgres]")
        return 1
    
    input_file = sys.argv[1]
    table_name = sys.argv[2]
    
    # Check for optional flags
    neo4j_load = "--no-neo4j" not in sys.argv
    postgres_load = "--no-postgres" not in sys.argv
    
    success = process_file(input_file, table_name, neo4j_load, postgres_load)
    
    if success:
        logger.info("All operations completed successfully")
        return 0
    else:
        logger.error("Some operations failed. Check logs for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 