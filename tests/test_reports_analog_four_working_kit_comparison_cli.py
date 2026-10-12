"""Strict passive CLI, privacy and exact file-comparison integration tests."""

from __future__ import annotations

import json
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from conftest import analog_four_saved_kit_frame
from rytm_randomizer import cli, cli_registry
from rytm_randomizer.reports import analog_four_working_kit_comparison_cli as adapter

pytestmark = pytest.mark.fast


def _argv(root: Path, *, track: int = 1) -> list[str]:
    offset = (128, 478, 828, 1178)[track - 1]
    baseline = analog_four_saved_kit_frame(unpacked_overrides={offset + 1: 1})
    working = bytearray(analog_four_saved_kit_frame(unpacked_overrides={offset + 1: 2}))
    working[6] = 88
    saved = analog_four_saved_kit_frame(unpacked_overrides={offset + 1: 2})
    flags = (
        "--manual-baseline",
        "--indexed-baseline",
        "--working-first",
        "--working-repeat",
        "--post-save",
        "--recovered",
    )
    argv: list[str] = []
    for index, (flag, raw) in enumerate(
        zip(
            flags,
            (baseline, baseline, bytes(working), bytes(working), saved, baseline),
            strict=True,
        )
    ):
        path = root / f"PRIVATE-stage-{index}.syx"
        path.write_bytes(raw)
        argv.extend((flag, str(path)))
    argv.extend(("--track", str(track), "--evidence-origin", "synthetic"))
    return argv


def _replace_value(argv: list[str], flag: str, value: str) -> list[str]:
    changed = list(argv)
    changed[changed.index(flag) + 1] = value
    return changed


def test_command_registers_exact_attribute_and_frozen_arguments(tmp_path: Path) -> None:
    command = adapter.ANALOG_FOUR_WORKING_KIT_COMPARISON_CLI_COMMAND
    assert command.name == "a4-working-kit-compare"
    assert cli_registry.get("a4-working-kit-compare") is command
    assert "post-edit indexed B" in command.summary
    assert "post-unsaved-edit, pre-SAVE queried 0x52" in adapter.USAGE
    assert "not verified by files" in adapter.USAGE
    parsed = command.args_parser(_argv(tmp_path))
    assert set(parsed) == {"arguments"}
    assert isinstance(parsed["arguments"], adapter.AnalogFourWorkingKitComparisonCliArguments)
    assert parsed["arguments"].track == 1
    assert parsed["arguments"].evidence_origin.value == "synthetic"
    assert parsed["arguments"].baseline_label is None
    with pytest.raises(FrozenInstanceError):
        parsed["arguments"].__setattr__("track", 2)


@pytest.mark.parametrize("track", [1, 2, 3, 4])
def test_cli_real_report_outputs_json_only_without_writing_or_inverse_labels(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], track: int
) -> None:
    argv = _argv(tmp_path, track=track) + ["--baseline-label", "0.00", "--changed-label", "0.00"]
    before = {path: path.read_bytes() for path in tmp_path.iterdir()}
    assert cli.main(["a4-working-kit-compare", *argv]) == 0
    output = capsys.readouterr()
    assert output.err == ""
    data = json.loads(output.out)
    assert data["track"] == track
    assert data["checks"]["selected_b_differs_from_u"] is True
    assert data["checks"]["baseline_label_matches"] is True
    assert data["checks"]["changed_label_matches"] is True
    assert data["frames"][0]["f1"][track - 1]["native"] == 1
    assert data["frames"][2]["f1"][track - 1]["native"] == 2
    assert data["query_authority"] is data["send_authority"] is data["restore_authority"] is False
    assert "PRIVATE-stage" not in output.out
    assert {path: path.read_bytes() for path in tmp_path.iterdir()} == before


def test_optional_labels_and_operator_origin_are_passed_forward(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    argv = _replace_value(_argv(tmp_path), "--evidence-origin", "operator_supplied_files")
    assert cli.main(["a4-working-kit-compare", *argv]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["evidence_origin"] == "operator_supplied_files"
    assert (
        data["checks"]["baseline_label_matches"] is data["checks"]["changed_label_matches"] is None
    )
    assert data["hardware_validated"] is False


@pytest.mark.parametrize(
    "flag",
    [
        "--manual-baseline",
        "--indexed-baseline",
        "--working-first",
        "--working-repeat",
        "--post-save",
        "--recovered",
        "--track",
        "--evidence-origin",
    ],
)
def test_every_required_flag_is_mandatory_and_errors_are_private(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], flag: str
) -> None:
    argv = _argv(tmp_path)
    position = argv.index(flag)
    del argv[position : position + 2]
    assert cli.main(["a4-working-kit-compare", *argv]) == 2
    output = capsys.readouterr()
    assert output.out == ""
    assert output.err == "Error: invalid a4-working-kit-compare arguments.\n"
    assert str(tmp_path) not in output.err


@pytest.mark.parametrize(
    "flag",
    [
        "--manual-baseline",
        "--indexed-baseline",
        "--working-first",
        "--working-repeat",
        "--post-save",
        "--recovered",
        "--track",
        "--evidence-origin",
        "--baseline-label",
        "--changed-label",
    ],
)
def test_duplicate_flags_are_refused_including_optional_labels(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], flag: str
) -> None:
    argv = _argv(tmp_path) + [
        "--baseline-label",
        "0.00",
        "--changed-label",
        "0.00",
        flag,
        "PRIVATE-value",
    ]
    assert cli.main(["a4-working-kit-compare", *argv]) == 2
    output = capsys.readouterr()
    assert output.out == ""
    assert output.err == "Error: invalid a4-working-kit-compare arguments.\n"


