"""Operator-path tests for Analog Four saved-kit export."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from rytm_randomizer.cockpit.export.file_export_contracts import (
    LocalFileExportPhase,
    classify_local_file_export_error,
)

pytestmark = pytest.mark.fast

FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "analog_four_saved_kit"
SOURCE_FIXTURE = FIXTURE_DIR / "filter2_res_000_source.syx"
EXPECTED_FIXTURE = FIXTURE_DIR / "filter2_res_127_expected.syx"


def test_registered_cli_exports_exact_hardware_fixture(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from rytm_randomizer.cli import main

    output = tmp_path / "generated.syx"

    exit_code = main(
        [
            "analog-four-saved-kit-export",
            "--source",
            str(SOURCE_FIXTURE),
            "--output",
            str(output),
            "--filter2-resonance",
            "1:127",
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["kit_name"] == "KIT 1"
    assert payload["bytes_written"] == 2770
    assert payload["sha256"] == "5ebb386677aff324ef96d631e7888a9681caefbd976bdc2eac69b52a0fb0e26b"
    assert payload["mutations"] == [
        {
            "parameter": "Filter2 Resonance",
            "rendered_unpacked_value": 127,
            "screen_value": "127",
            "track": 1,
            "unpacked_offset": 140,
        }
    ]
    assert output.read_bytes() == EXPECTED_FIXTURE.read_bytes()


def test_cli_text_output_supports_four_tracks_and_overwrite(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from rytm_randomizer.cockpit.export.analog_four_cli import (
        handle_analog_four_saved_kit_export,
        parse_analog_four_saved_kit_export_args,
    )

    output = tmp_path / "four-tracks.syx"
    output.write_bytes(b"replace me")
    options = parse_analog_four_saved_kit_export_args(
        [
            "--source",
            str(SOURCE_FIXTURE),
            "--output",
            str(output),
            "--filter2-resonance",
            "1:16",
            "--filter2-resonance",
            "2:48",
            "--filter2-resonance",
            "3:80",
            "--filter2-resonance",
            "4:112",
            "--overwrite",
        ]
    )

    exit_code = handle_analog_four_saved_kit_export(**options)

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.err == ""
    assert "overwrote_existing: true" in captured.out
    assert "mutation: T1 Filter2 Resonance=16 @ unpacked[140]" in captured.out
    assert "mutation: T4 Filter2 Resonance=112 @ unpacked[1190]" in captured.out


@pytest.mark.parametrize(
    ("args", "message"),
    [
        ([], "--source is required"),
        (["--source", "in.syx"], "--output is required"),
        (["--source", "in.syx", "--output", "out.syx"], "at least one"),
        (["--source"], "--source requires a value"),
        (["--unknown"], "unknown option"),
    ],
)
def test_parser_rejects_missing_or_unknown_options(args: list[str], message: str) -> None:
    from rytm_randomizer.cockpit.export.analog_four_cli import (
        parse_analog_four_saved_kit_export_args,
    )

    with pytest.raises(ValueError, match=message):
        parse_analog_four_saved_kit_export_args(args)


@pytest.mark.parametrize(
    ("assignment", "message"),
    [
        ("1", "TRACK:VALUE"),
        (":1", "TRACK:VALUE"),
        ("1:", "TRACK:VALUE"),
        ("x:1", "decimal integers"),
        ("1:x", "decimal integers"),
        ("01:1", "track must"),
        ("0:1", "track must"),
        ("5:1", "track must"),
        ("1:01", "value must"),
        ("1:-1", "value must"),
        ("1:128", "value must"),
    ],
)
def test_parser_rejects_invalid_resonance_assignment(assignment: str, message: str) -> None:
    from rytm_randomizer.cockpit.export.analog_four_cli import (
        parse_analog_four_saved_kit_export_args,
    )

    with pytest.raises(ValueError, match=message):
        parse_analog_four_saved_kit_export_args(
            [
                "--source",
                "in.syx",
                "--output",
                "out.syx",
                "--filter2-resonance",
                assignment,
            ]
        )


def test_registered_cli_formats_parse_error(
    capsys: pytest.CaptureFixture[str],
) -> None:
    from rytm_randomizer.cli import main

    exit_code = main(["analog-four-saved-kit-export", "--unknown"])

    captured = capsys.readouterr()
    assert exit_code == 2
    assert captured.out == ""
    assert "analog-four-saved-kit-export" in captured.err
    assert "unknown option" in captured.err


def test_registered_cli_formats_json_parse_error(
    capsys: pytest.CaptureFixture[str],
) -> None:
    from rytm_randomizer.cli import main

    exit_code = main(["analog-four-saved-kit-export", "--json"])

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 2
    assert payload == {
        "error": "--source is required",
        "error_code": "invalid_input",
        "ok": False,
    }
    assert captured.err == ""


@pytest.mark.parametrize("json_output", [False, True])
def test_handler_reports_missing_source_file(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    json_output: bool,
) -> None:
    from rytm_randomizer.cockpit.export.analog_four_cli import (
        FILTER2_RESONANCE_PARAMETER,
        handle_analog_four_saved_kit_export,
    )
    from rytm_randomizer.devices.strategies import AnalogFourSavedKitMutation

    exit_code = handle_analog_four_saved_kit_export(
        source_path=tmp_path / "missing.syx",
        output_path=tmp_path / "output.syx",
        mutations=(
            AnalogFourSavedKitMutation(
                parameter=FILTER2_RESONANCE_PARAMETER,
                track=1,
                screen_value="64",
            ),
        ),
        json_output=json_output,
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    if json_output:
        payload = json.loads(captured.out)
        assert payload["ok"] is False
        assert payload["error_code"] == "input_not_found"
        assert captured.err == ""
    else:
        assert captured.out == ""
        assert "Error [input_not_found]:" in captured.err


@pytest.mark.parametrize("json_output", [False, True])
def test_handler_reports_operator_interrupt(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    json_output: bool,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.cockpit.export import analog_four_cli as cli

    monkeypatch.setattr(
        cli,
        "export_analog_four_saved_kit",
        lambda **_kwargs: (_ for _ in ()).throw(KeyboardInterrupt("operator cancelled")),
    )

    exit_code = cli.handle_analog_four_saved_kit_export(
        source_path=tmp_path / "source.syx",
        output_path=tmp_path / "output.syx",
        mutations=(),
        json_output=json_output,
    )

    captured = capsys.readouterr()
    assert exit_code == 130
    if json_output:
        payload = json.loads(captured.out)
        assert payload["error_code"] == "interrupted"
        assert payload["ok"] is False
        assert captured.err == ""
    else:
        assert captured.out == ""
        assert "Error [interrupted]" in captured.err


@pytest.mark.parametrize(
    ("error", "error_code"),
    [
        (FileNotFoundError("missing"), "input_not_found"),
        (PermissionError("denied"), "permission_denied"),
        (FileExistsError("exists"), "overwrite_refused"),
        (OSError("disk"), "write_failed"),
        (ValueError("bad value"), "validation"),
    ],
)
def test_saved_kit_cli_error_codes_are_bounded(error: Exception, error_code: str) -> None:
    from rytm_randomizer.cockpit.export import analog_four_cli as cli

    assert cli._saved_kit_cli_error_code(error) == error_code


@pytest.mark.parametrize(
    ("error", "phase", "error_code"),
    [
        (FileNotFoundError("missing"), "source_read", "input_not_found"),
        (PermissionError("denied"), "source_read", "permission_denied"),
        (FileExistsError("exists"), "output_write", "overwrite_refused"),
        (OSError("read"), "source_read", "source_read_failed"),
        (OSError("write"), "output_write", "write_failed"),
        (ValueError("invalid"), "validation", "validation"),
    ],
)
def test_saved_kit_service_error_codes_cover_each_file_phase(
    error: KeyError | ValueError | TypeError | OSError,
    phase: LocalFileExportPhase,
    error_code: str,
) -> None:
    assert (
        classify_local_file_export_error(
            error,
            phase=phase,
        )
        == error_code
    )


def test_saved_kit_service_attaches_output_phase_collision_code(tmp_path: Path) -> None:
    from rytm_randomizer.cockpit.export.analog_four_cli import (
        FILTER2_RESONANCE_PARAMETER,
    )
    from rytm_randomizer.cockpit.export.analog_four_export_contracts import (
        analog_four_export_error_code,
    )
    from rytm_randomizer.cockpit.export.analog_four_kit import export_analog_four_saved_kit
    from rytm_randomizer.devices.strategies import AnalogFourSavedKitMutation

    output = tmp_path / "existing.syx"
    output.write_bytes(b"preserve")

    with pytest.raises(FileExistsError) as raised:
        export_analog_four_saved_kit(
            source_path=SOURCE_FIXTURE,
            output_path=output,
            mutations=(
                AnalogFourSavedKitMutation(
                    parameter=FILTER2_RESONANCE_PARAMETER,
                    track=1,
                    screen_value="64",
                ),
            ),
        )

    assert analog_four_export_error_code(raised.value) == "overwrite_refused"
    assert output.read_bytes() == b"preserve"


def test_saved_kit_service_rejects_invalid_and_unvalidated_mutations(tmp_path: Path) -> None:
    from rytm_randomizer.cockpit.export.analog_four_kit import export_analog_four_saved_kit
    from rytm_randomizer.devices.strategies import AnalogFourSavedKitMutation

    with pytest.raises(TypeError, match="AnalogFourSavedKitMutation"):
        export_analog_four_saved_kit(
            source_path=SOURCE_FIXTURE,
            output_path=tmp_path / "invalid.syx",
            mutations=(object(),),  # type: ignore[arg-type]
        )

    with pytest.raises(ValueError, match="not hardware-write-validated"):
        export_analog_four_saved_kit(
            source_path=SOURCE_FIXTURE,
            output_path=tmp_path / "unvalidated.syx",
            mutations=(
                AnalogFourSavedKitMutation(
                    parameter="Filter1 Frequency",
                    track=1,
                    screen_value="64.00",
                ),
            ),
        )
