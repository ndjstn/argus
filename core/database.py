import sqlite3
import threading
import time
from typing import Optional
from contextlib import contextmanager
import logging
import os
import yaml

logger = logging.getLogger(__name__)

class DatabaseError(Exception):
    """Custom exception for database operations"""
    pass

class DatabaseConnectionPool:
    """SQLite connection pool for thread-safe database access"""
    
    def __init__(self, db_path: str, max_connections: int = 10):
        self.db_path = db_path
        self.max_connections = max_connections
        self.connections = []
        self.lock = threading.Lock()
        self.connection_count = 0
        
        # Metrics
        self.total_connections_created = 0
        self.total_connections_returned = 0
        self.total_connections_closed = 0
        self.total_get_connection_calls = 0
        self.total_wait_time_ms = 0
        self.total_errors = 0
        
        # Ensure database file exists
        try:
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            if not os.path.exists(db_path):
                # Create the database file
                conn = sqlite3.connect(db_path)
                conn.close()
            logger.info(f"Initialized database connection pool with max {max_connections} connections")
        except Exception as e:
            logger.error(f"Failed to initialize database connection pool: {e}")
            raise DatabaseError(f"Failed to initialize database connection pool: {e}")
    
    def get_connection(self) -> sqlite3.Connection:
        """Get a connection from the pool"""
        start_time = time.time()
        self.total_get_connection_calls += 1
        
        try:
            with self.lock:
                wait_time = (time.time() - start_time) * 1000
                self.total_wait_time_ms += wait_time
                
                if self.connections:
                    self.total_connections_returned += 1
                    conn = self.connections.pop()
                    # Verify connection is still valid
                    try:
                        conn.execute("SELECT 1")
                        return conn
                    except sqlite3.Error:
                        # Connection is invalid, create a new one
                        self.connection_count -= 1
                        self.total_connections_closed += 1
                        self.total_errors += 1
                        logger.warning("Invalid connection found in pool, creating new one")
                
                if self.connection_count < self.max_connections:
                    self.connection_count += 1
                    self.total_connections_created += 1
                    try:
                        conn = sqlite3.connect(self.db_path)
                        conn.row_factory = sqlite3.Row
                        # Enable foreign key constraints
                        conn.execute("PRAGMA foreign_keys = ON")
                        return conn
                    except sqlite3.Error as e:
                        self.connection_count -= 1
                        self.total_errors += 1
                        logger.error(f"Failed to create database connection: {e}")
                        raise DatabaseError(f"Failed to create database connection: {e}")
                
                # If we've reached max connections, wait for one to be returned
                # This is a simple implementation - in production you might want to use a queue
                self.total_errors += 1
                raise DatabaseError("Maximum database connections reached")
        except Exception as e:
            if not isinstance(e, DatabaseError):
                self.total_errors += 1
                logger.error(f"Unexpected error in get_connection: {e}")
                raise DatabaseError(f"Unexpected error in get_connection: {e}")
            raise
    
    def return_connection(self, conn: sqlite3.Connection):
        """Return a connection to the pool"""
        try:
            with self.lock:
                if len(self.connections) < self.max_connections:
                    # Check if connection is still valid before returning to pool
                    try:
                        conn.execute("SELECT 1")
                        self.connections.append(conn)
                        self.total_connections_returned += 1
                    except sqlite3.Error:
                        # Connection is invalid, close it
                        conn.close()
                        self.connection_count -= 1
                        self.total_connections_closed += 1
                        self.total_errors += 1
                        logger.warning("Invalid connection returned to pool, closing it")
                else:
                    # Close the connection if pool is full
                    conn.close()
                    self.connection_count -= 1
                    self.total_connections_closed += 1
        except Exception as e:
            self.total_errors += 1
            logger.error(f"Error returning connection to pool: {e}")
            # Try to close the connection to prevent leaks
            try:
                conn.close()
            except:
                pass
            raise DatabaseError(f"Error returning connection to pool: {e}")
    
    @contextmanager
    def connection(self):
        """Context manager for database connections"""
        conn = None
        try:
            conn = self.get_connection()
            yield conn
        except Exception as e:
            self.total_errors += 1
            logger.error(f"Database operation failed: {e}")
            if conn:
                try:
                    conn.rollback()
                except:
                    pass
            raise
        finally:
            if conn:
                try:
                    self.return_connection(conn)
                except Exception as e:
                    self.total_errors += 1
                    logger.error(f"Failed to return connection to pool: {e}")
    
    def close_all(self):
        """Close all connections in the pool"""
        try:
            with self.lock:
                for conn in self.connections:
                    try:
                        conn.close()
                        self.total_connections_closed += 1
                    except Exception as e:
                        self.total_errors += 1
                        logger.warning(f"Error closing connection: {e}")
                self.connections.clear()
                self.connection_count = 0
        except Exception as e:
            self.total_errors += 1
            logger.error(f"Error closing all connections: {e}")
            raise DatabaseError(f"Error closing all connections: {e}")
    
    def get_pool_stats(self) -> dict:
        """Get pool statistics for monitoring"""
        with self.lock:
            return {
                "available_connections": len(self.connections),
                "active_connections": self.connection_count - len(self.connections),
                "max_connections": self.max_connections,
                "total_connections_created": self.total_connections_created,
                "total_connections_returned": self.total_connections_returned,
                "total_connections_closed": self.total_connections_closed,
                "total_get_connection_calls": self.total_get_connection_calls,
                "total_wait_time_ms": self.total_wait_time_ms,
                "total_errors": self.total_errors
            }

def load_db_config():
    """Load database configuration from config file"""
    config_path = os.path.join(os.path.dirname(__file__), "..", "configs", "policy.yaml")
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config.get('database', {})
    except Exception as e:
        logger.warning(f"Failed to load database config, using defaults: {e}")
        return {}

# Initialize the database pool with configuration
db_config = load_db_config()
db_path = os.path.join(os.path.dirname(__file__), "..", "data", "core.db")
max_connections = db_config.get('max_connections', 20)
db_pool = DatabaseConnectionPool(db_path, max_connections=max_connections)