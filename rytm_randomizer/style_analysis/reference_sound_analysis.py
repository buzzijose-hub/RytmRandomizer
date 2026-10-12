"""Strict persistence adapters for the existing measured audio contracts."""

from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Final, TypedDict, cast

from ..guardrails.input_validation import (
    require_float,
    require_int,
    require_object,
    require_sequence,
    require_text,
)
from ..guardrails.schema import Confidence, SourceType
from .extractor import (
    AudioDnaEvidence,
    AudioDnaEvidencePayload,
    AudioFeatureAnalysis,
    AudioSynthesisFeatures,
    AudioSynthesisFeaturesPayload,
    audio_dna_evidence_to_dict,
    audio_synthesis_features_to_dict,
)
from .feature_report import FeatureReport, FeatureReportPayload, feature_report_to_dict

_MAX_SOUND_TEXT_LENGTH: Final[int] = 1024
_MAX_SOUND_SCOPE_FIELDS: Final[int] = 256
_MAX_SOUND_ENERGY_ARC: Final[int] = 32


class ReferenceSoundAnalysisPayload(TypedDict):
    report: FeatureReportPayload
    features: AudioSynthesisFeaturesPayload
    evidence: AudioDnaEvidencePayload


def sound_mapping(value: object) -> Mapping[str, object]:
    data = require_object(value, "Reference-sound record", ValueError)
    if not isinstance(value, dict):
        raise ValueError("Reference-sound record is not an object.")
    return data


def sound_text(value: object) -> str:
    text = require_text(value, "Reference-sound text field", ValueError)
    if not text or len(text) > _MAX_SOUND_TEXT_LENGTH:
        raise ValueError("Reference-sound record has an invalid text field.")
    return text


def sound_number(value: object) -> float:
    try:
        number = require_float(value, "Reference-sound numeric field", ValueError)
    except OverflowError as exc:
        raise ValueError("Reference-sound numeric field is too large.") from exc
    if not math.isfinite(number):
        raise ValueError("Reference-sound record has an invalid numeric field.")
    return number


def sound_integer(value: object) -> int:
    return require_int(value, "Reference-sound integer field", ValueError)


def sound_string_tuple(value: object) -> tuple[str, ...]:
    items = require_sequence(value, "Reference-sound controls", ValueError, kind="list")
    if len(items) > _MAX_SOUND_SCOPE_FIELDS:
        raise ValueError("Reference-sound controls must be a bounded list.")
    values = tuple(sound_text(item) for item in items)
    if len(set(values)) != len(values):
        raise ValueError("Reference-sound controls cannot contain duplicates.")
    return values


def sound_analysis_to_dict(analysis: AudioFeatureAnalysis) -> ReferenceSoundAnalysisPayload:
    return {
        "report": feature_report_to_dict(analysis.feature_report),
        "features": audio_synthesis_features_to_dict(analysis.synthesis_features),
        "evidence": audio_dna_evidence_to_dict(analysis.dna_evidence),
    }


def sound_features_from_dict(value: object) -> AudioSynthesisFeatures:
    data = sound_mapping(value)
    return AudioSynthesisFeatures(
        audio_sha256=sound_text(data["audio_sha256"]),
        duration=sound_number(data["duration"]),
        attack=sound_number(data["attack"]),
        decay=sound_number(data["decay"]),
        sustain=sound_number(data["sustain"]),
        tail=sound_number(data["tail"]),
        brightness=sound_number(data["brightness"]),
        spectral_flatness=sound_number(data["spectral_flatness"]),
        noise=sound_number(data["noise"]),
        low_end=sound_number(data["low_end"]),
        harmonicity=sound_number(data["harmonicity"]),
        transient=sound_number(data["transient"]),
        modulation=sound_number(data["modulation"]),
    )


def sound_analysis_from_dict(value: object) -> AudioFeatureAnalysis:
    data = sound_mapping(value)
    report = sound_mapping(data["report"])
    evidence = sound_mapping(data["evidence"])
    arc = report["energy_arc"]
    if not isinstance(arc, list) or len(cast(list[object], arc)) > _MAX_SOUND_ENERGY_ARC:
        raise ValueError("Reference-sound energy measurements are invalid.")
    frequency = evidence["dominant_frequency_hz"]
    note = evidence["dominant_note"]
    return AudioFeatureAnalysis(
        FeatureReport(
            source_type=SourceType(sound_text(report["source_type"])),
            confidence=Confidence(sound_text(report["confidence"])),
            bpm=sound_number(report["bpm"]),
            tempo_stability=sound_number(report["tempo_stability"]),
            kick_density=sound_number(report["kick_density"]),
            percussion_density=sound_number(report["percussion_density"]),
            low_end_weight=sound_number(report["low_end_weight"]),
            spectral_brightness=sound_number(report["spectral_brightness"]),
            texture_noise=sound_number(report["texture_noise"]),
            energy_arc=tuple(sound_number(item) for item in cast(list[object], arc)),
            content_hash=sound_text(report["content_hash"]),
            derived_at=sound_text(report["derived_at"]),
        ),
        sound_features_from_dict(data["features"]),
        AudioDnaEvidence(
            dominant_frequency_hz=None if frequency is None else sound_number(frequency),
            dominant_note=None if note is None else sound_text(note),
            pitch_confidence=sound_number(evidence["pitch_confidence"]),
            tonal_stability=sound_number(evidence["tonal_stability"]),
            spectral_movement=sound_number(evidence["spectral_movement"]),
        ),
    )
