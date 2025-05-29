from neo4j import GraphDatabase
import time
import sys
import os
import logging
from knowledge_graph import KnowledgeGraph
from contextlib import contextmanager

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class Neo4jConnectionPool:
    """A simple connection pool for Neo4j"""
    
    def __init__(self, uri, user, password, max_connections=10):
        self.uri = uri
        self.user = user
        self.password = password
        self.max_connections = max_connections
        self._pool = []
        self._used = {}
        
    def get_driver(self):
        """Get a driver from the pool or create a new one if needed"""
        if self._pool:
            driver = self._pool.pop()
            self._used[id(driver)] = driver
            return driver
            
        # Create a new driver if the pool is empty
        driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
        self._used[id(driver)] = driver
        return driver
        
    def release(self, driver):
        """Release a driver back to the pool"""
        driver_id = id(driver)
        if driver_id in self._used:
            if len(self._pool) < self.max_connections:
                self._pool.append(driver)
            else:
                driver.close()
            del self._used[driver_id]
            
    def close_all(self):
        """Close all connections in the pool"""
        # Close drivers in use
        for driver in self._used.values():
            try:
                driver.close()
            except:
                pass
        self._used.clear()
        
        # Close drivers in pool
        for driver in self._pool:
            try:
                driver.close()
            except:
                pass
        self._pool.clear()

class Neo4jLauncher:
    def __init__(self, uri="neo4j://172.18.0.3:7687", user="neo4j", password="password"):
        self.uri = uri
        self.user = user
        self.password = password
        self.pool = Neo4jConnectionPool(uri, user, password)
        
    @contextmanager
    def get_session(self):
        """Context manager for Neo4j sessions"""
        driver = None
        try:
            driver = self.pool.get_driver()
            session = driver.session()
            yield session
        finally:
            if session:
                session.close()
            if driver:
                self.pool.release(driver)

    def connect(self, max_retries=5, retry_interval=5):
        """Attempt to connect to Neo4j with retries"""
        for attempt in range(max_retries):
            try:
                # Get a driver to test connection
                driver = self.pool.get_driver()
                # Verify connection
                driver.verify_connectivity()
                logger.info(f"Successfully connected to Neo4j at {self.uri}")
                # Release the driver back to the pool
                self.pool.release(driver)
                return True
            except Exception as e:
                logger.error(f"Attempt {attempt + 1}/{max_retries} failed: {str(e)}")
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {retry_interval} seconds...")
                    time.sleep(retry_interval)
                else:
                    logger.error("Failed to connect to Neo4j after all attempts")
                    return False

    def setup_database(self):
        """Set up initial database configuration"""
        try:
            with self.get_session() as session:
                # Create constraints
                session.run("""
                    CREATE CONSTRAINT IF NOT EXISTS FOR (d:Document)
                    REQUIRE d.title IS UNIQUE
                """)
                
                session.run("""
                    CREATE CONSTRAINT IF NOT EXISTS FOR (c:Chapter)
                    REQUIRE c.hash IS UNIQUE
                """)
                
                session.run("""
                    CREATE CONSTRAINT IF NOT EXISTS FOR (s:Section)
                    REQUIRE s.hash IS UNIQUE
                """)
                
                session.run("""
                    CREATE CONSTRAINT IF NOT EXISTS FOR (sub:Subsection)
                    REQUIRE sub.hash IS UNIQUE
                """)

                # Create full-text indexes
                session.run("""
                    CREATE FULLTEXT INDEX combinedIndex IF NOT EXISTS
                    FOR (n:Document|Chapter|Section|Subsection)
                    ON EACH [n.title, n.content]
                """)

                logger.info("Successfully set up Neo4j database configuration")
                return True
        except Exception as e:
            logger.error(f"Error setting up database: {str(e)}")
            return False
    
    def load_json_data(self, json_path, batch_size=100):
        """Load JSON data into Neo4j using KnowledgeGraph with batching"""
        if not os.path.exists(json_path):
            logger.error(f"JSON file not found: {json_path}")
            return False
            
        try:
            # Use our optimized connection
            kg = KnowledgeGraph(self.uri, self.user, self.password)
            # Set batch size for processing
            kg.batch_size = batch_size
            # Process the JSON file
            kg.process_json(json_path)
            kg.close()
            logger.info(f"Successfully loaded data from {json_path} into Neo4j")
            return True
        except Exception as e:
            logger.error(f"Error loading JSON data: {str(e)}")
            return False

    def close(self):
        """Close all Neo4j connections"""
        self.pool.close_all()
        logger.info("All Neo4j connections closed")

def main():
    # JSON file path
    json_path = "/home/cm36/Updated-LLM-Project/J1_corpus/json/kg/combined_output_3.json"
    
    # Create launcher instance
    launcher = Neo4jLauncher()

    try:
        # Connect to Neo4j
        if not launcher.connect():
            logger.error("Failed to connect to Neo4j")
            sys.exit(1)

        # Set up database
        if not launcher.setup_database():
            logger.error("Failed to set up Neo4j database")
            sys.exit(1)
            
        # Load JSON data with larger batch size for better performance
        if not launcher.load_json_data(json_path, batch_size=500):
            logger.warning("Warning: Failed to load JSON data, but continuing...")

        logger.info("Neo4j database is ready for use")
        
        # Keep the script running
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("\nShutting down Neo4j connection...")
            launcher.close()

    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        launcher.close()
        sys.exit(1)

if __name__ == "__main__":
    main() 