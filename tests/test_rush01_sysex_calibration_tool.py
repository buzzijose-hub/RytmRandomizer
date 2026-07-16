"""Passive artifact-tool tests for the RUSH01 SysEx calibration phase."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest

from rytm_randomizer.devices.strategies import ANALOG_FOUR_KIT_CODEC, ANALOG_RYTM_KIT_CODEC
from rytm_randomizer.snapshot import encode_elektron_u14, pack_elektron_7bit
from tools import rush01_sysex_calibration as tool

pytestmark = pytest.mark.fast

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _synthetic_frame(codec: object) -> bytes:
    spec = codec.spec
    unpacked = bytearray(spec.unpacked_size)
    unpacked[: len(spec.required_unpacked_prefix)] = spec.required_unpacked_prefix
    packed = pack_elektron_7bit(bytes(unpacked))
    header = spec.required_header_prefix.ljust(spec.header_size_without_f0, b"\x00")
    checksum = sum(packed[spec.checksum_packed_start :]) & 0x3FFF
    encoded_length = len(packed) + spec.length_adjustment
    return (
        b"\xf0"
        + header
        + packed
        + encode_elektron_u14(checksum)
        + encode_elektron_u14(encoded_length)
        + b"\xf7"
    )


def _copy_inputs(destination: Path, *, include_references: bool = True) -> None:
    for relative in (
        "specs/RUSH01_RYTM.yaml",
        "specs/RUSH01_A4.yaml",
        "output/RUSH01_mapping_gaps.md",
    ):
        source = PROJECT_ROOT / relative
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    if include_references:
        reference_dir = destination / "reference"
        reference_dir.mkdir(parents=True, exist_ok=True)
        (reference_dir / "RYTM_Test1_Init_Kit.syx").write_bytes(
            _synthetic_frame(ANALOG_RYTM_KIT_CODEC)
        )
        (reference_dir / "A4_Test1_Init_Kit.syx").write_bytes(
            _synthetic_frame(ANALOG_FOUR_KIT_CODEC)
        )


def test_tool_generates_and_checks_deterministic_artifacts_without_midi(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _copy_inputs(tmp_path)
    capture = tmp_path / "calibration" / "sysex" / "rytm" / "unplanned.syx"
    capture.parent.mkdir(parents=True)
    shutil.copyfile(tmp_path / "reference" / "RYTM_Test1_Init_Kit.syx", capture)
    imported_before = set(sys.modules)

    assert tool.run(project_root=tmp_path) == 0
    first = {
        path.relative_to(tmp_path).as_posix(): path.read_bytes()
        for path in sorted((tmp_path / "output").glob("RUSH01_*calibration*"))
    }
    first.update(
        {
            path.relative_to(tmp_path).as_posix(): path.read_bytes()
            for path in sorted((tmp_path / "output").glob("RUSH01_*capture_matrix.md"))
        }
    )
    first.update(
        {
            path.relative_to(tmp_path).as_posix(): path.read_bytes()
            for path in sorted((tmp_path / "output").glob("RUSH01_*mapping_status.json"))
        }
    )
    assert len(first) == 5
    assert tool.run(project_root=tmp_path, check=True) == 0
    assert tool.run(project_root=tmp_path) == 0
    second = {name: (tmp_path / name).read_bytes() for name in first}

    output = capsys.readouterr().out
    assert first == second
    assert "MIDI backend opened: false" in output
    assert "MIDI port opened: false" in output
    assert "MIDI data transmitted: false" in output
    assert "final SysEx generated: false" in output
    assert "mido" not in set(sys.modules) - imported_before
    assert "rtmidi" not in set(sys.modules) - imported_before
    assert not (tmp_path / "output" / "RUSH01_RYTM.syx").exists()
    assert not (tmp_path / "output" / "RUSH01_A4.syx").exists()


def test_tool_check_reports_stale_artifact_and_missing_inputs(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _copy_inputs(tmp_path)
    assert tool.run(project_root=tmp_path) == 0
    status_path = tmp_path / "output" / "RUSH01_RYTM_mapping_status.json"
    status_path.write_text("stale\n", encoding="utf-8")

    assert tool.run(project_root=tmp_path, check=True) == 1
    assert "RUSH01_RYTM_mapping_status.json" in capsys.readouterr().err
    assert tool.run(project_root=tmp_path / "missing") == 2
    assert "required local reference dump(s) are missing" in capsys.readouterr().err


def test_tool_check_without_private_references_reports_read_only_status(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _copy_inputs(tmp_path, include_references=False)
    imported_before = set(sys.modules)

    assert tool.run(project_root=tmp_path, check=True) == 0

    output = capsys.readouterr().out
    assert "check status: missing-local-references" in output
    assert "reference/RYTM_Test1_Init_Kit.syx" in output
    assert "reference/A4_Test1_Init_Kit.syx" in output
    assert "No files were written." in output
    assert "MIDI backend opened: false" in output
    assert "mido" not in set(sys.modules) - imported_before
    assert "rtmidi" not in set(sys.modules) - imported_before
    assert not (tmp_path / "output" / "RUSH01_RYTM_mapping_status.json").exists()


def test_tool_rejects_capture_path_that_is_not_a_directory(tmp_path: Path) -> None:
    _copy_inputs(tmp_path)
    capture_path = tmp_path / "calibration" / "sysex" / "rytm"
    capture_path.parent.mkdir(parents=True)
    capture_path.write_text("not a directory", encoding="utf-8")

    assert tool.run(project_root=tmp_path) == 2


def test_read_bytes_rejects_a_missing_file(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="required file does not exist"):
        tool._read_bytes(tmp_path / "missing.syx")


def test_read_text_rejects_a_missing_file(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="required file does not exist"):
        tool._read_text(tmp_path / "missing.yaml")


def test_tool_main_resolves_project_root_and_check_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    observed: list[tuple[Path, bool]] = []

    def fake_run(*, project_root: Path, check: bool) -> int:
        observed.append((project_root, check))
        return 7

    monkeypatch.setattr(tool, "run", fake_run)

    assert tool.main(["--project-root", ".", "--check"]) == 7
    assert observed == [(Path.cwd().resolve(), True)]
