"""Every icon-only <button> must declare an accessible name.

A <button> whose only children are an icon (<svg>, <Icon>, <img>)
needs an `aria-label` or `aria-labelledby` for SRs to announce its
purpose. Visible text children satisfy the accessible-name requirement
automatically.

Audit baseline (2026-05-25): 0 violations — every icon-only button in
LockButton, HistoryStrip, etc. already carries an aria-label.
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

# Buttons whose first non-whitespace child looks like an icon component
# (capital-letter JSX or <svg>/<img>) AND that lack aria-label /
# aria-labelledby on the <button> open tag.
_ICON_BUTTON: Final[re.Pattern[str]] = re.compile(
    r"<button(?P<attrs>(?:[^>]|>(?!</button>))*?)>\s*"
    r"<(?:svg|img|[A-Z][A-Za-z0-9]*)[^>]*/?>\s*</button>",
    re.MULTILINE,
)


def _ts_files() -> list[Path]:
    if not WEB_SRC.is_dir():
        return []
    return sorted(p for p in WEB_SRC.rglob("*.tsx") if "node_modules" not in p.parts)


def _count_violations(path: Path) -> int:
    count = 0
    for match in _ICON_BUTTON.finditer(path.read_text(encoding="utf-8")):
        attrs = match.group("attrs") or ""
        if "aria-label" not in attrs and "aria-labelledby" not in attrs:
            count += 1
    return count


def test_every_icon_button_has_aria_label() -> None:
    violations: list[str] = []
    for path in _ts_files():
        rel = path.relative_to(PROJECT_ROOT).as_posix()
        count = _count_violations(path)
        floor = _GRANDFATHERED.get(rel, 0)
        if count > floor:
            violations.append(
                f"{rel}: {count} icon-only <button> without aria-label " f"(floor {floor})."
            )
    assert (
        not violations
    ), "ADA AA regression: icon-only buttons missing accessible name.\n  " + "\n  ".join(violations)


def test_grandfathered_icon_button_floor_does_not_grow() -> None:
    redundant: list[str] = []
    for rel, floor in _GRANDFATHERED.items():
        path = PROJECT_ROOT / rel
        if not path.is_file():
            redundant.append(f"{rel}: in allowlist but file is gone.")
            continue
        actual = _count_violations(path)
        if actual < floor:
            redundant.append(f"{rel}: floor {floor} but actual {actual}. Drain entry.")
    assert not redundant, "\n  ".join(redundant) if redundant else ""
