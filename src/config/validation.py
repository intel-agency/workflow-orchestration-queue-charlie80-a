"""Environment validation utilities.

This module provides utilities for validating environment configuration
at startup and for manual verification.
"""

import os
import sys
from typing import List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class ValidationError(Exception):
    """Raised when environment validation fails.

    Attributes:
        message: Human-readable error message
        missing_vars: List of missing required variables
        invalid_vars: List of variables with invalid values
    """

    message: str
    missing_vars: Optional[List[str]] = None
    invalid_vars: Optional[List[Tuple[str, str]]] = None

    def __post_init__(self):
        if self.missing_vars is None:
            self.missing_vars = []
        if self.invalid_vars is None:
            self.invalid_vars = []

    def __str__(self) -> str:
        parts = [self.message]
        if self.missing_vars:
            parts.append(f"Missing variables: {', '.join(self.missing_vars)}")
        if self.invalid_vars:
            invalid_str = ", ".join(f"{k}={v}" for k, v in self.invalid_vars)
            parts.append(f"Invalid values: {invalid_str}")
        return "\n".join(parts)


# Placeholder values to reject
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


# Required environment variables by service
REQUIRED_VARS = {
    "shared": [
        "GITHUB_TOKEN",
        "ZHIPU_API_KEY",
    ],
    "sentinel": [
        "GITHUB_REPO",
        "SENTINEL_BOT_LOGIN",
        "SENTINEL_ID",
    ],
    "notifier": [
        "WEBHOOK_SECRET",
    ],
}

# Optional environment variables with defaults
OPTIONAL_VARS = {
    "shared": [
        ("GITHUB_PERSONAL_ACCESS_TOKEN", None),  # Falls back to GITHUB_TOKEN
        ("KIMI_CODE_ORCHESTRATOR_AGENT_API_KEY", None),
    ],
    "sentinel": [
        ("POLL_INTERVAL", "60"),
        ("MAX_BACKOFF", "300"),
        ("SENTINEL_HEARTBEAT_INTERVAL", "300"),
        ("SUBPROCESS_TIMEOUT", "1800"),
        ("DAILY_BUDGET_LIMIT", "10.0"),
    ],
    "notifier": [
        ("GITHUB_WEBHOOK_PORT", "8080"),
        ("GITHUB_APP_ID", None),
    ],
    "app": [
        ("LOG_LEVEL", "INFO"),
        ("ENVIRONMENT", "development"),
    ],
}

# Secret variable patterns (for scrub_secrets)
SECRET_PATTERNS = frozenset(
    [
        "GITHUB_TOKEN",
        "GITHUB_PERSONAL_ACCESS_TOKEN",
        "ZHIPU_API_KEY",
        "KIMI_CODE_ORCHESTRATOR_AGENT_API_KEY",
        "WEBHOOK_SECRET",
    ]
)


def is_placeholder(value: str) -> bool:
    """Check if a value is a placeholder that should be rejected."""
    if not value:
        return True
    stripped = value.strip()
    return stripped in PLACEHOLDER_VALUES or stripped.upper() in PLACEHOLDER_VALUES


def validate_required_vars() -> Tuple[List[str], List[Tuple[str, str]]]:
    """Validate that all required environment variables are set.

    Returns:
        Tuple of (missing_vars, invalid_vars)
    """
    missing = []
    invalid = []

    for service, vars in REQUIRED_VARS.items():
        for var in vars:
            value = os.environ.get(var)
            if value is None:
                missing.append(var)
            elif is_placeholder(value):
                invalid.append((var, value))

    return missing, invalid


def validate_var_format(var: str, value: str) -> Optional[str]:
    """Validate the format of a specific variable.

    Returns:
        Error message if invalid, None if valid.
    """
    if var == "GITHUB_REPO":
        if "/" not in value or value.count("/") != 1:
            return f"Must be in 'owner/repo' format, got '{value}'"
        parts = value.split("/")
        if not all(parts):
            return f"Must be in 'owner/repo' format, got '{value}'"

    elif var == "GITHUB_WEBHOOK_PORT":
        try:
            port = int(value)
            if not (1024 <= port <= 65535):
                return f"Port must be between 1024 and 65535, got {port}"
        except ValueError:
            return f"Must be a valid integer, got '{value}'"

    elif var == "POLL_INTERVAL":
        try:
            interval = int(value)
            if not (1 <= interval <= 3600):
                return f"Poll interval must be between 1 and 3600, got {interval}"
        except ValueError:
            return f"Must be a valid integer, got '{value}'"

    elif var == "LOG_LEVEL":
        valid = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if value.upper() not in valid:
            return f"Must be one of {valid}, got '{value}'"

    elif var == "ENVIRONMENT":
        valid = {"development", "staging", "production", "test"}
        if value.lower() not in valid:
            return f"Must be one of {valid}, got '{value}'"

    elif var == "WEBHOOK_SECRET":
        if len(value) < 16:
            return f"Must be at least 16 characters, got {len(value)}"

    return None


