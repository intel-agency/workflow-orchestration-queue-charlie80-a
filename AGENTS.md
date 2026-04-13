---
file: AGENTS.md
description: Project instructions for coding agents
scope: repository
---

<instructions>
  <purpose>
    <summary>
      **OS-APOW** (Orchestration System — Agent-Powered Orchestration Workflow) is a headless agentic
      orchestration system that transforms GitHub Issues into "Execution Orders" autonomously fulfilled
      by specialized AI agents. Built on the **Four Pillars** architecture — **Ear** (FastAPI webhook
      receiver), **State** (GitHub Issues as database), **Brain** (Sentinel orchestrator), and **Hands**
      (opencode worker) — the system moves AI from a passive co-pilot to a background production service.
      It is self-bootstrapping: the system uses its own orchestration capabilities to build and evolve
      its own components. On GitHub events, the `orchestrator-agent` workflow assembles a structured
      prompt, spins up a devcontainer, and runs `opencode --agent Orchestrator` to delegate work to
      specialist sub-agents in `.opencode/agents/`.
    </summary>
  </purpose>

  <tech_stack>
    <item>Python 3.12+ — primary language for orchestrator, API webhook receiver, and all system logic</item>
    <item>FastAPI + Uvicorn — async web framework for webhook receiver (The Ear)</item>
    <item>Pydantic + pydantic-settings — strict data validation, schema definitions, and settings management</item>
    <item>httpx — async HTTP client for non-blocking GitHub API calls</item>
    <item>uv (v0.10.9) — Rust-based Python package manager and dependency resolver</item>
    <item>opencode CLI (v1.2.24) — AI agent runtime (`opencode --model zai-coding-plan/glm-5 --agent Orchestrator`)</item>
    <item>ZhipuAI GLM models via `ZHIPU_API_KEY`</item>
    <item>Docker + DevContainers — sandboxed execution environments with resource constraints</item>
    <item>GitHub Actions — CI/CD pipelines and workflow orchestration triggers</item>
    <item>pytest + pytest-asyncio + pytest-cov — testing framework with async support and coverage</item>
    <item>ruff — fast Python linter and formatter</item>
    <item>mypy — static type checker (strict mode)</item>
    <item>MCP servers: `@modelcontextprotocol/server-sequential-thinking`, `@modelcontextprotocol/server-memory`</item>
  </tech_stack>

  <repository_map>
    <!-- Source Code (Python) -->
    <entry><path>src/os_apow/</path><description>Main package namespace for OS-APOW</description></entry>
    <entry><path>src/config/settings.py</path><description>Application settings using Pydantic BaseSettings (env vars, validation)</description></entry>
    <entry><path>src/config/validation.py</path><description>Configuration validation helpers</description></entry>
    <entry><path>src/models/work_item.py</path><description>WorkItem data model, TaskType/TaskStatus enums, scrub_secrets() utility</description></entry>
    <entry><path>src/queue/</path><description>Queue management (ITaskQueue interface, GitHubIssueQueue implementation)</description></entry>
    <entry><path>src/notifier/</path><description>FastAPI webhook receiver (The Ear) — HMAC verification, event triage, queue initialization</description></entry>
    <!-- Tests -->
    <entry><path>tests/</path><description>Python unit tests (pytest) — conftest.py, test modules</description></entry>
    <entry><path>test/</path><description>Shell-based integration tests: devcontainer build, tool availability, prompt assembly</description></entry>
    <entry><path>test/fixtures/</path><description>Sample webhook payloads for local testing</description></entry>
    <!-- Configuration -->
    <entry><path>pyproject.toml</path><description>Python project metadata, dependencies, and tool configs (pytest, ruff, mypy, coverage)</description></entry>
    <entry><path>uv.lock</path><description>Deterministic lockfile for exact package versions</description></entry>
    <entry><path>.python-version</path><description>Python version pin (3.12)</description></entry>
    <entry><path>.env.example</path><description>Environment variable template — copy to .env for local development</description></entry>
    <entry><path>requirements.txt</path><description>Legacy pip-compatible dependency list</description></entry>
    <!-- Workflows -->
    <entry><path>.github/workflows/orchestrator-agent.yml</path><description>Primary workflow — assembles prompt, logs into GHCR, runs opencode in devcontainer</description></entry>
    <entry><path>.github/workflows/prompts/orchestrator-agent-prompt.md</path><description>Prompt template with `__EVENT_DATA__` placeholder (sed-substituted at runtime)</description></entry>
    <entry><path>.github/workflows/publish-docker.yml</path><description>Builds Dockerfile, pushes to GHCR with branch-latest and branch-&lt;VERSION_PREFIX.run_number&gt; tags</description></entry>
    <entry><path>.github/workflows/prebuild-devcontainer.yml</path><description>Layers devcontainer Features on published Docker image (triggered by workflow_run)</description></entry>
    <entry><path>.github/workflows/validate.yml</path><description>CI validation — lint, scan, test, devcontainer build</description></entry>
    <!-- Agent definitions -->
    <entry><path>.opencode/agents/orchestrator.md</path><description>Orchestrator — coordinates specialists, never writes code directly</description></entry>
    <entry><path>.opencode/agents/</path><description>All specialist agents (developer, code-reviewer, planner, devops-engineer, github-expert, etc.)</description></entry>
    <entry><path>.opencode/commands/</path><description>Reusable command prompts (orchestrate-new-project, grind-pr-reviews, fix-failing-workflows, etc.)</description></entry>
    <entry><path>opencode.json</path><description>opencode config — MCP server definitions</description></entry>
    <!-- Devcontainer -->
    <entry><path>.github/.devcontainer/Dockerfile</path><description>Devcontainer image — Python 3.12, .NET SDK, Node.js, Bun, uv, opencode CLI (build context for publish-docker)</description></entry>
    <entry><path>.github/.devcontainer/devcontainer.json</path><description>Build-time devcontainer config (Dockerfile + Features: node, python, gh CLI)</description></entry>
    <entry><path>.devcontainer/devcontainer.json</path><description>Consumer devcontainer — pulls prebuilt GHCR image, forwards port 4096, and auto-starts `opencode serve` on container start</description></entry>
    <!-- Scripts -->
    <entry><path>scripts/start-opencode-server.sh</path><description>Guarded `opencode serve` bootstrapper used by the devcontainer lifecycle and workflow attach path</description></entry>
    <entry><path>scripts/devcontainer-opencode.sh</path><description>CLI wrapper around devcontainer for the opencode server workflow. Commands: up, start, prompt, stop, down. Used by the Sentinel (Brain) as the Shell-Bridge Protocol.</description></entry>
    <entry><path>scripts/verify-python-env.sh</path><description>Verifies Python environment: version, uv, venv, core imports, tool versions</description></entry>
    <entry><path>scripts/validate-env.ps1</path><description>Validates .env file for required variables and rejects placeholder values</description></entry>
    <!-- Documentation -->
    <entry><path>docs/architecture.md</path><description>System architecture — Four Pillars, data flow, security, ADRs</description></entry>
    <entry><path>docs/tech-stack.md</path><description>Technology stack details and design principles</description></entry>
    <entry><path>plan_docs/</path><description>Architecture guides and development plans (OS-APOW Development Plan, Architecture Guide, Implementation Spec)</description></entry>
    <!-- Remote instructions -->
    <entry><path>local_ai_instruction_modules/</path><description>Local instruction modules (development rules, workflows, delegation, terminal commands)</description></entry>

    <opencode_server>
      <summary>
        The consumer devcontainer auto-starts `opencode serve` through `scripts/start-opencode-server.sh`.
        The server listens on port `4096` by default so host or in-container clients can attach with
        `opencode run --attach http://127.0.0.1:4096 ...` (or the forwarded host port when connecting from outside the container).
      </summary>
    </opencode_server>
  </repository_map>

  <instruction_source>
    <repository>
      <name>nam20485/agent-instructions</name>
      <branch>main</branch>
    </repository>
    <guidance>
      Remote instructions are the single source of truth. Fetch from raw URLs:
      replace `github.com/` with `raw.githubusercontent.com/` and remove `blob/`.
      Core instructions: `https://raw.githubusercontent.com/nam20485/agent-instructions/main/ai_instruction_modules/ai-core-instructions.md`
    </guidance>
    <modules>
      <module type="core" required="true" link="https://github.com/nam20485/agent-instructions/blob/main/ai_instruction_modules/ai-core-instructions.md">Core Instructions</module>
      <module type="local" required="true" path="local_ai_instruction_modules">Local AI Instructions</module>
      <module type="local" required="true" path="local_ai_instruction_modules/ai-dynamic-workflows.md">Dynamic Workflow Orchestration</module>
      <module type="local" required="true" path="local_ai_instruction_modules/ai-workflow-assignments.md">Workflow Assignments</module>
      <module type="local" required="true" path="local_ai_instruction_modules/ai-development-instructions.md">Development Instructions</module>
      <module type="optional" path="local_ai_instruction_modules/ai-terminal-commands.md">Terminal Commands</module>
    </modules>
  </instruction_source>

  <environment_setup>
    <secrets>
      <item>`ZHIPU_API_KEY` — ZhipuAI model access; set in repo Settings → Secrets.</item>
      <item>`KIMI_CODE_ORCHESTRATOR_AGENT_API_KEY` — Kimi (Moonshot) model access; set in repo Settings → Secrets.</item>
      <item>`GITHUB_TOKEN` — provided automatically by Actions.</item>
      <item>`WEBHOOK_SECRET` — HMAC SHA256 key for webhook signature verification; generate with `openssl rand -hex 32`.</item>
      <item>`SENTINEL_BOT_LOGIN` — GitHub login of the sentinel bot account for assign-then-verify locking.</item>
      <item>`SENTINEL_ID` — Unique identifier for this sentinel instance.</item>
      <item>`GITHUB_REPO` — Target repository in `owner/repo` format.</item>
    </secrets>
    <local_development>
      Copy `.env.example` to `.env` and fill in required values. Validate with `pwsh -NoProfile -File ./scripts/validate-env.ps1`.
      Synchronize Python dependencies with `uv sync --all-extras`. Verify environment with `./scripts/verify-python-env.sh`.
    </local_development>
    <devcontainer_cache>
      Image at `ghcr.io/${{ github.repository }}/devcontainer`. `publish-docker.yml` builds the raw Dockerfile;
      `prebuild-devcontainer.yml` layers Features. Login via `docker/login-action` with `GITHUB_TOKEN`.
      Set repo variable `VERSION_PREFIX` (e.g., `1.0`) for versioned tags emitted by both image publishing workflows.
    </devcontainer_cache>
  </environment_setup>

  <testing>
    <guidance>
      The project has two test suites:
      1. **Python tests** (pytest) in `tests/` — unit tests, integration tests, async tests.
      2. **Shell tests** in `test/` — devcontainer build, tool availability, prompt assembly.
    </guidance>
    <commands>
      <command>Python tests: `uv run pytest`</command>
      <command>Python tests with coverage: `uv run pytest --cov=src/os_apow --cov-report=html`</command>
      <command>Python tests verbose: `uv run pytest -v --tb=short`</command>
      <command>Shell tests: `bash test/test-devcontainer-build.sh && bash test/test-devcontainer-tools.sh && bash test/test-prompt-assembly.sh`</command>
      <command>Prompt changes: `bash test/test-prompt-assembly.sh`</command>
      <command>Dockerfile changes: `bash test/test-devcontainer-tools.sh`</command>
    </commands>
    <guidance>Add new fixture payloads to `test/fixtures/` when testing new event types. Add new Python tests to `tests/`.</guidance>
  </testing>

  <coding_conventions>
    <rule>Keep changes minimal and targeted.</rule>
    <rule>Do not hardcode secrets/tokens.</rule>
    <rule>Preserve the `__EVENT_DATA__` placeholder in `orchestrator-agent-prompt.md`.</rule>
    <rule>Keep orchestrator delegation-depth ≤2 and "never write code directly" constraint.</rule>
    <rule>Pin ALL GitHub Actions by full SHA to the latest release — no tag or branch references (`@v4`, `@main`). Format: `uses: owner/action@<full-40-char-SHA> # vX.Y.Z`. The trailing comment with the semver tag is mandatory for human readability. This applies to every `uses:` line in every workflow file, including third-party actions, first-party (`actions/*`), and reusable workflows. Supply-chain attacks via tag mutation are a critical threat — SHA pinning is the only mitigation. When creating or modifying workflows, look up the SHA for the latest release of each action and pin to it.</rule>
    <rule>Never add duplicate top-level `name:`, `on:`, or `jobs:` keys in workflow YAML.</rule>
    <rule>`.opencode/` is checked out by `actions/checkout`; do not COPY it in the Dockerfile.</rule>
    <rule>Dockerfile lives at `.github/.devcontainer/Dockerfile`. Consumer devcontainer uses `"image:"` — no local build.</rule>
    <rule>Repository labels are defined in `.github/.labels.json`. Use `scripts/import-labels.ps1` to sync them to a repo instance. When adding new labels, add them to this file — it is the single source of truth for the label set.</rule>
    <rule>Use `uv` for all Python dependency management: `uv add`, `uv sync --all-extras`, `uv run`.</rule>
    <rule>Format code with `ruff format` before committing. Lint with `ruff check`. Type-check with `mypy`.</rule>
    <rule>Follow the project's ruff config in `pyproject.toml`: target Python 3.12, line-length 100, first-party package `os_apow`.</rule>
    <rule>All Python modules must have proper `__init__.py` files. Source code lives under `src/os_apow/`.</rule>
    <rule>Use strict Pydantic models for all configuration and data interchange (see `src/config/settings.py`, `src/models/work_item.py`).</rule>
    <rule>Never commit `.env` files — they are excluded via `.gitignore`.</rule>
    <rule>The `plan_docs/` directory contains external-generated documents. Exclude it from strict linting.</rule>
  </coding_conventions>

  <agent_specific_guardrails>
    <rule>The Orchestrator agent delegates to specialists via the `task` tool — never writes code directly.</rule>
    <rule>Prompt assembly pipeline:
      1. Read template from `.github/workflows/prompts/orchestrator-agent-prompt.md`.
      2. Prepend structured event context (event name, action, actor, repo, ref, SHA).
      3. Append raw event JSON from `${{ toJson(github.event) }}`.
      4. Write to `.assembled-orchestrator-prompt.md` and export path via `GITHUB_ENV`.
    </rule>
    <rule>Shell-Bridge Protocol: The Sentinel (Brain) interacts with the Worker (Hands) exclusively via `./scripts/devcontainer-opencode.sh`. Commands: `up`, `start`, `prompt`, `stop`, `down`.</rule>
    <rule>Return codes: Exit 0 = Success, Exit 1-10 = Infrastructure Error, Exit 11+ = Logic/Agent Error.</rule>
  </agent_specific_guardrails>

  <agent_readiness>
    <verification_protocol>
      For any non-trivial change (logic, behavior, refactors, dependency updates, config changes, multi-file edits):
      run verification, fix all failures, re-run until clean. Do not skip or suppress errors.
    </verification_protocol>

    <verification_commands>
      <!--
        MANDATORY: After every non-trivial change, run validation BEFORE commit/push.
        Do NOT commit or push until it passes. Do NOT skip steps.

        Local (runs all checks sequentially — lint, scan, test):
          pwsh -NoProfile -File ./scripts/validate.ps1 -All

        This is the SAME script that CI calls with individual switches:
          ./scripts/validate.ps1 -Lint   (CI: lint job)
          ./scripts/validate.ps1 -Scan   (CI: scan job)
          ./scripts/validate.ps1 -Test   (CI: test job)

        If a check is skipped due to a missing local tool, run:
          pwsh -NoProfile -File ./scripts/install-dev-tools.ps1

        Python-specific checks:
          uv run ruff check src/ tests/     # Lint
          uv run ruff format src/ tests/    # Format
          uv run mypy src/                  # Type check
          uv run pytest                     # Tests

        | Check                  | Command                                              | When to run              |
        |========================|======================================================|==========================|
        | All (local default)    | ./scripts/validate.ps1 -All                           | Every task               |
        | Lint only              | ./scripts/validate.ps1 -Lint                           | Quick check              |
        | Scan only              | ./scripts/validate.ps1 -Scan                           | Secrets concern          |
        | Test only              | ./scripts/validate.ps1 -Test                           | After lint passes        |
        | Python lint            | uv run ruff check src/ tests/                          | Python code changes      |
        | Python format          | uv run ruff format src/ tests/                         | Before commit            |
        | Python type check      | uv run mypy src/                                      | Type safety              |
        | Python tests           | uv run pytest                                         | Logic changes            |
        | Devcontainer tests     | bash test/test-devcontainer-tools.sh                   | Dockerfile changes       |
        | Env validation         | ./scripts/validate-env.ps1                             | Config changes           |
        | Python env verify      | ./scripts/verify-python-env.sh                         | Setup / dependency changes|
      -->
      <rule>When adding a CI workflow check, add its equivalent to scripts/validate.ps1.</rule>
    </verification_commands>

    <post_commit_monitoring>
      After push, monitor CI until green: `gh run list --limit 5`, `gh run watch <id>`, `gh run view <id> --log-failed`.
      If any workflow fails, stop feature work, triage, fix, re-verify, push. Do not mark work complete while CI is failing.
    </post_commit_monitoring>

    <pipeline_speed_policy>
      <lane name="fast_readiness" blocking="true">Lint (ruff), format, type check (mypy), unit tests (pytest) — keep fast for merge readiness.</lane>
      <lane name="extended_validation" blocking="false">Integration suites, security scans, dependency audits, devcontainer build.</lane>
      <rule>Protect the fast lane from slow steps.</rule>
    </pipeline_speed_policy>
  </agent_readiness>

  <validation_before_handoff>
    <step>Run `uv run ruff check src/ tests/` and `uv run ruff format --check src/ tests/` — must pass.</step>
    <step>Run `uv run mypy src/` — must pass with no errors.</step>
    <step>Run `uv run pytest` — all tests must pass.</step>
    <step>Run `pwsh -NoProfile -File ./scripts/validate.ps1 -All` — all checks must pass.</step>
    <step>Validate workflow YAML: `grep -c "^name:" .github/workflows/orchestrator-agent.yml  # expect 1`</step>
    <step>Verify Python environment: `./scripts/verify-python-env.sh`</step>
    <step>Summarize: what changed, what was validated, remaining risks (secret-dependent paths, image cache misses).</step>
  </validation_before_handoff>

  <tool_use_instructions>
    <instruction id="sequential_thinking_default_usage">
      <applyTo>*</applyTo>
      <title>Sequential Thinking</title>
      <tools><tool>sequential_thinking</tool></tools>
      <guidance>
        Use for all non-trivial requests. Enables step-by-step analysis with revision, branching, and dynamic adjustment.
        Use when: breaking down complex problems, planning, architectural decisions, debugging, multi-step context.
      </guidance>
    </instruction>
    <instruction id="memory_default_usage">
      <applyTo>*</applyTo>
      <title>Knowledge Graph Memory</title>
      <tools><tool>create_entities</tool><tool>create_relations</tool><tool>add_observations</tool><tool>delete_entities</tool><tool>delete_observations</tool><tool>delete_relations</tool><tool>read_graph</tool><tool>search_nodes</tool><tool>open_nodes</tool></tools>
      <guidance>
        Use for non-trivial requests. Persist user/project context (preferences, configs, decisions, challenges, solutions).
        Entities have names, types, and observations. Relations connect entities. Search/read at task start; update after significant work.
      </guidance>
    </instruction>
  </tool_use_instructions>

  <available_tools>
    <summary>
      Tools available inside the devcontainer at runtime. Installed via
      `.github/.devcontainer/Dockerfile` unless noted otherwise.
    </summary>

    <runtimes_and_package_managers>
      <tool name="python" version="3.12+">`Python` — primary language for all system logic. Managed via uv.</tool>
      <tool name="uv" version="0.10.9">`uv` — Rust-based Python package manager. Provides `uv run`, `uv add`, `uv sync`, `uv lock`.</tool>
      <tool name="node" version="24.14.0 LTS">`Node.js` — JavaScript runtime. Required for MCP server packages (`npx`).</tool>
      <tool name="npm">`npm` — Node package manager (bundled with Node.js).</tool>
      <tool name="bun" version="1.3.10">`Bun` — fast JavaScript/TypeScript runtime, bundler, and package manager.</tool>
    </runtimes_and_package_managers>

    <cli_tools>
      <tool name="gh">`GitHub CLI` — interact with GitHub API (issues, PRs, repos, releases, actions). Authenticated automatically via `GITHUB_TOKEN` env var in CI; use `gh auth login --with-token` otherwise.</tool>
      <tool name="opencode" version="1.2.24">`opencode CLI` — AI agent runtime. Runs agents defined in `.opencode/agents/` with MCP server support.</tool>
      <tool name="git">`Git` — version control (system package + devcontainer feature).</tool>
      <tool name="docker">`Docker` — container runtime for worker sandboxing and devcontainer management.</tool>
    </cli_tools>

    <python_tools>
      <tool name="pytest">`pytest` — testing framework with async support (`pytest-asyncio`) and coverage (`pytest-cov`).</tool>
      <tool name="ruff">`ruff` — fast Python linter and formatter (replaces flake8, isort, black).</tool>
      <tool name="mypy">`mypy` — static type checker in strict mode with Pydantic plugin.</tool>
    </python_tools>

    <github_authentication>
      <summary>
        GitHub API access is configured at multiple layers to support both `gh` CLI and MCP GitHub server operations.
      </summary>
      <layer name="GITHUB_TOKEN">Provided automatically by GitHub Actions. Passed into the devcontainer via `--remote-env`.</layer>
      <layer name="GITHUB_PERSONAL_ACCESS_TOKEN">Bridged from `GITHUB_TOKEN` for the `@modelcontextprotocol/server-github` MCP server, which requires this specific env var name. Set in `opencode.json` via the MCP `env` block, in `devcontainer.json` `remoteEnv`, and exported in `run_opencode_prompt.sh`.</layer>
      <layer name="gh auth login">`run_opencode_prompt.sh` authenticates the `gh` CLI via `echo "$GITHUB_TOKEN" | gh auth login --with-token` before launching opencode.</layer>
    </github_authentication>

    <scripts_directory>
      <summary>PowerShell and Bash helper scripts in `scripts/` for setup, validation, and management tasks.</summary>
      <script name="scripts/common-auth.ps1">Shared `Initialize-GitHubAuth` function — checks `gh auth status`, authenticates via PAT token (`$env:GITHUB_AUTH_TOKEN`) or interactive login.</script>
      <script name="scripts/gh-auth.ps1">Extended GitHub auth helper — supports PAT token auth via `--with-token` and interactive fallback.</script>
      <script name="scripts/import-labels.ps1">Imports labels from `.github/.labels.json` into the repository.</script>
      <script name="scripts/create-milestones.ps1">Creates project milestones from plan docs.</script>
      <script name="scripts/test-github-permissions.ps1">Verifies `GITHUB_TOKEN` has required permissions (contents, issues, PRs, packages).</script>
      <script name="scripts/query.ps1">PR review thread manager — fetches unresolved review threads from a PR, summarizes them, and can batch-reply and resolve them. Supports `--AutoResolve`, `--DryRun`, `--Interactive`, `--ReplyEach`, `--Path`, `--BodyContains` filtering.</script>
      <script name="scripts/update-remote-indices.ps1">Updates remote instruction module indices.</script>
      <script name="scripts/validate.ps1">Main validation script — runs lint, scan, and test checks. Called by CI with individual switches (`-Lint`, `-Scan`, `-Test`) or locally with `-All`.</script>
      <script name="scripts/validate-env.ps1">Validates `.env` file for required variables and rejects placeholder values.</script>
      <script name="scripts/verify-python-env.sh">Verifies Python environment: version, uv, venv, core imports, tool versions.</script>
      <script name="scripts/install-dev-tools.ps1">Installs development tools needed for validation.</script>
      <script name="scripts/devcontainer-opencode.sh">CLI wrapper around devcontainer for the opencode server. The Sentinel's Shell-Bridge Protocol.</script>
      <script name="scripts/start-opencode-server.sh">Guarded `opencode serve` bootstrapper for devcontainer lifecycle.</script>
    </scripts_directory>
  </available_tools>
</instructions>
