"""Tests for the passive resumable Audio-to-Patch studio-session command."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from rytm_randomizer import cli as root_cli
from rytm_randomizer.cockpit.export import audio_patch_studio_session as service
from rytm_randomizer.cockpit.export import audio_patch_studio_session_cli as cli
from rytm_randomizer.cockpit.export import cli_options

pytestmark = pytest.mark.fast


def test_shared_required_option_can_include_usage_guidance() -> None:
    with pytest.raises(
        ValueError,
        match=r"--session requires a value\. Usage: studio-session",
    ):
        cli_options.pop_required_cli_value(
            [],
            option="--session",
            usage="Usage: studio-session",
        )


def test_shared_bounded_integer_rejects_non_integer_text() -> None:
    with pytest.raises(
        ValueError,
        match="--select must be an integer from 1 to 12",
    ):
        cli_options.parse_bounded_integer(
            "not-an-integer",
            option="--select",
            lower=1,
            upper=12,
        )


def test_shared_exception_notes_rejects_non_list_storage() -> None:
    error = ValueError("invalid")
    error.__notes__ = ("not canonical",)  # type: ignore[assignment]

    assert cli_options.exception_notes(error) == []


def test_shared_exception_notes_returns_only_strings() -> None:
    error = ValueError("invalid")
    error.__notes__ = ["keep", 7]  # type: ignore[list-item]

    assert cli_options.exception_notes(error) == ["keep"]


def _result(
    tmp_path: Path, *, status: service.AudioPatchStudioSessionStatus
) -> service.AudioPatchStudioSessionResult:
    payload: service.AudioPatchStudioSessionPayload = {
        "schema_version": service.AUDIO_PATCH_STUDIO_SESSION_SCHEMA_VERSION,
        "session_id": "studio-123",
        "status": status,
        "reference_audio": {"filename": "reference.wav", "sha256": "a" * 64},
        "source_kit": {"filename": "source.syx", "sha256": "b" * 64},
        "selection": {
            "dna_candidate": 6,
            "manifest_candidate": 1,
            "key": "atmospheric",
            "label": "Atmospheric",
            "role": "Atmospheric direction",
            "closeness": 88,
            "track": 2,
            "generation_id": "generation-123",
        },
        "workspace": {
            "json": {"path": "workspace/audio-patch-dna.json", "sha256": "c" * 64},
            "markdown": {"path": "workspace/audio-patch-dna.md", "sha256": "d" * 64},
        },
        "selected_export": {
            "manifest": {"path": "workspace/selected-a4/manifest.json", "sha256": "e" * 64},
            "sysex": {"path": "workspace/selected-a4/candidate.syx", "sha256": "f" * 64},
            "sidecar": {"path": "workspace/selected-a4/candidate.json", "sha256": "0" * 64},
        },
        "safety": list(service.AUDIO_PATCH_STUDIO_SESSION_SAFETY),
    }
    return service.AudioPatchStudioSessionResult(
        payload=payload,
        json_path=tmp_path / "studio-session.json",
        markdown_path=tmp_path / "studio-session.md",
    )


def test_help_is_passive_and_successful(capsys: pytest.CaptureFixture[str]) -> None:
    parsed = cli.parse_audio_patch_studio_session_args(["--help"])

    assert parsed["help_requested"] is True
    assert root_cli.main([cli.COMMAND_NAME, "--help"]) == 0
    captured = capsys.readouterr()
    assert captured.out == f"{cli.USAGE}\n"
    assert captured.err == ""


def test_parser_accepts_start_options() -> None:
    parsed = cli.parse_audio_patch_studio_session_args(
        [
            "--reference",
            "reference.wav",
            "--source-kit",
            "source.syx",
            "--select",
            "6",
            "--output-dir",
            "output/session",
            "--track",
            "2",
            "--overwrite",
            "--json",
        ]
    )

    assert parsed["mode"] == "start"
    assert parsed["selection"] == 6
    assert parsed["output_dir"] == Path("output/session")
    assert parsed["track"] == 2
    assert parsed["session_path"] is None
    assert parsed["overwrite"] is True
    assert parsed["json_output"] is True
    assert parsed["help_requested"] is False


def test_parser_accepts_resume_options() -> None:
    parsed = cli.parse_audio_patch_studio_session_args(
        [
            "--session",
            "session/studio-session.json",
            "--reference",
            "reference.wav",
            "--source-kit",
            "source.syx",
            "--render",
            "render.wav",
            "--gain",
            "0.25",
            "--accept-similarity",
            "91",
        ]
    )

    assert parsed["mode"] == "resume"
    assert parsed["session_path"] == Path("session/studio-session.json")
    assert parsed["render_audio_path"] == Path("render.wav")
    assert parsed["selection"] is None
    assert parsed["output_dir"] is None
    assert parsed["correction_gain"] == 0.25
    assert parsed["accept_similarity"] == 91


@pytest.mark.parametrize(
    ("args", "message"),
    [
        ([], "--reference is required"),
        (["--reference", "a.wav"], "--source-kit is required"),
        (
            ["--reference", "a.wav", "--source-kit", "s.syx"],
            "--select is required",
        ),
        (
            [
                "--reference",
                "a.wav",
                "--source-kit",
                "s.syx",
                "--select",
                "1",
            ],
            "--output-dir is required",
        ),
        (
            [
                "--reference",
                "a.wav",
                "--source-kit",
                "s.syx",
                "--session",
                "state.json",
            ],
            "--session and --render are required together",
        ),
        (
            [
                "--reference",
                "a.wav",
                "--source-kit",
                "s.syx",
                "--render",
                "render.wav",
            ],
            "--session and --render are required together",
        ),
        (
            [
                "--reference",
                "a.wav",
                "--source-kit",
                "s.syx",
                "--session",
                "state.json",
                "--render",
                "render.wav",
                "--track",
                "2",
            ],
            "start-only options",
        ),
        (
            [
                "--reference",
                "a.wav",
                "--source-kit",
                "s.syx",
                "--select",
                "1",
                "--output-dir",
                "out",
                "--gain",
                "0.2",
            ],
            "resume-only options",
        ),
        (
            [
                "--reference",
                "a.wav",
                "--source-kit",
                "s.syx",
                "--select",
                "9",
                "--output-dir",
                "out",
            ],
            "1 to 8",
        ),
        (
            [
                "--reference",
                "a.wav",
                "--source-kit",
                "s.syx",
                "--session",
                "state.json",
                "--render",
                "render.wav",
                "--gain",
                "nan",
            ],
            "0.0 to 1.0",
        ),
        (
            [
                "--reference",
                "a.wav",
                "--source-kit",
                "s.syx",
                "--session",
                "state.json",
                "--render",
                "render.wav",
                "--gain",
                "nope",
            ],
            "0.0 to 1.0",
        ),
        (["--wat"], "unknown option"),
    ],
)
def test_parser_rejects_invalid_inputs(args: list[str], message: str) -> None:
    with pytest.raises(ValueError, match=message):
        cli.parse_audio_patch_studio_session_args(args)


def test_registry_parser_preserves_json_parse_failure() -> None:
    parsed = cli._parse_session_args_for_registry(["--json", "--reference"])

    assert parsed["json_output"] is True
    assert parsed["parse_error"] == "--reference requires a value"


def test_registry_parser_raises_text_parse_failure() -> None:
    with pytest.raises(ValueError, match="--reference requires a value"):
        cli._parse_session_args_for_registry(["--reference"])


def test_json_start_handler_forwards_inputs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    calls: list[dict[str, object]] = []

    def fake_start(**kwargs: object) -> service.AudioPatchStudioSessionResult:
        calls.append(kwargs)
        return _result(tmp_path, status="waiting_for_render")

    monkeypatch.setattr(cli, "_start_session", fake_start)
    exit_code = cli.handle_audio_patch_studio_session(
        mode="start",
        reference_audio_path=tmp_path / "reference.wav",
        source_kit_path=tmp_path / "source.syx",
        selection=6,
        output_dir=tmp_path,
        track=2,
        overwrite=True,
        json_output=True,
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert calls == [
        {
            "reference_audio_path": tmp_path / "reference.wav",
            "source_kit_path": tmp_path / "source.syx",
            "selection": 6,
            "output_dir": tmp_path,
            "track": 2,
            "overwrite": True,
        }
    ]
    assert payload["status"] == "waiting_for_render"
    assert payload["selection"]["dna_candidate"] == 6
    assert payload["selection"]["manifest_candidate"] == 1
    assert payload["transition"] == "replayed"
    assert payload["ok"] is True


def test_text_resume_handler_forwards_inputs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    calls: list[dict[str, object]] = []

    def fake_resume(**kwargs: object) -> service.AudioPatchStudioSessionResult:
        calls.append(kwargs)
        return _result(tmp_path, status="refined")

    monkeypatch.setattr(cli, "_resume_session", fake_resume)
    exit_code = cli.handle_audio_patch_studio_session(
        mode="resume",
        reference_audio_path=tmp_path / "reference.wav",
        source_kit_path=tmp_path / "source.syx",
        selection=None,
        output_dir=None,
        session_path=tmp_path / "studio-session.json",
        render_audio_path=tmp_path / "render.wav",
        correction_gain=0.25,
        accept_similarity=91,
    )

    stdout = capsys.readouterr().out
    assert exit_code == 0
    assert calls[0]["correction_gain"] == 0.25
    assert calls[0]["accept_similarity"] == 91
    assert "status: refined" in stdout
    assert "dna_candidate: 6" in stdout
    assert "manifest_candidate: 1" in stdout
    assert "transition: replayed" in stdout
    assert "- no MIDI ports enumerated or opened" in stdout


def test_handler_reports_structured_parse_error(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = cli.handle_audio_patch_studio_session(
        mode="start",
        reference_audio_path=Path(),
        source_kit_path=Path(),
        selection=None,
        output_dir=None,
        json_output=True,
        parse_error="bad option",
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 2
    assert payload["error_code"] == "invalid_input"
    assert payload["error"] == "bad option"


@pytest.mark.parametrize("exc", [KeyboardInterrupt(), SystemExit("stop")])
def test_handler_reports_interruption(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    exc: BaseException,
) -> None:
    def interrupt(**_kwargs: object) -> service.AudioPatchStudioSessionResult:
        raise exc

    monkeypatch.setattr(cli, "_start_session", interrupt)
    exit_code = cli.handle_audio_patch_studio_session(
        mode="start",
        reference_audio_path=tmp_path / "reference.wav",
        source_kit_path=tmp_path / "source.syx",
        selection=1,
        output_dir=tmp_path,
        json_output=True,
    )

    assert exit_code == 130
    assert json.loads(capsys.readouterr().out)["error_code"] == "interrupted"


def test_public_cli_dispatches_studio_session_command(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    calls: list[dict[str, object]] = []

    def fake_start(**kwargs: object) -> service.AudioPatchStudioSessionResult:
        calls.append(kwargs)
        return _result(tmp_path, status="waiting_for_render")

    monkeypatch.setattr(cli, "_start_session", fake_start)
    exit_code = root_cli.main(
        [
            cli.COMMAND_NAME,
            "--reference",
            str(tmp_path / "reference.wav"),
            "--source-kit",
            str(tmp_path / "source.syx"),
            "--select",
            "6",
            "--output-dir",
            str(tmp_path),
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["session_id"] == "studio-123"
    assert calls[0]["selection"] == 6


def test_registered_command_contract_and_error_formatter() -> None:
    assert cli.AUDIO_PATCH_STUDIO_SESSION_CLI_COMMAND.name == cli.COMMAND_NAME
    assert "Start or resume" in cli.AUDIO_PATCH_STUDIO_SESSION_CLI_COMMAND.summary
    assert cli._format_session_cli_error(ValueError("bad")) == (
        f"{cli.USAGE}\nError [invalid_input]: bad"
    )


def test_lazy_service_wrappers_forward_inputs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    start_calls: list[dict[str, object]] = []
    resume_calls: list[dict[str, object]] = []

    def fake_start(**kwargs: object) -> service.AudioPatchStudioSessionResult:
        start_calls.append(kwargs)
        return _result(tmp_path, status="waiting_for_render")

    def fake_resume(**kwargs: object) -> service.AudioPatchStudioSessionResult:
        resume_calls.append(kwargs)
        return _result(tmp_path, status="accepted")

    monkeypatch.setattr(service, "start_audio_patch_studio_session", fake_start)
    monkeypatch.setattr(service, "resume_audio_patch_studio_session", fake_resume)
    cli._start_session(
        reference_audio_path=tmp_path / "reference.wav",
        source_kit_path=tmp_path / "source.syx",
        selection=4,
        output_dir=tmp_path / "session",
        track=2,
        overwrite=True,
    )
    cli._resume_session(
        session_path=tmp_path / "studio-session.json",
        reference_audio_path=tmp_path / "reference.wav",
        source_kit_path=tmp_path / "source.syx",
        render_audio_path=tmp_path / "render.wav",
        correction_gain=0.2,
        accept_similarity=90,
        overwrite=True,
    )

    assert start_calls[0]["selection"] == 4
    assert start_calls[0]["overwrite"] is True
    assert resume_calls[0]["correction_gain"] == 0.2
    assert resume_calls[0]["accept_similarity"] == 90


@pytest.mark.parametrize("mode", ["start", "resume"])
def test_handler_rejects_missing_mode_contract(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    mode: cli.AudioPatchStudioSessionMode,
) -> None:
    exit_code = cli.handle_audio_patch_studio_session(
        mode=mode,
        reference_audio_path=tmp_path / "reference.wav",
        source_kit_path=tmp_path / "source.syx",
        selection=None,
        output_dir=None,
        json_output=True,
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 2
    assert payload["error_code"] == "invalid_input"
    assert "mode requires" in payload["error"]


def test_handler_rejects_an_unknown_mode(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = cli.handle_audio_patch_studio_session(
        mode="unknown",  # type: ignore[arg-type] - runtime boundary regression
        reference_audio_path=tmp_path / "reference.wav",
        source_kit_path=tmp_path / "source.syx",
        selection=None,
        output_dir=None,
        json_output=True,
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 2
    assert payload["error_code"] == "invalid_input"
    assert payload["error"] == "studio session mode must be 'start' or 'resume'"


def test_handler_reports_service_error_as_text(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fail(**_kwargs: object) -> service.AudioPatchStudioSessionResult:
        raise ValueError("broken session")

    monkeypatch.setattr(cli, "_start_session", fail)
    exit_code = cli.handle_audio_patch_studio_session(
        mode="start",
        reference_audio_path=tmp_path / "reference.wav",
        source_kit_path=tmp_path / "source.syx",
        selection=1,
        output_dir=tmp_path,
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    assert captured.out == ""
    assert "Error [invalid_input]: broken session" in captured.err
