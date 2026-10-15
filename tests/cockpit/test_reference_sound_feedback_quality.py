"""Server-authoritative feedback holds preserve local work and output boundaries."""

from __future__ import annotations

import asyncio
from dataclasses import replace
from pathlib import Path
from threading import Event

import pytest
from cockpit.conftest import (
    make_generated_reference_sound,
    make_reference_pcm,
    make_reference_sound_session,
)

from rytm_randomizer.cockpit.export.reference_sound_session import ReferenceSoundWorkspace
from rytm_randomizer.cockpit.ws.handlers import handle_command
from rytm_randomizer.observability.errors import BoundaryError
from rytm_randomizer.observability.metrics import get_metrics
from rytm_randomizer.style_analysis.extractor import AudioFeatureAnalysis

pytestmark = pytest.mark.fast


def _generated(workspace: ReferenceSoundWorkspace, source: tuple[bytes, str, int, tuple[str, ...]]):
    generated = make_generated_reference_sound(workspace, source, "Quality boundary")
    return workspace.select(
        generated["session_id"], generated["selected_candidate_id"], favorite=True
    )


@pytest.mark.parametrize(
    "problem,reason",
    [
        ("missing", "recording_quality_required"),
        ("quiet_audio", "recording_quality_unreliable"),
        ("clipped_audio", "recording_quality_unreliable"),
        ("multiple_notes", "recording_quality_unreliable"),
        ("pitch_uncertain", "recording_quality_unreliable"),
        ("octave", "recording_pitch_mismatch"),
    ],
)
@pytest.mark.usefixtures("offline_hardware_denied")
def test_raw_refinement_command_cannot_bypass_recording_quality_or_pitch_holds(
    tmp_path: Path,
    reference_sound_workspace: ReferenceSoundWorkspace,
    reference_sound_source: tuple[bytes, str, int, tuple[str, ...]],
    problem: str,
    reason: str,
) -> None:
    workspace = reference_sound_workspace
    payload = _generated(workspace, reference_sound_source)
    candidate = payload["candidates"][0]
    analyzer = workspace.analyzer

    def bad_recording(path: Path, cancel: Event) -> AudioFeatureAnalysis:
        measured = analyzer(path, cancel)
        diagnostics = measured.diagnostics
        assert diagnostics is not None
        if problem == "missing":
            diagnostics = None
        elif problem == "octave":
            diagnostics = replace(diagnostics, qualified_pitch_hz=220.0)
        else:
            diagnostics = replace(diagnostics, warnings=(problem,), refinement_blockers=(problem,))
            if problem == "quiet_audio":
                diagnostics = replace(diagnostics, rms=0.0005, peak=0.001)
            elif problem == "clipped_audio":
                diagnostics = replace(diagnostics, peak=1.0, clipped_fraction=0.2)
            elif problem == "multiple_notes":
                diagnostics = replace(
                    diagnostics,
                    multiple_pitch=True,
                    note_count=2,
                    onset_count=1,
                    qualified_pitch_hz=None,
                    pitch_status="uncertain",
                    warnings=("multiple_notes", "pitch_uncertain"),
                    refinement_blockers=("multiple_notes", "pitch_uncertain"),
                )
            else:
                diagnostics = replace(
                    diagnostics, qualified_pitch_hz=None, pitch_status="uncertain", note_count=None
                )
        return replace(
            measured,
            diagnostics=diagnostics,
            synthesis_features=replace(measured.synthesis_features, brightness=0.25),
        )

    workspace.analyzer = bad_recording
    compared = workspace.commit(
        workspace.compare(
            payload["session_id"],
            candidate["candidate_id"],
            candidate_sha256=candidate["frame_sha256"],
            recording=make_reference_pcm(frames=1600),
            cancel=Event(),
        )
    )
    assert compared["recordings"][0]["physical_validation"] is False
    assert compared["recordings"][0]["pitch_comparison"]["support_status"] == "held"
    session, _ = make_reference_sound_session(tmp_path, workspace, reference_sound_source)
    before = {p.name: p.read_bytes() for p in workspace.store.directory.iterdir()}
    command = {
        "type": "reference_sound",
        "action": "refine",
        "session_id": payload["session_id"],
        "candidate_id": candidate["candidate_id"],
        "correction_gain": 0.5,
    }
    ack = asyncio.run(
        handle_command({"request_id": "untrusted-ui-refine", "command": command}, session)
    )
    assert ack["ok"] is False
    assert reason in str(ack)
    assert session.armed_apply is None and session.current_send_plan is None
    assert {p.name: p.read_bytes() for p in workspace.store.directory.iterdir()} == before
    assert workspace.reopen(payload["session_id"]) == compared
    assert compared["favorites"] == [candidate["candidate_id"]]


