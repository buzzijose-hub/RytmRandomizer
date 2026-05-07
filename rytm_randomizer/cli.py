"""Passive report-only CLI entrypoint for RytmRandomizer."""

import sys

from .active_boundary_report import format_active_boundary_report
from .preview import preview_command
from .registry import get_registry_item, get_registry_section
from .mock_mapper_report import format_mock_mapper_report
from .registry_report import format_registry_report


USAGE = (
    "Usage: python -m rytm_randomizer.cli [--help] | report | "
    "mock-mapper-report | active-boundary-report | "
    "inspect-command <key> | inspect-scene <key> | inspect-group-profile <key> | "
    "list-commands | list-scenes | list-group-profiles | search-commands <query> | "
    "search-scenes <query> | search-group-profiles <query> | preview-command <key> | "
    "preview-scene <key> | preview-group-profile <key>"
)
TOP_LEVEL_HELP = """RytmRandomizer passive CLI

Usage:
  python -m rytm_randomizer.cli report
  python -m rytm_randomizer.cli mock-mapper-report
  python -m rytm_randomizer.cli active-boundary-report
  python -m rytm_randomizer.cli inspect-command <key>
  python -m rytm_randomizer.cli inspect-scene <key>
  python -m rytm_randomizer.cli inspect-group-profile <key>
  python -m rytm_randomizer.cli list-commands
  python -m rytm_randomizer.cli list-scenes
  python -m rytm_randomizer.cli list-group-profiles
  python -m rytm_randomizer.cli search-commands <query>
  python -m rytm_randomizer.cli search-scenes <query>
  python -m rytm_randomizer.cli search-group-profiles <query>
  python -m rytm_randomizer.cli preview-command <key>
  python -m rytm_randomizer.cli preview-scene <key>
  python -m rytm_randomizer.cli preview-group-profile <key>
  python -m rytm_randomizer.cli --help

Commands:
  report             Print the passive registry report.
  mock-mapper-report
                     Print the passive mock mapper report.
  active-boundary-report
                     Print the read-only active boundary report.
  inspect-command    Inspect passive command metadata by key.
  inspect-scene      Inspect passive scene metadata by key.
  inspect-group-profile
                     Inspect passive group profile metadata by key.
  list-commands      List passive command keys and labels.
  list-scenes        List passive scene keys and names.
  list-group-profiles
                     List passive group profile keys and names.
  search-commands    Search passive command metadata.
  search-scenes      Search passive scene metadata.
  search-group-profiles
                     Search passive group profile metadata.
  preview-command    Preview passive command metadata by key.
  preview-scene      Preview passive scene metadata by key.
  preview-group-profile
                     Preview passive group profile metadata by key.

Safety:
  passive/read-only
  no MIDI sending
  no port opening
  no command execution
  no hardware mutation
  no hardware required"""
PREVIEW_GROUP_PROFILE_HELP = """RytmRandomizer passive CLI: preview-group-profile

Usage:
  python -m rytm_randomizer.cli preview-group-profile <key>
  python -m rytm_randomizer.cli preview-group-profile --help

Behavior:
  Displays a passive dry-run preview for an existing group profile key.

Safety:
  passive/read-only
  no MIDI sending
  no port opening
  no command execution
  no hardware mutation
  no hardware required"""
PREVIEW_SCENE_HELP = """RytmRandomizer passive CLI: preview-scene

Usage:
  python -m rytm_randomizer.cli preview-scene <key>
  python -m rytm_randomizer.cli preview-scene --help

Behavior:
  Displays a passive dry-run preview for an existing scene key.

Safety:
  passive/read-only
  no MIDI sending
  no port opening
  no scene execution
  no command execution
  no hardware mutation
  no hardware required"""
PREVIEW_COMMAND_HELP = """RytmRandomizer passive CLI: preview-command

Usage:
  python -m rytm_randomizer.cli preview-command <key>
  python -m rytm_randomizer.cli preview-command --help

Behavior:
  Displays a passive dry-run preview for an existing command key.

Safety:
  passive/read-only
  no MIDI sending
  no port opening
  no command execution
  no hardware mutation
  no hardware required"""
SEARCH_GROUP_PROFILES_HELP = """RytmRandomizer passive CLI: search-group-profiles

Usage:
  python -m rytm_randomizer.cli search-group-profiles <query>
  python -m rytm_randomizer.cli search-group-profiles --help

Behavior:
  Searches existing passive group profile metadata.

Safety:
  passive/read-only
  no MIDI sending
  no port opening
  no command execution
  no hardware mutation
  no hardware required"""
