"""Scoped A4 MKII OS1.55 F1 facts, not installed-device/runtime validation.

Research paths are relative to ElektronNativeResearch/2026-09-28-integrated/
a4_companion. Only identities and derived arithmetic facts are retained here,
not firmware bytes. Numeric labels do not establish physical frequency in Hz.
"""

from __future__ import annotations

from typing import Final, Literal

from .analog_four_kit_fields import A4_WIRE_ADDRESSES
from .analog_four_midi import ANALOG_FOUR_SYNTH_TRACK_CC, AnalogFourCcMapping
from .analog_four_saved_kit_layout import (
    A4_KIT_OBJECT_TRACK_SOUND_SIZE,
    A4_KIT_OBJECT_TRACKS_OFFSET,
    A4_KIT_SYNTH_TRACK_COUNT,
    wire_address_to_track_raw_offset,
)

F1BaselineSource = Literal["current", "pending", "unknown"]
A4_F1_BASELINE_CURRENT: Final[F1BaselineSource] = "current"
A4_F1_BASELINE_PENDING: Final[F1BaselineSource] = "pending"
A4_F1_BASELINE_UNKNOWN: Final[F1BaselineSource] = "unknown"

A4_F1_MAPPING: Final[AnalogFourCcMapping] = ANALOG_FOUR_SYNTH_TRACK_CC["Filter1 Frequency"]
A4_F1_LOGICAL_ID: Final[int] = 78
A4_F1_PHYSICAL_SLOT: Final[int] = 34
A4_F1_NATIVE_MIN: Final[int] = 0
A4_F1_NATIVE_MAX: Final[int] = 32766
A4_F1_NATIVE_DEFAULT: Final[int] = 32512
A4_F1_NATIVE_SCALE: Final[int] = 256
A4_F1_DISPLAY_SCALE: Final[int] = 100
A4_F1_WIRE14_MAX: Final[int] = 16383
A4_F1_DATA_BYTE_MAX: Final[int] = 127
A4_F1_LOW_BYTE_MASK: Final[int] = 0xFF
A4_F1_HIGH_BYTE_MASK: Final[int] = 0xFF00
A4_F1_NRPN_NULL_ADDRESS_HALF: Final[int] = 127
A4_F1_NRPN_DATA_LSB_CC: Final[int] = 38
A4_F1_CURRENT_WORD_OFFSET: Final[int] = 0x58
A4_F1_SERIALIZED_SOUND_OFFSET: Final[int] = wire_address_to_track_raw_offset(
    A4_WIRE_ADDRESSES["filter1_frequency"]
)
A4_F1_KIT_BODY_OFFSETS: Final[tuple[int, ...]] = tuple(
    A4_KIT_OBJECT_TRACKS_OFFSET
    + A4_F1_SERIALIZED_SOUND_OFFSET
    + A4_KIT_OBJECT_TRACK_SOUND_SIZE * track
    for track in range(A4_KIT_SYNTH_TRACK_COUNT)
)

A4_F1_RESEARCH_OS: Final[str] = "1.55"
A4_F1_EVIDENCE_SCOPE: Final[str] = "source_static_and_retained_mapping"
A4_F1_MAIN_SHA256: Final[str] = "88b2a9cbac40cb6c8696e5e09a93c2b3b0603f7d09463883c22462cc10d29846"
A4_F1_RESEARCH_ARTIFACTS: Final[tuple[tuple[str, str], ...]] = (
    (
        "value/conversion_contract.json",
        "fb578c5c5fcbc12a8f70cae95f11c6122dafa698fc20e7c3e5f9f184264332e9",
    ),
    (
        "value/reference_converter.py",
        "588acf6bb776c36edfe54e09cd16dd3207d47bdd821a841709e3d87c3b4b1926",
    ),
    (
        "value/boundary_vectors.json",
        "023038410a98c903308a73d39003f451852d568cdc2b803324cbfa6a99506722",
    ),
    (
        "working_state/REVIEW_VALUE_INPUT.md",
        "dc152421b8b74090d73180392ff7fa4bb6b1a4f42cfd0fe8980ad65de3e9f6e4",
    ),
)
