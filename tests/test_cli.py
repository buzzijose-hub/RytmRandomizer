import json
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
USAGE = (
    "Usage: python -m rytm_randomizer.cli [--help] | report | "
    "project-status-report [--summary|--json|--check] | mock-mapper-report | runtime-plan-report | "
    "active-boundary-report | mock-runtime-active-bridge-report | "
    "anchor-profile-report | behavior-parity-report | performance-snapshot-target-report --target <target> | sysex-kit-bank-report <path> | "
    "sysex-project-report <path> | sysex-kit-snapshot-report <path> --slot <1-128> | "
    "sysex-snapshot-mutation-plan-report <path> --slot <1-128> --depth <micro|groove|strong> | "
    "sysex-snapshot-mock-runtime-report <path> --slot <1-128> --depth <micro|groove|strong> | "
    "rytm-controlled-diff-report <before> <after> --slot <1-128> (--pad <1-12>|--all-pads) --limit <n> | "
    "dual-machine-mock-bridge-report <path> --slot <1-128> --depth <micro|groove|strong> [--analog-four-path <path> --analog-four-slot <slot>] [--target <target>] [--analog-four-profile <profile>] | "
    "dual-machine-live-snapshot-readiness-report <path> --slot <1-128> --depth <micro|groove|strong> [--analog-four-path <path> --analog-four-slot <slot>] [--target <target>] [--analog-four-profile <profile>] | "
    "dual-machine-active-send-plan-report <path> --slot <1-128> --depth <micro|groove|strong> [--analog-four-path <path> --analog-four-slot <slot>] [--target <target>] [--analog-four-profile <profile>] | "
    "dual-machine-guarded-send-dry-run-report <path> --slot <1-128> --depth <micro|groove|strong> [--analog-four-path <path> --analog-four-slot <slot>] [--target <target>] [--analog-four-profile <profile>] | "
    "analog-four-kit-snapshot-report <path> --slot <1-128> | "
    "analog-four-snapshot-mutation-plan-report <path> --slot <1-128> --depth <micro|groove|strong> | "
    "analog-four-snapshot-mock-runtime-report <path> --slot <1-128> --depth <micro|groove|strong> | "
    "analog-four-offset-candidate-report <path> (--track <1-4>|--all-tracks) --limit <n> | "
    "analog-four-controlled-diff-report <before> <after> --slot <1-128> --track <1-4> --limit <n> | "
    "essence-plan-report (--tags <csv>|--description <text>) --discovery <0..1> | inspect-command <key> | "
    "essence-application-readiness-report --mode <mode> (--tags <csv>|--description <text>|--style <text>) [--discovery <0..1>] [--snapshot <status>|--fixture <key>] | "
    "style-intent-report --style <text> [--discovery <0..1>] | "
    "snapshot-essence-overlay-report <path> --slot <1-128> --depth <micro|groove|strong> --style <text> [--discovery <0..1>] | "
    "snapshot-essence-send-plan-report <path> --slot <1-128> --depth <micro|groove|strong> --style <text> [--discovery <0..1>] | "
    "snapshot-essence-guarded-send-dry-run-report <path> --slot <1-128> --depth <micro|groove|strong> --style <text> [--discovery <0..1>] | "
    "rytm-engine-cycle-plan-report --style <text> [--discovery <0..1>] | "
    "rytm-engine-cycle-starter-plan-report --style <text> [--discovery <0..1>] [--profile <profile>] | "
    "twelve-pad-mock-runtime-report --style <text> [--discovery <0..1>] | "
    "analog-four-reference-report | "
    "inspect-scene <key> | inspect-group-profile <key> | list-commands | "
    "list-scenes | list-group-profiles | search-commands <query> | "
    "search-scenes <query> | search-group-profiles <query> | preview-command <key> | "
    "preview-scene <key> | preview-group-profile <key>"
)


def normalize_newlines(text):
    return text.replace("\r\n", "\n").replace("\r", "\n").rstrip("\n")


def expected_report_text():
    return normalize_newlines(
        (FIXTURES_DIR / "registry_report_expected.txt").read_text(encoding="utf-8")
    )


def fixture_text(filename):
    return normalize_newlines((FIXTURES_DIR / filename).read_text(encoding="utf-8"))


