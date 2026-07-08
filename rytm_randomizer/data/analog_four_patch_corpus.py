"""Static Analog Four patch-corpus starter feature vectors.

These rows are synthetic A4 archetype targets derived from the passive patch
templates. They are not hardware captures. The style-analysis corpus matcher
labels them as starter rows until operator-recorded A4 audio/patch pairs are
available.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True)
class AnalogFourPatchCorpusStarterSpec:
    """One synthetic starter vector for an Analog Four patch candidate."""

    entry_id: str
    label: str
    selected_candidate: int
    bpm: float
    tempo_stability: float
    kick_density: float
    percussion_density: float
    low_end_weight: float
    spectral_brightness: float
    texture_noise: float
    energy_arc: tuple[float, ...]
    capture_notes: tuple[str, ...]


ANALOG_FOUR_PATCH_CORPUS_STARTER_SPECS: Final[tuple[AnalogFourPatchCorpusStarterSpec, ...]] = (
    AnalogFourPatchCorpusStarterSpec(
        entry_id="a4-template-closest-reference",
        label="Closest reference",
        selected_candidate=1,
        bpm=134.0,
        tempo_stability=0.91,
        kick_density=0.48,
        percussion_density=0.78,
        low_end_weight=0.42,
        spectral_brightness=0.63,
        texture_noise=0.34,
        energy_arc=(0.18, 0.34, 0.48, 0.72, 0.84, 0.78, 0.61, 0.4),
        capture_notes=("synthetic starter vector; hardware capture pending",),
    ),
    AnalogFourPatchCorpusStarterSpec(
        entry_id="a4-template-brighter-sync",
        label="Brighter sync",
        selected_candidate=2,
        bpm=134.0,
        tempo_stability=0.88,
        kick_density=0.36,
        percussion_density=0.74,
        low_end_weight=0.28,
        spectral_brightness=0.82,
        texture_noise=0.24,
        energy_arc=(0.22, 0.4, 0.6, 0.82, 0.9, 0.72, 0.48, 0.28),
        capture_notes=("synthetic brighter-sync vector; hardware capture pending",),
    ),
    AnalogFourPatchCorpusStarterSpec(
        entry_id="a4-template-noisy-texture",
        label="Noisy texture",
        selected_candidate=3,
        bpm=132.0,
        tempo_stability=0.84,
        kick_density=0.34,
        percussion_density=0.7,
        low_end_weight=0.31,
        spectral_brightness=0.58,
        texture_noise=0.62,
        energy_arc=(0.24, 0.36, 0.55, 0.76, 0.86, 0.82, 0.68, 0.46),
        capture_notes=("synthetic noisy-texture vector; hardware capture pending",),
    ),
    AnalogFourPatchCorpusStarterSpec(
        entry_id="a4-template-rounder-bass",
        label="Rounder bass",
        selected_candidate=4,
        bpm=130.0,
        tempo_stability=0.9,
        kick_density=0.52,
        percussion_density=0.62,
        low_end_weight=0.58,
        spectral_brightness=0.38,
        texture_noise=0.18,
        energy_arc=(0.18, 0.3, 0.48, 0.64, 0.76, 0.78, 0.7, 0.52),
        capture_notes=("synthetic rounder-bass vector; hardware capture pending",),
    ),
)


__all__ = [
    "ANALOG_FOUR_PATCH_CORPUS_STARTER_SPECS",
    "AnalogFourPatchCorpusStarterSpec",
]
