"""Source recovery and transient hardware claims remain explicit and fail closed."""

from __future__ import annotations

import asyncio
from dataclasses import replace
from datetime import timedelta
from decimal import localcontext
from pathlib import Path
from typing import cast

import pytest
from cockpit.conftest import FixedFrameCaptureProvider as _CaptureProvider

from conftest import RecordingOut
from rytm_randomizer.cockpit.capture import (
    ANALOG_FOUR_DEVICE_ID,
    ANALOG_RYTM_DEVICE_ID,
    KitCaptureService,
    decode_kit_capture_frame,
)
from rytm_randomizer.cockpit.data.show_bank import (
    A4_SHOW_KIT_DEVICE_ID,
    RYTM_SHOW_KIT_DEVICE_ID,
    AnalogFourCandidateValue,
    HardwareSaveAttestation,
    ShowBank,
    ShowKitCandidate,
)
from rytm_randomizer.cockpit.device import MockDeviceAdapter
from rytm_randomizer.cockpit.device.connection import ConnectionState
from rytm_randomizer.cockpit.history import HistoryStore
from rytm_randomizer.cockpit.profiles import ProfileRegistry
from rytm_randomizer.cockpit.show_bank import workspace as workspace_module
from rytm_randomizer.cockpit.show_bank.export import ShowPackService
from rytm_randomizer.cockpit.show_bank.readiness import normalize_catalog_import
from rytm_randomizer.cockpit.show_bank.workspace import ShowKitForgeWorkspace
from rytm_randomizer.cockpit.ws import handlers
from rytm_randomizer.cockpit.ws.protocol import ERR_INTERNAL, ERR_VALIDATION
from rytm_randomizer.cockpit.ws.session import CockpitSession
from rytm_randomizer.senders.armed_apply import ArmedApplySession

from ._support import candidate
from .conftest import SHOW_BANK_BOUNDARY_NOW as _NOW
from .conftest import build_show_bank_harness as _harness
from .conftest import generate_show_bank_candidates as _generate

pytestmark = pytest.mark.fast


@pytest.mark.parametrize(
    ("path", "value"),
    (
        (("seed",), True),
        (("seed",), 7.0),
        (("estimated_midi_msgs",), True),
        (("estimated_midi_msgs",), 1.0),
        (("source_snapshot_id",), 1),
        (("depth",), True),
        (("depth",), float("inf")),
        (("pad_deltas",), {}),
        (("pad_deltas", 0), "not-a-pad"),
        (("pad_deltas", 0, "pad_id"), True),
        (("pad_deltas", 0, "pad_id"), 1.0),
        (("pad_deltas", 0, "changed_keys"), ["amp_volume", "amp_volume"]),
        (("pad_deltas", 0, "changed_keys"), [1]),
        (("pad_deltas", 0, "proposed_params"), {1: 55}),
        (("pad_deltas", 0, "proposed_params"), {"amp_volume": True}),
        (("pad_deltas", 0, "proposed_params"), {"amp_volume": 55.0}),
        (("pad_deltas", 0, "proposed_params"), {"amp_volume": "55"}),
    ),
)
def test_nested_rytm_import_rejects_coercible_scalar_and_container_values(
    path: tuple[str | int, ...], value: object
) -> None:
    raw = candidate().to_dict()
    current: object = raw["rytm_candidate"]
    for key in path[:-1]:
        current = (
            cast(list[object], current)[key]
            if isinstance(key, int)
            else (cast(dict[str, object], current)[key])
        )
    final = path[-1]
    if isinstance(final, int):
        cast(list[object], current)[final] = value
    else:
        cast(dict[str, object], current)[final] = value
    with pytest.raises((TypeError, ValueError)):
        ShowKitCandidate.from_dict(raw)


def test_typed_nested_candidate_also_requires_exact_integer_values() -> None:
    base = candidate()
    for inner in (
        replace(base.rytm_candidate, seed=float(base.recipe.seed)),
        replace(base.rytm_candidate, estimated_midi_msgs=True),
        replace(
            base.rytm_candidate,
            pad_deltas=(replace(base.rytm_candidate.pad_deltas[0], pad_id=True),),
        ),
    ):
        with pytest.raises(TypeError, match="must be an integer"):
            replace(base, rytm_candidate=inner)


