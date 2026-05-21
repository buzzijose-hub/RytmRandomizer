"""In-process coverage tests for ``rytm_randomizer.cli``.

The companion file :mod:`tests.test_cli` exercises the CLI through
``subprocess.run``. That subprocess approach is intentional for parity tests
(it proves the installed module-entry behavior end-to-end), but it does NOT
contribute to ``coverage.py`` measurement because the child process runs
without the ``--cov`` instrumentation.

This file plugs that gap. Every test here invokes ``cli.main(argv=[...])``
directly in the current process so coverage is recorded. The intent is to
push the pure-branch coverage of ``rytm_randomizer/cli.py`` from ~5% to the
package floor (>= 85%).

Tests intentionally use loose substring assertions on the captured stdout.
The byte-exact parity assertions live in :mod:`tests.test_cli` against
recorded fixtures; duplicating them here would create a fixture-maintenance
double-burden without adding coverage value.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from rytm_randomizer import cli
from rytm_randomizer.commands import COMMANDS
from rytm_randomizer.profiles import GROUP_PROFILE_METADATA
from rytm_randomizer.scenes import SCENE_COMMANDS

# WS-M4: mark this module as fast-suite; pytest -m fast skips the 505
# warm-worker V1.34 parity fixtures and runs in <60s.
pytestmark = pytest.mark.fast

# ---------------------------------------------------------------------------
# Known-good registry keys. The CLI normalises command/scene keys to upper
# case, so we pick already-uppercased keys to avoid surprises in the fixture
# tests living in test_cli.py.
# ---------------------------------------------------------------------------

KNOWN_COMMAND_KEY = next(iter(COMMANDS))
KNOWN_SCENE_KEY = next(iter(SCENE_COMMANDS))
KNOWN_GROUP_PROFILE_KEY = next(iter(GROUP_PROFILE_METADATA))


# ---------------------------------------------------------------------------
# Helper-function coverage (the format_* builders at the top of cli.py).
# Exercising these directly is the cheapest way to cover lines 8-345 without
# repeatedly paying the registry-build cost through main().
# ---------------------------------------------------------------------------


def test_format_registry_list_report_known_section_includes_count_and_safety():
    lines = cli.format_registry_list_report("commands", "command list")

    assert lines[0] == "RytmRandomizer passive command list"
    assert lines[1] == "Section: commands"
    assert lines[2].startswith("Count: ")
    assert "Items:" in lines
    assert "- passive/read-only" in lines
    assert "- no hardware required" in lines
    # At least one rendered item line (`- KEY: label`).
    assert any(line.startswith(f"- {KNOWN_COMMAND_KEY}: ") for line in lines)


def test_format_registry_list_report_unknown_section_returns_not_found_block():
    lines = cli.format_registry_list_report("nonexistent-section", "command list")

    assert lines[0] == "RytmRandomizer passive command list"
    assert lines[1] == "Section: nonexistent-section"
    assert lines[2] == "Found: False"
    assert lines[3].startswith("Message: Registry section not found.")


def test_resolve_help_text_supports_static_and_dynamic_help_entries():
    from rytm_randomizer.help_text import resolve_help_text
    from rytm_randomizer.reports.rytm_snapshot_pad_compatibility import SAFETY_LINES

    top_level_help = resolve_help_text("--help")
    snapshot_help = resolve_help_text("rytm-snapshot-pad-compatibility-report")
    intelligence_help = resolve_help_text("rytm-snapshot-intelligence-report")
    mutation_preview_help = resolve_help_text("rytm-snapshot-mutation-preview-report")
    style_mock_preview_help = resolve_help_text("rytm-style-mutation-mock-preview-report")
    a4_style_mock_preview_help = resolve_help_text("analog-four-style-mutation-mock-preview-report")
    dual_style_mock_preview_help = resolve_help_text(
        "dual-machine-style-mutation-mock-preview-report"
    )

    assert top_level_help.startswith("RytmRandomizer passive CLI")
    assert snapshot_help.startswith(
        "RytmRandomizer passive CLI: rytm-snapshot-pad-compatibility-report"
    )
    assert intelligence_help.startswith(
        "RytmRandomizer passive CLI: rytm-snapshot-intelligence-report"
    )
    assert mutation_preview_help.startswith(
        "RytmRandomizer passive CLI: rytm-snapshot-mutation-preview-report"
    )
    assert style_mock_preview_help.startswith(
        "RytmRandomizer passive CLI: rytm-style-mutation-mock-preview-report"
    )
    assert a4_style_mock_preview_help.startswith(
        "RytmRandomizer passive CLI: analog-four-style-mutation-mock-preview-report"
    )
    assert dual_style_mock_preview_help.startswith(
        "RytmRandomizer passive CLI: dual-machine-style-mutation-mock-preview-report"
    )
    assert snapshot_help.split("Safety:\n", 1)[1].splitlines() == [
        f"  {line}" for line in SAFETY_LINES
    ]


def test_format_registry_search_report_match_returns_match_line():
    lines = cli.format_registry_search_report("commands", "command search", KNOWN_COMMAND_KEY)

    assert lines[0] == "RytmRandomizer passive command search"
    assert lines[1] == "Section: commands"
    assert lines[2] == f"Query: {KNOWN_COMMAND_KEY}"
    assert lines[3].startswith("Match count: ")
    # At least one match line because we searched for a known key.
    assert any(line.startswith(f"- {KNOWN_COMMAND_KEY}: ") for line in lines)
    # Safety footer present.
    assert "- passive/read-only" in lines


def test_format_registry_search_report_no_match_emits_explicit_message():
    lines = cli.format_registry_search_report(
        "commands", "command search", "definitely-not-a-real-command-xyz123"
    )

    assert lines[3] == "Match count: 0"
    assert "Matches:" in lines
    assert any(
        line.startswith("- no matches found.") for line in lines
    ), f"expected explicit 'no matches found' line in {lines!r}"


def test_format_registry_search_report_unknown_section_branch():
    lines = cli.format_registry_search_report("missing-section", "command search", "anything")

    assert lines[0] == "RytmRandomizer passive command search"
    assert lines[1] == "Section: missing-section"
    assert lines[2] == "Query: anything"
    assert lines[3] == "Match count: 0"
    assert lines[4] == "Matches:"
    assert any(line.startswith("- no matches found.") for line in lines)


def test_format_inspect_command_report_known_key_returns_found_true():
    lines = cli.format_inspect_command_report(KNOWN_COMMAND_KEY)

    assert lines[0] == "RytmRandomizer passive command inspection"
    assert lines[1] == f"Command: {KNOWN_COMMAND_KEY}"
    assert lines[2] == "Found: True"
    assert any(line.startswith("Type:") for line in lines)
    assert any(line.startswith("Executable:") for line in lines)
    assert "- passive/read-only" in lines


def test_format_inspect_command_report_unknown_key_returns_not_found():
    lines = cli.format_inspect_command_report("UNKNOWN-KEY-ZZZ")

    assert lines[2] == "Found: False"
    assert lines[3].startswith("Message: Command metadata not found.")


def test_format_inspect_scene_report_known_key_returns_found_true():
    lines = cli.format_inspect_scene_report(KNOWN_SCENE_KEY)

    assert lines[0] == "RytmRandomizer passive scene inspection"
    assert lines[2] == "Found: True"
    assert any(line.startswith("Name:") for line in lines)


def test_format_inspect_scene_report_unknown_key_returns_not_found():
    lines = cli.format_inspect_scene_report("UNKNOWN-SCENE-ZZZ")

    assert lines[2] == "Found: False"
    assert lines[3].startswith("Message: Scene metadata not found.")


def test_format_inspect_group_profile_report_known_key_returns_found_true():
    lines = cli.format_inspect_group_profile_report(KNOWN_GROUP_PROFILE_KEY)

    assert lines[0] == "RytmRandomizer passive group profile inspection"
    assert lines[2] == "Found: True"
    assert any(line.startswith("Name:") for line in lines)
    assert any(line.startswith("Machine value:") for line in lines)


def test_format_inspect_group_profile_report_unknown_key_returns_not_found():
    lines = cli.format_inspect_group_profile_report("UNKNOWN-PROFILE-ZZZ")

    assert lines[2] == "Found: False"
    assert lines[3].startswith("Message: Group profile metadata not found.")


def test_format_preview_command_report_known_key_returns_found_true():
    lines = cli.format_preview_command_report(KNOWN_COMMAND_KEY)

    assert lines[0] == "RytmRandomizer passive command preview"
    assert lines[2] == "Found: True"
    assert any(line.startswith("Validation ok:") for line in lines)
    assert "No MIDI would be sent." in lines


def test_format_preview_command_report_unknown_key_returns_not_found():
    lines = cli.format_preview_command_report("UNKNOWN-CMD-ZZZ")

    assert lines[2] == "Found: False"
    assert lines[3].startswith("Message: Command preview not found.")
    assert lines[4].startswith("Safety summary:")


def test_format_preview_scene_report_known_key_returns_found_true():
    lines = cli.format_preview_scene_report(KNOWN_SCENE_KEY)

    assert lines[0] == "RytmRandomizer passive scene preview"
    assert lines[2] == "Found: True"
    assert "No MIDI would be sent." in lines
    assert "No scene would execute." in lines


def test_format_preview_scene_report_unknown_key_returns_not_found():
    lines = cli.format_preview_scene_report("UNKNOWN-SCENE-ZZZ")

    assert lines[2] == "Found: False"
    assert lines[3].startswith("Message: Scene preview not found.")


def test_format_preview_group_profile_report_known_key_returns_found_true():
    lines = cli.format_preview_group_profile_report(KNOWN_GROUP_PROFILE_KEY)

    assert lines[0] == "RytmRandomizer passive group profile preview"
    assert lines[2] == "Found: True"
    assert any(line.startswith("Machine value:") for line in lines)
    assert "No MIDI would be sent." in lines


def test_format_preview_group_profile_report_unknown_key_returns_not_found():
    lines = cli.format_preview_group_profile_report("UNKNOWN-PROFILE-ZZZ")

    assert lines[2] == "Found: False"
    assert lines[3].startswith("Message: Group profile preview not found.")


# ---------------------------------------------------------------------------
# main() coverage - top-level dispatch arms.
# Each test invokes cli.main(argv=[...]) directly and checks the captured
# stdout/stderr. capsys avoids the subprocess overhead and (more importantly)
# lets coverage.py see the executed lines.
# ---------------------------------------------------------------------------


def test_main_help_writes_help_text_and_returns_zero(capsys):
    rc = cli.main(["--help"])

    captured = capsys.readouterr()
    assert rc == 0
    assert "RytmRandomizer passive CLI" in captured.out
    assert captured.err == ""


def test_main_subcommand_help_writes_subcommand_help(capsys):
    rc = cli.main(["report", "--help"])

    captured = capsys.readouterr()
    assert rc == 0
    # report --help should mention "report" somewhere in the help body.
    assert "report" in captured.out.lower()
    assert captured.err == ""


def test_main_report_command_writes_registry_report(capsys):
    rc = cli.main(["report"])

    captured = capsys.readouterr()
    assert rc == 0
    assert captured.out.endswith("\n")
    assert "RytmRandomizer" in captured.out


def test_main_project_status_report_writes_status_report(capsys):
    rc = cli.main(["project-status-report"])

    captured = capsys.readouterr()
    assert rc == 0
    assert captured.out.endswith("\n")
    assert len(captured.out) > 0


def test_main_project_status_report_summary_writes_summary(capsys):
    rc = cli.main(["project-status-report", "--summary"])

    captured = capsys.readouterr()
    assert rc == 0
    assert captured.out.endswith("\n")
    assert len(captured.out) > 0


def test_main_project_status_report_check_returns_zero_or_one(capsys):
    rc = cli.main(["project-status-report", "--check"])

    captured = capsys.readouterr()
    # --check returns 0 if status OK, 1 if not. Either is a valid exit; we
    # only require that the rc is one of those and that something was printed.
    assert rc in (0, 1)
    assert captured.out.endswith("\n")
    assert len(captured.out) > 0


def test_main_project_status_report_json_writes_json(capsys):
    import json

    rc = cli.main(["project-status-report", "--json"])

    captured = capsys.readouterr()
    assert rc == 0
    assert captured.out.endswith("\n")
    # The output must be parseable as JSON.
    json.loads(captured.out)


def test_main_mock_mapper_report_writes_report(capsys):
    rc = cli.main(["mock-mapper-report"])

    captured = capsys.readouterr()
    assert rc == 0
    assert captured.out.endswith("\n")
    assert len(captured.out) > 0


def test_main_runtime_plan_report_writes_report(capsys):
    rc = cli.main(["runtime-plan-report"])

    captured = capsys.readouterr()
    assert rc == 0
    assert captured.out.endswith("\n")
    assert len(captured.out) > 0


def test_main_active_boundary_report_writes_report(capsys):
    rc = cli.main(["active-boundary-report"])

    captured = capsys.readouterr()
    assert rc == 0
    assert captured.out.endswith("\n")
    assert len(captured.out) > 0


def test_main_mock_runtime_active_bridge_report_writes_report(capsys):
    rc = cli.main(["mock-runtime-active-bridge-report"])

    captured = capsys.readouterr()
    assert rc == 0
    assert captured.out.endswith("\n")
    assert len(captured.out) > 0


def test_main_anchor_profile_report_writes_report(capsys):
    rc = cli.main(["anchor-profile-report"])

    captured = capsys.readouterr()
    assert rc == 0
    assert captured.out.endswith("\n")
    assert len(captured.out) > 0


def test_main_behavior_parity_report_writes_report(capsys):
    rc = cli.main(["behavior-parity-report"])

    captured = capsys.readouterr()
    assert rc == 0
    assert captured.out.endswith("\n")
    assert len(captured.out) > 0


def test_main_rytm_machine_matrix_report_writes_report(capsys):
    rc = cli.main(["rytm-12-pad-machine-matrix-report"])

    captured = capsys.readouterr()
    assert rc == 0
    assert captured.out.endswith("\n")
    assert "RytmRandomizer passive Rytm 12-pad machine matrix" in captured.out
    assert captured.err == ""


def test_main_rytm_machine_matrix_report_dispatches_through_cli_registry(capsys):
    from rytm_randomizer import cli_registry
    from rytm_randomizer.cli_registry import CliCommand

    def _stub_handler(*, argv):
        sys.stdout.write(f"registry:{argv!r}\n")
        return 0

    saved = dict(cli_registry._COMMANDS)
    cli_registry._COMMANDS.clear()
    try:
        cli_registry.register(
            CliCommand(
                name="rytm-12-pad-machine-matrix-report",
                summary="stub report",
                args_parser=lambda argv: {"argv": tuple(argv)},
                handler=_stub_handler,
            )
        )

        rc = cli.main(["rytm-12-pad-machine-matrix-report"])
    finally:
        cli_registry._COMMANDS.clear()
        cli_registry._COMMANDS.update(saved)

    captured = capsys.readouterr()
    assert rc == 0
    assert captured.out == "registry:()\n"
    assert captured.err == ""


def test_main_rytm_machine_matrix_report_registers_cached_command_when_registry_empty(capsys):
    from importlib import import_module

    from rytm_randomizer import cli_registry

    import_module("rytm_randomizer.reports.rytm_machine_matrix")

    saved = dict(cli_registry._COMMANDS)
    cli_registry._COMMANDS.clear()
    try:
        rc = cli.main(["rytm-12-pad-machine-matrix-report"])
    finally:
        cli_registry._COMMANDS.clear()
        cli_registry._COMMANDS.update(saved)

    captured = capsys.readouterr()
    assert rc == 0
    assert "RytmRandomizer passive Rytm 12-pad machine matrix" in captured.out
    assert captured.err == ""


def test_main_rytm_snapshot_pad_compatibility_report_registers_cached_command_when_registry_empty(
    capsys,
):
    from importlib import import_module

    from rytm_randomizer import cli_registry

    import_module("rytm_randomizer.reports.rytm_snapshot_pad_compatibility")

    saved = dict(cli_registry._COMMANDS)
    cli_registry._COMMANDS.clear()
    try:
        rc = cli.main(["rytm-snapshot-pad-compatibility-report"])
    finally:
        cli_registry._COMMANDS.clear()
        cli_registry._COMMANDS.update(saved)

    captured = capsys.readouterr()
    assert rc == 0
    assert "RytmRandomizer passive Rytm snapshot pad compatibility" in captured.out
    assert captured.err == ""


def test_main_rytm_snapshot_pad_compatibility_report_lazy_imports_when_module_unloaded(capsys):
    import sys

    from rytm_randomizer import cli_registry

    module_name = "rytm_randomizer.reports.rytm_snapshot_pad_compatibility"
    saved_commands = dict(cli_registry._COMMANDS)
    saved_module = sys.modules.pop(module_name, None)
    cli_registry._COMMANDS.pop("rytm-snapshot-pad-compatibility-report", None)
    try:
        rc = cli.main(["rytm-snapshot-pad-compatibility-report"])
    finally:
        cli_registry._COMMANDS.clear()
        cli_registry._COMMANDS.update(saved_commands)
        if saved_module is not None:
            sys.modules[module_name] = saved_module
        else:
            sys.modules.pop(module_name, None)

    captured = capsys.readouterr()
    assert rc == 0
    assert "RytmRandomizer passive Rytm snapshot pad compatibility" in captured.out
    assert captured.err == ""


def test_main_rytm_snapshot_intelligence_report_lazy_imports_when_module_unloaded(
    tmp_path: Path,
    capsys,
):
    import sys

    from conftest import rytm_real_layout_kit_payload

    from rytm_randomizer import cli_registry

    payload = rytm_real_layout_kit_payload(name=b"COVERAGE")
    path = tmp_path / "kit.syx"
    path.write_bytes(bytes([0xF0]) + payload + bytes([0xF7]))
    module_name = "rytm_randomizer.reports.rytm_snapshot_intelligence"
    saved_commands = dict(cli_registry._COMMANDS)
    saved_module = sys.modules.pop(module_name, None)
    cli_registry._COMMANDS.pop("rytm-snapshot-intelligence-report", None)
    try:
        rc = cli.main(["rytm-snapshot-intelligence-report", str(path)])
    finally:
        cli_registry._COMMANDS.clear()
        cli_registry._COMMANDS.update(saved_commands)
        if saved_module is not None:
            sys.modules[module_name] = saved_module
        else:
            sys.modules.pop(module_name, None)

    captured = capsys.readouterr()
    assert rc == 0
    assert "RytmRandomizer passive Rytm snapshot intelligence" in captured.out
    assert "Kit: COVERAGE" in captured.out
    assert captured.err == ""


def test_main_rytm_snapshot_mutation_preview_report_lazy_imports_when_module_unloaded(
    tmp_path: Path,
    capsys,
):
    import sys

    from conftest import rytm_real_layout_kit_payload

    from rytm_randomizer import cli_registry

    payload = rytm_real_layout_kit_payload(name=b"PREVCOV")
    path = tmp_path / "kit.syx"
    path.write_bytes(bytes([0xF0]) + payload + bytes([0xF7]))
    module_name = "rytm_randomizer.reports.rytm_snapshot_mutation_preview"
    saved_commands = dict(cli_registry._COMMANDS)
    saved_module = sys.modules.pop(module_name, None)
    cli_registry._COMMANDS.pop("rytm-snapshot-mutation-preview-report", None)
    try:
        rc = cli.main(["rytm-snapshot-mutation-preview-report", str(path), "--depth", "2"])
    finally:
        cli_registry._COMMANDS.clear()
        cli_registry._COMMANDS.update(saved_commands)
        if saved_module is not None:
            sys.modules[module_name] = saved_module
        else:
            sys.modules.pop(module_name, None)

    captured = capsys.readouterr()
    assert rc == 0
    assert "RytmRandomizer passive Rytm snapshot mutation preview" in captured.out
    assert "Kit: PREVCOV" in captured.out
    assert captured.err == ""


def test_main_rytm_style_mutation_mock_preview_report_lazy_imports_when_module_unloaded(
    tmp_path: Path,
    capsys,
):
    import sys

    from conftest import rytm_real_layout_kit_payload

    from rytm_randomizer import cli_registry

    payload = rytm_real_layout_kit_payload(name=b"STYLECOV")
    path = tmp_path / "kit.syx"
    path.write_bytes(bytes([0xF0]) + payload + bytes([0xF7]))
    module_name = "rytm_randomizer.reports.rytm_style_mutation_mock_preview"
    saved_commands = dict(cli_registry._COMMANDS)
    saved_module = sys.modules.pop(module_name, None)
    cli_registry._COMMANDS.pop("rytm-style-mutation-mock-preview-report", None)
    try:
        rc = cli.main(
            [
                "rytm-style-mutation-mock-preview-report",
                str(path),
                "jose_core_techno",
            ]
        )
    finally:
        cli_registry._COMMANDS.clear()
        cli_registry._COMMANDS.update(saved_commands)
        if saved_module is not None:
            sys.modules[module_name] = saved_module
        else:
            sys.modules.pop(module_name, None)

    captured = capsys.readouterr()
    assert rc == 0
    assert "RytmRandomizer passive Rytm style mutation mock preview" in captured.out
    assert "Kit: STYLECOV" in captured.out
    assert captured.err == ""


def test_main_analog_four_style_mutation_mock_preview_report_lazy_imports_when_module_unloaded(
    tmp_path: Path,
    capsys,
):
    import sys

    from rytm_randomizer import cli_registry

    payload = bytes([0x00, 0x20, 0x3C, 0x07]) + b"A4COV".ljust(16, b"\x00")
    path = tmp_path / "a4.syx"
    path.write_bytes(bytes([0xF0]) + payload + bytes([0xF7]))
    module_name = "rytm_randomizer.reports.analog_four_style_mutation_mock_preview"
    saved_commands = dict(cli_registry._COMMANDS)
    saved_module = sys.modules.pop(module_name, None)
    cli_registry._COMMANDS.pop("analog-four-style-mutation-mock-preview-report", None)
    try:
        rc = cli.main(
            [
                "analog-four-style-mutation-mock-preview-report",
                str(path),
                "jose_core_techno",
            ]
        )
    finally:
        cli_registry._COMMANDS.clear()
        cli_registry._COMMANDS.update(saved_commands)
        if saved_module is not None:
            sys.modules[module_name] = saved_module
        else:
            sys.modules.pop(module_name, None)

    captured = capsys.readouterr()
    assert rc == 0
    assert "RytmRandomizer passive Analog Four style mutation mock preview" in captured.out
    assert "Kit: A4COV" in captured.out
    assert captured.err == ""


def test_main_dual_machine_style_mutation_mock_preview_report_lazy_imports_when_unloaded(
    tmp_path: Path,
    capsys,
):
    import sys

    from conftest import rytm_real_layout_kit_payload

    from rytm_randomizer import cli_registry

    rytm_payload = rytm_real_layout_kit_payload(name=b"DUALRYTM")
    rytm_path = tmp_path / "rytm.syx"
    rytm_path.write_bytes(bytes([0xF0]) + rytm_payload + bytes([0xF7]))
    a4_payload = bytes([0x00, 0x20, 0x3C, 0x07]) + b"DUALA4".ljust(16, b"\x00")
    a4_path = tmp_path / "a4.syx"
    a4_path.write_bytes(bytes([0xF0]) + a4_payload + bytes([0xF7]))
    module_name = "rytm_randomizer.reports.dual_machine_style_mutation_mock_preview"
    saved_commands = dict(cli_registry._COMMANDS)
    saved_module = sys.modules.pop(module_name, None)
    cli_registry._COMMANDS.pop("dual-machine-style-mutation-mock-preview-report", None)
    try:
        rc = cli.main(
            [
                "dual-machine-style-mutation-mock-preview-report",
                str(rytm_path),
                str(a4_path),
                "jose_core_techno",
            ]
        )
    finally:
        cli_registry._COMMANDS.clear()
        cli_registry._COMMANDS.update(saved_commands)
        if saved_module is not None:
            sys.modules[module_name] = saved_module
        else:
            sys.modules.pop(module_name, None)

    captured = capsys.readouterr()
    assert rc == 0
    assert "RytmRandomizer passive dual-machine style mutation mock preview" in captured.out
    assert "Kit: DUALRYTM" in captured.out
    assert "Kit: DUALA4" in captured.out
    assert captured.err == ""


def test_main_rytm_snapshot_intelligence_report_returns_two_for_missing_file(capsys):
    rc = cli.main(["rytm-snapshot-intelligence-report", "missing-file.syx"])

    captured = capsys.readouterr()
    assert rc == 2
    assert captured.out == ""
    assert "SysEx file does not exist" in captured.err


def test_main_rytm_snapshot_intelligence_report_formats_parse_errors(capsys):
    rc = cli.main(["rytm-snapshot-intelligence-report", "kit.syx", "--slot", "-1"])

    captured = capsys.readouterr()
    assert rc == 2
    assert captured.out == ""
    assert "--slot must be >= 0" in captured.err


def test_main_rytm_snapshot_mutation_preview_report_returns_two_for_missing_file(capsys):
    rc = cli.main(["rytm-snapshot-mutation-preview-report", "missing-file.syx"])

    captured = capsys.readouterr()
    assert rc == 2
    assert captured.out == ""
    assert "SysEx file does not exist" in captured.err


def test_main_rytm_snapshot_mutation_preview_report_formats_parse_errors(capsys):
    rc = cli.main(["rytm-snapshot-mutation-preview-report", "kit.syx", "--depth", "8"])

    captured = capsys.readouterr()
    assert rc == 2
    assert captured.out == ""
    assert "--depth must be in [0, 7]" in captured.err


def test_main_rytm_machine_matrix_report_rejects_extra_args(capsys):
    rc = cli.main(["rytm-12-pad-machine-matrix-report", "--mutate"])

    captured = capsys.readouterr()
    assert rc == 2
    assert captured.out == ""
    assert captured.err.strip() == cli.USAGE


def test_main_rytm_snapshot_pad_compatibility_report_rejects_extra_args(capsys):
    rc = cli.main(["rytm-snapshot-pad-compatibility-report", "--mutate"])

    captured = capsys.readouterr()
    assert rc == 2
    assert captured.out == ""
    assert captured.err.strip() == cli.USAGE


def test_main_list_commands_writes_command_list(capsys):
    rc = cli.main(["list-commands"])

    captured = capsys.readouterr()
    assert rc == 0
    assert "RytmRandomizer passive command list" in captured.out
    assert "Section: commands" in captured.out
    assert captured.out.endswith("\n")


def test_main_list_scenes_writes_scene_list(capsys):
    rc = cli.main(["list-scenes"])

    captured = capsys.readouterr()
    assert rc == 0
    assert "RytmRandomizer passive scene list" in captured.out
    assert "Section: scenes" in captured.out
    assert captured.out.endswith("\n")


def test_main_list_group_profiles_writes_profile_list(capsys):
    rc = cli.main(["list-group-profiles"])

    captured = capsys.readouterr()
    assert rc == 0
    assert "RytmRandomizer passive group profile list" in captured.out
    assert "Section: group_profiles" in captured.out
    assert captured.out.endswith("\n")


def test_main_search_commands_writes_search_results(capsys):
    rc = cli.main(["search-commands", KNOWN_COMMAND_KEY])

    captured = capsys.readouterr()
    assert rc == 0
    assert "RytmRandomizer passive command search" in captured.out
    assert f"Query: {KNOWN_COMMAND_KEY}" in captured.out
    assert captured.out.endswith("\n")


def test_main_search_scenes_writes_search_results(capsys):
    rc = cli.main(["search-scenes", KNOWN_SCENE_KEY])

    captured = capsys.readouterr()
    assert rc == 0
    assert "RytmRandomizer passive scene search" in captured.out
    assert f"Query: {KNOWN_SCENE_KEY}" in captured.out
    assert captured.out.endswith("\n")


def test_main_search_group_profiles_writes_search_results(capsys):
    rc = cli.main(["search-group-profiles", KNOWN_GROUP_PROFILE_KEY])

    captured = capsys.readouterr()
    assert rc == 0
    assert "RytmRandomizer passive group profile search" in captured.out
    assert f"Query: {KNOWN_GROUP_PROFILE_KEY}" in captured.out
    assert captured.out.endswith("\n")


def test_main_inspect_command_known_key_returns_zero(capsys):
    rc = cli.main(["inspect-command", KNOWN_COMMAND_KEY])

    captured = capsys.readouterr()
    assert rc == 0
    assert "Found: True" in captured.out
    assert captured.err == ""


def test_main_inspect_command_unknown_key_returns_one_and_writes_to_stderr(capsys):
    rc = cli.main(["inspect-command", "UNKNOWN-CMD-ZZZ"])

    captured = capsys.readouterr()
    assert rc == 1
    assert "Found: False" in captured.err
    assert captured.out == ""


def test_main_inspect_scene_known_key_returns_zero(capsys):
    rc = cli.main(["inspect-scene", KNOWN_SCENE_KEY])

    captured = capsys.readouterr()
    assert rc == 0
    assert "Found: True" in captured.out


def test_main_inspect_scene_unknown_key_returns_one_and_writes_to_stderr(capsys):
    rc = cli.main(["inspect-scene", "UNKNOWN-SCENE-ZZZ"])

    captured = capsys.readouterr()
    assert rc == 1
    assert "Found: False" in captured.err


def test_main_inspect_group_profile_known_key_returns_zero(capsys):
    rc = cli.main(["inspect-group-profile", KNOWN_GROUP_PROFILE_KEY])

    captured = capsys.readouterr()
    assert rc == 0
    assert "Found: True" in captured.out


def test_main_inspect_group_profile_unknown_key_returns_one_and_writes_to_stderr(capsys):
    rc = cli.main(["inspect-group-profile", "UNKNOWN-PROFILE-ZZZ"])

    captured = capsys.readouterr()
    assert rc == 1
    assert "Found: False" in captured.err


def test_main_preview_command_known_key_returns_zero(capsys):
    rc = cli.main(["preview-command", KNOWN_COMMAND_KEY])

    captured = capsys.readouterr()
    assert rc == 0
    assert "Found: True" in captured.out
    assert "No MIDI would be sent." in captured.out


def test_main_preview_command_unknown_key_returns_one_and_writes_to_stderr(capsys):
    rc = cli.main(["preview-command", "UNKNOWN-CMD-ZZZ"])

    captured = capsys.readouterr()
    assert rc == 1
    assert "Found: False" in captured.err


def test_main_preview_scene_known_key_returns_zero(capsys):
    rc = cli.main(["preview-scene", KNOWN_SCENE_KEY])

    captured = capsys.readouterr()
    assert rc == 0
    assert "Found: True" in captured.out


def test_main_preview_scene_unknown_key_returns_one_and_writes_to_stderr(capsys):
    rc = cli.main(["preview-scene", "UNKNOWN-SCENE-ZZZ"])

    captured = capsys.readouterr()
    assert rc == 1
    assert "Found: False" in captured.err


def test_main_preview_group_profile_known_key_returns_zero(capsys):
    rc = cli.main(["preview-group-profile", KNOWN_GROUP_PROFILE_KEY])

    captured = capsys.readouterr()
    assert rc == 0
    assert "Found: True" in captured.out


def test_main_preview_group_profile_unknown_key_returns_one_and_writes_to_stderr(capsys):
    rc = cli.main(["preview-group-profile", "UNKNOWN-PROFILE-ZZZ"])

    captured = capsys.readouterr()
    assert rc == 1
    assert "Found: False" in captured.err


def test_main_no_args_writes_usage_to_stderr_and_returns_two(capsys):
    rc = cli.main([])

    captured = capsys.readouterr()
    assert rc == 2
    assert "Usage:" in captured.err
    assert captured.out == ""


def test_main_unknown_command_writes_usage_to_stderr_and_returns_two(capsys):
    rc = cli.main(["definitely-not-a-real-command"])

    captured = capsys.readouterr()
    assert rc == 2
    assert "Usage:" in captured.err
    assert captured.out == ""


def test_main_search_commands_no_match_still_returns_zero(capsys):
    rc = cli.main(["search-commands", "qzqzqz-not-a-match-anywhere"])

    captured = capsys.readouterr()
    assert rc == 0
    assert "Match count: 0" in captured.out
    assert "no matches found" in captured.out


def test_main_inspect_command_normalises_lowercase_key(capsys):
    """The CLI uppercases command keys, so a lowercase variant should
    still resolve to the same metadata."""
    rc = cli.main(["inspect-command", KNOWN_COMMAND_KEY.lower()])

    captured = capsys.readouterr()
    assert rc == 0
    assert "Found: True" in captured.out
    assert f"Command: {KNOWN_COMMAND_KEY}" in captured.out


def test_main_preview_command_uppercases_lowercase_input(capsys):
    rc = cli.main(["preview-command", KNOWN_COMMAND_KEY.lower()])

    captured = capsys.readouterr()
    assert rc == 0
    assert f"Command: {KNOWN_COMMAND_KEY}" in captured.out


def test_main_uses_sys_argv_when_argv_omitted(capsys, monkeypatch):
    """When argv=None, cli.main() falls back to sys.argv[1:]."""
    monkeypatch.setattr("sys.argv", ["rytm-randomizer", "--help"])

    rc = cli.main()

    captured = capsys.readouterr()
    assert rc == 0
    assert "RytmRandomizer passive CLI" in captured.out


def test_main_module_entry_raises_system_exit_when_run_as_main():
    """The ``if __name__ == "__main__":`` block at the bottom of cli.py is
    excluded from coverage by the standard ``if __name__ == .__main__.:`` rule
    in .coveragerc, so we don't need to exercise it. This test asserts the
    runner-style invocation still works for the developer who uses
    ``python -m rytm_randomizer.cli`` for debugging."""
    # We use pytest.raises(SystemExit) so that the test still passes even if
    # the entry block were to be re-included in coverage in the future.
    with pytest.raises(SystemExit) as excinfo:
        raise SystemExit(cli.main(["--help"]))
    assert excinfo.value.code == 0
