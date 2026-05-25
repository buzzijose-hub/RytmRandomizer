"""Forbid <div onClick> / <span onClick> antipatterns in desktop/web/src/.

Semantic <button>/<a> elements are keyboard-accessible and announced
correctly by screen readers. Click handlers on generic containers are
not. This guard scans every TS/TSX file under desktop/web/src/ for the
JSX pattern <div onClick={...}> or <span onClick={...}>.

Audit baseline (2026-05-25): 0 violations — Cockpit + Wizard already
use semantic elements everywhere.

Companion: test_grandfathered_div_onclick_floor_does_not_grow
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Final

import pytest

pytestmark = pytest.mark.fast

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
WEB_SRC: Final[Path] = PROJECT_ROOT / "desktop" / "web" / "src"

# (relpath, count) pairs of currently-known violations. New violations
# without an allowlist entry fail the main rule.
_GRANDFATHERED: Final[dict[str, int]] = {}

_PATTERN: Final[re.Pattern[str]] = re.compile(r"<(div|span)[^>]*\sonClick\s*=", re.MULTILINE)


def _ts_files() -> list[Path]:
    if not WEB_SRC.is_dir():
        return []
    return sorted(p for p in WEB_SRC.rglob("*.tsx") if "node_modules" not in p.parts)


def _count_violations(path: Path) -> int:
    return len(_PATTERN.findall(path.read_text(encoding="utf-8")))


def test_no_div_onclick_in_desktop_web_src() -> None:
    """No <div onClick> / <span onClick> may appear in desktop/web/src/.

    Forces semantic <button>/<a>. Use the keyboard-event helper from
    desktop/web/src/a11y/ if you need a custom interactive widget.
    """
    violations: list[str] = []
    for path in _ts_files():
        rel = path.relative_to(PROJECT_ROOT).as_posix()
        count = _count_violations(path)
        floor = _GRANDFATHERED.get(rel, 0)
        if count > floor:
            violations.append(
                f"{rel}: {count} <div|span onClick> instances "
                f"(floor {floor}). Replace with <button> / <a>."
            )
    assert not violations, "ADA AA regression: <div onClick> antipatterns found.\n  " + "\n  ".join(
        violations
    )


def test_grandfathered_div_onclick_floor_does_not_grow() -> None:
    """Drain-allowlist: floor must equal (not exceed) actual count."""
    redundant: list[str] = []
    for rel, floor in _GRANDFATHERED.items():
        path = PROJECT_ROOT / rel
        if not path.is_file():
            redundant.append(f"{rel}: in allowlist but file is gone.")
            continue
        actual = _count_violations(path)
        if actual < floor:
            redundant.append(f"{rel}: floor {floor} but actual {actual}. Drain entry.")
    assert (
        not redundant
    ), "Stale a11y allowlist — drain entries to actual counts:\n  " + "\n  ".join(redundant)
