"""Shared offline-only renderer for calibrated Analog Four saved-KIT fields."""

from __future__ import annotations

import hashlib
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Final, Literal, TypeGuard, cast

from ...data.analog_four_saved_kit_layout import A4_SAVED_KIT_LENGTH_ADJUSTMENT
from ...data.analog_four_sysex_calibration import (
    A4_SYSEX_CALIBRATION_STATUS_OFFLINE_CAPTURED_KIT_MUTATION_VALIDATED,
    AnalogFourSysexFieldCalibration,
    analog_four_sysex_calibration_for,
)
from ...snapshot import extract_sysex_payloads
from .analog_four_kit_fields import A4Kit
from .analog_four_saved_kit_codec import (
    AnalogFourSavedKitPayload,
    decode_analog_four_saved_kit_payload,
    encode_analog_four_saved_kit_payload,
)

_SYSEX_START: Final[int] = 0xF0
_SYSEX_END: Final[int] = 0xF7


@dataclass(frozen=True)
class AnalogFourSavedKitCandidateMutation:
    """One local-only edit to a calibrated fixed-point field."""

    parameter: str
    track: int
    screen_value: str


@dataclass(frozen=True)
class AnalogFourSavedKitCandidateAppliedMutation:
    """One Q8.8 mutation resolved and re-decoded at exact native offsets."""

    parameter: str
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
class AnalogFourSavedKitCandidateResult:
    """Validated local bytes; this result cannot grant hardware output authority."""

    kit_name: str
    framed_sysex: bytes
    applied_mutations: tuple[AnalogFourSavedKitCandidateAppliedMutation, ...]
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
    output_authority: Literal["local-file-only"] = field(default="local-file-only", init=False)
    hardware_send_validated: Literal[False] = field(default=False, init=False)


def _validated_candidate_source(source_sysex: bytes) -> AnalogFourSavedKitPayload:
    if not source_sysex or source_sysex[0] != _SYSEX_START or source_sysex[-1] != _SYSEX_END:
        raise ValueError("Analog Four saved kit must be supplied as a framed F0/F7 SysEx file")
    payloads = extract_sysex_payloads(source_sysex)
    if len(payloads) != 1:
        raise ValueError("Analog Four saved-KIT candidate requires exactly one SysEx frame")
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


@dataclass(frozen=True)
class _PreparedCandidateMutation:
    mutation: AnalogFourSavedKitCandidateMutation
    calibration: AnalogFourSysexFieldCalibration
    field_name: str
    raw: int
    offsets: tuple[int, int]


def _is_candidate_mutation(value: object) -> TypeGuard[AnalogFourSavedKitCandidateMutation]:
    return isinstance(value, AnalogFourSavedKitCandidateMutation)


def _prepare_candidate_mutations(
    mutations: Sequence[AnalogFourSavedKitCandidateMutation],
) -> tuple[_PreparedCandidateMutation, ...]:
    seen: set[tuple[str, int]] = set()
    prepared: list[_PreparedCandidateMutation] = []
    for mutation in mutations:
        if not _is_candidate_mutation(mutation):
            raise TypeError("mutations must contain AnalogFourSavedKitCandidateMutation records")
        calibration = analog_four_sysex_calibration_for(mutation.parameter)
        if calibration.parameter != mutation.parameter:
            raise ValueError("requested parameter disagrees with calibration identity")
        if not calibration.offline_saved_kit_mutation_validated:
            raise ValueError(f"{mutation.parameter} is not offline-captured-kit-mutation-validated")
        start = calibration.native_offset_for_track(mutation.track)
        key = (mutation.parameter, mutation.track)
        if key in seen:
            raise ValueError(f"duplicate {mutation.parameter} mutation for track {mutation.track}")
        seen.add(key)
        # native_offset_for_track rejects descriptors without a mapped field.
        field_name = cast(str, calibration.native_field)
        prepared.append(
            _PreparedCandidateMutation(
                mutation=mutation,
                calibration=calibration,
                field_name=field_name,
                raw=calibration.parse_native_screen_value(mutation.screen_value),
                offsets=(start, start + calibration.native_width - 1),
            )
        )
    return tuple(prepared)


