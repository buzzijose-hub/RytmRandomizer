"""Passive report-only CLI entrypoint for RytmRandomizer."""

import sys

from .registry import get_registry_item
from .registry_report import format_registry_report


USAGE = (
    "Usage: python -m rytm_randomizer.cli [--help] | report | "
    "inspect-command <key> | inspect-scene <key>"
)
TOP_LEVEL_HELP = """RytmRandomizer passive CLI

Usage:
  python -m rytm_randomizer.cli report
  python -m rytm_randomizer.cli inspect-command <key>
  python -m rytm_randomizer.cli inspect-scene <key>
  python -m rytm_randomizer.cli --help

Commands:
  report             Print the passive registry report.
  inspect-command    Inspect passive command metadata by key.
  inspect-scene      Inspect passive scene metadata by key.

Safety:
  passive/read-only
  no MIDI sending
  no port opening
  no command execution
  no hardware mutation
  no hardware required"""
INSPECT_SCENE_HELP = """RytmRandomizer passive CLI: inspect-scene

Usage:
  python -m rytm_randomizer.cli inspect-scene <key>
  python -m rytm_randomizer.cli inspect-scene --help

Behavior:
  Displays passive metadata for an existing scene key.

Safety:
  passive/read-only
  no MIDI sending
  no port opening
  no command execution
  no hardware mutation
  no hardware required"""
INSPECT_COMMAND_HELP = """RytmRandomizer passive CLI: inspect-command

Usage:
  python -m rytm_randomizer.cli inspect-command <key>
  python -m rytm_randomizer.cli inspect-command --help

Behavior:
  Displays passive metadata for an existing command key.

Safety:
  passive/read-only
  no MIDI sending
  no port opening
  no command execution
  no hardware mutation
  no hardware required"""


def format_inspect_command_report(command_key):
    """Return deterministic passive command metadata lines."""
    report = get_registry_item("commands", command_key)
    key = report["key"]

    if not report["exists"]:
        return [
            "RytmRandomizer passive command inspection",
            f"Command: {key}",
            "Found: False",
            "Message: Command metadata not found. No MIDI was sent. No command executed.",
        ]

    metadata = report["metadata"]
    return [
        "RytmRandomizer passive command inspection",
        f"Command: {key}",
        "Found: True",
        f"Type: {metadata.get('type', '')}",
        f"Scope: {metadata.get('scope', '')}",
        f"Pad: {metadata.get('pad', '')}",
        f"Label: {metadata.get('label') or metadata.get('name', '')}",
        f"Executable: {metadata.get('executable')}",
        f"Scaffold only: {metadata.get('scaffold_only')}",
        f"V1.34 reference command: {metadata.get('v134_reference_command')}",
        "Safety:",
        "- passive/read-only",
        "- no MIDI sending",
        "- no port opening",
        "- no command execution",
        "- no hardware mutation",
        "- no hardware required",
    ]


def format_inspect_scene_report(scene_key):
    """Return deterministic passive scene metadata lines."""
    report = get_registry_item("scenes", scene_key)
    key = report["key"]

    if not report["exists"]:
        return [
            "RytmRandomizer passive scene inspection",
            f"Scene: {key}",
            "Found: False",
            "Message: Scene metadata not found. No MIDI was sent. No command executed.",
        ]

    metadata = report["metadata"]
    return [
        "RytmRandomizer passive scene inspection",
        f"Scene: {key}",
        "Found: True",
        f"Name: {metadata.get('name', '')}",
        f"Description: {metadata.get('description', '')}",
        f"Action: {metadata.get('action', '')}",
        f"Scope: {metadata.get('scope', '')}",
        f"Executable: {metadata.get('executable')}",
        f"Scaffold only: {metadata.get('scaffold_only')}",
        f"V1.34 reference command: {metadata.get('v134_reference_command')}",
        "Safety:",
        "- passive/read-only",
        "- no MIDI sending",
        "- no port opening",
        "- no command execution",
        "- no hardware mutation",
        "- no hardware required",
    ]


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

    if args == ["inspect-command", "--help"]:
        sys.stdout.write(f"{INSPECT_COMMAND_HELP}\n")
        return 0

    if args == ["inspect-scene", "--help"]:
        sys.stdout.write(f"{INSPECT_SCENE_HELP}\n")
        return 0

    if args == ["report"]:
        sys.stdout.write("\n".join(format_registry_report()))
        sys.stdout.write("\n")
        return 0

    if len(args) == 2 and args[0] == "inspect-command":
        lines = format_inspect_command_report(args[1])
        output = "\n".join(lines)
        if lines[2] == "Found: True":
            sys.stdout.write(f"{output}\n")
            return 0
        sys.stderr.write(f"{output}\n")
        return 1

    if len(args) == 2 and args[0] == "inspect-scene":
        lines = format_inspect_scene_report(args[1])
        output = "\n".join(lines)
        if lines[2] == "Found: True":
            sys.stdout.write(f"{output}\n")
            return 0
        sys.stderr.write(f"{output}\n")
        return 1

    sys.stderr.write(f"{USAGE}\n")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
