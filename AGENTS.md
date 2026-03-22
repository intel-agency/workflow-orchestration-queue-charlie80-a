---
file: AGENTS.md
description: Project instructions for coding agents working on OS-APOW
scope: repository
---

# AGENTS.md

## Project Overview

**OS-APOW** (Open Source - Agentic Production Orchestration Workflow) is a headless agentic orchestration platform that transforms AI coding into an autonomous background production service. It eliminates the human-in-the-loop dependency by shifting the AI from a passive assistant to an autonomous worker.

The system integrates with GitHub Issues and uses labels as a distributed state machine. When an issue is labeled with `agent:queued`, OS-APOW detects it, dispatches a specialized AI agent, and autonomously generates code, runs tests, and submits Pull Requests.

### Architecture: 4-Pillar Model

```
┌─────────────────────────────────────────────────────────────────┐
│                        OS-APOW System                           │
├─────────────────────────────────────────────────────────────────┤
│  ┌───────────┐    ┌───────────┐    ┌───────────┐    ┌────────┐ │
│  │    Ear    │───▶│   State   │───▶│   Brain   │───▶│ Hands  │ │
│  │ (Notifier)│    │  (Queue)  │    │ (Sentinel)│    │(Worker)│ │
│  └───────────┘    └───────────┘    └───────────┘    └────────┘ │
│       │                │                │               │      │
│       ▼                ▼                ▼               ▼      │
│   Webhook         GitHub           Polling         DevContainer│
│   Receiver        Issues           Daemon          Execution    │
└─────────────────────────────────────────────────────────────────┘
```

| Pillar | Component | Location | Description |
|--------|-----------|----------|-------------|
| **Ear** | Notifier | `src/os_apow/notifier/service.py` | FastAPI webhook receiver for GitHub events |
| **State** | GitHub Queue | `src/os_apow/queue/github_queue.py` | GitHub Issues + Labels as distributed state |
| **Brain** | Sentinel | `src/os_apow/orchestrator/sentinel.py` | Persistent polling, task claiming, worker dispatch |
| **Hands** | Worker | `scripts/devcontainer-opencode.sh` | DevContainer-based AI execution |

## Setup Commands

```bash
# Install dependencies (including dev tools)
uv sync --all-extras

# Copy environment template and configure
cp .env.example .env
# Edit .env with your GITHUB_TOKEN, WEBHOOK_SECRET, etc.
```

### Running Services

```bash
# Notifier (webhook receiver) - The "Ear"
uv run os-apow-notifier

# Sentinel (orchestrator) - The "Brain"
uv run os-apow-sentinel

# Or via module
python -m os_apow.main notifier
python -m os_apow.main sentinel
```

### Docker

```bash
# Run notifier only
docker compose --profile notifier up

# Run sentinel only (requires notifier)
docker compose --profile sentinel up

# Run all services
docker compose --profile all up
```

## Testing Commands

```bash
# Run all tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=os_apow --cov-report=term-missing

# Run specific test file
uv run pytest tests/test_work_item.py

# Run tests matching a pattern
uv run pytest -k "test_work_item"
```

## Code Quality Commands

```bash
# Lint check
uv run ruff check src/ tests/

# Format check (without modifying)
uv run ruff format --check src/ tests/

# Auto-format code
uv run ruff format src/ tests/

# Type check
uv run mypy src/
```

## Project Structure

```
workflow-orchestration-queue-charlie80-a/
├── src/os_apow/                    # Main application package
│   ├── __init__.py                 # Package init with version
│   ├── config.py                   # Configuration management (Pydantic Settings)
│   ├── main.py                     # CLI entry points (run_notifier, run_sentinel)
│   ├── models/                     # Data models
│   │   ├── __init__.py
│   │   └── work_item.py            # WorkItem, TaskType, WorkItemStatus enums
│   ├── queue/                      # Queue implementations
│   │   ├── __init__.py
│   │   └── github_queue.py         # ITaskQueue ABC + GitHubQueue implementation
│   ├── notifier/                   # Webhook receiver ("Ear" pillar)
│   │   ├── __init__.py
│   │   └── service.py              # FastAPI app with /webhooks/github endpoint
│   └── orchestrator/               # Sentinel orchestrator ("Brain" pillar)
│       ├── __init__.py
│       └── sentinel.py             # Polling daemon, task claiming, dispatch
├── tests/                          # Test suite
│   ├── __init__.py
│   ├── conftest.py                 # Pytest fixtures (sample_work_item, test_config)
│   └── test_work_item.py           # Model tests, scrub_secrets tests
├── scripts/                        # Helper scripts
│   ├── devcontainer-opencode.sh    # Shell bridge for worker execution
│   ├── gh-auth.ps1                 # GitHub authentication helper
│   ├── validate.ps1                # Validation script
│   └── test-github-permissions.ps1 # GitHub permissions verification
├── plan_docs/                      # Architecture and planning documents
│   └── src/                        # Reference implementations
├── .github/workflows/              # CI/CD workflows
├── pyproject.toml                  # Python project configuration
├── Dockerfile                      # Application container
├── docker-compose.yml              # Local development setup
├── .env.example                    # Environment template
├── .python-version                 # Python version pin (3.12)
├── README.md                       # Project documentation
└── .ai-repository-summary.md       # AI agent quick reference
```

## Technology Stack

