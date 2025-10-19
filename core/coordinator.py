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
    
    def __init__(self) -> None:
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
        
    def _handle_task_error(self, task_id: str, e: Exception, start_time: float, enqueue_start: float) -> Dict[str, Any]:
        """Helper method to handle errors during task processing."""
        enqueue_time = (time.time() - enqueue_start) * 1000
        self.total_enqueue_time_ms += enqueue_time
        processing_time = (time.time() - start_time) * 1000
        self.total_processing_time_ms += processing_time

        error_type = type(e).__name__
        error_message = str(e)

        self.logger.error(
            f"Error while enqueuing task {task_id}: {error_message}",
            extra={
                "task_id": task_id,
                "status": "error",
                "error": error_message,
                "error_type": error_type,
                "enqueue_time_ms": enqueue_time,
                "processing_time_ms": processing_time
            }
        )

        return {
            "status": "error",
            "task_id": task_id,
            "error": f"{error_type}: {error_message}",
            "processing_time_ms": processing_time
        }

    def process_task(self, task_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Process a task through the system with Redis error handling"""
        start_time = time.time()
        self.total_tasks_processed += 1
        
        task_id = task_spec.get("id", "unknown")
        task_description = task_spec.get("description", "no description")
        self.logger.info(f"Processing task {task_id}: {task_description}")
        
        enqueue_start = time.time()
        try:
            self.redis_client.lpush(self.task_queue, json.dumps(task_spec))
            enqueue_time = (time.time() - enqueue_start) * 1000
            self.total_enqueue_time_ms += enqueue_time
            self.total_tasks_enqueued += 1
            
            processing_time = (time.time() - start_time) * 1000
            self.total_processing_time_ms += processing_time
            
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
        except (redis.ConnectionError, redis.TimeoutError, redis.RedisError) as e:
            return self._handle_task_error(task_id, e, start_time, enqueue_start)
        except Exception as e:
            return self._handle_task_error(task_id, e, start_time, enqueue_start)


if __name__ == "__main__":
    # For testing purposes
    try:
        coordinator = Coordinator()
        result = coordinator.process_task({"id": 1, "description": "Test task"})
        print(result)
    except Exception as e:
        print(f"Error in Coordinator test: {e}")