"""Tests for passive bounded Analog Four render-feedback refinement."""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from rytm_randomizer.style_analysis.analog_four_patch_render_rank import (
    AnalogFourPatchRenderScore,
)
from rytm_randomizer.style_analysis.extractor import (
    AudioFeatureAnalysis,
    AudioSynthesisFeatures,
)

pytestmark = [pytest.mark.fast, pytest.mark.usefixtures("isolated_observability")]


def _render_score(
    reference: AudioSynthesisFeatures,
    rendered: AudioSynthesisFeatures,
) -> AnalogFourPatchRenderScore:
    from rytm_randomizer.style_analysis.analog_four_patch_render_rank import (
        AnalogFourRenderCandidateFeatures,
        rank_analog_four_render_features,
    )

    return rank_analog_four_render_features(
        reference,
        (
            AnalogFourRenderCandidateFeatures(
                candidate=2,
                label="Darker",
                render_path=Path("render.wav"),
                features=rendered,
            ),
        ),
    )[0]


def test_refinement_accepts_an_acoustically_matching_render(
    audio_patch_dna_analysis: AudioFeatureAnalysis,
) -> None:
    from rytm_randomizer.style_analysis.analog_four_patch_refinement import (
        plan_analog_four_patch_refinement,
    )

    reference = audio_patch_dna_analysis.synthesis_features
    rendered = replace(reference, audio_sha256="c" * 64)
    plan = plan_analog_four_patch_refinement(
        audio_patch_dna_analysis,
        _render_score(reference, rendered),
        rendered,
        track=1,
    )

    assert plan.action == "accept"
    assert plan.similarity == 100
    assert plan.next_candidate is None
    assert plan.corrected_features == reference
    assert plan.corrected_features.duration == reference.duration


def test_refinement_compensates_one_measured_error_deterministically(
    audio_patch_dna_analysis: AudioFeatureAnalysis,
) -> None:
    from rytm_randomizer.style_analysis.analog_four_patch_refinement import (
        analog_four_patch_refinement_plan_to_dict,
        plan_analog_four_patch_refinement,
    )

    reference = audio_patch_dna_analysis.synthesis_features
    rendered = replace(reference, audio_sha256="d" * 64, brightness=0.35)
    score = _render_score(reference, rendered)
    first = plan_analog_four_patch_refinement(
        audio_patch_dna_analysis,
        score,
        rendered,
        track=3,
        correction_gain=0.5,
        accept_similarity=100,
    )
    second = plan_analog_four_patch_refinement(
        audio_patch_dna_analysis,
        score,
        rendered,
        track=3,
        correction_gain=0.5,
        accept_similarity=100,
    )

    brightness = next(row for row in first.residuals if row.feature == "brightness")
    assert first.action == "refine"
    assert first.next_candidate is not None
    assert first.next_candidate.genome.candidate_count == 1
    assert first.selected_track == 3
    assert brightness.signed_error == pytest.approx(0.2)
    assert brightness.correction == pytest.approx(0.1)
    assert brightness.corrected_target == pytest.approx(0.65)
    assert first.corrected_features.brightness == pytest.approx(0.65)
    assert first.corrected_features.duration == reference.duration
    assert analog_four_patch_refinement_plan_to_dict(
        first
    ) == analog_four_patch_refinement_plan_to_dict(second)


def test_refinement_clamps_compensated_targets_to_normalized_domain(
    audio_patch_dna_analysis: AudioFeatureAnalysis,
) -> None:
    from rytm_randomizer.style_analysis.analog_four_patch_refinement import (
        plan_analog_four_patch_refinement,
    )

    reference = replace(
        audio_patch_dna_analysis.synthesis_features,
        brightness=0.9,
    )
    analysis = replace(audio_patch_dna_analysis, synthesis_features=reference)
    rendered = replace(reference, audio_sha256="e" * 64, brightness=0.0)
    plan = plan_analog_four_patch_refinement(
        analysis,
        _render_score(reference, rendered),
        rendered,
        track=1,
        correction_gain=1.0,
        accept_similarity=100,
    )

    brightness = next(row for row in plan.residuals if row.feature == "brightness")
    assert brightness.corrected_target == 1.0
    assert brightness.clamped is True
    assert plan.corrected_features.brightness == 1.0


