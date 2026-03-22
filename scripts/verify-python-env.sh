#!/bin/bash
#
# Python Environment Verification Script
# Story 3 - Epic #10: Python Environment Verification
#
# This script verifies that the Python development environment is properly
# configured with all required dependencies and tools.
#
# Usage:
#   ./scripts/verify-python-env.sh
#
# Exit codes:
#   0 - All verifications passed
#   1 - One or more verifications failed

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counters
PASSED=0
FAILED=0
WARNINGS=0

# Helper functions
pass() {
    echo -e "${GREEN}✓${NC} $1"
    PASSED=$((PASSED + 1))
}

fail() {
    echo -e "${RED}✗${NC} $1"
    FAILED=$((FAILED + 1))
}

warn() {
    echo -e "${YELLOW}!${NC} $1"
    WARNINGS=$((WARNINGS + 1))
}

section() {
    echo ""
    echo "=== $1 ==="
}

# Minimum required versions
MIN_PYTHON_MAJOR=3
MIN_PYTHON_MINOR=12
MIN_UV_MAJOR=0
MIN_UV_MINOR=10

echo "========================================"
echo "Python Environment Verification Script"
echo "========================================"

# ============================================
# 1. Python Version Verification
# ============================================
section "Python Version"

PYTHON_VERSION=$(python3 --version 2>/dev/null | awk '{print $2}' || echo "")
if [[ -z "$PYTHON_VERSION" ]]; then
    fail "Python3 not found in PATH"
else
    PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
    PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)
    
    if [[ "$PYTHON_MAJOR" -gt "$MIN_PYTHON_MAJOR" ]] || \
       ([[ "$PYTHON_MAJOR" -eq "$MIN_PYTHON_MAJOR" ]] && [[ "$PYTHON_MINOR" -ge "$MIN_PYTHON_MINOR" ]]); then
        pass "Python version: $PYTHON_VERSION (requires >= ${MIN_PYTHON_MAJOR}.${MIN_PYTHON_MINOR})"
    else
        fail "Python version $PYTHON_VERSION is below minimum required (${MIN_PYTHON_MAJOR}.${MIN_PYTHON_MINOR})"
    fi
fi

# Check via uv run (should match)
PYTHON_VERSION_UV=$(uv run python --version 2>/dev/null | awk '{print $2}' || echo "")
if [[ -n "$PYTHON_VERSION_UV" ]]; then
    if [[ "$PYTHON_VERSION" == "$PYTHON_VERSION_UV" ]]; then
        pass "uv run python version matches: $PYTHON_VERSION_UV"
    else
        warn "uv run python version ($PYTHON_VERSION_UV) differs from system ($PYTHON_VERSION)"
    fi
fi

# ============================================
# 2. uv Package Manager Verification
# ============================================
section "uv Package Manager"

UV_VERSION=$(uv --version 2>/dev/null | awk '{print $2}' || echo "")
if [[ -z "$UV_VERSION" ]]; then
    fail "uv not found in PATH"
else
    UV_MAJOR=$(echo "$UV_VERSION" | cut -d. -f1)
    UV_MINOR=$(echo "$UV_VERSION" | cut -d. -f2)
    
    if [[ "$UV_MAJOR" -gt "$MIN_UV_MAJOR" ]] || \
       ([[ "$UV_MAJOR" -eq "$MIN_UV_MAJOR" ]] && [[ "$UV_MINOR" -ge "$MIN_UV_MINOR" ]]); then
        pass "uv version: $UV_VERSION (requires >= ${MIN_UV_MAJOR}.${MIN_UV_MINOR})"
    else
        fail "uv version $UV_VERSION is below minimum required (${MIN_UV_MAJOR}.${MIN_UV_MINOR})"
    fi
fi

# Check uv pip functionality
if uv pip --help &>/dev/null; then
    pass "uv pip is functional"
else
    fail "uv pip is not functional"
fi

# ============================================
# 3. Virtual Environment Verification
# ============================================
section "Virtual Environment"

if [[ -d ".venv" ]]; then
    pass ".venv directory exists"
    
    if [[ -f ".venv/pyvenv.cfg" ]]; then
        pass "pyvenv.cfg found - virtual environment is valid"
    else
        warn ".venv exists but pyvenv.cfg not found"
    fi
else
    fail ".venv directory not found - run 'uv sync --all-extras'"
fi

# ============================================
# 4. Core Dependencies Verification
# ============================================
section "Core Dependencies Import"

DEPENDENCIES=("fastapi" "pydantic" "httpx" "pytest" "ruff" "mypy")

for dep in "${DEPENDENCIES[@]}"; do
    if uv run python -c "import $dep" 2>/dev/null; then
        pass "$dep is importable"
    else
        fail "$dep is not importable - run 'uv sync --all-extras'"
    fi
done

# ============================================
# 5. Tool Versions
# ============================================
section "Tool Versions"

# pytest
PYTEST_VERSION=$(uv run pytest --version 2>/dev/null | head -1 | awk '{print $2}' || echo "")
if [[ -n "$PYTEST_VERSION" ]]; then
    pass "pytest version: $PYTEST_VERSION"
else
    fail "pytest not available"
fi

# ruff
RUFF_VERSION=$(uv run ruff --version 2>/dev/null | awk '{print $2}' || echo "")
if [[ -n "$RUFF_VERSION" ]]; then
    pass "ruff version: $RUFF_VERSION"
else
    fail "ruff not available"
fi

# mypy
MYPY_VERSION=$(uv run mypy --version 2>/dev/null | awk '{print $2}' || echo "")
if [[ -n "$MYPY_VERSION" ]]; then
    pass "mypy version: $MYPY_VERSION"
else
    fail "mypy not available"
fi

# ============================================
# 6. pytest Collection Test
# ============================================
section "pytest Infrastructure"

if uv run pytest --collect-only &>/dev/null; then
    pass "pytest --collect-only runs successfully"
else
    warn "pytest --collect-only failed (may be due to no tests yet)"
fi

# ============================================
# 7. CI/CD Environment Match
# ============================================
section "CI/CD Environment Match"

# Check .python-version file
if [[ -f ".python-version" ]]; then
    PYTHON_VERSION_FILE=$(cat .python-version)
    pass ".python-version file exists: $PYTHON_VERSION_FILE"
else
    warn ".python-version file not found"
fi

# Check pyproject.toml requires-python
if [[ -f "pyproject.toml" ]]; then
    if grep -q "requires-python" pyproject.toml; then
        REQUIRES_PYTHON=$(grep "requires-python" pyproject.toml | head -1)
        pass "pyproject.toml specifies: $REQUIRES_PYTHON"
    else
        warn "pyproject.toml missing requires-python specification"
    fi
else
    fail "pyproject.toml not found"
fi

# ============================================
# Summary
# ============================================
echo ""
echo "========================================"
echo "Summary"
echo "========================================"
echo -e "Passed:   ${GREEN}$PASSED${NC}"
echo -e "Failed:   ${RED}$FAILED${NC}"
echo -e "Warnings: ${YELLOW}$WARNINGS${NC}"
echo ""

if [[ $FAILED -eq 0 ]]; then
    echo -e "${GREEN}All verifications passed!${NC}"
    exit 0
else
    echo -e "${RED}Some verifications failed. Please fix the issues above.${NC}"
    exit 1
fi