SEARCH_SCENES_HELP = """RytmRandomizer passive CLI: search-scenes

Usage:
  python -m rytm_randomizer.cli search-scenes <query>
  python -m rytm_randomizer.cli search-scenes --help

Behavior:
  Searches existing passive scene metadata.

Safety:
  passive/read-only
  no MIDI sending
  no port opening
  no command execution
  no hardware mutation
  no hardware required"""
SEARCH_COMMANDS_HELP = """RytmRandomizer passive CLI: search-commands

Usage:
  python -m rytm_randomizer.cli search-commands <query>
  python -m rytm_randomizer.cli search-commands --help

Behavior:
  Searches existing passive command metadata.

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


def _metadata_search_text(key, metadata):
    values = [str(key)]
    values.extend(value for value in metadata.values() if isinstance(value, str))
    return "\n".join(values).lower()


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


def format_registry_search_report(section_name, title, query):
    """Return deterministic passive registry search lines."""
    report = get_registry_section(section_name)
    normalized_query = str(query)
    search_query = normalized_query.lower()
    if not report["exists"]:
        return [
            f"RytmRandomizer passive {title}",
            f"Section: {report['section']}",
            f"Query: {normalized_query}",
            "Match count: 0",
            "Matches:",
            "- no matches found. No MIDI was sent. No command executed.",
        ]

    items = report["items"]
    matches = [
        (key, _format_list_label(metadata))
        for key, metadata in items.items()
        if search_query in _metadata_search_text(key, metadata)
    ]
    matches.sort(key=lambda item: item[0])

    lines = [
        f"RytmRandomizer passive {title}",
        f"Section: {report['section']}",
        f"Query: {normalized_query}",
        f"Match count: {len(matches)}",
        "Matches:",
    ]
    if matches:
        lines.extend(f"- {key}: {label}" for key, label in matches)
    else:
        lines.append("- no matches found. No MIDI was sent. No command executed.")

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


def format_preview_command_report(command_key):
    """Return deterministic passive command preview lines."""
    command = str(command_key).upper()
    registry_report = get_registry_section("commands")
    registry = registry_report["items"] if registry_report["exists"] else {}
    report = preview_command(registry, command)

    if not report["exists"]:
        return [
            "RytmRandomizer passive command preview",
            f"Command: {command}",
            "Found: False",
            (
                "Message: Command preview not found. No MIDI was sent. "
                "No command executed. No hardware was mutated."
            ),
            f"Safety summary: {report['safety_summary']}",
        ]

    validation = report["validation"]
    return [
        "RytmRandomizer passive command preview",
        f"Command: {command}",
        "Found: True",
        f"Category: {report['category'] or ''}",
        f"Scope: {report['scope'] or ''}",
        f"Target: {report['target'] or ''}",
        f"Pad: {report['pad'] if report['pad'] is not None else ''}",
        f"Scaffold only: {report['scaffold_only']}",
        f"Executable: {report['executable']}",
        f"Forbidden/no-touch: {report['forbidden_or_no_touch']}",
        f"Validation ok: {validation['ok']}",
        f"Validation errors: {len(validation['errors'])}",
        f"Safety summary: {report['safety_summary']}",
        "No MIDI would be sent.",
        "No command would execute.",
        "No hardware would be mutated.",
        "Safety:",
        "- passive/read-only",
        "- no MIDI sending",
        "- no port opening",
        "- no command execution",
        "- no hardware mutation",
        "- no hardware required",
    ]


def format_preview_scene_report(scene_key):
    """Return deterministic passive scene preview lines."""
    report = get_registry_item("scenes", scene_key)
    key = report["key"]

    if not report["exists"]:
        return [
            "RytmRandomizer passive scene preview",
            f"Scene: {key}",
            "Found: False",
            (
                "Message: Scene preview not found. No MIDI was sent. "
                "No scene executed. No command executed. No hardware was mutated."
            ),
        ]

    metadata = report["metadata"]
    return [
        "RytmRandomizer passive scene preview",
        f"Scene: {key}",
        "Found: True",
        f"Name: {metadata.get('name', '')}",
        f"Description: {metadata.get('description', '')}",
        f"Action: {metadata.get('action', '')}",
        f"Scope: {metadata.get('scope', '')}",
        f"Scaffold only: {metadata.get('scaffold_only')}",
        f"Executable: {metadata.get('executable')}",
        f"V1.34 reference command: {metadata.get('v134_reference_command')}",
        "No MIDI would be sent.",
        "No scene would execute.",
        "No command would execute.",
        "No hardware would be mutated.",
        "Safety:",
        "- passive/read-only",
        "- no MIDI sending",
        "- no port opening",
        "- no scene execution",
        "- no command execution",
        "- no hardware mutation",
        "- no hardware required",
    ]


def format_preview_group_profile_report(profile_key):
    """Return deterministic passive group profile preview lines."""
    report = get_registry_item("group_profiles", profile_key)
    key = report["key"]

    if not report["exists"]:
        return [
            "RytmRandomizer passive group profile preview",
            f"Group profile: {key}",
            "Found: False",
            (
                "Message: Group profile preview not found. No MIDI was sent. "
                "No command executed. No hardware was mutated."
            ),
        ]

    metadata = report["metadata"]
    return [
        "RytmRandomizer passive group profile preview",
        f"Group profile: {key}",
        "Found: True",
        f"Name: {metadata.get('name', '')}",
        f"Machine value: {metadata.get('machine_value', '')}",
        f"Group pad: {metadata.get('group_pad', '')}",
        "No MIDI would be sent.",
        "No command would execute.",
        "No hardware would be mutated.",
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
MOCK_MAPPER_REPORT_HELP = """RytmRandomizer passive CLI: mock-mapper-report

