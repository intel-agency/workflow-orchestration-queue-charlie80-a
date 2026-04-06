# Technology Stack - workflow-orchestration-queue

## Languages
- **Python 3.12+** - Primary language for orchestrator, API webhook receiver, and all system logic
- **PowerShell Core (pwsh)** - Shell bridge scripts and cross-platform CLI interactions
- **Bash** - Shell bridge scripts and utility functions

## Framework & Runtime
- **FastAPI** - High-performance async web framework for webhook receiver
- **Uvicorn** - ASGI web server for production deployment
- **opencode CLI (v1.2.24)** - AI agent runtime for executing workflows
- **ZhipuAI GLM-5** - Primary LLM model (via `ZHIPU_API_KEY`)

## Package Management
- **uv (v0.10.9)** - Rust-based Python package installer and dependency resolver
- **pyproject.toml** - Core definition file for dependencies and metadata
- **uv.lock** - Deterministic lockfile for exact package versions

## Data Validation & Serialization
- **Pydantic** - Strict data validation, settings management, and schema definitions
- **HTTPX** - Asynchronous HTTP client for non-blocking GitHub API calls

## Containerization & Infrastructure
- **Docker** - Core execution engine providing sandboxing and environment consistency
- **Docker Compose** - Multi-container orchestration for complex workflows
- **DevContainers** - Reproducible development environments with lifecycle hooks
- **GitHub Actions** - CI/CD pipelines (SHA-pinned to prevent supply-chain attacks)

## Version Control & Collaboration
- **Git** - Version control system
- **GitHub** - Repository hosting, issue tracking, and project management
- **GitHub App** - Webhook integration and authentication
- **GitHub REST API** - Task discovery and state management

## Security & Authentication
- **HMAC SHA256** - Webhook signature verification
- **GitHub App Installation Tokens** - Scoped authentication
- **GitHub Personal Access Tokens** - MCP server authentication
- **Environment Variable Injection** - Ephemeral credential management

## Observability & Logging
- **Structured Python Logging** - StreamHandler for console output
- **JSON Lines (JSONL)** - Worker output format for audit trails
- **Sentinel Heartbeat Comments** - Real-time status updates on GitHub issues
- **Credential Scrubbing** - Regex-based secret removal from logs

## Architecture Patterns
- **Event-Driven Architecture** - Asynchronous webhook and polling mechanisms
- **Strategy Pattern** - Provider-agnostic queue interface (ITaskQueue)
- **Polling-First Resiliency** - Primary discovery with webhook optimization
- **Assign-Then-Verify Pattern** - Distributed locking via GitHub assignees
- **Script-First Integration** - Shell bridge as primary API

## Development Tools
- **Node.js (v24.14.0 LTS)** - Required for MCP server packages
- **Bun (v1.3.10)** - Fast JavaScript runtime and bundler
- **MCP Servers** - Model Context Protocol for extended capabilities
  - `@modelcontextprotocol/server-sequential-thinking`
  - `@modelcontextprotocol/server-memory`
  - `@modelcontextprotocol/server-github`

## Resource Constraints
- **CPU Limit**: 2 CPUs per worker container
- **Memory Limit**: 4GB RAM per worker container
- **Network Isolation**: Dedicated Docker bridge network
- **Subprocess Timeout**: 5700s (95 min) for prompt commands, 60-300s for infrastructure commands

## Configuration Management
- **Environment Variables** - Runtime configuration and secrets
- **.env Files** - Local development configuration
- **Markdown Instruction Modules** - Decoupled AI behavior logic
- **Labels and Milestones** - Distributed state management

## Key Design Principles
1. **Script-First Integration** - Use existing shell scripts instead of reimplementing
2. **State Visibility** - GitHub as the source of truth (Markdown-as-a-Database)
3. **Self-Bootstrapping Evolution** - System builds itself using its own workflows
4. **Polling-First Resiliency** - Graceful degradation when webhooks fail
5. **Provider-Agnostic Interfaces** - Abstract queue implementations for portability
