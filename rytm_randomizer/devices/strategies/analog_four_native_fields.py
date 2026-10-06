"""Evidence-backed, source-preserving A4 native fields. No transport authority."""

from __future__ import annotations

import hashlib
from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import Enum
from typing import Final, Literal, TypeGuard

from ...data.analog_four_kit_fields import (
    A4_BIPOLAR_FIELDS,
    A4_FIXED_8_8_SCALE,
    A4_MOD_DEPTH_FIELDS,
    A4_NATIVE_CONTINUOUS_U7_FIELDS,
    A4_TRACK_OFFSETS,
    A4_TWO_BYTE_FIELDS,
    format_a4_fixed_8_8,
)
from ...data.analog_four_saved_kit_layout import (
    A4_KIT_OBJECT_TRACK_SOUND_SIZE,
    A4_KIT_OBJECT_TRACKS_OFFSET,
)
from .analog_four_kit_fields import (
    A4_MOD_DEPTH_ZERO,
    A4_PITCH_UNITS_PER_SEMITONE,
    A4_PITCH_ZERO,
    A4Destination,
    A4Kit,
    A4Sound,
    decode_a4_mod_depth,
    decode_a4_pitch_components,
)
from .analog_four_kit_recipe import A4_RECIPE_ENUM_FIELDS
from .analog_four_saved_kit_candidate import (
    encode_analog_four_candidate_patch,
    validate_analog_four_candidate_source,
)
from .analog_four_track_domain import AnalogFourTrackDomain

_TRACKS: Final[AnalogFourTrackDomain] = AnalogFourTrackDomain(4)
_RIO_EVIDENCE: Final[tuple[str, ...]] = (
    "tests/fixtures/rio145/A4_Test1_Init_Kit.syx",
    "tests/fixtures/rio145/A4_RIO145_CORE_RETURN_Kit.syx",
    "specs/rio145/come_to_rio_a4_core.json",
)
_PITCH_EVIDENCE: Final[tuple[str, ...]] = (
    *_RIO_EVIDENCE,
    "tests/fixtures/rio145/A4_Test2_T1_OSC1_FIN_P1_Kit.syx",
    "tests/fixtures/rio145/A4_Test3_T1_OSC1_FIN_M1_Kit.syx",
    "tests/fixtures/rio145/A4_Test6_T1_OSC1_FIN_P2_Kit.syx",
    "tests/fixtures/rio145/A4_Test7_T1_OSC1_FIN_M2_Kit.syx",
)
_DEPTH_EVIDENCE: Final[tuple[str, ...]] = (
    *_RIO_EVIDENCE,
    "tests/fixtures/rio145/A4_Test4_T1_ENV2_DEPA_P1_Kit.syx",
    "tests/fixtures/rio145/A4_Test5_T1_ENV2_DEPA_M1_Kit.syx",
)


class AnalogFourNativeEncoding(str, Enum):
    U7 = "unsigned-native-u7"
    BIPOLAR = "centered-64-native-u7"
    ENUM = "native-enum-u7"
    Q8_8 = "unsigned-big-endian-q8.8"
    MOD_DEPTH = "centered-16384-big-endian-q8.7"
    TUNE = "centered-16384-pitch-preserve-fine"
    FINE = "coupled-pitch-fine-read-only"
    UNKNOWN = "unestablished-native-domain"


@dataclass(frozen=True)
class AnalogFourNativeDomain:
    """An exact encoded-native grid, or an explicit non-contiguous enum set."""

    minimum: int
    maximum: int
    quantum: int = 1
    values: tuple[int, ...] = ()

    @property
    def value_count(self) -> int:
        return (
            len(self.values) if self.values else (self.maximum - self.minimum) // self.quantum + 1
        )

    def value_at(self, index: int) -> int:
        """Resolve a sampled index without guessing encodings or enum ordinals."""
        if type(index) is not int or not 0 <= index < self.value_count:
            raise ValueError("native domain index outside legal range")
        return self.values[index] if self.values else self.minimum + index * self.quantum

    def index_of(self, encoded_native: int) -> int:
        """Validate an exact value and return its deterministic sampling index."""
        if type(encoded_native) is not int:
            raise ValueError("encoded_native must be a non-boolean integer")
        if self.values:
            if encoded_native not in self.values:
                raise ValueError("unknown native selector")
            return self.values.index(encoded_native)
        if (
            not self.minimum <= encoded_native <= self.maximum
            or (encoded_native - self.minimum) % self.quantum
        ):
            raise ValueError("encoded_native outside exact native domain")
        return (encoded_native - self.minimum) // self.quantum


