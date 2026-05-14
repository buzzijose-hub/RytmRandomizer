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

PROJECT_STATUS_CHECKS = (
    ("safety.real_midi", "absent"),
    ("safety.port_opening", "absent"),
    ("safety.active_execution", "absent"),
    ("safety.command_execution", "absent"),
    ("safety.dispatch", "absent"),
    ("safety.hardware_required", False),
    ("safety.v134_reference", "untouched"),
    ("safety.package_metadata", "untouched"),
    ("runtime_plan.runtime_execution", "absent"),
    ("active_boundary.active_cli_behavior", "absent"),
    ("mock_runtime_active_bridge.emits_messages", False),
    ("source.in_memory_only", True),
    ("source.writes_files", False),
    ("closeout.failure_propagation", "guarded"),
)


def _get_nested_value(data, path):
    current = data
    for part in path.split("."):
        current = current[part]
    return current


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


def check_project_status_report(report=None):
    """Return deterministic safety check results for project status data."""

    source_report = build_project_status_report() if report is None else report
    checked = {}
    failures = []

    for path, expected in PROJECT_STATUS_CHECKS:
        actual = _get_nested_value(source_report, path)
        checked[path] = actual
        if actual != expected:
            failures.append({"path": path, "expected": expected, "actual": actual})

    return {
        "title": "RytmRandomizer Project Status Check",
        "ok": not failures,
        "failure_count": len(failures),
        "failures": failures,
        "checked": checked,
    }


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
        "port_opening": source_report["safety"]["port_opening"],
        "active_execution": source_report["safety"]["active_execution"],
        "hardware_required": source_report["safety"]["hardware_required"],
        "v134_reference": source_report["safety"]["v134_reference"],
    }


def format_project_status_summary(report=None):
    """Return deterministic compact project status summary lines."""

    summary = summarize_project_status_report(report)
    return [
        "RytmRandomizer Project Status Summary",
        f"- phase_name: {summary['phase_name']}",
        f"- creative_identity_candidate: {summary['creative_identity_candidate']}",
        f"- passive_cli_command_count: {summary['passive_cli_command_count']}",
        f"- accepted_packet_count: {summary['accepted_packet_count']}",
        f"- pad_lane_command_count: {summary['pad_lane_command_count']}",
        f"- runtime_supported_count: {summary['runtime_supported_count']}",
        f"- active_boundary_candidate: {summary['active_boundary_candidate']}",
        f"- mock_bridge_candidate: {summary['mock_bridge_candidate']}",
        f"- real_midi: {summary['real_midi']}",
        f"- port_opening: {summary['port_opening']}",
        f"- active_execution: {summary['active_execution']}",
        f"- hardware_required: {summary['hardware_required']}",
        f"- v134_reference: {summary['v134_reference']}",
    ]


def format_project_status_check(report=None):
    """Return deterministic project status safety check lines."""

    check = check_project_status_report(report)
    lines = [
        check["title"],
        f"- ok: {check['ok']}",
        f"- failure_count: {check['failure_count']}",
    ]

    for path, _expected in PROJECT_STATUS_CHECKS:
        lines.append(f"- {path}: {check['checked'][path]}")

    if check["failures"]:
        lines.append("Failures:")
        for failure in check["failures"]:
            lines.append(
                "- "
                f"{failure['path']}: expected {failure['expected']}, "
                f"actual {failure['actual']}"
            )

    return lines


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
