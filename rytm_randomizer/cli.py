"""Passive report-only CLI entrypoint for RytmRandomizer."""

import sys

from .registry import get_registry_item, get_registry_section
from .registry_report import format_registry_report


USAGE = (
    "Usage: python -m rytm_randomizer.cli [--help] | report | "
    "inspect-command <key> | inspect-scene <key> | inspect-group-profile <key> | "
    "list-commands | list-scenes | list-group-profiles"
)
TOP_LEVEL_HELP = """RytmRandomizer passive CLI

Usage:
  python -m rytm_randomizer.cli report
  python -m rytm_randomizer.cli inspect-command <key>
  python -m rytm_randomizer.cli inspect-scene <key>
  python -m rytm_randomizer.cli inspect-group-profile <key>
  python -m rytm_randomizer.cli list-commands
  python -m rytm_randomizer.cli list-scenes
  python -m rytm_randomizer.cli list-group-profiles
  python -m rytm_randomizer.cli --help

Commands:
  report             Print the passive registry report.
  inspect-command    Inspect passive command metadata by key.
  inspect-scene      Inspect passive scene metadata by key.
  inspect-group-profile
                     Inspect passive group profile metadata by key.
  list-commands      List passive command keys and labels.
  list-scenes        List passive scene keys and names.
  list-group-profiles
                     List passive group profile keys and names.

Safety:
  passive/read-only
  no MIDI sending
  no port opening
  no command execution
  no hardware mutation
  no hardware required"""
LIST_GROUP_PROFILES_HELP = """RytmRandomizer passive CLI: list-group-profiles

Usage:
  python -m rytm_randomizer.cli list-group-profiles
  python -m rytm_randomizer.cli list-group-profiles --help

Behavior:
  Lists existing passive group profile keys and names.

Safety:
  passive/read-only
  no MIDI sending
  no port opening
  no command execution
  no hardware mutation
  no hardware required"""
LIST_SCENES_HELP = """RytmRandomizer passive CLI: list-scenes

Usage:
  python -m rytm_randomizer.cli list-scenes
  python -m rytm_randomizer.cli list-scenes --help

Behavior:
  Lists existing passive scene keys and names.

Safety:
  passive/read-only
  no MIDI sending
  no port opening
  no command execution
  no hardware mutation
  no hardware required"""
LIST_COMMANDS_HELP = """RytmRandomizer passive CLI: list-commands

Usage:
  python -m rytm_randomizer.cli list-commands
  python -m rytm_randomizer.cli list-commands --help

Behavior:
  Lists existing passive command keys and labels.

Safety:
  passive/read-only
  no MIDI sending
  no port opening
  no command execution
  no hardware mutation
  no hardware required"""
INSPECT_GROUP_PROFILE_HELP = """RytmRandomizer passive CLI: inspect-group-profile

Usage:
  python -m rytm_randomizer.cli inspect-group-profile <key>
  python -m rytm_randomizer.cli inspect-group-profile --help

Behavior:
  Displays passive metadata for an existing group profile key.

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


def _format_list_label(metadata):
    return metadata.get("label") or metadata.get("name") or ""


def format_registry_list_report(section_name, title):
    """Return deterministic passive registry list lines."""
    report = get_registry_section(section_name)
    if not report["exists"]:
        return [
            f"RytmRandomizer passive {title}",
            f"Section: {report['section']}",
            "Found: False",
            "Message: Registry section not found. No MIDI was sent. No command executed.",
        ]

    items = report["items"]
    lines = [
        f"RytmRandomizer passive {title}",
        f"Section: {report['section']}",
        f"Count: {report['count']}",
        "Items:",
    ]
    for key in sorted(items):
        label = _format_list_label(items[key])
        lines.append(f"- {key}: {label}")

    lines.extend(
        [
            "Safety:",
            "- passive/read-only",
            "- no MIDI sending",
            "- no port opening",
            "- no command execution",
            "- no hardware mutation",
            "- no hardware required",
        ]
    )
    return lines


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


def format_inspect_group_profile_report(profile_key):
    """Return deterministic passive group profile metadata lines."""
    report = get_registry_item("group_profiles", profile_key)
    key = report["key"]

    if not report["exists"]:
        return [
            "RytmRandomizer passive group profile inspection",
            f"Group profile: {key}",
            "Found: False",
            "Message: Group profile metadata not found. No MIDI was sent. No command executed.",
        ]

    metadata = report["metadata"]
    return [
        "RytmRandomizer passive group profile inspection",
        f"Group profile: {key}",
        "Found: True",
        f"Name: {metadata.get('name', '')}",
        f"Machine value: {metadata.get('machine_value', '')}",
        f"Group pad: {metadata.get('group_pad', '')}",
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

    if args == ["list-commands", "--help"]:
        sys.stdout.write(f"{LIST_COMMANDS_HELP}\n")
        return 0

    if args == ["list-scenes", "--help"]:
        sys.stdout.write(f"{LIST_SCENES_HELP}\n")
        return 0

    if args == ["list-group-profiles", "--help"]:
        sys.stdout.write(f"{LIST_GROUP_PROFILES_HELP}\n")
        return 0

    if args == ["inspect-command", "--help"]:
        sys.stdout.write(f"{INSPECT_COMMAND_HELP}\n")
        return 0

    if args == ["inspect-scene", "--help"]:
        sys.stdout.write(f"{INSPECT_SCENE_HELP}\n")
        return 0

    if args == ["inspect-group-profile", "--help"]:
        sys.stdout.write(f"{INSPECT_GROUP_PROFILE_HELP}\n")
        return 0

    if args == ["report"]:
        sys.stdout.write("\n".join(format_registry_report()))
        sys.stdout.write("\n")
        return 0

    if args == ["list-commands"]:
        sys.stdout.write("\n".join(format_registry_list_report("commands", "command list")))
        sys.stdout.write("\n")
        return 0

    if args == ["list-scenes"]:
        sys.stdout.write("\n".join(format_registry_list_report("scenes", "scene list")))
        sys.stdout.write("\n")
        return 0

    if args == ["list-group-profiles"]:
        sys.stdout.write(
            "\n".join(
                format_registry_list_report("group_profiles", "group profile list")
            )
        )
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

    if len(args) == 2 and args[0] == "inspect-group-profile":
        lines = format_inspect_group_profile_report(args[1])
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
