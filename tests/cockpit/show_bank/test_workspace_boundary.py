"""Focused fail-closed coverage for the Show Kit Forge workspace boundary."""

from __future__ import annotations

from dataclasses import replace
from datetime import timedelta
from pathlib import Path

import pytest
from cockpit.conftest import capture_fixed_frame as _capture

from conftest import (
    analog_four_saved_kit_frame,
    elektron_syx_message,
    rytm_real_layout_kit_payload,
)
from rytm_randomizer.cockpit.capture import (
    ANALOG_FOUR_DEVICE_ID,
    ANALOG_RYTM_DEVICE_ID,
    cockpit_snapshot_from_rytm_capture,
    decode_kit_capture_frame,
)
from rytm_randomizer.cockpit.data.show_bank import (
    A4_SHOW_KIT_DEVICE_ID,
    RYTM_SHOW_KIT_DEVICE_ID,
    OxiShowMetadata,
)
from rytm_randomizer.cockpit.show_bank import workspace as workspace_module
from rytm_randomizer.cockpit.show_bank.forge import (
    build_source_entry,
    capture_reference,
    rytm_capture_semantic_fingerprint,
)
from rytm_randomizer.cockpit.show_bank.readiness import add_entry, create_show_bank
from rytm_randomizer.cockpit.show_bank.store import ShowBankStore
from rytm_randomizer.cockpit.show_bank.workspace import ShowKitForgeWorkspace

from ._real_capture_support import capture_matching_rytm_candidate
from .conftest import SHOW_BANK_BOUNDARY_NOW as _NOW
from .conftest import build_show_bank_harness as _harness
from .conftest import generate_show_bank_candidates as _generate

pytestmark = pytest.mark.fast


@pytest.mark.parametrize(
    ("device_id", "frame"),
    (
        (
            ANALOG_RYTM_DEVICE_ID,
            elektron_syx_message(rytm_real_layout_kit_payload(b"PUBLIC BRIDGE")),
        ),
        (
            ANALOG_FOUR_DEVICE_ID,
            analog_four_saved_kit_frame(name=b"PUBLIC BRIDGE"),
        ),
    ),
)
def test_public_capture_decoder_bridge_is_input_only_and_byte_exact(
    device_id: str,
    frame: bytes,
) -> None:
    result = decode_kit_capture_frame(device_id, frame)

    assert result.frame == frame
    assert result.frame_bytes == len(frame)
    assert result.round_trip_verified is True
    assert result.input_only is True
    assert result.sent_midi is False


