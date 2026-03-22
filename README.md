# workflow-orchestration-queue-charlie80-a

GitHub Actions-based AI orchestration system. On GitHub events (issues, PR comments, reviews),
the `orchestrator-agent` workflow assembles a structured prompt, spins up a devcontainer,
and runs `opencode --agent Orchestrator` to delegate work to specialist sub-agents in `.opencode/agents/`.

## Overview

This repository implements a headless agentic orchestration system that transforms standard project management artifacts (GitHub Issues) into "Execution Orders" that are autonomously fulfilled by specialized AI agents.

## Key Features

- **Event-Driven Orchestration**: Automatically responds to GitHub events (issues, labels, PRs)
- **DevContainer-Based Execution**: Isolated, reproducible execution environments
- **Specialized Agent Delegation**: Routes tasks to appropriate specialist agents
- **Self-Bootstrapping**: The system can build and evolve itself using its own orchestration capabilities

## Repository Structure

```
.
├── .devcontainer/           # Consumer devcontainer configuration
├── .github/
│   ├── .devcontainer/       # Build-time devcontainer (Dockerfile)
│   ├── workflows/           # GitHub Actions workflows
│   └── .labels.json         # Repository label definitions
├── .opencode/
│   ├── agents/              # Agent definitions
│   └── commands/            # Reusable command prompts
├── scripts/                 # Helper scripts (PowerShell/Bash)
├── src/
│   ├── config/              # Configuration management (Pydantic settings)
│   └── models/              # Shared data models
├── test/                    # Test suite
├── plan_docs/               # Architecture and planning documents
├── local_ai_instruction_modules/  # Local AI instruction modules
├── .env.example             # Environment template (copy to .env)
├── requirements.txt         # Python dependencies
├── AGENTS.md                # Project instructions for coding agents
└── opencode.json            # OpenCode CLI configuration
```

## Tech Stack

- **opencode CLI** — Agent runtime (`opencode --model zai-coding-plan/glm-5 --agent Orchestrator`)
- **ZhipuAI GLM models** via `ZHIPU_API_KEY`
- **GitHub Actions + devcontainers/ci** — Workflow trigger, runner, reproducible container
- **.NET SDK 10 + Aspire + Avalonia templates, Bun, uv** (all in devcontainer)
- **MCP servers**: `@modelcontextprotocol/server-sequential-thinking`, `@modelcontextprotocol/server-memory`

## Quick Start

1. **Clone the repository**
2. **Open in DevContainer** (VS Code or GitHub Codespaces)
3. **The opencode server starts automatically** on port 4096

## Python Dependencies