def run_cli(*args):
    return subprocess.run(
        [sys.executable, "-m", "rytm_randomizer.cli", *args],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_importing_cli_prints_nothing():
    result = subprocess.run(
        [sys.executable, "-c", "import rytm_randomizer.cli"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_top_level_help_exits_zero_and_matches_fixture():
    result = run_cli("--help")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text("cli_help_expected.txt")
    assert result.stderr == ""


def test_report_help_exits_zero_and_matches_fixture():
    result = run_cli("report", "--help")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text("cli_report_help_expected.txt")
    assert result.stderr == ""


def test_project_status_report_help_exits_zero_and_matches_fixture():
    result = run_cli("project-status-report", "--help")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text(
        "cli_project_status_report_help_expected.txt"
    )
    assert result.stderr == ""


def test_mock_mapper_report_help_exits_zero_and_matches_fixture():
    result = run_cli("mock-mapper-report", "--help")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text(
        "cli_mock_mapper_report_help_expected.txt"
    )
    assert result.stderr == ""


def test_runtime_plan_report_help_exits_zero_and_matches_fixture():
    result = run_cli("runtime-plan-report", "--help")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text(
        "cli_runtime_plan_report_help_expected.txt"
    )
    assert result.stderr == ""


def test_active_boundary_report_help_exits_zero_and_matches_fixture():
    result = run_cli("active-boundary-report", "--help")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text(
        "cli_active_boundary_report_help_expected.txt"
    )
    assert result.stderr == ""


def test_mock_runtime_active_bridge_report_help_exits_zero_and_matches_fixture():
    result = run_cli("mock-runtime-active-bridge-report", "--help")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text(
        "cli_mock_runtime_active_bridge_report_help_expected.txt"
    )
    assert result.stderr == ""


def test_anchor_profile_report_help_exits_zero_and_matches_fixture():
    result = run_cli("anchor-profile-report", "--help")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text(
        "cli_anchor_profile_report_help_expected.txt"
    )
    assert result.stderr == ""


def test_behavior_parity_report_help_exits_zero_and_matches_fixture():
    result = run_cli("behavior-parity-report", "--help")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text(
        "cli_behavior_parity_report_help_expected.txt"
    )
    assert result.stderr == ""


def test_analog_four_reference_report_help_exits_zero():
    result = run_cli("analog-four-reference-report", "--help")

    assert result.returncode == 0
    assert "RytmRandomizer passive CLI: analog-four-reference-report" in result.stdout
    assert "Analog Four MKII" in result.stdout
    assert "no MIDI sending" in result.stdout
    assert "no port opening" in result.stdout
    assert result.stderr == ""


def test_analog_four_kit_snapshot_report_help_exits_zero():
    result = run_cli("analog-four-kit-snapshot-report", "--help")

    assert result.returncode == 0
    assert "RytmRandomizer passive CLI: analog-four-kit-snapshot-report" in result.stdout
    assert "Analog Four kit" in result.stdout
    assert "saved_parameter_offsets_unmapped" in result.stdout
    assert "no MIDI sending" in result.stdout
    assert result.stderr == ""


def test_analog_four_snapshot_mutation_plan_report_help_exits_zero():
    result = run_cli("analog-four-snapshot-mutation-plan-report", "--help")

    assert result.returncode == 0
    assert (
        "RytmRandomizer passive CLI: analog-four-snapshot-mutation-plan-report"
        in result.stdout
    )
    assert "candidate_unverified" in result.stdout
    assert "no parameter names claimed" in result.stdout
    assert "no MIDI sending" in result.stdout
    assert result.stderr == ""


def test_analog_four_snapshot_mock_runtime_report_help_exits_zero():
    result = run_cli("analog-four-snapshot-mock-runtime-report", "--help")

    assert result.returncode == 0
    assert (
        "RytmRandomizer passive CLI: analog-four-snapshot-mock-runtime-report"
        in result.stdout
    )
    assert "saved-offset candidate" in result.stdout
    assert "no CC mapping claimed" in result.stdout
    assert result.stderr == ""


def test_analog_four_offset_candidate_report_help_exits_zero():
    result = run_cli("analog-four-offset-candidate-report", "--help")

    assert result.returncode == 0
    assert "RytmRandomizer passive CLI: analog-four-offset-candidate-report" in result.stdout
    assert "--all-tracks" in result.stdout
    assert "candidate_unverified" in result.stdout
    assert "no parameter names claimed" in result.stdout
    assert "no MIDI sending" in result.stdout
    assert result.stderr == ""


def test_analog_four_controlled_diff_report_help_exits_zero():
    result = run_cli("analog-four-controlled-diff-report", "--help")

    assert result.returncode == 0
    assert "RytmRandomizer passive CLI: analog-four-controlled-diff-report" in result.stdout
    assert "controlled comparison only" in result.stdout
    assert "candidate_unverified" in result.stdout
    assert "no MIDI sending" in result.stdout
    assert result.stderr == ""


def test_rytm_controlled_diff_report_help_exits_zero():
    result = run_cli("rytm-controlled-diff-report", "--help")

    assert result.returncode == 0
    assert "RytmRandomizer passive CLI: rytm-controlled-diff-report" in result.stdout
    assert "--all-pads" in result.stdout
    assert "mapped saved parameters only" in result.stdout
    assert "no MIDI sending" in result.stdout
    assert result.stderr == ""


def test_dual_machine_mock_bridge_report_help_exits_zero():
    result = run_cli("dual-machine-mock-bridge-report", "--help")

    assert result.returncode == 0
    assert "RytmRandomizer passive CLI: dual-machine-mock-bridge-report" in result.stdout
    assert "Rytm + Analog Four" in result.stdout
    assert "--target <rytm|analog-four|both>" in result.stdout
    assert "--analog-four-profile <profile>" in result.stdout
    assert "--analog-four-path <path>" in result.stdout
    assert "--analog-four-slot <1-128>" in result.stdout
    assert "untouched" in result.stdout
    assert "mock sender only" in result.stdout
    assert "no MIDI sending" in result.stdout
    assert result.stderr == ""


def test_dual_machine_live_snapshot_readiness_report_help_exits_zero():
    result = run_cli("dual-machine-live-snapshot-readiness-report", "--help")

    assert result.returncode == 0
    assert (
        "RytmRandomizer passive CLI: dual-machine-live-snapshot-readiness-report"
        in result.stdout
    )
    assert "readiness gate" in result.stdout
    assert "--analog-four-path <path>" in result.stdout
    assert "--analog-four-profile <profile>" in result.stdout
    assert "candidate_unverified" in result.stdout
    assert "no MIDI sending" in result.stdout
    assert result.stderr == ""


def test_dual_machine_active_send_plan_report_help_exits_zero():
    result = run_cli("dual-machine-active-send-plan-report", "--help")

    assert result.returncode == 0
    assert "RytmRandomizer passive CLI: dual-machine-active-send-plan-report" in result.stdout
    assert "active send plan" in result.stdout
    assert "--analog-four-path <path>" in result.stdout
    assert "--analog-four-profile <profile>" in result.stdout
    assert "saved-offset candidate events are blocked" in result.stdout
    assert "no MIDI sending" in result.stdout
    assert result.stderr == ""


def test_dual_machine_guarded_send_dry_run_report_help_exits_zero():
    result = run_cli("dual-machine-guarded-send-dry-run-report", "--help")

    assert result.returncode == 0
    assert "RytmRandomizer passive CLI: dual-machine-guarded-send-dry-run-report" in result.stdout
    assert "guarded send dry-run" in result.stdout
    assert "--analog-four-path <path>" in result.stdout
    assert "--analog-four-profile <profile>" in result.stdout
    assert "blocked plans emit no partial messages" in result.stdout
    assert "no MIDI sending" in result.stdout
    assert result.stderr == ""


def test_rytm_engine_cycle_plan_report_help_exits_zero():
    result = run_cli("rytm-engine-cycle-plan-report", "--help")

    assert result.returncode == 0
    assert "RytmRandomizer passive CLI: rytm-engine-cycle-plan-report" in result.stdout
    assert "engine-cycle candidates" in result.stdout
    assert "--style <text>" in result.stdout
    assert "--discovery <0..1>" in result.stdout
    assert "machine_selectable means engine switch only" in result.stdout
    assert "no MIDI sending" in result.stdout
    assert result.stderr == ""


def test_rytm_engine_cycle_starter_plan_report_help_exits_zero():
    result = run_cli("rytm-engine-cycle-starter-plan-report", "--help")

    assert result.returncode == 0
    assert (
        "RytmRandomizer passive CLI: rytm-engine-cycle-starter-plan-report"
        in result.stdout
    )
    assert "starter shaping" in result.stdout
    assert "--style <text>" in result.stdout
    assert "--discovery <0..1>" in result.stdout
    assert "--profile <profile>" in result.stdout
    assert "common filter/amp starter values only" in result.stdout
    assert "no MIDI sending" in result.stdout
    assert result.stderr == ""


def test_sysex_project_report_help_exits_zero():
    result = run_cli("sysex-project-report", "--help")

    assert result.returncode == 0
    assert "RytmRandomizer passive CLI: sysex-project-report" in result.stdout
    assert "whole-project" in result.stdout
    assert "no live SysEx receive" in result.stdout
    assert "no SysEx writes" in result.stdout
    assert result.stderr == ""


def test_sysex_kit_snapshot_report_help_exits_zero():
    result = run_cli("sysex-kit-snapshot-report", "--help")

    assert result.returncode == 0
    assert "RytmRandomizer passive CLI: sysex-kit-snapshot-report" in result.stdout
    assert "12-pad snapshot" in result.stdout
    assert "saved parameter baselines" in result.stdout
    assert "no live SysEx receive" in result.stdout
    assert result.stderr == ""


def test_sysex_snapshot_mutation_plan_report_help_exits_zero():
    result = run_cli("sysex-snapshot-mutation-plan-report", "--help")

    assert result.returncode == 0
    assert "RytmRandomizer passive CLI: sysex-snapshot-mutation-plan-report" in result.stdout
    assert "bounded deterministic deltas" in result.stdout
    assert "not load anchors" in result.stdout
    assert "no MIDI sending" in result.stdout
    assert result.stderr == ""


def test_sysex_snapshot_mock_runtime_report_help_exits_zero():
    result = run_cli("sysex-snapshot-mock-runtime-report", "--help")

    assert result.returncode == 0
    assert "RytmRandomizer passive CLI: sysex-snapshot-mock-runtime-report" in result.stdout
    assert "mock sender" in result.stdout
    assert "captured-value" in result.stdout
    assert "no MIDI sending" in result.stdout
    assert result.stderr == ""


def test_performance_snapshot_target_report_help_exits_zero():
    result = run_cli("performance-snapshot-target-report", "--help")

    assert result.returncode == 0
    assert "RytmRandomizer passive CLI: performance-snapshot-target-report" in result.stdout
    assert "--target <rytm|analog-four|both>" in result.stdout
    assert "untouched" in result.stdout
    assert "no MIDI sending" in result.stdout
    assert result.stderr == ""


def test_inspect_command_help_exits_zero_and_matches_fixture():
    result = run_cli("inspect-command", "--help")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text(
        "cli_inspect_command_help_expected.txt"
    )
    assert result.stderr == ""


def test_inspect_scene_help_exits_zero_and_matches_fixture():
    result = run_cli("inspect-scene", "--help")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text("cli_inspect_scene_help_expected.txt")
    assert result.stderr == ""


def test_inspect_group_profile_help_exits_zero_and_matches_fixture():
    result = run_cli("inspect-group-profile", "--help")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text(
        "cli_inspect_group_profile_help_expected.txt"
    )
    assert result.stderr == ""


def test_list_commands_help_exits_zero_and_matches_fixture():
    result = run_cli("list-commands", "--help")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text("cli_list_commands_help_expected.txt")
    assert result.stderr == ""


def test_list_scenes_help_exits_zero_and_matches_fixture():
    result = run_cli("list-scenes", "--help")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text("cli_list_scenes_help_expected.txt")
    assert result.stderr == ""


def test_list_group_profiles_help_exits_zero_and_matches_fixture():
    result = run_cli("list-group-profiles", "--help")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text(
        "cli_list_group_profiles_help_expected.txt"
    )
    assert result.stderr == ""


def test_search_commands_help_exits_zero_and_matches_fixture():
    result = run_cli("search-commands", "--help")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text(
        "cli_search_commands_help_expected.txt"
    )
    assert result.stderr == ""


def test_search_scenes_help_exits_zero_and_matches_fixture():
    result = run_cli("search-scenes", "--help")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text("cli_search_scenes_help_expected.txt")
    assert result.stderr == ""


def test_search_group_profiles_help_exits_zero_and_matches_fixture():
    result = run_cli("search-group-profiles", "--help")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text(
        "cli_search_group_profiles_help_expected.txt"
    )
    assert result.stderr == ""


def test_preview_command_help_exits_zero_and_matches_fixture():
    result = run_cli("preview-command", "--help")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text(
        "cli_preview_command_help_expected.txt"
    )
    assert result.stderr == ""


def test_preview_scene_help_exits_zero_and_matches_fixture():
    result = run_cli("preview-scene", "--help")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text("cli_preview_scene_help_expected.txt")
    assert result.stderr == ""


def test_preview_group_profile_help_exits_zero_and_matches_fixture():
    result = run_cli("preview-group-profile", "--help")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text(
        "cli_preview_group_profile_help_expected.txt"
    )
    assert result.stderr == ""


def test_report_command_exits_zero_and_matches_fixture():
    result = run_cli("report")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == expected_report_text()
    assert result.stderr == ""


def test_project_status_report_command_exits_zero_and_matches_fixture():
    result = run_cli("project-status-report")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text(
        "cli_project_status_report_expected.txt"
    )
    assert result.stderr == ""


def test_project_status_report_summary_command_exits_zero_and_matches_fixture():
    result = run_cli("project-status-report", "--summary")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text(
        "cli_project_status_report_summary_expected.txt"
    )
    assert result.stderr == ""


def test_project_status_report_check_command_exits_zero_and_matches_fixture():
    result = run_cli("project-status-report", "--check")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text(
        "cli_project_status_report_check_expected.txt"
    )
    assert result.stderr == ""


def test_project_status_report_json_command_exits_zero_and_returns_json():
    result = run_cli("project-status-report", "--json")

    assert result.returncode == 0
    parsed = json.loads(result.stdout)
    assert parsed["title"] == "RytmRandomizer Project Status Report"
    assert parsed["phase"]["creative_identity_candidate"] == "KitForge"
    assert parsed["behavior_parity"]["accepted_packet_count"] == 12
    assert parsed["runtime_plan"]["runtime_execution"] == "absent"
    assert parsed["active_boundary"]["active_cli_behavior"] == "absent"
    assert parsed["mock_runtime_active_bridge"]["emits_messages"] is False
    assert parsed["safety"]["real_midi"] == "present_behind_arm_flag"
    assert parsed["safety"]["port_opening"] == "present_behind_arm_flag"
    assert parsed["safety"]["active_execution"] == "present_behind_arm_flag"
    assert parsed["safety"]["default_mode"] == "passive"
    assert parsed["safety"]["hardware_required"] is False
    assert parsed["convergence"]["active_execution"] == "present"
    assert parsed["convergence"]["active_execution_gate"] == "--arm flag"
    assert parsed["convergence"]["default_mode"] == "passive"
    assert parsed["source"]["in_memory_only"] is True
    assert parsed["source"]["writes_files"] is False
    assert result.stderr == ""


def test_mock_mapper_report_command_exits_zero_and_matches_fixture():
    result = run_cli("mock-mapper-report")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text("cli_mock_mapper_report_expected.txt")
    assert result.stderr == ""


def test_runtime_plan_report_command_exits_zero_and_matches_fixture():
    result = run_cli("runtime-plan-report")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text("cli_runtime_plan_report_expected.txt")
    assert result.stderr == ""


def test_active_boundary_report_command_exits_zero_and_matches_fixture():
    result = run_cli("active-boundary-report")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text(
        "cli_active_boundary_report_expected.txt"
    )
    assert result.stderr == ""


def test_mock_runtime_active_bridge_report_command_exits_zero_and_matches_fixture():
    result = run_cli("mock-runtime-active-bridge-report")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text(
        "cli_mock_runtime_active_bridge_report_expected.txt"
    )
    assert result.stderr == ""


def test_anchor_profile_report_command_exits_zero_and_matches_fixture():
    result = run_cli("anchor-profile-report")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text(
        "cli_anchor_profile_report_expected.txt"
    )
    assert result.stderr == ""


def test_behavior_parity_report_command_exits_zero_and_matches_fixture():
    result = run_cli("behavior-parity-report")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text(
        "cli_behavior_parity_report_expected.txt"
    )
    assert result.stderr == ""


def test_analog_four_reference_report_cli_exits_zero():
    result = run_cli("analog-four-reference-report")

    assert result.returncode == 0
    assert "RytmRandomizer passive Analog Four MKII Reference Report" in result.stdout
    assert "Source: https://midi.guide/d/elektron/analog-four-mkii/" in result.stdout
    assert "Parameter count: 230" in result.stdout
    assert "Reference-known starter groups:" in result.stdout
    assert "- filter_pressure:" in result.stdout
    assert "- real Analog Four MIDI sending" in result.stdout
    assert "- no MIDI sending" in result.stdout
    assert result.stderr == ""


def test_report_command_is_deterministic():
    first = run_cli("report")
    second = run_cli("report")

    assert first.returncode == 0
    assert second.returncode == 0
    assert normalize_newlines(first.stdout) == normalize_newlines(second.stdout)
    assert first.stderr == ""
    assert second.stderr == ""


def test_project_status_report_command_is_deterministic():
    first = run_cli("project-status-report")
    second = run_cli("project-status-report")

    assert first.returncode == 0
    assert second.returncode == 0
    assert normalize_newlines(first.stdout) == normalize_newlines(second.stdout)
    assert first.stderr == ""
    assert second.stderr == ""


def test_project_status_report_summary_command_is_deterministic():
    first = run_cli("project-status-report", "--summary")
    second = run_cli("project-status-report", "--summary")

    assert first.returncode == 0
    assert second.returncode == 0
    assert normalize_newlines(first.stdout) == normalize_newlines(second.stdout)
    assert first.stderr == ""
    assert second.stderr == ""


def test_project_status_report_check_command_is_deterministic():
    first = run_cli("project-status-report", "--check")
    second = run_cli("project-status-report", "--check")

    assert first.returncode == 0
    assert second.returncode == 0
    assert normalize_newlines(first.stdout) == normalize_newlines(second.stdout)
    assert first.stderr == ""
    assert second.stderr == ""


def test_project_status_report_json_command_is_deterministic():
    first = run_cli("project-status-report", "--json")
    second = run_cli("project-status-report", "--json")

    assert first.returncode == 0
    assert second.returncode == 0
    assert json.loads(first.stdout) == json.loads(second.stdout)
    assert first.stdout == second.stdout
    assert first.stderr == ""
    assert second.stderr == ""


def test_mock_mapper_report_command_is_deterministic():
    first = run_cli("mock-mapper-report")
    second = run_cli("mock-mapper-report")

    assert first.returncode == 0
    assert second.returncode == 0
    assert normalize_newlines(first.stdout) == normalize_newlines(second.stdout)
    assert first.stderr == ""
    assert second.stderr == ""


def test_runtime_plan_report_command_is_deterministic():
    first = run_cli("runtime-plan-report")
    second = run_cli("runtime-plan-report")

    assert first.returncode == 0
    assert second.returncode == 0
    assert normalize_newlines(first.stdout) == normalize_newlines(second.stdout)
    assert first.stderr == ""
    assert second.stderr == ""


def test_active_boundary_report_command_is_deterministic():
    first = run_cli("active-boundary-report")
    second = run_cli("active-boundary-report")

    assert first.returncode == 0
    assert second.returncode == 0
    assert normalize_newlines(first.stdout) == normalize_newlines(second.stdout)
    assert first.stderr == ""
    assert second.stderr == ""


def test_mock_runtime_active_bridge_report_command_is_deterministic():
    first = run_cli("mock-runtime-active-bridge-report")
    second = run_cli("mock-runtime-active-bridge-report")

    assert first.returncode == 0
    assert second.returncode == 0
    assert normalize_newlines(first.stdout) == normalize_newlines(second.stdout)
    assert first.stderr == ""
    assert second.stderr == ""


def test_anchor_profile_report_command_is_deterministic():
    first = run_cli("anchor-profile-report")
    second = run_cli("anchor-profile-report")

    assert first.returncode == 0
    assert second.returncode == 0
    assert normalize_newlines(first.stdout) == normalize_newlines(second.stdout)
    assert first.stderr == ""
    assert second.stderr == ""


def test_behavior_parity_report_command_is_deterministic():
    first = run_cli("behavior-parity-report")
    second = run_cli("behavior-parity-report")

    assert first.returncode == 0
    assert second.returncode == 0
    assert normalize_newlines(first.stdout) == normalize_newlines(second.stdout)
    assert first.stderr == ""
    assert second.stderr == ""


def test_top_level_help_exposes_no_active_execution_commands():
    result = run_cli("--help")
    output = normalize_newlines(result.stdout)

    assert result.returncode == 0
    assert "execute-command" not in output
    assert "send-command" not in output
    assert "hardware-test" not in output
    assert "open-port" not in output
    assert "send-midi" not in output


def test_cli_source_does_not_evaluate_active_boundary_or_construct_sender():
    import inspect

    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))

    import rytm_randomizer.cli as cli

    source = inspect.getsource(cli)

    assert "evaluate_mock_active_boundary" not in source
    assert "evaluate_mock_runtime_active_bridge" not in source
    assert "MockMidiSender" not in source
    assert "evaluate_anchor_profile_behavior" not in source
    assert "evaluate_pad1_lane_behavior" not in source


def test_project_status_report_command_imports_no_real_midi_libraries():
    script = "\n".join(
        [
            "import runpy",
            "import sys",
            "sys.argv = ['rytm_randomizer.cli', 'project-status-report']",
            "runpy.run_module('rytm_randomizer.cli', run_name='__main__')",
            "assert 'mido' not in sys.modules",
            "assert 'rtmidi' not in sys.modules",
        ]
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "RytmRandomizer Project Status Report" in result.stdout
    assert result.stderr == ""


def test_project_status_report_summary_command_imports_no_real_midi_libraries():
    script = "\n".join(
        [
            "import runpy",
            "import sys",
            "sys.argv = ['rytm_randomizer.cli', 'project-status-report', '--summary']",
            "runpy.run_module('rytm_randomizer.cli', run_name='__main__')",
            "assert 'mido' not in sys.modules",
            "assert 'rtmidi' not in sys.modules",
        ]
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "RytmRandomizer Project Status Summary" in result.stdout
    assert result.stderr == ""


def test_project_status_report_check_command_imports_no_real_midi_libraries():
    script = "\n".join(
        [
            "import runpy",
            "import sys",
            "sys.argv = ['rytm_randomizer.cli', 'project-status-report', '--check']",
            "runpy.run_module('rytm_randomizer.cli', run_name='__main__')",
            "assert 'mido' not in sys.modules",
            "assert 'rtmidi' not in sys.modules",
        ]
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "RytmRandomizer Project Status Check" in result.stdout
    assert result.stderr == ""


def test_project_status_report_json_command_imports_no_real_midi_libraries():
    script = "\n".join(
        [
            "import runpy",
            "import sys",
            "sys.argv = ['rytm_randomizer.cli', 'project-status-report', '--json']",
            "runpy.run_module('rytm_randomizer.cli', run_name='__main__')",
            "assert 'mido' not in sys.modules",
            "assert 'rtmidi' not in sys.modules",
        ]
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert '"title": "RytmRandomizer Project Status Report"' in result.stdout
    assert result.stderr == ""


def test_mock_mapper_report_command_imports_no_real_midi_libraries():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys\n"
                "from contextlib import redirect_stdout\n"
                "from io import StringIO\n"
                "from rytm_randomizer.cli import main\n"
                "with redirect_stdout(StringIO()):\n"
                "    code = main(['mock-mapper-report'])\n"
                "assert code == 0\n"
                "assert 'mido' not in sys.modules\n"
                "assert 'rtmidi' not in sys.modules\n"
            ),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_runtime_plan_report_command_imports_no_real_midi_libraries():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys\n"
                "from contextlib import redirect_stdout\n"
                "from io import StringIO\n"
                "from rytm_randomizer.cli import main\n"
                "with redirect_stdout(StringIO()):\n"
                "    code = main(['runtime-plan-report'])\n"
                "assert code == 0\n"
                "assert 'mido' not in sys.modules\n"
                "assert 'rtmidi' not in sys.modules\n"
            ),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_active_boundary_report_command_imports_no_real_midi_libraries():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys\n"
                "from contextlib import redirect_stdout\n"
                "from io import StringIO\n"
                "from rytm_randomizer.cli import main\n"
                "with redirect_stdout(StringIO()):\n"
                "    code = main(['active-boundary-report'])\n"
                "assert code == 0\n"
                "assert 'mido' not in sys.modules\n"
                "assert 'rtmidi' not in sys.modules\n"
            ),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_mock_runtime_active_bridge_report_command_imports_no_real_midi_libraries():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys\n"
                "from contextlib import redirect_stdout\n"
                "from io import StringIO\n"
                "from rytm_randomizer.cli import main\n"
                "with redirect_stdout(StringIO()):\n"
                "    code = main(['mock-runtime-active-bridge-report'])\n"
                "assert code == 0\n"
                "assert 'mido' not in sys.modules\n"
                "assert 'rtmidi' not in sys.modules\n"
            ),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_mock_runtime_active_bridge_report_command_does_not_load_bridge_or_mock_midi():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys\n"
                "from contextlib import redirect_stdout\n"
                "from io import StringIO\n"
                "sys.modules.pop('rytm_randomizer.mock_runtime_active_bridge', None)\n"
                "sys.modules.pop('rytm_randomizer.mock_midi', None)\n"
                "from rytm_randomizer.cli import main\n"
                "with redirect_stdout(StringIO()):\n"
                "    code = main(['mock-runtime-active-bridge-report'])\n"
                "assert code == 0\n"
                "assert 'rytm_randomizer.mock_runtime_active_bridge' not in sys.modules\n"
                "assert 'rytm_randomizer.mock_midi' not in sys.modules\n"
                "assert 'mido' not in sys.modules\n"
                "assert 'rtmidi' not in sys.modules\n"
            ),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_importing_cli_does_not_load_behavior_report_modules():
    # After WS-P the per-report shim modules were collapsed into the unified
    # ``rytm_randomizer.reports`` module. Importing ``rytm_randomizer.cli``
    # must still keep the consolidated reports module (and any
    # report-adjacent behavior modules) out of ``sys.modules`` until a report
    # subcommand actually triggers a lazy import.
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys\n"
                "import rytm_randomizer.cli\n"
                "assert 'rytm_randomizer.reports' not in sys.modules\n"
                "assert 'rytm_randomizer.behavior_selected_isolated_pad' not in sys.modules\n"
                "assert 'rytm_randomizer.selected_isolated_pad_runtime_state' not in sys.modules\n"
                "assert 'rytm_randomizer.mock_midi' not in sys.modules\n"
                "assert 'mido' not in sys.modules\n"
                "assert 'rtmidi' not in sys.modules\n"
            ),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_importing_cli_does_not_load_runtime_or_bridge_report_modules():
    # After WS-P the runtime-plan and bridge report shim modules were
    # collapsed into the unified ``rytm_randomizer.reports`` module. The
    # lazy-load contract still applies: ``rytm_randomizer.reports`` must not
    # appear in ``sys.modules`` from importing ``rytm_randomizer.cli`` alone.
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys\n"
                "import rytm_randomizer.cli\n"
                "assert 'rytm_randomizer.reports' not in sys.modules\n"
                "assert 'rytm_randomizer.runtime_plan' not in sys.modules\n"
                "assert 'rytm_randomizer.mock_runtime_active_bridge' not in sys.modules\n"
                "assert 'rytm_randomizer.mock_midi' not in sys.modules\n"
                "assert 'mido' not in sys.modules\n"
                "assert 'rtmidi' not in sys.modules\n"
            ),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_importing_cli_does_not_load_registry_report_module():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys\n"
                "import rytm_randomizer.cli\n"
                "assert 'rytm_randomizer.registry_report' not in sys.modules\n"
                "assert 'mido' not in sys.modules\n"
                "assert 'rtmidi' not in sys.modules\n"
            ),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_importing_cli_does_not_load_passive_metadata_modules():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys\n"
                "import rytm_randomizer.cli\n"
                "assert 'rytm_randomizer.commands' not in sys.modules\n"
                "assert 'rytm_randomizer.scenes' not in sys.modules\n"
                "assert 'rytm_randomizer.profiles' not in sys.modules\n"
                "assert 'rytm_randomizer.registry' not in sys.modules\n"
                "assert 'rytm_randomizer.inspection' not in sys.modules\n"
                "assert 'rytm_randomizer.validation' not in sys.modules\n"
                "assert 'mido' not in sys.modules\n"
                "assert 'rtmidi' not in sys.modules\n"
            ),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_anchor_profile_report_command_imports_no_real_midi_libraries():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys\n"
                "from contextlib import redirect_stdout\n"
                "from io import StringIO\n"
                "from rytm_randomizer.cli import main\n"
                "with redirect_stdout(StringIO()):\n"
                "    code = main(['anchor-profile-report'])\n"
                "assert code == 0\n"
                "assert 'mido' not in sys.modules\n"
                "assert 'rtmidi' not in sys.modules\n"
            ),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_behavior_parity_report_command_imports_no_real_midi_libraries():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys\n"
                "from contextlib import redirect_stdout\n"
                "from io import StringIO\n"
                "from rytm_randomizer.cli import main\n"
                "with redirect_stdout(StringIO()):\n"
                "    code = main(['behavior-parity-report'])\n"
                "assert code == 0\n"
                "assert 'mido' not in sys.modules\n"
                "assert 'rtmidi' not in sys.modules\n"
            ),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_inspect_command_known_key_exits_zero_and_matches_fixture():
    result = run_cli("inspect-command", "P3A")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text(
        "cli_inspect_command_known_expected.txt"
    )
    assert result.stderr == ""


