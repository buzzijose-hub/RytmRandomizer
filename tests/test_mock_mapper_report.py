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


def test_importing_mock_mapper_report_prints_nothing():
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


def test_report_summarizes_supported_and_unsupported_profiles():
    from rytm_randomizer.reports import build_mock_mapper_report

    report = build_mock_mapper_report()

    assert report["title"] == "RytmRandomizer Mock Mapper Report"
    assert report["supported_group_profiles"] == (
        {
            "profile_key": "2",
            "name": "My BD Hard",
            "group_pad": 1,
            "machine_value": 0,
            "target": "Pad 1 / BD Hard",
        },
        {
            "profile_key": "3",
            "name": "My BD Classic",
            "group_pad": 2,
            "machine_value": 1,
            "target": "Pad 2 / BD Classic",
        },
    )
    assert report["unsupported_safe_group_profiles"] == (
        {
            "profile_key": "4",
            "name": "My BD Acoustic",
            "group_pad": 4,
            "machine_value": 30,
            "target": "Pad 4 / BD Acoustic",
            "reason": "intentionally unsupported until separately approved",
        },
    )


def test_report_records_passive_mock_only_boundaries():
    from rytm_randomizer.reports import build_mock_mapper_report

    report = build_mock_mapper_report()

    assert report["mock_only"] is True
    assert report["real_midi"] == "absent"
    assert report["port_opening"] == "absent"
    assert report["cli_wiring"] == "absent"
    assert report["active_behavior"] == "absent"
    assert report["hardware_required"] is False
    assert report["analog_four_support"] == "absent"
    assert report["pads_5_12_support"] == "absent"


def test_formatted_report_is_deterministic_and_human_readable():
    from rytm_randomizer.reports import format_mock_mapper_report

    first = format_mock_mapper_report()
    second = format_mock_mapper_report()

    assert first == second
    assert first == [
        "RytmRandomizer Mock Mapper Report",
        "Supported Mock Group Profile Mappings:",
        "- 2: My BD Hard (Pad 1 / BD Hard)",
        "- 3: My BD Classic (Pad 2 / BD Classic)",
        "Unsupported/Safe Group Profiles:",
        "- 4: My BD Acoustic (Pad 4 / BD Acoustic) - intentionally unsupported until separately approved",
        "Mock Mapper Boundary:",
        "- mock_only: True",
        "- real_midi: absent",
        "- port_opening: absent",
        "- cli_wiring: absent",
        "- active_behavior: absent",
        "- hardware_required: False",
        "- analog_four_support: absent",
        "- pads_5_12_support: absent",
        "Source: rytm_randomizer.mock_message_mapper",
        "In-memory only: True",
    ]


def test_report_summary_is_deterministic():
    from rytm_randomizer.reports import summarize_mock_mapper_report

    assert summarize_mock_mapper_report() == {
        "title": "RytmRandomizer Mock Mapper Report",
        "supported_count": 2,
        "unsupported_safe_count": 1,
        "supported_keys": ("2", "3"),
        "unsupported_safe_keys": ("4",),
        "mock_only": True,
        "active_behavior": "absent",
    }


def test_returned_report_data_is_copied_and_mutation_safe():
    from rytm_randomizer.reports import build_mock_mapper_report

    report = build_mock_mapper_report()
    report["supported_group_profiles"][0]["name"] = "MUTATED"
    report["source"]["supported_keys"] = ("MUTATED",)

    fresh_report = build_mock_mapper_report()

    assert fresh_report["supported_group_profiles"][0]["name"] == "My BD Hard"
    assert fresh_report["source"]["supported_keys"] == ("2", "3")


def test_no_real_midi_library_is_imported():
    import rytm_randomizer.reports  # noqa: F401

    assert "mido" not in sys.modules
    assert "rtmidi" not in sys.modules


def test_passive_cli_report_behavior_remains_unchanged():
    result = run_cli("report")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text("registry_report_expected.txt")
    assert result.stderr == ""


def test_profile_4_mapping_is_not_added():
    from rytm_randomizer.mock_message_mapper import (
        MockMessageMappingError,
        map_group_profile_to_mock_messages,
    )

    try:
        map_group_profile_to_mock_messages("4")
    except MockMessageMappingError as exc:
        assert "Group profile '4' is not supported by the mock mapper" in str(exc)
    else:
        raise AssertionError("profile 4 should remain unsupported")


def test_no_out_of_scope_support_is_exposed():
    import rytm_randomizer.reports as report

    module_text = "\n".join(
        [
            report.__doc__ or "",
            report.build_mock_mapper_report.__doc__ or "",
            report.format_mock_mapper_report.__doc__ or "",
            report.summarize_mock_mapper_report.__doc__ or "",
        ]
    )

    assert "Analog Four support" not in module_text
    assert "Pads 5-12 support" not in module_text


def test_mock_mapper_report_exposes_no_active_behavior_names():
    import rytm_randomizer.reports as report

    exposed_names = set(dir(report))

    assert "execute_command" not in exposed_names
    assert "send_command" not in exposed_names
    assert "hardware_test" not in exposed_names


if __name__ == "__main__":
    test_importing_mock_mapper_report_prints_nothing()
    test_report_summarizes_supported_and_unsupported_profiles()
    test_report_records_passive_mock_only_boundaries()
    test_formatted_report_is_deterministic_and_human_readable()
    test_report_summary_is_deterministic()
    test_returned_report_data_is_copied_and_mutation_safe()
    test_no_real_midi_library_is_imported()
    test_passive_cli_report_behavior_remains_unchanged()
    test_profile_4_mapping_is_not_added()
    test_no_out_of_scope_support_is_exposed()
    test_mock_mapper_report_exposes_no_active_behavior_names()