@pytest.mark.parametrize("cents", [-100.1, -99.9, 99.9, 100.1])
@pytest.mark.usefixtures("offline_hardware_denied")
def test_raw_refinement_command_enforces_signed_one_semitone_boundary(
    tmp_path: Path,
    reference_sound_workspace: ReferenceSoundWorkspace,
    reference_sound_source: tuple[bytes, str, int, tuple[str, ...]],
    cents: float,
    reference_sound_caplog: pytest.LogCaptureFixture,
) -> None:
    workspace = reference_sound_workspace
    caplog = reference_sound_caplog
    payload = _generated(workspace, reference_sound_source)
    candidate = payload["candidates"][0]
    analyzer = workspace.analyzer
    pitch = payload["analysis"]["diagnostics"]["qualified_pitch_hz"]

    def shifted(path: Path, cancel: Event) -> AudioFeatureAnalysis:
        measured = analyzer(path, cancel)
        assert measured.diagnostics is not None
        return replace(
            measured,
            diagnostics=replace(
                measured.diagnostics, qualified_pitch_hz=pitch * 2 ** (cents / 1200)
            ),
            synthesis_features=replace(measured.synthesis_features, brightness=0.25),
        )

    workspace.analyzer = shifted
    compared = workspace.commit(
        workspace.compare(
            payload["session_id"],
            candidate["candidate_id"],
            candidate_sha256=candidate["frame_sha256"],
            recording=make_reference_pcm(frames=1600),
            cancel=Event(),
        )
    )
    session, _ = make_reference_sound_session(tmp_path, workspace, reference_sound_source)
    before = {p.name: p.read_bytes() for p in workspace.store.directory.iterdir()}
    held = abs(cents) > 100
    metric = f"refinement_quality:{'refused' if held else 'verified'}"
    count = get_metrics().local_artifact_decisions[metric]
    with caplog.at_level("INFO", logger="rytm_randomizer.cockpit.export.reference_sound_session"):
        ack = asyncio.run(
            handle_command(
                {
                    "request_id": "boundary-refine",
                    "command": {
                        "type": "reference_sound",
                        "action": "refine",
                        "session_id": payload["session_id"],
                        "candidate_id": candidate["candidate_id"],
                        "correction_gain": 0.5,
                    },
                },
                session,
            )
        )
    assert ack["ok"] is not held
    comparison = compared["recordings"][0]["pitch_comparison"]
    assert comparison["delta_cents"] == pytest.approx(cents, abs=1e-8)
    assert comparison["blockers"] == (["pitch_mismatch"] if held else [])
    if held:
        assert "recording_pitch_mismatch" in str(ack)
        assert {p.name: p.read_bytes() for p in workspace.store.directory.iterdir()} == before
        assert workspace.reopen(payload["session_id"]) == compared
    else:
        assert len(workspace.reopen(payload["session_id"])["refinements"]) == 1
    assert session.armed_apply is None and session.current_send_plan is None
    assert get_metrics().local_artifact_decisions[metric] == count + 1
    decisions = [
        r for r in caplog.records if r.message == "reference_sound_refinement_quality_decision"
    ]
    assert len(decisions) == 1
    decision = decisions[0]
    assert decision.outcome == ("refused" if held else "accepted")
    assert decision.support_status == ("held" if held else "supported")
    assert decision.blockers == (("pitch_mismatch",) if held else ())
    assert decision.stage == "quality_gate_only"
    assert not any(
        key in decision.__dict__ for key in ("session_id", "candidate_id", "audio_sha256", "path")
    )


