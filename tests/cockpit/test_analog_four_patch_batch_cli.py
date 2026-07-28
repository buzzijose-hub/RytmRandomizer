"""Operator CLI tests for audio-dependent Analog Four patch batches."""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from pathlib import Path

import pytest

from rytm_randomizer.cockpit.export.analog_four_export_contracts import (
    ANALOG_FOUR_EXPORT_ERROR_CODES,
    AnalogFourExportErrorCode,
)

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
    generation_id: str
    manifest_path: Path
    manifest_sha256: str
    lock_cleanup_warning: str | None
    selected_track: int
    candidate_outputs: tuple[_CandidateOutput, ...]
    safety: tuple[str, ...]


def _batch_result(tmp_path: Path) -> _BatchResult:
    return _BatchResult(
        source_hash="audio-sha256",
        generation_id="generation-1234",
        manifest_path=tmp_path / "a4-t2-audio-patch-batch.json",
        manifest_sha256="manifest-sha256",
        lock_cleanup_warning=None,
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


def test_registry_parser_preserves_non_json_validation_errors() -> None:
    from rytm_randomizer.cockpit.export import analog_four_patch_batch_cli as cli

    with pytest.raises(ValueError, match="--audio is required"):
        cli._parse_batch_args_for_registry([])


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
        "generation_id": "generation-1234",
        "manifest_path": str(tmp_path / "a4-t2-audio-patch-batch.json"),
        "manifest_sha256": "manifest-sha256",
        "ok": True,
        "safety": ["local files only", "no MIDI sending"],
        "selected_track": 2,
        "source_hash": "audio-sha256",
        "warnings": [],
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
    assert "generation_id: generation-1234" in captured.out
    assert f"manifest_path: {tmp_path / 'a4-t2-audio-patch-batch.json'}" in captured.out
    assert "manifest_sha256: manifest-sha256" in captured.out
    assert "candidate_count: 2" in captured.out
    assert "candidate: 1 | Closest reference" in captured.out
    assert "sysex_applied_count: 2" in captured.out
    assert "live_sendable_count: 67" in captured.out
    assert "manual_count: 11" in captured.out
    assert "deferred_count: 76" in captured.out
    assert "- no MIDI sending" in captured.out


def test_handler_emits_lock_cleanup_warning_in_text(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.cockpit.export import analog_four_patch_batch_cli as cli

    warning = "committed batch retained publication lock metadata"
    monkeypatch.setattr(
        cli,
        "_export_analog_four_audio_patch_batch",
        lambda **_kwargs: replace(_batch_result(tmp_path), lock_cleanup_warning=warning),
    )

    exit_code = cli.handle_analog_four_audio_patch_batch(
        audio_path=tmp_path / "reference.wav",
        source_kit_path=tmp_path / "init.syx",
        output_dir=tmp_path / "batch",
    )

    assert exit_code == 0
    assert f"warning: {warning}" in capsys.readouterr().out


def test_lazy_export_loader_forwards_every_argument(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.cockpit.export import analog_four_patch_batch_cli as cli

    observed: dict[str, object] = {}

    def fake_export(**kwargs: object) -> _BatchResult:
        observed.update(kwargs)
        return _batch_result(tmp_path)

    monkeypatch.setattr(
        cli,
        "_load_batch_exporter",
        lambda: fake_export,
    )

    result = cli._export_analog_four_audio_patch_batch(
        audio_path=tmp_path / "reference.wav",
        source_kit_path=tmp_path / "init.syx",
        output_dir=tmp_path / "batch",
        track=3,
        candidate_count=2,
        overwrite=True,
    )

    assert result == _batch_result(tmp_path)
    assert observed == {
        "audio_path": tmp_path / "reference.wav",
        "source_kit_path": tmp_path / "init.syx",
        "output_dir": tmp_path / "batch",
        "track": 3,
        "candidate_count": 2,
        "overwrite": True,
    }


def test_lazy_export_loader_returns_the_typed_batch_service() -> None:
    from rytm_randomizer.cockpit.export import analog_four_patch_batch_cli as cli
    from rytm_randomizer.cockpit.export.analog_four_patch_batch import (
        export_analog_four_audio_patch_batch,
    )

    assert cli._load_batch_exporter() is export_analog_four_audio_patch_batch


@pytest.mark.parametrize(
    ("exc", "error_code"),
    [
        (FileNotFoundError("missing audio"), "input_not_found"),
        (FileExistsError("candidate exists"), "overwrite_refused"),
        (PermissionError("denied"), "permission_denied"),
        (OSError("disk error"), "write_failed"),
        (ValueError("unsupported audio"), "validation"),
        (ImportError("service unavailable"), "service_unavailable"),
        (RuntimeError("inference dependency unavailable"), "inference_failed"),
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


def test_handler_exposes_exception_notes_and_classified_stage_codes(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.cockpit.export import analog_four_patch_batch_cli as cli

    class ClassifiedFailure(RuntimeError):
        error_code = "audio_read_failed"

    failure = ClassifiedFailure("decode failed")
    failure.add_note("batch lock cleanup failure: lock busy")
    monkeypatch.setattr(
        cli,
        "_export_analog_four_audio_patch_batch",
        lambda **_kwargs: (_ for _ in ()).throw(failure),
    )

    exit_code = cli.handle_analog_four_audio_patch_batch(
        audio_path=tmp_path / "reference.wav",
        source_kit_path=tmp_path / "init.syx",
        output_dir=tmp_path / "batch",
        json_output=True,
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 2
    assert payload["error_code"] == "audio_read_failed"
    assert payload["details"] == ["batch lock cleanup failure: lock busy"]


def test_batch_cli_rejects_unbounded_dynamic_error_codes() -> None:
    from rytm_randomizer.cockpit.export import analog_four_patch_batch_cli as cli

    class UnboundedFailure(RuntimeError):
        error_code = "invented_code"

    assert cli._batch_cli_error_code(UnboundedFailure("failure")) == "inference_failed"


def test_a4_export_error_codes_share_one_bounded_vocabulary() -> None:
    from typing import get_args

    assert frozenset(get_args(AnalogFourExportErrorCode)) == ANALOG_FOUR_EXPORT_ERROR_CODES


def test_handler_surfaces_successful_commit_lock_warning(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.cockpit.export import analog_four_patch_batch_cli as cli

    warning = "batch committed; stale lock metadata remains at batch.lock"
    monkeypatch.setattr(
        cli,
        "_export_analog_four_audio_patch_batch",
        lambda **_kwargs: replace(_batch_result(tmp_path), lock_cleanup_warning=warning),
    )

    exit_code = cli.handle_analog_four_audio_patch_batch(
        audio_path=tmp_path / "reference.wav",
        source_kit_path=tmp_path / "init.syx",
        output_dir=tmp_path / "batch",
        json_output=True,
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["warnings"] == [warning]


def test_handler_emits_classified_text_error_and_registry_formatter(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.cockpit.export import analog_four_patch_batch_cli as cli

    failure = ValueError("unsupported audio")
    failure.add_note("batch lock cleanup failure: lock busy")

    def fail_export(**_kwargs: object) -> _BatchResult:
        raise failure

    monkeypatch.setattr(cli, "_export_analog_four_audio_patch_batch", fail_export)

    exit_code = cli.handle_analog_four_audio_patch_batch(
        audio_path=tmp_path / "reference.wav",
        source_kit_path=tmp_path / "init.syx",
        output_dir=tmp_path / "batch",
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    assert captured.out == ""
    assert "Error [validation]: unsupported audio" in captured.err
    assert "Detail: batch lock cleanup failure: lock busy" in captured.err
    assert cli._format_batch_cli_error(ValueError("bad args")) == (
        f"{cli.USAGE}\nError [invalid_input]: bad args"
    )


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


def test_registered_json_parse_failure_is_machine_readable(
    capsys: pytest.CaptureFixture[str],
) -> None:
    from rytm_randomizer.cli import main

    exit_code = main(["analog-four-audio-patch-batch", "--json"])

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 2
    assert payload["ok"] is False
    assert payload["error_code"] == "invalid_input"
    assert payload["error"] == "--audio is required"
    assert captured.err == ""


@pytest.mark.parametrize("interruption", [KeyboardInterrupt(), SystemExit(7)])
def test_batch_cli_returns_structured_interrupted_response(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    interruption: BaseException,
) -> None:
    from rytm_randomizer.cockpit.export import analog_four_patch_batch_cli as cli

    def interrupt_export(**_kwargs: object) -> None:
        raise interruption

    monkeypatch.setattr(cli, "_export_analog_four_audio_patch_batch", interrupt_export)

    exit_code = cli.handle_analog_four_audio_patch_batch(
        audio_path=tmp_path / "reference.wav",
        source_kit_path=tmp_path / "init.syx",
        output_dir=tmp_path / "batch",
        json_output=True,
    )

    assert exit_code == 130
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is False
    assert payload["error_code"] == "interrupted"


def test_batch_cli_reports_text_interrupted_response(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from rytm_randomizer.cockpit.export import analog_four_patch_batch_cli as cli

    monkeypatch.setattr(
        cli,
        "_export_analog_four_audio_patch_batch",
        lambda **_kwargs: (_ for _ in ()).throw(KeyboardInterrupt("operator cancelled")),
    )

    exit_code = cli.handle_analog_four_audio_patch_batch(
        audio_path=tmp_path / "reference.wav",
        source_kit_path=tmp_path / "init.syx",
        output_dir=tmp_path / "batch",
        json_output=False,
    )

    captured = capsys.readouterr()
    assert exit_code == 130
    assert "Error [interrupted]: operator cancelled" in captured.err
    assert captured.out == ""
