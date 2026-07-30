"""Analog Four acoustic render-ranking facts."""

from __future__ import annotations

from typing import Final

ANALOG_FOUR_RENDER_RANK_FEATURE_WEIGHTS: Final[tuple[tuple[str, float], ...]] = (
    ("attack", 0.12),
    ("decay", 0.09),
    ("sustain", 0.08),
    ("tail", 0.08),
    ("brightness", 0.15),
    ("spectral_flatness", 0.08),
    ("noise", 0.10),
    ("low_end", 0.12),
    ("harmonicity", 0.08),
    ("transient", 0.06),
    ("modulation", 0.04),
)

__all__ = ["ANALOG_FOUR_RENDER_RANK_FEATURE_WEIGHTS"]
