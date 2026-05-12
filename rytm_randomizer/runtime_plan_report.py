"""Read-only runtime plan report summary.

This module is passive and in-memory only. It reports current mock-only
runtime plan metadata without opening ports, sending MIDI, wiring CLI
execution, or touching hardware.
"""

from __future__ import annotations

from copy import deepcopy

from .runtime_plan import RuntimeIntent, validate_runtime_intent_scope


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


def _preview_summary(report_input):
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
            _preview_summary(report_input)
            for report_input in SUPPORTED_REPORT_INPUTS
        ),
        "parked_planning_inputs": tuple(
            _preview_summary(report_input)
            for report_input in PARKED_REPORT_INPUTS
        ),
        "unsupported_planning_inputs": tuple(
            _preview_summary(report_input)
            for report_input in UNSUPPORTED_REPORT_INPUTS
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


def _input_line(summary):
    return (
        f"- {summary['source_label']} -> {summary['target']} "
        f"({summary['reason_code']})"
    )


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
        lines.append(_input_line(summary))

    lines.append("Parked Planning Inputs:")
    for summary in source_report["parked_planning_inputs"]:
        lines.append(_input_line(summary))

    lines.append("Unsupported Planning Inputs:")
    for summary in source_report["unsupported_planning_inputs"]:
        lines.append(_input_line(summary))

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
            "Source: rytm_randomizer.runtime_plan",
            "In-memory only: True",
        ]
    )
    return lines
