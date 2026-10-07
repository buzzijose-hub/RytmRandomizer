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


def test_a4_one_explicit_cell_preserves_excluded_fractional_native_values(tmp_path) -> None:
    from dataclasses import replace

    from cockpit.conftest import capture_fixed_frame

    from conftest import analog_four_saved_kit_frame
    from rytm_randomizer.cockpit.capture import (
        ANALOG_FOUR_DEVICE_ID,
        cockpit_snapshot_from_rytm_capture,
    )
    from rytm_randomizer.cockpit.data.show_bank import ShowKitRecipe
    from rytm_randomizer.cockpit.show_bank.forge import build_source_entry, forge_candidate_pair
    from rytm_randomizer.data.analog_four_sysex_calibration import (
        A4_FILTER1_FREQUENCY_PARAMETER,
        analog_four_sysex_calibration_for,
    )
    from rytm_randomizer.devices import resolve_saved_kit_capture_capability

    harness = build_show_bank_harness(tmp_path)
    calibration = analog_four_sysex_calibration_for(A4_FILTER1_FREQUENCY_PARAMETER)
    overrides = {}
    for track in range(1, 5):
        offset = calibration.native_offset_for_track(track)
        overrides[offset], overrides[offset + 1] = divmod(16257, 256)
    frame = analog_four_saved_kit_frame(unpacked_overrides=overrides)
    a4 = capture_fixed_frame(ANALOG_FOUR_DEVICE_ID, frame)
    source = cockpit_snapshot_from_rytm_capture(harness.rytm)
    entry = build_source_entry(
        entry_id="positive-cell",
        cue_index=1,
        name="Positive scope",
        description="software fixture",
        rytm_capture=harness.rytm,
        analog_four_capture=a4,
        rytm_slot=20,
        analog_four_slot=21,
        rytm_snapshot_id=source.snapshot_id,
        now=harness.clock(),
    )
    recipe = ShowKitRecipe(
        profile_id=harness.profile.profile_id,
        depth_preset="small",
        depth=0.25,
        seed=7373,
        rytm_scope=ShowKitScope(RYTM_SHOW_KIT_DEVICE_ID, parameters=ParameterSelection(())),
        analog_four_scope=ShowKitScope(
            A4_SHOW_KIT_DEVICE_ID,
            target_ids=(1, 2, 3, 4),
            parameters=ParameterSelection((ParameterCell(3, A4_FILTER1_FREQUENCY_PARAMETER),)),
        ),
    )
    first = forge_candidate_pair(
        entry=entry,
        rytm_source_snapshot=source,
        analog_four_source_frame=frame,
        profile=harness.profile,
        recipe=recipe,
        now=harness.clock(),
    )
    second = forge_candidate_pair(
        entry=entry,
        rytm_source_snapshot=source,
        analog_four_source_frame=frame,
        profile=harness.profile,
        recipe=recipe,
        now=harness.clock(),
    )
    assert first.analog_four_frame == second.analog_four_frame
    assert first.candidate.to_dict() == second.candidate.to_dict()
    assert [value.track_id for value in first.candidate.analog_four_candidate.values] == [3]
    codec = resolve_saved_kit_capture_capability(ANALOG_FOUR_DEVICE_ID).capability
    original = codec.decode_saved_kit_capture(frame).unpacked
    rendered = codec.decode_saved_kit_capture(first.analog_four_frame).unpacked
    offset = calibration.native_offset_for_track(3)
    assert rendered[offset : offset + 2] != original[offset : offset + 2]
    assert (
        rendered[:offset] == original[:offset] and rendered[offset + 2 :] == original[offset + 2 :]
    )
    for track in (1, 2, 4):
        excluded = calibration.native_offset_for_track(track)
        assert int.from_bytes(rendered[excluded : excluded + 2], "big") == 16257
    assert first.candidate.analog_four_candidate.evidence_status != "hardware-write-validated"
    with pytest.raises(ValueError, match="offline-only"):
        replace(first.candidate.analog_four_candidate, evidence_status="hardware-write-validated")


@pytest.mark.parametrize("key", [None, "Amp Attack"])
def test_a4_scope_excludes_or_refuses_unpromoted_fields(tmp_path, key) -> None:
    harness = build_show_bank_harness(tmp_path)
    selection = (
        ParameterSelection(()) if key is None else ParameterSelection((ParameterCell(1, key),))
    )

    def generate():
        return harness.workspace.generate_candidates(
            harness.bank_id,
            harness.entry_id,
            harness.workspace.bank(harness.bank_id).revision,
            profile=harness.profile,
            depth_preset="small",
            depth=0.25,
            seed=6789,
            candidate_count=1,
            rytm_targets=(2,),
            rytm_locks=(),
            analog_four_targets=(),
            analog_four_locks=(),
            rytm_parameters=ParameterSelection(()),
            analog_four_parameters=selection,
        )

    if key is not None:
        with pytest.raises(ValueError, match="unsupported saved-KIT field"):
            generate()
    else:
        (candidate,) = generate()
        assert candidate.analog_four_candidate.values == ()


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
