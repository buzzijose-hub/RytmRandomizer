"""Consolidated passive, in-memory report layer for RytmRandomizer.

This module unifies the previously separate ``*_report.py`` modules behind a
single generic dispatcher. Every report is passive and in-memory only: building
or formatting a report opens no ports, sends no MIDI, dispatches no commands,
wires no active CLI behavior, and touches no hardware.

The per-report ``build_*`` / ``format_*`` / ``summarize_*`` functions are
preserved with their original names and re-exported from thin shim modules so
existing imports and CLI subcommands keep working unchanged.

Heavy or behavior-specific dependencies are imported lazily inside builders so
that importing this module (or the shim modules) stays side-effect free and
does not pull in MIDI libraries, bridge modules, or behavior evaluators.
"""

from __future__ import annotations

import sys
from collections.abc import Sequence
from copy import deepcopy
from typing import Any, Final

from ..cli_registry import CliCommand
from .formatter import passive_footer_lines, safety_section_lines
from .rytm_machine_matrix import (  # noqa: F401
    build_rytm_machine_matrix_report,
    format_rytm_machine_matrix_report,
)
from .rytm_snapshot_pad_compatibility import (  # noqa: F401
    build_rytm_snapshot_pad_compatibility_report,
    format_rytm_snapshot_pad_compatibility_report,
)
from .oxi_live_macro_catalog import (  # noqa: F401
    build_oxi_live_macro_catalog_payload,
    build_oxi_live_macro_catalog_report,
    format_oxi_live_macro_catalog_report,
)

# ---------------------------------------------------------------------------
# Registry report
# ---------------------------------------------------------------------------

SAFETY_BOUNDARIES = (
    "no MIDI sending",
    "no port opening",
    "no runtime dispatch",
    "no command execution",
    "no hardware mutation",
    "no SysEx writes",
    "no GUI",
    "no capture",
    "no Analog Four support",
    "no Pads 5-12 support",
)

UNSUPPORTED_SCOPE = (
    "MIDI sending",
    "MIDI port opening",
    "runtime dispatch",
    "command execution",
    "hardware state mutation",
    "SysEx writes",
    "GUI",
    "capture",
    "Analog Four",
    "Pads 5-12",
)

ACTIVE_BEHAVIOR_STATUS = {
    "executes_commands": False,
    "dispatches_commands": False,
    "sends_midi": False,
    "opens_ports": False,
    "mutates_hardware": False,
    "writes_sysex": False,
}


def build_registry_report():
    """Return a copied, in-memory report for passive registry inspection."""
    from ..registry import build_registry, list_registry_sections, summarize_registry

    registry_summary = summarize_registry()
    return {
        "title": "RytmRandomizer Passive Registry Report",
        "sections": tuple(list_registry_sections()),
        "section_counts": deepcopy(registry_summary["section_counts"]),
        "known_sections": ("commands", "scenes", "group_profiles"),
        "safety_boundaries": SAFETY_BOUNDARIES,
        "unsupported_scope": UNSUPPORTED_SCOPE,
        "active_behavior": deepcopy(ACTIVE_BEHAVIOR_STATUS),
        "source": {
            "registry_module": "rytm_randomizer.registry",
            "sections": tuple(build_registry().keys()),
            "in_memory_only": True,
        },
    }


def summarize_registry_report(report=None):
    """Return a compact copied summary for a registry report."""
    source_report = build_registry_report() if report is None else report
    return {
        "title": source_report["title"],
        "section_count": len(source_report["sections"]),
        "total_items": sum(source_report["section_counts"].values()),
        "sections": tuple(source_report["sections"]),
        "active_behavior": deepcopy(source_report["active_behavior"]),
    }


def format_registry_report(report=None):
    """Return a deterministic human-readable report as a list of strings."""
    source_report = build_registry_report() if report is None else report
    lines = [
        source_report["title"],
        "Sections:",
    ]

    for section in source_report["sections"]:
        count = source_report["section_counts"][section]
        lines.append(f"- {section}: {count}")

    lines.extend(
        [
            "Safety Boundaries:",
            *[f"- {boundary}" for boundary in source_report["safety_boundaries"]],
            "Unsupported Scope:",
            *[f"- {scope}" for scope in source_report["unsupported_scope"]],
            "Active Behavior:",
        ]
    )

    for key in sorted(source_report["active_behavior"]):
        lines.append(f"- {key}: {source_report['active_behavior'][key]}")

    lines.extend(passive_footer_lines("registry"))
    return lines


# ---------------------------------------------------------------------------
# Shared profile-summary helpers (active boundary + mock mapper reports)
# ---------------------------------------------------------------------------


def _target_concept(profile):
    source_name = profile["name"]
    target_name = source_name[3:] if source_name.startswith("My ") else source_name
    return f"Pad {profile['group_pad']} / {target_name}"


def _profile_summary(profile_key):
    from ..profile_lookup import describe_group_profile

    profile = describe_group_profile(profile_key)
    if not profile["exists"]:
        return {
            "profile_key": str(profile_key),
            "name": None,
            "group_pad": None,
            "machine_value": None,
            "target": None,
        }

    return {
        "profile_key": profile["profile_key"],
        "name": profile["name"],
        "group_pad": profile["group_pad"],
        "machine_value": profile["machine_value"],
        "target": _target_concept(profile),
    }


# ---------------------------------------------------------------------------
# Active boundary report
# ---------------------------------------------------------------------------

UNSUPPORTED_ACTIVE_BOUNDARY_PROFILE_KEYS = ("3", "4")
UNSUPPORTED_SOURCE_KINDS = ("scene", "command")
RESULT_METADATA_FIELDS = (
    "source_kind",
    "source_key",
    "target",
    "armed",
    "dry_run_confirmed",
    "operator_intent",
    "mock_only",
    "sends_real_midi",
)

