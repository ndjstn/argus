import redis
import threading
import atexit
from typing import Optional
import logging
import os
import yaml
from contextlib import contextmanager

# Local imports
from .exceptions import RedisError

logger = logging.getLogger(__name__)

class RedisConnectionPool:
    """Redis connection pool for thread-safe Redis access with error handling"""
    
    def __init__(self, host: str = None, port: int = None, max_connections: int = 20):
        self.host = host or os.getenv("REDIS_HOST", "localhost")
        self.port = port or int(os.getenv("REDIS_PORT", 6379))
        self.max_connections = max_connections
        self._shutdown = False
        
        try:
            # Create Redis connection pool
            self.pool = redis.ConnectionPool(
                host=self.host,
                port=self.port,
                max_connections=max_connections,
                decode_responses=True,
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            # Register cleanup handler
            atexit.register(self.close_all)
            
            logger.info("Initialized Redis connection pool", extra={
                "event": "redis_pool_initialized",
                "host": self.host,
                "port": self.port,
                "max_connections": max_connections
            })
        except Exception as e:
            logger.error("Failed to initialize Redis connection pool", extra={
                "event": "redis_pool_init_failed",
                "host": self.host,
                "port": self.port,
                "error": str(e),
                "error_type": type(e).__name__
            })
            raise RedisError(f"Failed to initialize Redis connection pool: {str(e)}", "REDIS_POOL_INIT_ERROR")
    
    def get_connection(self) -> redis.Redis:
        """Get a connection from the pool with error handling"""
        if self._shutdown:
            raise RedisError("Redis connection pool is shut down", "REDIS_POOL_SHUTDOWN")
        
        try:
            conn = redis.Redis(connection_pool=self.pool)
            # Test the connection
            conn.ping()
            return conn
        except redis.ConnectionError as e:
            logger.error("Redis connection error", extra={
                "event": "redis_connection_error",
                "host": self.host,
                "port": self.port,
                "error": str(e),
                "error_type": type(e).__name__
            })
            raise RedisError(f"Redis connection failed: {str(e)}", "REDIS_CONNECTION_ERROR")
        except redis.TimeoutError as e:
            logger.error("Redis timeout error", extra={
                "event": "redis_timeout_error",
                "host": self.host,
                "port": self.port,
                "error": str(e),
                "error_type": type(e).__name__
            })
            raise RedisError(f"Redis operation timed out: {str(e)}", "REDIS_TIMEOUT_ERROR")
        except Exception as e:
            logger.error("Unexpected Redis error", extra={
                "event": "redis_unexpected_error",
                "host": self.host,
                "port": self.port,
                "error": str(e),
                "error_type": type(e).__name__
            })
            raise RedisError(f"Unexpected Redis error: {str(e)}", "REDIS_UNEXPECTED_ERROR")
    
    @contextmanager
    def connection(self):
        """Context manager for Redis connections"""
        conn = None
        try:
            conn = self.get_connection()
            yield conn
        except Exception as e:
            logger.error("Redis operation failed", extra={
                "event": "redis_operation_failed",
                "host": self.host,
                "port": self.port,
                "error": str(e),
                "error_type": type(e).__name__
            })
            raise
        finally:
            # Redis connections from a pool are automatically returned to the pool
            # when they go out of scope, but we can explicitly close them if needed
            if conn:
                try:
                    # For Redis, we don't need to explicitly close connections from a pool
                    # They are automatically managed by the connection pool
                    pass
                except Exception as e:
                    logger.warning("Error during Redis connection cleanup", extra={
                        "event": "redis_connection_cleanup_error",
                        "host": self.host,
                        "port": self.port,
                        "error": str(e),
                        "error_type": type(e).__name__
                    })
    
    def close_all(self):
        """Close all connections in the pool"""
        if self._shutdown:
            return
            
        self._shutdown = True
        try:
            if self.pool:
                # Disconnect all connections in the pool
                self.pool.disconnect()
                logger.info("Closed all Redis connections in pool", extra={
                    "event": "redis_pool_closed",
                    "host": self.host,
                    "port": self.port
                })
        except Exception as e:
            logger.error("Error closing Redis connection pool", extra={
                "event": "redis_pool_close_error",
                "host": self.host,
                "port": self.port,
                "error": str(e),
                "error_type": type(e).__name__
            })
            raise RedisError(f"Error closing Redis connection pool: {str(e)}", "REDIS_POOL_CLOSE_ERROR")
    
    def get_pool_info(self) -> dict:
        """Get information about the connection pool"""
        try:
            return {
                "host": self.host,
                "port": self.port,
                "max_connections": self.max_connections,
                "created_connections": len(self.pool._available_connections) + len(self.pool._in_use_connections),
                "available_connections": len(self.pool._available_connections),
                "in_use_connections": len(self.pool._in_use_connections)
            }
        except Exception as e:
            logger.error("Failed to get Redis pool info", extra={
                "event": "redis_pool_info_failed",
                "error": str(e),
                "error_type": type(e).__name__
            })
            return {
                "host": self.host,
                "port": self.port,
                "max_connections": self.max_connections,
                "created_connections": -1,
                "available_connections": -1,
                "in_use_connections": -1
            }

def load_redis_config():
    """Load Redis configuration from config file"""
    config_path = os.path.join(os.path.dirname(__file__), "..", "configs", "policy.yaml")
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config.get('redis', {})
    except Exception as e:
        logger.warning("Failed to load Redis config, using defaults", extra={
            "event": "redis_config_load_failed",
            "config_path": config_path,
            "error": str(e),
            "error_type": type(e).__name__
        })
        return {}

# Initialize the Redis pool with configuration
try:
    redis_config = load_redis_config()
    redis_pool = RedisConnectionPool(
        host=redis_config.get('host'),
        port=redis_config.get('port'),
        max_connections=redis_config.get('max_connections', 20)
    )
except Exception as e:
    logger.error("Failed to initialize global Redis pool", extra={
        "event": "global_redis_pool_init_failed",
        "error": str(e),
        "error_type": type(e).__name__
    })
    redis_pool = None