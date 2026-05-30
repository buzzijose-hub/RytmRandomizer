"""Top-level conftest — self-heals local developer workflow gates.

This file lives at the repo root (above ``tests/``) so it runs once per
pytest session, BEFORE any test collection. Its sole job is to make sure
the local pre-push hook is actually wired into the current git worktree.

Why this exists
---------------

The repository ships a ``.githooks/pre-push`` script that runs the
mechanical code-review gates (ruff + black --check + isort --check-only +
architecture tests + V1.34 parity) before any ``git push``. That hook is
the local backstop against landing a lint failure on CI — a CI lint job
costs at least one minute *and* a fix-push round trip, which is exactly
what bit PR #107.

The hook is activated by ``git config core.hooksPath .githooks``.
``just install`` and the dev-container ``postCreateCommand`` run that for
you on a fresh clone, but two real workflows skip that path entirely:

1. ``git worktree add`` — each worktree gets its OWN local git config
   space (under ``.git/worktrees/<name>/config``). The parent repo's
   ``core.hooksPath`` is NOT inherited. So creating a fresh worktree
   without re-running ``just install`` silently disables the pre-push
   gate inside that worktree.
2. Cloning into an environment where ``just`` is not installed and
   skipping the documented install step.

Either path leaves the developer believing the local gate is live when
it is not. The lint failure on PR #107 happened exactly this way.

How the self-heal works
-----------------------

On every pytest session start, this hook checks ``git config
core.hooksPath`` for the current repo/worktree:

* If it's already set (to anything), do nothing. Respects the user's
  intentional override — including ``/dev/null`` if they deliberately
  disabled hooks for an emergency push.
* If it's unset AND ``.githooks/pre-push`` exists in the repo root,
  run ``git config core.hooksPath .githooks`` to wire it in. Prints a
  one-line notice so the developer knows the hook is now live.
* If ``git`` is not available (e.g. running tests from a tarball with
  no git installed), do nothing.

The companion architecture test
``tests/architecture/test_pre_push_hook_installed.py`` asserts the gate
IS active — so even if this self-heal fails on some exotic platform,
the test fails locally before push instead of letting a lint regression
escape to CI.

This hook is intentionally idempotent and side-effect-light: one
read-only ``git config --get`` per session in the steady state, one
write the first time only. No network, no installs, no monkey-patching
pytest internals.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent
_HOOKS_DIR = _REPO_ROOT / ".githooks"
_PRE_PUSH = _HOOKS_DIR / "pre-push"


def _self_heal_git_hooks_path() -> None:
    """Wire ``.githooks`` into the current git worktree if not already set."""

    if not _PRE_PUSH.is_file():
        return

    git = shutil.which("git")
    if git is None:
        return

    try:
        existing = subprocess.run(
            [git, "config", "--get", "core.hooksPath"],
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return

    if existing.returncode == 0 and existing.stdout.strip():
        return

    try:
        result = subprocess.run(
            [git, "config", "core.hooksPath", ".githooks"],
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return

    if result.returncode == 0:
        print(
            "[conftest] activated .githooks/pre-push for this worktree "
            "(was unset). The pre-push hook now runs ruff + black + isort + "
            "architecture tests before every push. See conftest.py for why."
        )


def pytest_configure(config: object) -> None:
    """Pytest session-start hook — runs once before collection."""

    _self_heal_git_hooks_path()
