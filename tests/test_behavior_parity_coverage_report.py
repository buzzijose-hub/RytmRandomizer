import subprocess
import sys
from pathlib import Path
import pytest

# WS-M4: mark this module as fast-suite; pytest -m fast skips the 505
# warm-worker V1.34 parity fixtures and runs in <60s.
pytestmark = pytest.mark.fast

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
        [sys.executable, "-c", "import rytm_randomizer.reports"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_report_summarizes_packet_coverage_and_runtime_adjacent_surfaces():
    from rytm_randomizer.reports import build_behavior_parity_coverage_report

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
        "Packet 11B PZ selected isolated pad anchor-return readiness",
    )
    assert report["runtime_adjacent_mock_only_safe_failures"] == ("PZ", "B", "L")


def test_report_records_structured_selected_isolated_pad_packet_coverage():
    from rytm_randomizer.behavior.selected_isolated_pad import (
        PACKET_11A_SELECTED_ISOLATED_PAD_KEYS,
        PACKET_11B_SELECTED_ISOLATED_PAD_KEYS,
    )
    from rytm_randomizer.reports import build_behavior_parity_coverage_report

    report = build_behavior_parity_coverage_report()

    assert report["selected_isolated_pad_packet_coverage"] == (
        {
            "packet": "11A",
            "command_keys": PACKET_11A_SELECTED_ISOLATED_PAD_KEYS,
            "coverage": "selected isolated pad target intent",
        },
        {
            "packet": "11B",
            "command_keys": PACKET_11B_SELECTED_ISOLATED_PAD_KEYS,
            "coverage": "selected isolated pad anchor-return readiness",
        },
    )


