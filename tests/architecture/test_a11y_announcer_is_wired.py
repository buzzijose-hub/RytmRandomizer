"""App.tsx must mount the live-region <div role="status" aria-live="polite">.

Without this region, every async UI update (mutation preview, send
result, profile selection) is silent to screen readers.

Audit baseline (2026-05-25): floor 1 (not mounted yet). Cluster 4 task
drops it to 0 by adding <LiveRegion /> to App.tsx.
"""

from __future__ import annotations

from pathlib import Path
from typing import Final

import pytest

pytestmark = pytest.mark.fast

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
APP_TSX: Final[Path] = PROJECT_ROOT / "desktop" / "web" / "src" / "App.tsx"

# Floor starts at 1 (not wired); Cluster 4 drops to 0.
_FLOOR: int = 1


def _is_announcer_wired() -> bool:
    if not APP_TSX.is_file():
        return False
    source = APP_TSX.read_text(encoding="utf-8")
    return ("<LiveRegion" in source) or (
        'role="status"' in source and 'aria-live="polite"' in source
    )


def test_announcer_is_wired_in_app_tsx() -> None:
    wired = _is_announcer_wired()
    actual = 0 if wired else 1
    assert actual <= _FLOOR, (
        "ADA AA regression: App.tsx no longer mounts the live region "
        "(<LiveRegion /> or equivalent role='status' + aria-live='polite' "
        "container). Without it every async event is silent to SR users."
    )


def test_announcer_floor_does_not_grow() -> None:
    """Once Cluster 4 lands the announcer, the floor drops to 0 here."""
    wired = _is_announcer_wired()
    actual = 0 if wired else 1
    assert actual >= _FLOOR or _FLOOR == 0, (
        f"Announcer floor stale: floor {_FLOOR} but actual {actual}. "
        "Drop the _FLOOR constant in this test to match."
    )
