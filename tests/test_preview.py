import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pytest

from rytm_randomizer.commands import COMMANDS
from rytm_randomizer.inspection import SAFETY_SUMMARY, preview_command

# WS-M4: mark this module as fast-suite; pytest -m fast skips the 505
# warm-worker V1.34 parity fixtures and runs in <60s.
pytestmark = pytest.mark.fast


def assert_safe_dry_run_report(report):
    assert report["safety_summary"] == SAFETY_SUMMARY


def test_known_scene_command_preview_is_passive():
    report = preview_command(COMMANDS, "S1A")

    assert report["command"] == "S1A"
    assert report["exists"] is True
    assert report["category"] == "scene"
    assert report["scope"] == "four_pad_group"
    assert report["target"] == "four_pad_group"
    assert report["pad"] is None
    assert report["scaffold_only"] is True
    assert report["executable"] is False
    assert report["forbidden_or_no_touch"] is False
    assert report["validation"] == {
        "ok": True,
        "errors": [],
    }
    assert_safe_dry_run_report(report)


def test_group_command_preview_is_passive():
    report = preview_command(COMMANDS, "O")

    assert report["command"] == "O"
    assert report["exists"] is True
    assert report["category"] == "load"
    assert report["scope"] == "four_pad_group"
    assert report["target"] == "four_pad_group"
    assert report["pad"] is None
    assert report["scaffold_only"] is True
    assert report["executable"] is False
    assert_safe_dry_run_report(report)


def test_pad_command_preview_reports_pad_target():
    report = preview_command(COMMANDS, "P3A")

    assert report["command"] == "P3A"
    assert report["exists"] is True
    assert report["category"] == "anchor_return"
    assert report["scope"] == "pad_3"
    assert report["target"] == "pad_3"
    assert report["pad"] == 3
    assert report["scaffold_only"] is True
    assert report["executable"] is False
    assert_safe_dry_run_report(report)


def test_unknown_command_preview_is_passive():
    report = preview_command(COMMANDS, "UNKNOWN")

    assert report == {
        "command": "UNKNOWN",
        "exists": False,
        "category": None,
        "scope": None,
        "target": None,
        "pad": None,
        "scaffold_only": None,
        "executable": None,
        "forbidden_or_no_touch": False,
        "validation": {
            "ok": True,
            "errors": [],
        },
        "safety_summary": SAFETY_SUMMARY,
    }


def test_synthetic_invalid_registry_preview_includes_validation_errors():
    report = preview_command(
        {
            "BAD": {
                "executable": True,
                "scaffold_only": True,
                "v134_reference_command": True,
            },
        },
        "BAD",
    )

    assert report["exists"] is True
    assert report["validation"]["ok"] is False
    assert "BAD: executable must not be True" in report["validation"]["errors"]
    assert_safe_dry_run_report(report)


def test_preview_report_does_not_mutate_source_metadata():
    registry = {
        "SAFE": {
            "type": "print",
            "label": "safe metadata",
            "executable": False,
            "scaffold_only": True,
            "v134_reference_command": True,
        },
    }

    report = preview_command(registry, "SAFE")
    report["validation"]["errors"].append("mutated test error")

    assert registry["SAFE"]["label"] == "safe metadata"
    assert preview_command(registry, "SAFE")["validation"] == {
        "ok": True,
        "errors": [],
    }


def test_every_preview_report_includes_safety_summary():
    reports = [
        preview_command(COMMANDS, "S1A"),
        preview_command(COMMANDS, "O"),
        preview_command(COMMANDS, "P3A"),
        preview_command(COMMANDS, "UNKNOWN"),
    ]

    for report in reports:
        assert_safe_dry_run_report(report)


if __name__ == "__main__":
    test_known_scene_command_preview_is_passive()
    test_group_command_preview_is_passive()
    test_pad_command_preview_reports_pad_target()
    test_unknown_command_preview_is_passive()
    test_synthetic_invalid_registry_preview_includes_validation_errors()
    test_preview_report_does_not_mutate_source_metadata()
    test_every_preview_report_includes_safety_summary()
