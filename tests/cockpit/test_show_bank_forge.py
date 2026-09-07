"""Pure paired Show Kit Forge generation and semantic-compare tests."""

from __future__ import annotations

import asyncio
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import localcontext
from functools import partial
from pathlib import Path
from typing import cast

import pytest
from cockpit.conftest import MutableClock as _MutableClock
from cockpit.conftest import capture_fixed_frame

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
from rytm_randomizer.cockpit.data import Snapshot
from rytm_randomizer.cockpit.data.show_bank import (
    A4_SHOW_KIT_DEVICE_ID,
    RYTM_SHOW_KIT_DEVICE_ID,
    ShowBankEntry,
    ShowKitRecipe,
    ShowKitScope,
)
from rytm_randomizer.cockpit.device import MockDeviceAdapter
from rytm_randomizer.cockpit.history import HistoryStore
from rytm_randomizer.cockpit.profiles import ProfileRegistry
from rytm_randomizer.cockpit.show_bank.export import ShowPackService
from rytm_randomizer.cockpit.show_bank.forge import (
    analog_four_capture_semantic_fingerprint,
    analog_four_recapture_semantically_matches,
    build_source_entry,
    capture_reference,
    forge_candidate_pair,
)
from rytm_randomizer.cockpit.show_bank.store import ShowBankStore
from rytm_randomizer.cockpit.show_bank.workspace import ShowKitForgeWorkspace
from rytm_randomizer.cockpit.ws.handlers import handle_command
from rytm_randomizer.cockpit.ws.session import CockpitSession
from rytm_randomizer.devices.strategies.analog_four_filter1_frequency_candidate import (
    AnalogFourFilter1FrequencyCandidateMutation,
    render_analog_four_filter1_frequency_candidate,
)

pytestmark = pytest.mark.fast
_NOW = datetime(2026, 9, 4, 12, 0, tzinfo=timezone.utc)


_capture = partial(capture_fixed_frame, port_name="Mock Input")


def _sources() -> tuple[KitCaptureResult, KitCaptureResult, Snapshot, ShowBankEntry]:
    rytm = replace(
        _capture(
            ANALOG_RYTM_DEVICE_ID,
            elektron_syx_message(rytm_real_layout_kit_payload(b"SHOW RYTM")),
        ),
        captured_at=_NOW - timedelta(minutes=2),
    )
    analog_four = replace(
        _capture(
            ANALOG_FOUR_DEVICE_ID,
            analog_four_saved_kit_frame(name=b"SHOW A4"),
        ),
        captured_at=_NOW - timedelta(minutes=2),
    )
    snapshot = cockpit_snapshot_from_rytm_capture(rytm)
    entry = build_source_entry(
        entry_id="entry-001",
        cue_index=1,
        name="Opening pressure",
        description="Paired source anchor",
        rytm_capture=rytm,
        analog_four_capture=analog_four,
        rytm_slot=20,
        analog_four_slot=20,
        rytm_snapshot_id=snapshot.snapshot_id,
        now=_NOW,
    )
    return rytm, analog_four, snapshot, entry


def test_source_entry_retains_hashes_without_pretending_files_exist() -> None:
    rytm, analog_four, _snapshot, entry = _sources()

    assert entry.status == "source"
    assert entry.rytm_source.hardware_slot == 20
    assert entry.analog_four_source.hardware_slot == 20
    assert entry.rytm_source.sysex.frame_sha256 != entry.rytm_source.fingerprint
    assert entry.rytm_source.sysex.retained is None
    assert entry.analog_four_source.sysex.retained is None
    assert entry.rytm_source.sysex.frame_bytes == len(rytm.frame)
    assert entry.analog_four_source.sysex.frame_bytes == len(analog_four.frame)


def test_capture_reference_rejects_an_unsupported_device_in_a_typed_capture() -> None:
    rytm, _analog_four, _snapshot, _entry = _sources()
    unsupported = replace(rytm, device_id="unsupported")

    with pytest.raises(ValueError, match="unsupported show-bank source device"):
        capture_reference(unsupported, hardware_slot=20, snapshot_id="source-snapshot")


