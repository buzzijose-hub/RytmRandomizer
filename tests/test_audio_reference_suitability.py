from __future__ import annotations

import dataclasses

import pytest

pytestmark = pytest.mark.fast

from rytm_randomizer.guardrails.schema import Confidence
from rytm_randomizer.style_analysis.audio_reference_suitability import (
    ReferenceWorkflow,
    SuitabilityRecommendation,
    SuitabilityStatus,
    WorkflowSuitability,
    assess_reference_audio,
    reference_audio_suitability_to_dict,
)
from rytm_randomizer.style_analysis.extractor import (
    AudioDnaEvidence,
    AudioFeatureAnalysis,
)


def _workflow(
    analysis: AudioFeatureAnalysis,
    workflow: ReferenceWorkflow,
) -> WorkflowSuitability:
    return next(
        item for item in assess_reference_audio(analysis).workflows if item.workflow is workflow
    )


def test_canonical_reference_supports_patch_pitch_and_rhythm(
    audio_patch_dna_analysis: AudioFeatureAnalysis,
) -> None:
    suitability = assess_reference_audio(audio_patch_dna_analysis)

    assert suitability.recommendation is SuitabilityRecommendation.PATCH_AND_RHYTHM
    assert [item.status for item in suitability.workflows] == [
        SuitabilityStatus.READY,
        SuitabilityStatus.READY,
        SuitabilityStatus.READY,
        SuitabilityStatus.NOT_APPLICABLE,
    ]
    assert len(suitability.assessment_id) == 64


def test_serialization_is_stable_and_retains_policy_evidence(
    audio_patch_dna_analysis: AudioFeatureAnalysis,
) -> None:
    first = assess_reference_audio(audio_patch_dna_analysis)
    second = assess_reference_audio(audio_patch_dna_analysis)

    assert first == second
    payload = reference_audio_suitability_to_dict(first)
    assert payload["assessment_id"] == first.assessment_id
    assert payload["workflows"][1]["checks"][1] == {
        "key": "pitch_confidence",
        "measured": 0.81,
        "operator": ">=",
        "required": 0.75,
        "passed": True,
    }
    assert payload["safety"][0] == "workflow suitability is not an artistic-quality score"


def test_long_form_source_routes_to_segmentation_first(
    audio_patch_dna_analysis: AudioFeatureAnalysis,
) -> None:
    features = dataclasses.replace(
        audio_patch_dna_analysis.synthesis_features,
        duration=1.0,
    )
    analysis = dataclasses.replace(audio_patch_dna_analysis, synthesis_features=features)
    suitability = assess_reference_audio(analysis)

    assert suitability.recommendation is SuitabilityRecommendation.SEGMENT_FIRST
    assert (
        _workflow(analysis, ReferenceWorkflow.FOCUSED_PATCH_DNA).status is SuitabilityStatus.LIMITED
    )
    segmentation = _workflow(analysis, ReferenceWorkflow.LONG_FORM_SEGMENTATION)
    assert segmentation.status is SuitabilityStatus.READY
    assert "8 seconds or longer" in segmentation.reasons[0]


def test_missing_pitch_blocks_note_specific_synthesis(
    audio_patch_dna_analysis: AudioFeatureAnalysis,
) -> None:
    analysis = dataclasses.replace(
        audio_patch_dna_analysis,
        dna_evidence=AudioDnaEvidence(
            dominant_frequency_hz=None,
            dominant_note=None,
            pitch_confidence=0.0,
            tonal_stability=0.0,
            spectral_movement=0.4,
        ),
    )

    lane = _workflow(analysis, ReferenceWorkflow.NOTE_SPECIFIC_SYNTHESIS)
    assert lane.status is SuitabilityStatus.BLOCKED
    assert lane.checks[0].passed is False


