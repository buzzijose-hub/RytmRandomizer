"""Retained reference-sound workflow, entirely on the passive file boundary."""

from __future__ import annotations

import tempfile
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field, replace
from pathlib import Path
from threading import Event
from types import MappingProxyType
from typing import Final

from ...data.reference_sound_candidates import REFERENCE_SOUND_SAVED_COMMANDS
from ...devices import resolve_saved_kit_capture_capability
from ...observability.errors import BoundaryError
from ...observability.tracing import trace
from ...snapshot.elektron_native_object import ElektronNativeObjectMessage
from ...style_analysis.analog_four_patch_inference import (
    analyze_analog_four_patch_audio_analysis_isolated,
)
from ...style_analysis.analog_four_patch_refinement import plan_audio_feature_refinement
from ...style_analysis.analog_four_patch_render_rank import (
    AnalogFourPatchRenderScore,
    AnalogFourRenderCandidateFeatures,
    rank_analog_four_render_features,
)
from ...style_analysis.extractor import (
    AudioFeatureAnalysis,
    StyleAnalysisDependencyError,
    audio_synthesis_features_to_dict,
)
from .reader import decode_json_rejecting_duplicate_keys
from .reference_sound_analysis import (
    sound_analysis_from_dict,
    sound_analysis_to_dict,
    sound_features_from_dict,
    sound_integer,
    sound_number,
    sound_text,
)
from .reference_sound_audio import (
    REFERENCE_SEGMENT_MAX_SECONDS,
    inspect_reference_audio,
    select_reference_segment,
)
from .reference_sound_candidates import (
    ReferenceSoundCandidate,
    render_reference_sound_candidates,
    render_refined_reference_sound_candidate,
)
from .reference_sound_records import (
    REFERENCE_SOUND_MAX_RECORDINGS,
    REFERENCE_SOUND_MAX_REFINEMENTS,
    REFERENCE_SOUND_METRIC,
    ReferenceSoundContextPayload,
    ReferenceSoundRecordingPayload,
    ReferenceSoundRefinementPayload,
    ReferenceSoundSegmentIdentity,
    ReferenceSoundSessionPayload,
    ReferenceSoundSource,
    narrow_sound_device_id,
    require_sound_digest,
    require_sound_title,
    sound_candidate_from_dict,
    sound_context_from_dict,
    sound_delta_payload,
    sound_segment_payload,
    sound_session_from_dict,
)
from .reference_sound_store import (
    REFERENCE_SOUND_SCHEMA,
    ReferenceSoundStore,
    reference_sound_digest,
    reference_sound_json,
    sound_artifact_name,
)
from .writer import atomic_write

_MAX_KIT_DESTINATION_SLOT: Final[int] = 127

SoundAnalyzer = Callable[[Path, Event], AudioFeatureAnalysis]


@dataclass(frozen=True, init=False)
class PreparedReferenceSound:
    """Worker result; only its owning event-loop action may publish it."""

    payload_bytes: bytes = field(repr=False)
    artifacts: Mapping[str, bytes]
    expected_manifest_sha256: str | None = None

    def __init__(
        self,
        payload: Mapping[str, object],
        artifacts: Mapping[str, bytes],
        expected_manifest_sha256: str | None = None,
    ) -> None:
        encoded = reference_sound_json(sound_session_from_dict(payload))
        copied = dict(artifacts)
        if any(type(name) is not str or type(data) is not bytes for name, data in copied.items()):
            raise ValueError("Prepared sound artifacts require names and immutable bytes.")
        expected = (
            None
            if expected_manifest_sha256 is None
            else require_sound_digest(expected_manifest_sha256)
        )
        object.__setattr__(self, "payload_bytes", encoded)
        object.__setattr__(self, "artifacts", MappingProxyType(copied))
        object.__setattr__(self, "expected_manifest_sha256", expected)

    @property
    def payload(self) -> ReferenceSoundSessionPayload:
        """Return a fresh validated value, never an alias of the worker snapshot."""
        return sound_session_from_dict(decode_json_rejecting_duplicate_keys(self.payload_bytes))