@dataclass(frozen=True)
class AnalogFourNativeField:
    """Canonical native metadata; this is not a MIDI display/transport mapping."""

    parameter: str
    native_encoding: AnalogFourNativeEncoding
    relative_offsets: tuple[int, ...]
    display_quantum: str | None
    domain: AnalogFourNativeDomain | None
    enum_values: tuple[tuple[int, str], ...]
    protection_reason: str | None
    evidence: tuple[str, ...]

    @property
    def width(self) -> int:
        return len(self.relative_offsets)

    @property
    def mutation_supported(self) -> bool:
        return self.protection_reason is None

    def offsets_for_track(self, track: int) -> tuple[int, ...]:
        checked = _TRACKS.require_track(track, context="A4 native field")
        start = A4_KIT_OBJECT_TRACKS_OFFSET + (checked - 1) * A4_KIT_OBJECT_TRACK_SOUND_SIZE
        return tuple(start + offset for offset in self.relative_offsets)


def analog_four_native_fields() -> tuple[AnalogFourNativeField, ...]:
    """Survey canonical facts once per request; never promote accessor placeholders."""
    fields: list[AnalogFourNativeField] = []
    for parameter, offset in A4_TRACK_OFFSETS.items():
        encoding = AnalogFourNativeEncoding.UNKNOWN
        offsets = (offset,)
        quantum: str | None = None
        domain: AnalogFourNativeDomain | None = None
        enums: tuple[tuple[int, str], ...] = ()
        evidence = _RIO_EVIDENCE
        reason: str | None = None
        if parameter in A4_TWO_BYTE_FIELDS:
            encoding = AnalogFourNativeEncoding.Q8_8
            offsets = (offset, offset + 1)
            quantum = "0.00390625"
            domain = AnalogFourNativeDomain(0, 127 * A4_FIXED_8_8_SCALE)
            if parameter == "filter1_frequency":
                evidence = (
                    *evidence,
                    "tests/fixtures/analog_four_saved_kit/filter1_freq_127_source.syx",
                    "tests/fixtures/analog_four_saved_kit/filter1_freq_000_expected.syx",
                    "tests/fixtures/analog_four_saved_kit/filter1_freq_063_50_expected.syx",
                )
        elif parameter in A4_MOD_DEPTH_FIELDS:
            encoding = AnalogFourNativeEncoding.MOD_DEPTH
            offsets = (offset, A4_TRACK_OFFSETS[A4_MOD_DEPTH_FIELDS[parameter]])
            quantum = "0.0078125"
            domain = AnalogFourNativeDomain(0, 0x7FFF)
            evidence = _DEPTH_EVIDENCE
        elif parameter in ("osc1_tune", "osc2_tune", "osc1_fine", "osc2_fine"):
            oscillator = parameter[3]
            offset = A4_TRACK_OFFSETS[f"osc{oscillator}_tune"]
            offsets = (offset, offset + 1)
            quantum = "1"
            evidence = _PITCH_EVIDENCE
            if parameter.endswith("tune"):
                encoding = AnalogFourNativeEncoding.TUNE
            else:
                encoding = AnalogFourNativeEncoding.FINE
                reason = "independently_unsafe_fine"
        elif parameter in A4_RECIPE_ENUM_FIELDS or "_destination_" in parameter:
            encoding = AnalogFourNativeEncoding.ENUM
            enum_type = A4_RECIPE_ENUM_FIELDS.get(parameter, A4Destination)
            enums = tuple(sorted((int(member), member.name) for member in enum_type))
            values = tuple(value for value, _ in enums)
            domain = AnalogFourNativeDomain(min(values), max(values), values=values)
        elif parameter in A4_BIPOLAR_FIELDS:
            encoding = AnalogFourNativeEncoding.BIPOLAR
            quantum = "1"
            domain = AnalogFourNativeDomain(0, 127)
        elif parameter in A4_NATIVE_CONTINUOUS_U7_FIELDS:
            encoding = AnalogFourNativeEncoding.U7
            quantum = "1"
            domain = AnalogFourNativeDomain(0, 127)
            if parameter == "filter2_resonance":
                evidence = (
                    *evidence,
                    "tests/fixtures/analog_four_saved_kit/filter2_res_000_source.syx",
                    "tests/fixtures/analog_four_saved_kit/filter2_res_127_expected.syx",
                )
        else:
            reason = (
                "hidden_fraction"
                if parameter.endswith("_fraction")
                else "native_domain_unestablished"
            )
            evidence = ()
        if parameter.startswith("amp_"):
            reason = "oxi_amp_protection"
        # Portamento has a codec enum but no retained recipe/cross-track evidence.
        if parameter == "portamento":
            reason = "native_domain_unestablished"
            evidence = ()
        if parameter in ("lfo1_phase", "osc1_sub", "osc2_sub"):
            reason = "native_nondefault_evidence_missing"
        fields.append(
            AnalogFourNativeField(
                parameter, encoding, offsets, quantum, domain, enums, reason, evidence
            )
        )
    return tuple(fields)