def test_workspace_fails_closed_on_stale_or_untrusted_capture_state(
    tmp_path: Path,
) -> None:
    empty = ShowKitForgeWorkspace(ShowBankStore(tmp_path / "empty"))
    assert empty.record_live_rytm_audition("candidate-missing") is None
    with pytest.raises(ValueError, match="unknown show bank"):
        empty.bank("missing")

    harness = _harness(tmp_path)
    workspace = harness.workspace
    bank = workspace.bank(harness.bank_id)
    assert workspace.store is harness.store
    assert workspace.active_bank_id == harness.bank_id
    assert workspace.select_bank(harness.bank_id) == bank

    for revision in (True, bank.revision - 1):
        with pytest.raises(ValueError, match="show bank changed"):
            workspace.checked_bank(harness.bank_id, revision)

    with pytest.raises(ValueError, match="current analog_rytm_mk2 KIT capture"):
        workspace.adopt_sources(
            harness.bank_id,
            bank.revision,
            captures={ANALOG_FOUR_DEVICE_ID: harness.analog_four},
            rytm_fingerprint=harness.rytm.fingerprint,
            analog_four_fingerprint=harness.analog_four.fingerprint,
            rytm_slot=1,
            analog_four_slot=1,
        )

    for untrusted in (
        replace(harness.rytm, round_trip_verified=False),
        replace(harness.rytm, sent_midi=True),
        replace(harness.rytm, input_only=False),
    ):
        with pytest.raises(ValueError, match="round-trip verified and input-only"):
            capture_reference(
                untrusted,
                hardware_slot=1,
                snapshot_id=cockpit_snapshot_from_rytm_capture(harness.rytm).snapshot_id,
            )
        with pytest.raises(ValueError, match="verified and input-only"):
            workspace.adopt_sources(
                harness.bank_id,
                bank.revision,
                captures={
                    ANALOG_RYTM_DEVICE_ID: untrusted,
                    ANALOG_FOUR_DEVICE_ID: harness.analog_four,
                },
                rytm_fingerprint=untrusted.fingerprint,
                analog_four_fingerprint=harness.analog_four.fingerprint,
                rytm_slot=1,
                analog_four_slot=1,
            )

    with pytest.raises(ValueError, match="capture fingerprint changed"):
        workspace.adopt_sources(
            harness.bank_id,
            bank.revision,
            captures=harness.captures,
            rytm_fingerprint="changed",
            analog_four_fingerprint=harness.analog_four.fingerprint,
            rytm_slot=1,
            analog_four_slot=1,
        )
    with pytest.raises(ValueError, match="source anchors are immutable"):
        workspace.adopt_sources(
            harness.bank_id,
            bank.revision,
            captures=harness.captures,
            rytm_fingerprint=harness.rytm.fingerprint,
            analog_four_fingerprint=harness.analog_four.fingerprint,
            rytm_slot=1,
            analog_four_slot=1,
            entry_id=harness.entry_id,
        )

    for count in (True, 0, 9):
        with pytest.raises(ValueError, match="candidate_count must be in 1..8"):
            workspace.generate_candidates(
                harness.bank_id,
                harness.entry_id,
                bank.revision,
                profile=harness.profile,
                depth_preset="small",
                depth=0.25,
                seed=1,
                candidate_count=count,
                rytm_targets=(),
                rytm_locks=(),
                analog_four_targets=(1,),
                analog_four_locks=(),
            )
    with pytest.raises(ValueError, match="select a candidate"):
        workspace.audition_context(harness.bank_id, harness.entry_id)
    with pytest.raises(ValueError, match="requires a favorite"):
        workspace.verify_recaptures(
            harness.bank_id,
            harness.entry_id,
            bank.revision,
            captures=harness.captures,
        )


