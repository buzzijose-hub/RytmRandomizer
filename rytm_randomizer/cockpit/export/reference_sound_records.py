"""Validated wire records for the existing passive reference-sound workspace."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Final, Literal, TypeAlias, TypedDict, TypeVar, cast

from ...data.audio_patch_dna import AUDIO_PATCH_DNA_CANDIDATE_COUNT
from ...snapshot.mutation_scope import registered_mutation_ids
from ...style_analysis.analog_four_patch_render_rank import AnalogFourRenderFeatureDelta
from ...style_analysis.extractor import (
    AudioDnaEvidencePayload,
    AudioSynthesisFeaturesPayload,
    audio_synthesis_features_to_dict,
)
from ...style_analysis.feature_report import FeatureReportPayload
from ..data import require_exact_keys, require_object, require_sequence
from ..data.stage import ANALOG_FOUR_DEVICE_ID, ANALOG_RYTM_DEVICE_ID, StageDeviceId
from .reference_sound_analysis import (
    ReferenceSoundAnalysisPayload,
    sound_analysis_from_dict,
    sound_analysis_to_dict,
    sound_features_from_dict,
    sound_integer,
    sound_number,
    sound_text,
)
from .reference_sound_audio import (
    REFERENCE_AUDIO_MAX_SECONDS,
    REFERENCE_SEGMENT_MAX_SECONDS,
    REFERENCE_SEGMENT_MIN_SECONDS,
    ReferenceAudioSegment,
)
from .reference_sound_store import (
    REFERENCE_SOUND_SCHEMA,
    reference_sound_digest,
    require_sound_session_id,
)

REFERENCE_SOUND_MAX_REFINEMENTS: Final[int] = 3
REFERENCE_SOUND_MAX_RECORDINGS: Final[int] = 16
REFERENCE_SOUND_METRIC: Final[str] = (
    "weighted normalized 11-feature L1 distance; score = round(100 * (1 - distance)); not a probability or verified sound match"
)
_SHA256_HEX_LENGTH: Final[int] = len(reference_sound_digest(b""))
_PCM_MIN_SAMPLE_RATE: Final[int] = 8000
_PCM_MAX_SAMPLE_RATE: Final[int] = 96000
_SCORE_MAXIMUM: Final[int] = 100
_TITLE_MAXIMUM: Final[int] = 120
_CONTROL_CHARACTER_LIMIT: Final[int] = 32
_Record = TypeVar("_Record")
ReferenceSoundFeatureName: TypeAlias = Literal[
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


class ReferenceAudioInfoPayload(TypedDict):
    sample_rate: int
    channels: int
    sample_width: int
    frame_count: int
    sha256: str
    seconds: float


class ReferenceSoundSegmentPayload(TypedDict):
    original: ReferenceAudioInfoPayload
    start_frame: int
    frame_count: int
    sha256: str


class ReferenceSoundSegmentIdentity(TypedDict):
    original: str
    start_frame: int
    frame_count: int


class ReferenceSoundContextPayload(TypedDict):
    device_id: StageDeviceId
    target: int
    source_sha256: str
    segment_sha256: str
    parameters: list[str]
    locks: list[str]
    strength: float


class ReferenceSoundChangePayload(TypedDict):
    parameter: str
    source_value: int
    proposed_value: int
    rendered_value: int
    source_display: str | None
    proposed_display: str
    rendered_display: str | None
    units: str
    rationale: str
    offsets: list[int]


class ReferenceSoundCandidatePayload(TypedDict):
    candidate_id: str
    direction: str
    label: str
    device_id: StageDeviceId
    target: int
    source_sha256: str
    frame_sha256: str
    frame_size: int
    changes: list[ReferenceSoundChangePayload]
    limitations: list[str]
    intended_unpacked_offsets: list[int]
    changed_unpacked_offsets: list[int]
    changed_wire_offsets: list[int]
    features: AudioSynthesisFeaturesPayload
    output_authority: Literal["local-file-only"]
    hardware_send_validated: Literal[False]
    roundtrip_redecoded: Literal[True]


class ReferenceSoundFeatureDeltaPayload(TypedDict):
    feature: ReferenceSoundFeatureName
    reference_value: float
    render_value: float
    absolute_delta: float
    weight: float
    weighted_delta: float


class ReferenceSoundRecordingPayload(TypedDict):
    candidate_id: str
    candidate_sha256: str
    audio_sha256: str
    features: ReferenceSoundAnalysisPayload
    distance: float
    score: int
    metric: str
    feature_deltas: list[ReferenceSoundFeatureDeltaPayload]
    physical_validation: Literal[False]


class ReferenceSoundRefinementPayload(TypedDict):
    parent_id: str
    recording_sha256: str
    gain: float
    features: AudioSynthesisFeaturesPayload


class ReferenceSoundSessionPayload(TypedDict):
    schema_version: int
    session_id: str
    title: str
    segment: ReferenceSoundSegmentPayload
    context: ReferenceSoundContextPayload | None
    analysis: ReferenceSoundAnalysisPayload | None
    candidates: list[ReferenceSoundCandidatePayload]
    selected_candidate_id: str | None
    favorites: list[str]
    recordings: list[ReferenceSoundRecordingPayload]
    refinements: list[ReferenceSoundRefinementPayload]


def narrow_sound_device_id(value: object) -> StageDeviceId:
    """Validate against the existing stage identities without a type assertion."""
    value = sound_text(value)
    if value == ANALOG_RYTM_DEVICE_ID:
        return ANALOG_RYTM_DEVICE_ID
    if value == ANALOG_FOUR_DEVICE_ID:
        return ANALOG_FOUR_DEVICE_ID
    raise ValueError("Reference-sound device is unsupported.")


@dataclass(frozen=True)
class ReferenceSoundSource:
    """Immutable request identity; native decoding remains owned by the shared codec."""

    frame: bytes
    device_id: StageDeviceId
    target: int

    def __post_init__(self) -> None:
        if type(self.frame) is not bytes or not self.frame:
            raise ValueError("Reference-sound source must be immutable frame bytes.")
        device = narrow_sound_device_id(self.device_id)
        _sound_record_target(self.target, device)

    @property
    def sha256(self) -> str:
        return reference_sound_digest(self.frame)


def _sound_record_target(value: object, device: StageDeviceId) -> int:
    target = sound_integer(value)
    if target not in registered_mutation_ids(device):
        raise ValueError("Reference-sound target is outside the device domain.")
    return target


def _record(value: object, keys: frozenset[str]) -> Mapping[str, object]:
    data = require_object(value, "Reference-sound record", ValueError)
    require_exact_keys(data, keys, "Reference-sound record")
    return data


def _records(
    value: object, parse: Callable[[object], _Record], maximum: int = 256
) -> list[_Record]:
    items = require_sequence(value, "Reference-sound records", ValueError, kind="array")
    if len(items) > maximum:
        raise ValueError("Reference-sound record limit exceeded.")
    return [parse(item) for item in items]


def _sound_record_number(value: object) -> float:
    try:
        checked = sound_number(value)
    except OverflowError as exc:
        raise ValueError("Reference-sound numeric field is too large.") from exc
    # Preserve integer JSON spellings: source/context identity and CAS hash them.
    return value if isinstance(value, int) else checked


def _normalized(value: object) -> float:
    number = _sound_record_number(value)
    if not 0 <= number <= 1:
        raise ValueError("Reference-sound number must be in 0..1.")
    return number


def require_sound_digest(value: object) -> str:
    digest = sound_text(value)
    if len(digest) != _SHA256_HEX_LENGTH or any(
        character not in "0123456789abcdef" for character in digest
    ):
        raise ValueError("Reference-sound digest is invalid.")
    return digest


def _optional_text(value: object) -> str | None:
    return None if value is None else sound_text(value)


def _strings(value: object) -> list[str]:
    values = _records(value, sound_text)
    if len(set(values)) != len(values):
        raise ValueError("Reference-sound records cannot contain duplicates.")
    return values


def sound_segment_payload(segment: ReferenceAudioSegment) -> ReferenceSoundSegmentPayload:
    """Reuse the sample-exact audio DTO's validated wire constructor."""
    return sound_segment_from_dict(segment.to_dict())


