"""Gate 14 — every plan cites ``docs/PLAN_REQUIREMENTS.md``.

Per ``docs/PLAN_REQUIREMENTS.md`` (the "How to update this file" section),
every ``docs/*PLAN*.md`` document MUST reference the requirements file —
either by the relative path ``docs/PLAN_REQUIREMENTS.md`` or by the bare
filename ``PLAN_REQUIREMENTS.md``. Without this rule, a new plan can ship
without a maintainability-audit / requirements-checklist section, which is a
silent Gate 14 violation.

This is the self-enforcing check: any new plan that does not cite the
requirements file fails CI on the plan PR itself.

Scope: top-level ``docs/*PLAN*.md`` (case-insensitive). The archive directory
(``docs/archive/``) is intentionally excluded — those files are historical
snapshots, frozen as artifacts, and are not subject to current gates.
"""

from __future__ import annotations

from pathlib import Path
from typing import Final

import pytest

# WS-M4: mark this module as fast-suite; pytest -m fast skips the 505
# warm-worker V1.34 parity fixtures and runs in <60s.
pytestmark = pytest.mark.fast

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DOCS_ROOT = PROJECT_ROOT / "docs"

# Either of these literal strings counts as a valid citation. The first is
# the canonical repo-relative path; the second matches in-section references
# like "Per PLAN_REQUIREMENTS.md ...".
_VALID_CITATIONS: Final[tuple[str, ...]] = (
    "docs/PLAN_REQUIREMENTS.md",
    "PLAN_REQUIREMENTS.md",
)


def _top_level_plan_files() -> list[Path]:
    """Return every ``docs/*PLAN*.md`` (case-insensitive), excluding archive."""

    out: list[Path] = []
    for path in sorted(DOCS_ROOT.glob("*.md")):
        if "plan" in path.name.lower():
            out.append(path)
    return out


def test_every_top_level_plan_cites_plan_requirements() -> None:
    """Every ``docs/*PLAN*.md`` must contain a ``PLAN_REQUIREMENTS.md`` citation.

    Enforces Gate 14 of ``docs/PLAN_REQUIREMENTS.md``. The citation can be
    either the repo-relative path or the bare filename — both are accepted
    so authors can use whichever fits the sentence naturally.
    """

    plan_files = _top_level_plan_files()
    assert plan_files, (
        "Expected at least one ``docs/*PLAN*.md`` to exist (the canonical "
        "requirements file lives at ``docs/PLAN_REQUIREMENTS.md``). If this "
        "fails, the docs/ directory has been gutted — that is a much larger "
        "problem than this test."
    )

    missing: list[str] = []
    for path in plan_files:
        content = path.read_text(encoding="utf-8")
        if not any(citation in content for citation in _VALID_CITATIONS):
            missing.append(path.relative_to(PROJECT_ROOT).as_posix())

    assert not missing, (
        "Every ``docs/*PLAN*.md`` must cite ``docs/PLAN_REQUIREMENTS.md`` "
        "(or the bare filename ``PLAN_REQUIREMENTS.md``) somewhere in the "
        "body. This is the self-enforcing Gate 14 check — without a citation, "
        "the plan can drift from the requirements silently.\n"
        "  Missing citation:\n    " + "\n    ".join(missing)
    )
