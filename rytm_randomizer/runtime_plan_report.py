"""Read-only runtime plan report summary.

Thin shim over :mod:`rytm_randomizer.reports`. The report logic was
consolidated into ``reports.py``; this module preserves the original public
names. It is passive and in-memory only: it reports current mock-only runtime
plan metadata without opening ports, sending MIDI, wiring CLI execution, or
touching hardware.
"""

from __future__ import annotations

from .reports import (
    PARKED_REPORT_INPUTS,
    RUNTIME_PLAN_REPORT_BOUNDARY,
    SUPPORTED_REPORT_INPUTS,
    UNSUPPORTED_REPORT_INPUTS,
    build_runtime_plan_report,
    format_runtime_plan_report,
    summarize_runtime_plan_report,
)

__all__ = [
    "PARKED_REPORT_INPUTS",
    "RUNTIME_PLAN_REPORT_BOUNDARY",
    "SUPPORTED_REPORT_INPUTS",
    "UNSUPPORTED_REPORT_INPUTS",
    "build_runtime_plan_report",
    "format_runtime_plan_report",
    "summarize_runtime_plan_report",
]
