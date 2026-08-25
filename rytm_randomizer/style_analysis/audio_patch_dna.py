"""Passive eight-direction Audio-to-Patch DNA workspace.

One shared audio analysis is transformed into eight deterministic creative
directions. Each direction reuses the existing Analog Four inference mapping;
this module performs no file I/O, MIDI enumeration, or hardware access.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Final, TypedDict

from ..data.audio_patch_dna import (
    AUDIO_PATCH_DNA_CANDIDATE_COUNT,
    AUDIO_PATCH_DNA_DIRECTION_SPECS,
    AudioPatchDnaDirectionSpec,
)
from .analog_four_patch_genome import (
    AnalogFourPatchCandidate,
    AnalogFourPatchCandidatePayload,
    AnalogFourPatchGenome,
    analog_four_patch_candidate_to_dict,
)
from .analog_four_patch_inference import (
    AnalogFourAudioPatchGenome,
    build_analog_four_audio_patch_genome_from_analysis,
)
from .extractor import (
    AudioDnaEvidence,
    AudioDnaEvidencePayload,
    AudioFeatureAnalysis,
    AudioSynthesisFeatures,
    AudioSynthesisFeaturesPayload,
    audio_dna_evidence_to_dict,
    audio_synthesis_features_to_dict,
    clamp_audio_feature_unit,
)
from .feature_report import FeatureReport, FeatureReportPayload, feature_report_to_dict
from .runtime_types import require_runtime_type

AUDIO_PATCH_DNA_SCHEMA_VERSION: Final[str] = "audio-patch-dna-v1"
AUDIO_PATCH_DNA_SAFETY: Final[tuple[str, ...]] = (
    "passive offline audio analysis",
    "one shared audio decode",
    "no MIDI port enumerated or opened",
    "no MIDI or SysEx sent",
    "candidate selection is explicit",
)


@dataclass(frozen=True)
class AudioPatchDnaCandidate:
    """One creative direction and its inferred Analog Four patch."""

    column: int
    key: str
    label: str
    role: str
    closeness: int
    audio_features: AudioSynthesisFeatures
    patch: AnalogFourPatchCandidate


@dataclass(frozen=True)
class AudioPatchDnaWorkspace:
    """Comparable eight-candidate result from one measured audio source."""

    schema_version: str
    feature_report: FeatureReport
    dna_evidence: AudioDnaEvidence
    base_audio_features: AudioSynthesisFeatures
    selected_track: int
    candidates: tuple[AudioPatchDnaCandidate, ...]
    genome_template: AnalogFourPatchGenome
    safety: tuple[str, ...]


class AudioPatchDnaCandidatePayload(TypedDict):
    column: int
    key: str
    label: str
    role: str
    closeness: int
    audio_features: AudioSynthesisFeaturesPayload
    patch: AnalogFourPatchCandidatePayload


class AudioPatchDnaWorkspacePayload(TypedDict):
    schema_version: str
    feature_report: FeatureReportPayload
    dna_evidence: AudioDnaEvidencePayload
    base_audio_features: AudioSynthesisFeaturesPayload
    selected_track: int
    candidate_count: int
    candidates: list[AudioPatchDnaCandidatePayload]
    safety: list[str]


def build_audio_patch_dna_workspace(
    analysis: AudioFeatureAnalysis,
    *,
    track: int = 1,
) -> AudioPatchDnaWorkspace:
    """Build all eight deterministic directions from one shared analysis."""

    validated_analysis = require_runtime_type(
        analysis,
        AudioFeatureAnalysis,
        "analysis must be AudioFeatureAnalysis",
    )
    inferred = tuple(
        _infer_direction(validated_analysis, direction, column=index, track=track)
        for index, direction in enumerate(AUDIO_PATCH_DNA_DIRECTION_SPECS, start=1)
    )
    return AudioPatchDnaWorkspace(
        schema_version=AUDIO_PATCH_DNA_SCHEMA_VERSION,
        feature_report=inferred[0][0].feature_report,
        dna_evidence=validated_analysis.dna_evidence,
        base_audio_features=validated_analysis.synthesis_features,
        selected_track=track,
        candidates=tuple(result[1] for result in inferred),
        genome_template=inferred[0][0].genome,
        safety=AUDIO_PATCH_DNA_SAFETY,
    )


def select_audio_patch_dna_candidate(
    workspace: AudioPatchDnaWorkspace,
    selection: int,
) -> AnalogFourAudioPatchGenome:
    """Return one selected candidate in the existing single-export shape."""

    validated_workspace = require_runtime_type(
        workspace,
        AudioPatchDnaWorkspace,
        "workspace must be AudioPatchDnaWorkspace",
    )
    if selection < 1 or selection > len(validated_workspace.candidates):
        raise ValueError(f"selection must be in 1..{len(validated_workspace.candidates)}")
    selected = validated_workspace.candidates[selection - 1]
    patch = replace(selected.patch, column=1)
    genome = replace(
        validated_workspace.genome_template,
        candidate_count=1,
        candidates=(patch,),
    )
    return AnalogFourAudioPatchGenome(
        feature_report=validated_workspace.feature_report,
        audio_features=selected.audio_features,
        genome=genome,
    )


def audio_patch_dna_workspace_to_dict(
    workspace: AudioPatchDnaWorkspace,
) -> AudioPatchDnaWorkspacePayload:
    """Return the stable JSON-ready workspace payload."""

    validated_workspace = require_runtime_type(
        workspace,
        AudioPatchDnaWorkspace,
        "workspace must be AudioPatchDnaWorkspace",
    )
    return {
        "schema_version": validated_workspace.schema_version,
        "feature_report": feature_report_to_dict(validated_workspace.feature_report),
        "dna_evidence": audio_dna_evidence_to_dict(validated_workspace.dna_evidence),
        "base_audio_features": audio_synthesis_features_to_dict(
            validated_workspace.base_audio_features
        ),
        "selected_track": validated_workspace.selected_track,
        "candidate_count": len(validated_workspace.candidates),
        "candidates": [
            _audio_patch_dna_candidate_payload(candidate)
            for candidate in validated_workspace.candidates
        ],
        "safety": list(validated_workspace.safety),
    }


def render_audio_patch_dna_markdown(workspace: AudioPatchDnaWorkspace) -> str:
    """Render a readable comparison and evidence report."""

    validated_workspace = require_runtime_type(
        workspace,
        AudioPatchDnaWorkspace,
        "workspace must be AudioPatchDnaWorkspace",
    )
    evidence = validated_workspace.dna_evidence
    frequency = (
        f"{evidence.dominant_frequency_hz:.2f} Hz"
        if evidence.dominant_frequency_hz is not None
        else "unresolved"
    )
    note = evidence.dominant_note or "unresolved"
    lines = [
        "# Audio-to-Patch DNA",
        "",
        "## Measured DNA",
        "",
        f"- Dominant pitch: {note} ({frequency})",
        f"- Pitch confidence: {evidence.pitch_confidence:.3f}",
        f"- Tonal stability: {evidence.tonal_stability:.3f}",
        f"- Spectral movement: {evidence.spectral_movement:.3f}",
        f"- BPM: {validated_workspace.feature_report.bpm:.2f}",
        f"- Selected A4 track: {validated_workspace.selected_track}",
        "",
        "## Candidate Comparison",
        "",
        "| # | Direction | Closeness | Bright | Low | Noise | Transient | Motion |",
        "|---:|---|---:|---:|---:|---:|---:|---:|",
    ]
    for candidate in validated_workspace.candidates:
        features = candidate.audio_features
        lines.append(
            f"| {candidate.column} | {candidate.label} | {candidate.closeness} | "
            f"{features.brightness:.3f} | {features.low_end:.3f} | "
            f"{features.noise:.3f} | {features.transient:.3f} | "
            f"{features.modulation:.3f} |"
        )
    lines.extend(("", "## Candidate Patch DNA", ""))
    for candidate in validated_workspace.candidates:
        lines.extend(
            (
                f"### {candidate.column}. {candidate.label}",
                "",
                candidate.role,
                "",
                *_candidate_gene_lines(candidate),
                "",
            )
        )
    lines.extend(("## Safety", "", *(f"- {item}" for item in validated_workspace.safety)))
    return "\n".join(lines).rstrip() + "\n"


def _infer_direction(
    analysis: AudioFeatureAnalysis,
    direction: AudioPatchDnaDirectionSpec,
    *,
    column: int,
    track: int,
) -> tuple[AnalogFourAudioPatchGenome, AudioPatchDnaCandidate]:
    transformed = _transform_features(analysis.synthesis_features, direction)
    directional_analysis = replace(analysis, synthesis_features=transformed)
    inferred = build_analog_four_audio_patch_genome_from_analysis(
        directional_analysis,
        track=track,
        candidate_count=1,
    )
    patch = replace(
        inferred.genome.candidates[0],
        column=column,
        label=direction.label,
        role=direction.role,
        closeness=direction.closeness,
    )
    return inferred, AudioPatchDnaCandidate(
        column=column,
        key=direction.key,
        label=direction.label,
        role=direction.role,
        closeness=direction.closeness,
        audio_features=transformed,
        patch=patch,
    )


def _transform_features(
    features: AudioSynthesisFeatures,
    direction: AudioPatchDnaDirectionSpec,
) -> AudioSynthesisFeatures:
    return replace(
        features,
        duration=clamp_audio_feature_unit(features.duration + direction.duration),
        attack=clamp_audio_feature_unit(features.attack + direction.attack),
        decay=clamp_audio_feature_unit(features.decay + direction.decay),
        sustain=clamp_audio_feature_unit(features.sustain + direction.sustain),
        tail=clamp_audio_feature_unit(features.tail + direction.tail),
        brightness=clamp_audio_feature_unit(features.brightness + direction.brightness),
        noise=clamp_audio_feature_unit(features.noise + direction.noise),
        low_end=clamp_audio_feature_unit(features.low_end + direction.low_end),
        harmonicity=clamp_audio_feature_unit(features.harmonicity + direction.harmonicity),
        transient=clamp_audio_feature_unit(features.transient + direction.transient),
        modulation=clamp_audio_feature_unit(features.modulation + direction.modulation),
    )


def _audio_patch_dna_candidate_payload(
    candidate: AudioPatchDnaCandidate,
) -> AudioPatchDnaCandidatePayload:
    return {
        "column": candidate.column,
        "key": candidate.key,
        "label": candidate.label,
        "role": candidate.role,
        "closeness": candidate.closeness,
        "audio_features": audio_synthesis_features_to_dict(candidate.audio_features),
        "patch": analog_four_patch_candidate_to_dict(candidate.patch),
    }


def _candidate_gene_lines(candidate: AudioPatchDnaCandidate) -> tuple[str, ...]:
    return tuple(
        f"- {gene.value.section} / {gene.value.parameter}: "
        f"{gene.value.screen_value} ({gene.value.transport_status})"
        for gene in candidate.patch.genes
    )


__all__ = [
    "AUDIO_PATCH_DNA_CANDIDATE_COUNT",
    "AUDIO_PATCH_DNA_SCHEMA_VERSION",
    "AUDIO_PATCH_DNA_SAFETY",
    "AudioPatchDnaCandidate",
    "AudioPatchDnaCandidatePayload",
    "AudioPatchDnaWorkspace",
    "AudioPatchDnaWorkspacePayload",
    "audio_patch_dna_workspace_to_dict",
    "build_audio_patch_dna_workspace",
    "render_audio_patch_dna_markdown",
    "select_audio_patch_dna_candidate",
]
