-- Database optimization recommendations for vector retrieval performance
-- 
-- IMPORTANT: Run these commands one by one, NOT as a single transaction
-- CREATE INDEX CONCURRENTLY cannot run inside a transaction block
--
-- Execute each section separately in pgAdmin or run them individually

-- =================================================================
-- SECTION 1: Vector Similarity Indexes (Run these one at a time)
-- =================================================================

-- Base document_embeddings table
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_document_embeddings_embedding 
ON document_embeddings USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);

-- Combined dataset table
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_document_embeddings_combined_embedding 
ON document_embeddings_combined USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);

-- Air Force dataset table
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_document_embeddings_airforce_embedding 
ON document_embeddings_airforce USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);

-- GS dataset table
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_document_embeddings_gs_embedding 
ON document_embeddings_gs USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);

-- STRATCOM dataset table
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_document_embeddings_stratcom_embedding 
ON document_embeddings_stratcom USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);

-- =================================================================
-- SECTION 2: Hash-based Filtering Indexes (Run these one at a time)
-- =================================================================

-- Base table
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_document_embeddings_hash 
ON document_embeddings (hash_document);

-- Combined table
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_document_embeddings_combined_hash 
ON document_embeddings_combined (hash_document);

-- Air Force table
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_document_embeddings_airforce_hash 
ON document_embeddings_airforce (hash_document);

-- GS table
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_document_embeddings_gs_hash 
ON document_embeddings_gs (hash_document);

-- STRATCOM table
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_document_embeddings_stratcom_hash 
ON document_embeddings_stratcom (hash_document);

-- =================================================================
-- SECTION 3: Composite Indexes (Run these one at a time)
-- =================================================================

-- Base table
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_document_embeddings_composite 
ON document_embeddings (hash_document, document_title);

-- Combined table
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_document_embeddings_combined_composite 
ON document_embeddings_combined (hash_document, document_title);

-- Air Force table
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_document_embeddings_airforce_composite 
ON document_embeddings_airforce (hash_document, document_title);

-- GS table
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_document_embeddings_gs_composite 
ON document_embeddings_gs (hash_document, document_title);

-- STRATCOM table
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_document_embeddings_stratcom_composite 
ON document_embeddings_stratcom (hash_document, document_title);

-- =================================================================
-- SECTION 4: Update Table Statistics (Can be run as a batch)
-- =================================================================

ANALYZE document_embeddings;
ANALYZE document_embeddings_combined;
ANALYZE document_embeddings_airforce;
ANALYZE document_embeddings_gs;
ANALYZE document_embeddings_stratcom;

-- =================================================================
-- SECTION 5: PostgreSQL Configuration Recommendations
-- =================================================================
-- Add these to your postgresql.conf and restart PostgreSQL:
--
-- shared_preload_libraries = 'vector'
-- work_mem = '256MB'  -- Increase for better vector operations
-- maintenance_work_mem = '1GB'  -- For index creation
-- max_connections = 100  -- Adjust based on your connection pool settings
--
-- Optional: Enable parallel query execution for large datasets
-- max_parallel_workers_per_gather = 4
-- parallel_tuple_cost = 0.1
-- parallel_setup_cost = 1000.0
