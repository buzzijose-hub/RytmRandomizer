"""Deterministic workflow suitability decisions for measured audio evidence.

This module answers which downstream workflow the current measurements can
support. It does not judge artistic quality and performs no file, model, MIDI,
or hardware I/O.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from typing import Final, TypeAlias, TypedDict

from ..guardrails.schema import Confidence
from .extractor import AUDIO_DURATION_CEILING_SECONDS, AudioFeatureAnalysis
from .runtime_types import require_runtime_type

AUDIO_REFERENCE_SUITABILITY_SCHEMA_VERSION: Final[str] = "audio-reference-suitability-v1"
AUDIO_REFERENCE_SUITABILITY_POLICY_VERSION: Final[str] = "measured-evidence-v1"
PATCH_FOCUSED_DURATION_CEILING: Final[float] = 1.0
PITCH_CONFIDENCE_MINIMUM: Final[float] = 0.75
TONAL_STABILITY_MINIMUM: Final[float] = 0.60
RHYTHM_DURATION_MINIMUM: Final[float] = 0.25
TEMPO_STABILITY_MINIMUM: Final[float] = 0.50
PERCUSSION_DENSITY_MINIMUM: Final[float] = 0.05
TRANSIENT_ACTIVITY_MINIMUM: Final[float] = 0.20

AUDIO_REFERENCE_SUITABILITY_SAFETY: Final[tuple[str, ...]] = (
    "workflow suitability is not an artistic-quality score",
    "decisions use measured evidence and explicit policy thresholds",
    "long-form audio is segmented before focused patch inference",
    "no model, filesystem, MIDI, SysEx, or hardware access",
)

SuitabilityValue: TypeAlias = bool | float | str | None


class ReferenceWorkflow(str, Enum):
    """Downstream workflows independently assessed by the policy."""

    FOCUSED_PATCH_DNA = "focused_patch_dna"
    NOTE_SPECIFIC_SYNTHESIS = "note_specific_synthesis"
    RHYTHM_ANALYSIS = "rhythm_analysis"
    LONG_FORM_SEGMENTATION = "long_form_segmentation"


class SuitabilityStatus(str, Enum):
    """Bounded outcome for one workflow lane."""

    READY = "ready"
    LIMITED = "limited"
    BLOCKED = "blocked"
    NOT_APPLICABLE = "not_applicable"


class SuitabilityRecommendation(str, Enum):
    """Preferred next workflow based on all lane outcomes."""

    SEGMENT_FIRST = "segment_first"
    PATCH_AND_RHYTHM = "patch_and_rhythm"
    PATCH_DNA = "patch_dna"
    RHYTHM_ANALYSIS = "rhythm_analysis"
    MANUAL_REVIEW = "manual_review"


@dataclass(frozen=True)
class SuitabilityCheck:
    """One measured value compared with one explicit policy rule."""

    key: str
    measured: SuitabilityValue
    operator: str
    required: SuitabilityValue
    passed: bool


@dataclass(frozen=True)
class WorkflowSuitability:
    """Evidence-backed outcome for one downstream workflow."""

    workflow: ReferenceWorkflow
    status: SuitabilityStatus
    checks: tuple[SuitabilityCheck, ...]
    reasons: tuple[str, ...]
    next_action: str


@dataclass(frozen=True)
class ReferenceAudioSuitability:
    """Stable suitability decision for one :class:`AudioFeatureAnalysis`."""

    schema_version: str
    policy_version: str
    assessment_id: str
    audio_sha256: str
    feature_report_hash: str
    workflows: tuple[WorkflowSuitability, ...]
    recommendation: SuitabilityRecommendation
    safety: tuple[str, ...]


class SuitabilityCheckPayload(TypedDict):
    key: str
    measured: SuitabilityValue
    operator: str
    required: SuitabilityValue
    passed: bool


class WorkflowSuitabilityPayload(TypedDict):
    workflow: str
    status: str
    checks: list[SuitabilityCheckPayload]
    reasons: list[str]
    next_action: str


class ReferenceAudioSuitabilityPayload(TypedDict):
    schema_version: str
    policy_version: str
    assessment_id: str
    audio_sha256: str
    feature_report_hash: str
    workflows: list[WorkflowSuitabilityPayload]
    recommendation: str
    safety: list[str]


def assess_reference_audio(
    analysis: AudioFeatureAnalysis,
) -> ReferenceAudioSuitability:
    """Assess which workflows are supported by ``analysis`` evidence."""

    validated = require_runtime_type(
        analysis,
        AudioFeatureAnalysis,
        "analysis must be AudioFeatureAnalysis",
    )
    workflows = (
        _assess_focused_patch(validated),
        _assess_note_specific_synthesis(validated),
        _assess_rhythm(validated),
        _assess_long_form(validated),
    )
    recommendation = _recommend(workflows)
    assessment_id = _assessment_id(validated, workflows, recommendation)
    return ReferenceAudioSuitability(
        schema_version=AUDIO_REFERENCE_SUITABILITY_SCHEMA_VERSION,
        policy_version=AUDIO_REFERENCE_SUITABILITY_POLICY_VERSION,
        assessment_id=assessment_id,
        audio_sha256=validated.audio_sha256,
        feature_report_hash=validated.feature_report.content_hash,
        workflows=workflows,
        recommendation=recommendation,
        safety=AUDIO_REFERENCE_SUITABILITY_SAFETY,
    )


def reference_audio_suitability_to_dict(
    suitability: ReferenceAudioSuitability,
) -> ReferenceAudioSuitabilityPayload:
    """Return a stable JSON-ready representation of ``suitability``."""

    validated = require_runtime_type(
        suitability,
        ReferenceAudioSuitability,
        "suitability must be ReferenceAudioSuitability",
    )
    return {
        "schema_version": validated.schema_version,
        "policy_version": validated.policy_version,
        "assessment_id": validated.assessment_id,
        "audio_sha256": validated.audio_sha256,
        "feature_report_hash": validated.feature_report_hash,
        "workflows": [_workflow_payload(item) for item in validated.workflows],
        "recommendation": validated.recommendation.value,
        "safety": list(validated.safety),
    }


def _assess_focused_patch(analysis: AudioFeatureAnalysis) -> WorkflowSuitability:
    duration_present = analysis.duration > 0.0
    focused_duration = analysis.duration < PATCH_FOCUSED_DURATION_CEILING
    high_confidence = analysis.feature_report.confidence is Confidence.HIGH
    checks = (
        _suitability_check("duration_present", analysis.duration, ">", 0.0, duration_present),
        _suitability_check(
            "duration_below_extractor_ceiling",
            analysis.duration,
            "<",
            PATCH_FOCUSED_DURATION_CEILING,
            focused_duration,
        ),
        _suitability_check(
            "measurement_confidence",
            analysis.feature_report.confidence.value,
            "==",
            Confidence.HIGH.value,
            high_confidence,
        ),
    )
    if not duration_present:
        return _workflow(
            ReferenceWorkflow.FOCUSED_PATCH_DNA,
            SuitabilityStatus.BLOCKED,
            checks,
            ("No non-zero audio duration was measured.",),
            "Measure a focused audio source before patch inference.",
        )
    reasons: list[str] = []
    if not focused_duration:
        reasons.append("Duration reached the extractor ceiling; the source may be long-form.")
    if not high_confidence:
        reasons.append("Measurement confidence is below the focused-patch policy.")
    if reasons:
        return _workflow(
            ReferenceWorkflow.FOCUSED_PATCH_DNA,
            SuitabilityStatus.LIMITED,
            checks,
            tuple(reasons),
            "Segment or re-measure a focused sound before direct patch inference.",
        )
    return _workflow(
        ReferenceWorkflow.FOCUSED_PATCH_DNA,
        SuitabilityStatus.READY,
        checks,
        ("Duration and confidence support bounded timbre inference.",),
        "Proceed with bounded patch-DNA inference.",
    )


def _assess_note_specific_synthesis(
    analysis: AudioFeatureAnalysis,
) -> WorkflowSuitability:
    evidence = analysis.dna_evidence
    pitch_present = (
        evidence.dominant_frequency_hz is not None and evidence.dominant_note is not None
    )
    confidence_ready = evidence.pitch_confidence >= PITCH_CONFIDENCE_MINIMUM
    stability_ready = evidence.tonal_stability >= TONAL_STABILITY_MINIMUM
    checks = (
        _suitability_check(
            "dominant_pitch_present",
            pitch_present,
            "==",
            True,
            pitch_present,
        ),
        _suitability_check(
            "pitch_confidence",
            evidence.pitch_confidence,
            ">=",
            PITCH_CONFIDENCE_MINIMUM,
            confidence_ready,
        ),
        _suitability_check(
            "tonal_stability",
            evidence.tonal_stability,
            ">=",
            TONAL_STABILITY_MINIMUM,
            stability_ready,
        ),
    )
    if not pitch_present:
        return _workflow(
            ReferenceWorkflow.NOTE_SPECIFIC_SYNTHESIS,
            SuitabilityStatus.BLOCKED,
            checks,
            ("No dominant note and positive frequency were resolved.",),
            "Preserve pitch or request a musically verified target note.",
        )
    reasons: list[str] = []
    if not confidence_ready:
        reasons.append("Pitch confidence is below the note-specific threshold.")
    if not stability_ready:
        reasons.append("Tonal stability is below the note-specific threshold.")
    if reasons:
        return _workflow(
            ReferenceWorkflow.NOTE_SPECIFIC_SYNTHESIS,
            SuitabilityStatus.LIMITED,
            checks,
            tuple(reasons),
            "Treat the detected pitch as a hint, not a verified target note.",
        )
    return _workflow(
        ReferenceWorkflow.NOTE_SPECIFIC_SYNTHESIS,
        SuitabilityStatus.READY,
        checks,
        ("Dominant pitch evidence clears both note-specific thresholds.",),
        "A device-specific tuning table may resolve the measured note.",
    )


def _assess_rhythm(analysis: AudioFeatureAnalysis) -> WorkflowSuitability:
    report = analysis.feature_report
    duration_ready = analysis.duration >= RHYTHM_DURATION_MINIMUM
    tempo_present = report.bpm > 0.0
    tempo_stable = report.tempo_stability >= TEMPO_STABILITY_MINIMUM
    activity_present = (
        report.percussion_density >= PERCUSSION_DENSITY_MINIMUM
        or analysis.transient >= TRANSIENT_ACTIVITY_MINIMUM
    )
    checks = (
        _suitability_check(
            "rhythm_duration",
            analysis.duration,
            ">=",
            RHYTHM_DURATION_MINIMUM,
            duration_ready,
        ),
        _suitability_check("tempo_present", report.bpm, ">", 0.0, tempo_present),
        _suitability_check(
            "tempo_stability",
            report.tempo_stability,
            ">=",
            TEMPO_STABILITY_MINIMUM,
            tempo_stable,
        ),
        _suitability_check(
            "rhythmic_activity_present",
            activity_present,
            "==",
            True,
            activity_present,
        ),
    )
    if analysis.duration <= 0.0 or not tempo_present:
        return _workflow(
            ReferenceWorkflow.RHYTHM_ANALYSIS,
            SuitabilityStatus.BLOCKED,
            checks,
            ("A non-zero duration and measured tempo are required.",),
            "Use transient-only evidence or provide a rhythmic reference.",
        )
    reasons: list[str] = []
    if not duration_ready:
        reasons.append("The measured source is too short for stable rhythm context.")
    if not tempo_stable:
        reasons.append("Tempo stability is below the rhythm policy threshold.")
    if not activity_present:
        reasons.append("Measured percussion and transient activity are both sparse.")
    if reasons:
        return _workflow(
            ReferenceWorkflow.RHYTHM_ANALYSIS,
            SuitabilityStatus.LIMITED,
            checks,
            tuple(reasons),
            "Use rhythm evidence conservatively or analyze a longer rhythmic segment.",
        )
    return _workflow(
        ReferenceWorkflow.RHYTHM_ANALYSIS,
        SuitabilityStatus.READY,
        checks,
        ("Tempo, duration, and rhythmic activity clear the workflow policy.",),
        "Proceed with rhythm-profile interpretation.",
    )


def _assess_long_form(analysis: AudioFeatureAnalysis) -> WorkflowSuitability:
    saturated = analysis.duration >= PATCH_FOCUSED_DURATION_CEILING
    checks = (
        _suitability_check(
            "duration_reached_extractor_ceiling",
            analysis.duration,
            ">=",
            PATCH_FOCUSED_DURATION_CEILING,
            saturated,
        ),
    )
    if saturated:
        return _workflow(
            ReferenceWorkflow.LONG_FORM_SEGMENTATION,
            SuitabilityStatus.READY,
            checks,
            (
                "Duration reached the normalized extractor ceiling "
                f"({AUDIO_DURATION_CEILING_SECONDS:.0f} seconds or longer).",
            ),
            "Build deterministic segments before focused patch inference.",
        )
    return _workflow(
        ReferenceWorkflow.LONG_FORM_SEGMENTATION,
        SuitabilityStatus.NOT_APPLICABLE,
        checks,
        ("The source remains below the long-form routing threshold.",),
        "No segmentation is required by this policy.",
    )


def _recommend(
    workflows: tuple[WorkflowSuitability, ...],
) -> SuitabilityRecommendation:
    statuses = {item.workflow: item.status for item in workflows}
    if statuses[ReferenceWorkflow.LONG_FORM_SEGMENTATION] is SuitabilityStatus.READY:
        return SuitabilityRecommendation.SEGMENT_FIRST
    patch_ready = statuses[ReferenceWorkflow.FOCUSED_PATCH_DNA] is SuitabilityStatus.READY
    rhythm_ready = statuses[ReferenceWorkflow.RHYTHM_ANALYSIS] is SuitabilityStatus.READY
    if patch_ready and rhythm_ready:
        return SuitabilityRecommendation.PATCH_AND_RHYTHM
    if patch_ready:
        return SuitabilityRecommendation.PATCH_DNA
    if rhythm_ready:
        return SuitabilityRecommendation.RHYTHM_ANALYSIS
    return SuitabilityRecommendation.MANUAL_REVIEW


def _suitability_check(
    key: str,
    measured: SuitabilityValue,
    operator: str,
    required: SuitabilityValue,
    passed: bool,
) -> SuitabilityCheck:
    return SuitabilityCheck(
        key=key,
        measured=measured,
        operator=operator,
        required=required,
        passed=passed,
    )


def _workflow(
    workflow: ReferenceWorkflow,
    status: SuitabilityStatus,
    checks: tuple[SuitabilityCheck, ...],
    reasons: tuple[str, ...],
    next_action: str,
) -> WorkflowSuitability:
    return WorkflowSuitability(
        workflow=workflow,
        status=status,
        checks=checks,
        reasons=reasons,
        next_action=next_action,
    )


def _workflow_payload(item: WorkflowSuitability) -> WorkflowSuitabilityPayload:
    return {
        "workflow": item.workflow.value,
        "status": item.status.value,
        "checks": [
            {
                "key": check.key,
                "measured": check.measured,
                "operator": check.operator,
                "required": check.required,
                "passed": check.passed,
            }
            for check in item.checks
        ],
        "reasons": list(item.reasons),
        "next_action": item.next_action,
    }


def _assessment_id(
    analysis: AudioFeatureAnalysis,
    workflows: tuple[WorkflowSuitability, ...],
    recommendation: SuitabilityRecommendation,
) -> str:
    payload = {
        "schema_version": AUDIO_REFERENCE_SUITABILITY_SCHEMA_VERSION,
        "policy_version": AUDIO_REFERENCE_SUITABILITY_POLICY_VERSION,
        "audio_sha256": analysis.audio_sha256,
        "feature_report_hash": analysis.feature_report.content_hash,
        "workflows": [_workflow_payload(item) for item in workflows],
        "recommendation": recommendation.value,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


__all__ = [
    "AUDIO_REFERENCE_SUITABILITY_POLICY_VERSION",
    "AUDIO_REFERENCE_SUITABILITY_SCHEMA_VERSION",
    "ReferenceAudioSuitability",
    "ReferenceAudioSuitabilityPayload",
    "ReferenceWorkflow",
    "SuitabilityCheck",
    "SuitabilityRecommendation",
    "SuitabilityStatus",
    "WorkflowSuitability",
    "assess_reference_audio",
    "reference_audio_suitability_to_dict",
]
