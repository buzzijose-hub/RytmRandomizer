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


def _studio_batch_result(tmp_path: Path) -> _BatchResult:
    base = _batch_result(tmp_path)
    candidate_template = base.candidate_outputs[0]
    return replace(
        base,
        candidate_outputs=tuple(
            replace(
                candidate_template,
                column=column,
                label=f"Candidate {column}",
                sysex_path=tmp_path / f"candidate-{column}.syx",
                sidecar_path=tmp_path / f"candidate-{column}.json",
            )
            for column in range(1, 5)
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
        "studio_handoff": False,
        "a4_output_port": None,
        "json_output": False,
    }


def test_batch_payload_keeps_studio_handoff_optional_without_python_311_typing() -> None:
    from rytm_randomizer.cockpit.export.analog_four_patch_batch_cli import (
        AnalogFourAudioPatchBatchPayload,
    )

    assert AnalogFourAudioPatchBatchPayload.__optional_keys__ == frozenset({"studio_handoff"})
    assert "studio_handoff" not in AnalogFourAudioPatchBatchPayload.__required_keys__


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
            "4",
            "--overwrite",
            "--studio-handoff",
            "--a4-output-port",
            "Elektron Analog Four MKII 2",
            "--json",
        ]
    )

    assert options["track"] == 4
    assert options["candidate_count"] == 4
    assert options["overwrite"] is True
    assert options["studio_handoff"] is True
    assert options["a4_output_port"] == "Elektron Analog Four MKII 2"
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
                "--studio-handoff",
            ],
            "--studio-handoff requires --a4-output-port",
        ),
        (
            [
                "--audio",
                "clip.wav",
                "--source-kit",
                "init.syx",
                "--output-dir",
                "out",
                "--a4-output-port",
                "A4 Port",
            ],
            "--a4-output-port requires --studio-handoff",
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
                "3",
                "--studio-handoff",
                "--a4-output-port",
                "A4 Port",
            ],
            "--studio-handoff requires exactly four candidates",
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


