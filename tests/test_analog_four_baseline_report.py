"""Tests for passive Analog Four initialized-baseline reports."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import elektron_syx_message, pack_elektron_7bit

pytestmark = pytest.mark.fast

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _saved_kit_frame(name: bytes, *, marker: int = 0) -> bytes:
    from rytm_randomizer.devices.strategies.analog_four_offset_manifest import (
        A4_FAMILY_BYTE,
        A4_KIT_NAME_LENGTH,
        A4_KIT_NAME_OFFSET,
        A4_KIT_OBJECT_BYTE,
    )
    from rytm_randomizer.snapshot.envelope import ELEKTRON_MFR_ID

    unpacked = bytearray(A4_KIT_NAME_OFFSET + A4_KIT_NAME_LENGTH + 24)
    unpacked[0] = A4_KIT_OBJECT_BYTE
    unpacked[1] = 0x01
    unpacked[2] = 0x01
    unpacked[A4_KIT_NAME_OFFSET : A4_KIT_NAME_OFFSET + A4_KIT_NAME_LENGTH] = name[
        :A4_KIT_NAME_LENGTH
    ].ljust(A4_KIT_NAME_LENGTH, b"\x00")
    unpacked[-1] = marker
    payload = ELEKTRON_MFR_ID + bytes([A4_FAMILY_BYTE]) + pack_elektron_7bit(bytes(unpacked))
    return elektron_syx_message(payload)


def _unsupported_pattern_frame() -> bytes:
    from rytm_randomizer.devices.strategies.analog_four_offset_manifest import A4_FAMILY_BYTE
    from rytm_randomizer.snapshot.envelope import ELEKTRON_MFR_ID

    unpacked = bytearray(24)
    unpacked[0] = 0x54
    unpacked[1] = 0x01
    return elektron_syx_message(
        ELEKTRON_MFR_ID + bytes([A4_FAMILY_BYTE]) + pack_elektron_7bit(bytes(unpacked))
    )


def _write_baseline_files(tmp_path: Path, *, kit_marker: int = 7) -> tuple[Path, Path, Path]:
    kit_path = tmp_path / "A4_Test1_Init_Kit.syx"
    pattern_kit_path = tmp_path / "A4_Test1_Init_A01_PatternKit.syx"
    whole_project_path = tmp_path / "A4_Test1_Init_WholeProject.syx"
    init_kit = _saved_kit_frame(b"INIT", marker=kit_marker)
    kit_path.write_bytes(init_kit)
    pattern_kit_path.write_bytes(_unsupported_pattern_frame() + init_kit)
    whole_project_path.write_bytes(
        init_kit
        + _saved_kit_frame(b"INIT 2", marker=kit_marker + 1)
        + _saved_kit_frame(b"INIT 3", marker=kit_marker + 2)
    )
    return kit_path, pattern_kit_path, whole_project_path


def test_importing_analog_four_baseline_report_prints_nothing() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import rytm_randomizer.reports.analog_four_baseline",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_baseline_report_confirms_matching_initialized_kit_across_sources(tmp_path: Path) -> None:
    from rytm_randomizer.reports.analog_four_baseline import (
        build_analog_four_baseline_report,
        format_analog_four_baseline_report,
        to_analog_four_baseline_json,
    )

    kit_path, pattern_kit_path, whole_project_path = _write_baseline_files(tmp_path)

    report = build_analog_four_baseline_report(
        kit_path=kit_path,
        pattern_kit_path=pattern_kit_path,
        whole_project_path=whole_project_path,
    )
    payload = to_analog_four_baseline_json(report)
    text = "\n".join(format_analog_four_baseline_report(report))

    assert report.baseline_status == "coherent-init-baseline"
    assert report.baseline_fingerprint == report.kit_source.baseline_fingerprint
    assert report.baseline_fingerprint == report.pattern_kit_source.baseline_fingerprint
    assert report.baseline_fingerprint == report.whole_project_source.baseline_fingerprint
    assert report.kit_source.frame_count == 1
    assert report.pattern_kit_source.frame_count == 2
    assert report.pattern_kit_source.unsupported_frame_count == 1
    assert report.whole_project_source.saved_kit_count == 3
    assert report.mismatch_reasons == ()
    assert payload["baseline_status"] == "coherent-init-baseline"
    assert payload["ready_for_changed_patch_diff"] is True
    assert payload["sources"]["kit"]["sha256"]
    assert text.startswith("RytmRandomizer passive Analog Four initialized baseline\n")
    assert "Baseline status: coherent-init-baseline" in text
    assert f"Baseline fingerprint: {report.baseline_fingerprint}" in text
    assert "Ready for changed-patch diff: True" in text
    assert "Offset status: candidate-only" in text
    assert "- no MIDI sending" in text
    assert "- no port opening" in text


def test_baseline_report_flags_fingerprint_mismatch_between_sources(tmp_path: Path) -> None:
    from rytm_randomizer.reports.analog_four_baseline import (
        build_analog_four_baseline_report,
        format_analog_four_baseline_report,
    )

    kit_path, pattern_kit_path, whole_project_path = _write_baseline_files(tmp_path)
    pattern_kit_path.write_bytes(
        _unsupported_pattern_frame() + _saved_kit_frame(b"INIT", marker=44)
    )

    report = build_analog_four_baseline_report(
        kit_path=kit_path,
        pattern_kit_path=pattern_kit_path,
        whole_project_path=whole_project_path,
    )
    text = "\n".join(format_analog_four_baseline_report(report))

    assert report.baseline_status == "baseline-mismatch"
    assert report.ready_for_changed_patch_diff is False
    assert report.baseline_fingerprint is None
    assert report.mismatch_reasons == (
        "kit, pattern+kit, and whole-project baseline fingerprints do not match",
    )
    assert "Baseline status: baseline-mismatch" in text
    assert "- kit, pattern+kit, and whole-project baseline fingerprints do not match" in text


def test_baseline_report_flags_missing_supported_kits(tmp_path: Path) -> None:
    from rytm_randomizer.reports.analog_four_baseline import build_analog_four_baseline_report

    kit_path = tmp_path / "kit.syx"
    pattern_kit_path = tmp_path / "pattern-kit.syx"
    whole_project_path = tmp_path / "whole-project.syx"
    kit_path.write_bytes(_unsupported_pattern_frame())
    pattern_kit_path.write_bytes(_unsupported_pattern_frame())
    whole_project_path.write_bytes(_unsupported_pattern_frame())

    report = build_analog_four_baseline_report(
        kit_path=kit_path,
        pattern_kit_path=pattern_kit_path,
        whole_project_path=whole_project_path,
    )

    assert report.baseline_status == "incomplete-baseline"
    assert report.ready_for_changed_patch_diff is False
    assert report.baseline_fingerprint is None
    assert report.mismatch_reasons == (
        "kit source has no decoded Analog Four saved kit",
        "pattern+kit source has no decoded Analog Four saved kit",
        "whole-project source has no decoded Analog Four saved kit",
    )


def test_baseline_cli_parser_accepts_required_sources() -> None:
    from rytm_randomizer.reports.analog_four_baseline import (
        _parse_analog_four_baseline_cli_args,
    )

    assert _parse_analog_four_baseline_cli_args(
        [
            "--kit",
            "kit.syx",
            "--pattern-kit",
            "pattern-kit.syx",
            "--whole-project",
            "project.syx",
            "--json",
        ]
    ) == {
        "kit_path": Path("kit.syx"),
        "pattern_kit_path": Path("pattern-kit.syx"),
        "whole_project_path": Path("project.syx"),
        "json_output": True,
    }


@pytest.mark.parametrize(
    ("argv", "message"),
    [
        ([], "usage"),
        (["--kit", "kit.syx"], "usage"),
        (["--kit"], "usage"),
        (["--unknown", "x"], "usage"),
        (
            [
                "--kit",
                "same.syx",
                "--pattern-kit",
                "same.syx",
                "--whole-project",
                "project.syx",
            ],
            "must be distinct",
        ),
    ],
)
def test_baseline_cli_parser_rejects_bad_args(argv: list[str], message: str) -> None:
    from rytm_randomizer.reports.analog_four_baseline import (
        _parse_analog_four_baseline_cli_args,
    )

    with pytest.raises(ValueError, match=message):
        _parse_analog_four_baseline_cli_args(argv)


def test_baseline_cli_handler_reports_json(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from rytm_randomizer.reports.analog_four_baseline import (
        _handle_analog_four_baseline_cli_report,
    )

    kit_path, pattern_kit_path, whole_project_path = _write_baseline_files(tmp_path)

    rc = _handle_analog_four_baseline_cli_report(
        kit_path=kit_path,
        pattern_kit_path=pattern_kit_path,
        whole_project_path=whole_project_path,
        json_output=True,
    )

    captured = capsys.readouterr()
    parsed = json.loads(captured.out)
    assert rc == 0
    assert parsed["baseline_status"] == "coherent-init-baseline"
    assert parsed["ready_for_changed_patch_diff"] is True
    assert captured.err == ""


def test_baseline_cli_handler_reports_text(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from rytm_randomizer.reports.analog_four_baseline import (
        _handle_analog_four_baseline_cli_report,
    )

    kit_path, pattern_kit_path, whole_project_path = _write_baseline_files(tmp_path)

    rc = _handle_analog_four_baseline_cli_report(
        kit_path=kit_path,
        pattern_kit_path=pattern_kit_path,
        whole_project_path=whole_project_path,
        json_output=False,
    )

    captured = capsys.readouterr()
    assert rc == 0
    assert "RytmRandomizer passive Analog Four initialized baseline" in captured.out
    assert "Baseline status: coherent-init-baseline" in captured.out
    assert "Ready for changed-patch diff: True" in captured.out
    assert captured.err == ""


def test_baseline_cli_handler_reports_errors(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from rytm_randomizer.reports.analog_four_baseline import (
        _handle_analog_four_baseline_cli_report,
    )

    rc = _handle_analog_four_baseline_cli_report(
        kit_path=tmp_path / "missing-kit.syx",
        pattern_kit_path=tmp_path / "missing-pattern-kit.syx",
        whole_project_path=tmp_path / "missing-project.syx",
        json_output=False,
    )

    captured = capsys.readouterr()
    assert rc == 2
    assert captured.out == ""
    assert "SysEx file does not exist" in captured.err
    assert "Traceback" not in captured.err


def test_baseline_cli_handler_rejects_directory_paths(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from rytm_randomizer.reports.analog_four_baseline import (
        _handle_analog_four_baseline_cli_report,
    )

    kit_path, pattern_kit_path, whole_project_path = _write_baseline_files(tmp_path)

    rc = _handle_analog_four_baseline_cli_report(
        kit_path=tmp_path,
        pattern_kit_path=pattern_kit_path,
        whole_project_path=whole_project_path,
        json_output=False,
    )

    captured = capsys.readouterr()
    assert rc == 2
    assert captured.out == ""
    assert "SysEx path is not a file" in captured.err
    assert str(kit_path.parent) in captured.err


def test_baseline_read_file_bytes_wraps_oserror(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.reports.analog_four_baseline import _read_file_bytes

    path = tmp_path / "locked.syx"
    path.write_bytes(_saved_kit_frame(b"LOCKED"))

    def _raise_oserror(_path: Path) -> bytes:
        raise OSError("locked by another process")

    monkeypatch.setattr(Path, "read_bytes", _raise_oserror)

    with pytest.raises(ValueError, match="Could not read SysEx file"):
        _read_file_bytes(path)


def test_baseline_cli_error_formatter_is_plain_error() -> None:
    from rytm_randomizer.reports.analog_four_baseline import (
        _format_analog_four_baseline_cli_error,
    )

    assert _format_analog_four_baseline_cli_error(ValueError("bad baseline")) == (
        "Error: bad baseline"
    )
