"""Offline-only Analog Four Filter 1 Frequency saved-KIT candidate renderer.

This module deliberately does not extend the hardware-validated saved-KIT
writer. It renders local candidate bytes from captured KIT anchors and carries
an explicit false hardware-send verdict. It performs no file or MIDI I/O.
"""

from __future__ import annotations

import hashlib
from collections.abc import Sequence
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Final, Literal, TypeGuard

from ...data.analog_four_saved_kit_layout import A4_SAVED_KIT_LENGTH_ADJUSTMENT
from ...data.analog_four_sysex_calibration import (
    A4_FILTER1_FREQUENCY_ENCODING,
    A4_FILTER1_FREQUENCY_NATIVE_WIDTH,
    A4_FILTER1_FREQUENCY_PARAMETER,
    A4_FILTER1_FREQUENCY_Q8_8_SCALE,
    A4_FILTER1_FREQUENCY_RAW_MAX,
    A4_FILTER1_FREQUENCY_RAW_MIN,
    A4_FILTER1_FREQUENCY_TRACK_1_UNPACKED_OFFSET,
    A4_FILTER1_FREQUENCY_TRACK_UNPACKED_STRIDE,
    A4_SYSEX_CALIBRATION_STATUS_OFFLINE_CAPTURED_KIT_MUTATION_VALIDATED,
    analog_four_sysex_calibration_for,
    format_analog_four_filter1_frequency_screen_value,
)
from ...snapshot import extract_sysex_payloads
from .analog_four_saved_kit_codec import (
    AnalogFourSavedKitPayload,
    decode_analog_four_saved_kit_payload,
    encode_analog_four_saved_kit_payload,
)