def validate_environment(strict: bool = True) -> bool:
    """Validate all environment configuration.

    Args:
        strict: If True, raise ValidationError on failure.
                If False, print warnings and return False.

    Returns:
        True if validation passes, False otherwise.

    Raises:
        ValidationError: If strict=True and validation fails.
    """
    missing, invalid = validate_required_vars()
    format_errors = []

    # Check format of all set variables
    for service, vars in REQUIRED_VARS.items():
        for var in vars:
            value = os.environ.get(var)
            if value and not is_placeholder(value):
                error = validate_var_format(var, value)
                if error:
                    format_errors.append((var, error))

    # Check optional variables that are set
    for service, vars in OPTIONAL_VARS.items():
        for var, _ in vars:
            value = os.environ.get(var)
            if value and not is_placeholder(value):
                error = validate_var_format(var, value)
                if error:
                    format_errors.append((var, error))

    # Combine all errors
    all_invalid = invalid + format_errors

    if missing or all_invalid:
        error = ValidationError(
            message="Environment validation failed",
            missing_vars=missing,
            invalid_vars=all_invalid,
        )
        if strict:
            raise error
        else:
            print(str(error), file=sys.stderr)
            return False

    return True


def get_validation_report() -> str:
    """Generate a human-readable validation report.

    Returns:
        Multi-line string with validation status for all variables.
    """
    lines = ["Environment Configuration Validation Report", "=" * 50]

    # Required variables
    lines.append("\nRequired Variables:")
    for service, vars in REQUIRED_VARS.items():
        lines.append(f"\n  [{service.upper()}]")
        for var in vars:
            value = os.environ.get(var)
            if value is None:
                status = "❌ MISSING"
            elif is_placeholder(value):
                status = "❌ PLACEHOLDER"
            else:
                error = validate_var_format(var, value)
                if error:
                    status = f"❌ INVALID: {error}"
                else:
                    # Mask secret values
                    if var in SECRET_PATTERNS:
                        status = "✅ SET (hidden)"
                    else:
                        status = f"✅ '{value}'"
            lines.append(f"    {var}: {status}")

    # Optional variables
    lines.append("\n\nOptional Variables:")
    for service, vars in OPTIONAL_VARS.items():
        lines.append(f"\n  [{service.upper()}]")
        for var, default in vars:
            value = os.environ.get(var)
            if value is None:
                status = f"⚪ not set (default: {default})"
            elif is_placeholder(value):
                status = "❌ PLACEHOLDER"
            else:
                error = validate_var_format(var, value)
                if error:
                    status = f"❌ INVALID: {error}"
                else:
                    if var in SECRET_PATTERNS:
                        status = "✅ SET (hidden)"
                    else:
                        status = f"✅ '{value}'"
            lines.append(f"    {var}: {status}")

    return "\n".join(lines)


def check_env_file_exists() -> bool:
    """Check if .env file exists in the current directory.

    Returns:
        True if .env exists, False otherwise.
    """
    return os.path.isfile(".env")


def check_gitignore() -> bool:
    """Check if .env is in .gitignore.

    Returns:
        True if .env is properly ignored, False otherwise.
    """
    gitignore_path = ".gitignore"
    if not os.path.isfile(gitignore_path):
        return False

    with open(gitignore_path, "r") as f:
        content = f.read()

    # Check for various .env patterns in gitignore
    patterns = [".env", "*.env", ".env*"]
    return any(pattern in content for pattern in patterns)


if __name__ == "__main__":
    # Run validation when called directly
    print(get_validation_report())
    print("\n" + "=" * 50)

    if check_env_file_exists():
        print("✅ .env file exists")
    else:
        print("⚠️  .env file not found (copy from .env.example)")

    if check_gitignore():
        print("✅ .env is in .gitignore")
    else:
        print("❌ .env is NOT in .gitignore - add it to prevent secret leaks!")

    print("\n" + "=" * 50)
    try:
        validate_environment(strict=True)
        print("✅ All validations passed!")
    except ValidationError as e:
        print(f"❌ Validation failed:\n{e}")
        sys.exit(1)