@pytest.mark.parametrize(
    "flags",
    ({"round_trip_verified": False}, {"input_only": False}, {"sent_midi": True}),
)
def test_capture_reference_requires_verified_input_only_evidence(flags: dict[str, bool]) -> None:
    rytm, _analog_four, _snapshot, _entry = _sources()
    invalid = replace(rytm, **flags)

    with pytest.raises(ValueError, match="codec round-trip verified and input-only"):
        capture_reference(invalid, hardware_slot=20, snapshot_id="source-snapshot")


def test_forge_pair_is_deterministic_scoped_and_a4_offline_only(tmp_path: Path) -> None:
    _rytm, analog_four, snapshot, entry = _sources()
    profile = ProfileRegistry(tmp_path).list_profiles()[0]
    recipe = ShowKitRecipe(
        profile_id=profile.profile_id,
        depth_preset="medium",
        depth=0.5,
        seed=1234,
        rytm_scope=ShowKitScope(
            device_id=RYTM_SHOW_KIT_DEVICE_ID,
            target_ids=(1, 2),
            locked_ids=(2,),
        ),
        analog_four_scope=ShowKitScope(
            device_id=A4_SHOW_KIT_DEVICE_ID,
            target_ids=(1, 2),
            locked_ids=(2,),
        ),
    )

    first = forge_candidate_pair(
        entry=entry,
        rytm_source_snapshot=snapshot,
        analog_four_source_frame=analog_four.frame,
        profile=profile,
        recipe=recipe,
        now=_NOW,
    )
    second = forge_candidate_pair(
        entry=entry,
        rytm_source_snapshot=snapshot,
        analog_four_source_frame=analog_four.frame,
        profile=profile,
        recipe=recipe,
        now=_NOW,
    )

    assert first.candidate.candidate_id == second.candidate.candidate_id
    assert first.analog_four_frame == second.analog_four_frame
    assert {delta.pad_id for delta in first.candidate.rytm_candidate.pad_deltas} == {1}
    assert {value.track_id for value in first.candidate.analog_four_candidate.values} == {1}
    assert first.candidate.analog_four_candidate.evidence_status == (
        "offline-captured-kit-mutation-validated"
    )
    assert first.candidate.evidence[0].status == "pending-physical-outbound-validation"


def test_forge_and_recapture_preserve_exact_a4_values_in_low_decimal_precision(
    tmp_path: Path,
) -> None:
    _rytm, analog_four, snapshot, entry = _sources()
    profile = ProfileRegistry(tmp_path).list_profiles()[0]
    recipe = ShowKitRecipe(
        profile_id=profile.profile_id,
        depth_preset="medium",
        depth=0.5,
        seed=1234,
        rytm_scope=ShowKitScope(device_id=RYTM_SHOW_KIT_DEVICE_ID, target_ids=(1,)),
        analog_four_scope=ShowKitScope(device_id=A4_SHOW_KIT_DEVICE_ID),
    )
    ordinary = forge_candidate_pair(
        entry=entry,
        rytm_source_snapshot=snapshot,
        analog_four_source_frame=analog_four.frame,
        profile=profile,
        recipe=recipe,
        now=_NOW,
    )
    expected = ordinary.candidate.analog_four_candidate
    assert any(value.encoded_unsigned_8_8 % 256 for value in expected.values)

    with localcontext() as context:
        context.prec = 2
        low_precision = forge_candidate_pair(
            entry=entry,
            rytm_source_snapshot=snapshot,
            analog_four_source_frame=analog_four.frame,
            profile=profile,
            recipe=recipe,
            now=_NOW,
        )
        recapture = _capture(ANALOG_FOUR_DEVICE_ID, ordinary.analog_four_frame)
        assert low_precision == ordinary
        assert analog_four_capture_semantic_fingerprint(recapture, expected) == (
            expected.semantic_fingerprint
        )
        assert analog_four_recapture_semantically_matches(recapture, expected)


