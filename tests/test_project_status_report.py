from pathlib import Path
import importlib
import json
import subprocess
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def test_importing_project_status_report_prints_nothing():
    result = subprocess.run(
        [sys.executable, "-c", "import rytm_randomizer.project_status_report"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_project_status_report_summarizes_current_project_state():
    from rytm_randomizer.project_status_report import build_project_status_report

    report = build_project_status_report()

    assert report["title"] == "RytmRandomizer Project Status Report"
    assert report["phase"] == {
        "name": "Passive/Mock Runtime Visibility Phase",
        "technical_name": "RytmRandomizer",
        "creative_identity_candidate": "KitForge",
        "repository_name": "RytmRandomizer",
        "package_name": "rytm_randomizer",
    }
    assert report["behavior_parity"]["accepted_packet_count"] == 12
    assert report["behavior_parity"]["pad_lane_packet_count"] == 4
    assert report["behavior_parity"]["pad_lane_command_count"] == 38
    assert report["runtime_plan"]["supported_count"] == 2
    assert report["runtime_plan"]["parked_count"] == 1
    assert report["active_boundary"]["supported_candidate"] == "group_profile:2"
    assert report["mock_runtime_active_bridge"]["accepted_source_key"] == "2"
    assert report["closeout"] == {
        "closeout_contract": "present",
        "failure_propagation": "guarded",
        "closeout_script": "Scripts/closeout_check.ps1",
    }


def test_project_status_report_records_passive_cli_visibility():
    from rytm_randomizer.project_status_report import build_project_status_report

    report = build_project_status_report()

    assert report["passive_cli_commands"] == (
        "report",
        "project-status-report",
        "mock-mapper-report",
        "runtime-plan-report",
        "active-boundary-report",
        "mock-runtime-active-bridge-report",
        "anchor-profile-report",
        "behavior-parity-report",
        "list-commands",
        "list-scenes",
        "list-group-profiles",
        "search-commands",
        "search-scenes",
        "search-group-profiles",
        "inspect-command",
        "inspect-scene",
        "inspect-group-profile",
        "preview-command",
        "preview-scene",
        "preview-group-profile",
    )


def test_project_status_report_records_absent_runtime_and_hardware_boundaries():
    from rytm_randomizer.project_status_report import build_project_status_report

    report = build_project_status_report()

    assert report["safety"] == {
        "real_midi": "absent",
        "port_opening": "absent",
        "active_execution": "absent",
        "dispatch": "absent",
        "command_execution": "absent",
        "hardware_required": False,
        "hardware_behavior": "absent",
        "analog_four_support": "absent",
        "pads_5_12_support": "absent",
        "v134_reference": "untouched",
        "package_metadata": "untouched",
    }


def test_project_status_summary_is_deterministic():
    from rytm_randomizer.project_status_report import summarize_project_status_report

    assert summarize_project_status_report() == {
        "title": "RytmRandomizer Project Status Report",
        "phase_name": "Passive/Mock Runtime Visibility Phase",
        "creative_identity_candidate": "KitForge",
        "passive_cli_command_count": 20,
        "accepted_packet_count": 12,
        "pad_lane_command_count": 38,
        "runtime_supported_count": 2,
        "active_boundary_candidate": "group_profile:2",
        "mock_bridge_candidate": "2",
        "real_midi": "absent",
        "port_opening": "absent",
        "active_execution": "absent",
        "hardware_required": False,
        "v134_reference": "untouched",
    }


def test_project_status_summary_lines_are_deterministic():
    from rytm_randomizer.project_status_report import format_project_status_summary

    first = format_project_status_summary()
    second = format_project_status_summary()

    assert first == second
    assert first == [
        "RytmRandomizer Project Status Summary",
        "- phase_name: Passive/Mock Runtime Visibility Phase",
        "- creative_identity_candidate: KitForge",
        "- passive_cli_command_count: 20",
        "- accepted_packet_count: 12",
        "- pad_lane_command_count: 38",
        "- runtime_supported_count: 2",
        "- active_boundary_candidate: group_profile:2",
        "- mock_bridge_candidate: 2",
        "- real_midi: absent",
        "- port_opening: absent",
        "- active_execution: absent",
        "- hardware_required: False",
        "- v134_reference: untouched",
    ]


def test_project_status_check_passes_for_current_report():
    from rytm_randomizer.project_status_report import check_project_status_report

    check = check_project_status_report()

    assert check == {
        "title": "RytmRandomizer Project Status Check",
        "ok": True,
        "failure_count": 0,
        "failures": [],
        "checked": {
            "safety.real_midi": "absent",
            "safety.port_opening": "absent",
            "safety.active_execution": "absent",
            "safety.command_execution": "absent",
            "safety.dispatch": "absent",
            "safety.hardware_required": False,
            "safety.v134_reference": "untouched",
            "safety.package_metadata": "untouched",
            "runtime_plan.runtime_execution": "absent",
            "active_boundary.active_cli_behavior": "absent",
            "mock_runtime_active_bridge.emits_messages": False,
            "source.in_memory_only": True,
            "source.writes_files": False,
            "closeout.failure_propagation": "guarded",
        },
    }


def test_project_status_check_fails_for_mutated_unsafe_report():
    from rytm_randomizer.project_status_report import (
        build_project_status_report,
        check_project_status_report,
    )

    report = build_project_status_report()
    report["safety"]["real_midi"] = "present"
    report["source"]["writes_files"] = True

    check = check_project_status_report(report)

    assert check["ok"] is False
    assert check["failure_count"] == 2
    assert check["failures"] == [
        {
            "path": "safety.real_midi",
            "expected": "absent",
            "actual": "present",
        },
        {
            "path": "source.writes_files",
            "expected": False,
            "actual": True,
        },
    ]


def test_project_status_check_lines_are_deterministic():
    from rytm_randomizer.project_status_report import format_project_status_check

    first = format_project_status_check()
    second = format_project_status_check()

    assert first == second
    assert first == [
        "RytmRandomizer Project Status Check",
        "- ok: True",
        "- failure_count: 0",
        "- safety.real_midi: absent",
        "- safety.port_opening: absent",
        "- safety.active_execution: absent",
        "- safety.command_execution: absent",
        "- safety.dispatch: absent",
        "- safety.hardware_required: False",
        "- safety.v134_reference: untouched",
        "- safety.package_metadata: untouched",
        "- runtime_plan.runtime_execution: absent",
        "- active_boundary.active_cli_behavior: absent",
        "- mock_runtime_active_bridge.emits_messages: False",
        "- source.in_memory_only: True",
        "- source.writes_files: False",
        "- closeout.failure_propagation: guarded",
    ]


def test_formatted_project_status_report_is_deterministic():
    from rytm_randomizer.project_status_report import format_project_status_report

    first = format_project_status_report()
    second = format_project_status_report()

    assert first == second
    assert first == [
        "RytmRandomizer Project Status Report",
        "Phase:",
        "- name: Passive/Mock Runtime Visibility Phase",
        "- technical_name: RytmRandomizer",
        "- creative_identity_candidate: KitForge",
        "Passive CLI Visibility:",
        "- report",
        "- project-status-report",
        "- mock-mapper-report",
        "- runtime-plan-report",
        "- active-boundary-report",
        "- mock-runtime-active-bridge-report",
        "- anchor-profile-report",
        "- behavior-parity-report",
        "- list-commands",
        "- list-scenes",
        "- list-group-profiles",
        "- search-commands",
        "- search-scenes",
        "- search-group-profiles",
        "- inspect-command",
        "- inspect-scene",
        "- inspect-group-profile",
        "- preview-command",
        "- preview-scene",
        "- preview-group-profile",
        "Behavior Parity:",
        "- accepted_packet_count: 12",
        "- selected_isolated_pad_packet_count: 2",
        "- pad_lane_packet_count: 4",
        "- pad_lane_command_count: 38",
        "- runtime_adjacent_safe_failure_count: 3",
        "- parked_scope_count: 2",
        "Runtime Plan:",
        "- supported_count: 2",
        "- parked_count: 1",
        "- unsupported_count: 2",
        "- runtime_execution: absent",
        "Active Boundary:",
        "- supported_candidate: group_profile:2",
        "- unsupported_keys: 3, 4",
        "- active_cli_behavior: absent",
        "Mock Runtime Active Bridge:",
        "- accepted_source_key: 2",
        "- rejected_count: 7",
        "- parked_count: 1",
        "- emits_messages: False",
        "Closeout:",
        "- closeout_contract: present",
        "- failure_propagation: guarded",
        "- closeout_script: Scripts/closeout_check.ps1",
        "Safety:",
        "- real_midi: absent",
        "- port_opening: absent",
        "- active_execution: absent",
        "- dispatch: absent",
        "- command_execution: absent",
        "- hardware_required: False",
        "- hardware_behavior: absent",
        "- analog_four_support: absent",
        "- pads_5_12_support: absent",
        "- v134_reference: untouched",
        "- package_metadata: untouched",
        "Source:",
        "- in_memory_only: True",
        "- writes_files: False",
    ]


def test_project_status_report_json_is_deterministic_and_parseable():
    from rytm_randomizer.project_status_report import format_project_status_report_json

    first = format_project_status_report_json()
    second = format_project_status_report_json()

    assert first == second
    parsed = json.loads(first)
    assert parsed["title"] == "RytmRandomizer Project Status Report"
    assert parsed["phase"]["name"] == "Passive/Mock Runtime Visibility Phase"
    assert parsed["phase"]["creative_identity_candidate"] == "KitForge"
    assert parsed["behavior_parity"]["accepted_packet_count"] == 12
    assert parsed["runtime_plan"]["runtime_execution"] == "absent"
    assert parsed["active_boundary"]["active_cli_behavior"] == "absent"
    assert parsed["mock_runtime_active_bridge"]["emits_messages"] is False
    assert parsed["safety"]["real_midi"] == "absent"
    assert parsed["safety"]["hardware_required"] is False
    assert parsed["source"]["in_memory_only"] is True
    assert parsed["source"]["writes_files"] is False


def test_returned_project_status_report_is_copied_and_mutation_safe():
    from rytm_randomizer.project_status_report import build_project_status_report

    report = build_project_status_report()
    report["phase"]["name"] = "MUTATED"
    report["behavior_parity"]["accepted_packet_count"] = 0
    report["passive_cli_commands"] = ()

    fresh_report = build_project_status_report()

    assert fresh_report["phase"]["name"] == "Passive/Mock Runtime Visibility Phase"
    assert fresh_report["behavior_parity"]["accepted_packet_count"] == 12
    assert "project-status-report" in fresh_report["passive_cli_commands"]


def test_project_status_report_imports_no_real_midi_libraries():
    sys.modules.pop("rytm_randomizer.project_status_report", None)
    importlib.import_module("rytm_randomizer.project_status_report")

    assert "mido" not in sys.modules
    assert "rtmidi" not in sys.modules


def test_project_status_report_exposes_no_active_cli_command_names():
    import rytm_randomizer.project_status_report as report

    exposed_names = set(dir(report))

    assert "execute_command" not in exposed_names
    assert "send_command" not in exposed_names
    assert "hardware_test" not in exposed_names
    assert "open_port" not in exposed_names
    assert "open_midi_port" not in exposed_names
    assert "send_midi" not in exposed_names


if __name__ == "__main__":
    test_importing_project_status_report_prints_nothing()
    test_project_status_report_summarizes_current_project_state()
    test_project_status_report_records_passive_cli_visibility()
    test_project_status_report_records_absent_runtime_and_hardware_boundaries()
    test_project_status_summary_is_deterministic()
    test_project_status_summary_lines_are_deterministic()
    test_project_status_check_passes_for_current_report()
    test_project_status_check_fails_for_mutated_unsafe_report()
    test_project_status_check_lines_are_deterministic()
    test_formatted_project_status_report_is_deterministic()
    test_project_status_report_json_is_deterministic_and_parseable()
    test_returned_project_status_report_is_copied_and_mutation_safe()
    test_project_status_report_imports_no_real_midi_libraries()
    test_project_status_report_exposes_no_active_cli_command_names()