def sound_segment_from_dict(value: object) -> ReferenceSoundSegmentPayload:
    data = _record(value, ReferenceSoundSegmentPayload.__required_keys__)
    info = _record(data["original"], ReferenceAudioInfoPayload.__required_keys__)
    rate, count = sound_integer(info["sample_rate"]), sound_integer(info["frame_count"])
    channels, width = sound_integer(info["channels"]), sound_integer(info["sample_width"])
    seconds = _sound_record_number(info["seconds"])
    start, frames = sound_integer(data["start_frame"]), sound_integer(data["frame_count"])
    if (
        not _PCM_MIN_SAMPLE_RATE <= rate <= _PCM_MAX_SAMPLE_RATE
        or channels not in (1, 2)
        or width not in (2, 3, 4)
        or not 0 < seconds <= REFERENCE_AUDIO_MAX_SECONDS
        or seconds != count / rate
        or start < 0
        or start + frames > count
        or not REFERENCE_SEGMENT_MIN_SECONDS <= frames / rate <= REFERENCE_SEGMENT_MAX_SECONDS
    ):
        raise ValueError("Reference-sound segment metadata is invalid.")
    return {
        "original": {
            "sample_rate": rate,
            "channels": channels,
            "sample_width": width,
            "frame_count": count,
            "sha256": require_sound_digest(info["sha256"]),
            "seconds": seconds,
        },
        "start_frame": start,
        "frame_count": frames,
        "sha256": require_sound_digest(data["sha256"]),
    }


