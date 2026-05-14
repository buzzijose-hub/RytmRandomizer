"""Read-only anchor/profile behavior report summary.

Thin shim over :mod:`rytm_randomizer.reports`. The report logic was
consolidated into ``reports.py``; this module preserves the original public
names. It summarizes existing passive anchor/profile-related behavior without
calling CLI entry points, opening ports, sending MIDI, dispatching commands,
creating runtime state, or touching hardware.
"""

from __future__ import annotations

from .reports import (
    ANCHOR_PROFILE_CLOSEOUT_COVERAGE as CLOSEOUT_COVERAGE,
    ANCHOR_PROFILE_PARKED_SECTIONS as PARKED_SECTIONS,
    ANCHOR_PROFILE_REPORT_TITLE as REPORT_TITLE,
    ANCHOR_PROFILE_SAFETY,
    build_anchor_profile_report,
    format_anchor_profile_report,
    summarize_anchor_profile_report,
)

__all__ = [
    "ANCHOR_PROFILE_SAFETY",
    "CLOSEOUT_COVERAGE",
    "PARKED_SECTIONS",
    "REPORT_TITLE",
    "build_anchor_profile_report",
    "format_anchor_profile_report",
    "summarize_anchor_profile_report",
]
