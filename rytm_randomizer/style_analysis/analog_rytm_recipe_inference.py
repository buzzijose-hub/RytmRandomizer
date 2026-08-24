"""Passive audio-to-Analog-Rytm recipe proposals with explicit evidence gaps.

This module is intentionally upstream of saved-kit encoding.  It translates a
measured :class:`AudioFeatureAnalysis` into deterministic musical intent while
keeping machine writes, machine-specific tuning, rendering, and hardware proof
visibly separate.  It performs no file, MIDI, SysEx, or audio I/O.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from typing import Final, Literal, TypeAlias, TypedDict

from rytm_randomizer.data.al16_rytm import (
    AL16_PAD_ROLES,
    AL16_RYTM_APPROVED_TUNING,
    AL16_RYTM_WRITABLE_FIELDS,
)
from rytm_randomizer.data.rytm_machine_catalog import is_machine_allowed_on_pad

from .extractor import AudioFeatureAnalysis, AudioSynthesisFeatures
from .runtime_types import require_runtime_type

RytmRecipeScalar: TypeAlias = int | str | bool
RytmRecipeFieldStatus: TypeAlias = Literal["writable_proposal", "mapping_required"]
RytmMachineStatus: TypeAlias = Literal["compatible_mapping_required"]
RytmTuningStatus: TypeAlias = Literal["approved_tuning", "mapping_required"]

RYTM_AUDIO_RECIPE_SCHEMA_VERSION: Final[int] = 1
RYTM_RECIPE_STATUS: Final[str] = "proposal_only"
RYTM_RECIPE_INFLUENCE_POLICY: Final[str] = "reference_to_discovery"
RYTM_RECIPE_PRESERVED_PADS: Final[tuple[int, ...]] = (2, 4, 5, 7, 8, 10, 11, 12)


@dataclass(frozen=True)
class RytmAudioFeatureEvidence:
    """One normalized measurement used by a proposed parameter equation."""

    feature: str
    value: float


class RytmAudioFeatureEvidencePayload(TypedDict):
    """JSON-ready audio evidence for one proposed field."""

    feature: str
    value: float


@dataclass(frozen=True)
class RytmRecipeFieldProposal:
    """One semantic Rytm value with its exact evidence and support status."""

    path: str
    requested_value: RytmRecipeScalar
    status: RytmRecipeFieldStatus
    converter: str | None
    evidence: tuple[RytmAudioFeatureEvidence, ...]
    equation: str
    reason: str


class RytmRecipeFieldProposalPayload(TypedDict):
    """JSON-ready form of one proposed Rytm field."""

    path: str
    requested_value: RytmRecipeScalar
    status: RytmRecipeFieldStatus
    converter: str | None
    evidence: list[RytmAudioFeatureEvidencePayload]
    equation: str
    reason: str


@dataclass(frozen=True)
class RytmTuningIntent:
    """Musical pitch intent kept separate from machine-specific raw tuning."""

    target_note: str | None
    pitch_confidence: float
    tonal_stability: float
    status: RytmTuningStatus
    raw_tune: int | None
    reason: str


class RytmTuningIntentPayload(TypedDict):
    """JSON-ready form of one machine-specific tuning intent."""

    target_note: str | None
    pitch_confidence: float
    tonal_stability: float
    status: RytmTuningStatus
    raw_tune: int | None
    reason: str


@dataclass(frozen=True)
class RytmTrackRecipeProposal:
    """One stable-role pad proposal for an Analog Rytm performance recipe."""

    pad: int
    role: str
    machine_key: str
    machine_status: RytmMachineStatus
    machine_reason: str
    fields: tuple[RytmRecipeFieldProposal, ...]
    tuning: RytmTuningIntent | None = None


class RytmTrackRecipeProposalPayload(TypedDict):
    """JSON-ready form of one Rytm pad proposal."""

    pad: int
    role: str
    machine_key: str
    machine_status: RytmMachineStatus
    machine_reason: str
    fields: list[RytmRecipeFieldProposalPayload]
    tuning: RytmTuningIntentPayload | None


class AnalogRytmAudioRecipeProposalPayload(TypedDict):
    """Stable JSON-ready public payload for a passive recipe proposal."""

    schema_version: int
    recipe_id: str
    audio_sha256: str
    status: str
    influence_policy: str
    hardware_verified: bool
    codec_ready: bool
    render_required: bool
    midi_sent: bool
    tracks: list[RytmTrackRecipeProposalPayload]
    preserved_pads: list[int]
    writable_field_count: int
    mapping_required_count: int
    limitations: list[str]


@dataclass(frozen=True)
class AnalogRytmAudioRecipeProposal:
    """Deterministic proposal that makes every verification boundary explicit."""

    recipe_id: str
    audio_sha256: str
    tracks: tuple[RytmTrackRecipeProposal, ...]
    writable_field_count: int
    mapping_required_count: int
    limitations: tuple[str, ...]
    schema_version: int = RYTM_AUDIO_RECIPE_SCHEMA_VERSION
    status: str = RYTM_RECIPE_STATUS
    influence_policy: str = RYTM_RECIPE_INFLUENCE_POLICY
    hardware_verified: bool = False
    codec_ready: bool = False
    render_required: bool = True
    midi_sent: bool = False
    preserved_pads: tuple[int, ...] = RYTM_RECIPE_PRESERVED_PADS


def _evidence(
    features: AudioSynthesisFeatures,
    *names: str,
) -> tuple[RytmAudioFeatureEvidence, ...]:
    values: dict[str, float] = {
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
    return tuple(RytmAudioFeatureEvidence(name, values[name]) for name in names)


def _to_7bit(value: float) -> int:
    if not math.isfinite(value):
        raise ValueError("Rytm recipe equation must produce a finite value")
    return round(127.0 * min(1.0, max(0.0, value)))


def _field(
    *,
    pad: int,
    field_path: str,
    requested_value: RytmRecipeScalar,
    evidence: tuple[RytmAudioFeatureEvidence, ...],
    equation: str,
    unsupported_reason: str | None = None,
) -> RytmRecipeFieldProposal:
    semantic_path = f"tracks.{pad}.{field_path}"
    writable = AL16_RYTM_WRITABLE_FIELDS.get(field_path)
    if writable is not None:
        return RytmRecipeFieldProposal(
            path=semantic_path,
            requested_value=requested_value,
            status="writable_proposal",
            converter=writable.converter,
            evidence=evidence,
            equation=equation,
            reason=(
                "The saved-kit field and converter are positively mapped; the value "
                "remains a proposal until rendered, auditioned, and measured."
            ),
        )
    return RytmRecipeFieldProposal(
        path=semantic_path,
        requested_value=requested_value,
        status="mapping_required",
        converter=None,
        evidence=evidence,
        equation=equation,
        reason=unsupported_reason or "No approved saved-kit field mapping exists.",
    )


def _dry_amp_fields(
    *,
    pad: int,
    features: AudioSynthesisFeatures,
    attack: int,
    hold: int,
    decay: int,
    overdrive: int,
    volume: int,
    attack_equation: str,
    hold_equation: str,
    decay_equation: str,
    overdrive_equation: str,
    volume_equation: str,
) -> tuple[RytmRecipeFieldProposal, ...]:
    return (
        _field(
            pad=pad,
            field_path="amp.atk",
            requested_value=attack,
            evidence=_evidence(features, "attack"),
            equation=attack_equation,
        ),
        _field(
            pad=pad,
            field_path="amp.hld",
            requested_value=hold,
            evidence=_evidence(features, "sustain"),
            equation=hold_equation,
        ),
        _field(
            pad=pad,
            field_path="amp.dec",
            requested_value=decay,
            evidence=_evidence(features, "decay", "tail", "transient"),
            equation=decay_equation,
        ),
        _field(
            pad=pad,
            field_path="amp.ovr",
            requested_value=overdrive,
            evidence=_evidence(features, "low_end", "noise", "transient"),
            equation=overdrive_equation,
        ),
        _field(
            pad=pad,
            field_path="amp.del",
            requested_value=0,
            evidence=(),
            equation="0 (dry performance-bank policy)",
        ),
        _field(
            pad=pad,
            field_path="amp.rev",
            requested_value=0,
            evidence=(),
            equation="0 (dry performance-bank policy)",
        ),
        _field(
            pad=pad,
            field_path="amp.pan",
            requested_value=0,
            evidence=(),
            equation="0 (centered stable-role policy)",
        ),
        _field(
            pad=pad,
            field_path="amp.vol",
            requested_value=volume,
            evidence=_evidence(features, "low_end", "transient"),
            equation=volume_equation,
            unsupported_reason=(
                "Track volume is useful musical intent, but its saved-kit location is "
                "not positively mapped and must be preserved by an exporter."
            ),
        ),
    )


def _filter_fields(
    *,
    pad: int,
    features: AudioSynthesisFeatures,
    filter_type: str,
    frequency: int,
    resonance: int,
    frequency_equation: str,
    resonance_equation: str,
    resonance_evidence: tuple[str, ...],
) -> tuple[RytmRecipeFieldProposal, ...]:
    return (
        _field(
            pad=pad,
            field_path="filter.type",
            requested_value=filter_type,
            evidence=_evidence(features, "brightness", "low_end"),
            equation=f'"{filter_type}" (role-specific topology)',
        ),
        _field(
            pad=pad,
            field_path="filter.frq",
            requested_value=frequency,
            evidence=_evidence(features, "brightness", "low_end", "noise"),
            equation=frequency_equation,
        ),
        _field(
            pad=pad,
            field_path="filter.res",
            requested_value=resonance,
            evidence=_evidence(features, *resonance_evidence),
            equation=resonance_equation,
        ),
        _field(
            pad=pad,
            field_path="filter.env",
            requested_value=0,
            evidence=(),
            equation="0 (neutral bipolar filter-envelope intent)",
        ),
    )


def _track(
    *,
    pad: int,
    machine_key: str,
    fields: tuple[RytmRecipeFieldProposal, ...],
    tuning: RytmTuningIntent | None = None,
) -> RytmTrackRecipeProposal:
    if not is_machine_allowed_on_pad(pad, machine_key):
        raise ValueError(f"Rytm machine {machine_key!r} is not legal on pad {pad}")
    return RytmTrackRecipeProposal(
        pad=pad,
        role=AL16_PAD_ROLES[pad],
        machine_key=machine_key,
        machine_status="compatible_mapping_required",
        machine_reason=(
            "The machine is legal on this physical pad, but saved-kit machine-selection "
            "bytes are not yet positively mapped."
        ),
        fields=fields,
        tuning=tuning,
    )


def _tuning_intent(analysis: AudioFeatureAnalysis) -> RytmTuningIntent:
    evidence = analysis.dna_evidence
    target_note = evidence.dominant_note
    if target_note is None or evidence.pitch_confidence < 0.75 or evidence.tonal_stability < 0.60:
        return RytmTuningIntent(
            target_note=target_note,
            pitch_confidence=evidence.pitch_confidence,
            tonal_stability=evidence.tonal_stability,
            status="mapping_required",
            raw_tune=None,
            reason=(
                "Pitch evidence is not stable enough to request machine tuning; preserve "
                "the initialized XT Classic source value."
            ),
        )
    raw_tune = AL16_RYTM_APPROVED_TUNING.get(("xt_classic", target_note))
    if raw_tune is None:
        return RytmTuningIntent(
            target_note=target_note,
            pitch_confidence=evidence.pitch_confidence,
            tonal_stability=evidence.tonal_stability,
            status="mapping_required",
            raw_tune=None,
            reason=(
                f"Musical target {target_note} is measured, but no approved XT Classic "
                "machine-specific tuning lookup exists; no raw value was guessed."
            ),
        )
    return RytmTuningIntent(
        target_note=target_note,
        pitch_confidence=evidence.pitch_confidence,
        tonal_stability=evidence.tonal_stability,
        status="approved_tuning",
        raw_tune=raw_tune,
        reason="The target note resolved through the approved XT Classic tuning table.",
    )


def _build_tracks(analysis: AudioFeatureAnalysis) -> tuple[RytmTrackRecipeProposal, ...]:
    f = analysis.synthesis_features
    kick_filter = _filter_fields(
        pad=1,
        features=f,
        filter_type="HP2",
        frequency=_to_7bit(0.12 + 0.28 * f.brightness + 0.10 * (1.0 - f.low_end)),
        resonance=_to_7bit(0.08 + 0.18 * f.transient),
        frequency_equation="7bit(0.12 + 0.28*brightness + 0.10*(1-low_end))",
        resonance_equation="7bit(0.08 + 0.18*transient)",
        resonance_evidence=("transient",),
    )
    kick_amp = _dry_amp_fields(
        pad=1,
        features=f,
        attack=_to_7bit(0.10 * f.attack),
        hold=_to_7bit(0.08 + 0.22 * f.sustain),
        decay=_to_7bit(0.22 + 0.42 * f.decay + 0.22 * f.tail),
        overdrive=_to_7bit(0.04 + 0.18 * f.low_end + 0.08 * f.transient),
        volume=_to_7bit(0.65 + 0.25 * f.low_end),
        attack_equation="7bit(0.10*attack)",
        hold_equation="7bit(0.08 + 0.22*sustain)",
        decay_equation="7bit(0.22 + 0.42*decay + 0.22*tail)",
        overdrive_equation="7bit(0.04 + 0.18*low_end + 0.08*transient)",
        volume_equation="7bit(0.65 + 0.25*low_end)",
    )

    punctuation_filter = _filter_fields(
        pad=3,
        features=f,
        filter_type="HP2",
        frequency=_to_7bit(0.42 + 0.32 * f.brightness + 0.12 * f.noise),
        resonance=_to_7bit(0.04 + 0.12 * f.spectral_flatness),
        frequency_equation="7bit(0.42 + 0.32*brightness + 0.12*noise)",
        resonance_equation="7bit(0.04 + 0.12*spectral_flatness)",
        resonance_evidence=("spectral_flatness",),
    )
    punctuation_amp = _dry_amp_fields(
        pad=3,
        features=f,
        attack=0,
        hold=0,
        decay=_to_7bit(0.08 + 0.24 * f.decay + 0.12 * (1.0 - f.transient)),
        overdrive=_to_7bit(0.02 + 0.10 * f.noise),
        volume=_to_7bit(0.32 + 0.20 * f.transient),
        attack_equation="0 (dry punctuation policy)",
        hold_equation="0 (dry punctuation policy)",
        decay_equation="7bit(0.08 + 0.24*decay + 0.12*(1-transient))",
        overdrive_equation="7bit(0.02 + 0.10*noise)",
        volume_equation="7bit(0.32 + 0.20*transient)",
    )

    low_body_filter = _filter_fields(
        pad=6,
        features=f,
        filter_type="LP2",
        frequency=_to_7bit(0.22 + 0.22 * f.brightness),
        resonance=_to_7bit(0.04 + 0.10 * f.harmonicity),
        frequency_equation="7bit(0.22 + 0.22*brightness)",
        resonance_equation="7bit(0.04 + 0.10*harmonicity)",
        resonance_evidence=("harmonicity",),
    )
    low_body_amp = _dry_amp_fields(
        pad=6,
        features=f,
        attack=_to_7bit(0.08 * f.attack),
        hold=_to_7bit(0.08 + 0.30 * f.sustain),
        decay=_to_7bit(0.18 + 0.34 * f.decay + 0.24 * f.tail),
        overdrive=_to_7bit(0.03 + 0.16 * f.low_end),
        volume=_to_7bit(0.48 + 0.24 * f.low_end),
        attack_equation="7bit(0.08*attack)",
        hold_equation="7bit(0.08 + 0.30*sustain)",
        decay_equation="7bit(0.18 + 0.34*decay + 0.24*tail)",
        overdrive_equation="7bit(0.03 + 0.16*low_end)",
        volume_equation="7bit(0.48 + 0.24*low_end)",
    )

    clock_filter = _filter_fields(
        pad=9,
        features=f,
        filter_type="LP2",
        frequency=_to_7bit(0.55 + 0.34 * f.brightness),
        resonance=_to_7bit(0.03 + 0.08 * f.noise),
        frequency_equation="7bit(0.55 + 0.34*brightness)",
        resonance_equation="7bit(0.03 + 0.08*noise)",
        resonance_evidence=("noise",),
    )
    clock_amp = _dry_amp_fields(
        pad=9,
        features=f,
        attack=0,
        hold=0,
        decay=_to_7bit(0.04 + 0.16 * f.decay + 0.10 * f.tail),
        overdrive=_to_7bit(0.01 + 0.06 * f.noise),
        volume=_to_7bit(0.38 + 0.18 * f.transient),
        attack_equation="0 (closed-hat clock policy)",
        hold_equation="0 (closed-hat clock policy)",
        decay_equation="7bit(0.04 + 0.16*decay + 0.10*tail)",
        overdrive_equation="7bit(0.01 + 0.06*noise)",
        volume_equation="7bit(0.38 + 0.18*transient)",
    )

    return (
        _track(pad=1, machine_key="bd_classic", fields=kick_filter + kick_amp),
        _track(
            pad=3,
            machine_key="rs_classic",
            fields=punctuation_filter + punctuation_amp,
        ),
        _track(
            pad=6,
            machine_key="xt_classic",
            fields=low_body_filter + low_body_amp,
            tuning=_tuning_intent(analysis),
        ),
        _track(pad=9, machine_key="ch_classic", fields=clock_filter + clock_amp),
    )


def _evidence_payload(
    evidence: RytmAudioFeatureEvidence,
) -> RytmAudioFeatureEvidencePayload:
    return {"feature": evidence.feature, "value": evidence.value}


def _field_payload(field: RytmRecipeFieldProposal) -> RytmRecipeFieldProposalPayload:
    return {
        "path": field.path,
        "requested_value": field.requested_value,
        "status": field.status,
        "converter": field.converter,
        "evidence": [_evidence_payload(item) for item in field.evidence],
        "equation": field.equation,
        "reason": field.reason,
    }


def _tuning_payload(tuning: RytmTuningIntent | None) -> RytmTuningIntentPayload | None:
    if tuning is None:
        return None
    return {
        "target_note": tuning.target_note,
        "pitch_confidence": tuning.pitch_confidence,
        "tonal_stability": tuning.tonal_stability,
        "status": tuning.status,
        "raw_tune": tuning.raw_tune,
        "reason": tuning.reason,
    }


def _track_payload(track: RytmTrackRecipeProposal) -> RytmTrackRecipeProposalPayload:
    return {
        "pad": track.pad,
        "role": track.role,
        "machine_key": track.machine_key,
        "machine_status": track.machine_status,
        "machine_reason": track.machine_reason,
        "fields": [_field_payload(field) for field in track.fields],
        "tuning": _tuning_payload(track.tuning),
    }


def analog_rytm_audio_recipe_proposal_to_dict(
    proposal: AnalogRytmAudioRecipeProposal,
) -> AnalogRytmAudioRecipeProposalPayload:
    """Return the canonical JSON-ready proposal payload."""

    settled = require_runtime_type(
        proposal,
        AnalogRytmAudioRecipeProposal,
        "proposal must be an AnalogRytmAudioRecipeProposal",
    )
    return {
        "schema_version": settled.schema_version,
        "recipe_id": settled.recipe_id,
        "audio_sha256": settled.audio_sha256,
        "status": settled.status,
        "influence_policy": settled.influence_policy,
        "hardware_verified": settled.hardware_verified,
        "codec_ready": settled.codec_ready,
        "render_required": settled.render_required,
        "midi_sent": settled.midi_sent,
        "tracks": [_track_payload(track) for track in settled.tracks],
        "preserved_pads": list(settled.preserved_pads),
        "writable_field_count": settled.writable_field_count,
        "mapping_required_count": settled.mapping_required_count,
        "limitations": list(settled.limitations),
    }


def _recipe_id_payload(
    *,
    audio_sha256: str,
    tracks: tuple[RytmTrackRecipeProposal, ...],
) -> dict[str, object]:
    return {
        "schema_version": RYTM_AUDIO_RECIPE_SCHEMA_VERSION,
        "audio_sha256": audio_sha256,
        "influence_policy": RYTM_RECIPE_INFLUENCE_POLICY,
        "tracks": [_track_payload(track) for track in tracks],
        "preserved_pads": list(RYTM_RECIPE_PRESERVED_PADS),
    }


def build_analog_rytm_audio_recipe_proposal(
    analysis: AudioFeatureAnalysis,
) -> AnalogRytmAudioRecipeProposal:
    """Build an explainable, deterministic, proposal-only Rytm recipe."""

    settled = require_runtime_type(
        analysis,
        AudioFeatureAnalysis,
        "analysis must be an AudioFeatureAnalysis",
    )
    tracks = _build_tracks(settled)
    fields = tuple(field for track in tracks for field in track.fields)
    writable_count = sum(field.status == "writable_proposal" for field in fields)
    mapping_count = sum(field.status == "mapping_required" for field in fields)
    mapping_count += len(tracks)
    mapping_count += sum(
        track.tuning is not None and track.tuning.status == "mapping_required" for track in tracks
    )
    canonical = json.dumps(
        _recipe_id_payload(audio_sha256=settled.audio_sha256, tracks=tracks),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    recipe_id = hashlib.sha256(canonical).hexdigest()
    return AnalogRytmAudioRecipeProposal(
        recipe_id=recipe_id,
        audio_sha256=settled.audio_sha256,
        tracks=tracks,
        writable_field_count=writable_count,
        mapping_required_count=mapping_count,
        limitations=(
            "Machine choices are pad-compatible musical proposals, not approved saved-kit writes.",
            "Machine source parameters are preserved until machine-specific mappings are verified.",
            "Track volume remains proposal-only because its saved-kit location is not approved.",
            "A tuning target never becomes a raw tune without an approved machine-specific lookup.",
            "Audible similarity requires rendering, capture, comparison, and bounded refinement.",
        ),
    )


__all__ = [
    "AnalogRytmAudioRecipeProposal",
    "AnalogRytmAudioRecipeProposalPayload",
    "RYTM_AUDIO_RECIPE_SCHEMA_VERSION",
    "RytmAudioFeatureEvidence",
    "RytmMachineStatus",
    "RytmRecipeFieldProposal",
    "RytmRecipeFieldStatus",
    "RytmTrackRecipeProposal",
    "RytmTuningIntent",
    "RytmTuningStatus",
    "analog_rytm_audio_recipe_proposal_to_dict",
    "build_analog_rytm_audio_recipe_proposal",
]
