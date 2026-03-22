"""
OS-APOW Configuration Management

Centralized configuration using environment variables with validation.
"""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    """Application configuration loaded from environment variables."""

    # GitHub Configuration
    github_token: str
    github_org: str
    github_repo: str
    sentinel_bot_login: str = ""

    # Webhook Configuration
    webhook_secret: str = ""

    # Sentinel Configuration
    poll_interval: int = 60  # seconds
    max_backoff: int = 960  # 16 minutes
    heartbeat_interval: int = 300  # 5 minutes
    subprocess_timeout: int = 5700  # 95 minutes

    # Shell Bridge
    shell_bridge_path: str = "./scripts/devcontainer-opencode.sh"

    # Server Configuration
    notifier_host: str = "0.0.0.0"
    notifier_port: int = 8000

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        return cls(
            github_token=os.getenv("GITHUB_TOKEN", ""),
            github_org=os.getenv("GITHUB_ORG", ""),
            github_repo=os.getenv("GITHUB_REPO", ""),
            sentinel_bot_login=os.getenv("SENTINEL_BOT_LOGIN", ""),
            webhook_secret=os.getenv("WEBHOOK_SECRET", ""),
            poll_interval=int(os.getenv("POLL_INTERVAL", "60")),
            max_backoff=int(os.getenv("MAX_BACKOFF", "960")),
            heartbeat_interval=int(os.getenv("HEARTBEAT_INTERVAL", "300")),
            subprocess_timeout=int(os.getenv("SUBPROCESS_TIMEOUT", "5700")),
            shell_bridge_path=os.getenv("SHELL_BRIDGE_PATH", "./scripts/devcontainer-opencode.sh"),
            notifier_host=os.getenv("NOTIFIER_HOST", "0.0.0.0"),
            notifier_port=int(os.getenv("NOTIFIER_PORT", "8000")),
        )

    def validate_sentinel(self) -> list[str]:
        """Validate configuration for sentinel operation."""
        missing = []
        if not self.github_token:
            missing.append("GITHUB_TOKEN")
        if not self.github_org:
            missing.append("GITHUB_ORG")
        if not self.github_repo:
            missing.append("GITHUB_REPO")
        return missing

    def validate_notifier(self) -> list[str]:
        """Validate configuration for notifier operation."""
        missing = []
        if not self.github_token:
            missing.append("GITHUB_TOKEN")
        if not self.webhook_secret:
            missing.append("WEBHOOK_SECRET")
        return missing
