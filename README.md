# Agentic System

An intelligent task orchestration system that integrates with Taskwarrior, Timewarrior, Obsidian, and GitHub to automate complex workflows using browser, vision, research, and memory agents.

## Features

- Orchestrate browser, vision, research, and memory agents against Tasks
- Measure I/O, latency, success, and cost with adaptive tool choices
- Learn from outcomes with a tiny, local model to improve routing and parameters
- Integrate with Taskwarrior/Timewarrior, Obsidian, FAISS, and GitHub

## Architecture

The system follows a modular architecture with the following components:

- **UI + Entry**: Streamlit UI, Taskwarrior TUI, CLI
- **Orchestration**: Coordinator, Policy Engine, Learning Loop, Event Bus, Message Queue
- **Agents**: Browser Agent, Vision Agent, Research Agent, Memory Agent
- **Task System**: Taskwarrior Adapter, Timewarrior Adapter, GitHub Sync, Proxy REST API
- **Tools**: Playwright Controller, OpenCV Ops, Searcher, Obsidian Connector, FAISS Store
- **Data + Telemetry**: SQLite database, Metrics Collector, Throughput Monitor, Feature Builder

## Getting Started

1. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   # Using pip
   pip install -r requirements.txt
   
   # Or using uv (recommended for better performance)
   uv pip install -r requirements.txt
   ```

3. Initialize the database:
   ```bash
   python scripts/migrate_db.py
   ```

4. Start the services:
   ```bash
   # Option 1: Start all services with the main entry point (recommended):
   python main.py
   
   # Option 2: Start services separately in different terminals:
   uvicorn apps.proxy_api.main:app --port 9000
   streamlit run apps/ui_streamlit/app.py
   python core/coordinator.py
   ```

## Configuration

The system can be configured using YAML files in the `configs/` directory:

- `policy.yaml`: Routing policies and agent configurations
- `routes.yaml`: API route definitions
- `ui.toml`: Streamlit UI configuration

## Directory Structure

```
agentic/
  apps/
    ui_streamlit/
    proxy_api/
  core/
    coordinator.py
    policy.py
    learning.py
    mq.py
    events.py
  agents/
    browser_agent/
    vision_agent/
    research_agent/
    memory_agent/
  tools/
    playwright_ctrl/
    opencv_ops/
    searcher/
    obsidian_conn/
    faiss_store/
  data/
    core.db
    vectors/
  configs/
    policy.yaml
    routes.yaml
    ui.toml
  scripts/
    probe_env.sh
    migrate_db.py
  tests/
```

## Development

This project follows PEP 8 style guidelines and uses type hints for all function parameters and return types. Before committing code, run:

```bash
pre-commit run --all-files
```

## License

MIT