@dataclass(frozen=True)
class AnalogFourNativeValue:
    """Exact source-bound native value and legal sampling domain."""

    metadata: AnalogFourNativeField
    track: int
    encoded_native: int
    screen_value: str | None
    unpacked_offsets: tuple[int, ...]
    native_bytes: bytes
    domain: AnalogFourNativeDomain | None
    source_value_known: bool
    protection_reason: str | None

    @property
    def parameter(self) -> str:
        return self.metadata.parameter

    @property
    def mutable(self) -> bool:
        return (
            self.source_value_known and self.protection_reason is None and self.domain is not None
        )


def _pitch_domain(raw: int) -> AnalogFourNativeDomain:
    tune, _, _, residual = decode_a4_pitch_components(raw)
    if not -64 <= tune <= 63:
        raise ValueError("source TUN outside established domain")
    first = A4_PITCH_ZERO - 64 * A4_PITCH_UNITS_PER_SEMITONE + residual
    if first < 0:
        first += A4_PITCH_UNITS_PER_SEMITONE
    last = A4_PITCH_ZERO + 63 * A4_PITCH_UNITS_PER_SEMITONE + residual
    return AnalogFourNativeDomain(first, last, A4_PITCH_UNITS_PER_SEMITONE)


def _screen_value(metadata: AnalogFourNativeField, raw: int) -> str:
    encoding = metadata.native_encoding
    if encoding is AnalogFourNativeEncoding.Q8_8:
        return format_a4_fixed_8_8(raw)
    if encoding is AnalogFourNativeEncoding.MOD_DEPTH:
        delta = raw - A4_MOD_DEPTH_ZERO
        return ("-" if delta < 0 else "") + format_a4_fixed_8_8(abs(delta) * 2, maximum=0x8000)
    if encoding is AnalogFourNativeEncoding.TUNE:
        return str(decode_a4_pitch_components(raw)[0])
    if encoding is AnalogFourNativeEncoding.FINE:
        return str(decode_a4_pitch_components(raw)[1])
    if encoding is AnalogFourNativeEncoding.BIPOLAR:
        return str(raw - 64)
    if encoding is AnalogFourNativeEncoding.ENUM:
        return dict(metadata.enum_values)[raw]
    return str(raw)


