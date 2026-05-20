"""Passive report-only CLI entrypoint for RytmRandomizer."""

import sys

from .help_text import HELP_TEXT, USAGE


def _registered_command_exit_code(args):
    if not args:
        return None

    from . import cli_registry

    command = cli_registry.get(args[0])
    if command is None and args[0] == "rytm-12-pad-machine-matrix-report":
        from importlib import import_module

        module = import_module("rytm_randomizer.reports.rytm_machine_matrix")
        if cli_registry.get(args[0]) is None:
            cli_registry.register(module.RYTM_MACHINE_MATRIX_CLI_COMMAND)
        command = cli_registry.get(args[0])

    if command is None:
        return None

    try:
        kwargs = command.args_parser(args[1:])
    except ValueError:
        sys.stderr.write(f"{USAGE}\n")
        return 2

    return command.handler(**kwargs)


def _format_list_label(metadata):
    return metadata.get("label") or metadata.get("name") or ""


def _metadata_search_text(key, metadata):
    values = [str(key)]
    values.extend(value for value in metadata.values() if isinstance(value, str))
    return "\n".join(values).lower()


def format_registry_list_report(section_name, title):
    """Return deterministic passive registry list lines."""
    from .registry import get_registry_section

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
    from .registry import get_registry_section

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
    from .registry import get_registry_item

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
    from .registry import get_registry_item

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
    from .registry import get_registry_item

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
    from .inspection import preview_command
    from .registry import get_registry_section

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
    from .registry import get_registry_item

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
    from .registry import get_registry_item

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


def main(argv=None):
    """Run the passive report-only CLI."""
    args = sys.argv[1:] if argv is None else list(argv)

    if args == ["--help"]:
        sys.stdout.write(f"{HELP_TEXT['--help']}\n")
        return 0

    if len(args) == 2 and args[1] == "--help" and args[0] in HELP_TEXT:
        sys.stdout.write(f"{HELP_TEXT[args[0]]}\n")
        return 0

    registered_exit_code = _registered_command_exit_code(args)
    if registered_exit_code is not None:
        return registered_exit_code

    if args == ["report"]:
        from .reports import format_registry_report

        sys.stdout.write("\n".join(format_registry_report()))
        sys.stdout.write("\n")
        return 0

    if args == ["project-status-report"]:
        from .project_status_report import format_project_status_report

        sys.stdout.write("\n".join(format_project_status_report()))
        sys.stdout.write("\n")
        return 0

    if args == ["project-status-report", "--summary"]:
        from .project_status_report import format_project_status_summary

        sys.stdout.write("\n".join(format_project_status_summary()))
        sys.stdout.write("\n")
        return 0

    if args == ["project-status-report", "--check"]:
        from .project_status_report import check_project_status_report, format_project_status_check

        check = check_project_status_report()
        sys.stdout.write("\n".join(format_project_status_check()))
        sys.stdout.write("\n")
        return 0 if check["ok"] else 1

    if args == ["project-status-report", "--json"]:
        from .project_status_report import format_project_status_report_json

        sys.stdout.write(format_project_status_report_json())
        sys.stdout.write("\n")
        return 0

    if args == ["mock-mapper-report"]:
        from .reports import format_mock_mapper_report

        sys.stdout.write("\n".join(format_mock_mapper_report()))
        sys.stdout.write("\n")
        return 0

    if args == ["runtime-plan-report"]:
        from .reports import format_runtime_plan_report

        sys.stdout.write("\n".join(format_runtime_plan_report()))
        sys.stdout.write("\n")
        return 0

    if args == ["active-boundary-report"]:
        from .reports import format_active_boundary_report

        sys.stdout.write("\n".join(format_active_boundary_report()))
        sys.stdout.write("\n")
        return 0

    if args == ["mock-runtime-active-bridge-report"]:
        from .reports import format_mock_runtime_active_bridge_report

        sys.stdout.write("\n".join(format_mock_runtime_active_bridge_report()))
        sys.stdout.write("\n")
        return 0

    if args == ["anchor-profile-report"]:
        from .reports import format_anchor_profile_report

        sys.stdout.write("\n".join(format_anchor_profile_report()))
        sys.stdout.write("\n")
        return 0

    if args == ["behavior-parity-report"]:
        from .reports import format_behavior_parity_coverage_report

        sys.stdout.write("\n".join(format_behavior_parity_coverage_report()))
        sys.stdout.write("\n")
        return 0

    if args and args[0] == "dual-machine-target-report":
        if len(args) != 2:
            sys.stderr.write(
                "Usage: python -m rytm_randomizer.cli "
                "dual-machine-target-report <rytm|a4|both>\n"
            )
            return 2

        from .dual_machine.reports import target_report

        try:
            sys.stdout.write(target_report(args[1]))
            sys.stdout.write("\n")
        except ValueError as exc:
            sys.stderr.write(f"{exc}\n")
            return 2
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
            "\n".join(format_registry_list_report("group_profiles", "group profile list"))
        )
        sys.stdout.write("\n")
        return 0

    if len(args) == 2 and args[0] == "search-commands":
        sys.stdout.write(
            "\n".join(format_registry_search_report("commands", "command search", args[1]))
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