def test_workspace_recapture_preflight_revocation_recovery_and_return(
    tmp_path: Path,
) -> None:
    harness = _harness(tmp_path)
    first, second = _generate(harness)
    workspace = harness.workspace

    selected, source, mutation = workspace.select_candidate(
        harness.bank_id,
        harness.entry_id,
        second.candidate_id,
        workspace.bank(harness.bank_id).revision,
    )
    assert selected.selected_candidate_id == second.candidate_id
    assert source.snapshot_id == selected.rytm_source.snapshot_id
    assert mutation.candidate_id == second.candidate_id

    favorite = workspace.mark_favorite(
        harness.bank_id,
        harness.entry_id,
        first.candidate_id,
        workspace.bank(harness.bank_id).revision,
    )
    assert favorite.favorite_candidate is not None
    assert favorite.selected_candidate_id == first.candidate_id
    assert (
        "Save on instrument, then recapture"
        in workspace.state_dict()["banks"][0]["entries"][0]["readiness"]["recovery_actions"]
    )

    with pytest.raises(ValueError, match="Save on instrument"):
        workspace.verify_recaptures(
            harness.bank_id,
            harness.entry_id,
            workspace.bank(harness.bank_id).revision,
            captures=harness.captures,
        )

    for device_id in (RYTM_SHOW_KIT_DEVICE_ID, A4_SHOW_KIT_DEVICE_ID):
        favorite = workspace.attest_saved(
            harness.bank_id,
            harness.entry_id,
            workspace.bank(harness.bank_id).revision,
            device_id=device_id,
            hardware_slot=64,
        )
    assert favorite.favorite_candidate is not None
    with pytest.raises(ValueError, match="requires a new current-KIT dump"):
        workspace.verify_recaptures(
            harness.bank_id,
            harness.entry_id,
            workspace.bank(harness.bank_id).revision,
            captures=harness.captures,
        )
    retained = favorite.favorite_candidate.analog_four_candidate.sysex.retained
    assert retained is not None
    analog_four_recapture = decode_kit_capture_frame(
        ANALOG_FOUR_DEVICE_ID,
        harness.store.read_retained(retained),
    )
    recapture_time = _NOW + timedelta(minutes=1)
    harness.clock.current = _NOW + timedelta(minutes=2)

    conflicting = capture_reference(
        harness.rytm,
        hardware_slot=64,
        snapshot_id=cockpit_snapshot_from_rytm_capture(harness.rytm).snapshot_id,
    )
    conflicting = replace(
        conflicting,
        sysex=replace(
            conflicting.sysex,
            frame_bytes=conflicting.sysex.frame_bytes + 1,
        ),
    )
    with pytest.raises(ValueError, match="conflicting exact bytes"):
        workspace._share_declared_sysex(
            workspace.bank(harness.bank_id),
            conflicting,
        )

    captures = {
        ANALOG_RYTM_DEVICE_ID: replace(
            harness.rytm,
            captured_at=recapture_time,
        ),
        ANALOG_FOUR_DEVICE_ID: replace(
            analog_four_recapture,
            captured_at=recapture_time,
        ),
    }
    verified = workspace.verify_recaptures(
        harness.bank_id,
        harness.entry_id,
        workspace.bank(harness.bank_id).revision,
        captures=captures,
    )
    assert verified.status == "verified"
    assert (
        harness.store.latest_revision(harness.bank_id) == workspace.bank(harness.bank_id).revision
    )
    assert (
        ShowKitForgeWorkspace(harness.store).bank(harness.bank_id).entry(harness.entry_id).status
        == "verified"
    )
    with pytest.raises(ValueError, match="requires a new current-KIT dump"):
        workspace.run_preflight(
            harness.bank_id,
            harness.entry_id,
            workspace.bank(harness.bank_id).revision,
            captures=captures,
        )

    preflight_time = _NOW + timedelta(minutes=3)
    harness.clock.current = _NOW + timedelta(minutes=4)
    mismatched = {
        device_id: replace(result, captured_at=preflight_time)
        for device_id, result in captures.items()
    }
    mismatched[ANALOG_RYTM_DEVICE_ID] = replace(
        mismatched[ANALOG_RYTM_DEVICE_ID],
        fingerprint="0" * 16,
    )
    revoked = workspace.run_preflight(
        harness.bank_id,
        harness.entry_id,
        workspace.bank(harness.bank_id).revision,
        captures=mismatched,
    )
    assert revoked.status == "verified"
    assert revoked.show_time_preflight is not None
    assert revoked.show_time_preflight.rytm_matches is False
    projected = workspace.state_dict()["banks"][0]["entries"][0]
    assert any(
        reason.startswith("Current Rytm KIT differs")
        for reason in projected["readiness"]["blocked_reasons"]
    )

    repeated_preflight_time = _NOW + timedelta(minutes=5)
    harness.clock.current = _NOW + timedelta(minutes=6)
    fresh_matching = {
        device_id: replace(result, captured_at=repeated_preflight_time)
        for device_id, result in captures.items()
    }
    ready = workspace.run_preflight(
        harness.bank_id,
        harness.entry_id,
        workspace.bank(harness.bank_id).revision,
        captures=fresh_matching,
    )
    assert ready.status == "show-ready"
    historical_projection = ShowKitForgeWorkspace(harness.store).state_dict()["banks"][0][
        "entries"
    ][0]
    assert historical_projection["status"] == "verified"
    assert historical_projection["readiness"]["show_ready"] is False
    assert any(
        "historical" in reason for reason in historical_projection["readiness"]["blocked_reasons"]
    )
    assert workspace.record_live_rytm_audition(first.candidate_id) is not None
    current_projection = workspace.state_dict()["banks"][0]["entries"][0]
    assert current_projection["rytm_audition_status"] == "live_unsaved_hardware"
    restarted_projection = ShowKitForgeWorkspace(harness.store).state_dict()["banks"][0]["entries"][
        0
    ]
    assert restarted_projection["rytm_audition_status"] == ("historical_audition_hardware_unknown")
    returned_source = workspace.return_entry_to_source(
        harness.bank_id,
        harness.entry_id,
        workspace.bank(harness.bank_id).revision,
    )
    returned = workspace.bank(harness.bank_id).entry(harness.entry_id)
    assert returned_source.snapshot_id == returned.rytm_source.snapshot_id
    assert returned.selected_candidate_id is None
    assert returned.rytm_live_auditioned_candidate_id is None
    assert returned.favorite == ready.favorite
    assert returned.status == "verified"
    assert workspace.record_live_rytm_audition("candidate-not-selected") is None

    unrelated = capture_reference(
        _capture(
            ANALOG_FOUR_DEVICE_ID,
            analog_four_saved_kit_frame(name=b"UNRELATED A4"),
        ),
        hardware_slot=10,
        snapshot_id=None,
    )
    assert (
        workspace._share_declared_sysex(
            workspace.bank(harness.bank_id),
            unrelated,
        )
        == unrelated
    )


