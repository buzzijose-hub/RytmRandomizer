"""Scoped cue recall preserves inert recovery evidence, never output authority."""

from __future__ import annotations

import asyncio
from datetime import timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest
from cockpit.conftest import FixedFrameCaptureProvider

from conftest import RecordingOut
from rytm_randomizer.cockpit.capture import ANALOG_RYTM_DEVICE_ID, KitCaptureService
from rytm_randomizer.cockpit.data.parameter_scope import ParameterCell, ParameterSelection
from rytm_randomizer.cockpit.data.show_bank import (
    A4_SHOW_KIT_DEVICE_ID,
    RYTM_SHOW_KIT_DEVICE_ID,
    ShowKitScope,
)
from rytm_randomizer.cockpit.device import MockDeviceAdapter
from rytm_randomizer.cockpit.history import HistoryStore
from rytm_randomizer.cockpit.profiles import ProfileRegistry
from rytm_randomizer.cockpit.ws import handlers
from rytm_randomizer.cockpit.ws.session import CockpitSession
from rytm_randomizer.senders.armed_apply import ArmedApplySession

from .conftest import ShowBankHarness, build_show_bank_harness

pytestmark = pytest.mark.fast


@pytest.fixture
def scoped_show(tmp_path: Path) -> tuple[ShowBankHarness, CockpitSession, tuple[str, ...]]:
    harness = build_show_bank_harness(tmp_path)
    workspace = harness.workspace
    ids: list[str] = []
    for key, seed in (("flt", 91), ("overdrive", 92)):
        (candidate,) = workspace.generate_candidates(
            harness.bank_id,
            harness.entry_id,
            workspace.bank(harness.bank_id).revision,
            profile=harness.profile,
            depth_preset="small",
            depth=0.25,
            seed=seed,
            candidate_count=1,
            rytm_targets=(2,),
            rytm_locks=tuple(item for item in range(1, 13) if item != 2),
            analog_four_targets=(),
            analog_four_locks=(1, 2, 3, 4),
            rytm_parameters=ParameterSelection((ParameterCell(2, key),)),
            analog_four_parameters=ParameterSelection(()),
        )
        ids.append(candidate.candidate_id)
    source = workspace.source_snapshot(harness.bank_id, harness.entry_id)
    history = HistoryStore()
    history.initial(source)
    session = CockpitSession(
        profile_registry=ProfileRegistry(tmp_path / "profiles"),
        history_store=history,
        device=MockDeviceAdapter(source),
        kit_captures=harness.captures,
        kit_capture_service=KitCaptureService(FixedFrameCaptureProvider(harness.rytm.frame)),
        show_kit_forge=workspace,
    )
    return harness, session, tuple(ids)


def _request(session: CockpitSession, command: dict[str, object]) -> dict[str, object]:
    return asyncio.run(
        handlers.handle_command({"request_id": "scope-recovery", "command": command}, session)
    )


def _select(
    harness: ShowBankHarness, session: CockpitSession, candidate_id: str
) -> dict[str, object]:
    return _request(
        session,
        {
            "type": "show_bank_select_candidate",
            "bank_id": harness.bank_id,
            "entry_id": harness.entry_id,
            "candidate_id": candidate_id,
            "expected_revision": harness.workspace.bank(harness.bank_id).revision,
        },
    )


def _fresh_dump_after_reload(harness: ShowBankHarness, session: CockpitSession) -> None:
    # Fake input only: exercise the actual capture handler and canonical codec.
    harness.workspace.revoke_hardware_evidence()
    captured = _request(
        session,
        {
            "type": "capture_current_kit",
            "device_id": ANALOG_RYTM_DEVICE_ID,
            "input_port": "Mock input",
        },
    )
    assert captured["ok"]
    result = session.kit_captures[ANALOG_RYTM_DEVICE_ID]
    assert result.fingerprint == harness.rytm.fingerprint
    harness.clock.current = result.captured_at + timedelta(seconds=2)


