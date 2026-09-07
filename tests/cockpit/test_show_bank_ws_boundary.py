"""Mock-only integration coverage for Show Kit Forge WebSocket commands."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import cast

import pytest
from cockpit.conftest import MutableClock as _MutableClock
from cockpit.conftest import capture_fixed_frame as _capture

from conftest import (
    analog_four_saved_kit_frame,
    elektron_syx_message,
    rytm_real_layout_kit_payload,
)
from rytm_randomizer.cockpit.capture import (
    ANALOG_FOUR_DEVICE_ID,
    ANALOG_RYTM_DEVICE_ID,
    KitCaptureResult,
    cockpit_snapshot_from_rytm_capture,
    decode_kit_capture_frame,
)
from rytm_randomizer.cockpit.device import MockDeviceAdapter
from rytm_randomizer.cockpit.history import HistoryStore
from rytm_randomizer.cockpit.profiles import ProfileRegistry
from rytm_randomizer.cockpit.show_bank.export import ShowPackService
from rytm_randomizer.cockpit.show_bank.store import ShowBankStore
from rytm_randomizer.cockpit.show_bank.workspace import ShowKitForgeWorkspace
from rytm_randomizer.cockpit.ws import show_bank_handlers
from rytm_randomizer.cockpit.ws.handlers import handle_command
from rytm_randomizer.cockpit.ws.session import CockpitSession

pytestmark = pytest.mark.fast

_NOW = datetime(2026, 9, 4, 17, 0, tzinfo=timezone.utc)


def test_show_bank_handler_registry_is_immutable() -> None:
    registry = show_bank_handlers.SHOW_BANK_HANDLERS
    with pytest.raises(TypeError):
        registry["show_bank_list"] = registry["show_bank_list"]  # type: ignore[index]


def test_show_bank_wire_fields_reject_ambiguous_optional_values() -> None:
    assert show_bank_handlers._optional_integer({}, "energy_level") is None
    assert show_bank_handlers._optional_integer({"energy_level": 7}, "energy_level") == 7
    with pytest.raises(ValueError, match="integer or null"):
        show_bank_handlers._optional_integer({"energy_level": True}, "energy_level")
    with pytest.raises(ValueError, match="boolean"):
        show_bank_handlers._optional_boolean(
            {"replace_existing": "true"}, "replace_existing", default=False
        )
    with pytest.raises(ValueError, match="integer list"):
        show_bank_handlers._integer_list({"rytm_targets": "1,2"}, "rytm_targets")


@dataclass
class _Boundary:
    session: CockpitSession
    workspace: ShowKitForgeWorkspace
    store: ShowBankStore
    pack_root: Path
    rytm: KitCaptureResult
    analog_four: KitCaptureResult
    clock: _MutableClock


def _boundary(tmp_path: Path, *, suffix: str = "source") -> _Boundary:
    rytm = replace(
        _capture(
            ANALOG_RYTM_DEVICE_ID,
            elektron_syx_message(rytm_real_layout_kit_payload(b"WS BOUNDARY")),
        ),
        captured_at=_NOW - timedelta(minutes=2),
    )
    analog_four = replace(
        _capture(
            ANALOG_FOUR_DEVICE_ID,
            analog_four_saved_kit_frame(name=b"WS BOUNDARY"),
        ),
        captured_at=_NOW - timedelta(minutes=2),
    )
    clock = _MutableClock(_NOW)
    store = ShowBankStore(tmp_path / f"banks-{suffix}", clock=clock)
    ids = iter((f"bank-{suffix}", f"cue-{suffix}", f"cue-{suffix}-copy"))
    workspace = ShowKitForgeWorkspace(
        store,
        clock=clock,
        id_factory=lambda _prefix: next(ids),
    )
    snapshot = cockpit_snapshot_from_rytm_capture(rytm)
    history = HistoryStore()
    history.initial(snapshot)
    pack_root = tmp_path / "packs"
    session = CockpitSession(
        profile_registry=ProfileRegistry(tmp_path / f"profiles-{suffix}"),
        history_store=history,
        device=MockDeviceAdapter(initial=snapshot),
        kit_captures={
            ANALOG_RYTM_DEVICE_ID: rytm,
            ANALOG_FOUR_DEVICE_ID: analog_four,
        },
        show_kit_forge=workspace,
        show_pack_service=ShowPackService(pack_root, store=store),
    )
    return _Boundary(
        session=session,
        workspace=workspace,
        store=store,
        pack_root=pack_root,
        rytm=rytm,
        analog_four=analog_four,
        clock=clock,
    )


def _command(
    session: CockpitSession,
    command_type: str,
    **body: object,
) -> tuple[dict[str, object], list[dict[str, object]]]:
    ack = asyncio.run(
        handle_command(
            {
                "request_id": f"req-{command_type}",
                "command": {"type": command_type, **body},
            },
            session,
        )
    )
    events = list(session.pending_events)
    session.clear_pending_events()
    return ack, events


def _revision(boundary: _Boundary) -> int:
    return boundary.workspace.banks[0].revision


@pytest.mark.parametrize("current_origin", ["removed", "derived", "other", "none"])
def test_removing_a_cue_revokes_only_its_prepared_candidate(
    tmp_path: Path, current_origin: str
) -> None:
    boundary = _boundary(tmp_path)
    workspace = boundary.workspace
    session = boundary.session
    bank = workspace.create_bank(name="Removal", description="", notes=())
    entry = workspace.adopt_sources(
        bank.bank_id,
        bank.revision,
        captures=session.kit_captures,
        rytm_fingerprint=boundary.rytm.fingerprint,
        analog_four_fingerprint=boundary.analog_four.fingerprint,
        rytm_slot=20,
        analog_four_slot=21,
    )
    profile = session.profile_registry.list_profiles()[0]
    generated = workspace.generate_candidates(
        bank.bank_id,
        entry.entry_id,
        _revision(boundary),
        profile=profile,
        depth_preset="small",
        depth=0.25,
        seed=91,
        candidate_count=1,
        rytm_targets=(1,),
        rytm_locks=(),
        analog_four_targets=(1,),
        analog_four_locks=(),
    )
    ack, _ = _command(
        session,
        "show_bank_select_candidate",
        bank_id=bank.bank_id,
        entry_id=entry.entry_id,
        expected_revision=_revision(boundary),
        candidate_id=generated[0].candidate_id,
    )
    assert ack["ok"] is True
    ack, _ = _command(session, "prepare_send_plan")
    assert ack["ok"] is True
    assert session.current_send_plan is not None
    old_plan = session.current_send_plan
    if current_origin == "none":
        session.current_candidate = None
    elif current_origin == "derived":
        session.current_candidate = replace(generated[0].rytm_candidate, candidate_id="other")
    elif current_origin == "other":
        session.current_candidate = replace(
            generated[0].rytm_candidate, candidate_id="other", source_snapshot_id="unrelated-source"
        )
    ack, events = _command(
        session,
        "show_bank_remove_entry",
        bank_id=bank.bank_id,
        entry_id=entry.entry_id,
        expected_revision=_revision(boundary),
    )
    assert ack["ok"] is True
    if current_origin in ("removed", "derived"):
        assert session.current_candidate is None
        assert session.current_send_plan is None
        assert session.preview_on is False
        assert any(event == {"type": "send_plan_changed", "send_plan": None} for event in events)
        refused, _ = _command(session, "send", confirm=True, send_plan_id=old_plan.plan_id)
        assert refused["ok"] is False
    else:
        assert session.current_send_plan is old_plan


def test_show_bank_websocket_complete_lifecycle_pack_and_recovery(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    boundary = _boundary(tmp_path)
    session = boundary.session

    ack, events = _command(session, "show_bank_list")
    assert ack["ok"] is True
    assert events[-1]["type"] == "show_bank_changed"

    ack, _ = _command(
        session,
        "show_bank_create",
        name="Boundary Show",
        description="Mock lifecycle",
        notes=["OXI metadata only"],
    )
    assert ack["ok"] is True
    bank_id = cast(str, ack["show_bank_id"])

    ack, _ = _command(session, "show_bank_select", bank_id=bank_id)
    assert ack["ok"] is True
    ack, _ = _command(
        session,
        "show_bank_update",
        bank_id=bank_id,
        expected_revision=_revision(boundary),
        name="Boundary Show Updated",
        description="All local",
        notes=["No hardware output"],
    )
    assert ack["ok"] is True

    ack, events = _command(
        session,
        "show_bank_adopt_sources",
        bank_id=bank_id,
        expected_revision=_revision(boundary),
        entry_id="cue-explicit",
        rytm_fingerprint=boundary.rytm.fingerprint,
        a4_fingerprint=boundary.analog_four.fingerprint,
        rytm_slot=20,
        a4_slot=21,
    )
    assert ack["ok"] is True
    entry_id = cast(str, ack["show_bank_entry_id"])
    assert entry_id == "cue-explicit"
    assert {event["type"] for event in events} >= {
        "snapshot_changed",
        "history_updated",
        "show_bank_changed",
    }

    profile = session.profile_registry.list_profiles()[0]
    ack, _ = _command(
        session,
        "show_bank_generate_candidates",
        bank_id=bank_id,
        entry_id=entry_id,
        expected_revision=_revision(boundary),
        profile_id=profile.profile_id,
        depth_preset="small",
        depth=0.25,
        seed=91,
        candidate_count=2,
        rytm_targets=[],
        rytm_locks=list(range(1, 13)),
        a4_targets=[1],
        a4_locks=[],
    )
    candidate_ids = cast(list[str], ack["candidate_ids"])
    assert len(candidate_ids) == 2
    assert session.current_candidate is not None
    with monkeypatch.context() as scoped:
        scoped.setattr(session.profile_registry, "get", lambda _profile_id: None)
        with pytest.raises(ValueError, match="profile is no longer available"):
            show_bank_handlers._sync_selected_candidate(
                session,
                boundary.workspace,
                bank_id,
                entry_id,
            )

    ack, _ = _command(
        session,
        "show_bank_select_candidate",
        bank_id=bank_id,
        entry_id=entry_id,
        candidate_id=candidate_ids[1],
        expected_revision=_revision(boundary),
    )
    assert ack["ok"] is True
    ack, _ = _command(
        session,
        "show_bank_mark_favorite",
        bank_id=bank_id,
        entry_id=entry_id,
        candidate_id=candidate_ids[0],
        expected_revision=_revision(boundary),
    )
    assert ack["ok"] is True

    for device_id in ("analog_rytm_mk2", "analog_four_mk2"):
        ack, _ = _command(
            session,
            "show_bank_attest_hardware_saved",
            bank_id=bank_id,
            entry_id=entry_id,
            expected_revision=_revision(boundary),
            device_id=device_id,
            slot=64,
        )
        assert ack["ok"] is True

    entry = boundary.workspace.bank(bank_id).entry(entry_id)
    favorite = entry.favorite_candidate
    assert favorite is not None
    retained = favorite.analog_four_candidate.sysex.retained
    assert retained is not None
    a4_recapture = decode_kit_capture_frame(
        ANALOG_FOUR_DEVICE_ID,
        boundary.store.read_retained(retained),
    )
    recapture_time = _NOW + timedelta(minutes=1)
    boundary.clock.current = _NOW + timedelta(minutes=2)
    session.kit_captures = {
        ANALOG_RYTM_DEVICE_ID: replace(
            boundary.rytm,
            captured_at=recapture_time,
        ),
        ANALOG_FOUR_DEVICE_ID: replace(
            a4_recapture,
            captured_at=recapture_time,
        ),
    }
    ack, _ = _command(
        session,
        "show_bank_verify_recapture",
        bank_id=bank_id,
        entry_id=entry_id,
        expected_revision=_revision(boundary),
    )
    assert ack["ok"] is True

    preflight_time = _NOW + timedelta(minutes=3)
    boundary.clock.current = _NOW + timedelta(minutes=4)
    session.kit_captures = {
        device_id: replace(result, captured_at=preflight_time)
        for device_id, result in session.kit_captures.items()
    }
    session.kit_captures[ANALOG_FOUR_DEVICE_ID] = replace(
        session.kit_captures[ANALOG_FOUR_DEVICE_ID],
        fingerprint="0" * 16,
    )
    ack, _ = _command(
        session,
        "show_bank_run_preflight",
        bank_id=bank_id,
        entry_id=entry_id,
        expected_revision=_revision(boundary),
    )
    assert ack["ok"] is True
    assert ack["show_ready"] is False
    repeated_time = _NOW + timedelta(minutes=5)
    boundary.clock.current = _NOW + timedelta(minutes=6)
    session.kit_captures = {
        ANALOG_RYTM_DEVICE_ID: replace(
            boundary.rytm,
            captured_at=repeated_time,
        ),
        ANALOG_FOUR_DEVICE_ID: replace(
            a4_recapture,
            captured_at=repeated_time,
        ),
    }
    ack, _ = _command(
        session,
        "show_bank_run_preflight",
        bank_id=bank_id,
        entry_id=entry_id,
        expected_revision=_revision(boundary),
    )
    assert ack["show_ready"] is True

    ack, _ = _command(
        session,
        "show_bank_update_entry",
        bank_id=bank_id,
        entry_id=entry_id,
        expected_revision=_revision(boundary),
        name="Opening",
        description="Exact recovery",
        oxi={
            "project": "Warehouse",
            "pattern": "A01",
            "chapter": "Opening",
            "direct_oxi_control": False,
        },
        audition_notes=["Dry"],
        energy_level=5,
        energy_notes=["High"],
        transition_notes=["Cut"],
        recovery_notes=["Load source slots"],
    )
    assert ack["ok"] is True

    for capture_kind, device_id in (
        ("source", "analog_rytm_mk2"),
        ("favorite", "analog_four_mk2"),
    ):
        ack, _ = _command(
            session,
            "show_bank_retain_capture",
            bank_id=bank_id,
            entry_id=entry_id,
            expected_revision=_revision(boundary),
            capture_kind=capture_kind,
            device_id=device_id,
        )
        assert ack["ok"] is True

    ack, _ = _command(
        session,
        "show_bank_duplicate_entry",
        bank_id=bank_id,
        entry_id=entry_id,
        expected_revision=_revision(boundary),
    )
    copied_id = cast(str, ack["show_bank_entry_id"])
    ack, _ = _command(
        session,
        "show_bank_reorder_entries",
        bank_id=bank_id,
        expected_revision=_revision(boundary),
        entry_ids=[copied_id, entry_id],
    )
    assert ack["ok"] is True
    ack, _ = _command(
        session,
        "show_bank_remove_entry",
        bank_id=bank_id,
        entry_id=copied_id,
        expected_revision=_revision(boundary),
    )
    assert ack["ok"] is True

    ack, _ = _command(
        session,
        "show_bank_export",
        bank_id=bank_id,
        expected_revision=_revision(boundary),
        artifact_name="boundary-pack",
    )
    export = cast(dict[str, object], ack["show_pack_export"])
    assert export["directory_name"] == "boundary-pack.show-pack"
    assert "path" not in export

    ack, events = _command(
        session,
        "show_bank_return_source",
        bank_id=bank_id,
        entry_id=entry_id,
        expected_revision=_revision(boundary),
    )
    assert ack["ok"] is True
    assert ack["hardware_changed"] is False
    assert ack["source_slots"] == {"rytm": 20, "analog_four": 21}
    assert ack["instruction"] == (
        "Cockpit reset its in-memory audition only; no instrument changed. "
        "Manually load the immutable Rytm and Analog Four source slots to "
        "return hardware."
    )
    assert events[-1]["type"] == "show_bank_changed"

    destination = _boundary(tmp_path, suffix="destination")
    destination.session.show_pack_service = ShowPackService(
        boundary.pack_root,
        store=destination.store,
    )
    ack, events = _command(
        destination.session,
        "show_bank_import",
        pack_name="boundary-pack",
    )
    imported = cast(dict[str, object], ack["show_pack_import"])
    assert imported["bank_id"] == bank_id
    assert destination.workspace.bank(bank_id).entry(entry_id).status == "verified"
    assert events[-1]["type"] == "show_bank_changed"

    duplicate, duplicate_events = _command(
        destination.session,
        "show_bank_import",
        pack_name="boundary-pack",
    )
    assert duplicate["ok"] is False
    assert duplicate["code"] == "validation_error"
    assert duplicate_events == []


def test_show_bank_websocket_validation_is_strict_and_fail_closed(
    tmp_path: Path,
) -> None:
    boundary = _boundary(tmp_path)
    session = boundary.session
    bare = replace(session, show_kit_forge=None, show_pack_service=None)

    ack, events = _command(bare, "show_bank_list")
    assert ack["ok"] is False
    assert ack["code"] == "validation_error"
    assert events == []

    _command(
        session,
        "show_bank_create",
        name="Validation",
        description="",
        notes=[],
    )
    bank_id = boundary.workspace.banks[0].bank_id
    bad_commands: tuple[tuple[str, dict[str, object]], ...] = (
        (
            "show_bank_create",
            {"name": 1, "description": "", "notes": []},
        ),
        (
            "show_bank_create",
            {"name": "  ", "description": "", "notes": []},
        ),
        (
            "show_bank_create",
            {"name": "Fine", "description": "", "notes": "bad"},
        ),
        (
            "show_bank_create",
            {"name": "Fine", "description": "", "notes": [1]},
        ),
        (
            "show_bank_update",
            {
                "bank_id": bank_id,
                "expected_revision": True,
                "name": "Fine",
                "description": "",
                "notes": [],
            },
        ),
        (
            "show_bank_adopt_sources",
            {
                "bank_id": bank_id,
                "expected_revision": _revision(boundary),
                "entry_id": 4,
                "rytm_fingerprint": boundary.rytm.fingerprint,
                "a4_fingerprint": boundary.analog_four.fingerprint,
                "rytm_slot": 1,
                "a4_slot": 1,
            },
        ),
        (
            "show_bank_generate_candidates",
            {"profile_id": "profile-that-does-not-exist"},
        ),
        (
            "show_bank_generate_candidates",
            {
                "bank_id": bank_id,
                "entry_id": "missing",
                "expected_revision": _revision(boundary),
                "profile_id": session.profile_registry.list_profiles()[0].profile_id,
                "depth_preset": "small",
                "depth": True,
                "seed": 1,
                "candidate_count": 1,
                "rytm_targets": [],
                "rytm_locks": [],
                "a4_targets": [1],
                "a4_locks": [],
            },
        ),
        (
            "show_bank_generate_candidates",
            {
                "bank_id": bank_id,
                "entry_id": "missing",
                "expected_revision": _revision(boundary),
                "profile_id": session.profile_registry.list_profiles()[0].profile_id,
                "depth_preset": "small",
                "depth": 0.25,
                "seed": 1,
                "candidate_count": 1,
                "rytm_targets": [True],
                "rytm_locks": [],
                "a4_targets": [1],
                "a4_locks": [],
            },
        ),
        (
            "show_bank_update_entry",
            {
                "bank_id": bank_id,
                "entry_id": "missing",
                "expected_revision": _revision(boundary),
                "name": "Fine",
                "description": "",
                "oxi": [],
                "audition_notes": [],
                "energy_notes": [],
                "transition_notes": [],
                "recovery_notes": [],
            },
        ),
        (
            "show_bank_update_entry",
            {
                "bank_id": bank_id,
                "entry_id": "missing",
                "expected_revision": _revision(boundary),
                "name": "Fine",
                "description": "",
                "oxi": {
                    "project": "",
                    "pattern": "",
                    "chapter": "",
                    "direct_oxi_control": True,
                },
                "audition_notes": [],
                "energy_notes": [],
                "transition_notes": [],
                "recovery_notes": [],
            },
        ),
        (
            "show_bank_retain_capture",
            {
                "bank_id": bank_id,
                "entry_id": "missing",
                "expected_revision": _revision(boundary),
                "capture_kind": "other",
                "device_id": "analog_rytm_mk2",
            },
        ),
    )
    for command_type, body in bad_commands:
        ack, events = _command(session, command_type, **body)
        assert ack["ok"] is False, (command_type, ack)
        assert ack["code"] == "validation_error"
        assert events == []

    session.show_pack_service = None
    for command_type, body in (
        (
            "show_bank_export",
            {
                "bank_id": bank_id,
                "expected_revision": _revision(boundary),
                "artifact_name": "pack",
            },
        ),
        ("show_bank_import", {"pack_name": "pack"}),
    ):
        ack, events = _command(session, command_type, **body)
        assert ack["ok"] is False
        assert ack["code"] == "validation_error"
        assert events == []


def test_show_bank_history_sync_covers_initial_append_load_and_mismatch(
    tmp_path: Path,
) -> None:
    boundary = _boundary(tmp_path)
    snapshot = boundary.session.device.capture_snapshot()

    empty_history = HistoryStore()
    initial_session = replace(boundary.session, history_store=empty_history)
    show_bank_handlers._ensure_history_snapshot(initial_session, snapshot.snapshot_id)
    assert empty_history.current.current_id == snapshot.snapshot_id

    different = replace(snapshot, snapshot_id="snapshot-different")
    boundary.session.device.adopt_snapshot(different)
    show_bank_handlers._ensure_history_snapshot(
        boundary.session,
        different.snapshot_id,
    )
    assert boundary.session.history_store.current.current_id == different.snapshot_id
    show_bank_handlers._ensure_history_snapshot(
        boundary.session,
        snapshot.snapshot_id,
    )
    assert boundary.session.history_store.current.current_id == snapshot.snapshot_id

    with pytest.raises(ValueError, match="did not adopt"):
        show_bank_handlers._ensure_history_snapshot(boundary.session, "snapshot-unknown")
