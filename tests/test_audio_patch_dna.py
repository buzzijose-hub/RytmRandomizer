"""Tests for the passive eight-direction Audio-to-Patch DNA workspace."""

from __future__ import annotations

import dataclasses

import pytest

from rytm_randomizer.guardrails.schema import Confidence, SourceType
from rytm_randomizer.style_analysis import (
    AUDIO_PATCH_DNA_CANDIDATE_COUNT,
    AudioDnaEvidence,
    AudioFeatureAnalysis,
    AudioSynthesisFeatures,
    FeatureReport,
    audio_patch_dna_workspace_to_dict,
    build_audio_patch_dna_workspace,
    render_audio_patch_dna_markdown,
    select_audio_patch_dna_candidate,
)

pytestmark = pytest.mark.fast


def _analysis(*, features: AudioSynthesisFeatures | None = None) -> AudioFeatureAnalysis:
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
        synthesis_features=features
        or AudioSynthesisFeatures(
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


def test_workspace_builds_ordered_eight_direction_comparison() -> None:
    analysis = _analysis()

    workspace = build_audio_patch_dna_workspace(analysis, track=3)

    assert AUDIO_PATCH_DNA_CANDIDATE_COUNT == 8
    assert workspace.selected_track == 3
    assert workspace.dna_evidence is analysis.dna_evidence
    assert workspace.base_audio_features is analysis.synthesis_features
    assert [candidate.key for candidate in workspace.candidates] == [
        "closest",
        "darker",
        "brighter",
        "metallic",
        "percussive",
        "atmospheric",
        "deeper",
        "animated",
    ]
    assert [candidate.column for candidate in workspace.candidates] == list(range(1, 9))
    assert all(candidate.patch.column == candidate.column for candidate in workspace.candidates)
    assert all(
        gene.track == 3 for candidate in workspace.candidates for gene in candidate.patch.genes
    )
    assert workspace.candidates[0].audio_features == analysis.synthesis_features
    assert workspace.candidates[1].audio_features.brightness == pytest.approx(0.33)
    assert workspace.candidates[2].audio_features.brightness == pytest.approx(0.77)
    assert workspace.candidates[4].audio_features.transient == pytest.approx(0.86)
    assert workspace.candidates[5].audio_features.tail == pytest.approx(0.64)
    assert workspace.candidates[6].audio_features.low_end == pytest.approx(0.80)
    assert workspace.candidates[7].audio_features.modulation == pytest.approx(0.55)


def test_workspace_clamps_all_directional_evidence_to_unit_interval() -> None:
    features = dataclasses.replace(
        _analysis().synthesis_features,
        attack=0.05,
        decay=0.05,
        sustain=0.05,
        tail=0.95,
        brightness=0.90,
        noise=0.98,
        low_end=0.90,
        harmonicity=0.95,
        transient=0.02,
        modulation=0.90,
    )

    workspace = build_audio_patch_dna_workspace(_analysis(features=features))

    assert workspace.candidates[2].audio_features.brightness == 1.0
    assert workspace.candidates[3].audio_features.noise == 1.0
    assert workspace.candidates[3].audio_features.harmonicity == 1.0
    assert workspace.candidates[4].audio_features.attack == 0.0
    assert workspace.candidates[4].audio_features.decay == 0.0
    assert workspace.candidates[4].audio_features.sustain == 0.0
    assert workspace.candidates[5].audio_features.tail == 1.0
    assert workspace.candidates[5].audio_features.transient == 0.0
    assert workspace.candidates[6].audio_features.low_end == 1.0
    assert workspace.candidates[7].audio_features.modulation == 1.0


def test_workspace_serializers_are_stable_and_readable() -> None:
    workspace = build_audio_patch_dna_workspace(_analysis())

    payload = audio_patch_dna_workspace_to_dict(workspace)
    markdown = render_audio_patch_dna_markdown(workspace)

    assert payload["schema_version"] == "audio-patch-dna-v1"
    assert payload["candidate_count"] == 8
    assert payload["dna_evidence"]["dominant_note"] == "F2"
    assert payload["candidates"][3]["label"] == "Metallic"
    assert payload["candidates"][3]["patch"]["column"] == 4
    assert "# Audio-to-Patch DNA" in markdown
    assert "Dominant pitch: F2 (87.31 Hz)" in markdown
    assert "| 8 | Animated |" in markdown
    assert "### 4. Metallic" in markdown
    assert "no MIDI port enumerated or opened" in markdown
    assert render_audio_patch_dna_markdown(workspace) == markdown


def test_markdown_handles_unresolved_pitch() -> None:
    analysis = dataclasses.replace(
        _analysis(),
        dna_evidence=AudioDnaEvidence(None, None, 0.0, 0.0, 0.0),
    )

    markdown = render_audio_patch_dna_markdown(build_audio_patch_dna_workspace(analysis))

    assert "Dominant pitch: unresolved (unresolved)" in markdown


def test_selected_candidate_uses_existing_single_export_shape() -> None:
    workspace = build_audio_patch_dna_workspace(_analysis(), track=2)

    selected = select_audio_patch_dna_candidate(workspace, 6)

    assert selected.audio_features == workspace.candidates[5].audio_features
    assert selected.genome.selected_track == 2
    assert selected.genome.candidate_count == 1
    assert len(selected.genome.candidates) == 1
    assert selected.genome.candidates[0].column == 1
    assert selected.genome.candidates[0].label == "Atmospheric"


@pytest.mark.parametrize("selection", [0, 9])
def test_selection_rejects_out_of_range_values(selection: int) -> None:
    with pytest.raises(ValueError, match="selection must be in 1..8"):
        select_audio_patch_dna_candidate(build_audio_patch_dna_workspace(_analysis()), selection)


def test_workspace_public_boundaries_reject_wrong_types_and_tracks() -> None:
    with pytest.raises(TypeError, match="AudioFeatureAnalysis"):
        build_audio_patch_dna_workspace(object())  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="track must be in 1..4"):
        build_audio_patch_dna_workspace(_analysis(), track=5)
    with pytest.raises(TypeError, match="AudioPatchDnaWorkspace"):
        audio_patch_dna_workspace_to_dict(object())  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="AudioPatchDnaWorkspace"):
        render_audio_patch_dna_markdown(object())  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="AudioPatchDnaWorkspace"):
        select_audio_patch_dna_candidate(object(), 1)  # type: ignore[arg-type]