@pytest.mark.parametrize(
    ("pitch_confidence", "tonal_stability", "expected_reason"),
    (
        (0.74, 0.72, "Pitch confidence"),
        (0.81, 0.59, "Tonal stability"),
        (0.74, 0.59, "Pitch confidence"),
    ),
)
def test_weak_pitch_evidence_is_only_a_hint(
    audio_patch_dna_analysis: AudioFeatureAnalysis,
    pitch_confidence: float,
    tonal_stability: float,
    expected_reason: str,
) -> None:
    evidence = dataclasses.replace(
        audio_patch_dna_analysis.dna_evidence,
        pitch_confidence=pitch_confidence,
        tonal_stability=tonal_stability,
    )
    analysis = dataclasses.replace(audio_patch_dna_analysis, dna_evidence=evidence)

    lane = _workflow(analysis, ReferenceWorkflow.NOTE_SPECIFIC_SYNTHESIS)
    assert lane.status is SuitabilityStatus.LIMITED
    assert expected_reason in lane.reasons[0]


def test_medium_confidence_limits_focused_patch_inference(
    audio_patch_dna_analysis: AudioFeatureAnalysis,
) -> None:
    report = dataclasses.replace(
        audio_patch_dna_analysis.feature_report,
        confidence=Confidence.MEDIUM,
    )
    analysis = dataclasses.replace(audio_patch_dna_analysis, feature_report=report)

    lane = _workflow(analysis, ReferenceWorkflow.FOCUSED_PATCH_DNA)
    assert lane.status is SuitabilityStatus.LIMITED
    assert lane.checks[-1].passed is False


def test_zero_duration_blocks_patch_and_rhythm(
    audio_patch_dna_analysis: AudioFeatureAnalysis,
) -> None:
    features = dataclasses.replace(
        audio_patch_dna_analysis.synthesis_features,
        duration=0.0,
    )
    report = dataclasses.replace(audio_patch_dna_analysis.feature_report, bpm=0.0)
    analysis = dataclasses.replace(
        audio_patch_dna_analysis,
        synthesis_features=features,
        feature_report=report,
    )
    suitability = assess_reference_audio(analysis)

    assert suitability.recommendation is SuitabilityRecommendation.MANUAL_REVIEW
    assert (
        _workflow(analysis, ReferenceWorkflow.FOCUSED_PATCH_DNA).status is SuitabilityStatus.BLOCKED
    )
    assert (
        _workflow(analysis, ReferenceWorkflow.RHYTHM_ANALYSIS).status is SuitabilityStatus.BLOCKED
    )


def test_short_unstable_sparse_rhythm_is_limited(
    audio_patch_dna_analysis: AudioFeatureAnalysis,
) -> None:
    features = dataclasses.replace(
        audio_patch_dna_analysis.synthesis_features,
        duration=0.20,
        transient=0.10,
    )
    report = dataclasses.replace(
        audio_patch_dna_analysis.feature_report,
        tempo_stability=0.40,
        percussion_density=0.01,
    )
    analysis = dataclasses.replace(
        audio_patch_dna_analysis,
        synthesis_features=features,
        feature_report=report,
    )

    lane = _workflow(analysis, ReferenceWorkflow.RHYTHM_ANALYSIS)
    assert lane.status is SuitabilityStatus.LIMITED
    assert len(lane.reasons) == 3


def test_patch_only_and_rhythm_only_recommendations(
    audio_patch_dna_analysis: AudioFeatureAnalysis,
) -> None:
    no_tempo = dataclasses.replace(audio_patch_dna_analysis.feature_report, bpm=0.0)
    patch_only = dataclasses.replace(audio_patch_dna_analysis, feature_report=no_tempo)
    assert assess_reference_audio(patch_only).recommendation is SuitabilityRecommendation.PATCH_DNA

    low_confidence = dataclasses.replace(
        audio_patch_dna_analysis.feature_report,
        confidence=Confidence.LOW,
    )
    rhythm_only = dataclasses.replace(
        audio_patch_dna_analysis,
        feature_report=low_confidence,
    )
    assert (
        assess_reference_audio(rhythm_only).recommendation
        is SuitabilityRecommendation.RHYTHM_ANALYSIS
    )


def test_public_boundaries_fail_closed() -> None:
    with pytest.raises(TypeError, match="analysis must be AudioFeatureAnalysis"):
        assess_reference_audio(object())  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="suitability must be ReferenceAudioSuitability"):
        reference_audio_suitability_to_dict(object())  # type: ignore[arg-type]
