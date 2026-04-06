# System Architecture - workflow-orchestration-queue

## Executive Summary

workflow-orchestration-queue represents a paradigm shift from **Interactive AI Coding** to **Headless Agentic Orchestration**. It transforms standard project management artifacts (GitHub Issues) into "Execution Orders" that are autonomously fulfilled by specialized AI agents, moving the agent from a passive co-pilot role to a background production service.

The system is **Self-Bootstrapping** - it uses its own orchestration capabilities to refine and build its components, allowing the AI to "build its own house" while residing within it.

## Four Pillars Architecture

The system is distributed across four conceptual pillars, each handling a distinct domain of the workflow:

### 1. The Ear (Work Event Notifier)

**Role:** Primary gateway for external stimuli and asynchronous triggers

**Technology Stack:**
- Python 3.12
- FastAPI
- uv for dependency management
- Pydantic for schema validation

**Responsibilities:**
- **Secure Webhook Ingestion**: Hardened endpoint for GitHub events (issues, issue_comment, pull_request)
- **Cryptographic Verification**: HMAC SHA256 validation against WEBHOOK_SECRET
- **Intelligent Event Triage**: Parse payloads and map to unified WorkItem objects
- **Manifest Generation**: Create structured WorkItem Manifest (JSON) for state sharing
- **Queue Initialization**: Apply agent:queued label via GitHub REST API

**Security:**
- Prevents "Prompt Injection via Webhook" through signature validation
- Only verified GitHub events can trigger agent actions

### 2. The State (Work Queue)

**Philosophy:** "Markdown as a Database"

**Implementation:**
- GitHub Issues, Labels, and Milestones as persistence layer
- World-class audit logs and transparent versioning
- Built-in UI for human supervision

**State Machine (Label Logic):**
- `agent:queued` - Task validated, awaiting Sentinel
- `agent:in-progress` - Sentinel claimed the issue (distributed lock via assignees)
- `agent:reconciling` - Recovery state for stale tasks
- `agent:success` - Terminal success state
- `agent:error` - Technical failure with diagnostic logs
- `agent:infra-failure` - Infrastructure-level failure
- `agent:impl-error` - Implementation-level failure
- `agent:stalled-budget` - Budget exceeded (deferred feature)

**Concurrency Control:**
- GitHub Assignees as semaphore
- **Assign-Then-Verify Pattern**:
  1. Attempt assignment to Sentinel bot account
  2. Re-fetch issue to verify assignment
  3. Only proceed if verification succeeds
  4. Graceful abort if race condition detected

### 3. The Brain (Sentinel Orchestrator)

**Role:** Persistent supervisor managing worker lifecycle and intent mapping

**Technology Stack:**
- Python (Async Background Service)
- PowerShell Core (pwsh)
- Docker CLI

**Lifecycle Management:**
1. **Polling Discovery** (every 60s, configurable)
   - Query GitHub Issues API for `agent:queued` label
   - Jittered exponential backoff on rate limits (403/429)
   - Future: Cross-repo org-wide polling via Search API

2. **Auth Synchronization**
   - Run `scripts/gh-auth.ps1` and `scripts/common-auth.ps1`
   - Ensure scoped installation tokens

3. **Shell-Bridge Protocol**
   - `./scripts/devcontainer-opencode.sh up` - Provision environment
   - `./scripts/devcontainer-opencode.sh start` - Launch opencode-server
   - `./scripts/devcontainer-opencode.sh prompt "{workflow_instruction}"` - Execute task
   - Formalized return codes (Exit 0 = Success, 1-10 = Infra Error, 11+ = Logic Error)

4. **Workflow Mapping**
   - Translate issue type to specific prompt string
   - Select appropriate agent-instruction module

5. **Telemetry**
   - Capture stdout to local log files
   - Post heartbeat comments every 5 minutes (configurable via `SENTINEL_HEARTBEAT_INTERVAL`)
   - Background `asyncio` coroutine for heartbeats

