"""Tests for passive Audio-to-Patch DNA causal lineage audits."""

from __future__ import annotations

import dataclasses
import json

import pytest

from rytm_randomizer.data.analog_four_audio_inference import (
    ANALOG_FOUR_AUDIO_INFERENCE_BY_PARAMETER,
)
from rytm_randomizer.style_analysis import (
    AudioFeatureAnalysis,
    AudioSynthesisFeatures,
    audio_patch_dna_lineage_audit_to_dict,
    build_audio_patch_dna_lineage_audit,
    build_audio_patch_dna_workspace,
    render_audio_patch_dna_lineage_markdown,
)
from rytm_randomizer.style_analysis.analog_four_patch_inference import (
    build_analog_four_inference_feature_values,
    evaluate_analog_four_inference_spec,
)
from rytm_randomizer.style_analysis.audio_patch_dna_lineage import (
    AUDIO_PATCH_DNA_LINEAGE_FEATURE_KEYS,
)

pytestmark = pytest.mark.fast


def test_lineage_feature_keys_exhaustively_match_audio_synthesis_features() -> None:
    assert (
        tuple(
            field.name
            for field in dataclasses.fields(AudioSynthesisFeatures)
            if field.name != "audio_sha256"
        )
        == AUDIO_PATCH_DNA_LINEAGE_FEATURE_KEYS
    )


def test_lineage_reconciles_inferred_and_template_only_genes(
    audio_patch_dna_analysis: AudioFeatureAnalysis,
) -> None:
    workspace = build_audio_patch_dna_workspace(audio_patch_dna_analysis, track=3)

    audit = build_audio_patch_dna_lineage_audit(workspace)

    assert audit.source_audio_sha256 == "b" * 64
    assert audit.selected_track == 3
    assert audit.candidate_count == 8
    assert [candidate.creative_proximity_hint for candidate in audit.candidates] == [
        candidate.closeness for candidate in workspace.candidates
    ]
    for source, candidate in zip(workspace.candidates, audit.candidates, strict=True):
        source_parameters = {gene.value.parameter for gene in source.patch.genes}
        expected_inferred_parameters = (
            source_parameters & ANALOG_FOUR_AUDIO_INFERENCE_BY_PARAMETER.keys()
        )
        assert candidate.acoustic_verification_status == "render_required"
        assert {
            parameter.parameter for parameter in candidate.inferred_parameters
        } == expected_inferred_parameters
        assert len(candidate.inferred_parameters) + len(candidate.template_only_parameters) == len(
            source.patch.genes
        )
        assert all(
            parameter.verification_status == "matches_candidate"
            for parameter in candidate.inferred_parameters
        )
        assert all(
            parameter.status == "template_only_no_audio_equation"
            for parameter in candidate.template_only_parameters
        )


def test_lineage_records_exact_equation_arithmetic(
    audio_patch_dna_analysis: AudioFeatureAnalysis,
) -> None:
    workspace = build_audio_patch_dna_workspace(audio_patch_dna_analysis)

    parameter = build_audio_patch_dna_lineage_audit(workspace).candidates[0].inferred_parameters[0]

    assert parameter.value_before_multiplier == pytest.approx(
        parameter.intercept + sum(term.contribution for term in parameter.terms)
    )
    assert parameter.value_after_multiplier == pytest.approx(
        parameter.value_before_multiplier * parameter.output_multiplier
    )
    for term in parameter.terms:
        product = 1.0
        for value in term.feature_values:
            product *= value
        assert term.feature_product == pytest.approx(product)
        assert term.contribution == pytest.approx(product * term.coefficient)


def test_lineage_exposes_directional_feature_changes_without_similarity_claims(
    audio_patch_dna_analysis: AudioFeatureAnalysis,
) -> None:
    audit = build_audio_patch_dna_lineage_audit(
        build_audio_patch_dna_workspace(audio_patch_dna_analysis)
    )

    closest = audit.candidates[0]
    darker = audit.candidates[1]
    brighter = audit.candidates[2]
    darker_brightness = next(item for item in darker.feature_deltas if item.feature == "brightness")
    brighter_brightness = next(
        item for item in brighter.feature_deltas if item.feature == "brightness"
    )

    assert closest.mean_absolute_feature_delta == 0.0
    assert all(item.status == "preserved" for item in closest.feature_deltas)
    assert darker_brightness.delta == pytest.approx(-0.22)
    assert darker_brightness.status == "decreased"
    assert brighter_brightness.delta == pytest.approx(0.22)
    assert brighter_brightness.status == "increased"


