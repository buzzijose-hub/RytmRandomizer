# Justfile — task runner for RytmRandomizer
#
# Install just:
#   cargo install just                       (Rust)
#   brew install just                        (macOS)
#   winget install --id Casey.Just           (Windows)
#   choco install just                       (Windows)
#
# Usage:
#   just              # list available tasks
#   just <task>       # run a task
#
# Every task is also runnable as the bare command shown in its recipe,
# so this file is convenience, not a hard dependency. Agents can copy the
# underlying commands directly if `just` isn't installed.

# Default task: list tasks
default:
    @just --list

# ─────────────────────────────────────────────────────────────────────────
# TESTS
# ─────────────────────────────────────────────────────────────────────────

# Run the full test suite (xdist parallelized by pyproject default)
test:
    python -m pytest

# Fast iteration loop — skips the 685 V1.34 parity items (<30s)
fast:
    python -m pytest -m fast

# Architecture-conformance subset only (~10s; preflight before push)
arch:
    python -m pytest tests/architecture/ -q

# E2E suite (mock-MIDI end-to-end; no hardware)
e2e:
    python -m pytest tests/test_e2e.py -q

# Run pytest with branch coverage + ratchet check
cov:
    python -m pytest --cov=rytm_randomizer --cov-branch --cov-report=term-missing

# One file, single-process (xdist worker spawn > test time for small selections)
test-file FILE:
    python -m pytest {{FILE}} -n 0

# One test by name (single-process)
test-name NAME:
    python -m pytest -k "{{NAME}}" -n 0

# Capture / regenerate V1.34 parity goldens — REQUIRES EXPLICIT APPROVAL
# See .claude/rules/parity-fixture-discipline.md for when this is allowed.
parity-capture:
    PARITY_CAPTURE_MODE=1 python -m pytest tests/test_engines_pad*.py tests/test_group_runner.py tests/test_scene_runner.py -o addopts=''

# ─────────────────────────────────────────────────────────────────────────
# LINT + FORMAT
# ─────────────────────────────────────────────────────────────────────────

# Check lint without modifying files (matches CI)
lint:
    python -m ruff check .
    python -m black --check --target-version=py311 .
    python -m isort --profile black --check-only .

# Auto-fix lint issues
fmt:
    python -m ruff check . --fix
    python -m black --target-version=py311 .
    python -m isort --profile black .

# Run the pre-commit hook battery on all files
pre-commit-all:
    pre-commit run --all-files

# Vulture dead-code scan (--min-confidence 80; CI threshold)
vulture:
    python -m vulture rytm_randomizer/ tests/ --min-confidence 80

# ─────────────────────────────────────────────────────────────────────────
# CLOSEOUT (the pre-PR verification gate)
# ─────────────────────────────────────────────────────────────────────────

# Cross-platform closeout (Python; preferred for new tooling)
closeout:
    python scripts/closeout_check.py

# Windows-only PowerShell closeout (legacy)
closeout-ps:
    powershell -ExecutionPolicy Bypass -File Scripts/closeout_check.ps1

# Full pre-PR check: lint + arch + full test suite + coverage
check: lint arch test cov
    @echo "✓ All checks passed. Ready to push."

# ─────────────────────────────────────────────────────────────────────────
# DEV ENV
# ─────────────────────────────────────────────────────────────────────────

# Install package in editable mode with dev extras
install:
    pip install -e ".[dev]"
    pre-commit install

# Show install status (Python version, deps, pytest plugins)
info:
    @python --version
    @pip show pytest pytest-xdist mido python-rtmidi ruff black isort 2>&1 | grep -E "^(Name|Version)" || true
    @echo "---"
    @python -m pytest --version

# ─────────────────────────────────────────────────────────────────────────
# GIT / PR HELPERS
# ─────────────────────────────────────────────────────────────────────────

# Show PR-ready summary (commits ahead of integration branch)
pr-summary:
    @git fetch origin
    @echo "=== Commits ahead of modularize-v1.34 ==="
    @git log --oneline origin/modularize-v1.34..HEAD
    @echo ""
    @echo "=== File diff stat ==="
    @git diff --stat origin/modularize-v1.34..HEAD

# Open a PR (interactive — opens $EDITOR for body)
pr:
    @echo "Branch: $(git rev-parse --abbrev-ref HEAD)"
    @echo ""
    @echo "Use:"
    @echo "  gh pr create --base modularize-v1.34 --title '<title>' --body-file <path>"
    @echo ""
    @echo "Or interactively:"
    @echo "  gh pr create --base modularize-v1.34"
    @echo ""
    @echo "Body must include: conformance checklist (16 gates), strict-rules confirmation, test plan."
    @echo "See .github/PULL_REQUEST_TEMPLATE.md for the canonical template."

# Watch CI on the current branch's PR
watch:
    @PR=$(gh pr view --json number --jq '.number'); \
        gh pr checks $$PR --watch

# Re-run failed CI jobs on the current branch's PR
rerun-failed:
    @RUN=$(gh run list --branch $(git rev-parse --abbrev-ref HEAD) --json databaseId --jq '.[0].databaseId'); \
        gh run rerun $$RUN --failed

# ─────────────────────────────────────────────────────────────────────────
# DOCS
# ─────────────────────────────────────────────────────────────────────────

# List the diagram sections in ARCHITECTURE_DIAGRAMS.md
diagrams:
    @grep '^## ' docs/ARCHITECTURE_DIAGRAMS.md | head -30

# Show the 16 plan-requirement gates
gates:
    @grep -A 1 '^### ' docs/PLAN_REQUIREMENTS.md 2>/dev/null | head -50 || cat docs/PLAN_REQUIREMENTS.md | head -80