def test_quality_acceptance_is_not_reported_as_publication_success_after_later_failure(
    reference_sound_workspace: ReferenceSoundWorkspace,
    reference_sound_source: tuple[bytes, str, int, tuple[str, ...]],
    monkeypatch: pytest.MonkeyPatch,
    reference_sound_caplog: pytest.LogCaptureFixture,
) -> None:
    workspace = reference_sound_workspace
    caplog = reference_sound_caplog
    payload = _generated(workspace, reference_sound_source)
    candidate = payload["candidates"][0]
    analyzer = workspace.analyzer

    def changed_feedback(path: Path, cancel: Event) -> AudioFeatureAnalysis:
        measured = analyzer(path, cancel)
        return replace(
            measured, synthesis_features=replace(measured.synthesis_features, brightness=0.25)
        )

    workspace.analyzer = changed_feedback
    compared = workspace.commit(
        workspace.compare(
            payload["session_id"],
            candidate["candidate_id"],
            candidate_sha256=candidate["frame_sha256"],
            recording=make_reference_pcm(),
            cancel=Event(),
        )
    )
    before = {p.name: p.read_bytes() for p in workspace.store.directory.iterdir()}

    def fail_after_quality(*_args: object, **_kwargs: object) -> None:
        raise ValueError("private-score-failure")

    monkeypatch.setattr(
        "rytm_randomizer.cockpit.export.reference_sound_session.plan_audio_feature_refinement",
        fail_after_quality,
    )
    with (
        caplog.at_level("INFO", logger="rytm_randomizer.cockpit.export.reference_sound_session"),
        pytest.raises(ValueError, match="private-score-failure"),
    ):
        workspace.refine(
            payload["session_id"], candidate["candidate_id"], correction_gain=0.5, cancel=Event()
        )
    decisions = [
        r for r in caplog.records if r.message == "reference_sound_refinement_quality_decision"
    ]
    assert len(decisions) == 1 and decisions[0].outcome == "accepted"
    assert decisions[0].stage == "quality_gate_only"
    assert "private-score-failure" not in str(decisions[0].__dict__)
    assert {p.name: p.read_bytes() for p in workspace.store.directory.iterdir()} == before
    assert workspace.reopen(payload["session_id"]) == compared


def test_legacy_recording_reopens_exactly_but_new_refinement_requires_fresh_diagnostics(
    reference_sound_workspace: ReferenceSoundWorkspace,
    reference_sound_source: tuple[bytes, str, int, tuple[str, ...]],
) -> None:
    workspace = reference_sound_workspace
    payload = _generated(workspace, reference_sound_source)
    candidate = payload["candidates"][0]
    compared = workspace.commit(
        workspace.compare(
            payload["session_id"],
            candidate["candidate_id"],
            candidate_sha256=candidate["frame_sha256"],
            recording=make_reference_pcm(frames=1600),
            cancel=Event(),
        )
    )
    del compared["analysis"]["diagnostics"]
    del compared["recordings"][0]["features"]["diagnostics"]
    del compared["recordings"][0]["pitch_comparison"]
    del compared["recordings"][0]["segment"]
    workspace.store.publish(compared, {})
    before = {p.name: p.read_bytes() for p in workspace.store.directory.iterdir()}
    assert workspace.reopen(payload["session_id"]) == compared
    with pytest.raises(BoundaryError) as failure:
        workspace.refine(
            payload["session_id"], candidate["candidate_id"], correction_gain=0.5, cancel=Event()
        )
    assert failure.value.context["error_code"] == "recording_quality_required"
    assert {p.name: p.read_bytes() for p in workspace.store.directory.iterdir()} == before


def test_rehashed_pitch_comparison_disagreement_is_refused_on_reopen(
    reference_sound_workspace: ReferenceSoundWorkspace,
    reference_sound_source: tuple[bytes, str, int, tuple[str, ...]],
) -> None:
    workspace = reference_sound_workspace
    payload = _generated(workspace, reference_sound_source)
    candidate = payload["candidates"][0]
    compared = workspace.commit(
        workspace.compare(
            payload["session_id"],
            candidate["candidate_id"],
            candidate_sha256=candidate["frame_sha256"],
            recording=make_reference_pcm(),
            cancel=Event(),
        )
    )
    compared["recordings"][0]["pitch_comparison"]["delta_cents"] = 50.0
    workspace.store.publish(compared, {})
    with pytest.raises(ValueError, match="pitch diagnostics"):
        workspace.reopen(payload["session_id"])


def test_measuring_legacy_reference_preserves_every_candidate_favorite_and_session_identity(
    reference_sound_workspace: ReferenceSoundWorkspace,
    reference_sound_source: tuple[bytes, str, int, tuple[str, ...]],
) -> None:
    workspace = reference_sound_workspace
    payload = _generated(workspace, reference_sound_source)
    candidate = payload["candidates"][0]
    del payload["analysis"]["diagnostics"]
    workspace.store.publish(payload, {})
    compared = workspace.commit(
        workspace.compare(
            payload["session_id"],
            candidate["candidate_id"],
            candidate_sha256=candidate["frame_sha256"],
            recording=make_reference_pcm(frames=1600),
            cancel=Event(),
        )
    )
    assert compared["recordings"][0]["pitch_comparison"]["blockers"] == ["diagnostics_missing"]
    refreshed = workspace.commit(workspace.measure_reference(payload["session_id"], cancel=Event()))
    assert refreshed["session_id"] == payload["session_id"]
    assert refreshed["candidates"] == payload["candidates"]
    assert refreshed["favorites"] == payload["favorites"]
    assert refreshed["context"] == payload["context"]
    assert refreshed["segment"] == payload["segment"]
    assert {k: v for k, v in refreshed["analysis"].items() if k != "diagnostics"} == payload[
        "analysis"
    ]
    assert refreshed["recordings"][0]["pitch_comparison"]["support_status"] == "supported"
    assert workspace.reopen(payload["session_id"]) == refreshed
    assert (
        workspace.commit(workspace.measure_reference(payload["session_id"], cancel=Event()))
        == refreshed
    )


