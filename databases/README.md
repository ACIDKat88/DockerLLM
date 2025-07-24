# Database Integration Pipeline

This directory contains scripts for processing JSON data and loading it into Neo4j and PostgreSQL databases. The pipeline has been optimized for performance and reliability.

## Optimized Workflow

The recommended workflow is:

1. **Fix JSON Hashes** - Ensure all documents have proper hash identifiers
2. **Process in Parallel** - Load data into both Neo4j and PostgreSQL efficiently
3. **Verify** - Confirm data was loaded correctly

## Main Scripts

### parallel_process.py

This is the primary script that handles the entire pipeline. It:
- Fixes JSON hashes in parallel
- Loads data into Neo4j and PostgreSQL concurrently
- Supports batch processing for performance optimization

```bash
# Basic usage:
python parallel_process.py

# Advanced usage with batch sizes:
python parallel_process.py --workers=4 --pg-batch=500 --neo4j-batch=200
```

### Additional Scripts

- **fix_json_hashes.py** - Standalone script to fix hash identifiers in JSON files
- **json2pgvector.py** - Loads data into PostgreSQL with pgvector extension
- **launch_neo4j.py** - Connects to and sets up Neo4j database with optimized connection handling
- **check_missing_hashes.py** - Diagnostic tool to check for missing hash identifiers
- **process_one_file.py** - Processes a single JSON file (for targeted updates)

## Performance Optimizations

This pipeline includes several performance optimizations:

1. **Connection Pooling** - Efficient database connections with automatic retry
2. **Batch Processing** - Reduced database round-trips through batch operations
3. **Parallel Processing** - Multi-core utilization through parallel workers
4. **Error Handling** - Robust error recovery to continue processing even after failures
5. **Hashing** - Pre-hashing with shared hash maps for consistent ID generation

## Configuration

Environment variables for database connections:

```
# PostgreSQL
DB_HOST=postgres
DB_PORT=5432
DB_NAME=j1chat
DB_USER=postgres
DB_PASSWORD=password

# Neo4j
NEO4J_URI=neo4j://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
```

## JSON File Paths

Default paths for JSON files:

- Main: `/app/combined_output_3.json`
- Air Force: `/app/combined_output_3_airforce.json`
- GS: `/app/combined_output_3_gs.json`

## Monitoring

All scripts include detailed logging that can be monitored during execution:

```bash
# To run with output to both console and file:
python parallel_process.py | tee processing.log
``` 