def test_inspect_command_known_key_is_deterministic():
    first = run_cli("inspect-command", "P3A")
    second = run_cli("inspect-command", "P3A")

    assert first.returncode == 0
    assert second.returncode == 0
    assert normalize_newlines(first.stdout) == normalize_newlines(second.stdout)
    assert first.stderr == ""
    assert second.stderr == ""


def test_inspect_scene_known_key_exits_zero_and_matches_fixture():
    result = run_cli("inspect-scene", "S1A")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text("cli_inspect_scene_known_expected.txt")
    assert result.stderr == ""


def test_inspect_scene_known_key_is_deterministic():
    first = run_cli("inspect-scene", "S1A")
    second = run_cli("inspect-scene", "S1A")

    assert first.returncode == 0
    assert second.returncode == 0
    assert normalize_newlines(first.stdout) == normalize_newlines(second.stdout)
    assert first.stderr == ""
    assert second.stderr == ""


def test_inspect_group_profile_known_key_exits_zero_and_matches_fixture():
    result = run_cli("inspect-group-profile", "2")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text(
        "cli_inspect_group_profile_known_expected.txt"
    )
    assert result.stderr == ""


def test_inspect_group_profile_known_key_is_deterministic():
    first = run_cli("inspect-group-profile", "2")
    second = run_cli("inspect-group-profile", "2")

    assert first.returncode == 0
    assert second.returncode == 0
    assert normalize_newlines(first.stdout) == normalize_newlines(second.stdout)
    assert first.stderr == ""
    assert second.stderr == ""


