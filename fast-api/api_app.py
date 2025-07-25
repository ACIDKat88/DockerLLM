import os
import json
import asyncio
import time
import uuid
import re
from datetime import datetime, timedelta
import pandas as pd
import shortuuid
import aiofiles
import numpy as np
from pydantic import BaseModel
from typing import List, Any
from sklearn.metrics.pairwise import cosine_similarity
from pathlib import Path
from prompts import promptDict 
from datetime import datetime
from typing import Optional
from urllib.parse import quote
import csv
import contextvars
import psycopg2
from bcrypt import hashpw, gensalt
import subprocess
import sys

# -----------------------------------
# Set up RAGAS with Ollama at startup
# -----------------------------------
print("\n=== Setting up RAGAS with Ollama ===")
RAGAS_SETUP_SUCCESS = False

# Check if Ollama is available
try:
    result = subprocess.run(
        "ollama --version", 
        shell=True, 
        capture_output=True, 
        text=True
    )
    if result.returncode != 0:
        print("× Ollama is not installed or not in PATH. RAGAS metrics will use fallback.")
    else:
        print(f"✓ Ollama is installed: {result.stdout.strip()}")
        
        # Check if Ollama server is running
        result = subprocess.run(
            "ollama list", 
            shell=True, 
            capture_output=True, 
            text=True
        )
        if result.returncode != 0:
            print("× Ollama server is not running. RAGAS metrics will use fallback.")
        else:
            print("✓ Ollama server is running")
            
            # Check for qwen3:0.6b model
            if "qwen3:0.6b" not in result.stdout:
                print("Pulling qwen3:0.6b model (this may take a while)...")
                pull_result = subprocess.run(
                    "ollama pull qwen3:0.6b", 
                    shell=True
                )
                if pull_result.returncode != 0:
                    print("× Failed to pull qwen3:0.6b model")
                else:
                    print("✓ qwen3:0.6b model pulled successfully")
            else:
                print("✓ qwen3:0.6b model is already available")
            
            # Create qwen3-ragas model if it doesn't exist
            if "qwen3-ragas" not in result.stdout:
                print("Creating qwen3-ragas custom model...")
                modelfile_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "qwen3_ragas.modelfile")
                
                if not os.path.exists(modelfile_path):
                    print(f"× Modelfile not found at {modelfile_path}")
                else:
                    create_result = subprocess.run(
                        f"ollama create qwen3-ragas -f {modelfile_path}", 
                        shell=True
                    )
                    
                    if create_result.returncode != 0:
                        print("× Failed to create qwen3-ragas model")
                    else:
                        print("✓ qwen3-ragas model created successfully")
                        RAGAS_SETUP_SUCCESS = True
            else:
                print("✓ qwen3-ragas model is already available")
                RAGAS_SETUP_SUCCESS = True
            
            # Import langchain-community if needed
            try:
                import langchain_community
                print("✓ langchain-community is installed")
            except ImportError:
                print("Installing langchain-community...")
                install_result = subprocess.run(
                    "pip install langchain-community", 
                    shell=True
                )
                if install_result.returncode != 0:
                    print("× Failed to install langchain-community")
                else:
                    print("✓ langchain-community installed successfully")
    
except Exception as e:
    print(f"× Error during RAGAS setup: {e}")

print("=== RAGAS setup complete! ===")

# Import modules for RAGAS with Ollama
try:
    from langchain_community.chat_models import ChatOllama
    HAVE_OLLAMA = True
    print("✓ ChatOllama is available for RAGAS evaluation")
except ImportError:
    HAVE_OLLAMA = False
    print("× ChatOllama not available. RAGAS evaluation may be limited.")

# Import the compute_ragas_metrics function from ragas_eval
try:
    from ragas_eval import (
        compute_ragas_metrics, extract_contexts_from_sources, 
        update_analytics_with_ragas, get_model
    )
    RAGAS_AVAILABLE = True and RAGAS_SETUP_SUCCESS  # Only consider RAGAS available if setup succeeded
    print("✓ RAGAS evaluation modules imported successfully")
    if RAGAS_AVAILABLE:
        print("🚀 RAGAS with Ollama is ready to use for metrics evaluation")
    else:
        print("⚠️ RAGAS will use fallback methods for metrics")
except ImportError as e:
    RAGAS_AVAILABLE = False
    print(f"× RAGAS evaluation modules could not be imported: {e}")

from fastapi import FastAPI, Depends, HTTPException, status, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import FileResponse
from fastapi import Header, HTTPException
from starlette.responses import StreamingResponse


# --- External Libraries for Retrieval, Metrics, and LLM ---
# These imports assume you have the corresponding packages installed.
# Replace or adjust as needed with your actual implementations.
from langchain_community.vectorstores import Chroma
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.chains import RetrievalQA, LLMChain
from langchain.schema.runnable.config import RunnableConfig
from langchain_community.chat_models import ChatOllama
from langchain.schema import HumanMessage


from sentence_transformers import CrossEncoder
from rouge_score import rouge_scorer
from bert_score import score as bert_score
import uuid
import json
import os
from datetime import datetime, timedelta
from bcrypt import hashpw, gensalt, checkpw
import uvicorn
from fastapi import FastAPI, Request, Header
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse
from fastapi import HTTPException


# Custom modules (assumed to be in your project)
from reranker import rerank_documents  # your reranker function
from hybrid import Hybrid, cypher_retriever, async_cypher_retriever   # your KG retrieval
from embedd_class import customembedding  # your custom embedding class
from retriever import CustomChromaRetriever
from db_utils import connect_db

# --- Configuration ---
SECRET_KEY = "YOUR_SECRET_KEY"  # Replace with a strong secret in production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24  # token valid for 24 hours



ALLOWED_ROOT = Path("/home/cm36/Updated-LLM-Project/J1_corpus/cleaned")

AVAILABLE_MODELS = ["mistral:latest", "sskostyaev/mistral:7b-instruct-v0.2-q6_K-32k", "mistral:7b-instruct-v0.3-q3_K_M"]

SIMILARITY_THRESHOLD = 0.3
# ------------------------------------------------------------------
# App Setup and CORS Configuration
# ------------------------------------------------------------------
app = FastAPI()

# Note: We're skipping the RAGAS router and using our fallback endpoint instead

# Mount static files and templates (preserving the original folders)
app.mount("/src", StaticFiles(directory="../front-end-app"), name="src")
templates = Jinja2Templates(directory="../front-end-app/")
# Mount the 'cleaned' directory to serve static files
app.mount("/static", StaticFiles(directory="/home/cm36/Updated-LLM-Project/J1_corpus/cleaned"), name="static")




