"""Read-only behavior-parity coverage report.

This module summarizes accepted behavior-parity coverage in memory only. It
does not import MIDI libraries, open ports, send MIDI, wire CLI behavior,
dispatch commands, execute runtime behavior, or touch hardware.
"""

from __future__ import annotations

from copy import deepcopy

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
)

RUNTIME_ADJACENT_MOCK_ONLY_SAFE_FAILURES = ("PZ", "B", "L")

PARKED_SCOPE = (
    "fourth runtime-adjacent candidate",
    "profile 4 mock mapper support",
)

ABSENT_BEHAVIOR = (
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

CLOSEOUT_COVERAGE = (
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

PROTECTED_FILE_STATE = {
    "v134_reference": "untouched",
    "package_metadata": "untouched",
    "runtime_execution_logic": "absent",
}

REPORT_BOUNDARY = {
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


def build_behavior_parity_coverage_report():
    """Return copied, in-memory data about current behavior-parity coverage."""

    report = {
        "title": "V1.34 Behavior Parity Coverage Report",
        "accepted_packet_coverage": tuple(ACCEPTED_PACKET_COVERAGE),
        "runtime_adjacent_mock_only_safe_failures": tuple(
            RUNTIME_ADJACENT_MOCK_ONLY_SAFE_FAILURES
        ),
        "parked_scope": tuple(PARKED_SCOPE),
        "absent_behavior": tuple(ABSENT_BEHAVIOR),
        "closeout_coverage": tuple(CLOSEOUT_COVERAGE),
        "protected_file_state": dict(PROTECTED_FILE_STATE),
        "source": {
            "plan_document": (
                "Docs/V134_BEHAVIOR_PARITY_PACKET_12_COVERAGE_REPORT_PLAN.md"
            ),
            "review_document": (
                "Docs/V134_BEHAVIOR_PARITY_PACKET_12_COVERAGE_REPORT_PLAN_REVIEW.md"
            ),
            "report_module": "rytm_randomizer.behavior_parity_coverage_report",
        },
        **REPORT_BOUNDARY,
    }
    return deepcopy(report)


def summarize_behavior_parity_coverage_report(report=None):
    """Return a compact copied summary of the behavior-parity coverage report."""

    source_report = (
        build_behavior_parity_coverage_report() if report is None else report
    )
    return {
        "title": source_report["title"],
        "accepted_packet_count": len(source_report["accepted_packet_coverage"]),
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

    source_report = (
        build_behavior_parity_coverage_report() if report is None else report
    )
    lines = [
        source_report["title"],
        "Accepted Packet Coverage:",
    ]

    for item in source_report["accepted_packet_coverage"]:
        lines.append(f"- {item}")

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
