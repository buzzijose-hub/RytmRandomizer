"""Passive anchor/profile behavior report.

Extracted verbatim from the former monolithic ``rytm_randomizer.reports``
module when it reached the 1500-LOC comprehensibility cap (see
``tests/architecture/test_reports_max_module_size.py``). Behavior is
unchanged; the public names are re-exported from ``rytm_randomizer.reports``
so every existing import keeps working.
"""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Final, TypedDict

from ..formatter import safety_section_lines


class AnchorProfileEntryDict(TypedDict):
    """One supported anchor/profile behavior entry."""

    command_key: str
    label: str
    concept: str
    intent_kind: str
    behavior_family: str
    target_pad: int | None
    target_scope: str
    source_helper: str
    reason: str
    read_only: bool
    active_behavior: str
    sends_real_midi: bool
    opens_ports: bool
    hardware_required: bool


class AnchorProfileSupportedSectionDict(TypedDict):
    """One supported section, grouping its entries."""

    section_key: str
    section_name: str
    source_helper: str
    entries: tuple[AnchorProfileEntryDict, ...]


class AnchorProfileParkedSectionDict(TypedDict):
    """One parked section awaiting separate approval."""

    key: str
    kind: str
    status: str
    reason: str
    source_helper: str
    requires_separate_approval: bool


class AnchorProfileSafetyDict(TypedDict):
    """Safety block for the anchor/profile report."""

    read_only: bool
    runtime_state: str
    active_behavior: str
    active_cli_wiring: str
    passive_cli_visibility: str
    real_midi: str
    port_opening: str
    midi_sending: str
    hardware_required: bool
    package_metadata_changes: str


class AnchorProfileSourceDict(TypedDict):
    """Provenance block for the anchor/profile report."""

    report_module: str
    in_memory_only: bool
    calls_cli: bool
    creates_runtime_state: bool


class AnchorProfileReportDict(TypedDict):
    """Fixed shape of :func:`build_anchor_profile_report`."""

    title: str
    supported_sections: tuple[AnchorProfileSupportedSectionDict, ...]
    parked_sections: tuple[AnchorProfileParkedSectionDict, ...]
    safety: AnchorProfileSafetyDict
    closeout_coverage: tuple[str, ...]
    recommended_next_branch: str
    source: AnchorProfileSourceDict


class AnchorProfileSummaryDict(TypedDict):
    """Fixed shape of :func:`summarize_anchor_profile_report`."""

    title: str
    supported_section_count: int
    supported_entry_count: int
    parked_count: int
    parked_keys: tuple[str, ...]
    read_only: bool
    active_behavior: str
    hardware_required: bool


class AnchorProfileSectionSpecDict(TypedDict):
    """Declarative spec for one supported section."""

    section_key: str
    section_name: str
    source_helper: str
    command_keys: tuple[str, ...]


ANCHOR_PROFILE_REPORT_TITLE: Final[str] = "RytmRandomizer Anchor/Profile Behavior Report"

ANCHOR_PROFILE_SAFETY: Final[dict[str, object]] = {
    "read_only": True,
    "passive_cli_visibility": "present",
    "real_midi": "absent",
    "port_opening": "absent",
    "midi_sending": "absent",
    "active_behavior": "absent",
    "active_cli_wiring": "absent",
    "hardware_required": False,
    "runtime_state": "absent",
    "package_metadata_changes": "absent",
}

ANCHOR_PROFILE_CLOSEOUT_COVERAGE: Final[tuple[str, ...]] = (
    "Behavior Anchor Profile",
    "Behavior Pad 1 Lane",
    "Behavior Pad 2 Lane",
    "Behavior Pad 3 Lane",
    "Behavior Pad 4 Lane",
    "Behavior Scene Group",
    "Behavior Undo Commit State",
    "Behavior Selected Profile",
    "Behavior Selected Isolated Pad",
)

ANCHOR_PROFILE_PARKED_SECTIONS: Final[tuple[dict[str, object], ...]] = (
    {
        "key": "PZ",
        "kind": "selected_isolated_pad_anchor_return",
        "status": "parked",
        "reason": "deferred_selected_isolated_pad_anchor_return",
        "source_helper": "rytm_randomizer.behavior.selected_isolated_pad",
        "requires_separate_approval": True,
    },
    {
        "key": "4",
        "kind": "group_profile_mock_mapper_support",
        "status": "parked",
        "reason": "profile 4 mock mapper support remains parked until separately approved",
        "source_helper": "rytm_randomizer.mock_message_mapper",
        "requires_separate_approval": True,
    },
)