@pytest.mark.parametrize("outcome", ["refreshed", "reused"])
def test_measure_reference_wire_action_adds_only_missing_diagnostics_and_keeps_output_disarmed(
    tmp_path: Path,
    reference_sound_workspace: ReferenceSoundWorkspace,
    reference_sound_source: tuple[bytes, str, int, tuple[str, ...]],
    outcome: str,
) -> None:
    workspace = reference_sound_workspace
    payload = _generated(workspace, reference_sound_source)
    if outcome == "refreshed":
        del payload["analysis"]["diagnostics"]
    workspace.store.publish(payload, {})
    runtime, _ = make_reference_sound_session(tmp_path, workspace, reference_sound_source)
    counter = get_metrics().local_artifact_decisions
    before = counter[f"measure_reference:{outcome}"]
    ack = asyncio.run(
        handle_command(
            {
                "request_id": "measure-exact-reference",
                "command": {
                    "type": "reference_sound",
                    "action": "measure",
                    "session_id": payload["session_id"],
                },
            },
            runtime,
        )
    )
    assert ack["ok"] is True
    reopened = workspace.reopen(payload["session_id"])
    assert reopened["analysis"]["diagnostics"]["audio_sha256"] == payload["segment"]["sha256"]
    assert reopened["candidates"] == payload["candidates"]
    assert reopened["favorites"] == payload["favorites"]
    assert runtime.armed_apply is None and runtime.current_send_plan is None
    assert runtime.sound_cancel is None
    assert counter[f"measure_reference:{outcome}"] == before + 1


def test_measure_refuses_unbound_or_missing_diagnostic_result_without_publication(
    reference_sound_workspace: ReferenceSoundWorkspace,
    reference_sound_source: tuple[bytes, str, int, tuple[str, ...]],
) -> None:
    workspace = reference_sound_workspace
    imported = workspace.import_reference(make_reference_pcm(), "Unbound")
    with pytest.raises(ValueError, match="source-bound"):
        workspace.measure_reference(imported["session_id"], cancel=Event())
    payload = _generated(workspace, reference_sound_source)
    del payload["analysis"]["diagnostics"]
    workspace.store.publish(payload, {})
    analyzer = workspace.analyzer
    workspace.analyzer = lambda path, cancel: replace(analyzer(path, cancel), diagnostics=None)
    before = {p.name: p.read_bytes() for p in workspace.store.directory.iterdir()}
    with pytest.raises(BoundaryError) as failure:
        workspace.measure_reference(payload["session_id"], cancel=Event())
    assert failure.value.context["error_code"] == "recording_quality_required"
    assert {p.name: p.read_bytes() for p in workspace.store.directory.iterdir()} == before


def test_rehashed_measurement_hash_disagreement_refuses_reopen_without_rewriting_work(
    reference_sound_workspace: ReferenceSoundWorkspace,
    reference_sound_source: tuple[bytes, str, int, tuple[str, ...]],
) -> None:
    workspace = reference_sound_workspace
    payload = _generated(workspace, reference_sound_source)
    payload["analysis"]["features"]["audio_sha256"] = "a" * 64
    payload["analysis"]["diagnostics"]["audio_sha256"] = "a" * 64
    workspace.store.publish(payload, {})
    before = {p.name: p.read_bytes() for p in workspace.store.directory.iterdir()}
    with pytest.raises(ValueError, match="different segment"):
        workspace.reopen(payload["session_id"])
    assert {p.name: p.read_bytes() for p in workspace.store.directory.iterdir()} == before


