"""Canonical creative directions for the Audio-to-Patch DNA workspace."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True)
class AudioPatchDnaDirectionSpec:
    """One deterministic creative transform applied to measured audio features."""

    key: str
    label: str
    role: str
    closeness: int
    duration: float = 0.0
    attack: float = 0.0
    decay: float = 0.0
    sustain: float = 0.0
    tail: float = 0.0
    brightness: float = 0.0
    noise: float = 0.0
    low_end: float = 0.0
    harmonicity: float = 0.0
    transient: float = 0.0
    modulation: float = 0.0


AUDIO_PATCH_DNA_DIRECTION_SPECS: Final[tuple[AudioPatchDnaDirectionSpec, ...]] = (
    AudioPatchDnaDirectionSpec("closest", "Closest", "closest measured match", 96),
    AudioPatchDnaDirectionSpec(
        "darker",
        "Darker",
        "reduced high-frequency energy",
        86,
        brightness=-0.22,
        low_end=0.10,
        tail=0.04,
    ),
    AudioPatchDnaDirectionSpec(
        "brighter",
        "Brighter",
        "sharper and more exposed",
        84,
        brightness=0.22,
        noise=0.04,
        transient=0.04,
    ),
    AudioPatchDnaDirectionSpec(
        "metallic",
        "Metallic",
        "inharmonic infrastructure texture",
        80,
        brightness=0.16,
        noise=0.14,
        harmonicity=0.08,
        modulation=0.10,
    ),
    AudioPatchDnaDirectionSpec(
        "percussive",
        "Percussive",
        "shorter and more transient-led",
        82,
        attack=-0.12,
        decay=-0.16,
        sustain=-0.16,
        tail=-0.18,
        transient=0.24,
    ),
    AudioPatchDnaDirectionSpec(
        "atmospheric",
        "Atmospheric",
        "slower envelope and longer pressure",
        76,
        attack=0.16,
        decay=0.18,
        sustain=0.18,
        tail=0.28,
        transient=-0.12,
        modulation=0.10,
    ),
    AudioPatchDnaDirectionSpec(
        "deeper",
        "Deeper",
        "heavier low-frequency body",
        81,
        duration=0.08,
        brightness=-0.12,
        low_end=0.22,
    ),
    AudioPatchDnaDirectionSpec(
        "animated",
        "Animated",
        "more spectral motion and modulation",
        78,
        tail=0.08,
        noise=0.06,
        modulation=0.28,
    ),
)

AUDIO_PATCH_DNA_CANDIDATE_COUNT: Final[int] = len(AUDIO_PATCH_DNA_DIRECTION_SPECS)

__all__ = [
    "AUDIO_PATCH_DNA_CANDIDATE_COUNT",
    "AUDIO_PATCH_DNA_DIRECTION_SPECS",
    "AudioPatchDnaDirectionSpec",
]
