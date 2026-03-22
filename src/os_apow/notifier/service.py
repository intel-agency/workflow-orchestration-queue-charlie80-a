"""
OS-APOW Work Event Notifier (The "Ear")

A FastAPI-based webhook receiver that maps provider events (GitHub, etc.)
to a unified Work Item queue. This is the entry point for event-driven
intake of work items.
"""

import hashlib
import hmac
import logging
import sys
from typing import Annotated, Any

from fastapi import Depends, FastAPI, Header, HTTPException, Request

from os_apow.config import Config
from os_apow.models.work_item import (
    TaskType,
    WorkItem,
    WorkItemStatus,
)
from os_apow.queue.github_queue import GitHubQueue, ITaskQueue

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("OS-APOW-Notifier")

# --- Configuration ---

_config = Config.from_env()

# Validate configuration at startup
_missing_notifier = _config.validate_notifier()
if _missing_notifier:
    logger.warning(
        f"Missing configuration for notifier: {', '.join(_missing_notifier)}. "
        "Some features may not work."
    )

# --- Application Factory ---


def create_app(config: Config | None = None) -> FastAPI:
    """Create and configure the FastAPI application.

    Args:
        config: Optional configuration override. Uses environment if not provided.

    Returns:
        Configured FastAPI application instance.
    """
    app_config = config or _config

    app = FastAPI(
        title="OS-APOW Event Notifier",
        description="Webhook receiver for OS-APOW agentic orchestration",
        version="0.1.0",
    )

    # Store config in app state
    app.state.config = app_config

    return app


# --- Default App Instance ---

app = create_app(_config)


# --- Dependencies ---


def get_queue() -> ITaskQueue:
    """Dependency injection for the queue implementation.

    Phase 1: GitHub. Can be swapped for Linear, Jira, etc.
    """
    return GitHubQueue(token=_config.github_token)


async def verify_signature(
    request: Request,
    x_hub_signature_256: Annotated[str | None, Header()] = None,
) -> None:
    """Verify GitHub webhook signature.

    Args:
        request: The incoming request.
        x_hub_signature_256: The X-Hub-Signature-256 header.

    Raises:
        HTTPException: If signature is missing or invalid.
    """
    if not x_hub_signature_256:
        raise HTTPException(status_code=401, detail="X-Hub-Signature-256 missing")

    if not _config.webhook_secret:
        raise HTTPException(status_code=500, detail="Webhook secret not configured")

    body = await request.body()
    signature = (
        "sha256=" + hmac.new(_config.webhook_secret.encode(), body, hashlib.sha256).hexdigest()
    )

    if not hmac.compare_digest(signature, x_hub_signature_256):
        raise HTTPException(status_code=401, detail="Invalid signature")


# --- Endpoints ---


@app.post("/webhooks/github", dependencies=[Depends(verify_signature)])
async def handle_github_webhook(
    request: Request,
    queue: Annotated[ITaskQueue, Depends(get_queue)],
) -> dict[str, Any]:
    """Handle incoming GitHub webhook events.

    Processes issue events and queues work items for agent processing.

    Args:
        request: The incoming request.
        queue: The task queue dependency.

    Returns:
        Response indicating whether the event was processed.
    """
    payload = await request.json()
    event_type = request.headers.get("X-GitHub-Event")

    if event_type == "issues" and payload.get("action") == "opened":
        issue = payload["issue"]
        labels = [label["name"] for label in issue.get("labels", [])]

        # Detect intent from title or labels
        if "[Application Plan]" in issue["title"] or "agent:plan" in labels:
            work_item = WorkItem(
                id=str(issue["id"]),
                issue_number=issue["number"],
                source_url=issue["html_url"],
                target_repo_slug=payload["repository"]["full_name"],
                task_type=TaskType.PLAN,
                context_body=issue.get("body") or "",
                status=WorkItemStatus.QUEUED,
                node_id=issue["node_id"],
            )
            await queue.add_to_queue(work_item)
            return {"status": "accepted", "item_id": work_item.id}

        # Add more event type mappings as needed

    return {"status": "ignored", "reason": "No actionable OS-APOW event mapping found"}


@app.get("/health")
def health_check() -> dict[str, str]:
    """Health check endpoint.

    Returns:
        Health status response.
    """
    return {"status": "online", "system": "OS-APOW Notifier"}


@app.get("/")
def root() -> dict[str, str]:
    """Root endpoint.

    Returns:
        Basic service information.
    """
    return {
        "service": "OS-APOW Notifier",
        "version": "0.1.0",
        "docs": "/docs",
    }
