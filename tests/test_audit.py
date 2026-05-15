import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from rytm_randomizer.commands import COMMANDS
from rytm_randomizer.inspection import SAFETY_SUMMARY, audit_command_registry


def test_real_commands_registry_audit_passes_validation():
    report = audit_command_registry(COMMANDS)

    assert report["registry_name"] == "COMMANDS"
    assert report["command_count"] == len(COMMANDS)
    assert report["validation"] == {
        "ok": True,
        "errors": [],
    }


def test_real_commands_registry_is_non_executable_and_scaffold_only():
    report = audit_command_registry(COMMANDS)

    assert report["all_non_executable"] is True
    assert report["all_scaffold_only"] is True


def test_scene_group_and_pad_scopes_are_counted():
    report = audit_command_registry(COMMANDS)

    assert report["scopes"]["four_pad_group"] > 0
    assert report["scopes"]["pad_1"] > 0
    assert report["scopes"]["pad_2"] > 0
    assert report["scopes"]["pad_3"] > 0
    assert report["scopes"]["pad_4"] > 0
    assert report["categories"]["scene"] > 0
    assert report["categories"]["load"] > 0
    assert report["categories"]["mutation"] > 0


def test_pad_counts_are_limited_to_pads_1_to_4_where_present():
    report = audit_command_registry(COMMANDS)

    assert set(report["pads"]).issubset({1, 2, 3, 4})
    assert report["pads"][1] > 0
    assert report["pads"][2] > 0
    assert report["pads"][3] > 0
    assert report["pads"][4] > 0


def test_synthetic_invalid_registry_reports_validation_errors():
    report = audit_command_registry(
        {
            "BAD": {
                "executable": True,
                "scaffold_only": True,
                "v134_reference_command": True,
            },
        },
        registry_name="SYNTHETIC",
    )

    assert report["registry_name"] == "SYNTHETIC"
    assert report["validation"]["ok"] is False
    assert "BAD: executable must not be True" in report["validation"]["errors"]
    assert report["all_non_executable"] is False
    assert report["all_scaffold_only"] is True


def test_every_audit_report_includes_safety_summary():
    reports = [
        audit_command_registry(COMMANDS),
        audit_command_registry(
            {
                "SAFE": {
                    "type": "print",
                    "executable": False,
                    "scaffold_only": True,
                    "v134_reference_command": True,
                },
            }
        ),
    ]

    for report in reports:
        assert report["safety_summary"] == SAFETY_SUMMARY


def test_audit_does_not_mutate_source_metadata():
    registry = {
        "SAFE": {
            "type": "print",
            "scope": "four_pad_group",
            "executable": False,
            "scaffold_only": True,
            "v134_reference_command": True,
        },
    }

    report = audit_command_registry(registry)
    report["categories"]["print"] = 99
    report["scopes"]["four_pad_group"] = 99

    assert registry == {
        "SAFE": {
            "type": "print",
            "scope": "four_pad_group",
            "executable": False,
            "scaffold_only": True,
            "v134_reference_command": True,
        },
    }


if __name__ == "__main__":
    test_real_commands_registry_audit_passes_validation()
    test_real_commands_registry_is_non_executable_and_scaffold_only()
    test_scene_group_and_pad_scopes_are_counted()
    test_pad_counts_are_limited_to_pads_1_to_4_where_present()
    test_synthetic_invalid_registry_reports_validation_errors()
    test_every_audit_report_includes_safety_summary()
    test_audit_does_not_mutate_source_metadata()
