#!/usr/bin/env python3

import asyncio
import logging
import signal
import sys
from typing import List
import uvicorn
import threading
import time

# Local imports
from core.coordinator import Coordinator
from core.mq import MessageQueue
from core.redis_pool import redis_pool
from core.database import db_pool
from apps.proxy_api.main import app as fastapi_app
from core.worker import Worker

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ApplicationManager:
    """Manages the lifecycle of all application services"""
    
    def __init__(self):
        self.services = {}
        self.shutdown_event = threading.Event()
        
    def setup_signal_handlers(self):
        """Set up signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating shutdown...")
            self.shutdown()
            
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
    def start_api_server(self, host: str = "0.0.0.0", port: int = 9000):
        """Start the FastAPI server in a separate thread"""
        def run_server():
            try:
                logger.info(f"Starting API server on {host}:{port}")
                uvicorn.run(fastapi_app, host=host, port=port, log_level="info")
            except Exception as e:
                logger.error(f"API server error: {e}")
                
        api_thread = threading.Thread(target=run_server, daemon=True)
        api_thread.start()
        self.services["api_server"] = api_thread
        logger.info("API server thread started")
        
    def start_message_queue_processor(self):
        """Start the message queue processor with efficient event-driven mechanism"""
        def process_messages():
            try:
                mq = MessageQueue()
                logger.info("Message queue processor started")
                
                # Use a blocking mechanism instead of polling
                while not self.shutdown_event.is_set():
                    # Block with timeout to allow graceful shutdown
                    message = mq.dequeue(timeout=5.0)  # 5 second timeout for better efficiency
                    if message:
                        logger.info(f"Processing message: {message}")
                        # In a real implementation, this would route to appropriate agents
                    # No need for sleep - the dequeue call blocks until timeout or message
                        
            except Exception as e:
                logger.error(f"Message queue processor error: {e}")
                
        mq_thread = threading.Thread(target=process_messages, daemon=True)
        mq_thread.start()
        self.services["mq_processor"] = mq_thread
        logger.info("Message queue processor thread started")
        
    def start_coordinator(self):
        """Start the coordinator service with efficient event-driven mechanism"""
        def run_coordinator():
            try:
                coordinator = Coordinator()
                logger.info("Coordinator service started")
                
                # Use a work event to signal when there's work to do
                work_event = threading.Event()
                
                # In a real implementation, this would coordinate tasks
                while not self.shutdown_event.is_set():
                    # Wait for work or shutdown signal with timeout
                    work_event.wait(timeout=5.0)  # Check every 5 seconds for work
                    work_event.clear()
                    
                    # Check if there's work to do (placeholder for real implementation)
                    # If work is found, process it, then reset the event
                    # For now, this is just a placeholder
                    
            except Exception as e:
                logger.error(f"Coordinator service error: {e}")
                
        coordinator_thread = threading.Thread(target=run_coordinator, daemon=True)
        coordinator_thread.start()
        self.services["coordinator"] = coordinator_thread
        logger.info("Coordinator service thread started")

    def start_worker(self):
        """Start the worker service"""
        def run_worker():
            try:
                worker = Worker()
                worker.run()
            except Exception as e:
                logger.error(f"Worker service error: {e}")

        worker_thread = threading.Thread(target=run_worker, daemon=True)
        worker_thread.start()
        self.services["worker"] = worker_thread
        logger.info("Worker service thread started")
        
    def start_all_services(self):
        """Start all application services"""
        logger.info("Starting all application services...")
        
        # Start services
        self.start_api_server()
        self.start_message_queue_processor()
        self.start_coordinator()
        self.start_worker()
        
        logger.info("All services started")
        
    def shutdown(self):
        """Gracefully shutdown all services"""
        logger.info("Shutting down application services...")
        
        # Signal shutdown to all services
        self.shutdown_event.set()
        
        # Wait for threads to finish (with timeout)
        for name, thread in self.services.items():
            logger.info(f"Shutting down {name}...")
            thread.join(timeout=5.0)
            logger.info(f"{name} shut down.")
            
        # Close Redis pool
        if redis_pool:
            try:
                redis_pool.close_all()
                logger.info("Redis connection pool closed")
            except Exception as e:
                logger.error(f"Error closing Redis pool: {e}")
                
        # Close database pool
        if db_pool:
            try:
                db_pool.close_all()
                logger.info("Database connection pool closed")
            except Exception as e:
                logger.error(f"Error closing database pool: {e}")
                
        logger.info("Application shutdown complete")
        sys.exit(0)

    def run(self):
        """Run the application and wait for shutdown signal"""
        self.setup_signal_handlers()
        self.start_all_services()

        # Keep the main thread alive to handle signals
        try:
            self.shutdown_event.wait()
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received, shutting down...")
            self.shutdown()


if __name__ == "__main__":
    manager = ApplicationManager()
    manager.run()