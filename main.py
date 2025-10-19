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

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ApplicationManager:
    """Manages the lifecycle of all application services"""
    
    def __init__(self):
        self.services = []
        self.shutdown_event = threading.Event()
        self.threads = []
        
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
        self.threads.append(api_thread)
        logger.info("API server thread started")
        
    def start_message_queue_processor(self):
        """Start the message queue processor"""
        def process_messages():
            try:
                mq = MessageQueue()
                logger.info("Message queue processor started")
                
                while not self.shutdown_event.is_set():
                    # Process messages from queue
                    message = mq.dequeue()
                    if message:
                        logger.info(f"Processing message: {message}")
                        # In a real implementation, this would route to appropriate agents
                    else:
                        # No messages, sleep briefly
                        time.sleep(0.1)
                        
            except Exception as e:
                logger.error(f"Message queue processor error: {e}")
                
        mq_thread = threading.Thread(target=process_messages, daemon=True)
        mq_thread.start()
        self.threads.append(mq_thread)
        logger.info("Message queue processor thread started")
        
    def start_coordinator(self):
        """Start the coordinator service"""
        def run_coordinator():
            try:
                coordinator = Coordinator()
                logger.info("Coordinator service started")
                
                # In a real implementation, this would coordinate tasks
                while not self.shutdown_event.is_set():
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"Coordinator service error: {e}")
                
        coordinator_thread = threading.Thread(target=run_coordinator, daemon=True)
        coordinator_thread.start()
        self.threads.append(coordinator_thread)
        logger.info("Coordinator service thread started")
        
    def start_all_services(self):
        """Start all application services"""
        logger.info("Starting all application services...")
        
        # Start services
        self.start_api_server()
        self.start_message_queue_processor()
        self.start_coordinator()
        
        logger.info("All services started")
        
    def shutdown(self):
        """Gracefully shutdown all services"""
        logger.info("Shutting down application services...")
        
        # Signal shutdown to all services
        self.shutdown_event.set()
        
        # Wait for threads to finish (with timeout)
        for thread in self.threads:
            thread.join(timeout=5.0)
            
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

def main():
    """Main entry point for the application"""
    logger.info("Starting Agentic System...")
    
    # Create application manager
    app_manager = ApplicationManager()
    
    # Set up signal handlers
    app_manager.setup_signal_handlers()
    
    # Start all services
    app_manager.start_all_services()
    
    # Keep main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
        app_manager.shutdown()

if __name__ == "__main__":
    main()