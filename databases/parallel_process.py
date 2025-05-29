import os
import sys
import logging
import json
import multiprocessing
import subprocess
import time
from functools import partial
import hashlib
from fix_json_hashes import fix_json_file, generate_hash

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(processName)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global hash mappings shared between processes
manager = multiprocessing.Manager()
doc_hash_map = manager.dict()
chap_hash_map = manager.dict()
sec_hash_map = manager.dict()
subsec_hash_map = manager.dict()

def fix_json_files_parallel(json_files, max_workers=None):
    """
    Fix JSON files in parallel to add missing hashes.
    
    Args:
        json_files: List of JSON files to fix
        max_workers: Maximum number of parallel workers
    
    Returns:
        List of fixed JSON file paths
    """
    if not max_workers:
        max_workers = max(1, multiprocessing.cpu_count() - 1)
    
    logger.info(f"Fixing {len(json_files)} JSON files with {max_workers} workers")
    
    # Process primary file first to populate hash maps
    primary_file = json_files[0]
    if not os.path.exists(primary_file):
        logger.error(f"Primary file not found: {primary_file}")
        return []
    
    # Process primary file
    logger.info(f"Processing primary file: {primary_file}")
    base, ext = os.path.splitext(primary_file)
    primary_output = f"{base}_fixed{ext}"
    
    try:
        # Fix primary file and populate hash maps
        fixed_primary = fix_json_file(primary_file, primary_output, is_primary=True)
        logger.info(f"Primary file fixed: {fixed_primary}")
        
        # Extract hash maps from primary file
        with open(fixed_primary, 'r') as f:
            data = json.load(f)
            
        # Populate shared hash maps
        for category, docs in data.items():
            for doc_name, doc_data in docs.items():
                if "hash_document" in doc_data:
                    doc_hash_map[doc_data.get("title", doc_name)] = doc_data["hash_document"]
                
                for chapter in doc_data.get('chapters', []):
                    if "hash_chapter" in chapter:
                        chap_key = f"{doc_data['hash_document']}|{chapter.get('title', '')}|{chapter.get('number', '')}"
                        chap_hash_map[chap_key] = chapter["hash_chapter"]
                    
                    for section in chapter.get('sections', []):
                        if "hash_section" in section:
                            sec_key = f"{chapter['hash_chapter']}|{section.get('title', '')}|{section.get('number', '')}"
                            sec_hash_map[sec_key] = section["hash_section"]
                        
                        for subsection in section.get('sublevels', []):
                            if "hash_subsection" in subsection:
                                sub_key = f"{section['hash_section']}|{subsection.get('title', '')}|{subsection.get('number', '')}"
                                subsec_hash_map[sub_key] = subsection["hash_subsection"]
        
        logger.info(f"Hash maps populated from primary file: {len(doc_hash_map)} docs, {len(chap_hash_map)} chapters, {len(sec_hash_map)} sections, {len(subsec_hash_map)} subsections")
        
        # Process secondary files in parallel
        secondary_files = json_files[1:]
        if secondary_files:
            logger.info(f"Processing {len(secondary_files)} secondary files in parallel")
            
            # Create output file paths
            outputs = []
            for file_path in secondary_files:
                base, ext = os.path.splitext(file_path)
                outputs.append(f"{base}_fixed{ext}")
            
            # Fix secondary files in parallel
            with multiprocessing.Pool(processes=max_workers) as pool:
                # We create a list of (input_file, output_file, is_primary) tuples
                file_args = list(zip(secondary_files, outputs, [False] * len(secondary_files)))
                # Use starmap to pass multiple arguments
                fixed_secondary = pool.starmap(fix_json_file_with_shared_maps, file_args)
                
            fixed_files = [fixed_primary] + fixed_secondary
            logger.info(f"All JSON files fixed successfully: {fixed_files}")
            return fixed_files
        else:
            logger.info("No secondary files to process")
            return [fixed_primary]
    except Exception as e:
        logger.error(f"Error fixing JSON files: {str(e)}")
        return []

