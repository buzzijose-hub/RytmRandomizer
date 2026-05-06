"""Passive report-only CLI entrypoint for RytmRandomizer."""

import sys

from .registry_report import format_registry_report


USAGE = "Usage: python -m rytm_randomizer.cli report"
TOP_LEVEL_HELP = """RytmRandomizer passive CLI

Usage:
  python -m rytm_randomizer.cli report
  python -m rytm_randomizer.cli --help

Commands:
  report    Print the passive registry report.

Safety:
  passive/read-only
  no MIDI sending
  no port opening
  no command execution
  no hardware mutation
  no hardware required"""
REPORT_HELP = """RytmRandomizer passive CLI: report

Usage:
  python -m rytm_randomizer.cli report
  python -m rytm_randomizer.cli report --help

Behavior:
  Prints the deterministic passive registry report to stdout.

Safety:
  passive/read-only
  no MIDI sending
  no port opening
  no command execution
  no hardware mutation
  no hardware required"""


def main(argv=None):
    """Run the passive report-only CLI."""
    args = sys.argv[1:] if argv is None else list(argv)

    if args == ["--help"]:
        sys.stdout.write(f"{TOP_LEVEL_HELP}\n")
        return 0

    if args == ["report", "--help"]:
        sys.stdout.write(f"{REPORT_HELP}\n")
        return 0

    if args == ["report"]:
        sys.stdout.write("\n".join(format_registry_report()))
        sys.stdout.write("\n")
        return 0

    sys.stderr.write(f"{USAGE}\n")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
