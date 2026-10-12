"""Strict record construction and immutable worker handoff, without native audio or MIDI."""

from __future__ import annotations

import copy
import dataclasses
import operator
from dataclasses import replace
from pathlib import Path
from threading import Event
from typing import get_args

import pytest
from cockpit.conftest import make_reference_pcm

from rytm_randomizer.cockpit.export.reference_sound_analysis import sound_analysis_from_dict
from rytm_randomizer.cockpit.export.reference_sound_records import (
    REFERENCE_SOUND_METRIC,
    ReferenceSoundFeatureName,
    ReferenceSoundRecordingPayload,
    ReferenceSoundSessionPayload,
    ReferenceSoundSource,
    narrow_sound_device_id,
    narrow_sound_feature,
    require_sound_digest,
    sound_analysis_payload,
    sound_candidate_from_dict,
    sound_context_from_dict,
    sound_delta_payload,
    sound_recording_from_dict,
    sound_refinement_from_dict,
    sound_segment_from_dict,
    sound_session_from_dict,
)
from rytm_randomizer.cockpit.export.reference_sound_session import (
    PreparedReferenceSound,
    ReferenceSoundWorkspace,
)
from rytm_randomizer.cockpit.export.reference_sound_store import (
    reference_sound_digest,
    reference_sound_json,
    sound_artifact_name,
)
from rytm_randomizer.data.analog_four_render_rank import ANALOG_FOUR_RENDER_RANK_FEATURE_WEIGHTS
from rytm_randomizer.style_analysis.analog_four_patch_render_rank import (
    AnalogFourRenderFeatureDelta,
)
from rytm_randomizer.style_analysis.extractor import (
    AudioFeatureAnalysis,
    audio_synthesis_features_to_dict,
)

pytestmark = pytest.mark.fast


def _generate(
    workspace: ReferenceSoundWorkspace, source: tuple[bytes, str, int, tuple[str, ...]]
) -> ReferenceSoundSessionPayload:
    original = workspace.import_reference(make_reference_pcm(), "Record schema")
    frame, device, target, parameters = source
    return workspace.commit(
        workspace.generate(
            original["session_id"],
            source_frame=frame,
            device_id=device,
            target=target,
            parameters=parameters,
            locks=(),
            strength=1.0,
            cancel=Event(),
        )
    )


def _record(analysis: AudioFeatureAnalysis) -> ReferenceSoundRecordingPayload:
    """Schema-only input; it grants no source, playback or comparison authority."""
    return {
        "candidate_id": "a" * 64,
        "candidate_sha256": "b" * 64,
        "audio_sha256": analysis.audio_sha256,
        "features": sound_analysis_payload(analysis),
        "distance": 0.0,
        "score": 100,
        "metric": REFERENCE_SOUND_METRIC,
        "physical_validation": False,
        "feature_deltas": [
            sound_delta_payload(AnalogFourRenderFeatureDelta("attack", 0.0, 0.0, 0.0, 0.12, 0.0))
        ],
    }


def test_prepared_snapshots_nested_payload_artifacts_and_manifest_expectation(
    reference_sound_workspace: ReferenceSoundWorkspace,
) -> None:
    payload = reference_sound_workspace.import_reference(make_reference_pcm(), "Original title")
    audio = make_reference_pcm(frames=801)
    name = sound_artifact_name(reference_sound_digest(audio), "wav")
    artifacts = {name: audio}
    expected = reference_sound_digest(reference_sound_json(payload))
    prepared = PreparedReferenceSound(payload, artifacts, expected)
    snapshot = copy.deepcopy(payload)
    payload["segment"]["start_frame"] = 7
    payload["favorites"].append("changed")
    artifacts[name] = b"replaced"
    artifacts.clear()
    returned = prepared.payload
    returned["title"] = "Changed title"
    returned["segment"]["original"]["sha256"] = "c" * 64
    returned["favorites"].append("changed again")
    assert prepared.payload == snapshot
    assert prepared.payload is not prepared.payload
    assert prepared.artifacts[name] == audio
    assert prepared.expected_manifest_sha256 == expected
    assert prepared.payload_bytes == reference_sound_json(snapshot)
    with pytest.raises(TypeError):
        operator.setitem(prepared.artifacts, name, b"replacement")
    with pytest.raises(dataclasses.FrozenInstanceError):
        prepared.expected_manifest_sha256 = None


