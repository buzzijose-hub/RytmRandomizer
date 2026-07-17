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
from typing import Final

from rytm_randomizer.data.analog_four_sysex_calibration import (
    A4_SYSEX_CALIBRATION_STATUS_CANDIDATE_PROMOTED,
    A4_SYSEX_CALIBRATION_STATUS_HARDWARE_WRITE_VALIDATED,
    AnalogFourSysexFieldCalibration,
    analog_four_sysex_calibration_for,
)
from rytm_randomizer.snapshot import (
    ELEKTRON_MFR_ID,
    extract_sysex_payloads,
    pack_elektron_7bit,
    read_ascii_name,
    unpack_elektron_7bit,
)

from .analog_four_offset_manifest import (
    A4_CHECKSUM_PACKED_OFFSET,
    A4_FAMILY_BYTE,
    A4_KIT_NAME_LENGTH,
    A4_KIT_NAME_OFFSET,
    A4_KIT_OBJECT_BYTE,
    A4_PACKED_PAYLOAD_OFFSET,
    A4_SAVED_KIT_TRAILER_SIZE,
    A4_SAVED_KIT_UNPACKED_SIZE,
)

_SYSEX_START: Final[int] = 0xF0
_SYSEX_END: Final[int] = 0xF7
_U14_MAX: Final[int] = 0x3FFF
_SUPPORTED_CALIBRATION_STATUSES = frozenset(
    {
        A4_SYSEX_CALIBRATION_STATUS_CANDIDATE_PROMOTED,
        A4_SYSEX_CALIBRATION_STATUS_HARDWARE_WRITE_VALIDATED,
    }
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


def _decode_u14(high: int, low: int) -> int:
    return (high << 7) | low


def _encode_u14(value: int) -> bytes:
    return bytes(((value >> 7) & 0x7F, value & 0x7F))


def _checksum(packed: bytes) -> int:
    return sum(packed[A4_CHECKSUM_PACKED_OFFSET:]) & _U14_MAX


def _raw_low7_for_screen_value(
    calibration: AnalogFourSysexFieldCalibration,
    screen_value: str,
) -> int:
    captured = calibration.primary_raw_values.get(screen_value)
    if captured is not None:
        return captured

    integer_scale = "." not in calibration.screen_min and "." not in calibration.screen_max
    if integer_scale:
        try:
            parsed = int(screen_value)
        except ValueError as exc:
            raise ValueError(
                f"unsupported screen value {screen_value!r} for {calibration.parameter}"
            ) from exc
        if str(parsed) == screen_value and 0 <= parsed <= 0x7F:
            return parsed

    raise ValueError(f"unsupported screen value {screen_value!r} for {calibration.parameter}")


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


def _validated_source(source_sysex: bytes) -> tuple[bytes, bytes, bytes, int]:
    if not source_sysex or source_sysex[0] != _SYSEX_START or source_sysex[-1] != _SYSEX_END:
        raise ValueError("Analog Four saved kit must be supplied as a framed F0/F7 SysEx file")

    payloads = extract_sysex_payloads(source_sysex)
    if len(payloads) != 1:
        raise ValueError("Analog Four saved-kit writer requires exactly one SysEx frame")

    payload = payloads[0]
    if source_sysex != bytes((_SYSEX_START,)) + payload + bytes((_SYSEX_END,)):
        raise ValueError("Analog Four saved-kit writer requires exactly one isolated SysEx frame")
    if not payload.startswith(ELEKTRON_MFR_ID):
        raise ValueError("SysEx manufacturer is not Elektron 00:20:3C")
    if len(payload) <= A4_PACKED_PAYLOAD_OFFSET + A4_SAVED_KIT_TRAILER_SIZE:
        raise ValueError("Analog Four saved-kit payload is too short")
    if payload[len(ELEKTRON_MFR_ID)] != A4_FAMILY_BYTE:
        raise ValueError("SysEx family is not Analog Four 0x06")

    packed = payload[A4_PACKED_PAYLOAD_OFFSET:-A4_SAVED_KIT_TRAILER_SIZE]
    trailer = payload[-A4_SAVED_KIT_TRAILER_SIZE:]
    stored_checksum = _decode_u14(trailer[0], trailer[1])
    if stored_checksum != _checksum(packed):
        raise ValueError("Analog Four saved-kit checksum does not match the packed payload")
    stored_length = _decode_u14(trailer[2], trailer[3])
    if stored_length != len(packed):
        raise ValueError("Analog Four saved-kit packed length does not match its trailer")

    unpacked = unpack_elektron_7bit(packed)
    if len(unpacked) != A4_SAVED_KIT_UNPACKED_SIZE:
        raise ValueError(
            "Analog Four saved-kit unpacked payload has unexpected length "
            f"{len(unpacked)}; expected {A4_SAVED_KIT_UNPACKED_SIZE}"
        )
    if unpacked[0] != A4_KIT_OBJECT_BYTE:
        raise ValueError("Analog Four SysEx object is not a saved kit")
    return payload[:A4_PACKED_PAYLOAD_OFFSET], packed, unpacked, stored_checksum


def render_analog_four_saved_kit(
    source_sysex: bytes,
    mutations: Sequence[AnalogFourSavedKitMutation],
) -> AnalogFourSavedKitRenderResult:
    """Render calibrated mutations into one validated A4 saved-kit frame."""

    if not mutations:
        raise ValueError("Analog Four saved-kit rendering requires at least one mutation")

    prefix, source_packed, source_unpacked, source_checksum = _validated_source(source_sysex)
    rendered_unpacked = bytearray(source_unpacked)
    seen: set[tuple[str, int]] = set()
    applied: list[AnalogFourSavedKitAppliedMutation] = []

    for mutation in mutations:
        if not isinstance(mutation, AnalogFourSavedKitMutation):
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
                f"{mutation.parameter} calibration is not promoted for saved-kit writing"
            )
        raw_low7 = _raw_low7_for_screen_value(calibration, mutation.screen_value)
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

    rendered_packed = pack_elektron_7bit(bytes(rendered_unpacked))
    if len(rendered_packed) != len(source_packed):
        raise ValueError("Analog Four saved-kit repacking changed the packed payload length")
    rendered_checksum = _checksum(rendered_packed)
    trailer = _encode_u14(rendered_checksum) + _encode_u14(len(rendered_packed))
    framed_sysex = (
        bytes((_SYSEX_START,)) + prefix + rendered_packed + trailer + bytes((_SYSEX_END,))
    )
    kit_name = read_ascii_name(bytes(rendered_unpacked), A4_KIT_NAME_OFFSET, A4_KIT_NAME_LENGTH)

    return AnalogFourSavedKitRenderResult(
        kit_name=kit_name,
        framed_sysex=framed_sysex,
        applied_mutations=tuple(applied),
        source_checksum=source_checksum,
        rendered_checksum=rendered_checksum,
        packed_length=len(rendered_packed),
        sha256=hashlib.sha256(framed_sysex).hexdigest(),
    )


__all__ = [
    "AnalogFourSavedKitAppliedMutation",
    "AnalogFourSavedKitMutation",
    "AnalogFourSavedKitRenderResult",
    "render_analog_four_saved_kit",
]