def test_empty_a4_partner_requires_empty_scope_and_full_source_fingerprint() -> None:
    base = candidate()
    empty = replace(base.analog_four_candidate, values=())
    with pytest.raises(ValueError, match="unchanged A4 partner"):
        replace(base, analog_four_candidate=empty)
    locked_recipe = replace(
        base.recipe,
        analog_four_scope=replace(base.recipe.analog_four_scope, locked_ids=(1, 2, 3, 4)),
    )
    with pytest.raises(ValueError, match="exact source fingerprint"):
        replace(base, recipe=locked_recipe, analog_four_candidate=empty)
    preserved = replace(empty, semantic_fingerprint=base.source_a4_fingerprint)
    assert (
        replace(
            base, recipe=locked_recipe, analog_four_candidate=preserved
        ).analog_four_candidate.values
        == ()
    )


@pytest.mark.parametrize(
    "screen",
    (
        "invalid",
        "NaN",
        "sNaN",
        "Infinity",
        "1e999999999",
        "1e-999999999",
        "63.5000000000000000000000000001",
        "63.51",
    ),
)
def test_a4_candidate_screen_is_exact_without_decimal_rounding(screen: str) -> None:
    with localcontext() as context:
        context.prec = 2
        with pytest.raises(ValueError, match="screen_value"):
            AnalogFourCandidateValue(1, "Filter1 Frequency", screen, 16256, 128)
        value = AnalogFourCandidateValue(1, "Filter1 Frequency", "63.50", 16256, 128)
        assert value.encoded_unsigned_8_8 == 16256


@pytest.mark.parametrize("offset", (129, 0, True, 128.0))
def test_a4_candidate_offset_cannot_be_redirected(offset: object) -> None:
    with pytest.raises(ValueError, match="verified Filter1 Frequency track offset"):
        AnalogFourCandidateValue(1, "Filter1 Frequency", "63.50", 16256, offset)


@pytest.mark.parametrize(
    ("device_id", "source_slot", "field"),
    (
        (RYTM_SHOW_KIT_DEVICE_ID, 20, "rytm_hardware_save"),
        (A4_SHOW_KIT_DEVICE_ID, 21, "analog_four_hardware_save"),
    ),
)
def test_source_slot_cannot_be_favorite_at_runtime_or_import(
    tmp_path: Path, device_id: str, source_slot: int, field: str
) -> None:
    harness = _harness(tmp_path)
    first, _ = _generate(harness)
    workspace = harness.workspace
    entry = workspace.mark_favorite(
        harness.bank_id,
        harness.entry_id,
        first.candidate_id,
        workspace.bank(harness.bank_id).revision,
    )
    previous = workspace.bank(harness.bank_id)
    with pytest.raises(ValueError, match="immutable source slot"):
        workspace.attest_saved(
            harness.bank_id,
            harness.entry_id,
            previous.revision,
            device_id=device_id,
            hardware_slot=source_slot,
        )
    assert workspace.bank(harness.bank_id) == previous
    save = HardwareSaveAttestation(
        device_id=device_id,
        hardware_slot=source_slot,
        attested_at=_NOW,
        note="Must not replace the hardware recovery source.",
    )
    with pytest.raises(ValueError, match="immutable source slot"):
        replace(entry, **{field: save})
    payload = previous.to_dict()
    payload["entries"][0][field] = save.to_dict()
    with pytest.raises(ValueError, match="immutable source slot"):
        ShowBank.from_dict(payload)


def test_other_cue_source_slot_is_protected_by_bank_model(tmp_path: Path) -> None:
    harness = _harness(tmp_path)
    workspace = harness.workspace
    first, _ = _generate(harness)
    workspace.mark_favorite(
        harness.bank_id,
        harness.entry_id,
        first.candidate_id,
        workspace.bank(harness.bank_id).revision,
    )
    workspace.attest_saved(
        harness.bank_id,
        harness.entry_id,
        workspace.bank(harness.bank_id).revision,
        device_id=RYTM_SHOW_KIT_DEVICE_ID,
        hardware_slot=64,
    )
    bank = workspace.bank(harness.bank_id)
    with pytest.raises(ValueError, match="another cue's source slot"):
        workspace.adopt_sources(
            bank.bank_id,
            bank.revision,
            captures=harness.captures,
            rytm_fingerprint=harness.rytm.fingerprint,
            analog_four_fingerprint=harness.analog_four.fingerprint,
            rytm_slot=64,
            analog_four_slot=30,
        )
    assert workspace.bank(harness.bank_id) == bank


