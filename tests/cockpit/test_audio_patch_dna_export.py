"""Tests for the passive Audio-to-Patch DNA export service."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import cast

import pytest

from rytm_randomizer.cockpit.export import audio_patch_dna as service
from rytm_randomizer.guardrails.schema import Confidence, SourceType
from rytm_randomizer.style_analysis import (
    AudioDnaEvidence,
    AudioFeatureAnalysis,
    AudioSynthesisFeatures,
    FeatureReport,
    build_audio_patch_dna_workspace,
)
from rytm_randomizer.style_analysis.analog_four_patch_inference import (
    AnalogFourAudioPatchGenome,
)

pytestmark = pytest.mark.fast


def _analysis() -> AudioFeatureAnalysis:
    return AudioFeatureAnalysis(
        feature_report=FeatureReport(
            source_type=SourceType.SINGLE_TRACK,
            confidence=Confidence.HIGH,
            bpm=138.0,
            tempo_stability=0.92,
            kick_density=0.31,
            percussion_density=0.48,
            low_end_weight=0.61,
            spectral_brightness=0.57,
            texture_noise=0.23,
            energy_arc=(0.2, 0.4, 0.7, 0.6),
            content_hash="placeholder",
            derived_at="2026-08-09T00:00:00Z",
        ),
        synthesis_features=AudioSynthesisFeatures(
            audio_sha256="b" * 64,
            duration=0.40,
            attack=0.18,
            decay=0.42,
            sustain=0.38,
            tail=0.36,
            brightness=0.55,
            spectral_flatness=0.20,
            noise=0.24,
            low_end=0.58,
            harmonicity=0.68,
            transient=0.62,
            modulation=0.27,
        ),
        dna_evidence=AudioDnaEvidence(
            dominant_frequency_hz=87.31,
            dominant_note="F2",
            pitch_confidence=0.81,
            tonal_stability=0.72,
            spectral_movement=0.19,
        ),
    )


@dataclass(frozen=True)
class _FakeA4Candidate:
    sysex_path: Path
    sidecar_path: Path


@dataclass(frozen=True)
class _FakeA4Export:
    generation_id: str
    manifest_path: Path
    manifest_sha256: str
    candidates: tuple[_FakeA4Candidate, ...]
    safety: tuple[str, ...]


def _fake_a4_export(output_dir: Path) -> _FakeA4Export:
    return _FakeA4Export(
        generation_id="generation-123",
        manifest_path=output_dir / "manifest.json",
        manifest_sha256="c" * 64,
        candidates=(
            _FakeA4Candidate(
                sysex_path=output_dir / "candidate.syx",
                sidecar_path=output_dir / "candidate.json",
            ),
        ),
        safety=("passive export",),
    )


def test_compare_only_analyzes_once_and_writes_exactly_eight_directions(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    audio_path = tmp_path / "reference.wav"
    output_dir = tmp_path / "dna"
    analyzed: list[Path] = []

    def fake_analyze(path: Path) -> AudioFeatureAnalysis:
        analyzed.append(path)
        return _analysis()

    def unexpected_export(**_kwargs: object) -> None:
        pytest.fail("compare-only mode must not invoke the A4 exporter")

    monkeypatch.setattr(service, "analyze_analog_four_patch_audio_analysis_isolated", fake_analyze)
    monkeypatch.setattr(service, "export_selected_analog_four_audio_patch", unexpected_export)

    result = service.export_audio_patch_dna_workspace(
        audio_path=audio_path,
        output_dir=output_dir,
        track=2,
    )

    payload = json.loads(result.json_path.read_text(encoding="utf-8"))
    markdown = result.markdown_path.read_text(encoding="utf-8")
    assert analyzed == [audio_path]
    assert len(result.workspace.candidates) == 8
    assert payload["workspace"]["candidate_count"] == 8
    assert "selected_candidate" not in payload
    assert "selected_a4" not in payload
    assert "| 8 | Animated |" in markdown
    assert "## Selected Direction" not in markdown
    assert result.selected_candidate is None
    assert result.analog_four_export is None


def test_compare_only_outputs_are_deterministic_for_the_same_destination(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        service,
        "analyze_analog_four_patch_audio_analysis_isolated",
        lambda _path: _analysis(),
    )
    output_dir = tmp_path / "dna"

    first = service.export_audio_patch_dna_workspace(
        audio_path=tmp_path / "reference.wav",
        output_dir=output_dir,
    )
    first_json = first.json_path.read_bytes()
    first_markdown = first.markdown_path.read_bytes()
    second = service.export_audio_patch_dna_workspace(
        audio_path=tmp_path / "reference.wav",
        output_dir=output_dir,
        overwrite=True,
    )

    assert second.json_path.read_bytes() == first_json
    assert second.markdown_path.read_bytes() == first_markdown


def test_selected_direction_exports_only_one_precomputed_a4_candidate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    audio_path = tmp_path / "reference.wav"
    source_kit_path = tmp_path / "source.syx"
    output_dir = tmp_path / "dna"
    analyzed: list[Path] = []
    export_calls: list[dict[str, object]] = []

    def fake_analyze(path: Path) -> AudioFeatureAnalysis:
        analyzed.append(path)
        return _analysis()

    def fake_export(**kwargs: object) -> _FakeA4Export:
        export_calls.append(kwargs)
        export_dir = kwargs["output_dir"]
        assert isinstance(export_dir, Path)
        return _fake_a4_export(export_dir)

    monkeypatch.setattr(service, "analyze_analog_four_patch_audio_analysis_isolated", fake_analyze)
    monkeypatch.setattr(service, "export_selected_analog_four_audio_patch", fake_export)

    result = service.export_audio_patch_dna_workspace(
        audio_path=audio_path,
        output_dir=output_dir,
        track=3,
        selection=6,
        source_kit_path=source_kit_path,
    )

    assert analyzed == [audio_path]
    assert len(export_calls) == 1
    call = export_calls[0]
    assert call["audio_path"] == audio_path
    assert call["source_kit_path"] == source_kit_path
    assert call["output_dir"] == output_dir / "selected-a4"
    audio_genome = cast(AnalogFourAudioPatchGenome, call["audio_genome"])
    assert audio_genome.genome.candidate_count == 1
    assert audio_genome.genome.candidates[0].label == "Atmospheric"

    payload = json.loads(result.json_path.read_text(encoding="utf-8"))
    markdown = result.markdown_path.read_text(encoding="utf-8")
    assert payload["selected_candidate"]["column"] == 6
    assert payload["selected_candidate"]["label"] == "Atmospheric"
    assert payload["selected_a4"]["generation_id"] == "generation-123"
    assert payload["selected_a4"]["safety"] == ["passive export"]
    assert "## Selected Direction" in markdown
    assert "Candidate: 6. Atmospheric" in markdown
    assert "A4 SysEx:" in markdown


@pytest.mark.parametrize(
    ("selection", "source_kit_path", "error_type", "message"),
    [
        (None, Path("source.syx"), ValueError, "requires a candidate selection"),
        (1, None, ValueError, "required for a candidate selection"),
        (0, Path("source.syx"), ValueError, "selection must be in 1..8"),
        (9, Path("source.syx"), ValueError, "selection must be in 1..8"),
        (True, Path("source.syx"), TypeError, "selection must be an integer"),
        ("1", Path("source.syx"), TypeError, "selection must be an integer"),
    ],
)
def test_selection_input_validation_fails_before_analysis(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    selection: object,
    source_kit_path: Path | None,
    error_type: type[Exception],
    message: str,
) -> None:
    def unexpected_analyze(_path: Path) -> AudioFeatureAnalysis:
        pytest.fail("invalid selection inputs must fail before audio analysis")

    monkeypatch.setattr(
        service,
        "analyze_analog_four_patch_audio_analysis_isolated",
        unexpected_analyze,
    )

    with pytest.raises(error_type, match=message):
        service.export_audio_patch_dna_workspace(
            audio_path=tmp_path / "reference.wav",
            output_dir=tmp_path / "dna",
            selection=selection,  # type: ignore[arg-type]
            source_kit_path=source_kit_path,
        )


@pytest.mark.parametrize("field_name", ["audio_path", "output_dir"])
def test_public_path_inputs_require_pathlib_paths(field_name: str) -> None:
    kwargs: dict[str, object] = {
        "audio_path": Path("reference.wav"),
        "output_dir": Path("output"),
    }
    kwargs[field_name] = "not-a-path"

    with pytest.raises(TypeError, match=rf"{field_name} must be a pathlib\.Path"):
        service.export_audio_patch_dna_workspace(**kwargs)  # type: ignore[arg-type]


def test_defensive_selected_export_requires_source_kit() -> None:
    workspace = build_audio_patch_dna_workspace(_analysis())

    with pytest.raises(ValueError, match="source_kit_path is required"):
        service._export_selected_candidate(
            workspace=workspace,
            selected_candidate=workspace.candidates[0],
            audio_path=Path("reference.wav"),
            source_kit_path=None,
            output_dir=Path("output"),
            overwrite=False,
        )


def test_selected_report_can_describe_selection_before_a4_export() -> None:
    workspace = build_audio_patch_dna_workspace(_analysis())
    selected = workspace.candidates[2]

    payload = service._audio_patch_dna_export_payload(
        workspace,
        selected_candidate=selected,
        analog_four_export=None,
    )
    markdown = service._audio_patch_dna_export_markdown(
        workspace,
        selected_candidate=selected,
        analog_four_export=None,
    )

    assert payload["selected_candidate"]["label"] == "Brighter"
    assert "Candidate: 3. Brighter" in markdown
    assert "A4 manifest:" not in markdown
