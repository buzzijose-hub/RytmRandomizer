"""Pre-push hook installation — the local lint-fail backstop must be active.

The repository ships a ``.githooks/pre-push`` script (see
``docs/CODE_REVIEW_HOOK_SETUP.md``) that runs ruff + black --check +
isort --check-only + the architecture suite + V1.34 parity before every
``git push``. CI runs the same gates on the remote side; the local hook
is the *first* place a developer learns their change is broken — saving
a CI-minute and a fix-push round trip per regression.

The hook is activated by ``git config core.hooksPath .githooks``. That
config is per-worktree on Windows / Linux / macOS (each ``git worktree
add`` gets its own config space), so a fresh worktree silently has NO
hook unless someone runs ``just install`` or the top-level
``conftest.py`` self-heals it on the first pytest run.

This test is the audible failure if the self-heal didn't fire:

* Run ``pytest tests/architecture/`` inside any worktree.
* If ``core.hooksPath`` is unset, this test fails with the one-line
  fix-up command (``git config core.hooksPath .githooks``) and the
  reason it matters (PR #107 lint regression cost a fix-push cycle
  exactly because the hook was silently inactive).

Why this matters: lint regressions caught locally cost ~5 seconds.
The same regression caught on CI costs at least one minute of
billable-runner time *plus* the time it takes to context-switch back
to the original task, fix, and push again. Multiply across a multi-PR
workflow and the cost adds up fast. The user feedback was explicit:
"prevent lint fails in the future. this is costly."

Out of scope: this test does NOT execute the hook. It only asserts the
git-config wiring is in place. Hook *content* is covered by
``scripts/code_review_gate.py`` and exercised on every push.

Bypass: if you have a legitimate reason to disable the hook locally
(e.g. an emergency push that intentionally skips lint), set
``core.hooksPath`` to any non-empty value other than ``.githooks`` —
the test only requires that the config is SET, not that it points at
this specific directory. ``/dev/null`` is the conventional disable.
This is a per-developer escape valve; CI's mirror of the same gates
still rejects the push server-side, so you cannot accidentally land
broken lint on main.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Final

import pytest

pytestmark = pytest.mark.fast

_REPO_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
_HOOKS_DIR: Final[Path] = _REPO_ROOT / ".githooks"
_PRE_PUSH_HOOK: Final[Path] = _HOOKS_DIR / "pre-push"


def _git_config_get(key: str) -> str | None:
    """Return the value of ``git config --get <key>`` or ``None`` if unset.

    Returns ``None`` rather than raising on a missing git binary so the
    test can produce a clear skip rather than a confusing error in
    environments where git is unavailable (e.g. running the test suite
    from a sdist tarball).
    """

    git = shutil.which("git")
    if git is None:
        return None
    try:
        result = subprocess.run(
            [git, "config", "--get", key],
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    value = result.stdout.strip()
    return value or None


def _git_available() -> bool:
    return shutil.which("git") is not None and (_REPO_ROOT / ".git").exists()


def test_pre_push_hook_file_exists() -> None:
    """The pre-push hook script must be present in ``.githooks/``.

    Regression guard: if a refactor moves or deletes the hook script,
    no amount of ``core.hooksPath`` configuration will save the
    developer — git will simply find no hook to run. The hook file is
    the local gate's substance; this test pins its location.
    """

    assert _HOOKS_DIR.is_dir(), (
        f"{_HOOKS_DIR} must exist. See docs/CODE_REVIEW_HOOK_SETUP.md " "for the canonical layout."
    )
    assert _PRE_PUSH_HOOK.is_file(), (
        f"{_PRE_PUSH_HOOK} must exist. Restore it from git history or "
        "see docs/CODE_REVIEW_HOOK_SETUP.md for the canonical template."
    )


def test_core_hookspath_is_configured() -> None:
    """``core.hooksPath`` must be set (anywhere) in the current worktree.

    Regression guard: a fresh ``git worktree add`` does NOT inherit the
    parent repo's ``core.hooksPath``. Without this test, the silent
    failure mode is: developer creates a worktree, makes a change, runs
    ``git push``, push succeeds locally with no gate, lint regression
    lands on CI, costs a fix-push cycle (this is exactly what bit
    PR #107).

    The top-level ``conftest.py`` self-heals this on the first pytest
    run in any worktree. If it fails for some reason, this test fires
    with the one-line manual fix.

    NB: we accept ANY non-empty value, not just ``.githooks`` — that
    way a developer can intentionally disable hooks (e.g. point at
    ``/dev/null``) for an emergency push without this test fighting
    them. CI still mirrors all gates server-side.
    """

    if not _git_available():
        pytest.skip("git not available in this environment")

    value = _git_config_get("core.hooksPath")
    assert value is not None, (
        "core.hooksPath is not set in this worktree.\n\n"
        "Fix: run from the worktree root:\n"
        "  git config core.hooksPath .githooks\n\n"
        "Or re-run `just install`. The top-level conftest.py is meant "
        "to do this for you on the first pytest run, so if you are "
        "seeing this message the self-heal failed — please file an "
        "issue noting your OS and shell.\n\n"
        "Why this matters: without core.hooksPath set, the pre-push "
        "hook at .githooks/pre-push does NOT run, and lint regressions "
        "escape to CI (where they cost a fix-push cycle, see PR #107). "
        "See conftest.py and docs/CODE_REVIEW_HOOK_SETUP.md."
    )


def test_configured_hookspath_resolves_to_a_pre_push_hook() -> None:
    """The configured hooks dir must actually contain a ``pre-push`` script.

    Regression guard: a developer who points ``core.hooksPath`` at an
    empty / wrong directory has a silently broken gate. This test
    accepts the conventional "disable" value (``/dev/null`` or any
    path with no ``pre-push`` inside) as an intentional opt-out, but
    if the path looks like a real hooks dir it must contain the hook.

    Specifically: if the configured path resolves to a directory
    INSIDE the repo (e.g. ``.githooks``), it must contain ``pre-push``.
    Out-of-repo paths and special values (``/dev/null``) are accepted
    as intentional overrides.
    """

    if not _git_available():
        pytest.skip("git not available in this environment")

    raw = _git_config_get("core.hooksPath")
    if raw is None:
        pytest.skip(
            "core.hooksPath is unset; the prior test fires the loud " "failure for that case."
        )

    if raw in {"/dev/null", "NUL"} or raw.startswith("/dev/"):
        return

    configured = (_REPO_ROOT / raw).resolve() if not Path(raw).is_absolute() else Path(raw)

    if not configured.exists():
        return
    if not configured.is_dir():
        return
    try:
        configured.relative_to(_REPO_ROOT)
    except ValueError:
        return

    expected_hook = configured / "pre-push"
    assert expected_hook.is_file(), (
        f"core.hooksPath points at {configured} (inside this repo) but "
        f"there is no pre-push script there. Either restore the hook or "
        f"reset the config:\n  git config core.hooksPath .githooks"
    )
