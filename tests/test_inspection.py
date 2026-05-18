import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from rytm_randomizer.commands import COMMANDS
from rytm_randomizer.inspection import inspect_command
import pytest

# WS-M4: mark this module as fast-suite; pytest -m fast skips the 505
# warm-worker V1.34 parity fixtures and runs in <60s.
pytestmark = pytest.mark.fast


def test_known_scene_command_returns_passive_report():
    report = inspect_command(COMMANDS, "S1A")

    assert report["exists"] is True
    assert report["command"] == "S1A"
    assert report["executable"] is False
    assert report["scaffold_only"] is True
    assert report["v134_reference_command"] is True
    assert report["scope"] == "four_pad_group"
    assert report["type"] == "scene"
    assert report["metadata"]["name"] == "Rolling Light"
    assert report["validation"] == {
        "ok": True,
        "errors": [],
    }


def test_unknown_command_returns_not_found_report():
    report = inspect_command(COMMANDS, "UNKNOWN")

    assert report == {
        "exists": False,
        "command": "UNKNOWN",
        "metadata": None,
        "validation": {
            "ok": True,
            "errors": [],
        },
    }


def test_group_command_report_includes_non_executable_scaffold_fields():
    report = inspect_command(COMMANDS, "O")

    assert report["exists"] is True
    assert report["executable"] is False
    assert report["scaffold_only"] is True
    assert report["v134_reference_command"] is True
    assert report["scope"] == "four_pad_group"
    assert report["type"] == "load"
    assert report["label"] == "load full 4-pad group anchors"


def test_pad_command_report_preserves_pad_scope_type_and_label():
    report = inspect_command(COMMANDS, "P3A")

    assert report["exists"] is True
    assert report["pad"] == 3
    assert report["scope"] == "pad_3"
    assert report["type"] == "anchor_return"
    assert report["label"] == "return Pad 3 to SY Raw Mid Bass anchor / home"


def test_synthetic_invalid_registry_returns_validation_errors():
    report = inspect_command(
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


def test_returned_metadata_is_a_copy():
    report = inspect_command(COMMANDS, "O")

    report["metadata"]["label"] = "mutated test label"

    assert COMMANDS["O"]["label"] == "load full 4-pad group anchors"


if __name__ == "__main__":
    test_known_scene_command_returns_passive_report()
    test_unknown_command_returns_not_found_report()
    test_group_command_report_includes_non_executable_scaffold_fields()
    test_pad_command_report_preserves_pad_scope_type_and_label()
    test_synthetic_invalid_registry_returns_validation_errors()
    test_returned_metadata_is_a_copy()
