import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import time
import sys
import requests
import argparse

class PostgresLauncher:
    def __init__(self, dbname="j1chat", user="postgres", password="password", host="postgres", port="5432"):
        self.dbname = dbname
        self.user = user
        self.password = password
        self.host = host
        self.port = port
        self.conn = None
        self.cursor = None

    def connect(self, max_retries=5, retry_interval=5):
        """Attempt to connect to PostgreSQL with retries"""
        for attempt in range(max_retries):
            try:
                # First try to connect to the default 'postgres' database
                self.conn = psycopg2.connect(
                    dbname="postgres",
                    user=self.user,
                    password=self.password,
                    host=self.host,
                    port=self.port
                )
                self.conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
                self.cursor = self.conn.cursor()
                print(f"Successfully connected to PostgreSQL at {self.host}:{self.port}")
                return True
            except Exception as e:
                print(f"Attempt {attempt + 1}/{max_retries} failed: {str(e)}")
                if attempt < max_retries - 1:
                    print(f"Retrying in {retry_interval} seconds...")
                    time.sleep(retry_interval)
                else:
                    print("Failed to connect to PostgreSQL after all attempts")
                    return False

    def create_database(self):
        """Create the database if it doesn't exist"""
        try:
            # Check if database exists
            self.cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{self.dbname}'")
            exists = self.cursor.fetchone()
            
            if not exists:
                self.cursor.execute(f"CREATE DATABASE {self.dbname}")
                print(f"Created database '{self.dbname}'")
            else:
                print(f"Database '{self.dbname}' already exists")

            # Close connection to postgres database
            self.conn.close()

            # Connect to the new database
            self.conn = psycopg2.connect(
                dbname=self.dbname,
                user=self.user,
                password=self.password,
                host=self.host,
                port=self.port
            )
            self.conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            self.cursor = self.conn.cursor()
            return True
        except Exception as e:
            print(f"Error creating database: {str(e)}")
            return False

    def setup_database(self):
        """Set up database schema"""
        try:
            # Create sequences
            sequences = [
                'analytics_id_seq',
                'chat_messages_id_seq',
                'feedback_id_seq',
                'offices_office_id_seq'
            ]
            
            for seq in sequences:
                self.cursor.execute(f"CREATE SEQUENCE IF NOT EXISTS {seq}")
            
            # Create vector extension
            self.cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")

            # Create tables
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS analytics (
                    id integer NOT NULL DEFAULT nextval('analytics_id_seq'::regclass),
                    question text NOT NULL,
                    answer text NOT NULL,
                    feedback character varying(50),
                    sources jsonb,
                    rouge1 double precision,
                    rouge2 double precision,
                    rougel double precision,
                    bert_p double precision,
                    bert_r double precision,
                    bert_f1 double precision,
                    cosine_similarity double precision,
                    response_time double precision,
                    user_id uuid,
                    office_code text,
                    chat_id character varying(255),
                    username text,
                    title text,
                    timestamp timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (id)
                )
            """)

            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id integer NOT NULL DEFAULT nextval('chat_messages_id_seq'::regclass),
                    user_id uuid NOT NULL,
                    chat_id character varying(255) NOT NULL,
                    message_index integer NOT NULL,
                    sender character varying(50) NOT NULL,
                    content text,
                    timestamp timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (id)
                )
            """)

            # Create document_embeddings tables
            for suffix in ['', '_airforce', '_combined', '_gs', '_stratcom']:
                table_name = f"document_embeddings{suffix}"
                self.cursor.execute(f"""
                    CREATE TABLE IF NOT EXISTS {table_name} (
                        id text NOT NULL,
                        content text,
                        embedding vector,
                        type text,
                        hash_document text,
                        document_title text,
                        category text,
                        pdf_path text,
                        hash_chapter text,
                        chapter_title text,
                        chapter_number text,
                        hash_section text,
                        section_title text,
                        section_number text,
                        section_page_number text,
                        hash_subsection text,
                        subsection_title text,
                        subsection_number text,
                        subsection_page_number text,
                        composite_id text,
                        PRIMARY KEY (id)
                    )
                """)

            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS feedback (
                    id integer NOT NULL DEFAULT nextval('feedback_id_seq'::regclass),
                    question text NOT NULL,
                    answer text NOT NULL,
                    feedback character varying(50),
                    sources jsonb,
                    rouge1 double precision,
                    rouge2 double precision,
                    rougel double precision,
                    bert_p double precision,
                    bert_r double precision,
                    bert_f1 double precision,
                    cosine_similarity double precision,
                    response_time double precision,
                    user_id uuid,
                    office_code text,
                    chat_id character varying(255),
                    username text,
                    title text,
                    timestamp timestamp without time zone NOT NULL,
                    PRIMARY KEY (id)
                )
            """)

            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS message_sources (
                    message_id integer NOT NULL,
                    title text NOT NULL,
                    content text,
                    url text,
                    PRIMARY KEY (message_id, title)
                )
            """)

            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS offices (
                    office_id integer NOT NULL DEFAULT nextval('offices_office_id_seq'::regclass),
                    office_code text NOT NULL,
                    office_name text,
                    PRIMARY KEY (office_id)
                )
            """)

            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    user_id uuid NOT NULL,
                    session_token character varying(255) NOT NULL,
                    expires_at timestamp without time zone NOT NULL,
                    PRIMARY KEY (user_id, session_token)
                )
            """)

            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_chats (
                    user_id uuid NOT NULL,
                    chat_id character varying(255) NOT NULL,
                    title character varying(255),
                    username character varying(255),
                    office_code character varying(255),
                    PRIMARY KEY (user_id, chat_id)
                )
            """)

            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_preferences (
                    user_id uuid NOT NULL,
                    selected_model character varying(255) DEFAULT 'mistral:latest'::character varying,
                    temperature double precision DEFAULT 1.0,
                    dataset character varying(50) DEFAULT 'KG'::character varying,
                    persona character varying(100) DEFAULT 'None'::character varying,
                    created_at timestamp without time zone DEFAULT now(),
                    updated_at timestamp without time zone DEFAULT now(),
                    PRIMARY KEY (user_id)
                )
            """)

            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id uuid NOT NULL,
                    username text NOT NULL,
                    password_hash text NOT NULL,
                    created_at timestamp without time zone NOT NULL DEFAULT now(),
                    role text DEFAULT 'user'::text,
                    office_code character varying(255),
                    is_admin boolean DEFAULT false,
                    disabled boolean DEFAULT false,
                    PRIMARY KEY (user_id)
                )
            """)

            # Add foreign key constraints
            constraints = [
                ("analytics", "user_id", "users", "user_id"),
                ("chat_messages", "user_id", "users", "user_id"),
                ("user_preferences", "user_id", "users", "user_id"),
                ("sessions", "user_id", "users", "user_id"),
                ("user_chats", "user_id", "users", "user_id"),
                ("analytics", "office_code", "offices", "office_code"),
                ("feedback", "office_code", "offices", "office_code"),
                ("users", "office_code", "offices", "office_code"),
                ("message_sources", "message_id", "chat_messages", "id")
            ]

            for table, column, ref_table, ref_column in constraints:
                self.cursor.execute(f"""
                    DO $$ 
                    BEGIN 
                        IF NOT EXISTS (
                            SELECT 1 
                            FROM information_schema.table_constraints 
                            WHERE constraint_name = '{table}_{column}_fkey'
                        ) THEN
                            ALTER TABLE {table}
                            ADD CONSTRAINT {table}_{column}_fkey
                            FOREIGN KEY ({column}) REFERENCES {ref_table}({ref_column});
                        END IF;
                    END $$;
                """)

            print("Successfully set up PostgreSQL database schema")
            return True
        except Exception as e:
            print(f"Error setting up database schema: {str(e)}")
            return False

    def verify_pgadmin_setup(self):
        """Verify pgAdmin is accessible"""
        try:
            response = requests.get("http://localhost:5050")
            if response.status_code == 200:
                print("pgAdmin is accessible at http://localhost:5050")
                print("Default credentials:")
                print("Email: admin@admin.com")
                print("Password: admin")
                return True
            else:
                print(f"pgAdmin returned status code: {response.status_code}")
                return False
        except Exception as e:
            print(f"Error verifying pgAdmin: {str(e)}")
            return False

    def close(self):
        """Close the PostgreSQL connection"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
            print("PostgreSQL connection closed")

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Initialize and verify PostgreSQL database")
    parser.add_argument("--host", default="postgres", help="PostgreSQL host")
    parser.add_argument("--user", default="postgres", help="PostgreSQL user")
    parser.add_argument("--password", default="password", help="PostgreSQL password")
    parser.add_argument("--dbname", default="j1chat", help="PostgreSQL database name")
    parser.add_argument("--port", default="5432", help="PostgreSQL port")
    parser.add_argument("--setup-only", action="store_true", help="Only set up the database schema, don't verify pgAdmin")
    args = parser.parse_args()
    
    # Initialize the launcher
    launcher = PostgresLauncher(
        dbname=args.dbname,
        user=args.user,
        password=args.password,
        host=args.host,
        port=args.port
    )
    
    # Connect to PostgreSQL
    if not launcher.connect():
        print("Failed to connect to PostgreSQL")
        sys.exit(1)
    
    # Create database
    if not launcher.create_database():
        print("Failed to create database")
        sys.exit(1)
    
    # Set up database schema
    if not launcher.setup_database():
        print("Failed to set up database schema")
        sys.exit(1)
    
    # Verify pgAdmin setup (unless --setup-only is specified)
    if not args.setup_only and not launcher.verify_pgadmin_setup():
        print("Warning: pgAdmin setup could not be verified")
    
    # Close connection
    launcher.close()
    print("Database setup completed successfully")

if __name__ == "__main__":
    main() 