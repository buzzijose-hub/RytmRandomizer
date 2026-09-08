"""Passive runtime-plan report.

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


class RuntimePlanInputDict(TypedDict):
    """One declarative planning input fed to the runtime-intent validator."""

    category: str
    source_kind: str
    source_key: str
    target: str


class RuntimePreviewDict(TypedDict):
    """One previewed runtime intent, flattened for the report."""

    source_kind: str
    source_key: str
    target: str
    source_label: str
    status: str
    reason: str
    reason_code: str
    supported: bool
    parked: bool
    would_execute: bool
    mock_only: bool
    sends_real_midi: bool
    ports_allowed: bool
    hardware_required: bool


class RuntimePlanModeDict(TypedDict):
    """Mode block for the runtime plan report."""

    mock_only: bool
    metadata_only: bool
    blocked_by_default: bool


class RuntimePlanSafetyDict(TypedDict):
    """Safety block for the runtime plan report."""

    would_execute: bool
    mock_only: bool
    sends_real_midi: bool
    ports_allowed: bool
    hardware_required: bool


class RuntimePlanSourceDict(TypedDict):
    """Provenance block for the runtime plan report."""

    runtime_plan_module: str
    in_memory_only: bool


class RuntimePlanReportDict(TypedDict):
    """Fixed shape of :func:`build_runtime_plan_report`.

    The ``runtime_execution`` .. ``hardware_required`` keys are spread in
    from ``RUNTIME_PLAN_REPORT_BOUNDARY``.
    """

    title: str
    mode: RuntimePlanModeDict
    supported_planning_inputs: tuple[RuntimePreviewDict, ...]
    parked_planning_inputs: tuple[RuntimePreviewDict, ...]
    unsupported_planning_inputs: tuple[RuntimePreviewDict, ...]
    reason_codes: tuple[str, ...]
    safety: RuntimePlanSafetyDict
    runtime_execution: str
    cli_execution_wiring: str
    dispatch: str
    command_execution: str
    scene_execution: str
    real_midi: str
    port_opening: str
    hardware_required: bool
    source: RuntimePlanSourceDict


class RuntimePlanSummaryDict(TypedDict):
    """Fixed shape of :func:`summarize_runtime_plan_report`."""

    title: str
    supported_count: int
    parked_count: int
    unsupported_count: int
    reason_codes: tuple[str, ...]
    would_execute: bool
    mock_only: bool
    runtime_execution: str


SUPPORTED_REPORT_INPUTS: Final[tuple[RuntimePlanInputDict, ...]] = (
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

PARKED_REPORT_INPUTS: Final[tuple[RuntimePlanInputDict, ...]] = (
    {
        "category": "parked",
        "source_kind": "group_profile",
        "source_key": "4",
        "target": "Pad 1 / My BD Acoustic",
    },
)

UNSUPPORTED_REPORT_INPUTS: Final[tuple[RuntimePlanInputDict, ...]] = (
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


class RuntimePlanBoundaryDict(TypedDict):
    """Boundary block spread into the report literal."""

    runtime_execution: str
    cli_execution_wiring: str
    dispatch: str
    command_execution: str
    scene_execution: str
    real_midi: str
    port_opening: str
    hardware_required: bool


RUNTIME_PLAN_REPORT_BOUNDARY: Final[RuntimePlanBoundaryDict] = {
    "runtime_execution": "absent",
    "cli_execution_wiring": "absent",
    "dispatch": "absent",
    "command_execution": "absent",
    "scene_execution": "absent",
    "real_midi": "absent",
    "port_opening": "absent",
    "hardware_required": False,
}


def _runtime_preview_summary(report_input: RuntimePlanInputDict) -> RuntimePreviewDict:
    from ...runtime_plan import RuntimeIntent, validate_runtime_intent_scope

    intent = RuntimeIntent(
        source_kind=report_input["source_kind"],
        source_key=report_input["source_key"],
        target=report_input["target"],
    )
    preview = validate_runtime_intent_scope(intent)
    metadata = preview.metadata
    return {
        "source_kind": str(metadata["source_kind"]),
        "source_key": str(metadata["source_key"]),
        "target": str(metadata["target"]),
        "source_label": str(metadata["source_label"]),
        "status": str(preview.status),
        "reason": str(preview.reason),
        "reason_code": str(metadata["reason_code"]),
        "supported": bool(metadata["supported"]),
        "parked": bool(metadata["parked"]),
        "would_execute": bool(metadata["would_execute"]),
        "mock_only": bool(metadata["mock_only"]),
        "sends_real_midi": bool(metadata["sends_real_midi"]),
        "ports_allowed": bool(metadata["ports_allowed"]),
        "hardware_required": bool(metadata["hardware_required"]),
    }


def build_runtime_plan_report() -> RuntimePlanReportDict:
    """Return copied, in-memory data about current runtime plan metadata."""
    report: RuntimePlanReportDict = {
        "title": "RytmRandomizer Runtime Plan Report",
        "mode": {
            "mock_only": True,
            "metadata_only": True,
            "blocked_by_default": True,
        },
        "supported_planning_inputs": tuple(
            _runtime_preview_summary(report_input) for report_input in SUPPORTED_REPORT_INPUTS
        ),
        "parked_planning_inputs": tuple(
            _runtime_preview_summary(report_input) for report_input in PARKED_REPORT_INPUTS
        ),
        "unsupported_planning_inputs": tuple(
            _runtime_preview_summary(report_input) for report_input in UNSUPPORTED_REPORT_INPUTS
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


def summarize_runtime_plan_report(
    report: RuntimePlanReportDict | None = None,
) -> RuntimePlanSummaryDict:
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


def _runtime_input_line(summary: RuntimePreviewDict) -> str:
    return f"- {summary['source_label']} -> {summary['target']} " f"({summary['reason_code']})"


def format_runtime_plan_report(
    report: RuntimePlanReportDict | None = None,
) -> list[str]:
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
        lines.append(_runtime_input_line(summary))

    lines.append("Parked Planning Inputs:")
    for summary in source_report["parked_planning_inputs"]:
        lines.append(_runtime_input_line(summary))

    lines.append("Unsupported Planning Inputs:")
    for summary in source_report["unsupported_planning_inputs"]:
        lines.append(_runtime_input_line(summary))

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
            *passive_footer_lines("runtime_plan"),
        ]
    )
    return lines
