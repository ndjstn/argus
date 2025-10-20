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
logging.basicConfig(level=logging.DEBUG)
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
    ["Chat", "Overview", "Agents", "Metrics", "Policy"]
)

@st.cache_data(ttl=60)
def get_ollama_models():
    logger.info("Attempting to fetch Ollama models from the API.")
    try:
        response = requests.get("http://localhost:11434/api/tags")
        response.raise_for_status()  # Raise an exception for bad status codes
        logger.info("Successfully fetched Ollama models from the API.")
        return [model["name"] for model in response.json().get("models", [])]
    except requests.exceptions.RequestException as e:
        logger.error(f"Error getting Ollama models: {e}")
        st.sidebar.warning("Could not connect to Ollama API. Using a placeholder list of models.")
        return ["deepseek-v3.1:671b-cloud", "kimi-k2:1t-cloud", "glm-4.6:cloud", "granite3.2-vision:latest", "mxbai-embed-large:latest", "gpt-oss:20b", "gemma3:4b", "mistral-small3.2:latest", "nomic-embed-text:latest", "qwen3-coder:480b-cloud"]
    except (KeyError, TypeError) as e:
        logger.error(f"Error parsing Ollama models response: {e}")
        st.sidebar.warning("Error parsing Ollama models response.")
        return []

# Helper functions
@st.cache_data(ttl=5)
def get_tasks():
    logger.info("Attempting to fetch tasks from the API.")
    try:
        response = requests.get(f"{API_BASE_URL}/tasks", timeout=10)
        response.raise_for_status()  # Raise an exception for bad status codes
        logger.info("Successfully fetched tasks from the API.")
        return response.json()
    except requests.exceptions.Timeout:
        logger.error("API request timed out while fetching tasks.")
        st.error("Request timed out. Please try again.")
        return []
    except requests.exceptions.ConnectionError:
        logger.error("API connection error while fetching tasks.")
        st.error("Could not connect to the API. Please check if the service is running.")
        return []
    except requests.exceptions.RequestException as e:
        logger.error(f"API request error while fetching tasks: {e}")
        st.error(f"Error fetching tasks: {e}")
        return []
    except Exception as e:
        logger.error(f"An unexpected error occurred in get_tasks: {e}")
        st.error(f"An unexpected error occurred: {e}")
        return []

@st.cache_data(ttl=5)
def get_runs():
    logger.info("Attempting to fetch runs from the API.")
    try:
        response = requests.get(f"{API_BASE_URL}/runs", timeout=10)
        response.raise_for_status()  # Raise an exception for bad status codes
        logger.info("Successfully fetched runs from the API.")
        return response.json()
    except requests.exceptions.Timeout:
        logger.error("API request timed out while fetching runs.")
        st.error("Request timed out. Please try again.")
        return []
    except requests.exceptions.ConnectionError:
        logger.error("API connection error while fetching runs.")
        st.error("Could not connect to the API. Please check if the service is running.")
        return []
    except requests.exceptions.RequestException as e:
        logger.error(f"API request error while fetching runs: {e}")
        st.error(f"Error fetching runs: {e}")
        return []
    except Exception as e:
        logger.error(f"An unexpected error occurred in get_runs: {e}")
        st.error(f"An unexpected error occurred: {e}")
        return []

@st.cache_data(ttl=5)
def get_metrics():
    logger.info("Attempting to fetch metrics from the API.")
    try:
        response = requests.get(f"{API_BASE_URL}/metrics/daily", timeout=10)
        response.raise_for_status()  # Raise an exception for bad status codes
        logger.info("Successfully fetched metrics from the API.")
        return response.json()
    except requests.exceptions.Timeout:
        logger.error("API request timed out while fetching metrics.")
        st.error("Request timed out. Please try again.")
        return []
    except requests.exceptions.ConnectionError:
        logger.error("API connection error while fetching metrics.")
        st.error("Could not connect to the API. Please check if the service is running.")
        return []
    except requests.exceptions.RequestException as e:
        logger.error(f"API request error while fetching metrics: {e}")
        st.error(f"Error fetching metrics: {e}")
        return []
    except Exception as e:
        logger.error(f"An unexpected error occurred in get_metrics: {e}")
        st.error(f"An unexpected error occurred: {e}")
        return []

