"""Redundant role attributes indicate misunderstanding of semantic HTML.

Forbids `role="button"` on a <button>, `role="link"` on <a>, etc.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Final

import pytest

pytestmark = pytest.mark.fast

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
WEB_SRC: Final[Path] = PROJECT_ROOT / "desktop" / "web" / "src"

_GRANDFATHERED: Final[dict[str, int]] = {}

REDUNDANT_PAIRS: Final[list[tuple[str, str]]] = [
    ("button", "button"),
    ("a", "link"),
    ("nav", "navigation"),
    ("main", "main"),
    ("header", "banner"),
    ("footer", "contentinfo"),
]


def _ts_files() -> list[Path]:
    if not WEB_SRC.is_dir():
        return []
    return sorted(p for p in WEB_SRC.rglob("*.tsx") if "node_modules" not in p.parts)


def _count_violations(path: Path) -> int:
    source = path.read_text(encoding="utf-8")
    count = 0
    for tag, role in REDUNDANT_PAIRS:
        pat = re.compile(rf'<{tag}\b[^>]*\brole\s*=\s*["\']{role}["\']', re.MULTILINE)
        count += len(pat.findall(source))
    return count


def test_no_role_attribute_redundancy() -> None:
    violations: list[str] = []
    for path in _ts_files():
        rel = path.relative_to(PROJECT_ROOT).as_posix()
        count = _count_violations(path)
        floor = _GRANDFATHERED.get(rel, 0)
        if count > floor:
            violations.append(f"{rel}: {count} redundant role (floor {floor}).")
    assert not violations, "\n  ".join(violations) if violations else ""


def test_grandfathered_role_redundancy_floor_does_not_grow() -> None:
    redundant: list[str] = []
    for rel, floor in _GRANDFATHERED.items():
        path = PROJECT_ROOT / rel
        if not path.is_file():
            redundant.append(f"{rel}: file gone.")
            continue
        actual = _count_violations(path)
        if actual < floor:
            redundant.append(f"{rel}: floor {floor} but actual {actual}.")
    assert not redundant, "\n  ".join(redundant)
