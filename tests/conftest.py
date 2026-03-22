"""Test configuration and fixtures for OS-APOW."""

import pytest

from os_apow.config import Config
from os_apow.models.work_item import TaskType, WorkItem, WorkItemStatus


@pytest.fixture
def sample_work_item() -> WorkItem:
    """Create a sample work item for testing."""
    return WorkItem(
        id="12345",
        issue_number=42,
        source_url="https://github.com/test-org/test-repo/issues/42",
        context_body="Sample issue body",
        target_repo_slug="test-org/test-repo",
        task_type=TaskType.IMPLEMENT,
        status=WorkItemStatus.QUEUED,
        node_id="I_kwDOtest123",
    )


@pytest.fixture
def test_config() -> Config:
    """Create a test configuration."""
    return Config(
        github_token="test_token",
        github_org="test-org",
        github_repo="test-repo",
        sentinel_bot_login="test-bot",
        webhook_secret="test_secret",
    )
