#!/bin/bash

# # Copy db_utils.py from fast-api directory
# echo "Copying db_utils.py from fast-api directory..."
# cp /app/../fast-api/db_utils.py /app/ 2>/dev/null || echo "Warning: Failed to copy db_utils.py"

# # Wait for the PostgreSQL server to be ready
# echo "Waiting for PostgreSQL..."
# while ! pg_isready -h $POSTGRES_HOST -p 5432 -U $POSTGRES_USER; do
#   echo "PostgreSQL is not ready yet... waiting"
#   sleep 2
# done
# echo "PostgreSQL is ready!"

# # Run the database initialization script
# echo "Setting up PostgreSQL database schema..."
# python launch_postgres.py --host $POSTGRES_HOST --user $POSTGRES_USER --password $POSTGRES_PASSWORD --dbname $POSTGRES_DB

# # Create an admin user
# echo "Creating admin user..."
# PGPASSWORD=$POSTGRES_PASSWORD psql -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB -c "DO \$\$ BEGIN IF NOT EXISTS (SELECT 1 FROM users WHERE username='admin') THEN INSERT INTO users (user_id, username, password_hash, role, is_admin) VALUES ('00000000-0000-0000-0000-000000000000', 'admin', '\$2b\$12\$KD9m1rIQehqi5NFR0sGCp.lM8mnxwmEG4qw0.6vP1zMqyGn78HQHy', 'admin', TRUE); END IF; END \$\$;"

# # Run vectorization scripts
# echo "Running vectorization scripts..."
# echo "Loading data into PostgreSQL vector database..."
# python json2pgvector.py || echo "Warning: Error in loading vectors into PostgreSQL"

# Only wait for Neo4j when needed for knowledge graph
if [ -f "/app/knowledge_graph.py" ]; then
  echo "Loading data into Neo4j..."
  # Wait for Neo4j to be ready
  echo "Waiting for Neo4j..."
  for i in {1..30}; do
    if nc -z $NEO4J_URI 7687 2>/dev/null; then
      echo "Neo4j is ready!"
      break
    fi
    echo "Neo4j is not ready yet... waiting"
    sleep 2
    if [ $i -eq 30 ]; then
      echo "Warning: Could not connect to Neo4j after 30 attempts, but continuing..."
    fi
  done
  python knowledge_graph.py || echo "Warning: Error in loading knowledge graph"
fi

echo "Data loading complete!"

# Sleep to keep the container running if needed
tail -f /dev/null 