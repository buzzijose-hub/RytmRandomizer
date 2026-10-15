"""Action-local recall proof reuse must retain whole-bank refusal semantics."""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Mapping
from dataclasses import FrozenInstanceError, replace
from pathlib import Path
from typing import Final

import pytest

from rytm_randomizer.cockpit.capture import (
    ANALOG_FOUR_DEVICE_ID,
    ANALOG_RYTM_DEVICE_ID,
    KitCaptureResult,
)
from rytm_randomizer.cockpit.data.parameter_scope import ParameterSelection
from rytm_randomizer.cockpit.data.show_bank import RetainedSysexArtifact, ShowBank
from rytm_randomizer.cockpit.export.writer import WriteError
from rytm_randomizer.cockpit.show_bank import store as store_module
from rytm_randomizer.cockpit.show_bank import workspace as workspace_module
from rytm_randomizer.cockpit.show_bank.export import verify_show_bank_frames
from rytm_randomizer.cockpit.show_bank.workspace import ShowKitForgeWorkspace
from rytm_randomizer.cockpit.ws import handlers
from rytm_randomizer.cockpit.ws.session import CockpitSession

from .test_native_offline_journey import _disk, _generate, _Journey, _journey, _session

pytestmark = [pytest.mark.fast, pytest.mark.usefixtures("offline_hardware_denied")]
_COMMANDS: Final[tuple[str, ...]] = ("show_bank_select_candidate", "show_bank_mark_favorite")


def _command(
    journey: _Journey,
    session: CockpitSession,
    command_type: str,
    candidate_id: str,
    *,
    revision: int | None = None,
    extra: Mapping[str, object] | None = None,
) -> dict[str, object]:
    return asyncio.run(
        handlers.handle_command(
            {
                "request_id": "action-local-recall",
                "command": {
                    "type": command_type,
                    "bank_id": journey.bank_id,
                    "entry_id": journey.entry_id,
                    "candidate_id": candidate_id,
                    "expected_revision": (
                        journey.workspace.bank(journey.bank_id).revision
                        if revision is None
                        else revision
                    ),
                    **({"replace_existing": True} if command_type.endswith("favorite") else {}),
                    **({} if extra is None else extra),
                },
            },
            session,
        )
    )


def _session_state(session: CockpitSession) -> tuple[object, ...]:
    return (
        session.device.capture_snapshot(),
        session.history_store.current,
        session.active_profile,
        session.current_candidate,
        session.current_send_plan,
        session.offline_a4_capture,
        session.depth,
        session.seed,
        session.preview_on,
        frozenset(session.pad_locks),
        frozenset(session.rytm_pad_targets),
        frozenset(session.a4_track_locks),
        frozenset(session.a4_track_targets),
        session.rytm_parameters,
        session.a4_parameters,
        session.stage_coordinator.state,
        tuple(session.pending_events),
        session.armed_apply,
        session.hardware_intent,
        session.recalled_offline_favorite,
    )


@pytest.mark.parametrize("command_type", _COMMANDS)
def test_recall_validates_complete_bank_once_per_command(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, command_type: str
) -> None:
    journey = _journey(tmp_path)
    candidates = _generate(journey, count=3)
    workspace = journey.workspace
    session = _session(workspace, journey.bank_id, journey.entry_id, tmp_path)
    verified: list[tuple[str, ...]] = []

    def count_full_proof(bank: ShowBank, frames: Mapping[str, bytes]) -> None:
        verify_show_bank_frames(bank, frames)
        verified.append(
            tuple(item.candidate_id for entry in bank.entries for item in entry.candidates)
        )

    monkeypatch.setattr(workspace_module, "verify_show_bank_frames", count_full_proof)
    for index, candidate in enumerate(candidates[1:]):
        ack = asyncio.run(
            handlers.handle_command(
                {
                    "request_id": f"recall-{index}",
                    "command": {
                        "type": command_type,
                        "bank_id": journey.bank_id,
                        "entry_id": journey.entry_id,
                        "candidate_id": candidate.candidate_id,
                        "expected_revision": workspace.bank(journey.bank_id).revision,
                        **({"replace_existing": True} if command_type.endswith("favorite") else {}),
                    },
                },
                session,
            )
        )
        assert ack["ok"], ack
        assert len(verified) == index + 1
        assert verified[-1] == tuple(item.candidate_id for item in candidates)
        assert session.current_candidate == candidate.rytm_candidate
        assert session.armed_apply is None and not session.hardware_intent
        assert session.current_send_plan is None and not session.device.is_armed