def _anchor_profile_section_specs() -> tuple[AnchorProfileSectionSpecDict, ...]:
    from ...behavior.anchor_profile import evaluate_anchor_profile_behavior
    from ...behavior.pad_lane import (
        evaluate_pad1_lane_behavior,
        evaluate_pad2_lane_behavior,
        evaluate_pad3_lane_behavior,
        evaluate_pad4_lane_behavior,
    )
    from ...behavior.scene_group import evaluate_scene_group_behavior
    from ...behavior.selected_isolated_pad import evaluate_selected_isolated_pad_behavior
    from ...behavior.selected_profile import evaluate_selected_profile_behavior
    from ...behavior.undo_commit_state import evaluate_undo_commit_state_behavior

    return (
        (
            "direct_packet_2_anchor_profile",
            "Direct Packet 2 Anchor/Profile",
            "rytm_randomizer.behavior.anchor_profile",
            evaluate_anchor_profile_behavior,
            ("BH", "BC", "BS", "BF"),
            {"intent_kind": "anchor/profile"},
        ),
        (
            "pad1_lane_anchor_profile",
            "Pad 1 Lane Anchor/Profile",
            "rytm_randomizer.behavior.pad_lane",
            evaluate_pad1_lane_behavior,
            ("FZ", "BP", "PBH", "BI", "SBH", "BA"),
            {},
        ),
        (
            "pad2_lane_anchor_profile",
            "Pad 2 Lane Anchor/Profile",
            "rytm_randomizer.behavior.pad_lane",
            evaluate_pad2_lane_behavior,
            ("P2B", "P2H", "P2C", "P2F", "P2Z"),
            {
                "concept_overrides": {
                    "P2Z": "Pad 2 current profile anchor",
                },
                "intent_kind_overrides": {
                    "P2Z": "anchor_return",
                },
            },
        ),
        (
            "pad3_anchor",
            "Pad 3 Anchor",
            "rytm_randomizer.behavior.pad_lane",
            evaluate_pad3_lane_behavior,
            ("P3A", "SA"),
            {},
        ),
        (
            "pad4_anchor",
            "Pad 4 Anchor",
            "rytm_randomizer.behavior.pad_lane",
            evaluate_pad4_lane_behavior,
            ("P4A",),
            {},
        ),
        (
            "group_anchor",
            "Group Anchor",
            "rytm_randomizer.behavior.scene_group",
            evaluate_scene_group_behavior,
            ("O", "Z"),
            {
                "intent_kind_overrides": {
                    "O": "anchor_load",
                    "Z": "anchor_return",
                },
            },
        ),
        (
            "current_anchor_state",
            "Current Anchor State",
            "rytm_randomizer.behavior.undo_commit_state",
            evaluate_undo_commit_state_behavior,
            ("B", "E"),
            {},
        ),
        (
            "selected_profile_workflow",
            "Selected Profile Workflow",
            "rytm_randomizer.behavior.selected_profile",
            evaluate_selected_profile_behavior,
            ("P", "M"),
            {
                "concept_overrides": {
                    "M": "current_selected_profile_state",
                },
            },
        ),
        (
            "selected_isolated_pad_target",
            "Selected Isolated Pad Target",
            "rytm_randomizer.behavior.selected_isolated_pad",
            evaluate_selected_isolated_pad_behavior,
            ("L",),
            {},
        ),
    )


def _anchor_profile_label(result: object, metadata: Mapping[str, object]) -> str:
    return (
        getattr(result, "label", "")
        or metadata.get("source_group_command_label", "")
        or metadata.get("source_scene_name", "")
    )


def _anchor_profile_target_scope(result: object, metadata: Mapping[str, object]) -> str:
    return (
        getattr(result, "target_scope", "")
        or getattr(result, "source_scope", "")
        or metadata.get("source_group_command_scope", "")
        or metadata.get("source_scope", "")
    )


def _anchor_profile_intent_kind(
    command_key: str, result: object, metadata: Mapping[str, object], options: Mapping[str, object]
) -> str:
    overrides = options.get("intent_kind_overrides", {})
    if command_key in overrides:
        return overrides[command_key]
    if "intent_kind" in options:
        return options["intent_kind"]
    return (
        getattr(result, "intent_kind", "")
        or metadata.get("intent_kind", "")
        or metadata.get("source_group_command_type", "")
        or metadata.get("command_type", "")
    )


