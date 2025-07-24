import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import time
import sys
import uuid
import bcrypt
from datetime import datetime

def connect_db(max_retries=5, retry_interval=5):
    """Connect to PostgreSQL database"""
    dbname = "postgres"
    user = "postgres"
    password = "password"
    host = "postgres"
    port = "5432"
    
    for attempt in range(max_retries):
        try:
            # Connect to postgres database
            conn = psycopg2.connect(
                dbname=dbname,
                user=user,
                password=password,
                host=host,
                port=port
            )
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            print(f"Successfully connected to PostgreSQL at {host}:{port}")
            return conn
        except Exception as e:
            print(f"Attempt {attempt + 1}/{max_retries} failed: {str(e)}")
            if attempt < max_retries - 1:
                print(f"Retrying in {retry_interval} seconds...")
                time.sleep(retry_interval)
            else:
                print("Failed to connect to PostgreSQL after all attempts")
                return None

def create_database(conn):
    """Create the j1chat database if it doesn't exist"""
    try:
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = 'j1chat'")
        exists = cursor.fetchone()
        
        if not exists:
            cursor.execute("CREATE DATABASE j1chat")
            print("Created database 'j1chat'")
        else:
            print("Database 'j1chat' already exists")
            
        cursor.close()
        return True
    except Exception as e:
        print(f"Error creating database: {str(e)}")
        return False

def setup_database():
    """Set up database schema and create admin user"""
    # Connect to postgres database
    conn = connect_db()
    if not conn:
        sys.exit(1)
        
    # Create j1chat database
    if not create_database(conn):
        conn.close()
        sys.exit(1)
        
    # Close connection to postgres database
    conn.close()
    
    # Connect to j1chat database
    try:
        conn = psycopg2.connect(
            dbname="j1chat",
            user="postgres",
            password="password",
            host="postgres",
            port="5432"
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Create vector extension
        cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")
        
        # Create tables
        print("Creating tables...")
        
        # Analytics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analytics (
                id SERIAL PRIMARY KEY,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                feedback VARCHAR(50),
                sources JSONB,
                rouge1 FLOAT,
                rouge2 FLOAT,
                rougel FLOAT,
                bert_p FLOAT,
                bert_r FLOAT,
                bert_f1 FLOAT,
                cosine_similarity FLOAT,
                response_time FLOAT,
                user_id UUID,
                office_code TEXT,
                chat_id VARCHAR(255),
                username TEXT,
                title TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                dataset VARCHAR(50),
                node_count INTEGER,
                model VARCHAR(255)
            )
        """)
        
        # Chat messages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_messages (
                id SERIAL PRIMARY KEY,
                user_id UUID NOT NULL,
                chat_id VARCHAR(255) NOT NULL,
                message_index INTEGER NOT NULL,
                sender VARCHAR(50) NOT NULL,
                content TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Feedback table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id SERIAL PRIMARY KEY,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                feedback VARCHAR(50),
                sources JSONB,
                rouge1 FLOAT,
                rouge2 FLOAT,
                rougel FLOAT,
                bert_p FLOAT,
                bert_r FLOAT,
                bert_f1 FLOAT,
                cosine_similarity FLOAT,
                response_time FLOAT,
                user_id UUID,
                office_code TEXT,
                chat_id VARCHAR(255),
                username TEXT,
                title TEXT,
                timestamp TIMESTAMP NOT NULL,
                node_count INTEGER
            )
        """)
        
        # Message sources table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS message_sources (
                message_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                content TEXT,
                url TEXT,
                PRIMARY KEY (message_id, title)
            )
        """)
        
        # Offices table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS offices (
                office_id SERIAL PRIMARY KEY,
                office_code TEXT NOT NULL UNIQUE,
                office_name TEXT
            )
        """)
        
        # Sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                user_id UUID NOT NULL,
                session_token VARCHAR(255) NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                PRIMARY KEY (user_id, session_token)
            )
        """)
        
        # User chats table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_chats (
                user_id UUID NOT NULL,
                chat_id VARCHAR(255) NOT NULL,
                title VARCHAR(255),
                username VARCHAR(255),
                office_code VARCHAR(255),
                PRIMARY KEY (user_id, chat_id)
            )
        """)
        
        # User preferences table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_preferences (
                user_id UUID NOT NULL PRIMARY KEY,
                selected_model VARCHAR(255) DEFAULT 'mistral:latest',
                temperature FLOAT DEFAULT 1.0,
                dataset VARCHAR(50) DEFAULT 'KG',
                persona VARCHAR(100) DEFAULT 'None',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id UUID NOT NULL PRIMARY KEY,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                role TEXT DEFAULT 'user',
                office_code VARCHAR(255),
                is_admin BOOLEAN DEFAULT FALSE,
                disabled BOOLEAN DEFAULT FALSE
            )
        """)
        
        # Create ADMIN office if it doesn't exist
        cursor.execute("SELECT 1 FROM offices WHERE office_code = 'ADMIN'")
        office_exists = cursor.fetchone()
        
        if not office_exists:
            cursor.execute("INSERT INTO offices (office_code, office_name) VALUES ('ADMIN', 'Administrators')")
            print("Created ADMIN office")
        
        # Create admin user if it doesn't exist
        cursor.execute("SELECT 1 FROM users WHERE username = 'admin'")
        user_exists = cursor.fetchone()
        
        if not user_exists:
            # Create admin user
            user_id = str(uuid.uuid4())
            hashed_password = bcrypt.hashpw('password'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            cursor.execute(
                "INSERT INTO users (user_id, username, password_hash, created_at, office_code, is_admin) VALUES (%s, %s, %s, %s, %s, %s)",
                (user_id, 'admin', hashed_password, created_at, 'ADMIN', True)
            )
            print("Created admin user with password: password")
        else:
            print("Admin user already exists")
        
        print("Database setup complete")
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error setting up database: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    setup_database() 