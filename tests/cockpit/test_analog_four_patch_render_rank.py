"""Passive Analog Four hardware-render ranking tests."""

from __future__ import annotations

import io
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from rytm_randomizer.style_analysis.analog_four_patch_inference import (
    AnalogFourPatchAudioFeatures,
)

pytestmark = [
    pytest.mark.fast,
    pytest.mark.usefixtures("isolated_observability"),
]


REFERENCE_SHA = "1" * 64
RENDER_1_SHA = "2" * 64
RENDER_2_SHA = "3" * 64


def _features(sha256: str, *, brightness: float, noise: float) -> AnalogFourPatchAudioFeatures:
    return AnalogFourPatchAudioFeatures(
        audio_sha256=sha256,
        duration=0.5,
        attack=0.1,
        decay=0.2,
        sustain=0.7,
        tail=0.2,
        brightness=brightness,
        spectral_flatness=0.2,
        noise=noise,
        low_end=0.6,
        harmonicity=0.8,
        transient=0.5,
        modulation=0.2,
    )


def test_pure_ranker_validates_inputs_and_breaks_ties_by_candidate(tmp_path: Path) -> None:
    from rytm_randomizer.style_analysis.analog_four_patch_render_rank import (
        AnalogFourRenderCandidateFeatures,
        rank_analog_four_render_features,
    )

    reference = _features(REFERENCE_SHA, brightness=0.5, noise=0.2)
    identical = _features(RENDER_1_SHA, brightness=0.5, noise=0.2)
    candidates = (
        AnalogFourRenderCandidateFeatures(2, "Second", tmp_path / "two.wav", identical),
        AnalogFourRenderCandidateFeatures(1, "First", tmp_path / "one.wav", identical),
    )

    ranked = rank_analog_four_render_features(reference, candidates)

    assert [score.candidate for score in ranked] == [1, 2]
    assert [score.rank for score in ranked] == [1, 2]
    assert ranked[0].render_path == (tmp_path / "one.wav").resolve()
    with pytest.raises(TypeError, match="AudioSynthesisFeatures"):
        rank_analog_four_render_features(object(), candidates)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="at least one measured"):
        rank_analog_four_render_features(reference, ())


@pytest.fixture
def _mocked_rank_inputs(monkeypatch: pytest.MonkeyPatch) -> None:
    from rytm_randomizer.cockpit.export import analog_four_patch_render_rank as ranker

    by_name = {
        "reference.wav": _features(REFERENCE_SHA, brightness=0.5, noise=0.2),
        "candidate-1.wav": _features(RENDER_1_SHA, brightness=0.5, noise=0.2),
        "candidate-2.wav": _features(RENDER_2_SHA, brightness=0.9, noise=0.8),
    }
    monkeypatch.setattr(
        ranker,
        "analyze_analog_four_patch_audio_isolated",
        lambda path: by_name[path.name],
    )

    def fake_load(_manifest_path: Path, *, candidate: int):
        return SimpleNamespace(
            generation_id="0123456789abcdef0123456789abcdef",
            audio_sha256=REFERENCE_SHA,
            plan=SimpleNamespace(
                selected_track=2,
                selected_label={1: "Closest reference", 2: "Brighter sync"}[candidate],
            ),
        )

    monkeypatch.setattr(ranker, "load_analog_four_patch_batch_candidate", fake_load)


