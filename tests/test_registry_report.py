import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pytest

from rytm_randomizer.registry import summarize_registry
from rytm_randomizer.reports import (
    build_registry_report,
    format_registry_report,
    summarize_registry_report,
)

# WS-M4: mark this module as fast-suite; pytest -m fast skips the 505
# warm-worker V1.34 parity fixtures and runs in <60s.
pytestmark = pytest.mark.fast

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
UNSUPPORTED_TEXT = (
    "MIDI sending",
    "MIDI port opening",
    "runtime dispatch",
    "command execution",
    "hardware state mutation",
    "SysEx writes",
    "GUI",
    "capture",
    "Analog Four",
    "Pads 5-12",
)


def normalize_newlines(text):
    return text.replace("\r\n", "\n").replace("\r", "\n").rstrip("\n")


def test_registry_report_includes_existing_sections():
    report = build_registry_report()

    assert report["title"] == "RytmRandomizer Passive Registry Report"
    assert report["sections"] == ("commands", "scenes", "group_profiles")
    assert report["known_sections"] == ("commands", "scenes", "group_profiles")


def test_registry_report_counts_match_registry_summary():
    report = build_registry_report()
    registry_summary = summarize_registry()

    assert report["section_counts"] == registry_summary["section_counts"]


def test_registry_report_summary_is_compact_and_copied():
    report = build_registry_report()
    summary = summarize_registry_report(report)

    assert summary == {
        "title": "RytmRandomizer Passive Registry Report",
        "section_count": 3,
        "total_items": sum(report["section_counts"].values()),
        "sections": ("commands", "scenes", "group_profiles"),
        "active_behavior": report["active_behavior"],
    }

    summary["active_behavior"]["sends_midi"] = True

    assert report["active_behavior"]["sends_midi"] is False


def test_formatted_registry_report_is_deterministic_and_human_readable():
    report = build_registry_report()
    lines = format_registry_report(report)

    assert lines == format_registry_report(report)
    assert lines[0] == "RytmRandomizer Passive Registry Report"
    assert "Sections:" in lines
    assert f"- commands: {report['section_counts']['commands']}" in lines
    assert f"- scenes: {report['section_counts']['scenes']}" in lines
    assert f"- group_profiles: {report['section_counts']['group_profiles']}" in lines
    assert "Safety Boundaries:" in lines
    assert "Unsupported Scope:" in lines
    assert "Active Behavior:" in lines
    assert "Source: rytm_randomizer.registry" in lines
    assert "In-memory only: True" in lines


def test_formatted_registry_report_matches_golden_fixture():
    expected = normalize_newlines(
        (FIXTURES_DIR / "registry_report_expected.txt").read_text(encoding="utf-8")
    )
    actual = normalize_newlines("\n".join(format_registry_report()))

    assert actual == expected


def test_registry_report_data_is_mutation_safe():
    report = build_registry_report()

    report["section_counts"]["commands"] = -1
    report["active_behavior"]["executes_commands"] = True

    fresh_report = build_registry_report()
    registry_summary = summarize_registry()

    assert fresh_report["section_counts"] == registry_summary["section_counts"]
    assert fresh_report["active_behavior"]["executes_commands"] is False


def test_registry_report_introduces_no_midi_or_execution_behavior():
    report = build_registry_report()

    assert report["active_behavior"] == {
        "executes_commands": False,
        "dispatches_commands": False,
        "sends_midi": False,
        "opens_ports": False,
        "mutates_hardware": False,
        "writes_sysex": False,
    }
    assert "no MIDI sending" in report["safety_boundaries"]
    assert "no command execution" in report["safety_boundaries"]
    assert "no runtime dispatch" in report["safety_boundaries"]


def test_registry_report_exposes_no_pads_5_to_12_or_analog_four_support():
    report = build_registry_report()

    for unsupported in UNSUPPORTED_TEXT:
        assert unsupported in report["unsupported_scope"]

    assert "Pads 5-12" in report["unsupported_scope"]
    assert "Analog Four" in report["unsupported_scope"]
    assert "no Pads 5-12 support" in report["safety_boundaries"]
    assert "no Analog Four support" in report["safety_boundaries"]


def test_registry_report_source_is_in_memory_only():
    report = build_registry_report()

    assert report["source"] == {
        "registry_module": "rytm_randomizer.registry",
        "sections": ("commands", "scenes", "group_profiles"),
        "in_memory_only": True,
    }


def test_importing_reports_has_no_side_effect_output():
    import importlib
    import io
    from contextlib import redirect_stdout

    import rytm_randomizer.reports as reports

    stream = io.StringIO()
    with redirect_stdout(stream):
        importlib.reload(reports)

    assert stream.getvalue() == ""


if __name__ == "__main__":
    test_registry_report_includes_existing_sections()
    test_registry_report_counts_match_registry_summary()
    test_registry_report_summary_is_compact_and_copied()
    test_formatted_registry_report_is_deterministic_and_human_readable()
    test_formatted_registry_report_matches_golden_fixture()
    test_registry_report_data_is_mutation_safe()
    test_registry_report_introduces_no_midi_or_execution_behavior()
    test_registry_report_exposes_no_pads_5_to_12_or_analog_four_support()
    test_registry_report_source_is_in_memory_only()
    test_importing_reports_has_no_side_effect_output()
