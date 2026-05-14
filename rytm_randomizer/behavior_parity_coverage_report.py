"""Read-only behavior-parity coverage report.

Thin shim over :mod:`rytm_randomizer.reports`. The report logic was
consolidated into ``reports.py``; this module preserves the original public
names. It summarizes accepted behavior-parity coverage in memory only. It does
not import MIDI libraries, open ports, send MIDI, wire CLI behavior, dispatch
commands, execute runtime behavior, or touch hardware.
"""

from __future__ import annotations

from .reports import (
    ACCEPTED_PACKET_COVERAGE,
    RUNTIME_ADJACENT_MOCK_ONLY_SAFE_FAILURES,
    build_behavior_parity_coverage_report,
    format_behavior_parity_coverage_report,
    summarize_behavior_parity_coverage_report,
)

__all__ = [
    "ACCEPTED_PACKET_COVERAGE",
    "RUNTIME_ADJACENT_MOCK_ONLY_SAFE_FAILURES",
    "build_behavior_parity_coverage_report",
    "format_behavior_parity_coverage_report",
    "summarize_behavior_parity_coverage_report",
]
