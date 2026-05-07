"""Read-only mock mapper report summary.

This module is passive and in-memory only. It reports current test-only mock
mapper support without opening ports, sending MIDI, wiring CLI behavior, or
touching hardware.
"""

from __future__ import annotations

from copy import deepcopy

from .mock_message_mapper import SUPPORTED_GROUP_PROFILE_KEYS
from .profile_lookup import describe_group_profile

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


def _unsupported_safe_profile_summary(profile_key):
    summary = _profile_summary(profile_key)
    summary["reason"] = "intentionally unsupported until separately approved"
    return summary


def build_mock_mapper_report():
    """Return copied, in-memory data about current mock mapper support."""

    supported_profiles = tuple(
        _profile_summary(profile_key)
        for profile_key in SUPPORTED_GROUP_PROFILE_KEYS
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
            profile["profile_key"]
            for profile in source_report["supported_group_profiles"]
        ),
        "unsupported_safe_keys": tuple(
            profile["profile_key"]
            for profile in source_report["unsupported_safe_group_profiles"]
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
        lines.append(
            f"- {profile['profile_key']}: {profile['name']} ({profile['target']})"
        )

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
            "Source: rytm_randomizer.mock_message_mapper",
            "In-memory only: True",
        ]
    )
    return lines