@pytest.mark.parametrize("kind", ["reference", "recording"])
@pytest.mark.parametrize(
    ("field", "value"),
    [("sample_rate", 16000), ("channels", 2), ("start_sample", 10**12), ("sample_count", 1599)],
)
def test_rehashed_diagnostic_range_must_match_the_actual_retained_wav(
    reference_sound_workspace: ReferenceSoundWorkspace,
    reference_sound_source: tuple[bytes, str, int, tuple[str, ...]],
    kind: str,
    field: str,
    value: int,
) -> None:
    workspace = reference_sound_workspace
    payload = _generated(workspace, reference_sound_source)
    candidate = payload["candidates"][0]
    payload = workspace.commit(
        workspace.compare(
            payload["session_id"],
            candidate["candidate_id"],
            candidate_sha256=candidate["frame_sha256"],
            recording=make_reference_pcm(frames=1600),
            cancel=Event(),
        )
    )
    analysis = payload["analysis"] if kind == "reference" else payload["recordings"][0]["features"]
    analysis["diagnostics"][field] = value
    workspace.store.publish(payload, {})
    before = {p.name: p.read_bytes() for p in workspace.store.directory.iterdir()}
    with pytest.raises(ValueError, match="Diagnostic sample range"):
        workspace.reopen(payload["session_id"])
    assert {p.name: p.read_bytes() for p in workspace.store.directory.iterdir()} == before


def test_rehashed_recording_measurements_cannot_claim_another_audio_hash(
    reference_sound_workspace: ReferenceSoundWorkspace,
    reference_sound_source: tuple[bytes, str, int, tuple[str, ...]],
) -> None:
    workspace = reference_sound_workspace
    payload = _generated(workspace, reference_sound_source)
    candidate = payload["candidates"][0]
    payload = workspace.commit(
        workspace.compare(
            payload["session_id"],
            candidate["candidate_id"],
            candidate_sha256=candidate["frame_sha256"],
            recording=make_reference_pcm(frames=1600),
            cancel=Event(),
        )
    )
    features = payload["recordings"][0]["features"]
    features["features"]["audio_sha256"] = "b" * 64
    features["diagnostics"]["audio_sha256"] = "b" * 64
    workspace.store.publish(payload, {})
    before = {p.name: p.read_bytes() for p in workspace.store.directory.iterdir()}
    with pytest.raises(ValueError, match="Recording measurements differ"):
        workspace.reopen(payload["session_id"])
    assert {p.name: p.read_bytes() for p in workspace.store.directory.iterdir()} == before


def test_measurement_publication_failure_has_no_success_outcome_or_partial_work(
    tmp_path: Path,
    reference_sound_workspace: ReferenceSoundWorkspace,
    reference_sound_source: tuple[bytes, str, int, tuple[str, ...]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = reference_sound_workspace
    payload = _generated(workspace, reference_sound_source)
    del payload["analysis"]["diagnostics"]
    workspace.store.publish(payload, {})
    runtime, _ = make_reference_sound_session(tmp_path, workspace, reference_sound_source)
    before = {p.name: p.read_bytes() for p in workspace.store.directory.iterdir()}
    decisions = dict(get_metrics().local_artifact_decisions)

    def fail_publish(*_args: object, **_kwargs: object) -> None:
        raise OSError("test-owned publication interruption")

    monkeypatch.setattr(workspace.store, "publish", fail_publish)
    ack = asyncio.run(
        handle_command(
            {
                "command": {
                    "type": "reference_sound",
                    "action": "measure",
                    "session_id": payload["session_id"],
                }
            },
            runtime,
        )
    )
    assert ack["ok"] is False
    assert dict(get_metrics().local_artifact_decisions) == decisions
    assert {p.name: p.read_bytes() for p in workspace.store.directory.iterdir()} == before
    assert runtime.armed_apply is None and runtime.current_send_plan is None


def test_worker_diagnostic_range_refuses_generation_before_publication(
    reference_sound_workspace: ReferenceSoundWorkspace,
    reference_sound_source: tuple[bytes, str, int, tuple[str, ...]],
) -> None:
    workspace = reference_sound_workspace
    payload = _generated(workspace, reference_sound_source)
    selected = workspace.select_segment(payload["session_id"], start_frame=1, frame_count=799)
    before = {p.name: p.read_bytes() for p in workspace.store.directory.iterdir()}
    analyzer = workspace.analyzer

    def wrong_range(path: Path, cancel: Event) -> AudioFeatureAnalysis:
        result = analyzer(path, cancel)
        assert result.diagnostics is not None
        return replace(result, diagnostics=replace(result.diagnostics, start_sample=1))

    workspace.analyzer = wrong_range
    frame, device, target, parameters = reference_sound_source
    with pytest.raises(ValueError, match="Diagnostic sample range"):
        workspace.generate(
            selected["session_id"],
            source_frame=frame,
            device_id=device,
            target=target,
            parameters=parameters,
            locks=(),
            strength=1.0,
            cancel=Event(),
        )
    assert {p.name: p.read_bytes() for p in workspace.store.directory.iterdir()} == before