REQUIRED_CONDITIONS = (
    "explicit arming",
    "dry-run confirmation",
    "supported source kind",
    "supported source key",
    "injected MockMidiSender",
)

SAFE_FAILURE_SUMMARY = (
    "missing arming emits no messages",
    "missing dry-run confirmation emits no messages",
    "unsupported source kind emits no messages",
    "unsupported or unknown key emits no messages",
    "invalid request or sender type fails before message emission",
)

ACTIVE_BOUNDARY_SAFETY = {
    "mock_only": True,
    "hardware_required": False,
    "real_midi": "absent",
    "port_opening": "absent",
    "active_cli_behavior": "absent",
    "dispatch": "absent",
    "command_execution": "absent",
    "scene_execution": "absent",
    "hardware_behavior": "absent",
}

ACTIVE_BOUNDARY_CLOSEOUT_COVERAGE = (
    "Mock-Only Active Candidate",
    "Active Boundary",
)


def _unsupported_profile_summary(profile_key):
    summary = _profile_summary(profile_key)
    if str(profile_key) == "3":
        summary["reason"] = "mock mapper/report scope only; not active-boundary supported"
    elif str(profile_key) == "4":
        summary["reason"] = "parked until separately approved"
    else:
        summary["reason"] = "unsupported by active boundary"
    return summary


def build_active_boundary_report():
    """Return copied, in-memory data about current active boundary support."""
    from ..active_boundary import (
        ACTIVE_BOUNDARY_NAME,
        SUPPORTED_CANDIDATE,
        SUPPORTED_SOURCE_KEY,
        SUPPORTED_SOURCE_KIND,
    )

    accepted_candidate = _profile_summary(SUPPORTED_SOURCE_KEY)
    accepted_candidate["source_kind"] = SUPPORTED_SOURCE_KIND

    report = {
        "title": "RytmRandomizer Active Boundary Report",
        "accepted_candidate": accepted_candidate,
        "unsupported_profiles": tuple(
            _unsupported_profile_summary(profile_key)
            for profile_key in UNSUPPORTED_ACTIVE_BOUNDARY_PROFILE_KEYS
        ),
        "unsupported_source_kinds": tuple(UNSUPPORTED_SOURCE_KINDS),
        "result_metadata": {
            "boundary": ACTIVE_BOUNDARY_NAME,
            "supported_candidate": SUPPORTED_CANDIDATE,
            "fields": tuple(RESULT_METADATA_FIELDS),
            "failure_reason": "included on failure paths",
        },
        "required_conditions": tuple(REQUIRED_CONDITIONS),
        "safe_failure_summary": tuple(SAFE_FAILURE_SUMMARY),
        "closeout_coverage": tuple(ACTIVE_BOUNDARY_CLOSEOUT_COVERAGE),
        "source": {
            "boundary_module": "rytm_randomizer.active_boundary",
            "report_module": "rytm_randomizer.reports",
            "in_memory_only": True,
            "evaluates_active_requests": False,
        },
        **ACTIVE_BOUNDARY_SAFETY,
    }
    return deepcopy(report)


def summarize_active_boundary_report(report=None):
    """Return a compact copied summary of the active boundary report."""
    source_report = build_active_boundary_report() if report is None else report
    return {
        "title": source_report["title"],
        "boundary": source_report["result_metadata"]["boundary"],
        "supported_candidate": source_report["result_metadata"]["supported_candidate"],
        "accepted_key": source_report["accepted_candidate"]["profile_key"],
        "unsupported_keys": tuple(
            profile["profile_key"] for profile in source_report["unsupported_profiles"]
        ),
        "required_condition_count": len(source_report["required_conditions"]),
        "mock_only": source_report["mock_only"],
        "active_cli_behavior": source_report["active_cli_behavior"],
        "hardware_required": source_report["hardware_required"],
    }


def format_active_boundary_report(report=None):
    """Return deterministic human-readable active boundary report lines."""
    source_report = build_active_boundary_report() if report is None else report
    candidate = source_report["accepted_candidate"]
    result_metadata = source_report["result_metadata"]
    lines = [
        source_report["title"],
        "Accepted Active Boundary Candidate:",
        (
            f"- {candidate['source_kind']} {candidate['profile_key']}: "
            f"{candidate['name']} ({candidate['target']})"
        ),
        "Unsupported Active Boundary Profiles:",
    ]

    for profile in source_report["unsupported_profiles"]:
        lines.append(
            f"- {profile['profile_key']}: {profile['name']} "
            f"({profile['target']}) - {profile['reason']}"
        )

    lines.extend(
        [
            "Result Metadata:",
            f"- boundary: {result_metadata['boundary']}",
            f"- supported_candidate: {result_metadata['supported_candidate']}",
            f"- fields: {', '.join(result_metadata['fields'])}",
            f"- failure_reason: {result_metadata['failure_reason']}",
        ]
    )

    lines.append("Required Conditions:")
    for condition in source_report["required_conditions"]:
        lines.append(f"- {condition}")

    lines.extend(
        [
            "Active Boundary Safety:",
            f"- mock_only: {source_report['mock_only']}",
            f"- hardware_required: {source_report['hardware_required']}",
            f"- real_midi: {source_report['real_midi']}",
            f"- port_opening: {source_report['port_opening']}",
            f"- active_cli_behavior: {source_report['active_cli_behavior']}",
            f"- dispatch: {source_report['dispatch']}",
            f"- command_execution: {source_report['command_execution']}",
            f"- scene_execution: {source_report['scene_execution']}",
            f"- hardware_behavior: {source_report['hardware_behavior']}",
            "Closeout Coverage:",
        ]
    )
    for coverage in source_report["closeout_coverage"]:
        lines.append(f"- {coverage}")

    return lines


