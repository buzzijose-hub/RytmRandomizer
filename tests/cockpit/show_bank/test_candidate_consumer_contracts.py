"""Consumers reject contradictory public producer results without MIDI authority."""

from __future__ import annotations

import asyncio
from collections.abc import Mapping, Sequence
from dataclasses import replace
from datetime import timedelta
from pathlib import Path

import pytest

from rytm_randomizer.cockpit.capture import ANALOG_FOUR_DEVICE_ID, decode_kit_capture_frame
from rytm_randomizer.cockpit.data import MutationCandidate, Snapshot
from rytm_randomizer.cockpit.data.a4_preparation import A4_PREPARATION_PERMANENT_BLOCKERS
from rytm_randomizer.cockpit.data.parameter_scope import ParameterSelection
from rytm_randomizer.cockpit.data.show_bank import ShowBank, ShowBankEntry, ShowKitCandidate
from rytm_randomizer.cockpit.show_bank import workspace as workspace_module
from rytm_randomizer.cockpit.show_bank.a4_preparation import (
    A4PreparationContext,
    prepare_a4_audition,
)
from rytm_randomizer.cockpit.show_bank.export import verify_show_bank_frames
from rytm_randomizer.cockpit.show_bank.workspace import ShowKitForgeWorkspace
from rytm_randomizer.cockpit.ws import handlers
from rytm_randomizer.cockpit.ws.session import CockpitSession
from rytm_randomizer.devices import (
    AnalogFourFilter1FrequencyCandidateMutation,
    AnalogFourKitSnapshot,
    get_analog_four_filter1_frequency_candidate_capability,
    resolve_saved_kit_capture_capability,
)
from rytm_randomizer.devices.strategies.analog_four_filter1_frequency_candidate import (
    AnalogFourFilter1FrequencyCandidateResult,
)
from rytm_randomizer.snapshot.mutation_scope import MutationScope

from .test_native_offline_journey import (
    _RIO,
    _disk,
    _frame,
    _generate,
    _Journey,
    _journey,
    _session,
)

pytestmark = [pytest.mark.fast, pytest.mark.usefixtures("offline_hardware_denied")]


@pytest.fixture(autouse=True)
def refuse_output_and_partial_device_adoption(monkeypatch: pytest.MonkeyPatch) -> None:
    def forbidden(*_args: object, **_kwargs: object) -> None:
        pytest.fail("a refused consumer contract attempted output or device adoption")

    for member in ("list_input_names", "list_output_names", "open_input", "open_output"):
        monkeypatch.setattr(
            f"rytm_randomizer.mido_provider.MidoMidiPortProvider.{member}", forbidden
        )
    for member in ("arm", "confirm", "apply"):
        monkeypatch.setattr(
            f"rytm_randomizer.senders.armed_apply.ArmedApplySession.{member}", forbidden
        )
    for member in ("adopt_snapshot", "apply", "apply_send_plan"):
        monkeypatch.setattr(f"rytm_randomizer.cockpit.device.MockDeviceAdapter.{member}", forbidden)


def _generate_legacy(journey: _Journey, *, fully_locked: bool = False) -> ShowKitCandidate:
    (candidate,) = journey.workspace.generate_candidates(
        journey.bank_id,
        journey.entry_id,
        journey.workspace.bank(journey.bank_id).revision,
        profile=journey.profile,
        depth_preset="small",
        depth=0.25,
        seed=99,
        candidate_count=1,
        rytm_targets=(),
        rytm_locks=tuple(range(1, 13)),
        analog_four_targets=(1, 2),
        analog_four_locks=(1, 2, 3, 4) if fully_locked else (),
        rytm_parameters=ParameterSelection(()),
        offline_only=True,
    )
    return candidate


