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


def test_importing_active_boundary_report_prints_nothing():
    result = subprocess.run(
        [sys.executable, "-c", "import rytm_randomizer.active_boundary_report"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_report_summarizes_active_boundary_candidate_and_unsupported_profiles():
    from rytm_randomizer.active_boundary_report import build_active_boundary_report

    report = build_active_boundary_report()

    assert report["title"] == "RytmRandomizer Active Boundary Report"
    assert report["accepted_candidate"] == {
        "source_kind": "group_profile",
        "profile_key": "2",
        "name": "My BD Hard",
        "group_pad": 1,
        "machine_value": 0,
        "target": "Pad 1 / BD Hard",
    }
    assert report["unsupported_profiles"] == (
        {
            "profile_key": "3",
            "name": "My BD Classic",
            "group_pad": 2,
            "machine_value": 1,
            "target": "Pad 2 / BD Classic",
            "reason": "mock mapper/report scope only; not active-boundary supported",
        },
        {
            "profile_key": "4",
            "name": "My BD Acoustic",
            "group_pad": 4,
            "machine_value": 30,
            "target": "Pad 4 / BD Acoustic",
            "reason": "parked until separately approved",
        },
    )
    assert report["unsupported_source_kinds"] == ("scene", "command")


def test_report_records_required_conditions_and_read_only_boundaries():
    from rytm_randomizer.active_boundary_report import build_active_boundary_report

    report = build_active_boundary_report()

    assert report["required_conditions"] == (
        "explicit arming",
        "dry-run confirmation",
        "supported source kind",
        "supported source key",
        "injected MockMidiSender",
    )
    assert report["safe_failure_summary"] == (
        "missing arming emits no messages",
        "missing dry-run confirmation emits no messages",
        "unsupported source kind emits no messages",
        "unsupported or unknown key emits no messages",
        "invalid request or sender type fails before message emission",
    )
    assert report["mock_only"] is True
    assert report["hardware_required"] is False
    assert report["real_midi"] == "absent"
    assert report["port_opening"] == "absent"
    assert report["active_cli_behavior"] == "absent"
    assert report["dispatch"] == "absent"
    assert report["command_execution"] == "absent"
    assert report["scene_execution"] == "absent"
    assert report["hardware_behavior"] == "absent"


def test_report_summary_is_deterministic():
    from rytm_randomizer.active_boundary_report import summarize_active_boundary_report

    assert summarize_active_boundary_report() == {
        "title": "RytmRandomizer Active Boundary Report",
        "accepted_key": "2",
        "unsupported_keys": ("3", "4"),
        "required_condition_count": 5,
        "mock_only": True,
        "active_cli_behavior": "absent",
        "hardware_required": False,
    }


def test_formatted_report_is_deterministic_and_human_readable():
    from rytm_randomizer.active_boundary_report import format_active_boundary_report

    first = format_active_boundary_report()
    second = format_active_boundary_report()

    assert first == second
    assert first == [
        "RytmRandomizer Active Boundary Report",
        "Accepted Active Boundary Candidate:",
        "- group_profile 2: My BD Hard (Pad 1 / BD Hard)",
        "Unsupported Active Boundary Profiles:",
        "- 3: My BD Classic (Pad 2 / BD Classic) - mock mapper/report scope only; not active-boundary supported",
        "- 4: My BD Acoustic (Pad 4 / BD Acoustic) - parked until separately approved",
        "Required Conditions:",
        "- explicit arming",
        "- dry-run confirmation",
        "- supported source kind",
        "- supported source key",
        "- injected MockMidiSender",
        "Active Boundary Safety:",
        "- mock_only: True",
        "- hardware_required: False",
        "- real_midi: absent",
        "- port_opening: absent",
        "- active_cli_behavior: absent",
        "- dispatch: absent",
        "- command_execution: absent",
        "- scene_execution: absent",
        "- hardware_behavior: absent",
        "Closeout Coverage:",
        "- Mock-Only Active Candidate",
        "- Active Boundary",
    ]


def test_returned_report_data_is_copied_and_mutation_safe():
    from rytm_randomizer.active_boundary_report import build_active_boundary_report

    report = build_active_boundary_report()
    report["accepted_candidate"]["name"] = "MUTATED"
    report["unsupported_profiles"][0]["name"] = "MUTATED"
    report["required_conditions"] = ("MUTATED",)

    fresh_report = build_active_boundary_report()

    assert fresh_report["accepted_candidate"]["name"] == "My BD Hard"
    assert fresh_report["unsupported_profiles"][0]["name"] == "My BD Classic"
    assert fresh_report["required_conditions"] == (
        "explicit arming",
        "dry-run confirmation",
        "supported source kind",
        "supported source key",
        "injected MockMidiSender",
    )


def test_no_real_midi_library_is_imported():
    import rytm_randomizer.active_boundary_report  # noqa: F401

    assert "mido" not in sys.modules
    assert "rtmidi" not in sys.modules


def test_passive_cli_report_behavior_remains_unchanged():
    result = run_cli("report")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text("registry_report_expected.txt")
    assert result.stderr == ""


def test_no_profile_3_or_4_active_boundary_support_is_added():
    from rytm_randomizer.active_boundary import (
        ActiveBoundaryRequest,
        evaluate_mock_active_boundary,
    )
    from rytm_randomizer.mock_midi import MockMidiSender

    for key in ("3", "4"):
        sender = MockMidiSender()
        request = ActiveBoundaryRequest(
            source_kind="group_profile",
            source_key=key,
            armed=True,
            dry_run_confirmed=True,
            target="mock",
        )

        result = evaluate_mock_active_boundary(request, sender)

        assert result.accepted is False
        assert result.reason == "unsupported_or_unknown_key"
        assert result.emitted_messages == ()
        assert sender.sent_messages == ()


def test_active_boundary_report_exposes_no_active_behavior_names():
    import rytm_randomizer.active_boundary_report as report

    exposed_names = set(dir(report))

    assert "execute_command" not in exposed_names
    assert "send_command" not in exposed_names
    assert "hardware_test" not in exposed_names
    assert "open_port" not in exposed_names
    assert "open_midi_port" not in exposed_names
    assert "send_midi" not in exposed_names
    assert "MidiPortProvider" not in exposed_names


if __name__ == "__main__":
    test_importing_active_boundary_report_prints_nothing()
    test_report_summarizes_active_boundary_candidate_and_unsupported_profiles()
    test_report_records_required_conditions_and_read_only_boundaries()
    test_report_summary_is_deterministic()
    test_formatted_report_is_deterministic_and_human_readable()
    test_returned_report_data_is_copied_and_mutation_safe()
    test_no_real_midi_library_is_imported()
    test_passive_cli_report_behavior_remains_unchanged()
    test_no_profile_3_or_4_active_boundary_support_is_added()
    test_active_boundary_report_exposes_no_active_behavior_names()
