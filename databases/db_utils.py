import os
import logging
import sys

# Add the parent directory to sys.path to allow importing db_pool
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

try:
    from fast_api.db_pool import get_connection, release_connection, initialize_pool, close_pool, with_connection
except ImportError:
    # Fall back to looking in the current directory
    try:
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from db_pool import get_connection, release_connection, initialize_pool, close_pool, with_connection
    except ImportError:
        raise ImportError("Could not import db_pool module. Make sure it's in the path.")

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Initialize environment variables for the pool
os.environ.setdefault("DB_HOST", os.environ.get('POSTGRES_HOST', 'postgres'))
os.environ.setdefault("DB_PORT", os.environ.get('POSTGRES_PORT', '5432'))
os.environ.setdefault("DB_NAME", os.environ.get('POSTGRES_DB', 'j1chat'))
os.environ.setdefault("DB_USER", os.environ.get('POSTGRES_USER', 'postgres'))
os.environ.setdefault("DB_PASSWORD", os.environ.get('POSTGRES_PASSWORD', 'password'))

# Initialize the connection pool at module load time
try:
    initialize_pool()
    logger.info("Database connection pool initialized")
except Exception as e:
    logger.error(f"Failed to initialize connection pool: {e}")

def connect_db():
    """Legacy function that uses the connection pool instead of creating a new connection.
    This provides backward compatibility with existing code."""
    return get_connection()
