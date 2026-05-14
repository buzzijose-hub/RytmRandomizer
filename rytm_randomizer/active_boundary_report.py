"""Read-only active boundary report summary.

Thin shim over :mod:`rytm_randomizer.reports`. The report logic was
consolidated into ``reports.py``; this module preserves the original public
names. It reports the current mock-first active boundary state without
evaluating requests, opening ports, sending MIDI, dispatching behavior, wiring
CLI commands, or touching hardware.
"""

from __future__ import annotations

from .reports import (
    ACTIVE_BOUNDARY_CLOSEOUT_COVERAGE as CLOSEOUT_COVERAGE,
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

__all__ = [
    "ACTIVE_BOUNDARY_SAFETY",
    "CLOSEOUT_COVERAGE",
    "REQUIRED_CONDITIONS",
    "RESULT_METADATA_FIELDS",
    "SAFE_FAILURE_SUMMARY",
    "UNSUPPORTED_ACTIVE_BOUNDARY_PROFILE_KEYS",
    "UNSUPPORTED_SOURCE_KINDS",
    "build_active_boundary_report",
    "format_active_boundary_report",
    "summarize_active_boundary_report",
]