# ---------------------------------------------------------------------------
# Mock mapper report
# ---------------------------------------------------------------------------

UNSUPPORTED_SAFE_GROUP_PROFILE_KEYS = ("4",)

MOCK_MAPPER_BOUNDARY = {
    "mock_only": True,
    "real_midi": "absent",
    "port_opening": "absent",
    "cli_wiring": "absent",
    "active_behavior": "absent",
    "hardware_required": False,
    "analog_four_support": "absent",
    "pads_5_12_support": "absent",
}


def _unsupported_safe_profile_summary(profile_key):
    summary = _profile_summary(profile_key)
    summary["reason"] = "intentionally unsupported until separately approved"
    return summary


def build_mock_mapper_report():
    """Return copied, in-memory data about current mock mapper support."""
    from ..mock_message_mapper import SUPPORTED_GROUP_PROFILE_KEYS

    supported_profiles = tuple(
        _profile_summary(profile_key) for profile_key in SUPPORTED_GROUP_PROFILE_KEYS
    )
    unsupported_safe_profiles = tuple(
        _unsupported_safe_profile_summary(profile_key)
        for profile_key in UNSUPPORTED_SAFE_GROUP_PROFILE_KEYS
    )

    report = {
        "title": "RytmRandomizer Mock Mapper Report",
        "supported_group_profiles": supported_profiles,
        "unsupported_safe_group_profiles": unsupported_safe_profiles,
        **MOCK_MAPPER_BOUNDARY,
        "source": {
            "mapper_module": "rytm_randomizer.mock_message_mapper",
            "supported_keys": tuple(SUPPORTED_GROUP_PROFILE_KEYS),
            "unsupported_safe_keys": tuple(UNSUPPORTED_SAFE_GROUP_PROFILE_KEYS),
            "in_memory_only": True,
        },
    }
    return deepcopy(report)


def summarize_mock_mapper_report(report=None):
    """Return a compact copied summary of the mock mapper report."""
    source_report = build_mock_mapper_report() if report is None else report
    return {
        "title": source_report["title"],
        "supported_count": len(source_report["supported_group_profiles"]),
        "unsupported_safe_count": len(source_report["unsupported_safe_group_profiles"]),
        "supported_keys": tuple(
            profile["profile_key"] for profile in source_report["supported_group_profiles"]
        ),
        "unsupported_safe_keys": tuple(
            profile["profile_key"] for profile in source_report["unsupported_safe_group_profiles"]
        ),
        "mock_only": source_report["mock_only"],
        "active_behavior": source_report["active_behavior"],
    }


def format_mock_mapper_report(report=None):
    """Return deterministic human-readable mock mapper report lines."""
    source_report = build_mock_mapper_report() if report is None else report
    lines = [
        source_report["title"],
        "Supported Mock Group Profile Mappings:",
    ]

    for profile in source_report["supported_group_profiles"]:
        lines.append(f"- {profile['profile_key']}: {profile['name']} ({profile['target']})")

    lines.append("Unsupported/Safe Group Profiles:")
    for profile in source_report["unsupported_safe_group_profiles"]:
        lines.append(
            f"- {profile['profile_key']}: {profile['name']} "
            f"({profile['target']}) - {profile['reason']}"
        )

    lines.extend(
        [
            "Mock Mapper Boundary:",
            f"- mock_only: {source_report['mock_only']}",
            f"- real_midi: {source_report['real_midi']}",
            f"- port_opening: {source_report['port_opening']}",
            f"- cli_wiring: {source_report['cli_wiring']}",
            f"- active_behavior: {source_report['active_behavior']}",
            f"- hardware_required: {source_report['hardware_required']}",
            f"- analog_four_support: {source_report['analog_four_support']}",
            f"- pads_5_12_support: {source_report['pads_5_12_support']}",
            *passive_footer_lines("mock_message_mapper"),
        ]
    )
    return lines


# ---------------------------------------------------------------------------
# Runtime plan report
# ---------------------------------------------------------------------------

SUPPORTED_REPORT_INPUTS = (
    {
        "category": "supported",
        "source_kind": "group_profile",
        "source_key": "2",
        "target": "Pad 1 / My BD Hard",
    },
    {
        "category": "supported",
        "source_kind": "group_profile",
        "source_key": "3",
        "target": "Pad 2 / My BD Classic",
    },
)

PARKED_REPORT_INPUTS = (
    {
        "category": "parked",
        "source_kind": "group_profile",
        "source_key": "4",
        "target": "Pad 1 / My BD Acoustic",
    },
)

UNSUPPORTED_REPORT_INPUTS = (
    {
        "category": "unsupported",
        "source_kind": "group_profile",
        "source_key": "unknown",
        "target": "unknown",
    },
    {
        "category": "unsupported",
        "source_kind": "scene",
        "source_key": "S1A",
        "target": "Rolling Light",
    },
)

RUNTIME_PLAN_REPORT_BOUNDARY = {
    "runtime_execution": "absent",
    "cli_execution_wiring": "absent",
    "dispatch": "absent",
    "command_execution": "absent",
    "scene_execution": "absent",
    "real_midi": "absent",
    "port_opening": "absent",
    "hardware_required": False,
}


def _runtime_preview_summary(report_input):
    from ..runtime_plan import RuntimeIntent, validate_runtime_intent_scope

    intent = RuntimeIntent(
        source_kind=report_input["source_kind"],
        source_key=report_input["source_key"],
        target=report_input["target"],
    )
    preview = validate_runtime_intent_scope(intent)
    metadata = preview.metadata
    return {
        "source_kind": metadata["source_kind"],
        "source_key": metadata["source_key"],
        "target": metadata["target"],
        "source_label": metadata["source_label"],
        "status": preview.status,
        "reason": preview.reason,
        "reason_code": metadata["reason_code"],
        "supported": metadata["supported"],
        "parked": metadata["parked"],
        "would_execute": metadata["would_execute"],
        "mock_only": metadata["mock_only"],
        "sends_real_midi": metadata["sends_real_midi"],
        "ports_allowed": metadata["ports_allowed"],
        "hardware_required": metadata["hardware_required"],
    }