def sound_context_from_dict(value: object) -> ReferenceSoundContextPayload:
    data = _record(value, ReferenceSoundContextPayload.__required_keys__)
    device = narrow_sound_device_id(data["device_id"])
    return {
        "device_id": device,
        "target": _sound_record_target(data["target"], device),
        "source_sha256": require_sound_digest(data["source_sha256"]),
        "segment_sha256": require_sound_digest(data["segment_sha256"]),
        "parameters": _strings(data["parameters"]),
        "locks": _strings(data["locks"]),
        "strength": _normalized(data["strength"]),
    }


def _analysis(value: object) -> ReferenceSoundAnalysisPayload:
    data = _record(value, ReferenceSoundAnalysisPayload.__required_keys__)
    _record(data["report"], FeatureReportPayload.__required_keys__)
    _record(data["features"], AudioSynthesisFeaturesPayload.__required_keys__)
    _record(data["evidence"], AudioDnaEvidencePayload.__required_keys__)
    return sound_analysis_to_dict(sound_analysis_from_dict(data))


def _features(value: object) -> AudioSynthesisFeaturesPayload:
    data = _record(value, AudioSynthesisFeaturesPayload.__required_keys__)
    return audio_synthesis_features_to_dict(sound_features_from_dict(data))


def _change(value: object) -> ReferenceSoundChangePayload:
    data = _record(value, ReferenceSoundChangePayload.__required_keys__)
    return {
        "parameter": sound_text(data["parameter"]),
        "source_value": sound_integer(data["source_value"]),
        "proposed_value": sound_integer(data["proposed_value"]),
        "rendered_value": sound_integer(data["rendered_value"]),
        "source_display": _optional_text(data["source_display"]),
        "proposed_display": sound_text(data["proposed_display"]),
        "rendered_display": _optional_text(data["rendered_display"]),
        "units": sound_text(data["units"]),
        "rationale": sound_text(data["rationale"]),
        "offsets": _records(data["offsets"], sound_integer),
    }


def sound_candidate_from_dict(value: object) -> ReferenceSoundCandidatePayload:
    data = _record(value, ReferenceSoundCandidatePayload.__required_keys__)
    if (
        data["output_authority"] != "local-file-only"
        or data["hardware_send_validated"] is not False
        or data["roundtrip_redecoded"] is not True
    ):
        raise ValueError("Reference-sound candidate evidence is invalid.")
    device = narrow_sound_device_id(data["device_id"])
    return {
        "candidate_id": require_sound_digest(data["candidate_id"]),
        "direction": sound_text(data["direction"]),
        "label": sound_text(data["label"]),
        "device_id": device,
        "target": _sound_record_target(data["target"], device),
        "source_sha256": require_sound_digest(data["source_sha256"]),
        "frame_sha256": require_sound_digest(data["frame_sha256"]),
        "frame_size": sound_integer(data["frame_size"]),
        "changes": _records(data["changes"], _change),
        "limitations": _strings(data["limitations"]),
        "intended_unpacked_offsets": _records(data["intended_unpacked_offsets"], sound_integer),
        "changed_unpacked_offsets": _records(data["changed_unpacked_offsets"], sound_integer),
        "changed_wire_offsets": _records(data["changed_wire_offsets"], sound_integer),
        "features": _features(data["features"]),
        "output_authority": "local-file-only",
        "hardware_send_validated": False,
        "roundtrip_redecoded": True,
    }


