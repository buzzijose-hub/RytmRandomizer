from pathlib import Path
import inspect
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


def _section_by_key(report, section_key):
    for section in report["supported_sections"]:
        if section["section_key"] == section_key:
            return section
    raise AssertionError(f"missing section {section_key!r}")


def _entry_by_key(section, command_key):
    for entry in section["entries"]:
        if entry["command_key"] == command_key:
            return entry
    raise AssertionError(f"missing entry {command_key!r}")


def test_importing_behavior_anchor_profile_report_prints_nothing():
    result = subprocess.run(
        [sys.executable, "-c", "import rytm_randomizer.behavior_anchor_profile_report"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_report_summarizes_supported_anchor_profile_sections():
    from rytm_randomizer.behavior_anchor_profile_report import (
        build_anchor_profile_report,
    )

    report = build_anchor_profile_report()

    assert report["title"] == "RytmRandomizer Anchor/Profile Behavior Report"
    assert tuple(section["section_key"] for section in report["supported_sections"]) == (
        "direct_packet_2_anchor_profile",
        "pad1_lane_anchor_profile",
        "pad2_lane_anchor_profile",
        "pad3_anchor",
        "pad4_anchor",
        "group_anchor",
        "current_anchor_state",
        "selected_profile_workflow",
        "selected_isolated_pad_target",
    )
    assert tuple(
        entry["command_key"]
        for entry in _section_by_key(report, "direct_packet_2_anchor_profile")["entries"]
    ) == ("BH", "BC", "BS", "BF")
    assert tuple(
        entry["command_key"]
        for entry in _section_by_key(report, "pad1_lane_anchor_profile")["entries"]
    ) == ("FZ", "BP", "PBH", "BI", "SBH", "BA")
    assert tuple(
        entry["command_key"]
        for entry in _section_by_key(report, "pad2_lane_anchor_profile")["entries"]
    ) == ("P2B", "P2H", "P2C", "P2F", "P2Z")
    assert tuple(
        entry["command_key"] for entry in _section_by_key(report, "pad3_anchor")["entries"]
    ) == ("P3A", "SA")
    assert tuple(
        entry["command_key"] for entry in _section_by_key(report, "pad4_anchor")["entries"]
    ) == ("P4A",)


def test_report_entries_include_read_only_behavior_details():
    from rytm_randomizer.behavior_anchor_profile_report import (
        build_anchor_profile_report,
    )

    report = build_anchor_profile_report()

    bh = _entry_by_key(_section_by_key(report, "direct_packet_2_anchor_profile"), "BH")
    p2z = _entry_by_key(_section_by_key(report, "pad2_lane_anchor_profile"), "P2Z")
    group_z = _entry_by_key(_section_by_key(report, "group_anchor"), "Z")
    selected_m = _entry_by_key(_section_by_key(report, "selected_profile_workflow"), "M")

    assert bh == {
        "command_key": "BH",
        "label": "load Pad 1 BD Hard anchor, primary default",
        "behavior_family": "anchor/profile",
        "reason": "supported_anchor_profile_intent",
        "source_helper": "rytm_randomizer.behavior_anchor_profile",
        "target_pad": 1,
        "target_scope": "",
        "intent_kind": "anchor/profile",
        "concept": "Pad 1 / BD Hard",
        "read_only": True,
        "sends_real_midi": False,
        "opens_ports": False,
        "hardware_required": False,
        "active_behavior": False,
    }
    assert p2z["command_key"] == "P2Z"
    assert p2z["intent_kind"] == "anchor_return"
    assert p2z["concept"] == "Pad 2 current profile anchor"
    assert group_z["behavior_family"] == "scene-group/group-anchor-intent"
    assert group_z["intent_kind"] == "anchor_return"
    assert selected_m["concept"] == "current_selected_profile_state"
    for entry in (bh, p2z, group_z, selected_m):
        assert entry["read_only"] is True
        assert entry["sends_real_midi"] is False
        assert entry["opens_ports"] is False
        assert entry["hardware_required"] is False
        assert entry["active_behavior"] is False


def test_report_marks_pz_and_profile_4_as_parked_not_supported():
    from rytm_randomizer.behavior_anchor_profile_report import (
        build_anchor_profile_report,
    )

    report = build_anchor_profile_report()

    supported_keys = {
        entry["command_key"]
        for section in report["supported_sections"]
        for entry in section["entries"]
    }

    assert "PZ" not in supported_keys
    assert report["parked_sections"] == (
        {
            "key": "PZ",
            "kind": "selected_isolated_pad_anchor_return",
            "status": "parked",
            "reason": "deferred_selected_isolated_pad_anchor_return",
            "source_helper": "rytm_randomizer.behavior_selected_isolated_pad",
            "requires_separate_approval": True,
        },
        {
            "key": "4",
            "kind": "group_profile_mock_mapper_support",
            "status": "parked",
            "reason": "profile 4 mock mapper support remains parked until separately approved",
            "source_helper": "rytm_randomizer.mock_message_mapper",
            "requires_separate_approval": True,
        },
    )


def test_report_records_safety_boundaries_and_closeout_coverage():
    from rytm_randomizer.behavior_anchor_profile_report import (
        build_anchor_profile_report,
    )

    report = build_anchor_profile_report()

    assert report["safety"] == {
        "read_only": True,
        "passive_cli_visibility": "present",
        "real_midi": "absent",
        "port_opening": "absent",
        "midi_sending": "absent",
        "active_behavior": "absent",
        "active_cli_wiring": "absent",
        "hardware_required": False,
        "runtime_state": "absent",
        "package_metadata_changes": "absent",
    }
    assert report["closeout_coverage"] == (
        "Behavior Anchor Profile",
        "Behavior Pad 1 Lane",
        "Behavior Pad 2 Lane",
        "Behavior Pad 3 Lane",
        "Behavior Pad 4 Lane",
        "Behavior Scene Group",
        "Behavior Undo Commit State",
        "Behavior Selected Profile",
        "Behavior Selected Isolated Pad",
    )


def test_report_summary_is_deterministic():
    from rytm_randomizer.behavior_anchor_profile_report import (
        summarize_anchor_profile_report,
    )

    assert summarize_anchor_profile_report() == {
        "title": "RytmRandomizer Anchor/Profile Behavior Report",
        "supported_section_count": 9,
        "supported_entry_count": 25,
        "parked_count": 2,
        "parked_keys": ("PZ", "4"),
        "read_only": True,
        "active_behavior": "absent",
        "hardware_required": False,
    }


def test_formatted_report_is_deterministic_and_human_readable():
    from rytm_randomizer.behavior_anchor_profile_report import (
        format_anchor_profile_report,
    )

    first = format_anchor_profile_report()
    second = format_anchor_profile_report()

    assert first == second
    assert first == [
        "RytmRandomizer Anchor/Profile Behavior Report",
        "Supported Anchor/Profile Sections:",
        "- direct_packet_2_anchor_profile: BH, BC, BS, BF",
        "- pad1_lane_anchor_profile: FZ, BP, PBH, BI, SBH, BA",
        "- pad2_lane_anchor_profile: P2B, P2H, P2C, P2F, P2Z",
        "- pad3_anchor: P3A, SA",
        "- pad4_anchor: P4A",
        "- group_anchor: O, Z",
        "- current_anchor_state: B, E",
        "- selected_profile_workflow: P, M",
        "- selected_isolated_pad_target: L",
        "Parked/Safe Scope:",
        "- PZ: selected_isolated_pad_anchor_return - deferred_selected_isolated_pad_anchor_return",
        "- 4: group_profile_mock_mapper_support - profile 4 mock mapper support remains parked until separately approved",
        "Safety:",
        "- read_only: True",
        "- passive_cli_visibility: present",
        "- real_midi: absent",
        "- port_opening: absent",
        "- midi_sending: absent",
        "- active_behavior: absent",
        "- active_cli_wiring: absent",
        "- hardware_required: False",
        "- runtime_state: absent",
        "- package_metadata_changes: absent",
        "Recommended Next Branch: documentation checkpoint after passive CLI visibility",
    ]


def test_returned_report_data_is_copied_and_mutation_safe():
    from rytm_randomizer.behavior_anchor_profile_report import (
        build_anchor_profile_report,
    )

    report = build_anchor_profile_report()
    report["supported_sections"][0]["entries"][0]["label"] = "MUTATED"
    report["parked_sections"][0]["reason"] = "MUTATED"
    report["safety"]["real_midi"] = "MUTATED"

    fresh_report = build_anchor_profile_report()

    assert fresh_report["supported_sections"][0]["entries"][0]["label"] == (
        "load Pad 1 BD Hard anchor, primary default"
    )
    assert fresh_report["parked_sections"][0]["reason"] == (
        "deferred_selected_isolated_pad_anchor_return"
    )
    assert fresh_report["safety"]["real_midi"] == "absent"


def test_report_module_does_not_call_cli_or_mock_message_mapping():
    import rytm_randomizer.behavior_anchor_profile_report as report

    source = inspect.getsource(report)

    assert "from .cli" not in source
    assert "import rytm_randomizer.cli" not in source
    assert "from .mock_message_mapper" not in source
    assert "import rytm_randomizer.mock_message_mapper" not in source
    assert "map_group_profile_to_mock_messages" not in source


def test_no_real_midi_library_is_imported():
    import rytm_randomizer.behavior_anchor_profile_report  # noqa: F401

    assert "mido" not in sys.modules
    assert "rtmidi" not in sys.modules


def test_passive_cli_visibility_is_formatter_only_and_existing_report_remains_unchanged():
    help_result = run_cli("--help")
    anchor_profile_result = run_cli("anchor-profile-report")
    report_result = run_cli("report")

    assert help_result.returncode == 0
    assert "anchor-profile-report" in help_result.stdout
    assert anchor_profile_result.returncode == 0
    assert "RytmRandomizer Anchor/Profile Behavior Report" in anchor_profile_result.stdout
    assert "execute-command" not in anchor_profile_result.stdout
    assert "send-command" not in anchor_profile_result.stdout
    assert "hardware-test" not in anchor_profile_result.stdout
    assert report_result.returncode == 0
    assert normalize_newlines(report_result.stdout) == fixture_text(
        "registry_report_expected.txt"
    )
    assert report_result.stderr == ""


def test_pz_readiness_and_profile_4_behavior_remain_safe():
    from rytm_randomizer.behavior_selected_isolated_pad import (
        evaluate_selected_isolated_pad_behavior,
    )
    from rytm_randomizer.mock_message_mapper import (
        MockMessageMappingError,
        map_group_profile_to_mock_messages,
    )

    pz = evaluate_selected_isolated_pad_behavior("PZ")

    assert pz.accepted is False
    assert pz.reason == "anchor_unavailable_for_selected_target"
    assert pz.utility_action == "describe_selected_isolated_pad_anchor_return_readiness"
    assert pz.anchor_return_intent is True
    assert pz.anchor_return_executed is False
    assert pz.sends_real_midi is False
    assert pz.opens_ports is False
    assert pz.hardware_required is False

    try:
        map_group_profile_to_mock_messages("4")
    except MockMessageMappingError as exc:
        assert "Group profile '4' is not supported by the mock mapper" in str(exc)
    else:
        raise AssertionError("profile 4 should remain unsupported")


def test_behavior_anchor_profile_report_exposes_no_active_behavior_names():
    import rytm_randomizer.behavior_anchor_profile_report as report

    exposed_names = set(dir(report))

    assert "execute_command" not in exposed_names
    assert "send_command" not in exposed_names
    assert "hardware_test" not in exposed_names
    assert "open_port" not in exposed_names
    assert "open_midi_port" not in exposed_names
    assert "send_midi" not in exposed_names
    assert "MidiPortProvider" not in exposed_names


def test_package_metadata_is_declared_without_legacy_setup_files():
    assert (PROJECT_ROOT / "pyproject.toml").exists()
    for filename in ("requirements.txt", "setup.py", "setup.cfg"):
        assert not (PROJECT_ROOT / filename).exists()


if __name__ == "__main__":
    test_importing_behavior_anchor_profile_report_prints_nothing()
    test_report_summarizes_supported_anchor_profile_sections()
    test_report_entries_include_read_only_behavior_details()
    test_report_marks_pz_and_profile_4_as_parked_not_supported()
    test_report_records_safety_boundaries_and_closeout_coverage()
    test_report_summary_is_deterministic()
    test_formatted_report_is_deterministic_and_human_readable()
    test_returned_report_data_is_copied_and_mutation_safe()
    test_report_module_does_not_call_cli_or_mock_message_mapping()
    test_no_real_midi_library_is_imported()
    test_passive_cli_visibility_is_formatter_only_and_existing_report_remains_unchanged()
    test_pz_readiness_and_profile_4_behavior_remain_safe()
    test_behavior_anchor_profile_report_exposes_no_active_behavior_names()
    test_package_metadata_is_declared_without_legacy_setup_files()
