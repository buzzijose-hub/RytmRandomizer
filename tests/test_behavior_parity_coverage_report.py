from pathlib import Path
import subprocess
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def normalize_newlines(text):
    return text.replace("\r\n", "\n").replace("\r", "\n").rstrip("\n")


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


def test_importing_behavior_parity_coverage_report_prints_nothing():
    result = subprocess.run(
        [sys.executable, "-c", "import rytm_randomizer.behavior_parity_coverage_report"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_report_summarizes_packet_coverage_and_runtime_adjacent_surfaces():
    from rytm_randomizer.behavior_parity_coverage_report import (
        build_behavior_parity_coverage_report,
    )

    report = build_behavior_parity_coverage_report()

    assert report["title"] == "V1.34 Behavior Parity Coverage Report"
    assert report["accepted_packet_coverage"] == (
        "Packet 1 menu/status and utility intent",
        "Packet 2 meaningful anchor/profile progress",
        "Packet 3 selected isolated pad mutation intent",
        "Packet 4 scene/group intent",
        "Packet 5 meaningful Pad 1 lane behavior progress",
        "Packet 6 Pad 2 lane behavior for the current read-only phase",
        "Packet 7 Pad 3 lane behavior for the current read-only phase",
        "Packet 8 Pad 4 command-helper scope for the current read-only phase",
        "Packet 9 undo/commit/state intent",
        "Packet 10 selected-profile workflow intent",
        "Packet 11A L selected isolated pad target intent",
    )
    assert report["runtime_adjacent_mock_only_safe_failures"] == ("PZ", "B", "L")


def test_report_records_parked_scope_and_absent_behavior():
    from rytm_randomizer.behavior_parity_coverage_report import (
        build_behavior_parity_coverage_report,
    )

    report = build_behavior_parity_coverage_report()

    assert report["parked_scope"] == (
        "fourth runtime-adjacent candidate",
        "profile 4 mock mapper support",
        "Packet 12 CLI visibility",
    )
    assert report["absent_behavior"] == (
        "dispatch",
        "command execution",
        "scene execution",
        "runtime mutation",
        "selected pad switching execution",
        "selected pad target state mutation",
        "selected pad anchor return execution",
        "current anchor return execution",
        "isolated pad mutation execution",
        "active CLI commands",
        "real MIDI dependencies",
        "port discovery",
        "port opening",
        "MIDI sending",
        "hardware behavior",
        "Analog Four support",
        "Pads 5-12 support",
        "SysEx",
        "GUI/capture",
    )


def test_report_records_closeout_coverage_and_protected_file_state():
    from rytm_randomizer.behavior_parity_coverage_report import (
        build_behavior_parity_coverage_report,
    )

    report = build_behavior_parity_coverage_report()

    assert report["closeout_coverage"] == (
        "Behavior Menu Utility",
        "Behavior Anchor Profile",
        "Behavior Anchor Profile Report",
        "Behavior Mutation Depth",
        "Behavior Scene Group",
        "Behavior Pad 1 Lane",
        "Behavior Pad 2 Lane",
        "Behavior Pad 3 Lane",
        "Behavior Pad 4 Lane",
        "Behavior Undo Commit State",
        "Behavior Selected Profile",
        "Behavior Selected Isolated Pad",
        "Selected Target State",
        "Anchor State",
        "Selected Isolated Pad Runtime State",
        "Runtime-Adjacent Mock-Only PZ",
        "Runtime-Adjacent Mock-Only B",
        "Runtime-Adjacent Mock-Only L",
    )
    assert report["protected_file_state"] == {
        "v134_reference": "untouched",
        "package_metadata": "untouched",
        "runtime_execution_logic": "absent",
    }


def test_report_records_read_only_safety_boundaries():
    from rytm_randomizer.behavior_parity_coverage_report import (
        build_behavior_parity_coverage_report,
    )

    report = build_behavior_parity_coverage_report()

    assert report["read_only"] is True
    assert report["in_memory_only"] is True
    assert report["cli_visibility"] == "absent"
    assert report["dispatch"] == "absent"
    assert report["command_execution"] == "absent"
    assert report["scene_execution"] == "absent"
    assert report["real_midi"] == "absent"
    assert report["port_opening"] == "absent"
    assert report["active_behavior"] == "absent"
    assert report["hardware_behavior"] == "absent"
    assert report["hardware_required"] is False


def test_report_summary_is_deterministic():
    from rytm_randomizer.behavior_parity_coverage_report import (
        summarize_behavior_parity_coverage_report,
    )

    assert summarize_behavior_parity_coverage_report() == {
        "title": "V1.34 Behavior Parity Coverage Report",
        "accepted_packet_count": 11,
        "runtime_adjacent_safe_failure_count": 3,
        "parked_scope_count": 3,
        "closeout_coverage_count": 18,
        "read_only": True,
        "cli_visibility": "absent",
        "active_behavior": "absent",
        "hardware_required": False,
    }


def test_formatted_report_is_deterministic_and_human_readable():
    from rytm_randomizer.behavior_parity_coverage_report import (
        format_behavior_parity_coverage_report,
    )

    first = format_behavior_parity_coverage_report()
    second = format_behavior_parity_coverage_report()

    assert first == second
    assert first == [
        "V1.34 Behavior Parity Coverage Report",
        "Accepted Packet Coverage:",
        "- Packet 1 menu/status and utility intent",
        "- Packet 2 meaningful anchor/profile progress",
        "- Packet 3 selected isolated pad mutation intent",
        "- Packet 4 scene/group intent",
        "- Packet 5 meaningful Pad 1 lane behavior progress",
        "- Packet 6 Pad 2 lane behavior for the current read-only phase",
        "- Packet 7 Pad 3 lane behavior for the current read-only phase",
        "- Packet 8 Pad 4 command-helper scope for the current read-only phase",
        "- Packet 9 undo/commit/state intent",
        "- Packet 10 selected-profile workflow intent",
        "- Packet 11A L selected isolated pad target intent",
        "Runtime-Adjacent Mock-Only Safe Failures:",
        "- PZ",
        "- B",
        "- L",
        "Parked Scope:",
        "- fourth runtime-adjacent candidate",
        "- profile 4 mock mapper support",
        "- Packet 12 CLI visibility",
        "Absent Behavior:",
        "- dispatch",
        "- command execution",
        "- scene execution",
        "- runtime mutation",
        "- selected pad switching execution",
        "- selected pad target state mutation",
        "- selected pad anchor return execution",
        "- current anchor return execution",
        "- isolated pad mutation execution",
        "- active CLI commands",
        "- real MIDI dependencies",
        "- port discovery",
        "- port opening",
        "- MIDI sending",
        "- hardware behavior",
        "- Analog Four support",
        "- Pads 5-12 support",
        "- SysEx",
        "- GUI/capture",
        "Protected File State:",
        "- v134_reference: untouched",
        "- package_metadata: untouched",
        "- runtime_execution_logic: absent",
        "Report Boundary:",
        "- read_only: True",
        "- in_memory_only: True",
        "- cli_visibility: absent",
        "- active_behavior: absent",
        "- hardware_required: False",
    ]


def test_returned_report_data_is_copied_and_mutation_safe():
    from rytm_randomizer.behavior_parity_coverage_report import (
        build_behavior_parity_coverage_report,
    )

    report = build_behavior_parity_coverage_report()
    report["accepted_packet_coverage"] = ("MUTATED",)
    report["protected_file_state"]["v134_reference"] = "MUTATED"

    fresh_report = build_behavior_parity_coverage_report()

    assert fresh_report["accepted_packet_coverage"][0] == (
        "Packet 1 menu/status and utility intent"
    )
    assert fresh_report["protected_file_state"]["v134_reference"] == "untouched"


def test_no_real_midi_library_is_imported():
    import rytm_randomizer.behavior_parity_coverage_report  # noqa: F401

    assert "mido" not in sys.modules
    assert "rtmidi" not in sys.modules


def test_passive_cli_report_behavior_remains_unchanged():
    result = run_cli("report")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text("registry_report_expected.txt")
    assert result.stderr == ""


def test_no_packet_12_cli_visibility_or_active_names_are_exposed():
    import rytm_randomizer.behavior_parity_coverage_report as report

    exposed_names = set(dir(report))

    assert "execute_command" not in exposed_names
    assert "send_command" not in exposed_names
    assert "hardware_test" not in exposed_names
    assert "open_port" not in exposed_names
    assert "open_midi_port" not in exposed_names
    assert "send_midi" not in exposed_names
    assert "MidiPortProvider" not in exposed_names


def test_module_remains_decoupled_from_cli_and_runtime_execution():
    import inspect
    import rytm_randomizer.behavior_parity_coverage_report as report

    source = inspect.getsource(report)

    assert "argparse" not in source
    assert "evaluate_mock_active_boundary" not in source
    assert "MockMidiSender(" not in source
    assert "from .mock_midi import" not in source


if __name__ == "__main__":
    test_importing_behavior_parity_coverage_report_prints_nothing()
    test_report_summarizes_packet_coverage_and_runtime_adjacent_surfaces()
    test_report_records_parked_scope_and_absent_behavior()
    test_report_records_closeout_coverage_and_protected_file_state()
    test_report_records_read_only_safety_boundaries()
    test_report_summary_is_deterministic()
    test_formatted_report_is_deterministic_and_human_readable()
    test_returned_report_data_is_copied_and_mutation_safe()
    test_no_real_midi_library_is_imported()
    test_passive_cli_report_behavior_remains_unchanged()
    test_no_packet_12_cli_visibility_or_active_names_are_exposed()
    test_module_remains_decoupled_from_cli_and_runtime_execution()