def test_rank_hardware_renders_recommends_closest_measured_candidate(
    tmp_path: Path,
    _mocked_rank_inputs: None,
) -> None:
    from rytm_randomizer.cockpit.export.analog_four_patch_render_rank import (
        analog_four_patch_render_rank_to_dict,
        rank_analog_four_patch_renders,
    )

    packet = rank_analog_four_patch_renders(
        reference_audio_path=tmp_path / "reference.wav",
        manifest_path=tmp_path / "batch.json",
        render_paths={
            2: tmp_path / "candidate-2.wav",
            1: tmp_path / "candidate-1.wav",
        },
    )
    payload = analog_four_patch_render_rank_to_dict(packet)

    assert packet.version == "analog-four-render-rank-v1"
    assert packet.generation_id == "0123456789abcdef0123456789abcdef"
    assert packet.selected_track == 2
    assert packet.reference_sha256 == REFERENCE_SHA
    assert packet.render_count == 2
    assert packet.recommended_candidate == 1
    assert packet.recommended_label == "Closest reference"
    assert [score.candidate for score in packet.scores] == [1, 2]
    assert packet.scores[0].similarity == 100
    assert packet.scores[0].distance == 0.0
    assert packet.scores[1].similarity < packet.scores[0].similarity
    assert len(packet.scores[0].feature_deltas) == 11
    assert payload["recommended_candidate"] == 1
    assert payload["scores"][0]["render_sha256"] == RENDER_1_SHA
    assert payload["scores"][0]["feature_deltas"][0]["feature"] == "attack"
    assert "no MIDI sent" in payload["safety"]
    from rytm_randomizer.observability.metrics import get_metrics

    metrics = get_metrics()
    assert metrics.a4_patch_render_rank_count == 1
    assert not metrics.a4_patch_render_rank_errors_by_code