def _applied_mutation(
    item: _PreparedCandidateMutation,
    source: bytes,
    rendered: bytes,
    redecoded: A4Kit,
) -> AnalogFourSavedKitCandidateAppliedMutation:
    raw = redecoded.sound(item.mutation.track - 1).get_fixed_8_8_raw(item.field_name)
    start, end = item.offsets
    return AnalogFourSavedKitCandidateAppliedMutation(
        parameter=item.mutation.parameter,
        track=item.mutation.track,
        requested_screen_value=item.mutation.screen_value,
        redecoded_screen_value=item.calibration.format_native_screen_value(raw),
        raw_q8_8=item.raw,
        redecoded_raw_q8_8=raw,
        native_encoding=item.calibration.native_encoding,
        intended_unpacked_offsets=item.offsets,
        source_unpacked_bytes=source[start : end + 1],
        rendered_unpacked_bytes=rendered[start : end + 1],
    )


def render_analog_four_saved_kit_candidate(
    source_sysex: bytes,
    mutations: Sequence[AnalogFourSavedKitCandidateMutation],
) -> AnalogFourSavedKitCandidateResult:
    """Render only offline-promoted fields through the shared copy-on-edit KIT view."""

    source = _validated_candidate_source(source_sysex)
    pending = _prepare_candidate_mutations(mutations)
    kit = A4Kit.from_bytes(source.unpacked)
    for item in pending:
        sound = kit.sound(item.mutation.track - 1)
        sound.set_fixed_8_8_raw(item.field_name, item.raw)
        kit.replace_sound(item.mutation.track - 1, sound)
    rendered_native = kit.to_bytes()
    encoded = encode_analog_four_saved_kit_payload(source.prefix, rendered_native)
    redecoded = decode_analog_four_saved_kit_payload(encoded.payload, require_trailer=True)
    framed_sysex = bytes((_SYSEX_START,)) + encoded.payload + bytes((_SYSEX_END,))
    intended = tuple(sorted({offset for item in pending for offset in item.offsets}))
    changed = tuple(
        index
        for index, (before, after) in enumerate(zip(source.unpacked, rendered_native, strict=True))
        if before != after
    )
    wire_changed = tuple(
        index
        for index, (before, after) in enumerate(zip(source_sysex, framed_sysex, strict=True))
        if before != after
    )
    redecoded_kit = A4Kit.from_bytes(redecoded.unpacked)
    return AnalogFourSavedKitCandidateResult(
        kit_name=source.kit_name,
        framed_sysex=framed_sysex,
        applied_mutations=tuple(
            _applied_mutation(item, source.unpacked, rendered_native, redecoded_kit)
            for item in pending
        ),
        source_checksum=source.checksum,
        rendered_checksum=encoded.checksum,
        packed_length=len(encoded.packed),
        encoded_length=len(encoded.packed) + A4_SAVED_KIT_LENGTH_ADJUSTMENT,
        source_sha256=hashlib.sha256(source_sysex).hexdigest(),
        sha256=hashlib.sha256(framed_sysex).hexdigest(),
        intended_unpacked_offsets=intended,
        changed_unpacked_offsets=changed,
        changed_wire_offsets=wire_changed,
        roundtrip_redecoded=redecoded.unpacked == rendered_native,
        native_byte_isolation_validated=set(changed).issubset(intended),
    )


__all__ = [
    "AnalogFourSavedKitCandidateAppliedMutation",
    "AnalogFourSavedKitCandidateMutation",
    "AnalogFourSavedKitCandidateResult",
    "render_analog_four_saved_kit_candidate",
]
