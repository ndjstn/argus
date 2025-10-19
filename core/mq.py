from typing import Dict, Any
import logging
import json
import os
import time
import redis

# Local imports
from .redis_pool import redis_pool
from .exceptions import RedisError

class MessageQueue:
    """Message queue for inter-component communication with Redis error handling"""
    
    def __init__(self, queue_name: str = "task_queue"):
        self.logger = logging.getLogger(__name__)
        self.enqueue_count = 0
        self.dequeue_count = 0
        self.logger.info("Initializing Message Queue")
        
        # Store queue name
        self.queue_name = queue_name
        
        # Test Redis connection
        try:
            with redis_pool.connection() as conn:
                conn.ping()
            self.logger.info("MessageQueue initialized successfully", extra={
                "event": "mq_init_success",
                "queue_name": queue_name
            })
        except RedisError as e:
            self.logger.error("Failed to initialize MessageQueue due to Redis error", extra={
                "event": "mq_init_redis_error",
                "queue_name": queue_name,
                "error": str(e),
                "error_code": e.error_code
            })
            raise
        except Exception as e:
            self.logger.error("Failed to initialize MessageQueue", extra={
                "event": "mq_init_failed",
                "queue_name": queue_name,
                "error": str(e),
                "error_type": type(e).__name__
            })
            raise RedisError(f"Failed to initialize MessageQueue: {str(e)}", "MQ_INIT_ERROR")
        
    def enqueue(self, message: Dict[str, Any]) -> bool:
        """Enqueue a message with Redis error handling"""
        start_time = time.time()
        self.enqueue_count += 1
        
        # Log the enqueue attempt
        self.logger.debug("Enqueuing message", extra={
            "event": "mq_enqueue_start",
            "queue_name": self.queue_name,
            "message_type": message.get("type", "unknown"),
            "enqueue_count": self.enqueue_count
        })
        
        try:
            with redis_pool.connection() as conn:
                conn.lpush(self.queue_name, json.dumps(message))
            enqueue_time = time.time() - start_time
            self.logger.info("Message enqueued successfully", extra={
                "event": "mq_enqueue_success",
                "queue_name": self.queue_name,
                "message_type": message.get("type", "unknown"),
                "enqueue_time_ms": round(enqueue_time * 1000, 2),
                "enqueue_count": self.enqueue_count
            })
            return True
        except redis.ConnectionError as e:
            enqueue_time = time.time() - start_time
            self.logger.error("Redis connection error during enqueue", extra={
                "event": "mq_enqueue_redis_connection_error",
                "queue_name": self.queue_name,
                "error": str(e),
                "error_type": type(e).__name__,
                "enqueue_time_ms": round(enqueue_time * 1000, 2),
                "enqueue_count": self.enqueue_count
            })
            return False
        except redis.TimeoutError as e:
            enqueue_time = time.time() - start_time
            self.logger.error("Redis timeout error during enqueue", extra={
                "event": "mq_enqueue_redis_timeout_error",
                "queue_name": self.queue_name,
                "error": str(e),
                "error_type": type(e).__name__,
                "enqueue_time_ms": round(enqueue_time * 1000, 2),
                "enqueue_count": self.enqueue_count
            })
            return False
        except redis.RedisError as e:
            enqueue_time = time.time() - start_time
            self.logger.error("Redis error during enqueue", extra={
                "event": "mq_enqueue_redis_error",
                "queue_name": self.queue_name,
                "error": str(e),
                "error_type": type(e).__name__,
                "enqueue_time_ms": round(enqueue_time * 1000, 2),
                "enqueue_count": self.enqueue_count
            })
            return False
        except Exception as e:
            enqueue_time = time.time() - start_time
            self.logger.error("Unexpected error during enqueue", extra={
                "event": "mq_enqueue_unexpected_error",
                "queue_name": self.queue_name,
                "error": str(e),
                "error_type": type(e).__name__,
                "enqueue_time_ms": round(enqueue_time * 1000, 2),
                "enqueue_count": self.enqueue_count
            })
            return False
        
    def dequeue(self, timeout: float = 1.0) -> Dict[str, Any]:
        """Dequeue a message with Redis error handling and configurable timeout"""
        start_time = time.time()
        self.dequeue_count += 1
        
        # Log the dequeue attempt
        self.logger.debug("Dequeuing message", extra={
            "event": "mq_dequeue_start",
            "queue_name": self.queue_name,
            "dequeue_count": self.dequeue_count,
            "timeout": timeout
        })
        
        try:
            with redis_pool.connection() as conn:
                message = conn.brpop(self.queue_name, timeout=timeout)
            dequeue_time = time.time() - start_time
            if message:
                msg_data = json.loads(message[1])
                self.logger.info("Message dequeued successfully", extra={
                    "event": "mq_dequeue_success",
                    "queue_name": self.queue_name,
                    "message_type": msg_data.get("type", "unknown"),
                    "dequeue_time_ms": round(dequeue_time * 1000, 2),
                    "has_message": True,
                    "dequeue_count": self.dequeue_count
                })
                return msg_data
            else:
                self.logger.info("No message available for dequeue", extra={
                "event": "mq_dequeue_empty",
                "queue_name": self.queue_name,
                "dequeue_time_ms": round(dequeue_time * 1000, 2),
                "has_message": False,
                "dequeue_count": self.dequeue_count
            })
                return {}
        except redis.ConnectionError as e:
            dequeue_time = time.time() - start_time
            self.logger.error("Redis connection error during dequeue", extra={
                "event": "mq_dequeue_redis_connection_error",
                "queue_name": self.queue_name,
                "error": str(e),
                "error_type": type(e).__name__,
                "dequeue_time_ms": round(dequeue_time * 1000, 2),
                "dequeue_count": self.dequeue_count
            })
            return {}
        except redis.TimeoutError as e:
            dequeue_time = time.time() - start_time
            self.logger.error("Redis timeout error during dequeue", extra={
                "event": "mq_dequeue_redis_timeout_error",
                "queue_name": self.queue_name,
                "error": str(e),
                "error_type": type(e).__name__,
                "dequeue_time_ms": round(dequeue_time * 1000, 2),
                "dequeue_count": self.dequeue_count
            })
            return {}
        except redis.RedisError as e:
            dequeue_time = time.time() - start_time
            self.logger.error("Redis error during dequeue", extra={
                "event": "mq_dequeue_redis_error",
                "queue_name": self.queue_name,
                "error": str(e),
                "error_type": type(e).__name__,
                "dequeue_time_ms": round(dequeue_time * 1000, 2),
                "dequeue_count": self.dequeue_count
            })
            return {}
        except Exception as e:
            dequeue_time = time.time() - start_time
            self.logger.error("Unexpected error during dequeue", extra={
                "event": "mq_dequeue_unexpected_error",
                "queue_name": self.queue_name,
                "error": str(e),
                "error_type": type(e).__name__,
                "dequeue_time_ms": round(dequeue_time * 1000, 2),
                "dequeue_count": self.dequeue_count
            })
            return {}
            
    def get_queue_info(self) -> Dict[str, Any]:
        """Get information about the message queue for monitoring with Redis error handling"""
        try:
            with redis_pool.connection() as conn:
                queue_length = conn.llen(self.queue_name)
            return {
                "queue_name": self.queue_name,
                "queue_length": queue_length,
                "enqueue_count": self.enqueue_count,
                "dequeue_count": self.dequeue_count
            }
        except redis.ConnectionError as e:
            self.logger.error("Redis connection error getting queue info", extra={
                "event": "mq_get_info_redis_connection_error",
                "queue_name": self.queue_name,
                "error": str(e),
                "error_type": type(e).__name__
            })
            return {
                "queue_name": self.queue_name,
                "queue_length": -1,
                "enqueue_count": self.enqueue_count,
                "dequeue_count": self.dequeue_count
            }
        except redis.TimeoutError as e:
            self.logger.error("Redis timeout error getting queue info", extra={
                "event": "mq_get_info_redis_timeout_error",
                "queue_name": self.queue_name,
                "error": str(e),
                "error_type": type(e).__name__
            })
            return {
                "queue_name": self.queue_name,
                "queue_length": -1,
                "enqueue_count": self.enqueue_count,
                "dequeue_count": self.dequeue_count
            }
        except redis.RedisError as e:
            self.logger.error("Redis error getting queue info", extra={
                "event": "mq_get_info_redis_error",
                "queue_name": self.queue_name,
                "error": str(e),
                "error_type": type(e).__name__
            })
            return {
                "queue_name": self.queue_name,
                "queue_length": -1,
                "enqueue_count": self.enqueue_count,
                "dequeue_count": self.dequeue_count
            }
        except Exception as e:
            self.logger.error("Unexpected error getting queue info", extra={
                "event": "mq_get_info_unexpected_error",
                "queue_name": self.queue_name,
                "error": str(e),
                "error_type": type(e).__name__
            })
            return {
                "queue_name": self.queue_name,
                "queue_length": -1,
                "enqueue_count": self.enqueue_count,
                "dequeue_count": self.dequeue_count
            }

if __name__ == "__main__":
    # For testing purposes
    try:
        mq = MessageQueue()
        mq.enqueue({"type": "task.enqueued", "task_id": 1})
        message = mq.dequeue()
        print(message)
    except Exception as e:
        print(f"Error in MessageQueue test: {e}")