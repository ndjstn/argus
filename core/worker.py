
import time
import logging
import json
import redis
import sqlite3
from . import redis_pool
from .database import db_pool
from .exceptions import RedisError, DatabaseError

class Worker:
    """A worker that processes tasks from the message queue."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing Worker")
        self.task_queue = "task_queue"
        self.shutdown_event = False

        try:
            self.redis_client = redis_pool.get_connection()
            self.db_conn = db_pool.get_connection()
        except (RedisError, DatabaseError) as e:
            self.logger.error(f"Failed to initialize Worker: {e}")
            raise

    def run(self):
        """Continuously process tasks from the queue."""
        self.logger.info("Worker started")
        while not self.shutdown_event:
            try:
                # Blocking pop from the queue
                _, task_data = self.redis_client.brpop(self.task_queue)
                task = json.loads(task_data)
                self.process_task(task)
            except redis.ConnectionError as e:
                self.logger.error(f"Redis connection error: {e}")
                time.sleep(5)  # Wait before retrying
            except Exception as e:
                self.logger.error(f"An unexpected error occurred: {e}")

    def process_task(self, task: dict):
        """Process a single task."""
        task_id = task.get("id")
        self.logger.info(f"Processing task {task_id}")

        # Simulate work
        time.sleep(2)

        # Update task status in the database
        try:
            cursor = self.db_conn.cursor()
            cursor.execute("UPDATE tasks SET status = ? WHERE id = ?", ("completed", task_id))
            self.db_conn.commit()
            self.logger.info(f"Task {task_id} completed")
        except sqlite3.Error as e:
            self.logger.error(f"Database error while updating task {task_id}: {e}")

    def shutdown(self):
        """Gracefully shut down the worker."""
        self.logger.info("Shutting down worker")
        self.shutdown_event = True
        redis_pool.close_all()
        db_pool.close_all()

if __name__ == "__main__":
    worker = Worker()
    worker.run()
