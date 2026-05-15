"""Passive in-memory reports for the unified registry view.

Thin shim over :mod:`rytm_randomizer.reports`. The report logic was
consolidated into ``reports.py``; this module preserves the original public
names and the ``python -m rytm_randomizer.registry_report`` entry point.

TODO: migrate callers and delete this shim. Unlike the other report shims
removed alongside the WS-P consolidation, this module is retained because
its ``__main__`` block provides the
``python -m rytm_randomizer.registry_report`` CLI entry point used by
``tests/test_registry_report_cli.py`` and ``Scripts/closeout_check.ps1``.
The consolidated ``rytm_randomizer.reports`` module does not currently
expose an equivalent ``__main__`` block, and giving it one would
asymmetrically pick the registry report out of seven report builders as
the package's default ``python -m rytm_randomizer.reports`` behavior.
Delete this module once the registry CLI entry point has been re-homed
(for example as ``python -m rytm_randomizer.reports registry`` or via a
``rytm_randomizer.__main__``).
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
