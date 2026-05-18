"""Analog Four MKII safe-starter profile data.

This module contains only deterministic mapped-CC starter profiles. It does
not import MIDI libraries, open ports, send MIDI, receive SysEx, write SysEx,
or mutate hardware.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

BALANCED_ANALOG_FOUR_STARTER_PROFILE_KEY = "balanced"


@dataclass(frozen=True)
class AnalogFourStarterParameter:
    """One mapped CC/value pair for an Analog Four starter profile."""

    parameter_name: str
    cc: int
    value: int


@dataclass(frozen=True)
class AnalogFourStarterTrackProfile:
    """One track role inside an Analog Four starter profile."""

    track: int
    role_label: str
    parameters: tuple[AnalogFourStarterParameter, ...]


@dataclass(frozen=True)
class AnalogFourStarterProfile:
    """One named safe-starter profile for Analog Four Track 1-4."""

    key: str
    label: str
    aliases: tuple[str, ...]
    description: str
    tracks: tuple[AnalogFourStarterTrackProfile, ...]


def _parameter(name: str, cc: int, value: int) -> AnalogFourStarterParameter:
    return AnalogFourStarterParameter(parameter_name=name, cc=cc, value=value)


def _track(
    track: int,
    role_label: str,
    parameters: tuple[tuple[str, int, int], ...],
) -> AnalogFourStarterTrackProfile:
    return AnalogFourStarterTrackProfile(
        track=track,
        role_label=role_label,
        parameters=tuple(_parameter(name, cc, value) for name, cc, value in parameters),
    )


ANALOG_FOUR_STARTER_PROFILES: tuple[AnalogFourStarterProfile, ...] = (
    AnalogFourStarterProfile(
        key=BALANCED_ANALOG_FOUR_STARTER_PROFILE_KEY,
        label="Balanced",
        aliases=("balanced", "default", "safe", "safe-starter"),
        description="Conservative four-track tonal support for dual-machine testing.",
        tracks=(
            _track(
                1,
                "bass / low tonal anchor",
                (
                    ("Track Level", 95, 104),
                    ("OSC1 Level", 69, 96),
                    ("OSC2 Level", 78, 72),
                    ("Filter 1 Frequency", 18, 112),
                    ("Amp Pan", 10, 60),
                ),
            ),
            _track(
                2,
                "stab / sequence pressure",
                (
                    ("Track Level", 95, 100),
                    ("OSC1 Waveform", 70, 2),
                    ("Filter 1 Frequency", 18, 104),
                    ("Amp Env Decay", 105, 54),
                    ("Amp Pan", 10, 68),
                ),
            ),
            _track(
                3,
                "pad / drone / atmosphere",
                (
                    ("Track Level", 95, 92),
                    ("OSC1 Level", 69, 82),
                    ("OSC2 Level", 78, 88),
                    ("Filter 2 Frequency", 19, 74),
                    ("Reverb Send", 93, 36),
                ),
            ),
            _track(
                4,
                "FX / noise / transition",
                (
                    ("Track Level", 95, 88),
                    ("Noise Level", 77, 72),
                    ("Noise Fade", 76, 68),
                    ("Filter 1 Frequency", 18, 88),
                    ("Amp Pan", 10, 64),
                ),
            ),
        ),
    ),
    AnalogFourStarterProfile(
        key="birmingham-dark",
        label="Birmingham Dark",
        aliases=(
            "birmingham-dark",
            "birmingham_dark",
            "birmingham",
            "birmingham-techno",
            "dark-techno",
        ),
        description="Cold industrial pressure with darker filters and stronger noise motion.",
        tracks=(
            _track(
                1,
                "dark bass pressure",
                (
                    ("Track Level", 95, 106),
                    ("OSC1 Level", 69, 92),
                    ("OSC2 Level", 78, 84),
                    ("Filter 1 Frequency", 18, 96),
                    ("Amp Pan", 10, 58),
                ),
            ),
            _track(
                2,
                "cold stab pressure",
                (
                    ("Track Level", 95, 104),
                    ("OSC1 Waveform", 70, 4),
                    ("Filter 1 Frequency", 18, 92),
                    ("Amp Env Decay", 105, 42),
                    ("Amp Pan", 10, 70),
                ),
            ),
            _track(
                3,
                "industrial drone",
                (
                    ("Track Level", 95, 94),
                    ("OSC1 Level", 69, 86),
                    ("OSC2 Level", 78, 94),
                    ("Filter 2 Frequency", 19, 58),
                    ("Reverb Send", 93, 44),
                ),
            ),
            _track(
                4,
                "noise transition",
                (
                    ("Track Level", 95, 96),
                    ("Noise Level", 77, 84),
                    ("Noise Fade", 76, 78),
                    ("Filter 1 Frequency", 18, 76),
                    ("Amp Pan", 10, 64),
                ),
            ),
        ),
    ),
    AnalogFourStarterProfile(
        key="detroit-classic",
        label="Detroit Classic",
        aliases=(
            "detroit-classic",
            "detroit_classic",
            "detroit",
            "classic-detroit",
            "classic-detroit-techno",
        ),
        description="Open melodic support with softer noise and wider atmosphere.",
        tracks=(
            _track(
                1,
                "analog bass motif",
                (
                    ("Track Level", 95, 100),
                    ("OSC1 Level", 69, 88),
                    ("OSC2 Level", 78, 64),
                    ("Filter 1 Frequency", 18, 116),
                    ("Amp Pan", 10, 60),
                ),
            ),
            _track(
                2,
                "classic chord stab",
                (
                    ("Track Level", 95, 98),
                    ("OSC1 Waveform", 70, 1),
                    ("Filter 1 Frequency", 18, 110),
                    ("Amp Env Decay", 105, 68),
                    ("Amp Pan", 10, 68),
                ),
            ),
            _track(
                3,
                "wide analog pad",
                (
                    ("Track Level", 95, 92),
                    ("OSC1 Level", 69, 84),
                    ("OSC2 Level", 78, 78),
                    ("Filter 2 Frequency", 19, 86),
                    ("Reverb Send", 93, 52),
                ),
            ),
            _track(
                4,
                "light machine texture",
                (
                    ("Track Level", 95, 84),
                    ("Noise Level", 77, 44),
                    ("Noise Fade", 76, 54),
                    ("Filter 1 Frequency", 18, 96),
                    ("Amp Pan", 10, 64),
                ),
            ),
        ),
    ),
    AnalogFourStarterProfile(
        key="peak-time",
        label="Peak Time",
        aliases=("peak-time", "peak_time", "peak time", "peak", "big-room"),
        description="Brighter and stronger four-track support for high-energy pressure.",
        tracks=(
            _track(
                1,
                "bright bass anchor",
                (
                    ("Track Level", 95, 108),
                    ("OSC1 Level", 69, 104),
                    ("OSC2 Level", 78, 78),
                    ("Filter 1 Frequency", 18, 122),
                    ("Amp Pan", 10, 58),
                ),
            ),
            _track(
                2,
                "peak stab pressure",
                (
                    ("Track Level", 95, 108),
                    ("OSC1 Waveform", 70, 2),
                    ("Filter 1 Frequency", 18, 116),
                    ("Amp Env Decay", 105, 48),
                    ("Amp Pan", 10, 70),
                ),
            ),
            _track(
                3,
                "large motion layer",
                (
                    ("Track Level", 95, 100),
                    ("OSC1 Level", 69, 90),
                    ("OSC2 Level", 78, 96),
                    ("Filter 2 Frequency", 19, 96),
                    ("Reverb Send", 93, 60),
                ),
            ),
            _track(
                4,
                "bright riser texture",
                (
                    ("Track Level", 95, 104),
                    ("Noise Level", 77, 90),
                    ("Noise Fade", 76, 72),
                    ("Filter 1 Frequency", 18, 108),
                    ("Amp Pan", 10, 64),
                ),
            ),
        ),
    ),
)


def list_analog_four_starter_profiles() -> tuple[AnalogFourStarterProfile, ...]:
    """Return deterministic Analog Four safe-starter profiles."""

    return ANALOG_FOUR_STARTER_PROFILES


def get_analog_four_starter_profile(key: str | None) -> AnalogFourStarterProfile:
    """Resolve a starter profile key or alias."""

    normalized = _normalize_profile_key(key)
    for profile in ANALOG_FOUR_STARTER_PROFILES:
        aliases = tuple(_normalize_profile_key(alias) for alias in profile.aliases)
        if normalized == profile.key or normalized in aliases:
            return profile
    choices = ", ".join(profile.key for profile in ANALOG_FOUR_STARTER_PROFILES)
    raise ValueError(f"Unknown Analog Four starter profile: {key}. Valid choices: {choices}")


def _normalize_profile_key(key: str | None) -> str:
    if key is None:
        return BALANCED_ANALOG_FOUR_STARTER_PROFILE_KEY
    normalized = str(key).strip().lower()
    normalized = re.sub(r"[\s_]+", "-", normalized)
    return normalized


__all__ = [
    "ANALOG_FOUR_STARTER_PROFILES",
    "BALANCED_ANALOG_FOUR_STARTER_PROFILE_KEY",
    "AnalogFourStarterParameter",
    "AnalogFourStarterProfile",
    "AnalogFourStarterTrackProfile",
    "get_analog_four_starter_profile",
    "list_analog_four_starter_profiles",
]