@st.cache_data(ttl=5)
def get_policy():
    logger.info("Attempting to fetch policy from the API.")
    try:
        response = requests.get(f"{API_BASE_URL}/policy", timeout=10)
        response.raise_for_status()  # Raise an exception for bad status codes
        logger.info("Successfully fetched policy from the API.")
        return response.json()
    except requests.exceptions.Timeout:
        logger.error("API request timed out while fetching policy.")
        st.error("Request timed out. Please try again.")
        return {}
    except requests.exceptions.ConnectionError:
        logger.error("API connection error while fetching policy.")
        st.error("Could not connect to the API. Please check if the service is running.")
        return {}
    except requests.exceptions.RequestException as e:
        logger.error(f"API request error while fetching policy: {e}")
        st.error(f"Error fetching policy: {e}")
        return {}
    except Exception as e:
        logger.error(f"An unexpected error occurred in get_policy: {e}")
        st.error(f"An unexpected error occurred: {e}")
        return {}

def create_task(description, project=None, tags=None, due=None, browser_task=False, url=None, actions=None):
    logger.info(f"Attempting to create task: {description}")
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
        response.raise_for_status()  # Raise an exception for bad status codes
        logger.info(f"Successfully created task: {description}")
        return response.json()
    except requests.exceptions.Timeout:
        logger.error(f"API request timed out while creating task: {description}")
        st.error("Request timed out. Please try again.")
        return {}
    except requests.exceptions.ConnectionError:
        logger.error(f"API connection error while creating task: {description}")
        st.error("Could not connect to the API. Please check if the service is running.")
        return {}
    except requests.exceptions.RequestException as e:
        logger.error(f"API request error while creating task: {description}: {e}")
        st.error(f"Error creating task: {e}")
        return {}
    except Exception as e:
        logger.error(f"An unexpected error occurred in create_task: {e}")
        st.error(f"An unexpected error occurred: {e}")
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
    provider = st.sidebar.selectbox(
        "Choose a provider:",
        ["Ollama", "OpenAI", "Gemini", "Groq", "Claude"]
    )

    models = {
        "Ollama": get_ollama_models(),
        "OpenAI": ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"],
        "Gemini": ["gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.0-flash"],
        "Groq": ["llama-3.1-8b-instant", "llama-3.3-70b-versatile", "mixtral-8x7b-32768"],
        "Claude": ["claude-3.5-sonnet", "claude-3-opus", "claude-3-haiku"]
    }

    model = st.sidebar.selectbox(
        "Choose a model:",
        models[provider]
    )

    if st.sidebar.button("Clear Chat"):
        st.session_state.messages = []

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

        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            with st.spinner("Thinking..."):
                # Call the API
                try:
                    response = requests.post(
                        f"{API_BASE_URL}/chat",
                        json={"message": prompt, "provider": provider, "model": model},
                        stream=True
                    )
                    response.raise_for_status()
                    full_response = ""
                    for chunk in response.iter_content(chunk_size=1024):
                        if chunk:
                            decoded_chunk = chunk.decode('utf-8')
                            try:
                                json_chunk = json.loads(decoded_chunk)
                                full_response += json_chunk.get("response", "")
                                message_placeholder.markdown(full_response + "▌")
                            except json.JSONDecodeError:
                                # Handle non-json chunks if any
                                pass
                    message_placeholder.markdown(full_response)
                    st.session_state.messages.append({"role": "assistant", "content": full_response})

                except requests.exceptions.RequestException as e:
                    full_response = f"Error: {e}"
                    message_placeholder.markdown(full_response)
                    st.session_state.messages.append({"role": "assistant", "content": full_response})

            if st.button("Copy", key=f"copy_{len(st.session_state.messages)}"):
                st.code(full_response)
    
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
