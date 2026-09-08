"""Passive mock-runtime active-bridge report + CLI command entries.

Extracted verbatim from the former monolithic ``rytm_randomizer.reports``
module when it reached the 1500-LOC comprehensibility cap (see
``tests/architecture/test_reports_max_module_size.py``). Behavior is
unchanged; the public names are re-exported from ``rytm_randomizer.reports``
so every existing import keeps working.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Final, TypedDict

from ...cli_registry import CliCommand, make_passive_report_command
from ..formatter import passive_footer_lines
from .active_boundary import format_active_boundary_report
from .mock_mapper import format_mock_mapper_report
from .runtime_plan import format_runtime_plan_report


class BridgeModeDict(TypedDict):
    """What the bridge report does and does not do."""

    read_only: bool
    mock_only: bool
    metadata_only: bool
    invokes_bridge: bool
    constructs_sender: bool
    emits_messages: bool


class BridgeContractDict(TypedDict):
    """The bridge module's evaluator contract."""

    module: str
    evaluator: str
    request_type: str
    result_type: str


class BridgeAcceptedCandidateDict(TypedDict):
    """The single accepted bridge candidate."""

    source_kind: str
    source_key: str
    source_name: str
    target: str
    sender: str
    requires_armed: bool
    requires_dry_run_confirmed: bool


class BridgeRejectedCaseDict(TypedDict):
    """One rejected bridge case."""

    case: str
    description: str
    emits_messages: bool


class BridgeParkedCaseDict(TypedDict):
    """One parked bridge case."""

    case: str
    source_kind: str
    source_key: str
    source_name: str
    reason: str
    emits_messages: bool


class BridgeSafetyDict(TypedDict):
    """Safety block for the bridge report."""

    runtime_execution: str
    cli_execution_wiring: str
    dispatch: str
    real_midi: str
    port_opening: str
    active_behavior: str
    hardware_behavior: str
    hardware_required: bool


class BridgeSourceDict(TypedDict):
    """Provenance block for the bridge report."""

    bridge_module: str
    in_memory_only: bool


class BridgeReportDict(TypedDict):
    """Fixed shape of :func:`build_mock_runtime_active_bridge_report`."""

    title: str
    mode: BridgeModeDict
    bridge: BridgeContractDict
    accepted_candidate: BridgeAcceptedCandidateDict
    rejected_cases: tuple[BridgeRejectedCaseDict, ...]
    parked_cases: tuple[BridgeParkedCaseDict, ...]
    safety: BridgeSafetyDict
    source: BridgeSourceDict


class BridgeSummaryDict(TypedDict):
    """Fixed shape of :func:`summarize_mock_runtime_active_bridge_report`."""

    title: str
    accepted_source_key: str
    rejected_count: int
    parked_count: int
    read_only: bool
    mock_only: bool
    invokes_bridge: bool
    constructs_sender: bool
    emits_messages: bool


REPORT_MODE: Final[dict[str, bool]] = {
    "read_only": True,
    "mock_only": True,
    "metadata_only": True,
    "invokes_bridge": False,
    "constructs_sender": False,
    "emits_messages": False,
}

BRIDGE_SUMMARY: Final[dict[str, str]] = {
    "module": "rytm_randomizer.mock_runtime_active_bridge",
    "request_type": "RuntimeActiveBridgeRequest",
    "result_type": "RuntimeActiveBridgeResult",
    "evaluator": "evaluate_mock_runtime_active_bridge",
}

ACCEPTED_CANDIDATE: Final[dict[str, object]] = {
    "source_kind": "group_profile",
    "source_key": "2",
    "source_name": "My BD Hard",
    "target": "Pad 1 / BD Hard",
    "requires_armed": True,
    "requires_dry_run_confirmed": True,
    "sender": "MockMidiSender",
}

REJECTED_CASES: Final[tuple[dict[str, object], ...]] = (
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

PARKED_CASES: Final[tuple[dict[str, object], ...]] = (
    {
        "case": "profile_4_parked",
        "source_kind": "group_profile",
        "source_key": "4",
        "source_name": "My BD Acoustic",
        "emits_messages": False,
        "reason": "parked until separately approved",
    },
)

SAFETY_BOUNDARY: Final[dict[str, object]] = {
    "real_midi": "absent",
    "port_opening": "absent",
    "hardware_required": False,
    "cli_execution_wiring": "absent",
    "runtime_execution": "absent",
    "dispatch": "absent",
    "active_behavior": "absent",
    "hardware_behavior": "absent",
}


def build_mock_runtime_active_bridge_report() -> BridgeReportDict:
    """Return copied, in-memory data about the current bridge report contract."""
    report: BridgeReportDict = {
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


def summarize_mock_runtime_active_bridge_report(
    report: BridgeReportDict | None = None,
) -> BridgeSummaryDict:
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


def _bridge_rejected_case_line(rejected_case: BridgeRejectedCaseDict) -> str:
    if rejected_case["case"] == "profile_3_bridge_rejected":
        return (
            f"- {rejected_case['source_kind']}:{rejected_case['source_key']} / "
            f"{rejected_case['source_name']}: bridge rejected"
        )
    return f"- {rejected_case['case']}: {rejected_case['description']}"


def _bridge_parked_case_line(parked_case: BridgeParkedCaseDict) -> str:
    return (
        f"- {parked_case['source_kind']}:{parked_case['source_key']} / "
        f"{parked_case['source_name']}: {parked_case['reason']}"
    )


def format_mock_runtime_active_bridge_report(
    report: BridgeReportDict | None = None,
) -> list[str]:
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


MOCK_MAPPER_REPORT_CLI_COMMAND: Final[CliCommand] = make_passive_report_command(
    "mock-mapper-report",
    "Print the passive mock message mapper report.",
    format_lines=format_mock_mapper_report,
    json_flag=False,
    error_formatter=None,
)


RUNTIME_PLAN_REPORT_CLI_COMMAND: Final[CliCommand] = make_passive_report_command(
    "runtime-plan-report",
    "Print the passive runtime plan report.",
    format_lines=format_runtime_plan_report,
    json_flag=False,
    error_formatter=None,
)


ACTIVE_BOUNDARY_REPORT_CLI_COMMAND: Final[CliCommand] = make_passive_report_command(
    "active-boundary-report",
    "Print the passive active boundary report.",
    format_lines=format_active_boundary_report,
    json_flag=False,
    error_formatter=None,
)