| Category | Technology | Version |
|----------|------------|---------|
| Language | Python | 3.12+ |
| Package Manager | uv | 0.10.9+ |
| Web Framework | FastAPI | 0.115+ |
| Validation | Pydantic | 2.10+ |
| HTTP Client | httpx | 0.28+ (async) |
| ASGI Server | Uvicorn | 0.34+ |
| Testing | pytest | 8.3+ |
| Linting | ruff | 0.9+ |
| Type Checking | mypy | 1.14+ |
| Containerization | Docker | - |

## Code Style

- **Line Length:** 100 characters (configured in pyproject.toml)
- **Formatting:** ruff (includes isort for import sorting)
- **Type Hints:** Required for all functions (mypy strict mode enabled)
- **Docstrings:** Google style for all public APIs
- **Async:** Use `async/await` for all I/O operations (httpx, FastAPI)

### Naming Conventions

- **Modules:** `snake_case.py`
- **Classes:** `PascalCase`
- **Functions/Methods:** `snake_case`
- **Constants:** `UPPER_SNAKE_CASE`
- **Private members:** Prefix with `_`

### Import Order (via ruff isort)

1. Standard library
2. Third-party packages
3. Local imports (`os_apow.*`)

## Testing Conventions

- **Location:** `tests/` directory at project root
- **Naming:** `test_*.py` files, `Test*` classes, `test_*` functions
- **Fixtures:** Define shared fixtures in `conftest.py`
- **Async Tests:** Use `pytest-asyncio` (auto mode enabled)
- **Coverage:** Run with `--cov=os_apow` to track coverage

### Test Structure

```python
class TestFeatureName:
    """Tests for FeatureName."""
    
    def test_specific_behavior(self, sample_work_item: WorkItem) -> None:
        """Test that specific behavior works as expected."""
        # Arrange
        expected = "value"
        
        # Act
        result = sample_work_item.some_method()
        
        # Assert
        assert result == expected
```

## Configuration

### Required Environment Variables

| Variable | Description | Required For |
|----------|-------------|--------------|
| `GITHUB_TOKEN` | GitHub PAT with repo, read:org scopes | All services |
| `WEBHOOK_SECRET` | GitHub webhook secret | Notifier |
| `GITHUB_ORG` | Target GitHub organization | Sentinel |
| `GITHUB_REPO` | Target GitHub repository | Sentinel |

### Optional Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SENTINEL_BOT_LOGIN` | - | Bot account for assign-then-verify locking |
| `POLL_INTERVAL` | 60 | Sentinel polling interval (seconds) |
| `MAX_BACKOFF` | 960 | Max backoff on rate limits (seconds) |
| `HEARTBEAT_INTERVAL` | 300 | Heartbeat interval (seconds) |
| `SUBPROCESS_TIMEOUT` | 5700 | Worker subprocess timeout (seconds) |
| `NOTIFIER_HOST` | 0.0.0.0 | Notifier bind host |
| `NOTIFIER_PORT` | 8000 | Notifier bind port |

## Work Item Status Labels

The system uses GitHub labels as a distributed state machine:

| Status | Label | Description |
|--------|-------|-------------|
| Queued | `agent:queued` | Ready for processing |
| In Progress | `agent:in-progress` | Currently being processed |
| Success | `agent:success` | Completed successfully |
| Error | `agent:error` | Execution error (retryable) |
| Infra Failure | `agent:infra-failure` | Infrastructure error |
| Stalled Budget | `agent:stalled-budget` | Budget/token limit reached |

## PR and Commit Guidelines

### Commit Message Format

```
<type>: <description>

[optional body]
```

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`

### PR Title Format

Same as commit messages: `<type>: <description>`

### Before Committing

1. Run lint check: `uv run ruff check src/ tests/`
2. Run format check: `uv run ruff format --check src/ tests/`
3. Run type check: `uv run mypy src/`
4. Run tests: `uv run pytest`
5. Ensure all checks pass

### Branch Naming

- Feature: `feature/description`
- Fix: `fix/description`
- Refactor: `refactor/description`

## Common Pitfalls

### Environment Setup

- **Missing .env file:** Copy `.env.example` to `.env` and fill in values
- **Missing GITHUB_TOKEN:** Required for all services; set in `.env`
- **uv not installed:** Install from https://astral.sh/uv/

### Running Tests

- **pytest not found:** Run `uv sync --all-extras` to install dev dependencies
- **Import errors:** Ensure you're running from the project root

### Docker

- **Port 8000 in use:** Change `NOTIFIER_PORT` or stop conflicting service
- **Docker socket permission:** Ensure user is in docker group or use sudo

### Code Style

- **Format check fails:** Run `uv run ruff format src/ tests/` to auto-fix
- **Lint check fails:** Run `uv run ruff check src/ tests/ --fix` for auto-fixable issues

### Type Checking

- **mypy errors:** Ensure all functions have type hints; strict mode is enabled

## API Endpoints

### Notifier Service

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Service info |
| `GET` | `/health` | Health check endpoint |
| `POST` | `/webhooks/github` | GitHub webhook receiver |
| `GET` | `/docs` | OpenAPI/Swagger documentation |

## Related Documentation

- **README.md** - Full project documentation and quick start
- **.ai-repository-summary.md** - AI agent quick reference
- **plan_docs/** - Architecture guides and development plans