def test_a4_recapture_comparison_reads_only_promoted_filter1_values(
    tmp_path: Path,
) -> None:
    source = analog_four_saved_kit_frame(name=b"SHOW A4")
    rendered = render_analog_four_filter1_frequency_candidate(
        source,
        (AnalogFourFilter1FrequencyCandidateMutation(track=3, screen_value="48.5"),),
    )
    candidate_capture = _capture(ANALOG_FOUR_DEVICE_ID, rendered.framed_sysex)
    source_capture = _capture(ANALOG_FOUR_DEVICE_ID, source)
    _rytm, analog_four, snapshot, entry = _sources()
    profile = ProfileRegistry(tmp_path).list_profiles()[0]
    recipe = ShowKitRecipe(
        profile_id=profile.profile_id,
        depth_preset="custom",
        depth=0.5,
        seed=8,
        rytm_scope=ShowKitScope(device_id=RYTM_SHOW_KIT_DEVICE_ID),
        analog_four_scope=ShowKitScope(
            device_id=A4_SHOW_KIT_DEVICE_ID,
            target_ids=(3,),
        ),
    )
    forged = forge_candidate_pair(
        entry=entry,
        rytm_source_snapshot=snapshot,
        analog_four_source_frame=analog_four.frame,
        profile=profile,
        recipe=recipe,
        now=_NOW,
    )
    expected = forged.candidate.analog_four_candidate
    expected_value = expected.values[0]
    comparison_render = render_analog_four_filter1_frequency_candidate(
        source,
        (
            AnalogFourFilter1FrequencyCandidateMutation(
                track=expected_value.track_id,
                screen_value=expected_value.screen_value,
            ),
        ),
    )
    matching_capture = _capture(ANALOG_FOUR_DEVICE_ID, comparison_render.framed_sysex)

    assert analog_four_recapture_semantically_matches(matching_capture, expected) is True
    assert analog_four_recapture_semantically_matches(source_capture, expected) is False
    assert analog_four_recapture_semantically_matches(candidate_capture, expected) is False


def test_capture_reference_and_forge_fail_closed_on_wrong_authority(tmp_path: Path) -> None:
    rytm, analog_four, snapshot, entry = _sources()
    profile = ProfileRegistry(tmp_path).list_profiles()[0]
    recipe = ShowKitRecipe(
        profile_id=profile.profile_id,
        depth_preset="small",
        depth=0.25,
        seed=1,
        rytm_scope=ShowKitScope(device_id=RYTM_SHOW_KIT_DEVICE_ID),
        analog_four_scope=ShowKitScope(
            device_id=A4_SHOW_KIT_DEVICE_ID,
            locked_ids=(1, 2, 3, 4),
        ),
    )

    with pytest.raises(ValueError, match="requires its promoted snapshot id"):
        capture_reference(rytm, hardware_slot=20, snapshot_id=None)
    with pytest.raises(ValueError, match="cannot carry a Rytm snapshot id"):
        capture_reference(analog_four, hardware_slot=20, snapshot_id="wrong")
    for frame in (b"", b"\x00\xf7", b"\xf0\x00"):
        with pytest.raises(ValueError, match="framed SysEx"):
            capture_reference(replace(rytm, frame=frame), hardware_slot=20, snapshot_id="snap")
    for overridden, message in (
        ({"rytm_source_snapshot": replace(snapshot, snapshot_id="wrong")}, "source snapshot"),
        ({"recipe": replace(recipe, profile_id="wrong")}, "active profile"),
        ({"analog_four_source_frame": b"\xf0\x01\xf7"}, "source bytes"),
    ):
        arguments = {
            "entry": entry,
            "rytm_source_snapshot": snapshot,
            "analog_four_source_frame": analog_four.frame,
            "profile": profile,
            "recipe": recipe,
            "now": _NOW,
        }
        arguments.update(overridden)
        with pytest.raises(ValueError, match=message):
            forge_candidate_pair(**arguments)
    locked = forge_candidate_pair(
        entry=entry,
        rytm_source_snapshot=snapshot,
        analog_four_source_frame=analog_four.frame,
        profile=profile,
        recipe=recipe,
        now=_NOW,
    )
    assert locked.analog_four_frame == analog_four.frame
    assert locked.candidate.analog_four_candidate.values == ()
    assert locked.candidate.analog_four_candidate.semantic_fingerprint == analog_four.fingerprint
    assert any(delta.changed_keys for delta in locked.candidate.rytm_candidate.pad_deltas)
    assert analog_four_recapture_semantically_matches(
        analog_four, locked.candidate.analog_four_candidate
    )
    changed_unrelated = _capture(
        ANALOG_FOUR_DEVICE_ID,
        analog_four_saved_kit_frame(name=b"DIFFERENT A4"),
    )
    assert not analog_four_recapture_semantically_matches(
        changed_unrelated,
        locked.candidate.analog_four_candidate,
    )