6. **Environment Reset**
   - Stop worker container between tasks
   - Prevent state bleed while maintaining fast restart

7. **Graceful Shutdown**
   - Handle `SIGTERM` and `SIGINT` signals
   - Finish current task before exit
   - Close connection pools cleanly

### 4. The Hands (Opencode Worker)

**Environment:**
- High-fidelity DevContainer from workflow-orchestration-queue-charlie80-a
- opencode-server CLI
- LLM Core (GLM-5 or Claude 3.5 Sonnet)

**Worker Capabilities:**
- **Contextual Awareness**: Local project structure access, vector-indexed codebase view
- **Instructional Logic**: Execute `.md` workflow modules from `/local_ai_instruction_modules/`
- **Verification**: Run local test suites before PR submission

**Key Principle:** Logic-as-Markdown - workflows updated via commits, not code changes

## Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        External Systems                          │
│  ┌──────────────┐         ┌──────────────┐                     │
│  │   GitHub     │◄────────┤   Webhook    │                     │
│  │   (Issues,   │         │   Events     │                     │
│  │   Labels,    │         └──────────────┘                     │
│  │   PRs)       │                                                │
│  └──────┬───────┘                                                │
└─────────┼───────────────────────────────────────────────────────┘
          │
          │ REST API
          │
┌─────────▼───────────────────────────────────────────────────────┐
│                    workflow-orchestration-queue                  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  1. THE EAR (Work Event Notifier)                        │  │
│  │     ┌─────────────────────────────────────────────┐      │  │
│  │     │ FastAPI Webhook Receiver                     │      │  │
│  │     │ - HMAC SHA256 Verification                   │      │  │
│  │     │ - Event Triage & Manifest Generation         │      │  │
│  │     │ - Apply agent:queued label                   │      │  │
│  │     └─────────────────────────────────────────────┘      │  │
│  └──────────────────────────────────────────────────────────┘  │
│                          │                                      │
│                          │ Write to GitHub Issues               │
│                          ▼                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  2. THE STATE (Work Queue)                               │  │
│  │     ┌─────────────────────────────────────────────┐      │  │
│  │     │ GitHub Issues (Markdown-as-a-Database)      │      │  │
│  │     │ - Labels: queued, in-progress, success,     │      │  │
│  │     │   error, reconciling                        │      │  │
│  │     │ - Assignees: Distributed Lock               │      │  │
│  │     │ - Comments: Audit Trail & Heartbeats        │      │  │
│  │     └─────────────────────────────────────────────┘      │  │
│  └──────────────────────────────────────────────────────────┘  │
│                          │                                      │
│                          │ Poll for agent:queued                │
│                          ▼                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  3. THE BRAIN (Sentinel Orchestrator)                    │  │
│  │     ┌─────────────────────────────────────────────┐      │  │
│  │     │ Async Polling Service (every 60s)           │      │  │
│  │     │ - Assign-Then-Verify Locking                │      │  │
│  │     │ - Workflow Mapping & Prompt Construction    │      │  │
│  │     │ - Heartbeat Comments (every 5 min)          │      │  │
│  │     │ - Graceful Shutdown (SIGTERM/SIGINT)        │      │  │
│  │     └─────────────────────────────────────────────┘      │  │
│  └──────────────────────────────────────────────────────────┘  │
│                          │                                      │
│                          │ Shell-Bridge Protocol                │
│                          ▼                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  4. THE HANDS (Opencode Worker)                          │  │
│  │     ┌─────────────────────────────────────────────┐      │  │
│  │     │ DevContainer (Docker)                       │      │  │
│  │     │ - opencode-server CLI                       │      │  │
│  │     │ - LLM Agent (GLM-5)                         │      │  │
│  │     │ - Instruction Modules (*.md)                │      │  │
│  │     │ - Isolated Network & Resource Limits        │      │  │
│  │     └─────────────────────────────────────────────┘      │  │
│  └──────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

## Data Flow (Happy Path)

