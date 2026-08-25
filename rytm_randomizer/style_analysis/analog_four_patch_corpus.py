"""Passive Analog Four patch capture-corpus matcher.

The matcher is the first corpus-shaped step toward Synthplant-like
audio-to-patch intelligence for Analog Four MKII. It can rank real captured
A4 audio/patch examples when supplied, and otherwise falls back to clearly
labeled synthetic starter vectors from the current patch templates.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Final, cast

from ..data.analog_four_patch_corpus import (
    ANALOG_FOUR_PATCH_CORPUS_STARTER_SPECS,
    AnalogFourPatchCorpusStarterSpec,
)
from ..guardrails.schema import Confidence, SourceType
from .analog_four_patch_genome import (
    ANALOG_FOUR_DEVICE_ID,
    ANALOG_FOUR_PATCH_CANDIDATE_MAX,
    ANALOG_FOUR_PATCH_CANDIDATE_MIN,
    ANALOG_FOUR_TRACK_MAX,
    ANALOG_FOUR_TRACK_MIN,
    build_analog_four_patch_genome,
)
from .feature_report import FeatureReport, compute_feature_report_hash
from .runtime_types import require_runtime_type

ANALOG_FOUR_PATCH_CORPUS_VERSION: Final[str] = "analog-four-patch-corpus-v1"
ANALOG_FOUR_PATCH_CORPUS_MODE: Final[str] = "single-sound-capture-corpus"
ANALOG_FOUR_PATCH_CORPUS_SOURCE_SYNTHETIC: Final[str] = "synthetic-template"
ANALOG_FOUR_PATCH_CORPUS_SOURCE_CAPTURED: Final[str] = "captured-hardware"
ANALOG_FOUR_PATCH_CORPUS_LIMIT_MIN: Final[int] = 1
ANALOG_FOUR_PATCH_CORPUS_LIMIT_MAX: Final[int] = 16
ANALOG_FOUR_PATCH_CORPUS_SAFETY: Final[tuple[str, ...]] = (
    "passive read-only patch capture corpus",
    "no MIDI port opened",
    "no MIDI sent",
    "no SysEx written",
    "no hardware state captured",
    "synthetic starter entries are not trained hardware evidence",
    "captured entries are ranked as evidence only until operator validation",
)
_STARTER_DERIVED_AT: Final[str] = "2026-07-03T00:00:00Z"
_FEATURE_WEIGHTS: Final[tuple[tuple[str, float], ...]] = (
    ("tempo_stability", 0.10),
    ("kick_density", 0.10),
    ("percussion_density", 0.13),
    ("low_end_weight", 0.15),
    ("spectral_brightness", 0.18),
    ("texture_noise", 0.16),
)
_BPM_WEIGHT: Final[float] = 0.10
_ENERGY_WEIGHT: Final[float] = 0.08
_BPM_NORMALIZATION: Final[float] = 60.0
_MIN_CAPTURED_READY_COUNT: Final[int] = 4


@dataclass(frozen=True)
class AnalogFourPatchCorpusEntry:
    """One A4 patch/audio example in the matching corpus."""

    entry_id: str
    label: str
    source_kind: str
    selected_track: int
    selected_candidate: int
    selected_label: str
    source_hash: str
    feature_report: FeatureReport
    patch_parameters: tuple[str, ...]
    capture_notes: tuple[str, ...]


@dataclass(frozen=True)
class AnalogFourPatchCorpusMatch:
    """Ranked nearest-neighbor match for one corpus entry."""

    rank: int
    entry_id: str
    label: str
    source_kind: str
    selected_track: int
    selected_candidate: int
    selected_label: str
    similarity: int
    distance: float
    bpm_delta: float
    brightness_delta: float
    noise_delta: float
    patch_parameters: tuple[str, ...]
    capture_notes: tuple[str, ...]


@dataclass(frozen=True)
class AnalogFourPatchCorpusSummary:
    """Readiness summary for the ranked corpus."""

    total_entries: int
    captured_count: int
    synthetic_count: int
    readiness: str


@dataclass(frozen=True)
class AnalogFourPatchCorpusMatchPacket:
    """Passive nearest-match packet for A4 patch-corpus learning."""

    version: str
    device_id: str
    mode: str
    selected_track: int
    source_hash: str
    source_confidence: str
    match_count: int
    recommended_candidate: int
    recommended_label: str
    match_summary: AnalogFourPatchCorpusSummary
    matches: tuple[AnalogFourPatchCorpusMatch, ...]
    calibration_gaps: tuple[str, ...]
    safety: tuple[str, ...]


def _require_corpus_feature_report(value: object, *, name: str) -> FeatureReport:
    return require_runtime_type(value, FeatureReport, f"{name} must be a FeatureReport")


def _require_corpus_capture_notes(value: object) -> tuple[str, ...]:
    if not isinstance(value, tuple):
        raise TypeError("capture_notes must be a tuple")
    return cast(tuple[str, ...], value)


def _require_corpus_entries(value: object) -> tuple[AnalogFourPatchCorpusEntry, ...]:
    if not isinstance(value, tuple):
        raise TypeError("entries must be a tuple")
    return cast(tuple[AnalogFourPatchCorpusEntry, ...], value)


def _require_corpus_match_packet(value: object) -> AnalogFourPatchCorpusMatchPacket:
    return require_runtime_type(
        value,
        AnalogFourPatchCorpusMatchPacket,
        "packet must be an AnalogFourPatchCorpusMatchPacket",
    )


def build_starter_analog_four_patch_corpus_entries(
    *,
    track: int = ANALOG_FOUR_TRACK_MIN,
) -> tuple[AnalogFourPatchCorpusEntry, ...]:
    """Return synthetic starter entries for all four patch candidates."""

    _validate_track(track)
    return tuple(
        build_analog_four_patch_corpus_entry(
            entry_id=spec.entry_id,
            label=spec.label,
            source_kind=ANALOG_FOUR_PATCH_CORPUS_SOURCE_SYNTHETIC,
            feature_report=_feature_report_from_starter_spec(spec),
            track=track,
            selected_candidate=spec.selected_candidate,
            capture_notes=spec.capture_notes,
        )
        for spec in ANALOG_FOUR_PATCH_CORPUS_STARTER_SPECS
    )


def build_analog_four_patch_corpus_entry(
    *,
    entry_id: str,
    label: str,
    source_kind: str,
    feature_report: FeatureReport,
    track: int,
    selected_candidate: int,
    capture_notes: tuple[str, ...],
) -> AnalogFourPatchCorpusEntry:
    """Build one typed corpus entry from a measured A4 example."""

    settled_feature_report = _require_corpus_feature_report(
        feature_report,
        name="feature_report",
    )
    settled_capture_notes = _require_corpus_capture_notes(capture_notes)
    _validate_track(track)
    _validate_candidate(selected_candidate)
    if not entry_id:
        raise ValueError("entry_id must not be empty")
    if not label:
        raise ValueError("label must not be empty")
    if not source_kind:
        raise ValueError("source_kind must not be empty")

    settled_report = _settle_feature_report_hash(settled_feature_report)
    genome = build_analog_four_patch_genome(settled_report, track=track)
    selected_patch = genome.candidates[selected_candidate - 1]
    return AnalogFourPatchCorpusEntry(
        entry_id=entry_id,
        label=label,
        source_kind=source_kind,
        selected_track=track,
        selected_candidate=selected_candidate,
        selected_label=selected_patch.label,
        source_hash=settled_report.content_hash,
        feature_report=settled_report,
        patch_parameters=tuple(gene.value.parameter for gene in selected_patch.genes),
        capture_notes=settled_capture_notes,
    )


def build_analog_four_patch_corpus_match_packet(
    reference_report: FeatureReport,
    *,
    entries: tuple[AnalogFourPatchCorpusEntry, ...],
    limit: int = 4,
) -> AnalogFourPatchCorpusMatchPacket:
    """Rank a reference against A4 patch-corpus entries."""

    settled_reference_report = _require_corpus_feature_report(
        reference_report,
        name="reference_report",
    )
    settled_entries = _require_corpus_entries(entries)
    _validate_limit(limit)

    settled_reference = _settle_feature_report_hash(settled_reference_report)
    corpus_entries = (
        settled_entries
        if settled_entries
        else build_starter_analog_four_patch_corpus_entries(track=ANALOG_FOUR_TRACK_MIN)
    )
    matches = tuple(
        replace(match, rank=rank)
        for rank, match in enumerate(
            sorted(
                (_build_match(settled_reference, entry) for entry in corpus_entries),
                key=lambda item: (
                    -item.similarity,
                    _source_sort_key(item.source_kind),
                    item.entry_id,
                ),
            )[:limit],
            start=1,
        )
    )
    summary = _build_match_summary(corpus_entries)
    recommended = matches[0]
    return AnalogFourPatchCorpusMatchPacket(
        version=ANALOG_FOUR_PATCH_CORPUS_VERSION,
        device_id=ANALOG_FOUR_DEVICE_ID,
        mode=ANALOG_FOUR_PATCH_CORPUS_MODE,
        selected_track=recommended.selected_track,
        source_hash=settled_reference.content_hash,
        source_confidence=settled_reference.confidence.value,
        match_count=len(matches),
        recommended_candidate=recommended.selected_candidate,
        recommended_label=recommended.selected_label,
        match_summary=summary,
        matches=matches,
        calibration_gaps=_build_calibration_gaps(corpus_entries),
        safety=ANALOG_FOUR_PATCH_CORPUS_SAFETY,
    )


def analog_four_patch_corpus_match_packet_to_dict(
    packet: AnalogFourPatchCorpusMatchPacket,
) -> dict[str, object]:
    """Return a stable JSON-ready representation of ``packet``."""

    packet = _require_corpus_match_packet(packet)
    return {
        "version": packet.version,
        "device_id": packet.device_id,
        "mode": packet.mode,
        "selected_track": packet.selected_track,
        "source_hash": packet.source_hash,
        "source_confidence": packet.source_confidence,
        "match_count": packet.match_count,
        "recommended_candidate": packet.recommended_candidate,
        "recommended_label": packet.recommended_label,
        "match_summary": _summary_payload(packet.match_summary),
        "matches": [_match_payload(match) for match in packet.matches],
        "calibration_gaps": list(packet.calibration_gaps),
        "safety": list(packet.safety),
    }


def _feature_report_from_starter_spec(spec: AnalogFourPatchCorpusStarterSpec) -> FeatureReport:
    report = FeatureReport(
        source_type=SourceType.FACTORY_SOUND_STUDY,
        confidence=Confidence.MEDIUM,
        bpm=spec.bpm,
        tempo_stability=spec.tempo_stability,
        kick_density=spec.kick_density,
        percussion_density=spec.percussion_density,
        low_end_weight=spec.low_end_weight,
        spectral_brightness=spec.spectral_brightness,
        texture_noise=spec.texture_noise,
        energy_arc=spec.energy_arc,
        content_hash="",
        derived_at=_STARTER_DERIVED_AT,
    )
    return _settle_feature_report_hash(report)


def _settle_feature_report_hash(report: FeatureReport) -> FeatureReport:
    digest = report.content_hash or compute_feature_report_hash(report)
    if digest == report.content_hash:
        return report
    return replace(report, content_hash=digest)


def _build_match(
    reference: FeatureReport,
    entry: AnalogFourPatchCorpusEntry,
) -> AnalogFourPatchCorpusMatch:
    effective_reference = _effective_reference_report(reference)
    distance = feature_distance(effective_reference, entry.feature_report)
    similarity = _similarity_from_distance(distance)
    return AnalogFourPatchCorpusMatch(
        rank=0,
        entry_id=entry.entry_id,
        label=entry.label,
        source_kind=entry.source_kind,
        selected_track=entry.selected_track,
        selected_candidate=entry.selected_candidate,
        selected_label=entry.selected_label,
        similarity=similarity,
        distance=round(distance, 6),
        bpm_delta=round(abs(effective_reference.bpm - entry.feature_report.bpm), 3),
        brightness_delta=round(
            abs(effective_reference.spectral_brightness - entry.feature_report.spectral_brightness),
            3,
        ),
        noise_delta=round(
            abs(effective_reference.texture_noise - entry.feature_report.texture_noise), 3
        ),
        patch_parameters=entry.patch_parameters,
        capture_notes=entry.capture_notes,
    )


def _effective_reference_report(reference: FeatureReport) -> FeatureReport:
    if not _is_empty_feature_report(reference):
        return reference
    first_spec = ANALOG_FOUR_PATCH_CORPUS_STARTER_SPECS[0]
    return replace(
        reference,
        bpm=first_spec.bpm,
        tempo_stability=first_spec.tempo_stability,
        kick_density=first_spec.kick_density,
        percussion_density=first_spec.percussion_density,
        low_end_weight=first_spec.low_end_weight,
        spectral_brightness=first_spec.spectral_brightness,
        texture_noise=first_spec.texture_noise,
        energy_arc=first_spec.energy_arc,
    )


def _is_empty_feature_report(report: FeatureReport) -> bool:
    return (
        report.bpm == 0.0
        and report.tempo_stability == 0.0
        and report.kick_density == 0.0
        and report.percussion_density == 0.0
        and report.low_end_weight == 0.0
        and report.spectral_brightness == 0.0
        and report.texture_noise == 0.0
        and all(value == 0.0 for value in report.energy_arc)
    )


def feature_distance(reference: FeatureReport, candidate: FeatureReport) -> float:
    """Return the established weighted distance between two feature reports."""

    distance = _BPM_WEIGHT * _normalized_bpm_delta(reference.bpm, candidate.bpm)
    for field_name, weight in _FEATURE_WEIGHTS:
        distance += weight * abs(
            float(getattr(reference, field_name)) - float(getattr(candidate, field_name))
        )
    distance += _ENERGY_WEIGHT * _energy_arc_distance(reference.energy_arc, candidate.energy_arc)
    return min(1.0, max(0.0, distance))


def _normalized_bpm_delta(left: float, right: float) -> float:
    return min(1.0, abs(left - right) / _BPM_NORMALIZATION)


def _energy_arc_distance(left: tuple[float, ...], right: tuple[float, ...]) -> float:
    if not left or not right:
        return 1.0
    count = min(len(left), len(right))
    return sum(abs(left[index] - right[index]) for index in range(count)) / float(count)


def _similarity_from_distance(distance: float) -> int:
    return max(0, min(100, int(round((1.0 - distance) * 100.0))))


def _source_sort_key(source_kind: str) -> int:
    if source_kind == ANALOG_FOUR_PATCH_CORPUS_SOURCE_CAPTURED:
        return 0
    return 1


def _build_match_summary(
    entries: tuple[AnalogFourPatchCorpusEntry, ...],
) -> AnalogFourPatchCorpusSummary:
    captured_count = sum(
        1 for entry in entries if entry.source_kind == ANALOG_FOUR_PATCH_CORPUS_SOURCE_CAPTURED
    )
    synthetic_count = sum(
        1 for entry in entries if entry.source_kind == ANALOG_FOUR_PATCH_CORPUS_SOURCE_SYNTHETIC
    )
    return AnalogFourPatchCorpusSummary(
        total_entries=len(entries),
        captured_count=captured_count,
        synthetic_count=synthetic_count,
        readiness=_readiness_label(captured_count),
    )


def _readiness_label(captured_count: int) -> str:
    if captured_count == 0:
        return "synthetic-starter-only"
    if captured_count < _MIN_CAPTURED_READY_COUNT:
        return "partial-hardware-corpus"
    return "hardware-corpus-ready"


def _build_calibration_gaps(
    entries: tuple[AnalogFourPatchCorpusEntry, ...],
) -> tuple[str, ...]:
    captured_count = sum(
        1 for entry in entries if entry.source_kind == ANALOG_FOUR_PATCH_CORPUS_SOURCE_CAPTURED
    )
    if captured_count == 0:
        return tuple(
            f"capture real A4 audio for candidate {spec.selected_candidate}"
            for spec in ANALOG_FOUR_PATCH_CORPUS_STARTER_SPECS
        )
    if captured_count < _MIN_CAPTURED_READY_COUNT:
        needed = _MIN_CAPTURED_READY_COUNT - captured_count
        needed_label = "three" if needed == 3 else str(needed)
        return (
            "capture at least "
            f"{needed_label} more hardware examples across brighter/noisy/rounder variations",
        )
    return ("review outlier hardware captures before model-training promotion",)


def _validate_track(track: int) -> None:
    if track < ANALOG_FOUR_TRACK_MIN or track > ANALOG_FOUR_TRACK_MAX:
        raise ValueError(f"track must be in {ANALOG_FOUR_TRACK_MIN}..{ANALOG_FOUR_TRACK_MAX}")


def _validate_candidate(selected_candidate: int) -> None:
    if (
        selected_candidate < ANALOG_FOUR_PATCH_CANDIDATE_MIN
        or selected_candidate > ANALOG_FOUR_PATCH_CANDIDATE_MAX
    ):
        raise ValueError(
            "candidate must be in "
            f"{ANALOG_FOUR_PATCH_CANDIDATE_MIN}..{ANALOG_FOUR_PATCH_CANDIDATE_MAX}"
        )


def _validate_limit(limit: int) -> None:
    if limit < ANALOG_FOUR_PATCH_CORPUS_LIMIT_MIN or limit > ANALOG_FOUR_PATCH_CORPUS_LIMIT_MAX:
        raise ValueError(
            "limit must be in "
            f"{ANALOG_FOUR_PATCH_CORPUS_LIMIT_MIN}..{ANALOG_FOUR_PATCH_CORPUS_LIMIT_MAX}"
        )


def _summary_payload(summary: AnalogFourPatchCorpusSummary) -> dict[str, object]:
    return {
        "total_entries": summary.total_entries,
        "captured_count": summary.captured_count,
        "synthetic_count": summary.synthetic_count,
        "readiness": summary.readiness,
    }


def _match_payload(match: AnalogFourPatchCorpusMatch) -> dict[str, object]:
    return {
        "rank": match.rank,
        "entry_id": match.entry_id,
        "label": match.label,
        "source_kind": match.source_kind,
        "selected_track": match.selected_track,
        "selected_candidate": match.selected_candidate,
        "selected_label": match.selected_label,
        "similarity": match.similarity,
        "distance": match.distance,
        "bpm_delta": match.bpm_delta,
        "brightness_delta": match.brightness_delta,
        "noise_delta": match.noise_delta,
        "patch_parameters": list(match.patch_parameters),
        "capture_notes": list(match.capture_notes),
    }


__all__ = [
    "ANALOG_FOUR_PATCH_CORPUS_LIMIT_MAX",
    "ANALOG_FOUR_PATCH_CORPUS_LIMIT_MIN",
    "ANALOG_FOUR_PATCH_CORPUS_MODE",
    "ANALOG_FOUR_PATCH_CORPUS_SAFETY",
    "ANALOG_FOUR_PATCH_CORPUS_SOURCE_CAPTURED",
    "ANALOG_FOUR_PATCH_CORPUS_SOURCE_SYNTHETIC",
    "ANALOG_FOUR_PATCH_CORPUS_VERSION",
    "AnalogFourPatchCorpusEntry",
    "AnalogFourPatchCorpusMatch",
    "AnalogFourPatchCorpusMatchPacket",
    "AnalogFourPatchCorpusSummary",
    "analog_four_patch_corpus_match_packet_to_dict",
    "build_analog_four_patch_corpus_entry",
    "build_analog_four_patch_corpus_match_packet",
    "build_starter_analog_four_patch_corpus_entries",
    "feature_distance",
]