@pytest.mark.parametrize("command_type", _COMMANDS)
@pytest.mark.parametrize("role", ["rytm-source", "a4-source", "unrelated-cue"])
@pytest.mark.parametrize("damage", ["missing", "changed", "unsafe"])
def test_next_recall_refuses_changed_whole_bank_without_losing_previous_state(
    tmp_path: Path, command_type: str, role: str, damage: str
) -> None:
    journey = _journey(tmp_path)
    kept, other = _generate(journey)
    workspace = journey.workspace
    duplicated = workspace.duplicate(
        journey.bank_id, journey.entry_id, workspace.bank(journey.bank_id).revision
    )
    (unrelated,) = _generate(replace(journey, entry_id=duplicated.entry_id), seed=305, count=1)
    session = _session(workspace, journey.bank_id, journey.entry_id, tmp_path)
    assert _command(journey, session, "show_bank_mark_favorite", kept.candidate_id)["ok"]
    bank = workspace.bank(journey.bank_id)
    entry = bank.entry(journey.entry_id)
    artifact = {
        "rytm-source": entry.rytm_source.sysex,
        "a4-source": entry.analog_four_source.sysex,
        "unrelated-cue": unrelated.analog_four_candidate.sysex,
    }[role].retained
    assert artifact is not None
    path = workspace.store.root / artifact.artifact_name
    exact = path.read_bytes()
    if damage == "missing":
        path.unlink()
    elif damage == "changed":
        path.write_bytes(exact[:-1] + bytes((exact[-1] ^ 1,)))
    else:
        path.unlink()
        path.mkdir()
    state = _session_state(session)
    bank_state = workspace.state_dict()
    disk = _disk(workspace.store.root)
    ack = _command(
        journey,
        session,
        command_type,
        other.candidate_id,
        extra={"verified_context": {"verified": True}},
    )
    assert not ack["ok"] and ack["code"] == handlers.ERR_VALIDATION
    assert _session_state(session) == state
    assert workspace.bank(journey.bank_id) == bank
    assert workspace.state_dict() == bank_state
    assert workspace.bank(journey.bank_id).entry(journey.entry_id).favorite_candidate == kept
    assert _disk(workspace.store.root) == disk


@pytest.mark.parametrize("command_type", _COMMANDS)
def test_next_recall_replays_unrelated_recipe_claims_fresh_after_restart(
    tmp_path: Path, command_type: str
) -> None:
    journey = _journey(tmp_path)
    kept, other, unrelated = _generate(journey, fields=("filter2_resonance",), count=3)
    workspace = journey.workspace
    session = _session(workspace, journey.bank_id, journey.entry_id, tmp_path)
    assert _command(journey, session, "show_bank_mark_favorite", kept.candidate_id)["ok"]
    original = workspace.bank(journey.bank_id)
    altered = replace(
        unrelated,
        recipe=replace(
            unrelated.recipe,
            analog_four_scope=replace(
                unrelated.recipe.analog_four_scope, parameters=ParameterSelection(())
            ),
        ),
    )
    damaged = replace(
        original,
        revision=original.revision + 1,
        entries=(replace(original.entry(journey.entry_id), candidates=(kept, other, altered)),),
    )
    workspace.store.save(damaged)
    restarted = ShowKitForgeWorkspace(workspace.store)
    journey = replace(journey, workspace=restarted)
    session.show_kit_forge = restarted
    before = _session_state(session)
    disk = _disk(restarted.store.root)
    ack = _command(journey, session, command_type, other.candidate_id)
    assert not ack["ok"] and ack["code"] == handlers.ERR_VALIDATION
    assert _session_state(session) == before
    assert restarted.bank(journey.bank_id) == damaged
    assert restarted.store.load(journey.bank_id, revision=original.revision) == original
    assert _disk(restarted.store.root) == disk