def fix_json_file_with_shared_maps(input_file, output_file, is_primary):
    """
    Version of fix_json_file that uses the shared hash maps.
    This function is designed to be used with multiprocessing.
    """
    logger.info(f"Processing {input_file} -> {output_file}")
    
    try:
        with open(input_file, 'r') as f:
            data = json.load(f)
        
        # Track counts of fixed items
        fixed_docs = 0
        fixed_chapters = 0
        fixed_sections = 0
        fixed_subsections = 0
        
        # Process all categories
        for category, docs in data.items():
            # Process all documents
            for doc_name, doc_data in docs.items():
                doc_title = doc_data.get("title", doc_name)
                
                # Fix document hash if missing
                if "hash_document" not in doc_data:
                    # If we already have a hash for this document, use it
                    if doc_title in doc_hash_map:
                        doc_hash = doc_hash_map[doc_title]
                    # Otherwise, generate a new hash
                    else:
                        doc_hash = generate_hash(f"{category}|{doc_title}")
                    
                    doc_data["hash_document"] = doc_hash
                    fixed_docs += 1
                
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
                        # Otherwise, generate a new hash
                        else:
                            chap_hash = generate_hash(chap_key)
                        
                        chapter["hash_chapter"] = chap_hash
                        fixed_chapters += 1
                    
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
                            continue
                        
                        # Fix section hash if missing
                        if "hash_section" not in section:
                            # If we already have a hash for this section, use it
                            if sec_key in sec_hash_map:
                                sec_hash = sec_hash_map[sec_key]
                            # Otherwise, generate a new hash
                            else:
                                sec_content = section.get("content", "")[:100]  # Use first 100 chars of content
                                sec_hash = generate_hash(f"{sec_key}|{sec_content}")
                            
                            section["hash_section"] = sec_hash
                            fixed_sections += 1
                        
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
                                # Otherwise, generate a new hash
                                else:
                                    sub_content = subsection.get("content", "")[:100]  # Use first 100 chars of content
                                    sub_hash = generate_hash(f"{sub_key}|{sub_content}")
                                
                                subsection["hash_subsection"] = sub_hash
                                fixed_subsections += 1
        
        # Save the fixed JSON file
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Fixed JSON saved to {output_file} (docs: {fixed_docs}, chapters: {fixed_chapters}, sections: {fixed_sections}, subsections: {fixed_subsections})")
        return output_file
    except Exception as e:
        logger.error(f"Error fixing {input_file}: {str(e)}")
        return None

def process_file_pgvector(json_file, table_name, batch_size=1000):
    """Process a single file for PostgreSQL vector database with batch operations."""
    try:
        process_id = multiprocessing.current_process().name
        logger.info(f"[{process_id}] Loading {json_file} into PostgreSQL table {table_name}...")
        
        # Add batch_size parameter to json2pgvector.py call
        cmd = ["python", "/app/json2pgvector.py", 
               "--json_files", json_file, 
               "--table_names", table_name,
               "--batch_size", str(batch_size)]
        
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode == 0:
            logger.info(f"[{process_id}] Successfully loaded {json_file} into PostgreSQL table {table_name}")
            return True
        else:
            logger.error(f"[{process_id}] Failed to load {json_file} into PostgreSQL: {result.stderr.decode()}")
            return False
    except Exception as e:
        logger.error(f"[{process_id}] Error in PostgreSQL processing: {str(e)}")
        return False

