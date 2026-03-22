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
├── test/                    # Test suite
├── plan_docs/               # Architecture and planning documents
├── local_ai_instruction_modules/  # Local AI instruction modules
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