def test_list_commands_exits_zero_and_matches_fixture():
    result = run_cli("list-commands")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text("cli_list_commands_expected.txt")
    assert result.stderr == ""


def test_list_scenes_exits_zero_and_matches_fixture():
    result = run_cli("list-scenes")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text("cli_list_scenes_expected.txt")
    assert result.stderr == ""


def test_list_group_profiles_exits_zero_and_matches_fixture():
    result = run_cli("list-group-profiles")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text("cli_list_group_profiles_expected.txt")
    assert result.stderr == ""


def test_list_commands_are_deterministic():
    first = run_cli("list-commands")
    second = run_cli("list-commands")

    assert first.returncode == 0
    assert second.returncode == 0
    assert normalize_newlines(first.stdout) == normalize_newlines(second.stdout)
    assert first.stderr == ""
    assert second.stderr == ""


def test_list_scenes_are_deterministic():
    first = run_cli("list-scenes")
    second = run_cli("list-scenes")

    assert first.returncode == 0
    assert second.returncode == 0
    assert normalize_newlines(first.stdout) == normalize_newlines(second.stdout)
    assert first.stderr == ""
    assert second.stderr == ""


def test_list_group_profiles_are_deterministic():
    first = run_cli("list-group-profiles")
    second = run_cli("list-group-profiles")

    assert first.returncode == 0
    assert second.returncode == 0
    assert normalize_newlines(first.stdout) == normalize_newlines(second.stdout)
    assert first.stderr == ""
    assert second.stderr == ""


def test_search_commands_known_query_exits_zero_and_matches_fixture():
    result = run_cli("search-commands", "guarded")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text(
        "cli_search_commands_known_expected.txt"
    )
    assert result.stderr == ""


def test_search_scenes_known_query_exits_zero_and_matches_fixture():
    result = run_cli("search-scenes", "Wild")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text("cli_search_scenes_known_expected.txt")
    assert result.stderr == ""


def test_search_group_profiles_known_query_exits_zero_and_matches_fixture():
    result = run_cli("search-group-profiles", "Hard")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text(
        "cli_search_group_profiles_known_expected.txt"
    )
    assert result.stderr == ""


def test_search_commands_no_match_exits_zero_and_matches_fixture():
    result = run_cli("search-commands", "NO_MATCH")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text(
        "cli_search_commands_none_expected.txt"
    )
    assert result.stderr == ""


