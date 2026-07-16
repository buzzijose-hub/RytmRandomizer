"""Passive saved-kit calibration model for the RUSH01 specifications.

The device-assisted MIDI plan is used only as an ordered semantic/catalog
inventory. Saved-kit readiness is evaluated independently against the
reference-bound kit codecs and promoted layout evidence. This module is pure:
it opens no MIDI backend, opens no port, sends no MIDI, and writes no files.
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from hashlib import sha256
from types import MappingProxyType
from typing import Final, Literal, TypeAlias, cast

from ..data.analog_four_display import ANALOG_FOUR_PARAMETER_DISPLAY
from ..data.analog_four_sysex_calibration import (
    ANALOG_FOUR_SYSEX_FIELD_CALIBRATIONS,
    AnalogFourSysexFieldCalibration,
)
from ..data.analog_rytm_kit_layout import (
    RYTM_KIT_TRACK_MACHINE_VALUE_OFFSET,
    RYTM_KIT_TRACK_SOUND_SIZE,
    RYTM_KIT_TRACKS_OFFSET,
    RYTM_SOUND_FIELD_BY_NRPN_LSB,
)
from ..data.analog_rytm_midi import (
    ANALOG_RYTM_CC_BY_SECTION_AND_PARAMETER,
    AnalogRytmCcMapping,
    get_machine_src_mappings,
)
from ..data.rush01_midi import (
    RUSH01_A4_BINDINGS,
    RUSH01_A4_TRACK_ORDER,
    RUSH01_RYTM_TRACK_ORDER,
    Rush01A4Binding,
)
from ..data.rytm_machine_catalog import RYTM_MACHINE_PROFILES, RytmMachineProfile
from ..devices.strategies.analog_rytm_snapshot_decoder import (
    AnalogRytmSnapshotDecoder,
    RytmKitSnapshot,
)
from ..snapshot.envelope import DecodedElektronKitFrame, ElektronKitCodec
from .rush01_midi_compiler import (
    RUSH01_DEVICE_A4,
    RUSH01_DEVICE_RYTM,
    STATUS_PRESERVE_REFERENCE,
    Rush01Device,
    Rush01MidiField,
    _json_value,
    _require_mapping,
    _validated_device,
    compile_rush01_midi_plan,
)

Rush01SysexFieldStatus: TypeAlias = Literal[
    "mapped",
    "preserve_reference",
    "capture_required",
    "candidate_only",
]
Rush01SysexConverterFamily: TypeAlias = Literal[
    "direct_7bit",
    "bipolar_7bit",
    "enum",
    "boolean",
    "high_resolution",
    "unverified_conversion",
    "unmapped",
    "machine_selection_and_validity",
]

RUSH01_SYSEX_CALIBRATION_VERSION: Final[str] = "rush01-saved-kit-calibration-v1"
FIELD_STATUS_MAPPED: Final[Rush01SysexFieldStatus] = "mapped"
FIELD_STATUS_PRESERVE: Final[Rush01SysexFieldStatus] = "preserve_reference"
FIELD_STATUS_CAPTURE_REQUIRED: Final[Rush01SysexFieldStatus] = "capture_required"
FIELD_STATUS_CANDIDATE_ONLY: Final[Rush01SysexFieldStatus] = "candidate_only"

_CAPTURE_ROOT: Final[str] = "calibration/sysex"
_REFERENCE_BY_DEVICE: Final[Mapping[Rush01Device, str]] = MappingProxyType(
    {
        RUSH01_DEVICE_RYTM: "reference/RYTM_Test1_Init_Kit.syx",
        RUSH01_DEVICE_A4: "reference/A4_Test1_Init_Kit.syx",
    }
)
_DEVICE_FILENAME_PREFIX: Final[Mapping[Rush01Device, str]] = MappingProxyType(
    {RUSH01_DEVICE_RYTM: "RYTM", RUSH01_DEVICE_A4: "A4"}
)
_GAP_PATH_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"`((?:tracks|track_levels)\.[A-Za-z0-9_. -]+)`"
)
_A4_BINDING_BY_SECTION_FIELD: Final[Mapping[tuple[str, str], Rush01A4Binding]] = MappingProxyType(
    {(binding.section_key, binding.field_key): binding for binding in RUSH01_A4_BINDINGS}
)
_A4_CANDIDATE_PARAMETER_BY_FIELD: Final[Mapping[tuple[str, str], str]] = MappingProxyType(
    {
        ("filter_1", "frequency"): "Filter1 Frequency",
        ("filter_1", "resonance"): "Filter1 Resonance",
        ("filter_2", "frequency"): "Filter2 Frequency",
    }
)
_SAFETY: Final[tuple[str, ...]] = (
    "passive local-file analysis only",
    "no MIDI backend imported",
    "no MIDI port opened",
    "no MIDI data transmitted",
    "no --apply execution",
    "no final RUSH01 SysEx generated while critical mappings remain unresolved",
)


@dataclass(frozen=True)
class Rush01SysexByteChange:
    """One changed byte in an unpacked, packed, header, or integrity view."""

    offset: int
    before: int
    after: int
    frame_offset: int | None = None


@dataclass(frozen=True)
class Rush01SysexCaptureTarget:
    """One operator capture requested for a single semantic parameter."""

    observation_label: str
    front_panel_value: str
    raw_midi_value: int | None
    filename: str
    mutation_command: str | None
    purpose: str


@dataclass(frozen=True)
class Rush01SysexCalibrationField:
    """Saved-kit evidence status for one RUSH01 semantic field."""

    sequence: int
    device: Rush01Device
    track: str | None
    semantic_path: str
    requested_value: object
    critical: bool
    status: Rush01SysexFieldStatus
    reason: str
    converter_family: Rush01SysexConverterFamily
    capture_group: str
    catalog_parameter: str | None
    controller: int | None
    nrpn_address: tuple[int, int] | None
    normalized_midi_value: int | None
    candidate_unpacked_offset: int | None
    candidate_packed_data_offset: int | None
    candidate_frame_offset: int | None
    candidate_unpacked_stride: int | None
    candidate_packed_stride: int | None
    capture_targets: tuple[Rush01SysexCaptureTarget, ...]
    shared_capture_group_owner: str | None
    evidence_needed: tuple[str, ...]


@dataclass(frozen=True)
class Rush01SysexCaptureDiff:
    """All byte changes observed in one supplied differential kit dump."""

    source_file: str
    semantic_path: str | None
    track: str | None
    capture_group: str | None
    observation_label: str | None
    observation_value: str | None
    valid: bool
    error: str | None
    byte_count: int
    sha256: str
    header_changes: tuple[Rush01SysexByteChange, ...]
    packed_changes: tuple[Rush01SysexByteChange, ...]
    unpacked_changes: tuple[Rush01SysexByteChange, ...]
    integrity_changes: tuple[Rush01SysexByteChange, ...]


@dataclass(frozen=True)
class Rush01SysexStrideCandidate:
    """A track-block stride observation that is never auto-promoted."""

    device: Rush01Device
    capture_group: str
    unpacked_stride: int | None
    packed_stride: int | None
    source: str
    distinct_tracks: tuple[str, ...]
    confirmed_on_second_track: bool
    promoted: bool
    reason: str


@dataclass(frozen=True)
class Rush01ReferenceRoundTrip:
    """Reference-bound decode/encode proof for one device."""

    filename: str
    byte_count: int
    sha256: str
    header_bytes: int
    packed_bytes: int
    unpacked_bytes: int
    checksum: int
    encoded_length: int
    byte_identical: bool


@dataclass(frozen=True)
class Rush01SysexCalibrationStatus:
    """Complete passive calibration status for one device."""

    version: str
    device: Rush01Device
    device_model: str
    spec_name: str
    reference: Rush01ReferenceRoundTrip
    mapping_gap_report_sha256: str
    mapping_gap_paths: tuple[str, ...]
    superseded_mapping_gap_paths: tuple[str, ...]
    fields: tuple[Rush01SysexCalibrationField, ...]
    capture_diffs: tuple[Rush01SysexCaptureDiff, ...]
    stride_candidates: tuple[Rush01SysexStrideCandidate, ...]
    fixture_files: tuple[str, ...]
    writer_ready: bool
    final_sysex_generated: bool
    safety: tuple[str, ...]


def build_rush01_sysex_calibration(
    device: str,
    spec: object,
    *,
    mapping_gaps_text: str,
    reference_frame: bytes,
    codec: ElektronKitCodec,
    capture_frames: Mapping[str, bytes] | None = None,
) -> Rush01SysexCalibrationStatus:
    """Build one deterministic saved-kit calibration status without hardware I/O."""

    normalized_device = _validated_device(device)
    plan = compile_rush01_midi_plan(normalized_device, spec)
    decoded = codec.decode_frame(reference_frame)
    round_trip = _reference_round_trip(
        _REFERENCE_BY_DEVICE[normalized_device], reference_frame, decoded, codec
    )
    if not round_trip.byte_identical:
        raise ValueError(f"{normalized_device} reference decode/encode round trip is not identical")

    if normalized_device == RUSH01_DEVICE_RYTM:
        fields = _classify_rytm_fields(plan.fields, spec, reference_frame, codec)
    else:
        fields = _classify_a4_fields(plan.fields)
    fields = _assign_capture_targets(fields)

    expected_targets = {
        target.filename: (field, target) for field in fields for target in field.capture_targets
    }
    diffs = tuple(
        _analyze_capture(
            source_file,
            frame,
            reference=decoded,
            codec=codec,
            expected=expected_targets.get(source_file),
        )
        for source_file, frame in sorted((capture_frames or {}).items())
    )
    strides = _existing_stride_candidates(normalized_device) + _detected_stride_candidates(
        normalized_device, diffs
    )
    gap_paths = _mapping_gap_paths(mapping_gaps_text, normalized_device)
    current_paths = {field.semantic_path for field in fields}
    superseded_paths = tuple(path for path in gap_paths if path not in current_paths)
    unresolved_count = sum(
        field.critical
        and field.status in {FIELD_STATUS_CAPTURE_REQUIRED, FIELD_STATUS_CANDIDATE_ONLY}
        for field in fields
    )
    fixtures = (
        tuple(
            f"tests/fixtures/rush01_sysex_calibration/{name}.json" for name in _a4_fixture_names()
        )
        if normalized_device == RUSH01_DEVICE_A4
        else ()
    )
    return Rush01SysexCalibrationStatus(
        version=RUSH01_SYSEX_CALIBRATION_VERSION,
        device=normalized_device,
        device_model=plan.device_model,
        spec_name=plan.spec_name,
        reference=round_trip,
        mapping_gap_report_sha256=sha256(mapping_gaps_text.encode("utf-8")).hexdigest(),
        mapping_gap_paths=gap_paths,
        superseded_mapping_gap_paths=superseded_paths,
        fields=fields,
        capture_diffs=diffs,
        stride_candidates=strides,
        fixture_files=fixtures,
        writer_ready=unresolved_count == 0,
        final_sysex_generated=False,
        safety=_SAFETY,
    )


def rush01_sysex_calibration_to_dict(
    status: Rush01SysexCalibrationStatus,
) -> dict[str, object]:
    """Return a stable JSON-ready representation of a calibration status."""

    counts = Counter(field.status for field in status.fields if field.critical)
    unresolved = tuple(
        field.semantic_path
        for field in status.fields
        if field.critical
        and field.status in {FIELD_STATUS_CAPTURE_REQUIRED, FIELD_STATUS_CANDIDATE_ONLY}
    )
    expected_capture_count = sum(len(field.capture_targets) for field in status.fields)
    return {
        "version": status.version,
        "device": status.device,
        "device_model": status.device_model,
        "spec_name": status.spec_name,
        "writer_ready": status.writer_ready,
        "final_sysex_generated": status.final_sysex_generated,
        "summary": {
            "critical_fields": sum(field.critical for field in status.fields),
            "mapped_fields": counts[FIELD_STATUS_MAPPED],
            "preserve_reference_fields": counts[FIELD_STATUS_PRESERVE],
            "capture_required_fields": counts[FIELD_STATUS_CAPTURE_REQUIRED],
            "candidate_only_fields": counts[FIELD_STATUS_CANDIDATE_ONLY],
            "unresolved_critical_fields": len(unresolved),
            "expected_changed_captures": expected_capture_count,
            "supplied_differential_dumps": len(status.capture_diffs),
            "valid_differential_dumps": sum(diff.valid for diff in status.capture_diffs),
            "invalid_differential_dumps": sum(not diff.valid for diff in status.capture_diffs),
            "promoted_mappings_from_this_run": 0,
        },
        "reference_round_trip": _round_trip_dict(status.reference),
        "mapping_gap_source": {
            "filename": "output/RUSH01_mapping_gaps.md",
            "sha256": status.mapping_gap_report_sha256,
            "semantic_paths": list(status.mapping_gap_paths),
            "superseded_by_current_specs": list(status.superseded_mapping_gap_paths),
        },
        "unresolved_critical_semantic_paths": list(unresolved),
        "fields": [_field_dict(field) for field in status.fields],
        "differential_dumps": [_capture_diff_dict(diff) for diff in status.capture_diffs],
        "stride_candidates": [_stride_dict(stride) for stride in status.stride_candidates],
        "promotion_policy": {
            "automatic_promotion": False,
            "multiple_observations_required": True,
            "second_track_required_for_stride": True,
            "signed_bipolar_enum_high_resolution_require_multiple_observations": True,
            "fixture_required_for_every_promoted_mapping": True,
            "fixture_files": list(status.fixture_files),
        },
        "safety": list(status.safety),
    }


def analog_four_candidate_fixture_payloads() -> Mapping[str, dict[str, object]]:
    """Return deterministic fixtures for every existing A4 candidate calibration fact."""

    payloads = {
        _fixture_slug(parameter): _a4_calibration_fixture(calibration)
        for parameter, calibration in sorted(ANALOG_FOUR_SYSEX_FIELD_CALIBRATIONS.items())
    }
    return MappingProxyType(payloads)


def _reference_round_trip(
    filename: str,
    frame: bytes,
    decoded: DecodedElektronKitFrame,
    codec: ElektronKitCodec,
) -> Rush01ReferenceRoundTrip:
    encoded = codec.encode_frame(decoded)
    return Rush01ReferenceRoundTrip(
        filename=filename,
        byte_count=len(frame),
        sha256=sha256(frame).hexdigest(),
        header_bytes=len(decoded.header),
        packed_bytes=len(decoded.packed),
        unpacked_bytes=len(decoded.unpacked),
        checksum=decoded.checksum,
        encoded_length=decoded.encoded_length,
        byte_identical=encoded == frame,
    )


def _classify_rytm_fields(
    plan_fields: Sequence[Rush01MidiField],
    spec: object,
    reference_frame: bytes,
    codec: ElektronKitCodec,
) -> tuple[Rush01SysexCalibrationField, ...]:
    spec_root = _require_mapping(spec, path="spec")
    tracks_spec = _require_mapping(spec_root.get("tracks"), path="spec.tracks")
    payload = reference_frame[1:-1]
    snapshot = AnalogRytmSnapshotDecoder().decode(payload, slot=0)
    decoded = codec.decode_frame(reference_frame)
    fields: list[Rush01SysexCalibrationField] = []
    for plan_field in plan_fields:
        if plan_field.semantic_path == "build_policy.kit_name":
            fields.append(_known_kit_name_field(plan_field))
            continue
        if plan_field.track is None:
            raise ValueError(f"Rytm critical field has no track: {plan_field.semantic_path}")
        track_index = RUSH01_RYTM_TRACK_ORDER.index(plan_field.track)
        track_spec = _require_mapping(
            tracks_spec.get(plan_field.track), path=f"spec.tracks.{plan_field.track}"
        )
        if plan_field.semantic_path.endswith(".machine"):
            fields.append(
                _classify_rytm_machine_field(
                    plan_field,
                    track_spec=track_spec,
                    track_index=track_index,
                    snapshot=snapshot,
                )
            )
            continue
        fields.append(
            _classify_rytm_parameter_field(
                plan_field,
                track_spec=track_spec,
                track_index=track_index,
                reference=decoded,
            )
        )
    return tuple(fields)


def _classify_rytm_machine_field(
    field: Rush01MidiField,
    *,
    track_spec: Mapping[str, object],
    track_index: int,
    snapshot: RytmKitSnapshot,
) -> Rush01SysexCalibrationField:
    machine = _require_mapping(track_spec.get("machine"), path=f"{field.semantic_path}.machine")
    requested_name = machine.get("name")
    profile = _rytm_machine_profile(requested_name)
    fact = snapshot.machine_facts.facts_by_pad[track_index + 1]
    offset = RYTM_KIT_TRACK_MACHINE_VALUE_OFFSET + (track_index * RYTM_KIT_TRACK_SOUND_SIZE)
    base = _base_field(
        field,
        converter_family="machine_selection_and_validity",
        capture_group="rytm.machine_selection",
        catalog_parameter="Track Machine Type",
        candidate_unpacked_offset=offset,
        candidate_unpacked_stride=RYTM_KIT_TRACK_SOUND_SIZE,
        candidate_packed_stride=None,
        header_size=9,
    )
    if fact.promoted and fact.decoded_machine_value == profile.machine_value:
        return replace(
            base,
            status=FIELD_STATUS_MAPPED,
            reason=(
                "reference machine already matches the requested catalog enum; "
                "no machine write is required"
            ),
            evidence_needed=(),
        )
    if not fact.promoted:
        return replace(
            base,
            status=FIELD_STATUS_CANDIDATE_ONLY,
            reason=(
                "tom-pad machine decode is candidate-only; a second-track differential is "
                "required before the machine stride or validity behavior can be promoted"
            ),
            normalized_midi_value=profile.machine_value,
            evidence_needed=(
                "front-panel machine name and catalog ID must agree",
                "same one-machine transition must be observed on a second track",
                "all adjacent changed bytes and high-bit behavior must be explained",
            ),
        )
    return replace(
        base,
        status=FIELD_STATUS_CAPTURE_REQUIRED,
        reason=(
            "requested machine differs from the reference; the apparent machine byte and "
            "adjacent validity/high-bit behavior are not writer-promoted"
        ),
        normalized_midi_value=profile.machine_value,
        evidence_needed=(
            "one-machine-at-a-time saved-kit differential",
            "second-track machine differential confirming the candidate stride",
            "complete explanation of adjacent validity and high-bit changes",
        ),
    )


def _classify_rytm_parameter_field(
    field: Rush01MidiField,
    *,
    track_spec: Mapping[str, object],
    track_index: int,
    reference: DecodedElektronKitFrame,
) -> Rush01SysexCalibrationField:
    if field.status == STATUS_PRESERVE_REFERENCE:
        return replace(
            _base_field(
                field,
                converter_family="enum",
                capture_group=_rytm_capture_group(field, None),
                catalog_parameter=_path_leaf(field.semantic_path),
                candidate_unpacked_offset=None,
                candidate_unpacked_stride=None,
                candidate_packed_stride=None,
                header_size=len(reference.header),
            ),
            status=FIELD_STATUS_PRESERVE,
            reason="the current specification explicitly preserves this selector",
            evidence_needed=(),
        )

    mapping = _rytm_mapping_for_field(field, track_spec)
    lsb = mapping.nrpn_lsb
    layout = RYTM_SOUND_FIELD_BY_NRPN_LSB.get(lsb) if lsb is not None else None
    unpacked_offset = (
        RYTM_KIT_TRACKS_OFFSET + (track_index * RYTM_KIT_TRACK_SOUND_SIZE) + layout.sound_offset
        if layout is not None
        else None
    )
    converter = "enum" if mapping.value_kind == "selector" else "direct_7bit"
    group = _rytm_capture_group(field, mapping)
    base = _base_field(
        field,
        converter_family=converter,
        capture_group=group,
        catalog_parameter=mapping.parameter,
        candidate_unpacked_offset=unpacked_offset,
        candidate_unpacked_stride=(
            RYTM_KIT_TRACK_SOUND_SIZE if unpacked_offset is not None else None
        ),
        candidate_packed_stride=None,
        header_size=len(reference.header),
    )
    if field.semantic_path.startswith("track_levels."):
        return replace(
            base,
            status=FIELD_STATUS_CAPTURE_REQUIRED,
            reason="Track Level NRPN 1:100 has no promoted saved-kit location",
            evidence_needed=_continuous_evidence("unknown Track Level location"),
        )
    if ".synth." in field.semantic_path:
        reason = (
            "source Level is locked for mutation and lacks a promoted saved-kit writer"
            if mapping.parameter == "Level"
            else (
                "live CC behavior is validated, but this machine-specific source semantic "
                "has no device differential proving its saved-kit slot and adjacent bytes"
                if mapping.mutation_status == "validated_runtime"
                else "manual-backed source row is documented-only for saved-kit mutation"
            )
        )
        evidence = (
            _enum_evidence(mapping.parameter)
            if mapping.value_kind == "selector"
            else _continuous_evidence("machine-specific source slot")
        )
        return replace(
            base,
            status=FIELD_STATUS_CAPTURE_REQUIRED,
            reason=reason,
            evidence_needed=evidence,
        )
    if ".sample.level" in field.semantic_path:
        return replace(
            base,
            status=FIELD_STATUS_CAPTURE_REQUIRED,
            reason=(
                "Sample Level has a candidate sound offset but remains locked; zero playback "
                "must be proven before the no-sample-dependency requirement can pass"
            ),
            evidence_needed=_continuous_evidence("Sample Level zero and adjacent bytes"),
        )
    if field.semantic_path.endswith(".amp.VOL"):
        return replace(
            base,
            status=FIELD_STATUS_CAPTURE_REQUIRED,
            reason="Amp Volume is locked and has no promoted saved-kit writer contract",
            evidence_needed=_continuous_evidence("Amp Volume slot and scale"),
        )
    if unpacked_offset is None:
        return replace(
            base,
            status=FIELD_STATUS_CAPTURE_REQUIRED,
            reason="no saved-kit location is present in the established Rytm layout",
            evidence_needed=_continuous_evidence("unknown saved-kit location"),
        )
    return replace(
        base,
        status=FIELD_STATUS_MAPPED,
        reason=(
            "validated runtime semantic, established sound-record location, and explicit "
            "7-bit/typed-enum conversion are all present"
        ),
        evidence_needed=(),
    )


def _classify_a4_fields(
    plan_fields: Sequence[Rush01MidiField],
) -> tuple[Rush01SysexCalibrationField, ...]:
    fields: list[Rush01SysexCalibrationField] = []
    for field in plan_fields:
        if field.semantic_path == "build_policy.kit_name":
            fields.append(_known_kit_name_field(field))
            continue
        if field.track is None:
            raise ValueError(f"A4 critical field has no track: {field.semantic_path}")
        if field.status == STATUS_PRESERVE_REFERENCE:
            fields.append(
                replace(
                    _base_field(
                        field,
                        converter_family="enum",
                        capture_group=_a4_capture_group(field),
                        catalog_parameter=_a4_parameter_for_field(field),
                        candidate_unpacked_offset=None,
                        candidate_unpacked_stride=None,
                        candidate_packed_stride=None,
                        header_size=4,
                    ),
                    status=FIELD_STATUS_PRESERVE,
                    reason="the current specification explicitly preserves this saved-kit field",
                    evidence_needed=(),
                )
            )
            continue

        binding = _a4_binding_for_path(field.semantic_path)
        candidate_parameter = _A4_CANDIDATE_PARAMETER_BY_FIELD.get(
            (binding.section_key, binding.field_key)
        )
        calibration = (
            ANALOG_FOUR_SYSEX_FIELD_CALIBRATIONS.get(candidate_parameter)
            if candidate_parameter is not None
            else None
        )
        converter = _a4_converter_family(binding)
        candidate_packed_offset = None
        candidate_unpacked_stride = None
        candidate_packed_stride = None
        if calibration is not None:
            track_number = RUSH01_A4_TRACK_ORDER.index(field.track) + 1
            candidate_packed_offset = calibration.primary_raw_offset_for_track(track_number)
            candidate_unpacked_stride = calibration.track_unpacked_stride
            candidate_packed_stride = calibration.track_raw_stride
        base = _base_field(
            field,
            converter_family=converter,
            capture_group=_a4_capture_group(field),
            catalog_parameter=binding.parameter,
            candidate_unpacked_offset=None,
            candidate_packed_data_offset=candidate_packed_offset,
            candidate_unpacked_stride=candidate_unpacked_stride,
            candidate_packed_stride=candidate_packed_stride,
            header_size=4,
        )
        if calibration is not None:
            fields.append(
                replace(
                    base,
                    status=FIELD_STATUS_CANDIDATE_ONLY,
                    reason=(
                        f"{candidate_parameter} has candidate-promoted observations, but the "
                        "source dumps are not supplied here and no arbitrary-value writer "
                        "conversion is promoted"
                    ),
                    evidence_needed=(
                        "supply or reproduce every recorded candidate differential dump",
                        "observe fine/intermediate values needed for the requested target",
                        "promote a typed writer only after semantic decode/encode tests pass",
                    ),
                )
            )
            continue
        reason = (
            "no manual MIDI address exists; use front-panel-only differential capture"
            if binding.parameter is None
            else ("transport conversion exists, but no saved-kit location or writer is promoted")
        )
        fields.append(
            replace(
                base,
                status=FIELD_STATUS_CAPTURE_REQUIRED,
                reason=reason,
                evidence_needed=_a4_evidence(binding, converter),
            )
        )
    return tuple(fields)


def _known_kit_name_field(field: Rush01MidiField) -> Rush01SysexCalibrationField:
    device = field.device
    offset = 4 if device == RUSH01_DEVICE_RYTM else 8
    header_size = 9 if device == RUSH01_DEVICE_RYTM else 4
    return replace(
        _base_field(
            field,
            converter_family="direct_7bit",
            capture_group=f"{device}.kit_name",
            catalog_parameter="Kit Name",
            candidate_unpacked_offset=offset,
            candidate_unpacked_stride=None,
            candidate_packed_stride=None,
            header_size=header_size,
            critical=False,
        ),
        status=FIELD_STATUS_MAPPED,
        reason="fixed-width ASCII kit-name location is established and round-trip tested",
        evidence_needed=(),
    )


def _base_field(
    field: Rush01MidiField,
    *,
    converter_family: Rush01SysexConverterFamily,
    capture_group: str,
    catalog_parameter: str | None,
    candidate_unpacked_offset: int | None,
    candidate_unpacked_stride: int | None,
    candidate_packed_stride: int | None,
    header_size: int,
    candidate_packed_data_offset: int | None = None,
    critical: bool = True,
) -> Rush01SysexCalibrationField:
    packed_offset = candidate_packed_data_offset
    if packed_offset is None and candidate_unpacked_offset is not None:
        packed_offset = _packed_data_offset(candidate_unpacked_offset)
    return Rush01SysexCalibrationField(
        sequence=field.sequence,
        device=field.device,
        track=field.track,
        semantic_path=field.semantic_path,
        requested_value=field.requested_value,
        critical=critical,
        status=FIELD_STATUS_CAPTURE_REQUIRED,
        reason="saved-kit evidence pending",
        converter_family=converter_family,
        capture_group=capture_group,
        catalog_parameter=catalog_parameter,
        controller=field.controller,
        nrpn_address=field.nrpn_address,
        normalized_midi_value=field.normalized_midi_value,
        candidate_unpacked_offset=candidate_unpacked_offset,
        candidate_packed_data_offset=packed_offset,
        candidate_frame_offset=(
            1 + header_size + packed_offset if packed_offset is not None else None
        ),
        candidate_unpacked_stride=candidate_unpacked_stride,
        candidate_packed_stride=candidate_packed_stride,
        capture_targets=(),
        shared_capture_group_owner=None,
        evidence_needed=(),
    )


def _assign_capture_targets(
    fields: Sequence[Rush01SysexCalibrationField],
) -> tuple[Rush01SysexCalibrationField, ...]:
    unresolved_by_group: dict[str, list[Rush01SysexCalibrationField]] = defaultdict(list)
    for field in fields:
        if field.status in {FIELD_STATUS_CAPTURE_REQUIRED, FIELD_STATUS_CANDIDATE_ONLY}:
            unresolved_by_group[field.capture_group].append(field)

    replacements: dict[int, Rush01SysexCalibrationField] = {}
    for group_fields in unresolved_by_group.values():
        ordered = sorted(group_fields, key=lambda candidate: candidate.sequence)
        owner = ordered[0]
        owner_targets = _capture_targets_for_field(owner, role="converter-and-location")
        replacements[owner.sequence] = replace(owner, capture_targets=owner_targets)
        second_track_added = False
        for field in ordered[1:]:
            needs_own_semantic_capture = (
                field.device == RUSH01_DEVICE_RYTM and ".synth." in field.semantic_path
            ) or field.converter_family == "machine_selection_and_validity"
            if needs_own_semantic_capture:
                targets = _capture_targets_for_field(field, role="semantic-location")
                replacements[field.sequence] = replace(
                    field,
                    capture_targets=targets,
                    shared_capture_group_owner=owner.semantic_path,
                )
                if field.track != owner.track:
                    second_track_added = True
                continue
            if not second_track_added and field.track != owner.track:
                target = _stride_witness_target(field, owner_targets)
                replacements[field.sequence] = replace(
                    field,
                    capture_targets=(target,),
                    shared_capture_group_owner=owner.semantic_path,
                )
                second_track_added = True
                continue
            replacements[field.sequence] = replace(
                field,
                shared_capture_group_owner=owner.semantic_path,
            )
    return tuple(replacements.get(field.sequence, field) for field in fields)


def _capture_targets_for_field(
    field: Rush01SysexCalibrationField,
    *,
    role: str,
) -> tuple[Rush01SysexCaptureTarget, ...]:
    observations = _observation_values(field, role=role)
    targets: list[Rush01SysexCaptureTarget] = []
    for label, front_panel, raw_midi, purpose in observations:
        filename = _capture_filename(field, label)
        targets.append(
            Rush01SysexCaptureTarget(
                observation_label=label,
                front_panel_value=front_panel,
                raw_midi_value=raw_midi,
                filename=filename,
                mutation_command=_mutation_command(field, raw_midi),
                purpose=purpose,
            )
        )
    return tuple(targets)


def _stride_witness_target(
    field: Rush01SysexCalibrationField,
    owner_targets: Sequence[Rush01SysexCaptureTarget],
) -> Rush01SysexCaptureTarget:
    if not owner_targets:
        raise ValueError(f"capture group owner has no targets: {field.capture_group}")
    source = next(
        (target for target in owner_targets if target.raw_midi_value == 64),
        owner_targets[0],
    )
    raw = source.raw_midi_value
    return Rush01SysexCaptureTarget(
        observation_label=source.observation_label,
        front_panel_value=source.front_panel_value,
        raw_midi_value=raw,
        filename=_capture_filename(field, f"stride_{source.observation_label}"),
        mutation_command=_mutation_command(field, raw),
        purpose="second-track witness; candidate stride remains unpromoted until reviewed",
    )


def _observation_values(
    field: Rush01SysexCalibrationField,
    *,
    role: str,
) -> tuple[tuple[str, str, int | None, str], ...]:
    requested_text = _requested_text(field.requested_value)
    requested_raw = field.normalized_midi_value
    purpose = f"{role}; one parameter only"
    if field.converter_family == "machine_selection_and_validity":
        return (("requested", requested_text, requested_raw, purpose),)
    if role == "semantic-location":
        return (("requested", requested_text, requested_raw, purpose),)
    if field.converter_family == "direct_7bit":
        values = [("min", "0", 0), ("mid", "64", 64), ("max", "127", 127)]
        if requested_raw is not None and requested_raw not in {0, 64, 127}:
            values.append(("requested", requested_text, requested_raw))
        return tuple((label, display, raw, purpose) for label, display, raw in values)
    if field.converter_family == "bipolar_7bit":
        values = [
            ("negative", "-64", 0),
            ("center", "0", 64),
            ("positive", "+63", 127),
        ]
        if requested_raw is not None and requested_raw not in {0, 64, 127}:
            values.append(("requested", requested_text, requested_raw))
        return tuple((label, display, raw, purpose) for label, display, raw in values)
    if field.converter_family == "boolean":
        return (
            ("false", "false/off", None, purpose),
            ("true", "true/on", None, purpose),
        )
    if field.converter_family == "enum":
        enum_values = _known_enum_values(field)
        if enum_values:
            return tuple((label, label, raw, purpose) for raw, label in enum_values)
        if field.device == RUSH01_DEVICE_RYTM:
            option_count = _rytm_enum_option_count(field)
            return tuple(
                (
                    f"option_{index:02d}",
                    f"record exact front-panel label for option {index + 1}",
                    None,
                    purpose,
                )
                for index in range(option_count)
            )
        return (
            ("baseline_alternative", "one named option other than the request", None, purpose),
            ("requested", requested_text, None, purpose),
        )
    if field.converter_family == "high_resolution":
        candidate = _a4_candidate_calibration(field)
        if candidate is not None:
            values = [
                ("minimum", candidate.screen_min, None),
                ("fine_step", "one exact encoder step above minimum", None),
                ("midpoint", candidate.screen_mid, None),
                ("maximum", candidate.screen_max, None),
                ("requested", requested_text, None),
            ]
        else:
            values = [
                ("step_down", "one exact encoder step below baseline", None),
                ("step_up", "one exact encoder step above baseline", None),
                ("requested", requested_text, None),
            ]
        return tuple((label, display, raw, purpose) for label, display, raw in values)
    return (
        ("step_down", "one exact front-panel step below baseline", None, purpose),
        ("step_up", "one exact front-panel step above baseline", None, purpose),
        ("requested", requested_text, None, purpose),
    )


def _known_enum_values(field: Rush01SysexCalibrationField) -> tuple[tuple[int, str], ...]:
    parameter = field.catalog_parameter
    if field.device != RUSH01_DEVICE_A4 or parameter is None:
        return ()
    display = ANALOG_FOUR_PARAMETER_DISPLAY.get(parameter)
    if display is None or not display.value_labels:
        return ()
    return tuple(sorted(display.value_labels.items()))


def _rytm_enum_option_count(field: Rush01SysexCalibrationField) -> int:
    if field.track is None:
        return 2
    if field.semantic_path.endswith(".machine"):
        return 2
    matching = tuple(
        row
        for profile in RYTM_MACHINE_PROFILES
        for row in get_machine_src_mappings(profile.key)
        if row.parameter == field.catalog_parameter and row.value_kind == "selector"
    )
    if not matching:
        return 2
    return max(mapping.value_max - mapping.value_min + 1 for mapping in matching)


def _mutation_command(
    field: Rush01SysexCalibrationField,
    raw_midi: int | None,
) -> str | None:
    if raw_midi is None or field.track is None:
        return None
    python = ".venv\\Scripts\\python.exe -m rytm_randomizer.app"
    if field.device == RUSH01_DEVICE_RYTM:
        if field.controller is None:
            return None
        return (
            f"{python} --arm --validate-one-cc --channel <{field.track}_CHANNEL_0_BASED> "
            f"--control {field.controller} --value {raw_midi}"
        )
    if field.catalog_parameter == "Track Level":
        return (
            f'{python} --arm --a4-send-param --parameter "Track Level" '
            f"--channel <{field.track}_CHANNEL_0_BASED> --value {raw_midi}"
        )
    if field.catalog_parameter is None or field.nrpn_address is None:
        return None
    return (
        f'{python} --arm --a4-send-nrpn-param --parameter "{field.catalog_parameter}" '
        f"--channel <{field.track}_CHANNEL_0_BASED> --value {raw_midi}"
    )


def _capture_filename(field: Rush01SysexCalibrationField, label: str) -> str:
    prefix = _DEVICE_FILENAME_PREFIX[field.device]
    track = field.track or "KIT"
    semantic = _capture_slug(field.semantic_path)
    return (
        f"{_CAPTURE_ROOT}/{field.device}/{prefix}_{track}_{semantic}_" f"{_capture_slug(label)}.syx"
    )


def _analyze_capture(
    source_file: str,
    frame: bytes,
    *,
    reference: DecodedElektronKitFrame,
    codec: ElektronKitCodec,
    expected: tuple[Rush01SysexCalibrationField, Rush01SysexCaptureTarget] | None,
) -> Rush01SysexCaptureDiff:
    field = expected[0] if expected is not None else None
    target = expected[1] if expected is not None else None
    digest = sha256(frame).hexdigest()
    try:
        decoded = codec.decode_frame(frame)
    except ValueError as exc:
        return Rush01SysexCaptureDiff(
            source_file=source_file,
            semantic_path=field.semantic_path if field is not None else None,
            track=field.track if field is not None else None,
            capture_group=field.capture_group if field is not None else None,
            observation_label=target.observation_label if target is not None else None,
            observation_value=target.front_panel_value if target is not None else None,
            valid=False,
            error=str(exc),
            byte_count=len(frame),
            sha256=digest,
            header_changes=(),
            packed_changes=(),
            unpacked_changes=(),
            integrity_changes=(),
        )
    header_changes = _byte_changes(
        reference.header,
        decoded.header,
        frame_offset_start=1,
    )
    packed_changes = _byte_changes(
        reference.packed,
        decoded.packed,
        frame_offset_start=1 + len(reference.header),
    )
    unpacked_changes = _byte_changes(reference.unpacked, decoded.unpacked)
    trailer_start = len(reference.original_frame) - 5
    integrity_changes = _byte_changes(
        reference.original_frame[trailer_start:-1],
        decoded.original_frame[trailer_start:-1],
        frame_offset_start=trailer_start,
    )
    return Rush01SysexCaptureDiff(
        source_file=source_file,
        semantic_path=field.semantic_path if field is not None else None,
        track=field.track if field is not None else None,
        capture_group=field.capture_group if field is not None else None,
        observation_label=target.observation_label if target is not None else None,
        observation_value=target.front_panel_value if target is not None else None,
        valid=True,
        error=None,
        byte_count=len(frame),
        sha256=digest,
        header_changes=header_changes,
        packed_changes=packed_changes,
        unpacked_changes=unpacked_changes,
        integrity_changes=integrity_changes,
    )


def _byte_changes(
    before: bytes,
    after: bytes,
    *,
    frame_offset_start: int | None = None,
) -> tuple[Rush01SysexByteChange, ...]:
    if len(before) != len(after):
        raise ValueError("differential byte views must have equal lengths")
    return tuple(
        Rush01SysexByteChange(
            offset=index,
            before=left,
            after=right,
            frame_offset=(frame_offset_start + index if frame_offset_start is not None else None),
        )
        for index, (left, right) in enumerate(zip(before, after))
        if left != right
    )


def _existing_stride_candidates(device: Rush01Device) -> tuple[Rush01SysexStrideCandidate, ...]:
    if device == RUSH01_DEVICE_RYTM:
        return (
            Rush01SysexStrideCandidate(
                device=device,
                capture_group="rytm.sound_record_layout",
                unpacked_stride=RYTM_KIT_TRACK_SOUND_SIZE,
                packed_stride=None,
                source="existing Rytm sound-record layout fact",
                distinct_tracks=(),
                confirmed_on_second_track=False,
                promoted=False,
                reason=(
                    "layout stride is an input candidate for unresolved semantics; this workbench "
                    "does not promote a field until a second-track differential confirms it"
                ),
            ),
        )
    return tuple(
        Rush01SysexStrideCandidate(
            device=device,
            capture_group=_a4_candidate_capture_group(parameter),
            unpacked_stride=calibration.track_unpacked_stride,
            packed_stride=calibration.track_raw_stride,
            source="existing candidate-promoted A4 calibration metadata",
            distinct_tracks=tuple(
                f"T{track}" for track in sorted({row.track for row in calibration.evidence})
            ),
            confirmed_on_second_track=len({row.track for row in calibration.evidence}) >= 2,
            promoted=False,
            reason=(
                "second-track evidence exists in metadata, but source dumps and an arbitrary-value "
                "writer contract are still required"
            ),
        )
        for parameter, calibration in sorted(ANALOG_FOUR_SYSEX_FIELD_CALIBRATIONS.items())
    )


def _detected_stride_candidates(
    device: Rush01Device,
    diffs: Sequence[Rush01SysexCaptureDiff],
) -> tuple[Rush01SysexStrideCandidate, ...]:
    grouped: dict[tuple[str, str, str], list[Rush01SysexCaptureDiff]] = defaultdict(list)
    for diff in diffs:
        if (
            diff.valid
            and diff.capture_group is not None
            and diff.observation_label is not None
            and diff.observation_value is not None
            and diff.track is not None
            and diff.unpacked_changes
        ):
            grouped[(diff.capture_group, diff.observation_label, diff.observation_value)].append(
                diff
            )
    candidates: list[Rush01SysexStrideCandidate] = []
    for (group, _label, _value), group_diffs in sorted(grouped.items()):
        ordered = sorted(group_diffs, key=lambda item: cast(str, item.track))
        for first_index, first in enumerate(ordered):
            for second in ordered[first_index + 1 :]:
                if first.track == second.track:
                    continue
                unpacked_stride = _constant_offset_delta(
                    first.unpacked_changes, second.unpacked_changes
                )
                packed_stride = _constant_offset_delta(first.packed_changes, second.packed_changes)
                if unpacked_stride is None and packed_stride is None:
                    continue
                tracks = tuple(sorted((cast(str, first.track), cast(str, second.track))))
                candidates.append(
                    Rush01SysexStrideCandidate(
                        device=device,
                        capture_group=group,
                        unpacked_stride=unpacked_stride,
                        packed_stride=packed_stride,
                        source=f"supplied differential dumps: {first.source_file}, {second.source_file}",
                        distinct_tracks=tracks,
                        confirmed_on_second_track=True,
                        promoted=False,
                        reason=(
                            "constant offset delta detected on a second track; candidate remains "
                            "unpromoted until converter and adjacent-byte evidence are reviewed"
                        ),
                    )
                )
                break
            else:
                continue
            break
    return tuple(candidates)


def _constant_offset_delta(
    first: Sequence[Rush01SysexByteChange],
    second: Sequence[Rush01SysexByteChange],
) -> int | None:
    if not first or len(first) != len(second):
        return None
    deltas = {right.offset - left.offset for left, right in zip(first, second)}
    if len(deltas) != 1:
        return None
    delta = deltas.pop()
    return delta if delta > 0 else None


def _rytm_mapping_for_field(
    field: Rush01MidiField,
    track_spec: Mapping[str, object],
) -> AnalogRytmCcMapping:
    if field.semantic_path.startswith("track_levels."):
        return ANALOG_RYTM_CC_BY_SECTION_AND_PARAMETER[("COMMON", "Track Level")]
    if ".sample.level" in field.semantic_path:
        return ANALOG_RYTM_CC_BY_SECTION_AND_PARAMETER[("SAMPLE", "Sample Level")]
    if ".filter." in field.semantic_path:
        parameter_by_key = {
            "ATK": "Filter Attack Time",
            "DEC": "Filter Decay Time",
            "SUS": "Filter Sustain Level",
            "REL": "Filter Release Time",
            "FRQ": "Filter Frequency",
            "RES": "Filter Resonance",
            "TYPE": "Filter Mode",
            "ENV": "Filter Env Depth",
        }
        return ANALOG_RYTM_CC_BY_SECTION_AND_PARAMETER[
            ("FILTER", parameter_by_key[_path_leaf(field.semantic_path)])
        ]
    if ".amp." in field.semantic_path:
        parameter_by_key = {
            "ATK": "Amp Attack Time",
            "HLD": "Amp Hold Time",
            "DEC": "Amp Decay Time",
            "OVR": "Amp Overdrive",
            "DEL": "Amp Delay Send",
            "REV": "Amp Reverb Send",
            "PAN": "Amp Pan",
            "VOL": "Amp Volume",
        }
        return ANALOG_RYTM_CC_BY_SECTION_AND_PARAMETER[
            ("AMP", parameter_by_key[_path_leaf(field.semantic_path)])
        ]
    machine = _require_mapping(track_spec.get("machine"), path=f"{field.semantic_path}.machine")
    profile = _rytm_machine_profile(machine.get("name"))
    parameter = _path_leaf(field.semantic_path)
    for mapping in get_machine_src_mappings(profile.key):
        if mapping.parameter == parameter:
            return mapping
    raise KeyError(f"no Rytm source mapping for {field.semantic_path}")


def _rytm_capture_group(
    field: Rush01MidiField,
    mapping: AnalogRytmCcMapping | None,
) -> str:
    if field.semantic_path.startswith("track_levels."):
        return "rytm.track_level"
    if ".sample.level" in field.semantic_path:
        return "rytm.sample_level"
    if field.semantic_path.endswith(".amp.VOL"):
        return "rytm.amp_volume"
    if ".synth." in field.semantic_path:
        lsb = mapping.nrpn_lsb if mapping is not None else None
        return f"rytm.source_slot_{lsb if lsb is not None else 'unknown'}"
    return f"rytm.{_capture_slug(field.semantic_path)}"


def _a4_binding_for_path(path: str) -> Rush01A4Binding:
    parts = path.split(".")
    if path.startswith("track_levels."):
        return Rush01A4Binding("track_levels", "track_level", "Track Level", "direct_7bit")
    if len(parts) != 4 or parts[0] != "tracks":
        raise KeyError(f"unsupported A4 semantic path: {path}")
    try:
        return _A4_BINDING_BY_SECTION_FIELD[(parts[2], parts[3])]
    except KeyError as exc:
        raise KeyError(f"no A4 binding for {path}") from exc


def _a4_converter_family(binding: Rush01A4Binding) -> Rush01SysexConverterFamily:
    if binding.conversion == "bipolar_7bit":
        return "bipolar_7bit"
    if binding.conversion in {"verified_enum", "unverified_enum"}:
        return "enum"
    if binding.conversion == "unverified_boolean":
        return "boolean"
    if binding.conversion == "unverified_high_resolution":
        return "high_resolution"
    if binding.conversion == "unverified_conversion":
        return "unverified_conversion"
    if binding.conversion == "unmapped":
        return "unmapped"
    return "direct_7bit"


def _a4_capture_group(field: Rush01MidiField | Rush01SysexCalibrationField) -> str:
    path = field.semantic_path
    if path.startswith("track_levels."):
        return "a4.track_level"
    parts = path.split(".")
    return f"a4.{parts[2]}.{parts[3]}"


def _a4_parameter_for_field(field: Rush01MidiField) -> str | None:
    return _a4_binding_for_path(field.semantic_path).parameter


def _a4_candidate_calibration(
    field: Rush01SysexCalibrationField,
) -> AnalogFourSysexFieldCalibration | None:
    if field.device != RUSH01_DEVICE_A4:
        return None
    parts = field.semantic_path.split(".")
    if len(parts) != 4:
        return None
    parameter = _A4_CANDIDATE_PARAMETER_BY_FIELD.get((parts[2], parts[3]))
    return ANALOG_FOUR_SYSEX_FIELD_CALIBRATIONS.get(parameter) if parameter else None


def _a4_evidence(
    binding: Rush01A4Binding,
    converter: Rush01SysexConverterFamily,
) -> tuple[str, ...]:
    common = (
        "one-parameter-at-a-time saved-kit differentials",
        "same observation on a second track before promoting a track stride",
        "all changed packed and unpacked bytes must be explained",
    )
    if converter == "enum":
        return common + ("multiple named enum observations and an exact typed label table",)
    if converter == "boolean":
        return common + ("both front-panel boolean states",)
    if converter == "bipolar_7bit":
        return common + ("negative, center, and positive observations",)
    if converter == "high_resolution":
        return common + ("coarse and fine-step observations proving the full-resolution encoding",)
    if converter in {"unverified_conversion", "unmapped"}:
        return common + ("multiple front-panel observations; no raw MIDI value may be inferred",)
    parameter = binding.parameter or "front-panel parameter"
    return common + (f"minimum, midpoint, maximum observations for {parameter}",)


def _continuous_evidence(subject: str) -> tuple[str, ...]:
    return (
        f"minimum, midpoint, and maximum observations for {subject}",
        "requested-value semantic decode check",
        "same observation on a second track before promoting a stride",
        "all adjacent changed bytes must be explained",
    )


def _enum_evidence(parameter: str) -> tuple[str, ...]:
    return (
        f"multiple named front-panel observations for {parameter}",
        "exact enum label-to-raw table; numeric ordinals alone are insufficient",
        "same observation on a second track before promoting a stride",
        "all adjacent changed bytes must be explained",
    )


def _rytm_machine_profile(name: object) -> RytmMachineProfile:
    if not isinstance(name, str):
        raise ValueError("Rytm machine name must be a string")
    for profile in RYTM_MACHINE_PROFILES:
        if profile.label == name:
            return profile
    raise KeyError(f"unknown Rytm machine name: {name}")


def _packed_data_offset(unpacked_offset: int) -> int:
    group, within_group = divmod(unpacked_offset, 7)
    return (group * 8) + 1 + within_group


def _mapping_gap_paths(text: str, device: Rush01Device) -> tuple[str, ...]:
    track_names = (
        set(RUSH01_RYTM_TRACK_ORDER) if device == RUSH01_DEVICE_RYTM else set(RUSH01_A4_TRACK_ORDER)
    )
    paths = {
        match.group(1).strip()
        for match in _GAP_PATH_PATTERN.finditer(text)
        if "*" not in match.group(1)
        and "<" not in match.group(1)
        and _gap_path_track(match.group(1)) in track_names
    }
    return tuple(sorted(paths))


def _gap_path_track(path: str) -> str:
    parts = path.split(".")
    return parts[1] if len(parts) > 1 else ""


def _a4_candidate_capture_group(parameter: str) -> str:
    for (section, field), candidate in _A4_CANDIDATE_PARAMETER_BY_FIELD.items():
        if candidate == parameter:
            return f"a4.{section}.{field}"
    raise KeyError(f"unknown A4 candidate calibration parameter: {parameter}")


def _path_leaf(path: str) -> str:
    return path.rsplit(".", 1)[-1]


def _requested_text(value: object) -> str:
    if isinstance(value, Mapping):
        requested = value.get("requested")
        name = value.get("name")
        if isinstance(requested, str):
            return requested
        if isinstance(name, str):
            return name
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _capture_slug(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "_", value.casefold()).strip("_")
    return normalized or "value"


def _fixture_slug(parameter: str) -> str:
    return f"analog_four_{_capture_slug(parameter)}"


def _a4_fixture_names() -> tuple[str, ...]:
    return tuple(
        _fixture_slug(parameter) for parameter in sorted(ANALOG_FOUR_SYSEX_FIELD_CALIBRATIONS)
    )


def _a4_calibration_fixture(
    calibration: AnalogFourSysexFieldCalibration,
) -> dict[str, object]:
    return {
        "parameter": calibration.parameter,
        "section": calibration.section,
        "status": calibration.status,
        "screen_values": {
            "minimum": calibration.screen_min,
            "midpoint": calibration.screen_mid,
            "maximum": calibration.screen_max,
        },
        "primary_raw_values": dict(calibration.primary_raw_values),
        "track_1_primary_raw_offset": calibration.track_1_primary_raw_offset,
        "track_raw_stride": calibration.track_raw_stride,
        "track_1_raw_group_start": calibration.track_1_raw_group_start,
        "raw_group_width": calibration.raw_group_width,
        "track_1_unpacked_group_start": calibration.track_1_unpacked_group_start,
        "unpacked_group_width": calibration.unpacked_group_width,
        "track_unpacked_stride": calibration.track_unpacked_stride,
        "evidence": [
            {
                "track": row.track,
                "screen_value": row.screen_value,
                "primary_raw_value": row.primary_raw_value,
                "kit_name": row.kit_name,
                "source_file": row.source_file,
                "payload_fingerprint": row.payload_fingerprint,
            }
            for row in calibration.evidence
        ],
        "notes": list(calibration.notes),
        "writer_ready": False,
    }


def _round_trip_dict(round_trip: Rush01ReferenceRoundTrip) -> dict[str, object]:
    return {
        "filename": round_trip.filename,
        "byte_count": round_trip.byte_count,
        "sha256": round_trip.sha256,
        "header_bytes": round_trip.header_bytes,
        "packed_bytes": round_trip.packed_bytes,
        "unpacked_bytes": round_trip.unpacked_bytes,
        "checksum": round_trip.checksum,
        "encoded_length": round_trip.encoded_length,
        "byte_identical": round_trip.byte_identical,
    }


def _field_dict(field: Rush01SysexCalibrationField) -> dict[str, object]:
    return {
        "sequence": field.sequence,
        "semantic_path": field.semantic_path,
        "track": field.track,
        "requested_value": _json_value(field.requested_value),
        "critical": field.critical,
        "status": field.status,
        "reason": field.reason,
        "converter_family": field.converter_family,
        "capture_group": field.capture_group,
        "catalog_parameter": field.catalog_parameter,
        "midi_address": {
            "controller": field.controller,
            "nrpn": list(field.nrpn_address) if field.nrpn_address is not None else None,
        },
        "normalized_midi_value": field.normalized_midi_value,
        "candidate_byte_location": {
            "unpacked_offset": field.candidate_unpacked_offset,
            "packed_data_offset": field.candidate_packed_data_offset,
            "frame_offset": field.candidate_frame_offset,
            "unpacked_track_stride": field.candidate_unpacked_stride,
            "packed_track_stride": field.candidate_packed_stride,
            "promoted": field.status == FIELD_STATUS_MAPPED,
        },
        "baseline_dump_filename": _REFERENCE_BY_DEVICE[field.device],
        "changed_dump_filenames": [target.filename for target in field.capture_targets],
        "number_of_changed_captures": len(field.capture_targets),
        "shared_capture_group_owner": field.shared_capture_group_owner,
        "captures": [_target_dict(target) for target in field.capture_targets],
        "evidence_needed": list(field.evidence_needed),
    }


def _target_dict(target: Rush01SysexCaptureTarget) -> dict[str, object]:
    return {
        "observation_label": target.observation_label,
        "front_panel_value": target.front_panel_value,
        "raw_midi_value": target.raw_midi_value,
        "filename": target.filename,
        "mutation_command": target.mutation_command,
        "purpose": target.purpose,
    }


def _capture_diff_dict(diff: Rush01SysexCaptureDiff) -> dict[str, object]:
    return {
        "source_file": diff.source_file,
        "semantic_path": diff.semantic_path,
        "track": diff.track,
        "capture_group": diff.capture_group,
        "observation_label": diff.observation_label,
        "observation_value": diff.observation_value,
        "valid": diff.valid,
        "error": diff.error,
        "byte_count": diff.byte_count,
        "sha256": diff.sha256,
        "header_changes": [_change_dict(change) for change in diff.header_changes],
        "packed_changes": [_change_dict(change) for change in diff.packed_changes],
        "unpacked_changes": [_change_dict(change) for change in diff.unpacked_changes],
        "integrity_changes": [_change_dict(change) for change in diff.integrity_changes],
    }


def _change_dict(change: Rush01SysexByteChange) -> dict[str, object]:
    return {
        "offset": change.offset,
        "frame_offset": change.frame_offset,
        "before": change.before,
        "after": change.after,
        "before_hex": f"0x{change.before:02X}",
        "after_hex": f"0x{change.after:02X}",
    }


def _stride_dict(stride: Rush01SysexStrideCandidate) -> dict[str, object]:
    return {
        "capture_group": stride.capture_group,
        "unpacked_stride": stride.unpacked_stride,
        "packed_stride": stride.packed_stride,
        "source": stride.source,
        "distinct_tracks": list(stride.distinct_tracks),
        "confirmed_on_second_track": stride.confirmed_on_second_track,
        "promoted": stride.promoted,
        "reason": stride.reason,
    }


__all__ = [
    "FIELD_STATUS_CANDIDATE_ONLY",
    "FIELD_STATUS_CAPTURE_REQUIRED",
    "FIELD_STATUS_MAPPED",
    "FIELD_STATUS_PRESERVE",
    "RUSH01_SYSEX_CALIBRATION_VERSION",
    "Rush01ReferenceRoundTrip",
    "Rush01SysexByteChange",
    "Rush01SysexCalibrationField",
    "Rush01SysexCalibrationStatus",
    "Rush01SysexCaptureDiff",
    "Rush01SysexCaptureTarget",
    "Rush01SysexStrideCandidate",
    "analog_four_candidate_fixture_payloads",
    "build_rush01_sysex_calibration",
    "rush01_sysex_calibration_to_dict",
]