def test_rank_rejects_reference_that_is_not_the_batch_source(
    tmp_path: Path,
    _mocked_rank_inputs: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.cockpit.export import analog_four_patch_render_rank as ranker

    monkeypatch.setattr(
        ranker,
        "load_analog_four_patch_batch_candidate",
        lambda _path, *, candidate: SimpleNamespace(
            generation_id="generation",
            audio_sha256="f" * 64,
            plan=SimpleNamespace(
                selected_track=2,
                selected_label="Closest reference",
            ),
        ),
    )

    with pytest.raises(ValueError, match="reference audio SHA-256"):
        ranker.rank_analog_four_patch_renders(
            reference_audio_path=tmp_path / "reference.wav",
            manifest_path=tmp_path / "batch.json",
            render_paths={1: tmp_path / "candidate-1.wav"},
        )

    from rytm_randomizer.observability.metrics import get_metrics

    metrics = get_metrics()
    assert metrics.a4_patch_render_rank_count == 1
    assert metrics.a4_patch_render_rank_errors_by_code["reference_mismatch"] == 1


def test_rank_rejects_candidates_from_different_generations(
    tmp_path: Path,
    _mocked_rank_inputs: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.cockpit.export import analog_four_patch_render_rank as ranker

    monkeypatch.setattr(
        ranker,
        "load_analog_four_patch_batch_candidate",
        lambda _path, *, candidate: SimpleNamespace(
            generation_id=f"generation-{candidate}",
            audio_sha256=REFERENCE_SHA,
            plan=SimpleNamespace(
                selected_track=2,
                selected_label=f"Candidate {candidate}",
            ),
        ),
    )

    with pytest.raises(ValueError, match="one committed batch generation"):
        ranker.rank_analog_four_patch_renders(
            reference_audio_path=tmp_path / "reference.wav",
            manifest_path=tmp_path / "batch.json",
            render_paths={
                1: tmp_path / "candidate-1.wav",
                2: tmp_path / "candidate-2.wav",
            },
        )


def test_rank_wraps_manifest_reader_failures_as_artifact_errors(
    tmp_path: Path,
    _mocked_rank_inputs: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.cockpit.export import analog_four_patch_render_rank as ranker

    def fail_load(_path: Path, *, candidate: int) -> None:
        del candidate
        raise ValueError("invalid committed sidecar")

    monkeypatch.setattr(ranker, "load_analog_four_patch_batch_candidate", fail_load)

    with pytest.raises(
        ranker.AnalogFourPatchRenderRankArtifactError,
        match="invalid committed sidecar",
    ) as exc_info:
        ranker.rank_analog_four_patch_renders(
            reference_audio_path=tmp_path / "reference.wav",
            manifest_path=tmp_path / "batch.json",
            render_paths={1: tmp_path / "candidate-1.wav"},
        )

    assert isinstance(exc_info.value.__cause__, ValueError)


@pytest.mark.parametrize(
    ("kwargs", "expected"),
    [
        (
            {"reference_audio_path": "reference.wav"},
            "reference_audio_path must be a Path",
        ),
        ({"manifest_path": "batch.json"}, "manifest_path must be a Path"),
        ({"render_paths": []}, "render_paths must be a mapping"),
        ({"render_paths": {}}, "at least one candidate render"),
        ({"render_paths": {0: Path("bad.wav")}}, "candidate integers 1..4"),
        ({"render_paths": {1: "bad.wav"}}, "candidate integers 1..4"),
    ],
)
def test_rank_rejects_invalid_requests(
    tmp_path: Path,
    kwargs: dict[str, object],
    expected: str,
) -> None:
    from rytm_randomizer.cockpit.export.analog_four_patch_render_rank import (
        rank_analog_four_patch_renders,
    )

    arguments: dict[str, object] = {
        "reference_audio_path": tmp_path / "reference.wav",
        "manifest_path": tmp_path / "batch.json",
        "render_paths": {1: tmp_path / "candidate-1.wav"},
        **kwargs,
    }
    with pytest.raises((TypeError, ValueError), match=expected):
        rank_analog_four_patch_renders(**arguments)  # type: ignore[arg-type]


def test_render_rank_payload_rejects_wrong_type() -> None:
    from rytm_randomizer.cockpit.export.analog_four_patch_render_rank import (
        analog_four_patch_render_rank_to_dict,
    )

    with pytest.raises(TypeError, match="packet must be"):
        analog_four_patch_render_rank_to_dict(object())  # type: ignore[arg-type]


def test_render_rank_cli_parses_repeated_render_assignments() -> None:
    from rytm_randomizer.cockpit.export.analog_four_patch_render_rank_cli import (
        parse_analog_four_patch_render_rank_args,
    )

    parsed = parse_analog_four_patch_render_rank_args(
        [
            "--reference",
            "reference.wav",
            "--manifest",
            "batch.json",
            "--render",
            "1=render one.wav",
            "--render",
            "4=render-four.wav",
            "--json",
        ]
    )

    assert parsed == {
        "reference_audio_path": Path("reference.wav"),
        "manifest_path": Path("batch.json"),
        "render_paths": {1: Path("render one.wav"), 4: Path("render-four.wav")},
        "json_output": True,
    }


@pytest.mark.parametrize(
    ("args", "expected"),
    [
        ([], "--reference is required"),
        (["--reference", "r.wav"], "--manifest is required"),
        (["--reference", "r.wav", "--manifest", "m.json"], "at least one --render"),
        (["--reference"], "--reference requires a value"),
        (["--wat"], "unknown option"),
        (
            ["--reference", "r", "--manifest", "m", "--render", "bad"],
            "N=audio-path",
        ),
        (
            ["--reference", "r", "--manifest", "m", "--render", "x=a.wav"],
            "integer from 1 to 4",
        ),
        (
            ["--reference", "r", "--manifest", "m", "--render", "5=a.wav"],
            "integer from 1 to 4",
        ),
        (
            [
                "--reference",
                "r",
                "--manifest",
                "m",
                "--render",
                "1=a.wav",
                "--render",
                "1=b.wav",
            ],
            "provided more than once",
        ),
    ],
)
def test_render_rank_cli_rejects_invalid_args(args: list[str], expected: str) -> None:
    from rytm_randomizer.cockpit.export.analog_four_patch_render_rank_cli import (
        parse_analog_four_patch_render_rank_args,
    )

    with pytest.raises(ValueError, match=expected):
        parse_analog_four_patch_render_rank_args(args)


def test_render_rank_cli_registry_adapters() -> None:
    from rytm_randomizer.cockpit.export import analog_four_patch_render_rank_cli as cli

    assert cli._parse_render_rank_args_for_registry(
        [
            "--reference",
            "r.wav",
            "--manifest",
            "m.json",
            "--render",
            "1=c.wav",
        ]
    )["render_paths"] == {1: Path("c.wav")}
    assert "Error: bad" in cli._format_render_rank_cli_error(ValueError("bad"))


def test_render_rank_registry_reraises_non_json_parse_failure() -> None:
    from rytm_randomizer.cockpit.export import analog_four_patch_render_rank_cli as cli

    with pytest.raises(ValueError, match="--reference is required"):
        cli._parse_render_rank_args_for_registry(())


def test_render_rank_registry_emits_json_for_parse_failure(
    capsys: pytest.CaptureFixture[str],
) -> None:
    from rytm_randomizer import cli

    exit_code = cli.main(
        [
            "analog-four-audio-patch-rank",
            "--reference",
            "reference.wav",
            "--json",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 2
    payload = json.loads(captured.out)
    assert payload["ok"] is False
    assert payload["error"] == "--manifest is required"
    assert payload["error_code"] == "validation"
    assert captured.err == ""


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (ValueError("bad artifact"), "validation"),
        (OSError("unreadable"), "input_read_failed"),
        (RuntimeError("unexpected"), "rank_failed"),
    ],
)
def test_render_rank_service_classifies_generic_errors(error: Exception, expected: str) -> None:
    from rytm_randomizer.cockpit.export.analog_four_patch_render_rank import (
        analog_four_patch_render_rank_error_code,
    )

    assert analog_four_patch_render_rank_error_code(error) == expected


def test_render_rank_service_classifies_domain_errors() -> None:
    from rytm_randomizer.cockpit.export.analog_four_patch_render_rank import (
        AnalogFourPatchRenderRankArtifactError,
        AnalogFourPatchRenderRankReferenceError,
        analog_four_patch_render_rank_error_code,
    )
    from rytm_randomizer.observability.errors import BoundaryError
    from rytm_randomizer.style_analysis.extractor import StyleAnalysisDependencyError

    assert (
        analog_four_patch_render_rank_error_code(
            AnalogFourPatchRenderRankArtifactError("bad artifact")
        )
        == "artifact_validation"
    )
    assert (
        analog_four_patch_render_rank_error_code(
            AnalogFourPatchRenderRankReferenceError("wrong source")
        )
        == "reference_mismatch"
    )
    assert (
        analog_four_patch_render_rank_error_code(StyleAnalysisDependencyError("missing"))
        == "dependency_missing"
    )
    assert analog_four_patch_render_rank_error_code(BoundaryError("native crash")) == "rank_failed"
    assert (
        analog_four_patch_render_rank_error_code(
            BoundaryError("read failed", context={"error_code": "audio_read_failed"})
        )
        == "input_read_failed"
    )
    assert (
        analog_four_patch_render_rank_error_code(
            BoundaryError("cancelled", context={"error_code": "interrupted"})
        )
        == "interrupted"
    )
    assert analog_four_patch_render_rank_error_code(KeyboardInterrupt()) == "interrupted"


def test_render_rank_service_records_interrupt_and_trace_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.cockpit.export import analog_four_patch_render_rank as ranker
    from rytm_randomizer.observability.logging import configure_logging
    from rytm_randomizer.observability.metrics import get_metrics

    log_stream = io.StringIO()
    configure_logging(stream=log_stream)
    monkeypatch.setattr(
        ranker,
        "_rank_analog_four_patch_renders",
        lambda **_kwargs: (_ for _ in ()).throw(KeyboardInterrupt()),
    )

    with pytest.raises(KeyboardInterrupt):
        ranker.rank_analog_four_patch_renders(
            reference_audio_path=tmp_path / "reference.wav",
            manifest_path=tmp_path / "batch.json",
            render_paths={1: tmp_path / "candidate-1.wav"},
        )

    metrics = get_metrics()
    assert metrics.a4_patch_render_rank_count == 1
    assert metrics.a4_patch_render_rank_errors_by_code["interrupted"] == 1
    assert "operation_error a4_patch_render_rank" in log_stream.getvalue()


def test_render_rank_preserves_native_analysis_failure_fingerprint(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.cockpit.export import analog_four_patch_render_rank as ranker
    from rytm_randomizer.observability.errors import BoundaryError

    failure = BoundaryError(
        "native analysis failed",
        context={
            "error_code": "inference_failed",
            "fingerprint": "a4.audio_patch.native_analysis_failed",
        },
    )
    logged: list[dict[str, object]] = []
    monkeypatch.setattr(
        ranker,
        "_rank_analog_four_patch_renders",
        lambda **_kwargs: (_ for _ in ()).throw(failure),
    )
    monkeypatch.setattr(
        ranker._logger,
        "warning",
        lambda _message, *, extra: logged.append(extra),
    )

    with pytest.raises(BoundaryError, match="native analysis failed"):
        ranker.rank_analog_four_patch_renders(
            reference_audio_path=tmp_path / "reference.wav",
            manifest_path=tmp_path / "batch.json",
            render_paths={1: tmp_path / "candidate-1.wav"},
        )

    assert logged[0]["fingerprint"] == "a4.audio_patch.native_analysis_failed"
    assert logged[0]["error_code"] == "rank_failed"


def test_render_rank_cli_outputs_text_and_json(
    tmp_path: Path,
    _mocked_rank_inputs: None,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from rytm_randomizer.cockpit.export.analog_four_patch_render_rank_cli import (
        handle_analog_four_patch_render_rank,
    )

    arguments = {
        "reference_audio_path": tmp_path / "reference.wav",
        "manifest_path": tmp_path / "batch.json",
        "render_paths": {1: tmp_path / "candidate-1.wav"},
    }
    assert handle_analog_four_patch_render_rank(**arguments) == 0
    text_output = capsys.readouterr()
    assert "recommended_candidate: 1" in text_output.out
    assert "similarity=100" in text_output.out
    assert text_output.err == ""

    assert handle_analog_four_patch_render_rank(**arguments, json_output=True) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert payload["recommended_candidate"] == 1
    from rytm_randomizer.observability.metrics import get_metrics

    assert get_metrics().a4_patch_render_rank_count == 2


@pytest.mark.parametrize("json_output", [False, True])
def test_render_rank_cli_reports_service_errors(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    json_output: bool,
) -> None:
    from rytm_randomizer.cockpit.export import analog_four_patch_render_rank_cli as cli

    monkeypatch.setattr(cli, "_rank", lambda **_kwargs: (_ for _ in ()).throw(ValueError("bad")))
    exit_code = cli.handle_analog_four_patch_render_rank(
        reference_audio_path=tmp_path / "reference.wav",
        manifest_path=tmp_path / "batch.json",
        render_paths={1: tmp_path / "candidate.wav"},
        json_output=json_output,
    )
    captured = capsys.readouterr()

    assert exit_code == 2
    if json_output:
        payload = json.loads(captured.out)
        assert payload["error"] == "bad"
        assert payload["error_code"] == "validation"
        assert captured.err == ""
    else:
        assert "Error: bad" in captured.err
        assert captured.out == ""


def test_render_rank_cli_reports_native_boundary_error(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.cockpit.export import analog_four_patch_render_rank_cli as cli
    from rytm_randomizer.observability.errors import BoundaryError

    monkeypatch.setattr(
        cli,
        "_rank",
        lambda **_kwargs: (_ for _ in ()).throw(BoundaryError("native crash")),
    )

    assert (
        cli.handle_analog_four_patch_render_rank(
            reference_audio_path=tmp_path / "reference.wav",
            manifest_path=tmp_path / "batch.json",
            render_paths={1: tmp_path / "candidate.wav"},
            json_output=True,
        )
        == 2
    )
    payload = json.loads(capsys.readouterr().out)
    assert payload["error_code"] == "rank_failed"


@pytest.mark.parametrize("interruption", [KeyboardInterrupt(), SystemExit(7)])
def test_render_rank_cli_returns_structured_interrupted_response(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    interruption: BaseException,
) -> None:
    from rytm_randomizer.cockpit.export import analog_four_patch_render_rank_cli as cli

    monkeypatch.setattr(
        cli,
        "_rank",
        lambda **_kwargs: (_ for _ in ()).throw(interruption),
    )

    exit_code = cli.handle_analog_four_patch_render_rank(
        reference_audio_path=tmp_path / "reference.wav",
        manifest_path=tmp_path / "batch.json",
        render_paths={1: tmp_path / "candidate.wav"},
        json_output=True,
    )

    assert exit_code == 130
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is False
    assert payload["error_code"] == "interrupted"