__all__ = [
    "PreparedReferenceSound",
    "ReferenceSoundWorkspace",
    "StyleAnalysisDependencyError",
    "analyze_reference_sound",
]


def analyze_reference_sound(path: Path, cancel: Event) -> AudioFeatureAnalysis:
    return analyze_analog_four_patch_audio_analysis_isolated(path, cancel=cancel)


def _check_cancel(cancel: Event) -> None:
    if cancel.is_set():
        raise BoundaryError(
            "Reference-sound operation cancelled; retained work is unchanged.",
            context={"error_code": "interrupted"},
        )


def _session_identity(context: ReferenceSoundContextPayload | ReferenceSoundSegmentIdentity) -> str:
    return "sound-" + reference_sound_digest(reference_sound_json(context))[:32]


class ReferenceSoundWorkspace:
    """Analyze, generate, compare and retain exact local artifacts, never transmit."""

    def __init__(
        self,
        store: ReferenceSoundStore | None = None,
        *,
        analyzer: SoundAnalyzer = analyze_reference_sound,
    ) -> None:
        self.store = store if store is not None else ReferenceSoundStore()
        self.analyzer = analyzer

    def _analyze(self, audio: bytes, cancel: Event) -> AudioFeatureAnalysis:
        _check_cancel(cancel)
        with tempfile.TemporaryDirectory(prefix="reference-sound-") as directory:
            path = Path(directory) / "segment.wav"
            atomic_write(path, audio)
            analysis = self.analyzer(path, cancel)
        _check_cancel(cancel)
        if analysis.audio_sha256 != reference_sound_digest(audio):
            raise ValueError("Audio analysis does not match the retained segment.")
        return analysis

    def _load(self, session_id: str) -> ReferenceSoundSessionPayload:
        return sound_session_from_dict(self.store.load(session_id))

    def commit(self, prepared: PreparedReferenceSound) -> ReferenceSoundSessionPayload:
        payload = prepared.payload
        self.store.publish(
            payload, prepared.artifacts, expected_manifest=prepared.expected_manifest_sha256
        )
        return payload

    @trace("reference_sound.import")
    def import_reference(self, original: bytes, title: str) -> ReferenceSoundSessionPayload:
        title = require_sound_title(sound_text(title).strip())
        info = inspect_reference_audio(original)
        segment = select_reference_segment(
            original, start_frame=0, frame_count=min(info.frame_count, info.sample_rate * 8)
        )
        context: ReferenceSoundSegmentIdentity = {
            "original": info.sha256,
            "start_frame": 0,
            "frame_count": segment.frame_count,
        }
        payload: ReferenceSoundSessionPayload = {
            "schema_version": REFERENCE_SOUND_SCHEMA,
            "session_id": _session_identity(context),
            "title": title,
            "segment": sound_segment_payload(segment),
            "context": None,
            "analysis": None,
            "candidates": [],
            "refinements": [],
            "recordings": [],
            "selected_candidate_id": None,
            "favorites": [],
        }
        self.store.publish(
            payload,
            {
                sound_artifact_name(info.sha256, "wav"): original,
                sound_artifact_name(segment.sha256, "wav"): segment.wav,
            },
        )
        return payload

    def _segment_bytes(self, payload: ReferenceSoundSessionPayload) -> bytes:
        segment = payload["segment"]
        original = segment["original"]
        audio = self.store.read_artifact(sound_text(original["sha256"]), "wav")
        selected = select_reference_segment(
            audio,
            start_frame=sound_integer(segment["start_frame"]),
            frame_count=sound_integer(segment["frame_count"]),
        )
        retained = self.store.read_artifact(sound_text(segment["sha256"]), "wav")
        if selected.wav != retained or reference_sound_json(
            selected.to_dict()
        ) != reference_sound_json(segment):
            raise ValueError("Selected segment disagrees with its exact original audio.")
        return retained

    @trace("reference_sound.segment")
    def select_segment(
        self, session_id: str, start_frame: int, frame_count: int
    ) -> ReferenceSoundSessionPayload:
        current = self._load(session_id)
        self._segment_bytes(current)
        old = current["segment"]["original"]
        original = self.store.read_artifact(sound_text(old["sha256"]), "wav")
        segment = select_reference_segment(
            original, start_frame=start_frame, frame_count=frame_count
        )
        identity: ReferenceSoundSegmentIdentity = {
            "original": segment.original.sha256,
            "start_frame": start_frame,
            "frame_count": frame_count,
        }
        payload: ReferenceSoundSessionPayload = {
            **current,
            "session_id": _session_identity(identity),
            "segment": sound_segment_payload(segment),
            "context": None,
            "analysis": None,
            "candidates": [],
            "recordings": [],
            "refinements": [],
            "favorites": [],
            "selected_candidate_id": None,
        }
        self.store.publish(payload, {sound_artifact_name(segment.sha256, "wav"): segment.wav})
        return payload

    @trace("reference_sound.generate")
    def generate(  # noqa: PLR0913 - explicit source-bound operator request
        self,
        session_id: str,
        *,
        source_frame: bytes,
        device_id: str,
        target: int,
        parameters: tuple[str, ...],
        locks: tuple[str, ...],
        strength: float,
        cancel: Event,
    ) -> PreparedReferenceSound:
        current = self._load(session_id)
        audio = self._segment_bytes(current)
        source = ReferenceSoundSource(source_frame, narrow_sound_device_id(device_id), target)
        context = sound_context_from_dict(
            {
                "segment_sha256": reference_sound_digest(audio),
                "source_sha256": source.sha256,
                "device_id": source.device_id,
                "target": source.target,
                "parameters": list(parameters),
                "locks": list(locks),
                "strength": strength,
            }
        )
        identity = _session_identity(context)
        if (self.store.directory / f"{identity}.sound.json").exists():
            _check_cancel(cancel)
            existing = self.reopen(identity)
            return PreparedReferenceSound(
                existing, {}, reference_sound_digest(reference_sound_json(existing))
            )
        analysis = self._analyze(audio, cancel)
        candidates = render_reference_sound_candidates(
            source_frame, device_id, target, analysis, parameters, locks, strength
        )
        payload: ReferenceSoundSessionPayload = {
            **current,
            "session_id": identity,
            "context": context,
            "analysis": sound_analysis_to_dict(analysis),
            "candidates": [sound_candidate_from_dict(item.to_dict()) for item in candidates],
            "recordings": [],
            "refinements": [],
            "favorites": [],
            "selected_candidate_id": candidates[0].candidate_id,
        }
        artifacts = {sound_artifact_name(reference_sound_digest(source_frame), "syx"): source_frame}
        artifacts.update(
            {
                sound_artifact_name(reference_sound_digest(item.frame), "syx"): item.frame
                for item in candidates
            }
        )
        _check_cancel(cancel)
        return PreparedReferenceSound(payload, artifacts)

    def _verified_candidates(
        self, payload: ReferenceSoundSessionPayload
    ) -> tuple[ReferenceSoundCandidate, ...]:
        audio = self._segment_bytes(payload)
        context = payload["context"]
        if context is None or payload["analysis"] is None:
            raise ValueError("Generate source-bound candidates before using this session.")
        if context["segment_sha256"] != reference_sound_digest(audio) or payload[
            "session_id"
        ] != _session_identity(context):
            raise ValueError("Reference-sound source or segment identity changed.")
        analysis = sound_analysis_from_dict(payload["analysis"])
        if analysis.audio_sha256 != reference_sound_digest(audio):
            raise ValueError("Retained measurements belong to a different segment.")
        source = self.store.read_artifact(sound_text(context["source_sha256"]), "syx")
        device = sound_text(context["device_id"])
        target = sound_integer(context["target"])
        parameters = tuple(context["parameters"])
        locks = tuple(context["locks"])
        strength = sound_number(context["strength"])
        candidates = render_reference_sound_candidates(
            source, device, target, analysis, parameters, locks, strength
        )
        refinements = payload["refinements"]
        for item in refinements:
            parent = next(
                (
                    candidate
                    for candidate in candidates
                    if candidate.candidate_id == item["parent_id"]
                ),
                None,
            )
            recording = next(
                (
                    record
                    for record in payload["recordings"]
                    if record["candidate_id"] == item["parent_id"]
                    and record["audio_sha256"] == item["recording_sha256"]
                ),
                None,
            )
            if parent is None or recording is None:
                raise ValueError("Refinement parent or measured recording is missing.")
            measured = self._verified_recording(recording, parent, analysis)
            score = self._score(analysis, measured, parent)
            feedback = plan_audio_feature_refinement(
                analysis,
                score,
                measured.synthesis_features,
                correction_gain=sound_number(item["gain"]),
            )
            corrected = sound_features_from_dict(item["features"])
            if corrected != feedback.corrected_features:
                raise ValueError("Refinement does not match its exact measured feedback.")
            candidates += (
                render_refined_reference_sound_candidate(
                    source,
                    device,
                    target,
                    replace(analysis, synthesis_features=corrected),
                    parameters,
                    locks,
                    strength,
                ),
            )
        if len({item.candidate_id for item in candidates}) != len(candidates):
            raise ValueError("Retained refinement contains duplicate candidate identities.")
        expected = reference_sound_json({"candidates": [item.to_dict() for item in candidates]})
        if expected != reference_sound_json({"candidates": payload["candidates"]}):
            raise ValueError("Candidate values or policy changed; generate a fresh candidate.")
        for item in candidates:
            if self.store.read_artifact(reference_sound_digest(item.frame), "syx") != item.frame:
                raise ValueError("Retained candidate differs from canonical generation.")
        for record in payload["recordings"]:
            parent = next(
                (
                    candidate
                    for candidate in candidates
                    if candidate.candidate_id == record["candidate_id"]
                ),
                None,
            )
            if parent is None:
                raise ValueError("Recording is associated with a missing candidate.")
            self._verified_recording(record, parent, analysis)
        return candidates

    @staticmethod
    def _score(
        reference: AudioFeatureAnalysis,
        measured: AudioFeatureAnalysis,
        candidate: ReferenceSoundCandidate,
    ) -> AnalogFourPatchRenderScore:
        return rank_analog_four_render_features(
            reference.synthesis_features,
            (
                AnalogFourRenderCandidateFeatures(
                    1, candidate.label, Path("supplied-recording.wav"), measured.synthesis_features
                ),
            ),
        )[0]

    def _verified_recording(
        self,
        record: ReferenceSoundRecordingPayload,
        candidate: ReferenceSoundCandidate,
        reference: AudioFeatureAnalysis,
    ) -> AudioFeatureAnalysis:
        if (
            record["candidate_sha256"] != reference_sound_digest(candidate.frame)
            or record["physical_validation"] is not False
        ):
            raise ValueError("Recorded feedback identity or evidence status is invalid.")
        audio = self.store.read_artifact(sound_text(record["audio_sha256"]), "wav")
        if inspect_reference_audio(audio).seconds > REFERENCE_SEGMENT_MAX_SECONDS:
            raise ValueError("Retained recording exceeds the bounded comparison window.")
        measured = sound_analysis_from_dict(record["features"])
        if measured.audio_sha256 != reference_sound_digest(audio):
            raise ValueError("Recording measurements differ from retained audio.")
        retained_score = sound_integer(record["score"])
        retained_distance = sound_number(record["distance"])
        score = self._score(reference, measured, candidate)
        if (
            record["metric"] != REFERENCE_SOUND_METRIC
            or retained_score != score.similarity
            or retained_distance != score.distance
            or reference_sound_json({"deltas": record["feature_deltas"]})
            != reference_sound_json(
                {"deltas": [sound_delta_payload(item) for item in score.feature_deltas]}
            )
        ):
            raise ValueError("Recording score disagrees with the defined feature metric.")
        return measured

    @trace("reference_sound.reopen")
    def reopen(self, session_id: str) -> ReferenceSoundSessionPayload:
        payload = self._load(session_id)
        self._segment_bytes(payload)
        if payload["context"] is not None:
            candidates = self._verified_candidates(payload)
            ids = {item.candidate_id for item in candidates}
            if payload["selected_candidate_id"] not in ids or not set(payload["favorites"]) <= ids:
                raise ValueError("Session selection or favorite references a missing candidate.")
        return payload

    def candidate(self, session_id: str, candidate_id: str) -> ReferenceSoundCandidate:
        payload = self._load(session_id)
        for candidate in self._verified_candidates(payload):
            if candidate.candidate_id == candidate_id:
                return candidate
        raise ValueError("Candidate belongs to another session or has been replaced.")

    def export_patch(self, session_id: str, candidate_id: str, destination_slot: object) -> bytes:
        """Export only to an explicit zero-based scratch slot, with exact payload proof."""
        slot = sound_integer(destination_slot)
        if not 0 <= slot <= _MAX_KIT_DESTINATION_SLOT:
            raise ValueError("Choose a scratch KIT slot in 0..127 before export.")
        candidate = self.candidate(session_id, candidate_id)
        source = ElektronNativeObjectMessage.from_bytes(candidate.frame)
        command = REFERENCE_SOUND_SAVED_COMMANDS[candidate.device_id]
        if source.command == command and source.slot == slot:
            raise ValueError(
                "Choose a different scratch KIT slot; the original saved source slot is protected."
            )
        targeted = replace(source.with_slot(slot), command=command)
        frame = targeted.to_bytes()
        codec = resolve_saved_kit_capture_capability(candidate.device_id).capability
        decoded = codec.decode_saved_kit_capture(frame)
        if (
            decoded.unpacked != source.payload
            or ElektronNativeObjectMessage.from_bytes(frame) != targeted
            or codec.encode_saved_kit_capture(decoded) != frame
        ):
            raise ValueError("Export failed exact scratch-slot and payload verification.")
        return frame

    def select(
        self, session_id: str, candidate_id: str, *, favorite: object = None
    ) -> ReferenceSoundSessionPayload:
        self.candidate(session_id, candidate_id)
        payload = self.reopen(session_id)
        favorites = set(payload["favorites"])
        if favorite is not None:
            if not isinstance(favorite, bool):
                raise ValueError("Favorite must be true or false.")
            if favorite:
                favorites.add(candidate_id)
            else:
                favorites.discard(candidate_id)
        updated: ReferenceSoundSessionPayload = {
            **payload,
            "selected_candidate_id": candidate_id,
            "favorites": sorted(favorites),
        }
        self.store.publish(
            updated, {}, expected_manifest=reference_sound_digest(reference_sound_json(payload))
        )
        return updated

    @trace("reference_sound.compare")
    def compare(  # noqa: PLR0913 - recording and candidate identities must be explicit
        self,
        session_id: str,
        candidate_id: str,
        *,
        candidate_sha256: str,
        recording: bytes,
        cancel: Event,
    ) -> PreparedReferenceSound:
        payload = self.reopen(session_id)
        candidate = self.candidate(session_id, candidate_id)
        if candidate_sha256 != reference_sound_digest(candidate.frame):
            raise ValueError("Recording is associated with a different candidate patch.")
        info = inspect_reference_audio(recording)
        if info.seconds > REFERENCE_SEGMENT_MAX_SECONDS:
            raise ValueError("Use a candidate recording up to eight seconds.")
        records = payload["recordings"]
        if len(records) >= REFERENCE_SOUND_MAX_RECORDINGS:
            raise ValueError("Recording limit reached; start a new bounded session.")
        analysis = self._analyze(recording, cancel)
        reference = sound_analysis_from_dict(payload["analysis"])
        score = self._score(reference, analysis, candidate)
        record: ReferenceSoundRecordingPayload = {
            "candidate_id": candidate_id,
            "candidate_sha256": candidate_sha256,
            "audio_sha256": info.sha256,
            "features": sound_analysis_to_dict(analysis),
            "distance": score.distance,
            "score": score.similarity,
            "metric": REFERENCE_SOUND_METRIC,
            "feature_deltas": [sound_delta_payload(item) for item in score.feature_deltas],
            "physical_validation": False,
        }
        updated: ReferenceSoundSessionPayload = {**payload, "recordings": [*records, record]}
        _check_cancel(cancel)
        return PreparedReferenceSound(
            updated,
            {sound_artifact_name(info.sha256, "wav"): recording},
            reference_sound_digest(reference_sound_json(payload)),
        )

    @trace("reference_sound.refine")
    def refine(
        self, session_id: str, candidate_id: str, *, correction_gain: float, cancel: Event
    ) -> PreparedReferenceSound:
        payload = self.reopen(session_id)
        candidate = self.candidate(session_id, candidate_id)
        refinements = payload["refinements"]
        if len(refinements) >= REFERENCE_SOUND_MAX_REFINEMENTS:
            raise ValueError("Three refinement rounds reached; audition the retained alternatives.")
        records = tuple(
            item for item in payload["recordings"] if item["candidate_id"] == candidate_id
        )
        if not records:
            raise ValueError("Supply a recording of this exact candidate before refinement.")
        record = records[-1]
        if record["candidate_sha256"] != reference_sound_digest(candidate.frame):
            raise ValueError("Recorded feedback belongs to a different patch.")
        reference = sound_analysis_from_dict(payload["analysis"])
        measured = self._verified_recording(record, candidate, reference)
        score = self._score(reference, measured, candidate)
        if score.distance == 0.0:
            _check_cancel(cancel)
            return PreparedReferenceSound(
                payload, {}, reference_sound_digest(reference_sound_json(payload))
            )
        feedback = plan_audio_feature_refinement(
            reference, score, measured.synthesis_features, correction_gain=correction_gain
        )
        context = payload["context"]
        if context is None:
            raise ValueError("Refinement requires a retained source context.")
        source = self.store.read_artifact(sound_text(context["source_sha256"]), "syx")
        refined = render_refined_reference_sound_candidate(
            source,
            sound_text(context["device_id"]),
            sound_integer(context["target"]),
            replace(reference, synthesis_features=feedback.corrected_features),
            tuple(context["parameters"]),
            tuple(context["locks"]),
            sound_number(context["strength"]),
        )
        entry: ReferenceSoundRefinementPayload = {
            "parent_id": candidate_id,
            "recording_sha256": measured.audio_sha256,
            "gain": correction_gain,
            "features": audio_synthesis_features_to_dict(feedback.corrected_features),
        }
        if any(reference_sound_json(item) == reference_sound_json(entry) for item in refinements):
            return PreparedReferenceSound(
                payload, {}, reference_sound_digest(reference_sound_json(payload))
            )
        if any(item["candidate_id"] == refined.candidate_id for item in payload["candidates"]):
            _check_cancel(cancel)
            return PreparedReferenceSound(
                payload, {}, reference_sound_digest(reference_sound_json(payload))
            )
        updated: ReferenceSoundSessionPayload = {
            **payload,
            "refinements": [*refinements, entry],
            "candidates": [*payload["candidates"], sound_candidate_from_dict(refined.to_dict())],
            "selected_candidate_id": refined.candidate_id,
        }
        _check_cancel(cancel)
        return PreparedReferenceSound(
            updated,
            {sound_artifact_name(reference_sound_digest(refined.frame), "syx"): refined.frame},
            reference_sound_digest(reference_sound_json(payload)),
        )
