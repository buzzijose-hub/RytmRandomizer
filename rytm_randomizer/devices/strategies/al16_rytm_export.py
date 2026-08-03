"""Passive AL16 Analog Rytm saved-kit compiler and evidence reporter."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Final, cast

from ...data.al16_rytm import (
    AL16_PAD_ROLES,
    AL16_PRESERVED_GLOBAL_SECTIONS,
    AL16_RYTM_APPROVED_TUNING,
    AL16_RYTM_FILTER_TYPES,
    AL16_RYTM_WRITABLE_FIELDS,
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
from ...observability.logging import configure_logging, get_logger
from .analog_rytm_saved_kit_codec import (
    decode_analog_rytm_saved_kit_frame,
    encode_analog_rytm_saved_kit_frame,
)

_LOGGER = get_logger(__name__)
_REFERENCE_EXPECTED_SHA256: Final[str] = (
    "8bda94d6d5031e038c8d810789301f35242ed539338a0399548869a34e1dc4dd"
)
_SOURCE_DATE_EPOCH: Final[str] = "SOURCE_DATE_EPOCH"


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


def _load_recipe(path: Path) -> Mapping[str, object]:
    # JSON is a strict YAML subset, keeping the public recipe dependency-free.
    parsed = cast(object, json.loads(path.read_text(encoding="utf-8")))
    return _as_mapping(parsed, "recipe")


def deterministic_recipe_identifier(recipe: Mapping[str, object]) -> str:
    canonical = json.dumps(recipe, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical.encode("ascii")).hexdigest()


def _build_timestamp() -> str:
    epoch = os.environ.get(_SOURCE_DATE_EPOCH)
    if epoch is not None:
        return datetime.fromtimestamp(int(epoch), tz=UTC).isoformat()
    return datetime.now(tz=UTC).replace(microsecond=0).isoformat()


def _portable_reference_path(reference: Path) -> str:
    return f"reference/{reference.name}"


def _track_offset(pad: int, sound_offset: int) -> int:
    return RYTM_KIT_TRACKS_OFFSET + ((pad - 1) * RYTM_KIT_TRACK_SOUND_SIZE) + sound_offset


def _machine_label_for_raw(raw_value: int) -> str:
    machine_value = raw_value & 0x7F
    for profile in RYTM_MACHINE_PROFILES:
        if profile.machine_value == machine_value:
            return profile.label
    return f"unknown machine value {machine_value}"


def _convert_supported_value(
    converter: str,
    requested: object,
) -> tuple[object, int]:
    if converter == "verified_7bit":
        raw = _as_int(requested, "verified 7-bit value")
        if not 0 <= raw <= 127:
            raise ValueError("verified 7-bit value must be in 0..127")
        return raw, raw
    if converter == "centered_7bit":
        if requested in ("neutral", "center"):
            return 0, 64
        displayed = _as_int(requested, "centered display value")
        if not -64 <= displayed <= 63:
            raise ValueError("centered display value must be in -64..63")
        return displayed, displayed + 64
    if converter == "filter_type_enum":
        label = _as_string(requested, "filter type").upper()
        try:
            return label, AL16_RYTM_FILTER_TYPES[label]
        except KeyError as exc:
            raise ValueError(f"unsupported filter type: {label}") from exc
    raise ValueError(f"unknown AL16 converter: {converter}")


def _original_semantic(converter: str, raw_value: int) -> object:
    low7 = raw_value & 0x7F
    if converter == "centered_7bit":
        return low7 - 64
    if converter == "filter_type_enum":
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
    for field_name, requested in source.items():
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
    for field_name, requested in section.items():
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
    project_id = _as_string(recipe.get("project_id"), "project_id")
    if project_id != "AL16":
        raise ValueError("recipe project_id must be AL16")
    kit = _as_mapping(recipe.get("kit"), "kit")
    kit_name = _as_string(kit.get("name"), "kit.name")
    if len(kit_name.encode("ascii")) > RYTM_KIT_NAME_LENGTH:
        raise ValueError("kit.name must fit the 16-byte ASCII Rytm name field")

    original_name = (
        raw[RYTM_KIT_NAME_OFFSET : RYTM_KIT_NAME_OFFSET + RYTM_KIT_NAME_LENGTH]
        .split(b"\x00", 1)[0]
        .decode("ascii")
    )
    audits = [
        FieldAudit(
            semantic_path="kit.name",
            original_semantic_value=original_name,
            requested_semantic_value=kit_name,
            normalized_semantic_value=kit_name,
            encoded_raw_value_or_bytes=list(kit_name.encode("ascii").ljust(16, b"\x00")),
            raw_location=f"unpacked[{RYTM_KIT_NAME_OFFSET}:{RYTM_KIT_NAME_OFFSET + 16}]",
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
    if set(tracks) != {str(pad) for pad in range(1, 13)}:
        raise ValueError("recipe must describe exactly pads 1..12")
    preserved: list[int] = []
    for pad in range(1, 13):
        track = _as_mapping(tracks[str(pad)], f"tracks.{pad}")
        role = _as_string(track.get("role"), f"tracks.{pad}.role")
        if role != AL16_PAD_ROLES[pad]:
            raise ValueError(f"tracks.{pad}.role does not match the permanent AL16 pad role")
        mode = _as_string(track.get("mode"), f"tracks.{pad}.mode")
        if mode == "preserve":
            preserved.append(pad)
            continue
        if mode != "patch":
            raise ValueError(f"tracks.{pad}.mode must be patch or preserve")

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
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    gap_lines = [
        f"- `{gap.semantic_path}`: {gap.reason} Evidence required: {gap.evidence_required}"
        for gap in gaps
    ]
    validation_path.write_text(
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
        encoding="utf-8",
    )
    byte_diff_path.write_text(
        "AL16 AL02 LOCK byte-diff report\n"
        "status: blocked before mutation\n"
        "intentionally changed raw bytes: 0\n"
        "unknown or reserved bytes changed: 0\n"
        "output SysEx emitted: no\n"
        "reason: critical saved-kit mappings are not positively verified\n",
        encoding="utf-8",
    )


def build_al16_rytm_kit(
    *,
    reference_path: Path,
    recipe_path: Path,
    destination_slot: int,
    output_path: Path,
) -> Al16BuildResult:
    """Compile one AL16 Rytm recipe or emit an exact fail-closed gap report."""

    reference_bytes = reference_path.read_bytes()
    reference_sha256 = hashlib.sha256(reference_bytes).hexdigest()
    decoded = decode_analog_rytm_saved_kit_frame(reference_bytes)
    if encode_analog_rytm_saved_kit_frame(decoded.header, decoded.unpacked) != reference_bytes:
        raise ValueError("Analog Rytm reference decode/encode is not byte-identical")

    recipe = _load_recipe(recipe_path)
    audits, gaps, preserved_tracks = _inspect_recipe(
        recipe,
        decoded.unpacked,
        destination_slot,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path = output_path.with_name(f"{output_path.stem}_manifest.json")
    validation_path = output_path.with_name(f"{output_path.stem}_validation.md")
    byte_diff_path = output_path.with_name(f"{output_path.stem}_byte_diff.txt")
    if output_path.exists():
        raise FileExistsError(
            f"refusing a blocked build while a potentially stale output exists: {output_path}"
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
    _write_blocked_artifacts(
        manifest_path=manifest_path,
        validation_path=validation_path,
        byte_diff_path=byte_diff_path,
        manifest=manifest,
        gaps=gaps,
    )
    return Al16BuildResult(
        status="blocked",
        output_path=output_path,
        manifest_path=manifest_path,
        validation_path=validation_path,
        byte_diff_path=byte_diff_path,
        reference_sha256=reference_sha256,
        output_sha256=None,
        gaps=tuple(gaps),
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Passive AL16 Analog Rytm kit exporter")
    subparsers = parser.add_subparsers(dest="command", required=True)
    build = subparsers.add_parser(
        "build-rytm-kit",
        help="compile one recipe offline or write a precise mapping-gap report",
    )
    build.add_argument("--reference", type=Path, required=True, help="initialized Rytm kit dump")
    build.add_argument("--recipe", type=Path, required=True, help="JSON-compatible YAML recipe")
    build.add_argument(
        "--destination-slot",
        type=int,
        required=True,
        help="explicit scratch kit slot in the range 0..127",
    )
    build.add_argument("--output", type=Path, required=True, help="requested output SysEx path")
    return parser


def run_al16_rytm_export_cli(argv: Sequence[str] | None = None) -> int:
    configure_logging(level="INFO")
    args = _parser().parse_args(argv)
    if args.command != "build-rytm-kit":
        raise ValueError(f"unsupported command: {args.command}")
    result = build_al16_rytm_kit(
        reference_path=cast(Path, args.reference),
        recipe_path=cast(Path, args.recipe),
        destination_slot=cast(int, args.destination_slot),
        output_path=cast(Path, args.output),
    )
    _LOGGER.info(
        "AL16 Rytm offline build completed",
        extra={
            "build_status": result.status,
            "critical_mapping_gaps": len(result.gaps),
            "manifest": str(result.manifest_path),
            "validation": str(result.validation_path),
            "sysex_output_emitted": False,
        },
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(run_al16_rytm_export_cli())


__all__ = [
    "Al16BuildResult",
    "FieldAudit",
    "MappingGap",
    "build_al16_rytm_kit",
    "deterministic_recipe_identifier",
    "run_al16_rytm_export_cli",
]
