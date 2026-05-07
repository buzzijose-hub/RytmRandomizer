"""Read-only active boundary report summary.

This module reports the current mock-first active boundary state without
evaluating requests, opening ports, sending MIDI, dispatching behavior, wiring
CLI commands, or touching hardware.
"""

from __future__ import annotations

from copy import deepcopy

from .active_boundary import SUPPORTED_SOURCE_KEY, SUPPORTED_SOURCE_KIND
from .profile_lookup import describe_group_profile

UNSUPPORTED_ACTIVE_BOUNDARY_PROFILE_KEYS = ("3", "4")
UNSUPPORTED_SOURCE_KINDS = ("scene", "command")

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

CLOSEOUT_COVERAGE = (
    "Mock-Only Active Candidate",
    "Active Boundary",
)


def _target_concept(profile):
    source_name = profile["name"]
    target_name = source_name[3:] if source_name.startswith("My ") else source_name
    return f"Pad {profile['group_pad']} / {target_name}"


def _profile_summary(profile_key):
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
        "required_conditions": tuple(REQUIRED_CONDITIONS),
        "safe_failure_summary": tuple(SAFE_FAILURE_SUMMARY),
        "closeout_coverage": tuple(CLOSEOUT_COVERAGE),
        "source": {
            "boundary_module": "rytm_randomizer.active_boundary",
            "report_module": "rytm_randomizer.active_boundary_report",
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
        "accepted_key": source_report["accepted_candidate"]["profile_key"],
        "unsupported_keys": tuple(
            profile["profile_key"]
            for profile in source_report["unsupported_profiles"]
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
