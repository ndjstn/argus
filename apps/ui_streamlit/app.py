import streamlit as st
import requests
import pandas as pd
import time
import logging
import sys
import os
import json

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# Local imports
from core.exceptions import APIError

# Configuration
API_BASE_URL = "http://localhost:9000/api"

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="Agentic System",
    page_icon="🤖",
    layout="wide"
)

st.title("Agentic System Dashboard")

st.markdown("""
Welcome to the Agentic System Dashboard. This interface allows you to:
- View and manage tasks
- Monitor agent performance
- Analyze system metrics
- Configure policies
""")

# Navigation
st.sidebar.title("Navigation")
page = st.sidebar.selectbox(
    "Choose a page:",
    ["Overview", "Tasks", "Agents", "Metrics", "Policy"]
)

# Helper functions
@st.cache_data(ttl=5)
def get_tasks():
    try:
        response = requests.get(f"{API_BASE_URL}/tasks", timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"API request failed with status code {response.status_code}")
            st.warning(f"Failed to fetch tasks: {response.status_code}")
            return []
    except requests.exceptions.Timeout:
        logger.error("API request timed out")
        st.error("Request timed out. Please try again.")
        return []
    except requests.exceptions.ConnectionError:
        logger.error("API connection error")
        st.error("Could not connect to the API. Please check if the service is running.")
        return []
    except requests.exceptions.RequestException as e:
        logger.error(f"API request error: {e}")
        st.error(f"Error fetching tasks: {str(e)}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error in get_tasks: {e}")
        st.error(f"Unexpected error: {str(e)}")
        return []

@st.cache_data(ttl=5)
def get_runs():
    try:
        response = requests.get(f"{API_BASE_URL}/runs", timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"API request failed with status code {response.status_code}")
            st.warning(f"Failed to fetch runs: {response.status_code}")
            return []
    except requests.exceptions.Timeout:
        logger.error("API request timed out")
        st.error("Request timed out. Please try again.")
        return []
    except requests.exceptions.ConnectionError:
        logger.error("API connection error")
        st.error("Could not connect to the API. Please check if the service is running.")
        return []
    except requests.exceptions.RequestException as e:
        logger.error(f"API request error: {e}")
        st.error(f"Error fetching runs: {str(e)}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error in get_runs: {e}")
        st.error(f"Unexpected error: {str(e)}")
        return []

@st.cache_data(ttl=5)
def get_metrics():
    try:
        response = requests.get(f"{API_BASE_URL}/metrics/daily", timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"API request failed with status code {response.status_code}")
            st.warning(f"Failed to fetch metrics: {response.status_code}")
            return []
    except requests.exceptions.Timeout:
        logger.error("API request timed out")
        st.error("Request timed out. Please try again.")
        return []
    except requests.exceptions.ConnectionError:
        logger.error("API connection error")
        st.error("Could not connect to the API. Please check if the service is running.")
        return []
    except requests.exceptions.RequestException as e:
        logger.error(f"API request error: {e}")
        st.error(f"Error fetching metrics: {str(e)}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error in get_metrics: {e}")
        st.error(f"Unexpected error: {str(e)}")
        return []

@st.cache_data(ttl=5)
def get_policy():
    try:
        response = requests.get(f"{API_BASE_URL}/policy", timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"API request failed with status code {response.status_code}")
            st.warning(f"Failed to fetch policy: {response.status_code}")
            return {}
    except requests.exceptions.Timeout:
        logger.error("API request timed out")
        st.error("Request timed out. Please try again.")
        return {}
    except requests.exceptions.ConnectionError:
        logger.error("API connection error")
        st.error("Could not connect to the API. Please check if the service is running.")
        return {}
    except requests.exceptions.RequestException as e:
        logger.error(f"API request error: {e}")
        st.error(f"Error fetching policy: {str(e)}")
        return {}
    except Exception as e:
        logger.error(f"Unexpected error in get_policy: {e}")
        st.error(f"Unexpected error: {str(e)}")
        return {}

