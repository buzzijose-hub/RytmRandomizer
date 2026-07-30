"""Pure Analog Four MKII saved-kit SysEx renderer.

The renderer accepts exactly one framed, hardware-exported saved kit, applies
calibrated synth-track mutations to its unpacked payload, then rebuilds the
Elektron 7-bit packing, checksum, length trailer, and SysEx framing. It never
opens a MIDI port and performs no file I/O.
"""

from __future__ import annotations

import hashlib
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final, TypeGuard

from ...data.analog_four_saved_kit_layout import (
    A4_PACKED_PAYLOAD_OFFSET,
)
from ...data.analog_four_sysex_calibration import (
    A4_SYSEX_CALIBRATION_STATUS_HARDWARE_WRITE_VALIDATED,
    AnalogFourSysexFieldCalibration,
    analog_four_sysex_calibration_for,
)
from ...snapshot import extract_sysex_payloads
from .analog_four_saved_kit_codec import (
    AnalogFourSavedKitPayload,
    decode_analog_four_saved_kit_payload,
    encode_analog_four_saved_kit_payload,
)

_SYSEX_START: Final[int] = 0xF0
_SYSEX_END: Final[int] = 0xF7
_SUPPORTED_CALIBRATION_STATUSES: Final[frozenset[str]] = frozenset(
    {A4_SYSEX_CALIBRATION_STATUS_HARDWARE_WRITE_VALIDATED}
)


@dataclass(frozen=True)
class AnalogFourSavedKitMutation:
    """One calibrated A4 screen-value change for a synth track."""

    parameter: str
    track: int
    screen_value: str


@dataclass(frozen=True)
class AnalogFourSavedKitAppliedMutation:
    """One mutation resolved to its concrete unpacked payload byte."""

    parameter: str
    track: int
    screen_value: str
    unpacked_offset: int
    source_unpacked_value: int
    rendered_unpacked_value: int


@dataclass(frozen=True)
class AnalogFourSavedKitRenderResult:
    """Validated bytes and audit metadata for one rendered saved kit."""

    kit_name: str
    framed_sysex: bytes
    applied_mutations: tuple[AnalogFourSavedKitAppliedMutation, ...]
    source_checksum: int
    rendered_checksum: int
    packed_length: int
    sha256: str


def is_analog_four_saved_kit_mutation(
    value: object,
) -> TypeGuard[AnalogFourSavedKitMutation]:
    return isinstance(value, AnalogFourSavedKitMutation)


def _unpacked_offset_for_calibration(
    calibration: AnalogFourSysexFieldCalibration,
    track: int,
) -> int:
    packed_body_offset = calibration.primary_raw_offset_for_track(track) - A4_PACKED_PAYLOAD_OFFSET
    group_index, position = divmod(packed_body_offset, 8)
    if position == 0:
        raise ValueError(
            f"{calibration.parameter} primary offset points to a packed group header; "
            "direct saved-kit mutation is not yet validated"
        )
    return (group_index * 7) + position - 1


def _validated_source(source_sysex: bytes) -> AnalogFourSavedKitPayload:
    if not source_sysex or source_sysex[0] != _SYSEX_START or source_sysex[-1] != _SYSEX_END:
        raise ValueError("Analog Four saved kit must be supplied as a framed F0/F7 SysEx file")

    payloads = extract_sysex_payloads(source_sysex)
    if len(payloads) != 1:
        raise ValueError("Analog Four saved-kit writer requires exactly one SysEx frame")

    payload = payloads[0]
    if source_sysex != bytes((_SYSEX_START,)) + payload + bytes((_SYSEX_END,)):
        raise ValueError("Analog Four saved-kit writer requires exactly one isolated SysEx frame")
    return decode_analog_four_saved_kit_payload(payload, require_trailer=True)


def render_analog_four_saved_kit(
    source_sysex: bytes,
    mutations: Sequence[AnalogFourSavedKitMutation],
) -> AnalogFourSavedKitRenderResult:
    """Render calibrated mutations into one validated A4 saved-kit frame."""

    if not mutations:
        raise ValueError("Analog Four saved-kit rendering requires at least one mutation")

    source = _validated_source(source_sysex)
    rendered_unpacked = bytearray(source.unpacked)
    seen: set[tuple[str, int]] = set()
    applied: list[AnalogFourSavedKitAppliedMutation] = []

    for mutation in mutations:
        if not is_analog_four_saved_kit_mutation(mutation):
            raise TypeError("mutations must contain AnalogFourSavedKitMutation records")
        key = (mutation.parameter, mutation.track)
        if key in seen:
            raise ValueError(
                f"duplicate mutation for {mutation.parameter} on track {mutation.track}"
            )
        seen.add(key)

        calibration = analog_four_sysex_calibration_for(mutation.parameter)
        if calibration.status not in _SUPPORTED_CALIBRATION_STATUSES:
            raise ValueError(
                f"{mutation.parameter} calibration is not hardware-write-validated "
                "for saved-kit writing"
            )
        raw_low7 = calibration.primary_raw_value_for_screen(mutation.screen_value)
        unpacked_offset = _unpacked_offset_for_calibration(calibration, mutation.track)
        source_value = rendered_unpacked[unpacked_offset]
        rendered_value = (source_value & 0x80) | raw_low7
        rendered_unpacked[unpacked_offset] = rendered_value
        applied.append(
            AnalogFourSavedKitAppliedMutation(
                parameter=mutation.parameter,
                track=mutation.track,
                screen_value=mutation.screen_value,
                unpacked_offset=unpacked_offset,
                source_unpacked_value=source_value,
                rendered_unpacked_value=rendered_value,
            )
        )

    encoded = encode_analog_four_saved_kit_payload(source.prefix, bytes(rendered_unpacked))
    framed_sysex = bytes((_SYSEX_START,)) + encoded.payload + bytes((_SYSEX_END,))

    return AnalogFourSavedKitRenderResult(
        kit_name=source.kit_name,
        framed_sysex=framed_sysex,
        applied_mutations=tuple(applied),
        source_checksum=source.checksum,
        rendered_checksum=encoded.checksum,
        packed_length=len(encoded.packed),
        sha256=hashlib.sha256(framed_sysex).hexdigest(),
    )


__all__ = [
    "AnalogFourSavedKitAppliedMutation",
    "AnalogFourSavedKitMutation",
    "AnalogFourSavedKitRenderResult",
    "is_analog_four_saved_kit_mutation",
    "render_analog_four_saved_kit",
]
