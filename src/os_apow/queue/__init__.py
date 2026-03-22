"""Queue package for OS-APOW."""

from os_apow.queue.github_queue import GitHubQueue, ITaskQueue

__all__ = [
    "GitHubQueue",
    "ITaskQueue",
]
