"""Every <input>/<textarea>/<select> must have a label association.

Three valid forms of association: a wrapping <label>, an aria-label
on the field, or aria-labelledby pointing at an id elsewhere.

Audit baseline (2026-05-25): 0 violations — NameStep + AddStep wrap
their inputs in <label> elements; DepthSlider has aria-label.
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

# Matches a self-closing <input ... /> tag.
_FORM_FIELD: Final[re.Pattern[str]] = re.compile(
    r"<(?P<tag>input|textarea|select)(?P<attrs>(?:[^>]|>(?!</))*?)/?>",
    re.MULTILINE,
)


def _ts_files() -> list[Path]:
    if not WEB_SRC.is_dir():
        return []
    return sorted(p for p in WEB_SRC.rglob("*.tsx") if "node_modules" not in p.parts)


def _has_association(attrs: str) -> bool:
    return "aria-label" in attrs or "aria-labelledby" in attrs or 'type="hidden"' in attrs


def _count_violations(path: Path) -> int:
    # Read the whole file; count fields that have neither an aria-label
    # nor sit inside a wrapping <label>.
    source = path.read_text(encoding="utf-8")
    count = 0
    for match in _FORM_FIELD.finditer(source):
        attrs = match.group("attrs") or ""
        if _has_association(attrs):
            continue
        # Check the 100 chars before the match for an opening <label
        window = source[max(0, match.start() - 200) : match.start()]
        if "<label" in window:
            continue
        count += 1
    return count


def test_every_form_field_has_label() -> None:
    violations: list[str] = []
    for path in _ts_files():
        rel = path.relative_to(PROJECT_ROOT).as_posix()
        count = _count_violations(path)
        floor = _GRANDFATHERED.get(rel, 0)
        if count > floor:
            violations.append(f"{rel}: {count} unlabeled form field(s) (floor {floor}).")
    assert not violations, "ADA AA regression: unlabeled form fields.\n  " + "\n  ".join(violations)


def test_grandfathered_form_field_floor_does_not_grow() -> None:
    redundant: list[str] = []
    for rel, floor in _GRANDFATHERED.items():
        path = PROJECT_ROOT / rel
        if not path.is_file():
            redundant.append(f"{rel}: in allowlist but file is gone.")
            continue
        actual = _count_violations(path)
        if actual < floor:
            redundant.append(f"{rel}: floor {floor} but actual {actual}. Drain entry.")
    assert not redundant, "\n  ".join(redundant)