def test_live_audition_requires_manual_reload_and_consumable_source_capture(tmp_path: Path) -> None:
    harness = _harness(tmp_path)
    first, second = _generate(harness)
    workspace = harness.workspace
    workspace.require_rytm_audition_source("unrelated", {}, manually_reloaded=False)
    workspace.require_rytm_audition_source(
        "unrelated",
        {},
        manually_reloaded=False,
        source_snapshot_id="unrelated-snapshot",
    )
    with pytest.raises(ValueError, match="select this Show Kit candidate again"):
        workspace.require_rytm_audition_source(
            "generic-regen",
            harness.captures,
            manually_reloaded=True,
            source_snapshot_id=workspace.bank(harness.bank_id)
            .entry(harness.entry_id)
            .rytm_source.snapshot_id,
        )
    with pytest.raises(ValueError, match="requires confirmation"):
        workspace.require_rytm_audition_source(
            first.candidate_id,
            harness.captures,
            manually_reloaded=False,
        )
    with pytest.raises(ValueError, match="a current"):
        workspace.require_rytm_audition_source(first.candidate_id, {}, manually_reloaded=True)
    with pytest.raises(ValueError, match="differs"):
        workspace.require_rytm_audition_source(
            first.candidate_id,
            {ANALOG_RYTM_DEVICE_ID: replace(harness.rytm, fingerprint="f" * 16)},
            manually_reloaded=True,
        )
    workspace.require_rytm_audition_source(
        first.candidate_id,
        harness.captures,
        manually_reloaded=True,
    )
    assert workspace.revoke_hardware_evidence() is False
    workspace.record_live_rytm_audition(first.candidate_id)
    workspace.select_candidate(
        harness.bank_id,
        harness.entry_id,
        second.candidate_id,
        workspace.bank(harness.bank_id).revision,
    )
    with pytest.raises(ValueError, match="requires a new current-KIT dump"):
        workspace.require_rytm_audition_source(
            second.candidate_id,
            harness.captures,
            manually_reloaded=True,
        )
    with pytest.raises(ValueError, match="select this Show Kit candidate again"):
        workspace.require_rytm_audition_source(
            first.candidate_id,
            harness.captures,
            manually_reloaded=True,
        )
    fresh_source = replace(harness.rytm, captured_at=_NOW + timedelta(seconds=1))
    workspace.require_rytm_audition_source(
        second.candidate_id,
        {ANALOG_RYTM_DEVICE_ID: fresh_source},
        manually_reloaded=True,
    )
    assert workspace.observe_capture(fresh_source) is False
    bank = workspace.bank(harness.bank_id)
    imported = normalize_catalog_import(bank, clock=harness.clock)
    # Imported selection is normally cleared; a stale external selection still
    # cannot lend catalog evidence to the hardware sender.
    imported = replace(
        imported, entries=(replace(imported.entries[0], selected_candidate_id=second.candidate_id),)
    )
    workspace._banks[harness.bank_id] = imported
    with pytest.raises(ValueError, match="catalog-only"):
        workspace.require_rytm_audition_source(
            second.candidate_id,
            harness.captures,
            manually_reloaded=True,
        )


def _ready_workspace(tmp_path: Path):
    harness = _harness(tmp_path)
    first, _ = _generate(harness)
    workspace = harness.workspace
    workspace.mark_favorite(
        harness.bank_id,
        harness.entry_id,
        first.candidate_id,
        workspace.bank(harness.bank_id).revision,
    )
    for device in (RYTM_SHOW_KIT_DEVICE_ID, A4_SHOW_KIT_DEVICE_ID):
        workspace.attest_saved(
            harness.bank_id,
            harness.entry_id,
            workspace.bank(harness.bank_id).revision,
            device_id=device,
            hardware_slot=64,
        )
    entry = workspace.bank(harness.bank_id).entry(harness.entry_id)
    retained = entry.favorite_candidate.analog_four_candidate.sysex.retained
    a4 = decode_kit_capture_frame(ANALOG_FOUR_DEVICE_ID, harness.store.read_retained(retained))
    captures = {
        ANALOG_RYTM_DEVICE_ID: replace(harness.rytm, captured_at=_NOW + timedelta(minutes=1)),
        ANALOG_FOUR_DEVICE_ID: replace(a4, captured_at=_NOW + timedelta(minutes=1)),
    }
    harness.clock.current = _NOW + timedelta(minutes=2)
    workspace.verify_recaptures(
        harness.bank_id,
        harness.entry_id,
        workspace.bank(harness.bank_id).revision,
        captures=captures,
    )
    captures = {
        device: replace(result, captured_at=_NOW + timedelta(minutes=3))
        for device, result in captures.items()
    }
    harness.clock.current = _NOW + timedelta(minutes=4)
    workspace.run_preflight(
        harness.bank_id,
        harness.entry_id,
        workspace.bank(harness.bank_id).revision,
        captures=captures,
    )
    assert workspace.state_dict()["banks"][0]["readiness"]["show_ready"] is True
    return harness, captures


