"""Operator CLI tests for audio-dependent Analog Four patch batches."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast


@dataclass(frozen=True)
class _CandidateOutput:
    column: int
    label: str
    sysex_path: Path
    sidecar_path: Path
    sysex_applied_count: int
    live_sendable_count: int
    manual_row_count: int
    deferred_count: int


@dataclass(frozen=True)
class _BatchResult:
    source_hash: str
    selected_track: int
    candidate_outputs: tuple[_CandidateOutput, ...]
    safety: tuple[str, ...]


def _batch_result(tmp_path: Path) -> _BatchResult:
    return _BatchResult(
        source_hash="audio-sha256",
        selected_track=2,
        candidate_outputs=(
            _CandidateOutput(
                column=1,
                label="Closest reference",
                sysex_path=tmp_path / "candidate-1.syx",
                sidecar_path=tmp_path / "candidate-1.json",
                sysex_applied_count=1,
                live_sendable_count=34,
                manual_row_count=5,
                deferred_count=38,
            ),
            _CandidateOutput(
                column=2,
                label="Brighter motion",
                sysex_path=tmp_path / "candidate-2.syx",
                sidecar_path=tmp_path / "candidate-2.json",
                sysex_applied_count=1,
                live_sendable_count=33,
                manual_row_count=6,
                deferred_count=38,
            ),
        ),
        safety=(
            "local files only",
            "no MIDI sending",
        ),
    )


def test_parser_uses_safe_single_track_four_candidate_defaults() -> None:
    from rytm_randomizer.cockpit.export.analog_four_patch_batch_cli import (
        parse_analog_four_audio_patch_batch_args,
    )

    options = parse_analog_four_audio_patch_batch_args(
        [
            "--audio",
            "reference.wav",
            "--source-kit",
            "init.syx",
            "--output-dir",
            "batch",
        ]
    )

    assert options == {
        "audio_path": Path("reference.wav"),
        "source_kit_path": Path("init.syx"),
        "output_dir": Path("batch"),
        "track": 1,
        "candidate_count": 4,
        "overwrite": False,
        "json_output": False,
    }


def test_parser_accepts_every_documented_option() -> None:
    from rytm_randomizer.cockpit.export.analog_four_patch_batch_cli import (
        parse_analog_four_audio_patch_batch_args,
    )

    options = parse_analog_four_audio_patch_batch_args(
        [
            "--audio",
            "reference.wav",
            "--source-kit",
            "init.syx",
            "--output-dir",
            "batch",
            "--track",
            "4",
            "--candidates",
            "1",
            "--overwrite",
            "--json",
        ]
    )

    assert options["track"] == 4
    assert options["candidate_count"] == 1
    assert options["overwrite"] is True
    assert options["json_output"] is True


@pytest.mark.parametrize(
    ("args", "message"),
    [
        ([], "--audio is required"),
        (["--audio", "clip.wav"], "--source-kit is required"),
        (
            ["--audio", "clip.wav", "--source-kit", "init.syx"],
            "--output-dir is required",
        ),
        (["--audio"], "--audio requires a value"),
        (["--unknown"], "unknown option"),
        (
            [
                "--audio",
                "clip.wav",
                "--source-kit",
                "init.syx",
                "--output-dir",
                "out",
                "--track",
                "0",
            ],
            "--track must be an integer from 1 to 4",
        ),
        (
            [
                "--audio",
                "clip.wav",
                "--source-kit",
                "init.syx",
                "--output-dir",
                "out",
                "--track",
                "01",
            ],
            "--track must be an integer from 1 to 4",
        ),
        (
            [
                "--audio",
                "clip.wav",
                "--source-kit",
                "init.syx",
                "--output-dir",
                "out",
                "--candidates",
                "5",
            ],
            "--candidates must be an integer from 1 to 4",
        ),
        (
            [
                "--audio",
                "clip.wav",
                "--source-kit",
                "init.syx",
                "--output-dir",
                "out",
                "--candidates",
                "many",
            ],
            "--candidates must be an integer from 1 to 4",
        ),
    ],
)
def test_parser_rejects_invalid_input(args: list[str], message: str) -> None:
    from rytm_randomizer.cockpit.export.analog_four_patch_batch_cli import (
        parse_analog_four_audio_patch_batch_args,
    )

    with pytest.raises(ValueError, match=message):
        parse_analog_four_audio_patch_batch_args(args)


def test_handler_forwards_to_service_and_emits_json_summary(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.cockpit.export import analog_four_patch_batch_cli as cli

    observed: dict[str, object] = {}

    def fake_export(**kwargs: object) -> _BatchResult:
        observed.update(kwargs)
        return _batch_result(tmp_path)

    monkeypatch.setattr(cli, "_export_analog_four_audio_patch_batch", fake_export)

    exit_code = cli.handle_analog_four_audio_patch_batch(
        audio_path=tmp_path / "reference.wav",
        source_kit_path=tmp_path / "init.syx",
        output_dir=tmp_path / "batch",
        track=2,
        candidate_count=2,
        overwrite=True,
        json_output=True,
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert observed == {
        "audio_path": tmp_path / "reference.wav",
        "source_kit_path": tmp_path / "init.syx",
        "output_dir": tmp_path / "batch",
        "track": 2,
        "candidate_count": 2,
        "overwrite": True,
    }
    assert payload == {
        "candidate_count": 2,
        "candidate_outputs": [
            {
                "candidate": 1,
                "deferred_count": 38,
                "label": "Closest reference",
                "live_sendable_count": 34,
                "manual_count": 5,
                "sidecar_path": str(tmp_path / "candidate-1.json"),
                "sysex_applied_count": 1,
                "sysex_path": str(tmp_path / "candidate-1.syx"),
            },
            {
                "candidate": 2,
                "deferred_count": 38,
                "label": "Brighter motion",
                "live_sendable_count": 33,
                "manual_count": 6,
                "sidecar_path": str(tmp_path / "candidate-2.json"),
                "sysex_applied_count": 1,
                "sysex_path": str(tmp_path / "candidate-2.syx"),
            },
        ],
        "counts": {
            "deferred": 76,
            "live_sendable": 67,
            "manual": 11,
            "sysex_applied": 2,
        },
        "ok": True,
        "safety": ["local files only", "no MIDI sending"],
        "selected_track": 2,
        "source_hash": "audio-sha256",
    }


def test_handler_emits_compact_text_summary(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.cockpit.export import analog_four_patch_batch_cli as cli

    monkeypatch.setattr(
        cli,
        "_export_analog_four_audio_patch_batch",
        lambda **_kwargs: _batch_result(tmp_path),
    )

    exit_code = cli.handle_analog_four_audio_patch_batch(
        audio_path=tmp_path / "reference.wav",
        source_kit_path=tmp_path / "init.syx",
        output_dir=tmp_path / "batch",
        track=2,
        candidate_count=2,
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.err == ""
    assert "source_hash: audio-sha256" in captured.out
    assert "candidate_count: 2" in captured.out
    assert "candidate: 1 | Closest reference" in captured.out
    assert "sysex_applied_count: 2" in captured.out
    assert "live_sendable_count: 67" in captured.out
    assert "manual_count: 11" in captured.out
    assert "deferred_count: 76" in captured.out
    assert "- no MIDI sending" in captured.out


@pytest.mark.parametrize(
    ("exc", "error_code"),
    [
        (FileNotFoundError("missing audio"), "input_not_found"),
        (FileExistsError("candidate exists"), "overwrite_refused"),
        (PermissionError("denied"), "permission_denied"),
        (OSError("disk error"), "file_error"),
        (ValueError("unsupported audio"), "invalid_input"),
        (ImportError("service unavailable"), "service_unavailable"),
    ],
)
def test_handler_emits_classified_json_errors(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    exc: Exception,
    error_code: str,
) -> None:
    from rytm_randomizer.cockpit.export import analog_four_patch_batch_cli as cli

    def fail_export(**_kwargs: object) -> _BatchResult:
        raise exc

    monkeypatch.setattr(cli, "_export_analog_four_audio_patch_batch", fail_export)

    exit_code = cli.handle_analog_four_audio_patch_batch(
        audio_path=tmp_path / "reference.wav",
        source_kit_path=tmp_path / "init.syx",
        output_dir=tmp_path / "batch",
        json_output=True,
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    assert json.loads(captured.out)["error_code"] == error_code
    assert captured.err == ""


def test_registered_command_dispatches_without_midi(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.cli import main
    from rytm_randomizer.cockpit.export import analog_four_patch_batch_cli as cli

    monkeypatch.setattr(
        cli,
        "_export_analog_four_audio_patch_batch",
        lambda **_kwargs: _batch_result(tmp_path),
    )

    exit_code = main(
        [
            "analog-four-audio-patch-batch",
            "--audio",
            str(tmp_path / "reference.wav"),
            "--source-kit",
            str(tmp_path / "init.syx"),
            "--output-dir",
            str(tmp_path / "batch"),
            "--track",
            "2",
            "--candidates",
            "2",
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["source_hash"] == "audio-sha256"
    assert payload["candidate_count"] == 2