origins = [
    "http://localhost:5173",
    "http://62.11.241.239:5173",
    "https://j1chatbottest.usgovvirginia.cloudapp.usgovcloudapi.net"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# HTTP Bearer security scheme for FastAPI dependency
bearer_scheme = HTTPBearer()




# ------------------------------------------------------------------
# Authentication Endpoints
# ------------------------------------------------------------------

# --- Helper: Retrieve full user info from USERS_FILE ---
def get_user_info(user_id: str):
    """
    Retrieve full user info from the PostgreSQL database based on the given user_id.
    """
    conn = connect_db()
    if conn is None:
        print("Database connection failed in get_user_info")
        return None
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT user_id, username, password_hash, office_code, is_admin, disabled, created_at
                FROM users
                WHERE user_id = %s;
            """, (user_id,))
            row = cur.fetchone()
            if row is None:
                return None
            user = {
                "user_id": row[0],
                "username": row[1],
                "password_hash": row[2],
                "office_code": row[3],
                "is_admin": row[4],
                "disabled": row[5],
                "created_at": row[6].strftime('%Y-%m-%d %H:%M:%S') if row[6] else None
            }
            return user
    except psycopg2.Error as e:
        print(f"Database error in get_user_info: {e}")
        return None
    finally:
        conn.close()
        
def generate_token():
    """Generate a unique session token using UUID."""
    return str(uuid.uuid4())

def get_current_user(authorization: str = Header(...)):
    """
    Retrieve and validate the session token from the Authorization header.
    If valid, return the full user info (including user_id and office_id)
    from the PostgreSQL database. Otherwise, raise an HTTPException.
    """
    session_token = authorization

    conn = connect_db()
    if conn is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        with conn.cursor() as cur:
            # Query the sessions table to find a session with the provided token.
            cur.execute(
                "SELECT user_id, expires_at FROM sessions WHERE session_token = %s;",
                (session_token,)
            )
            session_row = cur.fetchone()
            if not session_row:
                raise HTTPException(status_code=401, detail="Invalid or expired session token")
            
            user_id, expires_at = session_row
            # Assume expires_at is stored as a timestamp in the database.
            if expires_at <= datetime.now():
                raise HTTPException(status_code=401, detail="Invalid or expired session token")
            
            # Retrieve user info from the users table.
            cur.execute(
                "SELECT user_id, username, office_code, is_admin, created_at, disabled FROM users WHERE user_id = %s;",
                (user_id,)
            )
            user_row = cur.fetchone()
            if not user_row:
                raise HTTPException(status_code=404, detail="User not found")
            
            # Check if the user account is disabled
            if user_row[5]:  # Check the 'disabled' field (index 5)
                # Log the attempt
                print(f"API access attempt by disabled user: {user_row[1]} (ID: {user_row[0]})")
                # Invalidate any existing sessions for this user
                cur.execute(
                    "UPDATE sessions SET expires_at = %s WHERE user_id = %s;",
                    (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), user_id)
                )
                conn.commit()
                # Return an error
                raise HTTPException(status_code=403, detail="This account has been disabled. Please contact an administrator.")
            
            # Construct a dictionary of user info.
            user_info = {
                "user_id": user_row[0],
                "username": user_row[1],
                "office_code": user_row[2],
                "is_admin": user_row[3],
                "created_at": user_row[4].strftime('%Y-%m-%d %H:%M:%S') if user_row[4] else None,
                "disabled": user_row[5]
            }
            
            return user_info
    except psycopg2.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    finally:
        conn.close()

# --- Chat History--------------- ---

async def load_chat_history(user_id: str, chat_id: str):
    """
    Retrieve the chat history for a given user and chat session from PostgreSQL.
    Uses the new schema where messages are stored in chat_messages table.
    Returns a list of message objects in the same format as before for backward compatibility.
    """
    conn = connect_db()
    if conn is None:
        print("Database connection failed in load_chat_history")
        return []
    try:
        with conn.cursor() as cur:
            # Get all messages for this chat ordered by message_index
            cur.execute("""
                SELECT cm.id, cm.message_index, cm.sender, cm.content, cm.timestamp
                FROM chat_messages cm
                WHERE cm.user_id = %s AND cm.chat_id = %s
                ORDER BY cm.message_index;
            """, (user_id, chat_id))
            
            message_rows = cur.fetchall()
            if not message_rows:
                return []
                
            # For backward compatibility, convert the new schema into the old format
            # The old format had entries like {"user": "...", "bot": "...", "sources": {...}}
            history = []
            current_exchange = {}
            
            for msg_id, msg_index, sender, content, timestamp in message_rows:
                # For sources, we need to get the associated data from message_sources table
                if sender == 'user':
                    current_exchange = {"user": content}
                elif sender == 'bot':
                    current_exchange["bot"] = content
                    
                    # Fetch any associated sources for this message
                    cur.execute("""
                        SELECT title, content, url
                        FROM message_sources
                        WHERE message_id = %s;
                    """, (msg_id,))
                    
                    source_rows = cur.fetchall()
                    if source_rows:
                        # Convert source rows to the format expected by the frontend
                        sources_data = {
                            "content": "**Relevant Sources and Extracted Paragraphs:**\n\n",
                            "pdf_elements": []
                        }
                        
                        for src_title, src_content, src_url in source_rows:
                            sources_data["pdf_elements"].append({
                                "name": src_title,
                                "display": "side",
                                "pdf_url": src_url
                            })
                            
                            # Add to content as well (markdown format)
                            sources_data["content"] += f"**Source:** **{src_title}**\n\n"
                            if src_content:
                                sources_data["content"] += f"**Extracted Paragraph:**\n\n{src_content}\n\n"
                            if src_url:
                                sources_data["content"] += f"View full PDF: [Click Here]({src_url})\n\n"
                                
                        current_exchange["sources"] = sources_data
                    
                    # Add the exchange to history and reset
                    history.append(current_exchange)
                    current_exchange = {}
                    
            return history
    except psycopg2.Error as e:
        print(f"Database error in load_chat_history: {e}")
        return []
    finally:
        conn.close()


@app.post('/api/chat_history')
async def add_to_chat_history(user_id: str, chat_id: str, user_message: str, bot_response: str, sources: dict = None):
    """
    Append a new chat message entry to the chat history for a given user and chat session.
    
    Uses the new schema:
    - Stores user and bot messages in the chat_messages table
    - Stores associated sources in the message_sources table
    """
    conn = connect_db()
    if conn is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        with conn.cursor() as cur:
            # Check if the chat exists
            cur.execute(
                "SELECT title FROM user_chats WHERE user_id = %s AND chat_id = %s;",
                (user_id, chat_id)
            )
            row = cur.fetchone()
            
            # If chat doesn't exist, create it with a default title
            if not row:
                title = "Untitled Chat"
                cur.execute(
                    "INSERT INTO user_chats (user_id, chat_id, title) VALUES (%s, %s, %s);",
                    (user_id, chat_id, title)
                )
                conn.commit()
            else:
                title = row[0]
            
            # Get the current highest message_index for this chat
            cur.execute(
                "SELECT COALESCE(MAX(message_index), -1) FROM chat_messages WHERE user_id = %s AND chat_id = %s;",
                (user_id, chat_id)
            )
            max_index = cur.fetchone()[0]
            
            # Insert user message
            user_index = max_index + 1
            cur.execute(
                """
                INSERT INTO chat_messages (user_id, chat_id, message_index, sender, content, timestamp)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id;
                """,
                (user_id, chat_id, user_index, 'user', user_message, datetime.now())
            )
            
            # Insert bot message
            bot_index = user_index + 1
            cur.execute(
                """
                INSERT INTO chat_messages (user_id, chat_id, message_index, sender, content, timestamp)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id;
                """,
                (user_id, chat_id, bot_index, 'bot', bot_response, datetime.now())
            )
            bot_message_id = cur.fetchone()[0]
            
            # If sources exist, store them in the message_sources table
            if sources is not None:
                pdf_elements = sources.get('pdf_elements', [])
                
                for element in pdf_elements:
                    title = element.get('name', 'Unnamed Source')
                    url = element.get('pdf_url', '')
                    
                    # Extract content for this source from the markdown
                    source_content = ""
                    if sources.get('content'):
                        content_parts = sources['content'].split('**Source')
                        for part in content_parts:
                            if title in part:
                                # Try to extract paragraph text
                                if "**Extracted Paragraph:**" in part:
                                    try:
                                        paragraph = part.split("**Extracted Paragraph:**")[1].split("\n\n")[1]
                                        source_content = paragraph.strip()
                                    except:
                                        source_content = ""
                    
                    cur.execute(
                        """
                        INSERT INTO message_sources (message_id, title, content, url)
                        VALUES (%s, %s, %s, %s);
                        """,
                        (bot_message_id, title, source_content, url)
                    )
            
            conn.commit()
            print(f"[DEBUG] Added messages to chat history for user_id: {user_id}, chat_id: {chat_id}")
    except psycopg2.Error as e:
        conn.rollback()
        print(f"[DEBUG] Error updating chat history for user_id: {user_id}, chat_id: {chat_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update chat history: {e}")
    finally:
        conn.close()


@app.get('/api/username')
async def get_user(current_user: dict = Depends(get_current_user)):    
    return current_user

@app.post("/api/username")
async def update_username(request: Request, current_user: dict = Depends(get_current_user)):
    """
    Update the username for the current authenticated user.
    Expects a JSON payload with a "username" key.
    """
    data = await request.json()
    new_username = data.get("username")
    if not new_username:
        raise HTTPException(status_code=400, detail="New username is required.")
    
    # Connect to the PostgreSQL database.
    conn = connect_db()
    if conn is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        with conn.cursor() as cur:
            # Update the username for the current user and return the new username.
            cur.execute("""
                UPDATE users
                SET username = %s
                WHERE user_id = %s
                RETURNING username;
            """, (new_username, current_user.get("user_id")))
            result = cur.fetchone()
            if not result:
                raise HTTPException(status_code=404, detail="User not found.")
            
            conn.commit()
            print("Username updated successfully for user_id:", current_user.get("user_id"))
    except psycopg2.Error as e:
        print("Database error occurred while updating username:", e)
        raise HTTPException(status_code=400, detail=f"Failed to update username: {e}")
    finally:
        conn.close()
        print("Database connection closed.")
    
    return {"message": "Username updated successfully", "username": new_username}

@app.get("/api/offices")
async def get_offices():
    """
    Retrieve all offices from the PostgreSQL database.
    """
    conn = connect_db()
    if conn is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    offices = []
    try:
        with conn.cursor() as cur:
            # Update the query to use the correct column names
            cur.execute("SELECT office_id, office_code, office_name FROM offices;")
            rows = cur.fetchall()
            for row in rows:
                office = {
                    "office_id": row[0],
                    "office_code": row[1],
                    "office_name": row[2]
                }
                offices.append(office)
        return offices
    except psycopg2.Error as e:
        print(f"[ERROR] Database error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve offices: {e}")
    finally:
        conn.close()

@app.post("/api/offices")
async def update_office(request: Request, current_user: dict = Depends(get_current_user)):
    data = await request.json()
    office_code = data.get("office_code")
    if not office_code:
        raise HTTPException(status_code=400, detail="Office code is required")
    
    # Create a copy of data without the office_code (used for lookup)
    update_data = data.copy()
    update_data.pop("office_code", None)
    if not update_data:
        raise HTTPException(status_code=400, detail="No update data provided")
    
    conn = connect_db()
    if conn is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        with conn.cursor() as cur:
            # Verify that the office exists.
            cur.execute("SELECT office_code FROM offices WHERE office_code = %s;", (office_code,))
            office = cur.fetchone()
            if not office:
                raise HTTPException(status_code=404, detail="Office not found")
            
            # Dynamically build the UPDATE query using the keys from update_data.
            set_clauses = []
            values = []
            for key, value in update_data.items():
                set_clauses.append(f"{key} = %s")
                values.append(value)
            # Append the office_code for the WHERE clause.
            values.append(office_code)
            
            update_query = f"UPDATE offices SET {', '.join(set_clauses)} WHERE office_code = %s;"
            cur.execute(update_query, tuple(values))
            conn.commit()
            print(f"Office with office_code {office_code} updated with data: {update_data}")
            
        return {"message": "Office updated successfully", "office": data}
    except psycopg2.Error as e:
        raise HTTPException(status_code=500, detail=f"Failed to update office: {e}")
    finally:
        conn.close()

@app.post('/api/signup')
async def signup(request: Request):
    data = await request.json()
    username = data.get('username')
    password = data.get('password')
    office_code = data.get('office_code')

    if not username or not password or not office_code:
        print("Error: Username, password, and office code are required")
        return JSONResponse(content={"error": "Username, password, and office code are required"}, status_code=400)

    conn = connect_db()
    if conn is None:
        print("Error: Database connection failed")
        return JSONResponse(content={"error": "Database connection failed"}, status_code=500)

    try:
        with conn.cursor() as cur:
            # Verify the provided office code exists.
            cur.execute("SELECT 1 FROM offices WHERE office_code = %s;", (office_code,))
            if not cur.fetchone():
                print("Error: Invalid office code provided:", office_code)
                return JSONResponse(content={"error": "Invalid office code"}, status_code=400)
            print("Office verified. Office Code:", office_code)

            # Generate a unique user ID and creation timestamp.
            user_id = str(uuid.uuid4())
            created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print("Generated user_id:", user_id)
            print("Timestamp for creation:", created_at)

            # Hash the password.
            hashed_password = hashpw(password.encode('utf-8'), gensalt()).decode('utf-8')
            print("Password hashed successfully.")

            # Insert the new user record into the database using office_code.
            cur.execute("""
                INSERT INTO users (user_id, username, password_hash, office_code, created_at)
                VALUES (%s, %s, %s, %s, %s);
            """, (user_id, username, hashed_password, office_code, created_at))
            conn.commit()
            print("New user inserted with ID:", user_id)

        return JSONResponse(content={"message": "User created successfully", "user_id": user_id}, status_code=201)
    except psycopg2.Error as e:
        print("Database error occurred:", e)
        return JSONResponse(content={"error": f"Failed to create user: {e}"}, status_code=400)
    finally:
        conn.close()
        print("Database connection closed.")

@app.post('/api/login')
async def login(request: Request):
    data = await request.json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        print("Error: Username and password are required")
        return JSONResponse(content={"error": "Username and password are required"}, status_code=400)

    conn = connect_db()
    if conn is None:
        print("Error: Database connection failed")
        return JSONResponse(content={"error": "Database connection failed"}, status_code=500)

    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT user_id, password_hash, is_admin, disabled FROM users WHERE username = %s;",
                (username,)
            )
            user_row = cur.fetchone()
            if not user_row:
                print("Error: Invalid username or password")
                return JSONResponse(content={"error": "Invalid username or password"}, status_code=401)

            user_id, password_hash_db, is_admin, is_disabled = user_row
            
            # Check if the user account is disabled
            if is_disabled:
                print(f"Error: User {username} (ID: {user_id}) is disabled")
                return JSONResponse(content={"error": "This account has been disabled. Please contact an administrator."}, status_code=403)

            if not checkpw(password.encode('utf-8'), password_hash_db.encode('utf-8')):
                print("Error: Invalid username or password")
                return JSONResponse(content={"error": "Invalid username or password"}, status_code=401)

            session_token = generate_token()
            expires_at = (datetime.now() + timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S')

            cur.execute(
                """
                INSERT INTO sessions (user_id, session_token, expires_at)
                VALUES (%s, %s, %s);
                """,
                (user_id, session_token, expires_at)
            )
            conn.commit()
            print(f"Session created for user_id: {user_id}, token: {session_token}")

        return JSONResponse(content={
            "message": "Login successful",
            "session_token": session_token,
            "is_admin": is_admin if is_admin is not None else False
        }, status_code=200)
    except psycopg2.Error as e:
        print(f"Database error during login: {e}")
        return JSONResponse(content={"error": f"Failed to login: {e}"}, status_code=500)
    finally:
        conn.close()
        print("Database connection closed.")


@app.post('/api/logout')
async def logout(Authorization: str = Header(None)):
    """
    Logout Endpoint:
    - Requires a valid session token in the Authorization header.
    - Expires the session by updating its expiration time in the sessions table.
    """
    session_token = Authorization
    if not session_token:
        return JSONResponse(content={"error": "Session token required"}, status_code=401)
    
    conn = connect_db()
    if conn is None:
        return JSONResponse(content={"error": "Database connection failed"}, status_code=500)
    
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE sessions SET expires_at = %s WHERE session_token = %s;",
                (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), session_token)
            )
            if cur.rowcount == 0:
                return JSONResponse(content={"error": "Invalid session token"}, status_code=401)
            conn.commit()
            print(f"[DEBUG] Session with token {session_token} expired at {datetime.now()}")
        
        return JSONResponse(content={"message": "Logged out successfully"}, status_code=200)
    except psycopg2.Error as e:
        print(f"[DEBUG] Database error during logout: {e}")
        return JSONResponse(content={"error": f"Failed to log out: {e}"}, status_code=500)
    finally:
        conn.close()




# --- Admin Dependency ---
def get_current_admin_user(current_user: dict = Depends(get_current_user)):
    """
    Dependency to ensure that the current user is an admin.
    This example assumes that admin users have an 'is_admin' flag set to True.
    """
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Not authorized for admin actions")
    return current_user

# --- Admin GET Endpoint ---
@app.get("/api/admin")
async def admin_get(user_id: Optional[str] = None, current_admin: dict = Depends(get_current_admin_user)):
    """
    Admin GET Endpoint:
      - If a 'user_id' query parameter is provided, returns that user's chat history.
      - Otherwise, returns all user accounts from the PostgreSQL database.
    """
    if user_id:
        # Retrieve chat history for a specific user from PostgreSQL.
        conn = connect_db()
        if conn is None:
            raise HTTPException(status_code=500, detail="Database connection failed")
            
        try:
            with conn.cursor() as cur:
                # Get all chats for the specified user
                cur.execute("""
                    SELECT chat_id, title, username, office_code
                    FROM user_chats
                    WHERE user_id = %s;
                """, (user_id,))
                
                chat_rows = cur.fetchall()
                user_chat_history = {}
                
                # For each chat, get messages from chat_messages table
                for chat_id, title, username, office_code in chat_rows:
                    cur.execute("""
                        SELECT cm.id, cm.message_index, cm.sender, cm.content, cm.timestamp
                        FROM chat_messages cm
                        WHERE cm.user_id = %s AND cm.chat_id = %s
                        ORDER BY cm.message_index;
                    """, (user_id, chat_id))
                    
                    message_rows = cur.fetchall()
                    messages = []
                    
                    # Format each message
                    for msg_id, msg_index, sender, content, timestamp in message_rows:
                        message = {
                            "sender": sender,
                            "content": content,
                            "timestamp": timestamp.strftime('%Y-%m-%d %H:%M:%S') if timestamp else None
                        }
                        
                        # If bot message, check for sources
                        if sender == 'bot':
                            cur.execute("""
                                SELECT title, content, url
                                FROM message_sources
                                WHERE message_id = %s;
                            """, (msg_id,))
                            
                            source_rows = cur.fetchall()
                            if source_rows:
                                sources_data = []
                                for src_title, src_content, src_url in source_rows:
                                    sources_data.append({
                                        "title": src_title,
                                        "content": src_content,
                                        "url": src_url
                                    })
                                
                                message["sources"] = sources_data
                        
                        messages.append(message)
                    
                    # Store chat info and messages
                    user_chat_history[chat_id] = {
                        "title": title,
                        "messages": messages
                    }
                
                return {"user_id": user_id, "chat_history": user_chat_history}
        except psycopg2.Error as e:
            print(f"[ERROR] Database error in admin_get: {e}")
            raise HTTPException(status_code=500, detail=f"Database error: {e}")
        finally:
            conn.close()
    else:
        # Retrieve all user accounts from PostgreSQL.
        conn = connect_db()
        if conn is None:
            raise HTTPException(status_code=500, detail="Database connection failed")
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT user_id, username, office_code, is_admin, created_at, disabled
                    FROM users;
                """)
                users = []
                for row in cur.fetchall():
                    user = {
                        "user_id": row[0],
                        "username": row[1],
                        "office_code": row[2],
                        "is_admin": row[3],
                        "created_at": row[4].strftime('%Y-%m-%d %H:%M:%S') if row[4] else None,
                        "disabled": row[5]
                    }
                    users.append(user)
                return {"users": users}
        except psycopg2.Error as e:
            raise HTTPException(status_code=500, detail=f"Failed to retrieve user accounts: {e}")
        finally:
            conn.close()


# --- Admin POST Endpoint ---

# --- Admin Action Model ---
class AdminAction(BaseModel):
    action: str  # Expected values: "disable", "enable", "reassign", or "toggle_admin"
    target_user_id: str
    office_code: Optional[str] = None  # Required if action is "reassign"

