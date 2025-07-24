import os
import psycopg2
from psycopg2 import pool
import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('db_pool')

# Configuration (Hardcoded)
DB_HOST = "docker-llm-postgres--6b5efca2ab.platform--j-6--chatbot--f4045690a8e475fc389a60ca"
DB_PORT = "5432"
DB_NAME = "postgres"
DB_USER = "postgres"
DB_PASSWORD = "password"
MIN_CONNECTIONS = 5
MAX_CONNECTIONS = 100
CONNECTION_TIMEOUT = 30  # seconds

# Print connection details for verification
print(f"Connecting to database:")
print(f"  Host: {DB_HOST}")
print(f"  Port: {DB_PORT}")
print(f"  Name: {DB_NAME}")
print(f"  User: {DB_USER}")

# Initialize the connection pool as a global variable
connection_pool = None

def initialize_pool():
    """Initialize the PostgreSQL connection pool."""
    global connection_pool
    
    if connection_pool is not None:
        logger.info("Connection pool already initialized")
        return
    
    try:
        connection_pool = psycopg2.pool.ThreadedConnectionPool(
            minconn=MIN_CONNECTIONS,
            maxconn=MAX_CONNECTIONS,
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            connect_timeout=CONNECTION_TIMEOUT
        )
        logger.info(f"Connection pool initialized (min={MIN_CONNECTIONS}, max={MAX_CONNECTIONS})")
    except Exception as e:
        logger.error(f"Failed to initialize connection pool: {e}")
        connection_pool = None
        raise

def get_connection():
    """Get a connection from the pool."""
    global connection_pool
    
    if connection_pool is None:
        logger.info("Connection pool not initialized, initializing now")
        initialize_pool()
    
    # Retry logic for getting a connection
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            conn = connection_pool.getconn()
            if conn:
                # Test the connection with a simple query
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    cursor.fetchone()
                return conn
        except Exception as e:
            retry_count += 1
            logger.warning(f"Connection error (attempt {retry_count}/{max_retries}): {e}")
            
            # If connection was obtained but is bad, return it to the pool
            if 'conn' in locals() and conn:
                connection_pool.putconn(conn, close=True)
                
            if retry_count >= max_retries:
                logger.error(f"Failed to get a valid connection after {max_retries} attempts")
                return None
            
            # Wait before retrying
            time.sleep(1)
    
    return None

def release_connection(conn):
    """Return a connection to the pool."""
    global connection_pool
    
    if connection_pool is None or conn is None:
        return
    
    try:
        connection_pool.putconn(conn)
    except Exception as e:
        logger.error(f"Error releasing connection: {e}")
        # If we can't return it to the pool, try to close it
        try:
            conn.close()
        except:
            pass

def close_pool():
    """Close all connections in the pool."""
    global connection_pool
    
    if connection_pool is None:
        return
    
    try:
        connection_pool.closeall()
        logger.info("Connection pool closed")
    except Exception as e:
        logger.error(f"Error closing connection pool: {e}")
    finally:
        connection_pool = None

def with_connection(func):
    """
    Decorator for functions that need a database connection.
    Handles getting and releasing the connection automatically.
    """
    def wrapper(*args, **kwargs):
        conn = get_connection()
        if not conn:
            raise Exception("Could not obtain database connection")
        
        try:
            # Add connection as first argument
            result = func(conn, *args, **kwargs)
            conn.commit()
            return result
        except Exception as e:
            conn.rollback()
            logger.error(f"Database operation failed: {e}")
            raise
        finally:
            release_connection(conn)
    
    return wrapper

# Create a backwards-compatible connect_db function
def connect_db():
    """Legacy function for backwards compatibility"""
    return get_connection()
