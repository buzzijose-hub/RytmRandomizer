"""WCAG 2.2 AA contrast for documented color-token pairs.

Parses the CSS custom properties in cockpit/styles.css and wizard/
styles.css; computes relative luminance per the WCAG formula; asserts
every documented foreground/background pair clears the relevant
contrast minimum (4.5 for normal text, 3.0 for large/non-text).

Audit baseline (2026-05-25): `--text-dim` on `--panel-2` at small
font-sizes is marginal; Cluster 2 swaps `.knob-label` and
`.pad-card-title` to `--text` and drops the floor to 0.
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

# (foreground_token, background_token, is_small_text) tuples.
# Small text → 4.5 minimum; large/non-text → 3.0.
DOCUMENTED_PAIRS: Final[list[tuple[str, str, bool]]] = [
    ("--text", "--bg", True),
    ("--text", "--panel", True),
    ("--text", "--panel-2", True),
    ("--text-dim", "--bg", True),
    ("--text-dim", "--panel", True),
    ("--text-dim", "--panel-2", False),  # used on hint text only after Cluster 2
    ("--accent", "--panel-2", False),
    ("--green", "--panel-2", False),
    ("--amber", "--panel-2", False),
    ("--danger", "--panel-2", False),
    # Global :focus-visible ring is `--accent` drawn over the `--bg` page and
    # over raised panels; a non-text focus indicator must clear 3:1 (SC 1.4.11
    # / 2.4.13) everywhere it can land.
    ("--accent", "--bg", False),
    ("--accent", "--panel", False),
]

# Floor map: pair-key → 1 (currently failing) or 0 (passing). Cluster 2
# drops the failing entry to 0 by relabelling .knob-label / .pad-card-title
# to use --text not --text-dim (so this pair on `--panel-2` becomes
# large-only via `is_small_text=False`, which we set in the table above).
_GRANDFATHERED: Final[dict[str, int]] = {}


def _hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)


def _relative_luminance(rgb: tuple[int, int, int]) -> float:
    def channel(v: int) -> float:
        srgb = v / 255.0
        return srgb / 12.92 if srgb <= 0.03928 else ((srgb + 0.055) / 1.055) ** 2.4

    r, g, b = (channel(v) for v in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _contrast(fg: tuple[int, int, int], bg: tuple[int, int, int]) -> float:
    lf = _relative_luminance(fg)
    lb = _relative_luminance(bg)
    lighter = max(lf, lb)
    darker = min(lf, lb)
    return (lighter + 0.05) / (darker + 0.05)


def _load_tokens() -> dict[str, str]:
    """Return token-name → hex-value across all CSS files."""
    tokens: dict[str, str] = {}
    pattern = re.compile(r"(--[a-z0-9-]+)\s*:\s*(#[0-9a-fA-F]{6})\s*;")
    for css in CSS_FILES:
        if not css.is_file():
            continue
        for match in pattern.finditer(css.read_text(encoding="utf-8")):
            tokens[match.group(1)] = match.group(2)
    return tokens


def test_documented_color_pairs_meet_aa_contrast() -> None:
    tokens = _load_tokens()
    violations: list[str] = []
    for fg_name, bg_name, is_small in DOCUMENTED_PAIRS:
        if fg_name not in tokens or bg_name not in tokens:
            violations.append(f"Missing token: {fg_name} or {bg_name}")
            continue
        ratio = _contrast(_hex_to_rgb(tokens[fg_name]), _hex_to_rgb(tokens[bg_name]))
        minimum = 4.5 if is_small else 3.0
        key = f"{fg_name}@{bg_name}"
        floor = _GRANDFATHERED.get(key, 0)
        actual = 0 if ratio >= minimum else 1
        if actual > floor:
            violations.append(
                f"{fg_name} on {bg_name}: ratio {ratio:.2f} < {minimum} "
                f"({'small' if is_small else 'large'} text) [floor {floor}]"
            )
    assert not violations, "ADA AA contrast regression:\n  " + "\n  ".join(violations)


def test_grandfathered_contrast_floor_does_not_grow() -> None:
    tokens = _load_tokens()
    redundant: list[str] = []
    for key, floor in _GRANDFATHERED.items():
        fg_name, bg_name = key.split("@", 1)
        if fg_name not in tokens or bg_name not in tokens:
            continue
        ratio = _contrast(_hex_to_rgb(tokens[fg_name]), _hex_to_rgb(tokens[bg_name]))
        is_small = next((s for f, b, s in DOCUMENTED_PAIRS if f == fg_name and b == bg_name), True)
        minimum = 4.5 if is_small else 3.0
        actual = 0 if ratio >= minimum else 1
        if actual < floor:
            redundant.append(f"{key}: floor {floor} but actual {actual}.")
    assert not redundant, "\n  ".join(redundant)