def test_report_records_structured_pad_lane_packet_coverage():
    from rytm_randomizer.behavior.pad_lane import (
        DEFERRED_PACKET_5_PAD1_LANE_KEYS,
        DEFERRED_PACKET_6_PAD2_LANE_KEYS,
        DEFERRED_PACKET_7_PAD3_LANE_KEYS,
        DEFERRED_PACKET_8_PAD4_LANE_KEYS,
        PACKET_5A_PAD1_CURRENT_ENGINE_KEYS,
        PACKET_5B_PAD1_BD_FM_KEYS,
        PACKET_5C_PAD1_BD_PLASTIC_KEYS,
        PACKET_5D_PAD1_BD_SILKY_KEYS,
        PACKET_5E_PAD1_BD_ACOUSTIC_KEYS,
        PACKET_6A_PAD2_LANE_KEYS,
        PACKET_6B_PAD2_LANE_KEYS,
        PACKET_6C_PAD2_LANE_KEYS,
        PACKET_6D_PAD2_LANE_KEYS,
        PACKET_6E_PAD2_LANE_KEYS,
        PACKET_6F_PAD2_LANE_KEYS,
        PACKET_6G_PAD2_LANE_KEYS,
        PACKET_6H_PAD2_LANE_KEYS,
        PACKET_6I_PAD2_LANE_KEYS,
        PACKET_6J_PAD2_LANE_KEYS,
        PACKET_7A_PAD3_LANE_KEYS,
        PACKET_7B_PAD3_LANE_KEYS,
        PACKET_7C_PAD3_LANE_KEYS,
        PACKET_7D_PAD3_LANE_KEYS,
        PACKET_7E_PAD3_LANE_KEYS,
        PACKET_7F_PAD3_LANE_KEYS,
        PACKET_7G_PAD3_LANE_KEYS,
        PACKET_7H_PAD3_LANE_KEYS,
        PACKET_8A_PAD4_LANE_KEYS,
        PACKET_8B_PAD4_LANE_KEYS,
        PACKET_8C_PAD4_LANE_KEYS,
    )
    from rytm_randomizer.reports import build_behavior_parity_coverage_report

    report = build_behavior_parity_coverage_report()

    assert report["pad_lane_packet_coverage"] == (
        {
            "packet": "5",
            "lane": "Pad 1 BD lane family",
            "command_keys": (
                PACKET_5A_PAD1_CURRENT_ENGINE_KEYS
                + PACKET_5B_PAD1_BD_FM_KEYS
                + PACKET_5C_PAD1_BD_PLASTIC_KEYS
                + PACKET_5D_PAD1_BD_SILKY_KEYS
                + PACKET_5E_PAD1_BD_ACOUSTIC_KEYS
            ),
            "deferred_keys": DEFERRED_PACKET_5_PAD1_LANE_KEYS,
            "coverage": "Pad 1 lane behavior for the current read-only phase",
        },
        {
            "packet": "6",
            "lane": "Pad 2 secondary lane",
            "command_keys": (
                PACKET_6A_PAD2_LANE_KEYS
                + PACKET_6B_PAD2_LANE_KEYS
                + PACKET_6C_PAD2_LANE_KEYS
                + PACKET_6D_PAD2_LANE_KEYS
                + PACKET_6E_PAD2_LANE_KEYS
                + PACKET_6F_PAD2_LANE_KEYS
                + PACKET_6G_PAD2_LANE_KEYS
                + PACKET_6H_PAD2_LANE_KEYS
                + PACKET_6I_PAD2_LANE_KEYS
                + PACKET_6J_PAD2_LANE_KEYS
            ),
            "deferred_keys": DEFERRED_PACKET_6_PAD2_LANE_KEYS,
            "coverage": "Pad 2 lane behavior for the current read-only phase",
        },
        {
            "packet": "7",
            "lane": "Pad 3 SY Raw lane",
            "command_keys": (
                PACKET_7A_PAD3_LANE_KEYS
                + PACKET_7B_PAD3_LANE_KEYS
                + PACKET_7C_PAD3_LANE_KEYS
                + PACKET_7D_PAD3_LANE_KEYS
                + PACKET_7E_PAD3_LANE_KEYS
                + PACKET_7F_PAD3_LANE_KEYS
                + PACKET_7G_PAD3_LANE_KEYS
                + PACKET_7H_PAD3_LANE_KEYS
            ),
            "deferred_keys": DEFERRED_PACKET_7_PAD3_LANE_KEYS,
            "coverage": "Pad 3 lane behavior for the current read-only phase",
        },
        {
            "packet": "8",
            "lane": "Pad 4 BD Acoustic lane",
            "command_keys": (
                PACKET_8A_PAD4_LANE_KEYS + PACKET_8B_PAD4_LANE_KEYS + PACKET_8C_PAD4_LANE_KEYS
            ),
            "deferred_keys": DEFERRED_PACKET_8_PAD4_LANE_KEYS,
            "coverage": "Pad 4 command-helper scope for the current read-only phase",
        },
    )