@pytest.mark.parametrize("artifacts", [{"audio": bytearray(b"audio")}, {1: b"audio"}])
def test_prepared_rejects_mutable_artifact_values_and_nontext_names(
    reference_sound_workspace: ReferenceSoundWorkspace, artifacts: dict[str, bytes]
) -> None:
    payload = reference_sound_workspace.import_reference(make_reference_pcm(), "Reference")
    with pytest.raises(ValueError, match="immutable bytes"):
        PreparedReferenceSound(payload, artifacts)


def test_prepared_validates_manifest_expectation_and_session_schema(
    reference_sound_workspace: ReferenceSoundWorkspace,
) -> None:
    payload = reference_sound_workspace.import_reference(make_reference_pcm(), "Reference")
    with pytest.raises(ValueError, match="digest"):
        PreparedReferenceSound(payload, {}, "not-a-digest")
    with pytest.raises(ValueError, match="schema"):
        PreparedReferenceSound({**payload, "schema_version": 2}, {})
    assert PreparedReferenceSound(payload, {}).expected_manifest_sha256 is None


def test_source_constructor_is_strict_frozen_and_uses_existing_device_domains() -> None:
    for device, target in [("analog_rytm_mk2", 12), ("analog_four_mk2", 4)]:
        source = ReferenceSoundSource(b"frame", narrow_sound_device_id(device), target)
        assert source.sha256 == reference_sound_digest(b"frame")
        with pytest.raises(dataclasses.FrozenInstanceError):
            source.target = 1
    for frame, device, target in [
        (b"", "analog_four_mk2", 1),
        (bytearray(b"frame"), "analog_four_mk2", 1),
        (b"frame", "analog_four_mk2", True),
        (b"frame", "analog_four_mk2", 5),
    ]:
        with pytest.raises(ValueError):
            ReferenceSoundSource(frame, narrow_sound_device_id(device), target)
    with pytest.raises(ValueError):
        narrow_sound_device_id("unknown")
    assert require_sound_digest("a" * 64) == "a" * 64
    for value in ["a" * 63, "G" * 64]:
        with pytest.raises(ValueError):
            require_sound_digest(value)
    for feature in [
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
    ]:
        assert narrow_sound_feature(feature) == feature
    assert set(get_args(ReferenceSoundFeatureName)) == {
        name for name, _ in ANALOG_FOUR_RENDER_RANK_FEATURE_WEIGHTS
    }


def test_import_session_schema_rejects_unknown_fields_wrong_types_and_oversized_lists(
    reference_sound_workspace: ReferenceSoundWorkspace,
) -> None:
    payload = reference_sound_workspace.import_reference(make_reference_pcm(), "Reference")
    assert sound_session_from_dict(payload) == payload
    for field, value in [
        ("schema_version", 2),
        ("schema_version", True),
        ("title", " " * 3),
        ("title", "x" * 121),
        ("title", "line\nbreak"),
        ("favorites", ["duplicate"] * 2),
        ("favorites", [str(index) for index in range(257)]),
        ("recordings", {}),
        ("recordings", [None] * 17),
        ("refinements", [None] * 4),
        ("candidates", [None] * 12),
        ("unknown", True),
    ]:
        with pytest.raises(ValueError):
            sound_session_from_dict({**payload, field: value})
    with pytest.raises(ValueError):
        sound_session_from_dict({key: value for key, value in payload.items() if key != "title"})
    with pytest.raises(ValueError):
        sound_session_from_dict([])


def test_segment_constructor_retains_exact_numeric_spelling_and_validates_metadata(
    reference_sound_workspace: ReferenceSoundWorkspace,
) -> None:
    payload = reference_sound_workspace.import_reference(make_reference_pcm(), "Reference")
    segment = payload["segment"]
    original = segment["original"]
    for field, value in [
        ("sample_rate", 7999),
        ("channels", 3),
        ("sample_width", 1),
        ("seconds", 0),
        ("seconds", 0.2),
        ("seconds", 121),
    ]:
        with pytest.raises(ValueError):
            sound_segment_from_dict({**segment, "original": {**original, field: value}})
    for field, value in [
        ("start_frame", -1),
        ("frame_count", 801),
        ("frame_count", 1),
        ("start_frame", True),
        ("extra", 0),
    ]:
        with pytest.raises(ValueError):
            sound_segment_from_dict({**segment, field: value})
    longer = {**segment, "original": {**original, "frame_count": 8000, "seconds": 1}}
    assert reference_sound_json(sound_segment_from_dict(longer)) == reference_sound_json(longer)


