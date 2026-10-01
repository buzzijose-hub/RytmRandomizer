"""Passive behavior-parity coverage report.

Extracted verbatim from the former monolithic ``rytm_randomizer.reports``
module when it reached the 1500-LOC comprehensibility cap (see
``tests/architecture/test_reports_max_module_size.py``). Behavior is
unchanged; the public names are re-exported from ``rytm_randomizer.reports``
so every existing import keeps working.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Final, TypedDict


class SelectedIsolatedPadCoverageDict(TypedDict):
    """One selected-isolated-pad packet coverage row."""

    packet: str
    command_keys: tuple[str, ...]
    coverage: str


class PadLaneCoverageDict(TypedDict):
    """One pad-lane packet coverage row."""

    packet: str
    lane: str
    command_keys: tuple[str, ...]
    deferred_keys: tuple[str, ...]
    coverage: str


class ParityProtectedFileStateDict(TypedDict):
    """Protected-file state block."""

    v134_reference: str
    package_metadata: str
    runtime_execution_logic: str


class ParitySourceDict(TypedDict):
    """Provenance block for the behavior-parity report."""

    plan_document: str
    review_document: str
    report_module: str


class BehaviorParityReportDict(TypedDict):
    """Fixed shape of :func:`build_behavior_parity_coverage_report`.

    The ``read_only`` .. ``hardware_required`` keys are spread in from
    ``PARITY_REPORT_BOUNDARY``.
    """

    title: str
    accepted_packet_coverage: tuple[str, ...]
    selected_isolated_pad_packet_coverage: tuple[SelectedIsolatedPadCoverageDict, ...]
    pad_lane_packet_coverage: tuple[PadLaneCoverageDict, ...]
    runtime_adjacent_mock_only_safe_failures: tuple[str, ...]
    parked_scope: tuple[str, ...]
    absent_behavior: tuple[str, ...]
    closeout_coverage: tuple[str, ...]
    protected_file_state: ParityProtectedFileStateDict
    source: ParitySourceDict
    read_only: bool
    in_memory_only: bool
    cli_visibility: str
    dispatch: str
    command_execution: str
    scene_execution: str
    real_midi: str
    port_opening: str
    active_behavior: str
    hardware_behavior: str
    hardware_required: bool


class BehaviorParitySummaryDict(TypedDict):
    """Fixed shape of :func:`summarize_behavior_parity_coverage_report`."""

    title: str
    accepted_packet_count: int
    selected_isolated_pad_packet_count: int
    pad_lane_packet_count: int
    pad_lane_command_count: int
    runtime_adjacent_safe_failure_count: int
    parked_scope_count: int
    closeout_coverage_count: int
    read_only: bool
    cli_visibility: str
    active_behavior: str
    hardware_required: bool


ACCEPTED_PACKET_COVERAGE: Final[tuple[str, ...]] = (
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
    "Packet 11B PZ selected isolated pad anchor-return readiness",
)

RUNTIME_ADJACENT_MOCK_ONLY_SAFE_FAILURES: Final[tuple[str, ...]] = ("PZ", "B", "L")

PARITY_PARKED_SCOPE: Final[tuple[str, ...]] = (
    "fourth runtime-adjacent candidate",
    "profile 4 mock mapper support",
)

PARITY_ABSENT_BEHAVIOR: Final[tuple[str, ...]] = (
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

PARITY_CLOSEOUT_COVERAGE: Final[tuple[str, ...]] = (
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

PARITY_PROTECTED_FILE_STATE: Final[ParityProtectedFileStateDict] = {
    "v134_reference": "untouched",
    "package_metadata": "untouched",
    "runtime_execution_logic": "absent",
}


class ParityBoundaryDict(TypedDict):
    """Boundary block spread into the report literal."""

    read_only: bool
    in_memory_only: bool
    cli_visibility: str
    dispatch: str
    command_execution: str
    scene_execution: str
    real_midi: str
    port_opening: str
    active_behavior: str
    hardware_behavior: str
    hardware_required: bool


PARITY_REPORT_BOUNDARY: Final[ParityBoundaryDict] = {
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


def _selected_isolated_pad_packet_coverage() -> tuple[SelectedIsolatedPadCoverageDict, ...]:
    from ...behavior.selected_isolated_pad import (
        PACKET_11A_SELECTED_ISOLATED_PAD_KEYS,
        PACKET_11B_SELECTED_ISOLATED_PAD_KEYS,
    )

    return (
        {
            "packet": "11A",
            "command_keys": PACKET_11A_SELECTED_ISOLATED_PAD_KEYS,
            "coverage": "selected isolated pad target intent",
        },
        {
            "packet": "11B",
            "command_keys": PACKET_11B_SELECTED_ISOLATED_PAD_KEYS,
            "coverage": "selected isolated pad anchor-return readiness",
        },
    )


def _pad_lane_packet_coverage() -> tuple[PadLaneCoverageDict, ...]:
    from ...behavior.pad_lane import (
        DEFERRED_PACKET_5_PAD1_LANE_KEYS,
        DEFERRED_PACKET_6_PAD2_LANE_KEYS,
        DEFERRED_PACKET_7_PAD3_LANE_KEYS,
        DEFERRED_PACKET_8_PAD4_LANE_KEYS,
        PACKET_5A_PAD1_CURRENT_ENGINE_KEYS,
        PACKET_5B_PAD1_BD_FM_KEYS,
        PACKET_5C_PAD1_BD_PLASTIC_KEYS,
        PACKET_5D_PAD1_BD_SILKY_KEYS,
        PACKET_5E_PAD1_BD_ACOUSTIC_KEYS,
        PACKET_6A_PAD2_LANE_KEYS,
        PACKET_6B_PAD2_LANE_KEYS,
        PACKET_6C_PAD2_LANE_KEYS,
        PACKET_6D_PAD2_LANE_KEYS,
        PACKET_6E_PAD2_LANE_KEYS,
        PACKET_6F_PAD2_LANE_KEYS,
        PACKET_6G_PAD2_LANE_KEYS,
        PACKET_6H_PAD2_LANE_KEYS,
        PACKET_6I_PAD2_LANE_KEYS,
        PACKET_6J_PAD2_LANE_KEYS,
        PACKET_7A_PAD3_LANE_KEYS,
        PACKET_7B_PAD3_LANE_KEYS,
        PACKET_7C_PAD3_LANE_KEYS,
        PACKET_7D_PAD3_LANE_KEYS,
        PACKET_7E_PAD3_LANE_KEYS,
        PACKET_7F_PAD3_LANE_KEYS,
        PACKET_7G_PAD3_LANE_KEYS,
        PACKET_7H_PAD3_LANE_KEYS,
        PACKET_8A_PAD4_LANE_KEYS,
        PACKET_8B_PAD4_LANE_KEYS,
        PACKET_8C_PAD4_LANE_KEYS,
    )

    return (
        {
            "packet": "5",
            "lane": "Pad 1 BD lane family",
            "command_keys": (
                PACKET_5A_PAD1_CURRENT_ENGINE_KEYS
                + PACKET_5B_PAD1_BD_FM_KEYS
                + PACKET_5C_PAD1_BD_PLASTIC_KEYS
                + PACKET_5D_PAD1_BD_SILKY_KEYS
                + PACKET_5E_PAD1_BD_ACOUSTIC_KEYS
            ),
            "deferred_keys": DEFERRED_PACKET_5_PAD1_LANE_KEYS,
            "coverage": "Pad 1 lane behavior for the current read-only phase",
        },
        {
            "packet": "6",
            "lane": "Pad 2 secondary lane",
            "command_keys": (
                PACKET_6A_PAD2_LANE_KEYS
                + PACKET_6B_PAD2_LANE_KEYS
                + PACKET_6C_PAD2_LANE_KEYS
                + PACKET_6D_PAD2_LANE_KEYS
                + PACKET_6E_PAD2_LANE_KEYS
                + PACKET_6F_PAD2_LANE_KEYS
                + PACKET_6G_PAD2_LANE_KEYS
                + PACKET_6H_PAD2_LANE_KEYS
                + PACKET_6I_PAD2_LANE_KEYS
                + PACKET_6J_PAD2_LANE_KEYS
            ),
            "deferred_keys": DEFERRED_PACKET_6_PAD2_LANE_KEYS,
            "coverage": "Pad 2 lane behavior for the current read-only phase",
        },
        {
            "packet": "7",
            "lane": "Pad 3 SY Raw lane",
            "command_keys": (
                PACKET_7A_PAD3_LANE_KEYS
                + PACKET_7B_PAD3_LANE_KEYS
                + PACKET_7C_PAD3_LANE_KEYS
                + PACKET_7D_PAD3_LANE_KEYS
                + PACKET_7E_PAD3_LANE_KEYS
                + PACKET_7F_PAD3_LANE_KEYS
                + PACKET_7G_PAD3_LANE_KEYS
                + PACKET_7H_PAD3_LANE_KEYS
            ),
            "deferred_keys": DEFERRED_PACKET_7_PAD3_LANE_KEYS,
            "coverage": "Pad 3 lane behavior for the current read-only phase",
        },
        {
            "packet": "8",
            "lane": "Pad 4 BD Acoustic lane",
            "command_keys": (
                PACKET_8A_PAD4_LANE_KEYS + PACKET_8B_PAD4_LANE_KEYS + PACKET_8C_PAD4_LANE_KEYS
            ),
            "deferred_keys": DEFERRED_PACKET_8_PAD4_LANE_KEYS,
            "coverage": "Pad 4 command-helper scope for the current read-only phase",
        },
    )


def build_behavior_parity_coverage_report() -> BehaviorParityReportDict:
    """Return copied, in-memory data about current behavior-parity coverage."""
    report: BehaviorParityReportDict = {
        "title": "V1.34 Behavior Parity Coverage Report",
        "accepted_packet_coverage": tuple(ACCEPTED_PACKET_COVERAGE),
        "selected_isolated_pad_packet_coverage": deepcopy(_selected_isolated_pad_packet_coverage()),
        "pad_lane_packet_coverage": deepcopy(_pad_lane_packet_coverage()),
        "runtime_adjacent_mock_only_safe_failures": tuple(RUNTIME_ADJACENT_MOCK_ONLY_SAFE_FAILURES),
        "parked_scope": tuple(PARITY_PARKED_SCOPE),
        "absent_behavior": tuple(PARITY_ABSENT_BEHAVIOR),
        "closeout_coverage": tuple(PARITY_CLOSEOUT_COVERAGE),
        "protected_file_state": deepcopy(PARITY_PROTECTED_FILE_STATE),
        "source": {
            "plan_document": ("Docs/V134_BEHAVIOR_PARITY_PACKET_12_COVERAGE_REPORT_PLAN.md"),
            "review_document": (
                "Docs/V134_BEHAVIOR_PARITY_PACKET_12_COVERAGE_REPORT_PLAN_REVIEW.md"
            ),
            "report_module": "rytm_randomizer.reports",
        },
        **PARITY_REPORT_BOUNDARY,
    }
    return deepcopy(report)


def summarize_behavior_parity_coverage_report(
    report: BehaviorParityReportDict | None = None,
) -> BehaviorParitySummaryDict:
    """Return a compact copied summary of the behavior-parity coverage report."""
    source_report = build_behavior_parity_coverage_report() if report is None else report
    return {
        "title": source_report["title"],
        "accepted_packet_count": len(source_report["accepted_packet_coverage"]),
        "selected_isolated_pad_packet_count": len(
            source_report["selected_isolated_pad_packet_coverage"]
        ),
        "pad_lane_packet_count": len(source_report["pad_lane_packet_coverage"]),
        "pad_lane_command_count": sum(
            len(item["command_keys"]) for item in source_report["pad_lane_packet_coverage"]
        ),
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


def format_behavior_parity_coverage_report(
    report: BehaviorParityReportDict | None = None,
) -> list[str]:
    """Return deterministic human-readable behavior-parity coverage lines."""
    source_report = build_behavior_parity_coverage_report() if report is None else report
    lines = [
        source_report["title"],
        "Accepted Packet Coverage:",
    ]

    for item in source_report["accepted_packet_coverage"]:
        lines.append(f"- {item}")

    lines.append("Selected Isolated Pad Packet Coverage:")
    for item in source_report["selected_isolated_pad_packet_coverage"]:
        command_keys = ", ".join(item["command_keys"])
        lines.append(f"- Packet {item['packet']}: {command_keys} - {item['coverage']}")

    lines.append("Pad Lane Packet Coverage:")
    for item in source_report["pad_lane_packet_coverage"]:
        command_keys = ", ".join(item["command_keys"])
        lines.append(
            f"- Packet {item['packet']}: {item['lane']} - " f"{command_keys} - {item['coverage']}"
        )
        deferred_keys = ", ".join(item["deferred_keys"]) or "none"
        lines.append(f"- Packet {item['packet']} deferred/safe: {deferred_keys}")

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
