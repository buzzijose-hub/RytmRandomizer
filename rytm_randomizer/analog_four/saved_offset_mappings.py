"""Verified Analog Four saved-offset to CC mapping registry.

The default registry is intentionally empty until a controlled hardware diff
proves a saved-kit offset. Code may pass explicit mappings from such evidence
to promote a saved snapshot candidate into a guarded CC plan.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

VERIFIED_MAPPING_STATUS = "verified_cc_mapping"
VERIFIED_CHANGE_SOURCE = "saved_parameter_offset_verified_cc_mapping"
ANALOG_FOUR_TRACKS = range(1, 5)
MIDI_CC_MIN = 0
MIDI_CC_MAX = 127


@dataclass(frozen=True)
class AnalogFourVerifiedSavedOffsetMapping:
    """One controlled-diff-verified saved offset for one Analog Four track."""

    track: int
    relative_offset: int
    parameter_name: str
    cc: int
    mapping_status: str = VERIFIED_MAPPING_STATUS

    def __post_init__(self) -> None:
        if self.track not in ANALOG_FOUR_TRACKS:
            raise ValueError("track must be 1-4")
        if not isinstance(self.relative_offset, int) or self.relative_offset < 0:
            raise ValueError("relative_offset must be a non-negative integer")
        if not isinstance(self.parameter_name, str) or not self.parameter_name.strip():
            raise ValueError("parameter_name must be a non-empty string")
        if not isinstance(self.cc, int) or not MIDI_CC_MIN <= self.cc <= MIDI_CC_MAX:
            raise ValueError("cc must be 0-127")
        if self.mapping_status != VERIFIED_MAPPING_STATUS:
            raise ValueError("mapping_status must be verified_cc_mapping")


DEFAULT_VERIFIED_SAVED_OFFSET_MAPPINGS: tuple[AnalogFourVerifiedSavedOffsetMapping, ...] = ()


def normalize_verified_saved_offset_mappings(
    mappings: Iterable[AnalogFourVerifiedSavedOffsetMapping] | None = None,
) -> tuple[AnalogFourVerifiedSavedOffsetMapping, ...]:
    """Return explicit mappings or the empty default verified registry."""

    if mappings is None:
        return DEFAULT_VERIFIED_SAVED_OFFSET_MAPPINGS
    normalized = tuple(mappings)
    if not all(isinstance(mapping, AnalogFourVerifiedSavedOffsetMapping) for mapping in normalized):
        raise TypeError("verified mappings must be AnalogFourVerifiedSavedOffsetMapping objects")
    return normalized


def find_verified_saved_offset_mapping(
    *,
    track: int,
    relative_offset: int,
    mappings: Iterable[AnalogFourVerifiedSavedOffsetMapping] | None = None,
) -> AnalogFourVerifiedSavedOffsetMapping | None:
    """Find the verified mapping for a track/offset pair, if one exists."""

    for mapping in normalize_verified_saved_offset_mappings(mappings):
        if mapping.track == track and mapping.relative_offset == relative_offset:
            return mapping
    return None


__all__ = [
    "DEFAULT_VERIFIED_SAVED_OFFSET_MAPPINGS",
    "VERIFIED_CHANGE_SOURCE",
    "VERIFIED_MAPPING_STATUS",
    "AnalogFourVerifiedSavedOffsetMapping",
    "find_verified_saved_offset_mapping",
    "normalize_verified_saved_offset_mappings",
]