def test_search_scenes_no_match_exits_zero_and_matches_fixture():
    result = run_cli("search-scenes", "NO_MATCH")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text("cli_search_scenes_none_expected.txt")
    assert result.stderr == ""


def test_search_group_profiles_no_match_exits_zero_and_matches_fixture():
    result = run_cli("search-group-profiles", "NO_MATCH")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text(
        "cli_search_group_profiles_none_expected.txt"
    )
    assert result.stderr == ""


def test_search_commands_are_case_insensitive_and_deterministic():
    first = run_cli("search-commands", "guarded")
    second = run_cli("search-commands", "GUARDED")

    assert first.returncode == 0
    assert second.returncode == 0
    assert normalize_newlines(first.stdout).replace("Query: guarded", "Query: QUERY") == (
        normalize_newlines(second.stdout).replace("Query: GUARDED", "Query: QUERY")
    )
    assert first.stderr == ""
    assert second.stderr == ""


def test_search_scenes_are_deterministic():
    first = run_cli("search-scenes", "Wild")
    second = run_cli("search-scenes", "Wild")

    assert first.returncode == 0
    assert second.returncode == 0
    assert normalize_newlines(first.stdout) == normalize_newlines(second.stdout)
    assert first.stderr == ""
    assert second.stderr == ""


def test_search_group_profiles_are_deterministic():
    first = run_cli("search-group-profiles", "Hard")
    second = run_cli("search-group-profiles", "Hard")

    assert first.returncode == 0
    assert second.returncode == 0
    assert normalize_newlines(first.stdout) == normalize_newlines(second.stdout)
    assert first.stderr == ""
    assert second.stderr == ""


def test_preview_command_known_key_exits_zero_and_matches_fixture():
    result = run_cli("preview-command", "J")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text(
        "cli_preview_command_known_expected.txt"
    )
    assert result.stderr == ""


def test_preview_command_known_key_is_deterministic():
    first = run_cli("preview-command", "J")
    second = run_cli("preview-command", "J")

    assert first.returncode == 0
    assert second.returncode == 0
    assert normalize_newlines(first.stdout) == normalize_newlines(second.stdout)
    assert first.stderr == ""
    assert second.stderr == ""


def test_preview_scene_known_key_exits_zero_and_matches_fixture():
    result = run_cli("preview-scene", "S1A")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text("cli_preview_scene_known_expected.txt")
    assert result.stderr == ""


def test_preview_scene_known_key_is_deterministic():
    first = run_cli("preview-scene", "S1A")
    second = run_cli("preview-scene", "S1A")

    assert first.returncode == 0
    assert second.returncode == 0
    assert normalize_newlines(first.stdout) == normalize_newlines(second.stdout)
    assert first.stderr == ""
    assert second.stderr == ""


def test_preview_group_profile_known_key_exits_zero_and_matches_fixture():
    result = run_cli("preview-group-profile", "2")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text(
        "cli_preview_group_profile_known_expected.txt"
    )
    assert result.stderr == ""


def test_preview_group_profile_known_key_is_deterministic():
    first = run_cli("preview-group-profile", "2")
    second = run_cli("preview-group-profile", "2")

    assert first.returncode == 0
    assert second.returncode == 0
    assert normalize_newlines(first.stdout) == normalize_newlines(second.stdout)
    assert first.stderr == ""
    assert second.stderr == ""


def test_inspect_command_unknown_key_fails_safely():
    result = run_cli("inspect-command", "UNKNOWN")

    assert result.returncode == 1
    assert result.stdout == ""
    assert normalize_newlines(result.stderr) == fixture_text(
        "cli_inspect_command_unknown_expected.txt"
    )


def test_inspect_scene_unknown_key_fails_safely():
    result = run_cli("inspect-scene", "UNKNOWN")

    assert result.returncode == 1
    assert result.stdout == ""
    assert normalize_newlines(result.stderr) == fixture_text(
        "cli_inspect_scene_unknown_expected.txt"
    )


def test_inspect_group_profile_unknown_key_fails_safely():
    result = run_cli("inspect-group-profile", "UNKNOWN")

    assert result.returncode == 1
    assert result.stdout == ""
    assert normalize_newlines(result.stderr) == fixture_text(
        "cli_inspect_group_profile_unknown_expected.txt"
    )


def test_preview_command_unknown_key_fails_safely():
    result = run_cli("preview-command", "UNKNOWN")

    assert result.returncode == 1
    assert result.stdout == ""
    assert normalize_newlines(result.stderr) == fixture_text(
        "cli_preview_command_unknown_expected.txt"
    )


def test_preview_scene_unknown_key_fails_safely():
    result = run_cli("preview-scene", "DOES_NOT_EXIST")

    assert result.returncode == 1
    assert result.stdout == ""
    assert normalize_newlines(result.stderr) == fixture_text(
        "cli_preview_scene_unknown_expected.txt"
    )


def test_preview_group_profile_unknown_key_fails_safely():
    result = run_cli("preview-group-profile", "DOES_NOT_EXIST")

    assert result.returncode == 1
    assert result.stdout == ""
    assert normalize_newlines(result.stderr) == fixture_text(
        "cli_preview_group_profile_unknown_expected.txt"
    )


def test_missing_arguments_fail_safely():
    result = run_cli()

    assert result.returncode == 2
    assert result.stdout == ""
    assert normalize_newlines(result.stderr) == USAGE


def test_unknown_arguments_fail_safely():
    result = run_cli("mutate")

    assert result.returncode == 2
    assert result.stdout == ""
    assert normalize_newlines(result.stderr) == USAGE


def test_unknown_report_arguments_fail_safely():
    result = run_cli("report", "--mutate")

    assert result.returncode == 2
    assert result.stdout == ""
    assert normalize_newlines(result.stderr) == USAGE


def test_unknown_project_status_report_arguments_fail_safely():
    result = run_cli("project-status-report", "--mutate")

    assert result.returncode == 2
    assert result.stdout == ""
    assert normalize_newlines(result.stderr) == USAGE


def test_unknown_mock_mapper_report_arguments_fail_safely():
    result = run_cli("mock-mapper-report", "--mutate")

    assert result.returncode == 2
    assert result.stdout == ""
    assert normalize_newlines(result.stderr) == USAGE


def test_unknown_runtime_plan_report_arguments_fail_safely():
    result = run_cli("runtime-plan-report", "--mutate")

    assert result.returncode == 2
    assert result.stdout == ""
    assert normalize_newlines(result.stderr) == USAGE


def test_unknown_active_boundary_report_arguments_fail_safely():
    result = run_cli("active-boundary-report", "--mutate")

    assert result.returncode == 2
    assert result.stdout == ""
    assert normalize_newlines(result.stderr) == USAGE


def test_unknown_mock_runtime_active_bridge_report_arguments_fail_safely():
    result = run_cli("mock-runtime-active-bridge-report", "--mutate")

    assert result.returncode == 2
    assert result.stdout == ""
    assert normalize_newlines(result.stderr) == USAGE


def test_unknown_anchor_profile_report_arguments_fail_safely():
    result = run_cli("anchor-profile-report", "--mutate")

    assert result.returncode == 2
    assert result.stdout == ""
    assert normalize_newlines(result.stderr) == USAGE


def test_unknown_behavior_parity_report_arguments_fail_safely():
    result = run_cli("behavior-parity-report", "--mutate")

    assert result.returncode == 2
    assert result.stdout == ""
    assert normalize_newlines(result.stderr) == USAGE


def test_unknown_list_arguments_fail_safely():
    result = run_cli("list-commands", "--mutate")

    assert result.returncode == 2
    assert result.stdout == ""
    assert normalize_newlines(result.stderr) == USAGE


def test_missing_search_query_fails_safely():
    result = run_cli("search-commands")

    assert result.returncode == 2
    assert result.stdout == ""
    assert normalize_newlines(result.stderr) == USAGE


def test_unknown_search_arguments_fail_safely():
    result = run_cli("search-scenes", "Wild", "--mutate")

    assert result.returncode == 2
    assert result.stdout == ""
    assert normalize_newlines(result.stderr) == USAGE


def test_missing_inspect_command_key_fails_safely():
    result = run_cli("inspect-command")

    assert result.returncode == 2
    assert result.stdout == ""
    assert normalize_newlines(result.stderr) == USAGE


def test_missing_inspect_scene_key_fails_safely():
    result = run_cli("inspect-scene")

    assert result.returncode == 2
    assert result.stdout == ""
    assert normalize_newlines(result.stderr) == USAGE


def test_missing_inspect_group_profile_key_fails_safely():
    result = run_cli("inspect-group-profile")

    assert result.returncode == 2
    assert result.stdout == ""
    assert normalize_newlines(result.stderr) == USAGE


def test_missing_preview_command_key_fails_safely():
    result = run_cli("preview-command")

    assert result.returncode == 2
    assert result.stdout == ""
    assert normalize_newlines(result.stderr) == USAGE


def test_missing_preview_scene_key_fails_safely():
    result = run_cli("preview-scene")

    assert result.returncode == 2
    assert result.stdout == ""
    assert normalize_newlines(result.stderr) == USAGE


def test_missing_preview_group_profile_key_fails_safely():
    result = run_cli("preview-group-profile")

    assert result.returncode == 2
    assert result.stdout == ""
    assert normalize_newlines(result.stderr) == USAGE


def test_report_command_exposes_no_active_behavior_or_support_expansion():
    result = run_cli("report")
    output = normalize_newlines(result.stdout)

    assert "- dispatches_commands: False" in output
    assert "- executes_commands: False" in output
    assert "- mutates_hardware: False" in output
    assert "- opens_ports: False" in output
    assert "- sends_midi: False" in output
    assert "- writes_sysex: False" in output
    assert "- no Pads 5-12 support" in output
    assert "- no Analog Four support" in output
    assert "- Pads 5-12" in output
    assert "- Analog Four" in output


