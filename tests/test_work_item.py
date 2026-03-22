"""Tests for the Work Item model."""

from os_apow.models.work_item import (
    TaskType,
    WorkItem,
    WorkItemStatus,
    scrub_secrets,
)


class TestTaskType:
    """Tests for TaskType enum."""

    def test_task_type_values(self) -> None:
        """Test that TaskType has expected values."""
        assert TaskType.PLAN.value == "PLAN"
        assert TaskType.IMPLEMENT.value == "IMPLEMENT"
        assert TaskType.BUGFIX.value == "BUGFIX"


class TestWorkItemStatus:
    """Tests for WorkItemStatus enum."""

    def test_status_values(self) -> None:
        """Test that WorkItemStatus has expected values."""
        assert WorkItemStatus.QUEUED.value == "agent:queued"
        assert WorkItemStatus.IN_PROGRESS.value == "agent:in-progress"
        assert WorkItemStatus.SUCCESS.value == "agent:success"
        assert WorkItemStatus.ERROR.value == "agent:error"
        assert WorkItemStatus.INFRA_FAILURE.value == "agent:infra-failure"


class TestWorkItem:
    """Tests for WorkItem model."""

    def test_work_item_creation(self, sample_work_item: WorkItem) -> None:
        """Test that a work item can be created."""
        assert sample_work_item.id == "12345"
        assert sample_work_item.issue_number == 42
        assert sample_work_item.task_type == TaskType.IMPLEMENT
        assert sample_work_item.status == WorkItemStatus.QUEUED

    def test_work_item_from_dict(self) -> None:
        """Test creating a work item from a dictionary."""
        data = {
            "id": "99999",
            "issue_number": 1,
            "source_url": "https://github.com/org/repo/issues/1",
            "context_body": "Test body",
            "target_repo_slug": "org/repo",
            "task_type": TaskType.PLAN,
            "status": WorkItemStatus.QUEUED,
            "node_id": "node123",
        }
        item = WorkItem(**data)
        assert item.id == "99999"
        assert item.task_type == TaskType.PLAN


class TestScrubSecrets:
    """Tests for the scrub_secrets function."""

    def test_scrub_github_pat(self) -> None:
        """Test that GitHub PATs are scrubbed."""
        text = "Token: ghp_1234567890abcdefghijklmnopqrstuvwxyz1234"
        result = scrub_secrets(text)
        assert "ghp_" not in result
        assert "***REDACTED***" in result

    def test_scrub_bearer_token(self) -> None:
        """Test that Bearer tokens are scrubbed."""
        text = "Authorization: Bearer abc123def456ghi789jkl012mno345pqr678"
        result = scrub_secrets(text)
        assert "Bearer abc" not in result
        assert "***REDACTED***" in result

    def test_scrub_openai_key(self) -> None:
        """Test that OpenAI-style keys are scrubbed."""
        text = "API Key: sk-1234567890abcdefghijklmnopqrst"
        result = scrub_secrets(text)
        assert "sk-" not in result
        assert "***REDACTED***" in result

    def test_scrub_no_secrets(self) -> None:
        """Test that text without secrets is unchanged."""
        text = "This is a normal log message with no secrets."
        result = scrub_secrets(text)
        assert result == text

    def test_scrub_custom_replacement(self) -> None:
        """Test custom replacement string."""
        text = "Token: ghp_1234567890abcdefghijklmnopqrstuvwxyz1234"
        result = scrub_secrets(text, replacement="[HIDDEN]")
        assert "[HIDDEN]" in result
