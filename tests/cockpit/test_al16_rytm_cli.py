"""Operator-path tests for passive AL16 Analog Rytm kit export."""

from __future__ import annotations

from pathlib import Path

import pytest

from rytm_randomizer.cockpit.export.al16_rytm_kit import (
    Al16BuildResult,
    MappingGap,
)

pytestmark = pytest.mark.fast


def _result(tmp_path: Path, *, status: str) -> Al16BuildResult:
    return Al16BuildResult(
        status=status,
        output_path=tmp_path / "AL02_LOCK_RYTM.syx",
        manifest_path=tmp_path / "AL02_LOCK_RYTM_manifest.json",
        validation_path=tmp_path / "AL02_LOCK_RYTM_validation.md",
        byte_diff_path=tmp_path / "AL02_LOCK_RYTM_byte_diff.txt",
        reference_sha256="reference-sha",
        output_sha256="output-sha" if status == "built" else None,
        gaps=(
            (
                MappingGap(
                    semantic_path="tracks.1.machine",
                    pad=1,
                    machine="bd_classic",
                    expected_behavior="select BD Classic",
                    reason="writer evidence missing",
                    evidence_required="saved-kit writer observation",
                ),
            )
            if status == "blocked"
            else ()
        ),
    )


def test_registered_cli_help_describes_passive_safety(
    capsys: pytest.CaptureFixture[str],
) -> None:
    from rytm_randomizer.cli import main

    assert main(["al16-rytm-kit-export", "--help"]) == 0

    captured = capsys.readouterr()
    assert captured.err == ""
    assert "--destination-slot <0..127>" in captured.out
    assert "no MIDI backend imports" in captured.out
    assert "no MIDI port enumeration or opening" in captured.out


def test_registered_cli_reports_blocked_evidence(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.cli import main
    from rytm_randomizer.cockpit.export import al16_rytm_cli as cli

    monkeypatch.setattr(
        cli, "build_al16_rytm_kit", lambda **_kwargs: _result(tmp_path, status="blocked")
    )

    exit_code = main(
        [
            "al16-rytm-kit-export",
            "--reference",
            "reference.syx",
            "--recipe",
            "recipe.yaml",
            "--destination-slot",
            "127",
            "--output",
            "output.syx",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    assert captured.err == ""
    assert "build_status: blocked" in captured.out
    assert "output_emitted: false" in captured.out
    assert "mapping_gap: tracks.1.machine: writer evidence missing" in captured.out


def test_handler_returns_success_for_future_verified_build(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.cockpit.export import al16_rytm_cli as cli

    monkeypatch.setattr(
        cli, "build_al16_rytm_kit", lambda **_kwargs: _result(tmp_path, status="built")
    )

    exit_code = cli.handle_al16_rytm_kit_export(
        reference_path=Path("reference.syx"),
        recipe_path=Path("recipe.yaml"),
        destination_slot=127,
        output_path=Path("output.syx"),
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.err == ""
    assert "build_status: built" in captured.out
    assert "output_emitted: true" in captured.out
    assert "output_sha256: output-sha" in captured.out


@pytest.mark.parametrize(
    ("args", "message"),
    [
        ([], "--reference is required"),
        (["--reference", "reference.syx"], "--recipe is required"),
        (
            ["--reference", "reference.syx", "--recipe", "recipe.yaml"],
            "--destination-slot is required",
        ),
        (
            [
                "--reference",
                "reference.syx",
                "--recipe",
                "recipe.yaml",
                "--destination-slot",
                "127",
            ],
            "--output is required",
        ),
        (["--reference"], "--reference requires a value"),
        (["--unknown"], "unknown option"),
    ],
)
def test_parser_rejects_missing_or_unknown_options(args: list[str], message: str) -> None:
    from rytm_randomizer.cockpit.export.al16_rytm_cli import (
        parse_al16_rytm_kit_export_args,
    )

    with pytest.raises(ValueError, match=message):
        parse_al16_rytm_kit_export_args(args)


@pytest.mark.parametrize("slot", ["x", "01", "+1", "-1", "128"])
def test_parser_rejects_invalid_destination_slots(slot: str) -> None:
    from rytm_randomizer.cockpit.export.al16_rytm_cli import (
        parse_al16_rytm_kit_export_args,
    )

    with pytest.raises(ValueError, match="decimal integer from 0 to 127"):
        parse_al16_rytm_kit_export_args(
            [
                "--reference",
                "reference.syx",
                "--recipe",
                "recipe.yaml",
                "--destination-slot",
                slot,
                "--output",
                "output.syx",
            ]
        )


def test_parser_returns_precise_handler_arguments() -> None:
    from rytm_randomizer.cockpit.export.al16_rytm_cli import (
        parse_al16_rytm_kit_export_args,
    )

    assert parse_al16_rytm_kit_export_args(
        [
            "--reference",
            "reference.syx",
            "--recipe",
            "recipe.yaml",
            "--destination-slot",
            "0",
            "--output",
            "output.syx",
        ]
    ) == {
        "reference_path": Path("reference.syx"),
        "recipe_path": Path("recipe.yaml"),
        "destination_slot": 0,
        "output_path": Path("output.syx"),
    }


def test_registered_cli_formats_parse_error(capsys: pytest.CaptureFixture[str]) -> None:
    from rytm_randomizer.cli import main

    exit_code = main(["al16-rytm-kit-export", "--unknown"])

    captured = capsys.readouterr()
    assert exit_code == 2
    assert captured.out == ""
    assert "al16-rytm-kit-export" in captured.err
    assert "unknown option" in captured.err


@pytest.mark.parametrize(
    ("error", "exit_code", "message"),
    [
        (ValueError("bad recipe"), 2, "Error [offline_build_failed]: bad recipe"),
        (KeyboardInterrupt(), 130, "Error [interrupted]: AL16 kit export interrupted"),
    ],
)
def test_handler_reports_bounded_failures(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    error: BaseException,
    exit_code: int,
    message: str,
) -> None:
    from rytm_randomizer.cockpit.export import al16_rytm_cli as cli

    def raise_error(**_kwargs: object) -> Al16BuildResult:
        raise error

    monkeypatch.setattr(cli, "build_al16_rytm_kit", raise_error)

    actual_exit_code = cli.handle_al16_rytm_kit_export(
        reference_path=tmp_path / "reference.syx",
        recipe_path=tmp_path / "recipe.yaml",
        destination_slot=127,
        output_path=tmp_path / "output.syx",
    )

    captured = capsys.readouterr()
    assert actual_exit_code == exit_code
    assert captured.out == ""
    assert message in captured.err
