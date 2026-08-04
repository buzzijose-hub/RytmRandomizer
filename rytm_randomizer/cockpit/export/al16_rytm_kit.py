"""Passive AL16 Analog Rytm saved-kit compiler and evidence reporter."""

from __future__ import annotations

import hashlib
import json
import os
import time
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Final, cast

from ...data.al16_rytm import (
    AL16_BANK_STATES,
    AL16_PAD_ROLES,
    AL16_PRESERVED_GLOBAL_SECTIONS,
    AL16_RYTM_APPROVED_TUNING,
    AL16_RYTM_FILTER_TYPES,
    AL16_RYTM_WRITABLE_FIELDS,
    AL16_TRACK_MODE_PATCH,
    AL16_TRACK_MODE_PRESERVE,
    RYTM_CONVERTER_CENTERED_7BIT,
    RYTM_CONVERTER_FILTER_TYPE_ENUM,
    RYTM_CONVERTER_VERIFIED_7BIT,
    RytmValueConverter,
)
from ...data.analog_rytm_kit_layout import (
    RYTM_KIT_NAME_LENGTH,
    RYTM_KIT_NAME_OFFSET,
    RYTM_KIT_TRACK_SOUND_SIZE,
    RYTM_KIT_TRACKS_OFFSET,
    RYTM_SOUND_FIELD_BY_NRPN_LSB,
    RYTM_SOUND_MACHINE_TYPE_OFFSET,
)
from ...data.rytm_machine_catalog import (
    RYTM_MACHINE_PROFILES,
    get_rytm_machine_profile,
    is_machine_allowed_on_pad,
)
from ...devices.analog_rytm import get_analog_rytm_saved_kit_codec_capability
from ...observability.logging import get_logger
from ...observability.metrics import get_metrics
from ...observability.tracing import operation
from ...snapshot import read_ascii_name
from .file_export_contracts import (
    LocalFileExportPhase,
    attach_local_file_export_error_context,
    classify_local_file_export_error,
    local_file_export_error_context,
)
from .writer import atomic_write

_REFERENCE_EXPECTED_SHA256: Final[str] = (
    "8bda94d6d5031e038c8d810789301f35242ed539338a0399548869a34e1dc4dd"
)
_SOURCE_DATE_EPOCH: Final[str] = "SOURCE_DATE_EPOCH"
_DEFAULT_BUILD_EPOCH: Final[int] = 0
_PHASE_R1_STATE_NUMBER: Final[int] = 2
_AL16_EXPORT_FAILURE_FINGERPRINT: Final[str] = "al16.rytm_kit_export.failed"
_AL16_MAPPING_BLOCKED_ERROR_CODE: Final[str] = "mapping_blocked"

_logger = get_logger(__name__)


@dataclass(frozen=True)
class MappingGap:
    """One critical requested field that lacks positive writer evidence."""

    semantic_path: str
    pad: int | None
    machine: str | None
    expected_behavior: str
    reason: str
    evidence_required: str


@dataclass(frozen=True)
class FieldAudit:
    """Resolution record for one requested semantic field."""

    semantic_path: str
    original_semantic_value: object
    requested_semantic_value: object
    normalized_semantic_value: object
    encoded_raw_value_or_bytes: object
    raw_location: str | None
    converter_or_enumeration: str
    verification_status: str


@dataclass(frozen=True)
class Al16BuildResult:
    """Paths and status produced by one offline AL16 build attempt."""

    status: str
    output_path: Path
    manifest_path: Path
    validation_path: Path
    byte_diff_path: Path
    reference_sha256: str
    output_sha256: str | None
    gaps: tuple[MappingGap, ...]


def _as_mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object with string keys")
    untyped = cast(dict[object, object], value)
    if not all(isinstance(key, str) for key in untyped):
        raise ValueError(f"{label} must be an object with string keys")
    return cast(Mapping[str, object], untyped)


def _as_string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be a non-empty string")
    return value


