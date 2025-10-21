#!/usr/bin/env python3
"""
Unified launcher for the Agentic System.
Starts both the FastAPI server and Streamlit UI with a single command.
"""

import subprocess
import sys
import time
import signal
import os
import logging
from typing import List

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ApplicationLauncher:
    """Manages launching and shutting down all application services"""
    
    def __init__(self):
        self.processes: List[subprocess.Popen] = []
        
    def start_api_server(self):
        """Start the FastAPI server"""
        logger.info("Starting API server...")
        try:
            # Use the existing main.py which already handles the API server
            api_process = subprocess.Popen([
                sys.executable, "-m", "uvicorn", 
                "apps.proxy_api.main:app", 
                "--host", "0.0.0.0", 
                "--port", "9000"
            ])
            self.processes.append(api_process)
            logger.info("API server started with PID %d", api_process.pid)
            return api_process
        except Exception as e:
            logger.error("Failed to start API server: %s", e)
            raise
            
    def start_streamlit_ui(self):
        """Start the Streamlit UI"""
        logger.info("Starting Streamlit UI...")
        try:
            # Wait a moment for API to start
            time.sleep(2)
            
            ui_process = subprocess.Popen([
                sys.executable, "-m", "streamlit", 
                "run", "apps/ui_streamlit/app.py",
                "--server.port", "8501",
                "--server.address", "0.0.0.0"
            ])
            self.processes.append(ui_process)
            logger.info("Streamlit UI started with PID %d", ui_process.pid)
            return ui_process
        except Exception as e:
            logger.error("Failed to start Streamlit UI: %s", e)
            raise
            
    def setup_signal_handlers(self):
        """Set up signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            logger.info("Received signal %s, shutting down...", signum)
            self.shutdown()
            
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
    def shutdown(self):
        """Gracefully shutdown all processes"""
        logger.info("Shutting down application services...")
        
        for process in self.processes:
            if process.poll() is None:  # Process is still running
                logger.info("Terminating process %d", process.pid)
                process.terminate()
                
        # Wait for processes to terminate
        for process in self.processes:
            try:
                process.wait(timeout=5)
                logger.info("Process %d terminated", process.pid)
            except subprocess.TimeoutExpired:
                logger.warning("Process %d did not terminate in time, killing...", process.pid)
                process.kill()
                
        logger.info("All services shut down")
        sys.exit(0)
        
    def run(self):
        """Run the application"""
        try:
            self.setup_signal_handlers()
            
            # Start services
            api_process = self.start_api_server()
            ui_process = self.start_streamlit_ui()
            
            logger.info("Application services started successfully!")
            logger.info("API Server: http://localhost:9000")
            logger.info("Streamlit UI: http://localhost:8501")
            logger.info("Press Ctrl+C to stop all services")
            
            # Wait for processes
            while True:
                for process in self.processes:
                    if process.poll() is not None:  # Process has terminated
                        logger.error("Process %d terminated unexpectedly", process.pid)
                        self.shutdown()
                        return
                        
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
            self.shutdown()
        except Exception as e:
            logger.error("Unexpected error: %s", e)
            self.shutdown()


if __name__ == "__main__":
    launcher = ApplicationLauncher()
    launcher.run()