@pytest.mark.parametrize("contradiction", ["offset", "readback-value"])
def test_preparation_refuses_all_changes_when_verified_renderer_metadata_disagrees(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, contradiction: str
) -> None:
    journey = _journey(tmp_path)
    candidate = _generate_legacy(journey)
    workspace = journey.workspace
    bank = workspace.bank(journey.bank_id)
    entry = bank.entry(journey.entry_id)
    original = journey.originals[ANALOG_FOUR_DEVICE_ID]
    frame = _frame(journey, candidate)
    current = replace(
        decode_kit_capture_frame(ANALOG_FOUR_DEVICE_ID, original),
        captured_at=entry.updated_at + timedelta(seconds=1),
    )
    context = A4PreparationContext(
        scope=MutationScope(target_ids=frozenset({1, 2})),
        capture_after=entry.updated_at,
        checked_at=entry.updated_at + timedelta(seconds=2),
        current_capture=current,
        active_candidate_id=candidate.candidate_id,
        session_connected=True,
        candidate_is_local=True,
        source_reloaded=True,
        output_port_name="Exact offline A4 intent",
    )
    baseline = prepare_a4_audition(
        entry=entry, source_frame=original, candidate_frame=frame, context=context
    )
    assert baseline.candidate_bytes_verified and baseline.current_source_verified
    assert len(baseline.changes) == 2
    assert baseline.blocked_reasons == A4_PREPARATION_PERMANENT_BLOCKERS
    capability = get_analog_four_filter1_frequency_candidate_capability()
    render = capability.render_filter1_frequency_candidate
    results: list[AnalogFourFilter1FrequencyCandidateResult] = []

    def inconsistent_render(
        source: bytes, mutations: Sequence[AnalogFourFilter1FrequencyCandidateMutation]
    ) -> AnalogFourFilter1FrequencyCandidateResult:
        rendered = render(source, mutations)
        assert rendered.framed_sysex == frame
        assert rendered.roundtrip_redecoded and rendered.native_byte_isolation_validated
        assert rendered.hardware_send_validated is False
        first, last = rendered.applied_mutations
        # The first row is valid: refusing the later row must discard that partial review.
        if contradiction == "offset":
            last = replace(last, intended_unpacked_offsets=first.intended_unpacked_offsets)
        else:
            last = replace(last, redecoded_raw_q8_8=last.redecoded_raw_q8_8 ^ 1)
        result = replace(rendered, applied_mutations=(first, last))
        results.append(result)
        return result

    before = _disk(workspace.store.root)
    monkeypatch.setattr(capability, "render_filter1_frequency_candidate", inconsistent_render)
    report = prepare_a4_audition(
        entry=entry, source_frame=original, candidate_frame=frame, context=context
    )
    assert len(results) == 1
    assert report.blocked_reasons == ("candidate_bytes_invalid", *A4_PREPARATION_PERMANENT_BLOCKERS)
    assert not report.candidate_bytes_verified and report.current_source_verified
    assert report.changes == () and not report.ready and not report.hardware_send_validated
    assert report.output_authority == "offline-review-only"
    assert "packets" not in report.to_dict()
    assert workspace.bank(bank.bank_id) == bank
    assert _disk(workspace.store.root) == before


def _install_postverification_decoder_drift(
    monkeypatch: pytest.MonkeyPatch,
) -> list[str]:
    contradictory = decode_kit_capture_frame(
        ANALOG_FOUR_DEVICE_ID, (_RIO / "A4_Test2_T1_OSC1_FIN_P1_Kit.syx").read_bytes()
    ).snapshot
    assert isinstance(contradictory, AnalogFourKitSnapshot)
    decoder = resolve_saved_kit_capture_capability(ANALOG_FOUR_DEVICE_ID).device.snapshot_decoder
    decode = decoder.decode
    observations: list[str] = []

    def drifting_decode(raw: bytes, slot: int) -> AnalogFourKitSnapshot:
        snapshot = decode(raw, slot)
        assert isinstance(snapshot, AnalogFourKitSnapshot)
        if observations:
            assert snapshot.unpacked != contradictory.unpacked
            observations.append("contradictory-decode")
            return replace(snapshot, unpacked=contradictory.unpacked)
        return snapshot

    def verify_then_drift(bank: ShowBank, frames: Mapping[str, bytes]) -> None:
        # Run the complete real verifier before the registered decoder starts disagreeing.
        verify_show_bank_frames(bank, frames)
        observations.append("package-verified")

    monkeypatch.setattr(decoder, "decode", drifting_decode)
    monkeypatch.setattr(workspace_module, "verify_show_bank_frames", verify_then_drift)
    return observations


def _assert_no_recall_or_output(session: CockpitSession, source: Snapshot) -> None:
    assert session.device.capture_snapshot() == source
    assert session.active_profile is None and session.offline_a4_capture is None
    assert session.current_candidate is None and session.current_send_plan is None
    assert not session.recalled_offline_favorite and not session.pending_events
    assert not session.rytm_pad_targets and not session.pad_locks
    assert not session.a4_track_targets and not session.a4_track_locks
    assert session.armed_apply is None and not session.hardware_intent
    assert not session.device.is_armed