def test_disarmed_reselection_preserves_fresh_manual_reload_capture_gate(scoped_show) -> None:
    harness, session, ids = scoped_show
    assert _select(harness, session, ids[0])["ok"]
    _fresh_dump_after_reload(harness, session)
    before = session.kit_captures[ANALOG_RYTM_DEVICE_ID]
    harness.workspace.require_rytm_audition_source(
        ids[0], session.kit_captures, manually_reloaded=True
    )
    assert _select(harness, session, ids[0])["ok"]
    assert session.kit_captures[ANALOG_RYTM_DEVICE_ID] is before
    # Advancing cutoff during this inert selection would invalidate the dump.
    harness.workspace.require_rytm_audition_source(
        ids[0], session.kit_captures, manually_reloaded=True
    )
    assert session.armed_apply is None and not session.hardware_intent
    assert session.current_send_plan is None


def test_same_source_changed_cells_publish_scope_before_candidate(scoped_show) -> None:
    harness, session, ids = scoped_show
    assert _select(harness, session, ids[0])["ok"]
    first_source = session.device.capture_snapshot()
    first_scope = session.rytm_parameters
    assert _select(harness, session, ids[1])["ok"]
    assert session.device.capture_snapshot().snapshot_id == first_source.snapshot_id
    assert session.rytm_parameters != first_scope
    assert session.rytm_parameters == ParameterSelection((ParameterCell(2, "overdrive"),))
    events = session.pending_events
    kinds = [event["type"] for event in events]
    assert kinds.index("mutation_parameters_changed") < kinds.index("mutation_previewed")
    scope_event = events[kinds.index("mutation_parameters_changed")]
    assert scope_event["rytm_parameters"] == session.rytm_parameters.to_list()
    assert scope_event["a4_parameters"] == []
    candidate_event = events[kinds.index("mutation_previewed")]
    assert candidate_event["candidate"]["candidate_id"] == ids[1]
    assert session.current_send_plan is None and session.armed_apply is None


def test_real_output_revocation_advances_cutoff_even_when_preservation_requested(
    scoped_show,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    harness, session, ids = scoped_show
    assert _select(harness, session, ids[0])["ok"]
    _fresh_dump_after_reload(harness, session)
    recorder = RecordingOut()
    closed: list[bool] = []
    monkeypatch.setattr(recorder, "close", lambda: closed.append(True), raising=False)
    opener = SimpleNamespace(open_exact=lambda _name: recorder)
    token = "fixture-token"
    seam = ArmedApplySession(opener=opener, port_name="Fake output", arm_token=token)
    seam.arm(token)
    session.armed_apply = seam
    session.hardware_intent = True
    handlers.revoke_session_output(session, preserve_source_capture=True)
    assert session.armed_apply is None and not session.hardware_intent
    assert closed == [True] and recorder.sent == []
    with pytest.raises(ValueError, match="requires a new current-KIT dump"):
        harness.workspace.require_rytm_audition_source(
            ids[0], session.kit_captures, manually_reloaded=True
        )


@pytest.mark.parametrize("device,item", [(RYTM_SHOW_KIT_DEVICE_ID, 13), (A4_SHOW_KIT_DEVICE_ID, 5)])
def test_show_scope_refuses_parameter_cell_outside_device_domain(device, item) -> None:
    with pytest.raises(ValueError, match="parameter item is unavailable"):
        ShowKitScope(device, parameters=ParameterSelection((ParameterCell(item, "flt"),)))


@pytest.mark.parametrize("parameters", [None, [], {"cells": []}, "all"])
def test_show_scope_requires_typed_parameter_selection(parameters) -> None:
    with pytest.raises(TypeError, match="ParameterSelection"):
        ShowKitScope(RYTM_SHOW_KIT_DEVICE_ID, parameters=parameters)


@pytest.mark.parametrize(
    "selection",
    [ParameterSelection(), ParameterSelection(()), ParameterSelection((ParameterCell(2, "flt"),))],
)
def test_show_scope_serialization_retains_explicit_cells_and_legacy_all(selection) -> None:
    scope = ShowKitScope(
        RYTM_SHOW_KIT_DEVICE_ID, target_ids=(2,), locked_ids=(1,), parameters=selection
    )
    encoded = scope.to_dict()
    assert ("parameter_cells" in encoded) is (selection.cells is not None)
    assert ShowKitScope.from_dict(encoded) == scope
    if selection.cells is not None:
        assert encoded["parameter_cells"] == selection.to_list()