@app.post("/api/admin")
async def admin_post(action_data: AdminAction, current_admin: dict = Depends(get_current_admin_user)):
    """
    POST Admin Endpoint:
      - action "disable": Sets the user's account to disabled.
      - action "enable": Sets the user's account to enabled.
      - action "reassign": Reassigns the user's office; requires an 'office_code'.
      - action "toggle_admin": Flips the user's admin status.
    This refactored version uses PostgreSQL to update user records and minimizes data loss
    by performing targeted updates.
    """
    conn = connect_db()
    if conn is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        with conn.cursor() as cur:
            # Verify the target user exists.
            cur.execute("SELECT is_admin FROM users WHERE user_id = %s;", (action_data.target_user_id,))
            user_row = cur.fetchone()
            if user_row is None:
                raise HTTPException(status_code=404, detail="User not found")
            
            current_is_admin = user_row[0]

            # Prevent admin from removing their own admin status? (Optional check)
            # if action_data.action == "toggle_admin" and str(action_data.target_user_id) == str(current_admin.get("user_id")) and current_is_admin:
            #     raise HTTPException(status_code=400, detail="Admin cannot remove their own admin status.")
            
            # Perform the appropriate action.
            if action_data.action == "disable":
                cur.execute(
                    "UPDATE users SET disabled = %s WHERE user_id = %s;",
                    (True, action_data.target_user_id)
                )
            elif action_data.action == "enable":
                cur.execute(
                    "UPDATE users SET disabled = %s WHERE user_id = %s;",
                    (False, action_data.target_user_id)
                )
            elif action_data.action == "reassign":
                if not action_data.office_code:
                    raise HTTPException(status_code=400, detail="Office code is required for reassignment")
                # Check if the office_code exists in the offices table first
                cur.execute("SELECT office_id FROM offices WHERE office_code = %s;", (action_data.office_code,))
                if cur.fetchone() is None:
                     raise HTTPException(status_code=400, detail="Invalid office code provided for reassignment")
                cur.execute(
                    "UPDATE users SET office_code = %s WHERE user_id = %s;",
                    (action_data.office_code, action_data.target_user_id)
                )
            elif action_data.action == "toggle_admin": # Added handler for toggle_admin
                cur.execute(
                    "UPDATE users SET is_admin = NOT is_admin WHERE user_id = %s;",
                    (action_data.target_user_id,)
                )
            else:
                raise HTTPException(status_code=400, detail="Invalid action. Use 'disable', 'enable', 'reassign', or 'toggle_admin'.")
            
            conn.commit()
            print(f"[DEBUG] Action '{action_data.action}' completed successfully for user {action_data.target_user_id}")
        
        return {"message": f"Action '{action_data.action}' completed successfully for user {action_data.target_user_id}"}
    except psycopg2.Error as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    finally:
        conn.close()


@app.post("/api/admin/create_user")
async def admin_create_user(request: Request, current_admin: dict = Depends(get_current_admin_user)):
    """
    Create a new regular user from the admin panel.
    Expects JSON with 'username', 'password', and 'office_code'.
    """
    data = await request.json()
    username = data.get('username')
    password = data.get('password')
    office_code = data.get('office_code')

    if not username or not password or not office_code:
        raise HTTPException(status_code=400, detail="Username, password, and office code are required")

    conn = connect_db()
    if conn is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        with conn.cursor() as cur:
            # Check that the provided office code exists.
            cur.execute("SELECT office_id FROM offices WHERE office_code = %s;", (office_code,))
            office_row = cur.fetchone()
            if not office_row:
                raise HTTPException(status_code=400, detail="Invalid office code")
            
            # Ensure the username is unique.
            cur.execute("SELECT 1 FROM users WHERE username = %s;", (username,))
            if cur.fetchone():
                raise HTTPException(status_code=400, detail="Username already exists")
            
            # Hash the password and prepare other fields.
            hashed_password = hashpw(password.encode('utf-8'), gensalt()).decode('utf-8')
            user_id = str(uuid.uuid4())
            created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Insert the new user into the database.
            cur.execute("""
                INSERT INTO users (user_id, username, password_hash, office_code, created_at, is_admin, disabled)
                VALUES (%s, %s, %s, %s, %s, %s, %s);
            """, (user_id, username, hashed_password, office_code, created_at, False, False))
            conn.commit()
            print(f"[DEBUG] New user created: {user_id}")
    except psycopg2.Error as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create user: {e}")
    finally:
        conn.close()
    
    return JSONResponse(content={"message": "User created successfully"}, status_code=201)

# New endpoint for admin to change user password
@app.post("/api/admin/change_password")
async def admin_change_password(request: Request, current_admin: dict = Depends(get_current_admin_user)):
    """
    Change a user's password from the admin panel.
    Expects JSON with 'target_user_id' and 'new_password'.
    """
    data = await request.json()
    target_user_id = data.get('target_user_id')
    new_password = data.get('new_password')

    if not target_user_id or not new_password:
        raise HTTPException(status_code=400, detail="User ID and new password are required")

    # Get the target user to ensure they exist
    target_user = get_user_info(target_user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
        
    # Connect to the database
    conn = connect_db()
    if conn is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        with conn.cursor() as cur:
            # Hash the new password
            hashed_password = hashpw(new_password.encode('utf-8'), gensalt()).decode('utf-8')
            
            # Update the password in the database
            cur.execute("""
                UPDATE users 
                SET password_hash = %s
                WHERE user_id = %s;
            """, (hashed_password, target_user_id))
            
            conn.commit()
            print(f"Password updated for user: {target_user_id}")
            
            return JSONResponse(content={"message": "Password changed successfully"}, status_code=200)
    except Exception as e:
        print(f"Error changing password: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to change password: {str(e)}")
    finally:
        conn.close()

# ------------------------------------------------------------------
# LLM Retrieval 
# ------------------------------------------------------------------

def initialize_langchain_kg_retrievers():
    kg_langchain_retriever = custom_retriever.as_retriever(search_kwargs={"k": 50}).get_relevant_documents
    return kg_langchain_retriever

async def async_rerank_documents(query, documents, top_n=5):
    """
    Asynchronously rerank retrieved documents using cross-encoder model.
    
    Args:
        query (str): The user query
        documents (list): List of retrieved documents to rerank
        top_n (int): Number of top documents to return
        
    Returns:
        list: List of (score, document) tuples sorted by score
    """
    try:
        # Extract content for reranking
        passages = [doc.page_content for doc in documents]
        
        # Create query-passage pairs for reranking
        pairs = [[query, passage] for passage in passages]
        
        # Use asyncio to run cross-encoder in a thread pool
        scores = await asyncio.to_thread(cross_encoder.predict, pairs)
        
        # Sort documents by score
        scored_results = list(zip(scores, documents))
        scored_results.sort(key=lambda x: x[0], reverse=True)
        
        # Return top N results
        return scored_results[:top_n]
    except Exception as e:
        print(f"[ERROR] Exception in reranking: {e}")
        # Return original documents with default scores if reranking fails
        return [(0.0, doc) for doc in documents[:top_n]]

async def async_get_relevant_documents(retriever, query, k=30):
    """
    Asynchronously retrieve relevant documents using a retriever.
    
    Args:
        retriever: The document retriever
        query (str): The user query
        k (int): Number of documents to retrieve
        
    Returns:
        list: List of retrieved documents
    """
    try:
        # Run the retriever in a thread pool
        return await asyncio.to_thread(
            lambda: retriever.get_relevant_documents(query)
        )
    except Exception as e:
        print(f"[ERROR] Exception in document retrieval: {e}")
        return []

# Initialize embedding function and vectorstores
embedding_function = customembedding("mixedbread-ai/mxbai-embed-large-v1")

# Initialize pgvector extension 
def initialize_pgvector():
    """
    Initialize the pgvector extension in PostgreSQL.
    This should be called during application startup.
    """
    conn = connect_db()
    if not conn:
        print("[ERROR] Failed to connect to the database to initialize pgvector")
        return False
    
    try:
        cursor = conn.cursor()
        # Create pgvector extension if it doesn't exist
        cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")
        
        # Verify the tables exist
        for table_name in ["document_embeddings_combined", "document_embeddings_gs", "document_embeddings_airforce"]:
            cursor.execute(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = %s
                )
            """, (table_name,))
            
            table_exists = cursor.fetchone()[0]
            if not table_exists:
                print(f"[WARNING] Table {table_name} does not exist. You may need to run json2pgvector.py first.")
        
        conn.commit()
        print("[INFO] Successfully initialized pgvector extension")
        return True
    except Exception as e:
        conn.rollback()
        print(f"[ERROR] Failed to initialize pgvector: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

# Initialize pgvector on application startup
initialize_pgvector()

# Define PGVectorRetriever class
class PGVectorRetriever:
    def __init__(self, embedding_function, table_name="document_embeddings_combined", db_connection=None):
        self.embedding_function = embedding_function
        self.table_name = table_name
        self.db_connection = db_connection
        
    def connect_db(self):
        if self.db_connection is None or self.db_connection.closed:
            self.db_connection = connect_db()
        return self.db_connection
    
    def as_retriever(self, search_kwargs=None):
        if search_kwargs is None:
            search_kwargs = {"k": 50}
        self.search_kwargs = search_kwargs
        return self
    
    def get_relevant_documents(self, query):
        # Get the embedding for the query
        query_embedding = self.embedding_function.embed_query(query)
        
        # Convert the embedding to a format suitable for PostgreSQL
        if isinstance(query_embedding, np.ndarray):
            query_embedding = query_embedding.tolist()
        
        print(f"[DEBUG] PGVectorRetriever: Querying PostgreSQL table '{self.table_name}' for similar documents")
        
        # Connect to the database
        conn = self.connect_db()
        if conn is None:
            print("Database connection failed in PGVectorRetriever")
            return []
        
        try:
            cursor = conn.cursor()
            # Query the database for similar embeddings
            cursor.execute(f"""
                SELECT id, content, embedding <-> %s::vector AS distance, 
                       document_title, hash_document, type, category, pdf_path,
                       chapter_title, section_title, section_number, subsection_title
                FROM {self.table_name}
                ORDER BY distance
                LIMIT %s
            """, (json.dumps(query_embedding), self.search_kwargs.get("k", 50)))
            
            results = cursor.fetchall()
            print(f"[DEBUG] PGVectorRetriever: Retrieved {len(results)} documents from '{self.table_name}'")
            
            # Convert the results to Document objects
            documents = []
            for row in results:
                doc_id, content, distance, doc_title, hash_doc, doc_type, category, pdf_path, chapter_title, section_title, section_number, subsection_title = row
                
                # Create metadata dictionary
                metadata = {
                    "id": doc_id,
                    "distance": distance,
                    "document_title": doc_title,
                    "hash_document": hash_doc,
                    "type": doc_type,
                    "category": category,
                    "pdf_path": pdf_path,
                    "chapter_title": chapter_title,
                    "section_title": section_title,
                    "section_number": section_number,
                    "subsection_title": subsection_title
                }
                
                # Filter out None values
                metadata = {k: v for k, v in metadata.items() if v is not None}
                
                # Create a Document object
                from langchain.schema import Document
                document = Document(page_content=content, metadata=metadata)
                documents.append(document)
            
            return documents
        
        except Exception as e:
            print(f"Error in PGVectorRetriever: {e}")
            return []
        finally:
            if conn:
                conn.close()

# Comment out ChromaDB retriever for reference
# custom_retriever = Chroma(
#     embedding_function=embedding_function,
#     persist_directory=KG_VECTOR_STORE_PATH,
#     collection_name="kg2"
# )

# Use PGVector retriever instead
custom_retriever = PGVectorRetriever(
    embedding_function=embedding_function,
    table_name="document_embeddings_combined"  # Use the combined table as default
)

# Additional retrievers for specific datasets
airforce_retriever = PGVectorRetriever(
    embedding_function=embedding_function,
    table_name="document_embeddings_airforce"
)

gs_retriever = PGVectorRetriever(
    embedding_function=embedding_function,
    table_name="document_embeddings_gs"
)

cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
graph_db = Hybrid(uri="neo4j://62.11.241.239:7687", user="neo4j", password="password")


def load_llm(model_name: str, temperature: float):
    """
    Initialize the Ollama LLM with the given model name.
    This uses the actual model inference via Ollama.
    """
    return ChatOllama(
        model=model_name,
        temperature=temperature, # Pass temperature here
        num_gpu=1,  # Adjust number of GPUs if needed
        verbose=True,
        callback_manager=CallbackManager([StreamingStdOutCallbackHandler()])
    )


async def async_is_topic_change(user_query, recent_chat_history, embedding_function):
    loop = asyncio.get_event_loop()
    query_embedding = await loop.run_in_executor(None, embedding_function.embed_query, user_query)
    for entry in recent_chat_history:
        entry_text = f"User: {entry['user']}\nBot: {entry['bot']}"
        entry_embedding = await loop.run_in_executor(None, embedding_function.embed_query, entry_text)
        similarity = (await loop.run_in_executor(None, lambda: __import__("sklearn.metrics.pairwise").metrics.pairwise.cosine_similarity([query_embedding], [entry_embedding])))[0][0]
        if similarity > SIMILARITY_THRESHOLD:
            return False
    return True

# ------------------------------------------------------------------
# Chat Endpoints
# ------------------------------------------------------------------

async def set_chat_title(user_id: str, chat_id: str, title: str):
    """
    Set or update the title of a chat session for the given user.
    If the session does not exist, create a new record with an empty history.
    Works with the new schema without a history column.
    """
    conn = connect_db()
    if conn is None:
        print("Database connection failed in set_chat_title")
        return
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO user_chats (user_id, chat_id, title)
                VALUES (%s, %s, %s)
                ON CONFLICT (user_id, chat_id) DO UPDATE
                SET title = EXCLUDED.title;
            """, (user_id, chat_id, title))
            conn.commit()
            print(f"[DEBUG] Set chat title for user_id: {user_id}, chat_id: {chat_id} to '{title}'")
    except psycopg2.Error as e:
        conn.rollback()
        print(f"Database error in set_chat_title: {e}")
    finally:
        conn.close()


