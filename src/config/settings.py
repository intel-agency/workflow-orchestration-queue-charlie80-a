"""Pydantic settings classes for environment configuration.

This module defines all environment variables used by the workflow orchestration
system, organized into logical groups:
- SentinelSettings: Configuration for the Sentinel (polling) service
- NotifierSettings: Configuration for the Notifier (webhook) service
- SharedSettings: Common configuration shared across services
- AppSettings: Combined application settings

All settings use Pydantic's BaseSettings for automatic environment variable
loading and validation.
"""

from typing import Optional
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# Placeholder values that should be rejected
PLACEHOLDER_VALUES = frozenset(
    [
        "YOUR_VALUE_HERE",
        "YOUR_TOKEN_HERE",
        "YOUR_SECRET_HERE",
        "YOUR_API_KEY_HERE",
        "<YOUR_VALUE>",
        "<YOUR_TOKEN>",
        "<PLACEHOLDER>",
        "changeme",
        "placeholder",
        "xxx",
    ]
)


def _is_placeholder(value: str) -> bool:
    """Check if a value is a placeholder that should be rejected."""
    if not value:
        return True
    return (
        value.strip() in PLACEHOLDER_VALUES
        or value.strip().upper() in PLACEHOLDER_VALUES
    )


class SentinelSettings(BaseSettings):
    """Configuration for the Sentinel (polling) service.

    The Sentinel service polls GitHub for new events and dispatches
    work items to the orchestration queue.

    Environment Variables:
        GITHUB_REPO: Target repository in 'owner/repo' format (required)
        SENTINEL_BOT_LOGIN: GitHub login of the sentinel bot account (required)
        SENTINEL_ID: Unique identifier for this sentinel instance (required)
        POLL_INTERVAL: Seconds between polling cycles (default: 60)
        MAX_BACKOFF: Maximum backoff seconds on errors (default: 300)
        SENTINEL_HEARTBEAT_INTERVAL: Seconds between heartbeat checks (default: 300)
        SUBPROCESS_TIMEOUT: Timeout for subprocess operations (default: 1800)
        DAILY_BUDGET_LIMIT: Daily API budget limit in USD (default: 10.0)
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Required settings
    github_repo: str = Field(
        ...,
        alias="GITHUB_REPO",
        description="Target repository in 'owner/repo' format",
        examples=["intel-agency/workflow-orchestration-queue-charlie80-a"],
    )
    bot_login: str = Field(
        ...,
        alias="SENTINEL_BOT_LOGIN",
        description="GitHub login of the sentinel bot account",
        examples=["sentinel-bot[bot]"],
    )
    sentinel_id: str = Field(
        ...,
        alias="SENTINEL_ID",
        description="Unique identifier for this sentinel instance",
        examples=["sentinel-001", "prod-sentinel-primary"],
    )

    # Optional settings with defaults
    poll_interval: int = Field(
        default=60,
        ge=1,
        le=3600,
        alias="POLL_INTERVAL",
        description="Seconds between polling cycles",
    )
    max_backoff: int = Field(
        default=300,
        ge=10,
        le=3600,
        alias="MAX_BACKOFF",
        description="Maximum backoff seconds on errors",
    )
    heartbeat_interval: int = Field(
        default=300,
        ge=60,
        le=3600,
        alias="SENTINEL_HEARTBEAT_INTERVAL",
        description="Seconds between heartbeat checks",
    )
    subprocess_timeout: int = Field(
        default=1800,
        ge=60,
        le=7200,
        alias="SUBPROCESS_TIMEOUT",
        description="Timeout for subprocess operations in seconds",
    )
    daily_budget_limit: float = Field(
        default=10.0,
        ge=0.0,
        le=1000.0,
        alias="DAILY_BUDGET_LIMIT",
        description="Daily API budget limit in USD",
    )

    @field_validator("github_repo", "bot_login", "sentinel_id")
    @classmethod
    def reject_placeholders(cls, v: str) -> str:
        """Reject placeholder values for required fields."""
        if _is_placeholder(v):
            raise ValueError(
                f"Value appears to be a placeholder. "
                f"Please provide a real value instead of '{v}'"
            )
        return v

    @field_validator("github_repo")
    @classmethod
    def validate_repo_format(cls, v: str) -> str:
        """Validate repository format is 'owner/repo'."""
        if "/" not in v or v.count("/") != 1:
            raise ValueError(f"Repository must be in 'owner/repo' format, got '{v}'")
        parts = v.split("/")
        if not all(parts):
            raise ValueError(f"Repository must be in 'owner/repo' format, got '{v}'")
        return v


class NotifierSettings(BaseSettings):
    """Configuration for the Notifier (webhook) service.

    The Notifier service listens for GitHub webhooks and forwards
    events to the orchestration system.

    Environment Variables:
        WEBHOOK_SECRET: Secret for validating webhook payloads (required)
        GITHUB_WEBHOOK_PORT: Port for webhook listener (default: 8080)
        GITHUB_APP_ID: GitHub App ID for authentication (optional)
    """

    model_config = SettingsConfigDict(
        env_prefix="",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Required settings
    webhook_secret: str = Field(
        ...,
        alias="WEBHOOK_SECRET",
        min_length=16,
        description="Secret for validating webhook payloads (min 16 chars)",
    )

    # Optional settings with defaults
    github_webhook_port: int = Field(
        default=8080,
        ge=1024,
        le=65535,
        alias="GITHUB_WEBHOOK_PORT",
        description="Port for webhook listener",
    )

    # Optional authentication
    github_app_id: Optional[str] = Field(
        default=None,
        alias="GITHUB_APP_ID",
        description="GitHub App ID for authentication",
    )

    @field_validator("webhook_secret")
    @classmethod
    def reject_placeholder_secret(cls, v: str) -> str:
        """Reject placeholder values for webhook secret."""
        if _is_placeholder(v):
            raise ValueError(
                f"WEBHOOK_SECRET appears to be a placeholder. "
                f"Please generate a secure secret."
            )
        return v


class SharedSettings(BaseSettings):
    """Shared configuration used across all services.

    These settings are required by all services for authentication
    and API access.

    Environment Variables:
        GITHUB_TOKEN: GitHub API token (required)
        GITHUB_PERSONAL_ACCESS_TOKEN: GitHub PAT for MCP server (optional)
        ZHIPU_API_KEY: ZhipuAI API key for GLM models (required)
        KIMI_CODE_ORCHESTRATOR_AGENT_API_KEY: Kimi/Moonshot API key (optional)
    """

    model_config = SettingsConfigDict(
        env_prefix="",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Required authentication
    github_token: str = Field(
        ...,
        alias="GITHUB_TOKEN",
        description="GitHub API token for repository access",
    )
    zhipu_api_key: str = Field(
        ...,
        alias="ZHIPU_API_KEY",
        description="ZhipuAI API key for GLM model access",
    )

    # Optional authentication
    github_personal_access_token: Optional[str] = Field(
        default=None,
        alias="GITHUB_PERSONAL_ACCESS_TOKEN",
        description="GitHub PAT for MCP GitHub server (uses GITHUB_TOKEN if not set)",
    )
    kimi_api_key: Optional[str] = Field(
        default=None,
        alias="KIMI_CODE_ORCHESTRATOR_AGENT_API_KEY",
        description="Kimi/Moonshot API key for alternative model access",
    )

    @field_validator("github_token", "zhipu_api_key")
    @classmethod
    def reject_placeholder_tokens(cls, v: str) -> str:
        """Reject placeholder values for required tokens."""
        if _is_placeholder(v):
            raise ValueError(
                f"API key/token appears to be a placeholder. "
                f"Please provide a real value."
            )
        return v

    @model_validator(mode="after")
    def set_default_pat(self) -> "SharedSettings":
        """Use GITHUB_TOKEN as default for GITHUB_PERSONAL_ACCESS_TOKEN."""
        if self.github_personal_access_token is None:
            self.github_personal_access_token = self.github_token
        return self


class AppSettings(BaseSettings):
    """Combined application settings for all services.

    This class aggregates all settings groups and provides a single
    entry point for configuration validation at application startup.

    Environment Variables:
        All variables from SentinelSettings, NotifierSettings, and SharedSettings
        LOG_LEVEL: Logging level (default: INFO)
        ENVIRONMENT: Deployment environment (default: development)
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Nested settings groups
    sentinel: SentinelSettings = Field(default_factory=SentinelSettings)
    notifier: NotifierSettings = Field(default_factory=NotifierSettings)
    shared: SharedSettings = Field(default_factory=SharedSettings)

    # Application-level settings
    log_level: str = Field(
        default="INFO",
        alias="LOG_LEVEL",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )
    environment: str = Field(
        default="development",
        alias="ENVIRONMENT",
        description="Deployment environment (development, staging, production)",
    )

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is a known value."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of {valid_levels}, got '{v}'")
        return v_upper

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment is a known value."""
        valid_envs = {"development", "staging", "production", "test"}
        v_lower = v.lower()
        if v_lower not in valid_envs:
            raise ValueError(f"ENVIRONMENT must be one of {valid_envs}, got '{v}'")
        return v_lower

    @classmethod
    def load(cls) -> "AppSettings":
        """Load and validate all settings from environment.

        This method should be called at application startup to ensure
        all required configuration is present and valid.

        Raises:
            ValidationError: If any required settings are missing or invalid.

        Returns:
            AppSettings: Validated application settings.
        """
        try:
            return cls()
        except Exception as e:
            from .validation import ValidationError

            raise ValidationError(f"Configuration validation failed: {e}") from e
