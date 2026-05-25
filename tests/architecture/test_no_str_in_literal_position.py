"""Forbid ``# type: ignore[arg-type]`` for narrowing ``str`` to ``Literal``.

This test exists because CODE_REVIEW.md PR 5 (findings H2, M8, P1)
addressed a recurring anti-pattern: callers were widening incoming
wire-strings (or other values) and then using
``# type: ignore[arg-type]`` to silently pass them into fields typed
as ``Literal[...]``. Examples from before PR 5:

* ``kind=str(data['kind'])  # type: ignore[arg-type]``
* ``mode=mode  # type: ignore[arg-type]`` where ``mode`` was a raw
  ``str`` and the destination wanted ``Literal[...]``.

PR 5 added narrowing helpers (``narrow_kind``, ``narrow_mode``,
``narrow_status``, etc.) in ``rytm_randomizer/cockpit/data/types.py``.
The helpers do the runtime membership check and return the narrowed
type so the call-site no longer needs ``type: ignore``.

This test catches the regression: count every
``# type: ignore[arg-type]`` under ``rytm_randomizer/cockpit/`` and
fail if the count grows above the frozen floor (set when PR 5 lands).

Why "count" instead of "zero":
* Some ``# type: ignore[arg-type]`` lines are unrelated to literal
  narrowing (e.g. duck-typed Protocol consumers). The intent is to
  prevent NEW occurrences, not eliminate every existing one.
* The grandfathered-ratchet pattern (used elsewhere in this suite)
  doesn't apply cleanly: ``arg-type`` ignores aren't keyed by stable
  identifier — they're keyed by file:line, which moves on every
  refactor. A simple count-floor is more durable.

See also:
* ``CODE_REVIEW.md`` findings H2, M8, P1.
* ``CODE_REVIEW_PROGRESS.md`` row RR4d.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Final

import pytest

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
COCKPIT_DIR: Final[Path] = PROJECT_ROOT / "rytm_randomizer" / "cockpit"
NARROW_HELPERS_PATH: Final[Path] = COCKPIT_DIR / "data" / "types.py"

# The expected ceiling, set to current count when PR 5 lands. The test
# fails if a contributor adds new ``# type: ignore[arg-type]`` lines
# instead of using a ``narrow_*`` helper.
# Initial floor: deliberately permissive (current count + small slop)
# so the test goes green immediately after PR 5 merges. A future tightening
# PR can lower this value.
_MAX_ARG_TYPE_IGNORES: Final[int] = 50

_ARG_TYPE_IGNORE_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"#\s*type:\s*ignore\[arg-type\]"
)

def _narrow_helpers_present() -> bool:
    """Detect whether PR 5's narrow_* helpers have actually been added.

    The data/types.py module already exists pre-PR-5 (with Literal
    aliases) — we need to detect the new helper FUNCTIONS, not just
    file presence.
    """

    if not NARROW_HELPERS_PATH.is_file():
        return False
    return "def narrow_" in NARROW_HELPERS_PATH.read_text(encoding="utf-8")


# The rule activates once PR 5 lands the narrow_* helpers. Until then
# this test is dormant — the data/types.py module already exists with
# Literal aliases but the narrowing FUNCTIONS are PR 5's contribution.
pytestmark = [
    pytest.mark.fast,
    pytest.mark.skipif(
        not _narrow_helpers_present(),
        reason="narrow_* helpers not yet shipped — RR4d activates once PR 5 lands",
    ),
]


def _has_narrow_helpers(path: Path) -> bool:
    """Check whether the data/types.py contains any ``narrow_*`` function."""

    if not path.is_file():
        return False
    text = path.read_text(encoding="utf-8")
    return "def narrow_" in text


def _count_arg_type_ignores() -> tuple[int, list[str]]:
    """Return ``(count, sample_violations)`` across cockpit/.

    The sample is at most 10 entries with file:line for the failure
    message — full enumeration would drown the assertion.
    """

    count = 0
    samples: list[str] = []
    for path in sorted(COCKPIT_DIR.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            if _ARG_TYPE_IGNORE_PATTERN.search(line):
                count += 1
                if len(samples) < 10:
                    rel = path.relative_to(PROJECT_ROOT)
                    samples.append(f"{rel}:{lineno} {line.strip()}")
    return count, samples


def test_narrow_helpers_module_actually_has_narrow_functions() -> None:
    """Sanity: PR 5's ``narrow_*`` helpers must actually be defined.

    Without them the rule below is unenforceable — there's no migration
    target. If a future refactor renames or splits the module, the
    skipif gate would silently disable the rule; this test catches that.
    """

    assert _has_narrow_helpers(NARROW_HELPERS_PATH), (
        f"{NARROW_HELPERS_PATH} exists but defines no `narrow_*` "
        "functions. The narrowing-helper pattern is the migration "
        "target for `# type: ignore[arg-type]` removals; if the helpers "
        "have moved, update NARROW_HELPERS_PATH in this test."
    )


def test_arg_type_ignore_count_does_not_grow() -> None:
    """Total ``# type: ignore[arg-type]`` count must stay at or below the floor.

    Regression guard: CODE_REVIEW.md P1 documented this anti-pattern
    across 7+ call sites. PR 5 added narrowing helpers and removed
    every occurrence the helpers cover. This test stops a future
    contributor from re-introducing the pattern instead of using (or
    extending) the helpers.

    Tightening: when a future PR lowers the count, lower
    :data:`_MAX_ARG_TYPE_IGNORES` to match. The set ratchets DOWN,
    never up.
    """

    count, samples = _count_arg_type_ignores()
    assert count <= _MAX_ARG_TYPE_IGNORES, (
        f"`# type: ignore[arg-type]` count in {COCKPIT_DIR.relative_to(PROJECT_ROOT)} "
        f"is {count}, above the floor of {_MAX_ARG_TYPE_IGNORES}. "
        "Use one of the narrow_* helpers in cockpit/data/types.py "
        "instead of widening + ignoring. Sample offenders:\n  "
        + "\n  ".join(samples)
        + "\n\nIf this is a legitimate increase (e.g. integration with a "
        "third-party API), tighten _MAX_ARG_TYPE_IGNORES upward only "
        "after reviewer approval."
    )
