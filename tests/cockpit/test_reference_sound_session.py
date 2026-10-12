"""Complete source-bound sound session with genuine persistence and fake measurements."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from threading import Event

import pytest
from cockpit.conftest import make_reference_pcm

from rytm_randomizer.cockpit.export.reference_sound_session import ReferenceSoundWorkspace
from rytm_randomizer.cockpit.export.reference_sound_store import reference_sound_digest
from rytm_randomizer.observability.errors import BoundaryError
from rytm_randomizer.style_analysis.extractor import AudioFeatureAnalysis

pytestmark = pytest.mark.fast


def _generate(
    workspace: ReferenceSoundWorkspace,
    source: tuple[bytes, str, int, tuple[str, ...]],
    *,
    strength: float = 1.0,
    locks: tuple[str, ...] = (),
) -> dict[str, object]:
    imported = workspace.import_reference(make_reference_pcm(), "Reference")
    frame, device, target, parameters = source
    prepared = workspace.generate(
        str(imported["session_id"]),
        source_frame=frame,
        device_id=device,
        target=target,
        parameters=parameters,
        locks=locks,
        strength=strength,
        cancel=Event(),
    )
    assert not (workspace.store.directory / f"{prepared.payload['session_id']}.sound.json").exists()
    return workspace.commit(prepared)


def test_full_both_device_journey_survives_restart_and_original_loss(
    reference_sound_workspace: ReferenceSoundWorkspace,
    reference_sound_source: tuple[bytes, str, int, tuple[str, ...]],
    tmp_path: Path,
) -> None:
    workspace = reference_sound_workspace
    payload = _generate(workspace, reference_sound_source)
    session_id = str(payload["session_id"])
    selected = payload["candidates"][0]
    candidate_id = selected["candidate_id"]
    candidate = workspace.candidate(session_id, candidate_id)
    assert candidate.changes
    before = candidate.frame
    workspace.select(session_id, candidate_id, favorite=True)
    reopened = ReferenceSoundWorkspace(workspace.store, analyzer=workspace.analyzer)
    assert reopened.reopen(session_id)["favorites"] == [candidate_id]
    assert reopened.candidate(session_id, candidate_id).frame == before
    recording = make_reference_pcm(frames=801)
    analyzer = reopened.analyzer

    def measured_recording(path: Path, cancel: Event) -> AudioFeatureAnalysis:
        analysis = analyzer(path, cancel)
        return replace(
            analysis, synthesis_features=replace(analysis.synthesis_features, brightness=0.25)
        )

    reopened.analyzer = measured_recording
    compared = reopened.commit(
        reopened.compare(
            session_id,
            candidate_id,
            candidate_sha256=reference_sound_digest(before),
            recording=recording,
            cancel=Event(),
        )
    )
    assert compared["recordings"][0]["score"] == 96
    assert compared["recordings"][0]["distance"] == 0.045
    assert compared["recordings"][0]["physical_validation"] is False
    assert "not a probability" in compared["recordings"][0]["metric"]
    prepared = reopened.refine(session_id, candidate_id, correction_gain=0.5, cancel=Event())
    refined = reopened.commit(prepared)
    assert len(refined["candidates"]) == 9
    assert refined["favorites"] == [candidate_id]
    assert reopened.reopen(session_id) == refined
    replayed = reopened.commit(
        reopened.refine(session_id, candidate_id, correction_gain=0.5, cancel=Event())
    )
    assert replayed == refined
    reopened.select(session_id, candidate_id, favorite=False)
    assert reopened.reopen(session_id)["favorites"] == []
    with pytest.raises(ValueError, match="another session"):
        reopened.select(session_id, "not-this-candidate")


def test_scope_changes_preserve_previous_favorite_and_exact_exclusions(
    reference_sound_workspace: ReferenceSoundWorkspace,
    reference_sound_source: tuple[bytes, str, int, tuple[str, ...]],
) -> None:
    workspace = reference_sound_workspace
    payload = _generate(workspace, reference_sound_source, locks=(reference_sound_source[3][0],))
    session_id = str(payload["session_id"])
    candidate_id = str(payload["selected_candidate_id"])
    workspace.select(session_id, candidate_id, favorite=True)
    locked = workspace.candidate(session_id, candidate_id)
    assert reference_sound_source[3][0] not in {item.parameter for item in locked.changes}
    base = workspace.import_reference(make_reference_pcm(), "Reference")
    source, device, target, parameters = reference_sound_source
    next_payload = workspace.commit(
        workspace.generate(
            str(base["session_id"]),
            source_frame=source,
            device_id=device,
            target=target,
            parameters=parameters,
            locks=(),
            strength=0.0,
            cancel=Event(),
        )
    )
    assert next_payload["session_id"] != session_id
    assert all(
        workspace.candidate(str(next_payload["session_id"]), item["candidate_id"]).frame == source
        for item in next_payload["candidates"]
    )
    assert workspace.reopen(session_id)["favorites"] == [candidate_id]
    assert workspace.candidate(session_id, candidate_id).frame == locked.frame


def test_repeated_generation_replays_favorites_without_reanalysis(
    reference_sound_workspace: ReferenceSoundWorkspace,
    reference_sound_source: tuple[bytes, str, int, tuple[str, ...]],
) -> None:
    workspace = reference_sound_workspace
    payload = _generate(workspace, reference_sound_source)
    session_id = str(payload["session_id"])
    saved = workspace.select(session_id, str(payload["selected_candidate_id"]), favorite=True)

    def unexpected(path: Path, cancel: Event) -> AudioFeatureAnalysis:
        raise AssertionError(
            "Identical generation should reuse its retained measurements and favorite."
        )

    workspace.analyzer = unexpected
    base = workspace.import_reference(make_reference_pcm(), "Reference")
    source, device, target, parameters = reference_sound_source
    result = workspace.generate(
        str(base["session_id"]),
        source_frame=source,
        device_id=device,
        target=target,
        parameters=parameters,
        locks=(),
        strength=1.0,
        cancel=Event(),
    )
    assert result.payload == saved


def test_segment_selection_is_independent_and_no_stale_candidate_is_adopted(
    reference_sound_workspace: ReferenceSoundWorkspace,
) -> None:
    workspace = reference_sound_workspace
    base = workspace.import_reference(make_reference_pcm(frames=1600), "Exact segment")
    selected = workspace.select_segment(str(base["session_id"]), 800, 800)
    assert selected["session_id"] != base["session_id"]
    assert selected["segment"]["start_frame"] == 800
    assert selected["analysis"] is None and selected["candidates"] == []
    assert workspace.reopen(str(base["session_id"])) == base


def test_cancelled_or_mismatched_analysis_never_publishes(
    reference_sound_workspace: ReferenceSoundWorkspace,
    reference_sound_source: tuple[bytes, str, int, tuple[str, ...]],
    audio_patch_dna_analysis: AudioFeatureAnalysis,
) -> None:
    workspace = reference_sound_workspace
    base = workspace.import_reference(make_reference_pcm(), "Reference")
    source, device, target, parameters = reference_sound_source
    before = {path.name: path.read_bytes() for path in workspace.store.directory.iterdir()}
    cancelled = Event()
    cancelled.set()
    with pytest.raises(BoundaryError) as failure:
        workspace.generate(
            str(base["session_id"]),
            source_frame=source,
            device_id=device,
            target=target,
            parameters=parameters,
            locks=(),
            strength=1.0,
            cancel=cancelled,
        )
    assert failure.value.context["error_code"] == "interrupted"
    workspace.analyzer = lambda path, cancel: audio_patch_dna_analysis
    with pytest.raises(ValueError, match="does not match"):
        workspace.generate(
            str(base["session_id"]),
            source_frame=source,
            device_id=device,
            target=target,
            parameters=parameters,
            locks=(),
            strength=1.0,
            cancel=Event(),
        )
    assert {path.name: path.read_bytes() for path in workspace.store.directory.iterdir()} == before


def test_wrong_recording_candidate_or_missing_recording_preserves_session(
    reference_sound_workspace: ReferenceSoundWorkspace,
    reference_sound_source: tuple[bytes, str, int, tuple[str, ...]],
) -> None:
    workspace = reference_sound_workspace
    payload = _generate(workspace, reference_sound_source)
    session_id = str(payload["session_id"])
    candidate_id = str(payload["selected_candidate_id"])
    with pytest.raises(ValueError, match="different candidate"):
        workspace.compare(
            session_id,
            candidate_id,
            candidate_sha256="0" * 64,
            recording=make_reference_pcm(),
            cancel=Event(),
        )
    with pytest.raises(BoundaryError, match="Supply a recording"):
        workspace.refine(session_id, candidate_id, correction_gain=0.5, cancel=Event())
    assert workspace.reopen(session_id) == payload


@pytest.mark.parametrize(
    "title", [" ", "bad\nname", "a" * 121], ids=["blank", "control-character", "too-long"]
)
def test_titles_are_bounded(reference_sound_workspace: ReferenceSoundWorkspace, title: str) -> None:
    with pytest.raises(ValueError):
        reference_sound_workspace.import_reference(make_reference_pcm(), title)
