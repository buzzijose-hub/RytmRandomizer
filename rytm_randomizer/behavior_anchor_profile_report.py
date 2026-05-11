"""Read-only anchor/profile behavior report summary.

This module summarizes existing passive anchor/profile-related behavior without
calling CLI entry points, opening ports, sending MIDI, dispatching commands,
creating runtime state, or touching hardware.
"""

from __future__ import annotations

from copy import deepcopy

from .behavior_anchor_profile import evaluate_anchor_profile_behavior
from .behavior_pad1_lane import evaluate_pad1_lane_behavior
from .behavior_pad2_lane import evaluate_pad2_lane_behavior
from .behavior_pad3_lane import evaluate_pad3_lane_behavior
from .behavior_pad4_lane import evaluate_pad4_lane_behavior
from .behavior_scene_group import evaluate_scene_group_behavior
from .behavior_selected_isolated_pad import evaluate_selected_isolated_pad_behavior
from .behavior_selected_profile import evaluate_selected_profile_behavior
from .behavior_undo_commit_state import evaluate_undo_commit_state_behavior


REPORT_TITLE = "RytmRandomizer Anchor/Profile Behavior Report"

ANCHOR_PROFILE_SAFETY = {
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

CLOSEOUT_COVERAGE = (
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

SUPPORTED_SECTION_SPECS = (
    (
        "direct_packet_2_anchor_profile",
        "Direct Packet 2 Anchor/Profile",
        "rytm_randomizer.behavior_anchor_profile",
        evaluate_anchor_profile_behavior,
        ("BH", "BC", "BS", "BF"),
        {"intent_kind": "anchor/profile"},
    ),
    (
        "pad1_lane_anchor_profile",
        "Pad 1 Lane Anchor/Profile",
        "rytm_randomizer.behavior_pad1_lane",
        evaluate_pad1_lane_behavior,
        ("FZ", "BP", "PBH", "BI", "SBH", "BA"),
        {},
    ),
    (
        "pad2_lane_anchor_profile",
        "Pad 2 Lane Anchor/Profile",
        "rytm_randomizer.behavior_pad2_lane",
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
        "rytm_randomizer.behavior_pad3_lane",
        evaluate_pad3_lane_behavior,
        ("P3A", "SA"),
        {},
    ),
    (
        "pad4_anchor",
        "Pad 4 Anchor",
        "rytm_randomizer.behavior_pad4_lane",
        evaluate_pad4_lane_behavior,
        ("P4A",),
        {},
    ),
    (
        "group_anchor",
        "Group Anchor",
        "rytm_randomizer.behavior_scene_group",
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
        "rytm_randomizer.behavior_undo_commit_state",
        evaluate_undo_commit_state_behavior,
        ("B", "E"),
        {},
    ),
    (
        "selected_profile_workflow",
        "Selected Profile Workflow",
        "rytm_randomizer.behavior_selected_profile",
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
        "rytm_randomizer.behavior_selected_isolated_pad",
        evaluate_selected_isolated_pad_behavior,
        ("L",),
        {},
    ),
)

PARKED_SECTIONS = (
    {
        "key": "PZ",
        "kind": "selected_isolated_pad_anchor_return",
        "status": "parked",
        "reason": "deferred_selected_isolated_pad_anchor_return",
        "source_helper": "rytm_randomizer.behavior_selected_isolated_pad",
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


def build_anchor_profile_report():
    """Return copied, in-memory data about current anchor/profile behavior coverage."""

    report = {
        "title": REPORT_TITLE,
        "supported_sections": tuple(_supported_section(spec) for spec in SUPPORTED_SECTION_SPECS),
        "parked_sections": deepcopy(PARKED_SECTIONS),
        "safety": deepcopy(ANCHOR_PROFILE_SAFETY),
        "closeout_coverage": tuple(CLOSEOUT_COVERAGE),
        "recommended_next_branch": "documentation checkpoint after passive CLI visibility",
        "source": {
            "report_module": "rytm_randomizer.behavior_anchor_profile_report",
            "in_memory_only": True,
            "calls_cli": False,
            "creates_runtime_state": False,
        },
    }
    return deepcopy(report)


def summarize_anchor_profile_report(report=None):
    """Return a compact copied summary of the anchor/profile behavior report."""

    source_report = build_anchor_profile_report() if report is None else report
    supported_sections = source_report["supported_sections"]
    return {
        "title": source_report["title"],
        "supported_section_count": len(supported_sections),
        "supported_entry_count": sum(
            len(section["entries"]) for section in supported_sections
        ),
        "parked_count": len(source_report["parked_sections"]),
        "parked_keys": tuple(item["key"] for item in source_report["parked_sections"]),
        "read_only": source_report["safety"]["read_only"],
        "active_behavior": source_report["safety"]["active_behavior"],
        "hardware_required": source_report["safety"]["hardware_required"],
    }


def format_anchor_profile_report(report=None):
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

    lines.append("Safety:")
    for key, value in source_report["safety"].items():
        lines.append(f"- {key}: {value}")

    lines.append(
        f"Recommended Next Branch: {source_report['recommended_next_branch']}"
    )
    return lines


def _supported_section(spec):
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
            _supported_entry(
                command_key,
                evaluator(command_key),
                source_helper,
                options,
            )
            for command_key in command_keys
        ),
    }


def _supported_entry(command_key, result, source_helper, options):
    metadata = dict(getattr(result, "metadata", {}))
    return {
        "command_key": command_key,
        "label": _label(result, metadata),
        "behavior_family": getattr(result, "behavior_family", ""),
        "reason": getattr(result, "reason", ""),
        "source_helper": source_helper,
        "target_pad": getattr(result, "target_pad", None),
        "target_scope": _target_scope(result, metadata),
        "intent_kind": _intent_kind(command_key, result, metadata, options),
        "concept": _concept(command_key, result, metadata, options),
        "read_only": True,
        "sends_real_midi": False,
        "opens_ports": False,
        "hardware_required": False,
        "active_behavior": False,
    }


def _label(result, metadata):
    return (
        getattr(result, "label", "")
        or metadata.get("source_group_command_label", "")
        or metadata.get("source_scene_name", "")
    )


def _target_scope(result, metadata):
    return (
        getattr(result, "target_scope", "")
        or getattr(result, "source_scope", "")
        or metadata.get("source_group_command_scope", "")
        or metadata.get("source_scope", "")
    )


def _intent_kind(command_key, result, metadata, options):
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


def _concept(command_key, result, metadata, options):
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


__all__ = [
    "ANCHOR_PROFILE_SAFETY",
    "CLOSEOUT_COVERAGE",
    "PARKED_SECTIONS",
    "REPORT_TITLE",
    "SUPPORTED_SECTION_SPECS",
    "build_anchor_profile_report",
    "format_anchor_profile_report",
    "summarize_anchor_profile_report",
]
