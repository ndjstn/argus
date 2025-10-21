#!/usr/bin/env python3

import os
import sys
import logging

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Local imports
from core import db_pool
from core.database import DatabaseError

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database schema
SCHEMA = """
-- tasks mirrored from Taskwarrior (subset + linkage)
CREATE TABLE IF NOT EXISTS tasks(
  id INTEGER PRIMARY KEY,
  tw_uuid TEXT UNIQUE,
  description TEXT,
  project TEXT, tags TEXT,
  priority TEXT, urgency REAL,
  status TEXT, created_ts INTEGER, due_ts INTEGER,
  updated_ts INTEGER
);

-- each agent run on a task
CREATE TABLE IF NOT EXISTS runs(
  id INTEGER PRIMARY KEY,
  task_id INTEGER, agent TEXT, tool TEXT,
  params_json TEXT,
  start_ts INTEGER, end_ts INTEGER,
  success INTEGER, error_code TEXT, retries INTEGER,
  bytes_in INTEGER, bytes_out INTEGER,
  latency_ms INTEGER, cpu_ms INTEGER, mem_mb REAL,
  notes TEXT,
  FOREIGN KEY(task_id) REFERENCES tasks(id)
);

-- aggregated daily stats
CREATE TABLE IF NOT EXISTS metrics_daily(
  day TEXT PRIMARY KEY,
  tasks_completed INTEGER,
  success_rate REAL,
  avg_latency_ms REAL,
  avg_retries REAL
);

-- learning features+labels for routing
CREATE TABLE IF NOT EXISTS train_examples(
  id INTEGER PRIMARY KEY,
  agent TEXT, tool TEXT, feature_json TEXT,
  label_success INTEGER,
  label_latency_ms INTEGER,
  created_ts INTEGER
);

-- policy parameters and model metadata
CREATE TABLE IF NOT EXISTS policy(
  key TEXT PRIMARY KEY,
  value_json TEXT,
  updated_ts INTEGER
);

-- conversation history for persistent chat
CREATE TABLE IF NOT EXISTS conversations(
  session_id TEXT PRIMARY KEY,
  history_json TEXT,
  created_ts INTEGER,
  updated_ts INTEGER
);
"""

# Indexes for performance
INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_runs_task ON runs(task_id);",
    "CREATE INDEX IF NOT EXISTS idx_runs_ts ON runs(start_ts);",
    "CREATE INDEX IF NOT EXISTS idx_train_agent ON train_examples(agent);"
]

# Index for conversation history
INDEXES.extend([
    "CREATE INDEX IF NOT EXISTS idx_conversations_updated ON conversations(updated_ts);"
])

def migrate_database():
    """Create or migrate the database schema"""
    db_path = os.path.join(os.path.dirname(__file__), "..", "data", "core.db")
    
    # Ensure data directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    logger.info(f"Connecting to database: {db_path}")
    try:
        with db_pool.connection() as conn:
            cursor = conn.cursor()
            
            # Execute schema creation
            logger.info("Creating database schema...")
            cursor.executescript(SCHEMA)
            
            # Create indexes
            logger.info("Creating indexes...")
            for index_sql in INDEXES:
                cursor.execute(index_sql)
            
            # Commit changes
            conn.commit()
            logger.info("Database migration completed successfully")
    except DatabaseError as e:
        logger.error(f"Database migration failed due to database error: {e}")
        raise
    except Exception as e:
        logger.error(f"Database migration failed due to unexpected error: {e}")
        raise DatabaseError(f"Database migration failed: {e}")

if __name__ == "__main__":
    try:
        migrate_database()
    except DatabaseError as e:
        logger.error(f"Migration failed: {e}")
        exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during migration: {e}")
        exit(1)