def build_runtime_plan_report():
    """Return copied, in-memory data about current runtime plan metadata."""
    report = {
        "title": "RytmRandomizer Runtime Plan Report",
        "mode": {
            "mock_only": True,
            "metadata_only": True,
            "blocked_by_default": True,
        },
        "supported_planning_inputs": tuple(
            _runtime_preview_summary(report_input) for report_input in SUPPORTED_REPORT_INPUTS
        ),
        "parked_planning_inputs": tuple(
            _runtime_preview_summary(report_input) for report_input in PARKED_REPORT_INPUTS
        ),
        "unsupported_planning_inputs": tuple(
            _runtime_preview_summary(report_input) for report_input in UNSUPPORTED_REPORT_INPUTS
        ),
        "reason_codes": (
            "execution_not_implemented",
            "unsupported_key",
            "unsupported_source_kind",
            "profile_4_parked",
            "missing_arming",
        ),
        "safety": {
            "would_execute": False,
            "mock_only": True,
            "sends_real_midi": False,
            "ports_allowed": False,
            "hardware_required": False,
        },
        **RUNTIME_PLAN_REPORT_BOUNDARY,
        "source": {
            "runtime_plan_module": "rytm_randomizer.runtime_plan",
            "in_memory_only": True,
        },
    }
    return deepcopy(report)


def summarize_runtime_plan_report(report=None):
    """Return a compact copied summary of the runtime plan report."""
    source_report = build_runtime_plan_report() if report is None else report
    return {
        "title": source_report["title"],
        "supported_count": len(source_report["supported_planning_inputs"]),
        "parked_count": len(source_report["parked_planning_inputs"]),
        "unsupported_count": len(source_report["unsupported_planning_inputs"]),
        "reason_codes": tuple(source_report["reason_codes"]),
        "would_execute": source_report["safety"]["would_execute"],
        "mock_only": source_report["safety"]["mock_only"],
        "runtime_execution": source_report["runtime_execution"],
    }


def _runtime_input_line(summary):
    return f"- {summary['source_label']} -> {summary['target']} " f"({summary['reason_code']})"


def format_runtime_plan_report(report=None):
    """Return deterministic human-readable runtime plan report lines."""
    source_report = build_runtime_plan_report() if report is None else report
    lines = [
        source_report["title"],
        "Runtime Plan Mode:",
        f"- mock_only: {source_report['mode']['mock_only']}",
        f"- metadata_only: {source_report['mode']['metadata_only']}",
        f"- blocked_by_default: {source_report['mode']['blocked_by_default']}",
        "Supported Planning Inputs:",
    ]

    for summary in source_report["supported_planning_inputs"]:
        lines.append(_runtime_input_line(summary))

    lines.append("Parked Planning Inputs:")
    for summary in source_report["parked_planning_inputs"]:
        lines.append(_runtime_input_line(summary))

    lines.append("Unsupported Planning Inputs:")
    for summary in source_report["unsupported_planning_inputs"]:
        lines.append(_runtime_input_line(summary))

    lines.extend(
        [
            "Runtime Plan Safety:",
            f"- would_execute: {source_report['safety']['would_execute']}",
            f"- mock_only: {source_report['safety']['mock_only']}",
            f"- sends_real_midi: {source_report['safety']['sends_real_midi']}",
            f"- ports_allowed: {source_report['safety']['ports_allowed']}",
            f"- hardware_required: {source_report['safety']['hardware_required']}",
            f"- runtime_execution: {source_report['runtime_execution']}",
            f"- cli_execution_wiring: {source_report['cli_execution_wiring']}",
            f"- dispatch: {source_report['dispatch']}",
            *passive_footer_lines("runtime_plan"),
        ]
    )
    return lines


# ---------------------------------------------------------------------------
# Anchor/profile behavior report
# ---------------------------------------------------------------------------

ANCHOR_PROFILE_REPORT_TITLE = "RytmRandomizer Anchor/Profile Behavior Report"

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

