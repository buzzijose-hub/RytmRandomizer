"""Passive promotion report for verified Analog Four saved-offset mappings.

This module reads existing before/after SysEx data through the passive
controlled-diff analyzer. It does not import MIDI libraries, open ports, send
MIDI, receive live SysEx, write SysEx, execute commands, or mutate hardware.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .controlled_diff import (
    AnalogFourControlledDiffReport,
    build_analog_four_controlled_diff_report_from_bytes,
    build_analog_four_controlled_diff_report_from_file,
)
from .saved_offset_mapping_validation_guide import SUPPORTED_MAPPING_PARAMETERS
from .saved_offset_mappings import AnalogFourVerifiedSavedOffsetMapping


@dataclass(frozen=True)
class AnalogFourSavedOffsetMappingPromotion:
    """Result of checking a controlled diff for one mapping promotion."""

    before_path: str | None
    after_path: str | None
    parameter_key: str
    parameter_name: str
    cc: int
    limit: int
    ready: bool
    reason: str
    diff_report: AnalogFourControlledDiffReport
    mapping: AnalogFourVerifiedSavedOffsetMapping | None

    @property
    def slot(self) -> int:
        return self.diff_report.slot

    @property
    def track(self) -> int:
        return self.diff_report.track

    @property
    def changed_candidate_count(self) -> int:
        return self.diff_report.changed_candidate_count

    @property
    def relative_offset(self) -> int | None:
        if self.mapping is None:
            return None
        return self.mapping.relative_offset


def build_analog_four_saved_offset_mapping_promotion_from_file(
    before_path: str | Path,
    after_path: str | Path,
    *,
    slot: int,
    track: int,
    parameter: str,
    limit: int,
) -> AnalogFourSavedOffsetMappingPromotion:
    """Build a promotion report from existing before/after SysEx files."""

    parameter_key, parameter_name, cc = _resolve_parameter(parameter)
    diff_report = build_analog_four_controlled_diff_report_from_file(
        before_path,
        after_path,
        slot=slot,
        track=track,
        limit=limit,
    )
    promotion = _promotion_from_diff_report(
        diff_report,
        parameter_key=parameter_key,
        parameter_name=parameter_name,
        cc=cc,
        limit=limit,
    )
    return AnalogFourSavedOffsetMappingPromotion(
        before_path=str(before_path),
        after_path=str(after_path),
        parameter_key=promotion.parameter_key,
        parameter_name=promotion.parameter_name,
        cc=promotion.cc,
        limit=promotion.limit,
        ready=promotion.ready,
        reason=promotion.reason,
        diff_report=promotion.diff_report,
        mapping=promotion.mapping,
    )


def build_analog_four_saved_offset_mapping_promotion_from_bytes(
    before_data: bytes,
    after_data: bytes,
    *,
    slot: int,
    track: int,
    parameter: str,
    limit: int,
) -> AnalogFourSavedOffsetMappingPromotion:
    """Build a promotion report from raw before/after SysEx bytes."""

    parameter_key, parameter_name, cc = _resolve_parameter(parameter)
    diff_report = build_analog_four_controlled_diff_report_from_bytes(
        before_data,
        after_data,
        slot=slot,
        track=track,
        limit=limit,
    )
    return _promotion_from_diff_report(
        diff_report,
        parameter_key=parameter_key,
        parameter_name=parameter_name,
        cc=cc,
        limit=limit,
    )


def format_analog_four_saved_offset_mapping_promotion_report(
    promotion: AnalogFourSavedOffsetMappingPromotion,
) -> list[str]:
    """Format a deterministic passive A4 saved-offset mapping promotion report."""

    lines = [
        "RytmRandomizer passive Analog Four Saved-Offset Mapping Promotion Report",
        f"Before path: {promotion.before_path or '<bytes>'}",
        f"After path: {promotion.after_path or '<bytes>'}",
        f"Slot: {promotion.slot}",
        f"Track: {promotion.track}",
        f"Parameter: {promotion.parameter_name}",
        f"Parameter key: {promotion.parameter_key}",
        f"Known runtime CC: CC{promotion.cc}",
        f"Ready: {promotion.ready}",
        f"Reason: {promotion.reason}",
        f"Changed candidates: {promotion.changed_candidate_count}",
        "Changed offset candidates:",
    ]
    if promotion.diff_report.changes:
        lines.extend(_format_change_line(change) for change in promotion.diff_report.changes)
    else:
        lines.append("- none found")

    lines.append("Mapping entry:")
    if promotion.mapping is None:
        lines.append("- not ready; repeat a cleaner controlled diff before adding a mapping")
    else:
        lines.extend(_format_mapping_entry(promotion.mapping))

    lines.append("JSON manifest entry:")
    if promotion.mapping is None:
        lines.append("- not ready; no JSON entry emitted")
    else:
        lines.extend(_format_json_manifest_entry(promotion.mapping))

    lines.append("JSON manifest file example:")
    if promotion.mapping is None:
        lines.append("- not ready; no JSON manifest emitted")
    else:
        lines.extend(_format_json_manifest_example(promotion.mapping))

    lines.extend(
        [
            "Promotion policy:",
            "- one selected parameter only",
            "- one selected track only",
            "- single changed offset required before promotion",
            "- operator review still required before committing the mapping",
            "Safety:",
            "- passive/read-only",
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


def format_analog_four_saved_offset_mapping_promotion_error(message: str) -> list[str]:
    """Format deterministic promotion-report errors."""

    return [
        "RytmRandomizer passive Analog Four Saved-Offset Mapping Promotion Report",
        "Found: False",
        f"Message: {message}. No MIDI was sent. No command executed.",
        "Safety:",
        "- passive/read-only",
        "- no MIDI sending",
        "- no MIDI receive",
        "- no port opening",
        "- no command execution",
        "- no hardware mutation",
        "- no live SysEx receive",
        "- no SysEx writes",
        "- no hardware required",
    ]


def _promotion_from_diff_report(
    diff_report: AnalogFourControlledDiffReport,
    *,
    parameter_key: str,
    parameter_name: str,
    cc: int,
    limit: int,
) -> AnalogFourSavedOffsetMappingPromotion:
    ready = diff_report.changed_candidate_count == 1 and len(diff_report.changes) == 1
    reason = _reason_for_diff(diff_report)
    mapping = None
    if ready:
        change = diff_report.changes[0]
        mapping = AnalogFourVerifiedSavedOffsetMapping(
            track=diff_report.track,
            relative_offset=change.relative_offset,
            parameter_name=parameter_name,
            cc=cc,
        )
    return AnalogFourSavedOffsetMappingPromotion(
        before_path=diff_report.before_path,
        after_path=diff_report.after_path,
        parameter_key=parameter_key,
        parameter_name=parameter_name,
        cc=cc,
        limit=limit,
        ready=ready,
        reason=reason,
        diff_report=diff_report,
        mapping=mapping,
    )


def _reason_for_diff(diff_report: AnalogFourControlledDiffReport) -> str:
    if diff_report.changed_candidate_count == 0:
        return "blocked_no_changed_offsets"
    if diff_report.changed_candidate_count == 1 and len(diff_report.changes) == 1:
        return "single_changed_offset_ready_for_review"
    if diff_report.changed_candidate_count == 1:
        return "blocked_changed_offset_not_reported"
    return "blocked_multiple_changed_offsets"


def _resolve_parameter(parameter: str) -> tuple[str, str, int]:
    key = str(parameter).strip().lower().replace("_", "-")
    if key not in SUPPORTED_MAPPING_PARAMETERS:
        supported = ", ".join(sorted(SUPPORTED_MAPPING_PARAMETERS))
        raise ValueError(f"parameter must be one of: {supported}")
    parameter_name, cc = SUPPORTED_MAPPING_PARAMETERS[key]
    return key, parameter_name, cc


def _format_change_line(change) -> str:
    return (
        f"- Offset +{change.relative_offset} / word {change.word_index}: "
        f"{change.before_value} -> {change.after_value} "
        f"(delta {change.delta:+d}), {change.mapping_status}"
    )


def _format_mapping_entry(mapping: AnalogFourVerifiedSavedOffsetMapping) -> list[str]:
    return [
        "AnalogFourVerifiedSavedOffsetMapping(",
        f"    track={mapping.track},",
        f"    relative_offset={mapping.relative_offset},",
        f'    parameter_name="{mapping.parameter_name}",',
        f"    cc={mapping.cc},",
        ")",
    ]


def _format_json_manifest_entry(mapping: AnalogFourVerifiedSavedOffsetMapping) -> list[str]:
    return json.dumps(_json_manifest_entry(mapping), indent=2).splitlines()


def _format_json_manifest_example(mapping: AnalogFourVerifiedSavedOffsetMapping) -> list[str]:
    payload = {"mappings": [_json_manifest_entry(mapping)]}
    return json.dumps(payload, indent=2).splitlines()


def _json_manifest_entry(mapping: AnalogFourVerifiedSavedOffsetMapping) -> dict[str, int | str]:
    return {
        "track": mapping.track,
        "relative_offset": mapping.relative_offset,
        "parameter_name": mapping.parameter_name,
        "cc": mapping.cc,
        "mapping_status": mapping.mapping_status,
    }


__all__ = [
    "AnalogFourSavedOffsetMappingPromotion",
    "build_analog_four_saved_offset_mapping_promotion_from_bytes",
    "build_analog_four_saved_offset_mapping_promotion_from_file",
    "format_analog_four_saved_offset_mapping_promotion_error",
    "format_analog_four_saved_offset_mapping_promotion_report",
]
