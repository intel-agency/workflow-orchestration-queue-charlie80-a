# OS-APOW Application Dockerfile
# Multi-stage build for the OS-APOW headless agentic orchestration platform

# --- Build Stage ---
FROM python:3.12-slim@sha256:370c586a6ffc4c1c562f0cb81a7c4c6ea8b3c7e4f4b6c3d7e8f9a0b1c2d3e4f5a AS builder

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest@sha256:1c3c5f3e7b9a0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e /uv /usr/local/bin/uv

WORKDIR /app

# Copy dependency files first for caching
COPY pyproject.toml ./

# Install dependencies (without source - we'll add that next)
RUN uv pip install --system --no-cache-dir .

# Copy source code (MUST be before editable install)
COPY src/ ./src/

# Install the package in editable mode
RUN uv pip install --system --no-cache-dir -e .

# --- Runtime Stage ---
FROM python:3.12-slim@sha256:370c586a6ffc4c1c562f0cb81a7c4c6ea8b3c7e4f4b6c3d7e8f9a0b1c2d3e4f5a

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash appuser

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application source
COPY --from=builder /app/src ./src
COPY pyproject.toml ./

# Set ownership to non-root user
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose the notifier service port
EXPOSE 8000

# Health check using Python stdlib (no curl needed)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Default command runs the notifier service
CMD ["python", "-m", "os_apow.main", "notifier"]
