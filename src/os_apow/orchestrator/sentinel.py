"""
OS-APOW Sentinel Orchestrator (The "Brain")

Implementation of Phase 1: Story 2 & 3.

This script acts as the 'Brain' of the OS-APOW system. It:
1. Polls a GitHub repo for issues labeled 'agent:queued'.
2. Claims the task using assign-then-verify distributed locking.
3. Manages the worker lifecycle via './scripts/devcontainer-opencode.sh'.
4. Posts heartbeat comments during long-running tasks.
5. Reports progress and results back to GitHub.
"""

import asyncio
import contextlib
import logging
import random
import signal
import subprocess
import sys
import uuid

import httpx

from os_apow.config import Config
from os_apow.models.work_item import TaskType, WorkItem, WorkItemStatus
from os_apow.queue.github_queue import GitHubQueue

# --- Configuration ---

_config = Config.from_env()

# Generate unique sentinel ID
SENTINEL_ID = f"sentinel-{uuid.uuid4().hex[:8]}"

# Setup Structured Logging
logging.basicConfig(
    level=logging.INFO,
    format=f"%(asctime)s [%(levelname)s] {SENTINEL_ID} - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("OS-APOW-Sentinel")

# Graceful shutdown flag
_shutdown_requested = False


# --- Signal Handling ---


def _handle_signal(signum: int, _frame: object) -> None:
    """Set shutdown flag on SIGTERM/SIGINT so the current task can finish."""
    global _shutdown_requested
    sig_name = signal.Signals(signum).name
    logger.info(f"Received {sig_name} — will shut down after current task finishes")
    _shutdown_requested = True


signal.signal(signal.SIGTERM, _handle_signal)
signal.signal(signal.SIGINT, _handle_signal)


# --- Shell Bridge Interface ---


async def run_shell_command(
    args: list[str], timeout: int | None = None
) -> subprocess.CompletedProcess[str]:
    """Invokes the local shell bridge (devcontainer-opencode.sh).

    Args:
        args: Command and arguments.
        timeout: Maximum seconds to wait. None = no limit.

    Returns:
        CompletedProcess with returncode, stdout, and stderr.
    """
    try:
        logger.info(f"Executing Bridge: {' '.join(args)}")
        process = await asyncio.create_subprocess_exec(
            *args, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout,
            )
        except TimeoutError:
            logger.warning(f"Shell command timed out after {timeout}s — killing")
            process.kill()
            stdout_bytes, stderr_bytes = await process.communicate()
            return subprocess.CompletedProcess(
                args=args,
                returncode=-1,
                stdout=stdout_bytes.decode().strip() if stdout_bytes else "",
                stderr=f"TIMEOUT after {timeout}s\n"
                + (stderr_bytes.decode().strip() if stderr_bytes else ""),
            )

        return subprocess.CompletedProcess(
            args=args,
            returncode=process.returncode if process.returncode is not None else -1,
            stdout=stdout_bytes.decode().strip() if stdout_bytes else "",
            stderr=stderr_bytes.decode().strip() if stderr_bytes else "",
        )
    except Exception as e:
        logger.error(f"Critical shell execution error: {str(e)}")
        raise


# --- Sentinel Class ---


class Sentinel:
    """Sentinel orchestrator that polls for tasks and dispatches workers."""

    def __init__(self, queue: GitHubQueue, config: Config) -> None:
        """Initialize the Sentinel.

        Args:
            queue: The task queue to poll.
            config: Application configuration.
        """
        self.queue = queue
        self.config = config
        self._current_backoff = config.poll_interval

    # --- Heartbeat coroutine ---

    async def _heartbeat_loop(self, item: WorkItem, start_time: float) -> None:
        """Post periodic heartbeat comments while a task is running."""
        while True:
            await asyncio.sleep(self.config.heartbeat_interval)
            elapsed = int(asyncio.get_event_loop().time() - start_time)
            await self.queue.post_heartbeat(item, SENTINEL_ID, elapsed)

    async def process_task(self, item: WorkItem) -> None:
        """Process a single work item through the shell bridge.

        Args:
            item: The work item to process.
        """
        logger.info(f"Processing Task #{item.issue_number}...")
        start_time = asyncio.get_event_loop().time()

        # Launch heartbeat as a background task
        heartbeat_task = asyncio.create_task(self._heartbeat_loop(item, start_time))

        try:
            # Step 1: Initialize Infrastructure
            res_up = await run_shell_command([self.config.shell_bridge_path, "up"], timeout=300)
            if res_up.returncode != 0:
                err = f"❌ **Infrastructure Failure** during `up` stage:\n```\n{res_up.stderr}\n```"
                await self.queue.update_status(item, WorkItemStatus.INFRA_FAILURE, err)
                return

            # Step 2: Start Opencode Server
            res_start = await run_shell_command(
                [self.config.shell_bridge_path, "start"], timeout=120
            )
            if res_start.returncode != 0:
                err = f"❌ **Infrastructure Failure** starting `opencode-server`:\n```\n{res_start.stderr}\n```"
                await self.queue.update_status(item, WorkItemStatus.INFRA_FAILURE, err)
                return

            # Step 3: Trigger Agent Workflow
            workflow_map = {
                TaskType.PLAN: "create-app-plan.md",
                TaskType.IMPLEMENT: "perform-task.md",
                TaskType.BUGFIX: "recover-from-error.md",
            }
            workflow = workflow_map.get(item.task_type, "perform-task.md")
            instruction = f"Execute workflow {workflow} for context: {item.source_url}"

            # Primary bridge call with subprocess timeout safety net
            res_prompt = await run_shell_command(
                [self.config.shell_bridge_path, "prompt", instruction],
                timeout=self.config.subprocess_timeout,
            )

            # Step 4: Handle Completion
            if res_prompt.returncode == 0:
                success_msg = (
                    f"✅ **Workflow Complete**\n"
                    f"Sentinel successfully executed `{workflow}`. "
                    f"Please review Pull Requests."
                )
                await self.queue.update_status(item, WorkItemStatus.SUCCESS, success_msg)
            else:
                log_tail = (
                    res_prompt.stderr[-1500:] if res_prompt.stderr else "No error output captured."
                )
                fail_msg = f"❌ **Execution Error** during `{workflow}`:\n```\n...{log_tail}\n```"
                await self.queue.update_status(item, WorkItemStatus.ERROR, fail_msg)

        except Exception as e:
            logger.exception(f"Internal Sentinel Error on Task #{item.issue_number}")
            await self.queue.update_status(
                item,
                WorkItemStatus.INFRA_FAILURE,
                f"🚨 Sentinel encountered an unhandled exception: {str(e)}",
            )
        finally:
            heartbeat_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await heartbeat_task

            # Environment reset between tasks — stop container but keep for fast restart
            logger.info("Resetting environment (stop)")
            await run_shell_command([self.config.shell_bridge_path, "stop"], timeout=60)

    async def run_forever(self) -> None:
        """Run the main polling loop."""
        logger.info(
            f"Sentinel {SENTINEL_ID} entering polling loop (interval: {self.config.poll_interval}s)"
        )

        while not _shutdown_requested:
            try:
                tasks = await self.queue.fetch_queued_tasks()
                if tasks:
                    logger.info(f"Found {len(tasks)} queued task(s).")
                    for task in tasks:
                        if _shutdown_requested:
                            break
                        if await self.queue.claim_task(
                            task, SENTINEL_ID, self.config.sentinel_bot_login
                        ):
                            await self.process_task(task)
                            break

                # Reset backoff on successful poll
                self._current_backoff = self.config.poll_interval

            except httpx.HTTPStatusError as exc:
                status = exc.response.status_code
                if status in (403, 429):
                    # Jittered exponential backoff
                    jitter = random.uniform(0, self._current_backoff * 0.1)
                    wait = min(self._current_backoff + jitter, self.config.max_backoff)
                    logger.warning(f"Rate limited ({status}) — backing off {wait:.0f}s")
                    self._current_backoff = min(self._current_backoff * 2, self.config.max_backoff)
                    await asyncio.sleep(wait)
                    continue
                else:
                    logger.error(f"GitHub API error: {exc}")
            except Exception as e:
                logger.error(f"Polling cycle error: {str(e)}")

            await asyncio.sleep(self._current_backoff)

        logger.info("Shutdown flag set — exiting polling loop")


# --- Entry Point ---


async def run_sentinel() -> None:
    """Main entry point for the sentinel orchestrator."""
    missing = _config.validate_sentinel()
    if missing:
        logger.error(f"Critical Error: Missing environment variables: {', '.join(missing)}")
        sys.exit(1)

    if not _config.sentinel_bot_login:
        logger.warning(
            "SENTINEL_BOT_LOGIN is not set — assign-then-verify locking is disabled. "
            "Set it to the GitHub login of the bot account for concurrency safety."
        )

    gh_queue = GitHubQueue(_config.github_token, _config.github_org, _config.github_repo)
    sentinel = Sentinel(gh_queue, _config)

    try:
        await sentinel.run_forever()
    finally:
        await gh_queue.close()
        logger.info("Sentinel shut down.")


def main() -> None:
    """Synchronous entry point for the CLI."""
    try:
        asyncio.run(run_sentinel())
    except KeyboardInterrupt:
        logger.info("Sentinel shutting down gracefully.")