@pytest.mark.parametrize("command_type", _COMMANDS)
@pytest.mark.parametrize("failure", ["stale-revision", "cancel-proof", "write-failure"])
def test_recall_failure_before_publication_preserves_session_and_favorite(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, command_type: str, failure: str
) -> None:
    journey = _journey(tmp_path)
    kept, other = _generate(journey)
    workspace = journey.workspace
    session = _session(workspace, journey.bank_id, journey.entry_id, tmp_path)
    assert _command(journey, session, "show_bank_mark_favorite", kept.candidate_id)["ok"]
    bank = workspace.bank(journey.bank_id)
    before = _session_state(session)
    disk = _disk(workspace.store.root)

    def cancel_proof(bank: ShowBank, frames: Mapping[str, bytes]) -> None:
        verify_show_bank_frames(bank, frames)
        raise asyncio.CancelledError

    def fail_write(*_args: object, **_kwargs: object) -> None:
        raise WriteError("injected action-local publication failure")

    if failure == "cancel-proof":
        monkeypatch.setattr(workspace_module, "verify_show_bank_frames", cancel_proof)
        with pytest.raises(asyncio.CancelledError):
            _command(journey, session, command_type, other.candidate_id)
    else:
        if failure == "write-failure":
            monkeypatch.setattr(workspace.store, "retain_sysex_set", fail_write)
        ack = _command(
            journey,
            session,
            command_type,
            other.candidate_id,
            revision=bank.revision - 1 if failure == "stale-revision" else None,
        )
        assert not ack["ok"]
    assert _session_state(session) == before
    assert workspace.bank(journey.bank_id) == bank
    assert _disk(workspace.store.root) == disk