def test_report_records_parked_scope_and_absent_behavior():
    from rytm_randomizer.reports import build_behavior_parity_coverage_report

    report = build_behavior_parity_coverage_report()

    assert report["parked_scope"] == (
        "fourth runtime-adjacent candidate",
        "profile 4 mock mapper support",
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
    from rytm_randomizer.reports import build_behavior_parity_coverage_report

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
    from rytm_randomizer.reports import build_behavior_parity_coverage_report

    report = build_behavior_parity_coverage_report()

    assert report["read_only"] is True
    assert report["in_memory_only"] is True
    assert report["cli_visibility"] == "present"
    assert report["dispatch"] == "absent"
    assert report["command_execution"] == "absent"
    assert report["scene_execution"] == "absent"
    assert report["real_midi"] == "absent"
    assert report["port_opening"] == "absent"
    assert report["active_behavior"] == "absent"
    assert report["hardware_behavior"] == "absent"
    assert report["hardware_required"] is False


def test_report_summary_is_deterministic():
    from rytm_randomizer.reports import summarize_behavior_parity_coverage_report

    assert summarize_behavior_parity_coverage_report() == {
        "title": "V1.34 Behavior Parity Coverage Report",
        "accepted_packet_count": 12,
        "selected_isolated_pad_packet_count": 2,
        "pad_lane_packet_count": 4,
        "pad_lane_command_count": 38,
        "runtime_adjacent_safe_failure_count": 3,
        "parked_scope_count": 2,
        "closeout_coverage_count": 18,
        "read_only": True,
        "cli_visibility": "present",
        "active_behavior": "absent",
        "hardware_required": False,
    }


def test_formatted_report_is_deterministic_and_human_readable():
    from rytm_randomizer.reports import format_behavior_parity_coverage_report

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
        "- Packet 11B PZ selected isolated pad anchor-return readiness",
        "Selected Isolated Pad Packet Coverage:",
        "- Packet 11A: L - selected isolated pad target intent",
        "- Packet 11B: PZ - selected isolated pad anchor-return readiness",
        "Pad Lane Packet Coverage:",
        "- Packet 5: Pad 1 BD lane family - BR, BM, FT, FK, FG, FZ, BP, PT, PK, PX, PBH, BI, ST, SK, SC, SBH, BA - Pad 1 lane behavior for the current read-only phase",
        "- Packet 5 deferred/safe: none",
        "- Packet 6: Pad 2 secondary lane - P2B, P2H, P2C, P2F, P2T, P2P, P2G, P2R, P2X, P2Z - Pad 2 lane behavior for the current read-only phase",
        "- Packet 6 deferred/safe: P2M",
        "- Packet 7: Pad 3 SY Raw lane - P3A, SA, SL, SB, SX, SW, P3R, P3X - Pad 3 lane behavior for the current read-only phase",
        "- Packet 7 deferred/safe: P3M",
        "- Packet 8: Pad 4 BD Acoustic lane - P4A, P4R, P4X - Pad 4 command-helper scope for the current read-only phase",
        "- Packet 8 deferred/safe: P4M",
        "Runtime-Adjacent Mock-Only Safe Failures:",
        "- PZ",
        "- B",
        "- L",
        "Parked Scope:",
        "- fourth runtime-adjacent candidate",
        "- profile 4 mock mapper support",
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
        "- cli_visibility: present",
        "- active_behavior: absent",
        "- hardware_required: False",
    ]


def test_returned_report_data_is_copied_and_mutation_safe():
    from rytm_randomizer.reports import build_behavior_parity_coverage_report

    report = build_behavior_parity_coverage_report()
    report["accepted_packet_coverage"] = ("MUTATED",)
    report["selected_isolated_pad_packet_coverage"][0]["packet"] = "MUTATED"
    report["pad_lane_packet_coverage"][0]["packet"] = "MUTATED"
    report["protected_file_state"]["v134_reference"] = "MUTATED"

    fresh_report = build_behavior_parity_coverage_report()

    assert fresh_report["accepted_packet_coverage"][0] == (
        "Packet 1 menu/status and utility intent"
    )
    assert fresh_report["selected_isolated_pad_packet_coverage"][0]["packet"] == "11A"
    assert fresh_report["pad_lane_packet_coverage"][0]["packet"] == "5"
    assert fresh_report["protected_file_state"]["v134_reference"] == "untouched"


def test_no_real_midi_library_is_imported():
    import rytm_randomizer.reports  # noqa: F401

    assert "mido" not in sys.modules
    assert "rtmidi" not in sys.modules


def test_passive_cli_report_behavior_remains_unchanged():
    result = run_cli("report")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text("registry_report_expected.txt")
    assert result.stderr == ""


def test_no_packet_12_cli_visibility_or_active_names_are_exposed():
    import rytm_randomizer.reports as report

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

    import rytm_randomizer.reports as report

    source = inspect.getsource(report)

    assert "argparse" not in source
    assert "evaluate_mock_active_boundary" not in source
    assert "MockMidiSender(" not in source
    assert "from .mock_midi import" not in source


if __name__ == "__main__":
    test_importing_behavior_parity_coverage_report_prints_nothing()
    test_report_summarizes_packet_coverage_and_runtime_adjacent_surfaces()
    test_report_records_structured_selected_isolated_pad_packet_coverage()
    test_report_records_structured_pad_lane_packet_coverage()
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