def test_workspace_reloads_retained_source_and_fails_closed_on_missing_or_mismatch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    harness = _harness(tmp_path)
    reloaded = ShowKitForgeWorkspace(harness.store, clock=lambda: _NOW)
    source = reloaded.source_snapshot(harness.bank_id, harness.entry_id)
    assert (
        source.snapshot_id
        == harness.workspace.bank(harness.bank_id).entry(harness.entry_id).rytm_source.snapshot_id
    )
    revision = reloaded.bank(harness.bank_id).revision
    reloaded.retain_capture(
        harness.bank_id,
        harness.entry_id,
        revision,
        capture_kind="source",
        device_id=RYTM_SHOW_KIT_DEVICE_ID,
        current_captures={},
    )
    assert reloaded.bank(harness.bank_id).revision == revision

    mismatched = replace(harness.rytm, fingerprint="f" * 16)
    corrupt_view = ShowKitForgeWorkspace(harness.store, clock=lambda: _NOW)
    monkeypatch.setattr(
        workspace_module,
        "decode_kit_capture_frame",
        lambda _device_id, _frame: mismatched,
    )
    with pytest.raises(ValueError, match="fingerprint does not match"):
        corrupt_view.source_snapshot(harness.bank_id, harness.entry_id)

    missing_store = ShowBankStore(tmp_path / "missing", clock=lambda: _NOW)
    snapshot = cockpit_snapshot_from_rytm_capture(harness.rytm)
    entry = build_source_entry(
        entry_id="cue-unretained",
        cue_index=1,
        name="Unretained",
        description="Deliberate fail-closed fixture",
        rytm_capture=harness.rytm,
        analog_four_capture=harness.analog_four,
        rytm_slot=1,
        analog_four_slot=1,
        rytm_snapshot_id=snapshot.snapshot_id,
        now=_NOW,
    )
    bank = add_entry(
        create_show_bank(bank_id="bank-unretained", name="Unretained", clock=lambda: _NOW),
        entry,
        clock=lambda: _NOW,
    )
    missing_store.save(bank)
    missing = ShowKitForgeWorkspace(missing_store, clock=lambda: _NOW)
    with pytest.raises(ValueError, match="exact SysEx bytes are not retained"):
        missing.source_snapshot(bank.bank_id, entry.entry_id)

    with pytest.raises(ValueError, match="exact requested capture bytes"):
        missing.retain_capture(
            bank.bank_id,
            entry.entry_id,
            bank.revision,
            capture_kind="source",
            device_id=A4_SHOW_KIT_DEVICE_ID,
            current_captures={
                ANALOG_FOUR_DEVICE_ID: replace(
                    harness.analog_four,
                    fingerprint="0" * 16,
                )
            },
        )
    with pytest.raises(ValueError, match="requires a selected candidate"):
        missing.retain_capture(
            bank.bank_id,
            entry.entry_id,
            bank.revision,
            capture_kind="candidate",
            device_id=A4_SHOW_KIT_DEVICE_ID,
            current_captures={},
        )
    retained_entry = missing.retain_capture(
        bank.bank_id,
        entry.entry_id,
        bank.revision,
        capture_kind="source",
        device_id=RYTM_SHOW_KIT_DEVICE_ID,
        current_captures={ANALOG_RYTM_DEVICE_ID: harness.rytm},
    )
    assert retained_entry.rytm_source.sysex.retained is not None