```
1. Stimulus
   └─► User opens GitHub Issue with application-plan template

2. Notification
   └─► GitHub Webhook hits Notifier (FastAPI)

3. Triage
   └─► Notifier verifies signature
   └─► Confirms title pattern (e.g., [Plan])
   └─► Adds agent:queued label via GH API

4. Claim
   └─► Sentinel poller detects new label
   └─► Assigns issue to Agent account (assign-then-verify)
   └─► Updates label to agent:in-progress

5. Sync
   └─► Sentinel runs git clone/pull in managed workspace

6. Environment Check
   └─► Sentinel executes devcontainer-opencode.sh up

7. Dispatch
   └─► Sentinel sends: devcontainer-opencode.sh prompt "Run workflow..."

8. Execution
   └─► Worker reads issue
   └─► Analyzes tech stack
   └─► Calls GitHub API to create Epic issues
   └─► Links child issues to parent Plan

9. Finalize
   └─► Worker posts "Execution Complete" comment
   └─► Sentinel detects subprocess exit
   └─► Removes in-progress label
   └─► Adds agent:success label
```

## Security Architecture

### Network Isolation
- Worker containers in dedicated Docker network
- Cannot access host network or local subnet
- Prevents lateral movement attacks

### Credential Scoping
- GitHub App Installation Tokens
- Injected as temporary environment variables
- Destroyed on container exit
- Never written to disk

### Credential Scrubbing
All worker output passed through `scrub_secrets()`:
- GitHub PATs: `ghp_*`, `ghs_*`, `gho_*`, `github_pat_*`
- Bearer tokens
- API keys: `sk-*`
- ZhipuAI keys

Two log streams:
1. **Sanitized log** - Posted to GitHub (public)
2. **Raw log** - Local forensic audit trail (Black Box)

### Resource Constraints
- CPU: 2 CPUs max per worker
- RAM: 4GB max per worker
- Prevents DoS from rogue agents

## Key Architectural Decisions (ADRs)

### ADR 07: Standardized Shell-Bridge Execution
**Decision:** Orchestrator interacts via `./scripts/devcontainer-opencode.sh` exclusively
**Rationale:** Reuses existing Docker logic, prevents configuration drift
**Consequence:** Python remains lightweight, shell handles heavy lifting

### ADR 08: Polling-First Resiliency Model
**Decision:** Polling as primary discovery; webhooks as optimization
**Rationale:** Webhooks are fire-and-forget; polling ensures self-healing
**Consequence:** System recovers from downtime automatically

### ADR 09: Provider-Agnostic Interface Layer
**Decision:** All queue interactions behind `ITaskQueue` interface
**Rationale:** Prevents vendor lock-in (GitHub → Linear, Notion, SQL)
**Consequence:** Core logic reusable across providers

## Self-Bootstrapping Lifecycle

1. **Bootstrap** - Manually clone workflow-orchestration-queue-charlie80-a
2. **Seed** - Add plan docs to repo, run create-repo-from-plan-docs
3. **Init** - Run devcontainer-opencode.sh up
4. **Orchestrate** - Run orchestrate-dynamic-workflow with project-setup
5. **Autonomous** - Start Sentinel service; AI manages all further development

## Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| GitHub API Rate Limiting | High | App tokens (5K req/hr), local caching, long-polling |
| LLM Looping/Hallucination | High | max_steps timeout, cost guardrails, retry counter |
| Concurrency Collisions | Medium | Assign-then-verify pattern via GitHub Assignees |
| Container Drift | Medium | Stop worker between tasks, state isolation |
| Security Injection | Medium | HMAC validation, isolated containers, ephemeral creds |

## Implementation Phases

- **Phase 0**: Seeding & Bootstrapping (Manual)
- **Phase 1**: The Sentinel (MVP) - Autonomous polling & execution
- **Phase 2**: The Ear (Webhook Automation) - Real-time ingestion
- **Phase 3**: Deep Orchestration - Hierarchical decomposition & self-healing
