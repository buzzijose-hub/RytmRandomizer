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
# CODE REVIEW (the post-push review gate — see docs/CODE_REVIEW_HOOK_SETUP.md)
# ─────────────────────────────────────────────────────────────────────────

# Mechanical review gates only: lint + architecture + V1.34 parity.
# Delegates to scripts/code_review_gate.py — the SINGLE shared
# implementation also used by the git pre-push hook (.githooks/pre-push)
# and the codex PostToolUse hook (.codex/hooks.json). One script, so the
# gates never drift between callers.
_review-mechanical:
    python scripts/code_review_gate.py --mode cli

# NOTE: the single-line comment directly above `review:` is what
# `just --list` shows as the recipe summary — keep it a clean one-liner.
# Detail: `just review` runs the FULL 8-step code review with NO human
# interaction. First the mechanical gates (_review-mechanical), then it
# dispatches the `code-reviewer` agent — which walks all 8 steps of
# .claude/skills/code-review/SKILL.md, including the two judgement steps
# no test can automate: Step 7 (abstraction reuse / genericization) and
# Step 8 (architecture-doc + diagram freshness) — and emits the
# Critical/Important/Minor/Abstraction/Docs verdict.
#
# Agent dispatch is by ENVIRONMENT DETECTION, not a PATH probe — the
# running agent always exports an identifying env var even when its CLI
# is not on PATH:
#   * Claude Code -> $CLAUDE_CODE_EXECPATH points at the claude binary;
#     invoked non-interactively (`-p ... --agent code-reviewer`).
#   * codex       -> the .codex/hooks.json PostToolUse hook already runs
#     the review automatically on `git push`; `just review` confirms that
#     and exits, so codex is never asked to copy-paste anything.
# If no known agent environment is detected the recipe FAILS LOUDLY
# (non-zero exit) rather than degrading to a manual checklist — the
# review must not be silently skipped. Rationale: docs/CODE_REVIEW_HOOK_SETUP.md.

# Full pre-push code review: mechanical gates + 8-step code-reviewer agent
review: _review-mechanical
    #!/usr/bin/env bash
    set -euo pipefail
    echo ""
    REVIEW_PROMPT="Execute the code-review skill (.claude/skills/code-review/SKILL.md) against the about-to-be-pushed commits on this branch. Gather the diff with 'git log --oneline -10' plus 'git diff @{upstream}..HEAD' (or 'git diff modularize-v1.34...HEAD' if no upstream). Walk all 8 steps — including Step 7 (abstraction reuse / genericization: could the new code be generalized further, or does an existing abstraction such as the Device Protocol, the snapshot envelope helpers, the generic senders, cli_registry, data/, observability/metrics, or the report formatter already cover it) and Step 8 (architecture-doc + diagram freshness: are docs/ARCHITECTURE.md and docs/ARCHITECTURE_DIAGRAMS.md updated for any architecture-surface change, and do the counts the docs quote still match reality). Produce the structured Critical/Important/Minor/Abstraction/Docs verdict."
    if [ -n "${CLAUDE_CODE_EXECPATH:-}" ]; then
        echo "→ Claude Code detected — dispatching the code-reviewer agent (all 8 steps)…"
        "$CLAUDE_CODE_EXECPATH" -p "$REVIEW_PROMPT" --agent code-reviewer
    elif command -v claude >/dev/null 2>&1; then
        echo "→ claude CLI detected — dispatching the code-reviewer agent (all 8 steps)…"
        claude -p "$REVIEW_PROMPT" --agent code-reviewer
    elif [ -n "${CODEX_HOME:-}" ] || [ "${CODEX:-}" = "1" ] || [ -n "${CODEX_SANDBOX:-}" ]; then
        echo "→ codex detected. The .codex/hooks.json PostToolUse hook runs the"
        echo "  8-step review automatically on 'git push' — no action needed here."
        echo "  (If you have not pushed yet, push and the hook will fire.)"
    else
        echo "✗ No agent environment detected (neither Claude Code nor codex)." >&2
        echo "  The mechanical gates passed, but the 8-step judgement review" >&2
        echo "  (Steps 7-8) cannot be auto-dispatched and MUST NOT be skipped." >&2
        echo "  Run this inside Claude Code or codex, or invoke the" >&2
        echo "  code-review skill directly. See docs/CODE_REVIEW_HOOK_SETUP.md." >&2
        exit 1
    fi

# ─────────────────────────────────────────────────────────────────────────
# DEV ENV
# ─────────────────────────────────────────────────────────────────────────

# Install package in editable mode with dev extras + activate git hooks
install:
    pip install -e ".[dev]"
    pre-commit install
    git config core.hooksPath .githooks
    git config core.symlinks true
    git checkout -- .agents/skills
    @echo "✓ git hooks activated (.githooks); .agents/skills symlink materialized."

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
    @echo "  python scripts/create_pr.py --title '<title>' --body-file <path>"
    @echo ""
    @echo "Raw fallback:"
    @echo "  gh pr create --base modularize-v1.34 --reviewer edward-rosado --title '<title>' --body-file <path>"
    @echo ""
    @echo "Both paths request review from edward-rosado automatically."
    @echo "After updating an existing PR, re-request review with:"
    @echo "  python scripts/create_pr.py --request-review-for <pr-number-or-url>"
    @echo "Body must include: conformance checklist (18 gates), strict-rules confirmation, test plan."
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

# Show the 18 plan-requirement gates
gates:
    @grep -A 1 '^### ' docs/PLAN_REQUIREMENTS.md 2>/dev/null | head -50 || cat docs/PLAN_REQUIREMENTS.md | head -80