def _anchor_profile_concept(
    command_key: str, result: object, metadata: Mapping[str, object], options: Mapping[str, object]
) -> str:
    overrides = options.get("concept_overrides", {})
    if command_key in overrides:
        return overrides[command_key]
    return (
        metadata.get("target", "")
        or getattr(result, "anchor_concept", "")
        or metadata.get("anchor_concept", "")
        or metadata.get("anchor_return_concept", "")
        or getattr(result, "lane_action", "")
        or metadata.get("anchor_action", "")
        or getattr(result, "workflow_action", "")
        or getattr(result, "utility_action", "")
    )


def _anchor_profile_supported_entry(
    command_key: str,
    result: object,
    source_helper: str,
    options: Mapping[str, object],
) -> AnchorProfileEntryDict:
    metadata = dict(getattr(result, "metadata", {}))
    return {
        "command_key": command_key,
        "label": _anchor_profile_label(result, metadata),
        "behavior_family": getattr(result, "behavior_family", ""),
        "reason": getattr(result, "reason", ""),
        "source_helper": source_helper,
        "target_pad": getattr(result, "target_pad", None),
        "target_scope": _anchor_profile_target_scope(result, metadata),
        "intent_kind": _anchor_profile_intent_kind(command_key, result, metadata, options),
        "concept": _anchor_profile_concept(command_key, result, metadata, options),
        "read_only": True,
        "sends_real_midi": False,
        "opens_ports": False,
        "hardware_required": False,
        "active_behavior": False,
    }


def _anchor_profile_supported_section(
    spec: AnchorProfileSectionSpecDict,
) -> AnchorProfileSupportedSectionDict:
    (
        section_key,
        section_name,
        source_helper,
        evaluator,
        command_keys,
        options,
    ) = spec
    return {
        "section_key": section_key,
        "section_name": section_name,
        "source_helper": source_helper,
        "entries": tuple(
            _anchor_profile_supported_entry(
                command_key,
                evaluator(command_key),
                source_helper,
                options,
            )
            for command_key in command_keys
        ),
    }


def build_anchor_profile_report() -> AnchorProfileReportDict:
    """Return copied, in-memory data about current anchor/profile behavior coverage."""
    report: AnchorProfileReportDict = {
        "title": ANCHOR_PROFILE_REPORT_TITLE,
        "supported_sections": tuple(
            _anchor_profile_supported_section(spec) for spec in _anchor_profile_section_specs()
        ),
        "parked_sections": deepcopy(ANCHOR_PROFILE_PARKED_SECTIONS),
        "safety": deepcopy(ANCHOR_PROFILE_SAFETY),
        "closeout_coverage": tuple(ANCHOR_PROFILE_CLOSEOUT_COVERAGE),
        "recommended_next_branch": "documentation checkpoint after passive CLI visibility",
        "source": {
            "report_module": "rytm_randomizer.reports",
            "in_memory_only": True,
            "calls_cli": False,
            "creates_runtime_state": False,
        },
    }
    return deepcopy(report)


def summarize_anchor_profile_report(
    report: AnchorProfileReportDict | None = None,
) -> AnchorProfileSummaryDict:
    """Return a compact copied summary of the anchor/profile behavior report."""
    source_report = build_anchor_profile_report() if report is None else report
    supported_sections = source_report["supported_sections"]
    return {
        "title": source_report["title"],
        "supported_section_count": len(supported_sections),
        "supported_entry_count": sum(len(section["entries"]) for section in supported_sections),
        "parked_count": len(source_report["parked_sections"]),
        "parked_keys": tuple(item["key"] for item in source_report["parked_sections"]),
        "read_only": source_report["safety"]["read_only"],
        "active_behavior": source_report["safety"]["active_behavior"],
        "hardware_required": source_report["safety"]["hardware_required"],
    }


def format_anchor_profile_report(
    report: AnchorProfileReportDict | None = None,
) -> list[str]:
    """Return deterministic human-readable anchor/profile report lines."""
    source_report = build_anchor_profile_report() if report is None else report
    lines = [
        source_report["title"],
        "Supported Anchor/Profile Sections:",
    ]

    for section in source_report["supported_sections"]:
        command_keys = ", ".join(entry["command_key"] for entry in section["entries"])
        lines.append(f"- {section['section_key']}: {command_keys}")

    lines.append("Parked/Safe Scope:")
    for parked in source_report["parked_sections"]:
        lines.append(f"- {parked['key']}: {parked['kind']} - {parked['reason']}")

    lines.extend(safety_section_lines(source_report["safety"]))

    lines.append(f"Recommended Next Branch: {source_report['recommended_next_branch']}")
    return lines
