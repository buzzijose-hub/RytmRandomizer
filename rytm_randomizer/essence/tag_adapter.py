"""Passive bridge from style descriptions/reports to essence tags.

This module is planning metadata only. It does not analyze audio files, import
audio dependencies, open MIDI ports, send MIDI, write SysEx, or mutate
hardware.
"""

from __future__ import annotations

import re

from ..style_analysis import FeatureReport

ESSENCE_TAG_ORDER: tuple[str, ...] = (
    "metallic",
    "bell",
    "detroit",
    "driving",
    "pressure",
    "repetition",
    "density",
    "low",
    "deep",
    "bright",
    "noise",
    "air",
    "raw",
    "motion",
    "tension",
    "digital",
    "analog",
    "classic",
    "groove",
)

_DESCRIPTION_TAG_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("metallic", ("metallic", "metal", "industrial", "ringing")),
    ("bell", ("bell", "bells", "chime", "chimes")),
    ("detroit", ("detroit",)),
    ("driving", ("driving", "drive", "relentless", "pushing", "techno")),
    ("pressure", ("pressure", "pressurized", "push")),
    ("repetition", ("repetition", "repeating", "hypnotic", "loop", "looping", "pulse")),
    ("density", ("dense", "density", "busy")),
    ("low", ("low", "sub", "kick", "bass")),
    ("deep", ("deep", "dark")),
    ("bright", ("bright", "sharp", "cutting")),
    ("noise", ("noise", "noisy", "hat", "hats", "shimmer")),
    ("air", ("air", "open", "wash")),
    ("raw", ("raw", "rough")),
    ("motion", ("motion", "movement", "modulation", "moving")),
    ("tension", ("tension", "tense", "intense", "menacing")),
    ("digital", ("digital", "chip")),
    ("analog", ("analog", "vco")),
    ("classic", ("classic",)),
    ("groove", ("groove", "rolling", "swing")),
)


def derive_essence_tags_from_description(text: str) -> tuple[str, ...]:
    """Derive broad, non-copying essence tags from written reference language."""

    if not isinstance(text, str):
        raise TypeError("description text must be a string")

    normalized = text.lower()
    tags: set[str] = set()
    for tag, terms in _DESCRIPTION_TAG_RULES:
        if any(_contains_term(normalized, term) for term in terms):
            tags.add(tag)
    return _ordered_tags(tags)


def derive_essence_tags_from_feature_report(
    report: FeatureReport,
    *,
    description: str = "",
) -> tuple[str, ...]:
    """Derive broad essence tags from passive style-analysis measurements."""

    if not isinstance(report, FeatureReport):
        raise TypeError("report must be a FeatureReport")
    if not isinstance(description, str):
        raise TypeError("description must be a string")

    tags = set(derive_essence_tags_from_description(description))

    if report.bpm >= 125.0 or report.kick_density >= 0.55:
        tags.add("driving")
    if report.tempo_stability >= 0.70 or report.percussion_density >= 0.50:
        tags.add("repetition")
    if report.percussion_density >= 0.55:
        tags.add("density")
    if report.low_end_weight >= 0.55:
        tags.add("low")
    if report.spectral_brightness >= 0.55:
        tags.add("bright")
    if report.texture_noise >= 0.35:
        tags.add("noise")

    return _ordered_tags(tags)


def _ordered_tags(tags: set[str]) -> tuple[str, ...]:
    return tuple(tag for tag in ESSENCE_TAG_ORDER if tag in tags)


def _contains_term(text: str, term: str) -> bool:
    escaped = re.escape(term)
    if " " in term:
        return term in text
    return re.search(rf"\b{escaped}\b", text) is not None
