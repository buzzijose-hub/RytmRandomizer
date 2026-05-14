"""Read-only mock runtime/active bridge report summary.

Thin shim over :mod:`rytm_randomizer.reports`. The report logic was
consolidated into ``reports.py``; this module preserves the original public
names. It is passive and in-memory only: it reports the accepted mock
runtime/active bridge contract without invoking the bridge, constructing a
sender, emitting messages, opening ports, sending MIDI, wiring CLI execution,
or touching hardware.
"""

from __future__ import annotations

from .reports import (
    ACCEPTED_CANDIDATE,
    BRIDGE_SUMMARY,
    PARKED_CASES,
    REJECTED_CASES,
    REPORT_MODE,
    SAFETY_BOUNDARY,
    build_mock_runtime_active_bridge_report,
    format_mock_runtime_active_bridge_report,
    summarize_mock_runtime_active_bridge_report,
)

__all__ = [
    "ACCEPTED_CANDIDATE",
    "BRIDGE_SUMMARY",
    "PARKED_CASES",
    "REJECTED_CASES",
    "REPORT_MODE",
    "SAFETY_BOUNDARY",
    "build_mock_runtime_active_bridge_report",
    "format_mock_runtime_active_bridge_report",
    "summarize_mock_runtime_active_bridge_report",
]
