"""Read-only project status report summary.

This module is passive and in-memory only. It reports current project status
without opening ports, sending MIDI, wiring active execution, dispatching
commands, mutating runtime state, writing files, or touching hardware.
"""

from __future__ import annotations

from copy import deepcopy
import json


PASSIVE_CLI_COMMANDS = (
    "report",
    "project-status-report",
    "mock-mapper-report",
    "runtime-plan-report",
    "active-boundary-report",
    "mock-runtime-active-bridge-report",
    "anchor-profile-report",
    "behavior-parity-report",
    "list-commands",
    "list-scenes",
    "list-group-profiles",
    "search-commands",
    "search-scenes",
    "search-group-profiles",
    "inspect-command",
    "inspect-scene",
    "inspect-group-profile",
    "preview-command",
    "preview-scene",
    "preview-group-profile",
)

PROJECT_PHASE = {
    "name": "Passive/Mock Runtime Visibility Phase",
    "technical_name": "RytmRandomizer",
    "creative_identity_candidate": "KitForge",
    "repository_name": "RytmRandomizer",
    "package_name": "rytm_randomizer",
}

CLOSEOUT_STATUS = {
    "closeout_contract": "present",
    "failure_propagation": "guarded",
    "closeout_script": "Scripts/closeout_check.ps1",
}

PROJECT_STATUS_SAFETY = {
    "real_midi": "absent",
    "port_opening": "absent",
    "active_execution": "absent",
    "dispatch": "absent",
    "command_execution": "absent",
    "hardware_required": False,
    "hardware_behavior": "absent",
    "analog_four_support": "absent",
    "pads_5_12_support": "absent",
    "v134_reference": "untouched",
    "package_metadata": "untouched",
}


def build_project_status_report():
    """Return copied, in-memory data about the current project status."""

    from .active_boundary_report import summarize_active_boundary_report
    from .behavior_parity_coverage_report import (
        summarize_behavior_parity_coverage_report,
    )
    from .mock_runtime_active_bridge_report import (
        summarize_mock_runtime_active_bridge_report,
    )
    from .runtime_plan_report import summarize_runtime_plan_report

    report = {
        "title": "RytmRandomizer Project Status Report",
        "phase": PROJECT_PHASE,
        "passive_cli_commands": PASSIVE_CLI_COMMANDS,
        "behavior_parity": summarize_behavior_parity_coverage_report(),
        "runtime_plan": summarize_runtime_plan_report(),
        "active_boundary": summarize_active_boundary_report(),
        "mock_runtime_active_bridge": summarize_mock_runtime_active_bridge_report(),
        "closeout": CLOSEOUT_STATUS,
        "safety": PROJECT_STATUS_SAFETY,
        "source": {
            "in_memory_only": True,
            "writes_files": False,
            "report_module": "rytm_randomizer.project_status_report",
        },
    }
    return deepcopy(report)


def summarize_project_status_report(report=None):
    """Return a compact copied summary of the project status report."""

    source_report = build_project_status_report() if report is None else report
    return {
        "title": source_report["title"],
        "phase_name": source_report["phase"]["name"],
        "creative_identity_candidate": source_report["phase"][
            "creative_identity_candidate"
        ],
        "passive_cli_command_count": len(source_report["passive_cli_commands"]),
        "accepted_packet_count": source_report["behavior_parity"][
            "accepted_packet_count"
        ],
        "pad_lane_command_count": source_report["behavior_parity"][
            "pad_lane_command_count"
        ],
        "runtime_supported_count": source_report["runtime_plan"]["supported_count"],
        "active_boundary_candidate": source_report["active_boundary"][
            "supported_candidate"
        ],
        "mock_bridge_candidate": source_report["mock_runtime_active_bridge"][
            "accepted_source_key"
        ],
        "real_midi": source_report["safety"]["real_midi"],
        "hardware_required": source_report["safety"]["hardware_required"],
    }


def format_project_status_report(report=None):
    """Return deterministic human-readable project status report lines."""

    source_report = build_project_status_report() if report is None else report
    phase = source_report["phase"]
    behavior = source_report["behavior_parity"]
    runtime = source_report["runtime_plan"]
    active = source_report["active_boundary"]
    bridge = source_report["mock_runtime_active_bridge"]

    lines = [
        source_report["title"],
        "Phase:",
        f"- name: {phase['name']}",
        f"- technical_name: {phase['technical_name']}",
        f"- creative_identity_candidate: {phase['creative_identity_candidate']}",
        "Passive CLI Visibility:",
    ]

    for command in source_report["passive_cli_commands"]:
        lines.append(f"- {command}")

    lines.extend(
        [
            "Behavior Parity:",
            f"- accepted_packet_count: {behavior['accepted_packet_count']}",
            (
                "- selected_isolated_pad_packet_count: "
                f"{behavior['selected_isolated_pad_packet_count']}"
            ),
            f"- pad_lane_packet_count: {behavior['pad_lane_packet_count']}",
            f"- pad_lane_command_count: {behavior['pad_lane_command_count']}",
            (
                "- runtime_adjacent_safe_failure_count: "
                f"{behavior['runtime_adjacent_safe_failure_count']}"
            ),
            f"- parked_scope_count: {behavior['parked_scope_count']}",
            "Runtime Plan:",
            f"- supported_count: {runtime['supported_count']}",
            f"- parked_count: {runtime['parked_count']}",
            f"- unsupported_count: {runtime['unsupported_count']}",
            f"- runtime_execution: {runtime['runtime_execution']}",
            "Active Boundary:",
            f"- supported_candidate: {active['supported_candidate']}",
            f"- unsupported_keys: {', '.join(active['unsupported_keys'])}",
            f"- active_cli_behavior: {active['active_cli_behavior']}",
            "Mock Runtime Active Bridge:",
            f"- accepted_source_key: {bridge['accepted_source_key']}",
            f"- rejected_count: {bridge['rejected_count']}",
            f"- parked_count: {bridge['parked_count']}",
            f"- emits_messages: {bridge['emits_messages']}",
            "Closeout:",
        ]
    )

    for key, value in source_report["closeout"].items():
        lines.append(f"- {key}: {value}")

    lines.append("Safety:")
    for key, value in source_report["safety"].items():
        lines.append(f"- {key}: {value}")

    lines.extend(
        [
            "Source:",
            f"- in_memory_only: {source_report['source']['in_memory_only']}",
            f"- writes_files: {source_report['source']['writes_files']}",
        ]
    )
    return lines


def format_project_status_report_json(report=None):
    """Return deterministic JSON for the copied project status report."""

    source_report = build_project_status_report() if report is None else report
    return json.dumps(deepcopy(source_report), indent=2, sort_keys=True)