@pytest.mark.parametrize("algorithm", ["native", "legacy"])
@pytest.mark.parametrize("consumer", ["workspace", "command"])
def test_recall_refuses_decoder_drift_after_real_package_verification_without_publication(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, algorithm: str, consumer: str
) -> None:
    journey = _journey(tmp_path)
    candidate = (
        _generate(journey, fields=(), locks=(1, 2, 3, 4), count=1)[0]
        if algorithm == "native"
        else _generate_legacy(journey, fully_locked=True)
    )
    workspace = journey.workspace
    bank = workspace.bank(journey.bank_id)
    source, verified, frame = workspace.candidate_context(
        bank.bank_id, journey.entry_id, candidate.candidate_id
    )
    assert verified == candidate and candidate.analog_four_candidate.values == ()
    assert frame == journey.originals[ANALOG_FOUR_DEVICE_ID] == _frame(journey, candidate)
    session = _session(workspace, bank.bank_id, journey.entry_id, tmp_path)
    before = _disk(workspace.store.root)
    observations = _install_postverification_decoder_drift(monkeypatch)
    if consumer == "workspace":
        with pytest.raises(ValueError, match="candidate frame semantic fingerprint mismatch"):
            workspace.candidate_context(bank.bank_id, journey.entry_id, candidate.candidate_id)
    else:
        ack = asyncio.run(
            handlers.handle_command(
                {
                    "request_id": "decoder-drift",
                    "command": {
                        "type": "show_bank_select_candidate",
                        "bank_id": bank.bank_id,
                        "entry_id": journey.entry_id,
                        "candidate_id": candidate.candidate_id,
                        "expected_revision": bank.revision,
                    },
                },
                session,
            )
        )
        assert not ack["ok"] and ack["code"] == handlers.ERR_VALIDATION
    assert observations == ["package-verified", "contradictory-decode"]
    _assert_no_recall_or_output(session, source)
    assert workspace.bank(bank.bank_id) == bank
    assert _disk(workspace.store.root) == before
    assert not workspace.state_dict()["banks"][0]["readiness"]["show_ready"]


def test_command_refuses_successful_selection_result_when_store_still_has_no_selection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    journey = _journey(tmp_path)
    (candidate,) = _generate(journey, fields=("filter2_resonance",), count=1)
    bank = journey.workspace.bank(journey.bank_id)
    entry = replace(bank.entry(journey.entry_id), selected_candidate_id=None)
    unselected = replace(bank, entries=(entry,), revision=bank.revision + 1)
    journey.workspace.store.save(unselected)
    workspace = ShowKitForgeWorkspace(journey.workspace.store)
    source, verified, frame = workspace.candidate_context(
        bank.bank_id, entry.entry_id, candidate.candidate_id
    )
    assert verified == candidate and frame == _frame(journey, candidate)
    session = _session(workspace, bank.bank_id, entry.entry_id, tmp_path)
    calls: list[str] = []

    def selection_reports_success(
        bank_id: str,
        entry_id: str,
        candidate_id: str,
        expected_revision: int,
        *,
        offline_only: bool = False,
    ) -> tuple[ShowBankEntry, Snapshot, MutationCandidate]:
        assert (bank_id, entry_id, candidate_id, expected_revision, offline_only) == (
            bank.bank_id,
            entry.entry_id,
            candidate.candidate_id,
            unselected.revision,
            True,
        )
        calls.append(candidate_id)
        return entry, source, candidate.rytm_candidate

    before = _disk(workspace.store.root)
    monkeypatch.setattr(workspace, "select_candidate", selection_reports_success)
    ack = asyncio.run(
        handlers.handle_command(
            {
                "request_id": "selection-not-published",
                "command": {
                    "type": "show_bank_select_candidate",
                    "bank_id": bank.bank_id,
                    "entry_id": entry.entry_id,
                    "candidate_id": candidate.candidate_id,
                    "expected_revision": unselected.revision,
                },
            },
            session,
        )
    )
    assert calls == [candidate.candidate_id]
    assert not ack["ok"] and ack["code"] == handlers.ERR_VALIDATION
    _assert_no_recall_or_output(session, source)
    assert workspace.bank(bank.bank_id) == unselected
    assert _disk(workspace.store.root) == before
    assert not workspace.state_dict()["banks"][0]["readiness"]["show_ready"]