This project uses [uv](https://docs.astral.sh/uv/) for Python dependency management. All dependencies are defined in `pyproject.toml` with lock file integrity maintained via `uv.lock`.

### Initial Setup

After cloning, synchronize all dependencies:

```bash
uv sync --all-extras
```

This command:
- Creates a virtual environment (`.venv/`) if it doesn't exist
- Installs all dependencies including development extras (pytest, ruff, mypy, etc.)
- Uses the lock file to ensure reproducible installs

### Dependency Groups

| Group | Description | Installation |
|-------|-------------|--------------|
| `dev` | Development tools (pytest, ruff, mypy, coverage) | Included with `--all-extras` |

### Updating Dependencies

To update dependencies while preserving lock file integrity:

```bash
# Update all dependencies to latest compatible versions
uv lock --upgrade

# Sync the environment with updated lock file
uv sync --all-extras
```

### Adding New Dependencies

```bash
# Add a runtime dependency
uv add package-name

# Add a development dependency
uv add --dev package-name
```

### Running Commands in the Virtual Environment

```bash
# Run a single command
uv run python -m pytest

# Activate the virtual environment manually
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows
```

## Environment Configuration

This project uses environment variables for configuration. Secrets are managed through
GitHub Secrets in CI/CD and local `.env` files for development.

### Local Development Setup

1. **Copy the environment template:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` with your actual values:**
   ```bash
   # Required: Set your API keys and tokens
   GITHUB_TOKEN=ghp_your_token_here
   ZHIPU_API_KEY=your_zhipu_key_here
   GITHUB_REPO=owner/repo
   SENTINEL_BOT_LOGIN=your-bot[bot]
   SENTINEL_ID=sentinel-001
   WEBHOOK_SECRET=$(openssl rand -hex 32)
   ```

3. **Validate your configuration:**
   ```powershell
   pwsh -NoProfile -File ./scripts/validate-env.ps1
   ```

### Required Environment Variables

| Variable | Description | Source |
|----------|-------------|--------|
| `GITHUB_TOKEN` | GitHub API token with `repo`, `read:org`, `read:user` scopes | [Generate](https://github.com/settings/tokens) |
| `ZHIPU_API_KEY` | ZhipuAI API key for GLM models | [Get key](https://open.bigmodel.cn/) |
| `GITHUB_REPO` | Target repository in `owner/repo` format | Your repository |
| `SENTINEL_BOT_LOGIN` | GitHub login of the sentinel bot account | Your bot account |
| `SENTINEL_ID` | Unique identifier for this sentinel instance | Any unique string |
| `WEBHOOK_SECRET` | Secret for validating webhook payloads | Generate with `openssl rand -hex 32` |

### Optional Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GITHUB_PERSONAL_ACCESS_TOKEN` | (uses `GITHUB_TOKEN`) | PAT for MCP GitHub server |
| `KIMI_CODE_ORCHESTRATOR_AGENT_API_KEY` | - | Kimi/Moonshot API key |
| `POLL_INTERVAL` | `60` | Seconds between polling cycles |
| `MAX_BACKOFF` | `300` | Maximum backoff on errors |
| `SENTINEL_HEARTBEAT_INTERVAL` | `300` | Seconds between heartbeats |
| `SUBPROCESS_TIMEOUT` | `1800` | Subprocess timeout in seconds |
| `DAILY_BUDGET_LIMIT` | `10.0` | Daily API budget limit (USD) |
| `GITHUB_WEBHOOK_PORT` | `8080` | Webhook listener port |
| `GITHUB_APP_ID` | - | GitHub App ID for authentication |
| `LOG_LEVEL` | `INFO` | Logging level |
| `ENVIRONMENT` | `development` | Deployment environment |

### GitHub Secrets (CI/CD)

For GitHub Actions workflows, set these secrets in your repository settings
(Settings → Secrets and variables → Actions):

- `GITHUB_TOKEN` — Automatically provided by GitHub Actions
- `ZHIPU_API_KEY` — Your ZhipuAI API key
- `KIMI_CODE_ORCHESTRATOR_AGENT_API_KEY` — (Optional) Kimi API key

### Security Notes

- **Never commit `.env` files** — They are excluded via `.gitignore`
- **Use strong secrets** — Generate webhook secrets with `openssl rand -hex 32`
- **Rotate tokens regularly** — Especially if they may have been exposed
- **Minimal permissions** — Grant only required scopes to GitHub tokens

### Troubleshooting

#### "Missing required variable" error

Ensure all required variables are set in your `.env` file or environment.
Run `pwsh scripts/validate-env.ps1` to see which variables are missing.

#### "Placeholder value detected" error

Replace `YOUR_VALUE_HERE` placeholders with actual values. The validation
script rejects placeholder values to prevent misconfiguration.

#### ".env file not found" warning

Copy the example file: `cp .env.example .env`

#### Python import errors

Synchronize dependencies using uv:

```bash
uv sync --all-extras
```

Or use the legacy pip method:

```bash
pip install -r requirements.txt
```

## Development

### Validation

Run all checks locally:

```powershell
pwsh -NoProfile -File ./scripts/validate.ps1 -All
```

### Individual Checks

```powershell
./scripts/validate.ps1 -Lint   # Lint check
./scripts/validate.ps1 -Scan   # Secret scanning
./scripts/validate.ps1 -Test   # Run tests
```

### Testing

```bash
# All tests
bash test/test-devcontainer-build.sh && bash test/test-devcontainer-tools.sh && bash test/test-prompt-assembly.sh

# Prompt changes
bash test/test-prompt-assembly.sh

# Dockerfile changes
bash test/test-devcontainer-tools.sh
```

## Workflows

| Workflow | Description |
|----------|-------------|
| `orchestrator-agent.yml` | Primary workflow — assembles prompt, runs opencode in devcontainer |
| `publish-docker.yml` | Builds Dockerfile, pushes to GHCR |
| `prebuild-devcontainer.yml` | Layers devcontainer Features on published Docker image |
| `validate.yml` | CI: lint, scan, test, devcontainer build |

## Documentation

- [AGENTS.md](./AGENTS.md) — Project instructions for coding agents
- [plan_docs/](./plan_docs/) — Architecture guides and development plans

## License

See [LICENSE](./LICENSE) for details.