def test_workspace_metadata_order_duplicate_remove_and_retention_edges(
    tmp_path: Path,
) -> None:
    harness = _harness(tmp_path)
    workspace = harness.workspace
    _generate(harness, count=1)
    bank = workspace.update_bank(
        harness.bank_id,
        workspace.bank(harness.bank_id).revision,
        name="Updated show",
        description="Updated",
        notes=("One", "Two"),
    )
    entry = workspace.update_entry(
        harness.bank_id,
        harness.entry_id,
        bank.revision,
        name="Updated cue",
        description="Metadata only",
        oxi=OxiShowMetadata(project="Set", pattern="A01", chapter="Opening"),
        audition_notes=("Audition",),
        energy_level=5,
        energy_notes=("High",),
        transition_notes=("Cut",),
        recovery_notes=("Load sources",),
    )
    assert entry.oxi.project == "Set"
    assert entry.energy_level == 5

    selected = entry.selected_candidate
    assert selected is not None
    assert selected.analog_four_candidate.sysex.retained is None
    candidate_retained = workspace.retain_capture(
        harness.bank_id,
        harness.entry_id,
        workspace.bank(harness.bank_id).revision,
        capture_kind="candidate",
        device_id=A4_SHOW_KIT_DEVICE_ID,
        current_captures={},
    )
    retained_candidate = candidate_retained.selected_candidate
    assert retained_candidate is not None
    assert retained_candidate.analog_four_candidate.sysex.retained is not None
    with pytest.raises(ValueError, match="only for Analog Four"):
        workspace.retain_capture(
            harness.bank_id,
            harness.entry_id,
            workspace.bank(harness.bank_id).revision,
            capture_kind="candidate",
            device_id=RYTM_SHOW_KIT_DEVICE_ID,
            current_captures={},
        )

    revision = workspace.bank(harness.bank_id).revision
    retained = workspace.retain_capture(
        harness.bank_id,
        harness.entry_id,
        revision,
        capture_kind="source",
        device_id=RYTM_SHOW_KIT_DEVICE_ID,
        current_captures={},
    )
    assert retained.rytm_source.sysex.retained is not None
    assert workspace.bank(harness.bank_id).revision == revision
    assert harness.store.latest_revision(harness.bank_id) == revision

    with pytest.raises(ValueError, match="favorite retention requires"):
        workspace.retain_capture(
            harness.bank_id,
            harness.entry_id,
            workspace.bank(harness.bank_id).revision,
            capture_kind="favorite",
            device_id=A4_SHOW_KIT_DEVICE_ID,
            current_captures={},
        )
    with pytest.raises(
        ValueError,
        match="capture_kind must be source, favorite, or candidate",
    ):
        workspace.retain_capture(
            harness.bank_id,
            harness.entry_id,
            workspace.bank(harness.bank_id).revision,
            capture_kind="invalid",  # type: ignore[arg-type]
            device_id=A4_SHOW_KIT_DEVICE_ID,
            current_captures={},
        )

    copied = workspace.duplicate(
        harness.bank_id,
        harness.entry_id,
        workspace.bank(harness.bank_id).revision,
    )
    reordered = workspace.reorder(
        harness.bank_id,
        workspace.bank(harness.bank_id).revision,
        (copied.entry_id, harness.entry_id),
    )
    assert [item.entry_id for item in reordered.entries] == [
        copied.entry_id,
        harness.entry_id,
    ]
    one = workspace.remove(
        harness.bank_id,
        copied.entry_id,
        workspace.bank(harness.bank_id).revision,
    )
    assert one.entries[0].cue_index == 1
    empty = workspace.remove(
        harness.bank_id,
        harness.entry_id,
        workspace.bank(harness.bank_id).revision,
    )
    assert empty.entries == ()


