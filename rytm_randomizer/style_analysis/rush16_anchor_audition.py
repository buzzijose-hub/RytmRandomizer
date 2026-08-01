"""Pure RUSH16 semantic expansion and fail-closed build classification."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from copy import deepcopy
from dataclasses import dataclass
from hashlib import sha256
from types import MappingProxyType
from typing import Final, Literal, TypeAlias, cast

from ..data.rush16 import (
    RUSH16_ANCHORS,
    RUSH16_BATCH_ID,
    RUSH16_SHARED_FAMILY_LOCKS,
    RUSH16_STATUS_VALUES,
    RUSH16_VERSION,
    Rush16AnchorDefinition,
)
from .rush01_midi_compiler import (
    RUSH01_DEVICE_A4,
    RUSH01_DEVICE_RYTM,
    STATUS_INVALID_SPEC_FIELD,
    STATUS_LEARN_REQUIRED,
    STATUS_MANUAL_SETUP_REQUIRED,
    STATUS_PRESERVE_REFERENCE,
    STATUS_READY,
    Rush01Device,
    Rush01MidiField,
    Rush01MidiPlan,
    _require_mapping,
    compile_rush01_midi_plan,
)
from .rush01_sysex_calibration import (
    FIELD_STATUS_MAPPED,
    FIELD_STATUS_PRESERVE,
    Rush01SysexCalibrationStatus,
)

Rush16FieldStatus: TypeAlias = Literal[
    "writer_ready",
    "midi_apply_ready",
    "calibration_required",
    "manual_menu_action_only",
    "blocked_unverified",
]

WRITER_READY: Final[Rush16FieldStatus] = "writer_ready"
MIDI_APPLY_READY: Final[Rush16FieldStatus] = "midi_apply_ready"
CALIBRATION_REQUIRED: Final[Rush16FieldStatus] = "calibration_required"
MANUAL_MENU_ACTION_ONLY: Final[Rush16FieldStatus] = "manual_menu_action_only"
BLOCKED_UNVERIFIED: Final[Rush16FieldStatus] = "blocked_unverified"

_SOURCE_SPEC: Final[Mapping[Rush01Device, str]] = MappingProxyType(
    {
        RUSH01_DEVICE_RYTM: "specs/RUSH01_RYTM.yaml",
        RUSH01_DEVICE_A4: "specs/RUSH01_A4.yaml",
    }
)
_SPEC_SUFFIX: Final[Mapping[Rush01Device, str]] = MappingProxyType(
    {RUSH01_DEVICE_RYTM: "RYTM", RUSH01_DEVICE_A4: "A4"}
)
_DEVICE_LABEL: Final[Mapping[Rush01Device, str]] = MappingProxyType(
    {RUSH01_DEVICE_RYTM: "Analog Rytm MKII", RUSH01_DEVICE_A4: "Analog Four MKII"}
)
_DIRECT_ALLOWED: Final[frozenset[str]] = frozenset({FIELD_STATUS_MAPPED, FIELD_STATUS_PRESERVE})
_MIDI_ALLOWED: Final[frozenset[str]] = frozenset({STATUS_READY, STATUS_PRESERVE_REFERENCE})


@dataclass(frozen=True)
class Rush16FieldReadiness:
    """One exact semantic path and its current construction readiness."""

    semantic_path: str
    status: Rush16FieldStatus
    sound_critical: bool
    reason: str
    evidence_source: str


@dataclass(frozen=True)
class Rush16BuildEntry:
    """Construction and validation state for one anchor/device artifact."""

    anchor_id: str
    device: Rush01Device
    spec_filename: str
    target_filename: str
    spec_sha256: str
    reference_sha256: str
    reference_round_trip_identical: bool
    direct_sysex_ready: bool
    hardware_apply_ready: bool
    hardware_capture_configured: bool
    hardware_assisted_ready: bool
    final_sysex_generated: bool
    direct_blockers: tuple[str, ...]
    hardware_blockers: tuple[str, ...]
    status_counts: Mapping[str, int]
    midi_ready_fields: int
    midi_message_count: int
    output_port_configured: bool

    def __post_init__(self) -> None:
        object.__setattr__(self, "status_counts", MappingProxyType(dict(self.status_counts)))


def build_rush16_spec_documents(
    rytm_source: object,
    a4_source: object,
    *,
    source_hashes: Mapping[str, str],
    baseline_mapping_statuses: Mapping[str, object],
) -> Mapping[str, dict[str, object]]:
    """Expand RUSH01 into eight deterministic specs plus one family document."""

    sources: Mapping[Rush01Device, object] = {
        RUSH01_DEVICE_RYTM: rytm_source,
        RUSH01_DEVICE_A4: a4_source,
    }
    documents: dict[str, dict[str, object]] = {}
    for anchor in RUSH16_ANCHORS:
        for device in (RUSH01_DEVICE_RYTM, RUSH01_DEVICE_A4):
            source_path = _SOURCE_SPEC[device]
            status_document = baseline_mapping_statuses.get(device)
            if status_document is None:
                raise ValueError(f"baseline saved-kit status is required for {device}")
            document = _build_anchor_spec(
                anchor,
                device,
                sources[device],
                source_path=source_path,
                source_sha256=_required_hash(source_hashes, source_path),
                baseline_mapping_status=status_document,
            )
            filename = rush16_spec_filename(anchor.anchor_id, device)
            documents[filename] = document
    documents["RUSH16_FAMILY.yaml"] = build_rush16_family_document(source_hashes)
    return MappingProxyType(documents)


def build_rush16_family_document(source_hashes: Mapping[str, str]) -> dict[str, object]:
    """Return the deterministic family contract shared by all eight specs."""

    return {
        "spec_version": 1,
        "family_name": "RUSH16",
        "batch_id": RUSH16_BATCH_ID,
        "batch_version": RUSH16_VERSION,
        "source_specifications": {
            path: {"sha256": _required_hash(source_hashes, path), "role": "exact semantic source"}
            for path in _SOURCE_SPEC.values()
        },
        "shared_family_locks": list(RUSH16_SHARED_FAMILY_LOCKS),
        "status_vocabulary": list(RUSH16_STATUS_VALUES),
        "anchors": [
            {
                "anchor_id": anchor.anchor_id,
                "frequency_owner": anchor.frequency_owner,
                "expected_performance_role": anchor.expected_role,
                "rytm_spec": rush16_spec_filename(anchor.anchor_id, RUSH01_DEVICE_RYTM),
                "a4_spec": rush16_spec_filename(anchor.anchor_id, RUSH01_DEVICE_A4),
            }
            for anchor in RUSH16_ANCHORS
        ],
        "audition_lock": {
            "same_oxi_pattern": True,
            "same_tempo": True,
            "same_root": True,
            "same_velocities": True,
            "same_note_lengths": True,
            "same_gain_staging": True,
            "octatrack_role": "routing_and_recording_only",
            "octatrack_forbidden": [
                "transition scenes",
                "retriggers",
                "reverb freeze",
                "master coloration",
            ],
        },
        "finalization_policy": {
            "direct_sysex_requires_all_critical_writer_ready": True,
            "hardware_assisted_requires_all_critical_midi_ready": True,
            "hardware_return_dump_is_canonical": True,
            "partial_kits_are_never_final": True,
            "manual_sound_parameter_entry": "forbidden",
        },
    }


def rush16_spec_filename(anchor_id: str, device: Rush01Device) -> str:
    """Return the tracked filename for one exact anchor/device spec."""

    return f"{anchor_id}_{_SPEC_SUFFIX[device]}.yaml"


def validate_rush16_spec(spec: object, device: Rush01Device) -> Rush01MidiPlan:
    """Validate semantic coverage, status vocabulary, and no-sample policy."""

    root = _require_mapping(spec, path="spec")
    metadata = _require_mapping(root.get("rush16"), path="spec.rush16")
    if metadata.get("batch_version") != RUSH16_VERSION:
        raise ValueError("RUSH16 spec has an unsupported batch version")
    if metadata.get("device") != device:
        raise ValueError("RUSH16 metadata device does not match selected device")
    plan = compile_rush01_midi_plan(device, root)
    readiness = rush16_field_readiness(spec)
    expected_paths = _semantic_paths(plan, root, device)
    if set(readiness) != set(expected_paths):
        missing = sorted(set(expected_paths) - set(readiness))
        extra = sorted(set(readiness) - set(expected_paths))
        raise ValueError(f"RUSH16 field-status coverage mismatch: missing={missing}, extra={extra}")
    critical_manual = sorted(
        path
        for path, entry in readiness.items()
        if entry.sound_critical and entry.status == MANUAL_MENU_ACTION_ONLY
    )
    if critical_manual:
        raise ValueError(
            "manual_menu_action_only is forbidden for sound parameters: "
            + ", ".join(critical_manual)
        )
    _validate_no_sample_dependencies(root, device)
    return plan


def rush16_field_readiness(spec: object) -> Mapping[str, Rush16FieldReadiness]:
    """Read and validate the explicit per-semantic-path status records."""

    root = _require_mapping(spec, path="spec")
    metadata = _require_mapping(root.get("rush16"), path="spec.rush16")
    statuses = _require_mapping(
        metadata.get("semantic_field_statuses"),
        path="spec.rush16.semantic_field_statuses",
    )
    parsed: dict[str, Rush16FieldReadiness] = {}
    for path, raw_entry in statuses.items():
        if not isinstance(path, str) or not path:
            raise ValueError("RUSH16 semantic field paths must be non-empty strings")
        entry = _require_mapping(raw_entry, path=f"semantic_field_statuses.{path}")
        status = entry.get("status")
        if status not in RUSH16_STATUS_VALUES:
            raise ValueError(f"unsupported RUSH16 status for {path}: {status}")
        critical = entry.get("sound_critical")
        if not isinstance(critical, bool):
            raise ValueError(f"sound_critical must be boolean for {path}")
        reason = entry.get("reason")
        source = entry.get("evidence_source")
        if not isinstance(reason, str) or not reason:
            raise ValueError(f"readiness reason is required for {path}")
        if not isinstance(source, str) or not source:
            raise ValueError(f"readiness evidence source is required for {path}")
        parsed[path] = Rush16FieldReadiness(
            semantic_path=path,
            status=cast(Rush16FieldStatus, status),
            sound_critical=critical,
            reason=reason,
            evidence_source=source,
        )
    return MappingProxyType(parsed)


def rush16_hardware_blockers(
    spec: object,
    plan: Rush01MidiPlan,
) -> tuple[str, ...]:
    """Return every critical semantic path that prevents complete automatic apply."""

    readiness = rush16_field_readiness(spec)
    fields = {field.semantic_path: field for field in plan.fields}
    blockers: list[str] = []
    for path, entry in readiness.items():
        if not entry.sound_critical:
            continue
        field = fields.get(path)
        if field is None:
            if path.endswith(".sample.dependency") and rush16_value_at_path(spec, path) == "none":
                continue
            blockers.append(path)
            continue
        if field.status not in _MIDI_ALLOWED:
            blockers.append(path)
    return tuple(sorted(blockers))


def validate_rush16_plan_for_apply(spec: object, plan: Rush01MidiPlan) -> None:
    """Fail before provider construction when an anchor would be applied partially."""

    validate_rush16_spec(spec, plan.device)
    blockers = rush16_hardware_blockers(spec, plan)
    if blockers:
        raise ValueError(
            "RUSH16 plan is incomplete; automated calibration is required for: "
            + ", ".join(blockers)
        )
    unencoded = tuple(
        field.semantic_path
        for field in plan.fields
        if field.status == STATUS_READY
        and (field.channel is None or field.ordered_midi_bytes is None)
    )
    if unencoded:
        raise ValueError(
            "RUSH16 ready fields require configured channels and encoded messages: "
            + ", ".join(unencoded)
        )


def build_rush16_build_entry(
    *,
    anchor_id: str,
    device: Rush01Device,
    spec_filename: str,
    spec_bytes: bytes,
    spec: object,
    plan: Rush01MidiPlan,
    sysex_status: Rush01SysexCalibrationStatus,
    hardware_capture_configured: bool,
) -> Rush16BuildEntry:
    """Combine compiler and differential evidence without producing a kit file."""

    readiness = rush16_field_readiness(spec)
    direct_blockers = tuple(
        sorted(
            field.semantic_path
            for field in sysex_status.fields
            if field.critical and field.status not in _DIRECT_ALLOWED
        )
    )
    hardware_blockers = rush16_hardware_blockers(spec, plan)
    direct_ready = sysex_status.reference.byte_identical and not direct_blockers
    apply_ready = plan.configuration_ready and not hardware_blockers
    counts = Counter(entry.status for entry in readiness.values())
    return Rush16BuildEntry(
        anchor_id=anchor_id,
        device=device,
        spec_filename=spec_filename,
        target_filename=f"{anchor_id}_{_SPEC_SUFFIX[device]}.syx",
        spec_sha256=sha256(spec_bytes).hexdigest(),
        reference_sha256=sysex_status.reference.sha256,
        reference_round_trip_identical=sysex_status.reference.byte_identical,
        direct_sysex_ready=direct_ready,
        hardware_apply_ready=apply_ready,
        hardware_capture_configured=hardware_capture_configured,
        hardware_assisted_ready=apply_ready and hardware_capture_configured,
        final_sysex_generated=False,
        direct_blockers=direct_blockers,
        hardware_blockers=hardware_blockers,
        status_counts={status: counts.get(status, 0) for status in RUSH16_STATUS_VALUES},
        midi_ready_fields=plan.summary.ready_fields,
        midi_message_count=plan.summary.transport_message_count,
        output_port_configured=plan.output_port is not None,
    )


def rush16_anchor_id(spec: object) -> str:
    """Return the validated anchor id embedded in a RUSH16 spec."""

    root = _require_mapping(spec, path="spec")
    metadata = _require_mapping(root.get("rush16"), path="spec.rush16")
    anchor_id = metadata.get("anchor_id")
    if not isinstance(anchor_id, str) or anchor_id not in {
        anchor.anchor_id for anchor in RUSH16_ANCHORS
    }:
        raise ValueError("RUSH16 spec has an unknown anchor_id")
    return anchor_id


def _build_anchor_spec(
    anchor: Rush16AnchorDefinition,
    device: Rush01Device,
    source: object,
    *,
    source_path: str,
    source_sha256: str,
    baseline_mapping_status: object,
) -> dict[str, object]:
    root = deepcopy(dict(_require_mapping(source, path=source_path)))
    suffix = _SPEC_SUFFIX[device]
    root["spec_name"] = f"RUSH16_{anchor.anchor_id}_{suffix}"
    differences = anchor.rytm_differences if device == RUSH01_DEVICE_RYTM else anchor.a4_differences
    recorded_differences: list[dict[str, object]] = []
    for path, requested in differences:
        original = deepcopy(rush16_value_at_path(root, path))
        _set_value_at_path(root, path, deepcopy(requested))
        recorded_differences.append(
            {"semantic_path": path, "source_value": original, "requested_value": requested}
        )
    plan = compile_rush01_midi_plan(device, root)
    mapping_status_by_path = _baseline_mapping_status_by_path(baseline_mapping_status)
    field_statuses = _build_field_statuses(root, device, plan, mapping_status_by_path)
    root["rush16"] = {
        "batch_id": RUSH16_BATCH_ID,
        "batch_version": RUSH16_VERSION,
        "anchor_id": anchor.anchor_id,
        "device": device,
        "device_model": _DEVICE_LABEL[device],
        "source_specification": source_path,
        "source_specification_sha256": source_sha256,
        "shared_family_locks": list(RUSH16_SHARED_FAMILY_LOCKS),
        "kit_specific_differences": recorded_differences,
        "intended_frequency_owner": anchor.frequency_owner,
        "expected_performance_role": anchor.expected_role,
        "external_sample_dependency": "none",
        "manual_sound_parameter_entry": "forbidden",
        "semantic_field_statuses": field_statuses,
    }
    validate_rush16_spec(root, device)
    return root


def _build_field_statuses(
    spec: Mapping[str, object],
    device: Rush01Device,
    plan: Rush01MidiPlan,
    mapping_status_by_path: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    fields = {field.semantic_path: field for field in plan.fields}
    statuses: dict[str, object] = {}
    for path in _semantic_paths(plan, spec, device):
        critical = _is_sound_critical(path)
        sysex_entry = mapping_status_by_path.get(path)
        midi_field = fields.get(path)
        status, reason, source = _field_status(
            path,
            critical=critical,
            sysex_entry=sysex_entry,
            midi_field=midi_field,
            requested=rush16_value_at_path(spec, path),
        )
        statuses[path] = {
            "status": status,
            "sound_critical": critical,
            "reason": reason,
            "evidence_source": source,
        }
    return statuses


def _field_status(
    path: str,
    *,
    critical: bool,
    sysex_entry: Mapping[str, object] | None,
    midi_field: Rush01MidiField | None,
    requested: object,
) -> tuple[Rush16FieldStatus, str, str]:
    if sysex_entry is not None and sysex_entry.get("status") in _DIRECT_ALLOWED:
        return (
            WRITER_READY,
            str(sysex_entry.get("reason") or "saved-kit mapping is promoted"),
            "RUSH01 saved-kit calibration status",
        )
    if path.endswith(".sample.dependency") and requested == "none":
        return (
            WRITER_READY,
            "explicit no-external-sample dependency policy requires no transmitted value",
            "RUSH16 family policy",
        )
    if midi_field is None:
        return (
            BLOCKED_UNVERIFIED,
            "semantic path is absent from both saved-kit and MIDI compiler evidence",
            "RUSH16 fail-closed coverage sweep",
        )
    if midi_field.status == STATUS_READY:
        return MIDI_APPLY_READY, midi_field.reason, midi_field.mapping_evidence
    if midi_field.status == STATUS_PRESERVE_REFERENCE:
        return WRITER_READY, midi_field.reason, midi_field.mapping_evidence
    if midi_field.status == STATUS_INVALID_SPEC_FIELD:
        return BLOCKED_UNVERIFIED, midi_field.reason, midi_field.mapping_evidence
    if midi_field.status in {STATUS_LEARN_REQUIRED, STATUS_MANUAL_SETUP_REQUIRED}:
        if not critical and (path == "build_policy.kit_name" or path.endswith(".sound_name")):
            return MANUAL_MENU_ACTION_ONLY, midi_field.reason, midi_field.mapping_evidence
        return CALIBRATION_REQUIRED, midi_field.reason, midi_field.mapping_evidence
    return BLOCKED_UNVERIFIED, midi_field.reason, midi_field.mapping_evidence


def _semantic_paths(
    plan: Rush01MidiPlan,
    spec: Mapping[str, object],
    device: Rush01Device,
) -> tuple[str, ...]:
    paths = [field.semantic_path for field in plan.fields]
    track_order = (
        ("BD", "SD", "RS", "CP", "BT", "LT", "MT", "HT", "CH", "OH", "CY", "CB")
        if device == RUSH01_DEVICE_RYTM
        else ("T1", "T2", "T3", "T4")
    )
    if device == RUSH01_DEVICE_RYTM:
        paths.extend(f"tracks.{track}.sample.dependency" for track in track_order)
    for path in paths:
        rush16_value_at_path(spec, path)
    return tuple(paths)


def _is_sound_critical(path: str) -> bool:
    if path == "build_policy.kit_name" or path.startswith("track_levels.F"):
        return False
    return not (
        path == "track_levels.CV" or path.endswith(".sound_name") or path.endswith(".design_role")
    )


def _baseline_mapping_status_by_path(
    document: object,
) -> Mapping[str, Mapping[str, object]]:
    root = _require_mapping(document, path="baseline_mapping_status")
    fields = root.get("fields")
    if not isinstance(fields, Sequence) or isinstance(fields, (str, bytes, bytearray)):
        raise ValueError("baseline mapping status fields must be a sequence")
    result: dict[str, Mapping[str, object]] = {}
    for index, raw_field in enumerate(fields):
        field = _require_mapping(raw_field, path=f"baseline_mapping_status.fields[{index}]")
        path = field.get("semantic_path")
        if isinstance(path, str):
            result[path] = field
    return MappingProxyType(result)


def _validate_no_sample_dependencies(spec: Mapping[str, object], device: Rush01Device) -> None:
    if device != RUSH01_DEVICE_RYTM:
        return
    tracks = _require_mapping(spec.get("tracks"), path="spec.tracks")
    for track, raw_track in tracks.items():
        track_spec = _require_mapping(raw_track, path=f"spec.tracks.{track}")
        sample = _require_mapping(track_spec.get("sample"), path=f"spec.tracks.{track}.sample")
        if sample.get("level") != 0 or sample.get("dependency") != "none":
            raise ValueError(f"RUSH16 {track} must have sample level 0 and dependency none")


def _required_hash(hashes: Mapping[str, str], path: str) -> str:
    value = hashes.get(path)
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError(f"SHA-256 is required for {path}")
    return value


def rush16_value_at_path(root: object, path: str) -> object:
    current = root
    parts = path.split(".")
    for index, part in enumerate(parts):
        mapping = _require_mapping(current, path=".".join(parts[:index]) or "root")
        if part not in mapping:
            raise ValueError(f"semantic path does not exist: {path}")
        current = mapping[part]
    return current


def _set_value_at_path(root: dict[str, object], path: str, value: object) -> None:
    current = root
    parts = path.split(".")
    for part in parts[:-1]:
        child = current.get(part)
        if not isinstance(child, dict):
            raise ValueError(f"semantic parent path is not mutable: {path}")
        current = child
    if parts[-1] not in current:
        raise ValueError(f"semantic path does not exist: {path}")
    current[parts[-1]] = value


__all__ = [
    "BLOCKED_UNVERIFIED",
    "CALIBRATION_REQUIRED",
    "MANUAL_MENU_ACTION_ONLY",
    "MIDI_APPLY_READY",
    "WRITER_READY",
    "Rush16BuildEntry",
    "Rush16FieldReadiness",
    "build_rush16_build_entry",
    "build_rush16_family_document",
    "build_rush16_spec_documents",
    "rush16_anchor_id",
    "rush16_field_readiness",
    "rush16_hardware_blockers",
    "rush16_spec_filename",
    "rush16_value_at_path",
    "validate_rush16_plan_for_apply",
    "validate_rush16_spec",
]
