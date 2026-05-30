"""Passive techno style profiles for later snapshot/audio-analysis routing.

The profiles in this module are design-intent records only. They do not send
MIDI, choose machines, mutate snapshots, or execute scenes. They give future
runtime and analyzer work a stable vocabulary for underground techno
aesthetics while the current PR stays passive and deterministic.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final


@dataclass(frozen=True)
class StyleProfileScores:
    """Normalized 0-10 emphasis scores for one style profile."""

    energy: int
    density: int
    darkness: int
    grit: int
    groove: int
    hypnosis: int
    space: int


@dataclass(frozen=True)
class StyleProfile:
    """Passive style intent for Rytm/A4 sound-design planning."""

    key: str
    name: str
    summary: str
    tags: tuple[str, ...]
    scene_keys: tuple[str, ...]
    rytm_focus: tuple[str, ...]
    analog_four_focus: tuple[str, ...]
    analyzer_targets: tuple[str, ...]
    scores: StyleProfileScores


def _scores(
    *,
    energy: int,
    density: int,
    darkness: int,
    grit: int,
    groove: int,
    hypnosis: int,
    space: int,
) -> StyleProfileScores:
    return StyleProfileScores(
        energy=energy,
        density=density,
        darkness=darkness,
        grit=grit,
        groove=groove,
        hypnosis=hypnosis,
        space=space,
    )


_STYLE_PROFILE_ITEMS: Final[tuple[StyleProfile, ...]] = (
    StyleProfile(
        key="detroit_minimal",
        name="Detroit Minimal",
        summary="Stripped, stable pulse with dry machine funk and small hypnotic shifts.",
        tags=("detroit", "minimal", "stripped", "dry", "repetitive"),
        scene_keys=("s0", "s1a", "s2a"),
        rytm_focus=(
            "tight protected kick",
            "short hats and rim detail",
            "restrained filter movement",
        ),
        analog_four_focus=(
            "one-note pulse",
            "subtle oscillator detune",
            "short envelope stabs",
        ),
        analyzer_targets=("transient", "repetition", "low_end", "snapshot"),
        scores=_scores(
            energy=5,
            density=4,
            darkness=4,
            grit=3,
            groove=6,
            hypnosis=8,
            space=3,
        ),
    ),
    StyleProfile(
        key="mills_hypnotic",
        name="Mills Hypnotic",
        summary="Bell-like motion, sharp percussion, and futuristic loop pressure.",
        tags=("detroit", "hypnotic", "bells", "motion", "futurist"),
        scene_keys=("s1b", "s3a", "s4a"),
        rytm_focus=(
            "metallic percussion accents",
            "fast hat/rim motion",
            "Pad 3 modulation as the motion carrier",
        ),
        analog_four_focus=(
            "bell partials",
            "sync-like motion",
            "tight delay-space accents",
        ),
        analyzer_targets=("spectral_peaks", "motion", "transient", "snapshot"),
        scores=_scores(
            energy=8,
            density=6,
            darkness=5,
            grit=5,
            groove=6,
            hypnosis=9,
            space=6,
        ),
    ),
    StyleProfile(
        key="hood_stripped",
        name="Hood Stripped",
        summary="Hard minimal drive: few elements, strong pulse, and no wasted motion.",
        tags=("minimal", "hard", "stripped", "driving", "functional"),
        scene_keys=("s0", "s1", "s2b"),
        rytm_focus=(
            "kick dominance",
            "dry closed hat pressure",
            "controlled secondary percussion",
        ),
        analog_four_focus=(
            "single oscillator stab",
            "tight filter envelope",
            "low note restraint",
        ),
        analyzer_targets=("low_end", "density", "transient", "snapshot"),
        scores=_scores(
            energy=7,
            density=3,
            darkness=5,
            grit=4,
            groove=7,
            hypnosis=8,
            space=2,
        ),
    ),
    StyleProfile(
        key="ur_machine_funk",
        name="Machine Funk",
        summary="Electro-techno pressure with syncopated machine swing and bright bite.",
        tags=("detroit", "machine_funk", "syncopated", "bright", "electro"),
        scene_keys=("s1b", "s2a", "s3a"),
        rytm_focus=(
            "syncopated hats",
            "snare/rim call-and-response",
            "moderate overdrive bite",
        ),
        analog_four_focus=(
            "rubbery bass movement",
            "bright stab layer",
            "controlled pitch motion",
        ),
        analyzer_targets=("groove", "syncopation", "spectral_balance", "snapshot"),
        scores=_scores(
            energy=7,
            density=6,
            darkness=4,
            grit=5,
            groove=9,
            hypnosis=7,
            space=4,
        ),
    ),
    StyleProfile(
        key="hardgroove_percussive",
        name="Hardgroove Percussive",
        summary="Rolling percussion density with warm drive and a human-feeling push.",
        tags=("hardgroove", "percussive", "rolling", "funky", "driving"),
        scene_keys=("s1", "s1b", "s2b"),
        rytm_focus=(
            "multiple hat lanes",
            "tom and clap ghost pressure",
            "kick protected under percussion density",
        ),
        analog_four_focus=(
            "offbeat stab support",
            "short noisy accents",
            "filter-envelope bounce",
        ),
        analyzer_targets=("groove", "density", "transient", "snapshot"),
        scores=_scores(
            energy=8,
            density=8,
            darkness=4,
            grit=6,
            groove=10,
            hypnosis=7,
            space=3,
        ),
    ),
    StyleProfile(
        key="birmingham_pressure",
        name="Birmingham Pressure",
        summary="Raw, hard-edged loop pressure with aggressive grit and little air.",
        tags=("birmingham", "raw", "hard", "loop_pressure", "warehouse"),
        scene_keys=("s3b", "s4a", "s4b"),
        rytm_focus=(
            "hard kick body",
            "distorted hats and noise bite",
            "controlled wild scene pressure",
        ),
        analog_four_focus=(
            "overdriven monotone stab",
            "dark filter pressure",
            "short metallic scrape",
        ),
        analyzer_targets=("grit", "density", "darkness", "snapshot"),
        scores=_scores(
            energy=9,
            density=7,
            darkness=8,
            grit=9,
            groove=6,
            hypnosis=8,
            space=2,
        ),
    ),
    StyleProfile(
        key="industrial_dark",
        name="Industrial Dark",
        summary="Mechanized percussion, noisy edges, and black-room intensity.",
        tags=("industrial", "dark", "metallic", "noise", "severe"),
        scene_keys=("s3b", "s4", "s4b"),
        rytm_focus=(
            "metallic noise hats",
            "clap/rim impact layers",
            "high grit with bounded kick movement",
        ),
        analog_four_focus=(
            "metallic FM-like bite",
            "dark drones",
            "resonant filter stress",
        ),
        analyzer_targets=("noise_floor", "darkness", "spectral_peaks", "snapshot"),
        scores=_scores(
            energy=9,
            density=7,
            darkness=10,
            grit=10,
            groove=5,
            hypnosis=7,
            space=3,
        ),
    ),
    StyleProfile(
        key="deep_dark_hypnosis",
        name="Deep Dark Hypnosis",
        summary="Deep rolling pressure with wide shadow, slow motion, and patience.",
        tags=("deep", "dark", "rolling", "hypnotic", "atmospheric"),
        scene_keys=("s2", "s2a", "s3a"),
        rytm_focus=(
            "longer body hits",
            "subtle LFO movement",
            "deep kick and restrained hats",
        ),
        analog_four_focus=(
            "dark pad-like undertone",
            "slow filter movement",
            "low resonant support",
        ),
        analyzer_targets=("low_end", "space", "motion", "snapshot"),
        scores=_scores(
            energy=6,
            density=5,
            darkness=9,
            grit=5,
            groove=7,
            hypnosis=10,
            space=8,
        ),
    ),
    StyleProfile(
        key="warehouse_peak",
        name="Warehouse Peak",
        summary="Peak-time drive with high energy, sharp transients, and guarded chaos.",
        tags=("peak_time", "warehouse", "driving", "intense", "controlled_chaos"),
        scene_keys=("s3", "s3a", "s4b"),
        rytm_focus=(
            "protected kick under maximum motion",
            "hard hat pressure",
            "scene-safe wild discovery",
        ),
        analog_four_focus=(
            "urgent stab layer",
            "wide filter sweeps",
            "tight bass reinforcement",
        ),
        analyzer_targets=("energy", "density", "transient", "snapshot"),
        scores=_scores(
            energy=10,
            density=8,
            darkness=6,
            grit=7,
            groove=7,
            hypnosis=8,
            space=5,
        ),
    ),
    StyleProfile(
        key="jose_core_techno",
        name="Jose Core Techno",
        summary=(
            "Hard loop pressure, Jeff Mills hypnosis, Oscar Mulero tunnel darkness, "
            "and Birmingham/Stigmata industrial drive."
        ),
        tags=(
            "jose",
            "core",
            "jeff_mills",
            "oscar_mulero",
            "stigmata",
            "glenn_wilson",
            "nightshift",
            "regis",
            "surgeon",
            "birmingham",
            "industrial",
            "hard_loop",
            "warehouse",
        ),
        scene_keys=("s1b", "s3a", "s3b", "s4a"),
        rytm_focus=(
            "disciplined kick foundation",
            "metallic hat and rim pressure",
            "hard loop-tool percussion density",
            "controlled grit without collapsing the groove",
        ),
        analog_four_focus=(
            "A4 Track 1 bassline pressure",
            "A4 Track 2 lead/stab/alarm motion",
            "A4 Track 3 adaptive rhythmic texture or second lead",
            "A4 Track 4 atmosphere, pad, drone, or weird motion",
        ),
        analyzer_targets=(
            "low_end",
            "transient",
            "motion",
            "darkness",
            "spectral_peaks",
            "snapshot",
        ),
        scores=_scores(
            energy=9,
            density=8,
            darkness=9,
            grit=9,
            groove=8,
            hypnosis=10,
            space=5,
        ),
    ),
)

STYLE_PROFILES: Final[Mapping[str, StyleProfile]] = MappingProxyType(
    {profile.key: profile for profile in _STYLE_PROFILE_ITEMS}
)

__all__ = [
    "STYLE_PROFILES",
    "StyleProfile",
    "StyleProfileScores",
]
