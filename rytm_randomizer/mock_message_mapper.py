"""Test-only mock mapper from passive metadata to inert MidiMessage objects.

This module is mock-only. It does not import MIDI libraries, open ports, send
MIDI, wire into the CLI, or touch hardware.
"""

from __future__ import annotations

from .mock_midi import MidiMessage
from .profile_lookup import describe_group_profile

SUPPORTED_GROUP_PROFILE_KEY = "2"


class MockMessageMappingError(ValueError):
    """Raised when passive metadata cannot be mapped to mock messages."""


def _build_group_profile_metadata(profile):
    return {
        "source_kind": "group_profile",
        "source_key": profile["profile_key"],
        "source_name": profile["name"],
        "group_pad": profile["group_pad"],
        "machine_value": profile["machine_value"],
        "target": "Pad 1 / BD Hard",
        "mock_only": True,
        "sends_real_midi": False,
    }


def map_group_profile_to_mock_messages(key: str) -> list[MidiMessage]:
    """Return mock-only messages for the supported group profile key."""

    normalized_key = str(key)
    profile = describe_group_profile(normalized_key)

    if not profile["exists"]:
        raise MockMessageMappingError(
            f"Group profile '{normalized_key}' was not found; no MIDI was sent."
        )

    if normalized_key != SUPPORTED_GROUP_PROFILE_KEY:
        raise MockMessageMappingError(
            f"Group profile '{normalized_key}' is not supported by the mock mapper; "
            "no MIDI was sent."
        )

    metadata = _build_group_profile_metadata(profile)
    return [
        MidiMessage(
            message_type="mock_group_profile",
            channel=profile["group_pad"],
            control=0,
            value=profile["machine_value"],
            metadata=metadata,
        )
    ]
