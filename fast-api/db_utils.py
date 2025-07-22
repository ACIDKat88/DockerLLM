import os
import psycopg2

def connect_db():
    host = os.environ.get("DB_HOST", "127.0.0.1")
    port = os.environ.get("DB_PORT", 5432)
    user = os.environ.get("DB_USER", "postgres")
    password = os.environ.get("DB_PASSWORD", "admin")
    database = os.environ.get("DB_NAME", "postgres")
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            sslmode='require'
        )
        return conn
    except Exception as e:
        print("[ERROR] Database connection failed:", e)
        return None
