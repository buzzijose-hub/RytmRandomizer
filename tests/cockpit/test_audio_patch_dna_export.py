"""Tests for the passive Audio-to-Patch DNA export service."""

from __future__ import annotations

import json
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import cast

import pytest

from rytm_randomizer.cockpit.export import audio_patch_dna as service
from rytm_randomizer.observability.errors import BoundaryError
from rytm_randomizer.observability.metrics import get_metrics
from rytm_randomizer.style_analysis import (
    AudioFeatureAnalysis,
    build_audio_patch_dna_workspace,
)
from rytm_randomizer.style_analysis.analog_four_patch_inference import (
    AnalogFourAudioPatchGenome,
)

pytestmark = [pytest.mark.fast, pytest.mark.usefixtures("isolated_observability")]


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
    audio_patch_dna_analysis: AudioFeatureAnalysis,
) -> None:
    audio_path = tmp_path / "reference.wav"
    output_dir = tmp_path / "dna"
    analyzed: list[Path] = []

    def fake_analyze(path: Path) -> AudioFeatureAnalysis:
        analyzed.append(path)
        return audio_patch_dna_analysis

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
    audio_patch_dna_analysis: AudioFeatureAnalysis,
) -> None:
    monkeypatch.setattr(
        service,
        "analyze_analog_four_patch_audio_analysis_isolated",
        lambda _path: audio_patch_dna_analysis,
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
    audio_patch_dna_analysis: AudioFeatureAnalysis,
) -> None:
    audio_path = tmp_path / "reference.wav"
    source_kit_path = tmp_path / "source.syx"
    output_dir = tmp_path / "dna"
    analyzed: list[Path] = []
    export_calls: list[dict[str, object]] = []

    def fake_analyze(path: Path) -> AudioFeatureAnalysis:
        analyzed.append(path)
        return audio_patch_dna_analysis

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


def test_defensive_selected_export_requires_source_kit(
    audio_patch_dna_analysis: AudioFeatureAnalysis,
) -> None:
    workspace = build_audio_patch_dna_workspace(audio_patch_dna_analysis)

    with pytest.raises(ValueError, match="source_kit_path is required"):
        service._export_selected_candidate(
            workspace=workspace,
            selected_candidate=workspace.candidates[0],
            audio_path=Path("reference.wav"),
            source_kit_path=None,
            output_dir=Path("output"),
            overwrite=False,
        )


def test_selected_report_can_describe_selection_before_a4_export(
    audio_patch_dna_analysis: AudioFeatureAnalysis,
) -> None:
    workspace = build_audio_patch_dna_workspace(audio_patch_dna_analysis)
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


def test_export_records_one_terminal_success_with_trace_and_metrics(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    audio_patch_dna_analysis: AudioFeatureAnalysis,
) -> None:
    traced: list[tuple[str, str]] = []
    logged: list[dict[str, object]] = []

    @contextmanager
    def observe_operation(name: str, **_kwargs: object) -> Iterator[None]:
        traced.append(("start", name))
        yield
        traced.append(("end", name))

    monkeypatch.setattr(service, "trace_operation", observe_operation)
    monkeypatch.setattr(
        service,
        "analyze_analog_four_patch_audio_analysis_isolated",
        lambda _path: audio_patch_dna_analysis,
    )
    monkeypatch.setattr(
        service._logger,
        "info",
        lambda _message, *, extra: logged.append(extra),
    )

    service.export_audio_patch_dna_workspace(
        audio_path=tmp_path / "reference.wav",
        output_dir=tmp_path / "dna",
    )

    metrics = get_metrics()
    assert metrics.export_count == 1
    assert not metrics.export_errors_by_code
    assert traced == [
        ("start", "a4_audio_patch_dna_export"),
        ("end", "a4_audio_patch_dna_export"),
    ]
    assert len(logged) == 1
    assert logged[0]["outcome"] == "completed"
    assert logged[0]["candidate_count"] == 8
    assert logged[0]["selected"] is False
    assert float(logged[0]["duration_ms"]) >= 0.0
    assert "export_count=1" in str(logged[0]["metrics_summary"])


def test_export_records_one_terminal_boundary_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    logged: list[dict[str, object]] = []

    def fail_analysis(_path: Path) -> AudioFeatureAnalysis:
        raise BoundaryError("native analysis failed")

    monkeypatch.setattr(
        service,
        "analyze_analog_four_patch_audio_analysis_isolated",
        fail_analysis,
    )
    monkeypatch.setattr(
        service._logger,
        "warning",
        lambda _message, *, extra: logged.append(extra),
    )

    with pytest.raises(BoundaryError, match="native analysis failed"):
        service.export_audio_patch_dna_workspace(
            audio_path=tmp_path / "reference.wav",
            output_dir=tmp_path / "dna",
        )

    metrics = get_metrics()
    assert metrics.export_count == 1
    assert metrics.export_errors_by_code["inference_failed"] == 1
    assert len(logged) == 1
    assert logged[0]["outcome"] == "failed"
    assert logged[0]["error_code"] == "inference_failed"
    assert float(logged[0]["duration_ms"]) >= 0.0
    assert "inference_failed:1" in str(logged[0]["metrics_summary"])


def test_export_records_one_terminal_operator_interrupt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    logged: list[dict[str, object]] = []

    def interrupt_analysis(_path: Path) -> AudioFeatureAnalysis:
        raise KeyboardInterrupt("operator cancelled")

    monkeypatch.setattr(
        service,
        "analyze_analog_four_patch_audio_analysis_isolated",
        interrupt_analysis,
    )
    monkeypatch.setattr(
        service._logger,
        "warning",
        lambda _message, *, extra: logged.append(extra),
    )

    with pytest.raises(KeyboardInterrupt, match="operator cancelled"):
        service.export_audio_patch_dna_workspace(
            audio_path=tmp_path / "reference.wav",
            output_dir=tmp_path / "dna",
        )

    metrics = get_metrics()
    assert metrics.export_count == 1
    assert metrics.export_errors_by_code["interrupted"] == 1
    assert len(logged) == 1
    assert logged[0]["outcome"] == "failed"
    assert logged[0]["error_code"] == "interrupted"
