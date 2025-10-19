from typing import Dict, Any
import logging
import json
import os
import time
import redis

# Local imports
from . import redis_pool
from .exceptions import RedisError

class Coordinator:
    """Main coordinator for the agentic system with Redis error handling"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing Coordinator")
        
        # Metrics
        self.total_tasks_processed = 0
        self.total_tasks_enqueued = 0
        self.total_processing_time_ms = 0
        self.total_enqueue_time_ms = 0
        
        # Connect to Redis for message queue
        try:
            self.redis_client = redis_pool.get_connection()
        except RedisError as e:
            self.logger.error("Failed to initialize Coordinator due to Redis error", extra={
                "event": "coordinator_init_redis_error",
                "error": str(e),
                "error_code": e.error_code
            })
            raise
        except Exception as e:
            self.logger.error("Failed to initialize Coordinator", extra={
                "event": "coordinator_init_failed",
                "error": str(e),
                "error_type": type(e).__name__
            })
            raise RedisError(f"Failed to initialize Coordinator: {str(e)}", "COORDINATOR_INIT_ERROR")
        
        # Queue name
        self.task_queue = "task_queue"
        
    def process_task(self, task_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Process a task through the system with Redis error handling"""
        start_time = time.time()
        self.total_tasks_processed += 1
        
        # Log structured information about the task
        task_id = task_spec.get("id", "unknown")
        task_description = task_spec.get("description", "no description")
        self.logger.info(f"Processing task {task_id}: {task_description}")
        
        # In a real implementation, this would:
        # 1. Use the Policy Engine to decide which agent to use
        # 2. Enqueue the task to the message queue
        # 3. Wait for the result
        
        # For now, we'll just enqueue the task
        enqueue_start = time.time()
        try:
            self.redis_client.lpush(self.task_queue, json.dumps(task_spec))
            enqueue_time = (time.time() - enqueue_start) * 1000
            self.total_enqueue_time_ms += enqueue_time
            self.total_tasks_enqueued += 1
            
            processing_time = (time.time() - start_time) * 1000
            self.total_processing_time_ms += processing_time
            
            # Log structured result
            self.logger.info(
                "Task enqueued successfully",
                extra={
                    "task_id": task_id,
                    "status": "enqueued",
                    "enqueue_time_ms": enqueue_time,
                    "processing_time_ms": processing_time
                }
            )
            
            return {
                "status": "enqueued",
                "task_id": task_id,
                "message": "Task has been enqueued for processing",
                "processing_time_ms": processing_time
            }
        except redis.ConnectionError as e:
            enqueue_time = (time.time() - enqueue_start) * 1000
            self.total_enqueue_time_ms += enqueue_time
            processing_time = (time.time() - start_time) * 1000
            self.total_processing_time_ms += processing_time
            
            # Log structured error
            self.logger.error(
                f"Redis connection error while enqueuing task {task_id}",
                extra={
                    "task_id": task_id,
                    "status": "error",
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "enqueue_time_ms": enqueue_time,
                    "processing_time_ms": processing_time
                }
            )
            
            return {
                "status": "error",
                "task_id": task_id,
                "error": f"Redis connection error: {str(e)}",
                "processing_time_ms": processing_time
            }
        except redis.TimeoutError as e:
            enqueue_time = (time.time() - enqueue_start) * 1000
            self.total_enqueue_time_ms += enqueue_time
            processing_time = (time.time() - start_time) * 1000
            self.total_processing_time_ms += processing_time
            
            # Log structured error
            self.logger.error(
                f"Redis timeout error while enqueuing task {task_id}",
                extra={
                    "task_id": task_id,
                    "status": "error",
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "enqueue_time_ms": enqueue_time,
                    "processing_time_ms": processing_time
                }
            )
            
            return {
                "status": "error",
                "task_id": task_id,
                "error": f"Redis timeout error: {str(e)}",
                "processing_time_ms": processing_time
            }
        except redis.RedisError as e:
            enqueue_time = (time.time() - enqueue_start) * 1000
            self.total_enqueue_time_ms += enqueue_time
            processing_time = (time.time() - start_time) * 1000
            self.total_processing_time_ms += processing_time
            
            # Log structured error
            self.logger.error(
                f"Redis error while enqueuing task {task_id}",
                extra={
                    "task_id": task_id,
                    "status": "error",
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "enqueue_time_ms": enqueue_time,
                    "processing_time_ms": processing_time
                }
            )
            
            return {
                "status": "error",
                "task_id": task_id,
                "error": f"Redis error: {str(e)}",
                "processing_time_ms": processing_time
            }
        except Exception as e:
            enqueue_time = (time.time() - enqueue_start) * 1000
            self.total_enqueue_time_ms += enqueue_time
            processing_time = (time.time() - start_time) * 1000
            self.total_processing_time_ms += processing_time
            
            # Log structured error
            self.logger.error(
                f"Unexpected error while enqueuing task {task_id}: {e}",
                extra={
                    "task_id": task_id,
                    "status": "error",
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "enqueue_time_ms": enqueue_time,
                    "processing_time_ms": processing_time
                }
            )
            
            return {
                "status": "error",
                "task_id": task_id,
                "error": f"Unexpected error: {str(e)}",
                "processing_time_ms": processing_time
            }

if __name__ == "__main__":
    # For testing purposes
    try:
        coordinator = Coordinator()
        result = coordinator.process_task({"id": 1, "description": "Test task"})
        print(result)
    except Exception as e:
        print(f"Error in Coordinator test: {e}")