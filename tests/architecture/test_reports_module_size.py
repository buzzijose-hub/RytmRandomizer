"""Reports-tree per-file LOC ratchet — CODE_REVIEW.md TS2.

Complements ``test_reports_max_module_size.py`` (which enforces a fixed
1,500-LOC comprehensibility cap with a grandfathered allowlist) with a
**floating** ratchet: no file under ``rytm_randomizer/reports`` may exceed
``current_max + 500`` LOC, where ``current_max`` is the largest
non-grandfathered module's size at the time this gate landed.

Why both gates
==============

* ``test_reports_max_module_size.py`` is the **hard cap** — a fixed
  1,500-LOC ceiling reviewers can hold in working memory. Splits below
  that ceiling are encouraged but not enforced.
* This gate is the **soft ratchet** — even if a new module stays below
  the 1,500 hard cap, it may not balloon to within 500 LOC of the prior
  high-water mark in a single PR. That keeps file growth visible in the
  PR diff: a 200→700 LOC jump asks the reviewer to look at the diff with
  fresh eyes rather than slip in a 100-line append every PR until the
  file silently crosses the comprehensibility cliff.

The shape mirrors PR 11's split-by-floor pattern: pick a moving floor
that reflects today's reality and forbid backsliding by more than a
buffer's width.

Buffer rationale
================

500 LOC is the same headroom the file-size review heuristic in
``CODE_REVIEW.md`` allows between sibling modules in a split — a new
focused submodule should NOT immediately become larger than the largest
existing sibling plus that headroom. Using the same number here keeps
the two gates consistent.

References
==========

* ``tests/architecture/test_reports_max_module_size.py`` — the hard
  comprehensibility cap (1,500 LOC, one grandfathered entry).
* ``CODE_REVIEW.md`` TS2 — the finding that introduced this gate.
* PR 11 (``style_performance_arcs.py`` split) — the precedent for
  floor-based ratchets in the reports tree.
"""

from __future__ import annotations

from pathlib import Path
from typing import Final

import pytest

pytestmark = pytest.mark.fast

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
REPORTS_DIR: Final[Path] = PROJECT_ROOT / "rytm_randomizer" / "reports"

# Headroom buffer above the current max non-grandfathered module size.
# 500 LOC matches the sibling-split heuristic in CODE_REVIEW.md and is
# large enough to absorb routine PR-sized growth without rubber-stamping
# a doubling.
_HEADROOM_LOC: Final[int] = 500

# Files mirrored verbatim from ``test_reports_max_module_size.py`` — the
# consolidated reports ``__init__.py`` already exceeds the hard 1,500
# cap and is the one grandfathered exception. We exclude it from the
# "current max" computation below so the floating ratchet floor reflects
# the size of *splittable* modules, not the one historical outlier.
_GRANDFATHERED_OVERSIZED_REPORTS: Final[frozenset[str]] = frozenset({"__init__.py"})


def _iter_reports_python_files() -> list[Path]:
    """Return every ``.py`` file under ``rytm_randomizer/reports`` (recursive)."""

    if not REPORTS_DIR.is_dir():
        return []
    return sorted(REPORTS_DIR.rglob("*.py"))


def _module_loc(path: Path) -> int:
    """Return raw line count of ``path`` (one entry per newline)."""

    with path.open("r", encoding="utf-8") as handle:
        return sum(1 for _ in handle)


def _relative_name(path: Path) -> str:
    return path.relative_to(REPORTS_DIR).as_posix()


def test_no_report_module_exceeds_current_max_plus_buffer() -> None:
    """No module in ``reports/`` may exceed ``current_max + 500`` LOC.

    ``current_max`` is computed over all non-grandfathered modules. The
    grandfathered ``__init__.py`` is excluded so a single large legacy
    file cannot raise the floor for everyone else.

    A violation here means a single module has jumped more than 500 LOC
    above the prior high-water mark. Resolutions in order of preference:

    1. Split the module into focused sibling files under a subpackage
       (the ``style_performance/`` pattern in this tree).
    2. Move shared helpers into a sibling utility module so the diff
       redistributes rather than concentrates.
    3. (Only as a documented escape hatch) bump ``_HEADROOM_LOC`` with
       reviewer approval and a one-line PR justification.
    """

    sizes: list[tuple[int, str]] = []
    for path in _iter_reports_python_files():
        rel = _relative_name(path)
        if rel in _GRANDFATHERED_OVERSIZED_REPORTS:
            continue
        sizes.append((_module_loc(path), rel))

    if not sizes:
        # Empty tree (e.g. a stripped-down clone) — nothing to enforce.
        return

    sizes.sort(reverse=True)
    current_max_loc = sizes[0][0]
    cap = current_max_loc + _HEADROOM_LOC

    violations = [(loc, name) for loc, name in sizes if loc > cap]
    assert not violations, (
        f"reports/ floating-ratchet cap exceeded: cap={cap} "
        f"(current_max={current_max_loc} + headroom={_HEADROOM_LOC}). "
        "Split or redistribute these modules:\n  "
        + "\n  ".join(f"{name}: {loc} LOC" for loc, name in violations)
    )
