from typing import Dict, Any, Callable
import logging
import json
import os
import time
import redis

# Local imports
from .redis_pool import redis_pool
from .exceptions import RedisError

class EventBus:
    """Event bus for system-wide event handling with Redis error handling"""
    
    def __init__(self, redis_host: str = None, redis_port: int = None):
        self.logger = logging.getLogger(__name__)
        self.publish_count = 0
        self.subscribe_count = 0
        self.logger.info("Initializing Event Bus")
        
        # Connect to Redis
        if redis_host is None:
            redis_host = os.getenv("REDIS_HOST", "localhost")
        if redis_port is None:
            redis_port = int(os.getenv("REDIS_PORT", 6379))
            
        # Test Redis connection
        try:
            with redis_pool.connection() as conn:
                conn.ping()
            self.handlers = {}
            self.logger.info("EventBus initialized successfully", extra={
                "event": "eventbus_init_success",
                "host": redis_host,
                "port": redis_port
            })
        except RedisError as e:
            self.logger.error("Failed to initialize EventBus due to Redis error", extra={
                "event": "eventbus_init_redis_error",
                "host": redis_host,
                "port": redis_port,
                "error": str(e),
                "error_code": e.error_code
            })
            raise
        except Exception as e:
            self.logger.error("Failed to initialize EventBus", extra={
                "event": "eventbus_init_failed",
                "host": redis_host,
                "port": redis_port,
                "error": str(e),
                "error_type": type(e).__name__
            })
            raise RedisError(f"Failed to initialize EventBus: {str(e)}", "EVENTBUS_INIT_ERROR")
        
    def subscribe(self, event_type: str, handler: Callable):
        """Subscribe to an event type"""
        self.subscribe_count += 1
        
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        
        self.handlers[event_type].append(handler)
        self.logger.info("Subscribed handler to event type", extra={
            "event": "eventbus_subscribe",
            "event_type": event_type,
            "handler_count": len(self.handlers[event_type]),
            "subscribe_count": self.subscribe_count
        })
        
        # In a real implementation, we would also subscribe to Redis pub/sub
        # for distributed event handling
        
    def publish(self, event: Dict[str, Any]):
        """Publish an event to all subscribers with Redis error handling"""
        start_time = time.time()
        self.publish_count += 1
        event_type = event.get("type")
        
        # Log the publish attempt
        self.logger.debug("Publishing event", extra={
            "event": "eventbus_publish_start",
            "event_type": event_type,
            "publish_count": self.publish_count
        })
        
        # Publish to Redis for distributed event handling
        redis_published = False
        try:
            with redis_pool.connection() as conn:
                conn.publish(f"events:{event_type}", json.dumps(event))
            redis_published = True
        except redis.ConnectionError as e:
            self.logger.error("Redis connection error during publish", extra={
                "event": "eventbus_redis_publish_connection_error",
                "event_type": event_type,
                "error": str(e),
                "error_type": type(e).__name__
            })
        except redis.TimeoutError as e:
            self.logger.error("Redis timeout error during publish", extra={
                "event": "eventbus_redis_publish_timeout_error",
                "event_type": event_type,
                "error": str(e),
                "error_type": type(e).__name__
            })
        except redis.RedisError as e:
            self.logger.error("Redis error during publish", extra={
                "event": "eventbus_redis_publish_error",
                "event_type": event_type,
                "error": str(e),
                "error_type": type(e).__name__
            })
        except Exception as e:
            self.logger.error("Unexpected error during Redis publish", extra={
                "event": "eventbus_redis_publish_unexpected_error",
                "event_type": event_type,
                "error": str(e),
                "error_type": type(e).__name__
            })
        
        # Publish to local handlers
        local_handlers_count = 0
        if event_type in self.handlers:
            local_handlers_count = len(self.handlers[event_type])
            self.logger.debug("Publishing to local handlers", extra={
                "event": "eventbus_local_publish_start",
                "event_type": event_type,
                "handler_count": local_handlers_count
            })
            
            handler_errors = 0
            for i, handler in enumerate(self.handlers[event_type]):
                try:
                    handler(event)
                except Exception as e:
                    handler_errors += 1
                    self.logger.error("Error in event handler", extra={
                        "event": "eventbus_handler_error",
                        "event_type": event_type,
                        "handler_index": i,
                        "error": str(e),
                        "error_type": type(e).__name__
                    })
            
            publish_time = time.time() - start_time
            self.logger.info("Event published successfully", extra={
                "event": "eventbus_publish_completed",
                "event_type": event_type,
                "redis_published": redis_published,
                "local_handlers_count": local_handlers_count,
                "handler_errors": handler_errors,
                "publish_time_ms": round(publish_time * 1000, 2),
                "publish_count": self.publish_count
            })
        else:
            publish_time = time.time() - start_time
            self.logger.info("Event published with no local handlers", extra={
                "event": "eventbus_publish_no_handlers",
                "event_type": event_type,
                "redis_published": redis_published,
                "publish_time_ms": round(publish_time * 1000, 2),
                "publish_count": self.publish_count
            })
            
    def get_eventbus_info(self) -> Dict[str, Any]:
        """Get information about the event bus for monitoring with Redis error handling"""
        handler_types = list(self.handlers.keys())
        handler_counts = {k: len(v) for k, v in self.handlers.items()}
        
        # Try to get Redis info
        redis_info = {}
        try:
            # Get Redis connection info from pool
            redis_info = getattr(redis_pool, 'get_pool_info', lambda: {})()
        except Exception as e:
            self.logger.warning("Failed to get Redis pool info", extra={
                "event": "eventbus_get_redis_info_failed",
                "error": str(e),
                "error_type": type(e).__name__
            })
        
        return {
            "publish_count": self.publish_count,
            "subscribe_count": self.subscribe_count,
            "handler_types": handler_types,
            "handler_counts": handler_counts,
            "redis_info": redis_info
        }

if __name__ == "__main__":
    # For testing purposes
    try:
        event_bus = EventBus()
        
        def sample_handler(event):
            print(f"Handling event: {event}")
        
        event_bus.subscribe("task.enqueued", sample_handler)
        event_bus.publish({"type": "task.enqueued", "task_id": 1})
    except Exception as e:
        print(f"Error in EventBus test: {e}")