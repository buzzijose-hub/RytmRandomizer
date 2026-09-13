"""Consolidated passive, in-memory report layer for RytmRandomizer.

Every report is passive and in-memory only: building or formatting a report
opens no ports, sends no MIDI, dispatches no commands, wires no active CLI
behavior, and touches no hardware.

This module is a **facade**. The report builders/formatters live in focused
sibling modules under ``_core/`` -- the monolithic implementation reached the
1500-LOC comprehensibility cap enforced by
``tests/architecture/test_reports_max_module_size.py``, and was split rather
than grandfathered. Every public name keeps its original import path, so
``from rytm_randomizer.reports import build_registry_report`` still works.

Heavy or behavior-specific dependencies stay imported lazily inside builders
so importing this module remains side-effect free and does not pull in MIDI
libraries, bridge modules, or behavior evaluators.
"""

from __future__ import annotations

from ._core.active_boundary import (
    ACTIVE_BOUNDARY_CLOSEOUT_COVERAGE,
    ACTIVE_BOUNDARY_SAFETY,
    REQUIRED_CONDITIONS,
    RESULT_METADATA_FIELDS,
    SAFE_FAILURE_SUMMARY,
    UNSUPPORTED_ACTIVE_BOUNDARY_PROFILE_KEYS,
    UNSUPPORTED_SOURCE_KINDS,
    build_active_boundary_report,
    format_active_boundary_report,
    summarize_active_boundary_report,
)
from ._core.anchor_profile import (
    ANCHOR_PROFILE_CLOSEOUT_COVERAGE,
    ANCHOR_PROFILE_PARKED_SECTIONS,
    ANCHOR_PROFILE_REPORT_TITLE,
    ANCHOR_PROFILE_SAFETY,
    build_anchor_profile_report,
    format_anchor_profile_report,
    summarize_anchor_profile_report,
)
from ._core.behavior_parity import (
    ACCEPTED_PACKET_COVERAGE,
    PARITY_ABSENT_BEHAVIOR,
    PARITY_CLOSEOUT_COVERAGE,
    PARITY_PARKED_SCOPE,
    PARITY_PROTECTED_FILE_STATE,
    PARITY_REPORT_BOUNDARY,
    RUNTIME_ADJACENT_MOCK_ONLY_SAFE_FAILURES,
    build_behavior_parity_coverage_report,
    format_behavior_parity_coverage_report,
    summarize_behavior_parity_coverage_report,
)
from ._core.bridge import (
    ACCEPTED_CANDIDATE,
    ACTIVE_BOUNDARY_REPORT_CLI_COMMAND,
    BRIDGE_SUMMARY,
    MOCK_MAPPER_REPORT_CLI_COMMAND,
    PARKED_CASES,
    REJECTED_CASES,
    REPORT_MODE,
    RUNTIME_PLAN_REPORT_CLI_COMMAND,
    SAFETY_BOUNDARY,
    build_mock_runtime_active_bridge_report,
    format_mock_runtime_active_bridge_report,
    summarize_mock_runtime_active_bridge_report,
)
from ._core.mock_mapper import (
    MOCK_MAPPER_BOUNDARY,
    UNSUPPORTED_SAFE_GROUP_PROFILE_KEYS,
    build_mock_mapper_report,
    format_mock_mapper_report,
    summarize_mock_mapper_report,
)
from ._core.registry import (
    ACTIVE_BEHAVIOR_STATUS,
    SAFETY_BOUNDARIES,
    UNSUPPORTED_SCOPE,
    build_registry_report,
    format_registry_report,
    summarize_registry_report,
)
from ._core.runtime_plan import (
    PARKED_REPORT_INPUTS,
    RUNTIME_PLAN_REPORT_BOUNDARY,
    SUPPORTED_REPORT_INPUTS,
    UNSUPPORTED_REPORT_INPUTS,
    build_runtime_plan_report,
    format_runtime_plan_report,
    summarize_runtime_plan_report,
)
from .formatter import passive_footer_lines, safety_section_lines  # noqa: F401
from .oxi_live_macro_catalog import (  # noqa: F401
    build_oxi_live_macro_catalog_payload,
    build_oxi_live_macro_catalog_report,
    format_oxi_live_macro_catalog_report,
)
from .oxi_live_set_strategy import (  # noqa: F401
    build_oxi_live_set_strategy_payload,
    build_oxi_live_set_strategy_report,
    format_oxi_live_set_strategy_report,
)
from .rytm_machine_matrix import (  # noqa: F401
    build_rytm_machine_matrix_report,
    format_rytm_machine_matrix_report,
)
from .rytm_snapshot_pad_compatibility import (  # noqa: F401
    build_rytm_snapshot_pad_compatibility_report,
    format_rytm_snapshot_pad_compatibility_report,
)

