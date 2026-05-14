"""Passive in-memory reports for the unified registry view.

Thin shim over :mod:`rytm_randomizer.reports`. The report logic was
consolidated into ``reports.py``; this module preserves the original public
names and the ``python -m rytm_randomizer.registry_report`` entry point.
"""

from .reports import (
    ACTIVE_BEHAVIOR_STATUS,
    SAFETY_BOUNDARIES,
    UNSUPPORTED_SCOPE,
    build_registry_report,
    format_registry_report,
    registry_report_main as main,
    summarize_registry_report,
)

__all__ = [
    "ACTIVE_BEHAVIOR_STATUS",
    "SAFETY_BOUNDARIES",
    "UNSUPPORTED_SCOPE",
    "build_registry_report",
    "format_registry_report",
    "main",
    "summarize_registry_report",
]


if __name__ == "__main__":
    raise SystemExit(main())
