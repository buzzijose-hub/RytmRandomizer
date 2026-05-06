"""Passive report-only CLI entrypoint for RytmRandomizer."""

import sys

from .registry_report import format_registry_report


USAGE = "Usage: python -m rytm_randomizer.cli report"


def main(argv=None):
    """Run the passive report-only CLI."""
    args = sys.argv[1:] if argv is None else list(argv)

    if args == ["report"]:
        sys.stdout.write("\n".join(format_registry_report()))
        sys.stdout.write("\n")
        return 0

    sys.stderr.write(f"{USAGE}\n")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
