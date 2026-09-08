"""Passive active-boundary report.

Extracted verbatim from the former monolithic ``rytm_randomizer.reports``
module when it reached the 1500-LOC comprehensibility cap (see
``tests/architecture/test_reports_max_module_size.py``). Behavior is
unchanged; the public names are re-exported from ``rytm_randomizer.reports``
so every existing import keeps working.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Final, TypedDict

from .profile_summary import (
    ProfileSummaryDict,
    UnsupportedProfileSummaryDict,
    profile_summary_row,
)


class AcceptedCandidateDict(ProfileSummaryDict):
    """Accepted candidate row, carrying the source kind it was accepted for."""

    source_kind: str


class ResultMetadataDict(TypedDict):
    """Metadata block describing the boundary's result contract."""

    boundary: str
    supported_candidate: str
    fields: tuple[str, ...]
    failure_reason: str


class ActiveBoundarySourceDict(TypedDict):
    """Provenance block for the active boundary report."""

    boundary_module: str
    report_module: str
    in_memory_only: bool
    evaluates_active_requests: bool


class ActiveBoundaryReportDict(TypedDict):
    """Fixed shape of :func:`build_active_boundary_report`.

    The ``mock_only`` .. ``hardware_behavior`` keys are spread in from
    ``ACTIVE_BOUNDARY_SAFETY``; declaring them here keeps that spread
    type-checked.
    """

    title: str
    accepted_candidate: AcceptedCandidateDict
    unsupported_profiles: tuple[UnsupportedProfileSummaryDict, ...]
    unsupported_source_kinds: tuple[str, ...]
    result_metadata: ResultMetadataDict
    required_conditions: tuple[str, ...]
    safe_failure_summary: tuple[str, ...]
    closeout_coverage: tuple[str, ...]
    source: ActiveBoundarySourceDict
    mock_only: bool
    hardware_required: bool
    real_midi: str
    port_opening: str
    active_cli_behavior: str
    dispatch: str
    command_execution: str
    scene_execution: str
    hardware_behavior: str


class ActiveBoundarySummaryDict(TypedDict):
    """Fixed shape of :func:`summarize_active_boundary_report`."""

    title: str
    boundary: str
    supported_candidate: str
    accepted_key: str
    unsupported_keys: tuple[str, ...]
    required_condition_count: int
    mock_only: bool
    active_cli_behavior: str
    hardware_required: bool


UNSUPPORTED_ACTIVE_BOUNDARY_PROFILE_KEYS: Final[tuple[str, ...]] = ("3", "4")
UNSUPPORTED_SOURCE_KINDS: Final[tuple[str, ...]] = ("scene", "command")
RESULT_METADATA_FIELDS: Final[tuple[str, ...]] = (
    "source_kind",
    "source_key",
    "target",
    "armed",
    "dry_run_confirmed",
    "operator_intent",
    "mock_only",
    "sends_real_midi",
)

REQUIRED_CONDITIONS: Final[tuple[str, ...]] = (
    "explicit arming",
    "dry-run confirmation",
    "supported source kind",
    "supported source key",
    "injected MockMidiSender",
)

SAFE_FAILURE_SUMMARY: Final[tuple[str, ...]] = (
    "missing arming emits no messages",
    "missing dry-run confirmation emits no messages",
    "unsupported source kind emits no messages",
    "unsupported or unknown key emits no messages",
    "invalid request or sender type fails before message emission",
)

ACTIVE_BOUNDARY_SAFETY: Final[dict[str, object]] = {
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

ACTIVE_BOUNDARY_CLOSEOUT_COVERAGE: Final[tuple[str, ...]] = (
    "Mock-Only Active Candidate",
    "Active Boundary",
)


def _unsupported_profile_summary(profile_key: str) -> UnsupportedProfileSummaryDict:
    summary = profile_summary_row(profile_key)
    if str(profile_key) == "3":
        reason = "mock mapper/report scope only; not active-boundary supported"
    elif str(profile_key) == "4":
        reason = "parked until separately approved"
    else:
        reason = "unsupported by active boundary"
    return {
        "profile_key": summary["profile_key"],
        "name": summary["name"],
        "group_pad": summary["group_pad"],
        "machine_value": summary["machine_value"],
        "target": summary["target"],
        "reason": reason,
    }


def build_active_boundary_report() -> ActiveBoundaryReportDict:
    """Return copied, in-memory data about current active boundary support."""
    from ...active_boundary import (
        ACTIVE_BOUNDARY_NAME,
        SUPPORTED_CANDIDATE,
        SUPPORTED_SOURCE_KEY,
        SUPPORTED_SOURCE_KIND,
    )

    base_candidate = profile_summary_row(SUPPORTED_SOURCE_KEY)
    accepted_candidate: AcceptedCandidateDict = {
        "profile_key": base_candidate["profile_key"],
        "name": base_candidate["name"],
        "group_pad": base_candidate["group_pad"],
        "machine_value": base_candidate["machine_value"],
        "target": base_candidate["target"],
        "source_kind": SUPPORTED_SOURCE_KIND,
    }

    report: ActiveBoundaryReportDict = {
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


def summarize_active_boundary_report(
    report: ActiveBoundaryReportDict | None = None,
) -> ActiveBoundarySummaryDict:
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


def format_active_boundary_report(
    report: ActiveBoundaryReportDict | None = None,
) -> list[str]:
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