@pytest.mark.parametrize("device_id", (ANALOG_RYTM_DEVICE_ID, ANALOG_FOUR_DEVICE_ID))
def test_new_mismatching_capture_revokes_current_readiness_but_keeps_history(
    tmp_path: Path,
    device_id: str,
) -> None:
    harness, captures = _ready_workspace(tmp_path)
    workspace = harness.workspace
    previous = workspace.bank(harness.bank_id)
    assert workspace.observe_capture(captures[device_id]) is False
    assert workspace.observe_capture(replace(captures[device_id], fingerprint="f" * 16)) is True
    assert workspace.bank(harness.bank_id) == previous
    projected = workspace.state_dict()["banks"][0]["entries"][0]
    assert projected["status"] == "verified"
    assert projected["readiness"]["show_ready"] is False
    assert projected["show_time_preflight"] is not None


def test_capture_and_loss_revoke_live_markers_without_erasing_catalog(tmp_path: Path) -> None:
    harness = _harness(tmp_path)
    first, _ = _generate(harness)
    workspace = harness.workspace
    workspace.record_live_rytm_audition(first.candidate_id)
    previous = workspace.bank(harness.bank_id)
    assert workspace.observe_capture(harness.analog_four) is False
    assert workspace.observe_capture(harness.rytm) is True
    assert workspace.bank(harness.bank_id) == previous
    assert (
        workspace.state_dict()["banks"][0]["entries"][0]["rytm_audition_status"]
        == "historical_audition_hardware_unknown"
    )
    workspace.record_live_rytm_audition(first.candidate_id)
    previous = workspace.bank(harness.bank_id)
    assert workspace.revoke_hardware_evidence() is True
    assert workspace.revoke_hardware_evidence() is False
    assert workspace.bank(harness.bank_id) == previous
    empty = ShowKitForgeWorkspace(harness.store.__class__(tmp_path / "empty"))
    assert empty.observe_capture(harness.rytm) is False
    empty.create_bank(name="Empty", description="No cue yet", notes=())
    assert empty.observe_capture(harness.analog_four) is False


def test_passive_disconnect_and_teardown_revoke_preflight(tmp_path: Path) -> None:
    harness, _ = _ready_workspace(tmp_path)
    snapshot = harness.workspace.source_snapshot(harness.bank_id, harness.entry_id)
    session = CockpitSession(
        profile_registry=ProfileRegistry(tmp_path / "profiles"),
        history_store=HistoryStore(),
        device=MockDeviceAdapter(initial=snapshot),
        show_kit_forge=harness.workspace,
    )
    broadcasts = []
    watchdog = handlers.build_armed_watchdog(session, broadcasts.append)
    disconnected = ConnectionState(
        phase="searching",
        available_inputs=(),
        available_outputs=(),
        selected_input=None,
        selected_output=None,
        last_error_fingerprint=None,
        changed_at=1.0,
    )
    watchdog(disconnected)
    assert broadcasts[-1]["type"] == "show_bank_changed"
    assert broadcasts[-1]["show_bank"]["banks"][0]["readiness"]["show_ready"] is False
    count = len(broadcasts)
    watchdog(disconnected)
    assert len(broadcasts) == count
    handlers.disarm_session_on_teardown(session)
    handlers.build_armed_watchdog(session)(disconnected)


class _ClosingRecorder(RecordingOut):
    def close(self) -> None:
        pass

    def open_exact(self, _name: str):
        return self