def _read_value(
    metadata: AnalogFourNativeField, track: int, unpacked: bytes
) -> AnalogFourNativeValue:
    offsets = metadata.offsets_for_track(track)
    native_bytes = bytes(unpacked[offset] for offset in offsets)
    raw = int.from_bytes(native_bytes, "big")
    domain = metadata.domain
    reason = metadata.protection_reason
    screen: str | None = None
    known = False
    try:
        if metadata.native_encoding is AnalogFourNativeEncoding.TUNE:
            domain = _pitch_domain(raw)
        elif metadata.native_encoding is AnalogFourNativeEncoding.FINE:
            decode_a4_pitch_components(raw)
            screen = _screen_value(metadata, raw)
            known = True
        if domain is not None:
            domain.index_of(raw)
            screen = _screen_value(metadata, raw)
            known = True
    except ValueError:
        domain = None
        reason = reason or "source_value_outside_established_domain"
    return AnalogFourNativeValue(
        metadata, track, raw, screen, offsets, native_bytes, domain, known, reason
    )


@dataclass(frozen=True)
class AnalogFourNativeReadback:
    source_sha256: str
    kit_name: str
    values: tuple[AnalogFourNativeValue, ...]
    output_authority: Literal["local-file-only"] = field(default="local-file-only", init=False)
    hardware_send_validated: Literal[False] = field(default=False, init=False)

    def value(self, parameter: str, track: int) -> AnalogFourNativeValue:
        _TRACKS.require_track(track, context="A4 native readback")
        for value in self.values:
            if value.parameter == parameter and value.track == track:
                return value
        raise ValueError("unknown or foreign Analog Four native field")


def read_analog_four_native_fields(source_sysex: bytes) -> AnalogFourNativeReadback:
    """Read exact native cells; unknown values remain immutable source evidence."""
    source = validate_analog_four_candidate_source(source_sysex)
    kit = A4Kit.from_bytes(source.unpacked)
    for track in _TRACKS.track_ids:
        kit.sound(track - 1)
    fields = analog_four_native_fields()
    return AnalogFourNativeReadback(
        hashlib.sha256(source_sysex).hexdigest(),
        source.kit_name,
        tuple(
            _read_value(metadata, track, source.unpacked)
            for track in _TRACKS.track_ids
            for metadata in fields
        ),
    )


@dataclass(frozen=True)
class AnalogFourNativeMutation:
    parameter: str
    track: int
    encoded_native: int


def _is_native_mutation(value: object) -> TypeGuard[AnalogFourNativeMutation]:
    return isinstance(value, AnalogFourNativeMutation)


@dataclass(frozen=True)
class AnalogFourNativeAppliedMutation:
    source: AnalogFourNativeValue
    rendered: AnalogFourNativeValue


@dataclass(frozen=True)
class AnalogFourNativeCandidateResult:
    source_sha256: str
    sha256: str
    source_framed_sysex: bytes
    framed_sysex: bytes
    source_readback: AnalogFourNativeReadback
    readback: AnalogFourNativeReadback
    applied_mutations: tuple[AnalogFourNativeAppliedMutation, ...]
    intended_unpacked_offsets: tuple[int, ...]
    intended_wire_offsets: tuple[int, ...]
    changed_unpacked_offsets: tuple[int, ...]
    changed_wire_offsets: tuple[int, ...]
    source_checksum: int
    rendered_checksum: int
    roundtrip_redecoded: Literal[True] = field(default=True, init=False)
    native_byte_isolation_validated: Literal[True] = field(default=True, init=False)
    validation_status: Literal["offline-native-field-candidate"] = field(
        default="offline-native-field-candidate", init=False
    )
    output_authority: Literal["local-file-only"] = field(default="local-file-only", init=False)
    hardware_send_validated: Literal[False] = field(default=False, init=False)