def test_handler_emits_zero_calibration_four_candidate_studio_handoff(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.cockpit.export import analog_four_patch_batch_cli as cli

    monkeypatch.setattr(
        cli,
        "_export_analog_four_audio_patch_batch",
        lambda **_kwargs: _studio_batch_result(tmp_path),
    )

    exit_code = cli.handle_analog_four_audio_patch_batch(
        audio_path=tmp_path / "reference.wav",
        source_kit_path=tmp_path / "init.syx",
        output_dir=tmp_path / "batch",
        candidate_count=4,
        studio_handoff=True,
        a4_output_port="Elektron Analog Four MKII 2",
        json_output=True,
    )

    payload = json.loads(capsys.readouterr().out)
    handoff = payload["studio_handoff"]
    assert exit_code == 0
    assert handoff["calibration_rounds_required"] == 0
    assert handoff["candidate_auditions_required"] == 4
    assert len(handoff["candidates"]) == 4
    for column, candidate in enumerate(handoff["candidates"], start=1):
        assert candidate["candidate"] == column
        assert "--dry-run" in candidate["dry_run_argv"]
        assert "--confirm-a4-patch-send-plan" not in candidate["dry_run_argv"]
        assert "--arm" in candidate["armed_audition_argv"]
        assert "--confirm-a4-patch-send-plan" in candidate["armed_audition_argv"]
        assert candidate["armed_audition_argv"][-1] == "Elektron Analog Four MKII 2"
        assert candidate["render_path"].endswith(f"candidate-{column}.wav")
    assert handoff["rank_argv"].count("--render") == 4
    assert handoff["rank_argv"][-1] == "--json"


def test_studio_handoff_text_is_copyable_powershell_with_full_paths(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.cockpit.export import analog_four_patch_batch_cli as cli

    monkeypatch.setattr(
        cli,
        "_export_analog_four_audio_patch_batch",
        lambda **_kwargs: _studio_batch_result(tmp_path),
    )

    exit_code = cli.handle_analog_four_audio_patch_batch(
        audio_path=tmp_path / "reference.wav",
        source_kit_path=tmp_path / "init.syx",
        output_dir=tmp_path / "Jose's batch",
        studio_handoff=True,
        a4_output_port="Jose's A4",
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "calibration_rounds_required: 0" in output
    assert "candidate_auditions_required: 4" in output
    assert "powershell_setup: Set-Location '" in output
    assert "candidate_1_dry_run: & '" in output
    assert "candidate_4_armed_audition: & '" in output
    assert "'Jose''s A4'" in output
    assert "rank_after_recording: & '" in output


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("candidate-1.wav", "candidate-1.wav"),
        ("Jose's A4", "'Jose''s A4'"),
        ("", "''"),
    ],
)
def test_shared_powershell_literal_argument_formatting(value: str, expected: str) -> None:
    from rytm_randomizer.behavior.operator_console import powershell_literal_arg

    assert powershell_literal_arg(value) == expected


def test_studio_handoff_commands_round_trip_through_their_real_parsers(
    tmp_path: Path,
) -> None:
    from rytm_randomizer import app
    from rytm_randomizer.cockpit.export import analog_four_patch_batch_cli as cli
    from rytm_randomizer.cockpit.export.analog_four_patch_render_rank_cli import (
        parse_analog_four_patch_render_rank_args,
    )

    audio_path = tmp_path / "reference.wav"
    output_dir = tmp_path / "batch"
    result = _studio_batch_result(tmp_path)
    handoff = cli._studio_handoff_payload(
        result=result,
        audio_path=audio_path,
        output_dir=output_dir,
        a4_output_port="Elektron Analog Four MKII 2",
    )
    app_parser = app._build_parser()

    for column, candidate in enumerate(handoff["candidates"], start=1):
        dry_run = app_parser.parse_args(candidate["dry_run_argv"][3:])
        assert dry_run.dry_run is True
        assert dry_run.arm is False
        assert dry_run.a4_patch_send_plan is True
        assert dry_run.batch_manifest == str(result.manifest_path.resolve())
        assert dry_run.batch_manifest_sha256 == result.manifest_sha256
        assert dry_run.candidate == column
        assert dry_run.confirm_a4_patch_send_plan is False
        assert dry_run.a4_output_port is None

        armed = app_parser.parse_args(candidate["armed_audition_argv"][3:])
        assert armed.arm is True
        assert armed.dry_run is False
        assert armed.a4_patch_send_plan is True
        assert armed.batch_manifest == str(result.manifest_path.resolve())
        assert armed.batch_manifest_sha256 == result.manifest_sha256
        assert armed.candidate == column
        assert armed.confirm_a4_patch_send_plan is True
        assert armed.a4_output_port == "Elektron Analog Four MKII 2"

    rank = parse_analog_four_patch_render_rank_args(handoff["rank_argv"][4:])
    assert rank == {
        "reference_audio_path": audio_path.resolve(),
        "manifest_path": result.manifest_path.resolve(),
        "render_paths": {
            column: output_dir.resolve() / "renders" / f"candidate-{column}.wav"
            for column in range(1, 5)
        },
        "json_output": True,
    }


@pytest.mark.parametrize(
    ("studio_handoff", "a4_output_port", "candidate_count", "message"),
    [
        (True, None, 4, "--studio-handoff requires --a4-output-port"),
        (False, "A4 Port", 4, "--a4-output-port requires --studio-handoff"),
        (True, "A4 Port", 3, "--studio-handoff requires exactly four candidates"),
    ],
)
def test_handler_rejects_invalid_direct_studio_handoff_calls(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    studio_handoff: bool,
    a4_output_port: str | None,
    candidate_count: int,
    message: str,
) -> None:
    from rytm_randomizer.cockpit.export import analog_four_patch_batch_cli as cli

    exit_code = cli.handle_analog_four_audio_patch_batch(
        audio_path=tmp_path / "reference.wav",
        source_kit_path=tmp_path / "init.syx",
        output_dir=tmp_path / "batch",
        candidate_count=candidate_count,
        studio_handoff=studio_handoff,
        a4_output_port=a4_output_port,
        json_output=True,
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 2
    assert payload["error_code"] == "invalid_input"
    assert payload["error"] == message


def test_handler_reports_invalid_studio_handoff_as_text(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from rytm_randomizer.cockpit.export import analog_four_patch_batch_cli as cli

    exit_code = cli.handle_analog_four_audio_patch_batch(
        audio_path=tmp_path / "reference.wav",
        source_kit_path=tmp_path / "init.syx",
        output_dir=tmp_path / "batch",
        studio_handoff=True,
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    assert captured.out == ""
    assert "Error [invalid_input]: --studio-handoff requires --a4-output-port" in (captured.err)


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
