"""aria-hidden elements must not be focusable (would trap SR users in invisible state)."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Final

import pytest

pytestmark = pytest.mark.fast

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
WEB_SRC: Final[Path] = PROJECT_ROOT / "desktop" / "web" / "src"

_GRANDFATHERED: Final[dict[str, int]] = {}

_FOCUSABLE_TAGS = {"button", "input", "select", "textarea", "a"}
_ARIA_HIDDEN: Final[re.Pattern[str]] = re.compile(
    r'<(?P<tag>[A-Za-z][A-Za-z0-9-]*)(?P<attrs>(?:[^>]|>(?!</))*?)\baria-hidden\s*=\s*["\']?true',
    re.MULTILINE,
)


def _ts_files() -> list[Path]:
    if not WEB_SRC.is_dir():
        return []
    return sorted(p for p in WEB_SRC.rglob("*.tsx") if "node_modules" not in p.parts)


def _count_violations(path: Path) -> int:
    source = path.read_text(encoding="utf-8")
    count = 0
    for match in _ARIA_HIDDEN.finditer(source):
        tag = match.group("tag").lower()
        attrs = match.group("attrs") or ""
        if tag in _FOCUSABLE_TAGS or re.search(r"\btabIndex\s*=\s*\{?\s*[\"']?[0-9]", attrs):
            count += 1
    return count


def test_no_aria_hidden_focusable() -> None:
    violations: list[str] = []
    for path in _ts_files():
        rel = path.relative_to(PROJECT_ROOT).as_posix()
        count = _count_violations(path)
        floor = _GRANDFATHERED.get(rel, 0)
        if count > floor:
            violations.append(f"{rel}: {count} aria-hidden focusable (floor {floor}).")
    assert not violations, "\n  ".join(violations) if violations else ""


def test_grandfathered_aria_hidden_floor_does_not_grow() -> None:
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