@pytest.mark.parametrize("with_workspace", (True, False))
def test_output_loss_while_another_device_remains_connected_revokes_show_claims(
    tmp_path: Path, with_workspace: bool
) -> None:
    harness = _harness(tmp_path)
    first, _ = _generate(harness)
    workspace = harness.workspace
    workspace.record_live_rytm_audition(first.candidate_id)
    historical = workspace.bank(harness.bank_id)
    session = CockpitSession(
        profile_registry=ProfileRegistry(tmp_path / "profiles"),
        history_store=HistoryStore(),
        device=MockDeviceAdapter(
            initial=workspace.source_snapshot(harness.bank_id, harness.entry_id)
        ),
        show_kit_forge=workspace if with_workspace else None,
    )
    recorder = _ClosingRecorder()
    token = "mock-operator-token"
    seam = ArmedApplySession(opener=recorder, port_name="Mock Rytm", arm_token=token)
    seam.arm(token)
    session.armed_apply = seam
    broadcasts: list[dict[str, object]] = []
    handlers.build_armed_watchdog(session, broadcasts.append)(
        ConnectionState(
            phase="listening",
            available_inputs=("Mock A4",),
            available_outputs=("Mock A4",),
            selected_input="Mock A4",
            selected_output="Mock A4",
            last_error_fingerprint=None,
            changed_at=1.0,
        )
    )
    assert session.armed_apply is None
    assert recorder.sent == []
    show_events = [event for event in broadcasts if event["type"] == "show_bank_changed"]
    assert bool(show_events) is with_workspace
    if with_workspace:
        assert (
            workspace.state_dict()["banks"][0]["entries"][0]["rytm_audition_status"]
            == "historical_audition_hardware_unknown"
        )
        assert workspace.bank(harness.bank_id) == historical


def test_armed_show_send_rejects_stale_source_before_any_output(tmp_path: Path) -> None:
    harness = _harness(tmp_path)
    workspace = harness.workspace
    (candidate,) = workspace.generate_candidates(
        harness.bank_id,
        harness.entry_id,
        workspace.bank(harness.bank_id).revision,
        profile=harness.profile,
        depth_preset="small",
        depth=0.25,
        seed=22,
        candidate_count=1,
        rytm_targets=(1,),
        rytm_locks=(),
        analog_four_targets=(1,),
        analog_four_locks=(),
    )
    source = workspace.source_snapshot(harness.bank_id, harness.entry_id)
    session = CockpitSession(
        profile_registry=ProfileRegistry(tmp_path / "profiles"),
        history_store=HistoryStore(),
        device=MockDeviceAdapter(initial=source),
        show_kit_forge=workspace,
        kit_captures=harness.captures,
        active_profile=harness.profile,
        current_candidate=candidate.rytm_candidate,
        rytm_pad_targets={1},
    )
    session.history_store.initial(source)
    recorder = _ClosingRecorder()
    token = "mock-operator-token"
    seam = ArmedApplySession(opener=recorder, port_name="Mock", arm_token=token)
    seam.arm(token)
    session.armed_apply = seam

    def dispatch(command: dict[str, object]):
        return asyncio.run(
            handlers.handle_command({"request_id": "safety", "command": command}, session)
        )

    assert dispatch({"type": "prepare_send_plan"})["ok"] is True
    plan = session.current_send_plan
    send = {"type": "send", "confirm": True, "send_plan_id": plan.plan_id}
    assert dispatch(send)["ok"] is False
    assert recorder.sent == []
    send["show_bank_source_reloaded"] = True
    assert dispatch({**send, "confirm": False})["ok"] is False
    assert recorder.sent == []
    assert dispatch(send)["ok"] is True
    sent_count = len(recorder.sent)
    assert sent_count > 0
    session.device.adopt_snapshot(source)
    session.current_candidate = candidate.rytm_candidate
    assert dispatch({"type": "prepare_send_plan"})["ok"] is True
    send["send_plan_id"] = session.current_send_plan.plan_id
    assert dispatch(send)["ok"] is False
    assert len(recorder.sent) == sent_count
    session.kit_captures[ANALOG_RYTM_DEVICE_ID] = replace(
        harness.rytm,
        captured_at=_NOW + timedelta(seconds=1),
    )
    assert dispatch(send)["ok"] is True
    assert len(recorder.sent) == 2 * sent_count
    assert dispatch({"type": "disarm"})["ok"] is True
    assert any(event["type"] == "show_bank_changed" for event in session.pending_events)