def _apply_native_value(sound: A4Sound, source: AnalogFourNativeValue, raw: int) -> None:
    metadata = source.metadata
    encoding = metadata.native_encoding
    parameter = metadata.parameter
    if encoding is AnalogFourNativeEncoding.TUNE:
        sound.set_oscillator_tune(int(parameter[3]), decode_a4_pitch_components(raw)[0])
    elif encoding is AnalogFourNativeEncoding.Q8_8:
        sound.set_fixed_8_8_raw(parameter, raw)
    elif encoding is AnalogFourNativeEncoding.MOD_DEPTH:
        sound.set_mod_depth(parameter, decode_a4_mod_depth(raw))
    elif encoding is AnalogFourNativeEncoding.BIPOLAR:
        sound.set_bipolar(parameter, raw - 64)
    else:
        sound.set_u7(parameter, raw)


def render_analog_four_native_fields(
    source_sysex: bytes, mutations: Sequence[AnalogFourNativeMutation]
) -> AnalogFourNativeCandidateResult:
    """Render selected cells only, retaining unknown bytes and coupled precision."""
    source = validate_analog_four_candidate_source(source_sysex)
    before = read_analog_four_native_fields(source_sysex)
    pending: list[tuple[AnalogFourNativeMutation, AnalogFourNativeValue]] = []
    seen: set[tuple[str, int]] = set()
    for mutation in mutations:
        if not _is_native_mutation(mutation):
            raise TypeError("mutations must contain AnalogFourNativeMutation records")
        value = before.value(mutation.parameter, mutation.track)
        key = (mutation.parameter, mutation.track)
        if key in seen:
            raise ValueError("duplicate Analog Four native field mutation")
        seen.add(key)
        if not value.mutable or value.domain is None:
            raise ValueError(
                f"native field immutable: {value.protection_reason or 'unknown_source'}"
            )
        value.domain.index_of(mutation.encoded_native)
        pending.append((mutation, value))
    kit = A4Kit.from_bytes(source.unpacked)
    approved: set[int] = set()
    for mutation, value in pending:
        sound = kit.sound(mutation.track - 1)
        _apply_native_value(sound, value, mutation.encoded_native)
        kit.replace_sound(mutation.track - 1, sound)
        # TUN can change only the coarse byte, never the protected FIN residual.
        approved.update(
            value.unpacked_offsets[:1]
            if value.metadata.native_encoding is AnalogFourNativeEncoding.TUNE
            else value.unpacked_offsets
        )
    intended = tuple(sorted(approved))
    checked = encode_analog_four_candidate_patch(source_sysex, source, kit.to_bytes(), intended)
    after = read_analog_four_native_fields(checked.framed_sysex)
    applied: list[AnalogFourNativeAppliedMutation] = []
    for mutation, value in pending:
        rendered = after.value(mutation.parameter, mutation.track)
        if rendered.encoded_native != mutation.encoded_native:
            raise ValueError("native field readback disagrees with requested exact value")
        applied.append(AnalogFourNativeAppliedMutation(value, rendered))
    return AnalogFourNativeCandidateResult(
        source_sha256=before.source_sha256,
        sha256=after.source_sha256,
        source_framed_sysex=source_sysex,
        framed_sysex=checked.framed_sysex,
        source_readback=before,
        readback=after,
        applied_mutations=tuple(applied),
        intended_unpacked_offsets=intended,
        intended_wire_offsets=checked.intended_wire_offsets,
        changed_unpacked_offsets=checked.changed_unpacked_offsets,
        changed_wire_offsets=checked.changed_wire_offsets,
        source_checksum=source.checksum,
        rendered_checksum=checked.decoded.checksum,
    )


__all__ = [
    "AnalogFourNativeAppliedMutation",
    "AnalogFourNativeCandidateResult",
    "AnalogFourNativeDomain",
    "AnalogFourNativeEncoding",
    "AnalogFourNativeField",
    "AnalogFourNativeMutation",
    "AnalogFourNativeReadback",
    "AnalogFourNativeValue",
    "analog_four_native_fields",
    "read_analog_four_native_fields",
    "render_analog_four_native_fields",
]
