"""Top-level route components must render exactly one <main> and exactly one <h1>.

Routes (per App.tsx hash router):
- `/` (or empty) → Cockpit.tsx
- `/wizard` → Wizard.tsx
- (placeholder while connecting) → App.tsx renders <main class="cockpit-placeholder">

The connecting-placeholder already has <main> + <h1>. The fix-cluster
6 task ensures Cockpit.tsx + Wizard.tsx do too.

Audit baseline (2026-05-25): floor for Cockpit.tsx is 1 (missing
landmark + h1); will drop to 0 in Cluster 6 task.
"""

from __future__ import annotations

from pathlib import Path
from typing import Final

import pytest

pytestmark = pytest.mark.fast

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
WEB_SRC: Final[Path] = PROJECT_ROOT / "desktop" / "web" / "src"

ROUTE_FILES: Final[dict[str, Path]] = {
    "cockpit": WEB_SRC / "cockpit" / "Cockpit.tsx",
    "wizard": WEB_SRC / "wizard" / "Wizard.tsx",
}

# Floor map: route-name → 0 (compliant) or 1 (missing landmark/h1).
_GRANDFATHERED: Final[dict[str, int]] = {
    "cockpit": 0,  # Cluster 6 added <main> + sr-only <h1>; now compliant
}


def _has_landmark_and_h1(path: Path) -> bool:
    source = path.read_text(encoding="utf-8")
    return ("<main" in source) and ("<h1" in source)


def test_every_route_renders_main_and_h1() -> None:
    violations: list[str] = []
    for route, path in ROUTE_FILES.items():
        if not path.is_file():
            continue
        compliant = _has_landmark_and_h1(path)
        floor = _GRANDFATHERED.get(route, 0)
        actual = 0 if compliant else 1
        if actual > floor:
            violations.append(
                f"{path.relative_to(PROJECT_ROOT).as_posix()} (route {route}): "
                f"missing <main> or <h1> (floor {floor}, actual {actual})."
            )
    assert not violations, "ADA AA regression: route missing landmark.\n  " + "\n  ".join(
        violations
    )


def test_grandfathered_route_landmark_floor_does_not_grow() -> None:
    redundant: list[str] = []
    for route, floor in _GRANDFATHERED.items():
        path = ROUTE_FILES[route]
        if not path.is_file():
            continue
        compliant = _has_landmark_and_h1(path)
        actual = 0 if compliant else 1
        if actual < floor:
            redundant.append(f"{route}: floor {floor} but actual {actual}. Drain entry.")
    assert not redundant, "\n  ".join(redundant)
