"""Sample-exact audition selection retains originals without silently cropping."""

from __future__ import annotations

from pathlib import Path
from threading import Event

import pytest
from cockpit.conftest import make_reference_pcm

from rytm_randomizer.cockpit.export.reference_sound_audio import select_reference_segment
from rytm_randomizer.cockpit.export.reference_sound_records import (
    sound_context_from_dict,
    sound_recording_from_dict,
)
from rytm_randomizer.cockpit.export.reference_sound_session import ReferenceSoundWorkspace
from rytm_randomizer.cockpit.export.reference_sound_store import reference_sound_digest
from rytm_randomizer.observability.errors import BoundaryError

pytestmark = pytest.mark.fast


def _generated(workspace: ReferenceSoundWorkspace, source: tuple[bytes, str, int, tuple[str, ...]]):
    imported = workspace.import_reference(make_reference_pcm(), "Exact audition")
    frame, device, target, parameters = source
    return workspace.commit(
        workspace.generate(
            imported["session_id"],
            source_frame=frame,
            device_id=device,
            target=target,
            parameters=parameters,
            locks=(),
            strength=1.0,
            cancel=Event(),
        )
    )


def test_selected_recording_survives_restart_with_original_and_exact_sample_identity(
    reference_sound_workspace: ReferenceSoundWorkspace,
    reference_sound_source: tuple[bytes, str, int, tuple[str, ...]],
) -> None:
    workspace = reference_sound_workspace
    session = _generated(workspace, reference_sound_source)
    candidate = session["candidates"][0]
    original = make_reference_pcm(
        frames=80000, sample_values=tuple(i % 16000 for i in range(80000))
    )
    expected = select_reference_segment(original, start_frame=8000, frame_count=40000)
    prepared = workspace.compare(
        session["session_id"],
        candidate["candidate_id"],
        candidate_sha256=candidate["frame_sha256"],
        recording=original,
        start_frame=8000,
        frame_count=40000,
        cancel=Event(),
    )
    assert workspace.reopen(session["session_id"]) == session
    compared = workspace.commit(prepared)
    record = compared["recordings"][0]
    assert record["segment"] == expected.to_dict()
    assert record["audio_sha256"] == reference_sound_digest(expected.wav)
    assert record["features"]["features"]["audio_sha256"] == record["audio_sha256"]
    assert workspace.store.read_artifact(reference_sound_digest(original), "wav") == original
    assert workspace.store.read_artifact(record["audio_sha256"], "wav") == expected.wav
    reopened = ReferenceSoundWorkspace(workspace.store, analyzer=workspace.analyzer)
    assert reopened.reopen(session["session_id"]) == compared
    assert (
        reopened.candidate(session["session_id"], candidate["candidate_id"]).frame
        == workspace.candidate(session["session_id"], candidate["candidate_id"]).frame
    )


@pytest.mark.parametrize(
    "start,count",
    [
        (None, 400),
        (0, None),
        (-1, 400),
        (800, 400),
        (0, 399),
        (True, 400),
        (0, True),
        (0.5, 400),
        (0, 400.5),
    ],
)
def test_invalid_audition_ranges_refuse_before_analysis_and_preserve_retained_work(
    reference_sound_workspace: ReferenceSoundWorkspace,
    reference_sound_source: tuple[bytes, str, int, tuple[str, ...]],
    start: object,
    count: object,
) -> None:
    workspace = reference_sound_workspace
    session = _generated(workspace, reference_sound_source)
    candidate = session["candidates"][0]
    workspace.select(session["session_id"], candidate["candidate_id"], favorite=True)
    before = {p.name: p.read_bytes() for p in workspace.store.directory.iterdir()}

    def unexpected(path: Path, cancel: Event):
        pytest.fail("Invalid segment must be refused before audio analysis")

    workspace.analyzer = unexpected
    with pytest.raises(BoundaryError) as failure:
        workspace.compare(
            session["session_id"],
            candidate["candidate_id"],
            candidate_sha256=candidate["frame_sha256"],
            recording=make_reference_pcm(),
            start_frame=start,
            frame_count=count,
            cancel=Event(),
        )
    assert failure.value.context["error_code"] == "recording_segment_invalid"
    assert {p.name: p.read_bytes() for p in workspace.store.directory.iterdir()} == before


def test_long_audition_is_not_automatically_cropped(
    reference_sound_workspace: ReferenceSoundWorkspace,
    reference_sound_source: tuple[bytes, str, int, tuple[str, ...]],
) -> None:
    workspace = reference_sound_workspace
    session = _generated(workspace, reference_sound_source)
    candidate = session["candidates"][0]
    before = {p.name: p.read_bytes() for p in workspace.store.directory.iterdir()}
    with pytest.raises(BoundaryError, match="explicit single-note") as failure:
        workspace.compare(
            session["session_id"],
            candidate["candidate_id"],
            candidate_sha256=candidate["frame_sha256"],
            recording=make_reference_pcm(frames=80000),
            cancel=Event(),
        )
    assert failure.value.context["error_code"] == "recording_too_long"
    assert {p.name: p.read_bytes() for p in workspace.store.directory.iterdir()} == before


def test_selected_segment_identity_tampering_is_rejected_without_publication(
    reference_sound_workspace: ReferenceSoundWorkspace,
    reference_sound_source: tuple[bytes, str, int, tuple[str, ...]],
) -> None:
    workspace = reference_sound_workspace
    session = _generated(workspace, reference_sound_source)
    candidate = session["candidates"][0]
    compared = workspace.commit(
        workspace.compare(
            session["session_id"],
            candidate["candidate_id"],
            candidate_sha256=candidate["frame_sha256"],
            recording=make_reference_pcm(frames=1600, sample_values=tuple(range(1600))),
            start_frame=800,
            frame_count=800,
            cancel=Event(),
        )
    )
    compared["recordings"][0]["segment"]["start_frame"] = 0
    workspace.store.publish(compared, {})
    with pytest.raises(ValueError, match="exact original"):
        workspace.reopen(session["session_id"])


def test_recording_segment_digest_must_match_its_measured_audio(
    reference_sound_workspace: ReferenceSoundWorkspace,
    reference_sound_source: tuple[bytes, str, int, tuple[str, ...]],
) -> None:
    workspace = reference_sound_workspace
    session = _generated(workspace, reference_sound_source)
    candidate = session["candidates"][0]
    compared = workspace.compare(
        session["session_id"],
        candidate["candidate_id"],
        candidate_sha256=candidate["frame_sha256"],
        recording=make_reference_pcm(),
        cancel=Event(),
    ).payload
    record = compared["recordings"][0]
    record["segment"]["sha256"] = "0" * 64
    with pytest.raises(ValueError, match="segment identity"):
        sound_recording_from_dict(record)


@pytest.mark.parametrize(
    "alteration", ["missing", "extra", "future-version", "bool-version", "rytm-version"]
)
def test_optional_context_keys_do_not_weaken_required_fields_or_model_validation(
    alteration: str,
) -> None:
    context = {
        "device_id": "analog_four_mk2",
        "target": 1,
        "source_sha256": "a" * 64,
        "segment_sha256": "b" * 64,
        "parameters": ["noise_fade"],
        "locks": [],
        "strength": 0.5,
    }
    if alteration == "missing":
        del context["target"]
    elif alteration == "extra":
        context["untrusted_policy"] = True
    else:
        context["inference_version"] = (
            3 if alteration == "future-version" else True if alteration == "bool-version" else 2
        )
        if alteration == "rytm-version":
            context["device_id"] = "analog_rytm_mk2"
    with pytest.raises((ValueError, TypeError)):
        sound_context_from_dict(context)