def test_a4_semantic_capture_rejects_wrong_device_and_unverified_result(tmp_path: Path) -> None:
    rytm, analog_four, snapshot, entry = _sources()
    profile = ProfileRegistry(tmp_path).list_profiles()[0]
    recipe = ShowKitRecipe(
        profile_id=profile.profile_id,
        depth_preset="small",
        depth=0.25,
        seed=22,
        rytm_scope=ShowKitScope(device_id=RYTM_SHOW_KIT_DEVICE_ID),
        analog_four_scope=ShowKitScope(device_id=A4_SHOW_KIT_DEVICE_ID),
    )
    pair = forge_candidate_pair(
        entry=entry,
        rytm_source_snapshot=snapshot,
        analog_four_source_frame=analog_four.frame,
        profile=profile,
        recipe=recipe,
        now=_NOW,
    )
    for result in (rytm, replace(analog_four, round_trip_verified=False)):
        assert (
            analog_four_capture_semantic_fingerprint(result, pair.candidate.analog_four_candidate)
            is None
        )
        assert (
            analog_four_recapture_semantically_matches(result, pair.candidate.analog_four_candidate)
            is False
        )


def test_a4_source_out_of_promoted_range_fails_without_candidate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.cockpit.show_bank import forge

    _rytm, analog_four, snapshot, entry = _sources()
    profile = ProfileRegistry(tmp_path).list_profiles()[0]
    recipe = ShowKitRecipe(
        profile_id=profile.profile_id,
        depth_preset="small",
        depth=0.25,
        seed=22,
        rytm_scope=ShowKitScope(device_id=RYTM_SHOW_KIT_DEVICE_ID),
        analog_four_scope=ShowKitScope(device_id=A4_SHOW_KIT_DEVICE_ID, target_ids=(1,)),
    )
    # Simulate a codec-valid future/unsupported saved value on a promoted track.
    unpacked = bytearray(130)
    unpacked[128:130] = b"\xff\xff"
    monkeypatch.setattr(forge, "_a4_source_unpacked", lambda _frame: bytes(unpacked))
    with pytest.raises(ValueError, match="outside the verified"):
        forge_candidate_pair(
            entry=entry,
            rytm_source_snapshot=snapshot,
            analog_four_source_frame=analog_four.frame,
            profile=profile,
            recipe=recipe,
            now=_NOW,
        )