async def create_or_get_chat_session(user_id: str, chat_id: str, title: str, username: str, office_code: str):
    """
    Create a new chat session for the user if it doesn't exist, or retrieve the existing session.
    Works with the new schema where messages are stored in chat_messages table.
    
    Returns the session as a dictionary with the following structure:
        {
            "id": chat_id,
            "title": <session title>,
            "username": <username>,
            "office_code": <office_code>,
            "messages": <list of messages>
        }
    """
    conn = connect_db()
    if conn is None:
        print("Database connection failed in create_or_get_chat_session")
        return {}
    try:
        with conn.cursor() as cur:
            # Insert a new record if one doesn't exist; otherwise, do nothing.
            cur.execute("""
                INSERT INTO user_chats (user_id, chat_id, title, username, office_code)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (user_id, chat_id) DO NOTHING;
            """, (user_id, chat_id, title, username, office_code))
            conn.commit()
            
            # Retrieve the chat session record
            cur.execute("""
                SELECT chat_id, title, username, office_code
                FROM user_chats
                WHERE user_id = %s AND chat_id = %s;
            """, (user_id, chat_id))
            row = cur.fetchone()
            
            if row:
                chat_id, title, username, office_code = row
                
                # Now get messages for this chat
                cur.execute("""
                    SELECT cm.id, cm.sender, cm.content, cm.timestamp
                    FROM chat_messages cm
                    WHERE cm.user_id = %s AND cm.chat_id = %s
                    ORDER BY cm.message_index;
                """, (user_id, chat_id))
                
                message_rows = cur.fetchall()
                messages = []
                
                # Process each message
                for msg_id, sender, content, timestamp in message_rows:
                    message = {
                        "sender": sender,
                        "content": content,
                        "timestamp": timestamp.strftime('%Y-%m-%d %H:%M:%S') if timestamp else None
                    }
                    
                    # Check for sources if this is a bot message
                    if sender == 'bot':
                        cur.execute("""
                            SELECT title, content, url
                            FROM message_sources
                            WHERE message_id = %s;
                        """, (msg_id,))
                        
                        source_rows = cur.fetchall()
                        if source_rows:
                            message["hasSources"] = True
                            
                            # Format source content for frontend
                            source_content = "**Relevant Sources and Extracted Paragraphs:**\n\n"
                            for src_title, src_content, src_url in source_rows:
                                source_content += f"**Source:** **{src_title}**\n\n"
                                if src_content:
                                    source_content += f"**Extracted Paragraph:**\n\n{src_content}\n\n"
                                if src_url:
                                    source_content += f"View full PDF: [Click Here]({src_url})\n\n"
                            
                            message["sourcesMarkdown"] = source_content
                    
                    messages.append(message)
                
                chat_session = {
                    "id": chat_id,
                    "title": title,
                    "username": username,
                    "office_code": office_code,
                    "messages": messages
                }
                
                return chat_session
            else:
                return {}
    except psycopg2.Error as e:
        conn.rollback()
        print(f"Database error in create_or_get_chat_session: {e}")
        return {}
    finally:
        conn.close()


def generate_chat_id():
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return shortuuid.ShortUUID().random(length=6) + "-" + timestamp


def load_personality(personality: str) -> str:
    """
    Returns the personality prompt based on the provided personality name.
    """
    prompt_content = promptDict.get(personality, "")
    print(f"[DEBUG] Loading personality '{personality}' with prompt content length: {len(prompt_content)} chars")
    print(f"[DEBUG] First 200 chars of '{personality}' prompt: {prompt_content[:200]}...")
    return prompt_content