def test_deterministic_candidate_replay_is_rejected_without_revision_change(
    tmp_path: Path,
) -> None:
    harness = _harness(tmp_path)
    _generate(harness, count=1, seed=7)
    revision = harness.workspace.bank(harness.bank_id).revision

    with pytest.raises(ValueError, match="candidate set already exists"):
        _generate(harness, count=1, seed=7)
    assert harness.workspace.bank(harness.bank_id).revision == revision


def test_semantic_recapture_mismatch_stays_blocked_and_is_projected(
    tmp_path: Path,
) -> None:
    harness = _harness(tmp_path)
    workspace = harness.workspace
    bank = workspace.bank(harness.bank_id)
    (candidate,) = workspace.generate_candidates(
        harness.bank_id,
        harness.entry_id,
        bank.revision,
        profile=harness.profile,
        depth_preset="large",
        depth=0.75,
        seed=1234,
        candidate_count=1,
        rytm_targets=(1,),
        rytm_locks=(),
        analog_four_targets=(1,),
        analog_four_locks=(),
    )
    favorite = workspace.mark_favorite(
        harness.bank_id,
        harness.entry_id,
        candidate.candidate_id,
        workspace.bank(harness.bank_id).revision,
    )
    for device_id in (RYTM_SHOW_KIT_DEVICE_ID, A4_SHOW_KIT_DEVICE_ID):
        favorite = workspace.attest_saved(
            harness.bank_id,
            harness.entry_id,
            workspace.bank(harness.bank_id).revision,
            device_id=device_id,
            hardware_slot=64,
        )
    assert favorite.favorite_candidate is not None
    retained = favorite.favorite_candidate.analog_four_candidate.sysex.retained
    assert retained is not None
    harness.clock.current = _NOW + timedelta(minutes=2)
    recaptured = workspace.verify_recaptures(
        harness.bank_id,
        harness.entry_id,
        workspace.bank(harness.bank_id).revision,
        captures={
            ANALOG_RYTM_DEVICE_ID: replace(
                harness.rytm,
                captured_at=_NOW + timedelta(minutes=1),
            ),
            ANALOG_FOUR_DEVICE_ID: replace(
                decode_kit_capture_frame(
                    ANALOG_FOUR_DEVICE_ID,
                    harness.store.read_retained(retained),
                ),
                captured_at=_NOW + timedelta(minutes=1),
            ),
        },
    )
    assert recaptured.rytm_recapture is not None
    assert recaptured.rytm_recapture.matches_candidate is False
    reasons = workspace.state_dict()["banks"][0]["entries"][0]["readiness"]["blocked_reasons"]
    assert "Rytm recapture does not match the candidate semantics." in reasons