def process_file_neo4j(json_file, neo4j_uri, neo4j_user, neo4j_password, batch_size=500):
    """Process a single file for Neo4j graph database with batch operations."""
    try:
        process_id = multiprocessing.current_process().name
        logger.info(f"[{process_id}] Loading {json_file} into Neo4j...")
        
        # Import here to avoid circular dependencies
        from knowledge_graph import KnowledgeGraph
        
        # Create knowledge graph with batch size
        kg = KnowledgeGraph(neo4j_uri, neo4j_user, neo4j_password)
        kg.batch_size = batch_size
        
        # Process the file
        success = kg.process_json(json_file)
        
        # Close connection
        kg.close()
        
        if success:
            logger.info(f"[{process_id}] Successfully loaded {json_file} into Neo4j")
            return True
        else:
            logger.error(f"[{process_id}] Failed to load {json_file} into Neo4j")
            return False
    except Exception as e:
        logger.error(f"[{process_id}] Error in Neo4j processing: {str(e)}")
        return False

def run_parallel_processing(files_and_tables, neo4j=True, postgres=True, max_workers=None, pg_batch_size=1000, neo4j_batch_size=500):
    """
    Process multiple files in parallel.
    
    Args:
        files_and_tables: List of tuples (json_file, table_name)
        neo4j: Whether to load into Neo4j
        postgres: Whether to load into PostgreSQL
        max_workers: Maximum number of parallel workers (defaults to CPU count)
        pg_batch_size: Batch size for PostgreSQL operations
        neo4j_batch_size: Batch size for Neo4j operations
    """
    if not max_workers:
        # Use CPU count - 1 to leave some resources for the system
        max_workers = max(1, multiprocessing.cpu_count() - 1)
    
    logger.info(f"Starting parallel processing with {max_workers} workers")
    logger.info(f"Processing {len(files_and_tables)} files")
    
    # Get Neo4j connection details from environment variables
    neo4j_uri = os.environ.get("NEO4J_URI", "neo4j://neo4j:7687")
    neo4j_user = os.environ.get("NEO4J_USER", "neo4j")
    neo4j_password = os.environ.get("NEO4J_PASSWORD", "password")
    
    results = {}
    
    # Process Neo4j in parallel if requested
    if neo4j:
        logger.info(f"Starting Neo4j parallel processing (batch size: {neo4j_batch_size})...")
        start_time = time.time()
        
        with multiprocessing.Pool(processes=max_workers) as pool:
            # Create a partial function with the Neo4j connection details and batch size
            process_func = partial(
                process_file_neo4j,
                neo4j_uri=neo4j_uri,
                neo4j_user=neo4j_user,
                neo4j_password=neo4j_password,
                batch_size=neo4j_batch_size
            )
            
            # Apply the function to each file
            neo4j_results = pool.map(process_func, [file for file, _ in files_and_tables])
            
        end_time = time.time()
        logger.info(f"Neo4j processing completed in {end_time - start_time:.2f} seconds")
        
        # Store results
        results["neo4j"] = {
            files_and_tables[i][0]: neo4j_results[i] 
            for i in range(len(files_and_tables))
        }
    
    # Process PostgreSQL in parallel if requested
    if postgres:
        logger.info(f"Starting PostgreSQL parallel processing (batch size: {pg_batch_size})...")
        start_time = time.time()
        
        with multiprocessing.Pool(processes=max_workers) as pool:
            # Create a list of arguments for each file (with batch size)
            args = [(file, table, pg_batch_size) for file, table in files_and_tables]
            
            # Apply the function to each file-table pair with batch size
            pg_results = pool.starmap(process_file_pgvector, args)
            
        end_time = time.time()
        logger.info(f"PostgreSQL processing completed in {end_time - start_time:.2f} seconds")
        
        # Store results
        results["postgres"] = {
            files_and_tables[i][0]: pg_results[i] 
            for i in range(len(files_and_tables))
        }
    
    return results

