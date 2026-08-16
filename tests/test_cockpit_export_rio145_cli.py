from __future__ import annotations

import json
from pathlib import Path

import pytest

from rytm_randomizer import cli
from rytm_randomizer.cockpit.export import rio145_cli

pytestmark = pytest.mark.fast

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "rio145"
SPECS = ROOT / "specs" / "rio145"

COMMANDS = (
    "rio145-inspect-sysex",
    "rio145-diff-sysex",
    "rio145-validate-roundtrip",
    "rio145-build-kit",
    "rio145-validate-return",
    "rio145-export-oxi-manifest",
)


@pytest.mark.parametrize("command", COMMANDS)
def test_rio145_help_is_passive(command: str, capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.main((command, "--help")) == 0
    captured = capsys.readouterr()
    assert captured.out.startswith("Usage: rio145-")
    assert captured.err == ""


def test_inspect_and_build_commands_emit_json(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert (
        cli.main(
            (
                "rio145-inspect-sysex",
                "--input",
                str(FIXTURES / "A4_Test1_Init_Kit.syx"),
            )
        )
        == 0
    )
    inspected = json.loads(capsys.readouterr().out)
    assert inspected["frame_count"] == 1
    assert inspected["hardware_access"] is False

    output = tmp_path / "a4.syx"
    assert (
        cli.main(
            (
                "rio145-build-kit",
                "--device",
                "analog_four_mk2",
                "--reference",
                str(FIXTURES / "A4_Test1_Init_Kit.syx"),
                "--recipe",
                str(SPECS / "come_to_rio_a4_core.json"),
                "--destination-slot",
                "0",
                "--output",
                str(output),
            )
        )
        == 0
    )
    built = json.loads(capsys.readouterr().out)
    assert output.exists()
    assert built["status"] == "OFFLINE_KIT_COMPILED"
    assert built["hardware_access"] is False


def test_cli_rejects_invalid_slot_and_overwrite(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    args = (
        "rio145-build-kit",
        "--device",
        "analog_four_mk2",
        "--reference",
        str(FIXTURES / "A4_Test1_Init_Kit.syx"),
        "--recipe",
        str(SPECS / "come_to_rio_a4_core.json"),
        "--destination-slot",
        "128",
        "--output",
        str(tmp_path / "a4.syx"),
    )
    assert cli.main(args) == 2
    assert "0..127" in capsys.readouterr().err


@pytest.mark.parametrize(
    ("args", "message"),
    [
        (("rio145-inspect-sysex",), "arguments are required"),
        (("rio145-inspect-sysex", "--unknown", "x"), "unknown option"),
        (
            ("rio145-inspect-sysex", "--input", "a", "--input", "b"),
            "only once",
        ),
        (("rio145-inspect-sysex", "--input"), "requires a value"),
        (("rio145-inspect-sysex", "--input", "--left"), "requires a value"),
        (
            (
                "rio145-build-kit",
                "--device",
                "analog_four_mk2",
                "--reference",
                "a",
                "--recipe",
                "b",
                "--destination-slot",
                "slot",
                "--output",
                "c",
            ),
            "integer from 0 to 127",
        ),
        (
            (
                "rio145-build-kit",
                "--device",
                "analog_four_mk2",
                "--reference",
                "a",
                "--recipe",
                "b",
                "--destination-slot",
                "01",
                "--output",
                "c",
            ),
            "0..127",
        ),
        (("rio145-diff-sysex", "--left", "a"), "missing required option"),
        (
            (
                "rio145-build-kit",
                "--device",
                "analog_four_mk2",
                "--overwrite",
                "--overwrite",
                "--reference",
                "a",
                "--recipe",
                "b",
                "--destination-slot",
                "0",
                "--output",
                "c",
            ),
            "overwrite may be specified only once",
        ),
        (
            ("rio145-build-kit", "--device", "analog_four_mkii"),
            "must be analog_four_mk2 or analog_rytm_mk2",
        ),
        (("rio145-inspect-sysex", "--overwrite"), "unknown option"),
    ],
)
def test_rio145_parser_errors_are_action_specific(
    args: tuple[str, ...], message: str, capsys: pytest.CaptureFixture[str]
) -> None:
    assert cli.main(args) == 2
    captured = capsys.readouterr()
    assert message in captured.err
    assert captured.out == ""


def test_remaining_commands_execute_passively(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    commands = (
        (
            "rio145-diff-sysex",
            "--left",
            str(FIXTURES / "A4_Test1_Init_Kit.syx"),
            "--right",
            str(FIXTURES / "A4_Test2_T1_OSC1_FIN_P1_Kit.syx"),
        ),
        (
            "rio145-validate-roundtrip",
            "--input",
            str(FIXTURES / "A4_Test1_Init_Kit.syx"),
        ),
        (
            "rio145-build-kit",
            "--device",
            "analog_rytm_mk2",
            "--reference",
            str(FIXTURES / "RYTM_Test1_Init_Kit.syx"),
            "--recipe",
            str(SPECS / "come_to_rio_rytm_core.json"),
            "--destination-slot",
            "0",
            "--output",
            str(tmp_path / "rytm.syx"),
        ),
        (
            "rio145-validate-return",
            "--device",
            "analog_four_mk2",
            "--reference",
            str(FIXTURES / "A4_Test1_Init_Kit.syx"),
            "--recipe",
            str(SPECS / "come_to_rio_a4_core.json"),
            "--returned",
            str(FIXTURES / "A4_RIO145_CORE_RETURN_Kit.syx"),
        ),
        (
            "rio145-validate-return",
            "--device",
            "analog_rytm_mk2",
            "--reference",
            str(FIXTURES / "RYTM_Test1_Init_Kit.syx"),
            "--recipe",
            str(SPECS / "come_to_rio_rytm_core.json"),
            "--returned",
            str(FIXTURES / "RYTM_RIO145_AR_CORE_RETURN_Kit.syx"),
        ),
        (
            "rio145-export-oxi-manifest",
            "--manifest",
            str(SPECS / "oxi_program_manifest.json"),
            "--events",
            str(SPECS / "oxi_event_list.csv"),
            "--output",
            str(tmp_path / "oxi.json"),
        ),
    )

    for command in commands:
        assert cli.main(command) == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload["hardware_access"] is False


def test_overwrite_is_explicit_and_missing_files_fail_offline(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    output = tmp_path / "a4.syx"
    base = (
        "rio145-build-kit",
        "--device",
        "analog_four_mk2",
        "--reference",
        str(FIXTURES / "A4_Test1_Init_Kit.syx"),
        "--recipe",
        str(SPECS / "come_to_rio_a4_core.json"),
        "--destination-slot",
        "0",
        "--output",
        str(output),
    )
    assert cli.main(base) == 0
    capsys.readouterr()
    assert cli.main((*base, "--overwrite")) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "OFFLINE_KIT_COMPILED"

    assert cli.main(("rio145-inspect-sysex", "--input", str(tmp_path / "missing.syx"))) == 2
    assert "offline_validation" in capsys.readouterr().err


@pytest.mark.parametrize(
    ("action", "options", "message"),
    [
        ("inspect", {}, "option 'input' is missing"),
        (
            "build",
            {
                "device": "analog_four_mk2",
                "reference": Path("reference.syx"),
                "recipe": Path("recipe.json"),
                "destination_slot": True,
                "output": Path("output.syx"),
            },
            "destination-slot option is missing",
        ),
        (
            "build",
            {
                "device": "unsupported_device",
                "reference": Path("reference.syx"),
                "recipe": Path("recipe.json"),
                "destination_slot": 0,
                "output": Path("output.syx"),
            },
            "device option is missing or invalid",
        ),
        (
            "export_oxi",
            {
                "manifest": Path("manifest.json"),
                "events": Path("events.csv"),
                "output": Path("output.json"),
                "overwrite": "yes",
            },
            "overwrite option is invalid",
        ),
    ],
)
def test_internal_option_contracts_fail_closed(
    action: rio145_cli.Action,
    options: dict[str, object],
    message: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert rio145_cli.handle_rio145_command(action=action, options=options) == 2
    assert message in capsys.readouterr().err
