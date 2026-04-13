# Workflow Execution Plan: project-setup

**Created:** 2026-04-13
**Branch:** `dynamic-workflow-project-setup-init` (PR #15)
**Workflow:** `project-setup`
**Canonical Source:** `nam20485/agent-instructions` → `dynamic-workflows/project-setup.md`

---

## 1. Overview

| Field | Value |
|-------|-------|
| **Workflow** | `project-setup` |
| **Project** | OS-APOW (Orchestration System — Agent-Powered Orchestration Workflow) |
| **Repository** | `intel-agency/workflow-orchestration-queue-charlie80-a` |
| **Main Assignments** | 6 (`init-existing-repository` → `create-app-plan` → `create-project-structure` → `create-agents-md-file` → `debrief-and-document` → `pr-approval-and-merge`) |
| **Pre-script Events** | 1 (`create-workflow-plan`) |
| **Post-assignment Events** | 2 per assignment (`validate-assignment-completion`, `report-progress`) |
| **Post-script Events** | 1 (`plan-approved` label application) |
| **Total Assignment Invocations** | 6 main + 1 pre-script + (6 × 2) post-assignment + 1 post-script = **20 agent tasks** |

---

## 2. Project Context Summary

### 2.1 What Is Being Built

OS-APOW is a **headless agentic orchestration platform** that transforms GitHub Issues into autonomous execution orders. A user opens a specification issue, and the system dispatches an AI worker that clones the target repo, generates code, runs tests, and submits a PR — all without human intervention.

### 2.2 Architecture: The 4 Pillars

| Pillar | Component | Tech Stack | Responsibility |
|--------|-----------|------------|----------------|
| **Ear** | Work Event Notifier | Python 3.12+, FastAPI, Pydantic, uvicorn | Secure webhook ingestion, HMAC signature validation, intelligent event triage |
| **State** | Work Queue | GitHub Issues, Labels, Milestones | Distributed state via "Markdown as a Database"; labels = state machine (`agent:queued` → `agent:in-progress` → `agent:success`/`agent:error`) |
| **Brain** | Sentinel Orchestrator | Python async, HTTPX, signal handling | Persistent polling, task claiming (assign-then-verify), heartbeat, shell-bridge dispatch |
| **Hands** | Opencode Worker | opencode CLI, LLM (GLM-5), DevContainer | Executes markdown instruction modules against the codebase in an isolated Docker environment |

### 2.3 Tech Stack

- **Language:** Python 3.12+ (primary), PowerShell/Bash (shell bridge)
- **Web Framework:** FastAPI + Uvicorn (ASGI)
- **Validation:** Pydantic (strict schemas)
- **HTTP Client:** HTTPX (async, connection-pooled)
- **Package Manager:** uv (Rust-based, replaces pip/poetry)
- **Containerization:** Docker + DevContainers (isolated worker environments)
- **AI Runtime:** opencode CLI with ZhipuAI GLM-5
- **State Store:** GitHub Issues + Labels (no external DB)

### 2.4 Phased Rollout

| Phase | Name | Scope | Status |
|-------|------|-------|--------|
| **0** | Seeding & Bootstrapping | Manual clone, seed plan docs, project-setup workflow | **Current** |
| **1** | Sentinel MVP | Persistent polling service, shell-bridge dispatch, status feedback | Planned |
| **2** | The Ear (Webhooks) | FastAPI webhook receiver, instant triage, template validation | Planned |
| **3** | Deep Orchestration | Hierarchical task decomposition, self-healing, PR review loops | Planned |

### 2.5 Key Architectural Decisions (ADRs)

- **ADR 07 — Shell-Bridge Execution:** Orchestrator interacts with workers exclusively via `./scripts/devcontainer-opencode.sh`. No direct Docker SDK. Guarantees environment parity.
- **ADR 08 — Polling-First Resiliency:** Webhooks are an optimization; polling is the primary discovery mechanism. System self-heals on restart by reconciling GitHub label states.
- **ADR 09 — Provider-Agnostic Interface:** `ITaskQueue` ABC enables future swap from GitHub Issues to Linear/Jira without touching orchestrator logic.

### 2.6 Applied Simplifications (from OS-APOW Simplification Report v1)

| ID | Simplification | Status |
|----|---------------|--------|
| S-1 | ITaskQueue ABC kept for future provider swapping | KEPT |
| S-2 | Doc duplication retained to aid autonomous agents | KEPT |
| S-3 | Reduced to 3 required env vars: `GITHUB_TOKEN`, `GITHUB_ORG`, `GITHUB_REPO` | IMPLEMENTED |
| S-4 | Environment reset hardcoded to `"stop"` (no mode config) | IMPLEMENTED |
| S-5 | Single-repo polling only; cross-repo Search API deferred | IMPLEMENTED |
| S-6 | Queue consolidated to `src/queue/github_queue.py` (shared by sentinel & notifier) | IMPLEMENTED |
| S-7 | IPv4 scrubbing pattern removed from `scrub_secrets()` | IMPLEMENTED |
| S-8 | "Encrypted" log verbiage removed; plain local files for MVP | IMPLEMENTED |
| S-9 | Phase 3 features moved to "Future Work" appendix | IMPLEMENTED |
| S-10 | Sentinel logs to stdout only (no FileHandler) | IMPLEMENTED |
| S-11 | `raw_payload` field removed from `WorkItem` | IMPLEMENTED |

### 2.7 Reference Implementation (Seeded Scaffolding)

The `plan_docs/` directory contains scaffolded reference code:

```
plan_docs/
├── orchestrator_sentinel.py          # Phase 1 sentinel (polling, claiming, dispatch)
├── notifier_service.py               # Phase 2 webhook receiver (FastAPI + HMAC)
├── src/
│   ├── models/
│   │   └── work_item.py              # Unified WorkItem, TaskType, WorkItemStatus, scrub_secrets()
│   └── queue/
│       └── github_queue.py           # ITaskQueue ABC + GitHubQueue (shared)
├── OS-APOW Development Plan v4.2.md
├── OS-APOW Architecture Guide v3.2.md
├── OS-APOW Implementation Specification v1.2.md
├── OS-APOW Plan Review.md
└── OS-APOW Simplification Report v1.md
```

### 2.8 Constraints

- All GitHub Actions must be pinned to **full 40-char commit SHA** with trailing semver comment.
- The Orchestrator agent **never writes code directly** — it delegates via the `task` tool.
- The `__EVENT_DATA__` placeholder in `orchestrator-agent-prompt.md` must be preserved.
- Delegation depth ≤ 2.
- Secrets must never be hardcoded; env vars crash at startup if missing (per S-3, R-6).

---

## 3. Assignment Execution Plan

### Assignment 1: `init-existing-repository`

| Aspect | Detail |
|--------|--------|
| **Goal** | Initialize the repository: ensure devcontainer is functional, validate tools, establish baseline, open a setup PR on a feature branch. |
| **Key Acceptance Criteria** | - `./scripts/devcontainer-opencode.sh up` runs successfully<br>- All devcontainer tools are available (dotnet, node, bun, uv, gh, opencode, git)<br>- A setup PR is opened against the default branch<br>- PR number is captured as `#initiate-new-repository.init-existing-repository.$pr_num` for downstream use |
| **Project-Specific Notes** | This repo is a GitHub template clone (`intel-agency/workflow-orchestration-queue-charlie80-a`). The devcontainer uses a prebuilt GHCR image; on fresh clones, the image may not exist until `publish-docker` + `prebuild-devcontainer` workflows complete. The `validate` workflow must tolerate missing images (fallback build). |
| **Prerequisites** | Branch `dynamic-workflow-project-setup-init` exists and is checked out. Plan docs are seeded in `plan_docs/`. |
| **Dependencies** | None (first assignment). |
| **Risks** | - **GHCR image not prebuilt yet:** Fallback Dockerfile build may take longer. CI validation may initially fail until first image publish completes.<br>- **Missing secrets:** `ZHIPU_API_KEY` or `GITHUB_TOKEN` not configured will block agent runtime. |
| **Events** | `post-assignment-complete` → `validate-assignment-completion` + `report-progress` |

---

### Assignment 2: `create-app-plan`

| Aspect | Detail |
|--------|--------|
| **Goal** | Create a comprehensive Application Plan issue on GitHub, derived from the plan docs in `plan_docs/`. This plan serves as the master reference for all subsequent implementation. |
| **Key Acceptance Criteria** | - An Application Plan GitHub Issue is created with structured breakdown<br>- Issue references the architecture guide, development plan, and implementation spec<br>- Phases, epics, and stories are clearly delineated<br>- Issue is recorded as `#initiate-new-repository.create-app-plan` for downstream label application |
| **Project-Specific Notes** | The plan must reflect the 4-phase rollout (Phase 0: Seeding, Phase 1: Sentinel MVP, Phase 2: Ear/Webhooks, Phase 3: Deep Orchestration). Should incorporate the Plan Review's findings (I-1 through I-10) as resolved items and flag deferred items (cost guardrails, cross-repo polling, reconciliation loop). Must align with the Simplification Report's IMPLEMENTED changes. |
| **Prerequisites** | `init-existing-repository` completed. Repository is accessible and agent has GitHub API access. |
| **Dependencies** | `init-existing-repository` (must have working devcontainer + GitHub access) |
| **Risks** | - **Plan drift from reference docs:** Agent must faithfully represent the seeded plan docs, not invent new architecture.<br>- **Scope creep:** Phase 3 features must be in a "Future Work" appendix per S-9. |
| **Events** | `post-assignment-complete` → `validate-assignment-completion` + `report-progress` |

---

### Assignment 3: `create-project-structure`

| Aspect | Detail |
|--------|--------|
| **Goal** | Create the actual project directory structure and skeleton files that implement the OS-APOW system. Move scaffolded code from `plan_docs/` into the proper `src/` layout. |
| **Key Acceptance Criteria** | - Project directory matches the Implementation Spec structure:<br> `pyproject.toml`, `uv.lock`, `src/notifier_service.py`, `src/orchestrator_sentinel.py`, `src/models/work_item.py`, `src/queue/github_queue.py`, `scripts/`, `local_ai_instruction_modules/`<br>- `pyproject.toml` defines dependencies: `fastapi`, `uvicorn`, `pydantic`, `httpx`<br>- Reference code from `plan_docs/` is migrated to correct locations<br>- `uv sync` succeeds without errors<br>- All Python files pass basic lint checks |
| **Project-Specific Notes** | The scaffolded reference implementations in `plan_docs/orchestrator_sentinel.py`, `plan_docs/notifier_service.py`, and `plan_docs/src/` already incorporate the Plan Review fixes (unified data model, assign-then-verify, backoff, heartbeats, connection pooling, credential scrubbing, signal handling, subprocess timeout). These should be migrated with minimal modification. The `ITaskQueue` ABC is retained per S-1. |
| **Prerequisites** | `create-app-plan` completed (plan issue exists for reference). |
| **Dependencies** | `create-app-plan` (plan issue provides structure guidance) |
| **Risks** | - **Model divergence during migration:** Agent might inadvertently change field names or enums. Must preserve the unified `WorkItem` model from `src/models/work_item.py`.<br>- **Import path breakage:** Moving files from `plan_docs/src/` to `src/` may break relative imports. |
| **Events** | `post-assignment-complete` → `validate-assignment-completion` + `report-progress` |

---

### Assignment 4: `create-agents-md-file`

| Aspect | Detail |
|--------|--------|
| **Goal** | Create or update the `AGENTS.md` file with OS-APOW-specific project instructions, replacing template placeholders with project-specific content. |
| **Key Acceptance Criteria** | - `AGENTS.md` accurately describes the OS-APOW project, tech stack, and repository map<br>- Template placeholders (`workflow-orchestration-queue-charlie80-a`, `intel-agency`) are preserved (they are replaced at clone time by the creation script, not by agents)<br>- Testing section references the correct test commands<br>- Coding conventions reflect Python-first project (not .NET)<br>- Agent-specific guardrails reference the sentinel/notifier architecture |
| **Project-Specific Notes** | The existing `AGENTS.md` in the template repo is .NET/Aspire-focused. It must be updated to reflect that this is a **Python 3.12+** project using `uv`, `FastAPI`, and `HTTPX`. Key changes: remove .NET SDK references, update tech stack section, update testing commands (shell-based tests for devcontainer + `uv run pytest` for Python tests), update repository map to reflect `src/` Python layout. Keep the template placeholder rule since this is still a template repo. |
| **Prerequisites** | `create-project-structure` completed (file layout is known). |
| **Dependencies** | `create-project-structure` (directory structure must exist to accurately document it) |
| **Risks** | - **Overwriting template infrastructure instructions:** The existing AGENTS.md contains critical workflow and validation instructions that must be preserved (SHA pinning rules, CI validation, `__EVENT_DATA__` placeholder rule).<br>- **Template placeholder confusion:** Agent must not replace `workflow-orchestration-queue-charlie80-a` placeholders — those are handled by the clone-time creation script. |
| **Events** | `post-assignment-complete` → `validate-assignment-completion` + `report-progress` |

---

### Assignment 5: `debrief-and-document`

| Aspect | Detail |
|--------|--------|
| **Goal** | Produce a comprehensive debrief summarizing all work completed during the project-setup workflow. Document decisions made, deviations from plan, and any issues encountered. |
| **Key Acceptance Criteria** | - A debrief document is created (or GitHub Issue posted) summarizing all completed assignments<br>- Deviations from the plan docs are explicitly called out<br>- All reference code files are accounted for and migrated<br>- Open issues / TODO items are listed with recommended next steps<br>- The document references the Application Plan issue for traceability |
| **Project-Specific Notes** | Should confirm that all Simplification Report items (S-1 through S-11) are properly applied in the migrated code. Should verify that Plan Review recommendations (R-1 through R-8) are implemented. Should flag any items that were intentionally deferred (cost guardrails, cross-repo polling, reconciliation loop, encrypted logs). |
| **Prerequisites** | All 4 previous main assignments completed. |
| **Dependencies** | `create-agents-md-file` (all structural work must be done) |
| **Risks** | - **Incomplete audit:** Agent might miss subtle deviations between plan docs and implemented code.<br>- **Low actionability:** Debrief must contain concrete next steps, not just summaries. |
| **Events** | `post-assignment-complete` → `validate-assignment-completion` + `report-progress` |

---

### Assignment 6: `pr-approval-and-merge`

| Aspect | Detail |
|--------|--------|
| **Goal** | Merge the setup PR (opened during `init-existing-repository`) after validating CI passes. Handle CI remediation if checks fail. Clean up setup artifacts. |
| **Key Acceptance Criteria** | - `$pr_num` is extracted from `#initiate-new-repository.init-existing-repository` output<br>- CI checks on the PR are green (or remediated within 3 fix cycles)<br>- PR is approved and merged (self-approval acceptable for setup PR)<br>- Setup branch is deleted after merge<br>- Any related setup issues are closed<br>- Post-merge: default branch contains the complete project structure |
| **Project-Specific Notes** | This is an **automated setup PR** — no human stakeholder approval is required. The orchestrator self-approves. However, the CI remediation loop MUST still run: if CI checks fail, attempt up to 3 fix cycles before escalating. Common CI failures to anticipate: lint errors on new Python files, missing `pyproject.toml` configuration, devcontainer build issues if GHCR image doesn't exist yet. |
| **Prerequisites** | `debrief-and-document` completed. All code changes committed to the setup branch. |
| **Dependencies** | `debrief-and-document` (all work must be finalized before merge) |
| **Risks** | - **CI failures from template workflows:** The `validate` workflow includes .NET/lint checks that may not apply to this Python project. May need workflow updates.<br>- **GHCR image not published:** Fresh clone means no prebuilt devcontainer image exists. CI must tolerate this.<br>- **Fix loop exhaustion:** 3 fix cycles may not be enough for complex CI issues. |
| **Events** | `post-assignment-complete` → `validate-assignment-completion` + `report-progress` |

---

### Event: `pre-script-begin` — `create-workflow-plan`

| Aspect | Detail |
|--------|--------|
| **Goal** | Create this workflow execution plan document before any main assignments begin. |
| **Key Acceptance Criteria** | - `plan_docs/workflow-plan.md` exists and documents all 6 assignments with project-specific context<br>- Sequencing and dependencies are clearly mapped<br>- Open questions and risks are identified |
| **When** | Before Assignment 1 (`init-existing-repository`) |
| **Output Record** | `#events.pre-script-begin.create-workflow-plan` |

---

### Event: `post-assignment-complete` (repeated 6 times)

Triggered after each main assignment completes. Runs two sub-assignments:

| Sub-Assignment | Goal |
|----------------|------|
| `validate-assignment-completion` | Verify the just-completed assignment meets its acceptance criteria |
| `report-progress` | Post a progress update (GitHub comment or issue update) documenting what was completed |

**Output Records:** `#events.post-assignment-complete.validate-assignment-completion`, `#events.post-assignment-complete.report-progress`

---

### Event: `post-script-complete` — `plan-approved` Label

| Aspect | Detail |
|--------|--------|
| **Goal** | Apply the `orchestration:plan-approved` label to the Application Plan issue created during `create-app-plan`. This signals the plan is ready for epic creation and triggers the next phase of the orchestration pipeline. |
| **When** | After all assignments and post-assignment events complete successfully |
| **Prerequisites** | The Application Plan issue exists (from `create-app-plan`) and its issue number is recorded |
| **Output Record** | `#events.post-script-complete.plan-approved` |

---

## 4. Sequencing

```
┌─────────────────────────────────────────────────────────────────────┐
│                    PRE-SCRIPT BEGIN                                 │
│  ┌──────────────────────────┐                                       │
│  │  create-workflow-plan    │ → produces plan_docs/workflow-plan.md │
│  └──────────────────────────┘                                       │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│  ASSIGNMENT 1: init-existing-repository                             │
│  ├── validate-assignment-completion                                 │
│  └── report-progress                                                │
│  OUTPUT: #initiate-new-repository.init-existing-repository.$pr_num  │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│  ASSIGNMENT 2: create-app-plan                                      │
│  ├── validate-assignment-completion                                 │
│  └── report-progress                                                │
│  OUTPUT: #initiate-new-repository.create-app-plan (plan issue #)    │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│  ASSIGNMENT 3: create-project-structure                             │
│  ├── validate-assignment-completion                                 │
│  └── report-progress                                                │
│  OUTPUT: #initiate-new-repository.create-project-structure          │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│  ASSIGNMENT 4: create-agents-md-file                                │
│  ├── validate-assignment-completion                                 │
│  └── report-progress                                                │
│  OUTPUT: #initiate-new-repository.create-agents-md-file             │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│  ASSIGNMENT 5: debrief-and-document                                 │
│  ├── validate-assignment-completion                                 │
│  └── report-progress                                                │
│  OUTPUT: #initiate-new-repository.debrief-and-document              │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│  ASSIGNMENT 6: pr-approval-and-merge                                │
│  ├── Uses $pr_num from Assignment 1                                 │
│  ├── CI remediation: up to 3 fix cycles                             │
│  ├── Self-approve setup PR → merge → delete branch                  │
│  ├── validate-assignment-completion                                 │
│  └── report-progress                                                │
│  OUTPUT: #initiate-new-repository.pr-approval-and-merge             │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    POST-SCRIPT COMPLETE                              │
│  ┌──────────────────────────────────────────────────────┐           │
│  │  Apply `orchestration:plan-approved` label to        │           │
│  │  the Application Plan issue (from Assignment 2)      │           │
│  └──────────────────────────────────────────────────────┘           │
│  OUTPUT: #events.post-script-complete.plan-approved                  │
└─────────────────────────────────────────────────────────────────────┘
```

**Critical Path:** All 6 assignments are strictly sequential. No parallelization is possible because each assignment depends on the output of the previous one.

**Total Estimated Agent Tasks:** 20
- 1 pre-script event
- 6 main assignments
- 12 post-assignment sub-tasks (2 per assignment × 6 assignments)
- 1 post-script event

---

## 5. Open Questions

| # | Question | Impact | Recommended Resolution |
|---|----------|--------|----------------------|
| 1 | **Will the GHCR devcontainer image be prebuilt before CI runs?** | If not, the `validate` workflow must tolerate a fallback Dockerfile build, which may be slow or fail. | Ensure `publish-docker` and `prebuild-devcontainer` workflows complete their first run before merging. If they fail, the `validate` workflow must have fallback handling per template design constraints. |
| 2 | **Should the `validate` CI workflow be updated for a Python project?** | The current `validate` workflow includes lint/scan steps that may be .NET-focused (e.g., markdown lint, shellcheck). New Python files may not be covered. | Update `scripts/validate.ps1` to include Python-specific checks (`ruff check`, `mypy`, `pytest`). Add a Python lint step to the CI workflow. |
| 3 | **How should scaffolded code in `plan_docs/` be treated during migration?** | The reference implementations in `plan_docs/` are designed as scaffolds. They may have intentional gaps (e.g., cost guardrails marked as deferred). | Migrate code as-is. Do not "fill in" deferred features during project-setup. Those are Phase 1+ implementation tasks. Mark them with `# TODO:` comments referencing the plan. |
| 4 | **Should `pyproject.toml` use a `src/` layout or flat layout?** | Affects import paths, test configuration, and uv/packaging behavior. | Use `src/` layout as specified in the Implementation Spec. This matches the scaffolded `src/` directory structure already in `plan_docs/src/`. |
| 5 | **What Python version constraints should `pyproject.toml` specify?** | Determines compatibility and available language features (e.g., type parameter syntax in 3.12). | `requires-python = ">=3.12"` per the Implementation Spec. |
| 6 | **Should the template placeholder strings be preserved in AGENTS.md?** | The creation script (`create-repo-with-plan-docs.ps1`) replaces `workflow-orchestration-queue-charlie80-a` with the actual repo name. If AGENTS.md is updated with project-specific content, the placeholders may need to remain for future clones. | Preserve template placeholder strings (`workflow-orchestration-queue-charlie80-a`, `intel-agency`) in AGENTS.md. The creation script handles replacement at clone time. |
| 7 | **How will the `orchestration:plan-approved` label be created?** | The label must exist on the repository before it can be applied to an issue. | Ensure `.github/.labels.json` includes `orchestration:plan-approved`. Run `scripts/import-labels.ps1` to sync labels to the repo. |
| 8 | **What is the expected state of `plan_docs/` after project-setup completes?** | Should scaffolded files remain, be removed, or be archived? | Keep `plan_docs/` as the canonical design reference. The migrated code in `src/` is the implementation. Exclude `plan_docs/` from strict linting per template design constraints. |

---

## 6. Risk Register

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| CI workflow incompatibility (Python vs .NET expectations) | High | Medium | Update validate workflow to include Python checks before Assignment 6. Allow fallback for first run. |
| GHCR image not available on fresh clone | Medium | High | Template design constraints already specify fallback build tolerance. Monitor `publish-docker` workflow completion. |
| Agent modifies scaffolded code beyond acceptable scope | Medium | Medium | Explicit instructions in each assignment's "Project-Specific Notes" to preserve scaffolded code structure. |
| Template placeholders accidentally replaced by agent | Low | High | Guardrails in assignment descriptions. AGENTS.md rule about placeholder preservation. |
| PR merge conflicts from concurrent changes | Low | Medium | Setup branch is the only active branch during project-setup. Low conflict probability. |
| CI remediation loop exhausts 3 fix cycles | Low | Medium | Pre-validate Python lint/test locally before pushing. Use `./scripts/validate.ps1 -All` before commit. |

---

## 7. Acceptance Criteria (Overall Workflow)

- [ ] All 6 main assignments completed successfully
- [ ] `create-workflow-plan` pre-script event executed and output recorded
- [ ] `validate-assignment-completion` + `report-progress` executed after each main assignment
- [ ] `orchestration:plan-approved` label applied to the Application Plan issue
- [ ] Setup PR merged, setup branch deleted, related setup issues closed
- [ ] Any GitHub Actions workflows created/modified have all actions pinned to full commit SHA
- [ ] Project structure matches Implementation Spec (`src/`, `pyproject.toml`, etc.)
- [ ] `AGENTS.md` reflects Python-first project with correct tech stack
- [ ] All reference code migrated from `plan_docs/` to proper `src/` locations
