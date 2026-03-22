"""
OS-APOW Main Entry Points

Provides CLI entry points for running the notifier and sentinel services.
"""

import sys

import uvicorn

from os_apow.config import Config


def run_notifier() -> None:
    """Run the FastAPI webhook receiver (the 'Ear')."""
    config = Config.from_env()
    missing = config.validate_notifier()
    if missing:
        print(
            f"Error: Missing required environment variables: {', '.join(missing)}",
            file=sys.stderr,
        )
        sys.exit(1)

    uvicorn.run(
        "os_apow.notifier.service:app",
        host=config.notifier_host,
        port=config.notifier_port,
        reload=False,
    )


def run_sentinel() -> None:
    """Run the Sentinel orchestrator (the 'Brain')."""
    from os_apow.orchestrator.sentinel import main

    main()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m os_apow.main [notifier|sentinel]", file=sys.stderr)
        sys.exit(1)

    command = sys.argv[1]
    if command == "notifier":
        run_notifier()
    elif command == "sentinel":
        run_sentinel()
    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        print("Usage: python -m os_apow.main [notifier|sentinel]", file=sys.stderr)
        sys.exit(1)
