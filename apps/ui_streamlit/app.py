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
    ["Overview", "Chat", "Agents", "Metrics", "Policy"]
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
    
elif page == "Chat":
    st.header("Chat")

    # Model selection
    st.sidebar.title("Model")
    model = st.sidebar.selectbox(
        "Choose a model:",
        ["Ollama", "OpenAI", "Gemini", "Groq", "Claude"]
    )

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # React to user input
    if prompt := st.chat_input("What is up?"):
        # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(prompt)
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Call the API
        try:
            response = requests.post(
                f"{API_BASE_URL}/chat",
                json={"message": prompt, "model": model},
                timeout=30
            )
            if response.status_code == 200:
                full_response = response.json().get("response")
            else:
                full_response = f"Error: {response.status_code}"
        except requests.exceptions.RequestException as e:
            full_response = f"Error: {e}"

        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            st.markdown(full_response)
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": full_response})
    
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