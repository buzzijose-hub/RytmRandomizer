"""Test-only mock mapper from passive metadata to inert MidiMessage objects.

This module is mock-only. It does not import MIDI libraries, open ports, send
MIDI, wire into the CLI, or touch hardware.

``MockMessageMappingError`` is also a member of the unified
:mod:`rytm_randomizer.observability.errors` taxonomy: it inherits from both
:class:`~rytm_randomizer.observability.errors.DataError` AND ``ValueError``,
so existing ``except ValueError`` callers and new ``except DataError``
callers both work.
"""

from __future__ import annotations

from typing import ClassVar

from .mock_midi import MidiMessage
from .observability.errors import DataError
from .profile_lookup import describe_group_profile

SUPPORTED_GROUP_PROFILE_KEYS = ("2", "3")


class MockMessageMappingError(DataError, ValueError):
    """Raised when passive metadata cannot be mapped to mock messages.

    Member of the unified :class:`~rytm_randomizer.observability.errors.DataError`
    taxonomy. ``ValueError`` is kept as an additional base for
    backward-compatibility with any ``except ValueError`` caller.
    """

    fingerprint: ClassVar[str] = "mock.message.mapping_failed"


def _target_concept(profile):
    source_name = profile["name"]
    target_name = source_name[3:] if source_name.startswith("My ") else source_name
    return f"Pad {profile['group_pad']} / {target_name}"


def _build_group_profile_metadata(profile):
    return {
        "source_kind": "group_profile",
        "source_key": profile["profile_key"],
        "source_name": profile["name"],
        "group_pad": profile["group_pad"],
        "machine_value": profile["machine_value"],
        "target": _target_concept(profile),
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

    if normalized_key not in SUPPORTED_GROUP_PROFILE_KEYS:
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
