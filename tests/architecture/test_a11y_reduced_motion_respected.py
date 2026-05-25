"""CSS files with animations must honor prefers-reduced-motion.

Any file containing @keyframes, `animation:`, or non-instant
`transition:` must also contain a `@media (prefers-reduced-motion`
override. Cluster 8 task adds the overrides + drops the floor.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Final

import pytest

pytestmark = pytest.mark.fast

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
CSS_FILES: Final[tuple[Path, ...]] = (
    PROJECT_ROOT / "desktop" / "web" / "src" / "cockpit" / "styles.css",
    PROJECT_ROOT / "desktop" / "web" / "src" / "wizard" / "styles.css",
)

_GRANDFATHERED: Final[dict[str, int]] = {
    # Audit miss vs. plan (2026-05-25): wizard/styles.css declares
    # animations/transitions without a prefers-reduced-motion override.
    # Cluster 8 task drops this to 0.
    "desktop/web/src/wizard/styles.css": 1,
}

_ANIM_HINT: Final[re.Pattern[str]] = re.compile(
    r"(@keyframes|animation\s*:|transition\s*:\s*(?!none|0s|initial))",
    re.MULTILINE,
)


def _violation_count(path: Path) -> int:
    if not path.is_file():
        return 0
    source = path.read_text(encoding="utf-8")
    has_anim = bool(_ANIM_HINT.search(source))
    has_reduced = "@media (prefers-reduced-motion" in source
    return 1 if has_anim and not has_reduced else 0


def test_animations_honor_reduced_motion() -> None:
    violations: list[str] = []
    for path in CSS_FILES:
        rel = path.relative_to(PROJECT_ROOT).as_posix()
        count = _violation_count(path)
        floor = _GRANDFATHERED.get(rel, 0)
        if count > floor:
            violations.append(
                f"{rel}: declares animations/transitions but no "
                f"@media (prefers-reduced-motion) override [floor {floor}]"
            )
    assert not violations, "\n  ".join(violations) if violations else ""


def test_reduced_motion_floor_does_not_grow() -> None:
    redundant: list[str] = []
    for rel, floor in _GRANDFATHERED.items():
        path = PROJECT_ROOT / rel
        if not path.is_file():
            continue
        actual = _violation_count(path)
        if actual < floor:
            redundant.append(f"{rel}: floor {floor} but actual {actual}.")
    assert not redundant, "\n  ".join(redundant)