Usage:
  python -m rytm_randomizer.cli mock-mapper-report
  python -m rytm_randomizer.cli mock-mapper-report --help

Behavior:
  Prints the deterministic passive mock mapper report to stdout.

Safety:
  passive/read-only
  mock-only
  no MIDI sending
  no port opening
  no command execution
  no hardware mutation
  no hardware required"""
ACTIVE_BOUNDARY_REPORT_HELP = """RytmRandomizer passive CLI: active-boundary-report

Usage:
  python -m rytm_randomizer.cli active-boundary-report
  python -m rytm_randomizer.cli active-boundary-report --help

Behavior:
  Prints the deterministic read-only active boundary report to stdout.

Safety:
  passive/read-only
  mock-only
  no MIDI sending
  no port opening
  no active execution
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

    if args == ["mock-mapper-report", "--help"]:
        sys.stdout.write(f"{MOCK_MAPPER_REPORT_HELP}\n")
        return 0

    if args == ["active-boundary-report", "--help"]:
        sys.stdout.write(f"{ACTIVE_BOUNDARY_REPORT_HELP}\n")
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

    if args == ["search-commands", "--help"]:
        sys.stdout.write(f"{SEARCH_COMMANDS_HELP}\n")
        return 0

    if args == ["search-scenes", "--help"]:
        sys.stdout.write(f"{SEARCH_SCENES_HELP}\n")
        return 0

    if args == ["search-group-profiles", "--help"]:
        sys.stdout.write(f"{SEARCH_GROUP_PROFILES_HELP}\n")
        return 0

    if args == ["preview-command", "--help"]:
        sys.stdout.write(f"{PREVIEW_COMMAND_HELP}\n")
        return 0

    if args == ["preview-scene", "--help"]:
        sys.stdout.write(f"{PREVIEW_SCENE_HELP}\n")
        return 0

    if args == ["preview-group-profile", "--help"]:
        sys.stdout.write(f"{PREVIEW_GROUP_PROFILE_HELP}\n")
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

    if args == ["mock-mapper-report"]:
        sys.stdout.write("\n".join(format_mock_mapper_report()))
        sys.stdout.write("\n")
        return 0

    if args == ["active-boundary-report"]:
        sys.stdout.write("\n".join(format_active_boundary_report()))
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

    if len(args) == 2 and args[0] == "search-commands":
        sys.stdout.write(
            "\n".join(
                format_registry_search_report("commands", "command search", args[1])
            )
        )
        sys.stdout.write("\n")
        return 0

    if len(args) == 2 and args[0] == "search-scenes":
        sys.stdout.write(
            "\n".join(format_registry_search_report("scenes", "scene search", args[1]))
        )
        sys.stdout.write("\n")
        return 0

    if len(args) == 2 and args[0] == "search-group-profiles":
        sys.stdout.write(
            "\n".join(
                format_registry_search_report(
                    "group_profiles",
                    "group profile search",
                    args[1],
                )
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

    if len(args) == 2 and args[0] == "preview-command":
        lines = format_preview_command_report(args[1])
        output = "\n".join(lines)
        if lines[2] == "Found: True":
            sys.stdout.write(f"{output}\n")
            return 0
        sys.stderr.write(f"{output}\n")
        return 1

    if len(args) == 2 and args[0] == "preview-scene":
        lines = format_preview_scene_report(args[1])
        output = "\n".join(lines)
        if lines[2] == "Found: True":
            sys.stdout.write(f"{output}\n")
            return 0
        sys.stderr.write(f"{output}\n")
        return 1

    if len(args) == 2 and args[0] == "preview-group-profile":
        lines = format_preview_group_profile_report(args[1])
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
