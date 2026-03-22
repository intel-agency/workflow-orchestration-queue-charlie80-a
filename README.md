# OS-APOW: Workflow Orchestration Queue

> **Headless Agentic Orchestration Platform**

[![Python CI](https://github.com/intel-agency/workflow-orchestration-queue-charlie80-a/actions/workflows/python-ci.yml/badge.svg)](https://github.com/intel-agency/workflow-orchestration-queue-charlie80-a/actions/workflows/python-ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

**OS-APOW** (Open Source - Agentic Production Orchestration Workflow) is a groundbreaking headless agentic orchestration platform that transforms the current paradigm of "interactive" AI coding into an autonomous background production service. It eliminates the human-in-the-loop dependency by shifting the AI from a passive assistant to a tireless junior developer on your team.

The system natively integrates into existing Agile workflows by translating standard project management artifacts (GitHub Issues, Epics, Kanban board movements) into automated Execution Orders. A product manager simply writes a standard issue description, applies a specific label, and the system detects this intent and dispatches a specialized AI agent that autonomously clones the target repository, generates and modifies code, runs local test suites, and submits a fully formatted Pull Request.

## Architecture (4-Pillar Model)

```
┌─────────────────────────────────────────────────────────────────┐
│                        OS-APOW System                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌───────────┐    ┌───────────┐    ┌───────────┐    ┌────────┐ │
│  │    Ear    │───▶│   State   │───▶│   Brain   │───▶│ Hands  │ │
│  │ (Notifier)│    │  (Queue)  │    │ (Sentinel)│    │(Worker)│ │
│  └───────────┘    └───────────┘    └───────────┘    └────────┘ │
│       │                │                │               │      │
│       ▼                ▼                ▼               ▼      │
│   Webhook         GitHub           Polling         DevContainer│
│   Receiver        Issues           Daemon          Execution    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Components

| Pillar | Component | Description |
|--------|-----------|-------------|
| **Ear** | Notifier Service | FastAPI webhook receiver for GitHub events |
| **State** | GitHub Queue | GitHub Issues + Labels as distributed state management |
| **Brain** | Sentinel Orchestrator | Persistent polling, task claiming, worker lifecycle |
| **Hands** | Opencode Worker | Isolated DevContainer-based AI execution environment |

## Technology Stack

| Category | Technology |
|----------|------------|
| **Language** | Python 3.12+ |
| **Package Manager** | uv (Rust-based, fast) |
| **Web Framework** | FastAPI |
| **Validation** | Pydantic |
| **HTTP Client** | httpx (async) |
| **ASGI Server** | Uvicorn |
| **Containerization** | Docker, Docker Compose, DevContainers |
| **Agent Runtime** | opencode CLI with ZhipuAI GLM-5 |

## Quick Start

### Prerequisites

- Python 3.12+
- uv package manager
- Docker (for containerized deployment)
- GitHub Personal Access Token with appropriate scopes

### Installation

```bash
# Clone the repository
git clone https://github.com/intel-agency/workflow-orchestration-queue-charlie80-a.git
cd workflow-orchestration-queue-charlie80-a

# Install dependencies with uv
uv sync --dev

# Copy environment template
cp .env.example .env
# Edit .env with your configuration
```

### Running the Services

#### Notifier Service (Webhook Receiver)

```bash
# Run directly
uv run os-apow-notifier

# Or with custom host/port
NOTIFIER_HOST=0.0.0.0 NOTIFIER_PORT=8000 uv run os-apow-notifier
```

#### Sentinel Service (Orchestrator)

```bash
# Run directly
uv run os-apow-sentinel

# With configuration
GITHUB_ORG=your-org GITHUB_REPO=your-repo uv run os-apow-sentinel
```

#### Using Docker Compose

```bash
# Run notifier only
docker compose --profile notifier up

# Run sentinel only (requires notifier)
docker compose --profile sentinel up

# Run all services
docker compose --profile all up
```

## Project Structure

```
workflow-orchestration-queue-charlie80-a/
├── src/os_apow/                 # Main application package
│   ├── __init__.py              # Package initialization
│   ├── config.py                # Configuration management
│   ├── main.py                  # CLI entry points
│   ├── models/                  # Data models
│   │   └── work_item.py         # WorkItem, TaskType, WorkItemStatus
│   ├── queue/                   # Queue implementations
│   │   └── github_queue.py      # GitHub-backed queue
│   ├── notifier/                # Webhook receiver (Ear)
│   │   └── service.py           # FastAPI application
│   └── orchestrator/            # Sentinel orchestrator (Brain)
│       └── sentinel.py          # Polling and dispatch logic
├── tests/                       # Test suite
├── scripts/                     # Helper scripts
│   └── devcontainer-opencode.sh # Shell bridge for workers
├── plan_docs/                   # Planning documents
├── pyproject.toml               # Python project configuration
├── Dockerfile                   # Application container
├── docker-compose.yml           # Local development setup
└── .env.example                 # Environment template
```

## Configuration

### Required Environment Variables

| Variable | Description | Required For |
|----------|-------------|--------------|
| `GITHUB_TOKEN` | GitHub Personal Access Token | All services |
| `WEBHOOK_SECRET` | GitHub webhook secret | Notifier |
| `GITHUB_ORG` | GitHub organization name | Sentinel |
| `GITHUB_REPO` | GitHub repository name | Sentinel |

### Optional Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SENTINEL_BOT_LOGIN` | - | Bot account login for locking |
| `POLL_INTERVAL` | 60 | Polling interval in seconds |
| `MAX_BACKOFF` | 960 | Max backoff on rate limits |
| `HEARTBEAT_INTERVAL` | 300 | Heartbeat interval in seconds |
| `NOTIFIER_PORT` | 8000 | Notifier service port |

## API Endpoints

### Notifier Service

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Service info |
| `GET` | `/health` | Health check |
| `POST` | `/webhooks/github` | GitHub webhook receiver |
| `GET` | `/docs` | OpenAPI documentation |

## Development

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=os_apow --cov-report=term-missing
```

### Code Quality

```bash
# Lint check
uv run ruff check src/ tests/

# Format check
uv run ruff format --check src/ tests/

# Type check
uv run mypy src/
```

## Documentation

- [Repository Summary](./.ai-repository-summary.md) - AI agent reference
- [Architecture Guide](./plan_docs/OS-APOW%20Architecture%20Guide%20v3.2.md)
- [Development Plan](./plan_docs/OS-APOW%20Development%20Plan%20v4.2.md)
- [Implementation Specification](./plan_docs/OS-APOW%20Implementation%20Specification%20v1.2.md)

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
