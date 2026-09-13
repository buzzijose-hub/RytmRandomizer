"""Passive mock-mapper report.

Extracted verbatim from the former monolithic ``rytm_randomizer.reports``
module when it reached the 1500-LOC comprehensibility cap (see
``tests/architecture/test_reports_max_module_size.py``). Behavior is
unchanged; the public names are re-exported from ``rytm_randomizer.reports``
so every existing import keeps working.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Final, TypedDict

from ..formatter import passive_footer_lines
from .profile_summary import (
    ProfileSummaryDict,
    UnsupportedProfileSummaryDict,
    profile_summary_row,
)


class MockMapperSourceDict(TypedDict):
    """Provenance block for the mock mapper report."""

    mapper_module: str
    supported_keys: tuple[str, ...]
    unsupported_safe_keys: tuple[str, ...]
    in_memory_only: bool


class MockMapperReportDict(TypedDict):
    """Fixed shape of :func:`build_mock_mapper_report`.

    The ``mock_only`` .. ``pads_5_12_support`` keys are spread in from
    ``MOCK_MAPPER_BOUNDARY``; they are declared here so the spread stays
    type-checked.
    """

    title: str
    supported_group_profiles: tuple[ProfileSummaryDict, ...]
    unsupported_safe_group_profiles: tuple[UnsupportedProfileSummaryDict, ...]
    mock_only: bool
    real_midi: str
    port_opening: str
    cli_wiring: str
    active_behavior: str
    hardware_required: bool
    analog_four_support: str
    pads_5_12_support: str
    source: MockMapperSourceDict


class MockMapperSummaryDict(TypedDict):
    """Fixed shape of :func:`summarize_mock_mapper_report`."""

    title: str
    supported_count: int
    unsupported_safe_count: int
    supported_keys: tuple[str, ...]
    unsupported_safe_keys: tuple[str, ...]
    mock_only: bool
    active_behavior: str


UNSUPPORTED_SAFE_GROUP_PROFILE_KEYS: Final[tuple[str, ...]] = ("4",)


class MockMapperBoundaryDict(TypedDict):
    """Boundary block spread into the report literal."""

    mock_only: bool
    real_midi: str
    port_opening: str
    cli_wiring: str
    active_behavior: str
    hardware_required: bool
    analog_four_support: str
    pads_5_12_support: str


MOCK_MAPPER_BOUNDARY: Final[MockMapperBoundaryDict] = {
    "mock_only": True,
    "real_midi": "absent",
    "port_opening": "absent",
    "cli_wiring": "absent",
    "active_behavior": "absent",
    "hardware_required": False,
    "analog_four_support": "absent",
    "pads_5_12_support": "absent",
}


def _unsupported_safe_profile_summary(profile_key: str) -> UnsupportedProfileSummaryDict:
    summary = profile_summary_row(profile_key)
    return {
        "profile_key": summary["profile_key"],
        "name": summary["name"],
        "group_pad": summary["group_pad"],
        "machine_value": summary["machine_value"],
        "target": summary["target"],
        "reason": "intentionally unsupported until separately approved",
    }


def build_mock_mapper_report() -> MockMapperReportDict:
    """Return copied, in-memory data about current mock mapper support."""
    from ...mock_message_mapper import SUPPORTED_GROUP_PROFILE_KEYS

    supported_profiles = tuple(
        profile_summary_row(profile_key) for profile_key in SUPPORTED_GROUP_PROFILE_KEYS
    )
    unsupported_safe_profiles = tuple(
        _unsupported_safe_profile_summary(profile_key)
        for profile_key in UNSUPPORTED_SAFE_GROUP_PROFILE_KEYS
    )

    report: MockMapperReportDict = {
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


def summarize_mock_mapper_report(
    report: MockMapperReportDict | None = None,
) -> MockMapperSummaryDict:
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


def format_mock_mapper_report(report: MockMapperReportDict | None = None) -> list[str]:
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
