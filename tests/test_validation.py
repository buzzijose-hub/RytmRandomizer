from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from rytm_randomizer.commands import COMMANDS
from rytm_randomizer.validation import validate_command_registry


def test_existing_commands_registry_passes_validation():
    result = validate_command_registry(COMMANDS)

    assert result == {
        "ok": True,
        "errors": [],
    }


def test_executable_true_fails_validation():
    result = validate_command_registry(
        {
            "BAD": {
                "executable": True,
                "scaffold_only": True,
                "v134_reference_command": True,
            },
        }
    )

    assert result["ok"] is False
    assert "BAD: executable must not be True" in result["errors"]


def test_forbidden_execution_field_fails_validation():
    result = validate_command_registry(
        {
            "BAD": {
                "handler": "do_not_call",
                "executable": False,
                "scaffold_only": True,
                "v134_reference_command": True,
            },
        }
    )

    assert result["ok"] is False
    assert "BAD: forbidden execution field 'handler'" in result["errors"]


def test_forbidden_pad_reference_fails_validation():
    result = validate_command_registry(
        {
            "BAD": {
                "pad": 5,
                "executable": False,
                "scaffold_only": True,
                "v134_reference_command": True,
            },
        }
    )

    assert result["ok"] is False
    assert "BAD: forbidden pad reference at metadata.pad" in result["errors"]


def test_missing_scaffold_command_fields_fail_validation():
    result = validate_command_registry(
        {
            "BAD": {
                "executable": False,
            },
        }
    )

    assert result["ok"] is False
    assert "BAD: scaffold_only must be True" in result["errors"]
    assert "BAD: v134_reference_command must be True" in result["errors"]


if __name__ == "__main__":
    test_existing_commands_registry_passes_validation()
    test_executable_true_fails_validation()
    test_forbidden_execution_field_fails_validation()
    test_forbidden_pad_reference_fails_validation()
    test_missing_scaffold_command_fields_fail_validation()