@pytest.mark.parametrize(
    "tail",
    [
        ["--PRIVATE-unknown", "secret"],
        ["PRIVATE-positional"],
        ["--json"],
        ["--output", "PRIVATE-destination"],
        ["--track=1"],
        ["--baseline-label"],
        ["--changed-label", "--PRIVATE-unknown"],
        ["--baseline-label", ""],
        ["--baseline-label", " "],
    ],
)
def test_unknown_positional_equals_missing_or_empty_option_values_fail_closed(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], tail: list[str]
) -> None:
    assert cli.main(["a4-working-kit-compare", *_argv(tmp_path), *tail]) == 2
    output = capsys.readouterr()
    assert output.out == ""
    assert output.err == "Error: invalid a4-working-kit-compare arguments.\n"


@pytest.mark.parametrize("track", ["0", "5", "-1", "01", "1.0", "True", "PRIVATE-track"])
def test_track_requires_literal_ordinary_track_1_to_4(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], track: str
) -> None:
    assert (
        cli.main(["a4-working-kit-compare", *_replace_value(_argv(tmp_path), "--track", track)])
        == 2
    )
    assert capsys.readouterr().err == "Error: invalid a4-working-kit-compare arguments.\n"


@pytest.mark.parametrize("origin", ["unknown", "physical_validated", "PRIVATE-origin"])
def test_unknown_origin_is_refused_without_echoing_supplied_value(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], origin: str
) -> None:
    assert (
        cli.main(
            [
                "a4-working-kit-compare",
                *_replace_value(_argv(tmp_path), "--evidence-origin", origin),
            ]
        )
        == 2
    )
    assert capsys.readouterr().err == "Error: invalid a4-working-kit-compare arguments.\n"


def test_missing_source_and_invalid_frame_return_private_status2_and_preserve_sources(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    argv = _argv(tmp_path)
    before = {path: path.read_bytes() for path in tmp_path.iterdir()}
    missing = str(tmp_path / "PRIVATE-missing.syx")
    assert (
        cli.main(["a4-working-kit-compare", *_replace_value(argv, "--working-first", missing)]) == 2
    )
    output = capsys.readouterr()
    assert output.out == ""
    assert output.err == "Error: a4-working-kit-compare input comparison failed.\n"
    invalid = tmp_path / "PRIVATE-invalid.syx"
    invalid.write_bytes(bytes(2770))
    assert (
        cli.main(["a4-working-kit-compare", *_replace_value(argv, "--working-first", str(invalid))])
        == 2
    )
    assert capsys.readouterr().err == "Error: a4-working-kit-compare input comparison failed.\n"
    assert {path: path.read_bytes() for path in before} == before
    assert invalid.read_bytes() == bytes(2770)


def test_empty_invocation_is_private_status2(capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.main(["a4-working-kit-compare"]) == 2
    assert capsys.readouterr().err == "Error: invalid a4-working-kit-compare arguments.\n"


@pytest.mark.parametrize(
    "exception", [ValueError("PRIVATE-source-detail"), OSError("PRIVATE-source-detail")]
)
def test_expected_input_errors_are_fixed_but_never_echo_paths(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    exception: Exception,
) -> None:
    def fail(*args: object, **kwargs: object) -> None:
        raise exception

    monkeypatch.setattr(adapter, "build_analog_four_working_kit_comparison_report", fail)
    assert cli.main(["a4-working-kit-compare", *_argv(tmp_path)]) == 2
    output = capsys.readouterr()
    assert output.out == ""
    assert output.err == "Error: a4-working-kit-compare input comparison failed.\n"


@pytest.mark.parametrize("exception", [RuntimeError("logic failure"), TypeError("logic failure")])
def test_unexpected_production_logic_errors_are_not_swallowed(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    exception: Exception,
) -> None:
    def fail(*args: object, **kwargs: object) -> None:
        raise exception

    monkeypatch.setattr(adapter, "build_analog_four_working_kit_comparison_report", fail)
    with pytest.raises(type(exception), match="logic failure"):
        cli.main(["a4-working-kit-compare", *_argv(tmp_path)])
    assert capsys.readouterr().out == ""


def test_serializer_logic_errors_are_not_misreported_as_bad_input(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail(report: object) -> str:
        raise ValueError("serializer logic failure")

    monkeypatch.setattr(adapter, "to_analog_four_working_kit_comparison_json", fail)
    with pytest.raises(ValueError, match="serializer logic failure"):
        cli.main(["a4-working-kit-compare", *_argv(tmp_path)])