def test_project_status_report_tracks_convergence_behind_arm_flag():
    result = run_cli("project-status-report")
    output = normalize_newlines(result.stdout)

    # Convergence wave: active execution is present, but only behind --arm.
    # The default landing mode stays passive and the monolith stays untouched.
    assert "- real_midi: present_behind_arm_flag" in output
    assert "- port_opening: present_behind_arm_flag" in output
    assert "- active_execution: present_behind_arm_flag" in output
    assert "- dispatch: present_behind_arm_flag" in output
    assert "- command_execution: present_behind_arm_flag" in output
    assert "- default_mode: passive" in output
    assert "- hardware_required: False" in output
    assert "- hardware_behavior: opt_in_behind_arm_flag" in output
    assert "- analog_four_support: absent" in output
    assert "- pads_5_12_support: absent" in output
    assert "- v134_reference: untouched" in output
    assert "- package_metadata: untouched" in output
    assert "- active_execution_gate: --arm flag" in output
    assert "- active_modes_present: 2" in output
    assert "- total_modes: 3" in output
    assert "execute-command" not in output
    assert "send-command" not in output
    assert "hardware-test" not in output
    assert "Pad 5" not in output
    assert "Pad 6" not in output
    assert "Pad 7" not in output
    assert "Pad 8" not in output


def test_mock_mapper_report_exposes_no_active_behavior_or_support_expansion():
    result = run_cli("mock-mapper-report")
    output = normalize_newlines(result.stdout)

    assert "- 2: My BD Hard (Pad 1 / BD Hard)" in output
    assert "- 3: My BD Classic (Pad 2 / BD Classic)" in output
    assert (
        "- 4: My BD Acoustic (Pad 4 / BD Acoustic) - intentionally unsupported until separately approved"
        in output
    )
    assert "- mock_only: True" in output
    assert "- real_midi: absent" in output
    assert "- port_opening: absent" in output
    assert "- cli_wiring: absent" in output
    assert "- active_behavior: absent" in output
    assert "- hardware_required: False" in output
    assert "- analog_four_support: absent" in output
    assert "- pads_5_12_support: absent" in output
    assert "Pad 5" not in output
    assert "Pad 6" not in output
    assert "Pad 7" not in output
    assert "Pad 8" not in output
    assert "Pad 9" not in output
    assert "Pad 10" not in output
    assert "Pad 11" not in output
    assert "Pad 12" not in output
    assert "Analog Four support" not in output


def test_runtime_plan_report_exposes_no_active_behavior_or_support_expansion():
    result = run_cli("runtime-plan-report")
    output = normalize_newlines(result.stdout)

    assert result.returncode == 0
    assert "Supported Planning Inputs:" in output
    assert "- group_profile:2 -> Pad 1 / My BD Hard" in output
    assert "- group_profile:3 -> Pad 2 / My BD Classic" in output
    assert "Parked Planning Inputs:" in output
    assert "- group_profile:4 -> Pad 1 / My BD Acoustic" in output
    assert "- would_execute: False" in output
    assert "- mock_only: True" in output
    assert "- sends_real_midi: False" in output
    assert "- ports_allowed: False" in output
    assert "- hardware_required: False" in output
    assert "- runtime_execution: absent" in output
    assert "- cli_execution_wiring: absent" in output
    assert "- dispatch: absent" in output
    assert "execute-command" not in output
    assert "send-command" not in output
    assert "hardware-test" not in output


def test_active_boundary_report_exposes_no_active_behavior_or_support_expansion():
    result = run_cli("active-boundary-report")
    output = normalize_newlines(result.stdout)

    assert "- group_profile 2: My BD Hard (Pad 1 / BD Hard)" in output
    assert "- boundary: mock_active_boundary" in output
    assert "- supported_candidate: group_profile:2" in output
    assert (
        "- fields: source_kind, source_key, target, armed, dry_run_confirmed, operator_intent, mock_only, sends_real_midi"
        in output
    )
    assert "- failure_reason: included on failure paths" in output
    assert (
        "- 3: My BD Classic (Pad 2 / BD Classic) - mock mapper/report scope only; not active-boundary supported"
        in output
    )
    assert "- 4: My BD Acoustic (Pad 4 / BD Acoustic) - parked until separately approved" in output
    assert "- explicit arming" in output
    assert "- dry-run confirmation" in output
    assert "- injected MockMidiSender" in output
    assert "- mock_only: True" in output
    assert "- hardware_required: False" in output
    assert "- real_midi: absent" in output
    assert "- port_opening: absent" in output
    assert "- active_cli_behavior: absent" in output
    assert "- dispatch: absent" in output
    assert "- command_execution: absent" in output
    assert "- scene_execution: absent" in output
    assert "- hardware_behavior: absent" in output
    assert "execute-command" not in output
    assert "send-command" not in output
    assert "hardware-test" not in output
    assert "Pad 5" not in output
    assert "Pad 6" not in output
    assert "Pad 7" not in output
    assert "Pad 8" not in output
    assert "Pad 9" not in output
    assert "Pad 10" not in output
    assert "Pad 11" not in output
    assert "Pad 12" not in output
    assert "Analog Four support" not in output


def test_mock_runtime_active_bridge_report_exposes_no_active_behavior_or_support_expansion():
    result = run_cli("mock-runtime-active-bridge-report")
    output = normalize_newlines(result.stdout)

    assert result.returncode == 0
    assert "Accepted Candidate:" in output
    assert "- group_profile:2 / My BD Hard -> Pad 1 / BD Hard" in output
    assert "Rejected Cases:" in output
    assert "- group_profile:3 / My BD Classic: bridge rejected" in output
    assert "Parked Cases:" in output
    assert "- group_profile:4 / My BD Acoustic: parked until separately approved" in output
    assert "- read_only: True" in output
    assert "- mock_only: True" in output
    assert "- invokes_bridge: False" in output
    assert "- constructs_sender: False" in output
    assert "- emits_messages: False" in output
    assert "- real_midi: absent" in output
    assert "- port_opening: absent" in output
    assert "- hardware_required: False" in output
    assert "- cli_execution_wiring: absent" in output
    assert "- runtime_execution: absent" in output
    assert "- dispatch: absent" in output
    assert "- active_behavior: absent" in output
    assert "- hardware_behavior: absent" in output
    assert "execute-command" not in output
    assert "send-command" not in output
    assert "hardware-test" not in output
    assert "Pad 5" not in output
    assert "Pad 6" not in output
    assert "Pad 7" not in output
    assert "Pad 8" not in output
    assert "Pad 9" not in output
    assert "Pad 10" not in output
    assert "Pad 11" not in output
    assert "Pad 12" not in output
    assert "Analog Four support" not in output


def test_active_boundary_report_output_keeps_boundary_profiles_explicit():
    result = run_cli("active-boundary-report")
    output = normalize_newlines(result.stdout)

    assert result.returncode == 0
    assert "Unsupported Active Boundary Profiles:" in output
    assert "3: My BD Classic" in output
    assert "not active-boundary supported" in output
    assert "4: My BD Acoustic" in output
    assert "parked until separately approved" in output


def test_active_boundary_report_output_keeps_passive_safety_explicit():
    result = run_cli("active-boundary-report")
    output = normalize_newlines(result.stdout)

    assert result.returncode == 0
    assert "- real_midi: absent" in output
    assert "- port_opening: absent" in output
    assert "- active_cli_behavior: absent" in output
    assert "- dispatch: absent" in output
    assert "- command_execution: absent" in output
    assert "- scene_execution: absent" in output
    assert "- hardware_behavior: absent" in output


def test_anchor_profile_report_exposes_no_active_behavior_or_support_expansion():
    result = run_cli("anchor-profile-report")
    output = normalize_newlines(result.stdout)

    assert "- direct_packet_2_anchor_profile: BH, BC, BS, BF" in output
    assert "- pad1_lane_anchor_profile: FZ, BP, PBH, BI, SBH, BA" in output
    assert "- pad2_lane_anchor_profile: P2B, P2H, P2C, P2F, P2Z" in output
    assert "- pad3_anchor: P3A, SA" in output
    assert "- pad4_anchor: P4A" in output
    assert "- group_anchor: O, Z" in output
    assert "- current_anchor_state: B, E" in output
    assert "- selected_profile_workflow: P, M" in output
    assert "- selected_isolated_pad_target: L" in output
    assert (
        "- PZ: selected_isolated_pad_anchor_return - deferred_selected_isolated_pad_anchor_return"
        in output
    )
    assert (
        "- 4: group_profile_mock_mapper_support - profile 4 mock mapper support remains parked until separately approved"
        in output
    )
    assert "- read_only: True" in output
    assert "- passive_cli_visibility: present" in output
    assert "- real_midi: absent" in output
    assert "- port_opening: absent" in output
    assert "- midi_sending: absent" in output
    assert "- active_behavior: absent" in output
    assert "- active_cli_wiring: absent" in output
    assert "- hardware_required: False" in output
    assert "- runtime_state: absent" in output
    assert "- package_metadata_changes: absent" in output
    assert "execute-command" not in output
    assert "send-command" not in output
    assert "hardware-test" not in output
    assert "Pad 5" not in output
    assert "Pad 6" not in output
    assert "Pad 7" not in output
    assert "Pad 8" not in output
    assert "Pad 9" not in output
    assert "Pad 10" not in output
    assert "Pad 11" not in output
    assert "Pad 12" not in output
    assert "Analog Four support" not in output


