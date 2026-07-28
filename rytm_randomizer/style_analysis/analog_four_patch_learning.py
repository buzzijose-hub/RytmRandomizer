"""Passive Analog Four audio-to-patch learning packet compiler.

This module layers learning metadata on top of the patch genome compiler. It
does not train a model, open MIDI ports, send messages, or write SysEx. Its job
is to make the system's current "why" explicit: which candidate is closest,
which traits route to which Analog Four controls, which rows are ready for
future live dial-in, and what capture matrix will let future hardware
recordings improve the mapping.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Final, TypedDict

from ..data.analog_four_display import (
    TRANSPORT_CC_READY,
    TRANSPORT_NRPN_READY,
    TRANSPORT_SCREEN_ONLY,
    TRANSPORT_SCREEN_ONLY_NRPN,
)
from ..data.analog_four_learning import (
    ANALOG_FOUR_LEARNING_CAPTURE_MATRIX,
    ANALOG_FOUR_LEARNING_TRAIT_ROUTES,
    ANALOG_FOUR_LEARNING_TRANSPORT_STATUS_WEIGHTS,
)
from .analog_four_patch_genome import (
    ANALOG_FOUR_DEVICE_ID,
    AnalogFourPatchCandidate,
    AnalogFourPatchCandidatePayload,
    AnalogFourPatchGenome,
    AnalogFourPatchGenomePayload,
    analog_four_patch_candidate_to_dict,
    analog_four_patch_genome_to_dict,
    build_analog_four_patch_genome,
)
from .blueprint import ReferenceTrait
from .feature_report import FeatureReport

ANALOG_FOUR_PATCH_LEARNING_VERSION: Final[str] = "analog-four-patch-learning-v1"
ANALOG_FOUR_PATCH_LEARNING_MODE: Final[str] = "single-sound-learning"
ANALOG_FOUR_PATCH_LEARNING_SAFETY: Final[tuple[str, ...]] = (
    "passive read-only patch learning",
    "no MIDI port opened",
    "no MIDI sent",
    "no SysEx written",
    "no hardware state captured",
    "live dial-in remains gated by explicit transport readiness",
    "sparse destination ordinals validated against Elektron Overbridge 2.25.7",
)
_TRANSPORT_READY_STATUSES: Final[frozenset[str]] = frozenset(
    {TRANSPORT_CC_READY, TRANSPORT_NRPN_READY}
)
_TRANSPORT_PENDING_STATUSES: Final[frozenset[str]] = frozenset(
    {TRANSPORT_SCREEN_ONLY_NRPN, TRANSPORT_SCREEN_ONLY}
)
_MAX_TRANSPORT_WEIGHT: Final[int] = max(ANALOG_FOUR_LEARNING_TRANSPORT_STATUS_WEIGHTS.values())


@dataclass(frozen=True)
class AnalogFourCandidateLearningScore:
    """Ranked score for one candidate column."""

    rank: int
    column: int
    label: str
    role: str
    closeness: int
    trait_fit: int
    transport_readiness: int
    learning_score: int
    cc_ready_count: int
    nrpn_ready_count: int
    screen_only_nrpn_count: int
    screen_only_count: int
    pending_parameters: tuple[str, ...]


@dataclass(frozen=True)
class AnalogFourTraitLearningRoute:
    """How one measured trait influences A4 controls for the selected patch."""

    trait_key: str
    trait_label: str
    intensity: int
    evidence: tuple[str, ...]
    parameter_focus: tuple[str, ...]
    selected_parameters: tuple[str, ...]
    learning_question: str
    rationale: str


@dataclass(frozen=True)
class AnalogFourLearningCaptureStep:
    """One passive future-capture instruction."""

    step_id: str
    note_name: str
    midi_note: int
    velocity: int
    gate_ms: int
    repeat_count: int
    focus: str
    expected_evidence: tuple[str, ...]


@dataclass(frozen=True)
class AnalogFourLiveDialReadiness:
    """Transport-readiness summary for the selected candidate."""

    selected_candidate: int
    ready_count: int
    pending_count: int
    cc_ready_count: int
    nrpn_ready_count: int
    screen_only_nrpn_count: int
    screen_only_count: int
    ready_percentage: int
    live_dial_path: str
    blocking_reason: str
    ready_parameters: tuple[str, ...]
    pending_parameters: tuple[str, ...]


@dataclass(frozen=True)
class AnalogFourPatchLearningPacket:
    """Passive learning packet for a selected Analog Four patch candidate."""

    version: str
    device_id: str
    mode: str
    selected_track: int
    selected_candidate: int
    selected_label: str
    source_hash: str
    source_confidence: str
    genome: AnalogFourPatchGenome
    selected_patch: AnalogFourPatchCandidate
    candidate_scores: tuple[AnalogFourCandidateLearningScore, ...]
    trait_routes: tuple[AnalogFourTraitLearningRoute, ...]
    capture_steps: tuple[AnalogFourLearningCaptureStep, ...]
    live_dial_readiness: AnalogFourLiveDialReadiness
    safety: tuple[str, ...]


class AnalogFourCandidateLearningScorePayload(TypedDict):
    rank: int
    column: int
    label: str
    role: str
    closeness: int
    trait_fit: int
    transport_readiness: int
    learning_score: int
    cc_ready_count: int
    nrpn_ready_count: int
    screen_only_nrpn_count: int
    screen_only_count: int
    pending_parameters: list[str]


class AnalogFourTraitLearningRoutePayload(TypedDict):
    trait_key: str
    trait_label: str
    intensity: int
    evidence: list[str]
    parameter_focus: list[str]
    selected_parameters: list[str]
    learning_question: str
    rationale: str


class AnalogFourLearningCaptureStepPayload(TypedDict):
    step_id: str
    note_name: str
    midi_note: int
    velocity: int
    gate_ms: int
    repeat_count: int
    focus: str
    expected_evidence: list[str]


class AnalogFourLiveDialReadinessPayload(TypedDict):
    selected_candidate: int
    ready_count: int
    pending_count: int
    cc_ready_count: int
    nrpn_ready_count: int
    screen_only_nrpn_count: int
    screen_only_count: int
    ready_percentage: int
    live_dial_path: str
    blocking_reason: str
    ready_parameters: list[str]
    pending_parameters: list[str]


class AnalogFourPatchLearningPacketPayload(TypedDict):
    version: str
    device_id: str
    mode: str
    selected_track: int
    selected_candidate: int
    selected_label: str
    source_hash: str
    source_confidence: str
    candidate_scores: list[AnalogFourCandidateLearningScorePayload]
    trait_routes: list[AnalogFourTraitLearningRoutePayload]
    capture_steps: list[AnalogFourLearningCaptureStepPayload]
    live_dial_readiness: AnalogFourLiveDialReadinessPayload
    selected_patch: AnalogFourPatchCandidatePayload
    genome: AnalogFourPatchGenomePayload
    safety: list[str]


def _require_learning_feature_report(value: object) -> FeatureReport:
    if not isinstance(value, FeatureReport):
        raise TypeError("report must be a FeatureReport")
    return value


def _require_learning_patch_genome(value: object) -> AnalogFourPatchGenome:
    if not isinstance(value, AnalogFourPatchGenome):
        raise TypeError("genome must be an AnalogFourPatchGenome")
    return value


def _require_learning_packet(value: object) -> AnalogFourPatchLearningPacket:
    if not isinstance(value, AnalogFourPatchLearningPacket):
        raise TypeError("packet must be an AnalogFourPatchLearningPacket")
    return value


def build_analog_four_patch_learning_packet(
    report: FeatureReport,
    *,
    track: int = 1,
    selected_candidate: int = 1,
) -> AnalogFourPatchLearningPacket:
    """Build a passive A4 patch-learning packet from a measured reference."""

    report = _require_learning_feature_report(report)
    genome = build_analog_four_patch_genome(report, track=track)
    return build_analog_four_patch_learning_packet_from_genome(
        report,
        genome,
        selected_candidate=selected_candidate,
    )


def build_analog_four_patch_learning_packet_from_genome(
    report: FeatureReport,
    genome: AnalogFourPatchGenome,
    *,
    selected_candidate: int,
) -> AnalogFourPatchLearningPacket:
    """Build learning metadata around an already-compiled A4 genome."""

    report = _require_learning_feature_report(report)
    genome = _require_learning_patch_genome(genome)
    if selected_candidate < 1 or selected_candidate > genome.candidate_count:
        raise ValueError(f"candidate must be in 1..{genome.candidate_count}")

    selected_patch = genome.candidates[selected_candidate - 1]
    candidate_scores = _build_learning_scores(genome)
    return AnalogFourPatchLearningPacket(
        version=ANALOG_FOUR_PATCH_LEARNING_VERSION,
        device_id=ANALOG_FOUR_DEVICE_ID,
        mode=ANALOG_FOUR_PATCH_LEARNING_MODE,
        selected_track=genome.selected_track,
        selected_candidate=selected_candidate,
        selected_label=selected_patch.label,
        source_hash=genome.source_hash,
        source_confidence=genome.source_confidence.value,
        genome=genome,
        selected_patch=selected_patch,
        candidate_scores=candidate_scores,
        trait_routes=_build_trait_routes(genome.traits, selected_patch),
        capture_steps=_build_capture_steps(),
        live_dial_readiness=_build_live_dial_readiness(
            selected_patch,
            selected_candidate=selected_candidate,
        ),
        safety=ANALOG_FOUR_PATCH_LEARNING_SAFETY,
    )


def analog_four_patch_learning_packet_to_dict(
    packet: AnalogFourPatchLearningPacket,
) -> AnalogFourPatchLearningPacketPayload:
    """Return a stable JSON-ready representation of ``packet``."""

    packet = _require_learning_packet(packet)
    return {
        "version": packet.version,
        "device_id": packet.device_id,
        "mode": packet.mode,
        "selected_track": packet.selected_track,
        "selected_candidate": packet.selected_candidate,
        "selected_label": packet.selected_label,
        "source_hash": packet.source_hash,
        "source_confidence": packet.source_confidence,
        "candidate_scores": [
            _candidate_learning_score_payload(score) for score in packet.candidate_scores
        ],
        "trait_routes": [_trait_learning_route_payload(route) for route in packet.trait_routes],
        "capture_steps": [_learning_capture_step_payload(step) for step in packet.capture_steps],
        "live_dial_readiness": _live_dial_readiness_payload(packet.live_dial_readiness),
        "selected_patch": analog_four_patch_candidate_to_dict(packet.selected_patch),
        "genome": analog_four_patch_genome_to_dict(packet.genome),
        "safety": list(packet.safety),
    }


def _build_learning_scores(
    genome: AnalogFourPatchGenome,
) -> tuple[AnalogFourCandidateLearningScore, ...]:
    raw_scores = tuple(
        _build_candidate_learning_score(candidate, traits=genome.traits)
        for candidate in genome.candidates
    )
    ranked = sorted(
        raw_scores,
        key=lambda score: (-score.learning_score, score.column),
    )
    ranks = {score.column: rank for rank, score in enumerate(ranked, start=1)}
    return tuple(replace(score, rank=ranks[score.column]) for score in raw_scores)


def _build_candidate_learning_score(
    candidate: AnalogFourPatchCandidate,
    *,
    traits: tuple[ReferenceTrait, ...],
) -> AnalogFourCandidateLearningScore:
    readiness = _candidate_transport_readiness(candidate)
    trait_fit = _candidate_trait_fit(candidate, traits=traits)
    learning_score = int(round(candidate.closeness * 0.70 + trait_fit * 0.20 + readiness * 0.10))
    return AnalogFourCandidateLearningScore(
        rank=0,
        column=candidate.column,
        label=candidate.label,
        role=candidate.role,
        closeness=candidate.closeness,
        trait_fit=trait_fit,
        transport_readiness=readiness,
        learning_score=learning_score,
        cc_ready_count=_candidate_status_count(candidate, TRANSPORT_CC_READY),
        nrpn_ready_count=_candidate_status_count(candidate, TRANSPORT_NRPN_READY),
        screen_only_nrpn_count=_candidate_status_count(
            candidate,
            TRANSPORT_SCREEN_ONLY_NRPN,
        ),
        screen_only_count=_candidate_status_count(candidate, TRANSPORT_SCREEN_ONLY),
        pending_parameters=_candidate_pending_parameters(candidate),
    )


def _candidate_transport_readiness(candidate: AnalogFourPatchCandidate) -> int:
    if not candidate.genes:
        return 0
    points = sum(
        ANALOG_FOUR_LEARNING_TRANSPORT_STATUS_WEIGHTS.get(
            gene.value.transport_status,
            0,
        )
        for gene in candidate.genes
    )
    max_points = len(candidate.genes) * _MAX_TRANSPORT_WEIGHT
    return int(round((points / float(max_points)) * 100.0))


def _candidate_trait_fit(
    candidate: AnalogFourPatchCandidate,
    *,
    traits: tuple[ReferenceTrait, ...],
) -> int:
    trait_by_key = {trait.key: trait for trait in traits}
    candidate_parameters = {gene.value.parameter for gene in candidate.genes}
    weighted_total = 0
    matched_weight = 0
    for route in ANALOG_FOUR_LEARNING_TRAIT_ROUTES:
        trait = trait_by_key.get(route.trait_key)
        if trait is None:
            continue
        matches = candidate_parameters.intersection(route.parameter_focus)
        if not matches:
            continue
        weight = len(matches)
        weighted_total += trait.intensity * weight
        matched_weight += weight
    if matched_weight == 0:
        return 0
    return int(round(weighted_total / float(matched_weight)))


def _build_trait_routes(
    traits: tuple[ReferenceTrait, ...],
    selected_patch: AnalogFourPatchCandidate,
) -> tuple[AnalogFourTraitLearningRoute, ...]:
    trait_by_key = {trait.key: trait for trait in traits}
    selected_parameters = {gene.value.parameter for gene in selected_patch.genes}
    routes: list[AnalogFourTraitLearningRoute] = []
    for spec in ANALOG_FOUR_LEARNING_TRAIT_ROUTES:
        trait = trait_by_key.get(spec.trait_key)
        if trait is None:
            continue
        routes.append(
            AnalogFourTraitLearningRoute(
                trait_key=trait.key,
                trait_label=trait.label,
                intensity=trait.intensity,
                evidence=trait.evidence,
                parameter_focus=spec.parameter_focus,
                selected_parameters=tuple(
                    parameter
                    for parameter in spec.parameter_focus
                    if parameter in selected_parameters
                ),
                learning_question=spec.learning_question,
                rationale=spec.rationale,
            )
        )
    return tuple(routes)


def _build_capture_steps() -> tuple[AnalogFourLearningCaptureStep, ...]:
    return tuple(
        AnalogFourLearningCaptureStep(
            step_id=spec.step_id,
            note_name=spec.note_name,
            midi_note=spec.midi_note,
            velocity=spec.velocity,
            gate_ms=spec.gate_ms,
            repeat_count=spec.repeat_count,
            focus=spec.focus,
            expected_evidence=spec.expected_evidence,
        )
        for spec in ANALOG_FOUR_LEARNING_CAPTURE_MATRIX
    )


def _build_live_dial_readiness(
    selected_patch: AnalogFourPatchCandidate,
    *,
    selected_candidate: int,
) -> AnalogFourLiveDialReadiness:
    ready_parameters = tuple(
        gene.value.parameter
        for gene in selected_patch.genes
        if gene.value.transport_status in _TRANSPORT_READY_STATUSES
    )
    pending_parameters = tuple(
        gene.value.parameter
        for gene in selected_patch.genes
        if gene.value.transport_status in _TRANSPORT_PENDING_STATUSES
    )
    cc_ready_count = _candidate_status_count(selected_patch, TRANSPORT_CC_READY)
    nrpn_ready_count = _candidate_status_count(selected_patch, TRANSPORT_NRPN_READY)
    screen_only_nrpn_count = _candidate_status_count(
        selected_patch,
        TRANSPORT_SCREEN_ONLY_NRPN,
    )
    screen_only_count = _candidate_status_count(selected_patch, TRANSPORT_SCREEN_ONLY)
    ready_count = len(ready_parameters)
    pending_count = len(pending_parameters)
    total_count = ready_count + pending_count
    ready_percentage = 0 if total_count == 0 else int(round(ready_count / total_count * 100.0))
    return AnalogFourLiveDialReadiness(
        selected_candidate=selected_candidate,
        ready_count=ready_count,
        pending_count=pending_count,
        cc_ready_count=cc_ready_count,
        nrpn_ready_count=nrpn_ready_count,
        screen_only_nrpn_count=screen_only_nrpn_count,
        screen_only_count=screen_only_count,
        ready_percentage=ready_percentage,
        live_dial_path=_live_dial_path(ready_count, pending_count),
        blocking_reason=_live_dial_blocking_reason(screen_only_nrpn_count, pending_count),
        ready_parameters=ready_parameters,
        pending_parameters=pending_parameters,
    )


def _live_dial_path(ready_count: int, pending_count: int) -> str:
    if pending_count == 0:
        return "transport-ready"
    if ready_count > 0:
        return "partial-live-dial-ready"
    return "manual-only"


def _live_dial_blocking_reason(screen_only_nrpn_count: int, pending_count: int) -> str:
    if screen_only_nrpn_count > 0:
        return "NRPN destination ordinal capture required before full live dial-in"
    if pending_count > 0:
        return "front-panel-only values require manual capture before automation"
    return "none"


def _candidate_status_count(candidate: AnalogFourPatchCandidate, status: str) -> int:
    return sum(1 for gene in candidate.genes if gene.value.transport_status == status)


def _candidate_pending_parameters(
    candidate: AnalogFourPatchCandidate,
) -> tuple[str, ...]:
    return tuple(
        gene.value.parameter
        for gene in candidate.genes
        if gene.value.transport_status in _TRANSPORT_PENDING_STATUSES
    )


def _candidate_learning_score_payload(
    score: AnalogFourCandidateLearningScore,
) -> AnalogFourCandidateLearningScorePayload:
    return {
        "rank": score.rank,
        "column": score.column,
        "label": score.label,
        "role": score.role,
        "closeness": score.closeness,
        "trait_fit": score.trait_fit,
        "transport_readiness": score.transport_readiness,
        "learning_score": score.learning_score,
        "cc_ready_count": score.cc_ready_count,
        "nrpn_ready_count": score.nrpn_ready_count,
        "screen_only_nrpn_count": score.screen_only_nrpn_count,
        "screen_only_count": score.screen_only_count,
        "pending_parameters": list(score.pending_parameters),
    }


def _trait_learning_route_payload(
    route: AnalogFourTraitLearningRoute,
) -> AnalogFourTraitLearningRoutePayload:
    return {
        "trait_key": route.trait_key,
        "trait_label": route.trait_label,
        "intensity": route.intensity,
        "evidence": list(route.evidence),
        "parameter_focus": list(route.parameter_focus),
        "selected_parameters": list(route.selected_parameters),
        "learning_question": route.learning_question,
        "rationale": route.rationale,
    }


def _learning_capture_step_payload(
    step: AnalogFourLearningCaptureStep,
) -> AnalogFourLearningCaptureStepPayload:
    return {
        "step_id": step.step_id,
        "note_name": step.note_name,
        "midi_note": step.midi_note,
        "velocity": step.velocity,
        "gate_ms": step.gate_ms,
        "repeat_count": step.repeat_count,
        "focus": step.focus,
        "expected_evidence": list(step.expected_evidence),
    }


def _live_dial_readiness_payload(
    readiness: AnalogFourLiveDialReadiness,
) -> AnalogFourLiveDialReadinessPayload:
    return {
        "selected_candidate": readiness.selected_candidate,
        "ready_count": readiness.ready_count,
        "pending_count": readiness.pending_count,
        "cc_ready_count": readiness.cc_ready_count,
        "nrpn_ready_count": readiness.nrpn_ready_count,
        "screen_only_nrpn_count": readiness.screen_only_nrpn_count,
        "screen_only_count": readiness.screen_only_count,
        "ready_percentage": readiness.ready_percentage,
        "live_dial_path": readiness.live_dial_path,
        "blocking_reason": readiness.blocking_reason,
        "ready_parameters": list(readiness.ready_parameters),
        "pending_parameters": list(readiness.pending_parameters),
    }


__all__ = [
    "ANALOG_FOUR_PATCH_LEARNING_MODE",
    "ANALOG_FOUR_PATCH_LEARNING_SAFETY",
    "ANALOG_FOUR_PATCH_LEARNING_VERSION",
    "AnalogFourCandidateLearningScore",
    "AnalogFourCandidateLearningScorePayload",
    "AnalogFourLearningCaptureStep",
    "AnalogFourLearningCaptureStepPayload",
    "AnalogFourLiveDialReadiness",
    "AnalogFourLiveDialReadinessPayload",
    "AnalogFourPatchLearningPacket",
    "AnalogFourPatchLearningPacketPayload",
    "AnalogFourTraitLearningRoute",
    "AnalogFourTraitLearningRoutePayload",
    "analog_four_patch_learning_packet_to_dict",
    "build_analog_four_patch_learning_packet",
    "build_analog_four_patch_learning_packet_from_genome",
]