def test_changed_rytm_candidate_recapture_matches_candidate_not_source(
    tmp_path: Path,
) -> None:
    harness = _harness(tmp_path)
    workspace = harness.workspace
    bank = workspace.bank(harness.bank_id)
    (candidate,) = workspace.generate_candidates(
        harness.bank_id,
        harness.entry_id,
        bank.revision,
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
    assert candidate.rytm_candidate.pad_deltas[0].changed_keys
    favorite = workspace.mark_favorite(
        harness.bank_id,
        harness.entry_id,
        candidate.candidate_id,
        workspace.bank(harness.bank_id).revision,
    )
    for device_id in (RYTM_SHOW_KIT_DEVICE_ID, A4_SHOW_KIT_DEVICE_ID):
        favorite = workspace.attest_saved(
            harness.bank_id,
            harness.entry_id,
            workspace.bank(harness.bank_id).revision,
            device_id=device_id,
            hardware_slot=64,
        )

    recapture_time = _NOW + timedelta(minutes=1)
    harness.clock.current = _NOW + timedelta(minutes=2)
    rytm_recapture = capture_matching_rytm_candidate(
        harness.rytm,
        candidate.rytm_candidate,
        captured_at=recapture_time,
    )
    source_semantic = rytm_capture_semantic_fingerprint(harness.rytm)
    observed_semantic = rytm_capture_semantic_fingerprint(rytm_recapture)
    assert observed_semantic == candidate.rytm_semantic_fingerprint
    assert observed_semantic != source_semantic

    assert favorite.favorite_candidate is not None
    retained = favorite.favorite_candidate.analog_four_candidate.sysex.retained
    assert retained is not None
    analog_four_recapture = replace(
        decode_kit_capture_frame(
            ANALOG_FOUR_DEVICE_ID,
            harness.store.read_retained(retained),
        ),
        captured_at=recapture_time,
    )
    verified = workspace.verify_recaptures(
        harness.bank_id,
        harness.entry_id,
        workspace.bank(harness.bank_id).revision,
        captures={
            ANALOG_RYTM_DEVICE_ID: rytm_recapture,
            ANALOG_FOUR_DEVICE_ID: analog_four_recapture,
        },
    )

    assert verified.status == "verified"
    assert verified.rytm_recapture is not None
    assert verified.rytm_recapture.matches_candidate is True
    assert verified.rytm_recapture.matches_source is False


def test_register_imported_rejects_collision_and_store_mismatch_and_accepts_empty(
    tmp_path: Path,
) -> None:
    harness = _harness(tmp_path)
    bank = harness.workspace.bank(harness.bank_id)
    with pytest.raises(ValueError, match="already loaded"):
        harness.workspace.register_imported(bank)

    store = ShowBankStore(tmp_path / "imports", clock=lambda: _NOW)
    workspace = ShowKitForgeWorkspace(store, clock=lambda: _NOW)
    stored = create_show_bank(
        bank_id="bank-mismatch-import",
        name="Stored name",
        clock=lambda: _NOW,
    )
    store.save(stored)
    with pytest.raises(ValueError, match="differs from the stored revision"):
        workspace.register_imported(replace(stored, name="Different in-memory name"))

    empty = create_show_bank(
        bank_id="bank-empty-import",
        name="Empty import",
        clock=lambda: _NOW,
    )
    store.save(empty)
    assert workspace.register_imported(empty) == empty


def test_workspace_defensive_transition_and_source_invariants_fail_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    generated = ShowKitForgeWorkspace(
        ShowBankStore(tmp_path / "generated-ids", clock=lambda: _NOW),
        clock=lambda: _NOW,
    ).create_bank(name="Generated id", description="", notes=())
    assert generated.bank_id.startswith("bank-")

    harness = _harness(tmp_path)
    workspace = harness.workspace
    (candidate,) = _generate(harness, count=1)
    bank = workspace.bank(harness.bank_id)
    entry = bank.entry(harness.entry_id)

    without_selection = replace(entry, selected_candidate_id=None)
    transition_lost_selection = replace(bank, entries=(without_selection,))
    with monkeypatch.context() as scoped:
        scoped.setattr(
            workspace_module,
            "select_candidate",
            lambda *_args, **_kwargs: transition_lost_selection,
        )
        with pytest.raises(AssertionError, match="lost its selection"):
            workspace.select_candidate(
                harness.bank_id,
                harness.entry_id,
                candidate.candidate_id,
                bank.revision,
            )

    with monkeypatch.context() as scoped:
        scoped.setattr(
            workspace_module,
            "mark_favorite",
            lambda *_args, **_kwargs: bank,
        )
        with pytest.raises(AssertionError, match="lost its selected candidate"):
            workspace.mark_favorite(
                harness.bank_id,
                harness.entry_id,
                candidate.candidate_id,
                bank.revision,
            )

    no_snapshot = replace(
        entry,
        rytm_source=replace(entry.rytm_source, snapshot_id=None),
    )
    no_snapshot_bank = replace(bank, entries=(no_snapshot,))
    reloaded = ShowKitForgeWorkspace(harness.store, clock=lambda: _NOW)
    with pytest.raises(ValueError, match="missing its mutation snapshot identity"):
        reloaded._source_snapshot(no_snapshot_bank, no_snapshot)