@app.get("/api/chat/histories")
async def get_chat_histories(current_user: dict = Depends(get_current_user)):
    uid = current_user.get("user_id")
    
    conn = connect_db()
    if conn is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        with conn.cursor() as cur:
            # First get all chat sessions for this user
            cur.execute("""
                SELECT chat_id, title, username, office_code
                FROM user_chats
                WHERE user_id = %s;
            """, (uid,))
            chat_rows = cur.fetchall()
            
            # Build the user_chats dictionary
            user_chats = {}
            
            for chat_id, title, username, office_code in chat_rows:
                # For each chat, get all its messages from chat_messages table
                cur.execute("""
                    SELECT cm.id, cm.message_index, cm.sender, cm.content, cm.timestamp
                    FROM chat_messages cm
                    WHERE cm.user_id = %s AND cm.chat_id = %s
                    ORDER BY cm.message_index;
                """, (uid, chat_id))
                
                message_rows = cur.fetchall()
                messages = []
                
                # Process each message
                for msg_id, msg_index, sender, content, timestamp in message_rows:
                    # Basic message format
                    message = {
                        "sender": sender,
                        "content": content,
                        "timestamp": timestamp.strftime('%Y-%m-%d %H:%M:%S') if timestamp else None
                    }
                    
                    # If this is a bot message, check for associated sources
                    if sender == 'bot':
                        cur.execute("""
                            SELECT title, content, url
                            FROM message_sources
                            WHERE message_id = %s;
                        """, (msg_id,))
                        
                        source_rows = cur.fetchall()
                        if source_rows:
                            # Format sources for frontend
                            sources_data = {
                                "content": "**Relevant Sources and Extracted Paragraphs:**\n\n",
                                "pdf_elements": []
                            }
                            
                            for src_title, src_content, src_url in source_rows:
                                sources_data["pdf_elements"].append({
                                    "name": src_title,
                                    "display": "side",
                                    "pdf_url": src_url
                                })
                                
                                # Add markdown content
                                sources_data["content"] += f"**Source:** **{src_title}**\n\n"
                                if src_content:
                                    sources_data["content"] += f"**Extracted Paragraph:**\n\n{src_content}\n\n"
                                if src_url:
                                    sources_data["content"] += f"View full PDF: [Click Here]({src_url})\n\n"
                            
                            # Add sources info to message
                            message["hasSources"] = True
                            message["sourcesMarkdown"] = sources_data["content"]
                    
                    messages.append(message)
                
                # Add this chat to user_chats
                user_chats[chat_id] = {
                    "chat_id": chat_id,
                    "title": title,
                    "messages": messages
                }
            
            return user_chats
    except psycopg2.Error as e:
        print(f"[ERROR] Database error in get_chat_histories: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    finally:
        conn.close()


@app.post("/api/chat/histories")
async def create_chat_history(request: Request, current_user: dict = Depends(get_current_user)):
    data = await request.json()
    chat_title = data.get("chat_title", "Untitled Chat")
    chat_id = data.get("chat_id") or generate_chat_id()
    user_id = current_user.get("user_id")
    username = current_user.get("username")
    office_code = current_user.get("office_code")
    
    conn = connect_db()
    if conn is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
        
    try:
        with conn.cursor() as cur:
            # Check if chat exists
            cur.execute(
                "SELECT chat_id FROM user_chats WHERE user_id = %s AND chat_id = %s",
                (user_id, chat_id)
            )
            
            if cur.fetchone() is None:
                # Create new chat record
                cur.execute(
                    """
                    INSERT INTO user_chats (user_id, chat_id, title, username, office_code)
                    VALUES (%s, %s, %s, %s, %s);
                    """,
                    (user_id, chat_id, chat_title, username, office_code)
                )
                conn.commit()
                
            # Return basic chat session info
            session = {
                "id": chat_id,
                "title": chat_title,
                "username": username,
                "office_code": office_code,
                "messages": []  # New chats start with empty messages
            }
            
            return session
    except psycopg2.Error as e:
        conn.rollback()
        print(f"[ERROR] Database error in create_chat_history: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    finally:
        conn.close()


# --- New Endpoint to get available personas ---
@app.get("/api/personas")
async def get_personas():
    """
    Returns a list of available persona names from the promptDict,
    including "None".
    """
    persona_names = list(promptDict.keys())
    if "None" not in persona_names:
        persona_names.insert(0, "None") # Ensure "None" is an option, usually first
    return persona_names

# --- Streaming Chat Endpoint using HTTP StreamingResponse ---
def clean_llm_response(response: str) -> str:
    """
    Extracts plain text from a response string that may include metadata in the form of 
    "content='...'" and normalizes line breaks to maintain structure without excessive spacing.
    """
    # If the response contains metadata markers like "content=", extract the text segments.
    if "content=" in response:
        parts = response.split("content=")
        cleaned = ""
        for part in parts:
            # Look for a quoted string (either single or double quotes)
            if part.startswith("'") or part.startswith('"'):
                quote_char = part[0]
                try:
                    end_quote = part.index(quote_char, 1)
                    cleaned += part[1:end_quote]
                except ValueError:
                    cleaned += part
            else:
                cleaned += part
        cleaned_response = cleaned.strip()
    else:
        cleaned_response = response.strip()

    # Normalize line breaks to maintain structure without excessive breaks
    # 1. Replace literal '\n' sequences with actual newlines
    cleaned_response = cleaned_response.replace("\\n", "\n")
    
    # 2. Replace other escaped newline variants with actual newlines
    cleaned_response = cleaned_response.replace("\\\\n", "\n")
    
    # 3. Normalize all line break types (CR, LF, CRLF) to just LF
    cleaned_response = re.sub(r'\r\n?', '\n', cleaned_response)
    
    # 4. Replace sequences of 3 or more newlines with exactly 2 newlines
    cleaned_response = re.sub(r'\n{3,}', '\n\n', cleaned_response)
    
    # 5. Ensure no excessive spaces
    cleaned_response = re.sub(r' {2,}', ' ', cleaned_response)
    
    return cleaned_response.strip()

# --- Sanitize User Input ---
def is_appropriate_content(text):
    """
    Check if the provided text contains inappropriate content
    Returns (is_appropriate, reason) tuple
    """
    import re
    if not text or not isinstance(text, str):
        return False, "Invalid input"
    
    # Convert to lowercase for pattern matching
    text_lower = text.lower()
    
    # Patterns for inappropriate content
    inappropriate_patterns = [
        # Profanity and offensive language
        (r'\b(f[u\*]+ck|sh[i\*]+t|b[i\*]+tch|c[u\*]+nt|a[s\*]+hole|d[i\*]+ck|p[u\*]+ssy|porn|xxx)\b', 
         "Offensive language detected"),
        
        # Harmful instructions
        (r'\b(how to (make|create|build) (bomb|explosive|weapon|virus|malware))\b',
         "Harmful instructions detected"),
        
        # Requests for illegal content
        (r'\b(illegal (drugs|content)|child (porn|abuse)|underage)\b',
         "Requests for illegal content detected"),
        
        # Hate speech indicators
        (r'\b(kill|murder|attack|bomb|shoot|harm|hurt) (people|group|community|race|religion)\b',
         "Potential hate speech detected"),
        
        # Personal data requests
        (r'\b(social security|credit card|bank account|passport) (number|details|info)\b',
         "Requests for sensitive personal information"),
    ]
    
    # Check against each pattern
    for pattern, reason in inappropriate_patterns:
        if re.search(pattern, text_lower):
            print(f"[INAPPROPRIATE CONTENT] {reason}: {text}")
            return False, reason
    
    return True, None

@app.post("/api/chat")
async def chat_stream(request: Request, current_user: dict = Depends(get_current_user)):
    # Extract parameters from JSON payload.
    data = await request.json()
    user_message = data.get("message", "")
    model_name = data.get("model", AVAILABLE_MODELS[0])
    temperature = float(data.get("temperature", 1.0))
    dataset_option = data.get("dataset", "KG")
    # --- Log personality extraction --- 
    raw_persona = data.get("persona") # Get raw value first
    print(f"[DEBUG /api/chat] Raw 'persona' from request data: {raw_persona}")
    personality = raw_persona if raw_persona is not None else "None" # Apply default if None/missing
    print(f"[DEBUG /api/chat] Effective 'personality' after default: {personality}")
    
    # --- Log before calling load_personality --- 
    print(f"[DEBUG /api/chat] Value of 'personality' BEFORE calling load_personality: {personality}")
    prompt_prefix = load_personality(personality)
    print(f"[DEBUG /api/chat] Result from load_personality (prefix length): {len(prompt_prefix)}")
    
    user_id = current_user.get("user_id")
    if not user_message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    # Check if the message contains inappropriate content
    is_appropriate, reason = is_appropriate_content(user_message)
    if not is_appropriate:
        # Return a polite rejection message instead of raising an exception
        async def rejection_generator():
            rejection_message = {
                "token": f"I'm sorry, but I cannot respond to this message because it may contain inappropriate content. {reason}. Please revise your question."
            }
            yield f"data: {json.dumps(rejection_message)}\n\n"
            yield "data: [DONE]\n\n"
        
        # Log the rejection for review
        print(f"[CONTENT REJECTED] User: {user_id}, Message: {user_message}, Reason: {reason}")
        
        # Return the streaming response with the rejection message
        return StreamingResponse(
            rejection_generator(),
            media_type="text/event-stream"
        )

    # Retrieve or generate chat_id.
    chat_id = data.get("chat_id")
    if not chat_id:
        chat_id = generate_chat_id()
        chat_title = data.get("chat_title", "Untitled Chat")
        await set_chat_title(user_id, chat_id, chat_title)

    # --- Chat History Aggregation & Summarization ---
    recent_chat_history = await load_chat_history(user_id, chat_id)
    chat_history_context = ""
    if recent_chat_history:
        if await async_is_topic_change(user_message, recent_chat_history, embedding_function):
            print("Detected a new topic - ignoring previous chat history.")
        else:
            last_three = recent_chat_history[-3:]
            for entry in last_three:
                user_text = entry.get('user', '')
                bot_text = entry.get('bot')
                if isinstance(bot_text, dict) and 'content' in bot_text:
                    bot_text = bot_text['content']
                chat_history_context += f"User: {user_text}\nBot: {bot_text}\n\n"
    else:
        chat_history_context = ""

    retrieved_docs = []
    context = "" # Initialize context as empty
    node_count = None # Initialize node_count
    try:
        print(f"[DEBUG] Dataset option: {dataset_option}")
        print(f"[DEBUG] User query: {user_message}")
        loop = asyncio.get_event_loop()

        if dataset_option == "None":
            print("[DEBUG] Dataset is 'None', skipping document retrieval.")
            node_count = 0 # Set node_count to 0 when retrieval is skipped
            pass # Explicitly do nothing for retrieval
        elif dataset_option == "KG": # Changed from if to elif
            # Use Neo4j with the default combined pgvector retriever
            print(f"[DEBUG] Using dataset: 'KG' with Neo4j and PostgreSQL table: 'document_embeddings_combined'")
            context, retrieved_docs, node_count = await async_cypher_retriever(
                    user_message,
                    kg=graph_db,
                    vector_retriever=custom_retriever.as_retriever(search_kwargs={"k": 30}),
                    cross_encoder=cross_encoder,
                    k=30,
                    re_rank_top=5
                )
            # node_count is now captured here
            print(f"[DEBUG] Retrieved {node_count} nodes (hashes) from the knowledge graph.")
            print("[DEBUG] Top 5 reranked documents passed to the LLM:")
            for idx, doc in enumerate(retrieved_docs, 1):
                snippet = doc.page_content[:200].replace("\n", " ")
                print(f"Document {idx}: {snippet}...")
        elif dataset_option == "Air Force":
            # Use Neo4j with the Air Force specific retriever
            print(f"[DEBUG] Using dataset: 'Air Force' with Neo4j and PostgreSQL table: 'document_embeddings_airforce'")
            context, retrieved_docs, node_count = await async_cypher_retriever(
                    user_message,
                    kg=graph_db,
                    vector_retriever=airforce_retriever.as_retriever(search_kwargs={"k": 30}),
                    cross_encoder=cross_encoder,
                    k=30,
                    re_rank_top=5
                )
            # node_count is now captured here
            print(f"[DEBUG] Retrieved {node_count} nodes (hashes) from the knowledge graph (AirForce).")
            print("[DEBUG] Top 5 reranked AirForce documents passed to the LLM:")
            for idx, doc in enumerate(retrieved_docs, 1):
                snippet = doc.page_content[:200].replace("\n", " ")
                print(f"Document {idx}: {snippet}...")
        elif dataset_option == "GS":
            # Use Neo4j with the GS specific retriever
            print(f"[DEBUG] Using dataset: 'GS' with Neo4j and PostgreSQL table: 'document_embeddings_gs'")
            context, retrieved_docs, node_count = await async_cypher_retriever(
                    user_message,
                    kg=graph_db,
                    vector_retriever=gs_retriever.as_retriever(search_kwargs={"k": 30}),
                    cross_encoder=cross_encoder,
                    k=30,
                    re_rank_top=5
                )
            # node_count is now captured here
            print(f"[DEBUG] Retrieved {node_count} nodes (hashes) from the knowledge graph (GS).")
            print("[DEBUG] Top 5 reranked GS documents passed to the LLM:")
            for idx, doc in enumerate(retrieved_docs, 1):
                snippet = doc.page_content[:200].replace("\n", " ")
                print(f"Document {idx}: {snippet}...")
        else: # Handles other cases or unexpected values - use combined as default
            # Use the default combined pgvector retriever without Neo4j
            print(f"[DEBUG] Using fallback dataset option: '{dataset_option}' - defaulting to PostgreSQL table: 'document_embeddings_combined' without Neo4j")
            node_count = 0 # Set node_count to 0 as Neo4j wasn't used
            raw_docs = await loop.run_in_executor(
                None,
                lambda: custom_retriever.as_retriever(search_kwargs={"k": 30}).get_relevant_documents(user_message)
            )
            print(f"[DEBUG] Retrieved {len(raw_docs)} docs from combined retriever before reranking.")

            # Rerank the retrieved documents.
            if raw_docs:
                 scored_results = await async_rerank_documents(user_message, raw_docs)
                 retrieved_docs = [doc for score, doc in scored_results[:5]] # Assign reranked docs
                 context = "\n\n".join([doc.page_content for doc in retrieved_docs])
                 print(f"[DEBUG] Selected top {len(retrieved_docs)} documents after reranking.")
                 if retrieved_docs:
                     first_snippet = retrieved_docs[0].page_content[:200].replace("\n", " ")
                     print(f"[DEBUG] First combined doc snippet: {first_snippet}...")
                 else:
                     print("[DEBUG] No documents selected after reranking.")
            else:
                print("[DEBUG] No documents retrieved from combined retriever.")
                retrieved_docs = [] # Ensure it's empty if raw_docs was empty
                context = "" # Ensure context is empty
                
    except Exception as e:
        print(f"[ERROR] Exception in document retrieval: {e}")
        node_count = None # Set node_count to None on error
        context = "" # Ensure context is empty on error
        retrieved_docs = [] # Ensure retrieved_docs is empty on error

    # Build final prompt.
    # Context will be empty if dataset_option was "None" or if retrieval failed/returned nothing
    combined_context = f"{chat_history_context}\n\n{context.strip()}".strip() # Corrected closing brace and quote placement
    print(f"[DEBUG] Final combined context (first 500 chars): {combined_context[:500]}")
    
    # Construct the prompt based on whether context exists
    if combined_context:
        final_prompt = f"Context:\n{combined_context}\n\nUser Query:\n{user_message}"
    else:
        # Prompt without the "Context:" section if no context was retrieved
        final_prompt = f"User Query:\n{user_message}"
        
    if prompt_prefix:
        print(f"[DEBUG] Adding prompt for personality: {personality}")
        print(f"[DEBUG] Prompt before adding personality: {final_prompt[:100]}...")
        final_prompt = f"{prompt_prefix}\n\n{final_prompt}"
        print(f"[DEBUG] Prompt after adding personality (first 300 chars):\n{final_prompt[:300]}")
        
        # Log if common instructions are included
        if "You are a J1 Chatbot" in prompt_prefix:
            print(f"[DEBUG] Common instructions are included in the prompt")
        
        # Log if dataset-specific instructions are included
        if "If \"None\" dataset is selected" in prompt_prefix:
            print(f"[DEBUG] Dataset-specific instructions included in prompt")
        
        # Log role-specific instructions
        if personality != "None" and f"You are a {personality.lower()}" in prompt_prefix:
            print(f"[DEBUG] Role-specific instructions for '{personality}' included in prompt")
    else:
        print(f"[DEBUG] Warning: No prompt_prefix loaded!")

    print(f"[DEBUG] Final prompt sent to LLM (first 500 chars):\n{final_prompt[:500]}")

    llm = load_llm(model_name, temperature)

    async def token_generator():
        full_response = ""
        cleaned_response = "" # Initialize cleaned_response
        stream_start = time.perf_counter()
        tokens = []  # List to store token content.
        log_analytics_called = False # Flag to track if logging is called
        try:
            async for token in llm.astream(final_prompt, config=RunnableConfig()):
                token_text = str(token)
                # Sanitize the token to ensure it can be properly JSON serialized
                sanitized_token = token_text.replace('\\', '\\\\').replace('"', '\\"')
                tokens.append(token_text)
                try:
                    # Test that the token can be properly serialized
                    json_data = json.dumps({'token': sanitized_token})
                    yield f"data: {json_data}\n\n"
                except Exception as json_error:
                    print(f"[ERROR] JSON serialization error for token: {sanitized_token}")
                    print(f"[ERROR] JSON error details: {str(json_error)}")
                    # Send a safe version of the token
                    yield f"data: {json.dumps({'token': '[Content omitted due to formatting issues]'})}\n\n"
            full_response = ''.join(tokens)
            cleaned_response = clean_llm_response(full_response)
            yield f"data: {json.dumps({'final_text': cleaned_response})}\n\n"
            yield "data: [DONE]\n\n"
            print("[DEBUG /api/chat] Stream finished successfully.") # Log stream completion

        except Exception as e:
            print(f"[ERROR /api/chat] Error DURING stream generation: {str(e)}") # Enhanced logging
            import traceback
            traceback.print_exc() # Print full traceback
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            # Ensure we don't proceed to logging if stream failed
            return 

        # --- Code AFTER successful streaming --- 
        stream_elapsed = time.perf_counter() - stream_start
        print(f"Streamed response in {stream_elapsed:.3f} seconds")
        print(f"[DEBUG /api/chat] Calculated stream_elapsed: {stream_elapsed}") 
        
        print(f"[DEBUG /api/chat] Raw LLM response (full_response):\n'''{full_response}'''")
        cleaned_response = clean_llm_response(full_response) 
        print(f"[DEBUG /api/chat] Cleaned LLM response (cleaned_response):\n'''{cleaned_response}'''")
        
        # --- Compute Metrics --- 
        metrics = {} 
        try:
            print("[DEBUG /api/chat] Calculating metrics...")
            metrics = compute_metrics(cleaned_response, user_message, embedding_function, stream_elapsed)
            print(f"[DEBUG /api/chat] Metrics calculated: {metrics}")
        except Exception as metrics_error:
             print(f"[ERROR /api/chat] Error calculating metrics: {metrics_error}")
             import traceback
             traceback.print_exc()
             # Decide if you want to proceed without metrics or stop
             # For now, we'll proceed but log the error

        # --- Source Processing --- 
        sources_json = None 
        try:
            # print("[DEBUG /api/chat] Processing sources...") # Commented out
            if dataset_option != "None" and retrieved_docs: # Check if docs exist
                source_tuples = []
                for chunk in retrieved_docs: 
                    src = extract_source_from_metadata(chunk)
                    paragraph = chunk.page_content if hasattr(chunk, "page_content") else chunk.get("content")
                    source_tuples.append((src, paragraph))
                
                sources_json = await display_sources_with_paragraphs(source_tuples, dataset=dataset_option)
                yield f"data: {json.dumps({'sources': sources_json})}\n\n"
                # print("[DEBUG /api/chat] Sources processed and yielded.") # Commented out
            else:
                # print("[DEBUG /api/chat] No dataset or no retrieved docs, skipping source processing.") # Commented out
                pass # Explicitly do nothing if no sources needed
        except Exception as source_error:
             print(f"[ERROR /api/chat] Error processing sources: {source_error}")
             import traceback
             traceback.print_exc()
             # Decide if you want to proceed without sources or stop
             # For now, we'll proceed but log the error
             
        # --- Record Chat History --- 
        try:
            print("[DEBUG /api/chat] Adding to chat history...")
            await add_to_chat_history(user_id, chat_id, user_message, cleaned_response, sources_json)
            print("[DEBUG /api/chat] Added to chat history.")
        except Exception as history_error:
             print(f"[ERROR /api/chat] Error adding to chat history: {history_error}")
             import traceback
             traceback.print_exc()
             # This might be critical, maybe re-raise or handle differently

        # --- Integrated Analytics Logging --- 
        try:
            print("[DEBUG /api/chat] Preparing analytics payload...")
            # ... (existing code to get actual_title) ...
            conn = connect_db()
            actual_title = chat_id  # Default to chat_id if lookup fails
            if conn:
                try:
                    with conn.cursor() as cur:
                        cur.execute(
                            "SELECT title FROM user_chats WHERE user_id = %s AND chat_id = %s;",
                            (user_id, chat_id)
                        )
                        row = cur.fetchone()
                        if row and row[0]:
                            actual_title = row[0]
                except Exception as title_error:
                    print(f"[ERROR] Error fetching chat title: {title_error}")
                finally:
                    if conn:
                       conn.close()
            else: 
                 print("[WARNING] Failed to connect to DB for title lookup")

            current_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            print(f"[DEBUG /api/chat] Value of user_message before AnalyticsInput: {user_message}") 
            analytics_payload = AnalyticsInput(
                question=user_message,
                answer=cleaned_response,
                feedback="auto-logged", 
                sources=sources_json if sources_json is not None else {},
                chat_id=chat_id,
                rouge1=metrics.get("rouge1"),
                rouge2=metrics.get("rouge2"),
                rougeL=metrics.get("rougeL"),
                bert_p=metrics.get("bert_p"),
                bert_r=metrics.get("bert_r"),
                bert_f1=metrics.get("bert_f1"),
                response_time=metrics.get("elapsed_time"),
                cosine_similarity=metrics.get("cosine_similarity"),
                user_id=current_user.get("user_id"),
                title=actual_title, 
                username=current_user.get("username"),
                office_code=current_user.get("office_code"),
                timestamp=current_timestamp,
                dataset=dataset_option,  
                node_count=node_count, 
                model=model_name
            )
            
            print(f"[DEBUG /api/chat] analytics_payload before logging: {analytics_payload.dict()}") 
            print(f"[DEBUG /api/chat] Value of analytics_payload.question: {analytics_payload.question}") 
            
            print("------ CALLING log_analytics NOW ------") # Specific log before the call
            log_analytics_called = True # Set flag before calling
            await log_analytics(
                analytics_payload.question,
                analytics_payload.answer,
                analytics_payload.feedback,
                analytics_payload.sources,
                analytics_payload.response_time,
                analytics_payload.user_id,
                analytics_payload.title,
                analytics_payload.username,
                analytics_payload.office_code,
                analytics_payload.chat_id,
                analytics_payload.rouge1,
                analytics_payload.rouge2,
                analytics_payload.rougeL,
                analytics_payload.bert_p,
                analytics_payload.bert_r,
                analytics_payload.bert_f1,
                analytics_payload.cosine_similarity,
                analytics_payload.timestamp,
                analytics_payload.dataset,
                analytics_payload.node_count,
                analytics_payload.model,
                analytics_payload.faithfulness,
                analytics_payload.answer_relevancy,
                analytics_payload.context_relevancy,
                analytics_payload.context_precision,
                analytics_payload.context_recall,
                analytics_payload.harmfulness
            )
            print("[DEBUG /api/chat] Analytics logged successfully (call returned).") # Log after call returns
        except Exception as e:
            log_analytics_called = False # Ensure flag is false if error occurs before/during call
            print(f"[ERROR /api/chat] Error during analytics preparation or logging call: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # Optional: Add a final check log
            if log_analytics_called:
                 print("[DEBUG /api/chat] Log analytics call was attempted.")
            else:
                 print("[WARNING /api/chat] Log analytics call was NOT attempted due to prior error.")
                 
        # --- Trigger RAGAS evaluation asynchronously ---
        try:
            if RAGAS_AVAILABLE and dataset_option != "None" and retrieved_docs:
                print("[DEBUG /api/chat] Triggering async RAGAS evaluation")
                # Extract contexts from retrieved documents
                contexts = [doc.page_content for doc in retrieved_docs if hasattr(doc, "page_content")]
                
                # If we don't have direct context access, try to extract from sources
                if not contexts and sources_json:
                    from ragas_eval import extract_contexts_from_sources
                    contexts = extract_contexts_from_sources(sources_json)
                
                if contexts:
                    # Import here to avoid circular imports
                    from ragas_eval import compute_ragas_metrics, update_analytics_with_ragas
                    
                    # Launch evaluation in background task
                    async def run_ragas_evaluation():
                        try:
                            metrics = await compute_ragas_metrics(
                                question=user_message,
                                answer=cleaned_response,
                                contexts=contexts
                            )
                            
                            if metrics:
                                await update_analytics_with_ragas(
                                    user_id=user_id,
                                    chat_id=chat_id,
                                    question=user_message,
                                    metrics=metrics
                                )
                                print(f"[DEBUG /api/chat] RAGAS evaluation completed: {metrics}")
                        except Exception as ragas_error:
                            print(f"[ERROR /api/chat] RAGAS evaluation failed: {ragas_error}")
                    
                    # Start the background task
                    asyncio.create_task(run_ragas_evaluation())
                    print("[DEBUG /api/chat] RAGAS evaluation task launched")
                else:
                    print("[DEBUG /api/chat] Skipping RAGAS evaluation: No contexts available")
            else:
                print(f"[DEBUG /api/chat] Skipping RAGAS evaluation: RAGAS_AVAILABLE={RAGAS_AVAILABLE}, dataset={dataset_option}, has_docs={bool(retrieved_docs)}")
        except Exception as ragas_init_error:
            print(f"[ERROR /api/chat] Failed to initialize RAGAS evaluation: {ragas_init_error}")
            # Don't let RAGAS errors stop the response from being returned

    response_headers = {"X-Chat-ID": chat_id}
    return StreamingResponse(token_generator(), media_type="text/event-stream", headers=response_headers)


# ------------------------------------------------------------------
# Source Endpoints
# ------------------------------------------------------------------
@app.post("/api/sources")
async def get_sources(request: Request, current_user: dict = Depends(get_current_user)):
    data = await request.json()
    user_message = data.get("message", "")
    dataset_option = data.get("dataset", "KG")
    
    retrieved_docs = []  # Initialize empty list
    try:
        loop = asyncio.get_event_loop()
        if dataset_option == "KG":
            # Offload the blocking cypher_retriever call to a separate thread via run_in_executor.
            context, retrieved_docs, node_count = await async_cypher_retriever(
                    user_message,
                    kg=graph_db,
                    vector_retriever=custom_retriever.as_retriever(search_kwargs={"k": 30}),
                    cross_encoder=cross_encoder,
                    k=30,
                    re_rank_top=5
                )
        else:
            # Since there is no J1 dataset, use the custom retriever for the non-KG branch.
            retrieved_docs = await loop.run_in_executor(
                None,
                lambda: custom_retriever.as_retriever(search_kwargs={"k": 30}).get_relevant_documents(user_message)
            )
    except Exception as e:
        print(f"[ERROR] Exception in document retrieval: {e}")
        retrieved_docs = []
    
    # Continue with processing retrieved_docs (filtering duplicates, formatting sources, etc.)
    ...

    
    # Filter out duplicates and select the top 3 unique sources
    unique_sources = {}
    for doc in retrieved_docs:
        src = extract_source_from_metadata(doc)
        if src not in unique_sources and src != "Unknown":
            unique_sources[src] = doc
        if len(unique_sources) >= 3:
            break

    source_tuples = []
    for src, doc in unique_sources.items():
        paragraph = doc.page_content if hasattr(doc, "page_content") else doc.get("content")
        source_tuples.append((src, paragraph))
    
    # Use your display function to format the sources (you can modify as needed)
    sources_json = await display_sources_with_paragraphs(source_tuples, dataset=dataset_option)
    
    return sources_json


async def display_sources_with_paragraphs(sources_list, dataset: str = None):
    elements = []  # List to hold PDF info dicts
    sources_display = []
    displayed_sources = set()
    if dataset is None:
        dataset = "J1"
    for i, (source, paragraph) in enumerate(sources_list, 1):
        try:
            cleaned_paragraph = paragraph.strip().replace("\n", " ")
            if len(cleaned_paragraph) > 600:
                cleaned_paragraph = cleaned_paragraph[:600] + "..."
            
            # Use the source directly as the title instead of extracting from path
            # If source is a path, still extract the filename as a fallback
            if isinstance(source, str) and '/' in source:
                document_identifier = Path(source).name
                if document_identifier.endswith(".pdf.pdf"):
                    document_identifier = document_identifier[:-4]
                file_name = re.sub(r"L_[0-5]_", "", document_identifier).replace("_", " ")
            else:
                # Use the source directly as title if it's not a path
                file_name = source
                
            if file_name not in displayed_sources:
                displayed_sources.add(file_name)
                if isinstance(source, str) and source.endswith('.pdf'):
                    # Remove duplicate extension from the source if it exists.
                    if source.endswith('.pdf.pdf'):
                        source = source[:-4]
                    # Remove the absolute prefix if needed.
                    const_prefix = "/home/cm36/Updated-LLM-Project/J1_corpus/cleaned/"
                    # Ensure source is relative by stripping the prefix
                    relative_path = source.startswith(const_prefix) and source[len(const_prefix):] or source
                    # URL-encode the relative path.
                    encoded_path = quote(relative_path)
                    # Build the URL using the static mount:
                    pdf_url = f"https://j1chatbottest.usgovvirginia.cloudapp.usgovcloudapi.net/static/{encoded_path}"
                    elements.append({"name": file_name, "display": "side", "pdf_url": pdf_url})
                    sources_display.append(
                        f"**Source {i}:** **{file_name}**\n\n**Extracted Paragraph:**\n\n{cleaned_paragraph}\n\n"
                        f"View full PDF: [Click Here]({pdf_url})\n\n"
                    )
                else:
                    sources_display.append(
                        f"**Source {i}:** **{file_name}**\n\n**Extracted Paragraph:**\n\n{cleaned_paragraph}\n\n"
                    )
        except Exception as e:
            print(f"Error processing source {source}: {e}")
    combined_sources_content = "\n\n".join(sources_display)
    return {
        "content": "**Relevant Sources and Extracted Paragraphs:**\n\n" + combined_sources_content,
        "pdf_elements": elements
    }


def extract_source_from_metadata(chunk):
    if isinstance(chunk, dict):
        metadata = chunk.get("metadata", {})
    else:
        metadata = getattr(chunk, "metadata", {})
    source_val = metadata.get("pdf_path") or metadata.get("document_title")
    if not source_val:
        source_val = (metadata.get("chapter_title") or metadata.get("section_title") or
                      metadata.get("sublevel_title") or "Unknown")
    return source_val




@app.get("/api/pdf/{relative_path:path}")
async def get_pdf(relative_path: str):
    full_path = ALLOWED_ROOT / relative_path
    if not full_path.is_file():
        raise HTTPException(status_code=404, detail="PDF not found")
    return FileResponse(
        str(full_path),
        media_type="application/pdf",
        filename=full_path.name,
        headers={"Content-Disposition": f"inline; filename={full_path.name}"}
    )

# ------------------------------------------------------------------
# User Preferences Endpoints
# ------------------------------------------------------------------

@app.get("/api/user/preferences")
async def get_user_preferences(current_user: dict = Depends(get_current_user)):
    """
    Get the current user's preferences (model, temperature, dataset, persona).
    Creates default preferences if none exist.
    """
    user_id = current_user.get("user_id")
    
    conn = connect_db()
    if conn is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        with conn.cursor() as cur:
            # Check if user preferences exist
            cur.execute("SELECT selected_model, temperature, dataset, persona FROM user_preferences WHERE user_id = %s;", (user_id,))
            row = cur.fetchone()
            
            if row is None:
                # Create default preferences if none exist
                cur.execute("""
                    INSERT INTO user_preferences (user_id, selected_model, temperature, dataset, persona)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING selected_model, temperature, dataset, persona;
                """, (user_id, "mistral:latest", 1.0, "KG", "None"))
                row = cur.fetchone()
                conn.commit()
                print(f"[DEBUG] Created default preferences for user {user_id}")
            
            preferences = {
                "selected_model": row[0],
                "temperature": float(row[1]),
                "dataset": row[2],
                "persona": row[3]
            }
            
            return preferences
    except psycopg2.Error as e:
        print(f"[ERROR] Database error in get_user_preferences: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve user preferences: {e}")
    finally:
        conn.close()

@app.post("/api/user/preferences")
async def update_user_preferences(request: Request, current_user: dict = Depends(get_current_user)):
    """
    Update the current user's preferences (model, temperature, dataset, persona).
    """
    user_id = current_user.get("user_id")
    data = await request.json()
    
    # Validate preference data
    selected_model = data.get("selected_model")
    temperature = data.get("temperature")
    dataset = data.get("dataset")
    persona = data.get("persona")
    
    # Validation checks
    if temperature is not None and (not isinstance(temperature, (int, float)) or temperature < 0 or temperature > 1):
        raise HTTPException(status_code=400, detail="Temperature must be a number between 0 and 1")
    
    update_data = {}
    if selected_model is not None:
        update_data["selected_model"] = selected_model
    if temperature is not None:
        update_data["temperature"] = float(temperature)
    if dataset is not None:
        update_data["dataset"] = dataset
    if persona is not None:
        update_data["persona"] = persona
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No valid preference data provided")
    
    conn = connect_db()
    if conn is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        with conn.cursor() as cur:
            # Check if preferences exist
            cur.execute("SELECT 1 FROM user_preferences WHERE user_id = %s;", (user_id,))
            exists = cur.fetchone() is not None
            
            if exists:
                # Build update query dynamically
                set_clauses = []
                values = []
                for key, value in update_data.items():
                    set_clauses.append(f"{key} = %s")
                    values.append(value)
                
                # Add updated_at timestamp
                set_clauses.append("updated_at = %s")
                values.append(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                
                # Add user_id for WHERE clause
                values.append(user_id)
                
                # Execute update
                update_query = f"UPDATE user_preferences SET {', '.join(set_clauses)} WHERE user_id = %s;"
                cur.execute(update_query, tuple(values))
            else:
                # Create new preferences
                default_values = {
                    "selected_model": "mistral:latest",
                    "temperature": 1.0,
                    "dataset": "KG",
                    "persona": "None"
                }
                
                # Merge defaults with provided updates
                for key, value in update_data.items():
                    default_values[key] = value
                
                cur.execute("""
                    INSERT INTO user_preferences 
                    (user_id, selected_model, temperature, dataset, persona, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s);
                """, (
                    user_id, 
                    default_values["selected_model"],
                    default_values["temperature"],
                    default_values["dataset"],
                    default_values["persona"],
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                ))
            
            conn.commit()
            
            # Return updated preferences
            cur.execute("SELECT selected_model, temperature, dataset, persona FROM user_preferences WHERE user_id = %s;", (user_id,))
            row = cur.fetchone()
            
            updated_preferences = {
                "selected_model": row[0],
                "temperature": float(row[1]),
                "dataset": row[2],
                "persona": row[3]
            }
            
            return updated_preferences
    except psycopg2.Error as e:
        conn.rollback()
        print(f"[ERROR] Database error in update_user_preferences: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update user preferences: {e}")
    finally:
        conn.close()

# ------------------------------------------------------------------
# Feedback Endpoints
# ------------------------------------------------------------------

# --- Define models for feedback input ---
class FeedbackInput(BaseModel):
    question: str
    model: str
    temperature: float
    dataset: str
    answer: str
    personality: str
    sources: List[Any]
    chat_id: Optional[str] = None
    title: Optional[str] = None  # Make title optional to match frontend request
    elapsed_time: Optional[float] = None


async def update_analytics_feedback(user_id, chat_id, title, question, feedback_type):
    """
    Dedicated function to update only the feedback column in the analytics table.
    This function is used when a user provides explicit feedback through the feedback buttons.
    """
    print(f"[DEBUG] Updating analytics feedback to '{feedback_type}' for user_id={user_id}, chat_id={chat_id}, question={question}")
    
    conn = connect_db()
    if conn is None:
        print("Database connection failed in update_analytics_feedback")
        return False

    try:
        with conn.cursor() as cur:
            # First, check if the analytics entry exists
            cur.execute("""
                SELECT id FROM analytics
                WHERE 
                    user_id = %s AND 
                    chat_id = %s AND
                    question = %s;
            """, (
                user_id,
                chat_id,
                question
            ))
            
            row = cur.fetchone()
            if not row:
                print(f"[WARNING] No analytics entry found to update feedback for user_id={user_id}, chat_id={chat_id}, question={question}")
                return False
            
            # Update only the feedback column in the analytics table
            cur.execute("""
                UPDATE analytics
                SET feedback = %s
                WHERE 
                    user_id = %s AND 
                    chat_id = %s AND
                    question = %s;
            """, (
                feedback_type,
                user_id,
                chat_id,
                question
            ))
            
            updated_rows = cur.rowcount
            conn.commit()
            
            print(f"[DEBUG] Analytics table feedback updated successfully: {updated_rows} rows affected")
            return updated_rows > 0
    except psycopg2.Error as e:
        conn.rollback()
        print(f"[ERROR] Database error in update_analytics_feedback: {e}")
        print(f"[ERROR] Error details - pgcode: {e.pgcode}, pgerror: {e.pgerror}")
        return False
    except Exception as e:
        conn.rollback()
        print(f"[ERROR] General error in update_analytics_feedback: {e}")
        return False
    finally:
        conn.close()


def log_feedback(question, answer, feedback_type, sources, elapsed_time, user_id, title, username, office_code, chat_id, node_count=None, 
               faithfulness=None, answer_relevancy=None, context_relevancy=None, context_precision=None, context_recall=None, harmfulness=None): # Add RAGAS metrics parameters
    if not question or not answer:
        print("Error: Missing question or answer for feedback logging.")
        return
    
    # Ensure elapsed_time is a float, default to 0 if None or invalid
    try:
        elapsed_time_float = float(elapsed_time) if elapsed_time is not None else 0.0
    except (ValueError, TypeError):
        elapsed_time_float = 0.0

    # Set the current timestamp if not provided
    current_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    metrics = compute_metrics(answer, question, embedding_function, elapsed_time_float)
    feedback_data = {
        "question": question,
        "answer": answer,
        "feedback": feedback_type,
        "sources": sources,
        "rouge1": metrics.get("rouge1"),
        "rouge2": metrics.get("rouge2"),
        "rougeL": metrics.get("rougeL"),
        "bert_p": metrics.get("bert_p"),
        "bert_r": metrics.get("bert_r"),
        "bert_f1": metrics.get("bert_f1"),
        "cosine_similarity": metrics.get("cosine_similarity"),
        "response_time": elapsed_time_float,
        "title": title,
        "username": username,
        "user_id": user_id,
        "office_code": office_code,
        "chat_id": chat_id,
        "timestamp": current_timestamp, # Ensure timestamp is set
        "node_count": node_count, # Add node_count
        # RAGAS metrics
        "faithfulness": faithfulness,
        "answer_relevancy": answer_relevancy,
        "context_relevancy": context_relevancy,
        "context_precision": context_precision,
        "context_recall": context_recall,
        "harmfulness": harmfulness
    }
    print(f"Feedback Data for Update/Insert: {feedback_data}")

    conn = connect_db()
    if conn is None:
        print("Database connection failed in log_feedback")
        return

    try:
        with conn.cursor() as cur:
            # INSERT into feedback table only - the analytics update is handled separately
            cur.execute("""
                INSERT INTO feedback 
                (question, answer, feedback, sources, rouge1, rouge2, rougel, bert_p, bert_r, bert_f1, cosine_similarity, response_time, 
                user_id, title, username, office_code, chat_id, timestamp, node_count, 
                faithfulness, answer_relevancy, context_relevancy, context_precision, context_recall, harmfulness)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                feedback_data["question"],
                feedback_data["answer"],
                feedback_data["feedback"],
                json.dumps(feedback_data["sources"]) if feedback_data["sources"] is not None else None,
                feedback_data["rouge1"],
                feedback_data["rouge2"],
                feedback_data["rougeL"],
                feedback_data["bert_p"],
                feedback_data["bert_r"],
                feedback_data["bert_f1"],
                feedback_data["cosine_similarity"],
                feedback_data["response_time"],
                feedback_data["user_id"],
                feedback_data["title"],
                feedback_data["username"],
                feedback_data["office_code"],
                feedback_data["chat_id"],
                feedback_data["timestamp"],
                feedback_data["node_count"], # Pass node_count value
                feedback_data["faithfulness"],
                feedback_data["answer_relevancy"],
                feedback_data["context_relevancy"],
                feedback_data["context_precision"],
                feedback_data["context_recall"],
                feedback_data["harmfulness"]
            ))
            conn.commit()
            print("Feedback logged successfully to feedback table.")
    except psycopg2.Error as e:
        conn.rollback()
        print(f"Database error in log_feedback: {e}")
        print(f"Error details - pgcode: {e.pgcode}, pgerror: {e.pgerror}") # Add detailed error logging
    except Exception as e:
        conn.rollback()
        print(f"General error in log_feedback: {e}") # Add detailed error logging
    finally:
        conn.close()


async def fetch_node_count_for_feedback(user_id, chat_id, question):
    """Helper function to fetch node_count from the analytics table."""
    conn = connect_db()
    if conn is None:
        print("Database connection failed in fetch_node_count_for_feedback")
        return None
    try:
        with conn.cursor() as cur:
            # Fetch the latest analytics entry matching the criteria
            cur.execute("""
                SELECT node_count 
                FROM analytics
                WHERE user_id = %s AND chat_id = %s AND question = %s
                ORDER BY timestamp DESC
                LIMIT 1;
            """, (user_id, chat_id, question))
            row = cur.fetchone()
            return row[0] if row else None
    except psycopg2.Error as e:
        print(f"Database error fetching node_count: {e}")
        return None
    finally:
        if conn:
            conn.close()

@app.post("/api/feedback/positive")
async def positive_feedback(feedback: FeedbackInput, current_user: dict = Depends(get_current_user)):
    user_id = current_user.get("user_id")
    office_code = current_user.get("office_code")
    if not user_id or not office_code:
         raise HTTPException(status_code=401, detail="User information incomplete or missing.")

    chat_id = feedback.chat_id if feedback.chat_id else "unknown"
    question_text = feedback.question
    title = feedback.title if feedback.title else feedback.model

    try:
        # Fetch node_count for this interaction
        node_count = await fetch_node_count_for_feedback(user_id, chat_id, question_text)
        
        # Log feedback to the feedback table, including node_count
        log_feedback(
            question_text,
            feedback.answer,
            "positive",
            feedback.sources,
            feedback.elapsed_time,
            user_id,
            title,
            current_user.get("username"),
            office_code,
            chat_id,
            node_count, # Pass fetched node_count
            None, None, None, None, None, None # Pass None for all RAGAS metrics
        )
        
        # Update the analytics table separately
        feedback_updated = await update_analytics_feedback(
            user_id,
            chat_id,
            title,
            question_text,
            "positive"
        )
        
        if feedback_updated:
            print(f"[INFO] Analytics table updated successfully for positive feedback")
        else:
            print(f"[WARNING] Failed to update analytics table for positive feedback")
        
        # Trigger RAGAS evaluation if available
        if RAGAS_AVAILABLE:
            try:
                # Extract contexts from sources if present
                contexts = []
                if feedback.sources:
                    from ragas_eval import extract_contexts_from_sources
                    contexts = extract_contexts_from_sources(feedback.sources)
                
                # If we have contexts, trigger evaluation asynchronously
                if contexts:
                    from ragas_eval import compute_ragas_metrics, update_analytics_with_ragas
                    
                    # Launch evaluation in background task
                    async def run_feedback_ragas_evaluation():
                        try:
                            metrics = await compute_ragas_metrics(
                                question=question_text,
                                answer=feedback.answer,
                                contexts=contexts
                            )
                            
                            if metrics:
                                await update_analytics_with_ragas(
                                    user_id=user_id,
                                    chat_id=chat_id,
                                    question=question_text,
                                    metrics=metrics
                                )
                                print(f"[DEBUG /api/feedback/positive] RAGAS evaluation completed: {metrics}")
                        except Exception as ragas_error:
                            print(f"[ERROR /api/feedback/positive] RAGAS evaluation failed: {ragas_error}")
                    
                    # Start the background task
                    asyncio.create_task(run_feedback_ragas_evaluation())
                    print("[DEBUG /api/feedback/positive] RAGAS evaluation task launched")
            except Exception as ragas_error:
                print(f"[ERROR /api/feedback/positive] Failed to initialize RAGAS evaluation: {ragas_error}")
            
    except Exception as e:
        print(f"Error logging positive feedback: {e}") # Log the specific error
        raise HTTPException(status_code=500, detail=f"Error logging feedback: {e}")
    
    return {"message": "Thank you for your feedback!"}


@app.post("/api/feedback/negative")
async def negative_feedback(feedback: FeedbackInput, current_user: dict = Depends(get_current_user)):
    user_id = current_user.get("user_id")
    office_code = current_user.get("office_code")
    if not user_id or not office_code:
         raise HTTPException(status_code=401, detail="User information incomplete or missing.")

    chat_id = feedback.chat_id if feedback.chat_id else "unknown"
    question_text = feedback.question
    title = feedback.title if feedback.title else feedback.model

    try:
        # Fetch node_count for this interaction
        node_count = await fetch_node_count_for_feedback(user_id, chat_id, question_text)

        # Log feedback to the feedback table
        log_feedback(
            question_text,
            feedback.answer,
            "negative",
            feedback.sources,
            feedback.elapsed_time,
            user_id,
            title,
            current_user.get("username"),
            office_code,
            chat_id,
            node_count, # Pass fetched node_count
            None, None, None, None, None, None # Pass None for all RAGAS metrics
        )
        
        # Update the analytics table separately
        feedback_updated = await update_analytics_feedback(
            user_id,
            chat_id,
            title,
            question_text,
            "negative"
        )
        
        if feedback_updated:
            print(f"[INFO] Analytics table updated successfully for negative feedback")
        else:
            print(f"[WARNING] Failed to update analytics table for negative feedback")
            
        # Trigger RAGAS evaluation if available
        if RAGAS_AVAILABLE:
            try:
                # Extract contexts from sources if present
                contexts = []
                if feedback.sources:
                    from ragas_eval import extract_contexts_from_sources
                    contexts = extract_contexts_from_sources(feedback.sources)
                
                # If we have contexts, trigger evaluation asynchronously
                if contexts:
                    from ragas_eval import compute_ragas_metrics, update_analytics_with_ragas
                    
                    # Launch evaluation in background task
                    async def run_feedback_ragas_evaluation():
                        try:
                            metrics = await compute_ragas_metrics(
                                question=question_text,
                                answer=feedback.answer,
                                contexts=contexts
                            )
                            
                            if metrics:
                                await update_analytics_with_ragas(
                                    user_id=user_id,
                                    chat_id=chat_id,
                                    question=question_text,
                                    metrics=metrics
                                )
                                print(f"[DEBUG /api/feedback/negative] RAGAS evaluation completed: {metrics}")
                        except Exception as ragas_error:
                            print(f"[ERROR /api/feedback/negative] RAGAS evaluation failed: {ragas_error}")
                    
                    # Start the background task
                    asyncio.create_task(run_feedback_ragas_evaluation())
                    print("[DEBUG /api/feedback/negative] RAGAS evaluation task launched")
            except Exception as ragas_error:
                print(f"[ERROR /api/feedback/negative] Failed to initialize RAGAS evaluation: {ragas_error}")
            
    except Exception as e:
        print(f"Error logging negative feedback: {e}") # Log the specific error
        raise HTTPException(status_code=500, detail=f"Error logging feedback: {e}")
    return {"message": "Thank you for your feedback!"}


@app.post("/api/feedback/neutral")
async def neutral_feedback(feedback: FeedbackInput, current_user: dict = Depends(get_current_user)):
    user_id = current_user.get("user_id")
    office_code = current_user.get("office_code")
    if not user_id or not office_code:
         raise HTTPException(status_code=401, detail="User information incomplete or missing.")
         
    chat_id = feedback.chat_id if feedback.chat_id else "unknown"
    question_text = feedback.question
    title = feedback.title if feedback.title else feedback.model
    
    try:
        # Fetch node_count for this interaction
        node_count = await fetch_node_count_for_feedback(user_id, chat_id, question_text)

        # Log feedback to the feedback table
        log_feedback(
            question_text,
            feedback.answer,
            "neutral",
            feedback.sources,
            feedback.elapsed_time,
            user_id,
            title,
            current_user.get("username"),
            office_code,
            chat_id,
            node_count, # Pass fetched node_count
            None, None, None, None, None, None # Pass None for all RAGAS metrics
        )
        
        # Update the analytics table separately
        feedback_updated = await update_analytics_feedback(
            user_id,
            chat_id,
            title,
            question_text,
            "neutral"
        )
        
        if feedback_updated:
            print(f"[INFO] Analytics table updated successfully for neutral feedback")
        else:
            print(f"[WARNING] Failed to update analytics table for neutral feedback")
            
        # Trigger RAGAS evaluation if available
        if RAGAS_AVAILABLE:
            try:
                # Extract contexts from sources if present
                contexts = []
                if feedback.sources:
                    from ragas_eval import extract_contexts_from_sources
                    contexts = extract_contexts_from_sources(feedback.sources)
                
                # If we have contexts, trigger evaluation asynchronously
                if contexts:
                    from ragas_eval import compute_ragas_metrics, update_analytics_with_ragas
                    
                    # Launch evaluation in background task
                    async def run_feedback_ragas_evaluation():
                        try:
                            metrics = await compute_ragas_metrics(
                                question=question_text,
                                answer=feedback.answer,
                                contexts=contexts
                            )
                            
                            if metrics:
                                await update_analytics_with_ragas(
                                    user_id=user_id,
                                    chat_id=chat_id,
                                    question=question_text,
                                    metrics=metrics
                                )
                                print(f"[DEBUG /api/feedback/neutral] RAGAS evaluation completed: {metrics}")
                        except Exception as ragas_error:
                            print(f"[ERROR /api/feedback/neutral] RAGAS evaluation failed: {ragas_error}")
                    
                    # Start the background task
                    asyncio.create_task(run_feedback_ragas_evaluation())
                    print("[DEBUG /api/feedback/neutral] RAGAS evaluation task launched")
            except Exception as ragas_error:
                print(f"[ERROR /api/feedback/neutral] Failed to initialize RAGAS evaluation: {ragas_error}")
            
    except Exception as e:
        print(f"Error logging neutral feedback: {e}") # Log the specific error
        raise HTTPException(status_code=500, detail=f"Error logging feedback: {e}")
    return {"message": "Thank you for your feedback!"}

# ------------------------------------------------------------------
# Analytic Endpoints
# ------------------------------------------------------------------
# Define a new Pydantic model for analytics input.

class AnalyticsInput(BaseModel):
    question: str
    answer: str
    feedback: str
    sources: dict
    cosine_similarity: Optional[float] = None
    rouge1: Optional[float] = None
    rouge2: Optional[float] = None
    rougeL: Optional[float] = None
    bert_p: Optional[float] = None
    bert_r: Optional[float] = None
    bert_f1: Optional[float] = None
    response_time: Optional[float] = None
    user_id: str
    title: str  # Added back the title field that was removed
    username: str
    office_code: str
    chat_id: Optional[str] = None
    timestamp: Optional[str] = None
    dataset: Optional[str] = None  # Added dataset field
    node_count: Optional[int] = None # Added node_count field
    model: Optional[str] = None  # Added model field
    # RAGAS metrics
    faithfulness: Optional[float] = None
    answer_relevancy: Optional[float] = None
    context_relevancy: Optional[float] = None
    context_precision: Optional[float] = None
    context_recall: Optional[float] = None
    harmfulness: Optional[float] = None



@app.post("/api/analytics")
async def log_analytics(question, answer, feedback_type, sources, elapsed_time, user_id, title, 
                        username, office_code, chat_id, rouge1, rouge2, rougeL, bert_p, bert_r, 
                        bert_f1, cosine_similarity, timestamp, dataset=None, node_count=None, model=None,
                        faithfulness=None, answer_relevancy=None, context_relevancy=None, 
                        context_precision=None, context_recall=None, harmfulness=None): 
    
    print(f"[DEBUG log_analytics] Received question parameter: {question}") 
    values = {
        "question": question,
        "answer": answer,
        "feedback": feedback_type,
        "sources": sources,
        "rouge1": rouge1,
        "rouge2": rouge2,
        "rougeL": rougeL,
        "bert_p": bert_p,
        "bert_r": bert_r,
        "bert_f1": bert_f1,
        "cosine_similarity": cosine_similarity,
        "response_time": elapsed_time,
        "user_id": user_id,
        "office_code": office_code,
        "chat_id": chat_id,
        "username": username,
        "title": title,
        "dataset": dataset,
        "node_count": node_count,
        "timestamp": timestamp, # Add timestamp to the dictionary
        "model": model,  # Add model to the dictionary
        # RAGAS metrics
        "faithfulness": faithfulness,
        "answer_relevancy": answer_relevancy,
        "context_relevancy": context_relevancy,
        "context_precision": context_precision,
        "context_recall": context_recall,
        "harmfulness": harmfulness
    }
    print(f"[DEBUG log_analytics] Value of values['question'] before INSERT: {values.get('question')}") 
    
    query = """
    INSERT INTO analytics (question, answer, feedback, sources, rouge1, rouge2, rougel, 
                          bert_p, bert_r, bert_f1, cosine_similarity, response_time, 
                          user_id, office_code, chat_id, username, title, timestamp, dataset, node_count, model,
                          faithfulness, answer_relevancy, context_relevancy, context_precision, context_recall, harmfulness)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) 
    RETURNING id
    """
    
    conn = connect_db()
    if conn is None:
        print("Database connection failed in log_analytics")
        return

    try:
        with conn.cursor() as cur:
            cur.execute(query, (
                values["question"],
                values["answer"],
                values["feedback"],
                json.dumps(values["sources"]),
                values["rouge1"],
                values["rouge2"],
                values["rougeL"],
                values["bert_p"],
                values["bert_r"],
                values["bert_f1"],
                values["cosine_similarity"],
                values["response_time"],
                values["user_id"],
                values["office_code"],
                values["chat_id"],
                values["username"],
                values["title"],
                values["timestamp"], # Now this key exists in values
                values["dataset"],
                values["node_count"],
                values["model"],
                values["faithfulness"],
                values["answer_relevancy"],
                values["context_relevancy"],
                values["context_precision"],
                values["context_recall"],
                values["harmfulness"]
            ))
            # Get the inserted record ID
            analytics_id = cur.fetchone()[0]
            conn.commit()
            print("Analytics logged successfully to analytics table.")
            
            # Trigger RAGAS evaluation if available and metrics are not already set
            if RAGAS_AVAILABLE and dataset != "None" and (values["faithfulness"] is None or 
                                                         values["answer_relevancy"] is None or
                                                         values["context_relevancy"] is None):
                # Extract contexts from sources
                contexts = []
                try:
                    # Use the extract_contexts_from_sources function from ragas_eval
                    contexts = extract_contexts_from_sources(sources)
                    
                    if not contexts:
                        print("No contexts found in sources for RAGAS evaluation")
                    else:
                        print(f"Extracted {len(contexts)} contexts from sources for RAGAS evaluation")
                        
                        # Launch async RAGAS evaluation
                        async def run_ragas_evaluation():
                            try:
                                # Get metrics using the Ollama-based implementation
                                metrics = await compute_ragas_metrics(
                                    question=question,
                                    answer=answer,
                                    contexts=contexts
                                )
                                
                                print(f"RAGAS metrics computed successfully: {metrics}")
                                
                                if metrics:
                                    # Update the analytics record with the RAGAS metrics
                                    await update_analytics_with_ragas(
                                        user_id=user_id,
                                        chat_id=chat_id,
                                        question=question,
                                        metrics=metrics
                                    )
                                    print(f"Analytics record {analytics_id} updated with RAGAS metrics")
                            except Exception as e:
                                print(f"Error in RAGAS evaluation: {e}")
                                import traceback
                                traceback.print_exc()
                        
                        # Schedule the async task
                        asyncio.create_task(run_ragas_evaluation())
                        print("RAGAS evaluation scheduled in background")
                except Exception as e:
                    print(f"Error preparing RAGAS evaluation: {e}")
            
    except psycopg2.Error as e:
        conn.rollback()
        print(f"Database error while logging analytics: {e}")
        print(f"Error details - pgcode: {e.pgcode}, pgerror: {e.pgerror}")
    except Exception as e:
        conn.rollback()
        print(f"General error while logging analytics: {e}")
    finally:
        conn.close()


@app.get("/api/analytics")
async def get_analytics(current_user: dict = Depends(get_current_user)):
    """
    Retrieve all stored analytics records from the PostgreSQL database.
    Now reads directly from the analytics table which includes feedback/metrics.
    """
    conn = connect_db()
    if conn is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        with conn.cursor() as cur:
            # Select directly from analytics table, including node_count and RAGAS metrics
            cur.execute("""
                SELECT 
                    user_id, 
                    title, 
                    username, 
                    office_code, 
                    question, 
                    answer, 
                    feedback,     
                    (SELECT string_agg(elem ->> 'name', ', ') 
                     FROM jsonb_array_elements(sources -> 'pdf_elements') AS elem) AS source_names,
                    cosine_similarity, 
                    timestamp,
                    rouge1,       
                    rouge2,       
                    rougel,       
                    bert_p,       
                    bert_r,       
                    bert_f1,      
                    response_time, 
                    dataset,      
                    node_count,   
                    model,
                    faithfulness,
                    answer_relevancy,
                    context_relevancy,
                    context_precision,
                    context_recall,
                    harmfulness
                FROM analytics
                ORDER BY timestamp DESC; 
            """)
            rows = cur.fetchall()
            analytics_records = []
            for row in rows:
                # Map row columns to dictionary keys
                record = {
                    "user_id": row[0],
                    "title": row[1],
                    "username": row[2],
                    "office_code": row[3],
                    "question": row[4],
                    "answer": row[5],
                    "feedback": row[6], 
                    "sources": row[7], 
                    "cosine_similarity": row[8],
                    "timestamp": row[9].strftime('%Y-%m-%d %H:%M:%S') if row[9] else None,
                    "rouge1": row[10],
                    "rouge2": row[11],
                    "rougeL": row[12], 
                    "bert_p": row[13],
                    "bert_r": row[14],
                    "bert_f1": row[15],
                    "response_time": row[16],
                    "dataset": row[17],
                    "node_count": row[18],
                    "model": row[19],
                    # Add RAGAS metrics to the response
                    "faithfulness": row[20],
                    "answer_relevancy": row[21],
                    "context_relevancy": row[22],
                    "context_precision": row[23],
                    "context_recall": row[24],
                    "harmfulness": row[25]
                }
                analytics_records.append(record)
            return analytics_records
    except psycopg2.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    finally:
        conn.close()


@app.post("api/UserAnalytics")
def compute_metrics(prediction, reference, embedding_function, elapsed_time):
    rouge = rouge_scorer.RougeScorer(['rouge1', 'rouge2', 'rougeL'], use_stemmer=True)
    rouge_scores = rouge.score(reference, prediction)
    bert_p, bert_r, bert_f1 = bert_score([prediction], [reference], lang="en", verbose=True)
    prediction_embedding = embedding_function.embed_query(prediction)
    reference_embedding = embedding_function.embed_query(reference)
    # Correctly extract the scalar value using [0][0]
    cosine_sim_value = (lambda: 
        __import__("sklearn.metrics.pairwise").metrics.pairwise.cosine_similarity([prediction_embedding], [reference_embedding])
    )()[0][0]
    metrics = {
        "rouge1": rouge_scores['rouge1'].fmeasure,
        "rouge2": rouge_scores['rouge2'].fmeasure,
        "rougeL": rouge_scores['rougeL'].fmeasure,
        "bert_p": bert_p.mean().item(),
        "bert_r": bert_r.mean().item(),
        "bert_f1": bert_f1.mean().item(),
        # Store the scalar value directly
        "cosine_similarity": cosine_sim_value, 
        "elapsed_time": elapsed_time
    }
    return metrics


# Add this new endpoint after the analytics endpoint

@app.get("/api/ragas/analytics")
async def get_ragas_analytics(current_user: dict = Depends(get_current_user)):
    """
    Retrieve RAGAS metrics directly from the analytics table.
    This endpoint provides access to RAGAS data even without the full RAGAS router.
    """
    conn = connect_db()
    if conn is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        with conn.cursor() as cur:
            # Select records with RAGAS metrics
            cur.execute("""
                SELECT 
                    user_id, chat_id, question, answer, 
                    faithfulness, answer_relevancy, context_relevancy,
                    context_precision, context_recall, harmfulness,
                    timestamp, username, office_code, model, dataset
                FROM analytics
                WHERE faithfulness IS NOT NULL
                   OR answer_relevancy IS NOT NULL
                   OR context_relevancy IS NOT NULL
                   OR context_precision IS NOT NULL
                   OR context_recall IS NOT NULL
                   OR harmfulness IS NOT NULL
                ORDER BY timestamp DESC;
            """)
            rows = cur.fetchall()
            
            ragas_data = []
            for row in rows:
                record = {
                    "user_id": row[0],
                    "chat_id": row[1],
                    "question": row[2],
                    "answer": row[3],
                    "faithfulness": float(row[4]) if row[4] is not None else None,
                    "answer_relevancy": float(row[5]) if row[5] is not None else None,
                    "context_relevancy": float(row[6]) if row[6] is not None else None,
                    "context_precision": float(row[7]) if row[7] is not None else None,
                    "context_recall": float(row[8]) if row[8] is not None else None,
                    "harmfulness": float(row[9]) if row[9] is not None else None,
                    "timestamp": row[10].strftime('%Y-%m-%d %H:%M:%S') if row[10] else None,
                    "username": row[11],
                    "office_code": row[12],
                    "model": row[13],
                    "dataset": row[14]
                }
                ragas_data.append(record)
            
            # Include information about RAGAS availability and configuration
            response = {
                "ragas_available": RAGAS_AVAILABLE,
                "ollama_available": HAVE_OLLAMA if 'HAVE_OLLAMA' in globals() else False,
                "evaluation_model": "qwen3-ragas (Ollama)" if RAGAS_AVAILABLE and HAVE_OLLAMA else "Not configured",
                "data": ragas_data,
                "count": len(ragas_data)
            }
            
            return response
    except Exception as e:
        print(f"[ERROR] Database error in get_ragas_analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve RAGAS analytics: {e}")
    finally:
        conn.close()


# ------------------------------------------------------------------
# Error Handling and Debug Logging
# ------------------------------------------------------------------
# All endpoints return JSON error messages with appropriate HTTP status codes,
# and debug prints are included where useful (e.g., session creation).

# ------------------------------------------------------------------
# Run the FastAPI Application
# ------------------------------------------------------------------
if __name__ == "__main__":

    print("Starting FastAPI application...")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="debug")