def test_duplicate_pack_and_io_failure_are_safe_acks_and_session_continues(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    harness = _harness(tmp_path)
    workspace = harness.workspace
    source = workspace.source_snapshot(harness.bank_id, harness.entry_id)
    session = CockpitSession(
        profile_registry=ProfileRegistry(tmp_path / "profiles"),
        history_store=HistoryStore(),
        device=MockDeviceAdapter(initial=source),
        show_kit_forge=workspace,
        show_pack_service=ShowPackService(tmp_path / "packs", store=harness.store),
    )

    def dispatch(command: dict[str, object]):
        return asyncio.run(
            handlers.handle_command({"request_id": "io-safe", "command": command}, session)
        )

    export = {
        "type": "show_bank_export",
        "bank_id": harness.bank_id,
        "expected_revision": workspace.bank(harness.bank_id).revision,
        "artifact_name": "same-pack",
    }
    assert dispatch(export)["ok"] is True
    duplicate = dispatch(export)
    assert duplicate["ok"] is False
    assert duplicate["code"] == ERR_VALIDATION
    assert duplicate["message"] == "command rejected by handler validation"

    def denied(_bank):
        raise PermissionError("private-path-secret")

    monkeypatch.setattr(harness.store, "save", denied)
    failed = dispatch(
        {
            "type": "show_bank_update",
            "bank_id": harness.bank_id,
            "expected_revision": workspace.bank(harness.bank_id).revision,
            "name": "New name",
            "description": "",
            "notes": [],
        }
    )
    assert failed["ok"] is False
    assert failed["code"] == ERR_INTERNAL
    assert "private-path-secret" not in repr(failed)
    assert dispatch({"type": "show_bank_list"})["ok"] is True


@pytest.mark.parametrize("valid_capture,had_marker", ((True, True), (False, True), (False, False)))
def test_new_ws_capture_revokes_old_live_audition_label(
    tmp_path: Path, valid_capture: bool, had_marker: bool
) -> None:
    harness = _harness(tmp_path)
    first, _ = _generate(harness)
    workspace = harness.workspace
    if had_marker:
        workspace.record_live_rytm_audition(first.candidate_id)
    session = CockpitSession(
        profile_registry=ProfileRegistry(tmp_path / "profiles"),
        history_store=HistoryStore(),
        device=MockDeviceAdapter(
            initial=workspace.source_snapshot(harness.bank_id, harness.entry_id)
        ),
        show_kit_forge=workspace,
        kit_capture_service=KitCaptureService(
            _CaptureProvider(harness.rytm.frame if valid_capture else b"\xf0\x00\xf7")
        ),
    )
    result = asyncio.run(
        handlers.handle_command(
            {
                "request_id": "capture",
                "command": {
                    "type": "capture_current_kit",
                    "device_id": ANALOG_RYTM_DEVICE_ID,
                    "input_port": "Mock input",
                },
            },
            session,
        )
    )
    assert result["ok"] is valid_capture
    if not had_marker:
        assert not any(event["type"] == "show_bank_changed" for event in session.pending_events)
        return
    show_event = next(
        event for event in session.pending_events if event["type"] == "show_bank_changed"
    )
    assert (
        show_event["show_bank"]["banks"][0]["entries"][0]["rytm_audition_status"]
        == "historical_audition_hardware_unknown"
    )


def test_candidate_bytes_survive_explicit_keep_and_fail_closed_after_eviction(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    harness = _harness(tmp_path)
    workspace = harness.workspace
    first, second = _generate(harness)
    workspace._volatile_frames.clear()
    bank = workspace.bank(harness.bank_id)
    with pytest.raises(ValueError, match="no longer in memory"):
        workspace.retain_capture(
            harness.bank_id,
            harness.entry_id,
            bank.revision,
            capture_kind="candidate",
            device_id=A4_SHOW_KIT_DEVICE_ID,
            current_captures={},
        )
    # Regeneration repairs only the bounded byte cache, preserving deterministic
    # candidate identities and the prior revision even when no new candidate exists.
    with pytest.raises(ValueError, match="already exists"):
        _generate(harness)
    workspace.mark_favorite(
        harness.bank_id,
        harness.entry_id,
        first.candidate_id,
        bank.revision,
    )
    revision = workspace.bank(harness.bank_id).revision
    workspace.retain_capture(
        harness.bank_id,
        harness.entry_id,
        revision,
        capture_kind="candidate",
        device_id=A4_SHOW_KIT_DEVICE_ID,
        current_captures={},
    )
    assert workspace.bank(harness.bank_id).revision == revision
    workspace._cache_frame("rytm-cache", harness.rytm.frame)
    with monkeypatch.context() as patch:
        patch.setattr(workspace_module, "MAX_VOLATILE_FRAMES", 1)
        workspace._cache_frame("newest", harness.analog_four.frame)
        assert tuple(workspace._volatile_frames) == ("newest",)
    bank = workspace.bank(harness.bank_id)
    source_id = bank.entry(harness.entry_id).rytm_source.sysex.artifact_id
    with pytest.raises(ValueError, match="conflicting exact bytes"):
        workspace._retain_frames(bank, ((source_id, harness.rytm.frame), (source_id, b"different")))
    assert workspace.bank(harness.bank_id) == bank
    workspace.retain_capture(
        harness.bank_id,
        harness.entry_id,
        bank.revision,
        capture_kind="source",
        device_id=RYTM_SHOW_KIT_DEVICE_ID,
        current_captures={},
    )
    imported = normalize_catalog_import(workspace.bank(harness.bank_id), clock=harness.clock)
    workspace._banks[harness.bank_id] = imported
    assert workspace.record_live_rytm_audition(second.candidate_id) is None
    workspace._banks[harness.bank_id] = bank
    workspace._active_entry_ids.clear()
    assert workspace.record_live_rytm_audition(first.candidate_id) is None


def test_preflight_rechecks_persisted_evidence_and_requires_recaptures(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    harness = _harness(tmp_path)
    workspace = harness.workspace
    bank = workspace.bank(harness.bank_id)
    with pytest.raises(ValueError, match="verified paired recaptures"):
        workspace.run_preflight(
            harness.bank_id,
            harness.entry_id,
            bank.revision,
            captures=harness.captures,
        )
    monkeypatch.setattr(
        harness.store, "load", lambda *_args, **_kwargs: replace(bank, name="Changed")
    )
    with pytest.raises(ValueError, match="persisted show-bank evidence changed"):
        workspace.run_preflight(
            harness.bank_id,
            harness.entry_id,
            bank.revision,
            captures=harness.captures,
        )
    assert workspace.bank(harness.bank_id) == bank


def test_a4_mismatch_is_reported_and_semantic_failure_cannot_publish_partial_pair(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    harness, captures = _ready_workspace(tmp_path)
    workspace = harness.workspace
    bank = workspace.bank(harness.bank_id)
    with monkeypatch.context() as patch:
        patch.setattr(
            workspace_module, "analog_four_capture_semantic_fingerprint", lambda *_args: None
        )
        with pytest.raises(AssertionError, match="lost its promoted semantic projection"):
            workspace.verify_recaptures(
                harness.bank_id,
                harness.entry_id,
                bank.revision,
                captures=captures,
            )
    assert workspace.bank(harness.bank_id) == bank
    assert harness.store.latest_revision(harness.bank_id) == bank.revision
    workspace.retain_capture(
        harness.bank_id,
        harness.entry_id,
        bank.revision,
        capture_kind="favorite",
        device_id=RYTM_SHOW_KIT_DEVICE_ID,
        current_captures={},
    )
    fresh = {
        device: replace(result, captured_at=_NOW + timedelta(minutes=5))
        for device, result in captures.items()
    }
    fresh[ANALOG_FOUR_DEVICE_ID] = replace(fresh[ANALOG_FOUR_DEVICE_ID], fingerprint="f" * 16)
    harness.clock.current = _NOW + timedelta(minutes=6)
    workspace.run_preflight(
        harness.bank_id,
        harness.entry_id,
        bank.revision,
        captures=fresh,
    )
    projected = workspace.state_dict()["banks"][0]["entries"][0]
    assert projected["readiness"]["show_ready"] is False
    assert "a4_current_kit_mismatch" in projected["readiness"]["blocked_reasons"]