def test_workspace_complete_local_favorite_and_show_preflight_journey(
    tmp_path: Path,
) -> None:
    rytm, analog_four, _snapshot, _entry = _sources()
    ids = iter(("bank-show", "cue-opening"))
    clock = _MutableClock(_NOW)
    store = ShowBankStore(tmp_path / "banks", clock=clock)
    workspace = ShowKitForgeWorkspace(
        store,
        clock=clock,
        id_factory=lambda _prefix: next(ids),
    )

    bank = workspace.create_bank(
        name="Warehouse set",
        description="Ordered paired favorites",
        notes=("OXI continues to own sequencing.",),
    )
    source = workspace.adopt_sources(
        bank.bank_id,
        bank.revision,
        captures={
            ANALOG_RYTM_DEVICE_ID: rytm,
            ANALOG_FOUR_DEVICE_ID: analog_four,
        },
        rytm_fingerprint=rytm.fingerprint,
        analog_four_fingerprint=analog_four.fingerprint,
        rytm_slot=20,
        analog_four_slot=20,
    )
    assert source.status == "source"
    assert source.rytm_source.sysex.retained is not None
    assert source.analog_four_source.sysex.retained is not None

    profile = ProfileRegistry(tmp_path / "profiles").list_profiles()[0]
    created = workspace.generate_candidates(
        bank.bank_id,
        source.entry_id,
        workspace.bank(bank.bank_id).revision,
        profile=profile,
        depth_preset="small",
        depth=0.25,
        seed=91,
        candidate_count=2,
        # A full Rytm lock makes its semantic recapture intentionally equal
        # to the source in this no-hardware lifecycle test. Scope mutation is
        # independently covered above with a real changed Rytm pad.
        rytm_targets=(),
        rytm_locks=tuple(range(1, 13)),
        analog_four_targets=(1,),
        analog_four_locks=(),
    )
    assert len(created) == 2
    selected, source_snapshot, pair = workspace.audition_context(bank.bank_id, source.entry_id)
    assert selected.selected_candidate_id == pair.candidate_id
    assert source_snapshot.snapshot_id == source.rytm_source.snapshot_id

    favorite = workspace.mark_favorite(
        bank.bank_id,
        source.entry_id,
        pair.candidate_id,
        workspace.bank(bank.bank_id).revision,
    )
    assert favorite.status == "favorite"
    assert favorite.favorite_candidate is not None
    favorite_a4 = favorite.favorite_candidate.analog_four_candidate
    assert favorite_a4.sysex.retained is not None

    for device_id in (RYTM_SHOW_KIT_DEVICE_ID, A4_SHOW_KIT_DEVICE_ID):
        favorite = workspace.attest_saved(
            bank.bank_id,
            source.entry_id,
            workspace.bank(bank.bank_id).revision,
            device_id=device_id,
            hardware_slot=64,
        )
    assert favorite.status == "hardware-saved"

    a4_candidate_frame = store.read_retained(favorite_a4.sysex.retained)
    a4_recapture = decode_kit_capture_frame(ANALOG_FOUR_DEVICE_ID, a4_candidate_frame)
    recapture_time = _NOW + timedelta(minutes=1)
    clock.current = _NOW + timedelta(minutes=2)
    captures = {
        ANALOG_RYTM_DEVICE_ID: replace(rytm, captured_at=recapture_time),
        ANALOG_FOUR_DEVICE_ID: replace(
            a4_recapture,
            captured_at=recapture_time,
        ),
    }
    verified = workspace.verify_recaptures(
        bank.bank_id,
        source.entry_id,
        workspace.bank(bank.bank_id).revision,
        captures=captures,
    )
    assert verified.status == "verified"
    assert verified.rytm_recapture is not None
    assert verified.rytm_recapture.matches_candidate is True
    assert verified.rytm_recapture.matches_source is True
    assert verified.analog_four_recapture is not None
    assert verified.analog_four_recapture.matches_candidate is True
    assert verified.analog_four_recapture.matches_source is True

    preflight_time = _NOW + timedelta(minutes=3)
    clock.current = _NOW + timedelta(minutes=4)
    ready = workspace.run_preflight(
        bank.bank_id,
        source.entry_id,
        workspace.bank(bank.bank_id).revision,
        captures={
            device_id: replace(result, captured_at=preflight_time)
            for device_id, result in captures.items()
        },
    )
    assert ready.status == "show-ready"
    assert ready.show_time_preflight is not None
    assert ready.show_time_preflight.ready is True

    pack = ShowPackService(tmp_path / "packs", store=store).export(
        workspace.bank(bank.bank_id), package_id="warehouse-show"
    )
    assert pack.manifest.cue_order == (source.entry_id,)
    assert (pack.package_dir / "recovery.txt").is_file()

    source_projection = workspace.return_entry_to_source(
        bank.bank_id,
        source.entry_id,
        workspace.bank(bank.bank_id).revision,
    )
    recovered = workspace.bank(bank.bank_id).entry(source.entry_id)
    assert source_projection.snapshot_id == source.rytm_source.snapshot_id
    assert recovered.status == "verified"
    assert recovered.favorite == ready.favorite
    assert ShowKitForgeWorkspace(store).bank(bank.bank_id) == workspace.bank(bank.bank_id)