def sound_delta_payload(delta: AnalogFourRenderFeatureDelta) -> ReferenceSoundFeatureDeltaPayload:
    return {
        "feature": narrow_sound_feature(delta.feature),
        "reference_value": delta.reference_value,
        "render_value": delta.render_value,
        "absolute_delta": delta.absolute_delta,
        "weight": delta.weight,
        "weighted_delta": delta.weighted_delta,
    }


def narrow_sound_feature(value: object) -> ReferenceSoundFeatureName:
    """Narrow only after checking the shared feature schema's exact vocabulary."""
    feature = sound_text(value)
    if feature not in AudioSynthesisFeaturesPayload.__required_keys__ - {
        "audio_sha256",
        "duration",
    }:
        raise ValueError("Reference-sound comparison feature is unknown.")
    return cast(ReferenceSoundFeatureName, feature)


def _delta(value: object) -> ReferenceSoundFeatureDeltaPayload:
    data = _record(value, ReferenceSoundFeatureDeltaPayload.__required_keys__)
    return {
        "feature": narrow_sound_feature(data["feature"]),
        "reference_value": _normalized(data["reference_value"]),
        "render_value": _normalized(data["render_value"]),
        "absolute_delta": _normalized(data["absolute_delta"]),
        "weight": _normalized(data["weight"]),
        "weighted_delta": _normalized(data["weighted_delta"]),
    }


def sound_recording_from_dict(value: object) -> ReferenceSoundRecordingPayload:
    data = _record(value, ReferenceSoundRecordingPayload.__required_keys__)
    score, distance = sound_integer(data["score"]), _sound_record_number(data["distance"])
    if (
        not 0 <= score <= _SCORE_MAXIMUM
        or not 0 <= distance <= 1
        or data["physical_validation"] is not False
    ):
        raise ValueError("Reference-sound recording score or evidence is invalid.")
    return {
        "candidate_id": require_sound_digest(data["candidate_id"]),
        "candidate_sha256": require_sound_digest(data["candidate_sha256"]),
        "audio_sha256": require_sound_digest(data["audio_sha256"]),
        "features": _analysis(data["features"]),
        "distance": _sound_record_number(data["distance"]),
        "score": score,
        "metric": sound_text(data["metric"]),
        "feature_deltas": _records(data["feature_deltas"], _delta),
        "physical_validation": False,
    }


def sound_refinement_from_dict(value: object) -> ReferenceSoundRefinementPayload:
    data = _record(value, ReferenceSoundRefinementPayload.__required_keys__)
    return {
        "parent_id": require_sound_digest(data["parent_id"]),
        "recording_sha256": require_sound_digest(data["recording_sha256"]),
        "gain": _normalized(data["gain"]),
        "features": _features(data["features"]),
    }


def require_sound_title(value: object) -> str:
    title = sound_text(value)
    if (
        len(title) > _TITLE_MAXIMUM
        or not title.strip()
        or any(ord(character) < _CONTROL_CHARACTER_LIMIT for character in title)
    ):
        raise ValueError("Reference-sound title is invalid.")
    return title


def sound_session_from_dict(value: object) -> ReferenceSoundSessionPayload:
    """Validate shape without granting replay, source, calibration or SEND authority."""
    data = _record(value, ReferenceSoundSessionPayload.__required_keys__)
    if sound_integer(data["schema_version"]) != REFERENCE_SOUND_SCHEMA:
        raise ValueError("Reference-sound schema is incompatible.")
    context, analysis = data["context"], data["analysis"]
    return {
        "schema_version": REFERENCE_SOUND_SCHEMA,
        "session_id": require_sound_session_id(data["session_id"]),
        "title": require_sound_title(data["title"]),
        "segment": sound_segment_from_dict(data["segment"]),
        "context": None if context is None else sound_context_from_dict(context),
        "analysis": None if analysis is None else _analysis(analysis),
        "candidates": _records(
            data["candidates"],
            sound_candidate_from_dict,
            AUDIO_PATCH_DNA_CANDIDATE_COUNT + REFERENCE_SOUND_MAX_REFINEMENTS,
        ),
        "selected_candidate_id": _optional_text(data["selected_candidate_id"]),
        "favorites": _strings(data["favorites"]),
        "recordings": _records(
            data["recordings"], sound_recording_from_dict, REFERENCE_SOUND_MAX_RECORDINGS
        ),
        "refinements": _records(
            data["refinements"], sound_refinement_from_dict, REFERENCE_SOUND_MAX_REFINEMENTS
        ),
    }