def main():
    # Parse command line arguments for batch sizes
    pg_batch_size = 1000
    neo4j_batch_size = 500
    
    for arg in sys.argv:
        if arg.startswith("--pg-batch="):
            try:
                pg_batch_size = int(arg.split("=")[1])
            except (ValueError, IndexError):
                logger.error(f"Invalid PostgreSQL batch size: {arg}")
                return 1
        elif arg.startswith("--neo4j-batch="):
            try:
                neo4j_batch_size = int(arg.split("=")[1])
            except (ValueError, IndexError):
                logger.error(f"Invalid Neo4j batch size: {arg}")
                return 1
    
    # Set up input JSON files - default paths
    json_files = [
        "/app/combined_output_3.json",
        "/app/combined_output_3_gs.json",
        "/app/combined_output_3_airforce.json"
    ]
    
    # Override with command line arguments if provided
    if any(arg.endswith(".json") for arg in sys.argv[1:] if not arg.startswith("--")):
        json_files = [arg for arg in sys.argv[1:] if arg.endswith(".json") and not arg.startswith("--")]
    
    # Parse max workers if specified
    max_workers = None
    for arg in sys.argv:
        if arg.startswith("--workers="):
            try:
                max_workers = int(arg.split("=")[1])
            except (ValueError, IndexError):
                logger.error(f"Invalid workers argument: {arg}")
                return 1
    
    # First fix the JSON files in parallel
    logger.info("Step 1: Fixing JSON files by adding missing hashes...")
    fixed_json_files = fix_json_files_parallel(json_files, max_workers)
    
    if not fixed_json_files:
        logger.error("No JSON files were fixed. Aborting.")
        sys.exit(1)
    
    logger.info(f"Successfully fixed {len(fixed_json_files)} JSON files")
    
    # Default file mappings for fixed files
    default_files_and_tables = []
    for json_file in fixed_json_files:
        if "airforce" in json_file.lower():
            table_name = "document_embeddings_airforce"
        elif "gs" in json_file.lower():
            table_name = "document_embeddings_gs"
        else:
            table_name = "document_embeddings_combined"
        default_files_and_tables.append((json_file, table_name))
    
    # Check for file:table mappings in command line arguments
    files_and_tables = []
    for arg in sys.argv[1:]:
        if ":" in arg and not arg.startswith("--"):
            try:
                file_path, table_name = arg.split(":")
                if os.path.exists(file_path):
                    files_and_tables.append((file_path, table_name))
                else:
                    logger.warning(f"File not found: {file_path}")
            except ValueError:
                logger.error(f"Invalid argument format: {arg}. Expected format: file_path:table_name")
    
    # Use command line mappings if provided, otherwise use defaults
    if not files_and_tables:
        files_and_tables = default_files_and_tables
    
    # Check for flags
    neo4j = "--no-neo4j" not in sys.argv
    postgres = "--no-postgres" not in sys.argv
    
    # Run parallel processing
    logger.info(f"Step 2: Starting parallel processing")
    logger.info(f"Neo4j: {neo4j}, PostgreSQL: {postgres}")
    logger.info(f"Files to process: {files_and_tables}")
    logger.info(f"Batch sizes - PostgreSQL: {pg_batch_size}, Neo4j: {neo4j_batch_size}")
    
    start_time = time.time()
    results = run_parallel_processing(
        files_and_tables, 
        neo4j, 
        postgres, 
        max_workers,
        pg_batch_size=pg_batch_size,
        neo4j_batch_size=neo4j_batch_size
    )
    end_time = time.time()
    
    # Summarize results
    logger.info(f"All processing completed in {end_time - start_time:.2f} seconds")
    
    if neo4j:
        neo4j_success = all(results.get("neo4j", {}).values())
        logger.info(f"Neo4j processing: {'Success' if neo4j_success else 'Failed'}")
    
    if postgres:
        postgres_success = all(results.get("postgres", {}).values())
        logger.info(f"PostgreSQL processing: {'Success' if postgres_success else 'Failed'}")
    
    success = (not neo4j or all(results.get("neo4j", {}).values())) and \
              (not postgres or all(results.get("postgres", {}).values()))
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 