def test_mock_ws_forge_journey_reuses_exact_rytm_plan_and_never_claims_save(
    tmp_path: Path,
) -> None:
    rytm, analog_four, snapshot, _entry = _sources()
    ids = iter(("bank-ws", "cue-ws"))
    workspace = ShowKitForgeWorkspace(
        ShowBankStore(tmp_path / "banks", clock=lambda: _NOW),
        clock=lambda: _NOW,
        id_factory=lambda _prefix: next(ids),
    )
    history = HistoryStore()
    history.initial(snapshot)
    session = CockpitSession(
        profile_registry=ProfileRegistry(tmp_path / "profiles"),
        history_store=history,
        device=MockDeviceAdapter(initial=snapshot),
        kit_captures={
            ANALOG_RYTM_DEVICE_ID: rytm,
            ANALOG_FOUR_DEVICE_ID: analog_four,
        },
        show_kit_forge=workspace,
    )

    def command(
        command_type: str, **body: object
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

    ack, events = command(
        "show_bank_create",
        name="WS Show",
        description="Mock complete journey",
        notes=[],
    )
    assert ack["ok"] is True
    assert events[-1]["type"] == "show_bank_changed"
    bank = workspace.banks[0]

    ack, events = command(
        "show_bank_adopt_sources",
        bank_id=bank.bank_id,
        expected_revision=bank.revision,
        rytm_fingerprint=rytm.fingerprint,
        a4_fingerprint=analog_four.fingerprint,
        rytm_slot=20,
        a4_slot=20,
    )
    assert ack["ok"] is True
    assert {event["type"] for event in events} >= {
        "snapshot_changed",
        "show_bank_changed",
    }
    entry = workspace.bank(bank.bank_id).entries[0]
    profile = session.profile_registry.list_profiles()[0]

    ack, events = command(
        "show_bank_generate_candidates",
        bank_id=bank.bank_id,
        entry_id=entry.entry_id,
        expected_revision=workspace.bank(bank.bank_id).revision,
        depth_preset="medium",
        depth=0.5,
        candidate_count=3,
        seed=10,
        profile_id=profile.profile_id,
        rytm_targets=[1, 2],
        rytm_locks=[2],
        a4_targets=[1, 2],
        a4_locks=[2],
    )
    assert ack["ok"] is True
    assert len(cast(list[str], ack["candidate_ids"])) == 3
    assert session.current_candidate is not None
    assert {delta.pad_id for delta in session.current_candidate.pad_deltas} == {1}
    state_event = cast(
        dict[str, object],
        next(event for event in events if event["type"] == "show_bank_changed"),
    )
    state = cast(dict[str, object], state_event["show_bank"])
    assert state["schema_version"] == "show-bank-workspace-v1"

    ack, _events = command("prepare_send_plan")
    assert ack["ok"] is True
    assert session.current_send_plan is not None
    assert session.current_send_plan.target_pad_ids == frozenset({1, 2})
    assert session.current_send_plan.locked_pad_ids == frozenset({2})
    assert {packet.pad_id for packet in session.current_send_plan.packets} == {1}
    plan_id = session.current_send_plan.plan_id
    selected_id = session.current_send_plan.candidate_id
    ack, _events = command("send", send_plan_id=plan_id)
    assert ack["ok"] is True
    # Mock SEND is an in-memory projection, not a live unsaved hardware state.
    assert workspace.bank(bank.bank_id).entry(entry.entry_id).rytm_live_auditioned_at is None

    ack, _events = command(
        "show_bank_mark_favorite",
        bank_id=bank.bank_id,
        entry_id=entry.entry_id,
        candidate_id=selected_id,
        expected_revision=workspace.bank(bank.bank_id).revision,
    )
    assert ack["ok"] is True
    favorite = workspace.bank(bank.bank_id).entry(entry.entry_id)
    assert favorite.status == "favorite"
    assert favorite.rytm_hardware_save is None
    assert favorite.analog_four_hardware_save is None

    ack, _events = command(
        "show_bank_return_source",
        bank_id=bank.bank_id,
        entry_id=entry.entry_id,
        expected_revision=workspace.bank(bank.bank_id).revision,
    )
    assert ack["ok"] is True
    assert ack["hardware_changed"] is False
    assert ack["source_slots"] == {"rytm": 20, "analog_four": 20}
    assert ack["instruction"] == (
        "Cockpit reset its in-memory audition only; no instrument changed. "
        "Manually load the immutable Rytm and Analog Four source slots to "
        "return hardware."
    )
    returned = workspace.bank(bank.bank_id).entry(entry.entry_id)
    assert returned.favorite == favorite.favorite
    assert session.current_candidate is None