def _as_int(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{label} must be an integer")
    return value


def _as_string_list(value: object, label: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ValueError(f"{label} must be an array of strings")
    items = cast(list[object], value)
    if not all(isinstance(item, str) for item in items):
        raise ValueError(f"{label} must be an array of strings")
    return tuple(cast(str, item) for item in items)


def _require_exact_keys(
    value: Mapping[str, object],
    label: str,
    expected: set[str],
) -> None:
    actual = set(value)
    if actual == expected:
        return
    missing = sorted(expected - actual)
    unknown = sorted(actual - expected)
    details: list[str] = []
    if missing:
        details.append(f"missing={missing}")
    if unknown:
        details.append(f"unknown={unknown}")
    raise ValueError(f"{label} keys are invalid: {', '.join(details)}")


def _load_recipe(path: Path) -> Mapping[str, object]:
    # JSON is a strict YAML subset, keeping the public recipe dependency-free.
    parsed = cast(object, json.loads(path.read_text(encoding="utf-8")))
    return _as_mapping(parsed, "recipe")


def _canonical_recipe_value(value: object) -> object:
    if isinstance(value, Mapping):
        canonical: dict[str, object] = {}
        for key, item in cast(Mapping[object, object], value).items():
            if not isinstance(key, str):
                raise ValueError("deterministic recipe mappings require string keys")
            canonical[key] = _canonical_recipe_value(item)
        return canonical
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [_canonical_recipe_value(item) for item in cast(Sequence[object], value)]
    return value


def deterministic_recipe_identifier(recipe: Mapping[str, object]) -> str:
    canonical = json.dumps(
        _canonical_recipe_value(recipe),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return hashlib.sha256(canonical.encode("ascii")).hexdigest()


def _build_timestamp() -> str:
    raw_epoch = os.environ.get(_SOURCE_DATE_EPOCH, str(_DEFAULT_BUILD_EPOCH))
    try:
        return datetime.fromtimestamp(int(raw_epoch), tz=UTC).isoformat()
    except (ValueError, OverflowError, OSError) as exc:
        raise ValueError("SOURCE_DATE_EPOCH must be an in-range integer Unix timestamp") from exc


def _portable_reference_path(reference: Path) -> str:
    return f"reference/{reference.name}"


def _atomic_write_text(path: Path, value: str) -> None:
    try:
        atomic_write(path, value.encode("utf-8"), overwrite=True)
    except (ValueError, TypeError, OSError) as exc:
        phase: LocalFileExportPhase = "output_write"
        attach_local_file_export_error_context(
            exc,
            error_code=classify_local_file_export_error(exc, phase=phase),
            phase=phase,
            artifact_name=path.name,
        )
        raise


def _artifact_paths(output_path: Path) -> tuple[Path, Path, Path]:
    return (
        output_path.with_name(f"{output_path.stem}_manifest.json"),
        output_path.with_name(f"{output_path.stem}_validation.md"),
        output_path.with_name(f"{output_path.stem}_byte_diff.txt"),
    )


def _canonical_path_key(path: Path) -> str:
    return os.path.normcase(str(path.resolve(strict=False)))


def _validate_artifact_paths(
    *,
    reference_path: Path,
    recipe_path: Path,
    output_path: Path,
    manifest_path: Path,
    validation_path: Path,
    byte_diff_path: Path,
) -> None:
    inputs = {"reference": reference_path, "recipe": recipe_path}
    artifacts = {
        "output": output_path,
        "manifest": manifest_path,
        "validation": validation_path,
        "byte diff": byte_diff_path,
    }
    input_keys = {label: _canonical_path_key(path) for label, path in inputs.items()}
    artifact_keys: dict[str, str] = {}
    for artifact_label, artifact_path in artifacts.items():
        artifact_key = _canonical_path_key(artifact_path)
        for input_label, input_key in input_keys.items():
            if artifact_key == input_key:
                raise ValueError(
                    f"{artifact_label} artifact path collides with {input_label} input"
                )
        for other_label, other_key in artifact_keys.items():
            if artifact_key == other_key:
                raise ValueError(
                    f"{artifact_label} artifact path collides with {other_label} artifact"
                )
        artifact_keys[artifact_label] = artifact_key


def _track_offset(pad: int, sound_offset: int) -> int:
    return RYTM_KIT_TRACKS_OFFSET + ((pad - 1) * RYTM_KIT_TRACK_SOUND_SIZE) + sound_offset


def _machine_label_for_raw(raw_value: int) -> str:
    machine_value = raw_value & 0x7F
    for profile in RYTM_MACHINE_PROFILES:
        if profile.machine_value == machine_value:
            return profile.label
    return f"unknown machine value {machine_value}"


def _convert_supported_value(
    converter: RytmValueConverter,
    requested: object,
) -> tuple[object, int]:
    if converter == RYTM_CONVERTER_VERIFIED_7BIT:
        raw = _as_int(requested, "verified 7-bit value")
        if not 0 <= raw <= 127:
            raise ValueError("verified 7-bit value must be in 0..127")
        return raw, raw
    if converter == RYTM_CONVERTER_CENTERED_7BIT:
        if requested in ("neutral", "center"):
            return 0, 64
        displayed = _as_int(requested, "centered display value")
        if not -64 <= displayed <= 63:
            raise ValueError("centered display value must be in -64..63")
        return displayed, displayed + 64
    if converter == RYTM_CONVERTER_FILTER_TYPE_ENUM:
        label = _as_string(requested, "filter type").upper()
        try:
            return label, AL16_RYTM_FILTER_TYPES[label]
        except KeyError as exc:
            raise ValueError(f"unsupported filter type: {label}") from exc
    raise ValueError(f"unknown AL16 converter: {converter}")


def _original_semantic(converter: RytmValueConverter, raw_value: int) -> object:
    low7 = raw_value & 0x7F
    if converter == RYTM_CONVERTER_CENTERED_7BIT:
        return low7 - 64
    if converter == RYTM_CONVERTER_FILTER_TYPE_ENUM:
        for label, encoded in AL16_RYTM_FILTER_TYPES.items():
            if encoded == low7:
                return label
        return f"unknown filter type {low7}"
    return low7


def _gap_audit(path: str, requested: object, status: str = "critical_mapping_gap") -> FieldAudit:
    return FieldAudit(
        semantic_path=path,
        original_semantic_value=None,
        requested_semantic_value=requested,
        normalized_semantic_value=None,
        encoded_raw_value_or_bytes=None,
        raw_location=None,
        converter_or_enumeration="none_unverified",
        verification_status=status,
    )


def _supported_audit(
    *,
    raw: bytes,
    pad: int,
    semantic_path: str,
    field_key: str,
    requested: object,
) -> FieldAudit:
    writable = AL16_RYTM_WRITABLE_FIELDS[field_key]
    layout = RYTM_SOUND_FIELD_BY_NRPN_LSB[writable.nrpn_lsb]
    offset = _track_offset(pad, layout.sound_offset)
    normalized, encoded = _convert_supported_value(writable.converter, requested)
    return FieldAudit(
        semantic_path=semantic_path,
        original_semantic_value=_original_semantic(writable.converter, raw[offset]),
        requested_semantic_value=requested,
        normalized_semantic_value=normalized,
        encoded_raw_value_or_bytes=[encoded],
        raw_location=f"unpacked[{offset}] (track sound + 0x{layout.sound_offset:04X})",
        converter_or_enumeration=writable.converter,
        verification_status="resolved_but_not_emitted_while_preflight_is_blocked",
    )


def _record_machine(
    raw: bytes,
    pad: int,
    track: Mapping[str, object],
    audits: list[FieldAudit],
    gaps: list[MappingGap],
) -> str | None:
    requested_key = _as_string(track.get("machine"), f"tracks.{pad}.machine")
    path = f"tracks.{pad}.machine"
    machine_offset = _track_offset(pad, RYTM_SOUND_MACHINE_TYPE_OFFSET)
    original_label = _machine_label_for_raw(raw[machine_offset])
    try:
        profile = get_rytm_machine_profile(requested_key)
    except KeyError:
        allowed_catalog = ", ".join(
            f"{candidate.key} ({candidate.label})"
            for candidate in RYTM_MACHINE_PROFILES
            if is_machine_allowed_on_pad(pad, candidate.key)
        )
        audits.append(_gap_audit(path, requested_key))
        gaps.append(
            MappingGap(
                semantic_path=path,
                pad=pad,
                machine=requested_key,
                expected_behavior="Resolve an exact catalog machine and validate it for the pad.",
                reason=(
                    f"{requested_key!r} is not an exact Analog Rytm machine catalog key. "
                    f"Verified catalog choices for pad {pad}: {allowed_catalog}."
                ),
                evidence_required=(
                    "Choose the intended existing machine explicitly. The recipe's CH BASIC "
                    "wording must not be silently translated to CH Classic or HH Basic."
                ),
            )
        )
        return None

    if not is_machine_allowed_on_pad(pad, profile.key):
        audits.append(_gap_audit(path, requested_key, "invalid_machine_for_pad"))
        gaps.append(
            MappingGap(
                semantic_path=path,
                pad=pad,
                machine=profile.label,
                expected_behavior="Select a machine legally supported by the physical pad.",
                reason=f"{profile.label} is not allowed on pad {pad}.",
                evidence_required="Choose a machine from the pad capability catalog.",
            )
        )
        return profile.key

    original_value = raw[machine_offset] & 0x7F
    if original_value == profile.machine_value:
        audits.append(
            FieldAudit(
                semantic_path=path,
                original_semantic_value=original_label,
                requested_semantic_value=profile.label,
                normalized_semantic_value=profile.machine_value,
                encoded_raw_value_or_bytes=[raw[machine_offset]],
                raw_location=f"unpacked[{machine_offset}]",
                converter_or_enumeration="verified_machine_catalog_preserve",
                verification_status="verified_preserved_machine",
            )
        )
        return profile.key

    audits.append(_gap_audit(path, profile.label))
    gaps.append(
        MappingGap(
            semantic_path=path,
            pad=pad,
            machine=profile.label,
            expected_behavior=f"Change {original_label} to {profile.label} without altering flags.",
            reason="Saved-kit machine selection has a candidate location but is not writer-validated.",
            evidence_required=(
                "A saved-kit before/after capture proving the machine byte and adjacent validity bits."
            ),
        )
    )
    return profile.key


def _record_source_fields(
    pad: int,
    machine_key: str | None,
    source: Mapping[str, object],
    audits: list[FieldAudit],
    gaps: list[MappingGap],
) -> None:
    for field_name in sorted(source):
        requested = source[field_name]
        path = f"tracks.{pad}.source.{field_name}"
        if field_name == "target_note" and machine_key is not None:
            note = _as_string(requested, path).upper()
            tuning_key = (machine_key, note)
            if tuning_key in AL16_RYTM_APPROVED_TUNING:
                raw_tune = AL16_RYTM_APPROVED_TUNING[tuning_key]
                audits.append(
                    FieldAudit(
                        semantic_path=path,
                        original_semantic_value=None,
                        requested_semantic_value=note,
                        normalized_semantic_value=note,
                        encoded_raw_value_or_bytes=[raw_tune],
                        raw_location=None,
                        converter_or_enumeration=f"approved_tuning_table:{machine_key}",
                        verification_status="resolved_tuning_pending_source_writer",
                    )
                )
            else:
                audits.append(_gap_audit(path, note))
                gaps.append(
                    MappingGap(
                        semantic_path=path,
                        pad=pad,
                        machine=machine_key,
                        expected_behavior=f"Resolve {note} through a {machine_key}-specific tuning table.",
                        reason="No approved tuning observation exists for this machine/note pair.",
                        evidence_required=(
                            "A hardware-verified displayed-note/raw-tune observation for this machine."
                        ),
                    )
                )
            continue

        audits.append(_gap_audit(path, requested))
        gaps.append(
            MappingGap(
                semantic_path=path,
                pad=pad,
                machine=machine_key,
                expected_behavior="Write the selected machine-specific source parameter.",
                reason="Rytm source parameters are live-addressed but not saved-kit writer-validated.",
                evidence_required=(
                    "A saved-kit before/after capture proving the machine-specific field location "
                    "and typed display-to-raw conversion."
                ),
            )
        )


def _record_common_fields(
    raw: bytes,
    pad: int,
    section_name: str,
    section: Mapping[str, object],
    audits: list[FieldAudit],
    gaps: list[MappingGap],
    machine_key: str | None,
) -> None:
    for field_name in sorted(section):
        requested = section[field_name]
        field_key = f"{section_name}.{field_name}"
        semantic_path = f"tracks.{pad}.{field_key}"
        if field_key in AL16_RYTM_WRITABLE_FIELDS:
            audits.append(
                _supported_audit(
                    raw=raw,
                    pad=pad,
                    semantic_path=semantic_path,
                    field_key=field_key,
                    requested=requested,
                )
            )
            continue
        audits.append(_gap_audit(semantic_path, requested))
        gaps.append(
            MappingGap(
                semantic_path=semantic_path,
                pad=pad,
                machine=machine_key,
                expected_behavior=f"Write {field_key} as a typed saved-kit value.",
                reason="This common field is not in the strict saved-kit writer allowlist.",
                evidence_required="A promoted saved-kit location and converter with round-trip evidence.",
            )
        )


def _inspect_recipe(
    recipe: Mapping[str, object],
    raw: bytes,
    destination_slot: int,
) -> tuple[list[FieldAudit], list[MappingGap], list[int]]:
    if not 0 <= destination_slot <= 127:
        raise ValueError("destination slot must be in 0..127")
    _require_exact_keys(
        recipe,
        "recipe",
        {"schema_version", "project_id", "kit", "preserve", "tracks"},
    )
    if _as_int(recipe.get("schema_version"), "schema_version") != 1:
        raise ValueError("recipe schema_version must be 1")
    project_id = _as_string(recipe.get("project_id"), "project_id")
    if project_id != "AL16":
        raise ValueError("recipe project_id must be AL16")
    kit = _as_mapping(recipe.get("kit"), "kit")
    _require_exact_keys(
        kit,
        "kit",
        {"state", "name", "tonal_zone", "performance_context_bpm", "description"},
    )
    state_number = _as_int(kit.get("state"), "kit.state")
    if not 1 <= state_number <= len(AL16_BANK_STATES):
        raise ValueError("kit.state must be in 1..16")
    if state_number != _PHASE_R1_STATE_NUMBER:
        raise ValueError("Phase R1 supports only the AL02 LOCK proof recipe")
    state = AL16_BANK_STATES[state_number - 1]
    kit_name = _as_string(kit.get("name"), "kit.name")
    try:
        encoded_kit_name = kit_name.encode("ascii")
    except UnicodeEncodeError as exc:
        raise ValueError("kit.name must fit the 16-byte ASCII Rytm name field") from exc
    if len(encoded_kit_name) > RYTM_KIT_NAME_LENGTH:
        raise ValueError("kit.name must fit the 16-byte ASCII Rytm name field")
    if kit_name != f"AL{state.number:02d} {state.name}":
        raise ValueError("kit.name must match the reserved AL16 bank state")
    tonal_zone = _as_string(kit.get("tonal_zone"), "kit.tonal_zone")
    if tonal_zone != state.tonal_zone:
        raise ValueError("kit.tonal_zone must match the reserved AL16 bank state")
    if _as_int(kit.get("performance_context_bpm"), "kit.performance_context_bpm") != 138:
        raise ValueError("kit.performance_context_bpm must be 138")
    _as_string(kit.get("description"), "kit.description")
    preserve = _as_string_list(recipe.get("preserve"), "preserve")
    if preserve != AL16_PRESERVED_GLOBAL_SECTIONS:
        raise ValueError("preserve must list the complete ordered AL16 preservation boundary")

    original_name = read_ascii_name(raw, RYTM_KIT_NAME_OFFSET, RYTM_KIT_NAME_LENGTH)
    audits = [
        FieldAudit(
            semantic_path="kit.name",
            original_semantic_value=original_name,
            requested_semantic_value=kit_name,
            normalized_semantic_value=kit_name,
            encoded_raw_value_or_bytes=list(encoded_kit_name.ljust(RYTM_KIT_NAME_LENGTH, b"\x00")),
            raw_location=(
                f"unpacked[{RYTM_KIT_NAME_OFFSET}:"
                f"{RYTM_KIT_NAME_OFFSET + RYTM_KIT_NAME_LENGTH}]"
            ),
            converter_or_enumeration="ascii_16",
            verification_status="resolved_but_not_emitted_while_preflight_is_blocked",
        ),
        _gap_audit("destination_slot", destination_slot),
    ]
    gaps = [
        MappingGap(
            semantic_path="destination_slot",
            pad=None,
            machine=None,
            expected_behavior=f"Address user-selected destination slot {destination_slot}.",
            reason="The Rytm kit object-number header byte is not writer-validated on this branch.",
            evidence_required="One scratch-slot import/dump proving the destination header byte.",
        )
    ]

    tracks = _as_mapping(recipe.get("tracks"), "tracks")
    expected_pads = tuple(AL16_PAD_ROLES)
    if set(tracks) != {str(pad) for pad in expected_pads}:
        raise ValueError("recipe must describe exactly pads 1..12")
    preserved: list[int] = []
    for pad in expected_pads:
        track = _as_mapping(tracks[str(pad)], f"tracks.{pad}")
        role = _as_string(track.get("role"), f"tracks.{pad}.role")
        if role != AL16_PAD_ROLES[pad]:
            raise ValueError(f"tracks.{pad}.role does not match the permanent AL16 pad role")
        mode = _as_string(track.get("mode"), f"tracks.{pad}.mode")
        if mode == AL16_TRACK_MODE_PRESERVE:
            _require_exact_keys(track, f"tracks.{pad}", {"role", "mode"})
            preserved.append(pad)
            continue
        if mode != AL16_TRACK_MODE_PATCH:
            raise ValueError(f"tracks.{pad}.mode must be patch or preserve")
        _require_exact_keys(
            track,
            f"tracks.{pad}",
            {"role", "mode", "machine", "source", "filter", "amp"},
        )

        machine_key = _record_machine(raw, pad, track, audits, gaps)
        source = _as_mapping(track.get("source", {}), f"tracks.{pad}.source")
        _record_source_fields(pad, machine_key, source, audits, gaps)
        for section_name in ("filter", "amp"):
            section = _as_mapping(track.get(section_name, {}), f"tracks.{pad}.{section_name}")
            _record_common_fields(
                raw,
                pad,
                section_name,
                section,
                audits,
                gaps,
                machine_key,
            )
    return audits, gaps, preserved


def _write_blocked_artifacts(
    *,
    manifest_path: Path,
    validation_path: Path,
    byte_diff_path: Path,
    manifest: Mapping[str, object],
    gaps: Sequence[MappingGap],
) -> None:
    _atomic_write_text(
        manifest_path,
        json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
    )
    gap_lines = [
        f"- `{gap.semantic_path}`: {gap.reason} Evidence required: {gap.evidence_required}"
        for gap in gaps
    ]
    _atomic_write_text(
        validation_path,
        "\n".join(
            [
                "# AL02 LOCK Rytm Validation",
                "",
                "## Result",
                "",
                "**BLOCKED: no SysEx was emitted.**",
                "",
                "The initialized reference decoded and re-encoded byte-for-byte, but critical "
                "requested writer mappings remain unverified. This report is not a successful "
                "kit build and is not a forensic recreation claim.",
                "",
                "## Verified offline evidence",
                "",
                "- The reference frame passed envelope, payload-size, checksum, and length checks.",
                "- Reference decode then encode was byte-for-byte identical.",
                "- The recipe contract, permanent pad roles, and pad/machine compatibility were audited.",
                "- No requested field was written because the full critical preflight did not pass.",
                "- Unknown and reserved reference bytes therefore remain byte-identical.",
                "",
                "## Critical mapping gaps",
                "",
                *gap_lines,
                "",
                "## Safety",
                "",
                "- MIDI ports enumerated: 0",
                "- MIDI ports opened: 0",
                "- MIDI or SysEx transmitted: 0",
                "- Partial output files emitted: 0",
                "- Reference file modified: no",
                "- Manual hardware import authorized: no; there is no AL02 SysEx to load",
                "",
                "## Deferred output checks",
                "",
                "Generated-kit decode, requested-value verification, changed-byte allowlist, "
                "output checksum, and hardware import proof are not applicable until all critical "
                "mapping gaps are resolved and a complete SysEx is emitted.",
                "",
            ]
        ),
    )
    _atomic_write_text(
        byte_diff_path,
        "AL16 AL02 LOCK byte-diff report\n"
        "status: blocked before mutation\n"
        "intentionally changed raw bytes: 0\n"
        "unknown or reserved bytes changed: 0\n"
        "output SysEx emitted: no\n"
        "reason: critical saved-kit mappings are not positively verified\n",
    )


def build_al16_rytm_kit(
    *,
    reference_path: Path,
    recipe_path: Path,
    destination_slot: int,
    output_path: Path,
) -> Al16BuildResult:
    """Compile one AL16 Rytm recipe or emit an exact fail-closed gap report."""

    metrics = get_metrics()
    started_at = time.perf_counter()
    export_phase: LocalFileExportPhase = "validation"
    failure_artifact_name = output_path.name
    operation_id = ""
    result: Al16BuildResult
    try:
        with operation(
            "al16_rytm_kit_export",
            logger=_logger,
            reference_name=reference_path.name,
            recipe_name=recipe_path.name,
            output_name=output_path.name,
            destination_slot=destination_slot,
        ) as operation_id:
            manifest_path, validation_path, byte_diff_path = _artifact_paths(output_path)
            _validate_artifact_paths(
                reference_path=reference_path,
                recipe_path=recipe_path,
                output_path=output_path,
                manifest_path=manifest_path,
                validation_path=validation_path,
                byte_diff_path=byte_diff_path,
            )
            export_phase = "output_write"
            failure_artifact_name = output_path.name
            if output_path.exists():
                raise FileExistsError(
                    "refusing a blocked build while a potentially stale output exists: "
                    f"{output_path}"
                )
            export_phase = "source_read"
            failure_artifact_name = reference_path.name
            reference_bytes = reference_path.read_bytes()
            reference_sha256 = hashlib.sha256(reference_bytes).hexdigest()
            if reference_sha256 != _REFERENCE_EXPECTED_SHA256:
                raise ValueError(
                    "initialized Analog Rytm reference SHA-256 mismatch: "
                    f"expected {_REFERENCE_EXPECTED_SHA256}, got {reference_sha256}"
                )
            codec = get_analog_rytm_saved_kit_codec_capability()
            decoded = codec.decode_saved_kit_frame(reference_bytes)
            if codec.encode_saved_kit_frame(decoded.header, decoded.unpacked) != reference_bytes:
                raise ValueError("Analog Rytm reference decode/encode is not byte-identical")

            export_phase = "source_read"
            failure_artifact_name = recipe_path.name
            recipe = _load_recipe(recipe_path)
            export_phase = "validation"
            audits, gaps, preserved_tracks = _inspect_recipe(
                recipe,
                decoded.unpacked,
                destination_slot,
            )

            kit = _as_mapping(recipe.get("kit"), "kit")
            manifest: dict[str, object] = {
                "schema_version": 1,
                "project_id": "AL16",
                "build_status": "blocked",
                "build_timestamp": _build_timestamp(),
                "deterministic_recipe_identifier": deterministic_recipe_identifier(recipe),
                "reference_file": _portable_reference_path(reference_path),
                "reference_sha256": reference_sha256,
                "expected_initialized_reference_sha256": _REFERENCE_EXPECTED_SHA256,
                "initialized_reference_sha256_matches_expected": (
                    reference_sha256 == _REFERENCE_EXPECTED_SHA256
                ),
                "reference_sysex_length": len(reference_bytes),
                "output_emitted": False,
                "output_sha256": None,
                "output_sysex_length": None,
                "destination_slot": destination_slot,
                "kit_name": _as_string(kit.get("name"), "kit.name"),
                "changed_semantic_fields": [],
                "semantic_field_audits": [asdict(audit) for audit in audits],
                "intentionally_changed_raw_bytes": 0,
                "critical_mapping_gaps": [asdict(gap) for gap in gaps],
                "critical_mapping_gap_count": len(gaps),
                "preserved_tracks": preserved_tracks,
                "preserved_sections": list(AL16_PRESERVED_GLOBAL_SECTIONS),
                "unsupported_optional_fields": [
                    "sample playback level preserved because saved-kit writing is not positively mapped"
                ],
                "tuning_table_source": (
                    "none: no approved XT Classic F2 saved-kit tuning observation is present"
                ),
                "reference_round_trip_byte_identical": True,
                "unknown_and_reserved_bytes_unchanged": True,
                "generated_output_checks": "not_applicable_blocked_before_mutation",
                "manual_hardware_import_authorized": False,
                "midi_ports_enumerated": 0,
                "midi_ports_opened": 0,
                "midi_messages_sent": 0,
            }
            export_phase = "output_write"
            failure_artifact_name = manifest_path.name
            _write_blocked_artifacts(
                manifest_path=manifest_path,
                validation_path=validation_path,
                byte_diff_path=byte_diff_path,
                manifest=manifest,
                gaps=gaps,
            )
            result = Al16BuildResult(
                status="blocked",
                output_path=output_path,
                manifest_path=manifest_path,
                validation_path=validation_path,
                byte_diff_path=byte_diff_path,
                reference_sha256=reference_sha256,
                output_sha256=None,
                gaps=tuple(gaps),
            )
    except (KeyError, ValueError, TypeError, OSError, KeyboardInterrupt, SystemExit) as exc:
        error_context = local_file_export_error_context(exc)
        if error_context is None:
            error_code = classify_local_file_export_error(exc, phase=export_phase)
            attach_local_file_export_error_context(
                exc,
                error_code=error_code,
                phase=export_phase,
                artifact_name=failure_artifact_name,
            )
            error_context = local_file_export_error_context(exc)
        if error_context is None:
            raise AssertionError("failed to attach bounded AL16 export error context") from exc
        duration_ms = (time.perf_counter() - started_at) * 1000.0
        metrics.record_export(duration_ms, error_code=error_context.error_code)
        _logger.warning(
            "AL16 Analog Rytm kit export failed",
            extra={
                "op_id": operation_id,
                "operation": "al16_rytm_kit_export",
                "outcome": "failed",
                "error_code": error_context.error_code,
                "failure_phase": error_context.phase,
                "artifact_name": error_context.artifact_name,
                "fingerprint": _AL16_EXPORT_FAILURE_FINGERPRINT,
                "reference_name": reference_path.name,
                "recipe_name": recipe_path.name,
                "output_name": output_path.name,
                "error_type": type(exc).__name__,
                "duration_ms": duration_ms,
                "metrics_summary": metrics.format_summary(),
            },
        )
        raise

    duration_ms = (time.perf_counter() - started_at) * 1000.0
    metrics.record_export(duration_ms, error_code=_AL16_MAPPING_BLOCKED_ERROR_CODE)
    _logger.info(
        "AL16 Analog Rytm kit export blocked by verified mapping gaps",
        extra={
            "op_id": operation_id,
            "operation": "al16_rytm_kit_export",
            "outcome": "blocked",
            "error_code": _AL16_MAPPING_BLOCKED_ERROR_CODE,
            "output_name": output_path.name,
            "mapping_gap_count": len(result.gaps),
            "duration_ms": duration_ms,
            "metrics_summary": metrics.format_summary(),
        },
    )
    return result


__all__ = [
    "Al16BuildResult",
    "FieldAudit",
    "MappingGap",
    "build_al16_rytm_kit",
    "deterministic_recipe_identifier",
]