def test_behavior_parity_report_exposes_no_active_behavior_or_support_expansion():
    result = run_cli("behavior-parity-report")
    output = normalize_newlines(result.stdout)

    assert "- Packet 11A L selected isolated pad target intent" in output
    assert "- Packet 11B PZ selected isolated pad anchor-return readiness" in output
    assert "Selected Isolated Pad Packet Coverage:" in output
    assert "- Packet 11A: L - selected isolated pad target intent" in output
    assert "- Packet 11B: PZ - selected isolated pad anchor-return readiness" in output
    assert "Runtime-Adjacent Mock-Only Safe Failures:" in output
    assert "- PZ" in output
    assert "- B" in output
    assert "- L" in output
    assert "Parked Scope:" in output
    assert "- fourth runtime-adjacent candidate" in output
    assert "- profile 4 mock mapper support" in output
    assert "- Packet 12 CLI visibility" not in output
    assert "Absent Behavior:" in output
    assert "- dispatch" in output
    assert "- command execution" in output
    assert "- scene execution" in output
    assert "- runtime mutation" in output
    assert "- active CLI commands" in output
    assert "- real MIDI dependencies" in output
    assert "- port opening" in output
    assert "- MIDI sending" in output
    assert "- hardware behavior" in output
    assert "- Analog Four support" in output
    assert "- Pads 5-12 support" in output
    assert "Protected File State:" in output
    assert "- v134_reference: untouched" in output
    assert "- package_metadata: untouched" in output
    assert "- runtime_execution_logic: absent" in output
    assert "- read_only: True" in output
    assert "- in_memory_only: True" in output
    assert "- cli_visibility: present" in output
    assert "- active_behavior: absent" in output
    assert "- hardware_required: False" in output
    assert "execute-command" not in output
    assert "send-command" not in output
    assert "hardware-test" not in output
    assert "Pad 5" not in output
    assert "Pad 6" not in output
    assert "Pad 7" not in output
    assert "Pad 8" not in output
    assert "Pad 9" not in output
    assert "Pad 10" not in output
    assert "Pad 11" not in output
    assert "Pad 12" not in output


def test_inspect_command_exposes_no_active_behavior_or_support_expansion():
    result = run_cli("inspect-command", "P3A")
    output = normalize_newlines(result.stdout)

    assert "Executable: False" in output
    assert "- no MIDI sending" in output
    assert "- no port opening" in output
    assert "- no command execution" in output
    assert "- no hardware mutation" in output
    assert "Pad 5" not in output
    assert "Pad 6" not in output
    assert "Pad 7" not in output
    assert "Pad 8" not in output
    assert "Pad 9" not in output
    assert "Pad 10" not in output
    assert "Pad 11" not in output
    assert "Pad 12" not in output
    assert "Analog Four support" not in output


def test_inspect_scene_exposes_no_active_behavior_or_support_expansion():
    result = run_cli("inspect-scene", "S1A")
    output = normalize_newlines(result.stdout)

    assert "Executable: False" in output
    assert "- no MIDI sending" in output
    assert "- no port opening" in output
    assert "- no command execution" in output
    assert "- no hardware mutation" in output
    assert "Pad 5" not in output
    assert "Pad 6" not in output
    assert "Pad 7" not in output
    assert "Pad 8" not in output
    assert "Pad 9" not in output
    assert "Pad 10" not in output
    assert "Pad 11" not in output
    assert "Pad 12" not in output
    assert "Analog Four support" not in output


def test_inspect_group_profile_exposes_no_active_behavior_or_support_expansion():
    result = run_cli("inspect-group-profile", "2")
    output = normalize_newlines(result.stdout)

    assert "Machine value: 0" in output
    assert "Group pad: 1" in output
    assert "- no MIDI sending" in output
    assert "- no port opening" in output
    assert "- no command execution" in output
    assert "- no hardware mutation" in output
    assert "Pad 5" not in output
    assert "Pad 6" not in output
    assert "Pad 7" not in output
    assert "Pad 8" not in output
    assert "Pad 9" not in output
    assert "Pad 10" not in output
    assert "Pad 11" not in output
    assert "Pad 12" not in output
    assert "Analog Four support" not in output


def test_list_commands_exposes_no_active_behavior_or_support_expansion():
    result = run_cli("list-commands")
    output = normalize_newlines(result.stdout)

    assert "RytmRandomizer passive command list" in output
    assert "- no MIDI sending" in output
    assert "- no port opening" in output
    assert "- no command execution" in output
    assert "- no hardware mutation" in output
    assert "Pad 5" not in output
    assert "Pad 6" not in output
    assert "Pad 7" not in output
    assert "Pad 8" not in output
    assert "Pad 9" not in output
    assert "Pad 10" not in output
    assert "Pad 11" not in output
    assert "Pad 12" not in output
    assert "Analog Four support" not in output


def test_list_scenes_exposes_no_active_behavior_or_support_expansion():
    result = run_cli("list-scenes")
    output = normalize_newlines(result.stdout)

    assert "RytmRandomizer passive scene list" in output
    assert "- no MIDI sending" in output
    assert "- no port opening" in output
    assert "- no command execution" in output
    assert "- no hardware mutation" in output
    assert "Pad 5" not in output
    assert "Pad 6" not in output
    assert "Pad 7" not in output
    assert "Pad 8" not in output
    assert "Pad 9" not in output
    assert "Pad 10" not in output
    assert "Pad 11" not in output
    assert "Pad 12" not in output
    assert "Analog Four support" not in output


def test_list_group_profiles_exposes_no_active_behavior_or_support_expansion():
    result = run_cli("list-group-profiles")
    output = normalize_newlines(result.stdout)

    assert "RytmRandomizer passive group profile list" in output
    assert "- no MIDI sending" in output
    assert "- no port opening" in output
    assert "- no command execution" in output
    assert "- no hardware mutation" in output
    assert "Pad 5" not in output
    assert "Pad 6" not in output
    assert "Pad 7" not in output
    assert "Pad 8" not in output
    assert "Pad 9" not in output
    assert "Pad 10" not in output
    assert "Pad 11" not in output
    assert "Pad 12" not in output
    assert "Analog Four support" not in output


def test_search_commands_exposes_no_active_behavior_or_support_expansion():
    result = run_cli("search-commands", "guarded")
    output = normalize_newlines(result.stdout)

    assert "RytmRandomizer passive command search" in output
    assert "- no MIDI sending" in output
    assert "- no port opening" in output
    assert "- no command execution" in output
    assert "- no hardware mutation" in output
    assert "Pad 5" not in output
    assert "Pad 6" not in output
    assert "Pad 7" not in output
    assert "Pad 8" not in output
    assert "Pad 9" not in output
    assert "Pad 10" not in output
    assert "Pad 11" not in output
    assert "Pad 12" not in output
    assert "Analog Four support" not in output


def test_search_scenes_exposes_no_active_behavior_or_support_expansion():
    result = run_cli("search-scenes", "Wild")
    output = normalize_newlines(result.stdout)

    assert "RytmRandomizer passive scene search" in output
    assert "- no MIDI sending" in output
    assert "- no port opening" in output
    assert "- no command execution" in output
    assert "- no hardware mutation" in output
    assert "Pad 5" not in output
    assert "Pad 6" not in output
    assert "Pad 7" not in output
    assert "Pad 8" not in output
    assert "Pad 9" not in output
    assert "Pad 10" not in output
    assert "Pad 11" not in output
    assert "Pad 12" not in output
    assert "Analog Four support" not in output


def test_search_group_profiles_exposes_no_active_behavior_or_support_expansion():
    result = run_cli("search-group-profiles", "Hard")
    output = normalize_newlines(result.stdout)

    assert "RytmRandomizer passive group profile search" in output
    assert "- no MIDI sending" in output
    assert "- no port opening" in output
    assert "- no command execution" in output
    assert "- no hardware mutation" in output
    assert "Pad 5" not in output
    assert "Pad 6" not in output
    assert "Pad 7" not in output
    assert "Pad 8" not in output
    assert "Pad 9" not in output
    assert "Pad 10" not in output
    assert "Pad 11" not in output
    assert "Pad 12" not in output
    assert "Analog Four support" not in output


def test_preview_command_exposes_no_active_behavior_or_support_expansion():
    result = run_cli("preview-command", "J")
    output = normalize_newlines(result.stdout)

    assert "Executable: False" in output
    assert "No MIDI would be sent." in output
    assert "No command would execute." in output
    assert "No hardware would be mutated." in output
    assert "- no MIDI sending" in output
    assert "- no port opening" in output
    assert "- no command execution" in output
    assert "- no hardware mutation" in output
    assert "Pad 5" not in output
    assert "Pad 6" not in output
    assert "Pad 7" not in output
    assert "Pad 8" not in output
    assert "Pad 9" not in output
    assert "Pad 10" not in output
    assert "Pad 11" not in output
    assert "Pad 12" not in output
    assert "Analog Four support" not in output


def test_preview_scene_exposes_no_active_behavior_or_support_expansion():
    result = run_cli("preview-scene", "S1A")
    output = normalize_newlines(result.stdout)

    assert "Executable: False" in output
    assert "No MIDI would be sent." in output
    assert "No scene would execute." in output
    assert "No command would execute." in output
    assert "No hardware would be mutated." in output
    assert "- no MIDI sending" in output
    assert "- no port opening" in output
    assert "- no scene execution" in output
    assert "- no command execution" in output
    assert "- no hardware mutation" in output
    assert "Pad 5" not in output
    assert "Pad 6" not in output
    assert "Pad 7" not in output
    assert "Pad 8" not in output
    assert "Pad 9" not in output
    assert "Pad 10" not in output
    assert "Pad 11" not in output
    assert "Pad 12" not in output
    assert "Analog Four support" not in output