_SYSEX_START: Final[int] = 0xF0
_SYSEX_END: Final[int] = 0xF7
_Q8_8_MIN: Final[Decimal] = Decimal(A4_FILTER1_FREQUENCY_RAW_MIN // A4_FILTER1_FREQUENCY_Q8_8_SCALE)
_Q8_8_MAX: Final[Decimal] = Decimal(A4_FILTER1_FREQUENCY_RAW_MAX // A4_FILTER1_FREQUENCY_Q8_8_SCALE)
_Q8_8_STEP: Final[Decimal] = Decimal("0.00390625")


@dataclass(frozen=True)
class AnalogFourFilter1FrequencyCandidateMutation:
    """One local-only Filter 1 Frequency edit for an A4 synth track."""

    track: int
    screen_value: str


@dataclass(frozen=True)
class AnalogFourFilter1FrequencyCandidateAppliedMutation:
    """One Q8.8 mutation resolved and re-decoded at exact native offsets."""

    track: int
    requested_screen_value: str
    redecoded_screen_value: str
    raw_q8_8: int
    redecoded_raw_q8_8: int
    native_encoding: str
    intended_unpacked_offsets: tuple[int, int]
    source_unpacked_bytes: bytes
    rendered_unpacked_bytes: bytes


@dataclass(frozen=True)
class AnalogFourFilter1FrequencyCandidateResult:
    """Validated local candidate bytes and their native-byte audit record."""

    kit_name: str
    framed_sysex: bytes
    applied_mutations: tuple[AnalogFourFilter1FrequencyCandidateAppliedMutation, ...]
    source_checksum: int
    rendered_checksum: int
    packed_length: int
    encoded_length: int
    source_sha256: str
    sha256: str
    intended_unpacked_offsets: tuple[int, ...]
    changed_unpacked_offsets: tuple[int, ...]
    changed_wire_offsets: tuple[int, ...]
    roundtrip_redecoded: bool
    native_byte_isolation_validated: bool
    validation_status: str = field(
        default=A4_SYSEX_CALIBRATION_STATUS_OFFLINE_CAPTURED_KIT_MUTATION_VALIDATED,
        init=False,
    )
    output_authority: Literal["local-file-only"] = field(
        default="local-file-only",
        init=False,
    )
    hardware_send_validated: Literal[False] = field(default=False, init=False)


def is_analog_four_filter1_frequency_candidate_mutation(
    value: object,
) -> TypeGuard[AnalogFourFilter1FrequencyCandidateMutation]:
    """Return whether ``value`` is the narrow offline mutation record."""

    return isinstance(value, AnalogFourFilter1FrequencyCandidateMutation)


def _validated_filter1_candidate_source(
    source_sysex: bytes,
) -> AnalogFourSavedKitPayload:
    if not source_sysex or source_sysex[0] != _SYSEX_START or source_sysex[-1] != _SYSEX_END:
        raise ValueError("Analog Four saved kit must be supplied as a framed F0/F7 SysEx file")

    payloads = extract_sysex_payloads(source_sysex)
    if len(payloads) != 1:
        raise ValueError(
            "Analog Four Filter 1 Frequency candidate requires exactly one SysEx frame"
        )
    payload = payloads[0]
    if source_sysex != bytes((_SYSEX_START,)) + payload + bytes((_SYSEX_END,)):
        raise ValueError(
            "Analog Four candidate source must contain exactly one isolated SysEx frame"
        )
    decoded = decode_analog_four_saved_kit_payload(payload, require_trailer=True)
    reencoded = encode_analog_four_saved_kit_payload(decoded.prefix, decoded.unpacked)
    if reencoded.payload != payload:
        raise ValueError("Analog Four candidate source must round-trip byte-identically")
    return decoded


def _q8_8_for_screen(screen_value: str) -> int:
    try:
        parsed = Decimal(screen_value)
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError(
            f"unsupported screen value {screen_value!r} for {A4_FILTER1_FREQUENCY_PARAMETER}"
        ) from exc
    if not parsed.is_finite():
        raise ValueError(
            f"unsupported screen value {screen_value!r} for {A4_FILTER1_FREQUENCY_PARAMETER}"
        )

    if parsed < _Q8_8_MIN or parsed > _Q8_8_MAX or 0 < parsed < _Q8_8_STEP:
        raise ValueError(
            f"unsupported screen value {screen_value!r} for {A4_FILTER1_FREQUENCY_PARAMETER}; "
            "expected an exactly representable unsigned Q8.8 value from 0.00 to 127.00"
        )

    # Decimal arithmetic obeys ambient precision and can round an inexact
    # request onto the Q8.8 grid. Integer ratios preserve every input digit.
    numerator, denominator = parsed.as_integer_ratio()
    raw_q8_8, remainder = divmod(numerator * A4_FILTER1_FREQUENCY_Q8_8_SCALE, denominator)
    if remainder:
        raise ValueError(
            f"unsupported screen value {screen_value!r} for {A4_FILTER1_FREQUENCY_PARAMETER}; "
            "expected an exactly representable unsigned Q8.8 value from 0.00 to 127.00"
        )
    return raw_q8_8


def _intended_offsets_for_track(track: int) -> tuple[int, int]:
    calibration = analog_four_sysex_calibration_for(A4_FILTER1_FREQUENCY_PARAMETER)
    if calibration.status != A4_SYSEX_CALIBRATION_STATUS_OFFLINE_CAPTURED_KIT_MUTATION_VALIDATED:
        raise ValueError(
            f"{A4_FILTER1_FREQUENCY_PARAMETER} is not offline-captured-kit-mutation-validated"
        )
    calibration.primary_raw_offset_for_track(track)
    start = A4_FILTER1_FREQUENCY_TRACK_1_UNPACKED_OFFSET + (
        (track - 1) * A4_FILTER1_FREQUENCY_TRACK_UNPACKED_STRIDE
    )
    return start, start + A4_FILTER1_FREQUENCY_NATIVE_WIDTH - 1


def render_analog_four_filter1_frequency_candidate(
    source_sysex: bytes,
    mutations: Sequence[AnalogFourFilter1FrequencyCandidateMutation],
) -> AnalogFourFilter1FrequencyCandidateResult:
    """Render a validated local-only Filter 1 Frequency saved-KIT candidate."""

    source = _validated_filter1_candidate_source(source_sysex)
    rendered_unpacked = bytearray(source.unpacked)
    seen_tracks: set[int] = set()
    pending: list[
        tuple[AnalogFourFilter1FrequencyCandidateMutation, int, tuple[int, int], bytes]
    ] = []

    for mutation in mutations:
        if not is_analog_four_filter1_frequency_candidate_mutation(mutation):
            raise TypeError(
                "mutations must contain AnalogFourFilter1FrequencyCandidateMutation records"
            )
        if mutation.track in seen_tracks:
            raise ValueError(f"duplicate Filter 1 Frequency mutation for track {mutation.track}")
        seen_tracks.add(mutation.track)

        intended_offsets = _intended_offsets_for_track(mutation.track)
        raw_q8_8 = _q8_8_for_screen(mutation.screen_value)
        rendered_bytes = raw_q8_8.to_bytes(
            A4_FILTER1_FREQUENCY_NATIVE_WIDTH,
            byteorder="big",
        )
        source_bytes = bytes(source.unpacked[offset] for offset in intended_offsets)
        start = intended_offsets[0]
        rendered_unpacked[start : start + A4_FILTER1_FREQUENCY_NATIVE_WIDTH] = rendered_bytes
        pending.append((mutation, raw_q8_8, intended_offsets, source_bytes))

    rendered_native = bytes(rendered_unpacked)
    encoded = encode_analog_four_saved_kit_payload(source.prefix, rendered_native)
    redecoded = decode_analog_four_saved_kit_payload(encoded.payload, require_trailer=True)
    framed_sysex = bytes((_SYSEX_START,)) + encoded.payload + bytes((_SYSEX_END,))
    intended_unpacked_offsets = tuple(
        sorted({offset for _, _, offsets, _ in pending for offset in offsets})
    )
    changed_unpacked_offsets = tuple(
        index
        for index, (before, after) in enumerate(zip(source.unpacked, rendered_native, strict=True))
        if before != after
    )
    changed_wire_offsets = tuple(
        index
        for index, (before, after) in enumerate(zip(source_sysex, framed_sysex, strict=True))
        if before != after
    )
    applied = tuple(
        AnalogFourFilter1FrequencyCandidateAppliedMutation(
            track=mutation.track,
            requested_screen_value=mutation.screen_value,
            redecoded_screen_value=format_analog_four_filter1_frequency_screen_value(
                int.from_bytes(redecoded.unpacked[offsets[0] : offsets[1] + 1], byteorder="big")
            ),
            raw_q8_8=raw_q8_8,
            redecoded_raw_q8_8=int.from_bytes(
                redecoded.unpacked[offsets[0] : offsets[1] + 1], byteorder="big"
            ),
            native_encoding=A4_FILTER1_FREQUENCY_ENCODING,
            intended_unpacked_offsets=offsets,
            source_unpacked_bytes=source_bytes,
            rendered_unpacked_bytes=rendered_native[offsets[0] : offsets[1] + 1],
        )
        for mutation, raw_q8_8, offsets, source_bytes in pending
    )

    return AnalogFourFilter1FrequencyCandidateResult(
        kit_name=source.kit_name,
        framed_sysex=framed_sysex,
        applied_mutations=applied,
        source_checksum=source.checksum,
        rendered_checksum=encoded.checksum,
        packed_length=len(encoded.packed),
        encoded_length=len(encoded.packed) + A4_SAVED_KIT_LENGTH_ADJUSTMENT,
        source_sha256=hashlib.sha256(source_sysex).hexdigest(),
        sha256=hashlib.sha256(framed_sysex).hexdigest(),
        intended_unpacked_offsets=intended_unpacked_offsets,
        changed_unpacked_offsets=changed_unpacked_offsets,
        changed_wire_offsets=changed_wire_offsets,
        roundtrip_redecoded=redecoded.unpacked == rendered_native,
        native_byte_isolation_validated=set(changed_unpacked_offsets).issubset(
            intended_unpacked_offsets
        ),
    )


__all__ = [
    "AnalogFourFilter1FrequencyCandidateAppliedMutation",
    "AnalogFourFilter1FrequencyCandidateMutation",
    "AnalogFourFilter1FrequencyCandidateResult",
    "is_analog_four_filter1_frequency_candidate_mutation",
    "render_analog_four_filter1_frequency_candidate",
]