ANCHOR_PROFILE_CLOSEOUT_COVERAGE = (
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

ANCHOR_PROFILE_PARKED_SECTIONS = (
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


def _anchor_profile_section_specs():
    from ..behavior.anchor_profile import evaluate_anchor_profile_behavior
    from ..behavior.pad_lane import (
        evaluate_pad1_lane_behavior,
        evaluate_pad2_lane_behavior,
        evaluate_pad3_lane_behavior,
        evaluate_pad4_lane_behavior,
    )
    from ..behavior.scene_group import evaluate_scene_group_behavior
    from ..behavior.selected_isolated_pad import evaluate_selected_isolated_pad_behavior
    from ..behavior.selected_profile import evaluate_selected_profile_behavior
    from ..behavior.undo_commit_state import evaluate_undo_commit_state_behavior

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


def _anchor_profile_label(result, metadata):
    return (
        getattr(result, "label", "")
        or metadata.get("source_group_command_label", "")
        or metadata.get("source_scene_name", "")
    )


def _anchor_profile_target_scope(result, metadata):
    return (
        getattr(result, "target_scope", "")
        or getattr(result, "source_scope", "")
        or metadata.get("source_group_command_scope", "")
        or metadata.get("source_scope", "")
    )


def _anchor_profile_intent_kind(command_key, result, metadata, options):
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


def _anchor_profile_concept(command_key, result, metadata, options):
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


def _anchor_profile_supported_entry(command_key, result, source_helper, options):
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


def _anchor_profile_supported_section(spec):
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


def build_anchor_profile_report():
    """Return copied, in-memory data about current anchor/profile behavior coverage."""
    report = {
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


def summarize_anchor_profile_report(report=None):
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

    lines.extend(safety_section_lines(source_report["safety"]))

    lines.append(f"Recommended Next Branch: {source_report['recommended_next_branch']}")
    return lines


# ---------------------------------------------------------------------------
# Behavior parity coverage report
# ---------------------------------------------------------------------------

ACCEPTED_PACKET_COVERAGE = (
    "Packet 1 menu/status and utility intent",
    "Packet 2 meaningful anchor/profile progress",
    "Packet 3 selected isolated pad mutation intent",
    "Packet 4 scene/group intent",
    "Packet 5 meaningful Pad 1 lane behavior progress",
    "Packet 6 Pad 2 lane behavior for the current read-only phase",
    "Packet 7 Pad 3 lane behavior for the current read-only phase",
    "Packet 8 Pad 4 command-helper scope for the current read-only phase",
    "Packet 9 undo/commit/state intent",
    "Packet 10 selected-profile workflow intent",
    "Packet 11A L selected isolated pad target intent",
    "Packet 11B PZ selected isolated pad anchor-return readiness",
)

RUNTIME_ADJACENT_MOCK_ONLY_SAFE_FAILURES = ("PZ", "B", "L")

PARITY_PARKED_SCOPE = (
    "fourth runtime-adjacent candidate",
    "profile 4 mock mapper support",
)

PARITY_ABSENT_BEHAVIOR = (
    "dispatch",
    "command execution",
    "scene execution",
    "runtime mutation",
    "selected pad switching execution",
    "selected pad target state mutation",
    "selected pad anchor return execution",
    "current anchor return execution",
    "isolated pad mutation execution",
    "active CLI commands",
    "real MIDI dependencies",
    "port discovery",
    "port opening",
    "MIDI sending",
    "hardware behavior",
    "Analog Four support",
    "Pads 5-12 support",
    "SysEx",
    "GUI/capture",
)

PARITY_CLOSEOUT_COVERAGE = (
    "Behavior Menu Utility",
    "Behavior Anchor Profile",
    "Behavior Anchor Profile Report",
    "Behavior Mutation Depth",
    "Behavior Scene Group",
    "Behavior Pad 1 Lane",
    "Behavior Pad 2 Lane",
    "Behavior Pad 3 Lane",
    "Behavior Pad 4 Lane",
    "Behavior Undo Commit State",
    "Behavior Selected Profile",
    "Behavior Selected Isolated Pad",
    "Selected Target State",
    "Anchor State",
    "Selected Isolated Pad Runtime State",
    "Runtime-Adjacent Mock-Only PZ",
    "Runtime-Adjacent Mock-Only B",
    "Runtime-Adjacent Mock-Only L",
)

PARITY_PROTECTED_FILE_STATE = {
    "v134_reference": "untouched",
    "package_metadata": "untouched",
    "runtime_execution_logic": "absent",
}

PARITY_REPORT_BOUNDARY = {
    "read_only": True,
    "in_memory_only": True,
    "cli_visibility": "present",
    "dispatch": "absent",
    "command_execution": "absent",
    "scene_execution": "absent",
    "real_midi": "absent",
    "port_opening": "absent",
    "active_behavior": "absent",
    "hardware_behavior": "absent",
    "hardware_required": False,
}


def _selected_isolated_pad_packet_coverage():
    from ..behavior.selected_isolated_pad import (
        PACKET_11A_SELECTED_ISOLATED_PAD_KEYS,
        PACKET_11B_SELECTED_ISOLATED_PAD_KEYS,
    )

    return (
        {
            "packet": "11A",
            "command_keys": PACKET_11A_SELECTED_ISOLATED_PAD_KEYS,
            "coverage": "selected isolated pad target intent",
        },
        {
            "packet": "11B",
            "command_keys": PACKET_11B_SELECTED_ISOLATED_PAD_KEYS,
            "coverage": "selected isolated pad anchor-return readiness",
        },
    )


def _pad_lane_packet_coverage():
    from ..behavior.pad_lane import (
        DEFERRED_PACKET_5_PAD1_LANE_KEYS,
        DEFERRED_PACKET_6_PAD2_LANE_KEYS,
        DEFERRED_PACKET_7_PAD3_LANE_KEYS,
        DEFERRED_PACKET_8_PAD4_LANE_KEYS,
        PACKET_5A_PAD1_CURRENT_ENGINE_KEYS,
        PACKET_5B_PAD1_BD_FM_KEYS,
        PACKET_5C_PAD1_BD_PLASTIC_KEYS,
        PACKET_5D_PAD1_BD_SILKY_KEYS,
        PACKET_5E_PAD1_BD_ACOUSTIC_KEYS,
        PACKET_6A_PAD2_LANE_KEYS,
        PACKET_6B_PAD2_LANE_KEYS,
        PACKET_6C_PAD2_LANE_KEYS,
        PACKET_6D_PAD2_LANE_KEYS,
        PACKET_6E_PAD2_LANE_KEYS,
        PACKET_6F_PAD2_LANE_KEYS,
        PACKET_6G_PAD2_LANE_KEYS,
        PACKET_6H_PAD2_LANE_KEYS,
        PACKET_6I_PAD2_LANE_KEYS,
        PACKET_6J_PAD2_LANE_KEYS,
        PACKET_7A_PAD3_LANE_KEYS,
        PACKET_7B_PAD3_LANE_KEYS,
        PACKET_7C_PAD3_LANE_KEYS,
        PACKET_7D_PAD3_LANE_KEYS,
        PACKET_7E_PAD3_LANE_KEYS,
        PACKET_7F_PAD3_LANE_KEYS,
        PACKET_7G_PAD3_LANE_KEYS,
        PACKET_7H_PAD3_LANE_KEYS,
        PACKET_8A_PAD4_LANE_KEYS,
        PACKET_8B_PAD4_LANE_KEYS,
        PACKET_8C_PAD4_LANE_KEYS,
    )

    return (
        {
            "packet": "5",
            "lane": "Pad 1 BD lane family",
            "command_keys": (
                PACKET_5A_PAD1_CURRENT_ENGINE_KEYS
                + PACKET_5B_PAD1_BD_FM_KEYS
                + PACKET_5C_PAD1_BD_PLASTIC_KEYS
                + PACKET_5D_PAD1_BD_SILKY_KEYS
                + PACKET_5E_PAD1_BD_ACOUSTIC_KEYS
            ),
            "deferred_keys": DEFERRED_PACKET_5_PAD1_LANE_KEYS,
            "coverage": "Pad 1 lane behavior for the current read-only phase",
        },
        {
            "packet": "6",
            "lane": "Pad 2 secondary lane",
            "command_keys": (
                PACKET_6A_PAD2_LANE_KEYS
                + PACKET_6B_PAD2_LANE_KEYS
                + PACKET_6C_PAD2_LANE_KEYS
                + PACKET_6D_PAD2_LANE_KEYS
                + PACKET_6E_PAD2_LANE_KEYS
                + PACKET_6F_PAD2_LANE_KEYS
                + PACKET_6G_PAD2_LANE_KEYS
                + PACKET_6H_PAD2_LANE_KEYS
                + PACKET_6I_PAD2_LANE_KEYS
                + PACKET_6J_PAD2_LANE_KEYS
            ),
            "deferred_keys": DEFERRED_PACKET_6_PAD2_LANE_KEYS,
            "coverage": "Pad 2 lane behavior for the current read-only phase",
        },
        {
            "packet": "7",
            "lane": "Pad 3 SY Raw lane",
            "command_keys": (
                PACKET_7A_PAD3_LANE_KEYS
                + PACKET_7B_PAD3_LANE_KEYS
                + PACKET_7C_PAD3_LANE_KEYS
                + PACKET_7D_PAD3_LANE_KEYS
                + PACKET_7E_PAD3_LANE_KEYS
                + PACKET_7F_PAD3_LANE_KEYS
                + PACKET_7G_PAD3_LANE_KEYS
                + PACKET_7H_PAD3_LANE_KEYS
            ),
            "deferred_keys": DEFERRED_PACKET_7_PAD3_LANE_KEYS,
            "coverage": "Pad 3 lane behavior for the current read-only phase",
        },
        {
            "packet": "8",
            "lane": "Pad 4 BD Acoustic lane",
            "command_keys": (
                PACKET_8A_PAD4_LANE_KEYS + PACKET_8B_PAD4_LANE_KEYS + PACKET_8C_PAD4_LANE_KEYS
            ),
            "deferred_keys": DEFERRED_PACKET_8_PAD4_LANE_KEYS,
            "coverage": "Pad 4 command-helper scope for the current read-only phase",
        },
    )


def build_behavior_parity_coverage_report():
    """Return copied, in-memory data about current behavior-parity coverage."""
    report = {
        "title": "V1.34 Behavior Parity Coverage Report",
        "accepted_packet_coverage": tuple(ACCEPTED_PACKET_COVERAGE),
        "selected_isolated_pad_packet_coverage": deepcopy(_selected_isolated_pad_packet_coverage()),
        "pad_lane_packet_coverage": deepcopy(_pad_lane_packet_coverage()),
        "runtime_adjacent_mock_only_safe_failures": tuple(RUNTIME_ADJACENT_MOCK_ONLY_SAFE_FAILURES),
        "parked_scope": tuple(PARITY_PARKED_SCOPE),
        "absent_behavior": tuple(PARITY_ABSENT_BEHAVIOR),
        "closeout_coverage": tuple(PARITY_CLOSEOUT_COVERAGE),
        "protected_file_state": dict(PARITY_PROTECTED_FILE_STATE),
        "source": {
            "plan_document": ("Docs/V134_BEHAVIOR_PARITY_PACKET_12_COVERAGE_REPORT_PLAN.md"),
            "review_document": (
                "Docs/V134_BEHAVIOR_PARITY_PACKET_12_COVERAGE_REPORT_PLAN_REVIEW.md"
            ),
            "report_module": "rytm_randomizer.reports",
        },
        **PARITY_REPORT_BOUNDARY,
    }
    return deepcopy(report)


def summarize_behavior_parity_coverage_report(report=None):
    """Return a compact copied summary of the behavior-parity coverage report."""
    source_report = build_behavior_parity_coverage_report() if report is None else report
    return {
        "title": source_report["title"],
        "accepted_packet_count": len(source_report["accepted_packet_coverage"]),
        "selected_isolated_pad_packet_count": len(
            source_report["selected_isolated_pad_packet_coverage"]
        ),
        "pad_lane_packet_count": len(source_report["pad_lane_packet_coverage"]),
        "pad_lane_command_count": sum(
            len(item["command_keys"]) for item in source_report["pad_lane_packet_coverage"]
        ),
        "runtime_adjacent_safe_failure_count": len(
            source_report["runtime_adjacent_mock_only_safe_failures"]
        ),
        "parked_scope_count": len(source_report["parked_scope"]),
        "closeout_coverage_count": len(source_report["closeout_coverage"]),
        "read_only": source_report["read_only"],
        "cli_visibility": source_report["cli_visibility"],
        "active_behavior": source_report["active_behavior"],
        "hardware_required": source_report["hardware_required"],
    }


def format_behavior_parity_coverage_report(report=None):
    """Return deterministic human-readable behavior-parity coverage lines."""
    source_report = build_behavior_parity_coverage_report() if report is None else report
    lines = [
        source_report["title"],
        "Accepted Packet Coverage:",
    ]

    for item in source_report["accepted_packet_coverage"]:
        lines.append(f"- {item}")

    lines.append("Selected Isolated Pad Packet Coverage:")
    for item in source_report["selected_isolated_pad_packet_coverage"]:
        command_keys = ", ".join(item["command_keys"])
        lines.append(f"- Packet {item['packet']}: {command_keys} - {item['coverage']}")

    lines.append("Pad Lane Packet Coverage:")
    for item in source_report["pad_lane_packet_coverage"]:
        command_keys = ", ".join(item["command_keys"])
        lines.append(
            f"- Packet {item['packet']}: {item['lane']} - " f"{command_keys} - {item['coverage']}"
        )
        deferred_keys = ", ".join(item["deferred_keys"]) or "none"
        lines.append(f"- Packet {item['packet']} deferred/safe: {deferred_keys}")

    lines.append("Runtime-Adjacent Mock-Only Safe Failures:")
    for item in source_report["runtime_adjacent_mock_only_safe_failures"]:
        lines.append(f"- {item}")

    lines.append("Parked Scope:")
    for item in source_report["parked_scope"]:
        lines.append(f"- {item}")

    lines.append("Absent Behavior:")
    for item in source_report["absent_behavior"]:
        lines.append(f"- {item}")

    lines.append("Protected File State:")
    for key, value in source_report["protected_file_state"].items():
        lines.append(f"- {key}: {value}")

    lines.extend(
        [
            "Report Boundary:",
            f"- read_only: {source_report['read_only']}",
            f"- in_memory_only: {source_report['in_memory_only']}",
            f"- cli_visibility: {source_report['cli_visibility']}",
            f"- active_behavior: {source_report['active_behavior']}",
            f"- hardware_required: {source_report['hardware_required']}",
        ]
    )
    return lines


# ---------------------------------------------------------------------------
# Mock runtime active bridge report
# ---------------------------------------------------------------------------

REPORT_MODE = {
    "read_only": True,
    "mock_only": True,
    "metadata_only": True,
    "invokes_bridge": False,
    "constructs_sender": False,
    "emits_messages": False,
}

BRIDGE_SUMMARY = {
    "module": "rytm_randomizer.mock_runtime_active_bridge",
    "request_type": "RuntimeActiveBridgeRequest",
    "result_type": "RuntimeActiveBridgeResult",
    "evaluator": "evaluate_mock_runtime_active_bridge",
}

ACCEPTED_CANDIDATE = {
    "source_kind": "group_profile",
    "source_key": "2",
    "source_name": "My BD Hard",
    "target": "Pad 1 / BD Hard",
    "requires_armed": True,
    "requires_dry_run_confirmed": True,
    "sender": "MockMidiSender",
}

REJECTED_CASES = (
    {
        "case": "missing_arming",
        "description": "missing arming fails safely",
        "emits_messages": False,
    },
    {
        "case": "missing_dry_run_confirmation",
        "description": "missing dry-run confirmation fails safely",
        "emits_messages": False,
    },
    {
        "case": "profile_3_bridge_rejected",
        "source_kind": "group_profile",
        "source_key": "3",
        "source_name": "My BD Classic",
        "emits_messages": False,
    },
    {
        "case": "unknown_key",
        "description": "unknown group profile keys fail safely",
        "emits_messages": False,
    },
    {
        "case": "unsupported_source_kind",
        "description": "unsupported source kinds fail safely",
        "emits_messages": False,
    },
    {
        "case": "invalid_request",
        "description": "invalid request fails before message emission",
        "emits_messages": False,
    },
    {
        "case": "invalid_sender",
        "description": "invalid sender fails before message emission",
        "emits_messages": False,
    },
)

PARKED_CASES = (
    {
        "case": "profile_4_parked",
        "source_kind": "group_profile",
        "source_key": "4",
        "source_name": "My BD Acoustic",
        "emits_messages": False,
        "reason": "parked until separately approved",
    },
)

SAFETY_BOUNDARY = {
    "real_midi": "absent",
    "port_opening": "absent",
    "hardware_required": False,
    "cli_execution_wiring": "absent",
    "runtime_execution": "absent",
    "dispatch": "absent",
    "active_behavior": "absent",
    "hardware_behavior": "absent",
}


def build_mock_runtime_active_bridge_report():
    """Return copied, in-memory data about the current bridge report contract."""
    report = {
        "title": "RytmRandomizer Mock Runtime Active Bridge Report",
        "mode": REPORT_MODE,
        "bridge": BRIDGE_SUMMARY,
        "accepted_candidate": ACCEPTED_CANDIDATE,
        "rejected_cases": REJECTED_CASES,
        "parked_cases": PARKED_CASES,
        "safety": SAFETY_BOUNDARY,
        "source": {
            "bridge_module": "rytm_randomizer.mock_runtime_active_bridge",
            "in_memory_only": True,
        },
    }
    return deepcopy(report)


def summarize_mock_runtime_active_bridge_report(report=None):
    """Return a compact copied summary of the bridge report contract."""
    source_report = build_mock_runtime_active_bridge_report() if report is None else report
    return {
        "title": source_report["title"],
        "accepted_source_key": source_report["accepted_candidate"]["source_key"],
        "rejected_count": len(source_report["rejected_cases"]),
        "parked_count": len(source_report["parked_cases"]),
        "read_only": source_report["mode"]["read_only"],
        "mock_only": source_report["mode"]["mock_only"],
        "invokes_bridge": source_report["mode"]["invokes_bridge"],
        "constructs_sender": source_report["mode"]["constructs_sender"],
        "emits_messages": source_report["mode"]["emits_messages"],
    }


def _bridge_rejected_case_line(rejected_case):
    if rejected_case["case"] == "profile_3_bridge_rejected":
        return (
            f"- {rejected_case['source_kind']}:{rejected_case['source_key']} / "
            f"{rejected_case['source_name']}: bridge rejected"
        )
    return f"- {rejected_case['case']}: {rejected_case['description']}"


def _bridge_parked_case_line(parked_case):
    return (
        f"- {parked_case['source_kind']}:{parked_case['source_key']} / "
        f"{parked_case['source_name']}: {parked_case['reason']}"
    )


def format_mock_runtime_active_bridge_report(report=None):
    """Return deterministic human-readable bridge report lines."""
    source_report = build_mock_runtime_active_bridge_report() if report is None else report
    candidate = source_report["accepted_candidate"]
    lines = [
        source_report["title"],
        "Bridge Mode:",
        f"- read_only: {source_report['mode']['read_only']}",
        f"- mock_only: {source_report['mode']['mock_only']}",
        f"- metadata_only: {source_report['mode']['metadata_only']}",
        f"- invokes_bridge: {source_report['mode']['invokes_bridge']}",
        f"- constructs_sender: {source_report['mode']['constructs_sender']}",
        f"- emits_messages: {source_report['mode']['emits_messages']}",
        "Accepted Candidate:",
        (
            f"- {candidate['source_kind']}:{candidate['source_key']} / "
            f"{candidate['source_name']} -> {candidate['target']}"
        ),
        f"- requires_armed: {candidate['requires_armed']}",
        f"- requires_dry_run_confirmed: {candidate['requires_dry_run_confirmed']}",
        f"- sender: {candidate['sender']}",
        "Rejected Cases:",
    ]

    for rejected_case in source_report["rejected_cases"]:
        lines.append(_bridge_rejected_case_line(rejected_case))

    lines.append("Parked Cases:")
    for parked_case in source_report["parked_cases"]:
        lines.append(_bridge_parked_case_line(parked_case))

    lines.extend(
        [
            "Safety:",
            f"- real_midi: {source_report['safety']['real_midi']}",
            f"- port_opening: {source_report['safety']['port_opening']}",
            f"- hardware_required: {source_report['safety']['hardware_required']}",
            ("- cli_execution_wiring: " f"{source_report['safety']['cli_execution_wiring']}"),
            f"- runtime_execution: {source_report['safety']['runtime_execution']}",
            f"- dispatch: {source_report['safety']['dispatch']}",
            f"- active_behavior: {source_report['safety']['active_behavior']}",
            f"- hardware_behavior: {source_report['safety']['hardware_behavior']}",
            *passive_footer_lines("mock_runtime_active_bridge"),
        ]
    )
    return lines


# ---------------------------------------------------------------------------
# CLI registry entries (WS-S7 / H7 scoped migration)
#
# These three commands are migrated from the inline ``if args == [...]``
# ladder in ``rytm_randomizer/cli.py:main()`` to the ``cli_registry``
# extension seam. The arch test
# ``tests/architecture/test_cli_no_inline_arms.py`` grandfathers the
# remaining inline arms and rejects any *new* additions, so all future
# passive subcommands MUST register here (or in a per-report module like
# ``rytm_machine_matrix.py``) instead of being cut into ``main()``.
#
# Each ``CliCommand`` follows the same shape as
# ``RYTM_MACHINE_MATRIX_CLI_COMMAND``:
#
# * ``_parse_<command>_args`` rejects argv tails (these arms take no
#   arguments), raising ``ValueError`` so the dispatcher renders
#   ``USAGE`` and exits ``2`` — preserving the behavior asserted by
#   ``test_unknown_<command>_arguments_fail_safely``.
# * ``_handle_<command>`` writes the same lines the deleted inline arm
#   wrote, returning ``0`` on success.
# * ``register(...)`` is NOT called at module-import time here — the
#   registration is wired through ``cli.py:_registered_command_exit_code``'s
#   ``lazy_commands`` table, matching the existing pattern for every
#   per-report module. That avoids importing the reports package eagerly
#   from ``cli.py`` (which would defeat the lazy-import discipline this
#   ``__init__`` already relies on).
# ---------------------------------------------------------------------------


def _parse_mock_mapper_report_args(argv: Sequence[str]) -> dict[str, Any]:
    if argv:
        raise ValueError("mock-mapper-report takes no arguments")
    return {}


def _handle_mock_mapper_report() -> int:
    sys.stdout.write("\n".join(format_mock_mapper_report()))
    sys.stdout.write("\n")
    return 0


MOCK_MAPPER_REPORT_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="mock-mapper-report",
    summary="Print the passive mock message mapper report.",
    args_parser=_parse_mock_mapper_report_args,
    handler=_handle_mock_mapper_report,
)


def _parse_runtime_plan_report_args(argv: Sequence[str]) -> dict[str, Any]:
    if argv:
        raise ValueError("runtime-plan-report takes no arguments")
    return {}


def _handle_runtime_plan_report() -> int:
    sys.stdout.write("\n".join(format_runtime_plan_report()))
    sys.stdout.write("\n")
    return 0


RUNTIME_PLAN_REPORT_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="runtime-plan-report",
    summary="Print the passive runtime plan report.",
    args_parser=_parse_runtime_plan_report_args,
    handler=_handle_runtime_plan_report,
)


def _parse_active_boundary_report_args(argv: Sequence[str]) -> dict[str, Any]:
    if argv:
        raise ValueError("active-boundary-report takes no arguments")
    return {}


def _handle_active_boundary_report() -> int:
    sys.stdout.write("\n".join(format_active_boundary_report()))
    sys.stdout.write("\n")
    return 0


ACTIVE_BOUNDARY_REPORT_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="active-boundary-report",
    summary="Print the passive active boundary report.",
    args_parser=_parse_active_boundary_report_args,
    handler=_handle_active_boundary_report,
)
