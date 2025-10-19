#!/usr/bin/env python3

import argparse
import logging
import requests
import time
from typing import Dict, Any
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import os
import yaml

# Local imports
from core.exceptions import APIError

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API base URL
API_BASE_URL = "http://localhost:9000/api"

def load_cli_config():
    """Load CLI configuration from config file"""
    config_path = os.path.join(os.path.dirname(__file__), "configs", "policy.yaml")
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config.get('cli', {})
    except Exception as e:
        logger.warning(f"Failed to load CLI config, using defaults: {e}")
        return {}

# Load configuration
cli_config = load_cli_config()

# API base URL
API_BASE_URL = cli_config.get('api_base_url') or "http://localhost:9000/api"

# Metrics for CLI session
total_api_calls = 0
total_api_time_ms = 0

# Create a session with connection pooling and retry strategy
session = requests.Session()

# Configure retry strategy
retry_strategy = Retry(
    total=cli_config.get('max_retries', 3),
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
)

# Mount adapter with retry strategy and connection pooling
adapter = HTTPAdapter(
    max_retries=retry_strategy,
    pool_connections=cli_config.get('pool_connections', 10),
    pool_maxsize=cli_config.get('pool_maxsize', 20)
)

session.mount("http://", adapter)
session.mount("https://", adapter)

def plan_task(task_uuid: str) -> Dict[str, Any]:
    """Plan execution for a task"""
    logger.info(f"Planning execution for task: {task_uuid}")
    global total_api_calls, total_api_time_ms
    
    start_time = time.time()
    total_api_calls += 1
    
    try:
        response = session.post(f"{API_BASE_URL}/plan", data={"task_uuid": task_uuid}, timeout=30)
        api_time = (time.time() - start_time) * 1000
        total_api_time_ms += api_time
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"API request failed with status code {response.status_code}")
            return {"error": f"API request failed with status code {response.status_code}"}
    except requests.exceptions.Timeout as e:
        api_time = (time.time() - start_time) * 1000
        total_api_time_ms += api_time
        logger.error(f"API request timed out: {e}")
        return {"error": f"Request timed out: {str(e)}"}
    except requests.exceptions.ConnectionError as e:
        api_time = (time.time() - start_time) * 1000
        total_api_time_ms += api_time
        logger.error(f"API connection error: {e}")
        return {"error": f"Connection error: {str(e)}"}
    except requests.exceptions.RequestException as e:
        api_time = (time.time() - start_time) * 1000
        total_api_time_ms += api_time
        logger.error(f"API request error: {e}")
        return {"error": f"Request error: {str(e)}"}
    except Exception as e:
        api_time = (time.time() - start_time) * 1000
        total_api_time_ms += api_time
        logger.error(f"Unexpected error planning task: {e}")
        return {"error": f"Unexpected error: {str(e)}"}

def run_task(task_uuid: str, agent: str = None, retries: int = 1) -> Dict[str, Any]:
    """Run a task with specified agent and retries"""
    logger.info(f"Running task: {task_uuid} with agent: {agent}, retries: {retries}")
    
    # In a real implementation, this would interact with the Coordinator
    # For now, we'll just return a placeholder response
    return {
        "task_uuid": task_uuid,
        "status": "completed",
        "result": "Task execution logic would be implemented here"
    }

def show_metrics(since: str = "7d") -> Dict[str, Any]:
    """Show system metrics"""
    logger.info(f"Showing metrics since: {since}")
    global total_api_calls, total_api_time_ms
    
    start_time = time.time()
    total_api_calls += 1
    
    try:
        response = session.get(f"{API_BASE_URL}/metrics/daily", timeout=30)
        api_time = (time.time() - start_time) * 1000
        total_api_time_ms += api_time
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"API request failed with status code {response.status_code}")
            return {"error": f"API request failed with status code {response.status_code}"}
    except requests.exceptions.Timeout as e:
        api_time = (time.time() - start_time) * 1000
        total_api_time_ms += api_time
        logger.error(f"API request timed out: {e}")
        return {"error": f"Request timed out: {str(e)}"}
    except requests.exceptions.ConnectionError as e:
        api_time = (time.time() - start_time) * 1000
        total_api_time_ms += api_time
        logger.error(f"API connection error: {e}")
        return {"error": f"Connection error: {str(e)}"}
    except requests.exceptions.RequestException as e:
        api_time = (time.time() - start_time) * 1000
        total_api_time_ms += api_time
        logger.error(f"API request error: {e}")
        return {"error": f"Request error: {str(e)}"}
    except Exception as e:
        api_time = (time.time() - start_time) * 1000
        total_api_time_ms += api_time
        logger.error(f"Unexpected error fetching metrics: {e}")
        return {"error": f"Unexpected error: {str(e)}"}

def set_policy(key: str, value: str) -> Dict[str, Any]:
    """Set a policy parameter"""
    logger.info(f"Setting policy {key} = {value}")
    
    try:
        # Convert value to appropriate type
        if value.lower() in ('true', 'false'):
            value = value.lower() == 'true'
        elif value.isdigit():
            value = int(value)
        elif value.replace('.', '', 1).isdigit():
            value = float(value)
            
        response = session.post(f"{API_BASE_URL}/policy", json={key: value}, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"API request failed with status code {response.status_code}")
            return {"error": f"API request failed with status code {response.status_code}"}
    except requests.exceptions.Timeout as e:
        logger.error(f"API request timed out: {e}")
        return {"error": f"Request timed out: {str(e)}"}
    except requests.exceptions.ConnectionError as e:
        logger.error(f"API connection error: {e}")
        return {"error": f"Connection error: {str(e)}"}
    except requests.exceptions.RequestException as e:
        logger.error(f"API request error: {e}")
        return {"error": f"Request error: {str(e)}"}
    except Exception as e:
        logger.error(f"Unexpected error setting policy: {e}")
        return {"error": f"Unexpected error: {str(e)}"}

def main():
    parser = argparse.ArgumentParser(description="Agentic System CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Plan command
    plan_parser = subparsers.add_parser("plan", help="Plan execution for a task")
    plan_parser.add_argument("task_uuid", help="Task UUID to plan")
    
    # Run command
    run_parser = subparsers.add_parser("run", help="Run a task")
    run_parser.add_argument("task_uuid", help="Task UUID to run")
    run_parser.add_argument("--agent", help="Agent to use for execution")
    run_parser.add_argument("--retries", type=int, default=1, help="Number of retries")
    
    # Metrics command
    metrics_parser = subparsers.add_parser("metrics", help="Show system metrics")
    metrics_parser.add_argument("--since", default="7d", help="Time period for metrics")
    
    # Policy command
    policy_parser = subparsers.add_parser("policy", help="Manage policy configuration")
    policy_parser.add_argument("key", help="Policy key to set")
    policy_parser.add_argument("value", help="Policy value to set")
    
    args = parser.parse_args()
    
    if args.command == "plan":
        result = plan_task(args.task_uuid)
        print(result)
    elif args.command == "run":
        result = run_task(args.task_uuid, args.agent, args.retries)
        print(result)
    elif args.command == "metrics":
        result = show_metrics(args.since)
        print(result)
    elif args.command == "policy":
        result = set_policy(args.key, args.value)
        print(result)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()