def test_lineage_serialization_is_deterministic_and_truthful(
    audio_patch_dna_analysis: AudioFeatureAnalysis,
) -> None:
    audit = build_audio_patch_dna_lineage_audit(
        build_audio_patch_dna_workspace(audio_patch_dna_analysis, track=4)
    )

    payload = audio_patch_dna_lineage_audit_to_dict(audit)
    markdown = render_audio_patch_dna_lineage_markdown(audit)
    serialized = json.dumps(payload, sort_keys=True)

    assert payload == audio_patch_dna_lineage_audit_to_dict(audit)
    assert payload["schema_version"] == "audio-patch-dna-lineage-v1"
    assert payload["candidate_count"] == 8
    assert all(
        candidate["acoustic_verification_status"] == "render_required"
        for candidate in payload["candidates"]
    )
    assert '"creative_proximity_hint"' in serialized
    assert '"mean_absolute_feature_delta"' in serialized
    assert '"input_feature_distance"' not in serialized
    assert '"closeness"' not in serialized
    assert "not measured acoustic-fidelity scores" in markdown
    assert "`render_required`" in markdown
    assert "unweighted; descriptive only" in markdown
    assert "| Closeness |" not in markdown
    assert render_audio_patch_dna_lineage_markdown(audit) == markdown


def test_lineage_fails_closed_when_candidate_gene_does_not_match_equation(
    audio_patch_dna_analysis: AudioFeatureAnalysis,
) -> None:
    workspace = build_audio_patch_dna_workspace(audio_patch_dna_analysis)
    candidate = workspace.candidates[0]
    gene_index = next(
        index
        for index, gene in enumerate(candidate.patch.genes)
        if gene.value.parameter in ANALOG_FOUR_AUDIO_INFERENCE_BY_PARAMETER
    )
    genes = list(candidate.patch.genes)
    genes[gene_index] = dataclasses.replace(
        genes[gene_index],
        value=dataclasses.replace(genes[gene_index].value, screen_value="tampered"),
    )
    candidates = list(workspace.candidates)
    candidates[0] = dataclasses.replace(
        candidate,
        patch=dataclasses.replace(candidate.patch, genes=tuple(genes)),
    )
    mismatched_workspace = dataclasses.replace(workspace, candidates=tuple(candidates))

    with pytest.raises(ValueError, match="lineage mismatch"):
        build_audio_patch_dna_lineage_audit(mismatched_workspace)


def test_lineage_and_inference_public_boundaries_fail_closed(
    audio_patch_dna_analysis: AudioFeatureAnalysis,
) -> None:
    workspace = build_audio_patch_dna_workspace(audio_patch_dna_analysis)
    spec = next(iter(ANALOG_FOUR_AUDIO_INFERENCE_BY_PARAMETER.values()))

    with pytest.raises(TypeError, match="AudioPatchDnaWorkspace"):
        build_audio_patch_dna_lineage_audit(object())  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="AudioPatchDnaLineageAudit"):
        audio_patch_dna_lineage_audit_to_dict(object())  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="AudioPatchDnaLineageAudit"):
        render_audio_patch_dna_lineage_markdown(object())  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="AudioSynthesisFeatures"):
        build_analog_four_inference_feature_values(object(), column=1)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="column must be int"):
        build_analog_four_inference_feature_values(
            workspace.base_audio_features,
            column=True,  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="candidate column must be in 1..4"):
        build_analog_four_inference_feature_values(
            workspace.base_audio_features,
            column=0,
        )
    with pytest.raises(TypeError, match="AnalogFourAudioInferenceSpec"):
        evaluate_analog_four_inference_spec(object(), {})  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="feature_values must be Mapping"):
        evaluate_analog_four_inference_spec(spec, object())  # type: ignore[arg-type]
