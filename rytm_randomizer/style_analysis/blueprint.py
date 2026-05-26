"""Passive reference-style blueprint translation.

This module turns a measured :class:`FeatureReport` into a deterministic,
mock-safe starting point for the Analog Rytm plus Analog Four. It never opens
ports, sends MIDI, reads files, or attempts to recreate source material.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, replace
from typing import Final

from rytm_randomizer.guardrails.schema import Confidence, SourceType

from .feature_report import FeatureReport, compute_feature_report_hash

BLUEPRINT_VERSION: Final[str] = "reference-style-blueprint-v1"
INFLUENCE_RULE: Final[str] = "inspired-starting-point-not-replica"
SAFETY_FLAGS: Final[tuple[str, ...]] = (
    "passive read-only blueprint",
    "no MIDI port opened",
    "no MIDI sent",
    "no hardware mutation",
    "hardware entrypoint remains locked",
    "influence only; no melody, pattern, or patch copying",
)


@dataclass(frozen=True)
class ReferenceTrait:
    """One normalized trait inferred from a reference measurement."""

    key: str
    label: str
    intensity: int
    evidence: tuple[str, ...]


@dataclass(frozen=True)
class RytmPadBlueprint:
    """A passive recommendation for one Analog Rytm pad."""

    pad: int
    role: str
    engine_family: str
    mutation_depth: int
    parameter_focus: tuple[str, ...]
    safety: str


@dataclass(frozen=True)
class AnalogFourTrackBlueprint:
    """A passive recommendation for one Analog Four track."""

    track: int
    role: str
    voice_intent: str
    mutation_depth: int
    parameter_focus: tuple[str, ...]
    modulation: str


@dataclass(frozen=True)
class ReferenceStyleBlueprint:
    """Deterministic dual-device plan derived from a :class:`FeatureReport`."""

    version: str
    source_hash: str
    source_type: SourceType
    source_confidence: Confidence
    readiness: str
    influence_rule: str
    traits: tuple[ReferenceTrait, ...]
    rytm_pads: tuple[RytmPadBlueprint, ...]
    analog_four_tracks: tuple[AnalogFourTrackBlueprint, ...]
    safety: tuple[str, ...]
    blueprint_hash: str


@dataclass(frozen=True)
class _RytmPadTemplate:
    pad: int
    role: str
    engine_family: str
    trait_key: str
    weight: float
    parameter_focus: tuple[str, ...]


@dataclass(frozen=True)
class _AnalogFourTemplate:
    track: int
    role: str
    voice_intent: str
    trait_key: str
    weight: float
    parameter_focus: tuple[str, ...]
    modulation: str


_RYTM_PAD_TEMPLATES: Final[tuple[_RytmPadTemplate, ...]] = (
    _RytmPadTemplate(
        1,
        "kick foundation",
        "BD Hard / low-end anchor",
        "low_end_pressure",
        0.90,
        ("SRC Tune", "SRC Decay", "AMP Decay", "FLT Frequency"),
    ),
    _RytmPadTemplate(
        2,
        "snare pressure",
        "SD Hard / pressure snap",
        "groove_density",
        0.78,
        ("SRC Snap", "SRC Tune", "AMP Overdrive", "AMP Decay"),
    ),
    _RytmPadTemplate(
        3,
        "closed hat grid",
        "CH / dry tick",
        "groove_density",
        0.72,
        ("SRC Tune", "SRC Decay", "FLT Frequency", "AMP Decay"),
    ),
    _RytmPadTemplate(
        4,
        "open hat air",
        "OH / controlled air",
        "texture_noise",
        0.66,
        ("SRC Decay", "FLT Frequency", "FLT Resonance", "AMP Reverb Send"),
    ),
    _RytmPadTemplate(
        5,
        "low tom support",
        "BT / rolling body",
        "low_end_pressure",
        0.55,
        ("SRC Tune", "SRC Decay", "AMP Hold", "AMP Decay"),
    ),
    _RytmPadTemplate(
        6,
        "mid tom movement",
        "LT / groove fill",
        "arrangement_energy",
        0.54,
        ("SRC Tune", "SRC Decay", "FLT Env Depth", "AMP Decay"),
    ),
    _RytmPadTemplate(
        7,
        "high tom response",
        "MT / phrase lift",
        "arrangement_energy",
        0.52,
        ("SRC Tune", "SRC Decay", "FLT Frequency", "AMP Delay Send"),
    ),
    _RytmPadTemplate(
        8,
        "limited high accent",
        "HT / risk-capped hit",
        "metallic_pressure",
        0.40,
        ("SRC Tune", "FLT Resonance", "AMP Overdrive"),
    ),
    _RytmPadTemplate(
        9,
        "clap punctuation",
        "CP / sparse accent",
        "groove_density",
        0.58,
        ("SRC Decay", "SRC Snap", "AMP Reverb Send", "AMP Pan"),
    ),
    _RytmPadTemplate(
        10,
        "riser or noise fx",
        "RS / transition texture",
        "texture_noise",
        0.48,
        ("FLT Frequency", "FLT Resonance", "AMP Delay Send", "AMP Reverb Send"),
    ),
    _RytmPadTemplate(
        11,
        "synth percussion",
        "SY Raw / metallic texture",
        "metallic_pressure",
        0.84,
        ("SRC Balance", "SRC Detune", "LFO Depth", "FLT Frequency"),
    ),
    _RytmPadTemplate(
        12,
        "secondary body kick",
        "BD Acoustic / body accent",
        "low_end_pressure",
        0.62,
        ("SRC Tune", "SRC Decay", "SRC Impact", "AMP Hold"),
    ),
)

_ANALOG_FOUR_TEMPLATES: Final[tuple[_AnalogFourTemplate, ...]] = (
    _AnalogFourTemplate(
        1,
        "bass foundation",
        "sub bass movement",
        "low_end_pressure",
        0.82,
        ("Oscillator Tune", "Filter 1 Frequency", "Filter 2 Base", "Amp Decay"),
        "slow envelope-to-filter motion with velocity-safe depth",
    ),
    _AnalogFourTemplate(
        2,
        "metallic lead stab",
        "metallic stab",
        "metallic_pressure",
        0.76,
        ("Oscillator Sync", "Oscillator Detune", "Filter 1 Resonance", "Overdrive"),
        "short trig envelope into sync and resonance",
    ),
    _AnalogFourTemplate(
        3,
        "noise pad texture",
        "noisy chord texture",
        "texture_noise",
        0.64,
        ("Noise Level", "Filter 1 Frequency", "Chorus Send", "Reverb Send"),
        "subtle LFO drift on noise color and filter frequency",
    ),
    _AnalogFourTemplate(
        4,
        "performance macro lane",
        "arrangement pressure macro",
        "arrangement_energy",
        0.58,
        ("Filter 1 Frequency", "Filter 1 Resonance", "Delay Send", "Amp Level"),
        "macro-controlled pressure rise across phrase sections",
    ),
)


def build_reference_style_blueprint(report: FeatureReport) -> ReferenceStyleBlueprint:
    """Translate a measured reference into a passive dual-device blueprint."""

    if not isinstance(report, FeatureReport):
        raise TypeError("report must be a FeatureReport")

    settled_report = _settle_report_hash(report)
    traits = _build_traits(settled_report)
    trait_scores = {trait.key: trait.intensity for trait in traits}
    readiness = _readiness_for(settled_report.confidence)
    rytm_pads = tuple(
        _build_rytm_pad(template, trait_scores, settled_report.confidence)
        for template in _RYTM_PAD_TEMPLATES
    )
    analog_four_tracks = tuple(
        _build_analog_four_track(template, trait_scores, settled_report.confidence)
        for template in _ANALOG_FOUR_TEMPLATES
    )
    blueprint_without_hash = ReferenceStyleBlueprint(
        version=BLUEPRINT_VERSION,
        source_hash=settled_report.content_hash,
        source_type=settled_report.source_type,
        source_confidence=settled_report.confidence,
        readiness=readiness,
        influence_rule=INFLUENCE_RULE,
        traits=traits,
        rytm_pads=rytm_pads,
        analog_four_tracks=analog_four_tracks,
        safety=SAFETY_FLAGS,
        blueprint_hash="",
    )
    return replace(
        blueprint_without_hash,
        blueprint_hash=_compute_blueprint_hash(blueprint_without_hash),
    )


def reference_style_blueprint_to_dict(
    blueprint: ReferenceStyleBlueprint,
) -> dict[str, object]:
    """Return a stable JSON-ready representation of ``blueprint``."""

    if not isinstance(blueprint, ReferenceStyleBlueprint):
        raise TypeError("blueprint must be a ReferenceStyleBlueprint")
    return _blueprint_payload(blueprint, include_hash=True)


def _settle_report_hash(report: FeatureReport) -> FeatureReport:
    digest = report.content_hash or compute_feature_report_hash(report)
    if digest == report.content_hash:
        return report
    return replace(report, content_hash=digest)


def _build_traits(report: FeatureReport) -> tuple[ReferenceTrait, ...]:
    low_end = _unit_percent(_average(report.low_end_weight, report.kick_density))
    groove = _unit_percent(_average(report.percussion_density, report.tempo_stability))
    metallic = _unit_percent(_average(report.spectral_brightness, report.texture_noise))
    texture = _unit_percent(report.texture_noise)
    arrangement = _unit_percent(_arrangement_energy(report.energy_arc))
    tempo_drive = _unit_percent(_tempo_drive(report.bpm))

    return (
        ReferenceTrait(
            "low_end_pressure",
            "Low-end pressure",
            low_end,
            ("low_end_weight", "kick_density"),
        ),
        ReferenceTrait(
            "groove_density",
            "Groove density",
            groove,
            ("percussion_density", "tempo_stability"),
        ),
        ReferenceTrait(
            "metallic_pressure",
            "Metallic pressure",
            metallic,
            ("spectral_brightness", "texture_noise"),
        ),
        ReferenceTrait(
            "texture_noise",
            "Texture and noise",
            texture,
            ("texture_noise",),
        ),
        ReferenceTrait(
            "arrangement_energy",
            "Arrangement energy",
            arrangement,
            ("energy_arc",),
        ),
        ReferenceTrait(
            "tempo_drive",
            "Tempo drive",
            tempo_drive,
            ("bpm",),
        ),
    )


def _build_rytm_pad(
    template: _RytmPadTemplate,
    trait_scores: dict[str, int],
    confidence: Confidence,
) -> RytmPadBlueprint:
    trait_score = trait_scores.get(template.trait_key, 0)
    depth = _depth_for(trait_score, template.weight, confidence)
    safety = "mock-safe; prepare before hardware send"
    if confidence is Confidence.LOW:
        safety = "mock-safe low-confidence suggestion"
    return RytmPadBlueprint(
        pad=template.pad,
        role=template.role,
        engine_family=template.engine_family,
        mutation_depth=depth,
        parameter_focus=template.parameter_focus,
        safety=safety,
    )


def _build_analog_four_track(
    template: _AnalogFourTemplate,
    trait_scores: dict[str, int],
    confidence: Confidence,
) -> AnalogFourTrackBlueprint:
    trait_score = trait_scores.get(template.trait_key, 0)
    return AnalogFourTrackBlueprint(
        track=template.track,
        role=template.role,
        voice_intent=template.voice_intent,
        mutation_depth=_depth_for(trait_score, template.weight, confidence),
        parameter_focus=template.parameter_focus,
        modulation=template.modulation,
    )


def _depth_for(intensity: int, weight: float, confidence: Confidence) -> int:
    weighted = int(round(float(intensity) * weight))
    if weighted >= 82:
        depth = 6
    elif weighted >= 68:
        depth = 5
    elif weighted >= 50:
        depth = 4
    elif weighted >= 34:
        depth = 3
    elif weighted >= 16:
        depth = 2
    else:
        depth = 1
    return min(depth, _confidence_cap(confidence))


def _confidence_cap(confidence: Confidence) -> int:
    if confidence is Confidence.HIGH:
        return 6
    if confidence is Confidence.MEDIUM:
        return 4
    return 2


def _readiness_for(confidence: Confidence) -> str:
    if confidence is Confidence.LOW:
        return "mock_safe_low_confidence"
    return "mock_safe"


def _average(*values: float) -> float:
    if not values:
        return 0.0
    return sum(_clamp_unit(value) for value in values) / float(len(values))


def _arrangement_energy(arc: tuple[float, ...]) -> float:
    if not arc:
        return 0.0
    mean_energy = _average(*arc)
    lift = _clamp_unit(arc[-1] - arc[0]) if len(arc) > 1 else 0.0
    peak = max(_clamp_unit(value) for value in arc)
    return _average(mean_energy, lift, peak)


def _tempo_drive(bpm: float) -> float:
    if bpm <= 0.0:
        return 0.0
    return _clamp_unit((bpm - 90.0) / 80.0)


def _unit_percent(value: float) -> int:
    return int(round(_clamp_unit(value) * 100.0))


def _clamp_unit(value: float) -> float:
    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return float(value)


def _compute_blueprint_hash(blueprint: ReferenceStyleBlueprint) -> str:
    payload = _blueprint_payload(blueprint, include_hash=False)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _blueprint_payload(
    blueprint: ReferenceStyleBlueprint, *, include_hash: bool
) -> dict[str, object]:
    payload: dict[str, object] = {
        "version": blueprint.version,
        "source_hash": blueprint.source_hash,
        "source_type": blueprint.source_type.value,
        "source_confidence": blueprint.source_confidence.value,
        "readiness": blueprint.readiness,
        "influence_rule": blueprint.influence_rule,
        "traits": [_trait_payload(trait) for trait in blueprint.traits],
        "rytm_pads": [_rytm_pad_payload(pad) for pad in blueprint.rytm_pads],
        "analog_four_tracks": [
            _analog_four_track_payload(track) for track in blueprint.analog_four_tracks
        ],
        "safety": list(blueprint.safety),
    }
    if include_hash:
        payload["blueprint_hash"] = blueprint.blueprint_hash
    return payload


def _trait_payload(trait: ReferenceTrait) -> dict[str, object]:
    return {
        "key": trait.key,
        "label": trait.label,
        "intensity": trait.intensity,
        "evidence": list(trait.evidence),
    }


def _rytm_pad_payload(pad: RytmPadBlueprint) -> dict[str, object]:
    return {
        "pad": pad.pad,
        "role": pad.role,
        "engine_family": pad.engine_family,
        "mutation_depth": pad.mutation_depth,
        "parameter_focus": list(pad.parameter_focus),
        "safety": pad.safety,
    }


def _analog_four_track_payload(track: AnalogFourTrackBlueprint) -> dict[str, object]:
    return {
        "track": track.track,
        "role": track.role,
        "voice_intent": track.voice_intent,
        "mutation_depth": track.mutation_depth,
        "parameter_focus": list(track.parameter_focus),
        "modulation": track.modulation,
    }


__all__ = [
    "AnalogFourTrackBlueprint",
    "BLUEPRINT_VERSION",
    "ReferenceStyleBlueprint",
    "ReferenceTrait",
    "RytmPadBlueprint",
    "build_reference_style_blueprint",
    "reference_style_blueprint_to_dict",
]