def create_task(description, project=None, tags=None, due=None, browser_task=False, url=None, actions=None):
    try:
        data = {"description": description}
        if project:
            data["project"] = project
        if tags:
            data["tags"] = tags
        if due:
            data["due"] = due
        if browser_task:
            data["browser_task"] = True
            data["url"] = url
            data["actions"] = actions
            
        response = requests.post(f"{API_BASE_URL}/tasks", json=data, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"API request failed with status code {response.status_code}")
            st.error(f"Failed to create task: {response.status_code}")
            return {}
    except requests.exceptions.Timeout:
        logger.error("API request timed out")
        st.error("Request timed out. Please try again.")
        return {}
    except requests.exceptions.ConnectionError:
        logger.error("API connection error")
        st.error("Could not connect to the API. Please check if the service is running.")
        return {}
    except requests.exceptions.RequestException as e:
        logger.error(f"API request error: {e}")
        st.error(f"Error creating task: {str(e)}")
        return {}
    except Exception as e:
        logger.error(f"Unexpected error in create_task: {e}")
        st.error(f"Unexpected error: {str(e)}")
        return {}

if page == "Overview":
    st.header("System Overview")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    tasks = get_tasks()
    runs = get_runs()
    metrics = get_metrics()
    
    with col1:
        st.metric("Total Tasks", len(tasks))
    with col2:
        completed_tasks = len([t for t in tasks if t.get("status") == "completed"])
        st.metric("Completed Tasks", completed_tasks)
    with col3:
        st.metric("Total Runs", len(runs))
    with col4:
        if metrics:
            success_rate = metrics[-1].get("success_rate", 0) * 100
            st.metric("Success Rate", f"{success_rate:.1f}%")
    
    # Recent tasks
    st.subheader("Recent Tasks")
    if tasks:
        df = pd.DataFrame(tasks)
        st.dataframe(df[["description", "project", "status", "urgency"]].tail(10))
    else:
        st.info("No tasks found.")
    
elif page == "Tasks":
    st.header("Task Management")
    
    # Create new task
    with st.expander("Create New Task"):
        with st.form("create_task_form"):
            description = st.text_input("Description")
            project = st.text_input("Project")
            tags = st.text_input("Tags (comma-separated)")
            due = st.text_input("Due date (YYYY-MM-DD)")

            is_browser_task = st.checkbox("Browser Task")
            url = st.text_input("URL (for browser tasks)")
            actions = st.text_area("Actions (for browser tasks, JSON format)")

            submitted = st.form_submit_button("Create Task")
            
            if submitted:
                tag_list = [tag.strip() for tag in tags.split(",")] if tags else None
                
                task_data = {
                    "description": description,
                    "project": project,
                    "tags": tag_list,
                    "due": due,
                    "browser_task": is_browser_task,
                    "url": url,
                    "actions": json.loads(actions) if actions else []
                }

                result = create_task(**task_data)
                if result:
                    st.success("Task created successfully!")
                    st.cache_data.clear()
                else:
                    st.error("Failed to create task.")
    
    # Task list
    st.subheader("Task List")

    if st.button("Refresh"):
        st.cache_data.clear()

    if st.checkbox("Auto-refresh every 5 seconds"):
        time.sleep(5)
        st.experimental_rerun()

    tasks = get_tasks()
    if tasks:
        df = pd.DataFrame(tasks)
        st.dataframe(df[["description", "project", "tags", "status", "urgency", "due_ts"]])

        for task in tasks:
            with st.expander(f"Task {task['id']}: {task['description']}"):
                st.write(task)
    else:
        st.info("No tasks found.")
    
elif page == "Agents":
    st.header("Agent Monitoring")
    st.info("Agent monitoring dashboard will be implemented here.")
    
elif page == "Metrics":
    st.header("Performance Metrics")
    
    metrics = get_metrics()
    if metrics:
        df = pd.DataFrame(metrics)
        st.line_chart(df.set_index("day")[["success_rate", "avg_latency_ms"]])
    else:
        st.info("No metrics data available.")
    
elif page == "Policy":
    st.header("Policy Configuration")
    
    policy = get_policy()
    if policy:
        st.json(policy)
    else:
        st.info("No policy configuration available.")