def test_preview_group_profile_exposes_no_active_behavior_or_support_expansion():
    result = run_cli("preview-group-profile", "2")
    output = normalize_newlines(result.stdout)

    assert "Machine value: 0" in output
    assert "Group pad: 1" in output
    assert "No MIDI would be sent." in output
    assert "No command would execute." in output
    assert "No hardware would be mutated." in output
    assert "- no MIDI sending" in output
    assert "- no port opening" in output
    assert "- no command execution" in output
    assert "- no hardware mutation" in output
    assert "Pad 5" not in output
    assert "Pad 6" not in output
    assert "Pad 7" not in output
    assert "Pad 8" not in output
    assert "Pad 9" not in output
    assert "Pad 10" not in output
    assert "Pad 11" not in output
    assert "Pad 12" not in output
    assert "Analog Four support" not in output


if __name__ == "__main__":
    test_importing_cli_prints_nothing()
    test_top_level_help_exits_zero_and_matches_fixture()
    test_report_help_exits_zero_and_matches_fixture()
    test_project_status_report_help_exits_zero_and_matches_fixture()
    test_mock_mapper_report_help_exits_zero_and_matches_fixture()
    test_runtime_plan_report_help_exits_zero_and_matches_fixture()
    test_active_boundary_report_help_exits_zero_and_matches_fixture()
    test_mock_runtime_active_bridge_report_help_exits_zero_and_matches_fixture()
    test_anchor_profile_report_help_exits_zero_and_matches_fixture()
    test_behavior_parity_report_help_exits_zero_and_matches_fixture()
    test_inspect_command_help_exits_zero_and_matches_fixture()
    test_inspect_scene_help_exits_zero_and_matches_fixture()
    test_inspect_group_profile_help_exits_zero_and_matches_fixture()
    test_list_commands_help_exits_zero_and_matches_fixture()
    test_list_scenes_help_exits_zero_and_matches_fixture()
    test_list_group_profiles_help_exits_zero_and_matches_fixture()
    test_search_commands_help_exits_zero_and_matches_fixture()
    test_search_scenes_help_exits_zero_and_matches_fixture()
    test_search_group_profiles_help_exits_zero_and_matches_fixture()
    test_preview_command_help_exits_zero_and_matches_fixture()
    test_preview_scene_help_exits_zero_and_matches_fixture()
    test_preview_group_profile_help_exits_zero_and_matches_fixture()
    test_report_command_exits_zero_and_matches_fixture()
    test_project_status_report_command_exits_zero_and_matches_fixture()
    test_project_status_report_summary_command_exits_zero_and_matches_fixture()
    test_project_status_report_check_command_exits_zero_and_matches_fixture()
    test_project_status_report_json_command_exits_zero_and_returns_json()
    test_mock_mapper_report_command_exits_zero_and_matches_fixture()
    test_runtime_plan_report_command_exits_zero_and_matches_fixture()
    test_active_boundary_report_command_exits_zero_and_matches_fixture()
    test_mock_runtime_active_bridge_report_command_exits_zero_and_matches_fixture()
    test_anchor_profile_report_command_exits_zero_and_matches_fixture()
    test_behavior_parity_report_command_exits_zero_and_matches_fixture()
    test_report_command_is_deterministic()
    test_project_status_report_command_is_deterministic()
    test_project_status_report_summary_command_is_deterministic()
    test_project_status_report_check_command_is_deterministic()
    test_project_status_report_json_command_is_deterministic()
    test_mock_mapper_report_command_is_deterministic()
    test_runtime_plan_report_command_is_deterministic()
    test_active_boundary_report_command_is_deterministic()
    test_mock_runtime_active_bridge_report_command_is_deterministic()
    test_anchor_profile_report_command_is_deterministic()
    test_behavior_parity_report_command_is_deterministic()
    test_top_level_help_exposes_no_active_execution_commands()
    test_cli_source_does_not_evaluate_active_boundary_or_construct_sender()
    test_project_status_report_command_imports_no_real_midi_libraries()
    test_project_status_report_summary_command_imports_no_real_midi_libraries()
    test_project_status_report_check_command_imports_no_real_midi_libraries()
    test_project_status_report_json_command_imports_no_real_midi_libraries()
    test_mock_mapper_report_command_imports_no_real_midi_libraries()
    test_runtime_plan_report_command_imports_no_real_midi_libraries()
    test_active_boundary_report_command_imports_no_real_midi_libraries()
    test_mock_runtime_active_bridge_report_command_imports_no_real_midi_libraries()
    test_mock_runtime_active_bridge_report_command_does_not_load_bridge_or_mock_midi()
    test_importing_cli_does_not_load_behavior_report_modules()
    test_importing_cli_does_not_load_runtime_or_bridge_report_modules()
    test_importing_cli_does_not_load_registry_report_module()
    test_importing_cli_does_not_load_passive_metadata_modules()
    test_anchor_profile_report_command_imports_no_real_midi_libraries()
    test_behavior_parity_report_command_imports_no_real_midi_libraries()
    test_inspect_command_known_key_exits_zero_and_matches_fixture()
    test_inspect_command_known_key_is_deterministic()
    test_inspect_scene_known_key_exits_zero_and_matches_fixture()
    test_inspect_scene_known_key_is_deterministic()
    test_inspect_group_profile_known_key_exits_zero_and_matches_fixture()
    test_inspect_group_profile_known_key_is_deterministic()
    test_list_commands_exits_zero_and_matches_fixture()
    test_list_scenes_exits_zero_and_matches_fixture()
    test_list_group_profiles_exits_zero_and_matches_fixture()
    test_list_commands_are_deterministic()
    test_list_scenes_are_deterministic()
    test_list_group_profiles_are_deterministic()
    test_search_commands_known_query_exits_zero_and_matches_fixture()
    test_search_scenes_known_query_exits_zero_and_matches_fixture()
    test_search_group_profiles_known_query_exits_zero_and_matches_fixture()
    test_search_commands_no_match_exits_zero_and_matches_fixture()
    test_search_scenes_no_match_exits_zero_and_matches_fixture()
    test_search_group_profiles_no_match_exits_zero_and_matches_fixture()
    test_search_commands_are_case_insensitive_and_deterministic()
    test_search_scenes_are_deterministic()
    test_search_group_profiles_are_deterministic()
    test_preview_command_known_key_exits_zero_and_matches_fixture()
    test_preview_command_known_key_is_deterministic()
    test_preview_scene_known_key_exits_zero_and_matches_fixture()
    test_preview_scene_known_key_is_deterministic()
    test_preview_group_profile_known_key_exits_zero_and_matches_fixture()
    test_preview_group_profile_known_key_is_deterministic()
    test_inspect_command_unknown_key_fails_safely()
    test_inspect_scene_unknown_key_fails_safely()
    test_inspect_group_profile_unknown_key_fails_safely()
    test_preview_command_unknown_key_fails_safely()
    test_preview_scene_unknown_key_fails_safely()
    test_preview_group_profile_unknown_key_fails_safely()
    test_missing_arguments_fail_safely()
    test_unknown_arguments_fail_safely()
    test_unknown_report_arguments_fail_safely()
    test_unknown_project_status_report_arguments_fail_safely()
    test_unknown_mock_mapper_report_arguments_fail_safely()
    test_unknown_runtime_plan_report_arguments_fail_safely()
    test_unknown_active_boundary_report_arguments_fail_safely()
    test_unknown_mock_runtime_active_bridge_report_arguments_fail_safely()
    test_unknown_anchor_profile_report_arguments_fail_safely()
    test_unknown_behavior_parity_report_arguments_fail_safely()
    test_unknown_list_arguments_fail_safely()
    test_missing_search_query_fails_safely()
    test_unknown_search_arguments_fail_safely()
    test_missing_inspect_command_key_fails_safely()
    test_missing_inspect_scene_key_fails_safely()
    test_missing_inspect_group_profile_key_fails_safely()
    test_missing_preview_command_key_fails_safely()
    test_missing_preview_scene_key_fails_safely()
    test_missing_preview_group_profile_key_fails_safely()
    test_report_command_exposes_no_active_behavior_or_support_expansion()
    test_project_status_report_tracks_convergence_behind_arm_flag()
    test_mock_mapper_report_exposes_no_active_behavior_or_support_expansion()
    test_runtime_plan_report_exposes_no_active_behavior_or_support_expansion()
    test_active_boundary_report_exposes_no_active_behavior_or_support_expansion()
    test_mock_runtime_active_bridge_report_exposes_no_active_behavior_or_support_expansion()
    test_active_boundary_report_output_keeps_boundary_profiles_explicit()
    test_active_boundary_report_output_keeps_passive_safety_explicit()
    test_anchor_profile_report_exposes_no_active_behavior_or_support_expansion()
    test_behavior_parity_report_exposes_no_active_behavior_or_support_expansion()
    test_inspect_command_exposes_no_active_behavior_or_support_expansion()
    test_inspect_scene_exposes_no_active_behavior_or_support_expansion()
    test_inspect_group_profile_exposes_no_active_behavior_or_support_expansion()
    test_list_commands_exposes_no_active_behavior_or_support_expansion()
    test_list_scenes_exposes_no_active_behavior_or_support_expansion()
    test_list_group_profiles_exposes_no_active_behavior_or_support_expansion()
    test_search_commands_exposes_no_active_behavior_or_support_expansion()
    test_search_scenes_exposes_no_active_behavior_or_support_expansion()
    test_search_group_profiles_exposes_no_active_behavior_or_support_expansion()
    test_preview_command_exposes_no_active_behavior_or_support_expansion()
    test_preview_scene_exposes_no_active_behavior_or_support_expansion()
    test_preview_group_profile_exposes_no_active_behavior_or_support_expansion()
