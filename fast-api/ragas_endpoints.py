from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json
import psycopg2

from ragas_eval import (
    get_model,
    compute_ragas_metrics, 
    extract_contexts_from_sources,
    update_analytics_with_ragas
)

# Import DB connection directly instead of from api_app
from db_utils import connect_db

# Create router
router = APIRouter(prefix="/api/ragas", tags=["ragas"])

# Models
class RAGASEvaluationInput(BaseModel):
    question: str
    generated_answer: str
    contexts: Optional[List[str]] = None
    sources_json: Optional[Dict[str, Any]] = None

class RAGASBatchInput(BaseModel):
    max_items: int = 10

# Define get_current_user here instead of importing from api_app
async def get_current_user_for_ragas(authorization: str = Header(...)):
    """
    Retrieve and validate the session token from the Authorization header.
    A simplified version of the function from api_app to avoid circular imports.
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
                raise HTTPException(status_code=403, detail="This account has been disabled")
            
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

@router.post("/evaluate")
async def evaluate_with_ragas(
    data: RAGASEvaluationInput, 
    current_user: dict = Depends(get_current_user_for_ragas)
):
    """Evaluate a single question/answer with RAGAS metrics"""
    user_id = current_user.get("user_id")
    
    # Ensure Qwen model is loaded
    model = get_model()
    if model is None:
        raise HTTPException(status_code=500, detail="Failed to initialize Qwen3 model")
    
    try:
        # Get contexts either directly or from sources_json
        contexts = data.contexts
        if not contexts and data.sources_json:
            contexts = extract_contexts_from_sources(data.sources_json)
        
        if not contexts:
            contexts = ["No context available"]
        
        # Compute RAGAS metrics
        metrics = await compute_ragas_metrics(
            question=data.question,
            answer=data.generated_answer,
            contexts=contexts
        )
        
        if not metrics:
            raise HTTPException(status_code=500, detail="Failed to compute RAGAS metrics")
        
        # Get chat_id from analytics table for this question
        conn = connect_db()
        chat_id = None
        try:
            if conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT chat_id FROM analytics WHERE user_id = %s AND question = %s ORDER BY timestamp DESC LIMIT 1",
                        (user_id, data.question)
                    )
                    result = cur.fetchone()
                    if result:
                        chat_id = result[0]
                
                # Store metrics in analytics if chat_id was found
                if chat_id:
                    await update_analytics_with_ragas(user_id, chat_id, data.question, metrics)
        except Exception as e:
            print(f"Error updating analytics with RAGAS metrics: {e}")
        finally:
            if conn:
                conn.close()
        
        return metrics
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RAGAS evaluation failed: {str(e)}")

@router.get("/results")
async def get_ragas_results(current_user: dict = Depends(get_current_user_for_ragas)):
    """Get RAGAS evaluation results from the analytics table"""
    user_id = current_user.get("user_id")
    is_admin = current_user.get("is_admin", False)
    
    conn = connect_db()
    if conn is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        with conn.cursor() as cur:
            if is_admin:
                # Admins can see all results
                query = """
                SELECT user_id, chat_id, question, faithfulness, 
                       answer_relevancy, context_relevancy, context_precision,
                       context_recall, harmfulness, timestamp, username, office_code
                FROM analytics
                WHERE faithfulness IS NOT NULL
                ORDER BY timestamp DESC
                """
                cur.execute(query)
            else:
                # Regular users only see their own results
                query = """
                SELECT user_id, chat_id, question, faithfulness, 
                       answer_relevancy, context_relevancy, context_precision,
                       context_recall, harmfulness, timestamp, username, office_code
                FROM analytics
                WHERE user_id = %s AND faithfulness IS NOT NULL
                ORDER BY timestamp DESC
                """
                cur.execute(query, (user_id,))
            
            rows = cur.fetchall()
            results = []
            
            for row in rows:
                if row[3] is not None:  # Only include if faithfulness is not NULL
                    result = {
                        "user_id": row[0],
                        "chat_id": row[1],
                        "question": row[2],
                        "faithfulness_score": float(row[3]) if row[3] is not None else None,
                        "answer_relevancy_score": float(row[4]) if row[4] is not None else None,
                        "context_relevancy_score": float(row[5]) if row[5] is not None else None,
                        "context_precision_score": float(row[6]) if row[6] is not None else None,
                        "context_recall_score": float(row[7]) if row[7] is not None else None,
                        "harmfulness_score": float(row[8]) if row[8] is not None else None,
                        "timestamp": row[9].strftime('%Y-%m-%d %H:%M:%S') if row[9] else None,
                        "username": row[10],
                        "office_code": row[11]
                    }
                    results.append(result)
            
            return results
    except Exception as e:
        print(f"Error fetching RAGAS results: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve RAGAS results: {str(e)}")
    finally:
        if conn:
            conn.close()

@router.post("/evaluate-recent")
async def evaluate_recent_chats(
    data: RAGASBatchInput = RAGASBatchInput(), 
    current_user: dict = Depends(get_current_user_for_ragas)
):
    """Evaluate recent chat interactions with RAGAS"""
    is_admin = current_user.get("is_admin", False)
    
    if not is_admin:
        raise HTTPException(status_code=403, detail="Only admins can run batch evaluations")
    
    # Ensure Qwen model is loaded
    model = get_model()
    if model is None:
        raise HTTPException(status_code=500, detail="Failed to initialize Qwen3 model")
    
    conn = connect_db()
    if conn is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        with conn.cursor() as cur:
            # Get recent chat interactions that haven't been evaluated yet
            query = """
            SELECT a.user_id, a.chat_id, a.question, a.answer, 
                   a.sources, a.timestamp
            FROM analytics a
            WHERE a.faithfulness IS NULL
            ORDER BY a.timestamp DESC
            LIMIT %s
            """
            cur.execute(query, (data.max_items,))
            rows = cur.fetchall()
            
            results = []
            for row in rows:
                chat_user_id = row[0]
                chat_id = row[1]
                question = row[2]
                answer = row[3]
                sources_json = row[4]
                
                # Extract contexts from sources
                contexts = extract_contexts_from_sources(sources_json)
                
                # Compute metrics
                try:
                    metrics = await compute_ragas_metrics(question, answer, contexts)
                    if metrics:
                        # Update analytics and feedback tables
                        await update_analytics_with_ragas(user_id=chat_user_id, chat_id=chat_id, question=question, metrics=metrics)
                        
                        results.append({
                            "user_id": chat_user_id,
                            "chat_id": chat_id,
                            "question": question,
                            "metrics": metrics
                        })
                except Exception as e:
                    print(f"Error evaluating with RAGAS: {e}")
            
            return {
                "evaluated_count": len(results),
                "results": results
            }
    except Exception as e:
        print(f"Error in batch evaluation: {e}")
        raise HTTPException(status_code=500, detail=f"Batch evaluation failed: {str(e)}")
    finally:
        if conn:
            conn.close() 