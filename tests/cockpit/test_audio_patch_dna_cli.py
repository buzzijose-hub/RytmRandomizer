"""Tests for the passive Audio-to-Patch DNA command."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pytest

from rytm_randomizer.cockpit.export import audio_patch_dna_cli as cli
from rytm_randomizer.cockpit.export.analog_four_export_contracts import (
    attach_analog_four_export_error_code,
)

pytestmark = pytest.mark.fast


@dataclass(frozen=True)
class _Candidate:
    column: int
    key: str
    label: str
    role: str
    closeness: int


@dataclass(frozen=True)
class _Workspace:
    candidates: tuple[_Candidate, ...]


@dataclass(frozen=True)
class _A4Candidate:
    sysex_path: Path
    sidecar_path: Path


@dataclass(frozen=True)
class _A4Export:
    manifest_path: Path
    candidates: tuple[_A4Candidate, ...]


@dataclass(frozen=True)
class _Result:
    workspace: _Workspace
    json_path: Path
    markdown_path: Path
    selected_candidate: _Candidate | None = None
    analog_four_export: _A4Export | None = None


def _result(tmp_path: Path, *, selected: bool = False) -> _Result:
    labels = (
        "Closest",
        "Darker",
        "Brighter",
        "Metallic",
        "Percussive",
        "Atmospheric",
        "Deeper",
        "Animated",
    )
    candidates = tuple(
        _Candidate(
            column=index,
            key=label.lower(),
            label=label,
            role=f"{label} direction",
            closeness=101 - index,
        )
        for index, label in enumerate(labels, start=1)
    )
    if not selected:
        return _Result(
            workspace=_Workspace(candidates),
            json_path=tmp_path / "audio-patch-dna.json",
            markdown_path=tmp_path / "audio-patch-dna.md",
        )
    export_dir = tmp_path / "selected-a4"
    return _Result(
        workspace=_Workspace(candidates),
        json_path=tmp_path / "audio-patch-dna.json",
        markdown_path=tmp_path / "audio-patch-dna.md",
        selected_candidate=candidates[5],
        analog_four_export=_A4Export(
            manifest_path=export_dir / "manifest.json",
            candidates=(
                _A4Candidate(
                    sysex_path=export_dir / "candidate.syx",
                    sidecar_path=export_dir / "candidate.json",
                ),
            ),
        ),
    )


def test_parser_defaults_to_compare_only() -> None:
    parsed = cli.parse_audio_patch_dna_args(
        ["--audio", "reference.wav", "--output-dir", "output/dna"]
    )

    assert parsed == {
        "audio_path": Path("reference.wav"),
        "output_dir": Path("output/dna"),
        "track": 1,
        "selection": None,
        "source_kit_path": None,
        "overwrite": False,
        "json_output": False,
    }


def test_parser_accepts_selected_export_options() -> None:
    parsed = cli.parse_audio_patch_dna_args(
        [
            "--audio",
            "reference.wav",
            "--output-dir",
            "output/dna",
            "--track",
            "4",
            "--select",
            "8",
            "--source-kit",
            "source.syx",
            "--overwrite",
            "--json",
        ]
    )

    assert parsed["track"] == 4
    assert parsed["selection"] == 8
    assert parsed["source_kit_path"] == Path("source.syx")
    assert parsed["overwrite"] is True
    assert parsed["json_output"] is True


@pytest.mark.parametrize(
    ("args", "message"),
    [
        (["--output-dir", "out"], "--audio is required"),
        (["--audio", "a.wav"], "--output-dir is required"),
        (["--audio"], "--audio requires a value"),
        (["--wat"], "unknown option"),
        (["--audio", "a", "--output-dir", "o", "--track", "0"], "1 to 4"),
        (["--audio", "a", "--output-dir", "o", "--track", "01"], "1 to 4"),
        (["--audio", "a", "--output-dir", "o", "--track", "x"], "1 to 4"),
        (["--audio", "a", "--output-dir", "o", "--select", "9"], "1 to 8"),
        (["--audio", "a", "--output-dir", "o", "--select", "01"], "1 to 8"),
        (["--audio", "a", "--output-dir", "o", "--select", "x"], "1 to 8"),
        (["--audio", "a", "--output-dir", "o", "--select", "1"], "requires --source-kit"),
        (
            ["--audio", "a", "--output-dir", "o", "--source-kit", "s.syx"],
            "requires --select",
        ),
    ],
)
def test_parser_rejects_invalid_inputs(args: list[str], message: str) -> None:
    with pytest.raises(ValueError, match=message):
        cli.parse_audio_patch_dna_args(args)


def test_registry_parser_preserves_json_parse_failures() -> None:
    parsed = cli._parse_dna_args_for_registry(["--json", "--audio"])

    assert parsed["json_output"] is True
    assert parsed["parse_error"] == "--audio requires a value"


def test_registry_parser_raises_text_parse_failures() -> None:
    with pytest.raises(ValueError, match="--audio requires a value"):
        cli._parse_dna_args_for_registry(["--audio"])


def test_json_handler_forwards_compare_only_inputs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    calls: list[dict[str, object]] = []

    def fake_export(**kwargs: object) -> _Result:
        calls.append(kwargs)
        return _result(tmp_path)

    monkeypatch.setattr(cli, "_export_audio_patch_dna", fake_export)
    exit_code = cli.handle_audio_patch_dna(
        audio_path=tmp_path / "reference.wav",
        output_dir=tmp_path,
        track=2,
        json_output=True,
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert len(calls) == 1
    assert calls[0]["track"] == 2
    assert calls[0]["selection"] is None
    assert payload["ok"] is True
    assert payload["candidate_count"] == 8
    assert [candidate["label"] for candidate in payload["candidates"]] == [
        "Closest",
        "Darker",
        "Brighter",
        "Metallic",
        "Percussive",
        "Atmospheric",
        "Deeper",
        "Animated",
    ]
    assert "selected_candidate" not in payload


def test_text_handler_reports_selected_a4_artifacts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        cli, "_export_audio_patch_dna", lambda **_kwargs: _result(tmp_path, selected=True)
    )

    exit_code = cli.handle_audio_patch_dna(
        audio_path=tmp_path / "reference.wav",
        output_dir=tmp_path,
        selection=6,
        source_kit_path=tmp_path / "source.syx",
    )

    stdout = capsys.readouterr().out
    assert exit_code == 0
    assert "candidate_count: 8" in stdout
    assert "selected_candidate: 6 | Atmospheric" in stdout
    assert "selected_a4_manifest:" in stdout
    assert "selected_a4_sysex:" in stdout
    assert "selected_a4_sidecar:" in stdout
    assert "- no MIDI sending" in stdout


def test_json_handler_reports_selected_a4_artifacts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        cli, "_export_audio_patch_dna", lambda **_kwargs: _result(tmp_path, selected=True)
    )

    assert (
        cli.handle_audio_patch_dna(
            audio_path=tmp_path / "reference.wav",
            output_dir=tmp_path,
            selection=6,
            source_kit_path=tmp_path / "source.syx",
            json_output=True,
        )
        == 0
    )
    payload = json.loads(capsys.readouterr().out)
    assert payload["selected_candidate"]["label"] == "Atmospheric"
    assert payload["selected_a4_manifest"].endswith("manifest.json")
    assert payload["selected_a4_sysex"].endswith("candidate.syx")
    assert payload["selected_a4_sidecar"].endswith("candidate.json")


def test_handler_returns_structured_parse_error(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = cli.handle_audio_patch_dna(
        audio_path=Path(),
        output_dir=Path(),
        json_output=True,
        parse_error="bad option",
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 2
    assert payload["error_code"] == "invalid_input"
    assert payload["error"] == "bad option"


@pytest.mark.parametrize(
    ("exc", "expected"),
    [
        (FileNotFoundError("missing"), "input_not_found"),
        (FileExistsError("exists"), "overwrite_refused"),
        (PermissionError("denied"), "permission_denied"),
        (OSError("write"), "write_failed"),
        (ImportError("missing dependency"), "service_unavailable"),
        (RuntimeError("inference"), "inference_failed"),
        (ValueError("invalid"), "invalid_input"),
    ],
)
def test_error_classifier_is_bounded(exc: Exception, expected: str) -> None:
    assert cli._dna_cli_error_code(exc) == expected


def test_error_classifier_preserves_valid_attached_code() -> None:
    exc = RuntimeError("audio")
    attach_analog_four_export_error_code(exc, "audio_read_failed")

    assert cli._dna_cli_error_code(exc) == "audio_read_failed"


def test_error_classifier_ignores_unbounded_attached_code() -> None:
    exc = ValueError("invalid")
    exc.__dict__["error_code"] = "made_up"

    assert cli._dna_cli_error_code(exc) == "invalid_input"


def test_json_error_includes_string_notes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    exc = RuntimeError("analysis failed")
    exc.add_note("decode the operator-selected file")
    exc.__notes__.append(42)  # type: ignore[arg-type]

    def fail(**_kwargs: object) -> _Result:
        raise exc

    monkeypatch.setattr(cli, "_export_audio_patch_dna", fail)
    exit_code = cli.handle_audio_patch_dna(
        audio_path=tmp_path / "reference.wav",
        output_dir=tmp_path,
        json_output=True,
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 2
    assert payload["error_code"] == "inference_failed"
    assert payload["details"] == ["decode the operator-selected file"]


def test_text_error_includes_usage_and_details(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    exc = ValueError("bad audio")
    exc.add_note("choose a readable file")

    def fail(**_kwargs: object) -> _Result:
        raise exc

    monkeypatch.setattr(cli, "_export_audio_patch_dna", fail)
    assert cli.handle_audio_patch_dna(audio_path=tmp_path / "a.wav", output_dir=tmp_path) == 2

    stderr = capsys.readouterr().err
    assert cli.USAGE in stderr
    assert "Error [invalid_input]: bad audio" in stderr
    assert "Detail: choose a readable file" in stderr


@pytest.mark.parametrize("exc", [KeyboardInterrupt(), SystemExit("stop")])
@pytest.mark.parametrize("json_output", [False, True])
def test_handler_reports_interruption(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    exc: BaseException,
    json_output: bool,
) -> None:
    def interrupt(**_kwargs: object) -> _Result:
        raise exc

    monkeypatch.setattr(cli, "_export_audio_patch_dna", interrupt)
    assert (
        cli.handle_audio_patch_dna(
            audio_path=tmp_path / "a.wav",
            output_dir=tmp_path,
            json_output=json_output,
        )
        == 130
    )
    captured = capsys.readouterr()
    if json_output:
        assert json.loads(captured.out)["error_code"] == "interrupted"
    else:
        assert "Error [interrupted]" in captured.err


def test_exception_notes_ignores_non_list_notes() -> None:
    exc = ValueError("bad")
    exc.__dict__["__notes__"] = ("hidden",)

    assert cli.exception_notes(exc) == []


def test_lazy_export_boundary_calls_loaded_service(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[dict[str, object]] = []

    def exporter(**kwargs: object) -> _Result:
        calls.append(kwargs)
        return _result(tmp_path)

    monkeypatch.setattr(cli, "_load_dna_exporter", lambda: exporter)
    result = cli._export_audio_patch_dna(
        audio_path=tmp_path / "a.wav",
        output_dir=tmp_path,
        track=3,
        selection=None,
        source_kit_path=None,
        overwrite=True,
    )

    assert result.json_path == tmp_path / "audio-patch-dna.json"
    assert calls[0]["track"] == 3
    assert calls[0]["overwrite"] is True


def test_registered_command_contract_and_error_formatter() -> None:
    assert cli.AUDIO_PATCH_DNA_CLI_COMMAND.name == "audio-patch-dna"
    assert "eight comparable patch directions" in cli.AUDIO_PATCH_DNA_CLI_COMMAND.summary
    assert cli._format_audio_patch_dna_cli_error(ValueError("bad")) == (
        f"{cli.USAGE}\nError [invalid_input]: bad"
    )


def test_registry_parser_adds_empty_parse_error_on_success() -> None:
    parsed = cli._parse_dna_args_for_registry(["--audio", "a.wav", "--output-dir", "out"])

    assert parsed["audio_path"] == Path("a.wav")
    assert parsed["parse_error"] is None


def test_text_handler_reports_compare_only_workspace(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(cli, "_export_audio_patch_dna", lambda **_options: _result(tmp_path))

    assert (
        cli.handle_audio_patch_dna(
            audio_path=tmp_path / "reference.wav",
            output_dir=tmp_path,
        )
        == 0
    )
    output = capsys.readouterr().out

    assert "candidate: 1 | Closest" in output
    assert "selected_candidate:" not in output
    assert "selected_a4_sysex:" not in output


def test_lazy_loader_returns_workspace_exporter() -> None:
    from rytm_randomizer.cockpit.export.audio_patch_dna import (
        export_audio_patch_dna_workspace,
    )

    assert cli._load_dna_exporter() is export_audio_patch_dna_workspace
