import os
import psycopg2

def connect_db():
    host = "docker-llm-postgres--6b5efca2ab.platform--j-6--chatbot--f4045690a8e475fc389a60ca"
    port = "5432"
    user = "postgres"
    password = "password"
    database = "postgres"
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database
        )
        return conn
    except Exception as e:
        print("[ERROR] Database connection failed:", e)
        return None
