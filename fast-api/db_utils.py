import os
import logging
from db_pool import get_connection, release_connection, initialize_pool, close_pool, with_connection

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Initialize environment variables for the pool
os.environ.setdefault("DB_HOST", "docker-llm-postgres--6b5efca2ab.platform--j-6--chatbot--f4045690a8e475fc389a60ca")
os.environ.setdefault("DB_PORT", "5432")
os.environ.setdefault("DB_NAME", "postgres")
os.environ.setdefault("DB_USER", "postgres")
os.environ.setdefault("DB_PASSWORD", "password")

def connect_db():
    """Legacy function that uses the connection pool instead of creating a new connection.
    This provides backward compatibility with existing code."""
    return get_connection()