def test_context_constructor_rejects_boolean_strength_targets_and_unknown_device() -> None:
    context = {
        "device_id": "analog_four_mk2",
        "target": 1,
        "source_sha256": "a" * 64,
        "segment_sha256": "b" * 64,
        "parameters": ["filter1_frequency"],
        "locks": [],
        "strength": 1,
    }
    parsed = sound_context_from_dict(context)
    assert reference_sound_json(parsed) == reference_sound_json(context)
    for field, value in [
        ("device_id", "unknown"),
        ("target", True),
        ("target", 5),
        ("strength", False),
        ("strength", float("nan")),
        ("strength", 1.01),
        ("strength", 10**1000),
        ("parameters", ["duplicate", "duplicate"]),
        ("locks", None),
    ]:
        with pytest.raises(ValueError):
            sound_context_from_dict({**context, field: value})


def test_record_and_refinement_constructors_use_shared_analysis_and_strict_numeric_types(
    audio_patch_dna_analysis: AudioFeatureAnalysis,
) -> None:
    record = _record(audio_patch_dna_analysis)
    assert sound_recording_from_dict(record) == record
    for field, value in [
        ("score", False),
        ("score", True),
        ("score", 100.0),
        ("score", -1),
        ("score", 101),
        ("distance", False),
        ("distance", True),
        ("distance", float("inf")),
        ("distance", -0.1),
        ("distance", 1.1),
        ("physical_validation", 0),
        ("physical_validation", True),
    ]:
        with pytest.raises(ValueError):
            sound_recording_from_dict({**record, field: value})
    for field, value in [
        ("feature", "duration"),
        ("feature", "unknown"),
        ("absolute_delta", -0.1),
        ("weight", True),
    ]:
        delta = {**record["feature_deltas"][0], field: value}
        with pytest.raises(ValueError):
            sound_recording_from_dict({**record, "feature_deltas": [delta]})
    for section in ("report", "features", "evidence"):
        analysis = {**record["features"], section: {**record["features"][section], "unknown": True}}
        with pytest.raises(ValueError):
            sound_recording_from_dict({**record, "features": analysis})
    features = audio_synthesis_features_to_dict(audio_patch_dna_analysis.synthesis_features)
    refinement = {
        "parent_id": "a" * 64,
        "recording_sha256": "b" * 64,
        "gain": 0.5,
        "features": features,
    }
    assert sound_refinement_from_dict(refinement) == refinement
    with pytest.raises(ValueError):
        sound_refinement_from_dict({**refinement, "gain": True})


def test_generated_candidate_wire_types_preserve_native_precision_and_reject_false_claims(
    reference_sound_workspace: ReferenceSoundWorkspace,
    reference_sound_source: tuple[bytes, str, int, tuple[str, ...]],
) -> None:
    payload = _generate(reference_sound_workspace, reference_sound_source)
    assert sound_session_from_dict(payload) == payload
    candidate = payload["candidates"][0]
    assert sound_candidate_from_dict(candidate) == candidate
    assert all(type(change["rendered_value"]) is int for change in candidate["changes"])
    for field, value in [
        ("output_authority", "live"),
        ("hardware_send_validated", 0),
        ("roundtrip_redecoded", 1),
        ("frame_size", True),
    ]:
        with pytest.raises(ValueError):
            sound_candidate_from_dict({**candidate, field: value})
    if candidate["changes"]:
        change = {**candidate["changes"][0], "rendered_value": True}
        with pytest.raises(ValueError):
            sound_candidate_from_dict({**candidate, "changes": [change]})


