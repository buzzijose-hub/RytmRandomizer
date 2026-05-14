"""Read-only mock mapper report summary.

Thin shim over :mod:`rytm_randomizer.reports`. The report logic was
consolidated into ``reports.py``; this module preserves the original public
names. It is passive and in-memory only: it reports current test-only mock
mapper support without opening ports, sending MIDI, wiring CLI behavior, or
touching hardware.
"""

from __future__ import annotations

from .reports import (
    MOCK_MAPPER_BOUNDARY,
    UNSUPPORTED_SAFE_GROUP_PROFILE_KEYS,
    build_mock_mapper_report,
    format_mock_mapper_report,
    summarize_mock_mapper_report,
)

__all__ = [
    "MOCK_MAPPER_BOUNDARY",
    "UNSUPPORTED_SAFE_GROUP_PROFILE_KEYS",
    "build_mock_mapper_report",
    "format_mock_mapper_report",
    "summarize_mock_mapper_report",
]
