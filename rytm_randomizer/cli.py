"""Passive report-only CLI entrypoint for RytmRandomizer."""

import sys

from .help_text import HELP_TEXT, USAGE


def _format_list_label(metadata):
    return metadata.get("label") or metadata.get("name") or ""


def _metadata_search_text(key, metadata):
    values = [str(key)]
    values.extend(value for value in metadata.values() if isinstance(value, str))
    return "\n".join(values).lower()


def _parse_optional_key_value_args(args, allowed_flags):
    if len(args) % 2:
        return None
    parsed = {}
    for index in range(0, len(args), 2):
        flag = args[index]
        if flag not in allowed_flags or flag in parsed:
            return None
        parsed[flag] = args[index + 1]
    return parsed


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


def format_sysex_kit_bank_file_error(path, message):
    """Return deterministic passive SysEx file error lines."""

    return [
        "RytmRandomizer passive SysEx kit bank report",
        f"Path: {path}",
        "Found: False",
        f"Message: {message}. No MIDI was sent. No command executed.",
        "Safety:",
        "- passive/read-only",
        "- no MIDI sending",
        "- no port opening",
        "- no command execution",
        "- no hardware mutation",
        "- no SysEx writes",
        "- no hardware required",
    ]


def format_sysex_project_file_error(path, message):
    """Return deterministic passive SysEx project file error lines."""

    return [
        "RytmRandomizer passive SysEx project report",
        f"Path: {path}",
        "Found: False",
        f"Message: {message}. No MIDI was sent. No command executed.",
        "Safety:",
        "- passive/read-only",
        "- no MIDI sending",
        "- no port opening",
        "- no command execution",
        "- no hardware mutation",
        "- no live SysEx receive",
        "- no SysEx writes",
        "- no hardware required",
    ]


_DUAL_MACHINE_CLI_USAGE_ERROR = "__dual_machine_cli_usage__"


def _is_dual_machine_cli_usage_error(exc: ValueError) -> bool:
    return str(exc) == _DUAL_MACHINE_CLI_USAGE_ERROR


def _dual_machine_error_path(args) -> str:
    if len(args) > 1 and not str(args[1]).startswith("--"):
        return str(args[1])
    return "<not required>"


def _parse_dual_machine_bridge_cli_args(args, *, allow_lane_filters: bool = False):
    if len(args) < 2 or len(args) > (18 if allow_lane_filters else 14):
        raise ValueError(_DUAL_MACHINE_CLI_USAGE_ERROR)

    rytm_path = None
    slot = None
    depth = None
    if not args[1].startswith("--"):
        if len(args) < 6 or (len(args) - 6) % 2 or args[2] != "--slot" or args[4] != "--depth":
            raise ValueError(_DUAL_MACHINE_CLI_USAGE_ERROR)
        rytm_path = args[1]
        try:
            slot = int(args[3])
        except ValueError as exc:
            raise ValueError("Slot must be an integer") from exc
        depth = args[5]
        tail = list(args[6:])
    else:
        if (len(args) - 1) % 2:
            raise ValueError(_DUAL_MACHINE_CLI_USAGE_ERROR)
        tail = list(args[1:])

    target = "both"
    analog_four_path = None
    analog_four_slot = None
    analog_four_profile = "balanced"
    rytm_pad = None
    analog_four_track = None
    while tail:
        flag = tail.pop(0)
        if not tail:
            raise ValueError(_DUAL_MACHINE_CLI_USAGE_ERROR)
        value = tail.pop(0)
        if flag == "--target":
            target = value
        elif flag == "--depth" and rytm_path is None:
            depth = value
        elif flag == "--analog-four-profile":
            analog_four_profile = value
        elif flag == "--analog-four-path":
            analog_four_path = value
        elif flag == "--analog-four-slot":
            try:
                analog_four_slot = int(value)
            except ValueError as exc:
                raise ValueError("Analog Four slot must be an integer") from exc
        elif flag == "--rytm-pad" and allow_lane_filters:
            try:
                rytm_pad = int(value)
            except ValueError as exc:
                raise ValueError("Rytm pad must be an integer") from exc
        elif flag == "--analog-four-track" and allow_lane_filters:
            try:
                analog_four_track = int(value)
            except ValueError as exc:
                raise ValueError("Analog Four track must be an integer") from exc
        else:
            raise ValueError(_DUAL_MACHINE_CLI_USAGE_ERROR)

    if depth is None:
        raise ValueError(_DUAL_MACHINE_CLI_USAGE_ERROR)
    if rytm_path is None:
        from .performance.snapshot_target import build_performance_snapshot_target_plan

        target_plan = build_performance_snapshot_target_plan(target)
        if target_plan.canonical_target != "analog-four":
            raise ValueError("Rytm snapshot path and slot are required for target rytm or both")

    return {
        "rytm_path": rytm_path,
        "slot": slot,
        "depth": depth,
        "target": target,
        "analog_four_path": analog_four_path,
        "analog_four_slot": analog_four_slot,
        "analog_four_profile": analog_four_profile,
        "rytm_pad": rytm_pad,
        "analog_four_track": analog_four_track,
    }


def _parse_dual_machine_lane_validation_guide_cli_args(args):
    if len(args) % 2 == 0:
        raise ValueError(_DUAL_MACHINE_CLI_USAGE_ERROR)

    target = "both"
    rytm_pad = None
    analog_four_track = None
    tail = list(args[1:])
    while tail:
        flag = tail.pop(0)
        if not tail:
            raise ValueError(_DUAL_MACHINE_CLI_USAGE_ERROR)
        value = tail.pop(0)
        if flag == "--target":
            target = value
        elif flag == "--rytm-pad":
            try:
                rytm_pad = int(value)
            except ValueError as exc:
                raise ValueError("Rytm pad must be an integer") from exc
        elif flag == "--analog-four-track":
            try:
                analog_four_track = int(value)
            except ValueError as exc:
                raise ValueError("Analog Four track must be an integer") from exc
        else:
            raise ValueError(_DUAL_MACHINE_CLI_USAGE_ERROR)

    return {
        "target": target,
        "rytm_pad": rytm_pad,
        "analog_four_track": analog_four_track,
    }


