from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import sqlite3
import json
import os
import logging
from datetime import datetime
from core.llm_router import LLMRouter

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Agentic System API",
    description="Proxy REST API for the Agentic System",
    version="0.1.0"
)

# Database helper
def get_db_connection():
    """Get database connection with proper error handling and logging."""
    # Use absolute path from project root
    # File is in apps/proxy_api/, so we need to go up 3 levels to reach project root
    db_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "core.db"))
    
    # Ensure the data directory exists
    data_dir = os.path.dirname(db_path)
    if not os.path.exists(data_dir):
        os.makedirs(data_dir, exist_ok=True)
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        logger.info(f"Successfully connected to database at {db_path}")
        return conn
    except sqlite3.OperationalError as e:
        # Log the error and provide more context
        error_msg = f"Failed to connect to database at {db_path}: {e}"
        logger.error(error_msg)
        raise HTTPException(
            status_code=500,
            detail="Database connection failed. Please check if the database file exists and is accessible."
        )

llm_router = LLMRouter()

# Data models
class TaskCreate(BaseModel):
    description: str
    project: Optional[str] = None
    tags: Optional[List[str]] = None
    due: Optional[str] = None

class TaskUpdate(BaseModel):
    status: Optional[str] = None
    annotations: Optional[List[str]] = None

class TaskResponse(BaseModel):
    id: int
    tw_uuid: str
    description: str
    project: Optional[str] = None
    tags: Optional[List[str]] = None
    priority: Optional[str] = None
    urgency: Optional[float] = None
    status: str
    created_ts: int
    due_ts: Optional[int] = None
    updated_ts: int

class ChatRequest(BaseModel):
    message: str
    provider: str
    model: str
    history: List[dict]

# API endpoints
@app.get("/")
async def root():
    return {"message": "Agentic System API"}

@app.post("/api/chat")
async def chat(request: ChatRequest):
    """Handle a chat message"""
    logger.info(f"Received chat message for model {request.model} from provider {request.provider}: '{request.message}'")
    try:
        response_stream = llm_router.route(request.provider, request.model, request.message, request.history)
        return StreamingResponse(response_stream, media_type="text/event-stream")
    except Exception as e:
        logger.error(f"An error occurred while processing the chat message: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while processing the chat message.")

@app.get("/api/tasks", response_model=List[TaskResponse])
async def get_tasks(filter: Optional[str] = None):
    """Get tasks with optional filter"""
    logger.info(f"Attempting to fetch tasks with filter: {filter}")
    conn = get_db_connection()
    try:
        if filter:
            query = "SELECT * FROM tasks WHERE description LIKE ? OR project LIKE ? OR tags LIKE ?"
            params = (f"%{filter}%", f"%{filter}%", f"%{filter}%")
        else:
            query = "SELECT * FROM tasks"
            params = ()
        
        tasks = conn.execute(query, params).fetchall()
        logger.info(f"Successfully fetched {len(tasks)} tasks.")
        return [dict(task) for task in tasks]
    except Exception as e:
        logger.error(f"An error occurred while fetching tasks: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while fetching tasks.")
    finally:
        conn.close()

@app.post("/api/tasks", response_model=TaskResponse)
async def create_task(task: TaskCreate):
    """Create a new task"""
    logger.info(f"Attempting to create task: {task.description}")
    conn = get_db_connection()
    try:
        # In a real implementation, this would interface with Taskwarrior
        # For now, we'll create a mock task
        tw_uuid = "00000000-0000-0000-0000-" + str(int(datetime.now().timestamp()))[-12:]
        created_ts = int(datetime.now().timestamp())
        
        # Convert tags to string for storage
        tags_str = ",".join(task.tags) if task.tags else None
        
        query = """
        INSERT INTO tasks (tw_uuid, description, project, tags, priority, urgency, status, created_ts, updated_ts)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        cursor = conn.execute(query, (
            tw_uuid,
            task.description,
            task.project,
            tags_str,
            None,  # priority
            None,  # urgency
            "pending",
            created_ts,
            created_ts
        ))
        conn.commit()
        task_id = cursor.lastrowid
        logger.info(f"Successfully created task {task_id} with description: {task.description}")
        
        # Fetch the created task
        task_row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        return dict(task_row)
    except Exception as e:
        logger.error(f"An error occurred while creating task: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while creating the task.")
    finally:
        conn.close()

@app.patch("/api/tasks/{uuid}", response_model=TaskResponse)
async def update_task(uuid: str, task: TaskUpdate):
    """Update a task"""
    conn = get_db_connection()
    try:
        # Check if task exists
        existing_task = conn.execute("SELECT * FROM tasks WHERE tw_uuid = ?", (uuid,)).fetchone()
        if not existing_task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Update task
        updated_ts = int(datetime.now().timestamp())
        query = "UPDATE tasks SET status = ?, updated_ts = ? WHERE tw_uuid = ?"
        conn.execute(query, (task.status or existing_task['status'], updated_ts, uuid))
        conn.commit()
        
        # Fetch the updated task
        task_row = conn.execute("SELECT * FROM tasks WHERE tw_uuid = ?", (uuid,)).fetchone()
        return dict(task_row)
    finally:
        conn.close()

@app.get("/api/runs")
async def get_runs(task_uuid: Optional[str] = None):
    """Get agent runs with optional task filter"""
    conn = get_db_connection()
    try:
        if task_uuid:
            # First get task id from uuid
            task = conn.execute("SELECT id FROM tasks WHERE tw_uuid = ?", (task_uuid,)).fetchone()
            if not task:
                return []
            query = "SELECT * FROM runs WHERE task_id = ?"
            params = (task['id'],)
        else:
            query = "SELECT * FROM runs"
            params = ()
        
        runs = conn.execute(query, params).fetchall()
        return [dict(run) for run in runs]
    finally:
        conn.close()

@app.post("/api/plan")
async def plan_task(task_uuid: str):
    """Plan execution for a task"""
    # In a real implementation, this would use the Policy Engine
    return {
        "task_uuid": task_uuid,
        "plan": {
            "agent": "browser",
            "tool": "playwright",
            "params": {
                "timeout": 15,
                "retries": 2
            }
        }
    }

@app.get("/api/metrics/daily")
async def get_daily_metrics():
    """Get daily metrics"""
    conn = get_db_connection()
    try:
        metrics = conn.execute("SELECT * FROM metrics_daily ORDER BY day").fetchall()
        return [dict(metric) for metric in metrics]
    finally:
        conn.close()

@app.get("/api/policy")
async def get_policy():
    """Get current policy configuration"""
    # In a real implementation, this would load from configs/policy.yaml
    return {
        "routing": {
            "max_latency_ms": 12000,
            "min_success_prior": 0.55,
            "prefer_cached_when_ping_ms_gt": 120
        },
        "agents": {
            "browser": {
                "default_timeout_s": 15,
                "max_retries": 2,
                "headed_on_flake_rate_gt": 0.25
            }
        }
    }

@app.post("/api/policy")
async def update_policy(patch: dict):
    """Update policy configuration"""
    # In a real implementation, this would update configs/policy.yaml
    return {"message": "Policy updated", "patch": patch}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9000)