def test_workspace_recall_result_is_frozen_and_originals_are_read_only_before_publication(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    journey = _journey(tmp_path)
    _, candidate = _generate(journey)
    workspace = journey.workspace
    bank = workspace.bank(journey.bank_id)
    entry = bank.entry(journey.entry_id)
    source_names = {
        entry.rytm_source.sysex.retained.artifact_name,
        entry.analog_four_source.sysex.retained.artifact_name,
    }
    reads: list[str] = []
    read = workspace.store.read_retained

    def observe_read(artifact: RetainedSysexArtifact) -> bytes:
        reads.append(artifact.artifact_name)
        return read(artifact)

    monkeypatch.setattr(workspace.store, "read_retained", observe_read)
    context = workspace.recall_candidate(
        journey.bank_id, journey.entry_id, candidate.candidate_id, bank.revision, offline_only=True
    )
    assert all(reads.count(name) == 1 for name in source_names)
    assert context.analog_four_source.frame == journey.originals[ANALOG_FOUR_DEVICE_ID]
    assert context.source.snapshot_id == entry.rytm_source.snapshot_id
    assert context.entry.selected_candidate == context.candidate == candidate
    with pytest.raises(FrozenInstanceError):
        context.source = context.source
    with pytest.raises(TypeError):
        context.source.pads[0].params["volume"] = 10
    assert context.bank == workspace.bank(journey.bank_id)


@pytest.mark.parametrize("command_type", _COMMANDS)
def test_restarted_recall_does_not_read_artifacts_after_atomic_publication(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, command_type: str
) -> None:
    journey = _journey(tmp_path)
    candidates = _generate(journey)
    for restart in range(2):
        workspace = ShowKitForgeWorkspace(journey.workspace.store)
        journey = replace(journey, workspace=workspace)
        session = _session(workspace, journey.bank_id, journey.entry_id, tmp_path)
        publish = workspace.store.retain_sysex_set

        def publish_then_refuse_reads(
            bank: ShowBank,
            frames: Mapping[str, bytes],
            *,
            _publish: Callable[[ShowBank, Mapping[str, bytes]], ShowBank] = publish,
            _workspace: ShowKitForgeWorkspace = workspace,
        ) -> ShowBank:
            updated = _publish(bank, frames)

            def forbidden(*_args: object, **_kwargs: object) -> None:
                pytest.fail("recall tried to validate or read an artifact after publication")

            scoped.setattr(_workspace.store, "read_retained", forbidden)
            scoped.setattr(_workspace, "candidate_context", forbidden)
            return updated

        with monkeypatch.context() as scoped:
            scoped.setattr(workspace.store, "retain_sysex_set", publish_then_refuse_reads)
            ack = _command(journey, session, command_type, candidates[restart].candidate_id)
            assert ack["ok"], ack
            assert session.offline_a4_capture.frame == journey.originals[ANALOG_FOUR_DEVICE_ID]
            assert session.current_candidate == candidates[restart].rytm_candidate
            assert session.armed_apply is None and not session.device.is_armed


@pytest.mark.parametrize("favorite", [False, True])
def test_legacy_workspace_transition_validates_once_and_preserves_return_shape(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, favorite: bool
) -> None:
    journey = _journey(tmp_path)
    _, candidate = _generate(journey)
    workspace = journey.workspace
    bank = workspace.bank(journey.bank_id)
    verified: list[int] = []

    def count_proof(bank: ShowBank, frames: Mapping[str, bytes]) -> None:
        verify_show_bank_frames(bank, frames)
        verified.append(bank.revision)
        with pytest.raises(TypeError):
            frames["client-proof"] = b"not trusted"

    monkeypatch.setattr(workspace_module, "verify_show_bank_frames", count_proof)
    if favorite:
        entry = workspace.mark_favorite(
            journey.bank_id,
            journey.entry_id,
            candidate.candidate_id,
            bank.revision,
            offline_only=True,
        )
        assert entry.favorite_candidate == candidate
    else:
        entry, source, mutation = workspace.select_candidate(
            journey.bank_id,
            journey.entry_id,
            candidate.candidate_id,
            bank.revision,
            offline_only=True,
        )
        assert source.snapshot_id == entry.rytm_source.snapshot_id
        assert mutation == candidate.rytm_candidate
    assert entry == workspace.bank(journey.bank_id).entry(journey.entry_id)
    assert verified == [bank.revision]


@pytest.mark.parametrize("different_candidate", [False, True])
def test_workspace_recall_refuses_lost_selection_before_publication_or_adoption(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, different_candidate: bool
) -> None:
    journey = _journey(tmp_path)
    other, candidate = _generate(journey)
    workspace = journey.workspace
    session = _session(workspace, journey.bank_id, journey.entry_id, tmp_path)
    bank = workspace.bank(journey.bank_id)
    unselected = replace(
        bank,
        entries=(
            replace(
                bank.entry(journey.entry_id),
                selected_candidate_id=other.candidate_id if different_candidate else None,
            ),
        ),
    )

    def lost_selection(*_args: object, **_kwargs: object) -> ShowBank:
        return unselected

    before = _session_state(session)
    disk = _disk(workspace.store.root)
    monkeypatch.setattr(workspace_module, "select_candidate", lost_selection)
    with pytest.raises(
        AssertionError,
        match="changed its candidate" if different_candidate else "lost its selection",
    ):
        workspace.recall_candidate(
            journey.bank_id,
            journey.entry_id,
            candidate.candidate_id,
            bank.revision,
            offline_only=True,
        )
    assert _session_state(session) == before
    assert workspace.bank(journey.bank_id) == bank
    assert _disk(workspace.store.root) == disk


@pytest.mark.parametrize("command_type", _COMMANDS)
@pytest.mark.parametrize("device_id", [ANALOG_RYTM_DEVICE_ID, ANALOG_FOUR_DEVICE_ID])
def test_source_decoder_drift_after_proof_is_refused_before_publication(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, command_type: str, device_id: str
) -> None:
    journey = _journey(tmp_path)
    (candidate,) = _generate(journey, count=1)
    workspace = journey.workspace
    session = _session(workspace, journey.bank_id, journey.entry_id, tmp_path)
    before = _session_state(session)
    bank = workspace.bank(journey.bank_id)
    disk = _disk(workspace.store.root)
    decode = store_module.decode_kit_capture_frame

    def prove_then_drift(verified: ShowBank, frames: Mapping[str, bytes]) -> None:
        verify_show_bank_frames(verified, frames)

        def contradictory(family: str, frame: bytes) -> KitCaptureResult:
            result = decode(family, frame)
            if family == device_id and frame == journey.originals[device_id]:
                return replace(result, fingerprint="contradictory-source")
            return result

        monkeypatch.setattr(store_module, "decode_kit_capture_frame", contradictory)

    monkeypatch.setattr(workspace_module, "verify_show_bank_frames", prove_then_drift)
    ack = _command(journey, session, command_type, candidate.candidate_id)
    assert not ack["ok"] and ack["code"] == handlers.ERR_VALIDATION
    assert _session_state(session) == before
    assert workspace.bank(journey.bank_id) == bank
    assert _disk(workspace.store.root) == disk


def test_recall_requires_explicit_boolean_favorite_before_reading_or_publishing(
    tmp_path: Path,
) -> None:
    journey = _journey(tmp_path)
    (candidate,) = _generate(journey, count=1)
    workspace = journey.workspace
    bank = workspace.bank(journey.bank_id)
    disk = _disk(workspace.store.root)
    with pytest.raises(ValueError, match="favorite must be a boolean"):
        workspace.recall_candidate(
            journey.bank_id,
            journey.entry_id,
            candidate.candidate_id,
            bank.revision,
            favorite=1,  # type: ignore[arg-type]
            offline_only=True,
        )
    assert workspace.bank(journey.bank_id) == bank
    assert _disk(workspace.store.root) == disk


def test_recall_refuses_missing_source_identity_before_publication(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    journey = _journey(tmp_path)
    (candidate,) = _generate(journey, count=1)
    workspace = journey.workspace
    bank = workspace.bank(journey.bank_id)
    entry = bank.entry(journey.entry_id)
    missing = replace(
        bank, entries=(replace(entry, rytm_source=replace(entry.rytm_source, snapshot_id=None)),)
    )
    disk = _disk(workspace.store.root)
    monkeypatch.setattr(workspace, "_checked_bank", lambda *_args: missing)
    with pytest.raises(ValueError, match="missing its mutation snapshot identity"):
        workspace.recall_candidate(
            journey.bank_id,
            journey.entry_id,
            candidate.candidate_id,
            missing.revision,
            offline_only=True,
        )
    assert workspace.bank(journey.bank_id) == bank
    assert _disk(workspace.store.root) == disk


def test_recall_refuses_contradictory_favorite_transition_before_publication(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    journey = _journey(tmp_path)
    (candidate,) = _generate(journey, count=1)
    workspace = journey.workspace
    bank = workspace.bank(journey.bank_id)
    disk = _disk(workspace.store.root)
    monkeypatch.setattr(workspace_module, "mark_favorite", lambda bank, *_args, **_kwargs: bank)
    with pytest.raises(AssertionError, match="favorite transition lost"):
        workspace.recall_candidate(
            journey.bank_id,
            journey.entry_id,
            candidate.candidate_id,
            bank.revision,
            favorite=True,
            offline_only=True,
        )
    assert workspace.bank(journey.bank_id) == bank
    assert _disk(workspace.store.root) == disk


@pytest.mark.parametrize("command_type", _COMMANDS)
def test_recall_rechecks_revision_after_whole_bank_proof(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, command_type: str
) -> None:
    journey = _journey(tmp_path)
    (candidate,) = _generate(journey, count=1)
    workspace = journey.workspace
    session = _session(workspace, journey.bank_id, journey.entry_id, tmp_path)
    bank = workspace.bank(journey.bank_id)
    before = _session_state(session)
    disk = _disk(workspace.store.root)
    checked = workspace._checked_bank
    changed = False

    def prove_then_change(verified: ShowBank, frames: Mapping[str, bytes]) -> None:
        nonlocal changed
        verify_show_bank_frames(verified, frames)
        changed = True

    def changed_revision(bank_id: str, revision: int) -> ShowBank:
        original = checked(bank_id, revision)
        return replace(original, revision=original.revision + 1) if changed else original

    monkeypatch.setattr(workspace_module, "verify_show_bank_frames", prove_then_change)
    monkeypatch.setattr(workspace, "_checked_bank", changed_revision)
    ack = _command(journey, session, command_type, candidate.candidate_id)
    assert not ack["ok"] and ack["code"] == handlers.ERR_VALIDATION
    assert _session_state(session) == before
    assert workspace.bank(journey.bank_id) == bank
    assert _disk(workspace.store.root) == disk


@pytest.mark.parametrize("command_type", _COMMANDS)
@pytest.mark.parametrize("changed_bytes", [False, True])
def test_cache_only_legacy_candidate_is_verified_and_retained_before_recall(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    command_type: str,
    changed_bytes: bool,
) -> None:
    journey = _journey(tmp_path)
    (candidate,) = _generate(journey, count=1)
    workspace = journey.workspace
    bank = workspace.bank(journey.bank_id)
    entry = bank.entry(journey.entry_id)
    sysex = candidate.analog_four_candidate.sysex
    frame = workspace.store.read_retained(sysex.retained)
    legacy_candidate = replace(
        candidate,
        analog_four_candidate=replace(
            candidate.analog_four_candidate, sysex=replace(sysex, retained=None)
        ),
    )
    legacy = replace(
        bank,
        bank_id="cache-only-legacy-recall",
        revision=0,
        entries=(replace(entry, candidates=(legacy_candidate,)),),
    )
    workspace.store.save(legacy)
    workspace.register_imported(legacy)
    journey = replace(journey, bank_id=legacy.bank_id)
    monkeypatch.setitem(
        workspace._volatile_frames,
        sysex.artifact_id,
        journey.originals[ANALOG_FOUR_DEVICE_ID] if changed_bytes else frame,
    )
    session = _session(workspace, legacy.bank_id, journey.entry_id, tmp_path)
    before = _session_state(session)
    disk = _disk(workspace.store.root)
    ack = _command(journey, session, command_type, candidate.candidate_id)
    if changed_bytes:
        assert not ack["ok"] and ack["code"] == handlers.ERR_VALIDATION
        assert _session_state(session) == before
        assert workspace.bank(legacy.bank_id) == legacy
        assert _disk(workspace.store.root) == disk
        return
    assert ack["ok"], ack
    selected = workspace.bank(legacy.bank_id).entry(journey.entry_id).selected_candidate
    assert selected is not None
    retained = selected.analog_four_candidate.sysex.retained
    assert retained is not None and workspace.store.read_retained(retained) == frame
    restarted = ShowKitForgeWorkspace(workspace.store)
    assert restarted.bank(legacy.bank_id).entry(journey.entry_id).selected_candidate == selected
    assert session.current_candidate == candidate.rytm_candidate
    assert session.armed_apply is None and not session.hardware_intent
