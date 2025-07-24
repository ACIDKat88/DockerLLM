# Use Python 3.10 slim image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    postgresql-client \
    curl \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir psycopg2-binary pandas numpy neo4j sentence-transformers==2.5.1

# Copy application files
COPY launch_postgres.py .
COPY launch_neo4j.py .
COPY json2pgvector.py .
COPY embedd_class.py .
COPY knowledge_graph.py .
COPY combined_output_3.json .
COPY combined_output_3_gs.json .
COPY combined_output_3_airforce.json .
COPY db_utils.py .
COPY db_pool.py . 
# Create a script to wait for databases and load data
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

# Set the entrypoint
ENTRYPOINT ["./entrypoint.sh"] 