__all__ = [
    "ACCEPTED_CANDIDATE",
    "ACCEPTED_PACKET_COVERAGE",
    "ACTIVE_BEHAVIOR_STATUS",
    "ACTIVE_BOUNDARY_CLOSEOUT_COVERAGE",
    "ACTIVE_BOUNDARY_REPORT_CLI_COMMAND",
    "ACTIVE_BOUNDARY_SAFETY",
    "ANCHOR_PROFILE_CLOSEOUT_COVERAGE",
    "ANCHOR_PROFILE_PARKED_SECTIONS",
    "ANCHOR_PROFILE_REPORT_TITLE",
    "ANCHOR_PROFILE_SAFETY",
    "BRIDGE_SUMMARY",
    "MOCK_MAPPER_BOUNDARY",
    "MOCK_MAPPER_REPORT_CLI_COMMAND",
    "PARITY_ABSENT_BEHAVIOR",
    "PARITY_CLOSEOUT_COVERAGE",
    "PARITY_PARKED_SCOPE",
    "PARITY_PROTECTED_FILE_STATE",
    "PARITY_REPORT_BOUNDARY",
    "PARKED_CASES",
    "PARKED_REPORT_INPUTS",
    "REJECTED_CASES",
    "REPORT_MODE",
    "REQUIRED_CONDITIONS",
    "RESULT_METADATA_FIELDS",
    "RUNTIME_ADJACENT_MOCK_ONLY_SAFE_FAILURES",
    "RUNTIME_PLAN_REPORT_BOUNDARY",
    "RUNTIME_PLAN_REPORT_CLI_COMMAND",
    "SAFETY_BOUNDARIES",
    "SAFETY_BOUNDARY",
    "SAFE_FAILURE_SUMMARY",
    "SUPPORTED_REPORT_INPUTS",
    "UNSUPPORTED_ACTIVE_BOUNDARY_PROFILE_KEYS",
    "UNSUPPORTED_REPORT_INPUTS",
    "UNSUPPORTED_SAFE_GROUP_PROFILE_KEYS",
    "UNSUPPORTED_SCOPE",
    "UNSUPPORTED_SOURCE_KINDS",
    "build_active_boundary_report",
    "build_anchor_profile_report",
    "build_behavior_parity_coverage_report",
    "build_mock_mapper_report",
    "build_mock_runtime_active_bridge_report",
    "build_oxi_live_macro_catalog_payload",
    "build_oxi_live_macro_catalog_report",
    "build_oxi_live_set_strategy_payload",
    "build_oxi_live_set_strategy_report",
    "build_registry_report",
    "build_runtime_plan_report",
    "build_rytm_machine_matrix_report",
    "build_rytm_snapshot_pad_compatibility_report",
    "format_active_boundary_report",
    "format_anchor_profile_report",
    "format_behavior_parity_coverage_report",
    "format_mock_mapper_report",
    "format_mock_runtime_active_bridge_report",
    "format_oxi_live_macro_catalog_report",
    "format_oxi_live_set_strategy_report",
    "format_registry_report",
    "format_runtime_plan_report",
    "format_rytm_machine_matrix_report",
    "format_rytm_snapshot_pad_compatibility_report",
    "passive_footer_lines",
    "safety_section_lines",
    "summarize_active_boundary_report",
    "summarize_anchor_profile_report",
    "summarize_behavior_parity_coverage_report",
    "summarize_mock_mapper_report",
    "summarize_mock_runtime_active_bridge_report",
    "summarize_registry_report",
    "summarize_runtime_plan_report",
]
