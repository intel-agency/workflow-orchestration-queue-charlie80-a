"""Shared models and utilities for work items.

This module provides:
- WorkItem: Data model for work items in the orchestration queue
- scrub_secrets: Utility function to redact secrets from strings/dicts
"""

import re
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


# All secret variable patterns that should be scrubbed from logs/output
SECRET_PATTERNS: Set[str] = {
    # Authentication tokens
    "GITHUB_TOKEN",
    "GITHUB_PERSONAL_ACCESS_TOKEN",
    "WEBHOOK_SECRET",
    # API Keys
    "ZHIPU_API_KEY",
    "KIMI_CODE_ORCHESTRATOR_AGENT_API_KEY",
    # Additional patterns that may appear in secrets
    "API_KEY",
    "SECRET_KEY",
    "ACCESS_TOKEN",
    "AUTH_TOKEN",
    "PRIVATE_KEY",
    "PASSWORD",
}

# Regex patterns for detecting secret-like values
SECRET_VALUE_PATTERNS = [
    # GitHub tokens (ghp_, gho_, ghu_, ghs_, ghr_)
    re.compile(r"(ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{36,255}", re.IGNORECASE),
    # Generic API keys (typically 32-64 hex or base64 chars)
    re.compile(r"\b[A-Za-z0-9]{32,64}\b"),
    # JWT-like tokens
    re.compile(r"eyJ[A-Za-z0-9_-]*\.eyJ[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*"),
    # Connection strings with passwords
    re.compile(r"(?i)(password|pwd|pass)\s*[=:]\s*\S+"),
    # URL with credentials
    re.compile(r"//[^\s:]+:[^\s@]+@"),
]


class WorkItemStatus(str, Enum):
    """Status of a work item in the orchestration queue."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkItemPriority(str, Enum):
    """Priority level for work items."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class WorkItem:
    """Represents a work item in the orchestration queue.

    Work items are created from GitHub events and dispatched to
    appropriate agents for processing.

    Attributes:
        id: Unique identifier for this work item
        source: Source of the work item (e.g., "github_issue", "webhook")
        event_type: Type of event that created this item
        payload: Raw event data (will be scrubbed before logging)
        status: Current status of the work item
        priority: Priority level for processing
        created_at: When the item was created
        updated_at: When the item was last updated
        assigned_agent: Agent assigned to process this item
        metadata: Additional metadata about the work item
    """

    id: str
    source: str
    event_type: str
    payload: Dict[str, Any]
    status: WorkItemStatus = WorkItemStatus.PENDING
    priority: WorkItemPriority = WorkItemPriority.NORMAL
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    assigned_agent: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self, scrub: bool = True) -> Dict[str, Any]:
        """Convert work item to dictionary.

        Args:
            scrub: If True, redact secrets from the output.

        Returns:
            Dictionary representation of the work item.
        """
        data = {
            "id": self.id,
            "source": self.source,
            "event_type": self.event_type,
            "payload": self.payload,
            "status": self.status.value,
            "priority": self.priority.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "assigned_agent": self.assigned_agent,
            "metadata": self.metadata,
        }

        if scrub:
            return scrub_secrets(data)
        return data

    def to_safe_string(self) -> str:
        """Get a string representation safe for logging.

        Returns:
            String representation with secrets redacted.
        """
        safe_data = self.to_dict(scrub=True)
        return (
            f"WorkItem(id={safe_data['id']}, "
            f"source={safe_data['source']}, "
            f"event_type={safe_data['event_type']}, "
            f"status={safe_data['status']}, "
            f"priority={safe_data['priority']})"
        )


def scrub_secrets(data: Any, replacement: str = "[REDACTED]") -> Any:
    """Recursively scrub secrets from data structures.

    This function traverses dictionaries, lists, and strings to find
    and redact secret values. It checks:
    - Dictionary keys matching SECRET_PATTERNS
    - String values matching secret-like patterns (tokens, API keys)
    - Nested structures recursively

    Args:
        data: The data to scrub (dict, list, string, or other)
        replacement: String to replace secrets with

    Returns:
        Data with secrets redacted. Original data is not modified.

    Examples:
        >>> scrub_secrets({"token": "secret123", "name": "public"})
        {'token': '[REDACTED]', 'name': 'public'}

        >>> scrub_secrets("Token: ghp_abc123...")
        'Token: [REDACTED]'
    """
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            # Check if key matches a secret pattern
            key_upper = key.upper()
            is_secret_key = any(
                pattern in key_upper or key_upper in pattern
                for pattern in SECRET_PATTERNS
            )

            if is_secret_key:
                result[key] = replacement
            else:
                result[key] = scrub_secrets(value, replacement)
        return result

    elif isinstance(data, list):
        return [scrub_secrets(item, replacement) for item in data]

    elif isinstance(data, str):
        result = data
        # Apply regex patterns to detect secret-like values
        for pattern in SECRET_VALUE_PATTERNS:
            result = pattern.sub(replacement, result)
        return result

    else:
        # Return other types as-is (int, float, bool, None, etc.)
        return data


def is_secret_key(key: str) -> bool:
    """Check if a key name likely contains a secret.

    Args:
        key: The key name to check

    Returns:
        True if the key appears to be a secret, False otherwise.
    """
    key_upper = key.upper()
    return any(
        pattern in key_upper or key_upper in pattern for pattern in SECRET_PATTERNS
    )