@pytest.mark.parametrize(
    ("field", "value", "error_type", "message"),
    [
        ("reference", object(), TypeError, "reference_analysis"),
        ("score", object(), TypeError, "render_score"),
        ("rendered", object(), TypeError, "render_features"),
        ("track", True, TypeError, "track must be an integer"),
        ("track", 5, ValueError, "track must be between"),
        ("gain", True, TypeError, "correction_gain must be a float"),
        ("gain", -0.1, ValueError, "between 0.0 and 1.0"),
        ("gain", float("inf"), ValueError, "finite"),
        ("threshold", True, TypeError, "accept_similarity must be an integer"),
        ("threshold", 101, ValueError, "between 0 and 100"),
    ],
)
def test_refinement_rejects_invalid_inputs(
    audio_patch_dna_analysis: AudioFeatureAnalysis,
    field: str,
    value: object,
    error_type: type[Exception],
    message: str,
) -> None:
    from rytm_randomizer.style_analysis.analog_four_patch_refinement import (
        plan_analog_four_patch_refinement,
    )

    reference = audio_patch_dna_analysis.synthesis_features
    rendered = replace(reference, audio_sha256="f" * 64)
    arguments: dict[str, object] = {
        "reference_analysis": audio_patch_dna_analysis,
        "render_score": _render_score(reference, rendered),
        "render_features": rendered,
        "track": 1,
        "correction_gain": 0.65,
        "accept_similarity": 92,
    }
    names = {
        "reference": "reference_analysis",
        "score": "render_score",
        "rendered": "render_features",
        "track": "track",
        "gain": "correction_gain",
        "threshold": "accept_similarity",
    }
    arguments[names[field]] = value

    with pytest.raises(error_type, match=message):
        plan_analog_four_patch_refinement(**arguments)  # type: ignore[arg-type]


def test_refinement_rejects_render_hash_mismatch(
    audio_patch_dna_analysis: AudioFeatureAnalysis,
) -> None:
    from rytm_randomizer.style_analysis.analog_four_patch_refinement import (
        plan_analog_four_patch_refinement,
    )

    reference = audio_patch_dna_analysis.synthesis_features
    rendered = replace(reference, audio_sha256="1" * 64)
    score = _render_score(reference, rendered)

    with pytest.raises(ValueError, match="hashes must match"):
        plan_analog_four_patch_refinement(
            audio_patch_dna_analysis,
            score,
            replace(rendered, audio_sha256="2" * 64),
            track=1,
        )


@dataclass(frozen=True)
class _FakeStoredPlan:
    selected_candidate: int = 2
    selected_label: str = "Darker"
    selected_track: int = 1


@dataclass(frozen=True)
class _FakeSelection:
    generation_id: str
    manifest_path: Path
    audio_sha256: str
    plan: _FakeStoredPlan = _FakeStoredPlan()


def _patch_refinement_inputs(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    analysis: AudioFeatureAnalysis,
    rendered: AudioSynthesisFeatures,
) -> None:
    from rytm_randomizer.cockpit.export import analog_four_patch_refinement as service

    monkeypatch.setattr(
        service,
        "_load_selection",
        lambda _path, *, candidate: _FakeSelection(
            generation_id=f"generation-{candidate}",
            manifest_path=(tmp_path / "batch.json").resolve(),
            audio_sha256=analysis.synthesis_features.audio_sha256,
        ),
    )
    monkeypatch.setattr(
        service,
        "analyze_analog_four_patch_audio_analysis_isolated",
        lambda _path: analysis,
    )
    monkeypatch.setattr(
        service,
        "analyze_analog_four_patch_audio_isolated",
        lambda _path: rendered,
    )


def test_refinement_service_writes_deterministic_passive_artifacts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    audio_patch_dna_analysis: AudioFeatureAnalysis,
) -> None:
    from rytm_randomizer.cockpit.export import analog_four_patch_refinement as service

    reference = audio_patch_dna_analysis.synthesis_features
    rendered = replace(reference, audio_sha256="3" * 64, brightness=0.30)
    _patch_refinement_inputs(
        monkeypatch,
        tmp_path,
        audio_patch_dna_analysis,
        rendered,
    )
    output_dir = tmp_path / "refinement"
    arguments = {
        "reference_audio_path": tmp_path / "reference.wav",
        "manifest_path": tmp_path / "batch.json",
        "candidate": 2,
        "render_audio_path": tmp_path / "render.wav",
        "output_dir": output_dir,
        "accept_similarity": 100,
    }

    first = service.export_analog_four_patch_refinement(**arguments)
    first_json = first.json_path.read_bytes()
    first_markdown = first.markdown_path.read_bytes()
    second = service.export_analog_four_patch_refinement(
        **arguments,
        overwrite=True,
    )

    payload = json.loads(first_json)
    assert payload["plan"]["action"] == "refine"
    assert payload["next_export"] is None
    assert payload["selection"]["candidate"] == 2
    assert payload["render_audio"]["sha256"] == "3" * 64
    assert "no MIDI ports enumerated or opened" in payload["safety"]
    assert b"# Analog Four Patch Refinement" in first_markdown
    assert second.json_path.read_bytes() == first_json
    assert second.markdown_path.read_bytes() == first_markdown