def main(argv=None):
    """Run the passive report-only CLI."""
    args = sys.argv[1:] if argv is None else list(argv)

    if args == ["--help"]:
        sys.stdout.write(f"{HELP_TEXT['--help']}\n")
        return 0

    if len(args) == 2 and args[1] == "--help" and args[0] in HELP_TEXT:
        sys.stdout.write(f"{HELP_TEXT[args[0]]}\n")
        return 0

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

    if len(args) == 3 and args[0] == "performance-snapshot-target-report" and args[1] == "--target":
        from .performance.snapshot_target import (
            PerformanceSnapshotTargetError,
            build_performance_snapshot_target_plan,
            format_performance_snapshot_target_error,
            format_performance_snapshot_target_report,
        )

        try:
            plan = build_performance_snapshot_target_plan(args[2])
        except PerformanceSnapshotTargetError as exc:
            lines = format_performance_snapshot_target_error(str(exc))
            sys.stderr.write("\n".join(lines))
            sys.stderr.write("\n")
            return 1

        sys.stdout.write("\n".join(format_performance_snapshot_target_report(plan)))
        sys.stdout.write("\n")
        return 0

    if len(args) == 2 and args[0] == "sysex-kit-bank-report":
        from .sysex.bank_analyzer import (
            SysexBankAnalysisError,
            analyze_sysex_kit_bank_file,
            format_sysex_kit_bank_report,
        )

        try:
            lines = format_sysex_kit_bank_report(analyze_sysex_kit_bank_file(args[1]))
        except FileNotFoundError:
            lines = format_sysex_kit_bank_file_error(args[1], "File not found")
            sys.stderr.write("\n".join(lines))
            sys.stderr.write("\n")
            return 1
        except SysexBankAnalysisError as exc:
            lines = format_sysex_kit_bank_file_error(args[1], str(exc))
            sys.stderr.write("\n".join(lines))
            sys.stderr.write("\n")
            return 1

        sys.stdout.write("\n".join(lines))
        sys.stdout.write("\n")
        return 0

    if len(args) == 2 and args[0] == "sysex-project-report":
        from .sysex.project_analyzer import (
            SysexProjectAnalysisError,
            analyze_sysex_project_file,
            format_sysex_project_report,
        )

        try:
            lines = format_sysex_project_report(analyze_sysex_project_file(args[1]))
        except FileNotFoundError:
            lines = format_sysex_project_file_error(args[1], "File not found")
            sys.stderr.write("\n".join(lines))
            sys.stderr.write("\n")
            return 1
        except SysexProjectAnalysisError as exc:
            lines = format_sysex_project_file_error(args[1], str(exc))
            sys.stderr.write("\n".join(lines))
            sys.stderr.write("\n")
            return 1

        sys.stdout.write("\n".join(lines))
        sys.stdout.write("\n")
        return 0

    if len(args) == 4 and args[0] == "sysex-kit-snapshot-report" and args[2] == "--slot":
        from .snapshot.rytm_decoder import (
            SysexSnapshotDecodeError,
            decode_rytm_kit_snapshot_file,
            format_rytm_kit_snapshot_error,
            format_rytm_kit_snapshot_report,
        )

        try:
            slot = int(args[3])
            snapshot = decode_rytm_kit_snapshot_file(args[1], slot=slot)
        except FileNotFoundError:
            lines = format_rytm_kit_snapshot_error(args[1], "File not found")
            sys.stderr.write("\n".join(lines))
            sys.stderr.write("\n")
            return 1
        except SysexSnapshotDecodeError as exc:
            lines = format_rytm_kit_snapshot_error(args[1], str(exc))
            sys.stderr.write("\n".join(lines))
            sys.stderr.write("\n")
            return 1
        except ValueError:
            lines = format_rytm_kit_snapshot_error(args[1], "Slot must be an integer")
            sys.stderr.write("\n".join(lines))
            sys.stderr.write("\n")
            return 1

        sys.stdout.write("\n".join(format_rytm_kit_snapshot_report(snapshot)))
        sys.stdout.write("\n")
        return 0

    if (
        len(args) in (6, 8)
        and args[0] == "sysex-snapshot-mutation-plan-report"
        and args[2] == "--slot"
        and args[4] == "--depth"
    ):
        from .snapshot.rytm_decoder import SysexSnapshotDecodeError
        from .snapshot.rytm_mutation_planner import (
            SnapshotMutationPlanError,
            build_snapshot_mutation_plan_from_file,
            filter_snapshot_mutation_plan_to_pad,
            format_snapshot_mutation_plan_error,
            format_snapshot_mutation_plan_report,
        )

        optional_args = _parse_optional_key_value_args(args[6:], {"--pad"})
        if optional_args is None:
            sys.stderr.write(f"{USAGE}\n")
            return 2

        try:
            slot = int(args[3])
            plan = build_snapshot_mutation_plan_from_file(
                args[1],
                slot=slot,
                depth=args[5],
            )
            if "--pad" in optional_args:
                plan = filter_snapshot_mutation_plan_to_pad(
                    plan,
                    pad=int(optional_args["--pad"]),
                )
        except FileNotFoundError:
            lines = format_snapshot_mutation_plan_error(args[1], "File not found")
            sys.stderr.write("\n".join(lines))
            sys.stderr.write("\n")
            return 1
        except (SnapshotMutationPlanError, SysexSnapshotDecodeError) as exc:
            lines = format_snapshot_mutation_plan_error(args[1], str(exc))
            sys.stderr.write("\n".join(lines))
            sys.stderr.write("\n")
            return 1
        except ValueError:
            lines = format_snapshot_mutation_plan_error(
                args[1],
                "Slot and pad must be integers",
            )
            sys.stderr.write("\n".join(lines))
            sys.stderr.write("\n")
            return 1

        sys.stdout.write("\n".join(format_snapshot_mutation_plan_report(plan)))
        sys.stdout.write("\n")
        return 0

    if (
        len(args) in (6, 8)
        and args[0] == "sysex-snapshot-mock-runtime-report"
        and args[2] == "--slot"
        and args[4] == "--depth"
    ):
        from .snapshot.rytm_decoder import SysexSnapshotDecodeError
        from .snapshot.rytm_mock_runtime import (
            build_snapshot_mock_runtime_from_file,
            capture_snapshot_mutation_mock_messages,
            format_snapshot_mock_runtime_error,
            format_snapshot_mock_runtime_report,
        )
        from .snapshot.rytm_mutation_planner import (
            SnapshotMutationPlanError,
            filter_snapshot_mutation_plan_to_pad,
        )

        optional_args = _parse_optional_key_value_args(args[6:], {"--pad"})
        if optional_args is None:
            sys.stderr.write(f"{USAGE}\n")
            return 2

        try:
            slot = int(args[3])
            plan = build_snapshot_mock_runtime_from_file(
                args[1],
                slot=slot,
                depth=args[5],
            )
            if "--pad" in optional_args:
                plan = filter_snapshot_mutation_plan_to_pad(
                    plan,
                    pad=int(optional_args["--pad"]),
                )
            sender = capture_snapshot_mutation_mock_messages(plan)
        except FileNotFoundError:
            lines = format_snapshot_mock_runtime_error(args[1], "File not found")
            sys.stderr.write("\n".join(lines))
            sys.stderr.write("\n")
            return 1
        except (SnapshotMutationPlanError, SysexSnapshotDecodeError) as exc:
            lines = format_snapshot_mock_runtime_error(args[1], str(exc))
            sys.stderr.write("\n".join(lines))
            sys.stderr.write("\n")
            return 1
        except ValueError:
            lines = format_snapshot_mock_runtime_error(
                args[1],
                "Slot and pad must be integers",
            )
            sys.stderr.write("\n".join(lines))
            sys.stderr.write("\n")
            return 1

        sys.stdout.write("\n".join(format_snapshot_mock_runtime_report(args[1], plan, sender)))
        sys.stdout.write("\n")
        return 0

    if (
        len(args) == 9
        and args[0] == "rytm-controlled-diff-report"
        and args[3] == "--slot"
        and args[5] == "--pad"
        and args[7] == "--limit"
    ):
        from .rytm.controlled_diff import (
            RytmControlledDiffError,
            build_rytm_controlled_diff_report_from_file,
            format_rytm_controlled_diff_error,
            format_rytm_controlled_diff_report,
        )

        try:
            slot = int(args[4])
            pad = int(args[6])
            limit = int(args[8])
            report = build_rytm_controlled_diff_report_from_file(
                args[1],
                args[2],
                slot=slot,
                pad=pad,
                limit=limit,
            )
        except FileNotFoundError:
            lines = format_rytm_controlled_diff_error("File not found")
            sys.stderr.write("\n".join(lines))
            sys.stderr.write("\n")
            return 1
        except RytmControlledDiffError as exc:
            lines = format_rytm_controlled_diff_error(str(exc))
            sys.stderr.write("\n".join(lines))
            sys.stderr.write("\n")
            return 1
        except ValueError:
            lines = format_rytm_controlled_diff_error("Slot, pad, and limit must be integers")
            sys.stderr.write("\n".join(lines))
            sys.stderr.write("\n")
            return 1

        sys.stdout.write("\n".join(format_rytm_controlled_diff_report(report)))
        sys.stdout.write("\n")
        return 0

    if (
        len(args) == 8
        and args[0] == "rytm-controlled-diff-report"
        and args[3] == "--slot"
        and args[5] == "--all-pads"
        and args[6] == "--limit"
    ):
        from .rytm.controlled_diff import (
            RytmControlledDiffError,
            build_rytm_all_pad_controlled_diff_report_from_file,
            format_rytm_all_pad_controlled_diff_report,
            format_rytm_controlled_diff_error,
        )

        try:
            slot = int(args[4])
            limit = int(args[7])
            report = build_rytm_all_pad_controlled_diff_report_from_file(
                args[1],
                args[2],
                slot=slot,
                limit=limit,
            )
        except FileNotFoundError:
            lines = format_rytm_controlled_diff_error("File not found")
            sys.stderr.write("\n".join(lines))
            sys.stderr.write("\n")
            return 1
        except RytmControlledDiffError as exc:
            lines = format_rytm_controlled_diff_error(str(exc))
            sys.stderr.write("\n".join(lines))
            sys.stderr.write("\n")
            return 1
        except ValueError:
            lines = format_rytm_controlled_diff_error("Slot and limit must be integers")
            sys.stderr.write("\n".join(lines))
            sys.stderr.write("\n")
            return 1

        sys.stdout.write("\n".join(format_rytm_all_pad_controlled_diff_report(report)))
        sys.stdout.write("\n")
        return 0

    if (
        len(args) == 11
        and args[0] == "rytm-controlled-mapping-proof-report"
        and args[3] == "--slot"
        and args[5] == "--pad"
        and args[7] == "--parameter"
        and args[9] == "--limit"
    ):
        from .rytm.controlled_diff import RytmControlledDiffError
        from .rytm.controlled_mapping_proof import (
            build_rytm_controlled_mapping_proof_from_file,
            format_rytm_controlled_mapping_proof_error,
            format_rytm_controlled_mapping_proof_report,
        )

        try:
            slot = int(args[4])
            pad = int(args[6])
            limit = int(args[10])
            proof = build_rytm_controlled_mapping_proof_from_file(
                args[1],
                args[2],
                slot=slot,
                pad=pad,
                parameter=args[8],
                limit=limit,
            )
        except FileNotFoundError:
            lines = format_rytm_controlled_mapping_proof_error("File not found")
            sys.stderr.write("\n".join(lines))
            sys.stderr.write("\n")
            return 1
        except RytmControlledDiffError as exc:
            lines = format_rytm_controlled_mapping_proof_error(str(exc))
            sys.stderr.write("\n".join(lines))
            sys.stderr.write("\n")
            return 1
        except ValueError as exc:
            lines = format_rytm_controlled_mapping_proof_error(str(exc))
            sys.stderr.write("\n".join(lines))
            sys.stderr.write("\n")
            return 1

        sys.stdout.write("\n".join(format_rytm_controlled_mapping_proof_report(proof)))
        sys.stdout.write("\n")
        return 0

    if args and args[0] == "dual-machine-mock-bridge-report":
        from .analog_four.snapshot_mutation_planner import (
            AnalogFourSnapshotMutationPlanError,
        )
        from .dual_machine.mock_bridge import (
            build_dual_machine_mock_bridge,
            format_dual_machine_mock_bridge_error,
            format_dual_machine_mock_bridge_report,
        )
        from .performance.snapshot_target import PerformanceSnapshotTargetError
        from .snapshot.rytm_decoder import SysexSnapshotDecodeError
        from .snapshot.rytm_mutation_planner import SnapshotMutationPlanError

        try:
            parsed = _parse_dual_machine_bridge_cli_args(args, allow_lane_filters=True)
        except ValueError as exc:
            if _is_dual_machine_cli_usage_error(exc):
                sys.stderr.write(f"{USAGE}\n")
                return 2
            lines = format_dual_machine_mock_bridge_error(_dual_machine_error_path(args), str(exc))
            sys.stderr.write("\n".join(lines))
            sys.stderr.write("\n")
            return 1

        try:
            bridge = build_dual_machine_mock_bridge(
                parsed["rytm_path"],
                slot=parsed["slot"],
                depth=parsed["depth"],
                target=parsed["target"],
                analog_four_sysex_path=parsed["analog_four_path"],
                analog_four_slot=parsed["analog_four_slot"],
                analog_four_profile=parsed["analog_four_profile"],
                rytm_pad=parsed["rytm_pad"],
                analog_four_track=parsed["analog_four_track"],
            )
        except FileNotFoundError:
            lines = format_dual_machine_mock_bridge_error(
                parsed["rytm_path"] or "<not required>",
                "File not found",
            )
            sys.stderr.write("\n".join(lines))
            sys.stderr.write("\n")
            return 1
        except (
            PerformanceSnapshotTargetError,
            SnapshotMutationPlanError,
            AnalogFourSnapshotMutationPlanError,
            SysexSnapshotDecodeError,
            ValueError,
        ) as exc:
            lines = format_dual_machine_mock_bridge_error(
                parsed["rytm_path"] or "<not required>",
                str(exc),
            )
            sys.stderr.write("\n".join(lines))
            sys.stderr.write("\n")
            return 1

        sys.stdout.write("\n".join(format_dual_machine_mock_bridge_report(bridge)))
        sys.stdout.write("\n")
        return 0

    if args and args[0] == "dual-machine-live-snapshot-readiness-report":
        from .analog_four.snapshot_mutation_planner import (
            AnalogFourSnapshotMutationPlanError,
        )
        from .dual_machine.live_snapshot_readiness import (
            evaluate_dual_machine_live_snapshot_readiness,
            format_dual_machine_live_snapshot_readiness_error,
            format_dual_machine_live_snapshot_readiness_report,
        )
        from .dual_machine.mock_bridge import build_dual_machine_mock_bridge
        from .performance.snapshot_target import PerformanceSnapshotTargetError
        from .snapshot.rytm_decoder import SysexSnapshotDecodeError
        from .snapshot.rytm_mutation_planner import SnapshotMutationPlanError

        try:
            parsed = _parse_dual_machine_bridge_cli_args(args, allow_lane_filters=True)
        except ValueError as exc:
            if _is_dual_machine_cli_usage_error(exc):
                sys.stderr.write(f"{USAGE}\n")
                return 2
            lines = format_dual_machine_live_snapshot_readiness_error(str(exc))
            sys.stderr.write("\n".join(lines))
            sys.stderr.write("\n")
            return 1

        try:
            bridge = build_dual_machine_mock_bridge(
                parsed["rytm_path"],
                slot=parsed["slot"],
                depth=parsed["depth"],
                target=parsed["target"],
                analog_four_sysex_path=parsed["analog_four_path"],
                analog_four_slot=parsed["analog_four_slot"],
                analog_four_profile=parsed["analog_four_profile"],
                rytm_pad=parsed["rytm_pad"],
                analog_four_track=parsed["analog_four_track"],
            )
            readiness = evaluate_dual_machine_live_snapshot_readiness(bridge)
        except FileNotFoundError:
            lines = format_dual_machine_live_snapshot_readiness_error("File not found")
            sys.stderr.write("\n".join(lines))
            sys.stderr.write("\n")
            return 1
        except (
            PerformanceSnapshotTargetError,
            SnapshotMutationPlanError,
            AnalogFourSnapshotMutationPlanError,
            SysexSnapshotDecodeError,
            ValueError,
        ) as exc:
            lines = format_dual_machine_live_snapshot_readiness_error(str(exc))
            sys.stderr.write("\n".join(lines))
            sys.stderr.write("\n")
            return 1

        sys.stdout.write("\n".join(format_dual_machine_live_snapshot_readiness_report(readiness)))
        sys.stdout.write("\n")
        return 0

    if args and args[0] == "dual-machine-active-send-plan-report":
        from .analog_four.snapshot_mutation_planner import (
            AnalogFourSnapshotMutationPlanError,
        )
        from .dual_machine.active_send_plan import (
            build_dual_machine_active_send_plan,
            format_dual_machine_active_send_plan_error,
            format_dual_machine_active_send_plan_report,
        )
        from .dual_machine.mock_bridge import build_dual_machine_mock_bridge
        from .performance.snapshot_target import PerformanceSnapshotTargetError
        from .snapshot.rytm_decoder import SysexSnapshotDecodeError
        from .snapshot.rytm_mutation_planner import SnapshotMutationPlanError

        try:
            parsed = _parse_dual_machine_bridge_cli_args(args, allow_lane_filters=True)
        except ValueError as exc:
            if _is_dual_machine_cli_usage_error(exc):
                sys.stderr.write(f"{USAGE}\n")
                return 2
            lines = format_dual_machine_active_send_plan_error(str(exc))
            sys.stderr.write("\n".join(lines))
            sys.stderr.write("\n")
            return 1

        try:
            bridge = build_dual_machine_mock_bridge(
                parsed["rytm_path"],
                slot=parsed["slot"],
                depth=parsed["depth"],
                target=parsed["target"],
                analog_four_sysex_path=parsed["analog_four_path"],
                analog_four_slot=parsed["analog_four_slot"],
                analog_four_profile=parsed["analog_four_profile"],
                rytm_pad=parsed["rytm_pad"],
                analog_four_track=parsed["analog_four_track"],
            )
            plan = build_dual_machine_active_send_plan(bridge)
        except FileNotFoundError:
            lines = format_dual_machine_active_send_plan_error("File not found")
            sys.stderr.write("\n".join(lines))
            sys.stderr.write("\n")
            return 1
        except (
            PerformanceSnapshotTargetError,
            SnapshotMutationPlanError,
            AnalogFourSnapshotMutationPlanError,
            SysexSnapshotDecodeError,
            ValueError,
        ) as exc:
            lines = format_dual_machine_active_send_plan_error(str(exc))
            sys.stderr.write("\n".join(lines))
            sys.stderr.write("\n")
            return 1

        sys.stdout.write("\n".join(format_dual_machine_active_send_plan_report(plan)))
        sys.stdout.write("\n")
        return 0

    if args and args[0] == "dual-machine-guarded-send-dry-run-report":
        from .analog_four.snapshot_mutation_planner import (
            AnalogFourSnapshotMutationPlanError,
        )
        from .dual_machine.guarded_sender import (
            build_dual_machine_guarded_send_dry_run,
            format_dual_machine_guarded_send_dry_run_report,
            format_dual_machine_guarded_send_error,
        )
        from .dual_machine.mock_bridge import build_dual_machine_mock_bridge
        from .performance.snapshot_target import PerformanceSnapshotTargetError
        from .snapshot.rytm_decoder import SysexSnapshotDecodeError
        from .snapshot.rytm_mutation_planner import SnapshotMutationPlanError

        try:
            parsed = _parse_dual_machine_bridge_cli_args(args, allow_lane_filters=True)
        except ValueError as exc:
            if _is_dual_machine_cli_usage_error(exc):
                sys.stderr.write(f"{USAGE}\n")
                return 2
            lines = format_dual_machine_guarded_send_error(str(exc))
            sys.stderr.write("\n".join(lines))
            sys.stderr.write("\n")
            return 1

        try:
            bridge = build_dual_machine_mock_bridge(
                parsed["rytm_path"],
                slot=parsed["slot"],
                depth=parsed["depth"],
                target=parsed["target"],
                analog_four_sysex_path=parsed["analog_four_path"],
                analog_four_slot=parsed["analog_four_slot"],
                analog_four_profile=parsed["analog_four_profile"],
                rytm_pad=parsed["rytm_pad"],
                analog_four_track=parsed["analog_four_track"],
            )
            result = build_dual_machine_guarded_send_dry_run(bridge)
        except FileNotFoundError:
            lines = format_dual_machine_guarded_send_error("File not found")
            sys.stderr.write("\n".join(lines))
            sys.stderr.write("\n")
            return 1
        except (
            PerformanceSnapshotTargetError,
            SnapshotMutationPlanError,
            AnalogFourSnapshotMutationPlanError,
            SysexSnapshotDecodeError,
            ValueError,
        ) as exc:
            lines = format_dual_machine_guarded_send_error(str(exc))
            sys.stderr.write("\n".join(lines))
            sys.stderr.write("\n")
            return 1

        sys.stdout.write("\n".join(format_dual_machine_guarded_send_dry_run_report(result)))
        sys.stdout.write("\n")
        return 0

    if args and args[0] == "dual-machine-lane-validation-guide":
        from .dual_machine.lane_validation_guide import (
            format_dual_machine_all_lane_validation_guide,
            format_dual_machine_lane_validation_guide,
            format_dual_machine_lane_validation_guide_error,
        )

        try:
            if args == ["dual-machine-lane-validation-guide", "--all-lanes"]:
                report = format_dual_machine_all_lane_validation_guide()
            else:
                parsed = _parse_dual_machine_lane_validation_guide_cli_args(args)
                report = format_dual_machine_lane_validation_guide(**parsed)
        except ValueError as exc:
            if _is_dual_machine_cli_usage_error(exc):
                sys.stderr.write(f"{USAGE}\n")
            else:
                sys.stderr.write(
                    "\n".join(format_dual_machine_lane_validation_guide_error(str(exc)))
                )
                sys.stderr.write("\n")
            return 2

        sys.stdout.write("\n".join(report))
        sys.stdout.write("\n")
        return 0

    if args and args[0] == "dual-machine-kit-bank-readiness-report":
        from .dual_machine.bank_readiness import (
            DualMachineKitBankReadinessError,
            analyze_dual_machine_kit_bank_files,
            format_dual_machine_kit_bank_readiness_error,
            format_dual_machine_kit_bank_readiness_report,
        )

        parsed = _parse_optional_key_value_args(args[1:], {"--rytm", "--analog-four"})
        if parsed is None or set(parsed) != {"--rytm", "--analog-four"}:
            sys.stderr.write(f"{USAGE}\n")
            return 2

        try:
            readiness = analyze_dual_machine_kit_bank_files(
                parsed["--rytm"],
                parsed["--analog-four"],
            )
        except FileNotFoundError:
            lines = format_dual_machine_kit_bank_readiness_error(
                parsed["--rytm"],
                parsed["--analog-four"],
                "File not found",
            )
            sys.stderr.write("\n".join(lines))
            sys.stderr.write("\n")
            return 1
        except DualMachineKitBankReadinessError as exc:
            lines = format_dual_machine_kit_bank_readiness_error(
                parsed["--rytm"],
                parsed["--analog-four"],
                str(exc),
            )
            sys.stderr.write("\n".join(lines))
            sys.stderr.write("\n")
            return 1

        sys.stdout.write("\n".join(format_dual_machine_kit_bank_readiness_report(readiness)))
        sys.stdout.write("\n")
        return 0

    if args and args[0] == "dual-machine-mapping-validation-queue-report":
        from .dual_machine.mapping_validation_queue import (
            DEFAULT_MAPPING_QUEUE_LIMIT,
            format_dual_machine_mapping_validation_queue_error,
            format_dual_machine_mapping_validation_queue_report,
        )

        optional_args = _parse_optional_key_value_args(
            args[1:],
            {"--target", "--limit"},
        )
        if optional_args is None:
            sys.stderr.write(f"{USAGE}\n")
            return 2

        try:
            target = optional_args.get("--target", "both")
            limit = int(optional_args.get("--limit", str(DEFAULT_MAPPING_QUEUE_LIMIT)))
            report = format_dual_machine_mapping_validation_queue_report(
                target=target,
                limit=limit,
            )
        except ValueError as exc:
            lines = format_dual_machine_mapping_validation_queue_error(str(exc))
            sys.stderr.write("\n".join(lines))
            sys.stderr.write("\n")
            return 1

        sys.stdout.write("\n".join(report))
        sys.stdout.write("\n")
        return 0

    if len(args) == 4 and args[0] == "analog-four-kit-snapshot-report" and args[2] == "--slot":
        from .analog_four.snapshot_decoder import (
            AnalogFourSnapshotDecodeError,
            decode_analog_four_kit_snapshot_file,
            format_analog_four_kit_snapshot_error,
            format_analog_four_kit_snapshot_report,
        )

        try:
            slot = int(args[3])
            snapshot = decode_analog_four_kit_snapshot_file(args[1], slot=slot)
        except FileNotFoundError:
            lines = format_analog_four_kit_snapshot_error(args[1], "File not found")
            sys.stderr.write("\n".join(lines))
            sys.stderr.write("\n")
            return 1
        except AnalogFourSnapshotDecodeError as exc:
            lines = format_analog_four_kit_snapshot_error(args[1], str(exc))
            sys.stderr.write("\n".join(lines))
            sys.stderr.write("\n")
            return 1
        except ValueError:
            lines = format_analog_four_kit_snapshot_error(args[1], "Slot must be an integer")
            sys.stderr.write("\n".join(lines))
            sys.stderr.write("\n")
            return 1

        sys.stdout.write("\n".join(format_analog_four_kit_snapshot_report(snapshot)))
        sys.stdout.write("\n")
        return 0

    if len(args) == 2 and args[0] == "analog-four-kit-bank-report":
        from .analog_four.bank_analyzer import (
            AnalogFourKitBankAnalysisError,
            analyze_analog_four_kit_bank_file,
            format_analog_four_kit_bank_error,
            format_analog_four_kit_bank_report,
        )

        try:
            analysis = analyze_analog_four_kit_bank_file(args[1])
        except FileNotFoundError:
            lines = format_analog_four_kit_bank_error(args[1], "File not found")
            sys.stderr.write("\n".join(lines))
            sys.stderr.write("\n")
            return 1
        except AnalogFourKitBankAnalysisError as exc:
            lines = format_analog_four_kit_bank_error(args[1], str(exc))
            sys.stderr.write("\n".join(lines))
            sys.stderr.write("\n")
            return 1

        sys.stdout.write("\n".join(format_analog_four_kit_bank_report(analysis)))
        sys.stdout.write("\n")
        return 0

    if (
        len(args) in (6, 8)
        and args[0] == "analog-four-snapshot-mutation-plan-report"
        and args[2] == "--slot"
        and args[4] == "--depth"
    ):
        from .analog_four.snapshot_mutation_planner import (
            AnalogFourSnapshotMutationPlanError,
            build_analog_four_snapshot_mutation_plan_from_file,
            filter_analog_four_snapshot_mutation_plan_to_track,
            format_analog_four_snapshot_mutation_plan_error,
            format_analog_four_snapshot_mutation_plan_report,
        )

        optional_args = _parse_optional_key_value_args(args[6:], {"--track"})
        if optional_args is None:
            sys.stderr.write(f"{USAGE}\n")
            return 2

        try:
            slot = int(args[3])
            plan = build_analog_four_snapshot_mutation_plan_from_file(
                args[1],
                slot=slot,
                depth=args[5],
            )
            if "--track" in optional_args:
                plan = filter_analog_four_snapshot_mutation_plan_to_track(
                    plan,
                    track=int(optional_args["--track"]),
                )
        except FileNotFoundError:
            lines = format_analog_four_snapshot_mutation_plan_error(args[1], "File not found")
            sys.stderr.write("\n".join(lines))
            sys.stderr.write("\n")
            return 1
        except AnalogFourSnapshotMutationPlanError as exc:
            lines = format_analog_four_snapshot_mutation_plan_error(args[1], str(exc))
            sys.stderr.write("\n".join(lines))
            sys.stderr.write("\n")
            return 1
        except ValueError:
            lines = format_analog_four_snapshot_mutation_plan_error(
                args[1],
                "Slot must be an integer",
            )
            sys.stderr.write("\n".join(lines))
            sys.stderr.write("\n")
            return 1

        sys.stdout.write("\n".join(format_analog_four_snapshot_mutation_plan_report(plan)))
        sys.stdout.write("\n")
        return 0

    if (
        len(args) in (6, 8)
        and args[0] == "analog-four-snapshot-mock-runtime-report"
        and args[2] == "--slot"
        and args[4] == "--depth"
    ):
        from .analog_four.snapshot_mock_runtime import (
            build_analog_four_snapshot_mock_runtime_from_file,
            capture_analog_four_snapshot_mock_messages,
            format_analog_four_snapshot_mock_runtime_error,
            format_analog_four_snapshot_mock_runtime_report,
        )
        from .analog_four.snapshot_mutation_planner import (
            AnalogFourSnapshotMutationPlanError,
            filter_analog_four_snapshot_mutation_plan_to_track,
        )

        optional_args = _parse_optional_key_value_args(args[6:], {"--track"})
        if optional_args is None:
            sys.stderr.write(f"{USAGE}\n")
            return 2

        try:
            slot = int(args[3])
            plan = build_analog_four_snapshot_mock_runtime_from_file(
                args[1],
                slot=slot,
                depth=args[5],
            )
            if "--track" in optional_args:
                plan = filter_analog_four_snapshot_mutation_plan_to_track(
                    plan,
                    track=int(optional_args["--track"]),
                )
            sender = capture_analog_four_snapshot_mock_messages(plan)
        except FileNotFoundError:
            lines = format_analog_four_snapshot_mock_runtime_error(args[1], "File not found")
            sys.stderr.write("\n".join(lines))
            sys.stderr.write("\n")
            return 1
        except AnalogFourSnapshotMutationPlanError as exc:
            lines = format_analog_four_snapshot_mock_runtime_error(args[1], str(exc))
            sys.stderr.write("\n".join(lines))
            sys.stderr.write("\n")
            return 1
        except ValueError:
            lines = format_analog_four_snapshot_mock_runtime_error(
                args[1],
                "Slot must be an integer",
            )
            sys.stderr.write("\n".join(lines))
            sys.stderr.write("\n")
            return 1

        sys.stdout.write(
            "\n".join(format_analog_four_snapshot_mock_runtime_report(args[1], plan, sender))
        )
        sys.stdout.write("\n")
        return 0

    if (
        len(args) == 6
        and args[0] == "analog-four-offset-candidate-report"
        and args[2] == "--track"
        and args[4] == "--limit"
    ):
        from .analog_four.offset_candidates import (
            AnalogFourOffsetCandidateError,
            build_analog_four_offset_candidate_report_from_file,
            format_analog_four_offset_candidate_error,
            format_analog_four_offset_candidate_report,
        )

        try:
            track = int(args[3])
            limit = int(args[5])
            report = build_analog_four_offset_candidate_report_from_file(
                args[1],
                track=track,
                limit=limit,
            )
        except FileNotFoundError:
            lines = format_analog_four_offset_candidate_error(args[1], "File not found")
            sys.stderr.write("\n".join(lines))
            sys.stderr.write("\n")
            return 1
        except AnalogFourOffsetCandidateError as exc:
            lines = format_analog_four_offset_candidate_error(args[1], str(exc))
            sys.stderr.write("\n".join(lines))
            sys.stderr.write("\n")
            return 1
        except ValueError:
            lines = format_analog_four_offset_candidate_error(
                args[1],
                "Track and limit must be integers",
            )
            sys.stderr.write("\n".join(lines))
            sys.stderr.write("\n")
            return 1

        sys.stdout.write("\n".join(format_analog_four_offset_candidate_report(report)))
        sys.stdout.write("\n")
        return 0

    if (
        len(args) == 5
        and args[0] == "analog-four-offset-candidate-report"
        and args[2] == "--all-tracks"
        and args[3] == "--limit"
    ):
        from .analog_four.offset_candidates import (
            AnalogFourOffsetCandidateError,
            build_analog_four_all_track_offset_candidate_report_from_file,
            format_analog_four_all_track_offset_candidate_report,
            format_analog_four_offset_candidate_error,
        )

        try:
            limit = int(args[4])
            report = build_analog_four_all_track_offset_candidate_report_from_file(
                args[1],
                limit=limit,
            )
        except FileNotFoundError:
            lines = format_analog_four_offset_candidate_error(args[1], "File not found")
            sys.stderr.write("\n".join(lines))
            sys.stderr.write("\n")
            return 1
        except AnalogFourOffsetCandidateError as exc:
            lines = format_analog_four_offset_candidate_error(args[1], str(exc))
            sys.stderr.write("\n".join(lines))
            sys.stderr.write("\n")
            return 1
        except ValueError:
            lines = format_analog_four_offset_candidate_error(
                args[1],
                "Limit must be an integer",
            )
            sys.stderr.write("\n".join(lines))
            sys.stderr.write("\n")
            return 1

        sys.stdout.write("\n".join(format_analog_four_all_track_offset_candidate_report(report)))
        sys.stdout.write("\n")
        return 0

    if (
        len(args) == 9
        and args[0] == "analog-four-controlled-diff-report"
        and args[3] == "--slot"
        and args[5] == "--track"
        and args[7] == "--limit"
    ):
        from .analog_four.controlled_diff import (
            AnalogFourControlledDiffError,
            build_analog_four_controlled_diff_report_from_file,
            format_analog_four_controlled_diff_error,
            format_analog_four_controlled_diff_report,
        )

        try:
            slot = int(args[4])
            track = int(args[6])
            limit = int(args[8])
            report = build_analog_four_controlled_diff_report_from_file(
                args[1],
                args[2],
                slot=slot,
                track=track,
                limit=limit,
            )
        except FileNotFoundError:
            lines = format_analog_four_controlled_diff_error("File not found")
            sys.stderr.write("\n".join(lines))
            sys.stderr.write("\n")
            return 1
        except AnalogFourControlledDiffError as exc:
            lines = format_analog_four_controlled_diff_error(str(exc))
            sys.stderr.write("\n".join(lines))
            sys.stderr.write("\n")
            return 1
        except ValueError:
            lines = format_analog_four_controlled_diff_error(
                "Slot, track, and limit must be integers"
            )
            sys.stderr.write("\n".join(lines))
            sys.stderr.write("\n")
            return 1

        sys.stdout.write("\n".join(format_analog_four_controlled_diff_report(report)))
        sys.stdout.write("\n")
        return 0

    if args and args[0] == "analog-four-saved-offset-mapping-guide":
        from .analog_four.saved_offset_mapping_validation_guide import (
            format_analog_four_saved_offset_mapping_validation_error,
            format_analog_four_saved_offset_mapping_validation_guide,
        )

        if len(args) not in (1, 3, 5) or len(args[1:]) % 2:
            sys.stderr.write(f"{USAGE}\n")
            return 2
        optional_args = _parse_optional_key_value_args(
            args[1:],
            {"--track", "--parameter"},
        )
        if optional_args is None:
            sys.stderr.write(f"{USAGE}\n")
            return 2

        try:
            track = int(optional_args.get("--track", "1"))
            parameter = optional_args.get("--parameter", "filter-1-frequency")
            lines = format_analog_four_saved_offset_mapping_validation_guide(
                track=track,
                parameter=parameter,
            )
        except ValueError as exc:
            lines = format_analog_four_saved_offset_mapping_validation_error(str(exc))
            sys.stderr.write("\n".join(lines))
            sys.stderr.write("\n")
            return 1

        sys.stdout.write("\n".join(lines))
        sys.stdout.write("\n")
        return 0

    if (
        len(args) == 11
        and args[0] == "analog-four-saved-offset-mapping-promotion-report"
        and args[3] == "--slot"
        and args[5] == "--track"
        and args[7] == "--parameter"
        and args[9] == "--limit"
    ):
        from .analog_four.controlled_diff import AnalogFourControlledDiffError
        from .analog_four.saved_offset_mapping_promotion import (
            build_analog_four_saved_offset_mapping_promotion_from_file,
            format_analog_four_saved_offset_mapping_promotion_error,
            format_analog_four_saved_offset_mapping_promotion_report,
        )

        try:
            slot = int(args[4])
            track = int(args[6])
            limit = int(args[10])
            promotion = build_analog_four_saved_offset_mapping_promotion_from_file(
                args[1],
                args[2],
                slot=slot,
                track=track,
                parameter=args[8],
                limit=limit,
            )
        except FileNotFoundError:
            lines = format_analog_four_saved_offset_mapping_promotion_error("File not found")
            sys.stderr.write("\n".join(lines))
            sys.stderr.write("\n")
            return 1
        except (AnalogFourControlledDiffError, ValueError) as exc:
            lines = format_analog_four_saved_offset_mapping_promotion_error(str(exc))
            sys.stderr.write("\n".join(lines))
            sys.stderr.write("\n")
            return 1

        sys.stdout.write(
            "\n".join(format_analog_four_saved_offset_mapping_promotion_report(promotion))
        )
        sys.stdout.write("\n")
        return 0

    if (
        len(args) == 5
        and args[0] == "essence-plan-report"
        and args[1] in {"--tags", "--description"}
        and args[3] == "--discovery"
    ):
        from .essence.plan_report import (
            format_essence_plan_error,
            format_essence_plan_report,
            parse_discovery_value,
            parse_essence_tags,
        )

        try:
            if args[1] == "--description":
                from .essence.tag_adapter import derive_essence_tags_from_description

                tags = derive_essence_tags_from_description(args[2])
            else:
                tags = parse_essence_tags(args[2])
            discovery = parse_discovery_value(args[4])
        except ValueError as exc:
            lines = format_essence_plan_error(str(exc))
            sys.stderr.write("\n".join(lines))
            sys.stderr.write("\n")
            return 1

        sys.stdout.write("\n".join(format_essence_plan_report(tags=tags, discovery=discovery)))
        sys.stdout.write("\n")
        return 0

    if args and args[0] == "essence-application-readiness-report":
        from .essence.application import (
            evaluate_essence_application_readiness,
            format_essence_application_error,
            format_essence_application_readiness_report,
            parse_application_mode,
            parse_snapshot_state,
        )
        from .essence.plan_report import parse_discovery_value, parse_essence_tags
        from .snapshot.fixtures import get_snapshot_fixture

        if (
            len(args) < 5
            or args[1] != "--mode"
            or args[3]
            not in {
                "--description",
                "--tags",
                "--style",
            }
        ):
            sys.stderr.write(f"{USAGE}\n")
            return 2
        tail = args[5:]
        if len(tail) % 2:
            sys.stderr.write(f"{USAGE}\n")
            return 2

        try:
            mode = parse_application_mode(args[2])
            source_flag = args[3]
            source_value = args[4]
            discovery = None
            snapshot_state = None
            snapshot_fixture = None
            for flag, value in zip(tail[0::2], tail[1::2]):
                if flag == "--discovery":
                    if discovery is not None:
                        raise ValueError("Discovery was supplied more than once")
                    discovery = parse_discovery_value(value)
                elif flag == "--snapshot":
                    if snapshot_state is not None or snapshot_fixture is not None:
                        raise ValueError("Choose either --snapshot or --fixture, not both")
                    snapshot_state = parse_snapshot_state(value)
                elif flag == "--fixture":
                    if snapshot_state is not None or snapshot_fixture is not None:
                        raise ValueError("Choose either --snapshot or --fixture, not both")
                    snapshot_fixture = get_snapshot_fixture(value)
                else:
                    sys.stderr.write(f"{USAGE}\n")
                    return 2

            source_label = ""
            source_prompt = ""
            matched_profile_labels = ()
            if source_flag == "--description":
                from .essence.tag_adapter import derive_essence_tags_from_description

                if discovery is None:
                    sys.stderr.write(f"{USAGE}\n")
                    return 2
                tags = derive_essence_tags_from_description(source_value)
            elif source_flag == "--tags":
                if discovery is None:
                    sys.stderr.write(f"{USAGE}\n")
                    return 2
                tags = parse_essence_tags(source_value)
            else:
                from .essence.style_intent_profiles import build_style_intent_request

                request = build_style_intent_request(source_value, discovery=discovery)
                tags = request.tags
                discovery = request.discovery
                source_label = "Style Intent"
                source_prompt = request.prompt
                matched_profile_labels = tuple(
                    profile.label for profile in request.matched_profiles
                )

            if mode == "live_snapshot" and snapshot_state is None and snapshot_fixture is None:
                snapshot_state = parse_snapshot_state(None)
        except ValueError as exc:
            lines = format_essence_application_error(str(exc))
            sys.stderr.write("\n".join(lines))
            sys.stderr.write("\n")
            return 1
        except KeyError as exc:
            lines = format_essence_application_error(str(exc))
            sys.stderr.write("\n".join(lines))
            sys.stderr.write("\n")
            return 1

        readiness = evaluate_essence_application_readiness(
            mode=mode,
            tags=tags,
            discovery=discovery,
            snapshot_state=snapshot_state,
            snapshot_fixture=snapshot_fixture,
            source_label=source_label,
            source_prompt=source_prompt,
            matched_profile_labels=matched_profile_labels,
        )
        sys.stdout.write("\n".join(format_essence_application_readiness_report(readiness)))
        sys.stdout.write("\n")
        return 0

    if args and args[0] == "style-intent-report":
        from .essence.plan_report import parse_discovery_value
        from .essence.style_intent_profiles import (
            format_style_intent_error,
            format_style_intent_report,
        )

        if len(args) not in (3, 5) or args[1] != "--style":
            sys.stderr.write(f"{USAGE}\n")
            return 2

        try:
            discovery = None
            if len(args) == 5:
                if args[3] != "--discovery":
                    sys.stderr.write(f"{USAGE}\n")
                    return 2
                discovery = parse_discovery_value(args[4])
            lines = format_style_intent_report(args[2], discovery=discovery)
        except ValueError as exc:
            lines = format_style_intent_error(str(exc))
            sys.stderr.write("\n".join(lines))
            sys.stderr.write("\n")
            return 1

        sys.stdout.write("\n".join(lines))
        sys.stdout.write("\n")
        return 0

    if args and args[0] == "snapshot-essence-overlay-report":
        from .essence.plan_report import parse_discovery_value
        from .essence.snapshot_overlay import (
            build_snapshot_essence_overlay_plan_from_file,
            format_snapshot_essence_overlay_error,
            format_snapshot_essence_overlay_report,
        )
        from .observability.errors import DataError

        if (
            len(args) not in (8, 10)
            or args[2] != "--slot"
            or args[4] != "--depth"
            or args[6] != "--style"
        ):
            sys.stderr.write(f"{USAGE}\n")
            return 2

        try:
            slot = int(args[3])
        except ValueError:
            lines = format_snapshot_essence_overlay_error(
                args[1],
                "Slot must be an integer",
            )
            sys.stderr.write("\n".join(lines))
            sys.stderr.write("\n")
            return 1

        try:
            discovery = None
            if len(args) == 10:
                if args[8] != "--discovery":
                    sys.stderr.write(f"{USAGE}\n")
                    return 2
                discovery = parse_discovery_value(args[9])
            plan = build_snapshot_essence_overlay_plan_from_file(
                args[1],
                slot=slot,
                depth=args[5],
                style=args[7],
                discovery=discovery,
            )
        except FileNotFoundError:
            lines = format_snapshot_essence_overlay_error(args[1], "File not found")
            sys.stderr.write("\n".join(lines))
            sys.stderr.write("\n")
            return 1
        except (DataError, ValueError) as exc:
            lines = format_snapshot_essence_overlay_error(args[1], str(exc))
            sys.stderr.write("\n".join(lines))
            sys.stderr.write("\n")
            return 1

        sys.stdout.write("\n".join(format_snapshot_essence_overlay_report(plan)))
        sys.stdout.write("\n")
        return 0

    if args and args[0] == "snapshot-essence-send-plan-report":
        from .essence.plan_report import parse_discovery_value
        from .essence.snapshot_send_plan import (
            build_snapshot_essence_send_plan_from_file,
            capture_snapshot_essence_send_mock_messages,
            filter_snapshot_essence_send_plan_to_pad,
            format_snapshot_essence_send_plan_error,
            format_snapshot_essence_send_plan_report,
        )
        from .observability.errors import DataError

        if (
            len(args) not in (8, 10, 12)
            or args[2] != "--slot"
            or args[4] != "--depth"
            or args[6] != "--style"
        ):
            sys.stderr.write(f"{USAGE}\n")
            return 2
        optional_args = _parse_optional_key_value_args(
            args[8:],
            {"--discovery", "--snapshot-pad"},
        )
        if optional_args is None:
            sys.stderr.write(f"{USAGE}\n")
            return 2

        try:
            slot = int(args[3])
        except ValueError:
            lines = format_snapshot_essence_send_plan_error(
                args[1],
                "Slot must be an integer",
            )
            sys.stderr.write("\n".join(lines))
            sys.stderr.write("\n")
            return 1

        try:
            discovery = None
            if "--discovery" in optional_args:
                discovery = parse_discovery_value(optional_args["--discovery"])
            snapshot_pad = None
            if "--snapshot-pad" in optional_args:
                snapshot_pad = int(optional_args["--snapshot-pad"])
            plan = build_snapshot_essence_send_plan_from_file(
                args[1],
                slot=slot,
                depth=args[5],
                style=args[7],
                discovery=discovery,
            )
            if snapshot_pad is not None:
                plan = filter_snapshot_essence_send_plan_to_pad(plan, pad=snapshot_pad)
            sender = capture_snapshot_essence_send_mock_messages(plan)
        except FileNotFoundError:
            lines = format_snapshot_essence_send_plan_error(args[1], "File not found")
            sys.stderr.write("\n".join(lines))
            sys.stderr.write("\n")
            return 1
        except (DataError, ValueError) as exc:
            lines = format_snapshot_essence_send_plan_error(args[1], str(exc))
            sys.stderr.write("\n".join(lines))
            sys.stderr.write("\n")
            return 1

        sys.stdout.write("\n".join(format_snapshot_essence_send_plan_report(plan, sender)))
        sys.stdout.write("\n")
        return 0

    if args and args[0] == "snapshot-essence-guarded-send-dry-run-report":
        from .essence.plan_report import parse_discovery_value
        from .essence.snapshot_guarded_sender import (
            build_snapshot_essence_guarded_send_dry_run,
            format_snapshot_essence_guarded_send_dry_run_report,
            format_snapshot_essence_guarded_send_error,
        )
        from .essence.snapshot_send_plan import (
            build_snapshot_essence_send_plan_from_file,
            filter_snapshot_essence_send_plan_to_pad,
        )
        from .observability.errors import DataError

        if (
            len(args) not in (8, 10, 12)
            or args[2] != "--slot"
            or args[4] != "--depth"
            or args[6] != "--style"
        ):
            sys.stderr.write(f"{USAGE}\n")
            return 2
        optional_args = _parse_optional_key_value_args(
            args[8:],
            {"--discovery", "--snapshot-pad"},
        )
        if optional_args is None:
            sys.stderr.write(f"{USAGE}\n")
            return 2

        try:
            slot = int(args[3])
        except ValueError:
            lines = format_snapshot_essence_guarded_send_error(
                args[1],
                "Slot must be an integer",
            )
            sys.stderr.write("\n".join(lines))
            sys.stderr.write("\n")
            return 1

        try:
            discovery = None
            if "--discovery" in optional_args:
                discovery = parse_discovery_value(optional_args["--discovery"])
            snapshot_pad = None
            if "--snapshot-pad" in optional_args:
                snapshot_pad = int(optional_args["--snapshot-pad"])
            plan = build_snapshot_essence_send_plan_from_file(
                args[1],
                slot=slot,
                depth=args[5],
                style=args[7],
                discovery=discovery,
            )
            if snapshot_pad is not None:
                plan = filter_snapshot_essence_send_plan_to_pad(plan, pad=snapshot_pad)
            result = build_snapshot_essence_guarded_send_dry_run(plan)
        except FileNotFoundError:
            lines = format_snapshot_essence_guarded_send_error(args[1], "File not found")
            sys.stderr.write("\n".join(lines))
            sys.stderr.write("\n")
            return 1
        except (DataError, ValueError) as exc:
            lines = format_snapshot_essence_guarded_send_error(args[1], str(exc))
            sys.stderr.write("\n".join(lines))
            sys.stderr.write("\n")
            return 1

        sys.stdout.write("\n".join(format_snapshot_essence_guarded_send_dry_run_report(result)))
        sys.stdout.write("\n")
        return 0

    if args and args[0] == "rytm-engine-cycle-plan-report":
        from .essence.plan_report import parse_discovery_value
        from .essence.rytm_engine_cycle_plan import (
            build_rytm_engine_cycle_plan,
            format_rytm_engine_cycle_plan_error,
            format_rytm_engine_cycle_plan_report,
        )

        if len(args) not in (3, 5) or args[1] != "--style":
            sys.stderr.write(f"{USAGE}\n")
            return 2

        try:
            discovery = None
            if len(args) == 5:
                if args[3] != "--discovery":
                    sys.stderr.write(f"{USAGE}\n")
                    return 2
                discovery = parse_discovery_value(args[4])
            plan = build_rytm_engine_cycle_plan(args[2], discovery=discovery)
        except ValueError as exc:
            lines = format_rytm_engine_cycle_plan_error(str(exc))
            sys.stderr.write("\n".join(lines))
            sys.stderr.write("\n")
            return 1

        sys.stdout.write("\n".join(format_rytm_engine_cycle_plan_report(plan)))
        sys.stdout.write("\n")
        return 0

    if args and args[0] == "rytm-engine-cycle-starter-plan-report":
        from .essence.plan_report import parse_discovery_value
        from .essence.rytm_engine_cycle_plan import build_rytm_engine_cycle_plan
        from .essence.rytm_engine_cycle_starter_profiles import (
            build_rytm_engine_cycle_starter_plan,
            format_rytm_engine_cycle_starter_plan_error,
            format_rytm_engine_cycle_starter_plan_report,
        )

        if len(args) < 3 or args[1] != "--style" or len(args[3:]) % 2 != 0:
            sys.stderr.write(f"{USAGE}\n")
            return 2

        try:
            discovery = None
            profile = "balanced"
            index = 3
            while index < len(args):
                flag = args[index]
                value = args[index + 1]
                if flag == "--discovery":
                    discovery = parse_discovery_value(value)
                elif flag == "--profile":
                    profile = value
                else:
                    sys.stderr.write(f"{USAGE}\n")
                    return 2
                index += 2
            engine_plan = build_rytm_engine_cycle_plan(args[2], discovery=discovery)
            starter_plan = build_rytm_engine_cycle_starter_plan(
                engine_plan,
                profile=profile,
            )
        except ValueError as exc:
            lines = format_rytm_engine_cycle_starter_plan_error(str(exc))
            sys.stderr.write("\n".join(lines))
            sys.stderr.write("\n")
            return 1

        sys.stdout.write("\n".join(format_rytm_engine_cycle_starter_plan_report(starter_plan)))
        sys.stdout.write("\n")
        return 0

    if args and args[0] == "twelve-pad-mock-runtime-report":
        from .essence.plan_report import parse_discovery_value
        from .essence.twelve_pad_mock_runtime import (
            build_twelve_pad_mock_runtime_plan,
            format_twelve_pad_mock_runtime_error,
            format_twelve_pad_mock_runtime_report,
        )

        if len(args) not in (3, 5) or args[1] != "--style":
            sys.stderr.write(f"{USAGE}\n")
            return 2

        try:
            discovery = None
            if len(args) == 5:
                if args[3] != "--discovery":
                    sys.stderr.write(f"{USAGE}\n")
                    return 2
                discovery = parse_discovery_value(args[4])
            plan = build_twelve_pad_mock_runtime_plan(args[2], discovery=discovery)
        except ValueError as exc:
            lines = format_twelve_pad_mock_runtime_error(str(exc))
            sys.stderr.write("\n".join(lines))
            sys.stderr.write("\n")
            return 1

        sys.stdout.write("\n".join(format_twelve_pad_mock_runtime_report(plan)))
        sys.stdout.write("\n")
        return 0

    if args and args[0] == "twelve-pad-rytm-runtime-report":
        from .essence.plan_report import parse_discovery_value
        from .essence.twelve_pad_rytm_runtime import (
            build_twelve_pad_rytm_runtime_plan,
            format_twelve_pad_rytm_runtime_error,
            format_twelve_pad_rytm_runtime_report,
        )

        if len(args) < 3 or args[1] != "--style" or len(args[3:]) % 2 != 0:
            sys.stderr.write(f"{USAGE}\n")
            return 2

        try:
            discovery = None
            profile = "auto"
            runtime_pad = None
            index = 3
            while index < len(args):
                flag = args[index]
                value = args[index + 1]
                if flag == "--discovery":
                    discovery = parse_discovery_value(value)
                elif flag == "--profile":
                    profile = value
                elif flag == "--runtime-pad":
                    try:
                        runtime_pad = int(value)
                    except ValueError as exc:
                        raise ValueError("Pad must be between 1 and 12") from exc
                else:
                    sys.stderr.write(f"{USAGE}\n")
                    return 2
                index += 2
            plan = build_twelve_pad_rytm_runtime_plan(
                args[2],
                discovery=discovery,
                profile=profile,
                pad=runtime_pad,
            )
        except ValueError as exc:
            lines = format_twelve_pad_rytm_runtime_error(str(exc))
            sys.stderr.write("\n".join(lines))
            sys.stderr.write("\n")
            return 1

        sys.stdout.write("\n".join(format_twelve_pad_rytm_runtime_report(plan)))
        sys.stdout.write("\n")
        return 0

    if args == ["rytm-12-pad-engine-matrix-report"]:
        from .essence.rytm_12_pad_engine_matrix import (
            format_rytm_12_pad_engine_matrix_report,
        )

        sys.stdout.write("\n".join(format_rytm_12_pad_engine_matrix_report()))
        sys.stdout.write("\n")
        return 0

    if args == ["twelve-pad-rytm-runtime-validation-guide"]:
        from .essence.rytm_runtime_validation_guide import (
            format_rytm_runtime_validation_guide,
        )

        sys.stdout.write("\n".join(format_rytm_runtime_validation_guide()))
        sys.stdout.write("\n")
        return 0

    if args == ["analog-four-reference-report"]:
        from .analog_four.reference import format_analog_four_reference_report

        sys.stdout.write("\n".join(format_analog_four_reference_report()))
        sys.stdout.write("\n")
        return 0

    if args and args[0] == "analog-four-runtime-report":
        from .analog_four.runtime_plan import (
            build_analog_four_runtime_plan,
            capture_analog_four_runtime_mock_messages,
            filter_analog_four_runtime_plan_to_track,
            format_analog_four_runtime_error,
            format_analog_four_runtime_report,
        )

        if len(args) % 2 == 0:
            sys.stderr.write(f"{USAGE}\n")
            return 2

        profile = "balanced"
        runtime_track = None
        index = 1
        while index < len(args):
            flag = args[index]
            value = args[index + 1]
            if flag == "--profile":
                profile = value
            elif flag == "--track":
                try:
                    runtime_track = int(value)
                except ValueError:
                    sys.stderr.write(
                        "\n".join(
                            format_analog_four_runtime_error(
                                "Analog Four runtime track must be 1, 2, 3, or 4"
                            )
                        )
                    )
                    sys.stderr.write("\n")
                    return 1
            else:
                sys.stderr.write(f"{USAGE}\n")
                return 2
            index += 2
        try:
            plan = build_analog_four_runtime_plan(profile=profile)
            if runtime_track is not None:
                plan = filter_analog_four_runtime_plan_to_track(plan, track=runtime_track)
        except ValueError as exc:
            sys.stderr.write("\n".join(format_analog_four_runtime_error(str(exc))))
            sys.stderr.write("\n")
            return 1

        sender = capture_analog_four_runtime_mock_messages(plan)
        sys.stdout.write("\n".join(format_analog_four_runtime_report(plan, sender)))
        sys.stdout.write("\n")
        return 0

    if args and args[0] == "analog-four-runtime-guarded-send-dry-run":
        from .analog_four.guarded_runtime_sender import (
            build_analog_four_runtime_guarded_send_dry_run,
            format_analog_four_runtime_guarded_send_dry_run_report,
            format_analog_four_runtime_guarded_send_error,
        )
        from .analog_four.runtime_plan import build_analog_four_runtime_plan

        if len(args) not in (1, 3):
            sys.stderr.write(f"{USAGE}\n")
            return 2
        if len(args) == 3 and args[1] != "--profile":
            sys.stderr.write(f"{USAGE}\n")
            return 2

        profile = "balanced" if len(args) == 1 else args[2]
        try:
            plan = build_analog_four_runtime_plan(profile=profile)
            result = build_analog_four_runtime_guarded_send_dry_run(plan)
        except ValueError as exc:
            sys.stderr.write("\n".join(format_analog_four_runtime_guarded_send_error(str(exc))))
            sys.stderr.write("\n")
            return 1

        sys.stdout.write("\n".join(format_analog_four_runtime_guarded_send_dry_run_report(result)))
        sys.stdout.write("\n")
        return 0

    if args == ["analog-four-runtime-validation-guide"]:
        from .analog_four.runtime_validation_guide import (
            format_analog_four_runtime_validation_guide,
        )

        sys.stdout.write("\n".join(format_analog_four_runtime_validation_guide()))
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
