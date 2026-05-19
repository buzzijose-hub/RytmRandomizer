"""Passive Analog Four verified saved-offset mapping manifest report.

This module reads local JSON manifest files only. It imports no MIDI libraries,
opens no ports, sends no MIDI, receives no SysEx, writes no SysEx, executes no
commands, and mutates no hardware.
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from .saved_offset_mappings import (
    VERIFIED_MAPPING_STATUS,
    AnalogFourVerifiedSavedOffsetMapping,
)

AnalogFourSavedOffsetMappingManifestError = ValueError


@dataclass(frozen=True)
class AnalogFourSavedOffsetMappingDuplicate:
    """One duplicate track/offset pair in a verified mapping manifest."""

    track: int
    relative_offset: int
    count: int


@dataclass(frozen=True)
class AnalogFourSavedOffsetMappingManifest:
    """Parsed and validated verified mapping manifest."""

    path: str
    mappings: tuple[AnalogFourVerifiedSavedOffsetMapping, ...]
    duplicates: tuple[AnalogFourSavedOffsetMappingDuplicate, ...]

    @property
    def ready(self) -> bool:
        return bool(self.mappings) and not self.duplicates

    @property
    def reason(self) -> str:
        if self.duplicates:
            return "blocked_duplicate_track_offsets"
        if not self.mappings:
            return "blocked_empty_manifest"
        return "verified_manifest_ready"


def load_analog_four_saved_offset_mapping_manifest(
    path: str | Path,
) -> AnalogFourSavedOffsetMappingManifest:
    """Load and validate a passive verified mapping manifest from JSON."""

    manifest_path = Path(path)
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("manifest must be a JSON object")
    raw_mappings = payload.get("mappings")
    if not isinstance(raw_mappings, list):
        raise ValueError("manifest mappings must be a list")

    mappings = tuple(
        _mapping_from_entry(entry, index) for index, entry in enumerate(raw_mappings, 1)
    )
    return AnalogFourSavedOffsetMappingManifest(
        path=str(manifest_path),
        mappings=mappings,
        duplicates=_find_duplicates(mappings),
    )


def format_analog_four_saved_offset_mapping_manifest_report(
    manifest: AnalogFourSavedOffsetMappingManifest,
) -> list[str]:
    """Format a deterministic passive verified mapping manifest report."""

    lines = [
        "RytmRandomizer passive Analog Four Saved-Offset Mapping Manifest Report",
        f"Path: {manifest.path}",
        "Found: True",
        f"Ready: {manifest.ready}",
        f"Reason: {manifest.reason}",
        f"Mapping count: {len(manifest.mappings)}",
        f"Duplicate count: {len(manifest.duplicates)}",
        "Mappings:",
    ]
    if manifest.mappings:
        lines.extend(_format_mapping(mapping) for mapping in manifest.mappings)
    else:
        lines.append("- none")

    lines.append("Duplicate track/offset pairs:")
    if manifest.duplicates:
        lines.extend(_format_duplicate(duplicate) for duplicate in manifest.duplicates)
    else:
        lines.append("- none")

    lines.extend(
        [
            "Manifest policy:",
            "- one mapping per Analog Four track/relative-offset pair",
            "- mappings must come from controlled before/after proof sessions",
            "- duplicate track/offset pairs stay blocked until resolved",
            "- this manifest is passive input only; runtime integration is a later gate",
            "Safety:",
            "- passive/read-only",
            "- local JSON read only",
            "- no MIDI sending",
            "- no MIDI receive",
            "- no port opening",
            "- no command execution",
            "- no hardware mutation",
            "- no live SysEx receive",
            "- no SysEx writes",
            "- no hardware required",
        ]
    )
    return lines


def format_analog_four_saved_offset_mapping_manifest_error(message: str) -> list[str]:
    """Format deterministic manifest-report errors."""

    return [
        "RytmRandomizer passive Analog Four Saved-Offset Mapping Manifest Report",
        "Found: False",
        f"Message: {message}. No MIDI was sent. No command executed.",
        "Safety:",
        "- passive/read-only",
        "- local JSON read only",
        "- no MIDI sending",
        "- no MIDI receive",
        "- no port opening",
        "- no command execution",
        "- no hardware mutation",
        "- no live SysEx receive",
        "- no SysEx writes",
        "- no hardware required",
    ]


def _mapping_from_entry(entry, index: int) -> AnalogFourVerifiedSavedOffsetMapping:
    if not isinstance(entry, dict):
        raise ValueError(f"entry {index} must be an object")
    try:
        return AnalogFourVerifiedSavedOffsetMapping(
            track=entry["track"],
            relative_offset=entry["relative_offset"],
            parameter_name=entry["parameter_name"],
            cc=entry["cc"],
            mapping_status=entry.get("mapping_status", VERIFIED_MAPPING_STATUS),
        )
    except KeyError as exc:
        raise ValueError(f"entry {index} is missing {exc.args[0]}") from exc
    except (TypeError, ValueError) as exc:
        raise ValueError(f"entry {index}: {exc}") from exc


def _find_duplicates(
    mappings: tuple[AnalogFourVerifiedSavedOffsetMapping, ...],
) -> tuple[AnalogFourSavedOffsetMappingDuplicate, ...]:
    counts = Counter((mapping.track, mapping.relative_offset) for mapping in mappings)
    duplicates = [
        AnalogFourSavedOffsetMappingDuplicate(
            track=track,
            relative_offset=relative_offset,
            count=count,
        )
        for (track, relative_offset), count in counts.items()
        if count > 1
    ]
    return tuple(
        sorted(duplicates, key=lambda duplicate: (duplicate.track, duplicate.relative_offset))
    )


def _format_mapping(mapping: AnalogFourVerifiedSavedOffsetMapping) -> str:
    return (
        f"- Track {mapping.track} / offset +{mapping.relative_offset} / "
        f"{mapping.parameter_name} / CC{mapping.cc} / {mapping.mapping_status}"
    )


def _format_duplicate(duplicate: AnalogFourSavedOffsetMappingDuplicate) -> str:
    return (
        f"- Track {duplicate.track} / offset +{duplicate.relative_offset} "
        f"appears {duplicate.count} times"
    )


__all__ = [
    "AnalogFourSavedOffsetMappingManifest",
    "AnalogFourSavedOffsetMappingManifestError",
    "format_analog_four_saved_offset_mapping_manifest_error",
    "format_analog_four_saved_offset_mapping_manifest_report",
    "load_analog_four_saved_offset_mapping_manifest",
]