def test_refinement_service_rejects_reference_audio_mismatch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    audio_patch_dna_analysis: AudioFeatureAnalysis,
) -> None:
    from rytm_randomizer.cockpit.export import analog_four_patch_refinement as service

    reference = audio_patch_dna_analysis.synthesis_features
    rendered = replace(reference, audio_sha256="4" * 64)
    _patch_refinement_inputs(
        monkeypatch,
        tmp_path,
        audio_patch_dna_analysis,
        rendered,
    )
    monkeypatch.setattr(
        service,
        "_load_selection",
        lambda _path, *, candidate: _FakeSelection(
            generation_id=f"generation-{candidate}",
            manifest_path=tmp_path / "batch.json",
            audio_sha256="9" * 64,
        ),
    )

    with pytest.raises(service.AnalogFourPatchRenderRankReferenceError):
        service.export_analog_four_patch_refinement(
            reference_audio_path=tmp_path / "reference.wav",
            manifest_path=tmp_path / "batch.json",
            candidate=2,
            render_audio_path=tmp_path / "render.wav",
            output_dir=tmp_path / "out",
        )


def test_refinement_selection_wraps_artifact_errors(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.cockpit.export import analog_four_patch_refinement as service

    monkeypatch.setattr(
        service,
        "load_analog_four_patch_batch_candidate",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(ValueError("bad batch")),
    )

    with pytest.raises(service.AnalogFourPatchRenderRankArtifactError, match="bad batch"):
        service._load_selection(tmp_path / "batch.json", candidate=2)


def test_refinement_cli_parses_full_and_default_requests() -> None:
    from rytm_randomizer.cockpit.export.analog_four_patch_refinement_cli import (
        parse_analog_four_patch_refinement_args,
    )

    required = [
        "--reference",
        "reference.wav",
        "--manifest",
        "batch.json",
        "--candidate",
        "2",
        "--render",
        "render.wav",
        "--output-dir",
        "out",
    ]
    defaults = parse_analog_four_patch_refinement_args(required)
    full = parse_analog_four_patch_refinement_args(
        [
            *required,
            "--gain",
            "0.5",
            "--accept-similarity",
            "95",
            "--source-kit",
            "source.syx",
            "--overwrite",
            "--json",
        ]
    )

    assert defaults["correction_gain"] == 0.65
    assert defaults["accept_similarity"] == 92
    assert defaults["source_kit_path"] is None
    assert full["correction_gain"] == 0.5
    assert full["accept_similarity"] == 95
    assert full["source_kit_path"] == Path("source.syx")
    assert full["overwrite"] is True
    assert full["json_output"] is True


@pytest.mark.parametrize(
    ("args", "message"),
    [
        ([], "--reference is required"),
        (["--reference", "r"], "--manifest is required"),
        (["--reference", "r", "--manifest", "m"], "--candidate is required"),
        (
            ["--reference", "r", "--manifest", "m", "--candidate", "2"],
            "--render is required",
        ),
        (
            [
                "--reference",
                "r",
                "--manifest",
                "m",
                "--candidate",
                "2",
                "--render",
                "render.wav",
            ],
            "--output-dir is required",
        ),
        (["--reference"], "--reference requires a value"),
        (["--wat"], "unknown option"),
        (["--gain", "nan"], "0.0 to 1.0"),
        (["--gain", "bad"], "0.0 to 1.0"),
        (["--candidate", "5"], "integer from 1 to 4"),
        (["--accept-similarity", "101"], "integer from 0 to 100"),
    ],
)
def test_refinement_cli_rejects_invalid_args(
    args: list[str],
    message: str,
) -> None:
    from rytm_randomizer.cockpit.export.analog_four_patch_refinement_cli import (
        parse_analog_four_patch_refinement_args,
    )

    with pytest.raises(ValueError, match=message):
        parse_analog_four_patch_refinement_args(args)


def test_refinement_registry_emits_json_for_parse_failure(
    capsys: pytest.CaptureFixture[str],
) -> None:
    from rytm_randomizer import cli

    exit_code = cli.main(
        [
            "analog-four-audio-patch-refine",
            "--reference",
            "reference.wav",
            "--json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 2
    assert payload["ok"] is False
    assert payload["error"] == "--manifest is required"
    assert payload["error_code"] == "validation"


def test_refinement_registry_parser_preserves_success_and_plain_failure() -> None:
    from rytm_randomizer.cockpit.export.analog_four_patch_refinement_cli import (
        _parse_refinement_args_for_registry,
    )

    with pytest.raises(ValueError, match="--manifest is required"):
        _parse_refinement_args_for_registry(["--reference", "reference.wav"])

    parsed = _parse_refinement_args_for_registry(
        [
            "--reference",
            "reference.wav",
            "--manifest",
            "batch.json",
            "--candidate",
            "2",
            "--render",
            "render.wav",
            "--output-dir",
            "out",
        ]
    )

    assert parsed["parse_error"] is None


def test_refinement_cli_outputs_text_and_json(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    audio_patch_dna_analysis: AudioFeatureAnalysis,
) -> None:
    from rytm_randomizer.cockpit.export import analog_four_patch_refinement as service
    from rytm_randomizer.cockpit.export import analog_four_patch_refinement_cli as cli

    reference = audio_patch_dna_analysis.synthesis_features
    rendered = replace(reference, audio_sha256="5" * 64)
    _patch_refinement_inputs(
        monkeypatch,
        tmp_path,
        audio_patch_dna_analysis,
        rendered,
    )
    result = service.export_analog_four_patch_refinement(
        reference_audio_path=tmp_path / "reference.wav",
        manifest_path=tmp_path / "batch.json",
        candidate=2,
        render_audio_path=tmp_path / "render.wav",
        output_dir=tmp_path / "out",
    )
    monkeypatch.setattr(cli, "_refine", lambda **_kwargs: result)
    arguments = {
        "reference_audio_path": tmp_path / "reference.wav",
        "manifest_path": tmp_path / "batch.json",
        "candidate": 2,
        "render_audio_path": tmp_path / "render.wav",
        "output_dir": tmp_path / "unused",
    }

    assert cli.handle_analog_four_patch_refinement(**arguments) == 0
    text_output = capsys.readouterr()
    assert "action: accept" in text_output.out
    assert "next_export: none" in text_output.out
    assert text_output.err == ""

    assert cli.handle_analog_four_patch_refinement(**arguments, json_output=True) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert payload["plan"]["action"] == "accept"


def test_refinement_cli_lazy_dispatches_to_service(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.cockpit.export import analog_four_patch_refinement as service
    from rytm_randomizer.cockpit.export import analog_four_patch_refinement_cli as cli

    expected = object()
    calls: list[dict[str, object]] = []

    def fake_export(**kwargs: object) -> object:
        calls.append(kwargs)
        return expected

    monkeypatch.setattr(service, "export_analog_four_patch_refinement", fake_export)

    result = cli._refine(
        reference_audio_path=tmp_path / "reference.wav",
        manifest_path=tmp_path / "batch.json",
        candidate=2,
        render_audio_path=tmp_path / "render.wav",
        output_dir=tmp_path / "out",
        correction_gain=0.5,
        accept_similarity=95,
        source_kit_path=tmp_path / "source.syx",
        overwrite=True,
    )

    assert result is expected
    assert calls == [
        {
            "reference_audio_path": tmp_path / "reference.wav",
            "manifest_path": tmp_path / "batch.json",
            "candidate": 2,
            "render_audio_path": tmp_path / "render.wav",
            "output_dir": tmp_path / "out",
            "correction_gain": 0.5,
            "accept_similarity": 95,
            "source_kit_path": tmp_path / "source.syx",
            "overwrite": True,
        }
    ]


def test_refinement_cli_formats_optional_export_and_plain_error(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from rytm_randomizer.cockpit.export import analog_four_patch_refinement_cli as cli

    result = SimpleNamespace(
        payload={
            "selection": {"candidate": 2, "label": "Darker", "track": 1},
            "plan": {"action": "refine", "similarity": 80, "accept_similarity": 92},
            "next_export": {
                "sysex_path": str(tmp_path / "next.syx"),
                "sidecar_path": str(tmp_path / "next.json"),
            },
            "safety": ["offline only"],
        },
        json_path=tmp_path / "refinement.json",
        markdown_path=tmp_path / "refinement.md",
    )

    output = cli._format_refinement_text(result)
    assert f"next_sysex_path: {tmp_path / 'next.syx'}" in output
    assert f"next_sidecar_path: {tmp_path / 'next.json'}" in output

    assert cli._report_refinement_error(ValueError("bad request"), json_output=False) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "Error [validation]: bad request" in captured.err
    assert cli._format_refinement_cli_error(ValueError("bad request")).endswith(
        "Error [validation]: bad request"
    )


@pytest.mark.parametrize(
    ("failure", "exit_code", "error_code"),
    [
        (ValueError("bad"), 2, "validation"),
        (OSError("unreadable"), 2, "input_read_failed"),
        (KeyboardInterrupt(), 130, "interrupted"),
    ],
)
def test_refinement_cli_reports_failures(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    failure: BaseException,
    exit_code: int,
    error_code: str,
) -> None:
    from rytm_randomizer.cockpit.export import analog_four_patch_refinement_cli as cli

    monkeypatch.setattr(
        cli,
        "_refine",
        lambda **_kwargs: (_ for _ in ()).throw(failure),
    )

    assert (
        cli.handle_analog_four_patch_refinement(
            reference_audio_path=tmp_path / "reference.wav",
            manifest_path=tmp_path / "batch.json",
            candidate=2,
            render_audio_path=tmp_path / "render.wav",
            output_dir=tmp_path / "out",
            json_output=True,
        )
        == exit_code
    )
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is False
    assert payload["error_code"] == error_code


def test_refinement_optional_export_requires_a_next_candidate(
    audio_patch_dna_analysis: AudioFeatureAnalysis,
) -> None:
    from rytm_randomizer.cockpit.export import analog_four_patch_refinement as service
    from rytm_randomizer.style_analysis.analog_four_patch_refinement import (
        plan_analog_four_patch_refinement,
    )

    reference = audio_patch_dna_analysis.synthesis_features
    rendered = replace(reference, audio_sha256="6" * 64, brightness=0.0)
    plan = plan_analog_four_patch_refinement(
        audio_patch_dna_analysis,
        _render_score(reference, rendered),
        rendered,
        track=1,
        accept_similarity=100,
    )

    with pytest.raises(
        service.AnalogFourPatchRenderRankArtifactError,
        match="missing its inferred next candidate",
    ):
        service._export_next_candidate(
            plan=replace(plan, next_candidate=None),
            reference_path=Path("reference.wav"),
            source_kit_path=Path("source.syx"),
            output_dir=Path("out"),
            overwrite=False,
        )


def test_refinement_optional_export_and_payload_use_existing_batch_exporter(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    audio_patch_dna_analysis: AudioFeatureAnalysis,
) -> None:
    from rytm_randomizer.cockpit.export import analog_four_patch_refinement as service
    from rytm_randomizer.style_analysis.analog_four_patch_refinement import (
        plan_analog_four_patch_refinement,
    )

    reference = audio_patch_dna_analysis.synthesis_features
    rendered = replace(reference, audio_sha256="7" * 64, brightness=0.0)
    plan = plan_analog_four_patch_refinement(
        audio_patch_dna_analysis,
        _render_score(reference, rendered),
        rendered,
        track=1,
        accept_similarity=100,
    )
    candidate = SimpleNamespace(
        sysex_path=tmp_path / "next.syx",
        sidecar_path=tmp_path / "next.json",
    )
    expected = SimpleNamespace(
        generation_id="next-generation",
        manifest_path=tmp_path / "manifest.json",
        manifest_sha256="8" * 64,
        candidates=(candidate,),
        safety=("offline only",),
    )
    calls: list[dict[str, object]] = []

    def fake_export(**kwargs: object) -> object:
        calls.append(kwargs)
        return expected

    monkeypatch.setattr(service, "export_selected_analog_four_audio_patch", fake_export)

    result = service._export_next_candidate(
        plan=plan,
        reference_path=tmp_path / "reference.wav",
        source_kit_path=tmp_path / "source.syx",
        output_dir=tmp_path / "out",
        overwrite=True,
    )

    assert result is expected
    assert calls[0]["audio_genome"] == plan.next_candidate
    assert calls[0]["output_dir"] == tmp_path / "out" / "refined-a4"
    assert service._next_export_payload(result) == {
        "generation_id": "next-generation",
        "manifest_path": str(tmp_path / "manifest.json"),
        "manifest_sha256": "8" * 64,
        "sysex_path": str(tmp_path / "next.syx"),
        "sidecar_path": str(tmp_path / "next.json"),
        "safety": ["offline only"],
    }