def test_rehashed_boolean_zero_distance_is_refused_without_rewriting_retained_bytes(
    reference_sound_workspace: ReferenceSoundWorkspace,
    reference_sound_source: tuple[bytes, str, int, tuple[str, ...]],
) -> None:
    workspace = reference_sound_workspace
    payload = _generate(workspace, reference_sound_source)
    candidate_id = payload["candidates"][0]["candidate_id"]
    candidate = workspace.candidate(payload["session_id"], candidate_id)
    recorded = workspace.commit(
        workspace.compare(
            payload["session_id"],
            candidate_id,
            candidate_sha256=reference_sound_digest(candidate.frame),
            recording=make_reference_pcm(),
            cancel=Event(),
        )
    )
    assert recorded["recordings"][0]["distance"] == 0.0
    assert recorded["recordings"][0]["score"] == 100
    forged = {**recorded, "recordings": [{**recorded["recordings"][0], "distance": False}]}
    workspace.store.publish(forged, {})
    before = {path.name: path.read_bytes() for path in workspace.store.directory.iterdir()}
    with pytest.raises(ValueError, match="numeric"):
        workspace.reopen(payload["session_id"])
    assert {path.name: path.read_bytes() for path in workspace.store.directory.iterdir()} == before
    with pytest.raises(ValueError, match="numeric"):
        workspace._verified_recording(
            forged["recordings"][0], candidate, sound_analysis_from_dict(recorded["analysis"])
        )


def test_unbound_session_rejects_candidate_lookup_and_valid_metadata_segment_drift(
    reference_sound_workspace: ReferenceSoundWorkspace,
) -> None:
    workspace = reference_sound_workspace
    payload = workspace.import_reference(make_reference_pcm(frames=900), "Reference")
    with pytest.raises(ValueError, match="source-bound"):
        workspace.candidate(payload["session_id"], "a" * 64)
    forged = {**payload, "segment": {**payload["segment"], "start_frame": 1, "frame_count": 899}}
    workspace.store.publish(forged, {})
    before = {path.name: path.read_bytes() for path in workspace.store.directory.iterdir()}
    with pytest.raises(ValueError, match="Selected segment disagrees"):
        workspace.reopen(payload["session_id"])
    assert {path.name: path.read_bytes() for path in workspace.store.directory.iterdir()} == before


def test_recording_rejects_well_typed_but_unknown_candidate_identity(
    reference_sound_workspace: ReferenceSoundWorkspace,
    reference_sound_source: tuple[bytes, str, int, tuple[str, ...]],
) -> None:
    workspace = reference_sound_workspace
    payload = _generate(workspace, reference_sound_source)
    candidate = workspace.candidate(payload["session_id"], payload["candidates"][0]["candidate_id"])
    recorded = workspace.commit(
        workspace.compare(
            payload["session_id"],
            candidate.candidate_id,
            candidate_sha256=reference_sound_digest(candidate.frame),
            recording=make_reference_pcm(),
            cancel=Event(),
        )
    )
    forged = {**recorded, "recordings": [{**recorded["recordings"][0], "candidate_id": "0" * 64}]}
    workspace.store.publish(forged, {})
    with pytest.raises(ValueError, match="missing candidate"):
        workspace.reopen(payload["session_id"])


def test_refinement_refuses_missing_context_when_resolved_candidate_is_stale(
    reference_sound_workspace: ReferenceSoundWorkspace,
    reference_sound_source: tuple[bytes, str, int, tuple[str, ...]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = reference_sound_workspace
    payload = _generate(workspace, reference_sound_source)
    candidate = workspace.candidate(payload["session_id"], payload["candidates"][0]["candidate_id"])
    analyzer = workspace.analyzer

    def measured(path: Path, cancel: Event) -> AudioFeatureAnalysis:
        analysis = analyzer(path, cancel)
        return replace(
            analysis, synthesis_features=replace(analysis.synthesis_features, brightness=0.25)
        )

    workspace.analyzer = measured
    recorded = workspace.commit(
        workspace.compare(
            payload["session_id"],
            candidate.candidate_id,
            candidate_sha256=reference_sound_digest(candidate.frame),
            recording=make_reference_pcm(frames=802),
            cancel=Event(),
        )
    )
    assert recorded["recordings"][0]["distance"] > 0
    stale = copy.deepcopy(recorded)
    stale["context"] = None
    monkeypatch.setattr(workspace, "reopen", lambda session_id: stale)
    before = {path.name: path.read_bytes() for path in workspace.store.directory.iterdir()}
    with pytest.raises(ValueError, match="retained source context"):
        workspace.refine(
            payload["session_id"], candidate.candidate_id, correction_gain=0.5, cancel=Event()
        )
    assert {path.name: path.read_bytes() for path in workspace.store.directory.iterdir()} == before
