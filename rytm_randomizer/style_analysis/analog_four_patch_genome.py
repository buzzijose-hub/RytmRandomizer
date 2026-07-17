"""Passive Analog Four patch genome compiler.

The compiler translates a :class:`FeatureReport` into four front-panel Analog
Four MKII patch candidates. It deliberately stops at DNA/report metadata: no
MIDI ports are opened, no messages are sent, and NRPN-only destination rows
remain screen-only until their exact ordinals are captured.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Final, TypedDict

from ..data.analog_four_display import AnalogFourPatchValue, make_a4_patch_value
from ..data.analog_four_patch_templates import (
    ANALOG_FOUR_PATCH_CANDIDATE_TEMPLATES,
    ANALOG_FOUR_PATCH_FAMILY_ORDER,
    AnalogFourPatchCandidateTemplateSpec,
    AnalogFourPatchGeneTemplateSpec,
)
from ..data.analog_four_sysex_calibration import A4_SYNTH_TRACK_MAX, A4_SYNTH_TRACK_MIN
from ..guardrails.schema import Confidence
from .blueprint import ReferenceTrait, build_reference_style_blueprint
from .feature_report import FeatureReport, compute_feature_report_hash

ANALOG_FOUR_PATCH_GENOME_VERSION: Final[str] = "analog-four-patch-genome-v1"
ANALOG_FOUR_DEVICE_ID: Final[str] = "analog_four_mk2"
ANALOG_FOUR_PATCH_MODE: Final[str] = "single-sound"
ANALOG_FOUR_TRACK_MIN: Final[int] = A4_SYNTH_TRACK_MIN
ANALOG_FOUR_TRACK_MAX: Final[int] = A4_SYNTH_TRACK_MAX
ANALOG_FOUR_PATCH_CANDIDATE_MIN: Final[int] = 1
ANALOG_FOUR_PATCH_CANDIDATE_MAX: Final[int] = len(ANALOG_FOUR_PATCH_CANDIDATE_TEMPLATES)
ANALOG_FOUR_PATCH_SAFETY: Final[tuple[str, ...]] = (
    "passive read-only patch genome",
    "no MIDI port opened",
    "no MIDI sent",
    "no SysEx written",
    "manual front-panel DNA only",
    "NRPN-only destinations require ordinal capture before live dial-in",
)


@dataclass(frozen=True)
class AnalogFourPatchGene:
    """One A4 patch parameter row for the selected track."""

    track: int
    family: str
    value: AnalogFourPatchValue
    rationale: str
    confidence: str


@dataclass(frozen=True)
class AnalogFourPatchCandidate:
    """One candidate column in the patch genome."""

    column: int
    label: str
    role: str
    closeness: int
    genes: tuple[AnalogFourPatchGene, ...]


@dataclass(frozen=True)
class AnalogFourPatchGenome:
    """Four-column passive A4 patch genome for one single-sound track."""

    version: str
    device_id: str
    mode: str
    selected_track: int
    source_hash: str
    source_confidence: Confidence
    candidate_count: int
    traits: tuple[ReferenceTrait, ...]
    candidates: tuple[AnalogFourPatchCandidate, ...]
    safety: tuple[str, ...]


class AnalogFourPatchValuePayload(TypedDict):
    parameter: str
    section: str
    encoder: str
    screen_value: str
    midi_value: int | None
    cc_msb: int | None
    cc_lsb: int | None
    nrpn_address: list[int] | None
    transport_status: str
    dial_direction: str


class AnalogFourPatchGenePayload(TypedDict):
    track: int
    family: str
    rationale: str
    confidence: str
    value: AnalogFourPatchValuePayload


class AnalogFourPatchCandidatePayload(TypedDict):
    column: int
    label: str
    role: str
    closeness: int
    genes: list[AnalogFourPatchGenePayload]


class AnalogFourPatchTraitPayload(TypedDict):
    key: str
    label: str
    intensity: float
    evidence: list[str]


class AnalogFourPatchGenomePayload(TypedDict):
    version: str
    device_id: str
    mode: str
    selected_track: int
    source_hash: str
    source_confidence: str
    candidate_count: int
    traits: list[AnalogFourPatchTraitPayload]
    candidates: list[AnalogFourPatchCandidatePayload]
    safety: list[str]


def build_analog_four_patch_genome(
    report: FeatureReport,
    *,
    track: int = ANALOG_FOUR_TRACK_MIN,
    candidate_count: int = ANALOG_FOUR_PATCH_CANDIDATE_MAX,
) -> AnalogFourPatchGenome:
    """Build a deterministic passive Analog Four patch genome."""

    if not isinstance(report, FeatureReport):
        raise TypeError("report must be a FeatureReport")
    if track < ANALOG_FOUR_TRACK_MIN or track > ANALOG_FOUR_TRACK_MAX:
        raise ValueError(f"track must be in {ANALOG_FOUR_TRACK_MIN}..{ANALOG_FOUR_TRACK_MAX}")
    if (
        candidate_count < ANALOG_FOUR_PATCH_CANDIDATE_MIN
        or candidate_count > ANALOG_FOUR_PATCH_CANDIDATE_MAX
    ):
        raise ValueError(
            "candidate_count must be in "
            f"{ANALOG_FOUR_PATCH_CANDIDATE_MIN}..{ANALOG_FOUR_PATCH_CANDIDATE_MAX}"
        )

    settled_report = _settle_patch_genome_report_hash(report)
    blueprint = build_reference_style_blueprint(settled_report)
    candidates = tuple(
        _build_candidate(template, track=track)
        for template in ANALOG_FOUR_PATCH_CANDIDATE_TEMPLATES[:candidate_count]
    )
    return AnalogFourPatchGenome(
        version=ANALOG_FOUR_PATCH_GENOME_VERSION,
        device_id=ANALOG_FOUR_DEVICE_ID,
        mode=ANALOG_FOUR_PATCH_MODE,
        selected_track=track,
        source_hash=settled_report.content_hash,
        source_confidence=settled_report.confidence,
        candidate_count=len(candidates),
        traits=blueprint.traits,
        candidates=candidates,
        safety=ANALOG_FOUR_PATCH_SAFETY,
    )


def analog_four_patch_genome_to_dict(
    genome: AnalogFourPatchGenome,
) -> AnalogFourPatchGenomePayload:
    """Return a stable JSON-ready representation of ``genome``."""

    if not isinstance(genome, AnalogFourPatchGenome):
        raise TypeError("genome must be an AnalogFourPatchGenome")
    return {
        "version": genome.version,
        "device_id": genome.device_id,
        "mode": genome.mode,
        "selected_track": genome.selected_track,
        "source_hash": genome.source_hash,
        "source_confidence": genome.source_confidence.value,
        "candidate_count": genome.candidate_count,
        "traits": [_genome_trait_payload(trait) for trait in genome.traits],
        "candidates": [_candidate_payload(candidate) for candidate in genome.candidates],
        "safety": list(genome.safety),
    }


def analog_four_patch_candidate_to_dict(
    candidate: AnalogFourPatchCandidate,
) -> AnalogFourPatchCandidatePayload:
    """Return a stable JSON-ready representation of ``candidate``."""

    if not isinstance(candidate, AnalogFourPatchCandidate):
        raise TypeError("candidate must be an AnalogFourPatchCandidate")
    return _candidate_payload(candidate)


def _settle_patch_genome_report_hash(report: FeatureReport) -> FeatureReport:
    digest = report.content_hash or compute_feature_report_hash(report)
    if digest == report.content_hash:
        return report
    return replace(report, content_hash=digest)


def _build_candidate(
    template: AnalogFourPatchCandidateTemplateSpec,
    *,
    track: int,
) -> AnalogFourPatchCandidate:
    genes = tuple(
        sorted(
            (_build_gene(gene_template, track=track) for gene_template in template.genes),
            key=_gene_sort_key,
        )
    )
    return AnalogFourPatchCandidate(
        column=template.column,
        label=template.label,
        role=template.role,
        closeness=template.closeness,
        genes=genes,
    )


def _build_gene(
    template: AnalogFourPatchGeneTemplateSpec,
    *,
    track: int,
) -> AnalogFourPatchGene:
    return AnalogFourPatchGene(
        track=track,
        family=template.family,
        value=make_a4_patch_value(template.parameter, screen_target=template.screen_target),
        rationale=template.rationale,
        confidence=template.confidence,
    )


def _gene_sort_key(gene: AnalogFourPatchGene) -> tuple[int, str, str, str]:
    return (
        ANALOG_FOUR_PATCH_FAMILY_ORDER.index(gene.family),
        gene.value.section,
        gene.value.encoder,
        gene.value.parameter,
    )


def _genome_trait_payload(trait: ReferenceTrait) -> AnalogFourPatchTraitPayload:
    return {
        "key": trait.key,
        "label": trait.label,
        "intensity": trait.intensity,
        "evidence": list(trait.evidence),
    }


def _candidate_payload(candidate: AnalogFourPatchCandidate) -> AnalogFourPatchCandidatePayload:
    return {
        "column": candidate.column,
        "label": candidate.label,
        "role": candidate.role,
        "closeness": candidate.closeness,
        "genes": [_gene_payload(gene) for gene in candidate.genes],
    }


def _gene_payload(gene: AnalogFourPatchGene) -> AnalogFourPatchGenePayload:
    return {
        "track": gene.track,
        "family": gene.family,
        "rationale": gene.rationale,
        "confidence": gene.confidence,
        "value": _patch_value_payload(gene.value),
    }


def _patch_value_payload(value: AnalogFourPatchValue) -> AnalogFourPatchValuePayload:
    return {
        "parameter": value.parameter,
        "section": value.section,
        "encoder": value.encoder,
        "screen_value": value.screen_value,
        "midi_value": value.midi_value,
        "cc_msb": value.cc_msb,
        "cc_lsb": value.cc_lsb,
        "nrpn_address": list(value.nrpn_address) if value.nrpn_address is not None else None,
        "transport_status": value.transport_status,
        "dial_direction": value.dial_direction,
    }


__all__ = [
    "ANALOG_FOUR_DEVICE_ID",
    "ANALOG_FOUR_PATCH_CANDIDATE_MAX",
    "ANALOG_FOUR_PATCH_CANDIDATE_MIN",
    "ANALOG_FOUR_PATCH_FAMILY_ORDER",
    "ANALOG_FOUR_PATCH_GENOME_VERSION",
    "ANALOG_FOUR_PATCH_MODE",
    "ANALOG_FOUR_PATCH_SAFETY",
    "ANALOG_FOUR_TRACK_MAX",
    "ANALOG_FOUR_TRACK_MIN",
    "AnalogFourPatchCandidate",
    "AnalogFourPatchCandidatePayload",
    "AnalogFourPatchGene",
    "AnalogFourPatchGenePayload",
    "AnalogFourPatchGenome",
    "AnalogFourPatchGenomePayload",
    "AnalogFourPatchTraitPayload",
    "AnalogFourPatchValuePayload",
    "analog_four_patch_candidate_to_dict",
    "analog_four_patch_genome_to_dict",
    "build_analog_four_patch_genome",
]
