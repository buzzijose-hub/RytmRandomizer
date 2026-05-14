"""Read-only mock runtime/active bridge report summary.

This module is passive and in-memory only. It reports the accepted mock
runtime/active bridge contract without invoking the bridge, constructing a
sender, emitting messages, opening ports, sending MIDI, wiring CLI execution,
or touching hardware.
"""

from __future__ import annotations

from copy import deepcopy


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

__all__ = [
    "ACCEPTED_CANDIDATE",
    "BRIDGE_SUMMARY",
    "PARKED_CASES",
    "REJECTED_CASES",
    "REPORT_MODE",
    "SAFETY_BOUNDARY",
    "build_mock_runtime_active_bridge_report",
    "format_mock_runtime_active_bridge_report",
    "summarize_mock_runtime_active_bridge_report",
]


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

    source_report = (
        build_mock_runtime_active_bridge_report() if report is None else report
    )
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


def _rejected_case_line(rejected_case):
    if rejected_case["case"] == "profile_3_bridge_rejected":
        return (
            f"- {rejected_case['source_kind']}:{rejected_case['source_key']} / "
            f"{rejected_case['source_name']}: bridge rejected"
        )
    return f"- {rejected_case['case']}: {rejected_case['description']}"


def _parked_case_line(parked_case):
    return (
        f"- {parked_case['source_kind']}:{parked_case['source_key']} / "
        f"{parked_case['source_name']}: {parked_case['reason']}"
    )


def format_mock_runtime_active_bridge_report(report=None):
    """Return deterministic human-readable bridge report lines."""

    source_report = (
        build_mock_runtime_active_bridge_report() if report is None else report
    )
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
        lines.append(_rejected_case_line(rejected_case))

    lines.append("Parked Cases:")
    for parked_case in source_report["parked_cases"]:
        lines.append(_parked_case_line(parked_case))

    lines.extend(
        [
            "Safety:",
            f"- real_midi: {source_report['safety']['real_midi']}",
            f"- port_opening: {source_report['safety']['port_opening']}",
            f"- hardware_required: {source_report['safety']['hardware_required']}",
            (
                "- cli_execution_wiring: "
                f"{source_report['safety']['cli_execution_wiring']}"
            ),
            f"- runtime_execution: {source_report['safety']['runtime_execution']}",
            f"- dispatch: {source_report['safety']['dispatch']}",
            f"- active_behavior: {source_report['safety']['active_behavior']}",
            f"- hardware_behavior: {source_report['safety']['hardware_behavior']}",
            "Source: rytm_randomizer.mock_runtime_active_bridge",
            "In-memory only: True",
        ]
    )
    return lines
