
import time
import logging
import json
import redis
import sqlite3
from . import redis_pool
from .database import db_pool
from .exceptions import RedisError, DatabaseError
from agents.browser_agent.main import BrowserAgent

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

        self.browser_agent = BrowserAgent()

    def run(self):
        """Continuously process tasks from the queue."""
        self.logger.info("Worker started and listening for tasks.")
        while not self.shutdown_event:
            try:
                # Blocking pop from the queue
                self.logger.debug("Waiting for task on queue: %s", self.task_queue)
                _, task_data = self.redis_client.brpop(self.task_queue)
                self.logger.debug("Received task data from queue.")
                task = json.loads(task_data)
                self.process_task(task)
            except redis.ConnectionError as e:
                self.logger.error(f"Redis connection error: {e}. Retrying in 5 seconds.")
                time.sleep(5)  # Wait before retrying
            except json.JSONDecodeError as e:
                self.logger.error(f"Error decoding task data: {e}. Task data: {task_data}")
            except Exception as e:
                self.logger.error(f"An unexpected error occurred in worker run loop: {e}")

    def process_task(self, task: dict):
        """Process a single task."""
        task_id = task.get("id")
        self.logger.info(f"Starting processing for task {task_id}.")
        self.logger.debug(f"Task details: {task}")

        try:
            if task.get("browser_task"):
                self.logger.info(f"Task {task_id} is a browser task. Executing with BrowserAgent.")
                result = self.browser_agent.execute_task(task)
                status = result.get("status")
                self.logger.info(f"BrowserAgent finished task {task_id} with status: {status}")
            else:
                self.logger.info(f"Task {task_id} is a generic task. Simulating work.")
                # Simulate work for non-browser tasks
                time.sleep(2)
                status = "completed"
                self.logger.info(f"Generic task {task_id} completed.")

            # Update task status in the database
            self.logger.debug(f"Updating task {task_id} status to '{status}' in the database.")
            cursor = self.db_conn.cursor()
            cursor.execute("UPDATE tasks SET status = ? WHERE id = ?", (status, task_id))
            self.db_conn.commit()
            self.logger.info(f"Successfully updated task {task_id} to status '{status}'.")
        except Exception as e:
            self.logger.error(f"An error occurred while processing task {task_id}: {e}")
            # Optionally, update the task status to 'failed' in the database
            try:
                cursor = self.db_conn.cursor()
                cursor.execute("UPDATE tasks SET status = ? WHERE id = ?", ("failed", task_id))
                self.db_conn.commit()
                self.logger.info(f"Updated task {task_id} status to 'failed'.")
            except Exception as db_e:
                self.logger.error(f"Could not update task {task_id} status to 'failed': {db_e}")

    def shutdown(self):
        """Gracefully shut down the worker."""
        self.logger.info("Shutting down worker")
        self.shutdown_event = True
        redis_pool.close_all()
        db_pool.close_all()

if __name__ == "__main__":
    worker = Worker()
    worker.run()
