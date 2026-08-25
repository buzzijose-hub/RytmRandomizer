"""Passive causal audit for Audio-to-Patch DNA candidates.

The audit explains deterministic input transformations and Analog Four
inference equations. It does not score acoustic resemblance; rendered hardware
audio is required before any candidate can be described as acoustically
verified.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Final, Literal, TypedDict, cast

from ..data.analog_four_audio_inference import (
    ANALOG_FOUR_AUDIO_INFERENCE_BY_PARAMETER,
    AnalogFourInferenceFeatureKey,
    AnalogFourInferenceParameter,
)
from ..data.analog_four_display import make_a4_patch_value
from .analog_four_patch_inference import (
    build_analog_four_inference_feature_values,
    evaluate_analog_four_inference_spec,
)
from .audio_patch_dna import AudioPatchDnaCandidate, AudioPatchDnaWorkspace
from .extractor import AudioSynthesisFeatures
from .runtime_types import require_runtime_type

AUDIO_PATCH_DNA_LINEAGE_SCHEMA_VERSION: Final[str] = "audio-patch-dna-lineage-v1"
AUDIO_PATCH_DNA_INFERENCE_TEMPLATE_COLUMN: Final[int] = 1
AUDIO_PATCH_DNA_RENDER_REQUIRED: Final[str] = "render_required"
AUDIO_PATCH_DNA_LINEAGE_SAFETY: Final[tuple[str, ...]] = (
    "passive deterministic lineage audit",
    "creative proximity hint is authored direction metadata, not acoustic fidelity",
    "acoustic verification requires rendered output and a reference comparison",
    "no audio file decoded",
    "no MIDI port enumerated or opened",
    "no MIDI or SysEx sent",
)

AudioPatchDnaLineageFeatureKey = Literal[
    "duration",
    "attack",
    "decay",
    "sustain",
    "tail",
    "brightness",
    "spectral_flatness",
    "noise",
    "low_end",
    "harmonicity",
    "transient",
    "modulation",
]

AUDIO_PATCH_DNA_LINEAGE_FEATURE_KEYS: Final[tuple[AudioPatchDnaLineageFeatureKey, ...]] = (
    "duration",
    "attack",
    "decay",
    "sustain",
    "tail",
    "brightness",
    "spectral_flatness",
    "noise",
    "low_end",
    "harmonicity",
    "transient",
    "modulation",
)


@dataclass(frozen=True)
class AudioPatchDnaFeatureDelta:
    """One normalized source-to-candidate feature transformation."""

    feature: AudioPatchDnaLineageFeatureKey
    measured_value: float
    candidate_value: float
    delta: float
    status: Literal["preserved", "increased", "decreased"]


@dataclass(frozen=True)
class AudioPatchDnaTermLineage:
    """One weighted term in a canonical inference equation."""

    feature_keys: tuple[AnalogFourInferenceFeatureKey, ...]
    feature_values: tuple[float, ...]
    feature_product: float
    coefficient: float
    contribution: float


@dataclass(frozen=True)
class AudioPatchDnaParameterLineage:
    """Recomputed causal evidence for one audio-inferred A4 parameter."""

    track: int
    family: str
    parameter: str
    section: str
    scale: str
    intercept: float
    terms: tuple[AudioPatchDnaTermLineage, ...]
    output_multiplier: float
    value_before_multiplier: float
    value_after_multiplier: float
    clamped_screen_target: int
    actual_screen_value: str
    actual_midi_value: int | None
    transport_status: str
    confidence: str
    verification_status: Literal["matches_candidate"]


@dataclass(frozen=True)
class AudioPatchDnaTemplateGeneLineage:
    """One deterministic template gene with no measured-audio equation."""

    track: int
    family: str
    parameter: str
    section: str
    screen_value: str
    midi_value: int | None
    transport_status: str
    rationale: str
    status: Literal["template_only_no_audio_equation"]


@dataclass(frozen=True)
class AudioPatchDnaCandidateLineage:
    """Causal explanation and evidence boundary for one candidate."""

    column: int
    key: str
    label: str
    role: str
    creative_proximity_hint: int
    mean_absolute_feature_delta: float
    inference_template_column: int
    feature_deltas: tuple[AudioPatchDnaFeatureDelta, ...]
    inferred_parameters: tuple[AudioPatchDnaParameterLineage, ...]
    template_only_parameters: tuple[AudioPatchDnaTemplateGeneLineage, ...]
    acoustic_verification_status: str


@dataclass(frozen=True)
class AudioPatchDnaLineageAudit:
    """Stable passive lineage audit for one existing DNA workspace."""

    schema_version: str
    source_audio_sha256: str
    selected_track: int
    candidate_count: int
    candidates: tuple[AudioPatchDnaCandidateLineage, ...]
    safety: tuple[str, ...]


class AudioPatchDnaFeatureDeltaPayload(TypedDict):
    feature: str
    measured_value: float
    candidate_value: float
    delta: float
    status: str


class AudioPatchDnaTermLineagePayload(TypedDict):
    feature_keys: list[str]
    feature_values: list[float]
    feature_product: float
    coefficient: float
    contribution: float


class AudioPatchDnaParameterLineagePayload(TypedDict):
    track: int
    family: str
    parameter: str
    section: str
    scale: str
    intercept: float
    terms: list[AudioPatchDnaTermLineagePayload]
    output_multiplier: float
    value_before_multiplier: float
    value_after_multiplier: float
    clamped_screen_target: int
    actual_screen_value: str
    actual_midi_value: int | None
    transport_status: str
    confidence: str
    verification_status: str


class AudioPatchDnaTemplateGeneLineagePayload(TypedDict):
    track: int
    family: str
    parameter: str
    section: str
    screen_value: str
    midi_value: int | None
    transport_status: str
    rationale: str
    status: str


class AudioPatchDnaCandidateLineagePayload(TypedDict):
    column: int
    key: str
    label: str
    role: str
    creative_proximity_hint: int
    mean_absolute_feature_delta: float
    inference_template_column: int
    feature_deltas: list[AudioPatchDnaFeatureDeltaPayload]
    inferred_parameter_count: int
    inferred_parameters: list[AudioPatchDnaParameterLineagePayload]
    template_only_parameter_count: int
    template_only_parameters: list[AudioPatchDnaTemplateGeneLineagePayload]
    acoustic_verification_status: str


class AudioPatchDnaLineageAuditPayload(TypedDict):
    schema_version: str
    source_audio_sha256: str
    selected_track: int
    candidate_count: int
    candidates: list[AudioPatchDnaCandidateLineagePayload]
    safety: list[str]


def build_audio_patch_dna_lineage_audit(
    workspace: AudioPatchDnaWorkspace,
) -> AudioPatchDnaLineageAudit:
    """Recompute and verify the causal lineage for every workspace candidate."""

    validated_workspace = require_runtime_type(
        workspace,
        AudioPatchDnaWorkspace,
        "workspace must be AudioPatchDnaWorkspace",
    )
    candidates = tuple(
        _candidate_lineage(validated_workspace.base_audio_features, candidate)
        for candidate in validated_workspace.candidates
    )
    return AudioPatchDnaLineageAudit(
        schema_version=AUDIO_PATCH_DNA_LINEAGE_SCHEMA_VERSION,
        source_audio_sha256=validated_workspace.base_audio_features.audio_sha256,
        selected_track=validated_workspace.selected_track,
        candidate_count=len(candidates),
        candidates=candidates,
        safety=AUDIO_PATCH_DNA_LINEAGE_SAFETY,
    )


def audio_patch_dna_lineage_audit_to_dict(
    audit: AudioPatchDnaLineageAudit,
) -> AudioPatchDnaLineageAuditPayload:
    """Return the stable JSON-ready lineage payload."""

    validated_audit = require_runtime_type(
        audit,
        AudioPatchDnaLineageAudit,
        "audit must be AudioPatchDnaLineageAudit",
    )
    return {
        "schema_version": validated_audit.schema_version,
        "source_audio_sha256": validated_audit.source_audio_sha256,
        "selected_track": validated_audit.selected_track,
        "candidate_count": validated_audit.candidate_count,
        "candidates": [
            _candidate_lineage_payload(candidate) for candidate in validated_audit.candidates
        ],
        "safety": list(validated_audit.safety),
    }


def render_audio_patch_dna_lineage_markdown(
    audit: AudioPatchDnaLineageAudit,
) -> str:
    """Render a readable causal audit without implying acoustic verification."""

    validated_audit = require_runtime_type(
        audit,
        AudioPatchDnaLineageAudit,
        "audit must be AudioPatchDnaLineageAudit",
    )
    lines = [
        "# Audio-to-Patch DNA Lineage Audit",
        "",
        "## Evidence Boundary",
        "",
        "Creative proximity hints are authored direction metadata, not measured "
        "acoustic-fidelity scores. Every candidate remains `render_required` until "
        "its rendered output is captured and compared with the reference audio.",
        "",
        f"- Source audio SHA-256: `{validated_audit.source_audio_sha256}`",
        f"- Selected A4 track: {validated_audit.selected_track}",
        f"- Candidate count: {validated_audit.candidate_count}",
        "",
        "## Candidate Summary",
        "",
        "| # | Direction | Creative proximity hint | Mean feature delta | Inferred | "
        "Template-only | Acoustic status |",
        "|---:|---|---:|---:|---:|---:|---|",
    ]
    for candidate in validated_audit.candidates:
        lines.append(
            f"| {candidate.column} | {candidate.label} | "
            f"{candidate.creative_proximity_hint} | "
            f"{candidate.mean_absolute_feature_delta:.6f} | "
            f"{len(candidate.inferred_parameters)} | "
            f"{len(candidate.template_only_parameters)} | "
            f"{candidate.acoustic_verification_status} |"
        )
    for candidate in validated_audit.candidates:
        lines.extend(
            (
                "",
                f"## {candidate.column}. {candidate.label}",
                "",
                f"- Role: {candidate.role}",
                f"- Creative proximity hint: {candidate.creative_proximity_hint}",
                "- Mean absolute authored-input feature delta: "
                f"{candidate.mean_absolute_feature_delta:.6f} (unweighted; descriptive only)",
                f"- Acoustic verification: `{candidate.acoustic_verification_status}`",
                "",
                "### Feature Transformations",
                "",
                "| Feature | Measured | Candidate | Delta | Status |",
                "|---|---:|---:|---:|---|",
            )
        )
        for delta in candidate.feature_deltas:
            lines.append(
                f"| {delta.feature} | {delta.measured_value:.6f} | "
                f"{delta.candidate_value:.6f} | {delta.delta:+.6f} | "
                f"{delta.status} |"
            )
        lines.extend(
            (
                "",
                "### Verified Inference Equations",
                "",
                "| Parameter | Equation | Target | Screen | MIDI | Verification |",
                "|---|---|---:|---|---:|---|",
            )
        )
        for parameter in candidate.inferred_parameters:
            midi = (
                str(parameter.actual_midi_value)
                if parameter.actual_midi_value is not None
                else "n/a"
            )
            lines.append(
                f"| {parameter.parameter} | {_formula_text(parameter)} | "
                f"{parameter.clamped_screen_target} | "
                f"{parameter.actual_screen_value} | {midi} | "
                f"{parameter.verification_status} |"
            )
        lines.extend(("", "### Template-only Parameters", ""))
        lines.extend(
            f"- {gene.family} / {gene.parameter}: {gene.screen_value} " f"(`{gene.status}`)"
            for gene in candidate.template_only_parameters
        )
    lines.extend(("", "## Safety", ""))
    lines.extend(f"- {item}" for item in validated_audit.safety)
    return "\n".join(lines).rstrip() + "\n"


def _candidate_lineage(
    base_features: AudioSynthesisFeatures,
    candidate: AudioPatchDnaCandidate,
) -> AudioPatchDnaCandidateLineage:
    feature_deltas = _candidate_feature_deltas(base_features, candidate.audio_features)
    feature_values = build_analog_four_inference_feature_values(
        candidate.audio_features,
        column=AUDIO_PATCH_DNA_INFERENCE_TEMPLATE_COLUMN,
    )
    inferred: list[AudioPatchDnaParameterLineage] = []
    template_only: list[AudioPatchDnaTemplateGeneLineage] = []
    for gene in candidate.patch.genes:
        parameter = gene.value.parameter
        if parameter not in ANALOG_FOUR_AUDIO_INFERENCE_BY_PARAMETER:
            template_only.append(
                AudioPatchDnaTemplateGeneLineage(
                    track=gene.track,
                    family=gene.family,
                    parameter=parameter,
                    section=gene.value.section,
                    screen_value=gene.value.screen_value,
                    midi_value=gene.value.midi_value,
                    transport_status=gene.value.transport_status,
                    rationale=gene.rationale,
                    status="template_only_no_audio_equation",
                )
            )
            continue
        typed_parameter = cast(AnalogFourInferenceParameter, parameter)
        spec = ANALOG_FOUR_AUDIO_INFERENCE_BY_PARAMETER[typed_parameter]
        screen_target = evaluate_analog_four_inference_spec(spec, feature_values)
        expected_value = make_a4_patch_value(parameter, screen_target=screen_target)
        if gene.value != expected_value:
            raise ValueError(
                "Audio-to-Patch DNA lineage mismatch for "
                f"candidate {candidate.column} parameter {parameter!r}"
            )
        terms = tuple(
            _term_lineage(term.feature_keys, term.coefficient, feature_values)
            for term in spec.terms
        )
        before_multiplier = spec.intercept + sum(term.contribution for term in terms)
        after_multiplier = before_multiplier * spec.output_multiplier
        inferred.append(
            AudioPatchDnaParameterLineage(
                track=gene.track,
                family=gene.family,
                parameter=parameter,
                section=gene.value.section,
                scale=spec.scale,
                intercept=spec.intercept,
                terms=terms,
                output_multiplier=spec.output_multiplier,
                value_before_multiplier=before_multiplier,
                value_after_multiplier=after_multiplier,
                clamped_screen_target=screen_target,
                actual_screen_value=gene.value.screen_value,
                actual_midi_value=gene.value.midi_value,
                transport_status=gene.value.transport_status,
                confidence=gene.confidence,
                verification_status="matches_candidate",
            )
        )
    return AudioPatchDnaCandidateLineage(
        column=candidate.column,
        key=candidate.key,
        label=candidate.label,
        role=candidate.role,
        creative_proximity_hint=candidate.closeness,
        mean_absolute_feature_delta=sum(abs(item.delta) for item in feature_deltas)
        / len(feature_deltas),
        inference_template_column=AUDIO_PATCH_DNA_INFERENCE_TEMPLATE_COLUMN,
        feature_deltas=feature_deltas,
        inferred_parameters=tuple(inferred),
        template_only_parameters=tuple(template_only),
        acoustic_verification_status=AUDIO_PATCH_DNA_RENDER_REQUIRED,
    )


def _candidate_feature_deltas(
    base: AudioSynthesisFeatures,
    candidate: AudioSynthesisFeatures,
) -> tuple[AudioPatchDnaFeatureDelta, ...]:
    base_values = _audio_feature_values(base)
    candidate_values = _audio_feature_values(candidate)
    return tuple(
        _feature_delta(feature, base_values[feature], candidate_values[feature])
        for feature in AUDIO_PATCH_DNA_LINEAGE_FEATURE_KEYS
    )


def _feature_delta(
    feature: AudioPatchDnaLineageFeatureKey,
    measured: float,
    candidate: float,
) -> AudioPatchDnaFeatureDelta:
    delta = candidate - measured
    if delta > 0.0:
        status: Literal["preserved", "increased", "decreased"] = "increased"
    elif delta < 0.0:
        status = "decreased"
    else:
        status = "preserved"
    return AudioPatchDnaFeatureDelta(
        feature=feature,
        measured_value=measured,
        candidate_value=candidate,
        delta=delta,
        status=status,
    )


def _audio_feature_values(
    features: AudioSynthesisFeatures,
) -> dict[AudioPatchDnaLineageFeatureKey, float]:
    return {
        "duration": features.duration,
        "attack": features.attack,
        "decay": features.decay,
        "sustain": features.sustain,
        "tail": features.tail,
        "brightness": features.brightness,
        "spectral_flatness": features.spectral_flatness,
        "noise": features.noise,
        "low_end": features.low_end,
        "harmonicity": features.harmonicity,
        "transient": features.transient,
        "modulation": features.modulation,
    }


def _term_lineage(
    feature_keys: tuple[AnalogFourInferenceFeatureKey, ...],
    coefficient: float,
    feature_values: Mapping[AnalogFourInferenceFeatureKey, float],
) -> AudioPatchDnaTermLineage:
    values = tuple(feature_values[key] for key in feature_keys)
    product = 1.0
    for value in values:
        product *= value
    return AudioPatchDnaTermLineage(
        feature_keys=feature_keys,
        feature_values=values,
        feature_product=product,
        coefficient=coefficient,
        contribution=product * coefficient,
    )


def _formula_text(parameter: AudioPatchDnaParameterLineage) -> str:
    terms = " ".join(f"{term.contribution:+.6f}" for term in parameter.terms)
    return f"({parameter.intercept:.6f} {terms}) x " f"{parameter.output_multiplier:.6f}"


def _candidate_lineage_payload(
    candidate: AudioPatchDnaCandidateLineage,
) -> AudioPatchDnaCandidateLineagePayload:
    return {
        "column": candidate.column,
        "key": candidate.key,
        "label": candidate.label,
        "role": candidate.role,
        "creative_proximity_hint": candidate.creative_proximity_hint,
        "mean_absolute_feature_delta": candidate.mean_absolute_feature_delta,
        "inference_template_column": candidate.inference_template_column,
        "feature_deltas": [_feature_delta_payload(item) for item in candidate.feature_deltas],
        "inferred_parameter_count": len(candidate.inferred_parameters),
        "inferred_parameters": [
            _parameter_lineage_payload(item) for item in candidate.inferred_parameters
        ],
        "template_only_parameter_count": len(candidate.template_only_parameters),
        "template_only_parameters": [
            _template_gene_payload(item) for item in candidate.template_only_parameters
        ],
        "acoustic_verification_status": candidate.acoustic_verification_status,
    }


def _feature_delta_payload(
    item: AudioPatchDnaFeatureDelta,
) -> AudioPatchDnaFeatureDeltaPayload:
    return {
        "feature": item.feature,
        "measured_value": item.measured_value,
        "candidate_value": item.candidate_value,
        "delta": item.delta,
        "status": item.status,
    }


def _parameter_lineage_payload(
    item: AudioPatchDnaParameterLineage,
) -> AudioPatchDnaParameterLineagePayload:
    return {
        "track": item.track,
        "family": item.family,
        "parameter": item.parameter,
        "section": item.section,
        "scale": item.scale,
        "intercept": item.intercept,
        "terms": [_term_lineage_payload(term) for term in item.terms],
        "output_multiplier": item.output_multiplier,
        "value_before_multiplier": item.value_before_multiplier,
        "value_after_multiplier": item.value_after_multiplier,
        "clamped_screen_target": item.clamped_screen_target,
        "actual_screen_value": item.actual_screen_value,
        "actual_midi_value": item.actual_midi_value,
        "transport_status": item.transport_status,
        "confidence": item.confidence,
        "verification_status": item.verification_status,
    }


def _term_lineage_payload(
    item: AudioPatchDnaTermLineage,
) -> AudioPatchDnaTermLineagePayload:
    return {
        "feature_keys": list(item.feature_keys),
        "feature_values": list(item.feature_values),
        "feature_product": item.feature_product,
        "coefficient": item.coefficient,
        "contribution": item.contribution,
    }


def _template_gene_payload(
    item: AudioPatchDnaTemplateGeneLineage,
) -> AudioPatchDnaTemplateGeneLineagePayload:
    return {
        "track": item.track,
        "family": item.family,
        "parameter": item.parameter,
        "section": item.section,
        "screen_value": item.screen_value,
        "midi_value": item.midi_value,
        "transport_status": item.transport_status,
        "rationale": item.rationale,
        "status": item.status,
    }


__all__ = [
    "AUDIO_PATCH_DNA_INFERENCE_TEMPLATE_COLUMN",
    "AUDIO_PATCH_DNA_LINEAGE_FEATURE_KEYS",
    "AUDIO_PATCH_DNA_LINEAGE_SAFETY",
    "AUDIO_PATCH_DNA_LINEAGE_SCHEMA_VERSION",
    "AUDIO_PATCH_DNA_RENDER_REQUIRED",
    "AudioPatchDnaCandidateLineage",
    "AudioPatchDnaFeatureDelta",
    "AudioPatchDnaLineageAudit",
    "AudioPatchDnaParameterLineage",
    "AudioPatchDnaTemplateGeneLineage",
    "AudioPatchDnaTermLineage",
    "audio_patch_dna_lineage_audit_to_dict",
    "build_audio_patch_dna_lineage_audit",
    "render_audio_patch_dna_lineage_markdown",
]
